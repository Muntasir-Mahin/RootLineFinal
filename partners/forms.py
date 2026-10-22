from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Achievement, Certification, CompanyProfile, GalleryImage
from .validators import clean_upload


class PartnerRegistrationForm(forms.Form):
    company_name = forms.CharField(max_length=160)
    email = forms.EmailField(max_length=254)
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}))
    password2 = forms.CharField(label='Confirm password', widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}))
    phone = forms.CharField(max_length=30)
    address = forms.CharField(max_length=1000, widget=forms.Textarea(attrs={'rows': 3}))
    district = forms.CharField(max_length=100)
    division = forms.CharField(max_length=100)
    trade_license = forms.CharField(max_length=100, required=False)
    agree_terms = forms.BooleanField(label='I agree to the Partner Terms')

    def clean(self):
        data = super().clean()
        if data.get('password1') != data.get('password2'):
            self.add_error('password2', 'The passwords do not match.')
        if data.get('password1'):
            from django.contrib.auth import get_user_model
            user = get_user_model()(email=data.get('email', ''))
            try:
                validate_password(data['password1'], user)
            except ValidationError as error:
                self.add_error('password1', error)
        return data


class PartnerLoginForm(forms.Form):
    email = forms.EmailField(max_length=254)
    password = forms.CharField(widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}))


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
