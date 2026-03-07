from decimal import Decimal

from django.db.models import Sum
from django.db.models.functions import Coalesce
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.models import Order
from products.models import Product

from .models import Vendor, VendorOrder, VendorProduct
from .serializers import (
    VendorDashboardProductSerializer,
    VendorEarningsSerializer,
    VendorOrderSerializer,
    VendorProductUploadSerializer,
    VendorSerializer,
)


class VendorProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        vendor = Vendor.objects.filter(user=request.user).first()
        if not vendor:
            return Response({"detail": "Vendor profile not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = VendorSerializer(vendor)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        default_business_name = request.user.name or request.user.email or "Vendor Store"
        vendor, _ = Vendor.objects.get_or_create(
            user=request.user,
            defaults={"business_name": request.data.get("business_name", default_business_name)},
        )
        serializer = VendorSerializer(vendor, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        if request.user.role != request.user.Role.VENDOR:
            request.user.role = request.user.Role.VENDOR
            request.user.save(update_fields=["role"])
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class VendorDashboardProductView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def _get_vendor(self, request):
        return Vendor.objects.filter(user=request.user, is_active=True).first()

    def get(self, request):
        vendor = self._get_vendor(request)
        if not vendor:
            return Response({"detail": "Vendor profile not found."}, status=status.HTTP_404_NOT_FOUND)
        product_ids = VendorProduct.objects.filter(vendor=vendor).values_list("product_id", flat=True)
        products = Product.objects.filter(id__in=product_ids).select_related("category").order_by("-created_at")
        serializer = VendorDashboardProductSerializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        vendor = self._get_vendor(request)
        if not vendor:
            return Response({"detail": "Vendor profile not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = VendorProductUploadSerializer(data=request.data, context={"vendor": vendor})
        serializer.is_valid(raise_exception=True)
        product = serializer.save()
        output_serializer = VendorDashboardProductSerializer(product)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class VendorDashboardOrdersView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        vendor = Vendor.objects.filter(user=request.user, is_active=True).first()
        if not vendor:
            return Response({"detail": "Vendor profile not found."}, status=status.HTTP_404_NOT_FOUND)
        queryset = VendorOrder.objects.filter(vendor=vendor).select_related("order")
        serializer = VendorOrderSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class VendorDashboardEarningsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        vendor = Vendor.objects.filter(user=request.user, is_active=True).first()
        if not vendor:
            return Response({"detail": "Vendor profile not found."}, status=status.HTTP_404_NOT_FOUND)
        paid_orders = VendorOrder.objects.filter(vendor=vendor, order__payment_status=Order.PaymentStatus.PAID)
        summary = paid_orders.aggregate(
            gross_sales=Coalesce(Sum("total_amount"), Decimal("0.00")),
            total_commission=Coalesce(Sum("commission_amount"), Decimal("0.00")),
            total_earnings=Coalesce(Sum("earnings_amount"), Decimal("0.00")),
        )
        summary["total_orders"] = paid_orders.count()
        serializer = VendorEarningsSerializer(summary)
        return Response(serializer.data, status=status.HTTP_200_OK)
