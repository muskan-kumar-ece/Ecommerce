from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

from django.db import transaction
from django.db.models import Count, DecimalField, F, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from core.throttles import AdminRateThrottle
from orders.notifications import send_order_email
from orders.models import Order, OrderEvent, ShippingEvent
from users.models import Referral

from .serializers import (
    AdminDeliverOrderSerializer,
    AdminOrderDetailSerializer,
    AdminOrderListSerializer,
    AdminShipOrderSerializer,
    AdminOrderStatusUpdateSerializer,
    AnalyticsSummarySerializer,
)

TRACKING_ID_PREFIX = "TRK"


class AdminOrderPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200


class AnalyticsSummaryView(APIView):
    permission_classes = [IsAdminUser]
    throttle_classes = [AdminRateThrottle]

    def get(self, request):
        today = timezone.localdate()
        last_7_days_start = today - timedelta(days=6)

        metrics = Order.objects.aggregate(
            gross_revenue=Coalesce(
                Sum(
                    Coalesce(F("gross_amount"), F("total_amount")),
                    filter=Q(payment_status=Order.PaymentStatus.PAID),
                ),
                Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            ),
            discount_amount=Coalesce(
                Sum("coupon_discount", filter=Q(payment_status=Order.PaymentStatus.PAID)),
                Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            ),
            net_revenue=Coalesce(
                Sum("total_amount", filter=Q(payment_status=Order.PaymentStatus.PAID)),
                Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            ),
            total_orders=Count("id"),
            total_paid_orders=Count("id", filter=Q(payment_status=Order.PaymentStatus.PAID)),
            total_refunded_orders=Count("id", filter=Q(payment_status=Order.PaymentStatus.REFUNDED)),
            revenue_from_referrals=Coalesce(
                Sum(
                    "total_amount",
                    filter=Q(payment_status=Order.PaymentStatus.PAID, user__referral_record__isnull=False),
                ),
                Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            ),
            today_revenue=Coalesce(
                Sum(
                    "total_amount",
                    filter=Q(
                        payment_status=Order.PaymentStatus.PAID,
                        created_at__date=today,
                    ),
                ),
                Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            ),
            today_orders=Count("id", filter=Q(created_at__date=today)),
            last_7_days_revenue=Coalesce(
                Sum(
                    "total_amount",
                    filter=Q(
                        payment_status=Order.PaymentStatus.PAID,
                        created_at__date__gte=last_7_days_start,
                    ),
                ),
                Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            ),
        )

        total_orders = metrics["total_orders"]
        if total_orders:
            refund_rate_percent = float(
                (Decimal(metrics["total_refunded_orders"]) / Decimal(total_orders)) * Decimal("100")
            )
        else:
            refund_rate_percent = 0.0

        referral_metrics = Referral.objects.aggregate(
            total_referrals=Count("id"),
            successful_referrals=Count("id", filter=Q(reward_issued=True)),
        )

        serializer = AnalyticsSummarySerializer(
            {
                **metrics,
                **referral_metrics,
                "total_revenue": metrics["net_revenue"],
                "refund_rate_percent": round(refund_rate_percent, 2),
            }
        )
        return Response(serializer.data)


class AdminOrderListView(APIView):
    permission_classes = [IsAdminUser]
    throttle_classes = [AdminRateThrottle]

    def get(self, request):
        queryset = Order.objects.select_related("user").order_by("-created_at")
        status_filter = request.query_params.get("status")
        date_filter = request.query_params.get("date")
        search = request.query_params.get("search")

        if status_filter:
            normalized_status = Order.Status.CONFIRMED if status_filter == "processing" else status_filter
            valid_statuses = {choice[0] for choice in Order.Status.choices}
            if normalized_status in valid_statuses:
                queryset = queryset.filter(status=normalized_status)

        if date_filter:
            queryset = queryset.filter(created_at__date=date_filter)

        if search:
            normalized_search = search.strip()
            search_query = Q(user__email__icontains=normalized_search)
            if normalized_search.isdigit():
                search_query = search_query | Q(id=int(normalized_search))
            queryset = queryset.filter(search_query)

        paginator = AdminOrderPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = AdminOrderListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class AdminOrderDetailView(APIView):
    permission_classes = [IsAdminUser]
    throttle_classes = [AdminRateThrottle]

    def get(self, request, order_id):
        order = get_object_or_404(
            Order.objects.select_related("user", "shipping_address").prefetch_related(
                "items__product",
                "events__changed_by",
                "shipping_events",
            ),
            pk=order_id,
        )
        serializer = AdminOrderDetailSerializer(order)
        return Response(serializer.data)


class AdminOrderStatusUpdateView(APIView):
    permission_classes = [IsAdminUser]
    throttle_classes = [AdminRateThrottle]

    @transaction.atomic
    def post(self, request, order_id):
        order = get_object_or_404(Order.objects.select_for_update(), pk=order_id)
        serializer = AdminOrderStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        previous_status = order.status
        previous_payment_status = order.payment_status
        new_status = serializer.validated_data["status"]
        new_payment_status = serializer.validated_data.get("payment_status", order.payment_status)
        note = serializer.validated_data.get("note", "")

        if previous_status != new_status or previous_payment_status != new_payment_status:
            order.status = new_status
            order.payment_status = new_payment_status
            order.save(update_fields=["status", "payment_status", "updated_at"])
            OrderEvent.objects.create(
                order=order,
                previous_status=previous_status,
                new_status=new_status,
                previous_payment_status=previous_payment_status,
                new_payment_status=new_payment_status,
                changed_by=request.user,
                note=note,
            )
            if new_status == Order.Status.SHIPPED:
                send_order_email("order_shipped", order)
            elif new_status == Order.Status.DELIVERED:
                send_order_email("order_delivered", order)
            elif new_status == Order.Status.CANCELLED:
                send_order_email("order_cancelled", order)

        order = (
            Order.objects.select_related("user", "shipping_address")
            .prefetch_related("items__product", "events__changed_by", "shipping_events")
            .get(pk=order.pk)
        )
        return Response(AdminOrderDetailSerializer(order).data)


class AdminShipOrderView(APIView):
    permission_classes = [IsAdminUser]
    throttle_classes = [AdminRateThrottle]

    @transaction.atomic
    def post(self, request, order_id):
        order = get_object_or_404(Order.objects.select_for_update(), pk=order_id)
        serializer = AdminShipOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if order.status == Order.Status.DELIVERED:
            return Response({"detail": "Cannot ship a delivered order."}, status=400)
        if order.status != Order.Status.SHIPPED:
            order.status = Order.Status.SHIPPED
        if not order.tracking_id:
            order.tracking_id = f"{TRACKING_ID_PREFIX}-{uuid4().hex[:12].upper()}"
        shipping_provider = serializer.validated_data.get("shipping_provider")
        if shipping_provider:
            order.shipping_provider = shipping_provider
        elif not order.shipping_provider:
            order.shipping_provider = "Manual"
        if not order.shipped_at:
            order.shipped_at = timezone.now()
        order.save(update_fields=["status", "tracking_id", "shipping_provider", "shipped_at", "updated_at"])
        ShippingEvent.objects.create(
            order=order,
            event_type=ShippingEvent.EventType.CREATED,
            location=serializer.validated_data.get("location", ""),
        )
        send_order_email("order_shipped", order)
        order = (
            Order.objects.select_related("user", "shipping_address")
            .prefetch_related("items__product", "events__changed_by", "shipping_events")
            .get(pk=order.pk)
        )
        return Response(AdminOrderDetailSerializer(order).data)


class AdminDeliverOrderView(APIView):
    permission_classes = [IsAdminUser]
    throttle_classes = [AdminRateThrottle]

    @transaction.atomic
    def post(self, request, order_id):
        order = get_object_or_404(Order.objects.select_for_update(), pk=order_id)
        serializer = AdminDeliverOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if order.status == Order.Status.DELIVERED:
            return Response({"detail": "Order already delivered."}, status=200)
        if order.status != Order.Status.SHIPPED:
            return Response({"detail": "Only shipped orders can be marked delivered."}, status=400)
        order.status = Order.Status.DELIVERED
        order.delivered_at = timezone.now()
        order.save(update_fields=["status", "delivered_at", "updated_at"])
        ShippingEvent.objects.create(
            order=order,
            event_type=ShippingEvent.EventType.DELIVERED,
            location=serializer.validated_data.get("location", ""),
        )
        send_order_email("order_delivered", order)
        order = (
            Order.objects.select_related("user", "shipping_address")
            .prefetch_related("items__product", "events__changed_by", "shipping_events")
            .get(pk=order.pk)
        )
        return Response(AdminOrderDetailSerializer(order).data)
