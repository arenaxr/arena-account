import os

from django.apps import AppConfig

from . import startup


class UsersConfig(AppConfig):
    name = 'users'

    def ready(self):
        print(f"process: {os.getpid()}")
        startup.setup_socialapps()
