from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods
from django.urls import reverse
from urllib.parse import urlencode

from .email_verification import confirm_verification, is_verified, send_verification
from .forms import PartnerApplicationForm
from .models import CompanyProfile
from .services import register_company
from dashboard.permissions import PARTNERS, has_role


@never_cache
@require_http_methods(['GET', 'POST'])
def apply(request):
    if not request.user.is_authenticated:
        messages.info(request, 'Create a customer account first, then apply for partnership')
        return redirect_to_login(request.get_full_path())
    if request.user.is_staff or request.user.is_superuser:
        messages.error(request, 'Staff and superuser accounts cannot apply. Use a customer account.')
        return redirect('profile')
    company = CompanyProfile.objects.filter(user=request.user).first()
    if company and company.status != 'rejected':
        messages.info(request, 'Your application is pending.' if company.status == 'pending' else
                      'You are already an approved Partner. Check your application status for access details.')
        return redirect('partners:application_status')
    if not is_verified(request.user):
        return redirect('partners:verify_email')
    initial = {'email':request.user.email}
    if company:
        initial.update({field:getattr(company, field) for field in
            ('email', 'phone', 'address', 'district', 'division', 'trade_license')})
        initial['company_name'] = company.name
    form = PartnerApplicationForm(request.POST if request.method == 'POST' else None,
        request.FILES or None, initial=initial, company=company)
    if request.method == 'POST' and form.is_valid():
        try:
            register_company(form.cleaned_data, applicant=request.user)
        except ValidationError as error:
            form.add_error(None, '; '.join(error.messages))
        else:
            request.session['partner_application_submitted'] = request.user.pk
            messages.success(request, 'Your Partner application was submitted for staff review.')
            return redirect('partners:application_status')
    return render(request, 'partners/register.html', {'form':form, 'application':company,
        'terms_url':reverse('partners:terms') + '?' + urlencode({'next':reverse('partners:apply')})})


@never_cache
@login_required
@require_GET
def application_status(request):
    company = CompanyProfile.objects.filter(user=request.user).first()
    if not company:
        return redirect('partners:apply')
    clear_draft = request.session.pop('partner_application_submitted', None) == request.user.pk
    return render(request, 'partners/application_status.html', {'application':company, 'clear_draft':clear_draft})


@never_cache
@login_required
@require_http_methods(['GET', 'POST'])
def verify_email(request):
    if is_verified(request.user):
        return redirect('partners:apply')
    error = None
    if request.method == 'POST':
        try:
            send_verification(request.user, request)
        except ValidationError as exception:
            error = '; '.join(exception.messages)
        else:
            messages.info(request, 'Verification email requested. Check your inbox or, for the console backend, the server terminal.')
    return render(request, 'partners/verify_email.html', {'error':error})


@never_cache
@login_required
@require_http_methods(['GET', 'POST'])
def verify_email_confirm(request, token):
    error = None
    if request.method == 'POST':
        try:
            confirm_verification(request.user, token)
        except ValidationError as exception:
            error = '; '.join(exception.messages)
        else:
            messages.success(request, 'Customer email verified. You can now apply for partnership.')
            return redirect('partners:apply')
    return render(request, 'partners/verify_email_confirm.html', {'error':error})


@never_cache
@login_required
@require_GET
def trade_license_download(request, pk):
    company = get_object_or_404(CompanyProfile, pk=pk)
    owner = request.user.is_active and request.user.is_staff and request.user.is_superuser
    if company.user_id != request.user.pk and not owner and not has_role(request.user, PARTNERS):
        raise PermissionDenied
    if not company.trade_license_document:
        from django.http import Http404
        raise Http404
    response = FileResponse(company.trade_license_document.open('rb'), as_attachment=True)
    response['X-Content-Type-Options'] = 'nosniff'
    response['Content-Security-Policy'] = 'sandbox'
    return response
