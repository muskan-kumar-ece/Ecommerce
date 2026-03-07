from decimal import Decimal

from rest_framework import serializers

from orders.models import Order
from products.models import Category, Product

from .models import Vendor, VendorOrder, VendorProduct


class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = ("id", "user", "business_name", "slug", "commission_rate", "is_active", "created_at", "updated_at")
        read_only_fields = ("id", "user", "slug", "created_at", "updated_at")


class VendorDashboardProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)

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
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "slug", "created_at", "updated_at")


class VendorOrderSerializer(serializers.ModelSerializer):
    order_id = serializers.IntegerField(source="order.id", read_only=True)
    order_status = serializers.CharField(source="order.status", read_only=True)
    payment_status = serializers.CharField(source="order.payment_status", read_only=True)
    order_created_at = serializers.DateTimeField(source="order.created_at", read_only=True)

    class Meta:
        model = VendorOrder
        fields = (
            "id",
            "order_id",
            "order_status",
            "payment_status",
            "order_created_at",
            "total_amount",
            "commission_amount",
            "earnings_amount",
        )
        read_only_fields = fields


class VendorEarningsSerializer(serializers.Serializer):
    total_orders = serializers.IntegerField(min_value=0)
    gross_sales = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.00"))
    total_commission = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.00"))
    total_earnings = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.00"))


class VendorProductUploadSerializer(serializers.Serializer):
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(allow_blank=True, required=False)
    price = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))
    sku = serializers.CharField(max_length=64)
    stock_quantity = serializers.IntegerField(min_value=0)
    is_refurbished = serializers.BooleanField(default=False)
    condition_grade = serializers.CharField(max_length=20, allow_blank=True, required=False)
    is_active = serializers.BooleanField(default=True)

    def create(self, validated_data):
        vendor = self.context["vendor"]
        product = Product.objects.create(**validated_data)
        VendorProduct.objects.create(vendor=vendor, product=product)
        return product
