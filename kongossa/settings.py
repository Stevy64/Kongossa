"""
Configuration Django pour le projet Kongossa.

Ce fichier contient toutes les configurations nécessaires pour le fonctionnement
de l'application, incluant les paramètres de base de données, sécurité,
fichiers statiques, et intégrations tierces (Channels, REST Framework, etc.).
"""

import os
from pathlib import Path

# ============================================================================
# CONFIGURATION DE BASE
# ============================================================================

# Chemin de base du projet
BASE_DIR = Path(__file__).resolve().parent.parent

# Clé secrète Django - CRITIQUE pour la sécurité
# En production, définir via variable d'environnement SECRET_KEY
# Générer une nouvelle clé avec: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-kongossa-dev-key-change-in-production')

# Mode debug - DÉSACTIVER en production (DEBUG = False)
# En production, utiliser: DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'

# Hôtes autorisés - Configurer avec votre domaine en production
# Exemple: ALLOWED_HOSTS = ['kongossa.com', 'www.kongossa.com', 'api.kongossa.com']
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')

# ============================================================================
# APPLICATIONS INSTALLÉES
# ============================================================================

INSTALLED_APPS = [
    # Serveur ASGI pour Django Channels (WebSockets)
    'daphne',
    
    # Applications Django par défaut
    'django.contrib.admin',           # Interface d'administration
    'django.contrib.auth',             # Système d'authentification
    'django.contrib.contenttypes',     # Types de contenu
    'django.contrib.sessions',         # Gestion des sessions
    'django.contrib.messages',         # Système de messages
    'django.contrib.staticfiles',      # Gestion des fichiers statiques
    
    # Applications tierces
    'rest_framework',                  # Django REST Framework (API)
    'channels',                        # Django Channels (WebSockets)
    'corsheaders',                     # CORS headers (pour API cross-origin)
    
    # Applications locales
    'users.apps.UsersConfig',          # Gestion des utilisateurs
    'forum',                           # Forum et discussions
    'chat',                            # Chat en temps réel
    'stories',                         # Stories éphémères
    'notifications.apps.NotificationsConfig',  # Système de notifications
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'kongossa.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'notifications.context_processors.notifications_count',
            ],
        },
    },
]

WSGI_APPLICATION = 'kongossa.wsgi.application'
ASGI_APPLICATION = 'kongossa.asgi.application'

# ============================================================================
# CONFIGURATION DE LA BASE DE DONNÉES
# ============================================================================

# En production, utiliser PostgreSQL (recommandé)
# Pour activer PostgreSQL, définir USE_POSTGRES=True dans les variables d'environnement
USE_POSTGRES = os.environ.get('USE_POSTGRES', 'False').lower() == 'true'

if USE_POSTGRES:
    # Configuration PostgreSQL (production)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME', 'kongossa'),
            'USER': os.environ.get('DB_USER', 'postgres'),
            'PASSWORD': os.environ.get('DB_PASSWORD', 'postgres'),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '5432'),
            # Options de connexion pour la production
            'OPTIONS': {
                'connect_timeout': 10,
            },
            # Pool de connexions (optionnel, nécessite django-db-connection-pool)
            # 'CONN_MAX_AGE': 600,
        }
    }
else:
    # SQLite pour le développement (plus simple à démarrer)
    # ATTENTION: Ne pas utiliser SQLite en production
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Libreville'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'users.User'

# ============================================================================
# CONFIGURATION DJANGO CHANNELS (WebSockets)
# ============================================================================

# En production, utiliser Redis pour le channel layer
# Pour activer Redis, définir USE_REDIS=True et configurer REDIS_URL
USE_REDIS = os.environ.get('USE_REDIS', 'False').lower() == 'true'

if USE_REDIS:
    # Configuration Redis pour la production (recommandé)
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                "hosts": [(os.environ.get('REDIS_HOST', 'localhost'), 
                          int(os.environ.get('REDIS_PORT', 6379)))],
                # Optionnel: préfixe pour les clés Redis
                # "prefix": "kongossa:",
            },
        },
    }
else:
    # InMemoryChannelLayer pour le développement (non persistant)
    # ATTENTION: Ne pas utiliser en production (pas de persistance, pas de scaling)
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        },
    }

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# ============================================================================
# CONFIGURATION CORS (Cross-Origin Resource Sharing)
# ============================================================================

# Origines autorisées pour les requêtes CORS
# En production, spécifier les domaines exacts de votre frontend
CORS_ALLOWED_ORIGINS = os.environ.get(
    'CORS_ALLOWED_ORIGINS', 
    'http://localhost:3000,http://127.0.0.1:3000'
).split(',')

# Autoriser l'envoi de cookies et credentials
CORS_ALLOW_CREDENTIALS = True

# Méthodes HTTP autorisées
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# ============================================================================
# CONFIGURATION DES UPLOADS DE FICHIERS
# ============================================================================

# Taille maximale des fichiers uploadés (en bytes)
# 10MB par défaut - ajuster selon les besoins
FILE_UPLOAD_MAX_MEMORY_SIZE = int(os.environ.get('FILE_UPLOAD_MAX_MEMORY_SIZE', 10 * 1024 * 1024))
DATA_UPLOAD_MAX_MEMORY_SIZE = int(os.environ.get('DATA_UPLOAD_MAX_MEMORY_SIZE', 10 * 1024 * 1024))

# Types de fichiers autorisés (sécurité)
# À configurer selon les besoins de l'application
ALLOWED_FILE_EXTENSIONS = {
    'images': ['.jpg', '.jpeg', '.png', '.gif', '.webp'],
    'videos': ['.mp4', '.webm', '.ogg'],
    'audio': ['.mp3', '.wav', '.ogg'],
    'documents': ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.txt'],
}

# ============================================================================
# CONFIGURATION DES STORIES
# ============================================================================

# Durée de vie des stories en heures (24h par défaut)
STORY_EXPIRY_HOURS = int(os.environ.get('STORY_EXPIRY_HOURS', 24))

# ============================================================================
# CONFIGURATION DE SÉCURITÉ (Production)
# ============================================================================

if not DEBUG:
    # Sécurité HTTPS en production
    SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'False').lower() == 'true'
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    
    # Headers de sécurité
    SECURE_HSTS_SECONDS = 31536000  # 1 an
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

