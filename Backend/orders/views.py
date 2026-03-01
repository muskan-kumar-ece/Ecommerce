from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from .models import Cart, CartItem, Order, OrderItem, ShippingAddress
from .serializers import CartItemSerializer, CartSerializer, OrderItemSerializer, OrderSerializer, ShippingAddressSerializer


class UserScopedViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    user_field = "user"

    def get_queryset(self):
        return self.queryset.filter(**{self.user_field: self.request.user})

    def perform_create(self, serializer):
        model_fields = {field.name for field in serializer.Meta.model._meta.fields}
        if "__" not in self.user_field and self.user_field in model_fields:
            serializer.save(**{self.user_field: self.request.user})
            return
        serializer.save()


class CartViewSet(UserScopedViewSet):
    queryset = Cart.objects.prefetch_related("items").all()
    serializer_class = CartSerializer


class CartItemViewSet(UserScopedViewSet):
    queryset = CartItem.objects.select_related("cart", "product", "cart__user").all()
    serializer_class = CartItemSerializer
    user_field = "cart__user"


class OrderViewSet(UserScopedViewSet):
    queryset = Order.objects.prefetch_related("items").all()
    serializer_class = OrderSerializer


class OrderItemViewSet(UserScopedViewSet):
    queryset = OrderItem.objects.select_related("order", "product", "order__user").all()
    serializer_class = OrderItemSerializer
    user_field = "order__user"


class ShippingAddressViewSet(UserScopedViewSet):
    queryset = ShippingAddress.objects.select_related("user", "order").all()
    serializer_class = ShippingAddressSerializer
