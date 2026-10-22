import logging
from uuid import uuid4

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
    if publishing and not company.can_publish:
        raise PermissionDenied('An active, approved, non-suspended Partner Company is required.')


def notify(recipient, subject, body):
    if settings.EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend' and not (
            settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD):
        return

    def deliver():
        try:
            EmailMessage(subject, body, settings.DEFAULT_FROM_EMAIL, [recipient]).send()
        except Exception:
            logger.exception('Partner notification could not be delivered.')
    transaction.on_commit(deliver)


def register_company(data):
    # Both successful and duplicate-email registrations have the same public
    # redirect/message. Never attach a new company to an existing user's account.
    try:
        with transaction.atomic():
            user = get_user_model()._default_manager.create_user(
                username=f'partner-{uuid4().hex}', email=data['email'].strip(), password=data['password1'])
            company = CompanyProfile.objects.create(user=user, name=data['company_name'].strip(),
                email=data['email'].strip(), phone=data['phone'], address=data['address'],
                district=data['district'], division=data['division'], trade_license=data.get('trade_license', ''),
                terms_accepted_at=timezone.now())
            group, _ = Group.objects.get_or_create(name=ROLE_NAME)
            user.groups.add(group)
            audit(company, user, 'company.register', reason='Accepted draft-v1 Partner Terms.')
            return company
    except IntegrityError:
        return None


@transaction.atomic
def decide_company(company_id, *, actor, decision, reason=''):
    require_owner(actor)
    company = CompanyProfile.objects.select_for_update().get(pk=company_id)
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
    audit(company, actor, f'company.{decision}', reason=reason)
    if decision in ('approve', 'reject'):
        notify(company.email, f'RootLine Partner Company: {company.get_status_display()}',
               f'Your Partner Company, {company.name}, has been {company.status}.\n{reason}\n'
               'Sign in through Partner Company Login to view your dashboard.')
    return company
