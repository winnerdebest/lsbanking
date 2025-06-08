from django.urls import path
from .views import *

urlpatterns = [
    path('login/', login, name="login"),
    path('signup/', signup, name="signup"),
    path('reset-password/', reset_password, name="reset_password"),
    path('new-password/', new_password, name="new_password"),

    



]
