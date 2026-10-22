from uuid import uuid4

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.functions import Lower
from django.urls import reverse
from django.utils.text import slugify

from .validators import MAX_GALLERY_IMAGES, validate_document, validate_image


def new_slug(value):
    return f'{slugify(value)[:65] or "partner"}-{uuid4().hex[:10]}'


class PartnerCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'partner categories'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = new_slug(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class CompanyQuerySet(models.QuerySet):
    def public(self):
        return self.filter(status='approved', is_active=True, is_suspended=False, user__is_active=True)


class CompanyProfile(models.Model):
    STATUS_CHOICES = [('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')]
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='partner_company')
    name = models.CharField(max_length=160, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    address = models.TextField(max_length=1000)
    district = models.CharField(max_length=100)
    division = models.CharField(max_length=100)
    trade_license = models.CharField(max_length=100, blank=True)
    logo = models.ImageField(upload_to='partners/logos/', blank=True, validators=[validate_image])
    cover_image = models.ImageField(upload_to='partners/covers/', blank=True, validators=[validate_image])
    tagline = models.CharField(max_length=200, blank=True)
    about = models.TextField(max_length=12000, blank=True)
    established_year = models.PositiveSmallIntegerField(null=True, blank=True,
        validators=[MinValueValidator(1800), MaxValueValidator(2100)])
    why_choose_us = models.TextField(max_length=3000, blank=True, help_text='One reason per line.')
    website = models.URLField(blank=True)
    facebook = models.URLField(blank=True)
    maps_url = models.URLField(blank=True)
    categories = models.ManyToManyField(PartnerCategory, blank=True, related_name='companies')
    employees = models.PositiveIntegerField(null=True, blank=True)
    farmers_supported = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='pending')
    rejection_reason = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    is_suspended = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    approved_at = models.DateTimeField(null=True, blank=True)
    terms_accepted_at = models.DateTimeField()
    terms_version = models.CharField(max_length=40, default='draft-v1')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CompanyQuerySet.as_manager()

    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(Lower('email'), name='partner_unique_login_email'),
            models.UniqueConstraint(Lower('name'), name='partner_unique_company_name'),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = new_slug(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('partners:store', args=[self.slug])

    @property
    def reasons(self):
        return [line.strip() for line in self.why_choose_us.splitlines() if line.strip()]

    @property
    def can_publish(self):
        return self.status == 'approved' and self.is_active and not self.is_suspended and self.user.is_active

    def __str__(self):
        return self.name


class Achievement(models.Model):
    company = models.ForeignKey(CompanyProfile, on_delete=models.CASCADE, related_name='achievements')
    title = models.CharField(max_length=200)
    year = models.PositiveSmallIntegerField(validators=[MinValueValidator(1800), MaxValueValidator(2100)])
    description = models.TextField(max_length=4000, blank=True)
    image = models.ImageField(upload_to='partners/achievements/', blank=True, validators=[validate_image])

    class Meta:
        ordering = ['-year', 'pk']

    def __str__(self):
        return self.title


class Certification(models.Model):
    company = models.ForeignKey(CompanyProfile, on_delete=models.CASCADE, related_name='certifications')
    title = models.CharField(max_length=200)
    issuer = models.CharField(max_length=200)
    file = models.FileField(upload_to='partners/certifications/', blank=True, validators=[validate_document])

    def __str__(self):
        return self.title


class GalleryImage(models.Model):
    company = models.ForeignKey(CompanyProfile, on_delete=models.CASCADE, related_name='gallery')
    image = models.ImageField(upload_to='partners/gallery/', validators=[validate_image])
    caption = models.CharField(max_length=200, blank=True)

    def clean(self):
        super().clean()
        if self.company_id and GalleryImage.objects.filter(company_id=self.company_id).exclude(pk=self.pk).count() >= MAX_GALLERY_IMAGES:
            raise ValidationError(f'Keep at most {MAX_GALLERY_IMAGES} gallery images.')

    def __str__(self):
        return self.caption or f'{self.company} gallery image'


class PartnerAuditLog(models.Model):
    company = models.ForeignKey(CompanyProfile, on_delete=models.PROTECT, related_name='audit_logs')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=80)
    target = models.CharField(max_length=160)
    reason = models.TextField(blank=True)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-pk']

    def __str__(self):
        return f'{self.action}: {self.company}'
