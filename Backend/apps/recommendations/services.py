from django.db.models import Count, Q, Sum
from django.db.models.functions import Coalesce

from orders.models import Order, OrderItem
from products.models import Product


def _with_popularity(queryset):
    paid_order_filter = Q(order_items__order__payment_status=Order.PaymentStatus.PAID)
    return queryset.annotate(
        order_count=Count("order_items__order", filter=paid_order_filter, distinct=True),
        total_quantity=Coalesce(Sum("order_items__quantity", filter=paid_order_filter), 0),
    )


def get_similar_products(product_id):
    base_product = Product.objects.filter(id=product_id).values("category_id").first()
    if not base_product:
        return Product.objects.none()

    return (
        _with_popularity(
            Product.objects.filter(category_id=base_product["category_id"], is_active=True)
            .exclude(id=product_id)
            .select_related("category")
        )
        .order_by("-order_count", "-total_quantity", "-created_at")[:10]
    )


def get_user_recommendations(user_id):
    paid_order_items = OrderItem.objects.filter(
        order__user_id=user_id,
        order__payment_status=Order.PaymentStatus.PAID,
    )
    purchased_product_ids = paid_order_items.values_list("product_id", flat=True)
    purchased_category_ids = paid_order_items.values_list("product__category_id", flat=True)

    queryset = (
        _with_popularity(
            Product.objects.filter(
                is_active=True,
                category_id__in=purchased_category_ids,
            )
            .exclude(id__in=purchased_product_ids)
            .select_related("category")
        )
        .order_by("-order_count", "-total_quantity", "-created_at")[:10]
    )

    if queryset:
        return queryset
    return get_trending_products()


def get_trending_products():
    return (
        _with_popularity(
            Product.objects.filter(
                is_active=True,
                order_items__order__payment_status=Order.PaymentStatus.PAID,
            ).select_related("category")
        )
        .filter(order_count__gt=0)
        .order_by("-order_count", "-total_quantity", "-created_at")
        .distinct()[:10]
    )
