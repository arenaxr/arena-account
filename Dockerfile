FROM python:3

WORKDIR /usr/src/app

COPY . .

RUN mkdir static || true

COPY ./docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh

RUN pip install --no-cache-dir -r requirements.txt

RUN python -c "import django; django.setup(); \
   from django.contrib.auth.management.commands.createsuperuser import get_user_model; \
   get_user_model()._default_manager.db_manager('$DJANGO_DB_NAME').create_superuser( \
   username='$ACCOUNT_ADMIN_NAME', \
   email='$ACCOUNT_ADMIN_EMAIL', \
   password='$ACCOUNT_ADMIN_PASSWORD')"

EXPOSE 8000

ENTRYPOINT ["/docker-entrypoint.sh"]
