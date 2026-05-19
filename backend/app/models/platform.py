"""
Platform domain — audit, notifications, vendor onboarding, settings, support.

Design notes:
- audit_logs.before_state / after_state stored as JSON text (SQLite compatible).
- notifications.channel: EMAIL | SMS | IN_APP | PUSH
- notification.type uses a code: BOOKING_CONFIRMED | PAYOUT_SENT | etc.
- platform_settings.key acts as code — unique string key for global config.
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.identity import User


class AuditLog(Base):
    __tablename__ = "audit_logs"

    actor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    # user | system | webhook
    actor_type: Mapped[str] = mapped_column(String(20), default="user", nullable=False)

    # e.g. booking.cancel | vendor.approve | product.create
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # e.g. Booking | Vendor | Product
    resource_type: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(index=True)

    # JSON stored as text — works on SQLite and Postgres alike
    before_state: Mapped[str | None] = mapped_column(Text)
    after_state: Mapped[str | None] = mapped_column(Text)

    ip_address: Mapped[str | None] = mapped_column(String(45))    # IPv6 max = 45 chars
    user_agent: Mapped[str | None] = mapped_column(String(500))


class Notification(Base):
    __tablename__ = "notifications"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # EMAIL | SMS | IN_APP | PUSH
    channel: Mapped[str] = mapped_column(String(20), nullable=False)

    # code: BOOKING_CONFIRMED | BOOKING_CANCELLED | ORDER_SHIPPED
    #       PAYOUT_SENT | REVIEW_PUBLISHED | ACCOUNT_VERIFIED
    type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)

    subject: Mapped[str | None] = mapped_column(String(255))
    # JSON payload (template vars, deep-link, etc.) stored as text
    payload: Mapped[str | None] = mapped_column(Text)

    # queued | sent | failed | read
    status: Mapped[str] = mapped_column(String(20), default="queued", nullable=False, index=True)
    failure_reason: Mapped[str | None] = mapped_column(Text)

    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class VendorApplication(Base):
    __tablename__ = "vendor_applications"

    applicant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    business_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # FARM | WINERY | AGRITOURISM | RESTAURANT
    type: Mapped[str] = mapped_column(String(30), nullable=False)

    region: Mapped[str | None] = mapped_column(String(120))
    contact_email: Mapped[str] = mapped_column(String(255), nullable=False)
    website: Mapped[str | None] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)

    # JSON array of document URLs
    documents: Mapped[str | None] = mapped_column(Text)

    # pending | approved | rejected
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False, index=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text)

    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # FK to the created vendor once approved
    vendor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("vendors.id", ondelete="SET NULL"))
    applicant: Mapped["User"] = relationship(
        foreign_keys=[applicant_id],
    )
    reviewer: Mapped["User | None"] = relationship(
        foreign_keys=[reviewed_by],
    )


class PlatformSetting(Base):
    __tablename__ = "platform_settings"

    # key acts as code — e.g. BOOKING_COMMISSION_RATE | MAINTENANCE_MODE
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    # JSON value stored as text — can hold string, number, bool, or object
    value: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))


class FeatureFlag(Base):
    __tablename__ = "feature_flags"

    # name acts as code — e.g. DIASPORA_SHIPPING | PRO_ANALYTICS | MAP_VIEW
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # JSON conditions (e.g. restrict to vendor tiers, regions, user roles)
    conditions: Mapped[str | None] = mapped_column(Text)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    vendor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("vendors.id", ondelete="SET NULL"), index=True)
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    subject: Mapped[str] = mapped_column(String(255), nullable=False)

    # open | in_progress | waiting_on_user | resolved | closed
    status: Mapped[str] = mapped_column(String(30), default="open", nullable=False, index=True)
    # low | medium | high | urgent
    priority: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)

    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # ── Relationships ─────────────────────────────────────────────────────────
    user: Mapped["User"] = relationship(
        foreign_keys=[user_id],
    )
    assignee: Mapped["User | None"] = relationship(
        foreign_keys=[assigned_to],
    )
    messages: Mapped[list["SupportMessage"]] = relationship(
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="SupportMessage.created_at",
    )


class SupportMessage(Base):
    __tablename__ = "support_messages"

    ticket_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("support_tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)

    body: Mapped[str] = mapped_column(Text, nullable=False)
    # internal notes are visible only to platform staff
    is_internal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # ── Relationships ─────────────────────────────────────────────────────────
    sender: Mapped["User"] = relationship(
        foreign_keys=[sender_id],
    )
    ticket: Mapped["SupportTicket"] = relationship(back_populates="messages")
