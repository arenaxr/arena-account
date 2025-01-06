from django.contrib import admin

from .models import Device, Namespace, Scene


class NamespaceAdmin(admin.ModelAdmin):
    list_display = ["name"]
    autocomplete_fields = ["owners", "editors", "viewers"]


class SceneAdmin(admin.ModelAdmin):
    list_display = ["name", "public_read", "public_write", "anonymous_users", "video_conference", "users"]
    autocomplete_fields = ["owners", "editors", "viewers"]


admin.site.register(Namespace, NamespaceAdmin)
admin.site.register(Scene, SceneAdmin)
admin.site.register(Device)
