from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, DecimalField, F, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.models import Order

from .serializers import AnalyticsSummarySerializer


class AnalyticsSummaryView(APIView):
    permission_classes = [IsAdminUser]

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

        serializer = AnalyticsSummarySerializer(
            {
                **metrics,
                "total_revenue": metrics["net_revenue"],
                "refund_rate_percent": round(refund_rate_percent, 2),
            }
        )
        return Response(serializer.data)
