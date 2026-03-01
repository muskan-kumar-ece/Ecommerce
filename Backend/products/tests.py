from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from .models import Category, Product


class ProductModelTests(TestCase):
    def test_category_slug_is_auto_generated(self):
        category = Category.objects.create(name="Laptops")

        self.assertEqual(category.slug, "laptops")
        self.assertEqual(str(category), "Laptops")


class ProductApiTests(TestCase):
    def test_products_list_is_public(self):
        category = Category.objects.create(name="Accessories", slug="accessories")
        Product.objects.create(
            name="USB Cable",
            description="Fast charging cable",
            category=category,
            price="199.00",
            sku="USB-001",
            stock_quantity=10,
            slug="usb-cable",
        )
        client = APIClient()

        response = client.get(reverse("product-list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
