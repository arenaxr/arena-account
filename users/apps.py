import os

from django.apps import AppConfig

import users.startup as startup


class UsersConfig(AppConfig):
    name = 'users'

    def ready(self):
        # main process only
        if os.environ.get('RUN_MAIN', None) == 'true':
            startup.migrate_persist()
