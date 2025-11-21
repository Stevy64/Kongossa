from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Crée les tables FriendRequest et Friendship manuellement'

    def handle(self, *args, **options):
        sql = """
        CREATE TABLE IF NOT EXISTS users_friendrequest (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            from_user_id INTEGER NOT NULL REFERENCES users_user(id) ON DELETE CASCADE,
            to_user_id INTEGER NOT NULL REFERENCES users_user(id) ON DELETE CASCADE,
            UNIQUE(from_user_id, to_user_id)
        );

        CREATE TABLE IF NOT EXISTS users_friendship (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            status VARCHAR(20) NOT NULL DEFAULT 'accepted',
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            user1_id INTEGER NOT NULL REFERENCES users_user(id) ON DELETE CASCADE,
            user2_id INTEGER NOT NULL REFERENCES users_user(id) ON DELETE CASCADE,
            UNIQUE(user1_id, user2_id)
        );
        """
        
        with connection.cursor() as cursor:
            cursor.executescript(sql)
            self.stdout.write(self.style.SUCCESS('Tables créées avec succès!'))

