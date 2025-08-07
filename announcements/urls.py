from django.urls import path
from . import views

app_name = 'announcements'

urlpatterns = [
    path('dismiss/<int:id>/', views.dismiss_announcement, name='dismiss'),
    path('api/unread/', views.api_unread_announcements, name='api_unread_announcements'),
]
