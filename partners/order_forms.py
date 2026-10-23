from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone


class OrderRequestForm(forms.Form):
    quantity = forms.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('0.01'), initial=1)
    delivery_address = forms.CharField(max_length=1000, widget=forms.Textarea(attrs={'rows': 3}))
    phone = forms.CharField(max_length=30)
    note = forms.CharField(max_length=2000, required=False, widget=forms.Textarea(attrs={'rows': 3}))


class CompleteOrderForm(forms.Form):
    final_amount = forms.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal('0.01'))
    reason = forms.CharField(required=False, max_length=3000, label='Reason if the final sold amount changed',
                             widget=forms.Textarea(attrs={'rows': 3}))


class AmountDisputeForm(forms.Form):
    claimed_amount = forms.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal('0.01'), required=False)
    reason = forms.CharField(max_length=3000, widget=forms.Textarea(attrs={'rows': 3}))


class ManualSaleForm(forms.Form):
    amount = forms.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal('0.01'))
    sale_date = forms.DateField(initial=timezone.localdate, widget=forms.DateInput(attrs={'type': 'date'}))
    reference = forms.CharField(max_length=200, label='Sale reference / description')

    def clean_sale_date(self):
        value = self.cleaned_data['sale_date']
        if value > timezone.localdate():
            raise ValidationError('A sale cannot be in the future.')
        return value
