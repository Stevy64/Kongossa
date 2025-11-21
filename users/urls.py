from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('passwordless/', views.passwordless_login, name='passwordless_login'),
    path('verify/<str:token>/', views.verify_token, name='verify_token'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/<str:username>/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('follow/<str:username>/', views.toggle_follow, name='toggle_follow'),
    path('friend-request/<str:username>/send/', views.send_friend_request, name='send_friend_request'),
    path('friend-request/<int:request_id>/accept/', views.accept_friend_request, name='accept_friend_request'),
    path('friend-request/<int:request_id>/reject/', views.reject_friend_request, name='reject_friend_request'),
    path('friend-request/<str:username>/cancel/', views.cancel_friend_request, name='cancel_friend_request'),
]

