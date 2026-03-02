from django.contrib import admin
from django.db.models import Prefetch

from .models import Cart, CartItem, Coupon, CouponUsage, Order, OrderItem, ShippingAddress


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "is_active", "updated_at")
    list_filter = ("is_active", "updated_at")
    search_fields = ("user__email", "user__name")
    list_select_related = ("user",)


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("id", "cart", "product", "quantity", "updated_at")
    list_filter = ("updated_at",)
    search_fields = ("cart__user__email", "product__name", "product__sku")
    list_select_related = ("cart", "product")


@admin.action(description="Mark selected orders as confirmed")
def mark_orders_confirmed(modeladmin, request, queryset):
    queryset.update(status=Order.Status.CONFIRMED)


@admin.action(description="Mark selected orders as shipped")
def mark_orders_shipped(modeladmin, request, queryset):
    queryset.update(status=Order.Status.SHIPPED)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "total_amount", "status", "payment_status", "created_at")
    list_filter = ("status", "payment_status", "created_at")
    search_fields = ("user__email", "tracking_id")
    date_hierarchy = "created_at"
    list_select_related = ("user",)
    actions = (mark_orders_confirmed, mark_orders_shipped)

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("user")
            .prefetch_related(Prefetch("payments"))
        )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "product", "quantity", "price")
    list_filter = ("created_at",)
    search_fields = ("order__id", "product__name", "product__sku")
    list_select_related = ("order", "product")


@admin.register(ShippingAddress)
class ShippingAddressAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "full_name", "city", "state", "country")
    list_filter = ("country", "state", "city", "created_at")
    search_fields = ("full_name", "phone_number", "order__user__email")
    list_select_related = ("order", "order__user")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("order", "order__user")


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "discount_type",
        "discount_value",
        "minimum_order_amount",
        "max_uses",
        "used_count",
        "per_user_limit",
        "valid_from",
        "valid_until",
        "is_active",
    )
    list_filter = ("discount_type", "is_active", "valid_from", "valid_until")
    search_fields = ("code",)
    readonly_fields = ("used_count", "created_at", "updated_at")


@admin.register(CouponUsage)
class CouponUsageAdmin(admin.ModelAdmin):
    list_display = ("id", "coupon", "user", "order", "discount_amount", "created_at")
    list_filter = ("coupon", "created_at")
    search_fields = ("coupon__code", "user__email", "order__id")
    list_select_related = ("coupon", "user", "order")
    readonly_fields = ("coupon", "user", "order", "discount_amount", "created_at")
