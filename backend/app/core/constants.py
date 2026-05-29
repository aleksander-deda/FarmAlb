"""
All status codes, type codes, and magic strings in one place.
Never hardcode these anywhere else — always import from here.
"""

# ── User ───────────────────────────────────────────────────────────────────────
class UserStatus:
    ACTIVE               = "active"
    SUSPENDED            = "suspended"
    PENDING_VERIFICATION = "pending_verification"

# ── Roles ──────────────────────────────────────────────────────────────────────
class RoleCode:
    SUPER_ADMIN  = "SUPER_ADMIN"
    VENDOR_ADMIN = "VENDOR_ADMIN"
    VENDOR_STAFF = "VENDOR_STAFF"
    GUEST        = "GUEST"

# ── Vendor ─────────────────────────────────────────────────────────────────────
class VendorType:
    FARM        = "FARM"
    WINERY      = "WINERY"
    AGRITOURISM = "AGRITOURISM"
    RESTAURANT  = "RESTAURANT"
    ALL         = [FARM, WINERY, AGRITOURISM, RESTAURANT]

class VendorStatus:
    PENDING  = "pending"
    ACTIVE   = "active"
    SUSPENDED = "suspended"
    REJECTED = "rejected"

class VendorTier:
    FREE = "FREE"
    PRO  = "PRO"

# ── Experience ─────────────────────────────────────────────────────────────────
class ExperienceType:
    TASTING       = "TASTING"
    COOKING_CLASS = "COOKING_CLASS"
    FARM_STAY     = "FARM_STAY"
    TOUR          = "TOUR"
    HARVEST       = "HARVEST"
    ALL           = [TASTING, COOKING_CLASS, FARM_STAY, TOUR, HARVEST]

class ExperienceStatus:
    DRAFT    = "draft"
    ACTIVE   = "active"
    ARCHIVED = "archived"

class SlotStatus:
    OPEN      = "open"
    FULL      = "full"
    CANCELLED = "cancelled"

# ── Product ────────────────────────────────────────────────────────────────────
class ProductCategory:
    WINE      = "WINE"
    OLIVE_OIL = "OLIVE_OIL"
    CHEESE    = "CHEESE"
    RAKIA     = "RAKIA"
    HONEY     = "HONEY"
    OTHER     = "OTHER"
    ALL       = [WINE, OLIVE_OIL, CHEESE, RAKIA, HONEY, OTHER]

class ProductStatus:
    DRAFT        = "draft"
    ACTIVE       = "active"
    ARCHIVED     = "archived"
    OUT_OF_STOCK = "out_of_stock"

# ── Promotion ──────────────────────────────────────────────────────────────────
class PromotionType:
    PERCENTAGE   = "PERCENTAGE"
    FIXED_AMOUNT = "FIXED_AMOUNT"

class PromotionAppliesTo:
    ALL      = "ALL"
    BOOKINGS = "BOOKINGS"
    ORDERS   = "ORDERS"

class PromotionStatus:
    ACTIVE   = "active"
    EXPIRED  = "expired"
    DISABLED = "disabled"

# ── Booking ────────────────────────────────────────────────────────────────────
class BookingStatus:
    PENDING   = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW   = "no_show"

# ── Order ──────────────────────────────────────────────────────────────────────
class OrderStatus:
    PENDING    = "pending"
    CONFIRMED  = "confirmed"
    PROCESSING = "processing"
    SHIPPED    = "shipped"
    DELIVERED  = "delivered"
    CANCELLED  = "cancelled"
    REFUNDED   = "refunded"

# ── Payment ────────────────────────────────────────────────────────────────────
class PaymentStatus:
    PENDING             = "pending"
    CONFIRMED           = "confirmed"
    FAILED              = "failed"
    REFUNDED            = "refunded"
    PARTIALLY_REFUNDED  = "partially_refunded"

class PaymentProvider:
    STRIPE       = "stripe"
    MANUAL       = "manual"
    BANK_TRANSFER = "bank_transfer"

# ── Payout ─────────────────────────────────────────────────────────────────────
class PayoutStatus:
    PENDING    = "pending"
    PROCESSING = "processing"
    PAID       = "paid"
    FAILED     = "failed"

# ── Review ─────────────────────────────────────────────────────────────────────
class ReviewStatus:
    PENDING   = "pending"
    PUBLISHED = "published"
    REJECTED  = "rejected"

# ── Notification ───────────────────────────────────────────────────────────────
class NotificationChannel:
    EMAIL  = "EMAIL"
    SMS    = "SMS"
    IN_APP = "IN_APP"
    PUSH   = "PUSH"

class NotificationStatus:
    QUEUED = "queued"
    SENT   = "sent"
    FAILED = "failed"
    READ   = "read"

class NotificationType:
    BOOKING_CONFIRMED  = "BOOKING_CONFIRMED"
    BOOKING_CANCELLED  = "BOOKING_CANCELLED"
    ORDER_CONFIRMED    = "ORDER_CONFIRMED"
    ORDER_SHIPPED      = "ORDER_SHIPPED"
    ORDER_DELIVERED    = "ORDER_DELIVERED"
    PAYOUT_SENT        = "PAYOUT_SENT"
    REVIEW_PUBLISHED   = "REVIEW_PUBLISHED"
    ACCOUNT_VERIFIED   = "ACCOUNT_VERIFIED"
    VENDOR_APPROVED    = "VENDOR_APPROVED"
    VENDOR_REJECTED    = "VENDOR_REJECTED"

# ── Support ────────────────────────────────────────────────────────────────────
class TicketStatus:
    OPEN            = "open"
    IN_PROGRESS     = "in_progress"
    WAITING_ON_USER = "waiting_on_user"
    RESOLVED        = "resolved"
    CLOSED          = "closed"

class TicketPriority:
    LOW    = "low"
    MEDIUM = "medium"
    HIGH   = "high"
    URGENT = "urgent"

# ── Audit ──────────────────────────────────────────────────────────────────────
class AuditAction:
    # Auth
    AUTH_LOGIN    = "auth.login"
    AUTH_REGISTER = "auth.register"
    AUTH_REFRESH  = "auth.refresh"
    # Vendor
    VENDOR_CREATE  = "vendor.create"
    VENDOR_UPDATE  = "vendor.update"
    VENDOR_APPROVE = "vendor.approve"
    VENDOR_SUSPEND = "vendor.suspend"
    VENDOR_REJECT  = "vendor_application.reject"
    # Experience
    EXPERIENCE_CREATE  = "experience.create"
    EXPERIENCE_UPDATE  = "experience.update"
    EXPERIENCE_DELETE  = "experience.delete"
    SLOT_CREATE        = "slot.create"
    SLOT_UPDATE        = "slot.update"
    SLOT_DELETE        = "slot.delete"
    # Product
    PRODUCT_CREATE = "product.create"
    PRODUCT_UPDATE = "product.update"
    PRODUCT_DELETE = "product.delete"
    # Booking
    BOOKING_CREATE  = "booking.create"
    BOOKING_CONFIRM = "booking.confirm"
    BOOKING_CANCEL  = "booking.cancel"
    # Order
    ORDER_CREATE  = "order.create"
    ORDER_CONFIRM = "order.confirm"
    ORDER_SHIP    = "order.ship"
    ORDER_DELIVER = "order.deliver"
    ORDER_CANCEL  = "order.cancel"
    # Promotion
    PROMOTION_CREATE  = "promotion.create"
    PROMOTION_UPDATE  = "promotion.update"
    PROMOTION_DISABLE = "promotion.disable"
    # Review
    REVIEW_CREATE       = "review.create"
    REVIEW_UPDATE       = "review.update"
    REVIEW_APPROVE      = "review.approve"
    REVIEW_REJECT       = "review.reject"
    REVIEW_REPLY        = "review.reply"
    REVIEW_DELETE_REPLY = "review.delete_reply"
    # Payout
    PAYOUT_CREATE  = "payout.create"
    PAYOUT_APPROVE = "payout.approve"

class AuditActorType:
    USER    = "user"
    SYSTEM  = "system"
    WEBHOOK = "webhook"