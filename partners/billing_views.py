from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods

from .billing_forms import InvoicePaymentForm
from .billing_services import calculate, effective_policy, month_start, submit_invoice_payment
from .models import Invoice, InvoicePaymentSubmission
from .services import ROLE_NAME
from .views import company_required


@company_required
@require_GET
def billing(request):
    company = request.partner_company
    policy = effective_policy(company)
    month = month_start(timezone.localdate())
    totals = calculate(company, month, policy)
    overdue = company.invoices.exclude(status='paid').filter(due_date__lt=timezone.localdate())
    return render(request, 'partners/billing.html', {'company':company, 'policy':policy, 'totals':totals,
        'invoices':company.invoices.all(), 'overdue':overdue, 'month':month,
        'public_visible':type(company).objects.public().filter(pk=company.pk).exists()})


@company_required
@require_http_methods(['GET', 'POST'])
def invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, company=request.partner_company)
    form = InvoicePaymentForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        try:
            submit_invoice_payment(invoice.pk, actor=request.user, reference=form.cleaned_data['reference'],
                                   screenshot=form.cleaned_data['screenshot'])
        except ValidationError as error:
            form.add_error(None, error)
        else:
            messages.success(request, 'Payment reference submitted. The owner will verify it; this does not mark the invoice paid.')
            return redirect('partners:invoice_detail', pk=pk)
    return render(request, 'partners/invoice.html', {'company':request.partner_company, 'invoice':invoice, 'form':form})


@never_cache
@login_required
@require_GET
def payment_proof(request, pk):
    proof = get_object_or_404(InvoicePaymentSubmission.objects.select_related('invoice__company'), pk=pk)
    owner = request.user.is_active and request.user.is_staff and request.user.is_superuser
    company_user = proof.invoice.company.user_id == request.user.pk and request.user.groups.filter(name=ROLE_NAME).exists()
    if not owner and not company_user:
        raise PermissionDenied
    if not proof.screenshot:
        from django.http import Http404
        raise Http404
    response = FileResponse(proof.screenshot.open('rb'), as_attachment=True)
    response['X-Content-Type-Options'] = 'nosniff'
    response['Content-Security-Policy'] = 'sandbox'
    return response
