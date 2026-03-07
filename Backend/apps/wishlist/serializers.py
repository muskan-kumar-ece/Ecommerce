from rest_framework import serializers

from products.models import Product

from .models import Wishlist


class WishlistProductSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ('id', 'name', 'price', 'image', 'slug')

    def get_image(self, obj):
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image:
            return primary_image.image_url
        fallback_image = obj.images.first()
        return fallback_image.image_url if fallback_image else None


class WishlistItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_price = serializers.DecimalField(source='product.price', max_digits=12, decimal_places=2, read_only=True)
    image_url = serializers.SerializerMethodField()
    product_details = WishlistProductSerializer(source='product', read_only=True)

    class Meta:
        model = Wishlist
        fields = (
            'id',
            'product',
            'product_name',
            'product_price',
            'image_url',
            'product_details',
            'created_at',
        )
        read_only_fields = fields

    def get_image_url(self, obj):
        primary_image = obj.product.images.filter(is_primary=True).first()
        if primary_image:
            return primary_image.image_url
        fallback_image = obj.product.images.first()
        return fallback_image.image_url if fallback_image else None


class WishlistCreateSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
