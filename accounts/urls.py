from django.urls import path
from .views import *

urlpatterns = [
    path('account-settings/', account_settings_view, name="account_settings"),
]
