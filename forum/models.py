"""
Modèles pour le forum Kongossa
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse

User = get_user_model()


class Topic(models.Model):
    """Modèle pour les thèmes/sujets de discussion"""
    name = models.CharField(max_length=100, unique=True, verbose_name="Nom du thème")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="Slug")
    description = models.TextField(blank=True, verbose_name="Description")
    icon = models.CharField(max_length=50, default="💬", verbose_name="Icône")
    color = models.CharField(max_length=7, default="#9333ea", verbose_name="Couleur")
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_topics', verbose_name="Créateur")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    
    class Meta:
        ordering = ['name']
        verbose_name = "Thème"
        verbose_name_plural = "Thèmes"
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('forum:topic_detail', kwargs={'slug': self.slug})
    
    @property
    def post_count(self):
        return self.posts.count()


class Post(models.Model):
    """Modèle pour les posts du forum"""
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True, blank=True, related_name='posts', verbose_name="Thème")
    content = models.TextField()
    image = models.ImageField(upload_to='posts/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Post"
        verbose_name_plural = "Posts"
    
    def __str__(self):
        return f"Post by {self.author.username} - {self.created_at}"
    
    @property
    def like_count(self):
        return self.likes.count()
    
    @property
    def comment_count(self):
        return self.comments.count()


class Like(models.Model):
    """Modèle pour les likes"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'post']
        verbose_name = "Like"
        verbose_name_plural = "Likes"
    
    def __str__(self):
        return f"{self.user.username} liked {self.post.id}"


class Comment(models.Model):
    """Modèle pour les commentaires"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = "Commentaire"
        verbose_name_plural = "Commentaires"
    
    def __str__(self):
        return f"Comment by {self.author.username} on post {self.post.id}"


class Group(models.Model):
    """Modèle pour les groupes de discussion par topic (comme Telegram/WhatsApp)"""
    name = models.CharField(max_length=100, verbose_name="Nom du groupe")
    description = models.TextField(blank=True, verbose_name="Description")
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='groups', verbose_name="Thème")
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_groups', verbose_name="Créateur")
    members = models.ManyToManyField(User, related_name='forum_groups', verbose_name="Membres")
    image = models.ImageField(upload_to='groups/', blank=True, null=True, verbose_name="Image")
    is_public = models.BooleanField(default=True, verbose_name="Public")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = "Groupe"
        verbose_name_plural = "Groupes"
    
    def __str__(self):
        return f"{self.name} ({self.topic.name})"
    
    def get_absolute_url(self):
        return reverse('forum:group_detail', kwargs={'group_id': self.id})
    
    @property
    def member_count(self):
        return self.members.count()
    
    def is_member(self, user):
        """Vérifier si un utilisateur est membre du groupe"""
        if not user.is_authenticated:
            return False
        return self.members.filter(id=user.id).exists()


class GroupRequest(models.Model):
    """Modèle pour les demandes d'accès aux groupes"""
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='access_requests', verbose_name="Groupe")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_requests', verbose_name="Utilisateur")
    message = models.TextField(blank=True, verbose_name="Message")
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'En attente'),
            ('approved', 'Approuvée'),
            ('rejected', 'Rejetée'),
        ],
        default='pending',
        verbose_name="Statut"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['group', 'user']
        ordering = ['-created_at']
        verbose_name = "Demande d'accès"
        verbose_name_plural = "Demandes d'accès"
    
    def __str__(self):
        return f"Request from {self.user.username} to {self.group.name}"


class GroupMessage(models.Model):
    """Modèle pour les messages dans les groupes"""
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_messages')
    content = models.TextField(blank=True)
    image = models.ImageField(upload_to='group_messages/', blank=True, null=True)
    file = models.FileField(upload_to='group_messages/files/', blank=True, null=True)
    file_name = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = "Message de groupe"
        verbose_name_plural = "Messages de groupe"
    
    def __str__(self):
        return f"Message from {self.sender.username} in {self.group.name}"