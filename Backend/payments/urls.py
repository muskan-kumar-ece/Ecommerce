from django.urls import path

from .views import CreateRazorpayOrderView, RazorpayWebhookView, RefundOrderView, VerifyRazorpayPaymentView

urlpatterns = [
    path("create-order/", CreateRazorpayOrderView.as_view(), name="payment-create-order"),
    path("verify/", VerifyRazorpayPaymentView.as_view(), name="payment-verify"),
    path("refund/", RefundOrderView.as_view(), name="payment-refund"),
    path("webhook/", RazorpayWebhookView.as_view(), name="payment-webhook"),
]
