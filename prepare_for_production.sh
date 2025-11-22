#!/bin/bash

# ============================================================================
# SCRIPT DE PRÉPARATION POUR LA PRODUCTION - KONGOSSA
# ============================================================================
# Ce script prépare l'application pour la mise en production
# Usage: ./prepare_for_production.sh

set -e  # Arrêter en cas d'erreur

echo "🚀 Préparation de Kongossa pour la production..."
echo ""

# ============================================================================
# VÉRIFICATIONS PRÉLIMINAIRES
# ============================================================================

echo "📋 Vérification des prérequis..."

# Vérifier Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 n'est pas installé"
    exit 1
fi
echo "✅ Python 3 trouvé"

# Vérifier pip
if ! command -v pip &> /dev/null; then
    echo "❌ pip n'est pas installé"
    exit 1
fi
echo "✅ pip trouvé"

# ============================================================================
# VÉRIFICATION DES VARIABLES D'ENVIRONNEMENT
# ============================================================================

echo ""
echo "🔐 Vérification des variables d'environnement..."

if [ ! -f .env ]; then
    echo "⚠️  Fichier .env non trouvé"
    echo "📝 Création d'un fichier .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✅ Fichier .env créé depuis .env.example"
        echo "⚠️  IMPORTANT: Modifiez le fichier .env avec vos valeurs de production"
    else
        echo "❌ Fichier .env.example non trouvé"
        exit 1
    fi
else
    echo "✅ Fichier .env trouvé"
fi

# ============================================================================
# INSTALLATION DES DÉPENDANCES
# ============================================================================

echo ""
echo "📦 Installation des dépendances..."

if [ -d "venv" ] || [ -d ".venv" ]; then
    echo "✅ Environnement virtuel trouvé"
    if [ -d "venv" ]; then
        source venv/bin/activate
    else
        source .venv/bin/activate
    fi
else
    echo "⚠️  Environnement virtuel non trouvé, création..."
    python3 -m venv venv
    source venv/bin/activate
fi

pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Dépendances installées"

# ============================================================================
# VÉRIFICATION DES MIGRATIONS
# ============================================================================

echo ""
echo "🗄️  Vérification des migrations..."

python manage.py makemigrations --check --dry-run
if [ $? -eq 0 ]; then
    echo "✅ Aucune migration en attente"
else
    echo "⚠️  Des migrations sont en attente, exécution..."
    python manage.py makemigrations
fi

# ============================================================================
# COLLECTE DES FICHIERS STATIQUES
# ============================================================================

echo ""
echo "📁 Collecte des fichiers statiques..."

python manage.py collectstatic --noinput
echo "✅ Fichiers statiques collectés"

# ============================================================================
# VÉRIFICATION DU CODE
# ============================================================================

echo ""
echo "🔍 Vérification du code Django..."

python manage.py check --deploy
if [ $? -eq 0 ]; then
    echo "✅ Aucune erreur détectée"
else
    echo "⚠️  Des avertissements ont été détectés, vérifiez les messages ci-dessus"
fi

# ============================================================================
# RÉSUMÉ
# ============================================================================

echo ""
echo "✅ Préparation terminée!"
echo ""
echo "📝 Prochaines étapes:"
echo "   1. Vérifiez et modifiez le fichier .env avec vos valeurs de production"
echo "   2. Configurez votre base de données PostgreSQL"
echo "   3. Configurez Redis pour Django Channels"
echo "   4. Consultez DEPLOYMENT.md pour les instructions de déploiement"
echo ""
echo "🔒 Checklist de sécurité:"
echo "   - [ ] DEBUG = False dans .env"
echo "   - [ ] SECRET_KEY unique et sécurisé"
echo "   - [ ] ALLOWED_HOSTS configuré"
echo "   - [ ] Base de données avec utilisateur dédié"
echo "   - [ ] HTTPS configuré"
echo ""


