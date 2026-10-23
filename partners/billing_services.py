from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from .models import (BillingPlan, CompanyBillingSettings, CompanyProfile, Invoice,
                     InvoiceLine, InvoicePaymentSubmission, SalesLedger)
from .services import audit, require_company_actor, require_owner


ZERO = Decimal('0.00')
POLICY_FIELDS = ('billing_mode', 'commission_rate', 'fixed_fee', 'subscription_period',
                 'minimum_monthly_fee', 'due_days', 'grace_days')


def rounded(value):
    return Decimal(value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def month_start(value):
    return value.replace(day=1)


def next_month(value):
    return date(value.year + (value.month == 12), value.month % 12 + 1, 1)


def parse_month(value=None):
    if not value:
        return month_start(month_start(timezone.localdate()) - timedelta(days=1))
    try:
        year, month = [int(part) for part in value.split('-')]
        return date(year, month, 1)
    except (ValueError, TypeError):
        raise ValidationError('Use a billing month in YYYY-MM format.')


def default_plan():
    plan = BillingPlan.objects.filter(is_default=True, is_active=True).first()
    plan = plan or BillingPlan.objects.filter(is_active=True).order_by('pk').first()
    if not plan:
        raise ValidationError('The owner must configure an active Partner billing plan.')
    return plan


def effective_policy(company):
    override = CompanyBillingSettings.objects.select_related('plan').filter(company=company).first()
    plan = override.plan if override else default_plan()
    values = {name:getattr(plan, name) for name in POLICY_FIELDS}
    if override:
        for name in POLICY_FIELDS:
            value = getattr(override, name)
            if value is not None and value != '':
                values[name] = value
    values['start'] = (override.subscription_start if override and override.subscription_start else
                       timezone.localdate(company.approved_at) if company.approved_at else timezone.localdate())
    values['pause_billing'] = bool(override and override.pause_billing)
    values['payment_instructions'] = plan.payment_instructions
    return values


def cycle_start(month, start):
    return date(month.year if month.month >= start.month else month.year - 1, start.month, 1)


def calculate(company, month, policy):
    end = next_month(month)
    sales = company.ledger_entries.filter(sale_date__gte=month, sale_date__lt=end).aggregate(total=Sum('amount'))['total'] or ZERO
    commission = rounded(sales * policy['commission_rate'] / 100)
    fixed_applied = policy['fixed_fee']
    cycle_commission = commission
    prior = ZERO
    if policy['subscription_period'] == 'yearly':
        start = cycle_start(month, policy['start'])
        if policy['billing_mode'] == 'higher':
            total = company.ledger_entries.filter(sale_date__gte=start, sale_date__lt=end).aggregate(total=Sum('amount'))['total'] or ZERO
            cycle_commission = rounded(total * policy['commission_rate'] / 100)
            prior = company.invoices.filter(month__gte=start, month__lt=month).aggregate(total=Sum('total_due'))['total'] or ZERO
        else:
            fixed_applied = policy['fixed_fee'] if month.month == policy['start'].month else ZERO
    if policy['billing_mode'] == 'commission':
        base = commission
        fixed_applied = ZERO
    elif policy['billing_mode'] == 'subscription':
        base = fixed_applied
    elif policy['billing_mode'] == 'higher':
        base = max(ZERO, max(fixed_applied, cycle_commission) - prior)
    else:
        raise ValidationError('Unknown billing mode.')
    return {'sales_total': rounded(sales), 'commission_amount': commission, 'fixed_fee_applied': rounded(fixed_applied),
            'cycle_commission': cycle_commission, 'prior_cycle_due': rounded(prior),
            'total_due': rounded(max(base, policy['minimum_monthly_fee']))}


def frozen_policy(invoice, policy):
    return {**policy, **{name:getattr(invoice, name) for name in POLICY_FIELDS if hasattr(invoice, name)},
            'start':invoice.subscription_start}


@transaction.atomic
def generate_invoice(company_id, month, *, actor=None):
    if actor is not None:
        require_owner(actor)
    month = month_start(month)
    if month > month_start(timezone.localdate()):
        raise ValidationError('Do not generate an invoice for a future month.')
    company = CompanyProfile.objects.select_for_update().get(pk=company_id)
    policy = effective_policy(company)
    if not company.approved_at or month < month_start(timezone.localdate(company.approved_at)) or policy['pause_billing']:
        return None, False
    # Annual hybrid billing charges the annual floor once, then only commission
    # above fees already invoiced in the same annual cycle. Backfill earlier
    # months first, so invoking a later month cannot omit or double-charge it.
    if policy['billing_mode'] == 'higher' and policy['subscription_period'] == 'yearly':
        cursor = max(cycle_start(month, policy['start']), month_start(timezone.localdate(company.approved_at)))
        while cursor < month:
            _generate_locked(company, cursor, policy, actor)
            cursor = next_month(cursor)
    return _generate_locked(company, month, policy, actor)


def _generate_locked(company, month, policy, actor):
    invoice = Invoice.objects.select_for_update().filter(company=company, month=month).first()
    if invoice and invoice.status == 'paid':
        return invoice, False
    created = invoice is None
    if invoice:
        policy = frozen_policy(invoice, policy)
    totals = calculate(company, month, policy)
    if not invoice:
        due_date = next_month(month) - timedelta(days=1) + timedelta(days=policy['due_days'])
        invoice = Invoice(company=company, number=f'PI-{month:%Y%m}-{company.pk}', month=month,
            **{name:policy[name] for name in POLICY_FIELDS if name not in ('due_days', 'grace_days')},
            subscription_start=policy['start'],
            due_date=due_date, suspend_on=due_date + timedelta(days=max(1, policy['grace_days'])),
            payment_instructions=policy['payment_instructions'])
    changed = created or any(getattr(invoice, name) != value for name, value in totals.items())
    for name, value in totals.items():
        setattr(invoice, name, value)
    invoice.status = 'overdue' if invoice.due_date < timezone.localdate() else 'unpaid'
    # A zero amount needs no transfer. It remains an issued snapshot; later
    # changes are flagged for reconciliation like any other settled invoice.
    if invoice.total_due == 0:
        invoice.status = 'paid'
        invoice.paid_at = invoice.paid_at or timezone.now()
    if changed:
        invoice.save()
        audit(company, actor, 'invoice.generate' if created else 'invoice.refresh', invoice,
              amount=str(invoice.total_due), month=month.isoformat())
    for ledger in company.ledger_entries.filter(sale_date__gte=month, sale_date__lt=next_month(month)):
        InvoiceLine.objects.update_or_create(invoice=invoice, ledger=ledger, defaults={'amount':ledger.amount})
    return invoice, created


def refresh_ledger_invoice(ledger):
    """Called under the company's lock by ledger writers; paid invoices freeze."""
    invoice = Invoice.objects.filter(company=ledger.company, month=month_start(ledger.sale_date)).first()
    if not invoice:
        return
    if invoice.status == 'paid':
        ledger.needs_review = True
        ledger.save(update_fields=['needs_review'])
        audit(ledger.company, None, 'invoice.reconciliation_required', ledger,
              reason='A sale changed after this billing month was settled. Owner reconciliation is required.')
        return
    policy = effective_policy(ledger.company)
    if policy['billing_mode'] == 'higher' and policy['subscription_period'] == 'yearly':
        start = cycle_start(invoice.month, policy['start'])
        end = date(start.year + 1, start.month, 1)
        months = list(ledger.company.invoices.filter(month__gte=invoice.month,
            month__lt=end
        ).order_by('month').values_list('month', flat=True))
    else:
        months = [invoice.month]
    for month in months:
        _generate_locked(ledger.company, month, policy, None)


@transaction.atomic
def submit_invoice_payment(invoice_id, *, actor, reference, screenshot=None):
    company_id = Invoice.objects.values_list('company_id', flat=True).get(pk=invoice_id)
    company = CompanyProfile.objects.select_for_update().get(pk=company_id)
    require_company_actor(company, actor)
    invoice = Invoice.objects.select_for_update().get(pk=invoice_id)
    if invoice.status == 'paid':
        raise ValidationError('This invoice is already paid.')
    reference = reference.strip()
    if not reference:
        raise ValidationError('A payment reference or transaction ID is required.')
    submission, created = InvoicePaymentSubmission.objects.get_or_create(invoice=invoice, reference=reference,
        defaults={'screenshot':screenshot or '', 'submitted_by':actor})
    if created:
        audit(company, actor, 'invoice.payment_submitted', submission)
    return submission


@transaction.atomic
def mark_invoice_paid(invoice_id, *, actor, reason):
    require_owner(actor)
    if not reason.strip():
        raise ValidationError('Explain how the invoice payment was verified.')
    company_id = Invoice.objects.values_list('company_id', flat=True).get(pk=invoice_id)
    company = CompanyProfile.objects.select_for_update().get(pk=company_id)
    invoice = Invoice.objects.select_for_update().get(pk=invoice_id)
    if invoice.status == 'paid':
        return invoice
    invoice.status = 'paid'
    invoice.paid_at = timezone.now()
    invoice.save(update_fields=['status', 'paid_at', 'updated_at'])
    latest = invoice.payment_submissions.first()
    if latest:
        latest.reviewed_by = actor
        latest.reviewed_at = timezone.now()
        latest.save(update_fields=['reviewed_by', 'reviewed_at'])
    audit(company, actor, 'invoice.paid', invoice, reason=reason, amount=str(invoice.total_due))
    return invoice


def refresh_overdue_statuses():
    ids = list(Invoice.objects.filter(status='unpaid', due_date__lt=timezone.localdate()).values_list('pk', flat=True))
    for pk in ids:
        with transaction.atomic():
            company_id = Invoice.objects.values_list('company_id', flat=True).get(pk=pk)
            company = CompanyProfile.objects.select_for_update().get(pk=company_id)
            invoice = Invoice.objects.select_for_update().get(pk=pk)
            if invoice.status == 'unpaid':
                invoice.status = 'overdue'
                invoice.save(update_fields=['status', 'updated_at'])
                audit(company, None, 'invoice.overdue', invoice, reason='Invoice due date passed.')
    return len(ids)
