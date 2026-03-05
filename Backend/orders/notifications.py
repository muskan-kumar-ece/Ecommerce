from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from .models import EmailEvent, Order

EMAIL_SUBJECTS = {
    EmailEvent.EmailType.ORDER_CONFIRMED: "Your order is confirmed",
    EmailEvent.EmailType.PAYMENT_SUCCESS: "Payment received successfully",
    EmailEvent.EmailType.ORDER_SHIPPED: "Your order has been shipped",
    EmailEvent.EmailType.ORDER_DELIVERED: "Your order has been delivered",
    EmailEvent.EmailType.ORDER_CANCELLED: "Your order was cancelled",
    EmailEvent.EmailType.REFUND_PROCESSED: "Your refund has been processed",
}


def _build_order_email_message(email_type: str, order: Order) -> str:
    items = "\n".join(
        f"- {item.product.name} x {item.quantity} @ ₹{item.price}"
        for item in order.items.select_related("product").all()
    )
    status_label = order.get_status_display()
    support_email = settings.SUPPORT_EMAIL
    heading = EMAIL_SUBJECTS[email_type]
    return (
        f"{heading}\n\n"
        f"Order ID: {order.id}\n"
        f"Order Status: {status_label}\n"
        f"Total Amount: ₹{order.total_amount}\n\n"
        f"Products:\n{items or '- No items found'}\n\n"
        f"If you need help, contact us at {support_email}."
    )


def send_order_email(email_type: str, order: Order) -> bool:
    if email_type not in EMAIL_SUBJECTS:
        raise ValueError("Unsupported email type.")

    with transaction.atomic():
        email_event, _ = EmailEvent.objects.select_for_update().get_or_create(
            order=order,
            email_type=email_type,
        )
        if email_event.status == EmailEvent.Status.SENT:
            return False

        try:
            send_mail(
                subject=EMAIL_SUBJECTS[email_type],
                message=_build_order_email_message(email_type=email_type, order=order),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[order.user.email],
                fail_silently=False,
            )
        except Exception:
            email_event.status = EmailEvent.Status.FAILED
            email_event.sent_at = None
            email_event.save(update_fields=["status", "sent_at", "updated_at"])
            return False

        email_event.status = EmailEvent.Status.SENT
        email_event.sent_at = timezone.now()
        email_event.save(update_fields=["status", "sent_at", "updated_at"])
        return True
