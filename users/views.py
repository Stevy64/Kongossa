"""
Vues pour l'authentification et les profils utilisateurs
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
from .models import User, Follow, FriendRequest, Friendship


def signup_view(request):
    """Page d'inscription"""
    if request.user.is_authenticated:
        return redirect('/feed/')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        password_confirm = request.POST.get('password_confirm', '').strip()
        
        # Validation
        if not username:
            messages.error(request, 'Le nom d\'utilisateur est requis')
        elif not email:
            messages.error(request, 'L\'email est requis')
        elif not password:
            messages.error(request, 'Le mot de passe est requis')
        elif password != password_confirm:
            messages.error(request, 'Les mots de passe ne correspondent pas')
        elif len(password) < 6:
            messages.error(request, 'Le mot de passe doit contenir au moins 6 caractères')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Ce nom d\'utilisateur est déjà pris')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'Cet email est déjà utilisé')
        else:
            # Créer l'utilisateur
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            messages.success(request, 'Compte créé avec succès!')
            login(request, user)
            return redirect('/feed/')
    
    return render(request, 'users/signup.html')


def login_view(request):
    """Page de connexion"""
    if request.user.is_authenticated:
        return redirect('/feed/')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if email and password:
            try:
                user = User.objects.get(email=email)
                if user.check_password(password):
                    login(request, user)
                    return redirect('/feed/')
                else:
                    messages.error(request, 'Mot de passe incorrect')
            except User.DoesNotExist:
                messages.error(request, 'Utilisateur non trouvé. Créez un compte d\'abord.')
    
    return render(request, 'users/login.html')


def passwordless_login(request):
    """Connexion sans mot de passe (lien magique)"""
    login_url = None
    
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            try:
                user = User.objects.get(email=email)
                # Générer un token
                token = get_random_string(32)
                user.passwordless_token = token
                user.passwordless_token_expires = timezone.now() + timezone.timedelta(hours=1)
                user.save()
                
                # Construire le lien
                login_url = f"{request.scheme}://{request.get_host()}/auth/verify/{token}/"
                
                # En développement, afficher le lien directement
                # En production, envoyer par email
                if settings.DEBUG:
                    messages.success(request, f'Lien de connexion généré! Cliquez sur le lien ci-dessous.')
                else:
                    # En production, envoyer l'email
                    try:
                        send_mail(
                            'Connexion à Kongossa',
                            f'Cliquez sur ce lien pour vous connecter: {login_url}',
                            settings.DEFAULT_FROM_EMAIL or 'noreply@kongossa.com',
                            [email],
                            fail_silently=False,
                        )
                        messages.success(request, 'Un lien de connexion a été envoyé à votre email')
                    except Exception as e:
                        messages.error(request, f'Erreur lors de l\'envoi de l\'email: {str(e)}')
                        # En cas d'erreur, afficher le lien quand même en développement
                        if settings.DEBUG:
                            messages.info(request, f'Lien de connexion: {login_url}')
            except User.DoesNotExist:
                messages.error(request, 'Email non trouvé. Créez un compte d\'abord.')
    
    return render(request, 'users/passwordless_login.html', {'login_url': login_url})


def verify_token(request, token):
    """Vérifier le token de connexion passwordless"""
    try:
        user = User.objects.get(
            passwordless_token=token,
            passwordless_token_expires__gt=timezone.now()
        )
        user.passwordless_token = None
        user.passwordless_token_expires = None
        user.save()
        login(request, user)
        messages.success(request, 'Connexion réussie!')
        return redirect('/feed/')
    except User.DoesNotExist:
        messages.error(request, 'Lien invalide ou expiré')
        return redirect('users:login')


@login_required
def logout_view(request):
    """Déconnexion"""
    logout(request)
    messages.success(request, 'Vous avez été déconnecté')
    return redirect('users:login')


@login_required
def profile(request, username):
    """Profil utilisateur"""
    try:
        profile_user = User.objects.get(username=username)
        from forum.models import Post
        posts = Post.objects.filter(author=profile_user).order_by('-created_at')[:10]
        from stories.models import Story
        active_stories = Story.objects.filter(
            user=profile_user,
            expires_at__gt=timezone.now()
        )
        is_following = False
        is_friend = False
        friend_request_status = None
        pending_request_from_me = False
        pending_request_to_me = False
        friend_request = None
        
        if request.user.is_authenticated:
            is_following = profile_user.is_followed_by(request.user)
            is_friend = profile_user.is_friend_with(request.user)
            # Vérifier si request.user a envoyé une demande à profile_user
            pending_request_from_me = request.user.has_pending_friend_request_to(profile_user)
            # Vérifier si profile_user a envoyé une demande à request.user
            pending_request_to_me = profile_user.has_pending_friend_request_to(request.user)
            
            if pending_request_from_me:
                friend_request_status = 'sent'
                # Récupérer l'objet FriendRequest pour pouvoir l'annuler
                friend_request = FriendRequest.objects.filter(
                    from_user=request.user,
                    to_user=profile_user,
                    status='pending'
                ).first()
            elif pending_request_to_me:
                friend_request_status = 'received'
                # Récupérer la demande d'ami reçue
                friend_request = FriendRequest.objects.filter(
                    from_user=profile_user,
                    to_user=request.user,
                    status='pending'
                ).first()
            elif is_friend:
                friend_request_status = 'friends'
                friend_request = None
        
        return render(request, 'users/profile.html', {
            'profile_user': profile_user,
            'user': request.user,  # S'assurer que user est dans le contexte
            'posts': posts,
            'active_stories': active_stories,
            'is_following': is_following,
            'is_friend': is_friend,
            'friend_request_status': friend_request_status,
            'pending_request_from_me': pending_request_from_me,
            'pending_request_to_me': pending_request_to_me,
            'friend_request': friend_request,
        })
    except User.DoesNotExist:
        messages.error(request, 'Utilisateur non trouvé')
        return redirect('forum:feed')


@login_required
def edit_profile(request):
    """Modifier le profil"""
    if request.method == 'POST':
        user = request.user
        try:
            # Mettre à jour la bio
            user.bio = request.POST.get('bio', '').strip()
            
            # Mettre à jour l'email avec validation
            email = request.POST.get('email', '').strip()
            if email:
                # Vérifier si l'email est déjà utilisé par un autre utilisateur
                if User.objects.filter(email=email).exclude(id=user.id).exists():
                    messages.error(request, 'Cet email est déjà utilisé par un autre utilisateur')
                    return render(request, 'users/edit_profile.html', {'user': user})
                user.email = email
            elif user.email:  # Si l'email est vide mais qu'il y en avait un avant, on le garde
                pass
            else:
                user.email = None  # Permettre de supprimer l'email si vide
            
            # Mettre à jour le téléphone avec validation
            phone = request.POST.get('phone', '').strip()
            if phone:
                # Vérifier si le téléphone est déjà utilisé par un autre utilisateur
                if User.objects.filter(phone=phone).exclude(id=user.id).exists():
                    messages.error(request, 'Ce numéro de téléphone est déjà utilisé par un autre utilisateur')
                    return render(request, 'users/edit_profile.html', {'user': user})
                user.phone = phone
            elif user.phone:  # Si le téléphone est vide mais qu'il y en avait un avant, on le garde
                pass
            else:
                user.phone = None  # Permettre de supprimer le téléphone si vide
            
            # Mettre à jour le prénom et le nom
            user.first_name = request.POST.get('first_name', '').strip()
            user.last_name = request.POST.get('last_name', '').strip()
            
            # Gérer l'upload de l'avatar
            if 'avatar' in request.FILES and request.FILES['avatar']:
                avatar_file = request.FILES['avatar']
                # Valider la taille du fichier (max 5MB)
                if avatar_file.size > 5 * 1024 * 1024:
                    messages.error(request, 'L\'image de profil est trop grande. Taille maximale : 5MB')
                    return render(request, 'users/edit_profile.html', {'user': user})
                # Valider le type de fichier
                if not avatar_file.content_type.startswith('image/'):
                    messages.error(request, 'Le fichier doit être une image')
                    return render(request, 'users/edit_profile.html', {'user': user})
                user.avatar = avatar_file
            
            # Gérer l'upload de la bannière
            if 'banner' in request.FILES and request.FILES['banner']:
                banner_file = request.FILES['banner']
                # Valider la taille du fichier (max 10MB)
                if banner_file.size > 10 * 1024 * 1024:
                    messages.error(request, 'La bannière est trop grande. Taille maximale : 10MB')
                    return render(request, 'users/edit_profile.html', {'user': user})
                # Valider le type de fichier
                if not banner_file.content_type.startswith('image/'):
                    messages.error(request, 'Le fichier doit être une image')
                    return render(request, 'users/edit_profile.html', {'user': user})
                user.banner = banner_file
            
            # Sauvegarder les modifications
            user.save()
            messages.success(request, 'Profil mis à jour avec succès')
            # S'assurer que le username existe avant de rediriger
            if user.username:
                return redirect('users:profile', username=user.username)
            else:
                return redirect('forum:feed')
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la mise à jour du profil: {str(e)}')
            return render(request, 'users/edit_profile.html', {'user': user})
    
    return render(request, 'users/edit_profile.html', {'user': request.user})


@login_required
@require_http_methods(["POST"])
def toggle_follow(request, username):
    """Suivre/Ne plus suivre un utilisateur"""
    try:
        target_user = User.objects.get(username=username)
        if target_user == request.user:
            return JsonResponse({'error': 'Vous ne pouvez pas vous suivre vous-même'}, status=400)
        
        follow, created = Follow.objects.get_or_create(
            follower=request.user,
            following=target_user
        )
        
        if not created:
            follow.delete()
            is_following = False
        else:
            is_following = True
        
        return JsonResponse({
            'is_following': is_following,
            'followers_count': target_user.followers_count
        })
    except User.DoesNotExist:
        return JsonResponse({'error': 'Utilisateur non trouvé'}, status=404)


@login_required
@require_http_methods(["POST"])
def send_friend_request(request, username):
    """Envoyer une demande d'ami"""
    try:
        target_user = User.objects.get(username=username)
        if target_user == request.user:
            return JsonResponse({'error': 'Vous ne pouvez pas vous envoyer une demande d\'ami à vous-même'}, status=400)
        
        # Vérifier si déjà ami
        if target_user.is_friend_with(request.user):
            return JsonResponse({'error': 'Vous êtes déjà ami avec cet utilisateur'}, status=400)
        
        # Vérifier si une demande existe déjà
        existing_request = FriendRequest.objects.filter(
            from_user=request.user,
            to_user=target_user
        ).first()
        
        if existing_request:
            if existing_request.status == 'pending':
                return JsonResponse({'error': 'Une demande d\'ami est déjà en attente'}, status=400)
            elif existing_request.status == 'rejected':
                # Réactiver la demande
                existing_request.status = 'pending'
                existing_request.save()
                return JsonResponse({'success': True, 'status': 'sent'})
        
        # Créer une nouvelle demande
        friend_request = FriendRequest.objects.create(
            from_user=request.user,
            to_user=target_user,
            status='pending'
        )
        
        # Créer une notification
        try:
            from notifications.models import Notification
            from django.urls import reverse
            related_url = reverse('users:profile', kwargs={'username': request.user.username})
            Notification.create_notification(
                user=target_user,
                notification_type='friend_request',
                title='Nouvelle demande d\'ami',
                message=f'{request.user.username} vous a envoyé une demande d\'ami',
                related_user=request.user,
                related_url=related_url
            )
        except ImportError:
            pass
        
        return JsonResponse({'success': True, 'status': 'sent'})
    except User.DoesNotExist:
        return JsonResponse({'error': 'Utilisateur non trouvé'}, status=404)


@login_required
@require_http_methods(["POST"])
def accept_friend_request(request, request_id):
    """Accepter une demande d'ami"""
    try:
        friend_request = FriendRequest.objects.get(
            id=request_id,
            to_user=request.user,
            status='pending'
        )
        
        friend_request.status = 'accepted'
        friend_request.save()
        
        # Créer l'amitié (dans les deux sens pour faciliter les requêtes)
        user1, user2 = sorted([friend_request.from_user, friend_request.to_user], key=lambda u: u.id)
        Friendship.objects.get_or_create(
            user1=user1,
            user2=user2,
            defaults={'status': 'accepted'}
        )
        
        # Créer une notification pour l'expéditeur
        try:
            from notifications.models import Notification
            from django.urls import reverse
            related_url = reverse('users:profile', kwargs={'username': request.user.username})
            Notification.create_notification(
                user=friend_request.from_user,
                notification_type='friend_request_accepted',
                title='Demande d\'ami acceptée',
                message=f'{request.user.username} a accepté votre demande d\'ami',
                related_user=request.user,
                related_url=related_url
            )
        except ImportError:
            pass
        
        return JsonResponse({'success': True, 'status': 'accepted'})
    except FriendRequest.DoesNotExist:
        return JsonResponse({'error': 'Demande d\'ami non trouvée'}, status=404)


@login_required
@require_http_methods(["POST"])
def reject_friend_request(request, request_id):
    """Refuser une demande d'ami"""
    try:
        friend_request = FriendRequest.objects.get(
            id=request_id,
            to_user=request.user,
            status='pending'
        )
        
        friend_request.status = 'rejected'
        friend_request.save()
        
        return JsonResponse({'success': True, 'status': 'rejected'})
    except FriendRequest.DoesNotExist:
        return JsonResponse({'error': 'Demande d\'ami non trouvée'}, status=404)


@login_required
@require_http_methods(["POST"])
def cancel_friend_request(request, username):
    """Annuler une demande d'ami envoyée"""
    try:
        target_user = User.objects.get(username=username)
        friend_request = FriendRequest.objects.get(
            from_user=request.user,
            to_user=target_user,
            status='pending'
        )
        friend_request.delete()
        return JsonResponse({'success': True})
    except (User.DoesNotExist, FriendRequest.DoesNotExist):
        return JsonResponse({'error': 'Demande d\'ami non trouvée'}, status=404)

