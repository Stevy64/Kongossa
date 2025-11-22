# Generated manually
from django.conf import settings
from django.db import migrations, models


def create_subscribers_table(apps, schema_editor):
    """Créer la table forum_topic_subscribers si elle n'existe pas"""
    db_alias = schema_editor.connection.alias
    with schema_editor.connection.cursor() as cursor:
        # Vérifier si la table existe déjà
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='forum_topic_subscribers'
        """)
        if not cursor.fetchone():
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
                CREATE INDEX IF NOT EXISTS forum_topic_subscribers_topic_id 
                ON forum_topic_subscribers(topic_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS forum_topic_subscribers_user_id 
                ON forum_topic_subscribers(user_id)
            """)
        else:
            # La table existe déjà, on ne fait rien
            pass


def reverse_subscribers_table(apps, schema_editor):
    """Supprimer la table forum_topic_subscribers"""
    db_alias = schema_editor.connection.alias
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("DROP TABLE IF EXISTS forum_topic_subscribers")


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('forum', '0007_post_video_post_audio_groupmessage_video_groupmessage_audio'),
    ]

    operations = [
        # Créer la table si elle n'existe pas (ne fera rien si elle existe déjà)
        migrations.RunPython(create_subscribers_table, reverse_subscribers_table, atomic=False),
        # Ajouter le champ au modèle
        # On utilise SeparateDatabaseAndState pour indiquer que la table existe déjà dans la DB
        migrations.SeparateDatabaseAndState(
            database_operations=[
                # Ne rien faire dans la base de données - la table existe déjà
                migrations.RunSQL(
                    sql="-- Table forum_topic_subscribers existe déjà",
                    reverse_sql="-- Pas de rollback nécessaire",
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='topic',
                    name='subscribers',
                    field=models.ManyToManyField(blank=True, related_name='subscribed_topics', to=settings.AUTH_USER_MODEL, verbose_name='Abonnés'),
                ),
            ],
        ),
    ]
