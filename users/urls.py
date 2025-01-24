import os

from django.urls import path, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from . import views

schema_view = get_schema_view(
    openapi.Info(
        title="ARENA Users API",
        default_version="v1",
        description="ARENA Users Django site endpoints.",
        terms_of_service=f"https://{os.environ['HOSTNAME']}/terms.html",
        contact=openapi.Contact(email=os.environ["EMAIL"]),
        license=openapi.License(
            name="BSD 3-Clause License",
            url="https://opensource.org/licenses/BSD-3-Clause",
        ),
    ),
    url=f"https://{os.environ['HOSTNAME']}",
    public=True,
    permission_classes=(permissions.AllowAny,),
)

app_name = "users"
urlpatterns = [
    # pages
    path("", views.index, name="index"),
    path("health", views.health_state, name="health"),
    path("login", views.login_request, name="login"),
    path("logout", views.logout_request, name="logout"),
    path(
        "accounts/social/signup/",
        views.SocialSignupView.as_view(),
        name="socialaccount_signup",
    ),
    path("profile", views.user_profile, name="user_profile"),
    path("login_callback", views.login_callback, name="login_callback"),
    re_path(r"^profile/namespaces/(?P<pk>[^\/]+)$", views.namespace_perm_detail),
    re_path(r"^profile/scenes/(?P<pk>[^\/]+\/[^\/]+)$", views.scene_perm_detail),
    re_path(r"^profile/devices/(?P<pk>[^\/]+\/[^\/]+)$", views.device_perm_detail),
    # endpoints
    path("mqtt_auth", views.arena_token, name="arena_token"),
    path("user_state", views.user_state, name="user_state"),
    path("profile_update_staff", views.profile_update_staff, name="profile_update_staff"),
    path("profile_update_namespace", views.profile_update_namespace, name="profile_update_namespace"),
    path("profile_update_scene", views.profile_update_scene, name="profile_update_scene"),
    path("profile_update_device", views.profile_update_device, name="profile_update_device"),
    path("my_scenes", views.list_my_scenes, name="my_scenes"),
    path("my_namespaces", views.list_my_namespaces, name="my_namespaces"),
    # namespace/scenename
    re_path(r"^scenes/(?P<pk>[^\/]+\/[^\/]+)$", views.scene_detail),
    # docs
    re_path(
        r"^doc(?P<format>\.json|\.yaml)$",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),
    path(
        "doc/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    # autocomplete
    re_path(
        r"^user-autocomplete/$",
        views.UserAutocomplete.as_view(),
        name="user-autocomplete",
    ),
    # filebrowser auth
    path("storelogin", views.storelogin, name="storelogin"),
]
