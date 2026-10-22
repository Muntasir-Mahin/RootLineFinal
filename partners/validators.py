import io
import warnings
from pathlib import Path
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image, ImageOps, UnidentifiedImageError


MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_GALLERY_IMAGES = 12
MAX_PRODUCT_IMAGES = 6


def validate_image(upload):
    if upload.size > MAX_UPLOAD_BYTES:
        raise ValidationError('Choose a JPG, PNG or WebP image no larger than 5 MB.')
    position = upload.tell()
    try:
        upload.seek(0)
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(upload) as image:
                if image.format not in ('JPEG', 'PNG', 'WEBP') or image.width * image.height > 16_000_000:
                    raise ValidationError('Use a JPG, PNG or WebP image below 16 megapixels.')
                image.verify()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError,
            Image.DecompressionBombWarning):
        raise ValidationError('Choose a valid JPG, PNG or WebP image.')
    finally:
        upload.seek(position)


def validate_document(upload):
    if upload.size > MAX_UPLOAD_BYTES:
        raise ValidationError('Files must be no larger than 5 MB.')
    position = upload.tell()
    upload.seek(0)
    header = upload.read(5)
    upload.seek(position)
    if Path(upload.name).suffix.lower() == '.pdf' and header == b'%PDF-':
        return
    validate_image(upload)


def clean_upload(upload, *, document=False):
    if not upload or not hasattr(upload, 'temporary_file_path') and not hasattr(upload, 'content_type'):
        return upload
    if document:
        validate_document(upload)
        if Path(upload.name).suffix.lower() == '.pdf':
            upload.seek(0)
            return SimpleUploadedFile(f'{uuid4().hex}.pdf', upload.read(), content_type='application/pdf')
    validate_image(upload)
    upload.seek(0)
    with Image.open(upload) as source:
        image = ImageOps.exif_transpose(source).convert('RGB')
        image.thumbnail((2400, 2400))
        result = io.BytesIO()
        image.save(result, format='JPEG', quality=88)
    return SimpleUploadedFile(f'{uuid4().hex}.jpg', result.getvalue(), content_type='image/jpeg')
