from uuid import uuid4
from decimal import Decimal

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


class CompanyProduct(models.Model):
    UNIT_CHOICES = [('kg', 'kg'), ('litre', 'litre'), ('bag', 'bag'), ('piece', 'piece')]
    company = models.ForeignKey(CompanyProfile, on_delete=models.PROTECT, related_name='products')
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=100, blank=True)
    category = models.ForeignKey(PartnerCategory, on_delete=models.PROTECT, related_name='products')
    price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    discount_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True,
                                        validators=[MinValueValidator(Decimal('0.01'))])
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='kg')
    stock_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0,
                                         validators=[MinValueValidator(0)])
    description = models.TextField(max_length=12000)
    main_image = models.ImageField(upload_to='partners/products/', blank=True, validators=[validate_image])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at', '-pk']
        constraints = [
            models.UniqueConstraint(fields=['company', 'slug'], name='partner_product_unique_slug'),
            models.CheckConstraint(condition=models.Q(price__gt=0), name='partner_product_positive_price'),
            models.CheckConstraint(condition=models.Q(stock_quantity__gte=0), name='partner_product_nonnegative_stock'),
            models.CheckConstraint(condition=models.Q(discount_price__isnull=True) |
                models.Q(discount_price__gt=0, discount_price__lt=models.F('price')), name='partner_product_valid_discount'),
        ]

    @property
    def sale_price(self):
        return self.discount_price if self.discount_price is not None else self.price

    def clean(self):
        super().clean()
        if self.discount_price is not None and self.price is not None and self.discount_price >= self.price:
            raise ValidationError({'discount_price': 'The discount price must be lower than the regular price.'})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = new_slug(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('partners:product_detail', args=[self.company.slug, self.slug])

    def __str__(self):
        return self.name


class CompanyProductImage(models.Model):
    product = models.ForeignKey(CompanyProduct, on_delete=models.CASCADE, related_name='extra_images')
    image = models.ImageField(upload_to='partners/product-extras/', validators=[validate_image])
    caption = models.CharField(max_length=200, blank=True)

    def clean(self):
        from .validators import MAX_PRODUCT_IMAGES
        super().clean()
        if self.product_id and CompanyProductImage.objects.filter(product_id=self.product_id).exclude(pk=self.pk).count() >= MAX_PRODUCT_IMAGES:
            raise ValidationError(f'Keep at most {MAX_PRODUCT_IMAGES} extra product images.')

    def __str__(self):
        return f'{self.product}: {self.caption or "extra image"}'


def order_number():
    return 'PR-' + uuid4().hex[:16].upper()


class OrderRequest(models.Model):
    STATUS_CHOICES = [('requested', 'Requested'), ('accepted', 'Accepted'), ('completed', 'Completed'),
                      ('declined', 'Declined'), ('cancelled', 'Cancelled by buyer')]
    number = models.CharField(max_length=24, unique=True, default=order_number, editable=False)
    company = models.ForeignKey(CompanyProfile, on_delete=models.PROTECT, related_name='order_requests')
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='partner_order_requests')
    product = models.ForeignKey(CompanyProduct, on_delete=models.PROTECT, related_name='order_requests')
    product_name = models.CharField(max_length=200)
    unit = models.CharField(max_length=10)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    expected_amount = models.DecimalField(max_digits=14, decimal_places=2)
    phone = models.CharField(max_length=30)
    delivery_address = models.TextField(max_length=1000)
    note = models.TextField(max_length=2000, blank=True)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='requested')
    decision_reason = models.TextField(blank=True)
    final_amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    amount_change_reason = models.TextField(blank=True)
    buyer_confirmed_at = models.DateTimeField(null=True, blank=True)
    buyer_dispute = models.TextField(blank=True)
    buyer_claimed_amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at', '-pk']
        constraints = [
            models.CheckConstraint(condition=models.Q(quantity__gt=0), name='partner_order_positive_quantity'),
            models.CheckConstraint(condition=models.Q(expected_amount__gt=0), name='partner_order_positive_total'),
        ]

    def __str__(self):
        return self.number


class SalesLedger(models.Model):
    SOURCE_CHOICES = [('order', 'Order Request'), ('manual', 'Manually reported')]
    company = models.ForeignKey(CompanyProfile, on_delete=models.PROTECT, related_name='ledger_entries')
    order = models.OneToOneField(OrderRequest, null=True, blank=True, on_delete=models.PROTECT, related_name='ledger_entry')
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES)
    original_amount = models.DecimalField(max_digits=14, decimal_places=2)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    sale_date = models.DateField()
    reference = models.CharField(max_length=200, blank=True)
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    buyer_confirmed_at = models.DateTimeField(null=True, blank=True)
    needs_review = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-sale_date', '-pk']
        constraints = [
            models.CheckConstraint(condition=models.Q(amount__gte=0), name='partner_ledger_nonnegative_amount'),
            models.CheckConstraint(condition=models.Q(source='order', order__isnull=False) |
                models.Q(source='manual', order__isnull=True), name='partner_ledger_source_matches_order'),
        ]

    def __str__(self):
        return f'{self.company}: {self.amount} on {self.sale_date}'


class LedgerAdjustment(models.Model):
    ledger = models.ForeignKey(SalesLedger, on_delete=models.PROTECT, related_name='adjustments')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    previous_amount = models.DecimalField(max_digits=14, decimal_places=2)
    new_amount = models.DecimalField(max_digits=14, decimal_places=2)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-pk']
