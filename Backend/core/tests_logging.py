"""
Tests for the backend logging infrastructure.

Covers:
  - RequestIDFilter injects request_id into log records
  - JsonFormatter emits valid JSON with required fields
  - JsonFormatter includes exc_info when an exception is attached
  - orders/notifications.py logs SMTP failures at ERROR level
  - apps/price_watch/notifications.py logs SMTP failures at ERROR level
  - payments/services.py logs Razorpay API failures at ERROR level
"""

import json
import logging
from smtplib import SMTPException
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from products.models import Category, Product

from core.log_filters import JsonFormatter, RequestIDFilter, get_request_id, set_request_id


class RequestIDFilterTests(TestCase):
    """RequestIDFilter injects the correct request_id into every log record."""

    def _make_record(self, msg="test"):
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg=msg,
            args=(),
            exc_info=None,
        )
        return record

    def test_filter_adds_request_id_from_thread_local(self):
        set_request_id("abc-123")
        filt = RequestIDFilter()
        record = self._make_record()
        filt.filter(record)
        self.assertEqual(record.request_id, "abc-123")

    def test_filter_defaults_to_dash_when_no_request_in_flight(self):
        # Clear any thread-local value by using a fresh thread simulation
        import threading
        import core.log_filters as _lf
        original = _lf._local.__dict__.copy()
        try:
            _lf._local.__dict__.clear()
            filt = RequestIDFilter()
            record = self._make_record()
            filt.filter(record)
            self.assertEqual(record.request_id, "-")
        finally:
            _lf._local.__dict__.update(original)

    def test_filter_always_returns_true(self):
        filt = RequestIDFilter()
        record = self._make_record()
        self.assertTrue(filt.filter(record))

    def test_set_and_get_request_id_roundtrip(self):
        set_request_id("round-trip-id")
        self.assertEqual(get_request_id(), "round-trip-id")


class JsonFormatterTests(TestCase):
    """JsonFormatter produces valid JSON with the required schema fields."""

    def _make_record(self, msg="hello", level=logging.INFO, exc_info=None):
        record = logging.LogRecord(
            name="myapp.module",
            level=level,
            pathname="",
            lineno=0,
            msg=msg,
            args=(),
            exc_info=exc_info,
        )
        record.request_id = "req-uuid-456"
        return record

    def test_output_is_valid_json(self):
        formatter = JsonFormatter()
        record = self._make_record()
        output = formatter.format(record)
        data = json.loads(output)
        self.assertIsInstance(data, dict)

    def test_required_fields_present(self):
        formatter = JsonFormatter()
        record = self._make_record(msg="something happened", level=logging.WARNING)
        data = json.loads(formatter.format(record))
        for field in ("timestamp", "level", "request_id", "logger", "message"):
            self.assertIn(field, data, f"Missing field: {field}")

    def test_timestamp_is_iso8601_with_utc_offset(self):
        formatter = JsonFormatter()
        record = self._make_record()
        data = json.loads(formatter.format(record))
        # Should be ISO 8601 with UTC offset, e.g. "2026-03-08T06:00:00.123456+00:00"
        self.assertIn("+00:00", data["timestamp"])

    def test_level_name_is_correct(self):
        formatter = JsonFormatter()
        record = self._make_record(level=logging.ERROR)
        data = json.loads(formatter.format(record))
        self.assertEqual(data["level"], "ERROR")

    def test_request_id_propagated(self):
        formatter = JsonFormatter()
        record = self._make_record()
        data = json.loads(formatter.format(record))
        self.assertEqual(data["request_id"], "req-uuid-456")

    def test_message_field_matches_record(self):
        formatter = JsonFormatter()
        record = self._make_record(msg="payment failed")
        data = json.loads(formatter.format(record))
        self.assertEqual(data["message"], "payment failed")

    def test_exc_info_included_when_exception_present(self):
        formatter = JsonFormatter()
        try:
            raise ValueError("something went wrong")
        except ValueError:
            import sys
            exc = sys.exc_info()
        record = self._make_record(exc_info=exc)
        data = json.loads(formatter.format(record))
        self.assertIn("exc_info", data)
        self.assertIn("ValueError", data["exc_info"])

    def test_exc_info_absent_when_no_exception(self):
        formatter = JsonFormatter()
        record = self._make_record()
        data = json.loads(formatter.format(record))
        self.assertNotIn("exc_info", data)


class OrderNotificationsLoggingTests(TestCase):
    """orders/notifications.py logs SMTP failures at ERROR level."""

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            email="buyer@example.com",
            password="pass",
            name="Buyer",
        )
        from products.models import Category, Product
        self.category = Category.objects.create(name="Electronics", slug="electronics")
        self.product = Product.objects.create(
            category=self.category,
            name="Phone",
            slug="phone",
            price="999.00",
            sku="PHONE-001",
            stock_quantity=10,
        )
        from orders.models import Order, OrderItem
        self.order = Order.objects.create(user=self.user, total_amount="999.00")
        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=1,
            price="999.00",
        )

    @patch("orders.notifications.send_mail", side_effect=SMTPException("connection refused"))
    def test_send_order_email_logs_smtp_failure(self, mock_send):
        from orders.notifications import send_order_email
        from orders.models import EmailEvent

        with self.assertLogs("orders.notifications", level="ERROR") as cm:
            result = send_order_email(EmailEvent.EmailType.ORDER_CONFIRMED, self.order)

        self.assertFalse(result)
        # At least one log line should mention the email type and order id
        combined = " ".join(cm.output)
        self.assertIn("order_confirmed", combined)
        self.assertIn(str(self.order.id), combined)

    @patch("orders.notifications.send_mail", side_effect=SMTPException("SMTP error"))
    def test_send_abandoned_cart_email_logs_smtp_failure(self, mock_send):
        from orders.models import Cart
        from orders.notifications import send_abandoned_cart_email

        cart = Cart.objects.create(user=self.user)

        with self.assertLogs("orders.notifications", level="ERROR") as cm:
            result = send_abandoned_cart_email(cart)

        self.assertFalse(result)
        combined = " ".join(cm.output)
        self.assertIn(str(cart.id), combined)


class PriceWatchNotificationsLoggingTests(TestCase):
    """apps/price_watch/notifications.py logs SMTP failures at ERROR level."""

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            email="watcher@example.com",
            password="pass",
            name="Watcher",
        )
        self.category = Category.objects.create(name="Gadgets", slug="gadgets")
        self.product = Product.objects.create(
            category=self.category,
            name="Laptop",
            slug="laptop",
            price="50000.00",
            sku="LAPTOP-001",
            stock_quantity=5,
        )
        from apps.price_watch.models import PriceWatch
        self.price_watch = PriceWatch.objects.create(
            user=self.user,
            product=self.product,
            last_price="50000.00",
        )

    @patch("apps.price_watch.notifications.send_mail", side_effect=SMTPException("SMTP down"))
    def test_send_price_drop_email_logs_smtp_failure(self, mock_send):
        from apps.price_watch.notifications import send_price_drop_email

        with self.assertLogs("apps.price_watch.notifications", level="ERROR") as cm:
            result = send_price_drop_email(self.price_watch, "50000.00", "40000.00")

        self.assertFalse(result)
        combined = " ".join(cm.output)
        self.assertIn(str(self.product.id), combined)
        self.assertIn(str(self.user.id), combined)


class RazorpayServiceLoggingTests(TestCase):
    """payments/services.py logs Razorpay API failures at ERROR level."""

    @override_settings(
        RAZORPAY_KEY_ID="rzp_test_key",
        RAZORPAY_KEY_SECRET="secret",
        RAZORPAY_API_BASE_URL="https://api.razorpay.com/v1",
    )
    @patch("payments.services.urlopen", side_effect=TimeoutError("timed out"))
    def test_create_razorpay_order_logs_on_network_failure(self, mock_urlopen):
        from payments.services import create_razorpay_order, RazorpayIntegrationError

        with self.assertLogs("payments.services", level="ERROR") as cm:
            with self.assertRaises(RazorpayIntegrationError):
                create_razorpay_order(100000, "INR", "receipt-001")

        combined = " ".join(cm.output)
        self.assertIn("receipt-001", combined)
