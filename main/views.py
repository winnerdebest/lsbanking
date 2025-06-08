from django.shortcuts import render, get_object_or_404, redirect
from .models import *
from accounts.models import User
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.http import JsonResponse, HttpResponseBadRequest
from django.db.models import Q
from .services import TransactionService
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.http import require_POST
from decimal import Decimal
import uuid
import json
from django.utils.safestring import mark_safe
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from .forms import *


def landing_page(request):
    return render(request, 'main/index.html')



@login_required
def dashboard(request):
    user = request.user

    # Fetch user's wallets
    wallets = Wallet.objects.filter(user=user)

    # Prepare wallet data for the frontend
    wallets_data = []
    for wallet in wallets:
        wallets_data.append({
            "name": wallet.get_account_type_display(),
            "number": wallet.account_number,
            "balance": f"${wallet.balance:,.2f}",
            "type": wallet.account_type.lower(), 
            "trend": "+2.5% from last month",
            "is_active": wallet.is_active
        })

    #wallets_json = mark_safe(json.dumps(wallets_data))

    # Fetch recent transactions (limit 3)
    recent_transactions = (
        Transaction.objects
        .filter(wallet__user=user)
        .select_related("wallet")
        .order_by("-created_at")[:3]
    )

    context = {
        "wallets_json": wallets_data,
        "recent_transactions": recent_transactions,
        "last_login_time": user.last_login.strftime("%b %d, %I:%M %p") if user.last_login else "First login",
    }

    return render(request, "dashboard.html", context)




@login_required
def transfer(request):
    user = request.user
    # Get user's wallets for the source account selection
    user_wallets = Wallet.objects.filter(user=user, is_active=True)
    
    context = {
        'user_wallets': user_wallets,
    }
    return render(request, 'transfer_form.html', context)


@login_required
def search_recipient(request):
    """Search for a recipient by email or account number"""
    search_term = request.GET.get('search_term', '').strip()
    if not search_term:
        return JsonResponse({'success': False, 'message': 'Please provide an email or account number'})
    
    # Check if search term is an email
    if '@' in search_term:
        # Search by email
        try:
            recipient = User.objects.get(email=search_term)
            # Get recipient's wallets
            wallets = Wallet.objects.filter(user=recipient, is_active=True)
            
            wallet_data = [{
                'id': wallet.id,
                'account_type': wallet.get_account_type_display(),
                'account_number': wallet.account_number,
            } for wallet in wallets]
            
            return JsonResponse({
                'success': True,
                'recipient': {
                    'name': recipient.full_name,
                    'email': recipient.email,
                    'wallets': wallet_data
                }
            })
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'User not found with this email'})
    else:
        # Search by account number
        try:
            wallet = Wallet.objects.get(account_number=search_term, is_active=True)
            return JsonResponse({
                'success': True,
                'recipient': {
                    'name': wallet.user.full_name,
                    'account_type': wallet.get_account_type_display(),
                    'account_number': wallet.account_number,
                    'wallet_id': wallet.id
                }
            })
        except Wallet.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Account not found'})


@login_required
@require_POST
def process_transfer(request):
    """Process the transfer between accounts"""
    from_wallet_id = request.POST.get('from_wallet_id')
    to_wallet_id = request.POST.get('to_wallet_id')
    amount = request.POST.get('amount')
    description = request.POST.get('description', 'Transfer')
    
    # Validate inputs
    if not all([from_wallet_id, to_wallet_id, amount]):
        return JsonResponse({'success': False, 'message': 'Missing required fields'})
    
    try:
        amount = Decimal(amount)
        if amount <= 0:
            return JsonResponse({'success': False, 'message': 'Amount must be positive'})
    except:
        return JsonResponse({'success': False, 'message': 'Invalid amount'})
    
    try:
        from_wallet = Wallet.objects.get(id=from_wallet_id, user=request.user)
        to_wallet = Wallet.objects.get(id=to_wallet_id)
    except Wallet.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Wallet not found'})
    
    # Process the transfer
    try:
        transaction = TransactionService.transfer(from_wallet, to_wallet, amount, description)
        
        # Send email notification to recipient
        recipient_user = to_wallet.user
        try:
            send_mail(
                subject="You've received a transfer",
                message=f"Hi {recipient_user.full_name},\n\nYou received ${amount:,.2f} from {request.user.full_name}.\n\nCheck your wallet for details.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient_user.email],
                fail_silently=True,
            )
        except Exception as e:
            # Log the error but continue with the process
            print(f"Email sending failed: {str(e)}")
        
        # Get the transaction ID for redirect
        # We need to get the transaction that was created for the recipient
        """recipient_transaction = Transaction.objects.filter(
            wallet=to_wallet,
            transaction_type='CREDIT',
            related_wallet=from_wallet,
            created_at__gte=transaction.created_at
        ).order_by('-created_at').first()
        
        transaction_id = recipient_transaction.id if recipient_transaction else transaction.id"""
        
        return JsonResponse({
            'success': True, 
            'message': 'Transfer successful',
            'transaction_id': transaction.id
        })
    except ValueError as e:
        return JsonResponse({'success': False, 'message': str(e)})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'})


@login_required
def transaction_detail(request, transaction_id):
    """View a specific transaction's details"""
    transaction = get_object_or_404(Transaction, id=transaction_id)
    
    # Security check - ensure the user owns either the source or destination wallet
    if transaction.wallet.user != request.user and \
       (not transaction.related_wallet or transaction.related_wallet.user != request.user):
        return HttpResponseBadRequest("You don't have permission to view this transaction")
    
    # Determine if this is a credit or debit for display purposes
    is_credit = transaction.transaction_type == 'CREDIT'
    
    # Get the other party's information
    other_party = None
    if transaction.related_wallet:
        other_party = transaction.related_wallet.user.full_name
    
    context = {
        'transaction': transaction,
        'is_credit': is_credit,
        'other_party': other_party,
    }
    
    return render(request, 'transactions/transaction_details.html', context)







@login_required
def transaction_history_view(request):
    wallet = Wallet.objects.filter(user=request.user).first()
    transactions = Transaction.objects.filter(wallet=wallet).order_by('-created_at')[:20]

    context = {
        'transactions': transactions
    }
    return render(request, 'transactions/history.html', context)


@login_required
def load_more_transactions(request):
    user = request.user
    wallets = Wallet.objects.filter(user=user)

    if not wallets.exists():
        return JsonResponse({'transactions': [], 'has_more': False})

    offset = int(request.GET.get('offset', 0))
    limit = 20
    search_term = request.GET.get('search_term', '').strip()
    transaction_type = request.GET.get('transaction_type_filter', '').strip()

    # Fetch transactions for all of the user's wallets
    transactions = Transaction.objects.filter(wallet__in=wallets)

    if search_term:
        transactions = transactions.filter(
            Q(description__icontains=search_term) |
            Q(amount__icontains=search_term)
        )

    if transaction_type:
        transactions = transactions.filter(transaction_type__iexact=transaction_type.upper())

    total_count = transactions.count()
    transactions = transactions.select_related('wallet').order_by('-created_at')[offset:offset + limit]
    
    transaction_list = []
    for t in transactions:
        transaction_data = {
            'id': t.id,
            'description': t.description,
            'amount': float(t.amount),
            'transaction_type': t.transaction_type,
            'created_at': t.created_at.isoformat(),
            'get_transaction_type_display': t.get_transaction_type_display(),
            'wallet': {
                'account_type_display': t.wallet.get_account_type_display(),
                'account_number': t.wallet.account_number,
            }
        }
        if hasattr(t, 'status'):
            transaction_data['status'] = t.status
            transaction_data['get_status_display'] = t.get_status_display()
        else:
            transaction_data['status'] = 'COMPLETED'
            transaction_data['get_status_display'] = 'Completed'
        
        transaction_list.append(transaction_data)

    return JsonResponse({
        'transactions': transaction_list,
        'has_more': (offset + limit) < total_count
    })



def transactions_details(request):
    return render(request, 'transaction_details.html')

def loans(request):
    return render(request, 'loans.html')


@login_required
def deposit_funds(request):
    deposit_accounts = {
        'bank': DepositAccount.objects.filter(method='bank', is_active=True).first(),
        'cashapp': DepositAccount.objects.filter(method='cashapp', is_active=True).first(),
        'crypto': DepositAccount.objects.filter(method='crypto', is_active=True).first(),
    }

    active_tab = request.GET.get('tab', 'bank')
    form = None
    
    if request.method == 'POST':
        if active_tab == 'bank':
            form = BankDepositForm(request.POST, request.FILES)
        elif active_tab == 'gift':
            form = GiftCardDepositForm(request.POST, request.FILES)
        elif active_tab == 'cashapp':
            form = CashAppDepositForm(request.POST, request.FILES)
        elif active_tab == 'crypto':
            form = CryptoDepositForm(request.POST, request.FILES)

        if form and form.is_valid():
            try:
                deposit = form.save(commit=False)
                deposit.user = request.user
                deposit.method = active_tab

                # 🔥 Assign default wallet (CHECKING account)
                default_wallet = request.user.wallets.filter(account_type='CHECKING').first()
                if default_wallet:
                    deposit.wallet = default_wallet
                else:
                    messages.error(request, "No checking wallet found for this user.")
                    return redirect("deposit")

                deposit.save()

                messages.success(request, 'Deposit request submitted successfully!')
                return redirect("user_dashboard")
            except ValidationError as e:
                messages.error(request, str(e))
    else:
        if active_tab == 'bank':
            form = BankDepositForm()
        elif active_tab == 'gift':
            form = GiftCardDepositForm()
        elif active_tab == 'cashapp':
            form = CashAppDepositForm()
        elif active_tab == 'crypto':
            form = CryptoDepositForm()

    recent_deposits = Deposit.objects.filter(user=request.user).order_by('-created_at')[:5]

    context = {
        'active_tab': active_tab,
        'deposit_accounts': deposit_accounts,
        'bank_form': BankDepositForm() if active_tab != 'bank' else form,
        'gift_form': GiftCardDepositForm() if active_tab != 'gift' else form,
        'cashapp_form': CashAppDepositForm() if active_tab != 'cashapp' else form,
        'crypto_form': CryptoDepositForm() if active_tab != 'crypto' else form,
        'recent_deposits': recent_deposits,
    }
    
    return render(request, 'deposit/deposit.html', context)


@login_required
def deposit_success(request, deposit_id):
    deposit = get_object_or_404(Deposit, id=deposit_id, user=request.user)
    return render(request, 'deposit_success.html', {'deposit': deposit})



"""def deposit(request):
    return render(request, 'deposit/deposit.html')"""

def withdrawals(request):
    return render(request, 'withdrawals.html')

def settings_view(request):
    return render(request, 'settings.html')

 # Or 'main/home.html' if you prefer