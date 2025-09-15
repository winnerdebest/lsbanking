from django.urls import path
from .views import *


app_name = 'investments'

urlpatterns = [
    path('', investment_home, name='investment_home'),
    path('dashboard/', InvestmentDashboardView.as_view(), name='investment_dashboard'),
    path('packages/<int:package_id>/deposit/', PackageDepositView.as_view(), name='package_deposit'),
    path('chart-data/', ChartDataView.as_view(), name='chart_data'),
    path('withdraw/', InvestmentWithdrawView.as_view(), name='withdraw'),
    path('run-daily-roi/', run_daily_roi, name='run_daily_roi'),
]
