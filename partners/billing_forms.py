from django import forms

from .forms import UploadFormMixin


class InvoicePaymentForm(UploadFormMixin, forms.Form):
    reference = forms.CharField(max_length=200, label='Payment reference / transaction ID')
    screenshot = forms.ImageField(required=False, label='Optional payment screenshot (private, up to 5 MB)')
