import logging
from smtplib import SMTPException

from django.conf import settings
from django.core.mail import BadHeaderError, send_mail
from django.template.loader import render_to_string

from .models import PriceWatch

logger = logging.getLogger(__name__)

PRICE_DROP_SUBJECT = "Price drop alert for your watchlist product"


def _build_price_drop_message(price_watch: PriceWatch, old_price, new_price):
    return render_to_string(
        "price_watch/emails/price_drop_alert.txt",
        {
            "user_name": price_watch.user.name or price_watch.user.email,
            "product_name": price_watch.product.name,
            "old_price": old_price,
            "new_price": new_price,
            "product_url": f"{settings.FRONTEND_APP_URL}/products/{price_watch.product.slug}",
            "support_email": settings.SUPPORT_EMAIL,
        },
    ).strip()


def send_price_drop_email(price_watch: PriceWatch, old_price, new_price):
    if not price_watch.user.email:
        return False
    try:
        send_mail(
            subject=PRICE_DROP_SUBJECT,
            message=_build_price_drop_message(price_watch, old_price, new_price),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[price_watch.user.email],
            fail_silently=False,
        )
    except (SMTPException, BadHeaderError, OSError) as exc:
        logger.error(
            "Failed to send price drop email product_id=%s user_id=%s: %s",
            price_watch.product_id,
            price_watch.user_id,
            exc,
        )
        return False
    return True
