from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from partners.billing_services import generate_invoice, parse_month, refresh_overdue_statuses
from partners.models import CompanyProfile


class Command(BaseCommand):
    help = 'Generate or refresh one invoice per company/month. Defaults to the previous calendar month.'

    def add_arguments(self, parser):
        parser.add_argument('--month', help='YYYY-MM; defaults to previous month')
        parser.add_argument('--company', type=int, help='Optional company primary key')

    def handle(self, *args, **options):
        try:
            month = parse_month(options.get('month'))
        except ValidationError as error:
            raise CommandError('; '.join(error.messages))
        companies = CompanyProfile.objects.filter(approved_at__isnull=False).order_by('pk')
        if options.get('company'):
            companies = companies.filter(pk=options['company'])
        created = 0
        for company in companies.iterator():
            try:
                invoice, new = generate_invoice(company.pk, month)
            except ValidationError as error:
                raise CommandError(f'{company.name}: {"; ".join(error.messages)}')
            if invoice:
                self.stdout.write(f'{invoice.number}: {invoice.total_due} ({"created" if new else "retained/refreshed"})')
                created += bool(new)
        refresh_overdue_statuses()
        self.stdout.write(self.style.SUCCESS(f'{created} new invoice(s); no duplicate company/month invoices.'))
