from django.contrib import admin

from .models import Vendor, VendorOrder, VendorProduct


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ("id", "business_name", "user", "commission_rate", "is_active")
    list_filter = ("is_active",)
    search_fields = ("business_name", "user__email")


@admin.register(VendorProduct)
class VendorProductAdmin(admin.ModelAdmin):
    list_display = ("id", "vendor", "product", "created_at")
    list_filter = ("vendor",)
    search_fields = ("vendor__business_name", "product__name")


@admin.register(VendorOrder)
class VendorOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "vendor", "order", "total_amount", "commission_amount", "earnings_amount")
    list_filter = ("vendor",)
