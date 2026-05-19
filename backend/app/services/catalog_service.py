"""
Experience, slot, and product business logic.
"""
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.catalog import Experience, ExperienceSlot, Product, Vendor
from app.models.identity import User, UserRole, Role
from app.schemas.catalog import (
    ExperienceCreateRequest, ExperienceUpdateRequest,
    SlotCreateRequest, SlotUpdateRequest,
    ProductCreateRequest, ProductUpdateRequest,
)


# ── Auth helpers ───────────────────────────────────────────────────────────────

def _get_vendor_or_403(db: Session, vendor_id: uuid.UUID, current_user: User) -> Vendor:
    """
    Returns the vendor if it exists and the current user is its owner
    or a superadmin. Raises 403 otherwise.
    """
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    if current_user.is_superuser:
        return vendor

    is_vendor_admin = db.query(UserRole).join(Role).filter(
        UserRole.user_id == current_user.id,
        UserRole.vendor_id == vendor_id,
        Role.code.in_(["VENDOR_ADMIN", "VENDOR_STAFF"]),
    ).first()

    if not is_vendor_admin:
        raise HTTPException(status_code=403, detail="Not authorized for this vendor")

    return vendor


def _require_vendor_admin(db: Session, vendor_id: uuid.UUID, current_user: User) -> Vendor:
    """Stricter — requires VENDOR_ADMIN or superadmin (not VENDOR_STAFF)."""
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    if current_user.is_superuser:
        return vendor

    is_admin = db.query(UserRole).join(Role).filter(
        UserRole.user_id == current_user.id,
        UserRole.vendor_id == vendor_id,
        Role.code == "VENDOR_ADMIN",
    ).first()

    if not is_admin:
        raise HTTPException(status_code=403, detail="Vendor admin access required")

    return vendor


# ── Experiences ────────────────────────────────────────────────────────────────

def create_experience(
    db: Session,
    vendor_id: uuid.UUID,
    body: ExperienceCreateRequest,
    current_user: User,
) -> Experience:
    _require_vendor_admin(db, vendor_id, current_user)

    experience = Experience(
        vendor_id=vendor_id,
        title=body.title,
        description=body.description,
        type=body.type,
        duration_minutes=body.duration_minutes,
        capacity=body.capacity,
        base_price=body.base_price,
        currency=body.currency,
        status="draft",
    )
    db.add(experience)
    db.commit()
    db.refresh(experience)
    return experience


def get_experience(db: Session, experience_id: uuid.UUID) -> Experience:
    experience = db.query(Experience).filter(Experience.id == experience_id).first()
    if not experience:
        raise HTTPException(status_code=404, detail="Experience not found")
    return experience


def list_experiences(
    db: Session,
    vendor_id: uuid.UUID,
    include_drafts: bool = False,
) -> list[Experience]:
    q = db.query(Experience).filter(Experience.vendor_id == vendor_id)
    if not include_drafts:
        q = q.filter(Experience.status == "active")
    return q.order_by(Experience.created_at.desc()).all()


def update_experience(
    db: Session,
    experience_id: uuid.UUID,
    body: ExperienceUpdateRequest,
    current_user: User,
) -> Experience:
    experience = get_experience(db, experience_id)
    _require_vendor_admin(db, experience.vendor_id, current_user)

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(experience, field, value)

    db.commit()
    db.refresh(experience)
    return experience


def delete_experience(
    db: Session,
    experience_id: uuid.UUID,
    current_user: User,
) -> None:
    experience = get_experience(db, experience_id)
    _require_vendor_admin(db, experience.vendor_id, current_user)

    if experience.status == "active":
        raise HTTPException(
            status_code=409,
            detail="Cannot delete an active experience. Archive it first.",
        )

    db.delete(experience)
    db.commit()


# ── Slots ──────────────────────────────────────────────────────────────────────

def create_slot(
    db: Session,
    experience_id: uuid.UUID,
    body: SlotCreateRequest,
    current_user: User,
) -> ExperienceSlot:
    experience = get_experience(db, experience_id)
    _require_vendor_admin(db, experience.vendor_id, current_user)

    if body.starts_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=422, detail="Slot cannot start in the past")

    if body.ends_at and body.ends_at <= body.starts_at:
        raise HTTPException(status_code=422, detail="ends_at must be after starts_at")

    if body.available_spots > experience.capacity:
        raise HTTPException(
            status_code=422,
            detail=f"Available spots cannot exceed experience capacity ({experience.capacity})",
        )

    slot = ExperienceSlot(
        experience_id=experience_id,
        starts_at=body.starts_at,
        ends_at=body.ends_at,
        available_spots=body.available_spots,
        status="open",
    )
    db.add(slot)
    db.commit()
    db.refresh(slot)
    return slot


def list_slots(
    db: Session,
    experience_id: uuid.UUID,
    only_open: bool = True,
) -> list[ExperienceSlot]:
    q = db.query(ExperienceSlot).filter(
        ExperienceSlot.experience_id == experience_id,
        ExperienceSlot.starts_at >= datetime.now(timezone.utc),
    )
    if only_open:
        q = q.filter(ExperienceSlot.status == "open")
    return q.order_by(ExperienceSlot.starts_at.asc()).all()


def update_slot(
    db: Session,
    slot_id: uuid.UUID,
    body: SlotUpdateRequest,
    current_user: User,
) -> ExperienceSlot:
    slot = db.query(ExperienceSlot).filter(ExperienceSlot.id == slot_id).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")

    experience = get_experience(db, slot.experience_id)
    _require_vendor_admin(db, experience.vendor_id, current_user)

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(slot, field, value)

    db.commit()
    db.refresh(slot)
    return slot


def delete_slot(
    db: Session,
    slot_id: uuid.UUID,
    current_user: User,
) -> None:
    slot = db.query(ExperienceSlot).filter(ExperienceSlot.id == slot_id).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")

    experience = get_experience(db, slot.experience_id)
    _require_vendor_admin(db, experience.vendor_id, current_user)

    if slot.status == "open" and slot.starts_at > datetime.now(timezone.utc):
        # Check if anyone has booked this slot
        from app.models.commerce import Booking
        has_bookings = db.query(Booking).filter(
            Booking.slot_id == slot_id,
            Booking.status.in_(["pending", "confirmed"]),
        ).first()
        if has_bookings:
            raise HTTPException(
                status_code=409,
                detail="Cannot delete a slot with active bookings. Cancel it instead.",
            )

    db.delete(slot)
    db.commit()


# ── Products ───────────────────────────────────────────────────────────────────

def create_product(
    db: Session,
    vendor_id: uuid.UUID,
    body: ProductCreateRequest,
    current_user: User,
) -> Product:
    _require_vendor_admin(db, vendor_id, current_user)

    product = Product(
        vendor_id=vendor_id,
        name=body.name,
        description=body.description,
        category=body.category,
        price=body.price,
        currency=body.currency,
        stock_qty=body.stock_qty,
        shippable=body.shippable,
        weight_grams=body.weight_grams,
        status="draft",
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def get_product(db: Session, product_id: uuid.UUID) -> Product:
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


def list_products(
    db: Session,
    vendor_id: uuid.UUID,
    category: str | None = None,
    include_drafts: bool = False,
) -> list[Product]:
    q = db.query(Product).filter(Product.vendor_id == vendor_id)
    if not include_drafts:
        q = q.filter(Product.status == "active")
    if category:
        q = q.filter(Product.category == category.upper())
    return q.order_by(Product.created_at.desc()).all()


def update_product(
    db: Session,
    product_id: uuid.UUID,
    body: ProductUpdateRequest,
    current_user: User,
) -> Product:
    product = get_product(db, product_id)
    _require_vendor_admin(db, product.vendor_id, current_user)

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(product, field, value)

    # Auto set out_of_stock if stock hits 0
    if product.stock_qty == 0 and product.status == "active":
        product.status = "out_of_stock"

    db.commit()
    db.refresh(product)
    return product


def delete_product(
    db: Session,
    product_id: uuid.UUID,
    current_user: User,
) -> None:
    product = get_product(db, product_id)
    _require_vendor_admin(db, product.vendor_id, current_user)

    if product.status == "active":
        raise HTTPException(
            status_code=409,
            detail="Cannot delete an active product. Archive it first.",
        )

    db.delete(product)
    db.commit()