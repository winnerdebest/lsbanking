from django.contrib import admin
from .models import Announcement, AnnouncementRead

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'active', 'created_at']
    list_filter = ['active']
    search_fields = ['title', 'message']