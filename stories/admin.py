from django.contrib import admin
from .models import Story, StoryView


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'created_at', 'expires_at', 'is_expired']
    list_filter = ['created_at', 'expires_at']
    readonly_fields = ['expires_at']


@admin.register(StoryView)
class StoryViewAdmin(admin.ModelAdmin):
    list_display = ['story', 'user', 'viewed_at']
    list_filter = ['viewed_at']

