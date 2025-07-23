from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, TransactionPIN


class TransactionPINInline(admin.StackedInline):
    model = TransactionPIN
    can_delete = True
    readonly_fields = ('masked_pin_display',)
    extra = 0

    def masked_pin_display(self, obj):
        return '•••••• (hashed)'
    masked_pin_display.short_description = "PIN"


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('full_name', 'phone', 'profile_picture')}),
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
    list_display = ('email', 'full_name', 'is_staff', 'is_email_verified', 'is_suspended')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'is_email_verified', 'is_suspended', 'groups')
    search_fields = ('email', 'full_name', 'phone')
    ordering = ('-date_joined',)