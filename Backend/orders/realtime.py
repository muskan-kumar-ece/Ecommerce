from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

ORDER_STATUS_LABELS = {
    "pending": "Placed",
    "confirmed": "Packed",
    "shipped": "Shipped",
    "out_for_delivery": "Out for Delivery",
    "delivered": "Delivered",
}


def get_order_updates_group_name(user_id, order_id):
    return f"order_updates_{user_id}_{order_id}"


def get_order_status_label(status):
    return ORDER_STATUS_LABELS.get(status, status.replace("_", " ").title())


def handle_order_update_event(order):
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return

    async_to_sync(channel_layer.group_send)(
        get_order_updates_group_name(order.user_id, order.id),
        {
            "type": "order.update",
            "order_id": order.id,
            "status": order.status,
            "status_label": get_order_status_label(order.status),
            "updated_at": order.updated_at.isoformat(),
        },
    )
