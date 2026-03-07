from django.core.management.base import BaseCommand

from apps.price_watch.services import check_price_drops


class Command(BaseCommand):
    help = "Check price watch list and send email alerts when product prices drop."

    def handle(self, *args, **options):
        result = check_price_drops()
        self.stdout.write(
            self.style.SUCCESS(
                f"Checked {result['checked_count']} watches and sent {result['notified_count']} notifications."
            )
        )
