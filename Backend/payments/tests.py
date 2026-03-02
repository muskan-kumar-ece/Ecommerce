import hashlib
import hmac
import json
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from orders.models import Order

from .models import Payment, PaymentWebhookEvent


class MockHTTPResponse:
    def __init__(self, payload):
        self.payload = payload

    def read(self):
        return json.dumps(self.payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


@override_settings(
    RAZORPAY_KEY_ID="rzp_test_key",
    RAZORPAY_KEY_SECRET="rzp_test_secret",
    RAZORPAY_WEBHOOK_SECRET="rzp_webhook_secret",
    RAZORPAY_API_BASE_URL="https://api.razorpay.com/v1",
)
class PaymentAPITests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="payer@example.com",
            password="StrongPass123",
            name="Payer",
        )
        self.order = Order.objects.create(user=self.user, total_amount=Decimal("999.00"))
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    @patch("payments.views.urlopen")
    def test_create_order_with_idempotency(self, mock_urlopen):
        mock_urlopen.return_value = MockHTTPResponse(
            {"id": "order_123", "amount": 99900, "currency": "INR", "status": "created"}
        )

        response = self.client.post(
            "/api/v1/payments/create-order/",
            {"order_id": self.order.id, "idempotency_key": "idem-1"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Payment.objects.count(), 1)

        second = self.client.post(
            "/api/v1/payments/create-order/",
            {"order_id": self.order.id, "idempotency_key": "idem-1"},
            format="json",
        )
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertEqual(Payment.objects.count(), 1)
        self.assertEqual(mock_urlopen.call_count, 1)

    def test_payment_verification_and_duplicate_prevention(self):
        payment = Payment.objects.create(
            order=self.order,
            idempotency_key="idem-2",
            razorpay_order_id="order_ver_1",
            amount=99900,
        )
        signature = hmac.new(
            b"rzp_test_secret",
            msg=b"order_ver_1|pay_1",
            digestmod=hashlib.sha256,
        ).hexdigest()

        response = self.client.post(
            "/api/v1/payments/verify/",
            {
                "razorpay_order_id": "order_ver_1",
                "razorpay_payment_id": "pay_1",
                "razorpay_signature": signature,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payment.refresh_from_db()
        self.order.refresh_from_db()
        self.assertEqual(payment.status, Payment.Status.CAPTURED)
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PAID)

        another_order = Order.objects.create(user=self.user, total_amount=Decimal("100.00"))
        Payment.objects.create(
            order=another_order,
            idempotency_key="idem-3",
            razorpay_order_id="order_ver_2",
            amount=10000,
        )
        duplicate = self.client.post(
            "/api/v1/payments/verify/",
            {
                "razorpay_order_id": "order_ver_2",
                "razorpay_payment_id": "pay_1",
                "razorpay_signature": hmac.new(
                    b"rzp_test_secret",
                    msg=b"order_ver_2|pay_1",
                    digestmod=hashlib.sha256,
                ).hexdigest(),
            },
            format="json",
        )
        self.assertEqual(duplicate.status_code, status.HTTP_409_CONFLICT)

    def test_webhook_idempotency(self):
        payment = Payment.objects.create(
            order=self.order,
            idempotency_key="idem-4",
            razorpay_order_id="order_webhook_1",
            amount=99900,
        )
        payload = {
            "event": "payment.failed",
            "payload": {"payment": {"entity": {"id": "pay_web_1", "order_id": "order_webhook_1"}}},
        }
        body = json.dumps(payload).encode()
        signature = hmac.new(b"rzp_webhook_secret", msg=body, digestmod=hashlib.sha256).hexdigest()

        response = self.client.post(
            "/api/v1/payments/webhook/",
            data=body,
            content_type="application/json",
            HTTP_X_RAZORPAY_SIGNATURE=signature,
            HTTP_X_RAZORPAY_EVENT_ID="evt_1",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(PaymentWebhookEvent.objects.count(), 1)
        payment.refresh_from_db()
        self.order.refresh_from_db()
        self.assertEqual(payment.status, Payment.Status.FAILED)
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.FAILED)

        duplicate = self.client.post(
            "/api/v1/payments/webhook/",
            data=body,
            content_type="application/json",
            HTTP_X_RAZORPAY_SIGNATURE=signature,
            HTTP_X_RAZORPAY_EVENT_ID="evt_1",
        )
        self.assertEqual(duplicate.status_code, status.HTTP_200_OK)
        self.assertEqual(PaymentWebhookEvent.objects.count(), 1)

    def test_webhook_does_not_downgrade_paid_order(self):
        payment = Payment.objects.create(
            order=self.order,
            idempotency_key="idem-5",
            razorpay_order_id="order_webhook_2",
            amount=99900,
        )
        self.order.payment_status = Order.PaymentStatus.PAID
        self.order.save(update_fields=["payment_status", "updated_at"])

        payload = {
            "event": "payment.failed",
            "payload": {"payment": {"entity": {"id": "pay_web_2", "order_id": "order_webhook_2"}}},
        }
        body = json.dumps(payload).encode()
        signature = hmac.new(b"rzp_webhook_secret", msg=body, digestmod=hashlib.sha256).hexdigest()

        response = self.client.post(
            "/api/v1/payments/webhook/",
            data=body,
            content_type="application/json",
            HTTP_X_RAZORPAY_SIGNATURE=signature,
            HTTP_X_RAZORPAY_EVENT_ID="evt_2",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payment.refresh_from_db()
        self.order.refresh_from_db()
        self.assertEqual(payment.status, Payment.Status.CREATED)
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PAID)

    def test_webhook_does_not_change_failed_order_to_paid(self):
        payment = Payment.objects.create(
            order=self.order,
            idempotency_key="idem-6",
            razorpay_order_id="order_webhook_3",
            amount=99900,
            status=Payment.Status.FAILED,
        )
        self.order.payment_status = Order.PaymentStatus.FAILED
        self.order.save(update_fields=["payment_status", "updated_at"])

        payload = {
            "event": "payment.captured",
            "payload": {"payment": {"entity": {"id": "pay_web_3", "order_id": "order_webhook_3"}}},
        }
        body = json.dumps(payload).encode()
        signature = hmac.new(b"rzp_webhook_secret", msg=body, digestmod=hashlib.sha256).hexdigest()

        response = self.client.post(
            "/api/v1/payments/webhook/",
            data=body,
            content_type="application/json",
            HTTP_X_RAZORPAY_SIGNATURE=signature,
            HTTP_X_RAZORPAY_EVENT_ID="evt_3",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payment.refresh_from_db()
        self.order.refresh_from_db()
        self.assertEqual(payment.status, Payment.Status.FAILED)
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.FAILED)
