from django.conf import settings


def site_contact(request):
    return {'contact_email': settings.ROOTLINE_CONTACT_EMAIL}
