from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.viewsets import ModelViewSet

from .models import Category, Inventory, Product, ProductImage
from .serializers import CategorySerializer, InventorySerializer, ProductImageSerializer, ProductSerializer


class AdminWriteViewSet(ModelViewSet):
    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [AllowAny()]
        return [IsAdminUser()]


class CategoryViewSet(AdminWriteViewSet):
    queryset = Category.objects.select_related("parent").all()
    serializer_class = CategorySerializer
    lookup_field = "slug"


class ProductViewSet(AdminWriteViewSet):
    queryset = Product.objects.select_related("category").prefetch_related("images").all()
    serializer_class = ProductSerializer
    lookup_field = "slug"


class ProductImageViewSet(AdminWriteViewSet):
    queryset = ProductImage.objects.select_related("product").all()
    serializer_class = ProductImageSerializer


class InventoryViewSet(AdminWriteViewSet):
    queryset = Inventory.objects.select_related("product").all()
    serializer_class = InventorySerializer
