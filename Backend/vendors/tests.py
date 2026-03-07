from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from orders.models import Order
from products.models import Category

from .models import Vendor, VendorOrder, VendorProduct


class VendorDashboardAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.vendor_user = get_user_model().objects.create_user(
            email="vendor@example.com",
            password="StrongPass123",
            name="Vendor User",
        )
        self.customer_user = get_user_model().objects.create_user(
            email="buyer@example.com",
            password="StrongPass123",
            name="Buyer User",
        )
        self.category = Category.objects.create(name="Vendor Electronics")

    def test_vendor_dashboard_endpoints_require_authentication(self):
        response = self.client.get("/api/v1/vendors/dashboard/products/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_vendor_can_create_profile_and_upload_product(self):
        self.client.force_authenticate(user=self.vendor_user)

        profile_response = self.client.post(
            "/api/v1/vendors/profile/",
            {"business_name": "Acme Electronics", "commission_rate": "12.50"},
            format="json",
        )
        self.assertEqual(profile_response.status_code, status.HTTP_201_CREATED)
        self.vendor_user.refresh_from_db()
        self.assertEqual(self.vendor_user.role, self.vendor_user.Role.VENDOR)

        upload_response = self.client.post(
            "/api/v1/vendors/dashboard/products/",
            {
                "category": self.category.id,
                "name": "Acme Speaker",
                "description": "Portable speaker",
                "price": "2499.00",
                "sku": "ACME-SPK-001",
                "stock_quantity": 15,
                "is_refurbished": False,
                "condition_grade": "A",
                "is_active": True,
            },
            format="json",
        )

        self.assertEqual(upload_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(upload_response.data["name"], "Acme Speaker")
        self.assertTrue(
            VendorProduct.objects.filter(
                vendor__user=self.vendor_user,
                product_id=upload_response.data["id"],
            ).exists()
        )

    def test_vendor_can_view_orders_and_earnings(self):
        vendor = Vendor.objects.create(user=self.vendor_user, business_name="Acme Electronics", commission_rate=Decimal("10.00"))
        self.client.force_authenticate(user=self.vendor_user)
        product_response = self.client.post(
            "/api/v1/vendors/dashboard/products/",
            {
                "category": self.category.id,
                "name": "Acme Keyboard",
                "description": "Mechanical keyboard",
                "price": "5000.00",
                "sku": "ACME-KEY-001",
                "stock_quantity": 10,
                "is_refurbished": False,
                "condition_grade": "A",
                "is_active": True,
            },
            format="json",
        )
        self.assertEqual(product_response.status_code, status.HTTP_201_CREATED)
        product_id = product_response.data["id"]
        self.assertTrue(VendorProduct.objects.filter(vendor=vendor, product_id=product_id).exists())

        self.client.force_authenticate(user=self.customer_user)
        create_order_response = self.client.post(
            "/api/v1/orders/create/",
            {"items": [{"product_id": product_id, "quantity": 2}]},
            format="json",
        )
        self.assertEqual(create_order_response.status_code, status.HTTP_201_CREATED)
        order = Order.objects.get(id=create_order_response.data["id"])
        order.payment_status = Order.PaymentStatus.PAID
        order.save(update_fields=["payment_status"])

        self.client.force_authenticate(user=self.vendor_user)
        orders_response = self.client.get("/api/v1/vendors/dashboard/orders/")
        self.assertEqual(orders_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(orders_response.data), 1)
        self.assertEqual(orders_response.data[0]["order_id"], order.id)
        self.assertTrue(VendorOrder.objects.filter(vendor=vendor, order=order).exists())

        earnings_response = self.client.get("/api/v1/vendors/dashboard/earnings/")
        self.assertEqual(earnings_response.status_code, status.HTTP_200_OK)
        self.assertEqual(earnings_response.data["total_orders"], 1)
        self.assertEqual(earnings_response.data["gross_sales"], "10000.00")
        self.assertEqual(earnings_response.data["total_commission"], "1000.00")
        self.assertEqual(earnings_response.data["total_earnings"], "9000.00")
