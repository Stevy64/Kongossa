"""
Context processors pour les notifications
"""
from .models import Notification


def notifications_count(request):
    """Ajouter le nombre de notifications non lues au contexte"""
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
        return {'unread_notifications_count': unread_count}
    return {'unread_notifications_count': 0}

