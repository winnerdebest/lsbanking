from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, Q
from django.utils import timezone
from decimal import Decimal
import uuid
from datetime import timedelta
from .models import Loan, LoanApplication, LoanType, LoanPayment

@login_required
def loans_dashboard(request):
    """Display user's loans dashboard"""
    user = request.user
    
    # Get active loans
    active_loans = Loan.objects.filter(
        user=user,
        status__in=['active', 'current']
    )
    
    # Get loan applications
    pending_applications = LoanApplication.objects.filter(
        user=user,
        status__in=['pending_payment', 'payment_completed', 'under_review']
    )
    
    # Calculate statistics
    total_borrowed = active_loans.aggregate(
        total=Sum('original_amount')
    )['total'] or Decimal('0.00')
    
    # Mock available credit (you can adjust this based on your business logic)
    max_credit_limit = Decimal('50000.00')
    available_credit = max_credit_limit - total_borrowed
    
    # Get loan types for application form
    loan_types = LoanType.objects.filter(is_active=True)
    
    context = {
        'active_loans': active_loans,
        'pending_applications': pending_applications,
        'active_loans_count': active_loans.count(),
        'total_borrowed': total_borrowed,
        'available_credit': available_credit,
        'loan_types': loan_types,
        'is_kyc_verified': hasattr(user, 'profile') and user.profile.kyc_verified if hasattr(user, 'profile') else False,
    }
    
    return render(request, 'loans/loans.html', context)


@login_required
def submit_loan_application(request):
    """Handle loan application submission"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)
    
    try:
        # Get form data
        loan_type_id = request.POST.get('loan_type_id')
        amount = Decimal(request.POST.get('amount', 0))
        term_months = int(request.POST.get('term_months', 36))
        purpose = request.POST.get('purpose', '').strip()
        
        # Validate inputs
        if not all([loan_type_id, amount, purpose]):
            return JsonResponse({'error': 'All fields are required'}, status=400)
        
        loan_type = get_object_or_404(LoanType, id=loan_type_id, is_active=True)
        
        # Validate amount range
        if amount < loan_type.min_amount or amount > loan_type.max_amount:
            return JsonResponse({
                'error': f'Loan amount must be between ${loan_type.min_amount} and ${loan_type.max_amount}'
            }, status=400)
        
        # Check KYC verification
        if hasattr(request.user, 'profile') and not request.user.profile.kyc_verified:
            return JsonResponse({
                'error': 'KYC verification required',
                'redirect': '/account/kyc-verification'
            }, status=403)
        
        # Calculate loan details
        interest_rate = loan_type.min_rate  # You can implement more complex rate logic
        monthly_rate = (interest_rate / 100) / 12
        
        # Calculate monthly payment using PMT formula
        monthly_payment = (amount * monthly_rate) / (1 - (1 + monthly_rate) ** -term_months)
        total_interest = (monthly_payment * term_months) - amount
        
        # Calculate processing fee (5% of loan amount)
        processing_fee = amount * Decimal('0.05')
        
        # Create loan application
        application = LoanApplication.objects.create(
            user=request.user,
            loan_type=loan_type,
            amount=amount,
            term_months=term_months,
            purpose=purpose,
            interest_rate=interest_rate,
            monthly_payment=monthly_payment,
            total_interest=total_interest,
            processing_fee=processing_fee,
            status='pending_payment'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Loan application created',
            'application_id': application.id,
            'application_number': application.application_number,
            'processing_fee': str(processing_fee),
            'redirect': f'/loans/payment/{application.id}/'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def loan_processing_payment(request, application_id):
    """Display processing fee payment page"""
    application = get_object_or_404(
        LoanApplication,
        id=application_id,
        user=request.user,
        status='pending_payment'
    )
    
    context = {
        'application': application,
    }
    
    return render(request, 'loans/processing_payment.html', context)


@login_required
def process_fee_payment(request, application_id):
    """Process the 5% processing fee payment"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)
    
    application = get_object_or_404(
        LoanApplication,
        id=application_id,
        user=request.user,
        status='pending_payment'
    )
    
    try:
        # Generate unique transaction ID
        transaction_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
        
        # In a real application, you would integrate with a payment gateway here
        # For now, we'll simulate a successful payment
        
        # Create payment record
        payment = LoanPayment.objects.create(
            application=application,
            user=request.user,
            amount=application.processing_fee,
            payment_type='processing_fee',
            transaction_id=transaction_id,
            notes=f'Processing fee for loan application {application.application_number}'
        )
        
        # Update application status
        application.processing_fee_paid = True
        application.processing_fee_payment_date = timezone.now()
        application.processing_fee_transaction_id = transaction_id
        application.status = 'under_review'
        application.save()
        
        messages.success(
            request,
            f'Processing fee of ${application.processing_fee} paid successfully. '
            f'Your application is now under review.'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Payment successful',
            'transaction_id': transaction_id,
            'redirect': '/loans/'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def cancel_application(request, application_id):
    """Cancel a pending loan application"""
    application = get_object_or_404(
        LoanApplication,
        id=application_id,
        user=request.user,
        status='pending_payment'
    )
    
    application.status = 'cancelled'
    application.save()
    
    messages.info(request, 'Loan application cancelled.')
    return redirect('loans:dashboard')


@login_required
def make_loan_payment(request, loan_id):
    """Make a payment towards an active loan"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)
    
    loan = get_object_or_404(Loan, id=loan_id, user=request.user)
    
    try:
        amount = Decimal(request.POST.get('amount', loan.monthly_payment))
        
        # Generate transaction ID
        transaction_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
        
        # Calculate principal and interest split
        # Simple calculation - you can implement more complex amortization
        remaining_balance = loan.current_balance
        interest_amount = remaining_balance * (loan.interest_rate / 100 / 12)
        principal_amount = amount - interest_amount
        
        if principal_amount < 0:
            principal_amount = Decimal('0.00')
            interest_amount = amount
        
        # Create payment record
        payment = LoanPayment.objects.create(
            loan=loan,
            user=request.user,
            amount=amount,
            payment_type='regular',
            transaction_id=transaction_id,
            principal_amount=principal_amount,
            interest_amount=interest_amount,
            notes=f'Payment for loan {loan.loan_number}'
        )
        
        # Update loan
        loan.current_balance -= principal_amount
        loan.total_paid += amount
        loan.payments_made += 1
        
        # Update next payment date
        loan.next_payment_date += timedelta(days=30)
        
        # Check if loan is paid off
        if loan.current_balance <= 0:
            loan.current_balance = Decimal('0.00')
            loan.status = 'paid_off'
        
        loan.save()
        
        messages.success(request, f'Payment of ${amount} processed successfully.')
        
        return JsonResponse({
            'success': True,
            'message': 'Payment successful',
            'transaction_id': transaction_id,
            'new_balance': str(loan.current_balance)
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def loan_details(request, loan_id):
    """Display detailed information about a specific loan"""
    loan = get_object_or_404(Loan, id=loan_id, user=request.user)
    payments = loan.payments.all()[:10]  # Last 10 payments
    
    context = {
        'loan': loan,
        'payments': payments,
        'progress_percentage': loan.get_progress_percentage(),
    }
    
    return render(request, 'loans/loan_details.html', context)


@login_required
def application_details(request, application_id):
    """Display loan application details"""
    application = get_object_or_404(LoanApplication, id=application_id, user=request.user)
    
    context = {
        'application': application,
    }
    
    return render(request, 'loans/application_details.html', context)