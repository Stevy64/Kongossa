# Guide de Déploiement - Kongossa

Ce guide explique comment déployer Kongossa en production.

## 📋 Prérequis

- Python 3.10+
- PostgreSQL 12+
- Redis (pour Django Channels)
- Nginx (recommandé)
- Serveur web (Gunicorn/Daphne)

## 🔧 Configuration de Production

### 1. Variables d'environnement

Créer un fichier `.env` à la racine du projet avec les variables suivantes :

```env
# Sécurité
SECRET_KEY=votre-clé-secrète-très-longue-et-aléatoire
DEBUG=False

# Base de données PostgreSQL
USE_POSTGRES=True
DB_NAME=kongossa
DB_USER=kongossa_user
DB_PASSWORD=votre-mot-de-passe-sécurisé
DB_HOST=localhost
DB_PORT=5432

# Redis (pour Django Channels)
USE_REDIS=True
REDIS_HOST=localhost
REDIS_PORT=6379

# Hôtes autorisés
ALLOWED_HOSTS=kongossa.com,www.kongossa.com

# CORS
CORS_ALLOWED_ORIGINS=https://kongossa.com,https://www.kongossa.com

# Uploads
FILE_UPLOAD_MAX_MEMORY_SIZE=10485760
DATA_UPLOAD_MAX_MEMORY_SIZE=10485760

# Stories
STORY_EXPIRY_HOURS=24
```

### 2. Générer une clé secrète

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 3. Installation des dépendances

```bash
pip install -r requirements.txt
```

### 4. Configuration de la base de données

```bash
# Créer la base de données PostgreSQL
createdb kongossa

# Appliquer les migrations
python manage.py migrate

# Créer un superutilisateur
python manage.py createsuperuser
```

### 5. Collecter les fichiers statiques

```bash
python manage.py collectstatic --noinput
```

### 6. Configuration Nginx

Exemple de configuration Nginx (`/etc/nginx/sites-available/kongossa`) :

```nginx
server {
    listen 80;
    server_name kongossa.com www.kongossa.com;
    
    # Redirection HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name kongossa.com www.kongossa.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    # Fichiers statiques
    location /static/ {
        alias /path/to/kongossa/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # Fichiers média
    location /media/ {
        alias /path/to/kongossa/media/;
        expires 7d;
    }
    
    # Proxy vers Django
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 7. Configuration Systemd (Daphne)

Créer un fichier de service (`/etc/systemd/system/kongossa.service`) :

```ini
[Unit]
Description=Kongossa ASGI Server
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/kongossa
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/daphne -b 127.0.0.1 -p 8000 kongossa.asgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

Démarrer le service :

```bash
sudo systemctl daemon-reload
sudo systemctl enable kongossa
sudo systemctl start kongossa
```

### 8. Configuration Redis

```bash
# Installer Redis
sudo apt-get install redis-server

# Démarrer Redis
sudo systemctl start redis
sudo systemctl enable redis
```

### 9. Tâches périodiques (Stories)

Configurer un cron job pour supprimer les stories expirées :

```bash
# Éditer le crontab
crontab -e

# Ajouter cette ligne (exécute tous les jours à 2h du matin)
0 2 * * * cd /path/to/kongossa && /path/to/venv/bin/python manage.py cleanup_expired_stories
```

## 🔒 Sécurité

### Checklist de sécurité

- [ ] `DEBUG = False` en production
- [ ] `SECRET_KEY` unique et sécurisé
- [ ] `ALLOWED_HOSTS` configuré correctement
- [ ] HTTPS activé avec certificat SSL valide
- [ ] Cookies sécurisés (`SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`)
- [ ] Headers de sécurité configurés
- [ ] Base de données avec utilisateur dédié (pas root)
- [ ] Mots de passe forts pour la base de données
- [ ] Redis protégé par mot de passe (si exposé)
- [ ] Backups réguliers de la base de données
- [ ] Logs surveillés pour les erreurs

## 📊 Monitoring

### Logs

Les logs Django sont disponibles dans :
- `/var/log/kongossa/django.log` (à configurer)
- Logs systemd : `journalctl -u kongossa -f`

### Performance

- Utiliser un outil de monitoring (Sentry, New Relic, etc.)
- Surveiller l'utilisation de la mémoire et CPU
- Surveiller les connexions à la base de données
- Surveiller les performances Redis

## 🔄 Mises à jour

### Procédure de mise à jour

1. Sauvegarder la base de données
2. Arrêter le service : `sudo systemctl stop kongossa`
3. Faire un pull des dernières modifications
4. Installer les nouvelles dépendances : `pip install -r requirements.txt`
5. Appliquer les migrations : `python manage.py migrate`
6. Collecter les fichiers statiques : `python manage.py collectstatic --noinput`
7. Redémarrer le service : `sudo systemctl restart kongossa`
8. Vérifier les logs : `journalctl -u kongossa -f`

## 🐛 Dépannage

### Problèmes courants

1. **Erreur de connexion à la base de données**
   - Vérifier les credentials dans `.env`
   - Vérifier que PostgreSQL est démarré : `sudo systemctl status postgresql`

2. **Erreur WebSocket**
   - Vérifier que Redis est démarré : `sudo systemctl status redis`
   - Vérifier la configuration `CHANNEL_LAYERS` dans `settings.py`

3. **Fichiers statiques non servis**
   - Vérifier les permissions : `chmod -R 755 staticfiles/`
   - Vérifier la configuration Nginx

4. **Erreur 502 Bad Gateway**
   - Vérifier que Daphne est démarré : `sudo systemctl status kongossa`
   - Vérifier les logs : `journalctl -u kongossa -n 50`

## 📞 Support

Pour toute question ou problème, consulter la documentation ou ouvrir une issue sur le repository.


