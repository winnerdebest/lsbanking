from decimal import Decimal
from django.db import transaction as db_transaction
from .models import *




class TransactionService:

    @staticmethod
    def deposit(wallet: Wallet, amount: Decimal, method='manual', description='Deposit'):
        if amount <= 0:
            raise ValueError("Deposit amount must be positive.")

        with db_transaction.atomic():
            wallet.balance += amount
            wallet.save(update_fields=['balance'])
            return Transaction.objects.create(
                wallet=wallet,
                transaction_type='CREDIT',
                amount=amount,
                deposit_method=method,
                description=description
            )

    @staticmethod
    def withdraw(wallet: Wallet, amount: Decimal, description='Withdrawal'):
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive.")
        if wallet.balance < amount:
            raise ValueError("Insufficient funds.")

        with db_transaction.atomic():
            wallet.balance -= amount
            wallet.save(update_fields=['balance'])
            return Transaction.objects.create(
                wallet=wallet,
                transaction_type='DEBIT',
                amount=amount,
                description=description
            )

    @staticmethod
    def transfer(source: Wallet, dest: Wallet, amount: Decimal, description='Internal Transfer'):
        if source.currency != dest.currency:
            raise ValueError("Currency mismatch.")
        if source == dest:
            raise ValueError("Cannot transfer to same wallet.")
        if source.balance < amount:
            raise ValueError("Insufficient funds.")

        with db_transaction.atomic():
            # Debit source
            source.balance -= amount
            source.save(update_fields=['balance'])
            source_tx = Transaction.objects.create(
                wallet=source,
                transaction_type='DEBIT',
                amount=amount,
                description=description,
                related_wallet=dest
            )

            # Credit destination
            dest.balance += amount
            dest.save(update_fields=['balance'])
            Transaction.objects.create(
                wallet=dest,
                transaction_type='CREDIT',
                amount=amount,
                description=description,
                related_wallet=source
            )

            # ✅ Return the sender's transaction so the calling view can reference it
            return source_tx
