from rest_framework import permissions, viewsets

from .models import Cart, CartItem, Order, OrderItem, ShippingAddress
from .serializers import CartItemSerializer, CartSerializer, OrderItemSerializer, OrderSerializer, ShippingAddressSerializer


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
            existing_order = Order.objects.filter(user=self.request.user, idempotency_key=idempotency_key).first()
            if existing_order:
                serializer.instance = existing_order
                return
            serializer.save(user=self.request.user, idempotency_key=idempotency_key)
            return
        serializer.save(user=self.request.user)


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
