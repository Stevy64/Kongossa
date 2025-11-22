"""
Configuration des URLs principales du projet Kongossa.

Ce fichier définit les routes principales de l'application et inclut
les URLs de chaque application Django.

Structure des routes :
- / : Page d'accueil
- /admin/ : Interface d'administration Django
- /feed/ : Application Forum (posts, topics, groupes)
- /auth/ : Application Utilisateurs (authentification, profils)
- /chat/ : Application Chat (conversations, messages, appels)
- /stories/ : Application Stories (stories éphémères)
- /notifications/ : Application Notifications
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

# ============================================================================
# ROUTES PRINCIPALES
# ============================================================================

urlpatterns = [
    # Page d'accueil
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    
    # Interface d'administration Django
    path('admin/', admin.site.urls),
    
    # Application Forum (feed, topics, posts, groupes)
    path('feed/', include('forum.urls')),
    
    # Application Utilisateurs (authentification, profils)
    path('auth/', include('users.urls')),
    
    # Application Chat (conversations, messages, appels)
    path('chat/', include('chat.urls')),
    
    # Application Stories (stories éphémères)
    path('stories/', include('stories.urls')),
    
    # Application Notifications
    path('notifications/', include('notifications.urls')),
]

# ============================================================================
# CONFIGURATION DES FICHIERS MÉDIA ET STATIQUES (développement uniquement)
# ============================================================================

# En développement, servir les fichiers média et statiques directement depuis Django
# En production, utiliser Nginx ou un CDN pour servir ces fichiers
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

