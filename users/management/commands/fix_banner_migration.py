"""
Commande Django pour corriger le problème de migration du champ banner

Cette commande vérifie si la colonne banner existe déjà et marque
la migration comme appliquée si nécessaire.

Usage: python manage.py fix_banner_migration
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone


class Command(BaseCommand):
    help = 'Corrige le problème de migration du champ banner en vérifiant si la colonne existe déjà'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Vérifier si la colonne banner existe
            cursor.execute("PRAGMA table_info(users_user)")
            columns = [row[1] for row in cursor.fetchall()]
            
            self.stdout.write(f"Colonnes actuelles: {columns}")
            
            if 'banner' in columns:
                self.stdout.write(self.style.SUCCESS("✅ La colonne banner existe déjà dans la base de données"))
                
                # Vérifier si la migration 0006 est marquée comme appliquée
                cursor.execute("""
                    SELECT id FROM django_migrations 
                    WHERE app='users' AND name='0006_user_banner'
                """)
                
                if not cursor.fetchone():
                    self.stdout.write("Marquage de la migration 0006_user_banner comme appliquée...")
                    cursor.execute("""
                        INSERT INTO django_migrations (app, name, applied) 
                        VALUES ('users', '0006_user_banner', ?)
                    """, (timezone.now(),))
                    connection.commit()
                    self.stdout.write(self.style.SUCCESS("✅ Migration 0006_user_banner marquée comme appliquée"))
                else:
                    self.stdout.write(self.style.SUCCESS("✅ Migration 0006_user_banner déjà marquée comme appliquée"))
            else:
                self.stdout.write(self.style.WARNING("⚠️ La colonne banner n'existe pas. Exécutez les migrations normalement."))
                
                # Vérifier si la colonne existe mais avec un nom différent
                cursor.execute("PRAGMA table_info(users_user)")
                all_columns = [row[1] for row in cursor.fetchall()]
                self.stdout.write(f"Toutes les colonnes: {all_columns}")
        
        self.stdout.write(self.style.SUCCESS("\n✅ Vérification terminée!"))

