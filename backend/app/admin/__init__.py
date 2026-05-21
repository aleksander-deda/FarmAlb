from sqladmin import Admin
from .views import *

def setup_admin(app, engine, auth_backend=None):
    admin = Admin(app, engine, authentication_backend=auth_backend)
    
    # Registering views in logical order
    admin.add_view(VendorAdmin)
    admin.add_view(VendorMediaAdmin)
    admin.add_view(ExperienceAdmin)
    admin.add_view(ExperienceSlotAdmin)
    admin.add_view(ProductAdmin)
    admin.add_view(PromotionAdmin)
    
    return admin
