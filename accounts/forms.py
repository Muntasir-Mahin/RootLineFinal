from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'username',
            'email',
            'phone_number',
            'address',
            'birth_date',
            'profile_picture',
        ]
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
        }


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
            'phone_number',
            'address',
            'birth_date',
            'profile_picture',
        ]
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
        }