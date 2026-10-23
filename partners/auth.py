import re

from django.contrib.auth import authenticate
from django.core.cache import cache

from .models import CompanyProfile


def authenticate_legacy_company(request, identifier, password):
    """Keep old email credentials usable without renaming or migrating accounts."""
    if not identifier or '@' not in identifier:
        return None
    from hashlib import sha256
    key = 'partners:legacy-login:' + sha256(request.META.get('REMOTE_ADDR', '').encode()).hexdigest()
    attempts = cache.get(key, 0)
    cache.set(key, attempts + 1, 300)
    if attempts >= 20:
        return None
    company = CompanyProfile.objects.select_related('user').filter(email__iexact=identifier.strip()).first()
    if company and re.fullmatch(r'partner-[0-9a-f]{32}', company.user.get_username()):
        return authenticate(request, username=company.user.get_username(), password=password)
