from django.db import transaction
from django.utils import timezone

from .models import PriceWatch
from .notifications import send_price_drop_email


def add_price_watch(user, product):
    watch, created = PriceWatch.objects.get_or_create(
        user=user,
        product=product,
        defaults={"last_price": product.price},
    )
    if not created and watch.last_price != product.price:
        watch.last_price = product.price
        watch.save(update_fields=["last_price", "updated_at"])
    return watch, created


def check_price_drops():
    watches = PriceWatch.objects.select_related("user", "product").all()
    checked_count = 0
    notified_count = 0
    for watch in watches:
        checked_count += 1
        new_price = watch.product.price
        old_price = watch.last_price
        if new_price < old_price:
            with transaction.atomic():
                watch_for_update = PriceWatch.objects.select_for_update().get(pk=watch.pk)
                sent = send_price_drop_email(watch_for_update, old_price=watch_for_update.last_price, new_price=new_price)
                watch_for_update.last_price = new_price
                if sent:
                    watch_for_update.last_notified_at = timezone.now()
                    notified_count += 1
                watch_for_update.save(update_fields=["last_price", "last_notified_at", "updated_at"])
        elif new_price != old_price:
            watch.last_price = new_price
            watch.save(update_fields=["last_price", "updated_at"])
    return {"checked_count": checked_count, "notified_count": notified_count}
