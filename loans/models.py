from django.db import models
from accounts.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

class LoanType(models.Model):
    """Different types of loans available"""
    name = models.CharField(max_length=100)
    min_rate = models.DecimalField(max_digits=5, decimal_places=2, help_text="Minimum APR")
    max_rate = models.DecimalField(max_digits=5, decimal_places=2, help_text="Maximum APR")
    icon = models.CharField(max_length=50, default='fas fa-file-invoice-dollar')
    description = models.CharField(max_length=200)
    full_description = models.TextField()
    min_amount = models.DecimalField(max_digits=10, decimal_places=2, default=1000.00)
    max_amount = models.DecimalField(max_digits=10, decimal_places=2, default=100000.00)
    max_term_months = models.IntegerField(default=72)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    def get_rate_display(self):
        return f"{self.min_rate}% - {self.max_rate}% APR"


class LoanApplication(models.Model):
    """Loan application submitted by users"""
    
    STATUS_CHOICES = [
        ('pending_payment', 'Pending Payment'),
        ('payment_completed', 'Payment Completed'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loan_applications')
    loan_type = models.ForeignKey(LoanType, on_delete=models.PROTECT)
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('1000.00'))]
    )
    term_months = models.IntegerField(
        validators=[MinValueValidator(12), MaxValueValidator(72)]
    )
    purpose = models.TextField()
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    monthly_payment = models.DecimalField(max_digits=10, decimal_places=2)
    total_interest = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Processing fee (5% of loan amount)
    processing_fee = models.DecimalField(max_digits=10, decimal_places=2)
    processing_fee_paid = models.BooleanField(default=False)
    processing_fee_payment_date = models.DateTimeField(null=True, blank=True)
    processing_fee_transaction_id = models.CharField(max_length=100, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_payment')
    application_number = models.CharField(max_length=20, unique=True, editable=False)
    
    # Review fields
    reviewed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='reviewed_loan_applications'
    )
    review_date = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['application_number']),
        ]
    
    def __str__(self):
        return f"{self.application_number} - {self.user.username} - {self.loan_type.name}"
    
    def save(self, *args, **kwargs):
        # Generate application number if not exists
        if not self.application_number:
            import random
            import string
            prefix = self.loan_type.name[:2].upper()
            random_suffix = ''.join(random.choices(string.digits, k=6))
            self.application_number = f"{prefix}-{random_suffix}"
        
        # Calculate processing fee (5% of loan amount)
        self.processing_fee = self.amount * Decimal('0.05')
        
        super().save(*args, **kwargs)
    
    def get_total_repayment(self):
        """Calculate total amount to be repaid"""
        return self.monthly_payment * self.term_months


class Loan(models.Model):
    """Active/Approved loans"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('current', 'Current'),
        ('late', 'Late'),
        ('defaulted', 'Defaulted'),
        ('paid_off', 'Paid Off'),
        ('closed', 'Closed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loans')
    application = models.OneToOneField(LoanApplication, on_delete=models.PROTECT)
    loan_type = models.ForeignKey(LoanType, on_delete=models.PROTECT)
    
    loan_number = models.CharField(max_length=20, unique=True)
    original_amount = models.DecimalField(max_digits=10, decimal_places=2)
    current_balance = models.DecimalField(max_digits=10, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    term_months = models.IntegerField()
    monthly_payment = models.DecimalField(max_digits=10, decimal_places=2)
    
    disbursement_date = models.DateField()
    first_payment_date = models.DateField()
    next_payment_date = models.DateField()
    maturity_date = models.DateField()
    
    total_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payments_made = models.IntegerField(default=0)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['loan_number']),
        ]
    
    def __str__(self):
        return f"{self.loan_number} - {self.user.username}"
    
    def save(self, *args, **kwargs):
        # Generate loan number if not exists
        if not self.loan_number:
            import random
            import string
            prefix = self.loan_type.name[:2].upper()
            random_suffix = ''.join(random.choices(string.digits, k=4))
            self.loan_number = f"{prefix}-{random_suffix}"
        
        super().save(*args, **kwargs)
    
    def get_progress_percentage(self):
        """Calculate loan repayment progress"""
        if self.original_amount == 0:
            return 0
        return ((self.original_amount - self.current_balance) / self.original_amount) * 100


class LoanPayment(models.Model):
    """Payment records for loans"""
    
    PAYMENT_TYPE_CHOICES = [
        ('regular', 'Regular Payment'),
        ('extra', 'Extra Payment'),
        ('processing_fee', 'Processing Fee'),
    ]
    
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='payments', null=True, blank=True)
    application = models.ForeignKey(LoanApplication, on_delete=models.CASCADE, related_name='payments', null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES, default='regular')
    payment_date = models.DateTimeField(auto_now_add=True)
    transaction_id = models.CharField(max_length=100, unique=True)
    
    principal_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    interest_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-payment_date']
        indexes = [
            models.Index(fields=['user', 'payment_date']),
            models.Index(fields=['transaction_id']),
        ]
    
    def __str__(self):
        return f"Payment {self.transaction_id} - ${self.amount}"