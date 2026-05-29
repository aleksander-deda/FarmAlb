from sqladmin import Admin
from .views import *

def setup_admin(app, engine, auth_backend=None):
    admin = Admin(app, engine, authentication_backend=auth_backend)
    
    for view in [
        UserAdmin, RoleAdmin, PermissionAdmin, RolePermissionAdmin, UserRoleAdmin,
        VendorAdmin, VendorMediaAdmin, ExperienceAdmin, ExperienceSlotAdmin, ProductAdmin, PromotionAdmin,
        BookingAdmin, OrderAdmin, OrderItemAdmin, PaymentAdmin, RefundAdmin, PayoutAdmin, ReviewAdmin,
        AuditLogAdmin, NotificationAdmin, VendorApplicationAdmin, PlatformSettingAdmin, FeatureFlagAdmin,
        SupportTicketAdmin, SupportMessageAdmin,
    ]:
        admin.add_view(view)

    return admin
