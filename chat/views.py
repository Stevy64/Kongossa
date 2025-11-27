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
    
    return render(request, 'chat/chat_list.html', {
        'user': request.user,
        **sidebar_data,
    })


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
    
    conversation_messages = conversation.messages.all()[:50]  # Charger les 50 derniers messages initialement
    
    sidebar_data = get_chat_sidebar_data(request.user)
    
    return render(request, 'chat/chat_detail.html', {
        'conversation': conversation,
        'other_user': other_user,
        'messages': conversation_messages,
        'user': request.user,
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
    video = request.FILES.get('video')
    audio = request.FILES.get('audio')
    file = request.FILES.get('file')
    file_name = request.POST.get('file_name', '')
    
    if not content and not image and not video and not audio and not file:
        return JsonResponse({'error': 'Le message ne peut pas être vide'}, status=400)
    
    # Détecter si le fichier est une image, vidéo ou audio
    if file:
        if not file_name:
            file_name = file.name
        
        # Vérifier le type de fichier
        import mimetypes
        file_type, _ = mimetypes.guess_type(file_name)
        if file_type:
            if file_type.startswith('image/'):
                # C'est une image, l'enregistrer dans le champ image
                image = file
                file = None
                file_name = None
            elif file_type.startswith('video/'):
                # C'est une vidéo, l'enregistrer dans le champ video
                video = file
                file = None
                file_name = None
            elif file_type.startswith('audio/'):
                # C'est un audio, l'enregistrer dans le champ audio
                audio = file
                file = None
                file_name = None
    
    message = Message.objects.create(
        conversation=conversation,
        sender=request.user,
        content=content,
        image=image,
        video=video,
        audio=audio,
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
            'sender_avatar': message.sender.avatar.url if message.sender.avatar else None,
            'created_at': message.created_at.isoformat(),
            'image': message.image.url if message.image else None,
            'video': message.video.url if message.video else None,
            'audio': message.audio.url if message.audio else None,
            'file': message.file.url if message.file else None,
            'file_name': message.file_name,
            'read_at': message.read_at.isoformat() if message.read_at else None,
        }
    })


@login_required
@require_http_methods(["POST"])
def mark_message_read(request, message_id):
    """Marquer un message comme lu"""
    from django.http import JsonResponse
    
    message = get_object_or_404(Message, id=message_id)
    
    # Vérifier que l'utilisateur fait partie de la conversation
    if request.user not in message.conversation.participants.all():
        return JsonResponse({'error': 'Accès refusé'}, status=403)
    
    # Marquer comme lu seulement si ce n'est pas le propre message de l'utilisateur
    if message.sender != request.user and not message.read_at:
        message.read_at = timezone.now()
        message.save()
    
    return JsonResponse({'success': True})


@login_required
def load_messages(request, conversation_id):
    """Charger plus de messages (infinite scroll)"""
    from django.http import JsonResponse
    
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        participants=request.user
    )
    
    before_id = request.GET.get('before')
    limit = int(request.GET.get('limit', 20))
    
    messages_query = conversation.messages.all()
    
    if before_id:
        messages_query = messages_query.filter(id__lt=before_id)
    
    messages = messages_query.order_by('-created_at')[:limit]
    
    messages_data = []
    for msg in reversed(messages):  # Inverser pour avoir l'ordre chronologique
        messages_data.append({
            'id': msg.id,
            'content': msg.content,
            'sender': msg.sender.username,
            'sender_id': msg.sender.id,
            'sender_avatar': msg.sender.avatar.url if msg.sender.avatar else None,
            'created_at': msg.created_at.isoformat(),
            'image': msg.image.url if msg.image else None,
            'video': msg.video.url if msg.video else None,
            'audio': msg.audio.url if msg.audio else None,
            'file': msg.file.url if msg.file else None,
            'file_name': msg.file_name,
            'read_at': msg.read_at.isoformat() if msg.read_at else None,
        })
    
    return JsonResponse({
        'messages': messages_data,
        'has_more': len(messages) == limit
    })


@login_required
def get_new_messages(request, conversation_id):
    """Récupérer les nouveaux messages depuis un certain ID (pour polling)"""
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        participants=request.user
    )
    
    last_message_id = request.GET.get('last_message_id')
    
    if last_message_id:
        try:
            last_message_id = int(last_message_id)
            messages_query = conversation.messages.filter(id__gt=last_message_id)
        except ValueError:
            messages_query = conversation.messages.all()
    else:
        # Si pas de last_message_id, retourner les 10 derniers messages
        messages_query = conversation.messages.all()
    
    messages = messages_query.order_by('created_at')
    
    messages_data = []
    for msg in messages:
        messages_data.append({
            'id': msg.id,
            'content': msg.content,
            'sender': msg.sender.username,
            'sender_id': msg.sender.id,
            'sender_avatar': msg.sender.avatar.url if msg.sender.avatar else None,
            'created_at': msg.created_at.isoformat(),
            'image': msg.image.url if msg.image else None,
            'video': msg.video.url if msg.video else None,
            'audio': msg.audio.url if msg.audio else None,
            'file': msg.file.url if msg.file else None,
            'file_name': msg.file_name,
            'read_at': msg.read_at.isoformat() if msg.read_at else None,
        })
    
    return JsonResponse({
        'messages': messages_data,
        'count': len(messages_data)
    })


@login_required
def get_unread_count(request):
    """Récupérer le nombre total de messages non lus pour l'utilisateur"""
    # Récupérer toutes les conversations de l'utilisateur
    conversations = Conversation.objects.filter(participants=request.user)
    
    total_unread = 0
    for conv in conversations:
        other_user = conv.get_other_participant(request.user)
        if other_user:
            unread_count = conv.messages.filter(
                sender=other_user,
                read_at__isnull=True
            ).count()
            total_unread += unread_count
    
    return JsonResponse({
        'unread_count': total_unread
    })


@login_required
def contacts_list(request):
    """Liste des contacts pour démarrer une conversation (uniquement les amis)"""
    # Récupérer uniquement les amis de l'utilisateur
    from users.models import Friendship
    
    # Récupérer toutes les amitiés où l'utilisateur est impliqué
    friendships = Friendship.objects.filter(
        Q(user1=request.user) | Q(user2=request.user),
        status='accepted'
    ).select_related('user1', 'user2')
    
    # Extraire les amis
    friends = []
    for friendship in friendships:
        if friendship.user1 == request.user:
            friends.append(friendship.user2)
        else:
            friends.append(friendship.user1)
    
    # Trier par username
    friends = sorted(friends, key=lambda u: u.username)
    
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
    
    # Préparer les données des contacts (uniquement les amis)
    contacts_data = []
    for user in friends:
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
