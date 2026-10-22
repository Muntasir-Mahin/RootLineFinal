from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .models import CompanyProduct, CompanyProfile, OrderRequest
from .order_forms import AmountDisputeForm, CompleteOrderForm, ManualSaleForm, OrderRequestForm
from .order_services import (buyer_evidence, cancel_order, company_order_decision, complete_order,
                             report_manual_sale, request_order)
from .views import company_required


def add_error(form, error):
    form.add_error(None, '; '.join(error.messages))


@never_cache
@login_required
@require_http_methods(['GET', 'POST'])
def order_create(request, slug, product_slug):
    company = get_object_or_404(CompanyProfile.objects.public(), slug=slug)
    product = get_object_or_404(CompanyProduct, company=company, slug=product_slug, is_active=True)
    form = OrderRequestForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        try:
            order = request_order(product.pk, buyer=request.user, data=form.cleaned_data)
        except ValidationError as error:
            add_error(form, error)
        else:
            messages.success(request, 'Order Request sent. Payment and delivery are arranged directly with the company.')
            return redirect('partners:buyer_order', pk=order.pk)
    return render(request, 'partners/form.html', {'form': form, 'title': f'Order Request: {product.name}'})


@never_cache
@login_required
@require_GET
def buyer_orders(request):
    orders = OrderRequest.objects.filter(buyer=request.user).select_related('company', 'product')
    return render(request, 'partners/order_list.html', {'orders': orders, 'buyer_view': True})


@never_cache
@login_required
@require_http_methods(['GET', 'POST'])
def buyer_order(request, pk):
    order = get_object_or_404(OrderRequest.objects.select_related('company', 'buyer'), pk=pk, buyer=request.user)
    form = AmountDisputeForm(request.POST or None)
    if request.method == 'POST':
        action = request.POST.get('action')
        try:
            if action == 'cancel':
                cancel_order(order.pk, buyer=request.user)
            elif action == 'confirm':
                buyer_evidence(order.pk, buyer=request.user, confirm=True)
            elif action == 'dispute' and form.is_valid():
                buyer_evidence(order.pk, buyer=request.user, reason=form.cleaned_data['reason'],
                               claimed_amount=form.cleaned_data['claimed_amount'])
            else:
                if action != 'dispute':
                    form.add_error(None, 'Choose a valid order action.')
                return render(request, 'partners/order_detail.html', {'order': order, 'buyer_view': True, 'form': form})
        except ValidationError as error:
            add_error(form, error)
        else:
            return redirect('partners:buyer_order', pk=pk)
    return render(request, 'partners/order_detail.html', {'order': order, 'buyer_view': True, 'form': form})


@company_required
@require_GET
def company_orders(request):
    orders = request.partner_company.order_requests.select_related('buyer', 'product')
    return render(request, 'partners/order_list.html', {'company': request.partner_company, 'orders': orders})


@company_required
@require_http_methods(['GET', 'POST'])
def company_order(request, pk):
    company = request.partner_company
    order = get_object_or_404(OrderRequest.objects.select_related('buyer', 'company'), company=company, pk=pk)
    form = CompleteOrderForm(request.POST or None, initial={'final_amount': order.expected_amount})
    if request.method == 'POST':
        action = request.POST.get('action')
        try:
            if action in ('accept', 'decline'):
                company_order_decision(order.pk, actor=request.user, decision=action,
                                       reason=request.POST.get('reason', '')[:3000])
            elif action == 'complete' and form.is_valid():
                complete_order(order.pk, actor=request.user, final_amount=form.cleaned_data['final_amount'],
                               reason=form.cleaned_data['reason'])
            else:
                if action != 'complete':
                    form.add_error(None, 'Choose a valid order action.')
                return render(request, 'partners/order_detail.html', {'company': company, 'order': order, 'form': form})
        except ValidationError as error:
            add_error(form, error)
        else:
            return redirect('partners:company_order', pk=pk)
    return render(request, 'partners/order_detail.html', {'company': company, 'order': order, 'form': form})


@company_required
@require_GET
def ledger(request):
    entries = request.partner_company.ledger_entries.select_related('order')
    return render(request, 'partners/ledger.html', {'company': request.partner_company,
        'page': Paginator(entries, 30).get_page(request.GET.get('page'))})


@company_required
@require_http_methods(['GET', 'POST'])
def manual_sale(request):
    form = ManualSaleForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        try:
            report_manual_sale(request.partner_company.pk, actor=request.user, data=form.cleaned_data)
        except ValidationError as error:
            add_error(form, error)
        else:
            return redirect('partners:ledger')
    return render(request, 'partners/form.html', {'company': request.partner_company, 'form': form,
        'title': 'Record a manually reported store-originated sale'})
