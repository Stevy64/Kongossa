# Generated manually
from django.conf import settings
from django.db import migrations, models


def create_group_subscribers_table(apps, schema_editor):
    """Créer la table forum_group_subscribers si elle n'existe pas"""
    db_alias = schema_editor.connection.alias
    with schema_editor.connection.cursor() as cursor:
        # Vérifier si la table existe déjà
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='forum_group_subscribers'
        """)
        if not cursor.fetchone():
            # Créer la table
            cursor.execute("""
                CREATE TABLE forum_group_subscribers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id INTEGER NOT NULL REFERENCES forum_group(id) ON DELETE CASCADE,
                    user_id INTEGER NOT NULL REFERENCES users_user(id) ON DELETE CASCADE,
                    UNIQUE(group_id, user_id)
                )
            """)
            # Créer les index
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS forum_group_subscribers_group_id 
                ON forum_group_subscribers(group_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS forum_group_subscribers_user_id 
                ON forum_group_subscribers(user_id)
            """)


def add_requires_approval_column(apps, schema_editor):
    """Ajouter la colonne requires_approval si elle n'existe pas"""
    db_alias = schema_editor.connection.alias
    with schema_editor.connection.cursor() as cursor:
        # Vérifier si la colonne existe déjà
        cursor.execute("PRAGMA table_info(forum_group)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'requires_approval' not in columns:
            # Ajouter la colonne
            cursor.execute("ALTER TABLE forum_group ADD COLUMN requires_approval BOOLEAN DEFAULT 0 NOT NULL")


def reverse_group_subscribers_table(apps, schema_editor):
    """Supprimer la table forum_group_subscribers"""
    db_alias = schema_editor.connection.alias
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("DROP TABLE IF EXISTS forum_group_subscribers")


def reverse_requires_approval_column(apps, schema_editor):
    """Supprimer la colonne requires_approval (SQLite ne supporte pas DROP COLUMN, donc on ne fait rien)"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('forum', '0008_topic_subscribers'),
    ]

    operations = [
        # Créer la table forum_group_subscribers si elle n'existe pas
        migrations.RunPython(create_group_subscribers_table, reverse_group_subscribers_table, atomic=False),
        # Ajouter la colonne requires_approval si elle n'existe pas
        migrations.RunPython(add_requires_approval_column, reverse_requires_approval_column, atomic=False),
        # Ajouter les champs au modèle
        migrations.SeparateDatabaseAndState(
            database_operations=[
                # Ne rien faire dans la base de données - les tables/colonnes existent déjà
                migrations.RunSQL(
                    sql="-- Table forum_group_subscribers et colonne requires_approval existent déjà",
                    reverse_sql="-- Pas de rollback nécessaire",
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='group',
                    name='subscribers',
                    field=models.ManyToManyField(blank=True, related_name='subscribed_groups', to=settings.AUTH_USER_MODEL, verbose_name='Abonnés'),
                ),
                migrations.AddField(
                    model_name='group',
                    name='requires_approval',
                    field=models.BooleanField(default=False, verbose_name='Nécessite une approbation'),
                ),
            ],
        ),
    ]

