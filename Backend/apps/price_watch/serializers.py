from rest_framework import serializers

from products.models import Product

from .models import PriceWatch


class PriceWatchCreateSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.filter(is_active=True))


class PriceWatchItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    current_price = serializers.DecimalField(source="product.price", max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = PriceWatch
        fields = ("id", "product", "product_name", "last_price", "current_price", "created_at")
        read_only_fields = fields
