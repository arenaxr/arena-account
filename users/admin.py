from django.contrib import admin

from .models import ArenaUser, Device, Scene


# class ArenaUserAdmin(admin.ModelAdmin):
#     autocomplete_fields = ['owners', 'editors']


class SceneAdmin(admin.ModelAdmin):
    autocomplete_fields = ['editors']


#admin.site.register(ArenaUser, ArenaUserAdmin)
admin.site.register(ArenaUser)
admin.site.register(Scene, SceneAdmin)
admin.site.register(Device)
