from decimal import Decimal

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from .models import Category, Product


class ProductModelTests(TestCase):
    def test_product_slug_auto_generates(self):
        category = Category.objects.create(name="Laptops")
        product = Product.objects.create(
            category=category,
            name="Dell Inspiron 15",
            description="Student laptop",
            price=Decimal("50000.00"),
            sku="DL-INSP-15",
            stock_quantity=10,
            is_refurbished=False,
            condition_grade="A",
        )

        self.assertEqual(category.slug, "laptops")
        self.assertEqual(product.slug, "dell-inspiron-15")


class ProductAPITests(TestCase):
    def test_products_list_is_public(self):
        client = APIClient()
        response = client.get("/api/v1/products/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
