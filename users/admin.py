from django.contrib import admin

from .models import Device, Namespace, Scene


@admin.register(Namespace)
class NamespaceAdmin(admin.ModelAdmin):
    list_display = ["name", "is_default"]
    list_filter = ["editors", "viewers"]
    search_fields = ["name"]
    autocomplete_fields = ["editors", "viewers"]


@admin.register(Scene)
class SceneAdmin(admin.ModelAdmin):
    list_display = ["name", "is_default", "public_read", "public_write", "anonymous_users", "video_conference", "users"]
    list_filter = ["public_read", "public_write", "anonymous_users", "video_conference", "users", "editors", "viewers"]
    search_fields = ["name"]
    autocomplete_fields = ["editors", "viewers"]


admin.site.register(Device)
