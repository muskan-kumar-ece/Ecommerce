from rest_framework.routers import DefaultRouter

from .views import FlashSaleViewSet

router = DefaultRouter()
router.register("", FlashSaleViewSet, basename="flash-sale")

urlpatterns = router.urls
