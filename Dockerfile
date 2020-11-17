FROM python:3

WORKDIR /usr/src/app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

RUN python manage.py makemigrations --noinput
RUN python manage.py migrate
RUN python manage.py collectstatic

CMD python manage.py runserver 0.0.0.0:8000
