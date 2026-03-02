from decimal import Decimal

from django.db import IntegrityError
from django.db import transaction
from django.db.models import F
from rest_framework import decorators
from rest_framework import permissions, viewsets
from rest_framework.response import Response

from .models import Cart, CartItem, Coupon, CouponUsage, Order, OrderItem, ShippingAddress
from .serializers import (
    ApplyCouponSerializer,
    CartItemSerializer,
    CartSerializer,
    CouponSerializer,
    OrderItemSerializer,
    OrderSerializer,
    ShippingAddressSerializer,
)


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

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).select_related("shipping_address").prefetch_related("items")

    def perform_create(self, serializer):
        idempotency_key = self.request.headers.get("Idempotency-Key")
        if idempotency_key:
            existing_order = (
                Order.objects.filter(user=self.request.user, idempotency_key=idempotency_key)
                .select_related("shipping_address")
                .prefetch_related("items")
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
