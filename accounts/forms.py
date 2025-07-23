from allauth.account.forms import SignupForm
from django import forms
from .models import User



class CustomSignupForm(SignupForm):
    full_name = forms.CharField(max_length=255, required=True)

    def save(self, request):
        user = super().save(request)
        user.full_name = self.cleaned_data['full_name']
        user.save()
        return user


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['full_name', 'email', 'phone', 'profile_picture']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'phone': forms.TextInput(attrs={'class': 'form-input'}),
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'form-input'}),
        }


import re

class TransactionPINForm(forms.Form):
    pin = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter 4-digit PIN'}),
        max_length=4,
        min_length=4,
        label='Transaction PIN'
    )
    confirm_pin = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm PIN'}),
        max_length=4,
        min_length=4,
        label='Confirm PIN'
    )

    def clean_pin(self):
        pin = self.cleaned_data.get('pin')
        if not re.fullmatch(r'\d{4}', pin):
            raise forms.ValidationError("PIN must be exactly 4 digits.")
        return pin

    def clean(self):
        cleaned_data = super().clean()
        pin = cleaned_data.get('pin')
        confirm = cleaned_data.get('confirm_pin')
        if pin and confirm and pin != confirm:
            raise forms.ValidationError("PINs do not match.")
        return cleaned_data
