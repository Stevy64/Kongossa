# ✅ Checklist de Production - Kongossa

Cette checklist doit être complétée avant de déployer en production.

## 🔐 Sécurité

- [ ] `SECRET_KEY` unique et sécurisé (minimum 50 caractères)
- [ ] `DEBUG = False` dans les variables d'environnement
- [ ] `ALLOWED_HOSTS` configuré avec votre domaine (pas `*`)
- [ ] HTTPS activé avec certificat SSL valide
- [ ] `SECURE_SSL_REDIRECT = True` en production
- [ ] `SESSION_COOKIE_SECURE = True` en production
- [ ] `CSRF_COOKIE_SECURE = True` en production
- [ ] Headers de sécurité configurés (HSTS, X-Frame-Options, etc.)
- [ ] Mots de passe forts pour la base de données
- [ ] Utilisateur de base de données dédié (pas root/admin)

## 🗄️ Base de données

- [ ] PostgreSQL installé et configuré
- [ ] Base de données créée
- [ ] Utilisateur de base de données créé avec permissions appropriées
- [ ] Migrations appliquées : `python manage.py migrate`
- [ ] Backups automatiques configurés
- [ ] Stratégie de restauration testée

## 🔴 Redis

- [ ] Redis installé et démarré
- [ ] Redis protégé par mot de passe (si exposé)
- [ ] `USE_REDIS = True` dans les variables d'environnement
- [ ] Configuration Redis testée avec Django Channels

## 📁 Fichiers statiques et média

- [ ] Fichiers statiques collectés : `python manage.py collectstatic`
- [ ] Serveur web configuré pour servir les fichiers statiques (Nginx)
- [ ] CDN configuré (optionnel mais recommandé)
- [ ] Permissions correctes sur les dossiers `media/` et `staticfiles/`
- [ ] Quotas d'upload configurés

## 🌐 Serveur web

- [ ] Nginx installé et configuré
- [ ] Configuration Nginx pour proxy vers Daphne
- [ ] Support WebSocket configuré dans Nginx
- [ ] Service systemd créé pour Daphne
- [ ] Service démarré et activé : `systemctl enable kongossa`
- [ ] Logs configurés et surveillés

## 🔄 Tâches périodiques

- [ ] Cron job configuré pour supprimer les stories expirées
- [ ] Cron job configuré pour les backups (si nécessaire)
- [ ] Monitoring des tâches périodiques

## 📊 Monitoring et logs

- [ ] Système de logging configuré
- [ ] Logs surveillés pour les erreurs
- [ ] Outil de monitoring configuré (Sentry, New Relic, etc.)
- [ ] Alertes configurées pour les erreurs critiques
- [ ] Métriques de performance surveillées

## 🧪 Tests

- [ ] Tests fonctionnels passés
- [ ] Tests de charge effectués
- [ ] Tests de sécurité effectués
- [ ] Tests de restauration de backup effectués

## 📝 Documentation

- [ ] README.md à jour
- [ ] DEPLOYMENT.md consulté
- [ ] Variables d'environnement documentées
- [ ] Procédures de mise à jour documentées

## 🚀 Déploiement

- [ ] Code versionné et tagué
- [ ] Branche de production identifiée
- [ ] Procédure de rollback préparée
- [ ] Fenêtre de maintenance planifiée (si nécessaire)
- [ ] Équipe notifiée du déploiement

## ✅ Post-déploiement

- [ ] Application accessible via HTTPS
- [ ] Toutes les fonctionnalités testées
- [ ] Performance vérifiée
- [ ] Erreurs surveillées
- [ ] Backups vérifiés

---

**Date de déploiement :** _______________

**Déployé par :** _______________

**Version :** _______________


