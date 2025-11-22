"""
Configuration WSGI pour le projet Kongossa.

WSGI (Web Server Gateway Interface) est l'interface standard pour
servir les applications Python sur le web.

Ce fichier expose l'application WSGI comme variable de niveau module
nommée ``application``.

Note: Pour Kongossa, nous utilisons principalement ASGI (via Daphne)
pour le support des WebSockets. WSGI est conservé pour compatibilité
avec certains serveurs web ou pour des déploiements sans WebSockets.

Pour plus d'informations, voir :
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application

# Définir le module de settings par défaut
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kongossa.settings')

# Obtenir l'application WSGI
application = get_wsgi_application()

