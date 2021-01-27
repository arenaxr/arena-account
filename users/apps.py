import os

from django.apps import AppConfig
# from django.db.models.signals import post_migrate


# def post_migration_callback(sender, **kwargs):
#     from . import startup
#     startup.setup_socialapps()


class UsersConfig(AppConfig):
    name = 'users'

    # def ready(self):
    #     post_migrate.connect(post_migration_callback, sender=self)
