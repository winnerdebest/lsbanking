from django.shortcuts import render
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from .models import Announcement, AnnouncementRead
from django.contrib.auth.decorators import login_required

@require_POST
def dismiss_announcement(request, id):
    if request.user.is_authenticated:
        from django.shortcuts import get_object_or_404
        announcement = get_object_or_404(Announcement, id=id)
        AnnouncementRead.objects.get_or_create(user=request.user, announcement=announcement)
    return JsonResponse({'status': 'ok'})

def get_unread_announcements(user):
    from .models import Announcement
    active = Announcement.objects.filter(active=True).order_by('-created_at')
    return [
        a for a in active
        if not AnnouncementRead.objects.filter(user=user, announcement=a).exists()
    ]

@login_required
def api_unread_announcements(request):
    """API endpoint to return unread announcements as JSON"""
    unread = get_unread_announcements(request.user)
    
    # Convert announcements to JSON-serializable format
    announcements_data = []
    for announcement in unread:
        announcements_data.append({
            'id': announcement.id,
            'title': announcement.title,
            'message': announcement.message,
            'created_at': announcement.created_at.isoformat(),
            'priority': getattr(announcement, 'priority', 'normal'),  # if you have a priority field
        })
    
    return JsonResponse(announcements_data, safe=False)