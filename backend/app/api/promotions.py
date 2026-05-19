from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.identity import User
from app.schemas.promotion import (
    PromotionCreateRequest, PromotionUpdateRequest,
    PromotionResponse, PromotionValidateRequest, PromotionValidateResponse,
)
from app.services.promotion_service import (
    create_promotion, list_promotions, get_promotion,
    update_promotion, disable_promotion, validate_promotion,
)

router = APIRouter(prefix="/promotions", tags=["Promotions"])


@router.post("/vendors/{vendor_id}", response_model=PromotionResponse, status_code=201)
def create(
    vendor_id: UUID,
    body: PromotionCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_promotion(db, vendor_id, body, current_user, request)


@router.get("/vendors/{vendor_id}", response_model=list[PromotionResponse])
def list_vendor_promotions(
    vendor_id: UUID,
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_promotions(db, vendor_id, current_user, status)


@router.get("/{promotion_id}", response_model=PromotionResponse)
def detail(
    promotion_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_promotion(db, promotion_id, current_user)


@router.patch("/{promotion_id}", response_model=PromotionResponse)
def update(
    promotion_id: UUID,
    body: PromotionUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return update_promotion(db, promotion_id, body, current_user, request)


@router.post("/{promotion_id}/disable", response_model=PromotionResponse)
def disable(
    promotion_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return disable_promotion(db, promotion_id, current_user, request)


@router.post("/validate", response_model=PromotionValidateResponse)
def validate(
    body: PromotionValidateRequest,
    db: Session = Depends(get_db),
):
    valid, discount, message = validate_promotion(
        db, body.code, body.vendor_id, body.amount
    )
    return PromotionValidateResponse(
        valid=valid,
        discount_amount=discount,
        message=message,
    )