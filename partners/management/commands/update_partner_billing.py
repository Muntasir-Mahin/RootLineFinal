from django.core.management.base import BaseCommand

from partners.billing_services import refresh_overdue_statuses


class Command(BaseCommand):
    help = 'Audit overdue invoice status changes. Store visibility also checks due/grace dates live.'

    def handle(self, *args, **options):
        self.stdout.write(f'{refresh_overdue_statuses()} overdue invoice status(es) checked.')
