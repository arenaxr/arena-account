"""
WSGI config for arena_account project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/wsgi/
"""

import datetime
import os

from django.core.wsgi import get_wsgi_application
from users.models import Scene

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'arena_account.settings')

##############
# TODO: add unknown scenes to scene database
# TODO: get key for persist
# TODO: request all scenes from persist
# TODO: add only-missing scenes to scene database

now = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
s = Scene(
    name=f'example-{now}',
    summary='An example scene.',
)
print(f'Adding scene example-{now}')
s.save()
#################

application = get_wsgi_application()
