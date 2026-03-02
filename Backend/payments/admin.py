from django.contrib import admin

from .models import Payment, PaymentWebhookEvent


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "razorpay_order_id",
        "razorpay_payment_id",
        "amount",
        "currency",
        "status",
        "created_at",
    )
    list_filter = ("status", "currency", "created_at", "verified_at")
    search_fields = (
        "order__id",
        "order__user__email",
        "razorpay_order_id",
        "razorpay_payment_id",
        "idempotency_key",
    )
    list_select_related = ("order", "order__user")
    readonly_fields = ("created_at", "updated_at", "verified_at")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("order", "order__user")


@admin.register(PaymentWebhookEvent)
class PaymentWebhookEventAdmin(admin.ModelAdmin):
    list_display = ("event_id", "event_type", "processed_at")
    list_filter = ("event_type", "processed_at")
    search_fields = ("event_id", "event_type")
