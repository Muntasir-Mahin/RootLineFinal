from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods

from .forms import (AchievementForm, CertificationForm, CompanyProfileForm,
                    GalleryImageForm)
from .models import Achievement, Certification, CompanyProfile, GalleryImage
from .services import ROLE_NAME, audit
from .validators import MAX_GALLERY_IMAGES


def company_required(view):
    @login_required
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        company = CompanyProfile.objects.select_related('user').filter(user=request.user).first()
        if not company or not company.can_publish or not request.user.groups.filter(name=ROLE_NAME).exists():
            raise PermissionDenied('A Partner Company account is required.')
        request.partner_company = company
        return view(request, *args, **kwargs)
    return never_cache(wrapped)


@require_http_methods(['GET', 'POST'])
def register(request):
    return redirect('partners:apply')


@require_http_methods(['GET', 'POST'])
def partner_login(request):
    if request.user.is_authenticated:
        return redirect('partners:application_status')
    from django.urls import reverse
    return redirect(reverse('login') + '?next=' + reverse('partners:application_status'))


@require_GET
def terms(request):
    from .billing_services import default_plan
    from accounts.navigation import internal_next
    from django.urls import reverse
    try:
        plan = default_plan()
    except ValidationError:
        plan = None
    return render(request, 'partners/terms.html', {'default_plan':plan,
        'back_url':internal_next(request.GET.get('next'), reverse('partners:apply'))})


@company_required
@require_GET
def dashboard(request):
    return render(request, 'partners/dashboard.html', {'company': request.partner_company})


@company_required
@require_http_methods(['GET', 'POST'])
def profile_edit(request):
    company = request.partner_company
    form = CompanyProfileForm(request.POST or None, request.FILES or None, instance=company)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            form.save()
            audit(company, request.user, 'company.profile.update')
        messages.success(request, 'Your Partner Company profile was updated.')
        return redirect('partners:dashboard')
    return render(request, 'partners/form.html', {'form': form, 'company': company, 'title': 'Edit company profile'})


ASSETS = {
    'achievements': (Achievement, AchievementForm, 'Achievement'),
    'certifications': (Certification, CertificationForm, 'Certification'),
    'gallery': (GalleryImage, GalleryImageForm, 'Gallery image'),
}


@company_required
@require_GET
def asset_list(request, kind):
    if kind not in ASSETS:
        from django.http import Http404
        raise Http404
    model, _, label = ASSETS[kind]
    return render(request, 'partners/assets.html', {'company': request.partner_company,
        'items': model.objects.filter(company=request.partner_company), 'kind': kind, 'label': label})


@company_required
@require_http_methods(['GET', 'POST'])
def asset_edit(request, kind, pk=None):
    if kind not in ASSETS:
        from django.http import Http404
        raise Http404
    model, form_class, label = ASSETS[kind]
    company = request.partner_company
    item = get_object_or_404(model, pk=pk, company=company) if pk else None
    form = form_class(request.POST or None, request.FILES or None, instance=item)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            CompanyProfile.objects.select_for_update().get(pk=company.pk)
            if kind == 'gallery' and item is None and company.gallery.count() >= MAX_GALLERY_IMAGES:
                form.add_error(None, f'Keep at most {MAX_GALLERY_IMAGES} gallery images.')
            else:
                item = form.save(commit=False)
                item.company = company
                item.save()
                audit(company, request.user, f'company.{kind}.save', item)
                return redirect('partners:asset_list', kind=kind)
    return render(request, 'partners/form.html', {'form': form, 'company': company, 'title': f'Edit {label}'})


@company_required
@require_http_methods(['GET', 'POST'])
def asset_delete(request, kind, pk):
    if kind not in ASSETS:
        from django.http import Http404
        raise Http404
    item = get_object_or_404(ASSETS[kind][0], pk=pk, company=request.partner_company)
    if request.method == 'POST':
        with transaction.atomic():
            audit(request.partner_company, request.user, f'company.{kind}.delete', item)
            item.delete()
        return redirect('partners:asset_list', kind=kind)
    return render(request, 'partners/confirm_delete.html', {'item': item, 'company': request.partner_company})
