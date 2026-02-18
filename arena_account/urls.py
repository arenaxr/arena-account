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
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from users.api import api

urlpatterns = [
    # configure user api version based endpoints
    path("user/", include((api.urls, "users_api"), namespace="v1")),
    path("user/v2/", include((api.urls, "users_api"), namespace="v2")),
    path("user/", include("users.urls", namespace="v1")),
    path("user/v2/", include("users.urls", namespace="v2")),

    # include admin paths
    path("user/admin/", admin.site.urls),
    path("user/accounts/", include("allauth.urls")),
]
