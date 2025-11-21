from django.urls import path
from . import views

app_name = 'stories'

urlpatterns = [
    path('', views.stories_feed, name='feed'),
    path('viewer/<int:story_id>/', views.story_viewer, name='viewer'),
    path('create/', views.create_story, name='create'),
    path('create-form/', views.create_story_form, name='create_form'),
]

