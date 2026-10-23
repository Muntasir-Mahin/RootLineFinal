from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.urls import reverse

from dashboard.permissions import PARTNERS
from notifications.services import create_notification
from .services import notify


def application_submitted(company):
    recipients = get_user_model().objects.filter(is_active=True, is_staff=True).filter(
        Q(groups__name=PARTNERS) | Q(is_superuser=True)).distinct()
    message = f'Partner application awaiting review: {company.name}'
    link = reverse('dashboard:partner_detail', args=[company.pk])
    emails = {email.strip().lower() for email in settings.STAFF_NOTIFICATION_EMAILS if email.strip()}
    for user in recipients:
        create_notification(user, message, link)
        if user.email:
            emails.add(user.email.strip().lower())
    for email in sorted(emails):
        notify(email, 'RootLine: new Partner application', message + '\nSign in to the staff dashboard to review: ' + link)


def application_decided(company):
    message = f'Your Partner application, {company.name}, was {company.status}.'
    if company.decision_reason:
        message += '\nStaff reason: ' + company.decision_reason
    link = reverse('partners:application_status')
    create_notification(company.user, message, link)
    notify(company.user.email, f'RootLine Partner application: {company.get_status_display()}',
        message + '\nSign in with your existing customer account to view your application: ' + link)
