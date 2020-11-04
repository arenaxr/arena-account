from django.urls import path

from . import views

urlpatterns = [
    #path('', views.index, name='index'),
    path("", views.homepage, name="homepage"),
    path("register", views.register_request, name="register")]
