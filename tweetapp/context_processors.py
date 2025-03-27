from .models import Notification

def notification_count(request):
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(
            notified_user=request.user.profile,
            is_read=False
        ).count()
        return {'unread_notifications': unread_count}
    return {'unread_notifications': 0}
