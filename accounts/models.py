from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password

from django.conf import settings
from cloudinary.models import CloudinaryField


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    if settings.USE_CLOUDINARY:
        profile_picture = CloudinaryField('profile_pics/', transformation=[
                {'width': 800, 'height': 800, 'crop': 'limit', 'quality': 'auto', 'fetch_format': 'webp'}
            ],)
    else:
        profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    is_email_verified = models.BooleanField(default=False)
    is_suspended = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    objects = UserManager()

    def __str__(self):
        return self.email



# Pin User model

from django.core.exceptions import ValidationError
import re
# This is necessary for Transactions to have a pin before they can be created
class TransactionPIN(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="transaction_pin")
    pin_hash = models.CharField(max_length=128)

    def set_pin(self, raw_pin):
        if not re.fullmatch(r"\d{4}", raw_pin):
            raise ValidationError("PIN must be exactly 4 digits.")
        self.pin_hash = make_password(raw_pin)
        self.save()

    def check_pin(self, raw_pin):
        return check_password(raw_pin, self.pin_hash)

    def __str__(self):
        return f"PIN for {self.user.email}"


# KYC Verification Models
STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
]

ID_TYPE_CHOICES = [
    ('passport', 'U.S. Passport'),
    ('ssn', 'Social Security Number'),
    ('state_id', 'State ID'),
    ('driver_license', 'Driver’s License'),
    ('greencard', 'Green Card'),
]



class KYC(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # Basic Info
    full_name = models.CharField(max_length=255)
    date_of_birth = models.DateField()
    address = models.TextField()
    state = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    nationality = models.CharField(max_length=100, default='USA')
    occupation = models.CharField(max_length=255, blank=True, null=True)

    # Government ID Info
    id_type = models.CharField(max_length=50, choices=ID_TYPE_CHOICES)
    id_number = models.CharField(max_length=50)
    id_expiry_date = models.DateField(blank=True, null=True)

    if settings.USE_CLOUDINARY:
        id_document = CloudinaryField('kyc/id_documents/', transformation=[
            {'width': 1000, 'height': 1000, 'crop': 'limit', 'quality': 'auto', 'fetch_format': 'webp'}
        ])
        selfie_with_id = CloudinaryField('kyc/selfies/', transformation=[
            {'width': 1000, 'height': 1000, 'crop': 'limit', 'quality': 'auto', 'fetch_format': 'webp'}
        ])
        proof_of_address = CloudinaryField('kyc/proof_of_address/', transformation=[
            {'width': 1000, 'height': 1000, 'crop': 'limit', 'quality': 'auto', 'fetch_format': 'webp'}
        ])
    else:
        id_document = models.ImageField(upload_to='kyc/id_documents/', blank=True, null=True)
        selfie_with_id = models.ImageField(upload_to='kyc/selfies/', blank=True, null=True)
        proof_of_address = models.ImageField(upload_to='kyc/proof_of_address/', blank=True, null=True)

    # KYC Status
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = "KYC Verification"
        verbose_name_plural = "KYC Verifications"

    def __str__(self):
        return f"{self.user.email} - {self.status}"
