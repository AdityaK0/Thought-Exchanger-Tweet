from django.urls import path,include
from .views import *
from django.contrib.auth import views as auth_views
from .forms import CustomResetForm

urlpatterns = [
    
    path('',home,name='home_page'),
    path('register/',register,name='register'),
    path('login/',login_user,name='login_user'),
    path('logout/',logout_user,name='logout_user'),
    path('reset_password/', auth_views.PasswordResetView.as_view(form_class=CustomResetForm), name='reset_password'),
    path('reset_password_done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset_password_complete/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    
]
