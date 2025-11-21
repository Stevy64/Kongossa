#!/bin/bash

# Script de configuration initiale pour Kongossa

echo "🚀 Configuration de Kongossa..."

# Créer l'environnement virtuel
if [ ! -d "venv" ]; then
    echo "📦 Création de l'environnement virtuel..."
    python3 -m venv venv
fi

# Activer l'environnement virtuel
echo "🔌 Activation de l'environnement virtuel..."
source venv/bin/activate

# Installer les dépendances
echo "📥 Installation des dépendances..."
pip install -r requirements.txt

# Créer le fichier .env s'il n'existe pas
if [ ! -f ".env" ]; then
    echo "📝 Création du fichier .env..."
    cp .env.example .env
    echo "⚠️  N'oubliez pas de configurer votre fichier .env avec vos paramètres de base de données!"
fi

# Créer les dossiers nécessaires
mkdir -p media/avatars
mkdir -p media/posts
mkdir -p media/stories
mkdir -p media/messages
mkdir -p staticfiles

# Appliquer les migrations
echo "🗄️  Application des migrations..."
python manage.py migrate

# Créer un superutilisateur (optionnel)
echo "👤 Création du superutilisateur..."
python manage.py createsuperuser

echo "✅ Configuration terminée!"
echo ""
echo "Pour démarrer le serveur:"
echo "  source venv/bin/activate"
echo "  python manage.py runserver"
echo ""
echo "Pour nettoyer les stories expirées (cron job):"
echo "  python manage.py cleanup_expired_stories"

