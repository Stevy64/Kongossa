from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.chat_list, name='list'),
    path('contacts/', views.contacts_list, name='contacts'),
    path('<int:conversation_id>/', views.chat_detail, name='detail'),
    path('<int:conversation_id>/send/', views.send_message, name='send_message'),
    path('start/<int:user_id>/', views.start_conversation, name='start'),
]

