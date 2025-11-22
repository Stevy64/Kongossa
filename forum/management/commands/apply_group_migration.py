"""
Commande Django pour appliquer manuellement la migration 0009_group_subscribers_requires_approval
Usage: python manage.py apply_group_migration
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone


class Command(BaseCommand):
    help = 'Applique manuellement la migration 0009_group_subscribers_requires_approval'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Vérifier si la colonne requires_approval existe
            cursor.execute("PRAGMA table_info(forum_group)")
            columns = [row[1] for row in cursor.fetchall()]
            
            self.stdout.write(f"Colonnes actuelles: {columns}")
            
            # Ajouter requires_approval si elle n'existe pas
            if 'requires_approval' not in columns:
                self.stdout.write("Ajout de la colonne requires_approval...")
                cursor.execute("ALTER TABLE forum_group ADD COLUMN requires_approval BOOLEAN DEFAULT 0 NOT NULL")
                self.stdout.write(self.style.SUCCESS("✅ Colonne requires_approval ajoutée"))
            else:
                self.stdout.write(self.style.SUCCESS("✅ Colonne requires_approval existe déjà"))
            
            # Vérifier si la table forum_group_subscribers existe
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='forum_group_subscribers'
            """)
            if not cursor.fetchone():
                self.stdout.write("Création de la table forum_group_subscribers...")
                cursor.execute("""
                    CREATE TABLE forum_group_subscribers (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        group_id INTEGER NOT NULL REFERENCES forum_group(id) ON DELETE CASCADE,
                        user_id INTEGER NOT NULL REFERENCES users_user(id) ON DELETE CASCADE,
                        UNIQUE(group_id, user_id)
                    )
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS forum_group_subscribers_group_id 
                    ON forum_group_subscribers(group_id)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS forum_group_subscribers_user_id 
                    ON forum_group_subscribers(user_id)
                """)
                self.stdout.write(self.style.SUCCESS("✅ Table forum_group_subscribers créée"))
            else:
                self.stdout.write(self.style.SUCCESS("✅ Table forum_group_subscribers existe déjà"))
            
            # Marquer la migration comme appliquée
            cursor.execute("""
                SELECT id FROM django_migrations 
                WHERE app='forum' AND name='0009_group_subscribers_requires_approval'
            """)
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO django_migrations (app, name, applied) 
                    VALUES (?, ?, ?)
                """, ('forum', '0009_group_subscribers_requires_approval', timezone.now()))
                self.stdout.write(self.style.SUCCESS("✅ Migration marquée comme appliquée"))
            else:
                self.stdout.write(self.style.SUCCESS("✅ Migration déjà marquée comme appliquée"))
            
            connection.commit()
            self.stdout.write(self.style.SUCCESS("\n✅ Migration appliquée avec succès!"))

