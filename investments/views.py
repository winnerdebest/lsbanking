from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from investments.decorators import login_context_required
from django.db.models import Sum, F, DecimalField, ExpressionWrapper
from .models import *
from django.utils import timezone
from decimal import Decimal
from django.views import View
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from investments.services import *
from main.services import *


#For Cron Job
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.management import call_command
from django.conf import settings




def investment_home(request):
    return render(request, 'investments/investment_home.html')




@method_decorator(login_required, name='dispatch')
class InvestmentDashboardView(View):
    def get(self, request):
        packages = InvestmentPackage.objects.filter(is_active=True)
        user_investments = UserInvestment.objects.filter(user=request.user).order_by('-created_at')
        investment_returns = InvestmentReturn.objects.filter(investment__user=request.user)

        # Total balance invested in active investments
        total_balance = sum([
            inv.package.price for inv in user_investments if inv.status == 'active'
        ])

        # Total earnings per day from active investments
        daily_earnings = sum([
            inv.calculate_daily_roi() for inv in user_investments if inv.status == 'active'
        ])

        # Total paid returns so far
        total_paid_returns = investment_returns.filter(is_paid=True).aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')

        # Total expected returns across all investments
        total_expected_returns = user_investments.aggregate(
            total=models.Sum('total_expected_return')
        )['total'] or Decimal('0.00')

        # Remaining balance to be paid
        remaining_returns = total_expected_returns - total_paid_returns

        # ✅ Get or show 0.00 if InvestorAccount doesn't exist
        investor_account = InvestorAccount.objects.filter(user=request.user).first()
        current_balance = investor_account.balance if investor_account else Decimal('0.00')

        context = {
            "packages": packages,
            "user_investments": user_investments,
            "investment_returns": investment_returns,
            "total_balance": total_balance,
            "daily_earnings": daily_earnings,
            "total_paid_returns": total_paid_returns,
            "remaining_returns": remaining_returns,
            "current_balance": current_balance,
        }
        return render(request, 'investments/main/dashboard.html', context)


@method_decorator(login_required, name='dispatch')
class CreateInvestmentView(View):
    def post(self, request):
        package_id = request.POST.get('package_id')
        package = get_object_or_404(InvestmentPackage, id=package_id, is_active=True)

        # Prevent duplicate active investment in same package (optional)
        if UserInvestment.objects.filter(user=request.user, package=package, status='active').exists():
            return JsonResponse({"error": "You already have an active investment in this package."}, status=400)

        investment = UserInvestment.objects.create(
            user=request.user,
            package=package,
            status='active',  # auto-activate for this example
        )

        # Optionally create daily return records immediately
        for i in range(package.duration_days):
            InvestmentReturn.objects.create(
                investment=investment,
                date=timezone.now().date() + timezone.timedelta(days=i),
                amount=(package.price * package.roi_percent / Decimal(100))
            )

        return JsonResponse({
            "message": "Investment created successfully!",
            "investment_id": investment.id,
        })


@method_decorator(login_required, name='dispatch')
class ChartDataView(View):
    def get(self, request):
        range_days = int(request.GET.get("range", 7))  # 7, 30, or 90
        end_date = timezone.now().date()
        start_date = end_date - timezone.timedelta(days=range_days)

        returns = InvestmentReturn.objects.filter(
            investment__user=request.user,
            date__range=(start_date, end_date),
        ).order_by('date')

        daily_totals = {}
        for r in returns:
            daily_totals.setdefault(r.date, Decimal(0))
            daily_totals[r.date] += r.amount

        labels = []
        values = []
        current = start_date
        total = Decimal("0.00")

        while current <= end_date:
            day_total = daily_totals.get(current, 0)
            total += day_total
            labels.append(current.strftime("%b %d"))
            values.append(round(total, 2))
            current += timezone.timedelta(days=1)

        return JsonResponse({
            "labels": labels,
            "values": values
        })


@method_decorator(login_required, name='dispatch')
class InvestmentWithdrawView(View):

    def get(self, request):

        investor_accounts = InvestorAccount.objects.filter(user=request.user).first()
        current_balance = investor_accounts.balance if investor_accounts else Decimal('0.00')

        context = {
            'current_balance': current_balance,
        }

        return render(request, 'investments/main/withdraw.html', context)

    def post(self, request):
        user = request.user

        try:
            investor_account = user.investor_account
        except InvestorAccount.DoesNotExist:
            return render(request, 'investments/partials/withdraw_modal.html', {
                'success': False,
                'title': "Withdrawal Failed",
                'message': "Investor account not found."
            })

        if investor_account.balance < Decimal('1000.00'):
            return render(request, 'investments/main/partials/withdraw_modal.html', {
                'success': False,
                'title': "Withdrawal Failed",
                'message': "Balance must be at least $1000 to withdraw."
            })

        try:
            wallet = Wallet.objects.get(user=user, account_type='SAVINGS')
        except Wallet.DoesNotExist:
            return render(request, 'investments/main/partials/withdraw_modal.html', {
                'success': False,
                'title': "Withdrawal Failed",
                'message': "Wallet not found."
            })

        try:
            amount = investor_account.balance
            TransactionService.deposit(wallet, amount, method='Investment Payout', description='Investment withdrawal')
            investor_account.balance = Decimal('0.00')
            investor_account.save(update_fields=['balance'])

            return render(request, 'investments/main/partials/withdraw_modal.html', {
                'success': True,
                'title': "Withdrawal Successful",
                'message': f"${amount} withdrawn successfully."
            })

        except Exception as e:
            return render(request, 'investments/main/partials/withdraw_modal.html', {
                'success': False,
                'title': "Withdrawal Failed",
                'message': str(e)
            })
        


@method_decorator(login_required, name='dispatch')
class PackageDepositView(View):
    def get(self, request, package_id):
        package = get_object_or_404(InvestmentPackage, id=package_id)
        accounts = DepositAccount.objects.filter(is_active=True)
        return render(request, 'investments/main/deposit_package.html', {
            'package': package,
            'accounts': accounts
        })

    def post(self, request, package_id):
        package = get_object_or_404(InvestmentPackage, id=package_id)
        method = request.POST.get('method')
        amount = package.price
        note = request.POST.get('note')
        proof_image = request.FILES.get('proof_image')
        giftcard_pin = request.POST.get('giftcard_pin')
        #giftcard_type = request.POST.get('giftcard_type')

        if not method:
            messages.error(request, "Please select a payment method.")
            return redirect(request.path)

        deposit = Deposit.objects.create(
            user=request.user,
            method=method,
            amount=amount,
            related_package=package,
            note=note,
            proof_image=proof_image,
            giftcard_pin=giftcard_pin if method == 'giftcard' else None
        )

        messages.success(request, "Deposit submitted. Awaiting admin approval.")
        return redirect('investments:investment_dashboard')



@csrf_exempt
@require_POST
def run_daily_roi(request):
    token = request.headers.get('X-RUN-TOKEN')
    if token != settings.DAILY_ROI_RUN_TOKEN:
        return HttpResponse("Forbidden", status=403)
    try:
        call_command('generate_daily_returns')
        return HttpResponse("OK")
    except Exception as e:
        # log e
        return HttpResponse(f"Error: {str(e)}", status=500)