from django.contrib.auth import get_user_model
from django.db.models import Q
from django.urls import reverse

from notifications.services import create_notification
from .permissions import CATALOGUE


def seller_requested(seller):
    recipients = get_user_model().objects.filter(is_active=True).filter(
        Q(is_staff=True, groups__name=CATALOGUE) | Q(is_superuser=True)).distinct()
    for recipient in recipients:
        create_notification(recipient, f'New seller request awaiting review: {seller.get_username()}',
                            reverse('dashboard:sellers') + '?tab=requests')


def seller_decided(seller, decision, note=''):
    messages = {
        'approve':'Your RootLine seller request has been approved.',
        'reject':'Your RootLine seller request has been rejected.',
        'revoke':'Your RootLine seller access has been revoked.',
    }
    message = messages[decision]
    if note.strip():
        message += '\nStaff note: ' + note.strip()
    link = reverse('seller_dashboard') if decision == 'approve' else reverse('profile')
    create_notification(seller, message, link)


def product_reviewed(product, previous, note=''):
    message = (f'Your product "{product.name}" changed from {previous} '
               f'to {product.verification_status}.')
    if note:
        message += '\nStaff reason: ' + note
    create_notification(product.seller, message, reverse('product_detail', args=[product.pk]))
