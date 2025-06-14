from django.core.management.base import BaseCommand
from django.utils import timezone
from investments.models import UserInvestment, InvestmentReturn, InvestorAccount
from django.db.models import Sum

class Command(BaseCommand):
    help = 'Generates daily ROI returns for all active investments and completes them when done.'

    def handle(self, *args, **kwargs):
        today = timezone.now().date()
        count = 0

        active_investments = UserInvestment.objects.filter(
            status='active',
            start_date__date__lte=today,
            end_date__date__gte=today,
        )

        for investment in active_investments:
            if InvestmentReturn.objects.filter(investment=investment, date=today).exists():
                continue

            total_earned = InvestmentReturn.objects.filter(
                investment=investment
            ).aggregate(total=Sum('amount'))['total'] or 0

            daily_roi = investment.calculate_daily_roi()
            remaining = investment.total_expected_return - total_earned
            payout = min(daily_roi, remaining)

            # Create return record
            InvestmentReturn.objects.create(
                investment=investment,
                date=today,
                amount=payout,
                is_paid=True,
            )
            count += 1

            # 💰 CREDIT the payout to InvestorAccount
            try:
                investor_account = investment.user.investor_account
                investor_account.balance += payout
                investor_account.save(update_fields=['balance'])
            except InvestorAccount.DoesNotExist:
                self.stderr.write(self.style.ERROR(
                    f"InvestorAccount does not exist for user {investment.user.email}"
                ))
                continue  # Skip the rest of this loop

            total_earned += payout

            if total_earned >= investment.total_expected_return or today >= investment.end_date.date():
                investment.status = 'completed'
                investment.save(update_fields=['status'])

        self.stdout.write(self.style.SUCCESS(f"Generated {count} return(s) for {today}"))
