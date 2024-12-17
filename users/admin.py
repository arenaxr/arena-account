from django.contrib import admin

from .models import Device, Scene


class SceneAdmin(admin.ModelAdmin):
    list_display = ["name", "public_read", "public_write", "anonymous_users", "video_conference", "users"]
    autocomplete_fields = ["editors"]


admin.site.register(Scene, SceneAdmin)
admin.site.register(Device)
