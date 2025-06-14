from django.contrib import admin
from .models import *




@admin.register(InvestorAccount)
class InvestorAccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'last_updated')
    search_fields = ('user__email',)


# --- InvestmentPackage Admin Configuration ---
@admin.register(InvestmentPackage)
class InvestmentPackageAdmin(admin.ModelAdmin):


    list_display = (
        'name',
        'price',
        'roi_percent',
        'duration_days',
        'is_active'
    )
    
    search_fields = (
        'name',
    )
    
    list_filter = (
        'is_active',
        'duration_days',
    )
    
    readonly_fields = ()


# --- UserInvestment Admin Configuration ---
@admin.register(UserInvestment)
class UserInvestmentAdmin(admin.ModelAdmin):

    list_display = (
        'user',
        'package',
        'roi_percent',
        'total_expected_return',
        'start_date',
        'end_date',
        'status',
        'created_at'
    )

    search_fields = (
        'user__email',
        'package__name',
        'status'
    )

    list_filter = (
        'status',
        'package',
        'start_date',
        'end_date'
    )

    readonly_fields = (
        'roi_percent',
        'total_expected_return',
        'end_date',
        'created_at'
    )


# --- InvestmentReturn Admin Configuration ---
@admin.register(InvestmentReturn)
class InvestmentReturnAdmin(admin.ModelAdmin):

    list_display = (
        'investment',
        'date',
        'amount',
        'is_paid'
    )

    search_fields = (
        'investment__user__email',
        'date',
    )

    list_filter = (
        'is_paid',
        'date',
        'investment__package', 
    )
    
    readonly_fields = ()

