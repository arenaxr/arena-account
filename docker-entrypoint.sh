#!/bin/bash

python manage.py makemigrations --noinput
python manage.py migrate   
python manage.py collectstatic --noinput

export DJANGO_SETTINGS_MODULE=arena_account.settings
bash -c 'python manage.py createsuperuser --noinput' || true
# if above command fails because user exists, change user password
python -c "\
import django; django.setup(); \
import os; \
USER = os.getenv('DJANGO_SUPERUSER_USERNAME'); \
PASS = os.getenv('DJANGO_SUPERUSER_PASSWORD'); \
from django.contrib.auth.models import User; \
u = User.objects.get(username=USER); \
u.set_password(PASS);\
u.save();" || true
  
python manage.py runserver 0.0.0.0:8000
