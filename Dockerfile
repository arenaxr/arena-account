FROM python:3

WORKDIR /usr/src/app

COPY . .

RUN mkdir static || true

COPY ./docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh

RUN pip install --no-cache-dir -r requirements.txt

RUN python manage.py makemigrations --noinput
RUN python manage.py migrate 
RUN python manage.py collectstatic --noinput

RUN python manage.py createsuperuser --username $DJANGO_SUPERUSER_USERNAME --noinput

EXPOSE 8000

ENTRYPOINT ["/docker-entrypoint.sh"]
