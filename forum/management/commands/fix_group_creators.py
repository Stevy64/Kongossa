"""
Commande pour corriger les groupes existants : ajouter le créateur comme membre et abonné
"""
from django.core.management.base import BaseCommand
from forum.models import Group


class Command(BaseCommand):
    help = 'Ajoute le créateur comme membre et abonné pour tous les groupes existants'

    def handle(self, *args, **options):
        groups_fixed = 0
        for group in Group.objects.all():
            if group.creator:
                fixed = False
                # Ajouter comme membre si pas déjà membre
                if not group.members.filter(id=group.creator.id).exists():
                    group.members.add(group.creator)
                    fixed = True
                # Ajouter comme abonné si pas déjà abonné
                if not group.subscribers.filter(id=group.creator.id).exists():
                    group.subscribers.add(group.creator)
                    fixed = True
                if fixed:
                    groups_fixed += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Groupe "{group.name}" (ID: {group.id}) - Créateur ajouté comme membre et abonné'
                        )
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Correction terminée : {groups_fixed} groupe(s) corrigé(s)'
            )
        )

