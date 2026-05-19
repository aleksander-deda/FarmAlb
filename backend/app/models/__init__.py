"""
Import all models here so SQLAlchemy's metadata is fully populated
before Alembic generates migrations or Base.metadata.create_all() runs.
"""
from app.models.identity import User, Role, Permission, RolePermission, UserRole
from app.models.catalog import Vendor, VendorMedia, Experience, ExperienceSlot, Product, Promotion
from app.models.commerce import Booking, Order, OrderItem, Payment, Refund, Payout, Review
from app.models.platform import AuditLog, Notification, VendorApplication, PlatformSetting, FeatureFlag, SupportTicket, SupportMessage

__all__ = [
    # identity
    "User", "Role", "Permission", "RolePermission", "UserRole",
    # catalog
    "Vendor", "VendorMedia", "Experience", "ExperienceSlot", "Product", "Promotion",
    # commerce
    "Booking", "Order", "OrderItem", "Payment", "Refund", "Payout", "Review",
    # platform
    "AuditLog", "Notification", "VendorApplication", "PlatformSetting", "FeatureFlag",
    "SupportTicket", "SupportMessage",
]
