"""
Signaux pour créer automatiquement des notifications
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone
from chat.models import Message
from forum.models import GroupRequest, GroupMessage
from .models import Notification


@receiver(post_save, sender=Message)
def handle_message_notification(sender, instance, created, **kwargs):
    """Gérer les notifications pour les messages (création et marquage comme lu)"""
    conversation = instance.conversation
    sender_user = instance.sender
    other_user = conversation.get_other_participant(sender_user)
    
    if not other_user:
        return
    
    related_url = reverse('chat:detail', kwargs={'conversation_id': conversation.id})
    
    if created:
        # Créer une notification lorsqu'un nouveau message est reçu
        # Vérifier s'il existe déjà une notification non lue pour cette conversation
        existing_notification = Notification.objects.filter(
            user=other_user,
            notification_type='message',
            related_user=sender_user,
            is_read=False,
            related_url=related_url
        ).first()
        
        if existing_notification:
            # Mettre à jour le message existant
            existing_notification.message = f'{sender_user.username} vous a envoyé un message'
            existing_notification.created_at = timezone.now()
            existing_notification.save()
        else:
            # Créer une nouvelle notification
            Notification.create_notification(
                user=other_user,
                notification_type='message',
                title='Nouveau message',
                message=f'{sender_user.username} vous a envoyé un message',
                related_user=sender_user,
                related_url=related_url
            )
    elif instance.read_at:
        # Marquer les notifications comme lues quand un message est marqué comme lu
        try:
            Notification.objects.filter(
                user=other_user,
                notification_type='message',
                related_user=sender_user,
                related_url=related_url,
                is_read=False
            ).update(is_read=True)
        except Exception:
            # Ignorer les erreurs silencieusement
            pass


@receiver(post_save, sender=GroupRequest)
def create_group_request_notification(sender, instance, created, **kwargs):
    """Créer une notification lorsqu'une nouvelle demande d'accès au groupe est créée"""
    if created and instance.status == 'pending':
        # Notifier le créateur du groupe
        related_url = reverse('forum:manage_group', kwargs={'group_id': instance.group.id})
        Notification.create_notification(
            user=instance.group.creator,
            notification_type='group_request',
            title='Nouvelle demande d\'accès',
            message=f'{instance.user.username} a demandé à rejoindre le groupe "{instance.group.name}"',
            related_user=instance.user,
            related_url=related_url
        )


@receiver(post_save, sender=GroupMessage)
def create_group_message_notification(sender, instance, created, **kwargs):
    """Créer une notification lorsqu'un nouveau message est envoyé dans un groupe"""
    if created:
        group = instance.group
        related_url = reverse('forum:group_detail', kwargs={'group_id': group.id})
        
        # Notifier tous les membres sauf l'expéditeur
        for member in group.members.exclude(id=instance.sender.id):
            # Vérifier s'il existe déjà une notification non lue pour ce groupe
            existing_notification = Notification.objects.filter(
                user=member,
                notification_type='group_message',
                related_url=related_url,
                is_read=False
            ).first()
            
            if existing_notification:
                # Mettre à jour la notification existante
                existing_notification.message = f'{instance.sender.username} a envoyé un message dans "{group.name}"'
                existing_notification.related_user = instance.sender
                existing_notification.created_at = timezone.now()
                existing_notification.save()
            else:
                # Créer une nouvelle notification
                Notification.create_notification(
                    user=member,
                    notification_type='group_message',
                    title='Nouveau message de groupe',
                    message=f'{instance.sender.username} a envoyé un message dans "{group.name}"',
                    related_user=instance.sender,
                    related_url=related_url
                )

