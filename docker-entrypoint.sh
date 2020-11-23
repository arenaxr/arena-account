#!/bin/bash

export DJANGO_SETTINGS_MODULE=arena_account.settings
python manage.py createsuperuser --noinput || python -c "\
import django; django.setup(); \
import os; \
USER = os.getenv('DJANGO_SUPERUSER_USERNAME'); \
PASS = os.getenv('DJANGO_SUPERUSER_PASSWORD'); \
from django.contrib.auth.models import User; \
u = User.objects.get(username=USER); \
u.set_password(PASS);\
u.save();"
  
python manage.py collectstatic --noinput
python manage.py runserver 0.0.0.0:8000
