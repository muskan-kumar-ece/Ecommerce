from decimal import Decimal, ROUND_HALF_UP

from django.utils import timezone
from rest_framework import serializers

from .models import Cart, CartItem, Coupon, CouponUsage, Order, OrderItem, ShippingAddress


class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = ("id", "user", "is_active", "created_at", "updated_at")
        read_only_fields = ("id", "user", "created_at", "updated_at")


class CartItemSerializer(serializers.ModelSerializer):
    def validate_cart(self, cart):
        request = self.context.get("request")
        if request and request.user.is_authenticated and cart.user_id != request.user.id:
            raise serializers.ValidationError("You can only add items to your own cart.")
        return cart

    class Meta:
        model = CartItem
        fields = ("id", "cart", "product", "quantity", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = (
            "id",
            "user",
            "total_amount",
            "gross_amount",
            "coupon_discount",
            "applied_coupon",
            "status",
            "payment_status",
            "tracking_id",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "user",
            "status",
            "payment_status",
            "gross_amount",
            "coupon_discount",
            "applied_coupon",
            "created_at",
            "updated_at",
        )


class OrderItemSerializer(serializers.ModelSerializer):
    def validate_order(self, order):
        request = self.context.get("request")
        if request and request.user.is_authenticated and order.user_id != request.user.id:
            raise serializers.ValidationError("You can only add items to your own order.")
        return order

    class Meta:
        model = OrderItem
        fields = ("id", "order", "product", "quantity", "price", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")


class ShippingAddressSerializer(serializers.ModelSerializer):
    def validate_order(self, order):
        request = self.context.get("request")
        if request and request.user.is_authenticated and order.user_id != request.user.id:
            raise serializers.ValidationError("You can only add a shipping address to your own order.")
        return order

    class Meta:
        model = ShippingAddress
        fields = (
            "id",
            "order",
            "full_name",
            "phone_number",
            "address_line_1",
            "address_line_2",
            "city",
            "state",
            "postal_code",
            "country",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = (
            "id",
            "code",
            "discount_type",
            "discount_value",
            "minimum_order_amount",
            "max_uses",
            "used_count",
            "per_user_limit",
            "eligible_user",
            "valid_from",
            "valid_until",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "used_count", "created_at", "updated_at")


class ApplyCouponSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=50)

    def validate_code(self, value):
        return value.upper()

    def validate(self, attrs):
        request = self.context["request"]
        order = self.context["order"]
        now = timezone.now()
        coupon = (
            Coupon.objects.select_for_update()
            .filter(code=attrs["code"])
            .first()
        )
        if not coupon:
            raise serializers.ValidationError({"code": "Invalid coupon code."})
        if not coupon.is_active:
            raise serializers.ValidationError({"code": "Coupon is inactive."})
        if coupon.valid_from > now or coupon.valid_until < now:
            raise serializers.ValidationError({"code": "Coupon is not valid at this time."})
        order_base_amount = order.gross_amount or order.total_amount
        if coupon.minimum_order_amount and order_base_amount < coupon.minimum_order_amount:
            raise serializers.ValidationError({"code": "Order does not meet minimum amount for this coupon."})
        if coupon.max_uses is not None and coupon.used_count >= coupon.max_uses:
            raise serializers.ValidationError({"code": "Coupon usage limit exceeded."})
        if coupon.per_user_limit is not None:
            user_usage_count = CouponUsage.objects.filter(coupon=coupon, user=request.user).count()
            if user_usage_count >= coupon.per_user_limit:
                raise serializers.ValidationError({"code": "Per-user coupon usage limit exceeded."})
        if coupon.eligible_user_id and coupon.eligible_user_id != request.user.id:
            raise serializers.ValidationError({"code": "Coupon is not eligible for this user."})
        attrs["coupon"] = coupon
        return attrs

    def calculate_discount(self, order_amount: Decimal) -> Decimal:
        coupon: Coupon = self.validated_data["coupon"]
        if coupon.discount_type == Coupon.DiscountType.PERCENTAGE:
            discount = (order_amount * coupon.discount_value / Decimal("100")).quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP,
            )
        else:
            discount = coupon.discount_value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        max_discount = max(order_amount - Decimal("0.01"), Decimal("0.00"))
        return min(discount, max_discount)
