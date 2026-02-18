from django.urls import path, re_path

from . import views

app_name = "users"
urlpatterns = [
    # views/pages
    path("", views.index, name="index"),
    path("login", views.login_request, name="login"),
    path("logout", views.logout_request, name="logout"),
    path(
        "accounts/3rdparty/signup/",
        views.SocialSignupView.as_view(),
        name="socialaccount_signup",
    ),
    path("profile", views.user_profile, name="user_profile"),
    path("login_callback", views.login_callback, name="login_callback"),
    re_path(r"^profile/namespaces/(?P<pk>[^\/]+)$", views.namespace_perm_detail),
    re_path(r"^profile/scenes/(?P<pk>[^\/]+\/[^\/]+)$", views.scene_perm_detail),
    re_path(r"^profile/devices/(?P<pk>[^\/]+\/[^\/]+)$", views.device_perm_detail),
    # view form submission processing
    path("profile_update_staff", views.profile_update_staff, name="profile_update_staff"),
    path("profile_update_namespace", views.profile_update_namespace, name="profile_update_namespace"),
    path("profile_update_scene", views.profile_update_scene, name="profile_update_scene"),
    path("profile_update_device", views.profile_update_device, name="profile_update_device"),
    # autocomplete
    path(
        "user-autocomplete/",
        views.UserAutocomplete.as_view(),
        name="user-autocomplete",
    ),
    # api docs: served at /doc by Ninja
    # apis: served from users/api.py by Ninja
]
