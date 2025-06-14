from django.db import models
from accounts.models import User
from django.utils import timezone
from datetime import timedelta


class InvestorAccount(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='investor_account')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - Balance: ${self.balance}"



# This model represents different investment packages available to users.
class InvestmentPackage(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=12, decimal_places=2, help_text="Fixed investment amount for this package")
    roi_percent = models.DecimalField(max_digits=5, decimal_places=2, help_text="Daily ROI in percent")
    duration_days = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.roi_percent}% daily for {self.duration_days} days - ${self.price}"




# This model tracks user investments in different investment packages.
class UserInvestment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    package = models.ForeignKey('InvestmentPackage', on_delete=models.CASCADE)
    roi_percent = models.DecimalField(max_digits=5, decimal_places=2)
    total_expected_return = models.DecimalField(max_digits=12, decimal_places=2)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    deposit = models.OneToOneField('main.Deposit', null=True, blank=True, on_delete=models.CASCADE, related_name='user_investment')

    def __str__(self):
        return f"{self.user} - {self.package.name}"

    def calculate_daily_roi(self):
        return (self.package.price * self.roi_percent) / 100

    def save(self, *args, **kwargs):
        # Auto-fill fields based on selected package
        if not self.pk:
            self.roi_percent = self.package.roi_percent
            self.total_expected_return = (
                self.package.price * (self.roi_percent / 100) * self.package.duration_days
            )
            self.end_date = self.start_date + timedelta(days=self.package.duration_days)
        super().save(*args, **kwargs)
    
    @property
    def days_passed(self):
        return (timezone.now() - self.start_date).days

    @property
    def days_remaining(self):
        return (self.end_date - timezone.now()).days


# This model tracks the returns on investments made by users.
class InvestmentReturn(models.Model):
    investment = models.ForeignKey(UserInvestment, on_delete=models.CASCADE, related_name='returns')
    date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    is_paid = models.BooleanField(default=False)

    class Meta:
        unique_together = ('investment', 'date')

    

    def __str__(self):
        return f"{self.investment.user} - {self.date} - ${self.amount}"



class InvestmentWithdrawal(models.Model):
    investor = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    investor_account = models.ForeignKey(InvestorAccount, on_delete=models.CASCADE)
    destination_wallet = models.ForeignKey('main.Wallet', on_delete=models.CASCADE)
    is_processed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.investor.email} - ${self.amount} to {self.destination_wallet.account_type}"

