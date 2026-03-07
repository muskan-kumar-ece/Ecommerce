from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

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
