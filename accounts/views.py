from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from .forms import ProfileUpdateForm, TransactionPINForm
from .models import TransactionPIN

@login_required
def account_settings_view(request):
    profile_form = ProfileUpdateForm(request.POST or None, request.FILES or None, instance=request.user)
    pin_form = TransactionPINForm(request.POST or None)

    
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if 'set_pin' in request.POST:
            if pin_form.is_valid():
                pin = pin_form.cleaned_data['pin']
                pin_obj, _ = TransactionPIN.objects.get_or_create(user=request.user)
                try:
                    pin_obj.set_pin(pin)
                    return JsonResponse({
                        'success': True,
                        'message': 'Transaction PIN set successfully.'
                    })
                except ValidationError as ve:
                    return JsonResponse({
                        'success': False,
                        'message': str(ve.message)
                    }, status=400)
                except Exception as e:
                    return JsonResponse({
                        'success': False,
                        'message': f"An unexpected error occurred: {str(e)}"
                    }, status=500)
            else:
                return JsonResponse({
                    'success': False,
                    'message': ' '.join([' '.join(err) for err in pin_form.errors.values()])
                }, status=400)

    
    if request.method == 'POST':
        if 'update_profile' in request.POST and profile_form.is_valid():
            profile_form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('account_settings')

        elif 'set_pin' in request.POST and pin_form.is_valid():
            pin = pin_form.cleaned_data['pin']
            pin_obj, _ = TransactionPIN.objects.get_or_create(user=request.user)
            try:
                pin_obj.set_pin(pin)
                messages.success(request, 'Transaction PIN set successfully.')
            except Exception as e:
                messages.error(request, str(e))
            return redirect('account_settings')

        messages.error(request, 'Please fix the errors below.')

    return render(request, 'accounts/settings.html', {
        'form': profile_form,
        'pin_form': pin_form,
    })
