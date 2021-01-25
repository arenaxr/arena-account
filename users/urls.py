import os

from django.urls import path, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from . import startup, views

schema_view = get_schema_view(
    openapi.Info(
        title="ARENA Users API",
        default_version='v1',
        description="ARENA Users Django site endpoints.",
        # TODO: terms_of_service=f"/eula",
        contact=openapi.Contact(email=os.environ['EMAIL']),
        license=openapi.License(
            name="BSD 3-Clause License",
            url="https://opensource.org/licenses/BSD-3-Clause"),
    ),
    # TODO: review permissions
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    re_path(r'^doc(?P<format>\.json|\.yaml)$',
            schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('doc/', schema_view.with_ui('swagger', cache_timeout=0),
         name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0),
         name='schema-redoc'),
    path("", views.index, name="index"),
    # path("register", views.register_request, name="register"),
    path("login", views.login_request, name="login"),
    path("logout", views.logout_request, name="logout"),
    # path("password_reset", views.password_reset_request, name="password_reset"),
    path('accounts/social/signup/', views.SocialSignupView.as_view(),
         name='socialaccount_signup'),
    path("profile", views.user_profile, name="user_profile"),
    path("login_callback", views.login_callback, name="login_callback"),
    path('mqtt_auth', views.mqtt_token, name="mqtt_token"),
    path('user_state', views.user_state, name="user_state"),
    path('profile_update_staff', views.profile_update_staff,
         name="profile_update_staff"),
    path('profile_new_scene', views.profile_new_scene,
         name="profile_new_scene"),
    path('profile_update_scene', views.profile_update_scene,
         name="profile_update_scene"),
    path('new_scene', views.new_scene, name="new_scene"),
    path('my_scenes', views.my_scenes, name="my_scenes"),
]

startup.setup_socialapps()
