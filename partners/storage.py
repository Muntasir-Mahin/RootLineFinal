from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.deconstruct import deconstructible


@deconstructible
class PartnerPrivateStorage(FileSystemStorage):
    """Payment evidence is outside MEDIA_ROOT and has no public URL."""
    def __init__(self):
        super().__init__(location=settings.BASE_DIR / 'private_partner_files')

    def url(self, name):
        raise ValueError('Use the authenticated payment-proof download view.')
