from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .forms import CompanyProductForm, CompanyProductImageForm
from .models import CompanyProduct, CompanyProductImage, CompanyProfile
from .services import audit, require_company_actor
from .validators import MAX_PRODUCT_IMAGES
from .views import company_required


@company_required
@require_GET
def product_list(request):
    return render(request, 'partners/product_list.html', {'company': request.partner_company,
        'products': request.partner_company.products.select_related('category')})


@company_required
@require_http_methods(['GET', 'POST'])
def product_edit(request, pk=None):
    company = request.partner_company
    require_company_actor(company, request.user, publishing=True)
    product = get_object_or_404(CompanyProduct, company=company, pk=pk) if pk else CompanyProduct(company=company)
    form = CompanyProductForm(request.POST or None, request.FILES or None, instance=product)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            locked = CompanyProfile.objects.select_for_update().select_related('user').get(pk=company.pk)
            require_company_actor(locked, request.user, publishing=True)
            product = form.save(commit=False)
            product.company = locked
            product.save()
            audit(locked, request.user, 'product.save', product)
        messages.success(request, 'Your company product was saved.')
        return redirect('partners:product_list')
    return render(request, 'partners/form.html', {'company': company, 'form': form, 'title': 'Edit company product'})


@company_required
@require_POST
def product_toggle(request, pk):
    company = request.partner_company
    with transaction.atomic():
        locked = CompanyProfile.objects.select_for_update().select_related('user').get(pk=company.pk)
        product = get_object_or_404(CompanyProduct.objects.select_for_update(), pk=pk, company=locked)
        if not product.is_active:
            require_company_actor(locked, request.user, publishing=True)
        product.is_active = not product.is_active
        product.save(update_fields=['is_active', 'updated_at'])
        audit(company, request.user, 'product.show' if product.is_active else 'product.hide', product)
    return redirect('partners:product_list')


@company_required
@require_http_methods(['GET', 'POST'])
def product_delete(request, pk):
    product = get_object_or_404(CompanyProduct, pk=pk, company=request.partner_company)
    if request.method == 'POST':
        try:
            with transaction.atomic():
                audit(request.partner_company, request.user, 'product.delete', product)
                product.delete()
        except ProtectedError:
            messages.error(request, 'Orders protect this product from deletion. Hide it instead to retain its records.')
        return redirect('partners:product_list')
    return render(request, 'partners/confirm_delete.html', {'company': request.partner_company, 'item': product})


@company_required
@require_http_methods(['GET', 'POST'])
def product_images(request, pk):
    company = request.partner_company
    require_company_actor(company, request.user, publishing=True)
    product = get_object_or_404(CompanyProduct, pk=pk, company=company)
    form = CompanyProductImageForm(request.POST or None, request.FILES or None,
                                  instance=CompanyProductImage(product=product))
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            CompanyProfile.objects.select_for_update().get(pk=company.pk)
            if product.extra_images.count() >= MAX_PRODUCT_IMAGES:
                form.add_error(None, f'Keep at most {MAX_PRODUCT_IMAGES} extra product images.')
            else:
                image = form.save()
                audit(company, request.user, 'product.image.add', image)
                return redirect('partners:product_images', pk=product.pk)
    return render(request, 'partners/product_images.html', {'company': company, 'product': product,
        'images': product.extra_images.all(), 'form': form})


@company_required
@require_POST
def product_image_delete(request, pk):
    image = get_object_or_404(CompanyProductImage, pk=pk, product__company=request.partner_company)
    product_pk = image.product_id
    with transaction.atomic():
        audit(request.partner_company, request.user, 'product.image.delete', image)
        image.delete()
    return redirect('partners:product_images', pk=product_pk)
