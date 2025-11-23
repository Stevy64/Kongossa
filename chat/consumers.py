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
        try:
            self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
            self.room_group_name = f'chat_{self.conversation_id}'
            self.user = self.scope['user']
            
            # Vérifier que l'utilisateur est authentifié et fait partie de la conversation
            if not self.user.is_authenticated:
                await self.close(code=4001)  # Code personnalisé pour non authentifié
                return
            
            # Vérifier l'accès à la conversation
            has_access = await self.check_conversation_access()
            if not has_access:
                await self.close(code=4003)  # Code personnalisé pour accès refusé
                return
            
            # Rejoindre le groupe
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
            await self.accept()
        except Exception as e:
            print(f"Error in connect: {e}")
            await self.close(code=4000)  # Code d'erreur générique
    
    async def disconnect(self, close_code):
        # Quitter le groupe
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Recevoir un message du WebSocket"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'chat_message':
                content = data.get('content', '').strip()
                if content:
                    # Sauvegarder le message
                    message = await self.save_message(content)
                    
                    # Récupérer l'avatar de l'expéditeur
                    sender_avatar = None
                    if message.sender.avatar:
                        sender_avatar = message.sender.avatar.url
                    
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
                                'sender_avatar': sender_avatar,
                                'created_at': message.created_at.isoformat(),
                                'image': message.image.url if message.image else None,
                                'video': message.video.url if message.video else None,
                                'audio': message.audio.url if message.audio else None,
                                'file': message.file.url if message.file else None,
                                'file_name': message.file_name,
                                'read_at': message.read_at.isoformat() if message.read_at else None,
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
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON in receive: {e}")
        except Exception as e:
            print(f"Error in receive: {e}")
            # Ne pas fermer la connexion en cas d'erreur
    
    async def chat_message(self, event):
        """Envoyer le message au WebSocket"""
        try:
            message_data = event['message']
            # S'assurer que tous les champs sont présents
            message_payload = {
                'id': message_data.get('id'),
                'content': message_data.get('content', ''),
                'sender': message_data.get('sender', ''),
                'sender_id': message_data.get('sender_id'),
                'sender_avatar': message_data.get('sender_avatar'),
                'created_at': message_data.get('created_at'),
                'image': message_data.get('image'),
                'video': message_data.get('video'),
                'audio': message_data.get('audio'),
                'file': message_data.get('file'),
                'file_name': message_data.get('file_name'),
                'read_at': message_data.get('read_at'),
            }
            await self.send(text_data=json.dumps({
                'type': 'chat_message',
                'message': message_payload
            }))
        except Exception as e:
            print(f"Error in chat_message handler: {e}")
            # Ne pas fermer la connexion en cas d'erreur
    
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
    
    async def message_read(self, event):
        """Envoyer la mise à jour du statut de lecture au WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'message_read',
            'message_id': event['message_id'],
            'read_at': event['read_at'],
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

