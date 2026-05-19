from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_superadmin
from app.db.session import get_db
from app.models.identity import User
from app.schemas.order import (
    OrderCreateRequest, OrderCancelRequest,
    OrderResponse, OrderDetailResponse,
    OrderShipRequest,
)
from app.services.order_service import (
    create_order, get_order, list_my_orders,
    list_vendor_orders, confirm_order,
    ship_order, deliver_order, cancel_order,
)

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("", response_model=OrderResponse, status_code=201)
def place_order(
    body: OrderCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_order(db, body, current_user)


@router.get("/me", response_model=list[OrderResponse])
def my_orders(
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_my_orders(db, current_user, status)


@router.get("/vendor/{vendor_id}", response_model=list[OrderResponse])
def vendor_orders(
    vendor_id: UUID,
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_vendor_orders(db, vendor_id, current_user, status)


@router.get("/{order_id}", response_model=OrderDetailResponse)
def order_detail(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = get_order(db, order_id, current_user)
    response = OrderDetailResponse.model_validate(order)
    response.items = order.items
    response.payment_status = order.payment.status if order.payment else None
    return response


@router.post("/{order_id}/confirm", response_model=OrderResponse)
def confirm(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superadmin),
):
    return confirm_order(db, order_id, current_user)


@router.post("/{order_id}/ship", response_model=OrderResponse)
def ship(
    order_id: UUID,
    body: OrderShipRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ship_order(db, order_id, body, current_user)


@router.post("/{order_id}/deliver", response_model=OrderResponse)
def deliver(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return deliver_order(db, order_id, current_user)


@router.post("/{order_id}/cancel", response_model=OrderResponse)
def cancel(
    order_id: UUID,
    body: OrderCancelRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return cancel_order(db, order_id, body, current_user)