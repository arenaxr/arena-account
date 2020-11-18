#!/bin/bash

#create admin user
export DJANGO_SETTINGS_MODULE=arena_account.settings
python -c "import django; django.setup(); \
   from django.contrib.auth.management.commands.createsuperuser import get_user_model; \
   get_user_model()._default_manager.db_manager('$DJANGO_DB_NAME').create_superuser( \
   username='$ACCOUNT_ADMIN_NAME', \
   email='$ACCOUNT_ADMIN_EMAIL', \
   password='$ACCOUNT_ADMIN_PASSWORD')"
   
python manage.py makemigrations --noinput
python manage.py migrate 
python manage.py collectstatic --noinput

 python manage.py runserver 0.0.0.0:8000
