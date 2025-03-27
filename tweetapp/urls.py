from django.urls import path,include
from .views import *
from django.contrib.auth import views as auth_view
appname="tweetapp"
urlpatterns = [

    path('',home,name='home'),
    path('profile_list/',profile_list,name='profile_list'),
    path('profile/<int:pk>',profile,name='prof'),
    path('add_tweet/',add_tweet,name='add_tweet'),
    path('add_likes/<int:id>',add_likes,name="add_likes"),
    path('add_comments/<int:id>', add_comments, name="add_comments"),
    path('follow_unfollow/<int:id>',follow_unfollow,name="follow_unfollow"),
    path('search_user/',search_user,name="search_user"),
    path('suggest-users/', suggest_users, name='suggest_users'),
    path('savepost/<int:id>',add_Save_Post,name="add_post"),
    path('saved_posts/',saved_posts,name="saved_posts"),
    path('delete_tweet/<int:pk>/',delete_tweet,name="delete_tweet"),
    path('update_profile/<str:username>/',update_profile,name="update_profile"),
    path('login/',signin,name="signin"),
    path('register/',register,name="signup"),
    path('logout/',logout_user,name="logout"),
    path('notifications/',user_notifications,name="notification_list"),
    path('mark_as_read/<int:id>/',mark_as_read_notification,name="mark_as_read_notification"),
    path('password_reset/',auth_view.PasswordResetView.as_view(),name="password_reset"),
    path('password_reset_done/',auth_view.PasswordResetDoneView.as_view(),name="password_reset_done"),
    path('password_reset_confirm/<uidb64>/<token>',auth_view.PasswordResetConfirmView.as_view(),name="password_reset_confirm"),
    path('password_reset_complete/',auth_view.PasswordResetCompleteView.as_view(),name="password_reset_complete"),
    
     
    
]
