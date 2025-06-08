from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main.urls')),
    # path('api/auth/', include('dj_rest_auth.urls')), # Remove API auth
    # path('api/auth/registration/', include('dj_rest_auth.registration.urls')), # Remove API registration
    path('accounts/', include('allauth.urls')), # Add allauth urls
    
    # path('accounts/', include('accounts.urls')), # allauth handles most account urls, we'll add specific ones later if needed
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)