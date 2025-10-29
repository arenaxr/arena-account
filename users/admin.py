from django.contrib import admin

from .models import ArenaObject, Device, Namespace, Scene


@admin.register(Namespace)
class NamespaceAdmin(admin.ModelAdmin):
    list_display = ["name", "is_default"]
    list_filter = ["editors", "viewers"]
    search_fields = ["name"]
    autocomplete_fields = ["editors", "viewers"]


@admin.register(Scene)
class SceneAdmin(admin.ModelAdmin):
    list_display = ["name", "is_default", "public_read", "public_write", "anonymous_users", "video_conference", "users", "creation_date"]
    list_filter = ["creation_date", "public_read", "public_write", "anonymous_users", "video_conference", "users", "editors", "viewers"]
    search_fields = ["name"]
    autocomplete_fields = ["editors", "viewers"]

@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ["name", "creation_date"]
    list_filter = ["creation_date"]
    search_fields = ["name", "summary"]

@admin.register(ArenaObject)
class ArenaObjectModelAdmin(admin.ModelAdmin):

    def get_queryset(self, request):
        # return super().get_queryset(request).using('persist').order_by()
        # qs = ArenaObject.objects.using('persist')
        qs = super().get_queryset(request).using('persist').order_by()

        # if self.q:
        #     qs = qs.filter(username__istartswith=self.q)

        return qs

    def save_model(self, request, obj, form, change):
        # Custom save logic here
        super().save_model(request, obj, form, change).using('persist')
