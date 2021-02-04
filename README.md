# arena-account
Django project user account management for the ARENA.

**Dependencies**: `python3`, `pip3`, `virtualenv` (and `requirements.txt`; check if path in `Makefile` is correct)

**Setup:**
1. [Create Google Auth App](https://django-allauth.readthedocs.io/en/latest/providers.html#google)
2. Create an environment file, [.env](.env), for testing on localhost using your Google auth app "Client id" and "Secret key".
```env
HOSTNAME=localhost
EMAIL=nouser@nomail.com
GAUTH_CLIENTID=Google_OAuth_Web_Client_ID
GAUTH_CLIENTSECRET=Google_OAuth_Web_Client_Secret
MQTT_TOKEN_PRIVKEY=/path/to/your/test/key/file.pem
```
3. Create db: ```make migrate```
4. Create admin user: ```python3 manage.py createsuperuser --email admin@example.com --username admin```

**Execute:**
- ```make run```

**UIs:**
- Admin: [http://localhost:8000/user/admin](http://localhost:8000/user/admin)
- Main Page: [http://localhost:8000/user](http://localhost:8000/user)
