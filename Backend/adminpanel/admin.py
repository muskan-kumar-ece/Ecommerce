from django.contrib import admin
from django.db.models import DecimalField, F, Sum, Value
from django.db.models.functions import Coalesce
from django.utils.dateparse import parse_date
from django.utils import timezone

from orders.models import Order
from products.models import Inventory


def _dashboard_date_range(request):
    end_date = parse_date(request.GET.get("end_date", "")) or timezone.localdate()
    start_date = parse_date(request.GET.get("start_date", "")) or (end_date - timezone.timedelta(days=30))
    if start_date > end_date:
        start_date, end_date = end_date, start_date
    return start_date, end_date


def _dashboard_context(request):
    start_date, end_date = _dashboard_date_range(request)
    order_queryset = Order.objects.filter(created_at__date__gte=start_date, created_at__date__lte=end_date)
    revenue = order_queryset.filter(payment_status=Order.PaymentStatus.PAID).aggregate(
        total=Coalesce(Sum("total_amount"), Value(0, output_field=DecimalField(max_digits=12, decimal_places=2)))
    )["total"]
    low_stock_queryset = (
        Inventory.objects.select_related("product")
        .annotate(available=F("quantity") - F("reserved_quantity"))
        .filter(available__lte=F("reorder_level"))
        .order_by("available")
    )
    return {
        "dashboard_total_orders": order_queryset.count(),
        "dashboard_pending_orders": order_queryset.filter(status=Order.Status.PENDING).count(),
        "dashboard_revenue": revenue,
        "dashboard_start_date": start_date.isoformat(),
        "dashboard_end_date": end_date.isoformat(),
        "dashboard_low_stock_items": low_stock_queryset[:5],
        "dashboard_low_stock_count": low_stock_queryset.count(),
    }


_default_admin_index = admin.site.index


def _custom_admin_index(request, extra_context=None):
    context = extra_context or {}
    context.update(_dashboard_context(request))
    return _default_admin_index(request, extra_context=context)


admin.site.site_header = "Ecommerce Enterprise Admin"
admin.site.site_title = "Ecommerce Admin"
admin.site.index_title = "Operations Dashboard"
admin.site.index_template = "adminpanel/index.html"
admin.site.index = _custom_admin_index
