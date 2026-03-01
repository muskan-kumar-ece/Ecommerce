from rest_framework.routers import DefaultRouter

from .views import CartItemViewSet, CartViewSet, OrderItemViewSet, OrderViewSet, ShippingAddressViewSet

router = DefaultRouter()
router.register("carts", CartViewSet, basename="cart")
router.register("cart-items", CartItemViewSet, basename="cart-item")
router.register("orders", OrderViewSet, basename="order")
router.register("order-items", OrderItemViewSet, basename="order-item")
router.register("shipping-addresses", ShippingAddressViewSet, basename="shipping-address")

urlpatterns = router.urls
