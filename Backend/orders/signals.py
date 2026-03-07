from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Cart, CartItem, Order
from .realtime import handle_order_update_event


@receiver(post_save, sender=Order)
def broadcast_order_update(sender, instance, created, update_fields, **kwargs):
    if not created and update_fields is not None and "status" not in update_fields:
        return
    handle_order_update_event(instance)


@receiver(post_save, sender=CartItem)
@receiver(post_delete, sender=CartItem)
def sync_cart_updated_at(sender, instance, **kwargs):
    Cart.objects.filter(pk=instance.cart_id).update(updated_at=timezone.now())
