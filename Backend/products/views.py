from django.db.models import Avg, Count, Value
from django.db.models.functions import Coalesce
from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, permissions, viewsets
from rest_framework.generics import ListAPIView
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import PermissionDenied

from .models import Category, Inventory, Product, ProductImage, Review
from .permissions import IsAdminOrReadOnly
from .serializers import CategorySerializer, InventorySerializer, ProductImageSerializer, ProductSerializer, ReviewSerializer


class ReviewPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50


class ProductPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class ProductFilterSet(filters.FilterSet):
    category = filters.CharFilter(method="filter_category")
    price = filters.NumberFilter(field_name="price")
    min_price = filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = filters.NumberFilter(field_name="price", lookup_expr="lte")
    stock_quantity = filters.NumberFilter(field_name="stock_quantity")
    is_active = filters.BooleanFilter(field_name="is_active")
    in_stock = filters.BooleanFilter(method="filter_in_stock")

    class Meta:
        model = Product
        fields = ["category", "price", "stock_quantity", "is_active"]

    def filter_category(self, queryset, name, value):
        if value.isdigit():
            return queryset.filter(category_id=int(value))
        return queryset.filter(category__slug=value)

    def filter_in_stock(self, queryset, name, value):
        if value is None:
            return queryset
        if value:
            return queryset.filter(stock_quantity__gt=0)
        return queryset.filter(stock_quantity=0)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = ProductPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProductFilterSet
    search_fields = ["name", "description", "sku"]
    ordering_fields = ["price", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = Product.objects.select_related("category", "inventory").prefetch_related("images").annotate(
            average_rating=Coalesce(Avg("reviews__rating"), Value(0.0)),
            reviews_count=Count("reviews"),
        )
        if self.request.user.is_authenticated and self.request.user.is_staff:
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


class ProductReviewListView(ListAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = ReviewPagination

    def get_queryset(self):
        return Review.objects.filter(product_id=self.kwargs["product_id"]).select_related("user", "product")


class ReviewViewSet(mixins.CreateModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Review.objects.select_related("user", "product")
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(user=self.request.user)

    def perform_update(self, serializer):
        if serializer.instance.user_id != self.request.user.id:
            raise PermissionDenied("You can only edit your own review.")
        serializer.save()
