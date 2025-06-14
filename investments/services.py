from decimal import Decimal
from django.utils import timezone
from main.services import TransactionService  # Adjust import if needed
from investments.models import InvestmentWithdrawal


class InvestmentService:

    @staticmethod
    def withdraw_investment_funds(user, destination_wallet):
        account = user.investor_account

        if account.balance < Decimal('1000.00'):
            raise ValueError("Minimum withdrawal threshold of $1000 not met.")

        # Check for matured investments (optional strict check)
        has_matured_investment = user.userinvestment_set.filter(
            status='completed'
        ).exists()

        if not has_matured_investment:
            raise ValueError("No matured investments available for withdrawal.")

        amount = account.balance

        # Deduct from investment balance
        account.balance = Decimal('0.00')
        account.save(update_fields=['balance'])

        # Deposit to user's bank wallet
        TransactionService.deposit(
            wallet=destination_wallet,
            amount=amount,
            method='Investment Payout',
            description='Withdrawal from investment account'
        )

        # Log the withdrawal
        InvestmentWithdrawal.objects.create(
            investor=user,
            amount=amount,
            investor_account=account,
            destination_wallet=destination_wallet,
            is_processed=True,
            created_at=timezone.now()
        )

        return amount
