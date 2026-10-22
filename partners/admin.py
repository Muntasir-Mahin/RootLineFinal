from django import forms
from django.contrib import admin, messages
from django.contrib.admin.helpers import ActionForm
from django.core.exceptions import ValidationError

from .forms import AchievementForm, CertificationForm, GalleryImageForm, CompanyProfileForm
from .models import Achievement, Certification, CompanyProfile, GalleryImage, PartnerAuditLog, PartnerCategory
from .services import decide_company


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
