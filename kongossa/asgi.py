"""
Configuration ASGI pour le projet Kongossa.

ASGI (Asynchronous Server Gateway Interface) est utilisé pour :
- Applications asynchrones
- Support des connexions WebSocket pour les appels vidéo/audio

Pour plus d'informations, voir :
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

# Définir le module de settings par défaut AVANT toute autre importation
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kongossa.settings')

# Initialiser Django AVANT d'importer les modules qui utilisent les modèles
django_asgi_app = get_asgi_application()

# Configuration du routage ASGI
# - HTTP : Routé vers l'application Django standard
# - WebSocket : Routé vers les consumers Django Channels avec authentification (pour les appels)
try:
    from chat.call_consumer import CallConsumer
    from django.urls import re_path
    
    websocket_urlpatterns = [
        re_path(r'ws/call/(?P<conversation_id>\w+)/$', CallConsumer.as_asgi()),
    ]
    
    application = ProtocolTypeRouter({
        "http": django_asgi_app,  # Requêtes HTTP normales
        "websocket": AuthMiddlewareStack(  # WebSockets avec authentification
            URLRouter(websocket_urlpatterns)
        ),
    })
except ImportError:
    # Si call_consumer n'est pas disponible, utiliser seulement HTTP
    application = django_asgi_app

