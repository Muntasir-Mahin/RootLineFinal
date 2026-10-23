import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.mail import EmailMessage
from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import CompanyProfile, PartnerAuditLog


ROLE_NAME = 'Partner Company'
logger = logging.getLogger(__name__)


def audit(company, actor, action, target=None, reason='', **details):
    return PartnerAuditLog.objects.create(company=company, actor=actor, action=action,
        target=f'{target._meta.label}:{target.pk}' if target else f'partners.CompanyProfile:{company.pk}',
        reason=reason, details=details)


def require_owner(actor):
    if not actor or not actor.is_active or not actor.is_staff or not actor.is_superuser:
        raise PermissionDenied('Only the owner can make this decision.')


def require_company_actor(company, actor, *, publishing=False):
    if not actor.is_authenticated or not actor.is_active or company.user_id != actor.pk:
        raise PermissionDenied('This Partner Company does not belong to you.')
    if not company.can_publish or not actor.groups.filter(name=ROLE_NAME).exists():
        raise PermissionDenied('An active, approved, non-suspended Partner Company is required.')


def notify(recipient, subject, body):
    if not recipient:
        return
    if settings.EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend' and not (
            settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD):
        logger.warning('Partner email skipped: SMTP credentials are not configured.')
        return

    def deliver():
        try:
            EmailMessage(subject, body, settings.DEFAULT_FROM_EMAIL, [recipient]).send()
        except Exception:
            logger.exception('Partner notification could not be delivered.')
    transaction.on_commit(deliver)


def register_company(data, *, applicant):
    from .email_verification import is_verified
    if not applicant.is_authenticated or not applicant.is_active or applicant.is_staff or applicant.is_superuser:
        raise PermissionDenied('Only a customer account may apply for partnership.')
    try:
        with transaction.atomic():
            user = get_user_model().objects.select_for_update().get(pk=applicant.pk)
            if not user.is_active or user.is_staff or user.is_superuser or not is_verified(user):
                raise ValidationError('Verify your current customer email before applying.')
            company = CompanyProfile.objects.select_for_update().filter(user=user).first()
            if company and company.status != 'rejected':
                raise ValidationError('You already have a pending or approved Partner application.')
            company = company or CompanyProfile(user=user)
            if CompanyProfile.objects.filter(name__iexact=data['company_name']).exclude(pk=company.pk).exists():
                raise ValidationError('A company with this name already exists.')
            company.name = data['company_name']
            for field in ('email', 'phone', 'address', 'district', 'division', 'trade_license'):
                setattr(company, field, data.get(field, '').strip())
            if not data.get('agree_terms'):
                raise ValidationError('You must agree to the Partner Terms.')
            if data.get('trade_license_document'):
                company.trade_license_document = data['trade_license_document']
            company.status = 'pending'
            company.rejection_reason = ''
            company.decision_reason = ''
            company.decided_by = company.decided_at = None
            company.submitted_at = company.terms_accepted_at = timezone.now()
            company.save()
            user.groups.remove(*Group.objects.filter(name=ROLE_NAME))
            audit(company, user, 'company.apply', reason='Accepted draft-v1 Partner Terms.')
            from .application_notifications import application_submitted
            application_submitted(company)
            return company
    except IntegrityError:
        raise ValidationError('We could not submit this application with these details. Please check them or contact staff.')


@transaction.atomic
def decide_company(company_id, *, actor, decision, reason=''):
    from dashboard.permissions import PARTNERS, has_role
    if decision in ('approve', 'reject'):
        if not has_role(actor, PARTNERS):
            raise PermissionDenied('The Partners staff role is required.')
    else:
        require_owner(actor)
    company = CompanyProfile.objects.select_for_update().get(pk=company_id)
    if decision in ('approve', 'reject'):
        if company.status != 'pending':
            raise ValidationError('Only a pending application can be decided. This decision cannot be repeated.')
        if len(reason) > 4000:
            raise ValidationError('Keep the decision reason within 4000 characters.')
        company.decided_by = actor
        company.decided_at = timezone.now()
        company.decision_reason = reason.strip()
    if decision == 'approve':
        company.status = 'approved'
        company.rejection_reason = ''
        company.approved_at = company.approved_at or timezone.now()
    elif decision == 'reject':
        if not reason.strip():
            raise ValidationError('A rejection reason is required.')
        company.status = 'rejected'
        company.rejection_reason = reason.strip()
        company.is_verified = False
    elif decision == 'verify':
        if company.status != 'approved':
            raise ValidationError('Approve this Partner Company before marking it verified.')
        company.is_verified = True
    elif decision in ('suspend', 'unsuspend'):
        if not reason.strip():
            raise ValidationError('A reason is required for a suspension change.')
        company.is_suspended = decision == 'suspend'
    else:
        raise ValidationError('Unknown company decision.')
    company.save()
    group, _ = Group.objects.get_or_create(name=ROLE_NAME)
    if company.can_publish:
        company.user.groups.add(group)
    else:
        company.user.groups.remove(group)
    audit(company, actor, f'company.{decision}', reason=reason)
    if decision in ('approve', 'reject'):
        from .application_notifications import application_decided
        application_decided(company)
    return company
