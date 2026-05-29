from sqladmin import ModelView
from sqladmin.models import ModelViewMeta

from app.models import (
    User, Role, Permission, RolePermission, UserRole,
    Vendor, VendorMedia, Experience, ExperienceSlot, Product, Promotion,
    Booking, Order, OrderItem, Payment, Refund, Payout, Review,
    AuditLog, Notification, VendorApplication, PlatformSetting, FeatureFlag,
    SupportTicket, SupportMessage,
)


class BaseModelAdmin(ModelView):
    page_size = 20
    can_view_details = True
    can_create = True
    can_edit = True
    can_delete = True


def create_admin_view(model, name, plural, icon, category, **kwargs):
    attrs = {
        "name": name,
        "name_plural": plural,
        "icon": icon,
        "category": category,
    }
    attrs.update(kwargs)
    return ModelViewMeta(f"{name}Admin", (BaseModelAdmin,), attrs, model=model)


UserAdmin = create_admin_view(
    User,
    "User",
    "Users",
    "fa-solid fa-user",
    "Identity",
    column_list=[User.id, User.email, User.full_name, User.status, User.is_superuser, User.last_login_at],
    column_searchable_list=[User.email, User.full_name],
)

RoleAdmin = create_admin_view(
    Role,
    "Role",
    "Roles",
    "fa-solid fa-shield",
    "Identity",
    column_list=[Role.id, Role.code, Role.name],
    column_searchable_list=[Role.code, Role.name],
)

PermissionAdmin = create_admin_view(
    Permission,
    "Permission",
    "Permissions",
    "fa-solid fa-key",
    "Identity",
    column_list=[Permission.id, Permission.code,],
    column_searchable_list=[Permission.code],
)

RolePermissionAdmin = create_admin_view(
    RolePermission,
    "RolePermission",
    "Role Permissions",
    "fa-solid fa-list-check",
    "Identity",
)

UserRoleAdmin = create_admin_view(
    UserRole,
    "UserRole",
    "User Roles",
    "fa-solid fa-user-tag",
    "Identity",
)

VendorAdmin = create_admin_view(
    Vendor,
    "Vendor",
    "Vendors",
    "fa-solid fa-store",
    "Partners",
    column_list=[Vendor.id, Vendor.name, Vendor.type, Vendor.status, Vendor.tier, Vendor.region],
    column_searchable_list=[Vendor.name, Vendor.slug, Vendor.email],
)

VendorMediaAdmin = create_admin_view(
    VendorMedia,
    "VendorMedia",
    "Vendor Media",
    "fa-solid fa-image",
    "Partners",
    column_list=[VendorMedia.id, VendorMedia.vendor_id, VendorMedia.type, VendorMedia.sort_order],
)

ExperienceAdmin = create_admin_view(
    Experience,
    "Experience",
    "Experiences",
    "fa-solid fa-ticket",
    "Booking System",
    column_list=[Experience.id, Experience.vendor_id, Experience.title, Experience.type, Experience.base_price, Experience.status],
    column_searchable_list=[Experience.title],
)

ExperienceSlotAdmin = create_admin_view(
    ExperienceSlot,
    "ExperienceSlot",
    "Experience Slots",
    "fa-solid fa-calendar-day",
    "Booking System",
    column_list=[ExperienceSlot.id, ExperienceSlot.experience_id, ExperienceSlot.starts_at, ExperienceSlot.available_spots, ExperienceSlot.status],
)

ProductAdmin = create_admin_view(
    Product,
    "Product",
    "Products",
    "fa-solid fa-cart-shopping",
    "Shop",
    column_list=[Product.id, Product.vendor_id, Product.name, Product.category, Product.price, Product.stock_qty, Product.status],
    column_searchable_list=[Product.name],
)

PromotionAdmin = create_admin_view(
    Promotion,
    "Promotion",
    "Promotions",
    "fa-solid fa-tag",
    "Marketing",
    column_list=[Promotion.id, Promotion.vendor_id, Promotion.code, Promotion.type, Promotion.value, Promotion.status],
    column_searchable_list=[Promotion.code],
)

BookingAdmin = create_admin_view(
    Booking,
    "Booking",
    "Bookings",
    "fa-solid fa-book",
    "Commerce",
    column_list=[Booking.id, Booking.user_id, Booking.slot_id, Booking.status, Booking.total, Booking.created_at],
)

OrderAdmin = create_admin_view(
    Order,
    "Order",
    "Orders",
    "fa-solid fa-receipt",
    "Commerce",
    column_list=[Order.id, Order.user_id, Order.vendor_id, Order.status, Order.total, Order.created_at],
)

OrderItemAdmin = create_admin_view(
    OrderItem,
    "OrderItem",
    "Order Items",
    "fa-solid fa-box",
    "Commerce",
)

PaymentAdmin = create_admin_view(
    Payment,
    "Payment",
    "Payments",
    "fa-solid fa-credit-card",
    "Commerce",
    column_list=[Payment.id, Payment.order_id, Payment.booking_id, Payment.status, Payment.amount, Payment.provider],
)

RefundAdmin = create_admin_view(
    Refund,
    "Refund",
    "Refunds",
    "fa-solid fa-money-bill-arrow-left",
    "Commerce",
)

PayoutAdmin = create_admin_view(
    Payout,
    "Payout",
    "Payouts",
    "fa-solid fa-hand-holding-dollar",
    "Commerce",
)

ReviewAdmin = create_admin_view(
    Review,
    "Review",
    "Reviews",
    "fa-solid fa-star",
    "Commerce",
    column_list=[Review.id, Review.booking_id, Review.rating, Review.status, Review.created_at],
)

AuditLogAdmin = create_admin_view(
    AuditLog,
    "AuditLog",
    "Audit Logs",
    "fa-solid fa-history",
    "Platform",
    column_list=[AuditLog.id, AuditLog.actor_id, AuditLog.action, AuditLog.resource_type, AuditLog.resource_id, AuditLog.actor_type, AuditLog.created_at],
)

NotificationAdmin = create_admin_view(
    Notification,
    "Notification",
    "Notifications",
    "fa-solid fa-bell",
    "Platform",
)

VendorApplicationAdmin = create_admin_view(
    VendorApplication,
    "VendorApplication",
    "Vendor Applications",
    "fa-solid fa-file-signature",
    "Platform",
    column_list=[VendorApplication.id, VendorApplication.applicant_id, VendorApplication.business_name, VendorApplication.status, VendorApplication.submitted_at],
)

PlatformSettingAdmin = create_admin_view(
    PlatformSetting,
    "PlatformSetting",
    "Platform Settings",
    "fa-solid fa-cog",
    "Platform",
)

FeatureFlagAdmin = create_admin_view(
    FeatureFlag,
    "FeatureFlag",
    "Feature Flags",
    "fa-solid fa-toggle-on",
    "Platform",
)

SupportTicketAdmin = create_admin_view(
    SupportTicket,
    "SupportTicket",
    "Support Tickets",
    "fa-solid fa-headset",
    "Support",
)

SupportMessageAdmin = create_admin_view(
    SupportMessage,
    "SupportMessage",
    "Support Messages",
    "fa-solid fa-envelope",
    "Support",
)
