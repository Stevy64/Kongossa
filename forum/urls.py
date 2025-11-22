from django.urls import path
from . import views

app_name = 'forum'

urlpatterns = [
    path('', views.feed, name='feed'),
    path('feed/page/', views.feed, name='feed_page'),  # Pour infinite scroll
    path('topics/', views.topics_list, name='topics_list'),
    path('topics/create/', views.create_topic, name='create_topic'),
    path('topic/<slug:slug>/', views.topic_detail, name='topic_detail'),
    path('topic/<slug:slug>/manage/', views.manage_topic, name='manage_topic'),
    path('topic/<slug:slug>/update/', views.update_topic, name='update_topic'),
    path('topic/<slug:slug>/archive/', views.archive_topic, name='archive_topic'),
    path('topic/<slug:slug>/delete/', views.delete_topic, name='delete_topic'),
    path('topic/<slug:slug>/subscribe/', views.toggle_topic_subscribe, name='toggle_topic_subscribe'),
    path('post/create/', views.create_post, name='create_post'),
    path('post/<int:post_id>/', views.post_detail, name='post_detail'),
    path('post/<int:post_id>/like/', views.toggle_like, name='toggle_like'),
    path('post/<int:post_id>/comment/', views.add_comment, name='add_comment'),
    path('groups/', views.groups_list, name='groups_list'),
    path('topic/<slug:topic_slug>/groups/', views.groups_list, name='topic_groups_list'),
    path('group/<int:group_id>/', views.group_feed, name='group_feed'),
    path('group/<int:group_id>/messages/', views.group_detail, name='group_detail'),
    path('group/<int:group_id>/manage/', views.manage_group, name='manage_group'),
    path('group/<int:group_id>/update/', views.update_group, name='update_group'),
    path('group/<int:group_id>/delete/', views.delete_group, name='delete_group'),
    path('group/<int:group_id>/request-access/', views.request_group_access, name='request_group_access'),
    path('group/<int:group_id>/subscribe/', views.toggle_group_subscribe, name='toggle_group_subscribe'),
    path('group-request/<int:request_id>/approve/', views.approve_group_request, name='approve_group_request'),
    path('group-request/<int:request_id>/reject/', views.reject_group_request, name='reject_group_request'),
    path('group-request/<int:request_id>/cancel/', views.cancel_group_request, name='cancel_group_request'),
    path('group/<int:group_id>/leave/', views.leave_group, name='leave_group'),
    path('group/<int:group_id>/message/', views.send_group_message, name='send_group_message'),
    path('topic/<slug:topic_slug>/group/create/', views.create_group, name='create_group'),
]

