"""
Catalog domain — vendors, experiences, products, promotions.

Design notes:
- vendor.type uses a code string: FARM | WINERY | AGRITOURISM | RESTAURANT
- vendor.tier controls platform features: FREE | PRO
- experience.type: TASTING | COOKING_CLASS | FARM_STAY | TOUR | HARVEST
- product.category code: WINE | OLIVE_OIL | CHEESE | RAKIA | HONEY | OTHER
- promotion.type: PERCENTAGE | FIXED_AMOUNT
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey,
    Integer, Numeric, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models import identity


class Vendor(Base):
    __tablename__ = "vendors"

    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)

    # code: FARM | WINERY | AGRITOURISM | RESTAURANT
    type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)

    # pending | active | suspended | rejected
    status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False, index=True)

    description: Mapped[str | None] = mapped_column(Text)
    region: Mapped[str | None] = mapped_column(String(120), index=True)
    address: Mapped[str | None] = mapped_column(Text)
    lat: Mapped[float | None] = mapped_column(Float)
    lng: Mapped[float | None] = mapped_column(Float)

    # FREE | PRO — controls feature access
    tier: Mapped[str] = mapped_column(String(20), default="FREE", nullable=False)

    website: Mapped[str | None] = mapped_column(String(500))
    phone: Mapped[str | None] = mapped_column(String(30))
    email: Mapped[str | None] = mapped_column(String(255))

    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))

    # ── Relationships ─────────────────────────────────────────────────────────
    owner: Mapped["identity.User"] = relationship(
        back_populates="vendors",
        foreign_keys=[owner_id],
    )
    media: Mapped[list["VendorMedia"]] = relationship(
        back_populates="vendor",
        cascade="all, delete-orphan",
        order_by="VendorMedia.sort_order",
    )
    experiences: Mapped[list["Experience"]] = relationship(
        back_populates="vendor", cascade="all, delete-orphan",
    )
    products: Mapped[list["Product"]] = relationship(
        back_populates="vendor", cascade="all, delete-orphan",
    )
    promotions: Mapped[list["Promotion"]] = relationship(
        back_populates="vendor", cascade="all, delete-orphan",
    )


class VendorMedia(Base):
    __tablename__ = "vendor_media"

    vendor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False, index=True)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    # image | video
    type: Mapped[str] = mapped_column(String(20), default="image", nullable=False)
    alt_text: Mapped[str | None] = mapped_column(String(255))
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # ── Relationships ─────────────────────────────────────────────────────────
    vendor: Mapped["Vendor"] = relationship(back_populates="media")


class Experience(Base):
    __tablename__ = "experiences"

    vendor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False, index=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # TASTING | COOKING_CLASS | FARM_STAY | TOUR | HARVEST
    type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)

    duration_minutes: Mapped[int | None] = mapped_column(Integer)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    base_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="EUR", nullable=False)

    # draft | active | archived
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False, index=True)

    # ── Relationships ─────────────────────────────────────────────────────────
    vendor: Mapped["Vendor"] = relationship(back_populates="experiences")
    slots: Mapped[list["ExperienceSlot"]] = relationship(back_populates="experience", cascade="all, delete-orphan")


class ExperienceSlot(Base):
    __tablename__ = "experience_slots"

    experience_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("experiences.id", ondelete="CASCADE"), nullable=False, index=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    available_spots: Mapped[int] = mapped_column(Integer, nullable=False)

    # open | full | cancelled
    status: Mapped[str] = mapped_column(String(20), default="open", nullable=False, index=True)

    # ── Relationships ─────────────────────────────────────────────────────────
    experience: Mapped["Experience"] = relationship(back_populates="slots")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="slot")  # type: ignore[name-defined]


class Product(Base):
    __tablename__ = "products"

    vendor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False, index=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # WINE | OLIVE_OIL | CHEESE | RAKIA | HONEY | OTHER
    category: Mapped[str] = mapped_column(String(40), nullable=False, index=True)

    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="EUR", nullable=False)
    stock_qty: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    shippable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    weight_grams: Mapped[int | None] = mapped_column(Integer)

    # draft | active | archived | out_of_stock
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False, index=True)

    # ── Relationships ─────────────────────────────────────────────────────────
    vendor: Mapped["Vendor"] = relationship(back_populates="products")
    order_items: Mapped[list["OrderItem"]] = relationship(back_populates="product")  # type: ignore[name-defined]


class Promotion(Base):
    __tablename__ = "promotions"

    vendor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False, index=True)

    code: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    # PERCENTAGE | FIXED_AMOUNT
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    value: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    max_uses: Mapped[int | None] = mapped_column(Integer)
    used_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # applies_to: ALL | BOOKINGS | ORDERS
    applies_to: Mapped[str] = mapped_column(String(20), default="ALL", nullable=False)

    valid_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # active | expired | disabled
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint("vendor_id", "code", name="uq_promotion_vendor_code"),
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    vendor: Mapped["Vendor"] = relationship(back_populates="promotions")
