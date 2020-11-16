from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    #path("register", views.register_request, name="register"),
    path("register", views.register, name="register"),
    path("login", views.login_request, name="login"),
    path("logout", views.logout_request, name="logout"),
    path("password_reset", views.password_reset_request, name="password_reset"),
    path("profile/<username>", views.user_profile, name="user_profile"),
    path("login_callback", views.login_callback, name="login_callback"),
    path('api/token/mqtt/scene', views.mqtt_token_scene, name = "mqtt_token_scene"),
]
