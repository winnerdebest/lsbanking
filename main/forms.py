from django import forms
from .models import *
from django.core.validators import MinValueValidator

class BankDepositForm(forms.ModelForm):
    amount = forms.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(10.00)],
        widget=forms.NumberInput(attrs={'placeholder': '0.00'})
    )
    
    class Meta:
        model = Deposit
        fields = ['amount', 'proof_image', 'note']
        widgets = {
            'note': forms.Textarea(attrs={'rows': 3}),
        }



class GiftCardDepositForm(forms.ModelForm):
    card_number = forms.CharField(max_length=20)
    pin = forms.CharField(max_length=4, required=False)
    amount = forms.DecimalField(
        max_digits=10, 
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={'placeholder': '0.00'})
    )
    
    class Meta:
        model = Deposit
        fields = ['proof_image', 'note']
        widgets = {
            'note': forms.Textarea(attrs={'rows': 3}),
        }

class CashAppDepositForm(forms.ModelForm):
    amount = forms.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(1.00)],
        widget=forms.NumberInput(attrs={'placeholder': '0.00'})
    )
    cashapp_tag = forms.CharField(max_length=50)
    
    class Meta:
        model = Deposit
        fields = ['amount', 'proof_image', 'note']
        widgets = {
            'note': forms.Textarea(attrs={'rows': 3}),
        }

class CryptoDepositForm(forms.ModelForm):
    amount = forms.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(10.00)],
        widget=forms.NumberInput(attrs={'placeholder': '0.00'})
    )
    crypto_type = forms.ChoiceField(choices=[
        ('BTC', 'Bitcoin'),
    ])
    
    class Meta:
        model = Deposit
        fields = ['amount', 'note']
        widgets = {
            'note': forms.Textarea(attrs={'rows': 3}),
        }