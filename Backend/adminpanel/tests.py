from datetime import timedelta
from decimal import Decimal

from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

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
