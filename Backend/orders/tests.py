from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient, APIRequestFactory, force_authenticate

from products.models import Category, Product

from .models import Cart, Order
from .views import OrderViewSet


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

    def test_order_create_is_idempotent_for_same_header_key(self):
        user = get_user_model().objects.create_user(
            email="idempotent@example.com",
            password="StrongPass123",
            name="Idempotent",
        )
        factory = APIRequestFactory()
        view = OrderViewSet.as_view({"post": "create"})
        payload = {"total_amount": "499.00"}
        first_request = factory.post(
            "/api/v1/orders/",
            payload,
            format="json",
            headers={"Idempotency-Key": "order-key-1"},
        )
        force_authenticate(first_request, user=user)
        first_response = view(first_request)
        second_request = factory.post(
            "/api/v1/orders/",
            payload,
            format="json",
            headers={"Idempotency-Key": "order-key-1"},
        )
        force_authenticate(second_request, user=user)
        second_response = view(second_request)

        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.get(id=first_response.data["id"]).idempotency_key, "order-key-1")
        self.assertEqual(first_response.data["id"], second_response.data["id"])
        self.assertEqual(Order.objects.filter(user=user, idempotency_key="order-key-1").count(), 1)
