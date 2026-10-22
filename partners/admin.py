from django import forms
from django.contrib import admin, messages
from django.contrib.admin.helpers import ActionForm
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html

from .forms import AchievementForm, CertificationForm, GalleryImageForm, CompanyProfileForm
from .models import Achievement, Certification, CompanyProfile, GalleryImage, PartnerAuditLog, PartnerCategory
from .services import decide_company
from .forms import CompanyProductForm, CompanyProductImageForm
from .models import CompanyProduct, CompanyProductImage
from .models import LedgerAdjustment, OrderRequest, SalesLedger
from .order_services import adjust_ledger


class PartnerActionForm(ActionForm):
    reason = forms.CharField(required=False, widget=forms.TextInput, label='Decision reason')


@admin.register(CompanyProfile)
class CompanyProfileAdmin(admin.ModelAdmin):
    form = CompanyProfileForm
    list_display = ('name', 'email', 'district', 'status', 'is_active', 'is_verified', 'is_suspended')
    list_filter = ('status', 'is_active', 'is_suspended', 'is_verified', 'district')
    search_fields = ('name', 'email', 'phone', 'trade_license')
    readonly_fields = ('user', 'slug', 'status', 'rejection_reason', 'is_verified', 'is_suspended',
                       'approved_at', 'terms_accepted_at', 'terms_version', 'created_at', 'updated_at')
    action_form = PartnerActionForm
    actions = ('approve', 'reject', 'verify', 'suspend', 'unsuspend')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def decide(self, request, queryset, decision):
        for company in queryset.order_by('pk'):
            try:
                decide_company(company.pk, actor=request.user, decision=decision, reason=request.POST.get('reason', ''))
            except ValidationError as error:
                self.message_user(request, '; '.join(error.messages), messages.ERROR)

    @admin.action(description='Approve selected Partner Companies')
    def approve(self, request, queryset):
        self.decide(request, queryset, 'approve')

    @admin.action(description='Reject selected companies (reason required)')
    def reject(self, request, queryset):
        self.decide(request, queryset, 'reject')

    @admin.action(description='Mark selected companies verified')
    def verify(self, request, queryset):
        self.decide(request, queryset, 'verify')

    @admin.action(description='Suspend selected companies (reason required)')
    def suspend(self, request, queryset):
        self.decide(request, queryset, 'suspend')

    @admin.action(description='Remove suspension (reason required)')
    def unsuspend(self, request, queryset):
        self.decide(request, queryset, 'unsuspend')


@admin.register(PartnerCategory)
class PartnerCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    readonly_fields = ('slug',)


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    form = AchievementForm
    fields = ('company', 'title', 'year', 'description', 'image')
    list_display = ('title', 'company', 'year')
    list_filter = ('year',)
    search_fields = ('title', 'company__name')


@admin.register(Certification)
class CertificationAdmin(admin.ModelAdmin):
    form = CertificationForm
    fields = ('company', 'title', 'issuer', 'file')
    list_display = ('title', 'issuer', 'company')
    search_fields = ('title', 'issuer', 'company__name')


@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    form = GalleryImageForm
    fields = ('company', 'image', 'caption')
    list_display = ('company', 'caption')
    search_fields = ('company__name', 'caption')


class ImmutableAdmin(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        return [field.name for field in self.model._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(PartnerAuditLog)
class PartnerAuditLogAdmin(ImmutableAdmin):
    list_display = ('created_at', 'company', 'actor', 'action', 'target')
    list_filter = ('action',)
    search_fields = ('company__name', 'reason', 'target')


@admin.register(CompanyProduct)
class CompanyProductAdmin(admin.ModelAdmin):
    form = CompanyProductForm
    fields = ('company', 'name', 'slug', 'category', 'price', 'discount_price', 'unit', 'stock_quantity',
              'description', 'main_image', 'is_active', 'created_at', 'updated_at')
    readonly_fields = ('slug', 'created_at', 'updated_at')
    list_display = ('name', 'company', 'category', 'price', 'stock_quantity', 'is_active')
    list_filter = ('is_active', 'category')
    search_fields = ('name', 'company__name')


@admin.register(CompanyProductImage)
class CompanyProductImageAdmin(admin.ModelAdmin):
    form = CompanyProductImageForm
    fields = ('product', 'image', 'caption')
    list_display = ('product', 'caption')
    search_fields = ('product__name',)


@admin.register(OrderRequest)
class OrderRequestAdmin(ImmutableAdmin):
    list_display = ('number', 'company', 'buyer', 'status', 'expected_amount', 'final_amount', 'created_at')
    list_filter = ('status', 'company')
    search_fields = ('number', 'product_name', 'company__name')


class LedgerAdjustmentForm(forms.Form):
    amount = forms.DecimalField(max_digits=14, decimal_places=2, min_value=0)
    reason = forms.CharField(widget=forms.Textarea, max_length=4000)
    resolve_review = forms.BooleanField(required=False, label='Resolve owner review (does not claim buyer confirmation)')


@admin.register(SalesLedger)
class SalesLedgerAdmin(ImmutableAdmin):
    list_display = ('company', 'sale_date', 'source', 'order', 'amount', 'buyer_confirmed_at', 'needs_review', 'adjust_link')
    list_filter = ('source', 'needs_review', 'company')
    search_fields = ('reference', 'company__name', 'order__number')

    @admin.display(description='Owner decision')
    def adjust_link(self, obj):
        return format_html('<a href="{}">Adjust / review with reason</a>',
            reverse('admin:partners_salesledger_adjust', args=[obj.pk]))

    def get_urls(self):
        return [path('<int:pk>/adjust/', self.admin_site.admin_view(self.adjust_view),
                     name='partners_salesledger_adjust')] + super().get_urls()

    def adjust_view(self, request, pk):
        ledger = get_object_or_404(SalesLedger, pk=pk)
        form = LedgerAdjustmentForm(request.POST or None, initial={'amount': ledger.amount})
        if request.method == 'POST' and form.is_valid():
            try:
                adjust_ledger(ledger.pk, actor=request.user, amount=form.cleaned_data['amount'],
                              reason=form.cleaned_data['reason'], resolve=form.cleaned_data['resolve_review'])
            except ValidationError as error:
                form.add_error(None, error)
            else:
                return HttpResponseRedirect(reverse('admin:partners_salesledger_changelist'))
        return TemplateResponse(request, 'admin/partners/action_form.html', {
            **self.admin_site.each_context(request), 'opts': self.model._meta, 'form': form,
            'title': 'Adjust Partner sales ledger',
            'explanation': 'The original amount is retained. Your reason and adjustment are permanently logged.',
        })


@admin.register(LedgerAdjustment)
class LedgerAdjustmentAdmin(ImmutableAdmin):
    list_display = ('ledger', 'actor', 'previous_amount', 'new_amount', 'created_at')
    search_fields = ('ledger__company__name', 'reason')
