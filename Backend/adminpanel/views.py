from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, DecimalField, Q, Sum, Value
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
        seven_days_ago = today - timedelta(days=6)

        metrics = Order.objects.aggregate(
            total_revenue=Coalesce(
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
                        created_at__date__gte=seven_days_ago,
                    ),
                ),
                Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            ),
        )

        total_orders = metrics["total_orders"]
        refund_rate_percent = (metrics["total_refunded_orders"] / total_orders * 100.0) if total_orders else 0.0

        serializer = AnalyticsSummarySerializer(
            {
                **metrics,
                "refund_rate_percent": round(refund_rate_percent, 2),
            }
        )
        return Response(serializer.data)
