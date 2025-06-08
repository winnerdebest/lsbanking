from django.urls import path
from .views import *


urlpatterns = [
    path('', landing_page, name='landing_page'),
    path('dashboard/', dashboard, name='user_dashboard'),
    path('transfer/', transfer, name='transfer'),
    path('transfer/search-recipient/', search_recipient, name='search_recipient'),
    path('transfer/process/', process_transfer, name='process_transfer'),
    path('transactions/', transaction_history_view, name='transactions'),
    path('transactions/load-more/', load_more_transactions, name='load-more-transactions'),
    path('transactions/<int:transaction_id>/', transaction_detail, name='transaction_detail'),
    path('transactions-details/', transactions_details, name='transactions-details'),
    path('loans/', loans, name='loans'),
    path('deposit/', deposit_funds, name='deposit'),
    path('withdrawals/', withdrawals, name='withdrawals'),
    path('settings/', settings_view, name='settings'),
]
