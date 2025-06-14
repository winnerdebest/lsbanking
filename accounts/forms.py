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