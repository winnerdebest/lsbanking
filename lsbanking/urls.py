from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Importing views for allauth investments login and signup
from django.views.generic import TemplateView
from allauth.account.views import LoginView, SignupView 


admin.site.site_header = "GECU Admin"
admin.site.site_title = "GECU Admin Portal"
admin.site.index_title = "Welcome to GECU Admin Portal"
# Customizing the admin site header, title, and index title 
# to make it more user-friendly and relevant to the GECU brand.
# This will help in identifying the admin portal easily when managing the site.  

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main.urls')),
    path('profile/', include('accounts.urls')),

    # path('api/auth/', include('dj_rest_auth.urls')),
    # path('api/auth/registration/', include('dj_rest_auth.registration.urls')),
    path('investments/', include('investments.urls')),
    path('accounts/', include('allauth.urls')), 
    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),


    # Path for investments allauth login and registration pages
    path("investments/login/", LoginView.as_view(template_name="investments/login.html"), name="investment_login"),
    
    path("investments/signup/", SignupView.as_view(template_name="investments/signup.html"), name="investment_signup"),
    # path('accounts/', include('accounts.urls')), 
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)