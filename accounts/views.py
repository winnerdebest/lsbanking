from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from .forms import ProfileUpdateForm, TransactionPINForm
from .models import TransactionPIN, KYC

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




# KYC Views
from django.utils import timezone
from django.contrib import messages

@login_required
def kyc_submission_view(request):
    user = request.user
    try:
        kyc = KYC.objects.get(user=user)
    except KYC.DoesNotExist:
        kyc = None

    if kyc and kyc.status in ['pending', 'approved']:
        messages.info(request, "You cannot edit your KYC while it is under review or already approved.")
        return redirect('account_settings')  # fix the typo if needed

    if request.method == "POST":
        if not kyc:
            kyc = KYC(user=user)

        kyc.full_name = request.POST.get('full_name')
        kyc.date_of_birth = request.POST.get('date_of_birth')
        kyc.address = request.POST.get('address')
        kyc.city = request.POST.get('city')
        kyc.state = request.POST.get('state')
        kyc.zip_code = request.POST.get('zip_code')
        kyc.occupation = request.POST.get('occupation')
        kyc.id_type = request.POST.get('id_type')
        kyc.id_number = request.POST.get('id_number')
        kyc.id_expiry_date = request.POST.get('id_expiry_date')

        if 'id_document' in request.FILES:
            kyc.id_document = request.FILES['id_document']
        if 'selfie_with_id' in request.FILES:
            kyc.selfie_with_id = request.FILES['selfie_with_id']
        if 'proof_of_address' in request.FILES:
            kyc.proof_of_address = request.FILES['proof_of_address']

        kyc.status = 'pending'
        kyc.submitted_at = timezone.now()
        kyc.reviewed_at = None
        kyc.save()

        messages.success(request, "KYC submitted successfully. Please wait for approval.")
        return redirect('account_settings')

    return render(request, "kyc/kyc_form.html", {"kyc": kyc})
