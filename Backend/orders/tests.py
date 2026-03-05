from decimal import Decimal
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.test.utils import override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APIRequestFactory, force_authenticate

from products.models import Category, Product

from .models import Cart, Coupon, CouponUsage, EmailEvent, Order, OrderEvent, OrderItem, ShippingAddress
from .notifications import send_order_email
from .views import OrderViewSet


class OrderModelTests(TestCase):
    def test_order_defaults(self):
        user = get_user_model().objects.create_user(
            email="buyer@example.com",
            password="StrongPass123",
            name="Buyer",
        )
        order = Order.objects.create(user=user, total_amount=Decimal("1200.00"))

        self.assertEqual(order.status, Order.Status.PENDING)
        self.assertEqual(order.payment_status, Order.PaymentStatus.PENDING)


class OrderAPITests(TestCase):
    def test_orders_list_requires_authentication(self):
        client = APIClient()
        response = client.get("/api/v1/orders/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_can_create_order(self):
        user = get_user_model().objects.create_user(
            email="student@example.com",
            password="StrongPass123",
            name="Student",
        )
        category = Category.objects.create(name="Accessories")
        Product.objects.create(
            category=category,
            name="Mouse",
            description="Wireless mouse",
            price=Decimal("999.00"),
            sku="MSE-001",
            stock_quantity=20,
            is_refurbished=False,
            condition_grade="A",
        )

        client = APIClient()
        client.force_authenticate(user=user)
        response = client.post("/api/v1/orders/", {"total_amount": "999.00"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_cart_item_create_rejects_other_users_cart(self):
        user = get_user_model().objects.create_user(
            email="buyer1@example.com",
            password="StrongPass123",
            name="Buyer 1",
        )
        other_user = get_user_model().objects.create_user(
            email="buyer2@example.com",
            password="StrongPass123",
            name="Buyer 2",
        )
        category = Category.objects.create(name="Audio")
        product = Product.objects.create(
            category=category,
            name="Headphones",
            description="Noise cancelling",
            price=Decimal("2499.00"),
            sku="AUD-001",
            stock_quantity=10,
            is_refurbished=False,
            condition_grade="A",
        )
        other_cart = Cart.objects.create(user=other_user)

        client = APIClient()
        client.force_authenticate(user=user)
        response = client.post(
            "/api/v1/orders/cart-items/",
            {"cart": other_cart.id, "product": product.id, "quantity": 1},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_order_create_is_idempotent_for_same_header_key(self):
        user = get_user_model().objects.create_user(
            email="idempotent@example.com",
            password="StrongPass123",
            name="Idempotent",
        )
        factory = APIRequestFactory()
        view = OrderViewSet.as_view({"post": "create"})
        payload = {"total_amount": "499.00"}
        first_request = factory.post(
            "/api/v1/orders/",
            payload,
            format="json",
            headers={"Idempotency-Key": "order-key-1"},
        )
        force_authenticate(first_request, user=user)
        first_response = view(first_request)
        second_request = factory.post(
            "/api/v1/orders/",
            payload,
            format="json",
            headers={"Idempotency-Key": "order-key-1"},
        )
        force_authenticate(second_request, user=user)
        second_response = view(second_request)

        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.get(id=first_response.data["id"]).idempotency_key, "order-key-1")
        self.assertEqual(first_response.data["id"], second_response.data["id"])
        self.assertEqual(Order.objects.filter(user=user, idempotency_key="order-key-1").count(), 1)


class OrderCreateWithItemsAPITests(TestCase):
    """Tests for the new create order with items endpoint."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="orderuser@example.com",
            password="StrongPass123",
            name="Order User",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Create test products
        self.category = Category.objects.create(name="Electronics")
        self.product1 = Product.objects.create(
            category=self.category,
            name="Laptop",
            description="Gaming laptop",
            price=Decimal("50000.00"),
            sku="LAP-001",
            stock_quantity=10,
        )
        self.product2 = Product.objects.create(
            category=self.category,
            name="Mouse",
            description="Wireless mouse",
            price=Decimal("1500.00"),
            sku="MSE-001",
            stock_quantity=20,
        )

    def test_create_order_with_items(self):
        """Test creating an order with multiple items."""
        response = self.client.post(
            "/api/v1/orders/create/",
            {
                "items": [
                    {"product_id": self.product1.id, "quantity": 1},
                    {"product_id": self.product2.id, "quantity": 2},
                ]
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)
        self.assertIn("items", response.data)
        self.assertEqual(len(response.data["items"]), 2)
        expected_total = str(self.product1.price * 1 + self.product2.price * 2)
        self.assertEqual(response.data["total_amount"], expected_total)
        self.assertEqual(response.data["status"], Order.Status.PENDING)
        self.assertEqual(response.data["payment_status"], Order.PaymentStatus.PENDING)

        # Verify order was created in database
        order = Order.objects.get(id=response.data["id"])
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.items.count(), 2)

    def test_create_order_with_single_item(self):
        """Test creating an order with a single item."""
        response = self.client.post(
            "/api/v1/orders/create/",
            {
                "items": [
                    {"product_id": self.product1.id, "quantity": 2},
                ]
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        expected_total = str(self.product1.price * 2)
        self.assertEqual(response.data["total_amount"], expected_total)
        self.assertEqual(len(response.data["items"]), 1)
        self.assertEqual(response.data["items"][0]["quantity"], 2)
        self.assertEqual(response.data["items"][0]["price"], str(self.product1.price))

    def test_create_order_requires_authentication(self):
        """Test that creating an order requires authentication."""
        client = APIClient()
        response = client.post(
            "/api/v1/orders/create/",
            {
                "items": [
                    {"product_id": self.product1.id, "quantity": 1},
                ]
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_order_requires_items(self):
        """Test that items are required to create an order."""
        response = self.client.post(
            "/api/v1/orders/create/",
            {"items": []},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("items", response.data)

    def test_create_order_with_invalid_product(self):
        """Test creating an order with a non-existent product."""
        response = self.client.post(
            "/api/v1/orders/create/",
            {
                "items": [
                    {"product_id": 99999, "quantity": 1},
                ]
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_order_with_inactive_product(self):
        """Test creating an order with an inactive product."""
        self.product1.is_active = False
        self.product1.save()

        response = self.client.post(
            "/api/v1/orders/create/",
            {
                "items": [
                    {"product_id": self.product1.id, "quantity": 1},
                ]
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_my_orders_endpoint(self):
        """Test the my-orders endpoint."""
        # Create some orders
        order1 = Order.objects.create(user=self.user, total_amount=Decimal("1000.00"))
        order2 = Order.objects.create(user=self.user, total_amount=Decimal("2000.00"))
        
        # Create orders for another user
        other_user = get_user_model().objects.create_user(
            email="other@example.com",
            password="StrongPass123",
            name="Other User",
        )
        Order.objects.create(user=other_user, total_amount=Decimal("3000.00"))

        response = self.client.get("/api/v1/orders/my-orders/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        order_ids = [order["id"] for order in response.data]
        self.assertIn(order1.id, order_ids)
        self.assertIn(order2.id, order_ids)

    def test_my_orders_requires_authentication(self):
        """Test that my-orders requires authentication."""
        client = APIClient()
        response = client.get("/api/v1/orders/my-orders/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_order_detail_includes_items(self):
        """Test that order detail endpoint includes items."""
        order = Order.objects.create(user=self.user, total_amount=Decimal("51500.00"))
        OrderItem.objects.create(order=order, product=self.product1, quantity=1, price=self.product1.price)
        OrderItem.objects.create(order=order, product=self.product2, quantity=1, price=self.product2.price)

        response = self.client.get(f"/api/v1/orders/{order.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("items", response.data)
        self.assertEqual(len(response.data["items"]), 2)


class CouponAPITests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="couponuser@example.com",
            password="StrongPass123",
            name="Coupon User",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        now = timezone.now()
        self.coupon = Coupon.objects.create(
            code="SAVE10",
            discount_type=Coupon.DiscountType.PERCENTAGE,
            discount_value=Decimal("10.00"),
            minimum_order_amount=Decimal("500.00"),
            max_uses=2,
            per_user_limit=1,
            valid_from=now - timedelta(days=1),
            valid_until=now + timedelta(days=1),
            is_active=True,
        )

    def test_apply_coupon_updates_order_amounts_and_usage(self):
        order = Order.objects.create(user=self.user, total_amount=Decimal("1000.00"))

        response = self.client.post(
            f"/api/v1/orders/{order.id}/apply-coupon/",
            {"code": "save10"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.coupon.refresh_from_db()
        self.assertEqual(order.gross_amount, Decimal("1000.00"))
        self.assertEqual(order.coupon_discount, Decimal("100.00"))
        self.assertEqual(order.total_amount, Decimal("900.00"))
        self.assertEqual(order.applied_coupon_id, self.coupon.id)
        self.assertEqual(self.coupon.used_count, 1)
        self.assertEqual(CouponUsage.objects.filter(coupon=self.coupon, user=self.user, order=order).count(), 1)

    def test_apply_coupon_is_idempotent_when_same_coupon_is_reused(self):
        order = Order.objects.create(user=self.user, total_amount=Decimal("1000.00"))

        first = self.client.post(f"/api/v1/orders/{order.id}/apply-coupon/", {"code": "SAVE10"}, format="json")
        second = self.client.post(f"/api/v1/orders/{order.id}/apply-coupon/", {"code": "SAVE10"}, format="json")

        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.coupon.refresh_from_db()
        self.assertEqual(self.coupon.used_count, 1)
        self.assertEqual(CouponUsage.objects.filter(coupon=self.coupon, order=order).count(), 1)

    def test_apply_coupon_rejects_per_user_limit_and_minimum_amount(self):
        first_order = Order.objects.create(user=self.user, total_amount=Decimal("1000.00"))
        self.client.post(f"/api/v1/orders/{first_order.id}/apply-coupon/", {"code": "SAVE10"}, format="json")

        second_order = Order.objects.create(user=self.user, total_amount=Decimal("1000.00"))
        per_user_limit_response = self.client.post(
            f"/api/v1/orders/{second_order.id}/apply-coupon/",
            {"code": "SAVE10"},
            format="json",
        )
        self.assertEqual(per_user_limit_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Per-user coupon usage limit exceeded.", str(per_user_limit_response.data))

        low_amount_order = Order.objects.create(user=self.user, total_amount=Decimal("200.00"))
        low_amount_response = self.client.post(
            f"/api/v1/orders/{low_amount_order.id}/apply-coupon/",
            {"code": "SAVE10"},
            format="json",
        )
        self.assertEqual(low_amount_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("minimum amount", str(low_amount_response.data))

    def test_apply_coupon_rejects_expired_and_max_use_limit(self):
        max_use_coupon = Coupon.objects.create(
            code="MAXED",
            discount_type=Coupon.DiscountType.FIXED,
            discount_value=Decimal("50.00"),
            max_uses=1,
            used_count=1,
            valid_from=timezone.now() - timedelta(days=2),
            valid_until=timezone.now() + timedelta(days=2),
            is_active=True,
        )
        order = Order.objects.create(user=self.user, total_amount=Decimal("1000.00"))
        maxed_response = self.client.post(
            f"/api/v1/orders/{order.id}/apply-coupon/",
            {"code": max_use_coupon.code},
            format="json",
        )
        self.assertEqual(maxed_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("usage limit exceeded", str(maxed_response.data))

        expired_coupon = Coupon.objects.create(
            code="EXPIRED",
            discount_type=Coupon.DiscountType.FIXED,
            discount_value=Decimal("50.00"),
            valid_from=timezone.now() - timedelta(days=5),
            valid_until=timezone.now() - timedelta(days=1),
            is_active=True,
        )
        expired_response = self.client.post(
            f"/api/v1/orders/{order.id}/apply-coupon/",
            {"code": expired_coupon.code},
            format="json",
        )
        self.assertEqual(expired_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("not valid", str(expired_response.data))

    def test_apply_coupon_rejects_ineligible_user_coupon(self):
        other_user = get_user_model().objects.create_user(
            email="other-coupon@example.com",
            password="StrongPass123",
            name="Other Coupon",
        )
        user_only_coupon = Coupon.objects.create(
            code="PRIVATE100",
            discount_type=Coupon.DiscountType.FIXED,
            discount_value=Decimal("100.00"),
            eligible_user=other_user,
            valid_from=timezone.now() - timedelta(days=1),
            valid_until=timezone.now() + timedelta(days=1),
            is_active=True,
        )
        order = Order.objects.create(user=self.user, total_amount=Decimal("1000.00"))
        response = self.client.post(
            f"/api/v1/orders/{order.id}/apply-coupon/",
            {"code": user_only_coupon.code},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("not eligible", str(response.data))


class AdminOrderManagementAPITests(TestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_user(
            email="admin@example.com",
            password="StrongPass123",
            name="Admin User",
            is_staff=True,
        )
        self.customer_user = get_user_model().objects.create_user(
            email="customer@example.com",
            password="StrongPass123",
            name="Customer User",
        )
        self.client = APIClient()
        self.category = Category.objects.create(name="Devices")
        self.product = Product.objects.create(
            category=self.category,
            name="Keyboard",
            description="Mechanical keyboard",
            price=Decimal("3500.00"),
            sku="KBD-001",
            stock_quantity=15,
        )
        self.order = Order.objects.create(
            user=self.customer_user,
            total_amount=Decimal("7000.00"),
            payment_status=Order.PaymentStatus.PAID,
        )
        OrderItem.objects.create(order=self.order, product=self.product, quantity=2, price=self.product.price)
        ShippingAddress.objects.create(
            order=self.order,
            full_name="Customer User",
            phone_number="9999999999",
            address_line_1="12 Main Street",
            city="Bengaluru",
            state="Karnataka",
            postal_code="560001",
            country="India",
        )

    def test_non_admin_cannot_access_admin_order_endpoints(self):
        self.client.force_authenticate(user=self.customer_user)

        response = self.client.get("/admin/orders/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_list_and_filter_orders(self):
        second_user = get_user_model().objects.create_user(
            email="another@example.com",
            password="StrongPass123",
            name="Another User",
        )
        Order.objects.create(
            user=second_user,
            total_amount=Decimal("1100.00"),
            status=Order.Status.CANCELLED,
        )
        self.client.force_authenticate(user=self.admin_user)

        by_status = self.client.get("/admin/orders/", {"status": "cancelled"})
        by_search = self.client.get("/admin/orders/", {"search": "customer@example.com"})

        self.assertEqual(by_status.status_code, status.HTTP_200_OK)
        self.assertEqual(len(by_status.data), 1)
        self.assertEqual(by_status.data[0]["status"], Order.Status.CANCELLED)
        self.assertEqual(by_search.status_code, status.HTTP_200_OK)
        self.assertEqual(len(by_search.data), 1)
        self.assertEqual(by_search.data[0]["id"], self.order.id)

    def test_admin_can_view_order_detail(self):
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(f"/admin/orders/{self.order.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user_email"], self.customer_user.email)
        self.assertEqual(len(response.data["items"]), 1)
        self.assertEqual(response.data["shipping_address"]["city"], "Bengaluru")
        self.assertIn("timeline", response.data)

    def test_admin_status_update_creates_order_event(self):
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.post(
            f"/admin/orders/{self.order.id}/status/",
            {"status": "processing", "payment_status": Order.PaymentStatus.PAID},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.CONFIRMED)
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PAID)
        event = OrderEvent.objects.get(order=self.order)
        self.assertEqual(event.previous_status, Order.Status.PENDING)
        self.assertEqual(event.new_status, Order.Status.CONFIRMED)
        self.assertEqual(event.changed_by, self.admin_user)

    @patch("adminpanel.views.send_order_email")
    def test_admin_status_update_triggers_shipped_and_delivered_emails(self, mock_send_order_email):
        self.client.force_authenticate(user=self.admin_user)

        shipped_response = self.client.post(
            f"/admin/orders/{self.order.id}/status/",
            {"status": Order.Status.SHIPPED, "payment_status": Order.PaymentStatus.PAID},
            format="json",
        )
        delivered_response = self.client.post(
            f"/admin/orders/{self.order.id}/status/",
            {"status": Order.Status.DELIVERED, "payment_status": Order.PaymentStatus.PAID},
            format="json",
        )

        self.assertEqual(shipped_response.status_code, status.HTTP_200_OK)
        self.assertEqual(delivered_response.status_code, status.HTTP_200_OK)
        self.assertEqual(mock_send_order_email.call_count, 2)
        mock_send_order_email.assert_any_call("order_shipped", self.order)
        mock_send_order_email.assert_any_call("order_delivered", self.order)


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="no-reply@example.com",
    SUPPORT_EMAIL="support@example.com",
)
class OrderNotificationServiceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="notify@example.com",
            password="StrongPass123",
            name="Notify User",
        )
        self.category = Category.objects.create(name="NotifyCategory")
        self.product = Product.objects.create(
            category=self.category,
            name="Notify Product",
            description="Notification test product",
            price=Decimal("2500.00"),
            sku="NTF-001",
            stock_quantity=50,
        )
        self.order = Order.objects.create(
            user=self.user,
            total_amount=Decimal("5000.00"),
            status=Order.Status.CONFIRMED,
            payment_status=Order.PaymentStatus.PAID,
        )
        OrderItem.objects.create(order=self.order, product=self.product, quantity=2, price=self.product.price)

    def test_send_order_email_sends_once_and_persists_sent_event(self):
        first = send_order_email("payment_success", self.order)
        second = send_order_email("payment_success", self.order)

        self.assertTrue(first)
        self.assertFalse(second)
        self.assertEqual(len(mail.outbox), 1)
        sent_event = EmailEvent.objects.get(order=self.order, email_type=EmailEvent.EmailType.PAYMENT_SUCCESS)
        self.assertEqual(sent_event.status, EmailEvent.Status.SENT)
        self.assertIsNotNone(sent_event.sent_at)
        self.assertIn(f"Order ID: {self.order.id}", mail.outbox[0].body)
        self.assertIn("Notify Product", mail.outbox[0].body)
        self.assertIn("support@example.com", mail.outbox[0].body)
