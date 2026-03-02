from rest_framework import serializers

from .models import Cart, CartItem, Order, OrderItem, ShippingAddress


class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = ("id", "user", "is_active", "created_at", "updated_at")
        read_only_fields = ("id", "user", "created_at", "updated_at")


class CartItemSerializer(serializers.ModelSerializer):
    def validate_cart(self, cart):
        request = self.context.get("request")
        if request and cart.user_id != request.user.id:
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
            "status",
            "payment_status",
            "tracking_id",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "user", "created_at", "updated_at")


class OrderItemSerializer(serializers.ModelSerializer):
    def validate_order(self, order):
        request = self.context.get("request")
        if request and order.user_id != request.user.id:
            raise serializers.ValidationError("You can only add items to your own order.")
        return order

    class Meta:
        model = OrderItem
        fields = ("id", "order", "product", "quantity", "price", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")


class ShippingAddressSerializer(serializers.ModelSerializer):
    def validate_order(self, order):
        request = self.context.get("request")
        if request and order.user_id != request.user.id:
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
