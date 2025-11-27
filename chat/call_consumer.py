"""
Consumer WebSocket pour les appels vocaux
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Conversation


class CallConsumer(AsyncWebsocketConsumer):
    """Consumer pour les appels vocaux en temps réel"""
    
    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'call_{self.conversation_id}'
        self.user = self.scope['user']
        
        # Vérifier que l'utilisateur est authentifié
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Vérifier l'accès à la conversation
        has_access = await self.check_conversation_access()
        if not has_access:
            await self.close()
            return
        
        # Rejoindre le groupe d'appel
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    @database_sync_to_async
    def check_conversation_access(self):
        """Vérifier que l'utilisateur a accès à la conversation"""
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            return self.user in conversation.participants.all()
        except Conversation.DoesNotExist:
            return False
    
    async def disconnect(self, close_code):
        # Quitter le groupe d'appel
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Recevoir un message du WebSocket"""
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'call-offer':
            # Offre d'appel
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'call_offer',
                    'from_user_id': self.user.id,
                    'from_username': self.user.username,
                    'offer': data.get('offer'),
                }
            )
        elif message_type == 'call-answer':
            # Réponse à l'appel
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'call_answer',
                    'from_user_id': self.user.id,
                    'answer': data.get('answer'),
                }
            )
        elif message_type == 'call-ice-candidate':
            # Candidat ICE
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'call_ice_candidate',
                    'from_user_id': self.user.id,
                    'candidate': data.get('candidate'),
                }
            )
        elif message_type == 'call-end':
            # Fin d'appel
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'call_end',
                    'from_user_id': self.user.id,
                }
            )
    
    async def call_offer(self, event):
        """Envoyer l'offre d'appel au WebSocket"""
        if event['from_user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'call-offer',
                'from_user_id': event['from_user_id'],
                'from_username': event['from_username'],
                'offer': event['offer'],
            }))
    
    async def call_answer(self, event):
        """Envoyer la réponse à l'appel au WebSocket"""
        if event['from_user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'call-answer',
                'from_user_id': event['from_user_id'],
                'answer': event['answer'],
            }))
    
    async def call_ice_candidate(self, event):
        """Envoyer le candidat ICE au WebSocket"""
        if event['from_user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'call-ice-candidate',
                'from_user_id': event['from_user_id'],
                'candidate': event['candidate'],
            }))
    
    async def call_end(self, event):
        """Envoyer la fin d'appel au WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'call-end',
            'from_user_id': event['from_user_id'],
        }))

