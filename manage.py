#!/usr/bin/env python
"""
Django's command-line utility for administrative tasks.

Ce script permet d'exécuter les commandes de gestion Django :
- python manage.py runserver : Démarrer le serveur de développement
- python manage.py migrate : Appliquer les migrations
- python manage.py createsuperuser : Créer un superutilisateur
- python manage.py collectstatic : Collecter les fichiers statiques
- etc.
"""
import os
import sys


def main():
    """
    Point d'entrée principal pour les commandes Django.
    
    Configure le module de settings par défaut et exécute la commande
    demandée depuis la ligne de commande.
    """
    # Définir le module de settings par défaut
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kongossa.settings')
    
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    
    # Exécuter la commande demandée
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()

