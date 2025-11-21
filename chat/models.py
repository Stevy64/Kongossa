"""
Modèles pour le chat en temps réel Kongossa
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class Conversation(models.Model):
    """Modèle pour les conversations privées"""
    participants = models.ManyToManyField(User, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = "Conversation"
        verbose_name_plural = "Conversations"
    
    def __str__(self):
        return f"Conversation {self.id}"
    
    def get_other_participant(self, user):
        """Récupérer l'autre participant"""
        return self.participants.exclude(id=user.id).first()


class Message(models.Model):
    """Modèle pour les messages"""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField(blank=True)
    image = models.ImageField(upload_to='messages/', blank=True, null=True)
    file = models.FileField(upload_to='messages/files/', blank=True, null=True)
    file_name = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = "Message"
        verbose_name_plural = "Messages"
    
    def __str__(self):
        return f"Message from {self.sender.username} in {self.conversation.id}"
    
    def mark_as_read(self):
        """Marquer le message comme lu"""
        if not self.read_at:
            self.read_at = timezone.now()
            self.save()

