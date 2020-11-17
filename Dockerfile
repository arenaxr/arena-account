FROM python:3

WORKDIR /usr/src/app

COPY . .

COPY ./docker-entrypoint.sh /

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

ENTRYPOINT ["/docker-entrypoint.sh"]
