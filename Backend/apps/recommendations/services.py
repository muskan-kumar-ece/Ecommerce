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
    category_id = Product.objects.filter(id=product_id).values_list("category_id", flat=True).first()
    if category_id is None:
        return []

    return list(
        _with_popularity(
            Product.objects.filter(category_id=category_id, is_active=True)
            .exclude(id=product_id)
            .select_related("category")
        )
        .order_by("-order_count", "-total_quantity", "-created_at")[:10]
    )


def get_user_recommendations(user_id):
    purchased_rows = list(
        OrderItem.objects.filter(
            order__user_id=user_id,
            order__payment_status=Order.PaymentStatus.PAID,
        )
        .values_list("product_id", "product__category_id")
        .distinct()
    )
    if not purchased_rows:
        return get_trending_products()

    purchased_product_ids = {product_id for product_id, _ in purchased_rows}
    purchased_category_ids = {category_id for _, category_id in purchased_rows}

    recommendations = list(
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

    if recommendations:
        return recommendations
    return get_trending_products()


def get_trending_products():
    return list(
        _with_popularity(
            Product.objects.filter(is_active=True).select_related("category")
        )
        .filter(order_count__gt=0)
        .order_by("-order_count", "-total_quantity", "-created_at")
        [:10]
    )
