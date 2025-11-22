"""
Vues pour les stories Kongossa
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from .models import Story, StoryView
from django.contrib.auth import get_user_model

User = get_user_model()


@login_required
def stories_feed(request):
    """Carrousel de stories en haut du feed"""
    # Récupérer tous les utilisateurs avec des stories actives
    active_stories = Story.objects.filter(
        expires_at__gt=timezone.now()
    ).select_related('user').order_by('-created_at')
    
    # Grouper par utilisateur
    users_with_stories = {}
    for story in active_stories:
        if story.user_id not in users_with_stories:
            users_with_stories[story.user_id] = {
                'user': story.user,
                'stories': []
            }
        users_with_stories[story.user_id]['stories'].append(story)
    
    return render(request, 'stories/feed.html', {
        'users_with_stories': list(users_with_stories.values()),
    })


@login_required
def story_viewer(request, story_id):
    """Visionneuse de story en plein écran"""
    story = get_object_or_404(Story, id=story_id)
    
    if story.is_expired:
        messages.error(request, 'Cette story a expiré')
        return redirect('stories:feed')
    
    # Marquer comme vue
    StoryView.objects.get_or_create(
        story=story,
        user=request.user
    )
    
    # Récupérer toutes les stories de l'utilisateur pour navigation
    user_stories = Story.objects.filter(
        user=story.user,
        expires_at__gt=timezone.now()
    ).order_by('created_at')
    
    return render(request, 'stories/viewer.html', {
        'story': story,
        'user_stories': user_stories,
        'current_index': list(user_stories).index(story) if story in user_stories else 0,
    })


@login_required
def create_story_form(request):
    """Formulaire de création de story"""
    return render(request, 'stories/create.html')


@login_required
@require_http_methods(["POST"])
def create_story(request):
    """Créer une nouvelle story"""
    content = request.POST.get('content', '').strip()
    image = request.FILES.get('image')
    video = request.FILES.get('video')
    
    if not content and not image and not video:
        messages.error(request, 'Vous devez ajouter du texte, une image ou une vidéo')
        return redirect('stories:create_form')
    
    story = Story.objects.create(
        user=request.user,
        content=content,
        image=image,
        video=video
    )
    
    messages.success(request, 'Story créée! Elle expirera dans 24h')
    return redirect('stories:viewer', story_id=story.id)
