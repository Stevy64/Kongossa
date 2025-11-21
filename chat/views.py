"""
Vues pour le chat Kongossa
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from django.utils import timezone
from django.http import JsonResponse
from .models import Conversation, Message
from django.contrib.auth import get_user_model

User = get_user_model()


def get_chat_sidebar_data(user):
    """Helper function pour récupérer les données de la sidebar (conversations et groupes)"""
    # Récupérer les conversations
    conversations = Conversation.objects.filter(
        participants=user
    ).prefetch_related('participants', 'messages').order_by('-updated_at')
    
    # Ajouter le dernier message et l'autre participant pour chaque conversation
    conversations_data = []
    for conv in conversations:
        other_user = conv.get_other_participant(user)
        last_message = conv.messages.last()
        conversations_data.append({
            'conversation': conv,
            'other_user': other_user,
            'last_message': last_message,
            'unread_count': conv.messages.filter(
                sender__id=other_user.id if other_user else None,
                read_at__isnull=True
            ).count() if other_user else 0,
            'type': 'conversation',
        })
    
    # Récupérer les groupes où l'utilisateur est membre
    try:
        from forum.models import Group, GroupMessage
        from django.db.models import Count
        
        groups = Group.objects.filter(members=user).annotate(
            members_count=Count('members')
        ).order_by('-updated_at')
        
        groups_data = []
        for group in groups:
            last_message = group.messages.last() if hasattr(group, 'messages') else None
            groups_data.append({
                'group': group,
                'last_message': last_message,
                'unread_count': 0,  # TODO: Implémenter le comptage des messages non lus pour les groupes
                'type': 'group',
            })
        
        # Combiner et trier par date de mise à jour
        all_items = conversations_data + groups_data
        # Trier par date de mise à jour (plus récent en premier)
        all_items.sort(key=lambda x: (
            x['conversation'].updated_at if x['type'] == 'conversation' and x.get('conversation') else 
            x['group'].updated_at if x['type'] == 'group' and x.get('group') else timezone.now()
        ), reverse=True)
    except ImportError:
        all_items = conversations_data
    
    return {
        'conversations': conversations_data,
        'all_items': all_items,
    }


@login_required
def chat_list(request):
    """Liste des conversations et groupes"""
    sidebar_data = get_chat_sidebar_data(request.user)
    
    return render(request, 'chat/list.html', sidebar_data)


@login_required
def chat_detail(request, conversation_id):
    """Détails d'une conversation (uniquement si ami)"""
    conversation = get_object_or_404(
        Conversation.objects.prefetch_related('participants', 'messages__sender'),
        id=conversation_id,
        participants=request.user
    )
    
    other_user = conversation.get_other_participant(request.user)
    
    # Vérifier si les utilisateurs sont amis
    if not other_user.is_friend_with(request.user):
        messages.error(request, 'Vous devez être ami avec cet utilisateur pour pouvoir chatter ou l\'appeler')
        return redirect('users:profile', username=other_user.username)
    
    # Marquer les messages comme lus
    unread_messages = Message.objects.filter(
        conversation=conversation,
        sender=other_user,
        read_at__isnull=True
    )
    
    # Marquer les messages comme lus
    unread_messages.update(read_at=timezone.now())
    
    # Marquer les notifications correspondantes comme lues
    try:
        from notifications.models import Notification
        from django.urls import reverse
        related_url = reverse('chat:detail', kwargs={'conversation_id': conversation.id})
        Notification.objects.filter(
            user=request.user,
            notification_type='message',
            related_user=other_user,
            related_url=related_url,
            is_read=False
        ).update(is_read=True)
    except ImportError:
        pass
    
    conversation_messages = conversation.messages.all()
    
    sidebar_data = get_chat_sidebar_data(request.user)
    
    return render(request, 'chat/detail.html', {
        'conversation': conversation,
        'other_user': other_user,
        'messages': conversation_messages,
        **sidebar_data,
    })


@login_required
def start_conversation(request, user_id):
    """Démarrer une conversation avec un utilisateur (uniquement si ami)"""
    other_user = get_object_or_404(User, id=user_id)
    
    # Vérifier si les utilisateurs sont amis
    if not other_user.is_friend_with(request.user):
        messages.error(request, 'Vous devez être ami avec cet utilisateur pour pouvoir chatter ou l\'appeler')
        return redirect('users:profile', username=other_user.username)
    
    # Chercher une conversation existante
    conversation = Conversation.objects.filter(
        participants=request.user
    ).filter(
        participants=other_user
    ).first()
    
    if not conversation:
        conversation = Conversation.objects.create()
        conversation.participants.add(request.user, other_user)
    
    return redirect('chat:detail', conversation_id=conversation.id)


@login_required
@require_http_methods(["POST"])
def send_message(request, conversation_id):
    """Envoyer un message avec fichiers dans une conversation"""
    from django.http import JsonResponse
    
    conversation = get_object_or_404(
        Conversation.objects.prefetch_related('participants'),
        id=conversation_id,
        participants=request.user
    )
    
    content = request.POST.get('content', '').strip()
    image = request.FILES.get('image')
    file = request.FILES.get('file')
    file_name = request.POST.get('file_name', '')
    
    if not content and not image and not file:
        return JsonResponse({'error': 'Le message ne peut pas être vide'}, status=400)
    
    # Détecter si le fichier est une image
    if file:
        if not file_name:
            file_name = file.name
        
        # Vérifier si c'est une image par l'extension
        import mimetypes
        file_type, _ = mimetypes.guess_type(file_name)
        if file_type and file_type.startswith('image/'):
            # C'est une image, l'enregistrer dans le champ image
            image = file
            file = None
            file_name = None
    
    message = Message.objects.create(
        conversation=conversation,
        sender=request.user,
        content=content,
        image=image,
        file=file,
        file_name=file_name
    )
    
    # Mettre à jour la date de modification de la conversation
    conversation.save()
    
    return JsonResponse({
        'success': True,
        'message': {
            'id': message.id,
            'content': message.content,
            'sender': message.sender.username,
            'sender_id': message.sender.id,
            'created_at': message.created_at.isoformat(),
            'image': message.image.url if message.image else None,
            'file': message.file.url if message.file else None,
            'file_name': message.file_name,
        }
    })


@login_required
def contacts_list(request):
    """Liste des contacts pour démarrer une conversation"""
    # Récupérer tous les utilisateurs sauf l'utilisateur actuel
    all_users = User.objects.exclude(id=request.user.id).order_by('username')
    
    # Récupérer les conversations existantes pour marquer les contacts
    existing_conversations = Conversation.objects.filter(
        participants=request.user
    ).prefetch_related('participants')
    
    # Créer un dictionnaire pour marquer les utilisateurs avec qui on a déjà une conversation
    users_with_conversations = {}
    for conv in existing_conversations:
        other_user = conv.get_other_participant(request.user)
        if other_user:
            users_with_conversations[other_user.id] = conv.id
    
    # Préparer les données des contacts
    contacts_data = []
    for user in all_users:
        contacts_data.append({
            'user': user,
            'has_conversation': user.id in users_with_conversations,
            'conversation_id': users_with_conversations.get(user.id),
        })
    
    sidebar_data = get_chat_sidebar_data(request.user)
    
    return render(request, 'chat/contacts.html', {
        'contacts': contacts_data,
        **sidebar_data,
    })
