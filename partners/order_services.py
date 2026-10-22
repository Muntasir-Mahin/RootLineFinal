from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from .models import CompanyProduct, CompanyProfile, LedgerAdjustment, OrderRequest, SalesLedger
from .services import audit, notify, require_company_actor, require_owner


def money(value):
    value = Decimal(value)
    if not value.is_finite() or value < 0 or value > Decimal('999999999999.99'):
        raise ValidationError('Enter a valid non-negative amount within the supported limit.')
    return value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def require_buyer(order, actor):
    if not actor.is_authenticated or not actor.is_active or order.buyer_id != actor.pk:
        raise PermissionDenied('This Order Request does not belong to you.')


@transaction.atomic
def request_order(product_id, *, buyer, data):
    if not buyer.is_authenticated or not buyer.is_active:
        raise PermissionDenied
    product = CompanyProduct.objects.select_related('company').get(pk=product_id)
    company = CompanyProfile.objects.select_for_update().get(pk=product.company_id)
    if not CompanyProfile.objects.public().filter(pk=company.pk).exists() or not product.is_active:
        raise ValidationError('This Partner Store or product is unavailable.')
    if company.user_id == buyer.pk:
        raise ValidationError('A Partner Company cannot order its own products.')
    quantity = Decimal(data['quantity'])
    if quantity <= 0 or quantity > product.stock_quantity:
        raise ValidationError('The requested quantity exceeds the available stock.')
    amount = money(product.sale_price * quantity)
    if amount <= 0:
        raise ValidationError('The order total must be positive.')
    order = OrderRequest.objects.create(company=company, buyer=buyer, product=product,
        product_name=product.name, unit=product.unit, unit_price=product.sale_price, quantity=quantity,
        expected_amount=amount, phone=data['phone'], delivery_address=data['delivery_address'], note=data.get('note', ''))
    audit(company, buyer, 'order.request', order, amount=str(amount))
    notify(company.email, f'New RootLine Order Request {order.number}',
           f'{order.number}: {quantity} {product.get_unit_display()} of {product.name}.\n'
           'Sign in to your Partner Company dashboard to accept or decline. Buyer phone is shown only after acceptance.')
    return order


@transaction.atomic
def company_order_decision(order_id, *, actor, decision, reason=''):
    company_id = OrderRequest.objects.values_list('company_id', flat=True).get(pk=order_id)
    company = CompanyProfile.objects.select_for_update().select_related('user').get(pk=company_id)
    require_company_actor(company, actor, publishing=decision == 'accept')
    order = OrderRequest.objects.select_for_update().select_related('buyer', 'product').get(pk=order_id, company=company)
    if order.status != 'requested':
        raise ValidationError('Only a requested order can be accepted or declined.')
    if decision == 'accept':
        changed = CompanyProduct.objects.filter(pk=order.product_id, is_active=True,
            stock_quantity__gte=order.quantity).update(stock_quantity=F('stock_quantity') - order.quantity)
        if not changed:
            raise ValidationError('The product is unavailable or has insufficient stock.')
        order.status = 'accepted'
    elif decision == 'decline':
        order.status = 'declined'
    else:
        raise ValidationError('Unknown order decision.')
    order.decision_reason = reason.strip()[:3000]
    order.save(update_fields=['status', 'decision_reason', 'updated_at'])
    audit(company, actor, f'order.{decision}', order, reason=reason)
    notify(order.buyer.email, f'RootLine {order.number}: {order.status}',
           f'Your Order Request {order.number} was {order.status}.\n{reason}\n'
           'View your Partner Order Requests while signed in. Payment and delivery are arranged directly with the company.')
    return order


@transaction.atomic
def cancel_order(order_id, *, buyer):
    company_id = OrderRequest.objects.values_list('company_id', flat=True).get(pk=order_id)
    company = CompanyProfile.objects.select_for_update().get(pk=company_id)
    order = OrderRequest.objects.select_for_update().get(pk=order_id)
    require_buyer(order, buyer)
    if order.status not in ('requested', 'accepted'):
        raise ValidationError('This order can no longer be cancelled.')
    if order.status == 'accepted':
        CompanyProduct.objects.filter(pk=order.product_id).update(stock_quantity=F('stock_quantity') + order.quantity)
    order.status = 'cancelled'
    order.save(update_fields=['status', 'updated_at'])
    audit(company, buyer, 'order.cancel', order)
    return order


@transaction.atomic
def complete_order(order_id, *, actor, final_amount, reason=''):
    company_id = OrderRequest.objects.values_list('company_id', flat=True).get(pk=order_id)
    company = CompanyProfile.objects.select_for_update().get(pk=company_id)
    require_company_actor(company, actor)
    order = OrderRequest.objects.select_for_update().get(pk=order_id)
    if order.status == 'completed':
        return order.ledger_entry
    if order.status != 'accepted':
        raise ValidationError('Accept this Order Request before recording a completed sale.')
    amount = money(final_amount)
    if amount <= 0:
        raise ValidationError('The final sold amount must be positive.')
    if amount != order.expected_amount and not reason.strip():
        raise ValidationError('Explain why the final sold amount differs from the requested total.')
    order.status = 'completed'
    order.completed_at = timezone.now()
    order.final_amount = amount
    order.amount_change_reason = reason.strip()
    order.save(update_fields=['status', 'completed_at', 'final_amount', 'amount_change_reason', 'updated_at'])
    ledger = SalesLedger.objects.create(company=company, order=order, source='order',
        original_amount=amount, amount=amount, sale_date=timezone.localdate(), reported_by=actor)
    audit(company, actor, 'order.complete', order, reason=reason, amount=str(amount))
    return ledger


@transaction.atomic
def buyer_evidence(order_id, *, buyer, confirm=False, reason='', claimed_amount=None):
    company_id = OrderRequest.objects.values_list('company_id', flat=True).get(pk=order_id)
    company = CompanyProfile.objects.select_for_update().get(pk=company_id)
    order = OrderRequest.objects.select_for_update().get(pk=order_id)
    require_buyer(order, buyer)
    if order.status != 'completed':
        raise ValidationError('Only a completed order can be confirmed or disputed.')
    ledger = SalesLedger.objects.select_for_update().get(order=order)
    if confirm:
        if order.buyer_dispute:
            raise ValidationError('The owner must review this amount dispute before confirmation.')
        order.buyer_confirmed_at = ledger.buyer_confirmed_at = timezone.now()
    else:
        if not reason.strip():
            raise ValidationError('Explain the amount discrepancy for the owner.')
        order.buyer_dispute = reason.strip()
        order.buyer_claimed_amount = money(claimed_amount) if claimed_amount is not None else None
        order.buyer_confirmed_at = ledger.buyer_confirmed_at = None
        ledger.needs_review = True
    order.save()
    ledger.save(update_fields=['buyer_confirmed_at', 'needs_review'])
    audit(company, buyer, 'order.buyer_confirm' if confirm else 'order.amount_dispute', order, reason=reason)
    return ledger


@transaction.atomic
def report_manual_sale(company_id, *, actor, data):
    company = CompanyProfile.objects.select_for_update().get(pk=company_id)
    require_company_actor(company, actor)
    if not company.approved_at:
        raise ValidationError('Only a previously approved Partner Company can report store-originated sales.')
    if data['sale_date'] > timezone.localdate() or data['sale_date'] < timezone.localdate(company.approved_at):
        raise ValidationError('Choose a sale date between company approval and today.')
    amount = money(data['amount'])
    if amount <= 0 or not data['reference'].strip():
        raise ValidationError('A positive sold amount and reference are required.')
    ledger = SalesLedger.objects.create(company=company, source='manual', amount=amount, original_amount=amount,
        sale_date=data['sale_date'], reference=data['reference'].strip(), reported_by=actor)
    audit(company, actor, 'ledger.manual_report', ledger, amount=str(amount))
    return ledger


@transaction.atomic
def adjust_ledger(ledger_id, *, actor, amount, reason, resolve=False):
    require_owner(actor)
    company_id = SalesLedger.objects.values_list('company_id', flat=True).get(pk=ledger_id)
    company = CompanyProfile.objects.select_for_update().get(pk=company_id)
    ledger = SalesLedger.objects.select_for_update().get(pk=ledger_id)
    if not reason.strip():
        raise ValidationError('An adjustment reason is required.')
    amount = money(amount)
    adjustment = LedgerAdjustment.objects.create(ledger=ledger, actor=actor, previous_amount=ledger.amount,
        new_amount=amount, reason=reason.strip())
    ledger.amount = amount
    ledger.buyer_confirmed_at = None
    ledger.needs_review = not resolve
    ledger.save(update_fields=['amount', 'buyer_confirmed_at', 'needs_review'])
    if ledger.order_id:
        OrderRequest.objects.filter(pk=ledger.order_id).update(buyer_confirmed_at=None)
    audit(company, actor, 'ledger.adjust', ledger, reason=reason, previous=str(adjustment.previous_amount), amount=str(amount))
    return ledger
