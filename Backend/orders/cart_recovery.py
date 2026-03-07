from datetime import timedelta

from django.db.models import F, Q
from django.utils import timezone

from .models import Cart
from .notifications import send_abandoned_cart_email

ABANDONED_CART_INACTIVITY_HOURS = 2


def get_abandoned_carts_queryset(cutoff_time=None):
    if cutoff_time is None:
        cutoff_time = timezone.now() - timedelta(hours=ABANDONED_CART_INACTIVITY_HOURS)

    return (
        Cart.objects.select_related("user")
        .prefetch_related("items__product")
        .filter(is_active=True, updated_at__lte=cutoff_time)
        .filter(items__isnull=False)
        .filter(
            Q(abandoned_cart_reminder_sent_at__isnull=True)
            | Q(abandoned_cart_reminder_sent_at__lt=F("updated_at"))
        )
        .distinct()
    )


def send_abandoned_cart_reminders(cutoff_time=None):
    sent_count = 0
    for cart in get_abandoned_carts_queryset(cutoff_time=cutoff_time):
        if send_abandoned_cart_email(cart):
            cart.abandoned_cart_reminder_sent_at = timezone.now()
            cart.save(update_fields=["abandoned_cart_reminder_sent_at"])
            sent_count += 1
    return sent_count
