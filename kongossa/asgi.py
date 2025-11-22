"""
Configuration ASGI pour le projet Kongossa.

ASGI (Asynchronous Server Gateway Interface) est utilisé pour :
- Django Channels (WebSockets)
- Applications asynchrones
- Support des connexions WebSocket pour le chat en temps réel et les appels

Ce fichier configure le routage des protocoles HTTP et WebSocket.
Les connexions WebSocket sont authentifiées et routées vers les consumers
définis dans chat.routing.

Pour plus d'informations, voir :
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
https://channels.readthedocs.io/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import chat.routing

# Définir le module de settings par défaut
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kongossa.settings')

# Configuration du routage ASGI
# - HTTP : Routé vers l'application Django standard
# - WebSocket : Routé vers les consumers Django Channels avec authentification
application = ProtocolTypeRouter({
    "http": get_asgi_application(),  # Requêtes HTTP normales
    "websocket": AuthMiddlewareStack(  # WebSockets avec authentification
        URLRouter(
            chat.routing.websocket_urlpatterns  # Routes WebSocket définies dans chat.routing
        )
    ),
})

