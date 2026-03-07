from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Order
from .realtime import handle_order_update_event


@receiver(post_save, sender=Order)
def broadcast_order_update(sender, instance, created, update_fields, **kwargs):
    if not created and update_fields is not None and "status" not in update_fields:
        return
    handle_order_update_event(instance)
