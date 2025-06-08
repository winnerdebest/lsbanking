from django.db import models
from accounts.models import User
import uuid
from decimal import Decimal


from django.conf import settings
from cloudinary.models import CloudinaryField



class Wallet(models.Model):
    ACCOUNT_TYPE_CHOICES = (
        ('CHECKING', 'Checking Account'),
        ('SAVINGS', 'Savings Account'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wallets')
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    currency = models.CharField(max_length=3, default='USD')
    account_number = models.CharField(max_length=20, unique=True, editable=False)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'account_type')
        ordering = ['user', 'account_type']

    def __str__(self):
        return f"{self.user.full_name} - {self.get_account_type_display()}"


class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('CREDIT', 'Credit'),  
        ('DEBIT', 'Debit'),   
    )

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.TextField(blank=True, null=True)

    deposit_method = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        help_text="e.g., ACH, Zelle, Transfer, Cash Deposit"
    )

    related_wallet = models.ForeignKey(  
        Wallet, on_delete=models.SET_NULL,
        blank=True, null=True,
        related_name='related_transactions'
    )

    reference_code = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']



class DepositAccount(models.Model):
    METHOD_CHOICES = [
        ('bank', 'Bank Transfer'),
        ('cashapp', 'Cash App'),
        ('crypto', 'Crypto'),
    ]

    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    label = models.CharField(max_length=100, help_text="e.g. BTC Wallet 1, CashApp Tag 2")

    # Common fields
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # Bank fields
    account_name = models.CharField(max_length=100, blank=True, null=True)
    account_number = models.CharField(max_length=100, blank=True, null=True)
    bank_name = models.CharField(max_length=100, blank=True, null=True)

    # Crypto fields
    crypto_type = models.CharField(max_length=20, blank=True, null=True)  # e.g., BTC, ETH
    crypto_address = models.CharField(max_length=200, blank=True, null=True)

    # Cash App field
    cashapp_tag = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.get_method_display()} - {self.label}"

    class Meta:
        verbose_name = "Deposit Destination"
        verbose_name_plural = "Deposit Destinations"

    def clean(self):
        # Optionally enforce: only one active per method
        from django.core.exceptions import ValidationError
        if self.is_active:
            others = DepositAccount.objects.filter(method=self.method, is_active=True).exclude(pk=self.pk)
            if others.exists():
                raise ValidationError(f"Only one active {self.get_method_display()} account is allowed.")


class Deposit(models.Model):
    METHOD_CHOICES = [
        ('bank', 'Bank Transfer'),
        ('giftcard', 'Gift Card'),
        ('cashapp', 'Cash App'),
        ('crypto', 'Crypto'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('failed', 'Failed'),
        ('unavailable', 'Unavailable'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='deposits')
    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    wallet = models.ForeignKey('Wallet', on_delete=models.SET_NULL, null=True, blank=True, related_name='deposits')
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    note = models.TextField(blank=True, null=True)
    if settings.USE_CLOUDINARY:
        proof_image = CloudinaryField('deposit_proofs/', transformation=[
                {'width': 800, 'height': 800, 'crop': 'limit', 'quality': 'auto', 'fetch_format': 'webp'}
            ], default='static/default_field.png')
    else:
        proof_image = models.ImageField(upload_to='deposit_proofs/', blank=True, null=True)
    giftcard_pin = models.CharField(max_length=64, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.full_name} - {self.method} - {self.status} - {self.amount or 'N/A'}"



