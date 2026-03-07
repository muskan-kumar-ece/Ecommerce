from django.core.management.base import BaseCommand

from orders.cart_recovery import send_abandoned_cart_reminders


class Command(BaseCommand):
    help = "Send abandoned cart reminder emails for carts inactive for 2 hours."

    def handle(self, *args, **options):
        sent_count = send_abandoned_cart_reminders()
        self.stdout.write(self.style.SUCCESS(f"Sent {sent_count} abandoned cart reminder email(s)."))
