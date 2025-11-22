"""
Modèles pour les stories Kongossa
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class Story(models.Model):
    """Modèle pour les stories (24h)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stories')
    content = models.TextField(blank=True, verbose_name="Texte")
    image = models.ImageField(upload_to='stories/', blank=True, null=True)
    video = models.FileField(upload_to='stories/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Story"
        verbose_name_plural = "Stories"
    
    def __str__(self):
        return f"Story by {self.user.username} - expires {self.expires_at}"
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            # Auto-expire après 24h
            from django.conf import settings
            hours = getattr(settings, 'STORY_EXPIRY_HOURS', 24)
            self.expires_at = timezone.now() + timedelta(hours=hours)
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at


class StoryView(models.Model):
    """Suivi des vues de stories"""
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='views')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='viewed_stories')
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['story', 'user']
        verbose_name = "Vue de Story"
        verbose_name_plural = "Vues de Stories"
    
    def __str__(self):
        return f"{self.user.username} viewed {self.story.id}"

