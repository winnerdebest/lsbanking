from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import ProfileUpdateForm

@login_required
def account_settings_view(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('account_settings')
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = ProfileUpdateForm(instance=request.user)

    return render(request, 'accounts/settings.html', {'form': form})
