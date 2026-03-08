import json
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.throttling import SimpleRateThrottle

from orders.models import Order
from products.models import Category, Product


class ChatbotAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="chatbot-user@example.com",
            password="StrongPass123",
            name="Chatbot User",
        )
        self.other_user = get_user_model().objects.create_user(
            email="other-user@example.com",
            password="StrongPass123",
            name="Other User",
        )
        category = Category.objects.create(name="Chatbot Gadgets")
        self.product = Product.objects.create(
            category=category,
            name="Smart Speaker",
            description="Voice assistant speaker",
            price=Decimal("4999.00"),
            sku="SPK-CHAT-1",
            stock_quantity=30,
            is_refurbished=False,
            condition_grade="A",
            is_active=True,
        )
        self.order = Order.objects.create(
            user=self.user,
            total_amount=Decimal("4999.00"),
            status=Order.Status.SHIPPED,
            payment_status=Order.PaymentStatus.PAID,
            tracking_id="TRK123",
        )
        Order.objects.create(
            user=self.other_user,
            total_amount=Decimal("999.00"),
            status=Order.Status.DELIVERED,
            payment_status=Order.PaymentStatus.PAID,
        )

    def test_chatbot_message_requires_authentication(self):
        response = self.client.post("/api/v1/chatbot/message", {"message": "order status"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_order_status_message_returns_order_details(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            "/api/v1/chatbot/message",
            {"message": f"What is my order status for order #{self.order.id}?"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["intent"], "order_status")
        self.assertEqual(response.data["order_details"]["order_id"], self.order.id)
        self.assertIn("order", response.data["response"].lower())
        self.assertIn("shipped", response.data["response"].lower())

    def test_refund_message_detects_refund_intent(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            "/api/v1/chatbot/message",
            {"message": f"I need a refund for order #{self.order.id}"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["intent"], "refund")
        self.assertIn(str(self.order.id), response.data["response"])

    @patch("apps.chatbot.services.get_user_recommendations")
    def test_product_suggestion_message_returns_suggestions(self, mock_recommendations):
        mock_recommendations.return_value = [self.product]
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            "/api/v1/chatbot/message",
            {"message": "Can you suggest products for me?"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["intent"], "product_suggestions")
        self.assertEqual(len(response.data["suggestions"]), 1)
        self.assertEqual(response.data["suggestions"][0]["id"], self.product.id)

    @override_settings(OPENAI_API_KEY="test-key")
    @patch("apps.chatbot.services.request.urlopen")
    def test_openai_response_is_used_when_available(self, mock_urlopen):
        class MockHTTPResponse:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self):
                return json.dumps(
                    {"choices": [{"message": {"content": "AI generated answer about your order."}}]}
                ).encode("utf-8")

        mock_urlopen.return_value = MockHTTPResponse()
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            "/api/v1/chatbot/message",
            {"message": f"Track my order #{self.order.id}"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["intent"], "order_status")
        self.assertEqual(response.data["response"], "AI generated answer about your order.")

    def test_chatbot_endpoint_is_rate_limited(self):
        cache.clear()
        original_rates = SimpleRateThrottle.THROTTLE_RATES.copy()
        SimpleRateThrottle.THROTTLE_RATES["chatbot"] = "2/minute"
        self.client.force_authenticate(user=self.user)
        try:
            self.assertEqual(
                self.client.post("/api/v1/chatbot/message", {"message": "order status"}, format="json").status_code,
                status.HTTP_200_OK,
            )
            self.assertEqual(
                self.client.post("/api/v1/chatbot/message", {"message": "order status"}, format="json").status_code,
                status.HTTP_200_OK,
            )
            self.assertEqual(
                self.client.post("/api/v1/chatbot/message", {"message": "order status"}, format="json").status_code,
                status.HTTP_429_TOO_MANY_REQUESTS,
            )
        finally:
            SimpleRateThrottle.THROTTLE_RATES = original_rates
            cache.clear()
