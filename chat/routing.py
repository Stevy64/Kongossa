"""
Routing WebSocket pour le chat
"""
from django.urls import re_path
from . import consumers
from . import call_consumer

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<conversation_id>\w+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/call/(?P<conversation_id>\w+)/$', call_consumer.CallConsumer.as_asgi()),
]

