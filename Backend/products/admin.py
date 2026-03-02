from django.contrib import admin
from django.db.models import F
from django.db.models.functions import Coalesce
from django.utils.html import format_html

from .models import Category, Inventory, Product, ProductImage


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "updated_at")
    list_filter = ("is_active", "updated_at")
    search_fields = ("name", "slug")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "sku", "category", "price", "stock_quantity", "inventory_alert", "is_active", "updated_at")
    list_filter = ("is_active", "is_refurbished", "category", "created_at")
    search_fields = ("name", "sku", "description")
    list_select_related = ("category",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("category", "inventory")

    @admin.display(description="Inventory Alert")
    def inventory_alert(self, obj):
        inventory = getattr(obj, "inventory", None)
        if not inventory:
            return format_html('<span style="color:#d97706;font-weight:600;">No inventory</span>')
        available = max(inventory.quantity - inventory.reserved_quantity, 0)
        if available <= inventory.reorder_level:
            return format_html('<span style="color:#dc2626;font-weight:700;">Low ({})</span>', available)
        return format_html('<span style="color:#16a34a;font-weight:600;">Healthy ({})</span>', available)


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("product", "is_primary", "sort_order", "updated_at")
    list_filter = ("is_primary", "updated_at")
    search_fields = ("product__name", "product__sku", "alt_text")
    list_select_related = ("product",)


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ("product", "quantity", "reserved_quantity", "reorder_level", "available_stock", "stock_alert")
    list_filter = ("updated_at",)
    search_fields = ("product__name", "product__sku")
    list_select_related = ("product",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("product").annotate(
            available=Coalesce(F("quantity") - F("reserved_quantity"), 0)
        )

    @admin.display(ordering="available", description="Available")
    def available_stock(self, obj):
        return max(obj.available, 0)

    @admin.display(description="Alert")
    def stock_alert(self, obj):
        available = max(obj.available, 0)
        if available <= obj.reorder_level:
            return format_html('<span style="color:#dc2626;font-weight:700;">Reorder</span>')
        return format_html('<span style="color:#16a34a;font-weight:600;">OK</span>')
