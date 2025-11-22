# 🚀 Guide de Démarrage Rapide - Kongossa

## Installation rapide (Développement)

```bash
# 1. Cloner le repository
git clone <repository-url>
cd Kongossa

# 2. Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Copier le fichier d'environnement
cp .env.example .env
# Éditer .env avec vos valeurs

# 5. Appliquer les migrations
python manage.py migrate

# 6. Créer un superutilisateur
python manage.py createsuperuser

# 7. Lancer le serveur
python manage.py runserver
```

## Configuration minimale (.env)

```env
SECRET_KEY=votre-clé-secrète
DEBUG=True
USE_POSTGRES=False
USE_REDIS=False
ALLOWED_HOSTS=*
```

## Commandes utiles

```bash
# Vérifier la configuration
python manage.py check

# Créer des migrations
python manage.py makemigrations

# Appliquer les migrations
python manage.py migrate

# Collecter les fichiers statiques
python manage.py collectstatic

# Créer un superutilisateur
python manage.py createsuperuser

# Nettoyer les stories expirées
python manage.py cleanup_expired_stories
```

## Structure des URLs

- `/` - Page d'accueil
- `/feed/` - Fil d'actualité
- `/auth/login/` - Connexion
- `/auth/signup/` - Inscription
- `/chat/` - Messagerie
- `/stories/` - Stories
- `/notifications/` - Notifications
- `/admin/` - Administration

## Documentation complète

- **README.md** - Documentation principale
- **DEPLOYMENT.md** - Guide de déploiement
- **PRODUCTION_CHECKLIST.md** - Checklist de production
- **COMMENTS_GUIDE.md** - Guide des commentaires


