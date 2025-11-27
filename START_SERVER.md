# 🚀 Comment démarrer le serveur Kongossa

## ⚠️ Important : WebSockets nécessitent Daphne

Le chat en temps réel (peer-to-peer ET groupes) nécessite **Daphne** (serveur ASGI) pour fonctionner. Le serveur Django standard (`runserver`) **ne supporte pas les WebSockets**.

## ✅ Fonctionnalités du chat implémentées

- ✅ **Chat peer-to-peer** : Conversations privées en temps réel
- ✅ **Chat de groupe** : Messages de groupe en temps réel
- ✅ **Envoi instantané** : Messages affichés immédiatement après l'envoi
- ✅ **Support fichiers** : Images, vidéos, audio, fichiers
- ✅ **Indicateurs de frappe** : Voir quand quelqu'un écrit
- ✅ **Read receipts** : Double coche pour les messages lus (chat privé)

## 📋 Méthodes de démarrage

### Option 1 : Daphne (Recommandé - Support WebSockets)

```bash
# Installer Daphne si ce n'est pas déjà fait
pip install daphne

# Démarrer le serveur avec Daphne
daphne -b 0.0.0.0 -p 8000 kongossa.asgi:application
```

Ou avec Python directement :
```bash
python -m daphne -b 0.0.0.0 -p 8000 kongossa.asgi:application
```

### Option 2 : Runserver (⚠️ Pas de WebSockets)

```bash
# ⚠️ ATTENTION : Le chat en temps réel ne fonctionnera PAS avec cette méthode
python manage.py runserver
```

## 🔧 Résolution des problèmes

### Erreur "Not Found: /ws/chat/1/"

Si vous voyez cette erreur, c'est que vous utilisez `runserver` au lieu de Daphne.

**Solution :** Utilisez Daphne comme indiqué dans l'Option 1 ci-dessus.

### Erreur "X-Frame-Options: deny"

Cette erreur a été corrigée. Le paramètre `X_FRAME_OPTIONS` est maintenant défini sur `'SAMEORIGIN'` dans `settings.py`, ce qui permet l'affichage du chat dans un iframe.

## ✅ Vérification

Une fois le serveur démarré avec Daphne, vous devriez voir :
- Les messages apparaissent instantanément dans le chat
- Les WebSockets se connectent correctement (pas d'erreur 404)
- Le popup chat s'affiche correctement

