from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from products.models import Category, Product

from .models import PriceWatch
from .services import check_price_drops


class PriceWatchAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="pricewatch-user@example.com",
            password="StrongPass123",
            name="Price Watch User",
        )
        category = Category.objects.create(name="Price Watch Category")
        self.product = Product.objects.create(
            category=category,
            name="Smart Watch",
            description="Fitness smart watch",
            price=Decimal("1999.00"),
            sku="PW-SMART-001",
            stock_quantity=10,
            is_refurbished=False,
            condition_grade="A",
            is_active=True,
        )

    def test_price_watch_requires_authentication(self):
        response = self.client.post("/api/v1/price-watch/", {"product": self.product.id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_can_add_product_to_price_watch(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post("/api/v1/price-watch/", {"product": self.product.id}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(PriceWatch.objects.filter(user=self.user, product=self.product).exists())
        self.assertEqual(response.data["last_price"], "1999.00")


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class PriceDropServiceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="drop-user@example.com",
            password="StrongPass123",
            name="Drop User",
        )
        category = Category.objects.create(name="Price Drop Category")
        self.product = Product.objects.create(
            category=category,
            name="Gaming Keyboard",
            description="Mechanical keyboard",
            price=Decimal("5000.00"),
            sku="PW-KEY-001",
            stock_quantity=8,
            is_refurbished=False,
            condition_grade="A",
            is_active=True,
        )
        self.watch = PriceWatch.objects.create(
            user=self.user,
            product=self.product,
            last_price=Decimal("5000.00"),
        )

    def test_check_price_drops_sends_email_and_updates_watch(self):
        self.product.price = Decimal("4500.00")
        self.product.save(update_fields=["price", "updated_at"])

        result = check_price_drops()
        self.watch.refresh_from_db()

        self.assertEqual(result["checked_count"], 1)
        self.assertEqual(result["notified_count"], 1)
        self.assertEqual(self.watch.last_price, Decimal("4500.00"))
        self.assertIsNotNone(self.watch.last_notified_at)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Gaming Keyboard", mail.outbox[0].body)

    def test_check_price_drops_does_not_notify_on_price_increase(self):
        self.product.price = Decimal("5500.00")
        self.product.save(update_fields=["price", "updated_at"])

        result = check_price_drops()
        self.watch.refresh_from_db()

        self.assertEqual(result["notified_count"], 0)
        self.assertEqual(self.watch.last_price, Decimal("5500.00"))
        self.assertEqual(len(mail.outbox), 0)
