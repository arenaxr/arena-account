"""arena_account URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from allauth.socialaccount import views as signup_views
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

urlpatterns = [
    path('user/', include('users.urls')),
    path('user/admin/', admin.site.urls),
    #path('user/accounts/', include('django.contrib.auth.urls')),
    path('user/password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='users/password/password_reset_done.html'), name='password_reset_done'),
    path('user/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name="users/password/password_reset_confirm.html"), name='password_reset_confirm'),
    path('user/reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='users/password/password_reset_complete.html'), name='password_reset_complete'),
    path('user/accounts/', include('allauth.urls')),
    path("user/accounts/social/signup", signup_views.SignupView.as_view(
        template_name='users/social_signup.html'), name='social_signup'),
]
