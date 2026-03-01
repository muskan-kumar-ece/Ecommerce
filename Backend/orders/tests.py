from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from products.models import Category, Product

from .models import Cart, CartItem, Order


class OrdersApiTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.user = self.user_model.objects.create_user(
            email="user@example.com",
            password="secure-pass-123",
            full_name="User",
        )
        self.other_user = self.user_model.objects.create_user(
            email="other@example.com",
            password="secure-pass-123",
            full_name="Other User",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_order_list_is_scoped_to_authenticated_user(self):
        Order.objects.create(user=self.user, total_amount="100.00")
        Order.objects.create(user=self.other_user, total_amount="200.00")

        response = self.client.get(reverse("order-list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_cart_item_rejects_other_user_cart(self):
        category = Category.objects.create(name="Storage", slug="storage")
        product = Product.objects.create(
            name="SSD",
            slug="ssd",
            description="1TB SSD",
            category=category,
            price="4999.00",
            sku="SSD-001",
            stock_quantity=20,
        )
        other_user_cart = Cart.objects.create(user=self.other_user)

        response = self.client.post(
            reverse("cart-item-list"),
            {"cart": str(other_user_cart.id), "product": str(product.id), "quantity": 1},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(CartItem.objects.count(), 0)
