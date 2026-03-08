from decimal import Decimal
from datetime import timedelta
import hashlib
import time
from urllib.parse import urlencode

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.throttling import SimpleRateThrottle

from orders.models import Order, OrderItem
from .models import Category, FlashSale, Product


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
        cache.clear()
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
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["name"], "Active Phone")


class ProductSearchFilterPaginationTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.electronics = Category.objects.create(name="Electronics")
        self.appliances = Category.objects.create(name="Appliances")

        self.laptop = Product.objects.create(
            category=self.electronics,
            name="Gaming Laptop",
            description="High performance laptop",
            price=Decimal("4500.00"),
            sku="LAP-4500",
            stock_quantity=5,
            is_refurbished=False,
            condition_grade="A",
            is_active=True,
        )
        self.phone = Product.objects.create(
            category=self.electronics,
            name="Smartphone",
            description="Affordable device",
            price=Decimal("2500.00"),
            sku="PHN-2500",
            stock_quantity=0,
            is_refurbished=False,
            condition_grade="A",
            is_active=True,
        )
        self.fridge = Product.objects.create(
            category=self.appliances,
            name="Mini Fridge",
            description="Compact refrigerator",
            price=Decimal("5000.00"),
            sku="FRG-5000",
            stock_quantity=3,
            is_refurbished=False,
            condition_grade="A",
            is_active=True,
        )

    def test_search_filter_on_name_description_and_sku(self):
        by_name = self.client.get("/api/v1/products/?search=laptop")
        self.assertEqual(by_name.status_code, status.HTTP_200_OK)
        self.assertEqual(by_name.data["count"], 1)
        self.assertEqual(by_name.data["results"][0]["id"], self.laptop.id)

        by_sku = self.client.get("/api/v1/products/?search=FRG-5000")
        self.assertEqual(by_sku.status_code, status.HTTP_200_OK)
        self.assertEqual(by_sku.data["count"], 1)
        self.assertEqual(by_sku.data["results"][0]["id"], self.fridge.id)

    def test_category_and_price_filters(self):
        category_response = self.client.get("/api/v1/products/?category=electronics")
        self.assertEqual(category_response.status_code, status.HTTP_200_OK)
        self.assertEqual(category_response.data["count"], 2)

        min_price_response = self.client.get("/api/v1/products/?min_price=3000")
        self.assertEqual(min_price_response.status_code, status.HTTP_200_OK)
        self.assertEqual(min_price_response.data["count"], 2)

        max_price_response = self.client.get("/api/v1/products/?max_price=3000")
        self.assertEqual(max_price_response.status_code, status.HTTP_200_OK)
        self.assertEqual(max_price_response.data["count"], 1)
        self.assertEqual(max_price_response.data["results"][0]["id"], self.phone.id)

    def test_in_stock_and_ordering_filters(self):
        in_stock_response = self.client.get("/api/v1/products/?in_stock=true")
        self.assertEqual(in_stock_response.status_code, status.HTTP_200_OK)
        self.assertEqual(in_stock_response.data["count"], 2)

        ordering_response = self.client.get("/api/v1/products/?ordering=price")
        self.assertEqual(ordering_response.status_code, status.HTTP_200_OK)
        prices = [Decimal(item["price"]) for item in ordering_response.data["results"]]
        self.assertEqual(prices, sorted(prices))

    def test_products_list_is_paginated(self):
        for index in range(21):
            Product.objects.create(
                category=self.electronics,
                name=f"Extra Product {index}",
                description="Extra item",
                price=Decimal("1000.00"),
                sku=f"EXTRA-{index}",
                stock_quantity=1,
                is_refurbished=False,
                condition_grade="A",
                is_active=True,
            )

        response = self.client.get("/api/v1/products/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 24)
        self.assertEqual(len(response.data["results"]), 20)
        self.assertIn("next", response.data)
        self.assertIn("previous", response.data)


class AdvancedProductSearchAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.electronics = Category.objects.create(name="Electronics")
        self.appliances = Category.objects.create(name="Appliances")

        self.laptop = Product.objects.create(
            category=self.electronics,
            name="Gaming Laptop",
            description="High performance laptop",
            price=Decimal("4500.00"),
            sku="LAP-4500",
            stock_quantity=5,
            is_refurbished=False,
            condition_grade="A",
            is_active=True,
        )
        self.phone = Product.objects.create(
            category=self.electronics,
            name="Smartphone",
            description="Affordable device",
            price=Decimal("2500.00"),
            sku="PHN-2500",
            stock_quantity=7,
            is_refurbished=False,
            condition_grade="A",
            is_active=True,
        )
        self.fridge = Product.objects.create(
            category=self.appliances,
            name="Mini Fridge",
            description="Compact refrigerator",
            price=Decimal("5000.00"),
            sku="FRG-5000",
            stock_quantity=3,
            is_refurbished=False,
            condition_grade="A",
            is_active=True,
        )

    def test_search_by_product_name_returns_ranked_results(self):
        response = self.client.get("/api/v1/search?q=laptop")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], self.laptop.id)
        self.assertIn("relevance_score", response.data["results"][0])

    def test_search_by_category(self):
        response = self.client.get("/api/v1/search?q=electronics")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result_ids = {item["id"] for item in response.data["results"]}
        self.assertIn(self.laptop.id, result_ids)
        self.assertIn(self.phone.id, result_ids)

    def test_search_supports_typo_tolerance(self):
        response = self.client.get("/api/v1/search?q=laptpo")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result_ids = {item["id"] for item in response.data["results"]}
        self.assertIn(self.laptop.id, result_ids)

    def test_search_suggestions(self):
        response = self.client.get("/api/v1/search/suggestions?q=lap")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.laptop.id)


class ProductReviewAPITests(TestCase):
    def setUp(self):
        cache.clear()
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

    def test_review_create_endpoint_is_rate_limited(self):
        cache.clear()
        original_rates = SimpleRateThrottle.THROTTLE_RATES.copy()
        SimpleRateThrottle.THROTTLE_RATES["reviews"] = "2/minute"
        try:
            product_two = Product.objects.create(
                category=self.category,
                name="Study Tablet Plus",
                description="for notes plus",
                price=Decimal("22000.00"),
                sku="TAB-002",
                stock_quantity=4,
                is_refurbished=False,
                condition_grade="A",
                is_active=True,
            )
            product_three = Product.objects.create(
                category=self.category,
                name="Study Tablet Pro",
                description="for notes pro",
                price=Decimal("24000.00"),
                sku="TAB-003",
                stock_quantity=3,
                is_refurbished=False,
                condition_grade="A",
                is_active=True,
            )
            for product in (self.product, product_two, product_three):
                order = Order.objects.create(
                    user=self.user,
                    total_amount=product.price,
                    status=Order.Status.CONFIRMED,
                    payment_status=Order.PaymentStatus.PAID,
                )
                OrderItem.objects.create(order=order, product=product, quantity=1, price=product.price)
            self.client.force_authenticate(user=self.user)
            self.assertEqual(
                self.client.post(
                    "/api/v1/reviews/",
                    {"product": self.product.id, "rating": 5, "title": "Excellent", "comment": "Loved it"},
                    format="json",
                ).status_code,
                status.HTTP_201_CREATED,
            )
            self.assertEqual(
                self.client.post(
                    "/api/v1/reviews/",
                    {"product": product_two.id, "rating": 4, "title": "Update", "comment": "Second review"},
                    format="json",
                ).status_code,
                status.HTTP_201_CREATED,
            )
            self.assertEqual(
                self.client.post(
                    "/api/v1/reviews/",
                    {"product": product_three.id, "rating": 3, "title": "Again", "comment": "Another"},
                    format="json",
                ).status_code,
                status.HTTP_429_TOO_MANY_REQUESTS,
            )
        finally:
            SimpleRateThrottle.THROTTLE_RATES = original_rates
            cache.clear()

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
        self.assertEqual(response.data["results"][0]["reviews_count"], 2)
        self.assertEqual(response.data["results"][0]["average_rating"], 4.0)


class FlashSaleAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category = Category.objects.create(name="Flash Sale Category")
        self.product = Product.objects.create(
            category=self.category,
            name="Flash Sale Product",
            description="Discounted product",
            price=Decimal("1000.00"),
            sku="FLASH-001",
            stock_quantity=25,
            is_refurbished=False,
            condition_grade="A",
            is_active=True,
        )

    def test_flash_sale_list_and_detail_include_countdown_and_discounted_price(self):
        now = timezone.now()
        sale = FlashSale.objects.create(
            product=self.product,
            discount_percentage=25,
            start_time=now - timedelta(minutes=5),
            end_time=now + timedelta(hours=1),
            stock_limit=10,
            sold_quantity=3,
        )

        list_response = self.client.get("/api/v1/flash-sales/")
        detail_response = self.client.get(f"/api/v1/flash-sales/{sale.id}/")

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data), 1)
        self.assertEqual(Decimal(list_response.data[0]["discounted_price"]), Decimal("750.00"))
        self.assertEqual(list_response.data[0]["remaining_stock"], 7)
        self.assertTrue(list_response.data[0]["is_active"])
        self.assertGreater(list_response.data[0]["countdown_seconds"], 0)
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.data["id"], sale.id)

    def test_flash_sale_not_active_when_stock_limit_exhausted(self):
        now = timezone.now()
        sale = FlashSale.objects.create(
            product=self.product,
            discount_percentage=10,
            start_time=now - timedelta(minutes=10),
            end_time=now + timedelta(minutes=10),
            stock_limit=5,
            sold_quantity=5,
        )

        response = self.client.get(f"/api/v1/flash-sales/{sale.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["is_active"])
        self.assertEqual(response.data["remaining_stock"], 0)
        self.assertEqual(response.data["countdown_seconds"], 0)


class ProductCachingTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.category = Category.objects.create(name="Caching Category")
        self.product = Product.objects.create(
            category=self.category,
            name="Cached Product",
            description="Cache me",
            price=Decimal("1200.00"),
            sku="CACHE-001",
            stock_quantity=5,
            is_refurbished=False,
            condition_grade="A",
            is_active=True,
        )
        self.admin_user = get_user_model().objects.create_superuser(
            email="cache-admin@example.com",
            password="StrongPass123",
            name="Cache Admin",
        )

    def _product_list_cache_key(self, path, params=None):
        params = params or {}
        query_param_lists = [(key, [value] if not isinstance(value, list) else value) for key, value in params.items()]
        sorted_query_params = urlencode(sorted(query_param_lists), doseq=True)
        page_number = params.get("page", "1")
        key_source = f"{path}|{sorted_query_params}|page={page_number}"
        key_hash = hashlib.sha256(key_source.encode("utf-8")).hexdigest()
        return f"product_list:{key_hash}"

    def test_product_list_cache_hit_returns_identical_response(self):
        cached_payload = {"count": 1, "next": None, "previous": None, "results": [{"id": self.product.id, "name": "Cached Product"}]}
        cache_key = self._product_list_cache_key("/api/v1/products/")
        cache.set(cache_key, cached_payload, timeout=300)
        response = self.client.get("/api/v1/products/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, cached_payload)

    def test_product_list_cache_miss_populates_cache_with_ttl(self):
        cache_key = self._product_list_cache_key("/api/v1/products/", {"category": "caching-category", "page": "1"})
        cache.delete(cache_key)
        response = self.client.get("/api/v1/products/?category=caching-category&page=1")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(cache.get(cache_key))
        if hasattr(cache, "_expire_info"):
            remaining_ttl = cache._expire_info[cache.make_key(cache_key)] - time.time()
            self.assertGreater(remaining_ttl, 0)
            self.assertLessEqual(remaining_ttl, 300)

    def test_product_detail_cache_miss_populates_cache_with_ttl(self):
        cache_key = f"product_detail:{self.product.id}"
        cache.delete(cache_key)
        response = self.client.get(f"/api/v1/products/{self.product.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(cache.get(cache_key))
        if hasattr(cache, "_expire_info"):
            remaining_ttl = cache._expire_info[cache.make_key(cache_key)] - time.time()
            self.assertGreater(remaining_ttl, 0)
            self.assertLessEqual(remaining_ttl, 600)

    def test_product_mutation_endpoint_bypasses_cache(self):
        self.client.force_authenticate(user=self.admin_user)
        list_cache_key = self._product_list_cache_key("/api/v1/products/")
        cache.delete(list_cache_key)

        response = self.client.post(
            "/api/v1/products/",
            {
                "category": self.category.id,
                "name": "Created Without Cache",
                "slug": "created-without-cache",
                "description": "New",
                "price": "1300.00",
                "sku": "CACHE-POST-001",
                "stock_quantity": 3,
                "is_refurbished": False,
                "condition_grade": "A",
                "is_active": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(cache.get(list_cache_key))
        self.assertIsNone(cache.get(f"product_detail:{response.data['id']}"))
