from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.forms import ModelForm
from .models import *

from .services import TransactionService
from django.utils.html import format_html
from decimal import Decimal
from django import forms
from datetime import timedelta
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import path
from .models import Wallet, Transaction
from django.urls import reverse
import random
import uuid

class ManualCreditForm(forms.Form):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    amount = forms.DecimalField(decimal_places=2, max_digits=12)
    description = forms.CharField(widget=forms.Textarea, required=False)
    deposit_method = forms.CharField(max_length=50, required=False)



@admin.action(description="Freeze selected wallets")
def freeze_wallets(modeladmin, request, queryset):
    queryset.update(is_active=False)





@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'account_type', 'account_number', 'currency', 'balance', 'is_active', 'created_at')
    list_filter = ('account_type', 'currency', 'is_active', 'user__is_suspended', 'user__is_active')
    search_fields = ('user__email', 'user__full_name', 'account_number')
    readonly_fields = ('created_at', 'updated_at', 'balance', 'account_number', 'seed_fake_transactions_button')
    ordering = ('user', 'account_type')
    actions = ['manual_credit', freeze_wallets]

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('manual-credit/', self.admin_site.admin_view(self.manual_credit_view), name='manual-credit'),
            path('seed-fake-transactions/<int:wallet_id>/', self.admin_site.admin_view(self.seed_fake_transactions_view), name='seed-fake-transactions'),
        ]
        return custom_urls + urls

    def manual_credit(self, request, queryset):
        selected = request.POST.getlist('_selected_action')
        return redirect(f'./manual-credit/?ids={",".join(selected)}')

    manual_credit.short_description = "Manually Credit Selected Wallets"

    def manual_credit_view(self, request):
        wallet_ids = request.GET.get('ids', '').split(',')
        wallets = Wallet.objects.filter(pk__in=wallet_ids)

        if request.method == 'POST':
            form = ManualCreditForm(request.POST)
            if form.is_valid():
                amount = form.cleaned_data['amount']
                description = form.cleaned_data['description']
                method = form.cleaned_data['deposit_method']

                for wallet in wallets:
                    wallet.balance += amount
                    wallet.save()

                    Transaction.objects.create(
                        wallet=wallet,
                        transaction_type='CREDIT',
                        amount=amount,
                        description=description or f"Manual credit via admin by {request.user}",
                        deposit_method=method or "Manual"
                    )
                self.message_user(request, f"Credited {len(wallets)} wallet(s) with ${amount}")
                return redirect('..')
        else:
            form = ManualCreditForm(initial={'_selected_action': wallet_ids})

        return render(request, 'admin/manual_credit.html', {
            'wallets': wallets,
            'form': form,
            'title': 'Manually Credit Wallets'
        })

    def seed_fake_transactions_button(self, obj):
        url = reverse('admin:seed-fake-transactions', args=[obj.pk])
        return format_html('<a class="button" href="{}">Seed Fake Transactions</a>', url)
        
    seed_fake_transactions_button.short_description = "Seed Transactions"

    def seed_fake_transactions_view(self, request, wallet_id):
        wallet = get_object_or_404(Wallet, pk=wallet_id)
        user = wallet.user

        descriptions = [
            "Transfer", "Deposit", "Venmo Payment", "PayPal Transaction", "Zelle Payment",
            "Wire Transfer", "ACH Transfer", "Crypto Trade", "Loan Payment", "Loan Disbursement",
            "Reimbursement", "Invoice", "Wallet Funding", "Wallet Withdrawal", "Stock Trade",
            "Bank Adjustment", "Payment", "P2P Transfer", "Account Credit", "Account Debit"
        ]

        methods = [
            "ACH Transfer", "Zelle Payment", "Wire Transfer", 
            "Direct Deposit", "Cash App Payment", "Bank Transfer", None
        ]
        
        other_wallets = Wallet.objects.exclude(id=wallet.id).order_by('?')[:10]

        now = timezone.now()
        txs = []
        running_balance = Decimal(wallet.balance)

        for _ in range(50):
            raw_tx_type = random.choices(['CREDIT', 'DEBIT'], weights=[3, 4])[0]
            amount = Decimal(random.randint(2000, 300000)) / Decimal("100")
            days_ago = random.randint(1, 730)
            created_at = now - timedelta(days=days_ago, hours=random.randint(0, 23), minutes=random.randint(0, 59))

            description = random.choice(descriptions)
            deposit_method = random.choice(methods) if raw_tx_type == "CREDIT" else None
            related_wallet = random.choice(other_wallets) if other_wallets and random.random() < 0.3 else None

            # Ensure balance never goes negative
            if raw_tx_type == 'DEBIT' and running_balance < amount:
                tx_type = 'CREDIT'
            else:
                tx_type = raw_tx_type

            tx = Transaction(
                wallet=wallet,
                transaction_type=tx_type,
                amount=amount,
                description=description,
                deposit_method=deposit_method if tx_type == 'CREDIT' else None,
                related_wallet=related_wallet if tx_type == 'DEBIT' else None,
                reference_code=str(uuid.uuid4()),
                created_at=created_at
            )

            txs.append(tx)
            running_balance += amount if tx_type == 'CREDIT' else -amount

        Transaction.objects.bulk_create(txs)
        wallet.balance = running_balance.quantize(Decimal("0.01"))
        wallet.save()

        self.message_user(
            request,
            f"✅ Seeded 50 transactions for {wallet.user.full_name}. New balance: ${wallet.balance}",
            messages.SUCCESS
        )
        return redirect(f"/admin/main/wallet/{wallet.id}/change/")




class DepositAccountForm(ModelForm):
    class Meta:
        model = DepositAccount
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        instance = self.instance

        if cleaned_data.get('is_active'):
            # Enforce only one active account per method
            existing = DepositAccount.objects.filter(
                method=cleaned_data.get('method'),
                is_active=True
            ).exclude(pk=instance.pk)
            if existing.exists():
                raise ValidationError(f"Only one active {instance.get_method_display()} account is allowed.")

        return cleaned_data


@admin.register(DepositAccount)
class DepositAccountAdmin(admin.ModelAdmin):
    form = DepositAccountForm

    list_display = ('label', 'method', 'is_active', 'created_at')
    list_filter = ('method', 'is_active', 'created_at')
    search_fields = ('label', 'account_name', 'account_number', 'crypto_address', 'cashapp_tag')
    readonly_fields = ('created_at',)

    fieldsets = (
        (None, {
            'fields': ('method', 'label', 'is_active', 'created_at')
        }),
        ('Bank Info', {
            'fields': ('account_name', 'account_number', 'bank_name'),
            'classes': ('collapse',),
        }),
        ('Crypto Info', {
            'fields': ('crypto_type', 'crypto_address'),
            'classes': ('collapse',),
        }),
        ('Cash App Info', {
            'fields': ('cashapp_tag',),
            'classes': ('collapse',),
        }),
    )



@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('wallet', 'transaction_type', 'amount', 'reference_code', 'deposit_method', 'created_at')
    list_filter = ('transaction_type', 'deposit_method', 'created_at')
    search_fields = ('wallet__user__email', 'wallet__account_number', 'reference_code')
    readonly_fields = ('reference_code', 'created_at')
    ordering = ('-created_at',)



@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    list_display = ('user', 'method', 'amount', 'status', 'wallet', 'created_at')
    list_filter = ('method', 'status', 'created_at')
    search_fields = ('user__email', 'user__full_name', 'amount')
    readonly_fields = ('created_at', 'proof_image')
    actions = ['mark_as_approved', 'mark_as_rejected']

    fieldsets = (
        ("Deposit Info", {
            'fields': ('user', 'wallet', 'method', 'amount', 'status', 'note')
        }),
        ("Proof of Payment", {
            'fields': ('proof_image',),
        }),
        ("Gift Card Info", {
            'fields': ('giftcard_pin',),
            'classes': ('collapse',),
        }),
        ("Timestamps", {
            'fields': ('created_at',),
        }),
    )

    def has_add_permission(self, request):
        return False

    def save_model(self, request, obj, form, change):
        # Detect transition to approved
        if change:
            previous = Deposit.objects.get(pk=obj.pk)
            if previous.status != 'approved' and obj.status == 'approved':
                self.process_approval(obj, request)
        super().save_model(request, obj, form, change)

    def process_approval(self, obj, request=None):
        if obj.wallet and obj.amount and obj.status == 'approved':
            # Prevent double-crediting
            already_credited = obj.wallet.transactions.filter(
                amount=obj.amount,
                transaction_type='CREDIT',
                description__icontains=f'Deposit'
            ).exists()

            if already_credited:
                if request:
                    self.message_user(request, f"{obj} already credited.", level=messages.WARNING)
                return

            try:
                TransactionService.deposit(
                    wallet=obj.wallet,
                    amount=Decimal(obj.amount),
                    method=obj.method,
                    description=f"Deposit approved"
                )
                if request:
                    self.message_user(request, f"{obj} credited successfully.", level=messages.SUCCESS)
            except Exception as e:
                if request:
                    self.message_user(request, f"Error crediting deposit: {str(e)}", level=messages.ERROR)

    @admin.action(description="✅ Approve selected deposits")
    def mark_as_approved(self, request, queryset):
        updated = 0
        for deposit in queryset.filter(status='pending'):
            deposit.status = 'approved'
            deposit.save()
            self.process_approval(deposit, request)
            updated += 1
        self.message_user(request, f"{updated} deposit(s) approved.")

    @admin.action(description="❌ Reject selected deposits")
    def mark_as_rejected(self, request, queryset):
        updated = queryset.filter(status='pending').update(status='rejected')
        self.message_user(request, f"{updated} deposit(s) rejected.")