"""
Modèles utilisateurs pour Kongossa
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    """Modèle utilisateur personnalisé"""
    email = models.EmailField(unique=True, blank=True, null=True)
    phone = models.CharField(max_length=20, unique=True, blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    banner = models.ImageField(upload_to='banners/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Pour l'authentification passwordless
    passwordless_token = models.CharField(max_length=100, blank=True, null=True)
    passwordless_token_expires = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
    
    def __str__(self):
        return self.username or self.email or self.phone
    
    @property
    def followers_count(self):
        return self.followers.count()
    
    @property
    def following_count(self):
        return self.following.count()
    
    def is_followed_by(self, user):
        """Vérifier si un utilisateur suit cet utilisateur"""
        if not user.is_authenticated:
            return False
        return Follow.objects.filter(follower=user, following=self).exists()
    
    def is_friend_with(self, user):
        """Vérifier si un utilisateur est ami avec cet utilisateur"""
        if not user.is_authenticated:
            return False
        return Friendship.objects.filter(
            (models.Q(user1=self, user2=user) | models.Q(user1=user, user2=self)),
            status='accepted'
        ).exists()
    
    def has_pending_friend_request_from(self, user):
        """Vérifier si cet utilisateur a une demande d'ami en attente de la part d'un utilisateur"""
        if not user.is_authenticated:
            return False
        return FriendRequest.objects.filter(
            from_user=user,
            to_user=self,
            status='pending'
        ).exists()
    
    def has_pending_friend_request_to(self, user):
        """Vérifier si cet utilisateur a envoyé une demande d'ami en attente à un utilisateur"""
        if not user.is_authenticated:
            return False
        return FriendRequest.objects.filter(
            from_user=self,
            to_user=user,
            status='pending'
        ).exists()


class Follow(models.Model):
    """Modèle pour les abonnements entre utilisateurs"""
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['follower', 'following']
        verbose_name = "Abonnement"
        verbose_name_plural = "Abonnements"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.follower.username} suit {self.following.username}"


class FriendRequest(models.Model):
    """Modèle pour les demandes d'ami"""
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_friend_requests')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_friend_requests')
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'En attente'),
            ('accepted', 'Acceptée'),
            ('rejected', 'Refusée'),
        ],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['from_user', 'to_user']
        verbose_name = "Demande d'ami"
        verbose_name_plural = "Demandes d'ami"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Demande de {self.from_user.username} à {self.to_user.username}"


class Friendship(models.Model):
    """Modèle pour les amitiés acceptées"""
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friendships_as_user1')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friendships_as_user2')
    status = models.CharField(
        max_length=20,
        choices=[
            ('accepted', 'Acceptée'),
            ('blocked', 'Bloquée'),
        ],
        default='accepted'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user1', 'user2']
        verbose_name = "Amitié"
        verbose_name_plural = "Amitiés"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Amitié entre {self.user1.username} et {self.user2.username}"

