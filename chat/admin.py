from django.contrib import admin
from .models import Conversation, Message


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'participants_list', 'created_at', 'updated_at']
    filter_horizontal = ['participants']
    
    def participants_list(self, obj):
        return ", ".join([p.username for p in obj.participants.all()])
    participants_list.short_description = 'Participants'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'conversation', 'sender', 'content_preview', 'created_at', 'read_at']
    list_filter = ['created_at', 'read_at']
    search_fields = ['content', 'sender__username']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Contenu'

