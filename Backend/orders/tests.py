from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from products.models import Category, Product

from .models import Order


class OrderModelTests(TestCase):
    def test_order_defaults(self):
        user = get_user_model().objects.create_user(
            email="buyer@example.com",
            password="StrongPass123",
            name="Buyer",
        )
        order = Order.objects.create(user=user, total_amount=Decimal("1200.00"))

        self.assertEqual(order.status, Order.Status.PENDING)
        self.assertEqual(order.payment_status, Order.PaymentStatus.PENDING)


class OrderAPITests(TestCase):
    def test_orders_list_requires_authentication(self):
        client = APIClient()
        response = client.get("/api/v1/orders/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_can_create_order(self):
        user = get_user_model().objects.create_user(
            email="student@example.com",
            password="StrongPass123",
            name="Student",
        )
        category = Category.objects.create(name="Accessories")
        Product.objects.create(
            category=category,
            name="Mouse",
            description="Wireless mouse",
            price=Decimal("999.00"),
            sku="MSE-001",
            stock_quantity=20,
            is_refurbished=False,
            condition_grade="A",
        )

        client = APIClient()
        client.force_authenticate(user=user)
        response = client.post("/api/v1/orders/", {"total_amount": "999.00"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
