from django.urls import path

from .views import CreateRazorpayOrderView, RazorpayWebhookView, RefundOrderView, RetryPaymentView, VerifyRazorpayPaymentView

urlpatterns = [
    path("create-order/", CreateRazorpayOrderView.as_view(), name="payment-create-order"),
    path("retry/<int:order_id>/", RetryPaymentView.as_view(), name="payment-retry"),
    path("verify/", VerifyRazorpayPaymentView.as_view(), name="payment-verify"),
    path("refund/", RefundOrderView.as_view(), name="payment-refund"),
    path("webhook/", RazorpayWebhookView.as_view(), name="payment-webhook"),
]
