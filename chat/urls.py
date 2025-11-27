from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.chat_list, name='list'),
    path('contacts/', views.contacts_list, name='contacts'),
    path('unread-count/', views.get_unread_count, name='unread_count'),
    path('<int:conversation_id>/', views.chat_detail, name='detail'),
    path('<int:conversation_id>/send/', views.send_message, name='send_message'),
    path('<int:conversation_id>/messages/', views.load_messages, name='load_messages'),
    path('<int:conversation_id>/new-messages/', views.get_new_messages, name='get_new_messages'),
    path('start/<int:user_id>/', views.start_conversation, name='start'),
    path('messages/<int:message_id>/read/', views.mark_message_read, name='mark_message_read'),
]

