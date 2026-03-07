from decimal import Decimal

from django.db import transaction

from .models import VendorOrder


@transaction.atomic
def create_vendor_orders_for_order(order):
    vendor_totals = {}
    order_items = order.items.select_related("product__vendor_listing__vendor")
    for item in order_items:
        vendor_listing = getattr(item.product, "vendor_listing", None)
        if not vendor_listing:
            continue
        vendor_id = vendor_listing.vendor_id
        if vendor_id not in vendor_totals:
            vendor_totals[vendor_id] = {"vendor": vendor_listing.vendor, "total": Decimal("0.00")}
        vendor_totals[vendor_id]["total"] += item.price * item.quantity

    for vendor_data in vendor_totals.values():
        total = vendor_data["total"].quantize(Decimal("0.01"))
        commission = (total * vendor_data["vendor"].commission_rate / Decimal("100")).quantize(Decimal("0.01"))
        earnings = (total - commission).quantize(Decimal("0.01"))
        VendorOrder.objects.update_or_create(
            vendor=vendor_data["vendor"],
            order=order,
            defaults={
                "total_amount": total,
                "commission_amount": commission,
                "earnings_amount": earnings,
            },
        )
