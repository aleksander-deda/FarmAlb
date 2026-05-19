"""
Commerce domain — bookings, orders, payments, refunds, payouts, reviews.

Design notes:
- Both bookings and orders reference payments via nullable FK (one-to-one).
  A payment belongs to either a booking OR an order, never both.
- Payouts aggregate multiple transactions per vendor per period.
- Reviews are tied to a confirmed booking to enforce verified-visit logic.
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.catalog import ExperienceSlot
from app.models.identity import User


class Booking(Base):
    __tablename__ = "bookings"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    slot_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("experience_slots.id", ondelete="RESTRICT"), nullable=False, index=True)
    promotion_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("promotions.id", ondelete="SET NULL"))

    guests: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    subtotal: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    discount_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    platform_fee: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    total: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="EUR", nullable=False)

    # pending | confirmed | cancelled | completed | no_show
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False, index=True)
    cancellation_reason: Mapped[str | None] = mapped_column(Text)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))

    # internal notes visible only to platform staff
    staff_notes: Mapped[str | None] = mapped_column(Text)

    # ── Relationships ─────────────────────────────────────────────────────────
    user: Mapped["User"] = relationship(
        foreign_keys=[user_id],
    )
    slot: Mapped["ExperienceSlot"] = relationship(back_populates="bookings")
    payment: Mapped["Payment | None"] = relationship(back_populates="booking", uselist=False)
    review: Mapped["Review | None"] = relationship(back_populates="booking", uselist=False)


class Order(Base):
    __tablename__ = "orders"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    vendor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("vendors.id", ondelete="RESTRICT"), nullable=False, index=True)
    promotion_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("promotions.id", ondelete="SET NULL"))

    subtotal: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    discount_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    platform_fee: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    shipping_cost: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    total: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="EUR", nullable=False)

    shipping_address: Mapped[str | None] = mapped_column(Text)
    tracking_number: Mapped[str | None] = mapped_column(String(120))

    # pending | confirmed | processing | shipped | delivered | cancelled | refunded
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False, index=True)
    cancellation_reason: Mapped[str | None] = mapped_column(Text)

    shipped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # ── Relationships ─────────────────────────────────────────────────────────
    user: Mapped["User"] = relationship(
        foreign_keys=[user_id],
    )
    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan",
    )
    payment: Mapped["Payment | None"] = relationship(back_populates="order", uselist=False)


class OrderItem(Base):
    __tablename__ = "order_items"

    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)

    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    line_total: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    # snapshot of product name at time of purchase (product may change later)
    product_name_snapshot: Mapped[str] = mapped_column(String(255), nullable=False)

    # ── Relationships ─────────────────────────────────────────────────────────
    order: Mapped["Order"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship(back_populates="order_items")  # type: ignore[name-defined]


class Payment(Base):
    __tablename__ = "payments"

    # Exactly one of booking_id or order_id is set — enforced at application layer.
    booking_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("bookings.id", ondelete="RESTRICT"), unique=True, index=True)
    order_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("orders.id", ondelete="RESTRICT"), unique=True, index=True)

    # stripe | manual | bank_transfer
    provider: Mapped[str] = mapped_column(String(30), default="stripe", nullable=False)
    provider_ref: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)

    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="EUR", nullable=False)

    # pending | confirmed | failed | refunded | partially_refunded
    status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False, index=True)
    failure_reason: Mapped[str | None] = mapped_column(Text)

    initiated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    refunded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # ── Relationships ─────────────────────────────────────────────────────────
    booking: Mapped["Booking | None"] = relationship(back_populates="payment")
    order: Mapped["Order | None"] = relationship(back_populates="payment")
    refunds: Mapped[list["Refund"]] = relationship(back_populates="payment", cascade="all, delete-orphan")


class Refund(Base):
    __tablename__ = "refunds"

    payment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("payments.id", ondelete="RESTRICT"), nullable=False, index=True)
    initiated_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    provider_ref: Mapped[str | None] = mapped_column(String(255))

    # pending | processed | failed
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(Text)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # ── Relationships ─────────────────────────────────────────────────────────
    initiated_by_user: Mapped["User"] = relationship(
        foreign_keys=[initiated_by],
    )
    payment: Mapped["Payment"] = relationship(back_populates="refunds")


class Payout(Base):
    __tablename__ = "payouts"

    vendor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("vendors.id", ondelete="RESTRICT"), nullable=False, index=True)

    gross_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    commission_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    net_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="EUR", nullable=False)

    # pending | processing | paid | failed
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False, index=True)
    provider_ref: Mapped[str | None] = mapped_column(String(255))
    failure_reason: Mapped[str | None] = mapped_column(Text)

    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Review(Base):
    __tablename__ = "reviews"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    booking_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("bookings.id", ondelete="RESTRICT"), unique=True, nullable=False)
    vendor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False, index=True)

    rating: Mapped[int] = mapped_column(Integer, nullable=False)   # 1–5
    body: Mapped[str | None] = mapped_column(Text)
    verified_visit: Mapped[bool] = mapped_column(default=True, nullable=False)

    # pending | published | rejected
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False, index=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text)

    # ── Relationships ─────────────────────────────────────────────────────────
    booking: Mapped["Booking"] = relationship(back_populates="review")
