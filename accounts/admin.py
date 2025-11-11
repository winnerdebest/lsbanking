from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import User, TransactionPIN, KYC


# --- Inline for Transaction PIN ---
class TransactionPINInline(admin.StackedInline):
    model = TransactionPIN
    can_delete = True
    readonly_fields = ('masked_pin_display',)
    extra = 0

    def masked_pin_display(self, obj):
        return '•••••• (hashed)'
    masked_pin_display.short_description = "PIN"


# --- Custom User Admin ---
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('full_name', 'phone', 'profile_picture', 'profile_image_preview')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_email_verified', 'is_suspended', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'phone', 'password1', 'password2'),
        }),
    )
    inlines = [TransactionPINInline]
    list_display = ('email', 'full_name', 'is_staff', 'is_email_verified', 'is_suspended', 'profile_picture_preview')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'is_email_verified', 'is_suspended', 'groups')
    search_fields = ('email', 'full_name', 'phone')
    ordering = ('-date_joined',)
    readonly_fields = ('profile_image_preview',)

    def profile_picture_preview(self, obj):
        """Small image preview for list_display"""
        if obj.profile_picture:
            return format_html(
                '<img src="{}" width="40" height="40" style="border-radius:50%; object-fit:cover;" />',
                obj.profile_picture.url
            )
        return "—"
    profile_picture_preview.short_description = 'Profile'

    def profile_image_preview(self, obj):
        """Larger preview in edit page"""
        if obj.profile_picture:
            return format_html(
                '<img src="{}" width="120" height="120" style="border-radius:50%; object-fit:cover; border:1px solid #ddd;" />',
                obj.profile_picture.url
            )
        return "No Image"
    profile_image_preview.short_description = 'Profile Preview'


# --- Custom KYC Admin ---
@admin.register(KYC)
class KYCAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'full_name', 'id_type', 'status', 'submitted_at', 'reviewed_at',
        'id_document_preview', 'selfie_with_id_preview'
    )
    list_filter = ('status', 'id_type', 'nationality')
    search_fields = ('user__email', 'full_name', 'id_number', 'address', 'city', 'state', 'zip_code')
    readonly_fields = ('submitted_at', 'reviewed_at', 'id_document_preview', 'selfie_with_id_preview', 'proof_of_address_preview')

    fieldsets = (
        (None, {
            'fields': (
                'user', 'full_name', 'date_of_birth', 'address', 'state', 'city', 'zip_code', 'nationality', 'occupation'
            )
        }),
        ('Government ID Info', {
            'fields': (
                'id_type', 'id_number', 'id_expiry_date',
                'id_document', 'id_document_preview',
                'selfie_with_id', 'selfie_with_id_preview',
                'proof_of_address', 'proof_of_address_preview'
            )
        }),
        ('KYC Status', {
            'fields': ('status', 'submitted_at', 'reviewed_at')
        }),
    )

    # --- Inline Previews ---
    def id_document_preview(self, obj):
        if obj.id_document:
            return format_html('<img src="{}" width="100" height="100" style="object-fit:cover; border:1px solid #ddd;" />', obj.id_document.url)
        return "—"
    id_document_preview.short_description = "ID Document"

    def selfie_with_id_preview(self, obj):
        if obj.selfie_with_id:
            return format_html('<img src="{}" width="100" height="100" style="object-fit:cover; border:1px solid #ddd;" />', obj.selfie_with_id.url)
        return "—"
    selfie_with_id_preview.short_description = "Selfie with ID"

    def proof_of_address_preview(self, obj):
        if obj.proof_of_address:
            return format_html('<img src="{}" width="100" height="100" style="object-fit:cover; border:1px solid #ddd;" />', obj.proof_of_address.url)
        return "—"
    proof_of_address_preview.short_description = "Proof of Address"
