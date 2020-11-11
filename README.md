# arena-account
Django project user account management for the ARENA.

**Dependencies**: `python3`, `pip3`, `virtualenv` (and `requirements.txt`; check if path in `Makefile` is correct)

**Setup:**
- Create db: ```make migrate```
- Create admin user: ```python manage.py createsuperuser --email admin@example.com --username admin```
- [Create GitHub Auth App](https://django-allauth.readthedocs.io/en/latest/providers.html#github)
- [Create Google Auth App](https://django-allauth.readthedocs.io/en/latest/providers.html#google)
- Add Google and GitHub social apps and their "Client id" and "Secret key": http://localhost:8000/admin/socialaccount/socialapp/

**Execute:**
- ```make run```

**UIs:**
- Admin: http://localhost:8000/admin/
- Visualize: http://localhost:8000/
