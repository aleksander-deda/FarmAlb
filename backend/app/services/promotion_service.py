import uuid
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.catalog import Promotion, Vendor
from app.models.identity import User, UserRole, Role
from app.schemas.promotion import (
    PromotionCreateRequest, PromotionUpdateRequest,
)
from app.utils.audit import audit_log


def _round(value: float) -> float:
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _require_vendor_admin(db: Session, vendor_id: uuid.UUID, user: User) -> Vendor:
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    if user.is_superuser:
        return vendor
    is_admin = db.query(UserRole).join(Role).filter(
        UserRole.user_id == user.id,
        UserRole.vendor_id == vendor_id,
        Role.code == "VENDOR_ADMIN",
    ).first()
    if not is_admin:
        raise HTTPException(status_code=403, detail="Vendor admin access required")
    return vendor


def create_promotion(
    db: Session,
    vendor_id: uuid.UUID,
    body: PromotionCreateRequest,
    current_user: User,
    request=None,
) -> Promotion:
    _require_vendor_admin(db, vendor_id, current_user)

    # Code must be unique per vendor
    existing = db.query(Promotion).filter(
        Promotion.vendor_id == vendor_id,
        Promotion.code == body.code,
    ).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Promotion code '{body.code}' already exists for this vendor",
        )

    # Percentage cap validation
    if body.type == "PERCENTAGE" and body.value > 100:
        raise HTTPException(status_code=422, detail="Percentage discount cannot exceed 100%")

    # Date range validation
    if body.valid_from and body.valid_until:
        if body.valid_until <= body.valid_from:
            raise HTTPException(status_code=422, detail="valid_until must be after valid_from")

    promotion = Promotion(
        vendor_id=vendor_id,
        code=body.code,
        type=body.type,
        value=body.value,
        applies_to=body.applies_to,
        max_uses=body.max_uses,
        valid_from=body.valid_from,
        valid_until=body.valid_until,
        status="active",
        used_count=0,
    )
    db.add(promotion)
    db.flush()

    audit_log(
        db=db,
        actor=current_user,
        action="promotion.create",
        resource_type="Promotion",
        resource_id=promotion.id,
        after={
            "code": promotion.code,
            "type": promotion.type,
            "value": promotion.value,
            "vendor_id": str(vendor_id),
        },
        request=request,
    )

    db.commit()
    db.refresh(promotion)
    return promotion


def list_promotions(
    db: Session,
    vendor_id: uuid.UUID,
    current_user: User,
    status: str | None = None,
) -> list[Promotion]:
    _require_vendor_admin(db, vendor_id, current_user)
    q = db.query(Promotion).filter(Promotion.vendor_id == vendor_id)
    if status:
        q = q.filter(Promotion.status == status)
    return q.order_by(Promotion.created_at.desc()).all()


def get_promotion(
    db: Session,
    promotion_id: uuid.UUID,
    current_user: User,
) -> Promotion:
    promotion = db.query(Promotion).filter(Promotion.id == promotion_id).first()
    if not promotion:
        raise HTTPException(status_code=404, detail="Promotion not found")
    _require_vendor_admin(db, promotion.vendor_id, current_user)
    return promotion


def update_promotion(
    db: Session,
    promotion_id: uuid.UUID,
    body: PromotionUpdateRequest,
    current_user: User,
    request=None,
) -> Promotion:
    promotion = db.query(Promotion).filter(Promotion.id == promotion_id).first()
    if not promotion:
        raise HTTPException(status_code=404, detail="Promotion not found")
    _require_vendor_admin(db, promotion.vendor_id, current_user)

    if promotion.used_count > 0 and body.value is not None:
        raise HTTPException(
            status_code=409,
            detail="Cannot change the value of a promotion that has already been used",
        )

    before = {
        "value": promotion.value,
        "max_uses": promotion.max_uses,
        "status": promotion.status,
        "valid_from": str(promotion.valid_from),
        "valid_until": str(promotion.valid_until),
    }

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(promotion, field, value)

    audit_log(
        db=db,
        actor=current_user,
        action="promotion.update",
        resource_type="Promotion",
        resource_id=promotion.id,
        before=before,
        after=body.model_dump(exclude_unset=True),
        request=request,
    )

    db.commit()
    db.refresh(promotion)
    return promotion


def disable_promotion(
    db: Session,
    promotion_id: uuid.UUID,
    current_user: User,
    request=None,
) -> Promotion:
    promotion = db.query(Promotion).filter(Promotion.id == promotion_id).first()
    if not promotion:
        raise HTTPException(status_code=404, detail="Promotion not found")
    _require_vendor_admin(db, promotion.vendor_id, current_user)

    if promotion.status == "disabled":
        raise HTTPException(status_code=409, detail="Promotion is already disabled")

    before = {"status": promotion.status}
    promotion.status = "disabled"

    audit_log(
        db=db,
        actor=current_user,
        action="promotion.disable",
        resource_type="Promotion",
        resource_id=promotion.id,
        before=before,
        after={"status": "disabled"},
        request=request,
    )

    db.commit()
    db.refresh(promotion)
    return promotion


def validate_promotion(
    db: Session,
    code: str,
    vendor_id: uuid.UUID,
    amount: float,
) -> tuple[bool, float, str]:
    """
    Public validation — used by frontend before checkout to show discount preview.
    Returns (is_valid, discount_amount, message).
    """
    now = datetime.now(timezone.utc)
    promo = db.query(Promotion).filter(
        Promotion.code == code.upper(),
        Promotion.vendor_id == vendor_id,
        Promotion.status == "active",
    ).first()

    if not promo:
        return False, 0.0, "Promotion code not found"
    if promo.valid_from and promo.valid_from > now:
        return False, 0.0, "Promotion is not active yet"
    if promo.valid_until and promo.valid_until < now:
        return False, 0.0, "Promotion has expired"
    if promo.max_uses and promo.used_count >= promo.max_uses:
        return False, 0.0, "Promotion has reached its usage limit"

    if promo.type == "PERCENTAGE":
        discount = _round(amount * float(promo.value) / 100)
        message = f"{promo.value}% discount applied — you save €{discount}"
    else:
        discount = _round(min(float(promo.value), amount))
        message = f"€{discount} discount applied"

    return True, discount, message