from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from orders.models import Order, OrderItem
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


class ProductReviewAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="buyer@example.com",
            password="StrongPass123",
            name="Buyer",
        )
        self.other_user = get_user_model().objects.create_user(
            email="other@example.com",
            password="StrongPass123",
            name="Other",
        )
        self.admin_user = get_user_model().objects.create_superuser(
            email="admin@example.com",
            password="StrongPass123",
            name="Admin",
        )
        self.category = Category.objects.create(name="Tablets")
        self.product = Product.objects.create(
            category=self.category,
            name="Study Tablet",
            description="for notes",
            price=Decimal("20000.00"),
            sku="TAB-001",
            stock_quantity=5,
            is_refurbished=False,
            condition_grade="A",
            is_active=True,
        )

    def _create_paid_order_for(self, user):
        order = Order.objects.create(
            user=user,
            total_amount=self.product.price,
            status=Order.Status.CONFIRMED,
            payment_status=Order.PaymentStatus.PAID,
        )
        OrderItem.objects.create(order=order, product=self.product, quantity=1, price=self.product.price)
        return order

    def test_review_creation_requires_authentication(self):
        response = self.client.post(
            "/api/v1/reviews/",
            {"product": self.product.id, "rating": 5, "title": "Great", "comment": "Worth it"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_only_verified_buyer_can_review(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            "/api/v1/reviews/",
            {"product": self.product.id, "rating": 4, "title": "Good", "comment": "Nice product"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("verified buyers", str(response.data))

    def test_verified_buyer_can_create_single_review(self):
        self._create_paid_order_for(self.user)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            "/api/v1/reviews/",
            {"product": self.product.id, "rating": 5, "title": "Excellent", "comment": "Loved it"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        duplicate_response = self.client.post(
            "/api/v1/reviews/",
            {"product": self.product.id, "rating": 4, "title": "Update", "comment": "Second review"},
            format="json",
        )
        self.assertEqual(duplicate_response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_product_reviews_endpoint_is_paginated(self):
        self._create_paid_order_for(self.user)
        self._create_paid_order_for(self.other_user)
        self.client.force_authenticate(user=self.user)
        self.client.post(
            "/api/v1/reviews/",
            {"product": self.product.id, "rating": 5, "title": "Excellent", "comment": "Loved it"},
            format="json",
        )
        self.client.force_authenticate(user=self.other_user)
        self.client.post(
            "/api/v1/reviews/",
            {"product": self.product.id, "rating": 3, "title": "Okay", "comment": "Average"},
            format="json",
        )
        self.client.force_authenticate(user=None)
        response = self.client.get(f"/api/v1/products/{self.product.id}/reviews/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertIn("count", response.data)
        self.assertEqual(response.data["count"], 2)

    def test_user_can_edit_own_review_only(self):
        self._create_paid_order_for(self.user)
        self._create_paid_order_for(self.other_user)
        self.client.force_authenticate(user=self.user)
        create_response = self.client.post(
            "/api/v1/reviews/",
            {"product": self.product.id, "rating": 5, "title": "Excellent", "comment": "Loved it"},
            format="json",
        )
        review_id = create_response.data["id"]
        patch_response = self.client.patch(
            f"/api/v1/reviews/{review_id}/",
            {"rating": 4, "title": "Very Good", "comment": "Updated thoughts"},
            format="json",
        )
        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_response.data["rating"], 4)

        self.client.force_authenticate(user=self.other_user)
        forbidden_patch = self.client.patch(
            f"/api/v1/reviews/{review_id}/",
            {"rating": 2},
            format="json",
        )
        self.assertEqual(forbidden_patch.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_can_delete_any_review(self):
        self._create_paid_order_for(self.user)
        self.client.force_authenticate(user=self.user)
        create_response = self.client.post(
            "/api/v1/reviews/",
            {"product": self.product.id, "rating": 5, "title": "Excellent", "comment": "Loved it"},
            format="json",
        )
        review_id = create_response.data["id"]

        self.client.force_authenticate(user=self.admin_user)
        delete_response = self.client.delete(f"/api/v1/reviews/{review_id}/")
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)

    def test_product_list_includes_rating_aggregation(self):
        self._create_paid_order_for(self.user)
        self._create_paid_order_for(self.other_user)
        self.client.force_authenticate(user=self.user)
        self.client.post(
            "/api/v1/reviews/",
            {"product": self.product.id, "rating": 5, "title": "Excellent", "comment": "Loved it"},
            format="json",
        )
        self.client.force_authenticate(user=self.other_user)
        self.client.post(
            "/api/v1/reviews/",
            {"product": self.product.id, "rating": 3, "title": "Okay", "comment": "Average"},
            format="json",
        )

        self.client.force_authenticate(user=None)
        response = self.client.get("/api/v1/products/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["reviews_count"], 2)
        self.assertEqual(response.data[0]["average_rating"], 4.0)
