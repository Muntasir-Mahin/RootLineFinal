from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils import timezone

from partners.models import CompanyProfile
from partners.services import ROLE_NAME


def make_company(name='Green Farm', status='approved', **kwargs):
    user = get_user_model().objects.create_user(username=name.replace(' ', '-'),
        email=kwargs.pop('email', name.replace(' ', '').lower() + '@example.com'), password='Partner-demo-793!')
    group, _ = Group.objects.get_or_create(name=ROLE_NAME)
    user.groups.add(group)
    return CompanyProfile.objects.create(user=user, name=name, email=user.email, phone='01700000000',
        address='Private road, Dhaka', district='Dhaka', division='Dhaka', status=status,
        terms_accepted_at=timezone.now(), approved_at=timezone.now() if status == 'approved' else None, **kwargs)
