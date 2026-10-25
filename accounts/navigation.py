from django.utils.http import url_has_allowed_host_and_scheme


def internal_next(value, fallback=''):
    if isinstance(value, str) and value.startswith('/') and url_has_allowed_host_and_scheme(value, allowed_hosts=set()):
        return value
    return fallback
