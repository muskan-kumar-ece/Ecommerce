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
        category = Category.objects.create(name="Mobiles")
        Product.objects.create(
            category=category,
            name="Active Phone",
            description="in stock",
            price=Decimal("12000.00"),
            sku="MBL-001",
            stock_quantity=5,
            is_refurbished=False,
            condition_grade="A",
            is_active=True,
        )
        Product.objects.create(
            category=category,
            name="Inactive Phone",
            description="hidden",
            price=Decimal("8000.00"),
            sku="MBL-002",
            stock_quantity=0,
            is_refurbished=False,
            condition_grade="B",
            is_active=False,
        )
        client = APIClient()
        response = client.get("/api/v1/products/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Active Phone")
