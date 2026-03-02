from datetime import timedelta
from decimal import Decimal

from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from orders.admin import OrderAdmin, mark_orders_confirmed
from orders.models import Order
from products.models import Category, Inventory, Product


class AdminDashboardTests(TestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_superuser(
            email="admin@example.com",
            password="SecurePass123!",
            name="Admin",
        )
        self.client.force_login(self.admin_user)

    def test_dashboard_metrics_with_date_range(self):
        inside_order = Order.objects.create(
            user=self.admin_user,
            total_amount=Decimal("100.00"),
            payment_status=Order.PaymentStatus.PAID,
        )
        outside_order = Order.objects.create(
            user=self.admin_user,
            total_amount=Decimal("200.00"),
            payment_status=Order.PaymentStatus.PAID,
        )
        Order.objects.filter(id=inside_order.id).update(created_at=timezone.now() - timedelta(days=1))
        Order.objects.filter(id=outside_order.id).update(created_at=timezone.now() - timedelta(days=45))

        category = Category.objects.create(name="Laptops")
        product = Product.objects.create(
            category=category,
            name="Notebook",
            description="thin",
            price=Decimal("999.00"),
            sku="NB-1",
            stock_quantity=2,
            is_refurbished=False,
            condition_grade="A",
        )
        Inventory.objects.create(product=product, quantity=2, reserved_quantity=1, reorder_level=2)

        today = timezone.localdate()
        start = (today - timedelta(days=7)).isoformat()
        end = today.isoformat()
        response = self.client.get(f"/admin/?start_date={start}&end_date={end}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["dashboard_total_orders"], 1)
        self.assertEqual(response.context["dashboard_revenue"], Decimal("100"))
        self.assertEqual(response.context["dashboard_low_stock_count"], 1)


class OrderAdminActionTests(TestCase):
    def test_mark_orders_confirmed_action(self):
        user = get_user_model().objects.create_user(
            email="buyer@example.com",
            password="SecurePass123!",
            name="Buyer",
        )
        order = Order.objects.create(user=user, total_amount=Decimal("550.00"), status=Order.Status.PENDING)

        admin_instance = OrderAdmin(Order, AdminSite())
        queryset = Order.objects.filter(id=order.id)
        mark_orders_confirmed(admin_instance, None, queryset)

        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.CONFIRMED)


class AnalyticsSummaryAPITests(TestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_superuser(
            email="founder@example.com",
            password="SecurePass123!",
            name="Founder",
        )
        self.regular_user = get_user_model().objects.create_user(
            email="user@example.com",
            password="SecurePass123!",
            name="User",
        )
        self.client = APIClient()

    def test_admin_can_view_analytics_summary(self):
        paid_order = Order.objects.create(
            user=self.regular_user,
            total_amount=Decimal("100.00"),
            payment_status=Order.PaymentStatus.PAID,
        )
        today_refunded = Order.objects.create(
            user=self.regular_user,
            total_amount=Decimal("50.00"),
            payment_status=Order.PaymentStatus.REFUNDED,
        )
        old_paid_order = Order.objects.create(
            user=self.regular_user,
            total_amount=Decimal("200.00"),
            payment_status=Order.PaymentStatus.PAID,
        )
        Order.objects.filter(id=paid_order.id).update(created_at=timezone.now())
        Order.objects.filter(id=today_refunded.id).update(created_at=timezone.now())
        Order.objects.filter(id=old_paid_order.id).update(created_at=timezone.now() - timedelta(days=10))

        self.client.force_authenticate(self.admin_user)
        response = self.client.get("/admin/analytics/summary/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_revenue"], "300.00")
        self.assertEqual(response.data["total_orders"], 3)
        self.assertEqual(response.data["total_paid_orders"], 2)
        self.assertEqual(response.data["total_refunded_orders"], 1)
        self.assertEqual(response.data["refund_rate_percent"], 33.33)
        self.assertEqual(response.data["today_revenue"], "100.00")
        self.assertEqual(response.data["today_orders"], 2)
        self.assertEqual(response.data["last_7_days_revenue"], "100.00")

    def test_non_admin_cannot_view_analytics_summary(self):
        self.client.force_authenticate(self.regular_user)
        response = self.client.get("/admin/analytics/summary/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
