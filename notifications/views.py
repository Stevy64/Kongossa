"""
Vues pour les notifications Kongossa
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from .models import Notification


@login_required
def notifications_list(request):
    """Liste des notifications de l'utilisateur"""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Séparer les notifications lues et non lues
    unread_notifications = notifications.filter(is_read=False)
    read_notifications = notifications.filter(is_read=True)[:20]  # Limiter les lues
    
    return render(request, 'notifications/list.html', {
        'unread_notifications': unread_notifications,
        'read_notifications': read_notifications,
    })


@login_required
@require_http_methods(["POST"])
def mark_notification_read(request, notification_id):
    """Marquer une notification comme lue"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.mark_as_read()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    return redirect('notifications:list')


@login_required
@require_http_methods(["POST"])
def mark_all_read(request):
    """Marquer toutes les notifications comme lues"""
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    return redirect('notifications:list')


@login_required
def unread_count(request):
    """Retourner le nombre de notifications non lues (API)"""
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'count': count})


@login_required
@require_http_methods(["POST", "DELETE"])
def delete_notification(request, notification_id):
    """Supprimer une notification"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.delete()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    return redirect('notifications:list')

