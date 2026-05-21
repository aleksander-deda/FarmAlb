from sqladmin import ModelView
from ..models.catalog import Vendor, VendorMedia, Experience, ExperienceSlot, Product, Promotion

class VendorAdmin(ModelView, model=Vendor):
    name = "Vendor"
    name_plural = "Vendors"
    icon = "fa-solid fa-store"
    category = "Partners"
    
    # column_list = [Vendor.id, Vendor.name, Vendor.type, Vendor.status, Vendor.tier, Vendor.region]
    column_list = [
        Vendor.id, 
        Vendor.name, 
         # Try passing the string name instead of the object
        Vendor.status, 
        Vendor.tier
    ]
    column_searchable_list = [Vendor.name, Vendor.slug, Vendor.email]
    column_filters = [
          ]
    column_details_exclude_list = [Vendor.owner_id]
    
    form_widget_args = {"description": {"rows": 5}}

class VendorMediaAdmin(ModelView, model=VendorMedia):
    name = "Media"
    name_plural = "Vendor Media"
    icon = "fa-solid fa-image"
    category = "Partners"
    
    column_list = [VendorMedia.vendor, VendorMedia.type, VendorMedia.sort_order]
    column_filters = []

class ExperienceAdmin(ModelView, model=Experience):
    name = "Experience"
    name_plural = "Experiences"
    icon = "fa-solid fa-ticket"
    category = "Booking System"
    
    column_list = [Experience.title, Experience.vendor, Experience.type, Experience.base_price, Experience.status]
    column_searchable_list = [Experience.title]
    column_filters = []

class ExperienceSlotAdmin(ModelView, model=ExperienceSlot):
    name = "Slot"
    name_plural = "Experience Slots"
    icon = "fa-solid fa-calendar-day"
    category = "Booking System"
    
    column_list = [ExperienceSlot.experience, ExperienceSlot.starts_at, ExperienceSlot.available_spots, ExperienceSlot.status]
    column_filters = []

class ProductAdmin(ModelView, model=Product):
    name = "Product"
    name_plural = "Products"
    icon = "fa-solid fa-cart-shopping"
    category = "Shop"
    
    column_list = [Product.name, Product.vendor, Product.category, Product.price, Product.stock_qty, Product.status]
    column_searchable_list = [Product.name]
    column_filters = []

class PromotionAdmin(ModelView, model=Promotion):
    name = "Promotion"
    name_plural = "Promotions"
    icon = "fa-solid fa-tag"
    category = "Marketing"
    
    column_list = [Promotion.code, Promotion.vendor, Promotion.type, Promotion.value, Promotion.status]
    column_searchable_list = [Promotion.code]
    column_filters = []
