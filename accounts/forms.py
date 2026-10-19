from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = [
            'profile_picture',
            'first_name',
            'last_name',
            'birth_date',
            'age',
            'username',
            'email',
            'phone_number',
            'address',
        ]
        widgets = {
            'profile_picture': forms.FileInput(),
            'birth_date': forms.DateInput(attrs={'type': 'date', 'id': 'id_birth_date'}),
            'age': forms.NumberInput(attrs={'readonly': 'readonly', 'id': 'id_age', 'placeholder': 'Auto-calculated'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['age'].required = False


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'profile_picture',
            'first_name',
            'last_name',
            'birth_date',
            'age',
            'email',
            'phone_number',
            'address',
        ]
        widgets = {
            'profile_picture': forms.FileInput(),
            'birth_date': forms.DateInput(attrs={'type': 'date', 'id': 'id_birth_date'}),
            'age': forms.NumberInput(attrs={'readonly': 'readonly', 'id': 'id_age', 'placeholder': 'Auto-calculated'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['age'].required = False