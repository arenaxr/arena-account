# arena-account
Django project user account management for the ARENA.

**Dependencies**: `python3`, `pip3`, `virtualenv` (and `requirements.txt`; check if path in `Makefile` is correct)

**Setup:**
- Create db: ```make migrate```
- Create admin user: ```python3 manage.py createsuperuser --email admin@example.com --username admin```
- [Create Google Auth App](https://django-allauth.readthedocs.io/en/latest/providers.html#google)
- Create an environment file, [.env](.env), for testing on localhost using your Google auth app "Client id" and "Secret key".
```bash
HOSTNAME=localhost
EMAIL=nouser@nomail.com
GAUTH_CLIENTID=Google_OAuth_Web_Client_ID
GAUTH_CLIENTSECRET=Google_OAuth_Web_Client_Secret
```

**Execute:**
- ```make run```

**UIs:**
- Admin: [http://localhost:8000/user/admin](ttp://localhost:8000/user/admin)
- Visualize: [http://localhost:8000/user](http://localhost:8000/user)
