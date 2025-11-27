from django.contrib import admin
from .models import Post, Like, Comment, Topic, Group, GroupRequest, GroupMessage


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'creator', 'is_active', 'post_count', 'subscribers_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ['subscribers']
    
    def post_count(self, obj):
        return obj.posts.count()
    post_count.short_description = 'Nombre de posts'
    
    def subscribers_count(self, obj):
        return obj.subscribers.count()
    subscribers_count.short_description = 'Abonnés'


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['id', 'author', 'content_preview', 'topic', 'like_count', 'comment_count', 'created_at']
    list_filter = ['created_at', 'author', 'topic']
    search_fields = ['content', 'author__username', 'topic__name']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Contenu'


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'created_at']
    list_filter = ['created_at']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['id', 'post', 'author', 'content_preview', 'created_at']
    list_filter = ['created_at']
    search_fields = ['content', 'author__username']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Contenu'


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'topic', 'creator', 'is_public', 'requires_approval', 'member_count', 'subscribers_count', 'created_at']
    list_filter = ['is_public', 'requires_approval', 'created_at', 'topic']
    search_fields = ['name', 'description', 'creator__username', 'topic__name']
    filter_horizontal = ['members', 'subscribers']
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 50  # Afficher plus de groupes par page
    show_full_result_count = True  # Afficher le nombre total réel
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('name', 'description', 'topic', 'creator', 'image')
        }),
        ('Paramètres', {
            'fields': ('is_public', 'requires_approval')
        }),
        ('Membres et abonnés', {
            'fields': ('members', 'subscribers')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = 'Membres'
    
    def subscribers_count(self, obj):
        return obj.subscribers.count()
    subscribers_count.short_description = 'Abonnés'


@admin.register(GroupRequest)
class GroupRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'group', 'status', 'created_at', 'updated_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'group__name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Demande', {
            'fields': ('user', 'group', 'message', 'status')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(GroupMessage)
class GroupMessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'group', 'sender', 'content_preview', 'has_media', 'created_at']
    list_filter = ['created_at', 'group']
    search_fields = ['content', 'sender__username', 'group__name']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Contenu'
    
    def has_media(self, obj):
        return bool(obj.image or obj.video or obj.audio or obj.file)
    has_media.boolean = True
    has_media.short_description = 'Média'

