from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import LoanType, LoanApplication, Loan, LoanPayment

@admin.register(LoanType)
class LoanTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'get_rate_display', 'min_amount', 'max_amount', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['is_active']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'icon', 'description', 'full_description')
        }),
        ('Rate & Limits', {
            'fields': ('min_rate', 'max_rate', 'min_amount', 'max_amount', 'max_term_months')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


@admin.register(LoanApplication)
class LoanApplicationAdmin(admin.ModelAdmin):
    list_display = ['application_number', 'user', 'loan_type', 'amount', 'status_badge', 'processing_fee_paid', 'created_at']
    list_filter = ['status', 'processing_fee_paid', 'loan_type', 'created_at']
    search_fields = ['application_number', 'user__username', 'user__email']
    readonly_fields = ['application_number', 'processing_fee', 'monthly_payment', 'total_interest', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Application Details', {
            'fields': ('application_number', 'user', 'loan_type', 'amount', 'term_months', 'purpose')
        }),
        ('Loan Calculations', {
            'fields': ('interest_rate', 'monthly_payment', 'total_interest')
        }),
        ('Processing Fee', {
            'fields': ('processing_fee', 'processing_fee_paid', 'processing_fee_payment_date', 'processing_fee_transaction_id')
        }),
        ('Status & Review', {
            'fields': ('status', 'reviewed_by', 'review_date', 'review_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'pending_payment': 'orange',
            'payment_completed': 'blue',
            'under_review': 'purple',
            'approved': 'green',
            'rejected': 'red',
            'cancelled': 'gray',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 5px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    actions = ['approve_applications', 'reject_applications']
    
    def approve_applications(self, request, queryset):
        updated = queryset.filter(status='under_review').update(
            status='approved',
            reviewed_by=request.user,
            review_date=timezone.now()
        )
        self.message_user(request, f'{updated} application(s) approved.')
    approve_applications.short_description = 'Approve selected applications'
    
    def reject_applications(self, request, queryset):
        updated = queryset.filter(status='under_review').update(
            status='rejected',
            reviewed_by=request.user,
            review_date=timezone.now()
        )
        self.message_user(request, f'{updated} application(s) rejected.')
    reject_applications.short_description = 'Reject selected applications'


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ['loan_number', 'user', 'loan_type', 'original_amount', 'current_balance', 'status_badge', 'next_payment_date']
    list_filter = ['status', 'loan_type', 'disbursement_date']
    search_fields = ['loan_number', 'user__username', 'user__email']
    readonly_fields = ['loan_number', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Loan Information', {
            'fields': ('loan_number', 'user', 'application', 'loan_type')
        }),
        ('Financial Details', {
            'fields': ('original_amount', 'current_balance', 'interest_rate', 'term_months', 'monthly_payment')
        }),
        ('Payment Tracking', {
            'fields': ('total_paid', 'payments_made')
        }),
        ('Dates', {
            'fields': ('disbursement_date', 'first_payment_date', 'next_payment_date', 'maturity_date')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'active': 'green',
            'current': 'blue',
            'late': 'orange',
            'defaulted': 'red',
            'paid_off': 'teal',
            'closed': 'gray',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 5px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'


@admin.register(LoanPayment)
class LoanPaymentAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'user', 'amount', 'payment_type', 'payment_date', 'loan_display']
    list_filter = ['payment_type', 'payment_date']
    search_fields = ['transaction_id', 'user__username', 'loan__loan_number']
    readonly_fields = ['transaction_id', 'payment_date', 'created_at']
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('transaction_id', 'user', 'loan', 'application', 'amount', 'payment_type')
        }),
        ('Payment Breakdown', {
            'fields': ('principal_amount', 'interest_amount')
        }),
        ('Additional Info', {
            'fields': ('notes', 'payment_date', 'created_at')
        }),
    )
    
    def loan_display(self, obj):
        if obj.loan:
            return obj.loan.loan_number
        elif obj.application:
            return f"App: {obj.application.application_number}"
        return "N/A"
    loan_display.short_description = 'Loan/Application'
