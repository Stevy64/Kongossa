"""
Commande Django pour créer la table forum_topic_subscribers
Usage: python manage.py create_subscribers_table
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Crée la table forum_topic_subscribers si elle n\'existe pas'

    def handle(self, *args, **options):
        cursor = connection.cursor()
        
        try:
            # Vérifier si la table existe
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='forum_topic_subscribers'
            """)
            
            if cursor.fetchone():
                self.stdout.write(
                    self.style.SUCCESS('✅ La table forum_topic_subscribers existe déjà!')
                )
            else:
                # Créer la table
                cursor.execute("""
                    CREATE TABLE forum_topic_subscribers (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        topic_id INTEGER NOT NULL REFERENCES forum_topic(id) ON DELETE CASCADE,
                        user_id INTEGER NOT NULL REFERENCES users_user(id) ON DELETE CASCADE,
                        UNIQUE(topic_id, user_id)
                    )
                """)
                
                # Créer les index
                cursor.execute("""
                    CREATE INDEX forum_topic_subscribers_topic_id 
                    ON forum_topic_subscribers(topic_id)
                """)
                
                cursor.execute("""
                    CREATE INDEX forum_topic_subscribers_user_id 
                    ON forum_topic_subscribers(user_id)
                """)
                
                connection.commit()
                self.stdout.write(
                    self.style.SUCCESS('✅ Table forum_topic_subscribers créée avec succès!')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erreur: {e}')
            )
            import traceback
            traceback.print_exc()

