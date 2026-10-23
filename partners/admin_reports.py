import csv

from django.db.models import Sum
from django.http import HttpResponse
from django.template.response import TemplateResponse

from .models import CompanyProfile, Invoice, SalesLedger
from .services import require_owner


def csv_value(value):
    text = str(value if value is not None else '')
    return "'" + text if text.startswith(('=', '+', '-', '@', '\t', '\r', '\n')) else text


def export_ledger(request):
    require_owner(request.user)
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="partner-ledger.csv"'
    writer = csv.writer(response)
    writer.writerow(['ID', 'Company', 'Date', 'Source', 'Order/reference', 'Original amount', 'Current amount', 'Buyer-confirmed', 'Needs review'])
    for entry in SalesLedger.objects.select_related('company', 'order').iterator():
        writer.writerow([csv_value(value) for value in [entry.pk, entry.company.name, entry.sale_date,
            entry.source, entry.order.number if entry.order_id else entry.reference,
            entry.original_amount, entry.amount, bool(entry.buyer_confirmed_at), entry.needs_review]])
    response['X-Content-Type-Options'] = 'nosniff'
    return response


def export_invoices(request):
    require_owner(request.user)
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="partner-invoices.csv"'
    writer = csv.writer(response)
    writer.writerow(['Invoice', 'Company', 'Month', 'Sales', 'Calculated commission', 'Total due', 'Due date', 'Status'])
    for invoice in Invoice.objects.select_related('company').iterator():
        writer.writerow([csv_value(value) for value in [invoice.number, invoice.company.name, invoice.month,
            invoice.sales_total, invoice.commission_amount, invoice.total_due, invoice.due_date, invoice.payment_state]])
    response['X-Content-Type-Options'] = 'nosniff'
    return response


def report(request, admin_site):
    require_owner(request.user)
    monthly = Invoice.objects.order_by('month').values('month').annotate(
        commission=Sum('commission_amount'), fees=Sum('total_due'))
    outstanding = Invoice.objects.exclude(status='paid').aggregate(total=Sum('total_due'))['total'] or 0
    top = CompanyProfile.objects.annotate(total_sales=Sum('ledger_entries__amount')).order_by('-total_sales', 'pk')[:10]
    return TemplateResponse(request, 'admin/partners/billing_report.html', {
        **admin_site.each_context(request), 'title':'Agro Partners billing report', 'monthly':monthly,
        'outstanding':outstanding, 'top_companies':top,
        'review_entries':SalesLedger.objects.filter(needs_review=True).select_related('company', 'order')[:50],
        'manual_entries':SalesLedger.objects.filter(source='manual').select_related('company')[:50],
    })
