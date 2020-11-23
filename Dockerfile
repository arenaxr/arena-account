FROM python:3

WORKDIR /usr/src/app

COPY . .

RUN mkdir static || true
RUN mkdir db || true

COPY ./docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

ENTRYPOINT ["/docker-entrypoint.sh"]
