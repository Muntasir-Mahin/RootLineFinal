from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Case, IntegerField, Value, When
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_GET, require_POST

from partners.models import CompanyProfile
from partners.services import decide_company
from .forms import PartnerDecisionForm
from .permissions import PARTNERS, staff_role_required
from .views import page, panel


@staff_role_required(PARTNERS)
@require_GET
def partners(request):
    queryset = CompanyProfile.objects.select_related('user', 'decided_by')
    status = request.GET.get('status', 'pending')
    if status not in ('all', 'pending', 'approved', 'rejected'):
        status = 'pending'
    if status != 'all':
        queryset = queryset.filter(status=status)
    query = request.GET.get('q', '').strip()[:160]
    if query:
        queryset = queryset.filter(name__icontains=query)
    queryset = queryset.annotate(pending_first=Case(When(status='pending', then=Value(0)),
        default=Value(1), output_field=IntegerField())).order_by('pending_first', 'submitted_at', 'pk')
    return panel(request, 'partners', 'Partners', 'partners', page_obj=page(request, queryset),
                 selected_status=status, search=query)


def detail_response(request, company, form, status=200):
    fields = [(field.verbose_name, getattr(company, field.name)) for field in company._meta.fields
              if field.name not in ('user', 'logo', 'cover_image', 'trade_license_document')]
    response = panel(request, 'partner_detail', 'Partner application', 'partners',
        company=company, applicant=company.user, details=fields, form=form)
    response.status_code = status
    return response


@staff_role_required(PARTNERS)
@require_GET
def partner_detail(request, pk):
    company = get_object_or_404(CompanyProfile.objects.select_related('user', 'decided_by'), pk=pk)
    return detail_response(request, company, PartnerDecisionForm())


@staff_role_required(PARTNERS)
@require_POST
def partner_decide(request, pk):
    company = get_object_or_404(CompanyProfile.objects.select_related('user', 'decided_by'), pk=pk)
    form = PartnerDecisionForm(request.POST)
    if form.is_valid():
        try:
            decide_company(company.pk, actor=request.user, **form.cleaned_data)
        except ValidationError as error:
            form.add_error(None, '; '.join(error.messages))
        else:
            messages.success(request, 'Partner application decision saved and applicant notified.')
            return redirect('dashboard:partner_detail', pk=company.pk)
    return detail_response(request, company, form, status=400)
