from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import IntegrityError
from django.db import transaction
from django.db.models import F, Sum
from django.db.models.functions import Coalesce
from rest_framework import decorators
from rest_framework import permissions, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.response import Response

from core.throttles import AdminRateThrottle, OrderCreateRateThrottle
from .models import Cart, CartItem, Coupon, CouponUsage, Order, OrderItem, ShippingAddress
from .notifications import send_order_email
from .serializers import (
    ApplyCouponSerializer,
    CartItemSerializer,
    CartSerializer,
    CouponSerializer,
    CreateOrderSerializer,
    OrderDetailSerializer,
    OrderItemSerializer,
    OrderSerializer,
    ShippingAddressSerializer,
)


class OrderPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user).prefetch_related("items")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CartItemViewSet(viewsets.ModelViewSet):
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CartItem.objects.filter(cart__user=self.request.user).select_related("cart", "product")


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = OrderPagination

    def get_throttles(self):
        if self.action in {"create", "create_order"}:
            return [OrderCreateRateThrottle()]
        return super().get_throttles()

    def get_queryset(self):
        return (
            Order.objects.filter(user=self.request.user)
            .select_related("shipping_address", "applied_coupon")
            .prefetch_related("items__product", "shipping_events", "events")
        )

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action in ['retrieve', 'list']:
            return OrderDetailSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        idempotency_key = self.request.headers.get("Idempotency-Key")
        if idempotency_key:
            existing_order = (
                Order.objects.filter(user=self.request.user, idempotency_key=idempotency_key)
                .select_related("shipping_address", "applied_coupon")
                .prefetch_related("items__product")
                .first()
            )
            if existing_order:
                serializer.instance = existing_order
                return
            try:
                serializer.save(user=self.request.user, idempotency_key=idempotency_key)
            except IntegrityError:
                existing_order = Order.objects.filter(user=self.request.user, idempotency_key=idempotency_key).first()
                if existing_order:
                    serializer.instance = existing_order
                    return
                raise
            return
        serializer.save(user=self.request.user)

    @decorators.action(detail=False, methods=["post"], url_path="create")
    @transaction.atomic
    def create_order(self, request):
        """
        Create an order with items.
        
        Request body:
        {
            "items": [
                {"product_id": 1, "quantity": 2},
                {"product_id": 2, "quantity": 1}
            ]
        }
        """
        serializer = CreateOrderSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        
        # Return the created order with items
        output_serializer = OrderDetailSerializer(order, context={"request": request})
        return Response(output_serializer.data, status=201)

    @decorators.action(detail=False, methods=["get"], url_path="my-orders")
    def my_orders(self, request):
        """
        Get all orders for the authenticated user.
        This is an alias for the list action with a more descriptive endpoint name.
        """
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = OrderDetailSerializer(page, many=True, context={"request": request})
            return self.get_paginated_response(serializer.data)

        serializer = OrderDetailSerializer(queryset, many=True, context={"request": request})
        return Response(serializer.data)

    @decorators.action(detail=True, methods=["post"], url_path="apply-coupon")
    @transaction.atomic
    def apply_coupon(self, request, pk=None):
        order = (
            Order.objects.select_for_update()
            .select_related("applied_coupon")
            .filter(id=pk, user=request.user)
            .first()
        )
        if not order:
            return Response({"detail": "Order not found."}, status=404)
        if order.payment_status != Order.PaymentStatus.PENDING:
            return Response({"detail": "Coupon can only be applied to pending payment orders."}, status=400)
        requested_code = str(request.data.get("code", "")).upper()
        if order.applied_coupon_id:
            if order.applied_coupon and order.applied_coupon.code == requested_code:
                return Response(
                    {
                        "order_id": order.id,
                        "coupon_code": order.applied_coupon.code,
                        "gross_amount": order.gross_amount or order.total_amount,
                        "discount_amount": order.coupon_discount,
                        "net_amount": order.total_amount,
                    },
                    status=200,
                )
            return Response({"detail": "A different coupon is already applied to this order."}, status=400)

        serializer = ApplyCouponSerializer(data=request.data, context={"request": request, "order": order})
        serializer.is_valid(raise_exception=True)
        coupon = serializer.validated_data["coupon"]

        gross_amount = (order.gross_amount or order.total_amount).quantize(Decimal("0.01"))
        discount_amount = serializer.calculate_discount(gross_amount)
        net_amount = (gross_amount - discount_amount).quantize(Decimal("0.01"))

        order.gross_amount = gross_amount
        order.coupon_discount = discount_amount
        order.total_amount = net_amount
        order.applied_coupon = coupon
        order.save(update_fields=["gross_amount", "coupon_discount", "total_amount", "applied_coupon", "updated_at"])

        CouponUsage.objects.create(
            coupon=coupon,
            user=request.user,
            order=order,
            discount_amount=discount_amount,
        )
        Coupon.objects.filter(id=coupon.id).update(used_count=F("used_count") + 1)

        return Response(
            {
                "order_id": order.id,
                "coupon_code": coupon.code,
                "gross_amount": gross_amount,
                "discount_amount": discount_amount,
                "net_amount": net_amount,
            },
            status=200,
        )

    @decorators.action(detail=True, methods=["post"], url_path="cancel")
    @transaction.atomic
    def cancel_order(self, request, pk=None):
        order = (
            Order.objects.select_for_update()
            .filter(id=pk, user=request.user)
            .first()
        )
        if not order:
            return Response({"detail": "Order not found."}, status=404)
        if order.status in {Order.Status.SHIPPED, Order.Status.DELIVERED, Order.Status.CANCELLED, Order.Status.REFUNDED}:
            return Response({"detail": "This order can no longer be cancelled."}, status=400)
        previous_status = order.status
        previous_payment_status = order.payment_status
        order.status = Order.Status.CANCELLED
        order.save(update_fields=["status", "updated_at"])
        order.events.create(
            previous_status=previous_status,
            new_status=Order.Status.CANCELLED,
            previous_payment_status=previous_payment_status,
            new_payment_status=order.payment_status,
            changed_by=request.user,
            note="Cancelled by customer",
        )
        send_order_email("order_cancelled", order)
        return Response({"detail": "Order cancelled successfully."}, status=200)


class OrderItemViewSet(viewsets.ModelViewSet):
    serializer_class = OrderItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return OrderItem.objects.filter(order__user=self.request.user).select_related("order", "product")


class ShippingAddressViewSet(viewsets.ModelViewSet):
    serializer_class = ShippingAddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ShippingAddress.objects.filter(order__user=self.request.user).select_related("order")


class CouponViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CouponSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = Coupon.objects.all()


class AdminAnalyticsView(APIView):
    permission_classes = [permissions.IsAdminUser]
    throttle_classes = [AdminRateThrottle]

    def get(self, request):
        if request.method == "GET":
            try:
                cached = cache.get("admin_analytics_summary")
                if cached is not None:
                    return Response(cached)
            except Exception:
                pass

        total_orders = Order.objects.count()
        total_revenue = (
            Order.objects.filter(payment_status=Order.PaymentStatus.PAID).aggregate(
                total=Coalesce(Sum("total_amount"), Decimal("0.00"))
            )["total"]
        )
        total_users = get_user_model().objects.count()
        top_products = list(
            OrderItem.objects.filter(order__payment_status=Order.PaymentStatus.PAID)
            .values("product_id", "product__name")
            .annotate(total_sold=Coalesce(Sum("quantity"), 0))
            .order_by("-total_sold", "product_id")[:5]
        )
        recent_orders = [
            {
                "order_id": order.id,
                "user_email": order.user.email,
                "total_amount": str(order.total_amount),
                "status": order.status,
                "created_at": order.created_at.isoformat(),
            }
            for order in Order.objects.select_related("user").order_by("-created_at")[:10]
        ]

        response_data = {
            "total_orders": total_orders,
            "total_revenue": f"{total_revenue:.2f}",
            "total_users": total_users,
            "top_products": [
                {
                    "product_id": row["product_id"],
                    "name": row["product__name"],
                    "total_sold": row["total_sold"],
                }
                for row in top_products
            ],
            "recent_orders": recent_orders,
        }
        if request.method == "GET":
            try:
                cache.set("admin_analytics_summary", response_data, timeout=120)
            except Exception:
                pass
        return Response(response_data)
