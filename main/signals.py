import os
import mimetypes


from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.utils.html import format_html
from django.utils.crypto import get_random_string
from main.models import *
from accounts.models import User
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string



@receiver(post_save, sender=User)
def create_wallets_for_new_user(sender, instance, created, **kwargs):
    if created:
        account_types = ['CHECKING', 'SAVINGS']
        for acc_type in account_types:
            Wallet.objects.create(
                user=instance,
                account_type=acc_type,
                account_number=generate_unique_account_number()
            )

def generate_unique_account_number():
    from main.models import Wallet
    while True:
        number = get_random_string(length=10, allowed_chars='0123456789')
        if not Wallet.objects.filter(account_number=number).exists():
            return number



@receiver(post_save, sender=Deposit)
def notify_staff_on_deposit(sender, instance, created, **kwargs):
    if not created:
        return

    staff_emails = User.objects.filter(is_staff=True, is_active=True).exclude(email='').values_list('email', flat=True)
    if not staff_emails:
        return

    subject = "🧾 New Deposit Pending Approval"
    approve_url = f"{settings.SITE_URL}/admin/main/deposit/{instance.id}/change/"

    # Get Cloudinary image URL
    proof_image_url = instance.proof_image.url if instance.proof_image else None

    context = {
        'user': instance.user,
        'amount': instance.amount,
        'method': instance.method,
        'status': instance.status,
        'approve_url': approve_url,
        'created_at': instance.created_at,
        'proof_image_url': proof_image_url,
    }

    # Text-only fallback email
    text_content = f"""
New deposit submitted:

User: {instance.user.full_name} ({instance.user.email})
Amount: {instance.amount}
Method: {instance.method}
Status: {instance.status}
Submitted at: {instance.created_at}

Review and Approve: {approve_url}
"""

    html_content = render_to_string("emails/new_deposit.html", context)

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=list(staff_emails),
    )
    email.attach_alternative(html_content, "text/html")
    email.send(fail_silently=True)