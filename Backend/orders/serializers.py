from rest_framework import serializers

from .models import Cart, CartItem, Order, OrderItem, ShippingAddress


class CartItemSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        request = self.context.get("request")
        cart = attrs.get("cart") or getattr(self.instance, "cart", None)
        if request and cart and cart.user_id != request.user.id:
            raise serializers.ValidationError("You can only manage items in your own cart.")
        return attrs

    class Meta:
        model = CartItem
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")


class OrderItemSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        request = self.context.get("request")
        order = attrs.get("order") or getattr(self.instance, "order", None)
        if request and order and order.user_id != request.user.id:
            raise serializers.ValidationError("You can only manage items in your own order.")
        return attrs

    class Meta:
        model = OrderItem
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")


class ShippingAddressSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        request = self.context.get("request")
        order = attrs.get("order") or getattr(self.instance, "order", None)
        if request and order and order.user_id != request.user.id:
            raise serializers.ValidationError("You can only assign addresses to your own order.")
        return attrs

    class Meta:
        model = ShippingAddress
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")
