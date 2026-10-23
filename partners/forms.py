from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Achievement, Certification, CompanyProduct, CompanyProductImage, CompanyProfile, GalleryImage
from .validators import clean_upload


class PartnerApplicationForm(forms.Form):
    company_name = forms.CharField(max_length=160)
    email = forms.EmailField(max_length=254)
    phone = forms.CharField(max_length=30)
    address = forms.CharField(max_length=1000, widget=forms.Textarea(attrs={'rows': 3}))
    district = forms.CharField(max_length=100)
    division = forms.CharField(max_length=100)
    trade_license = forms.CharField(max_length=100, required=False)
    trade_license_document = forms.FileField(required=False, help_text='PDF, JPG, PNG or WebP; up to 5 MB. Visible only to you and application reviewers.')
    agree_terms = forms.BooleanField(label='I agree to the Partner Terms')

    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.company = company

    def clean_company_name(self):
        name = self.cleaned_data['company_name'].strip()
        matches = CompanyProfile.objects.filter(name__iexact=name)
        if self.company:
            matches = matches.exclude(pk=self.company.pk)
        if matches.exists():
            raise ValidationError('A company with this name already exists.')
        return name

    def clean_trade_license_document(self):
        return clean_upload(self.cleaned_data.get('trade_license_document'), document=True)


class UploadFormMixin:
    def clean(self):
        data = super().clean()
        for name, value in list(data.items()):
            if isinstance(self.fields.get(name), forms.FileField) and value:
                try:
                    data[name] = clean_upload(value, document=name == 'file')
                except ValidationError as error:
                    self.add_error(name, error)
        return data


class CompanyProfileForm(UploadFormMixin, forms.ModelForm):
    class Meta:
        model = CompanyProfile
        fields = ['name', 'email', 'phone', 'address', 'district', 'division', 'trade_license',
                  'logo', 'cover_image', 'tagline', 'about', 'established_year', 'why_choose_us',
                  'website', 'facebook', 'maps_url', 'categories', 'employees', 'farmers_supported']
        widgets = {'about': forms.Textarea(attrs={'rows': 6}), 'address': forms.Textarea(attrs={'rows': 3}),
                   'why_choose_us': forms.Textarea(attrs={'rows': 4})}

    def clean_established_year(self):
        year = self.cleaned_data['established_year']
        if year and year > timezone.localdate().year:
            raise ValidationError('The established year cannot be in the future.')
        return year


class AchievementForm(UploadFormMixin, forms.ModelForm):
    class Meta:
        model = Achievement
        fields = ['title', 'year', 'description', 'image']


class CertificationForm(UploadFormMixin, forms.ModelForm):
    class Meta:
        model = Certification
        fields = ['title', 'issuer', 'file']


class GalleryImageForm(UploadFormMixin, forms.ModelForm):
    class Meta:
        model = GalleryImage
        fields = ['image', 'caption']


class CompanyProductForm(UploadFormMixin, forms.ModelForm):
    class Meta:
        model = CompanyProduct
        fields = ['name', 'category', 'price', 'discount_price', 'unit', 'stock_quantity',
                  'description', 'main_image', 'is_active']


class CompanyProductImageForm(UploadFormMixin, forms.ModelForm):
    class Meta:
        model = CompanyProductImage
        fields = ['image', 'caption']
