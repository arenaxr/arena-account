from django.contrib import admin

from .models import Scene


class SceneAdmin(admin.ModelAdmin):
    autocomplete_fields = ['editors']


admin.site.register(Scene, SceneAdmin)
