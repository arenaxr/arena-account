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
from django.urls import include, path
from users.api import apis

urlpatterns = [
    # configure user api version based django views
    path("user/", include(("users.urls", "users"), namespace="v1")),
    path("user/v2/", include(("users.urls", "users"), namespace="v2")),
    # include admin paths
    path("user/admin/", admin.site.urls),
    path("user/accounts/", include("allauth.urls")),
]

# configure user api version based ninja apis
for version, api in apis.items():
    if version == "v1":
        urlpatterns.insert(0, path("user/", api.urls))  # v1 default
    else:
        urlpatterns.insert(1, path(f"user/{version}/", api.urls))
