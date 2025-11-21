"""
Consumers WebSocket pour le chat en temps réel
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Conversation, Message
from django.utils import timezone

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    """Consumer pour le chat en temps réel"""
    
    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'chat_{self.conversation_id}'
        self.user = self.scope['user']
        
        # Vérifier que l'utilisateur est authentifié et fait partie de la conversation
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Vérifier l'accès à la conversation
        has_access = await self.check_conversation_access()
        if not has_access:
            await self.close()
            return
        
        # Rejoindre le groupe
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # Quitter le groupe
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Recevoir un message du WebSocket"""
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'chat_message':
            content = data.get('content', '').strip()
            if content:
                # Sauvegarder le message
                message = await self.save_message(content)
                
                # Envoyer le message au groupe
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': {
                            'id': message.id,
                            'content': message.content,
                            'sender': message.sender.username,
                            'sender_id': message.sender.id,
                            'created_at': message.created_at.isoformat(),
                        }
                    }
                )
        elif message_type == 'typing':
            # Envoyer l'indicateur de frappe au groupe
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_typing',
                    'user_id': self.user.id,
                    'username': self.user.username,
                }
            )
        elif message_type == 'stop_typing':
            # Envoyer l'arrêt de frappe au groupe
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_stopped_typing',
                    'user_id': self.user.id,
                }
            )
    
    async def chat_message(self, event):
        """Envoyer le message au WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message']
        }))
    
    async def user_typing(self, event):
        """Envoyer l'indicateur de frappe au WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'user_typing',
            'user_id': event['user_id'],
            'username': event['username'],
        }))
    
    async def user_stopped_typing(self, event):
        """Envoyer l'arrêt de frappe au WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'user_stopped_typing',
            'user_id': event['user_id'],
        }))
    
    @database_sync_to_async
    def check_conversation_access(self):
        """Vérifier que l'utilisateur a accès à la conversation"""
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            return self.user in conversation.participants.all()
        except Conversation.DoesNotExist:
            return False
    
    @database_sync_to_async
    def save_message(self, content):
        """Sauvegarder le message en base de données"""
        conversation = Conversation.objects.get(id=self.conversation_id)
        message = Message.objects.create(
            conversation=conversation,
            sender=self.user,
            content=content
        )
        # Mettre à jour la date de modification de la conversation
        conversation.save()
        return message

