from rest_framework import viewsets

from .models import Category, Inventory, Product, ProductImage
from .permissions import IsAdminOrReadOnly
from .serializers import CategorySerializer, InventorySerializer, ProductImageSerializer, ProductSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        queryset = Product.objects.select_related("category", "inventory").prefetch_related("images")
        if self.request.user and self.request.user.is_staff:
            return queryset
        return queryset.filter(is_active=True)


class ProductImageViewSet(viewsets.ModelViewSet):
    queryset = ProductImage.objects.select_related("product")
    serializer_class = ProductImageSerializer
    permission_classes = [IsAdminOrReadOnly]


class InventoryViewSet(viewsets.ModelViewSet):
    queryset = Inventory.objects.select_related("product")
    serializer_class = InventorySerializer
    permission_classes = [IsAdminOrReadOnly]
