"""
Template filters pour le chat
"""
from django import template
from django.utils import timezone
from datetime import timedelta

register = template.Library()


@register.filter
def format_chat_time(value):
    """Formater l'heure pour l'affichage dans le chat"""
    if not value:
        return ''
    
    now = timezone.now()
    if isinstance(value, str):
        from django.utils.dateparse import parse_datetime
        value = parse_datetime(value)
    
    if not value:
        return ''
    
    # Calculer la différence
    diff = now - value
    
    # Aujourd'hui : afficher l'heure (HH:MM)
    if diff.days == 0:
        return value.strftime('%H:%M')
    
    # Hier : afficher "Hier HH:MM"
    elif diff.days == 1:
        return f"Hier {value.strftime('%H:%M')}"
    
    # Cette semaine : afficher le jour de la semaine
    elif diff.days < 7:
        days = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']
        return f"{days[value.weekday()]} {value.strftime('%H:%M')}"
    
    # Plus ancien : afficher la date complète
    else:
        return value.strftime('%d/%m/%Y %H:%M')

