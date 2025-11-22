"""
Vues pour le forum Kongossa
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Count, Q
from django.urls import reverse
from .models import Post, Like, Comment, Topic, Group, GroupMessage, GroupRequest
from stories.models import Story
from django.contrib.auth import get_user_model

User = get_user_model()


def create_group_notification(group_request, notification_type, title, message):
    """Créer une notification pour une demande d'accès au groupe"""
    try:
        from notifications.models import Notification
        related_url = reverse('forum:group_detail', kwargs={'group_id': group_request.group.id})
        Notification.create_notification(
            user=group_request.user,
            notification_type=notification_type,
            title=title,
            message=message,
            related_user=group_request.group.creator,
            related_url=related_url
        )
    except ImportError:
        # Si l'app notifications n'est pas disponible, ignorer silencieusement
        pass


def feed(request):
    """Fil d'actualité principal - Mode broadcast uniquement (posts sans topic)"""
    if not request.user.is_authenticated:
        return redirect('/auth/login/')
    
    # Filtrer uniquement les posts sans topic (mode broadcast)
    posts = Post.objects.filter(topic__isnull=True).select_related('author').prefetch_related('likes', 'comments').order_by('-created_at')
    
    # Pagination
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Vérifier les likes de l'utilisateur
    liked_posts = set()
    if request.user.is_authenticated:
        liked_posts = set(Like.objects.filter(
            user=request.user,
            post__in=page_obj.object_list
        ).values_list('post_id', flat=True))
    
    # Récupérer les stories actives pour le carrousel (uniquement première page)
    users_with_stories = []
    if page_number == 1 or not request.GET.get('page'):
        active_stories = Story.objects.filter(
            expires_at__gt=timezone.now()
        ).select_related('user').order_by('-created_at')
        
        # Grouper par utilisateur
        users_with_stories_dict = {}
        for story in active_stories:
            if story.user_id not in users_with_stories_dict:
                users_with_stories_dict[story.user_id] = {
                    'user': story.user,
                    'stories': []
                }
            users_with_stories_dict[story.user_id]['stories'].append(story)
        users_with_stories = list(users_with_stories_dict.values())
    
    # Si requête AJAX, retourner uniquement les posts
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('ajax'):
        return render(request, 'forum/posts_list.html', {
            'page_obj': page_obj,
            'liked_posts': liked_posts,
        })
    
    return render(request, 'forum/feed.html', {
        'page_obj': page_obj,
        'liked_posts': liked_posts,
        'users_with_stories': users_with_stories,
    })


@login_required
def topics_list(request):
    """Liste des thèmes de discussion avec recherche de groupes intégrée"""
    if not request.user.is_authenticated:
        return redirect('/auth/login/')
    
    # Récupérer les topics auxquels l'utilisateur est abonné
    subscribed_topic_ids = set()
    if request.user.is_authenticated:
        try:
            subscribed_topic_ids = set(request.user.subscribed_topics.filter(is_active=True).values_list('id', flat=True))
        except Exception:
            # Si la table n'existe pas encore, retourner un set vide
            subscribed_topic_ids = set()
    
    # Filtrer pour n'afficher que les topics auxquels l'utilisateur est abonné
    topics = Topic.objects.filter(
        is_active=True,
        id__in=subscribed_topic_ids
    ).annotate(
        posts_count=Count('posts'),
        subscribers_count=Count('subscribers')
    ).order_by('name')
    
    # Recherche de groupes (si une requête de recherche est présente)
    groups = None
    search_query = request.GET.get('q', '').strip()
    topic_filter = request.GET.get('topic', '')
    show_groups = request.GET.get('show', '') == 'groups' or search_query
    
    # Récupérer les groupes auxquels l'utilisateur est déjà abonné ou membre
    subscribed_group_ids = set()
    user_subscribed_group_ids = set()
    if request.user.is_authenticated:
        try:
            subscribed_group_ids = set(request.user.subscribed_groups.values_list('id', flat=True))
            user_subscribed_group_ids = set(request.user.forum_groups.values_list('id', flat=True))
            # Combiner les deux sets
            user_subscribed_group_ids = subscribed_group_ids | user_subscribed_group_ids
        except Exception:
            subscribed_group_ids = set()
            user_subscribed_group_ids = set()
    
    # Toujours afficher les groupes auxquels l'utilisateur est abonné/membre
    # Et aussi les groupes publics si recherche ou show_groups
    if show_groups or search_query:
        # Récupérer les groupes publics OU les groupes auxquels l'utilisateur est abonné/membre
        groups = Group.objects.filter(
            Q(is_public=True) | Q(id__in=user_subscribed_group_ids)
        ).annotate(
            members_count=Count('members'),
            subscribers_count=Count('subscribers')
        )
        
        # Filtrer par recherche
        if search_query:
            groups = groups.filter(
                Q(name__icontains=search_query) | 
                Q(description__icontains=search_query) |
                Q(topic__name__icontains=search_query)
            )
        
        # Filtrer par topic
        if topic_filter:
            groups = groups.filter(topic__slug=topic_filter)
        
        groups = groups.order_by('-subscribers_count', '-members_count', '-created_at')
    else:
        # Si pas de recherche, afficher uniquement les groupes auxquels l'utilisateur est abonné/membre
        if user_subscribed_group_ids:
            groups = Group.objects.filter(
                id__in=user_subscribed_group_ids
            ).annotate(
                members_count=Count('members'),
                subscribers_count=Count('subscribers')
            ).order_by('-updated_at')
            # Forcer show_groups à True pour afficher les groupes
            show_groups = True
        else:
            groups = Group.objects.none()
    
    # Récupérer tous les topics pour le filtre
    all_topics = Topic.objects.filter(is_active=True).order_by('name')
    
    return render(request, 'forum/topics_list.html', {
        'topics': topics,
        'subscribed_topic_ids': subscribed_topic_ids,
        'groups': groups,
        'all_topics': all_topics,
        'search_query': search_query,
        'selected_topic': topic_filter,
        'subscribed_group_ids': subscribed_group_ids,
        'show_groups': show_groups,
    })


@login_required
def create_topic(request):
    """Créer un nouveau sujet de discussion"""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        icon = request.POST.get('icon', '💬').strip()
        color = request.POST.get('color', '#9333ea').strip()
        
        if not name:
            messages.error(request, 'Le nom du sujet est requis')
            return redirect('forum:topics_list')
        
        # Générer le slug à partir du nom
        from django.utils.text import slugify
        slug = slugify(name)
        
        # Vérifier si le slug existe déjà
        if Topic.objects.filter(slug=slug).exists():
            messages.error(request, 'Un sujet avec ce nom existe déjà')
            return redirect('forum:topics_list')
        
        try:
            topic = Topic.objects.create(
                name=name,
                slug=slug,
                description=description,
                icon=icon,
                color=color,
                creator=request.user,
                is_active=True
            )
            messages.success(request, f'Sujet "{topic.name}" créé avec succès!')
            return redirect('forum:topic_detail', slug=topic.slug)
        except Exception as e:
            messages.error(request, f'Erreur lors de la création du sujet: {str(e)}')
            return redirect('forum:topics_list')
    
    # GET request - afficher le formulaire
    return render(request, 'forum/create_topic.html')


@login_required
def topic_detail(request, slug):
    """Détails d'un thème avec ses posts - Style feed principal"""
    topic = get_object_or_404(Topic, slug=slug, is_active=True)
    
    # Vérifier si l'utilisateur est abonné au topic
    if not topic.is_subscribed(request.user):
        messages.error(request, 'Vous devez être abonné à ce forum pour y accéder')
        return redirect('forum:topics_list')
    
    posts = Post.objects.filter(topic=topic).select_related('author', 'topic').prefetch_related('likes', 'comments').order_by('-created_at')
    
    # Pagination
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Vérifier les likes de l'utilisateur
    liked_posts = set()
    if request.user.is_authenticated:
        liked_posts = set(Like.objects.filter(
            user=request.user,
            post__in=page_obj.object_list
        ).values_list('post_id', flat=True))
    
    # Récupérer les stories actives des membres du topic (uniquement première page)
    users_with_stories = []
    if page_number == 1 or not request.GET.get('page'):
        # Récupérer les utilisateurs qui ont posté dans ce topic
        topic_authors = posts.values_list('author_id', flat=True).distinct()
        active_stories = Story.objects.filter(
            expires_at__gt=timezone.now(),
            user_id__in=topic_authors
        ).select_related('user').order_by('-created_at')
        
        # Grouper par utilisateur
        users_with_stories_dict = {}
        for story in active_stories:
            if story.user_id not in users_with_stories_dict:
                users_with_stories_dict[story.user_id] = {
                    'user': story.user,
                    'stories': []
                }
            users_with_stories_dict[story.user_id]['stories'].append(story)
        users_with_stories = list(users_with_stories_dict.values())
    
    # Récupérer les groupes du topic
    groups = Group.objects.filter(topic=topic).annotate(
        members_count=Count('members')
    ).order_by('-updated_at')
    
    # Récupérer le premier groupe (pour le bouton flottant)
    first_group = groups.first() if groups.exists() else None
    
    # Vérifier les groupes où l'utilisateur est membre
    user_groups = set()
    pending_requests = set()
    user_group_requests = {}  # Dict pour stocker les demandes par groupe
    if request.user.is_authenticated:
        user_groups = set(groups.filter(members=request.user).values_list('id', flat=True))
        pending_requests = set(GroupRequest.objects.filter(
            user=request.user,
            group__in=groups,
            status='pending'
        ).values_list('group_id', flat=True))
        
        # Récupérer les demandes d'accès de l'utilisateur pour chaque groupe
        user_requests = GroupRequest.objects.filter(
            user=request.user,
            group__in=groups,
            status='pending'
        ).select_related('group')
        
        for req in user_requests:
            user_group_requests[req.group.id] = req
    
    # Si requête AJAX, retourner uniquement les posts
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('ajax'):
        return render(request, 'forum/posts_list.html', {
            'page_obj': page_obj,
            'liked_posts': liked_posts,
        })
    
    return render(request, 'forum/topic_detail.html', {
        'topic': topic,
        'page_obj': page_obj,
        'liked_posts': liked_posts,
        'groups': groups,
        'user_groups': user_groups,
        'pending_requests': pending_requests,
        'user_group_requests': user_group_requests,
        'users_with_stories': users_with_stories,
        'first_group': first_group,
    })


@login_required
@require_http_methods(["POST"])
def create_post(request):
    """Créer un nouveau post"""
    import mimetypes
    
    content = request.POST.get('content', '').strip()
    image = request.FILES.get('image')
    video = request.FILES.get('video')
    audio = request.FILES.get('audio')
    topic_id = request.POST.get('topic_id')
    group_id = request.POST.get('group_id')
    
    if not content and not image and not video and not audio:
        messages.error(request, 'Le post doit contenir du texte, une image, une vidéo ou un audio')
        return redirect('forum:feed')
    
    topic = None
    if topic_id:
        try:
            topic = Topic.objects.get(id=topic_id, is_active=True)
        except Topic.DoesNotExist:
            pass
    
    post = Post.objects.create(
        author=request.user,
        topic=topic,
        content=content,
        image=image,
        video=video,
        audio=audio
    )
    messages.success(request, 'Post créé avec succès!')
    
    # Si un group_id est fourni, rediriger vers le fil d'actualité du groupe
    if group_id:
        try:
            group = Group.objects.get(id=group_id)
            return redirect('forum:group_feed', group_id=group.id)
        except Group.DoesNotExist:
            pass
    
    # Sinon, rediriger vers le topic ou le feed principal
    if topic:
        return redirect('forum:topic_detail', slug=topic.slug)
    return redirect('/feed/')


@login_required
@require_http_methods(["POST"])
def toggle_like(request, post_id):
    """Ajouter/retirer un like"""
    post = get_object_or_404(Post, id=post_id)
    like, created = Like.objects.get_or_create(
        user=request.user,
        post=post
    )
    
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
    
    return JsonResponse({
        'liked': liked,
        'like_count': post.like_count
    })


@login_required
@require_http_methods(["POST"])
def add_comment(request, post_id):
    """Ajouter un commentaire"""
    post = get_object_or_404(Post, id=post_id)
    content = request.POST.get('content', '').strip()
    
    if not content:
        return JsonResponse({'error': 'Le commentaire ne peut pas être vide'}, status=400)
    
    comment = Comment.objects.create(
        post=post,
        author=request.user,
        content=content
    )
    
    return JsonResponse({
        'success': True,
        'comment': {
            'id': comment.id,
            'content': comment.content,
            'author': comment.author.username,
            'author_avatar': comment.author.avatar.url if comment.author.avatar else '',
            'created_at': comment.created_at.strftime('%d/%m/%Y %H:%M'),
        },
        'comment_count': post.comment_count
    })


@login_required
def post_detail(request, post_id):
    """Détails d'un post avec commentaires"""
    post = get_object_or_404(Post.objects.select_related('author').prefetch_related('comments__author'), id=post_id)
    is_liked = Like.objects.filter(user=request.user, post=post).exists()
    
    return render(request, 'forum/post_detail.html', {
        'post': post,
        'is_liked': is_liked,
    })


@login_required
def groups_list(request, topic_slug=None):
    """Liste des groupes de discussion - Groupes auxquels l'utilisateur est abonné"""
    # Afficher uniquement les groupes auxquels l'utilisateur est abonné ou membre
    groups = Group.objects.filter(
        Q(subscribers=request.user) | Q(members=request.user)
    ).annotate(
        members_count=Count('members'),
        subscribers_count=Count('subscribers')
    ).distinct().order_by('-updated_at')
    
    # Vérifier les groupes où l'utilisateur est membre ou abonné
    user_groups = set(groups.values_list('id', flat=True))
    
    return render(request, 'forum/groups_list.html', {
        'groups': groups,
        'topic': None,
        'user_groups': user_groups,
    })


@login_required
def group_feed(request, group_id):
    """Fil d'actualité d'un groupe - Affiche les posts du topic du groupe"""
    group = get_object_or_404(Group, id=group_id)
    
    # Vérifier si l'utilisateur peut accéder au groupe (abonné ou membre)
    if not group.can_access(request.user):
        messages.error(request, 'Vous devez être abonné à ce groupe pour y accéder')
        return redirect('forum:topics_list')
    
    topic = group.topic
    
    # Récupérer les posts du topic du groupe
    posts = Post.objects.filter(topic=topic).select_related('author', 'topic').prefetch_related('likes', 'comments').order_by('-created_at')
    
    # Pagination
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Vérifier les likes de l'utilisateur
    liked_posts = set()
    if request.user.is_authenticated:
        liked_posts = set(Like.objects.filter(
            user=request.user,
            post__in=page_obj.object_list
        ).values_list('post_id', flat=True))
    
    # Récupérer les stories actives des membres du groupe (uniquement première page)
    users_with_stories = []
    if page_number == 1 or not request.GET.get('page'):
        # Récupérer les utilisateurs qui sont membres du groupe
        group_member_ids = group.members.values_list('id', flat=True)
        active_stories = Story.objects.filter(
            expires_at__gt=timezone.now(),
            user_id__in=group_member_ids
        ).select_related('user').order_by('-created_at')
        
        # Grouper par utilisateur
        users_with_stories_dict = {}
        for story in active_stories:
            if story.user_id not in users_with_stories_dict:
                users_with_stories_dict[story.user_id] = {
                    'user': story.user,
                    'stories': []
                }
            users_with_stories_dict[story.user_id]['stories'].append(story)
        users_with_stories = list(users_with_stories_dict.values())
    
    # Si requête AJAX, retourner uniquement les posts
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('ajax'):
        return render(request, 'forum/posts_list.html', {
            'page_obj': page_obj,
            'liked_posts': liked_posts,
        })
    
    return render(request, 'forum/group_feed.html', {
        'group': group,
        'topic': topic,
        'page_obj': page_obj,
        'liked_posts': liked_posts,
        'users_with_stories': users_with_stories,
    })


@login_required
def group_detail(request, group_id):
    """Détails d'un groupe avec ses messages - Accès restreint aux abonnés/membres uniquement"""
    group = get_object_or_404(Group.objects.prefetch_related('members', 'subscribers', 'messages__sender'), id=group_id)
    
    # Vérifier si l'utilisateur peut accéder au groupe (abonné ou membre)
    if not group.can_access(request.user):
        messages.error(request, 'Vous devez être abonné à ce groupe pour y accéder')
        return redirect('forum:topics_list')
    
    is_member = group.is_member(request.user)
    
    messages_list = group.messages.all()[:50]  # Derniers 50 messages
    
    # Récupérer les données de la sidebar (conversations et groupes)
    try:
        from chat.views import get_chat_sidebar_data
        sidebar_data = get_chat_sidebar_data(request.user)
    except ImportError:
        sidebar_data = {'conversations': [], 'all_items': []}
    
    # Récupérer les membres du groupe avec leurs avatars
    group_members = group.members.all().order_by('username')
    
    return render(request, 'forum/group_detail.html', {
        'group': group,
        'messages': messages_list,
        'is_member': is_member,
        'group_members': group_members,
        **sidebar_data,
    })


@login_required
@require_http_methods(["POST"])
def create_group(request, topic_slug):
    """Créer un nouveau groupe"""
    topic = get_object_or_404(Topic, slug=topic_slug, is_active=True)
    name = request.POST.get('name', '').strip()
    description = request.POST.get('description', '').strip()
    image = request.FILES.get('image')
    is_public = request.POST.get('is_public', 'on') == 'on'
    
    if not name:
        messages.error(request, 'Le nom du groupe est requis')
        return redirect('forum:topic_detail', slug=topic_slug)
    
    group = Group.objects.create(
        name=name,
        description=description,
        topic=topic,
        creator=request.user,
        image=image,
        is_public=is_public
    )
    group.members.add(request.user)  # Ajouter le créateur comme membre
    
    messages.success(request, f'Groupe "{group.name}" créé avec succès!')
    return redirect('forum:group_detail', group_id=group.id)


@login_required
@require_http_methods(["POST"])
def request_group_access(request, group_id):
    """Demander l'accès à un groupe"""
    group = get_object_or_404(Group, id=group_id)
    message = request.POST.get('message', '').strip()
    
    if group.is_member(request.user):
        messages.info(request, 'Vous êtes déjà membre de ce groupe')
    else:
        # Vérifier si une demande existe déjà
        request_obj, created = GroupRequest.objects.get_or_create(
            group=group,
            user=request.user,
            defaults={'message': message, 'status': 'pending'}
        )
        
        if created:
            messages.success(request, f'Votre demande d\'accès au groupe "{group.name}" a été envoyée')
        else:
            if request_obj.status == 'pending':
                messages.info(request, 'Vous avez déjà une demande en attente pour ce groupe')
            elif request_obj.status == 'rejected':
                # Réactiver la demande
                request_obj.status = 'pending'
                request_obj.message = message
                request_obj.save()
                messages.success(request, f'Votre demande d\'accès a été renouvelée')
    
    # Rediriger vers la page du topic
    return redirect('forum:topic_detail', slug=group.topic.slug)


@login_required
@require_http_methods(["POST"])
def approve_group_request(request, request_id):
    """Approuver une demande d'accès à un groupe"""
    group_request = get_object_or_404(GroupRequest, id=request_id)
    group = group_request.group
    
    # Vérifier que l'utilisateur est le créateur du groupe
    if group.creator != request.user:
        messages.error(request, 'Vous n\'avez pas la permission d\'approuver cette demande')
        return redirect('forum:manage_group', group_id=group.id)
    
    # Vérifier que la demande est en attente
    if group_request.status != 'pending':
        messages.info(request, 'Cette demande a déjà été traitée')
        return redirect('forum:manage_group', group_id=group.id)
    
    # Ajouter l'utilisateur au groupe
    group.members.add(group_request.user)
    group_request.status = 'approved'
    group_request.save()
    
    # Créer une notification pour le demandeur
    create_group_notification(
        group_request,
        'group_request_approved',
        f'Demande d\'accès approuvée',
        f'Votre demande d\'accès au groupe "{group.name}" a été approuvée par {request.user.username}. Vous pouvez maintenant accéder au groupe.'
    )
    
    messages.success(request, f'La demande de {group_request.user.username} a été approuvée')
    return redirect('forum:manage_group', group_id=group.id)


@login_required
@require_http_methods(["POST"])
def reject_group_request(request, request_id):
    """Rejeter une demande d'accès à un groupe"""
    group_request = get_object_or_404(GroupRequest, id=request_id)
    group = group_request.group
    
    # Vérifier que l'utilisateur est le créateur du groupe
    if group.creator != request.user:
        messages.error(request, 'Vous n\'avez pas la permission de rejeter cette demande')
        return redirect('forum:manage_group', group_id=group.id)
    
    # Vérifier que la demande est en attente
    if group_request.status != 'pending':
        messages.info(request, 'Cette demande a déjà été traitée')
        return redirect('forum:manage_group', group_id=group.id)
    
    group_request.status = 'rejected'
    group_request.save()
    
    # Créer une notification pour le demandeur
    create_group_notification(
        group_request,
        'group_request_rejected',
        f'Demande d\'accès rejetée',
        f'Votre demande d\'accès au groupe "{group.name}" a été rejetée par {request.user.username}.'
    )
    
    messages.info(request, f'La demande de {group_request.user.username} a été rejetée')
    return redirect('forum:manage_group', group_id=group.id)


@login_required
@require_http_methods(["POST"])
def cancel_group_request(request, request_id):
    """Annuler une demande d'accès à un groupe"""
    group_request = get_object_or_404(GroupRequest, id=request_id)
    group = group_request.group
    
    # Vérifier que l'utilisateur est le demandeur
    if group_request.user != request.user:
        messages.error(request, 'Vous n\'avez pas la permission d\'annuler cette demande')
        return redirect('forum:topic_detail', slug=group.topic.slug)
    
    # Vérifier que la demande est en attente
    if group_request.status != 'pending':
        messages.info(request, 'Cette demande a déjà été traitée')
        return redirect('forum:topic_detail', slug=group.topic.slug)
    
    # Supprimer la demande
    group_request.delete()
    
    messages.success(request, f'Votre demande d\'accès au groupe "{group.name}" a été annulée')
    return redirect('forum:topic_detail', slug=group.topic.slug)


@login_required
@require_http_methods(["POST"])
def leave_group(request, group_id):
    """Quitter un groupe"""
    group = get_object_or_404(Group, id=group_id)
    
    if group.creator == request.user:
        messages.error(request, 'Le créateur ne peut pas quitter le groupe')
    elif group.is_member(request.user):
        group.members.remove(request.user)
        messages.success(request, f'Vous avez quitté le groupe "{group.name}"')
    else:
        messages.info(request, 'Vous n\'êtes pas membre de ce groupe')
    
    return redirect('forum:groups_list')


@login_required
@require_http_methods(["POST"])
def send_group_message(request, group_id):
    """Envoyer un message dans un groupe"""
    group = get_object_or_404(Group, id=group_id)
    
    if not group.is_member(request.user):
        return JsonResponse({'error': 'Vous devez être membre pour envoyer des messages'}, status=403)
    
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
    
    message = GroupMessage.objects.create(
        group=group,
        sender=request.user,
        content=content,
        image=image,
        video=video,
        audio=audio,
        file=file,
        file_name=file_name
    )
    
    # Mettre à jour la date de modification du groupe
    group.save()
    
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
        }
    })


@login_required
def manage_group(request, group_id):
    """Gérer un groupe (CRUD) - Uniquement pour le créateur"""
    group = get_object_or_404(Group.objects.prefetch_related('members', 'access_requests__user'), id=group_id)
    
    # Vérifier que l'utilisateur est le créateur
    if group.creator != request.user:
        messages.error(request, 'Vous n\'avez pas la permission de gérer ce groupe')
        return redirect('forum:group_detail', group_id=group_id)
    
    # Récupérer les demandes d'accès en attente
    pending_requests = group.access_requests.filter(status='pending').select_related('user').order_by('-created_at')
    
    return render(request, 'forum/manage_group.html', {
        'group': group,
        'pending_requests': pending_requests,
    })


@login_required
@require_http_methods(["POST"])
def update_group(request, group_id):
    """Mettre à jour un groupe"""
    group = get_object_or_404(Group, id=group_id)
    
    # Vérifier que l'utilisateur est le créateur
    if group.creator != request.user:
        messages.error(request, 'Vous n\'avez pas la permission de modifier ce groupe')
        return redirect('forum:group_detail', group_id=group_id)
    
    name = request.POST.get('name', '').strip()
    description = request.POST.get('description', '').strip()
    image = request.FILES.get('image')
    is_public = request.POST.get('is_public', 'off') == 'on'
    
    if not name:
        messages.error(request, 'Le nom du groupe est requis')
        return redirect('forum:manage_group', group_id=group_id)
    
    group.name = name
    group.description = description
    group.is_public = is_public
    if image:
        group.image = image
    group.save()
    
    messages.success(request, f'Le groupe "{group.name}" a été mis à jour')
    return redirect('forum:manage_group', group_id=group_id)


@login_required
@require_http_methods(["POST"])
def delete_group(request, group_id):
    """Supprimer un groupe"""
    group = get_object_or_404(Group, id=group_id)
    
    # Vérifier que l'utilisateur est le créateur
    if group.creator != request.user:
        messages.error(request, 'Vous n\'avez pas la permission de supprimer ce groupe')
        return redirect('forum:group_detail', group_id=group_id)
    
    topic_slug = group.topic.slug
    group_name = group.name
    group.delete()
    
    messages.success(request, f'Le groupe "{group_name}" a été supprimé')
    return redirect('forum:topic_detail', slug=topic_slug)


@login_required
def manage_topic(request, slug):
    """Gérer un sujet (CRUD) - Uniquement pour le créateur"""
    topic = get_object_or_404(Topic, slug=slug)
    
    # Vérifier que l'utilisateur est le créateur
    if topic.creator and topic.creator != request.user:
        messages.error(request, 'Vous n\'avez pas la permission de gérer ce sujet')
        return redirect('forum:topic_detail', slug=slug)
    
    # Récupérer les statistiques
    posts_count = topic.posts.count()
    groups_count = topic.groups.count()
    
    return render(request, 'forum/manage_topic.html', {
        'topic': topic,
        'posts_count': posts_count,
        'groups_count': groups_count,
    })


@login_required
@require_http_methods(["POST"])
def update_topic(request, slug):
    """Mettre à jour un sujet"""
    topic = get_object_or_404(Topic, slug=slug)
    
    # Vérifier que l'utilisateur est le créateur
    if topic.creator and topic.creator != request.user:
        messages.error(request, 'Vous n\'avez pas la permission de modifier ce sujet')
        return redirect('forum:topic_detail', slug=slug)
    
    name = request.POST.get('name', '').strip()
    description = request.POST.get('description', '').strip()
    icon = request.POST.get('icon', '').strip()
    color = request.POST.get('color', '#9333ea').strip()
    
    if not name:
        messages.error(request, 'Le nom du sujet est requis')
        return redirect('forum:manage_topic', slug=slug)
    
    # Générer le slug si le nom a changé
    from django.utils.text import slugify
    new_slug = slugify(name)
    
    if new_slug != topic.slug and Topic.objects.filter(slug=new_slug).exists():
        messages.error(request, 'Un sujet avec ce nom existe déjà')
        return redirect('forum:manage_topic', slug=slug)
    
    topic.name = name
    topic.description = description
    topic.icon = icon
    topic.color = color
    if new_slug != topic.slug:
        topic.slug = new_slug
    
    topic.save()
    
    messages.success(request, f'Le sujet "{topic.name}" a été mis à jour')
    return redirect('forum:manage_topic', slug=topic.slug)


@login_required
@require_http_methods(["POST"])
def archive_topic(request, slug):
    """Archiver un sujet (désactiver)"""
    topic = get_object_or_404(Topic, slug=slug)
    
    # Vérifier que l'utilisateur est le créateur
    if topic.creator and topic.creator != request.user:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Vous n\'avez pas la permission d\'archiver ce sujet'}, status=403)
        messages.error(request, 'Vous n\'avez pas la permission d\'archiver ce sujet')
        return redirect('forum:topic_detail', slug=slug)
    
    topic_name = topic.name
    topic.is_active = False  # Désactiver
    topic.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': f'Le forum "{topic_name}" a été archivé'})
    
    messages.success(request, f'Le sujet "{topic_name}" a été archivé')
    return redirect('forum:topics_list')


@login_required
@require_http_methods(["POST"])
def delete_topic(request, slug):
    """Supprimer définitivement un sujet"""
    topic = get_object_or_404(Topic, slug=slug)
    
    # Vérifier que l'utilisateur est le créateur
    if topic.creator and topic.creator != request.user:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Vous n\'avez pas la permission de supprimer ce sujet'}, status=403)
        messages.error(request, 'Vous n\'avez pas la permission de supprimer ce sujet')
        return redirect('forum:topic_detail', slug=slug)
    
    topic_name = topic.name
    topic.delete()  # Supprimer définitivement
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': f'Le forum "{topic_name}" a été supprimé'})
    
    messages.success(request, f'Le sujet "{topic_name}" a été supprimé')
    return redirect('forum:topics_list')


@login_required
@require_http_methods(["POST"])
def toggle_topic_subscribe(request, slug):
    """S'abonner/Se désabonner d'un topic"""
    topic = get_object_or_404(Topic, slug=slug, is_active=True)
    
    if topic.subscribers.filter(id=request.user.id).exists():
        # Se désabonner
        topic.subscribers.remove(request.user)
        is_subscribed = False
        message = f'Vous vous êtes désabonné du forum "{topic.name}"'
    else:
        # S'abonner
        topic.subscribers.add(request.user)
        is_subscribed = True
        message = f'Vous vous êtes abonné au forum "{topic.name}"'
    
    subscribers_count = topic.subscribers.count()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'is_subscribed': is_subscribed,
            'subscribers_count': subscribers_count,
            'message': message
        })
    
    messages.success(request, message)
    return redirect('forum:topics_list')

@login_required
@require_http_methods(["POST"])
def toggle_group_subscribe(request, group_id):
    """S'abonner/Se désabonner d'un groupe"""
    group = get_object_or_404(Group, id=group_id)
    
    # Si le groupe nécessite une approbation, utiliser le système de demande
    if group.requires_approval:
        if group.is_subscribed(request.user) or group.is_member(request.user):
            # Se désabonner
            group.subscribers.remove(request.user)
            is_subscribed = False
            message = f'Vous vous êtes désabonné du groupe "{group.name}"'
        else:
            # Créer une demande d'accès
            request_obj, created = GroupRequest.objects.get_or_create(
                group=group,
                user=request.user,
                defaults={'message': '', 'status': 'pending'}
            )
            
            if created:
                # Créer une notification pour le créateur
                from notifications.models import Notification
                Notification.objects.create(
                    user=group.creator,
                    notification_type='group_request',
                    title='Nouvelle demande d\'accès',
                    message=f'{request.user.username} demande à rejoindre le groupe "{group.name}"',
                    related_object_id=group.id
                )
                message = f'Votre demande d\'accès au groupe "{group.name}" a été envoyée'
            else:
                message = 'Vous avez déjà une demande en attente pour ce groupe'
            
            is_subscribed = False
            subscribers_count = group.subscribers.count()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'is_subscribed': is_subscribed,
                    'subscribers_count': subscribers_count,
                    'message': message,
                    'requires_approval': True
                })
            
            messages.success(request, message)
            return redirect('forum:topics_list')
    else:
        # Groupe public, abonnement direct
        if group.subscribers.filter(id=request.user.id).exists():
            # Se désabonner
            group.subscribers.remove(request.user)
            # Retirer aussi des membres si présent
            if group.is_member(request.user):
                group.members.remove(request.user)
            is_subscribed = False
            message = f'Vous vous êtes désabonné du groupe "{group.name}"'
        else:
            # S'abonner
            group.subscribers.add(request.user)
            # Ajouter aussi aux membres pour l'accès
            if not group.is_member(request.user):
                group.members.add(request.user)
            is_subscribed = True
            message = f'Vous vous êtes abonné au groupe "{group.name}"'
    
    subscribers_count = group.subscribers.count()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'is_subscribed': is_subscribed,
            'subscribers_count': subscribers_count,
            'message': message
        })
    
    messages.success(request, message)
    return redirect('forum:topics_list')


