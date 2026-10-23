from accounts.navigation import internal_next
from .models import Notification


def create_notification(recipient, message, link=''):
    return Notification.objects.create(recipient=recipient, message=message[:6000], link=internal_next(link))
