from difflib import SequenceMatcher

from django.db.models import Avg, Count, Value
from django.db.models.functions import Coalesce
from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, permissions, viewsets
from rest_framework.generics import GenericAPIView
from rest_framework.generics import ListAPIView
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from .models import Category, Inventory, Product, ProductImage, Review
from .permissions import IsAdminOrReadOnly
from .serializers import (
    CategorySerializer,
    InventorySerializer,
    ProductImageSerializer,
    ProductSearchResultSerializer,
    ProductSerializer,
    ProductSuggestionSerializer,
    ReviewSerializer,
)


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


class ProductSearchView(GenericAPIView):
    serializer_class = ProductSearchResultSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = ProductPagination

    @staticmethod
    def _max_similarity(query, text):
        query = query.lower()
        text = text.lower()
        candidates = [text] + text.split()
        return max(SequenceMatcher(None, query, candidate).ratio() for candidate in candidates if candidate)

    def get(self, request):
        query = request.query_params.get("q", "").strip().lower()
        if not query:
            return Response({"count": 0, "next": None, "previous": None, "results": []})

        products = Product.objects.select_related("category").filter(is_active=True)
        ranked = []
        for product in products:
            name = product.name.lower()
            category_name = product.category.name.lower()
            score = 0.0

            if query in name:
                score += 10.0
            if query in category_name:
                score += 8.0

            score += self._max_similarity(query, name) * 6.0
            score += self._max_similarity(query, category_name) * 4.0

            if score >= 5.0:
                product.relevance_score = round(score, 3)
                ranked.append(product)

        ranked.sort(key=lambda p: (-p.relevance_score, p.id))
        page = self.paginate_queryset(ranked)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class ProductSearchSuggestionsView(GenericAPIView):
    serializer_class = ProductSuggestionSerializer
    permission_classes = [permissions.AllowAny]

    @staticmethod
    def _suggestion_score(query, product):
        query = query.lower()
        name = product.name.lower()
        category_name = product.category.name.lower()
        score = 0.0

        if name.startswith(query):
            score += 12.0
        if category_name.startswith(query):
            score += 6.0
        if query in name:
            score += 8.0
        if query in category_name:
            score += 4.0

        score += SequenceMatcher(None, query, name).ratio() * 5.0
        score += SequenceMatcher(None, query, category_name).ratio() * 3.0
        return score

    def get(self, request):
        query = request.query_params.get("q", "").strip().lower()
        if not query:
            return Response([])

        products = Product.objects.select_related("category").filter(is_active=True)
        scored = []
        for product in products:
            score = self._suggestion_score(query, product)
            if score >= 2.5:
                scored.append((score, product))

        scored.sort(key=lambda item: (-item[0], item[1].id))
        top_products = [item[1] for item in scored[:10]]
        serializer = self.get_serializer(top_products, many=True)
        return Response(serializer.data)
