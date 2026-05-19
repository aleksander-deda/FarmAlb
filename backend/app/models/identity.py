"""
Identity domain — users, roles, permissions.

Design notes:
- Roles and permissions use a `code` column (e.g. 'VENDOR_ADMIN', 'BOOKING_READ')
  as the stable identifier for business logic. `name` is display-only.
- user_roles is scoped: a user can be VENDOR_ADMIN for vendor A and GUEST elsewhere.
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Integer,
    String, Text, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.catalog import Vendor


class User(Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(30), unique=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str | None] = mapped_column(String(255))
    locale: Mapped[str] = mapped_column(String(10), default="sq")   # sq | en | it
    # active | suspended | pending_verification
    status: Mapped[str] = mapped_column(String(30), default="pending_verification", nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # ── Relationships ─────────────────────────────────────────────────────────
    user_roles: Mapped[list["UserRole"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="[UserRole.user_id]",
    )
    vendors: Mapped[list["Vendor"]] = relationship(
        back_populates="owner",
        foreign_keys="[Vendor.owner_id]",    # ← string form, not [Vendor.owner_id]
    )


class Role(Base):
    __tablename__ = "roles"

    # code is the stable identifier used in business logic — never changes.
    # e.g. SUPER_ADMIN | VENDOR_ADMIN | VENDOR_STAFF | GUEST
    code: Mapped[str] = mapped_column(String(60), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # ── Relationships ─────────────────────────────────────────────────────────
    role_permissions: Mapped[list["RolePermission"]] = relationship(back_populates="role", cascade="all, delete-orphan")
    user_roles: Mapped[list["UserRole"]] = relationship(back_populates="role")


class Permission(Base):
    __tablename__ = "permissions"

    # code pattern: RESOURCE_ACTION  e.g. BOOKING_READ | PRODUCT_CREATE | PAYOUT_APPROVE
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    resource: Mapped[str] = mapped_column(String(60), nullable=False)   # e.g. booking
    action: Mapped[str] = mapped_column(String(60), nullable=False)     # e.g. read
    description: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        UniqueConstraint("resource", "action", name="uq_permission_resource_action"),
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    role_permissions: Mapped[list["RolePermission"]] = relationship(back_populates="permission")


class RolePermission(Base):
    __tablename__ = "role_permissions"

    role_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    permission_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False)

    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    role: Mapped["Role"] = relationship(back_populates="role_permissions")
    permission: Mapped["Permission"] = relationship(back_populates="role_permissions")


class UserRole(Base):
    __tablename__ = "user_roles"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    vendor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("vendors.id", ondelete="CASCADE"))
    granted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    granted_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))  # second FK to users — this was the ambiguity

    __table_args__ = (
        UniqueConstraint("user_id", "role_id", "vendor_id", name="uq_user_role_vendor"),
    )

    user: Mapped["User"] = relationship(
        back_populates="user_roles",
        foreign_keys=[user_id],        # ← explicitly point to user_id only
    )
    role: Mapped["Role"] = relationship(back_populates="user_roles")
