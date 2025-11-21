"""
Commande Django pour supprimer automatiquement les stories expirées
À exécuter via un cron job toutes les heures
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from stories.models import Story


class Command(BaseCommand):
    help = 'Supprime les stories expirées (plus de 24h)'

    def handle(self, *args, **options):
        expired_stories = Story.objects.filter(expires_at__lt=timezone.now())
        count = expired_stories.count()
        expired_stories.delete()
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully deleted {count} expired stories')
        )

