from django.urls import path

from . import startup, views

urlpatterns = [
    path("", views.index, name="index"),
    # path("register", views.register_request, name="register"),
    path("login", views.login_request, name="login"),
    path("logout", views.logout_request, name="logout"),
    # path("password_reset", views.password_reset_request, name="password_reset"),
    path("profile", views.user_profile, name="user_profile"),
    path("login_callback", views.login_callback, name="login_callback"),
    path('mqtt_auth', views.mqtt_token, name="mqtt_token"),
    path('user_state', views.user_state, name="user_state"),
    path('update_staff', views.update_staff, name="update_staff"),
    path('new_scene', views.new_scene, name="new_scene"),
]

startup.migrate_persist()
