from django.db.models.signals import post_save
from django.dispatch import receiver
from accounts.models import User
from investments.models import *

@receiver(post_save, sender=User)
def create_investor_account(sender, instance, created, **kwargs):
    if created:
        InvestorAccount.objects.create(user=instance)




from investments.models import UserInvestment
from main.models import Deposit
from django.utils import timezone
from datetime import timedelta

@receiver(post_save, sender=Deposit)
def handle_deposit_investment(sender, instance, created, **kwargs):
    if not instance.related_package:
        return  # Skip if no package was selected

    if created:
        # Create a pending investment immediately
        if not hasattr(instance, 'user_investment'):
            UserInvestment.objects.create(
                user=instance.user,
                package=instance.related_package,
                roi_percent=instance.related_package.roi_percent,
                total_expected_return=(
                    instance.related_package.price *
                    (instance.related_package.roi_percent / 100) *
                    instance.related_package.duration_days
                ),
                end_date=timezone.now() + timedelta(days=instance.related_package.duration_days),
                deposit=instance,
                status='pending'
            )
    else:
        # If already created, and now approved, activate it
        if instance.status == 'approved' and hasattr(instance, 'user_investment'):
            investment = instance.user_investment
            if investment.status != 'active':
                investment.status = 'active'
                investment.start_date = timezone.now()
                investment.end_date = investment.start_date + timedelta(days=investment.package.duration_days)
                investment.save()
