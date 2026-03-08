import logging
from smtplib import SMTPException

from django.conf import settings
from django.core.mail import BadHeaderError
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.template.loader import render_to_string
from django.utils import timezone

from .models import Cart, EmailEvent, Order

logger = logging.getLogger(__name__)

EMAIL_SUBJECTS = {
    EmailEvent.EmailType.ORDER_CONFIRMED: "Your order is confirmed",
    EmailEvent.EmailType.PAYMENT_SUCCESS: "Payment received successfully",
    EmailEvent.EmailType.ORDER_SHIPPED: "Your order has been shipped",
    EmailEvent.EmailType.ORDER_DELIVERED: "Your order has been delivered",
    EmailEvent.EmailType.ORDER_CANCELLED: "Your order was cancelled",
    EmailEvent.EmailType.REFUND_PROCESSED: "Your refund has been processed",
}
ABANDONED_CART_EMAIL_SUBJECT = "You left items in your cart"


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
        raise ValueError(
            f"Unsupported email type: {email_type}. Valid types are: {', '.join(EMAIL_SUBJECTS.keys())}."
        )

    with transaction.atomic():
        try:
            email_event, _ = EmailEvent.objects.get_or_create(
                order=order,
                email_type=email_type,
            )
        except IntegrityError:
            email_event = EmailEvent.objects.get(
                order=order,
                email_type=email_type,
            )
        email_event = EmailEvent.objects.select_for_update().get(pk=email_event.pk)
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
        except (SMTPException, BadHeaderError, OSError) as exc:
            logger.error(
                "Failed to send order email type=%s order_id=%s: %s",
                email_type,
                order.id,
                exc,
            )
            email_event.status = EmailEvent.Status.FAILED
            email_event.sent_at = None
            email_event.save(update_fields=["status", "sent_at", "updated_at"])
            return False

        email_event.status = EmailEvent.Status.SENT
        email_event.sent_at = timezone.now()
        email_event.save(update_fields=["status", "sent_at", "updated_at"])
        return True


def _build_abandoned_cart_email_message(cart: Cart) -> str:
    cart_items = cart.items.select_related("product").all()
    return render_to_string(
        "orders/emails/abandoned_cart_reminder.txt",
        {
            "user_name": cart.user.name or cart.user.email,
            "cart_items": cart_items,
            "cart_url": f"{settings.FRONTEND_APP_URL}/cart",
            "support_email": settings.SUPPORT_EMAIL,
        },
    ).strip()


def send_abandoned_cart_email(cart: Cart) -> bool:
    if not cart.user.email:
        return False

    try:
        send_mail(
            subject=ABANDONED_CART_EMAIL_SUBJECT,
            message=_build_abandoned_cart_email_message(cart),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[cart.user.email],
            fail_silently=False,
        )
    except (SMTPException, BadHeaderError, OSError) as exc:
        logger.error(
            "Failed to send abandoned cart email cart_id=%s user_id=%s: %s",
            cart.id,
            cart.user_id,
            exc,
        )
        return False
    return True
