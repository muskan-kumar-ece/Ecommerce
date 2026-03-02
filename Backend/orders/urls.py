from rest_framework.routers import DefaultRouter

from .views import CouponViewSet, CartItemViewSet, CartViewSet, OrderItemViewSet, OrderViewSet, ShippingAddressViewSet

router = DefaultRouter()
router.register("carts", CartViewSet, basename="cart")
router.register("cart-items", CartItemViewSet, basename="cart-item")
router.register("items", OrderItemViewSet, basename="order-item")
router.register("shipping-addresses", ShippingAddressViewSet, basename="shipping-address")
router.register("coupons", CouponViewSet, basename="coupon")
router.register("", OrderViewSet, basename="order")

urlpatterns = router.urls
