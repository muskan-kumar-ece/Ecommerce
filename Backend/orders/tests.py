from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from products.models import Category, Product

from .models import Cart, Order


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

    def test_cart_item_create_rejects_other_users_cart(self):
        user = get_user_model().objects.create_user(
            email="buyer1@example.com",
            password="StrongPass123",
            name="Buyer 1",
        )
        other_user = get_user_model().objects.create_user(
            email="buyer2@example.com",
            password="StrongPass123",
            name="Buyer 2",
        )
        category = Category.objects.create(name="Audio")
        product = Product.objects.create(
            category=category,
            name="Headphones",
            description="Noise cancelling",
            price=Decimal("2499.00"),
            sku="AUD-001",
            stock_quantity=10,
            is_refurbished=False,
            condition_grade="A",
        )
        other_cart = Cart.objects.create(user=other_user)

        client = APIClient()
        client.force_authenticate(user=user)
        response = client.post(
            "/api/v1/orders/cart-items/",
            {"cart": other_cart.id, "product": product.id, "quantity": 1},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
