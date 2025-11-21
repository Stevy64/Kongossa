"""
Modèles pour les notifications Kongossa
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse

User = get_user_model()


class Notification(models.Model):
    """Modèle pour les notifications utilisateur"""
    NOTIFICATION_TYPES = [
        ('message', 'Nouveau message'),
        ('group_message', 'Message de groupe'),
        ('group_request', 'Demande d\'accès au groupe'),
        ('group_request_approved', 'Demande d\'accès approuvée'),
        ('group_request_rejected', 'Demande d\'accès rejetée'),
        ('group_activity', 'Activité de groupe'),
        ('post_like', 'Like sur un post'),
        ('post_comment', 'Commentaire sur un post'),
        ('topic_update', 'Mise à jour du sujet'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', verbose_name="Utilisateur")
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES, verbose_name="Type")
    title = models.CharField(max_length=200, verbose_name="Titre")
    message = models.TextField(verbose_name="Message")
    is_read = models.BooleanField(default=False, verbose_name="Lu")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    
    # Liens optionnels vers les objets concernés
    related_user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='sent_notifications',
        verbose_name="Utilisateur concerné"
    )
    related_url = models.URLField(blank=True, null=True, verbose_name="URL liée")
    
    class Meta:
        app_label = 'notifications'
        ordering = ['-created_at']
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        indexes = [
            models.Index(fields=['user', 'is_read', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    def mark_as_read(self):
        """Marquer la notification comme lue"""
        if not self.is_read:
            self.is_read = True
            self.save()
    
    @classmethod
    def create_notification(cls, user, notification_type, title, message, related_user=None, related_url=None):
        """Créer une notification"""
        return cls.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            related_user=related_user,
            related_url=related_url
        )
