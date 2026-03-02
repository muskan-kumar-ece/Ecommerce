from rest_framework.routers import DefaultRouter

from .views import CategoryViewSet, InventoryViewSet, ProductImageViewSet, ProductViewSet

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("images", ProductImageViewSet, basename="product-image")
router.register("inventory", InventoryViewSet, basename="inventory")
router.register("", ProductViewSet, basename="product")

urlpatterns = router.urls
