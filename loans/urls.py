from django.urls import path
from . import views

app_name = 'loans'

urlpatterns = [
    # Main dashboard
    path('', views.loans_dashboard, name='dashboard'),
    
    # Loan application
    path('apply/', views.submit_loan_application, name='submit_application'),
    path('application/<int:application_id>/', views.application_details, name='application_details'),
    path('application/<int:application_id>/cancel/', views.cancel_application, name='cancel_application'),
    
    # Processing fee payment
    path('payment/<int:application_id>/', views.loan_processing_payment, name='processing_payment'),
    path('payment/<int:application_id>/process/', views.process_fee_payment, name='process_fee_payment'),
    
    # Active loans
    path('loan/<int:loan_id>/', views.loan_details, name='loan_details'),
    path('loan/<int:loan_id>/pay/', views.make_loan_payment, name='make_payment'),
]