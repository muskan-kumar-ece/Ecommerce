from rest_framework import serializers

from .models import Category, Inventory, Product, ProductImage, Review
from orders.models import Order, OrderItem


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = (
            "id",
            "product",
            "image_url",
            "alt_text",
            "is_primary",
            "sort_order",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class InventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventory
        fields = (
            "id",
            "product",
            "quantity",
            "reserved_quantity",
            "reorder_level",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    reviews_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "category",
            "category_name",
            "name",
            "slug",
            "description",
            "price",
            "sku",
            "stock_quantity",
            "is_refurbished",
            "condition_grade",
            "is_active",
            "average_rating",
            "reviews_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.name", read_only=True)
    is_mine = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Review
        fields = (
            "id",
            "user",
            "user_name",
            "is_mine",
            "product",
            "rating",
            "title",
            "comment",
            "created_at",
        )
        read_only_fields = ("id", "user", "user_name", "is_mine", "created_at")

    def get_is_mine(self, obj):
        request = self.context.get("request")
        return bool(request and request.user.is_authenticated and obj.user_id == request.user.id)

    def validate(self, attrs):
        request = self.context.get("request")
        if request is None or not request.user.is_authenticated:
            return attrs

        product = attrs.get("product") or getattr(self.instance, "product", None)
        if product is None:
            return attrs

        if self.instance is None:
            if Review.objects.filter(user=request.user, product=product).exists():
                raise serializers.ValidationError("You have already reviewed this product.")
            has_verified_purchase = OrderItem.objects.filter(
                order__user=request.user,
                order__payment_status=Order.PaymentStatus.PAID,
                product=product,
            ).exists()
            if not has_verified_purchase:
                raise serializers.ValidationError("Only verified buyers can review this product.")

        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        return Review.objects.create(user=request.user, **validated_data)
