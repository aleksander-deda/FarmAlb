"""
Order business logic.

Flow:
  1. Guest submits cart (vendor_id + items + optional promotion + shipping address)
  2. System validates all products belong to the vendor, are active, have stock
  3. Calculates line totals, subtotal, promotion discount, platform fee, total
  4. Reserves stock (decrements stock_qty)
  5. Creates order (pending) + order_items + payment (pending)
  6. Vendor ships → order becomes shipped + tracking number set
  7. Cancellation → stock restored, payment refunded
"""
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.core.constants import AuditAction
from app.models.catalog import Product, Promotion, Vendor
from app.models.commerce import Order, OrderItem, Payment
from app.models.identity import User, UserRole, Role
from app.schemas.order import (
    OrderCreateRequest, OrderCancelRequest,
    OrderShipRequest, TrackingUpdateRequest,
)
from app.utils.audit import AuditLogger
from app.services.base import BaseService


class OrderService(BaseService):
    """Service for managing orders."""

    def _is_vendor_member(self, db: Session, user: User, vendor_id: uuid.UUID) -> bool:
        if user.is_superuser:
            return True
        return bool(
            db.query(UserRole).join(Role).filter(
                UserRole.user_id == user.id,
                UserRole.vendor_id == vendor_id,
                Role.code.in_(["VENDOR_ADMIN", "VENDOR_STAFF"]),
            ).first()
        )

    def _apply_promotion(
        self,
        db: Session,
        code: str,
        vendor_id: uuid.UUID,
        subtotal: float,
    ) -> tuple[Promotion, float]:
        now = datetime.now(timezone.utc)
        promo = db.query(Promotion).filter(
            Promotion.code == code,
            Promotion.vendor_id == vendor_id,
            Promotion.status == "active",
            Promotion.applies_to.in_(["ALL", "ORDERS"]),
        ).first()

        if not promo:
            raise HTTPException(status_code=404, detail="Promotion code not found or not applicable")
        if promo.valid_from and promo.valid_from > now:
            raise HTTPException(status_code=422, detail="Promotion is not active yet")
        if promo.valid_until and promo.valid_until < now:
            raise HTTPException(status_code=422, detail="Promotion has expired")
        if promo.max_uses and promo.used_count >= promo.max_uses:
            raise HTTPException(status_code=422, detail="Promotion has reached its usage limit")

        if promo.type == "PERCENTAGE":
            discount = self.round_amount(subtotal * float(promo.value) / 100)
        else:
            discount = self.round_amount(min(float(promo.value), subtotal))

        return promo, discount

    def _calculate_shipping(self, items: list[tuple[Product, int]]) -> float:
        """
        Simple shipping calculation based on total weight.
        All shippable items — flat rate for now, easy to extend later.
        """
        total_grams = sum(
            (p.weight_grams or 500) * qty   # default 500g if not set
            for p, qty in items
            if p.shippable
        )
        if total_grams == 0:
            return 0.0
        elif total_grams <= 1000:
            return 3.50
        elif total_grams <= 5000:
            return 6.00
        else:
            return 10.00

    def create(
        self,
        db: Session,
        body: OrderCreateRequest,
        current_user: User,
        request: Any | None = None,
    ) -> Order:
        # 1. Validate vendor exists and is active
        vendor = db.query(Vendor).filter(
            Vendor.id == body.vendor_id,
            Vendor.status == "active",
        ).first()
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found or inactive")

        # 2. Validate and lock all products
        product_ids = [item.product_id for item in body.items]
        products = (
            db.query(Product)
            .filter(Product.id.in_(product_ids))
            .with_for_update()
            .all()
        )
        product_map = {p.id: p for p in products}

        # All products must exist and belong to the vendor
        for item in body.items:
            product = product_map.get(item.product_id)
            if not product:
                raise HTTPException(
                    status_code=404,
                    detail=f"Product {item.product_id} not found",
                )
            if product.vendor_id != body.vendor_id:
                raise HTTPException(
                    status_code=422,
                    detail=f"Product '{product.name}' does not belong to this vendor",
                )
            if product.status not in ("active",):
                raise HTTPException(
                    status_code=409,
                    detail=f"Product '{product.name}' is not available (status: {product.status})",
                )
            if product.stock_qty < item.quantity:
                raise HTTPException(
                    status_code=409,
                    detail=f"Insufficient stock for '{product.name}'. "
                           f"Available: {product.stock_qty}, requested: {item.quantity}",
                )

        # 3. Build order items and calculate subtotal
        item_tuples: list[tuple[Product, int]] = []
        order_items_data = []
        subtotal = 0.0

        for cart_item in body.items:
            product = product_map[cart_item.product_id]
            line_total = self.round_amount(float(product.price) * cart_item.quantity)
            subtotal = self.round_amount(subtotal + line_total)
            item_tuples.append((product, cart_item.quantity))
            order_items_data.append({
                "product": product,
                "quantity": cart_item.quantity,
                "unit_price": float(product.price),
                "line_total": line_total,
            })

        # 4. Apply promotion if provided
        promotion = None
        discount_amount = 0.0
        if body.promotion_code:
            promotion, discount_amount = self._apply_promotion(
                db, body.promotion_code, body.vendor_id, subtotal
            )

        # 5. Shipping cost
        shipping_cost = self._calculate_shipping(item_tuples)

        # 6. Platform fee and total
        discounted_subtotal = self.round_amount(subtotal - discount_amount)
        platform_fee = self.round_amount(discounted_subtotal * settings.platform_order_commission_rate)
        total = self.round_amount(discounted_subtotal + platform_fee + shipping_cost)

        # 7. Determine currency from first product
        currency = item_tuples[0][0].currency if item_tuples else "EUR"

        # 8. Create order
        order = Order(
            user_id=current_user.id,
            vendor_id=body.vendor_id,
            promotion_id=promotion.id if promotion else None,
            subtotal=subtotal,
            discount_amount=discount_amount,
            platform_fee=platform_fee,
            shipping_cost=shipping_cost,
            total=total,
            currency=currency,
            shipping_address=body.shipping_address,
            status="pending",
        )
        db.add(order)
        db.flush()

        # 9. Create order items and reserve stock
        for item_data in order_items_data:
            db.add(OrderItem(
                order_id=order.id,
                product_id=item_data["product"].id,
                product_name_snapshot=item_data["product"].name,
                quantity=item_data["quantity"],
                unit_price=item_data["unit_price"],
                line_total=item_data["line_total"],
            ))
            # Reserve stock
            item_data["product"].stock_qty -= item_data["quantity"]
            if item_data["product"].stock_qty == 0:
                item_data["product"].status = "out_of_stock"

        # 10. Create pending payment
        db.add(Payment(
            order_id=order.id,
            provider="stripe",
            amount=total,
            currency=currency,
            status="pending",
            initiated_at=datetime.now(timezone.utc),
        ))

        # 11. Increment promotion usage
        if promotion:
            promotion.used_count += 1

        db.commit()
        db.refresh(order)
        AuditLogger.log(
            db=db,
            action=AuditAction.ORDER_CREATE,
            resource_type="Order",
            actor=current_user,
            resource_id=order.id,
            after={
                "status": order.status,
                "total": float(order.total),
                "vendor_id": str(order.vendor_id),
            },
            request=request,
        )
        return order

    def get(
        self,
        db: Session,
        order_id: uuid.UUID,
        current_user: User,
    ) -> Order:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        if (
            order.user_id != current_user.id
            and not current_user.is_superuser
            and not self._is_vendor_member(db, current_user, order.vendor_id)
        ):
            raise HTTPException(status_code=403, detail="Not authorized")

        return order

    def list_my(
        self,
        db: Session,
        current_user: User,
        status: str | None = None,
    ) -> list[Order]:
        q = db.query(Order).filter(Order.user_id == current_user.id)
        if status:
            q = q.filter(Order.status == status)
        return q.order_by(Order.created_at.desc()).all()

    def list_vendor(
        self,
        db: Session,
        vendor_id: uuid.UUID,
        current_user: User,
        status: str | None = None,
    ) -> list[Order]:
        if not self._is_vendor_member(db, current_user, vendor_id):
            raise HTTPException(status_code=403, detail="Not authorized")

        q = db.query(Order).filter(Order.vendor_id == vendor_id)
        if status:
            q = q.filter(Order.status == status)
        return q.order_by(Order.created_at.desc()).all()

    def confirm(
        self,
        db: Session,
        order_id: uuid.UUID,
        current_user: User,
        request: Any | None = None,
    ) -> Order:
        """Move order from pending → confirmed after payment success."""
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        if order.status != "pending":
            raise HTTPException(status_code=409, detail=f"Order is already {order.status}")
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Superadmin only")

        order.status = "confirmed"
        if order.payment:
            order.payment.status = "confirmed"
            order.payment.confirmed_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(order)
        AuditLogger.log(
            db=db,
            action=AuditAction.ORDER_CONFIRM,
            resource_type="Order",
            actor=current_user,
            resource_id=order.id,
            before={"status": "pending"},
            after={"status": order.status},
            request=request,
        )
        return order

    def ship(
        self,
        db: Session,
        order_id: uuid.UUID,
        body: OrderShipRequest,
        current_user: User,
        request: Any | None = None,
    ) -> Order:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        if order.status != "confirmed":
            raise HTTPException(
                status_code=409,
                detail="Only confirmed orders can be marked as shipped",
            )
        if not self._is_vendor_member(db, current_user, order.vendor_id):
            raise HTTPException(status_code=403, detail="Not authorized")

        order.status = "shipped"
        order.tracking_number = body.tracking_number
        order.shipped_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(order)
        AuditLogger.log(
            db=db,
            action=AuditAction.ORDER_SHIP,
            resource_type="Order",
            actor=current_user,
            resource_id=order.id,
            before={"status": "confirmed"},
            after={"status": order.status, "tracking_number": order.tracking_number},
            request=request,
        )
        return order

    def deliver(
        self,
        db: Session,
        order_id: uuid.UUID,
        current_user: User,
        request: Any | None = None,
    ) -> Order:
        """Mark as delivered — can be called by vendor or triggered by webhook later."""
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        if order.status != "shipped":
            raise HTTPException(status_code=409, detail="Only shipped orders can be marked delivered")
        if not self._is_vendor_member(db, current_user, order.vendor_id) and not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Not authorized")

        order.status = "delivered"
        order.delivered_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(order)
        AuditLogger.log(
            db=db,
            action=AuditAction.ORDER_DELIVER,
            resource_type="Order",
            actor=current_user,
            resource_id=order.id,
            before={"status": "shipped"},
            after={"status": order.status},
            request=request,
        )
        return order

    def cancel(
        self,
        db: Session,
        order_id: uuid.UUID,
        body: OrderCancelRequest,
        current_user: User,
        request: Any | None = None,
    ) -> Order:
        order = db.query(Order).filter(Order.id == order_id).with_for_update().first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        if order.status not in ("pending", "confirmed"):
            raise HTTPException(
                status_code=409,
                detail=f"Cannot cancel an order with status '{order.status}'",
            )

        is_owner = order.user_id == current_user.id
        is_vendor = self._is_vendor_member(db, current_user, order.vendor_id)

        if not is_owner and not is_vendor and not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Not authorized")

        # Restore stock
        for item in order.items:
            product = db.query(Product).filter(
                Product.id == item.product_id
            ).with_for_update().first()
            if product:
                product.stock_qty += item.quantity
                if product.status == "out_of_stock" and product.stock_qty > 0:
                    product.status = "active"

        # Restore promotion usage
        if order.promotion_id:
            promo = db.query(Promotion).filter(
                Promotion.id == order.promotion_id
            ).first()
            if promo and promo.used_count > 0:
                promo.used_count -= 1

        # Update payment
        if order.payment:
            order.payment.status = "refunded"
            order.payment.refunded_at = datetime.now(timezone.utc)

        previous_status = order.status
        order.status = "cancelled"
        order.cancellation_reason = body.reason
        order.cancelled_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(order)
        AuditLogger.log(
            db=db,
            action=AuditAction.ORDER_CANCEL,
            resource_type="Order",
            actor=current_user,
            resource_id=order.id,
            before={"status": previous_status},
            after={"status": order.status, "reason": body.reason},
            request=request,
        )
        return order


# ── Global singleton instance and accessors ────────────────────────────────────

_order_service = OrderService()


def get_order_service() -> OrderService:
    """Get the global order service instance."""
    return _order_service


# ── Backward-compatible wrapper functions ──────────────────────────────────────

def create_order(
    db: Session,
    body: OrderCreateRequest,
    current_user: User,
    request: Any | None = None,
) -> Order:
    return get_order_service().create(db, body, current_user, request)


def get_order(
    db: Session,
    order_id: uuid.UUID,
    current_user: User,
) -> Order:
    return get_order_service().get(db, order_id, current_user)


def list_my_orders(
    db: Session,
    current_user: User,
    status: str | None = None,
) -> list[Order]:
    return get_order_service().list_my(db, current_user, status)


def list_vendor_orders(
    db: Session,
    vendor_id: uuid.UUID,
    current_user: User,
    status: str | None = None,
) -> list[Order]:
    return get_order_service().list_vendor(db, vendor_id, current_user, status)


def confirm_order(
    db: Session,
    order_id: uuid.UUID,
    current_user: User,
    request: Any | None = None,
) -> Order:
    return get_order_service().confirm(db, order_id, current_user, request)


def ship_order(
    db: Session,
    order_id: uuid.UUID,
    body: OrderShipRequest,
    current_user: User,
    request: Any | None = None,
) -> Order:
    return get_order_service().ship(db, order_id, body, current_user, request)


def deliver_order(
    db: Session,
    order_id: uuid.UUID,
    current_user: User,
    request: Any | None = None,
) -> Order:
    return get_order_service().deliver(db, order_id, current_user, request)


def cancel_order(
    db: Session,
    order_id: uuid.UUID,
    body: OrderCancelRequest,
    current_user: User,
    request: Any | None = None,
) -> Order:
    return get_order_service().cancel(db, order_id, body, current_user, request)
