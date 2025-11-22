"""
Commande Django pour marquer la migration 0008_topic_subscribers comme appliquée
Usage: python manage.py mark_subscribers_migration
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone


class Command(BaseCommand):
    help = 'Marque la migration 0008_topic_subscribers comme appliquée'

    def handle(self, *args, **options):
        cursor = connection.cursor()
        
        try:
            # Vérifier si la migration est déjà marquée comme appliquée
            cursor.execute("""
                SELECT name FROM django_migrations 
                WHERE app='forum' AND name='0008_topic_subscribers'
            """)
            
            if cursor.fetchone():
                self.stdout.write(
                    self.style.SUCCESS('✅ La migration est déjà marquée comme appliquée!')
                )
            else:
                # Marquer la migration comme appliquée
                cursor.execute("""
                    INSERT INTO django_migrations (app, name, applied) 
                    VALUES (?, ?, ?)
                """, ('forum', '0008_topic_subscribers', timezone.now().isoformat()))
                
                connection.commit()
                self.stdout.write(
                    self.style.SUCCESS('✅ Migration marquée comme appliquée!')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erreur: {e}')
            )
            import traceback
            traceback.print_exc()

