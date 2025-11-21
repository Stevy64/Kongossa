# Kongossa

Le forum gabonais moderne pour discuter, partager et connecter.

## 🚀 Fonctionnalités

- **Forum** : Création de posts avec texte et images, commentaires, likes
- **Chat en temps réel** : Conversations privées avec WebSockets (Django Channels)
- **Stories** : Stories éphémères (24h) avec images et vidéos
- **Profils utilisateurs** : Photos, bio, posts et stories
- **Authentification** : Email/mot de passe ou passwordless (lien magique)

## 🎨 Design

- Design moderne avec **glassmorphism** (effet de verre flouté)
- Fond flouté avec overlay translucide
- Boutons arrondis (forme pilule)
- Typographie élégante (Inter, Poppins)
- **Mobile-first** : Optimisé pour WebView Flutter

## 🛠️ Technologies

- **Backend** : Django 5+, Django Channels, Django REST Framework
- **Base de données** : PostgreSQL
- **Frontend** : TailwindCSS, Alpine.js
- **Temps réel** : WebSockets via Django Channels

## 📦 Installation

### Prérequis

- Python 3.10+
- PostgreSQL
- pip

### Étapes

1. **Cloner le projet**
```bash
git clone <repository-url>
cd Kongossa
```

2. **Créer un environnement virtuel**
```bash
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate
```

3. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

4. **Configurer la base de données**

Créer un fichier `.env` à la racine du projet :
```env
SECRET_KEY=votre-secret-key-ici
DB_NAME=kongossa
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
```

5. **Créer la base de données PostgreSQL**
```bash
createdb kongossa
```

6. **Appliquer les migrations**
```bash
python manage.py migrate
```

7. **Créer un superutilisateur**
```bash
python manage.py createsuperuser
```

8. **Lancer le serveur**
```bash
python manage.py runserver
```

L'application sera accessible sur `http://localhost:8000`

## 📁 Structure du projet

```
Kongossa/
├── kongossa/          # Configuration du projet
├── users/             # Application utilisateurs
├── forum/             # Application forum
├── chat/              # Application chat (WebSockets)
├── stories/           # Application stories
├── templates/         # Templates HTML
├── static/            # Fichiers statiques
├── media/             # Fichiers uploadés
└── manage.py
```

## 🔧 Configuration

### Variables d'environnement

Créer un fichier `.env` avec :
- `SECRET_KEY` : Clé secrète Django
- `DB_NAME` : Nom de la base de données
- `DB_USER` : Utilisateur PostgreSQL
- `DB_PASSWORD` : Mot de passe PostgreSQL
- `DB_HOST` : Hôte PostgreSQL
- `DB_PORT` : Port PostgreSQL

### Production

Pour la production :
1. Changer `DEBUG = False` dans `settings.py`
2. Configurer `ALLOWED_HOSTS`
3. Utiliser Redis pour `CHANNEL_LAYERS` au lieu de `InMemoryChannelLayer`
4. Configurer un serveur web (Nginx + Gunicorn/Daphne)
5. Utiliser un CDN pour les fichiers statiques

## 📱 Utilisation

1. **Créer un compte** : Accédez à `/auth/login/`
2. **Créer un post** : Sur le feed, cliquez sur "Quoi de neuf ?"
3. **Créer une story** : Cliquez sur le bouton "+" dans le carrousel de stories
4. **Chatter** : Accédez à `/chat/` pour voir vos conversations
5. **Voir un profil** : Cliquez sur un nom d'utilisateur

## 🎯 Roadmap

- [ ] Notifications en temps réel
- [ ] Recherche d'utilisateurs et posts
- [ ] Partage de posts
- [ ] Réactions (emoji)
- [ ] Groupes/communautés
- [ ] API REST complète

## 📄 Licence

Ce projet est sous licence MIT.

## 👥 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir une issue ou une pull request.

---

**Kongossa** - Le forum gabonais moderne 🌍

