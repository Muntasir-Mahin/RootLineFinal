from uuid import uuid4

from django.contrib.auth import get_user_model
from django.core import signing
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from .models import CustomerEmailVerification
from .services import notify


SALT = 'partners.customer-email.v1'
MAX_AGE = 3600


def is_verified(user):
    return bool(user.email and CustomerEmailVerification.objects.filter(user=user,
        email=user.email.strip().lower(), verified_at__isnull=False).exists())


@transaction.atomic
def send_verification(user, request):
    user = get_user_model().objects.select_for_update().get(pk=user.pk)
    if not user.email:
        raise ValidationError('Add an email to your customer profile first.')
    if is_verified(user):
        return
    if not cache.add(f'partners:verify-email:{user.pk}', True, timeout=60):
        raise ValidationError('Please wait one minute before requesting another verification email.')
    record, _ = CustomerEmailVerification.objects.get_or_create(user=user, defaults={'email':user.email.strip().lower()})
    record.email, record.nonce, record.verified_at = user.email.strip().lower(), uuid4(), None
    record.save()
    token = signing.dumps({'uid':user.pk, 'email':record.email, 'nonce':record.nonce.hex}, salt=SALT)
    url = request.build_absolute_uri(reverse('partners:verify_email_confirm', args=[token]))
    notify(user.email, 'Verify your RootLine customer email',
        'Verify your customer email before applying for Agro Partners.\n\n'
        f'{url}\n\nThis link expires in one hour. Sign in to your customer account and confirm it.\n'
        'If you did not request this email, ignore it.')


@transaction.atomic
def confirm_verification(user, token):
    user = get_user_model().objects.select_for_update().get(pk=user.pk)
    try:
        data = signing.loads(token, salt=SALT, max_age=MAX_AGE)
        record = CustomerEmailVerification.objects.select_for_update().get(user=user)
        valid = (data['uid'] == user.pk and data['email'] == user.email.strip().lower() == record.email
                 and data['nonce'] == record.nonce.hex and record.verified_at is None)
        if not valid:
            raise ValueError
    except (signing.BadSignature, CustomerEmailVerification.DoesNotExist, KeyError, TypeError, ValueError):
        raise ValidationError('This verification link is invalid, expired or already used. Request a new link.')
    record.verified_at, record.nonce = timezone.now(), uuid4()
    record.save(update_fields=['verified_at', 'nonce'])
