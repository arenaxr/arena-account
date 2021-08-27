import json
import os

import requests

ADDUSER_OPTS = {
    "what": "user",
    "which": [],
    "data": {
        "scope": ".",
        "locale": "en",
        "viewMode": "mosaic",
        "singleClick": False,
        "sorting": {
            "by": "",
            "asc": False
        },
        "perm": {
            "admin": False,
            "execute": False,
            "create": True,
            "rename": False,
            "modify": True,
            "delete": True,
            "share": True,
            "download": True
        },
        "commands": [],
        "hideDotfiles": False,
        "rules": [],
        "lockPassword": True,
        "id": 0,
        "passsword": "",
    }
}


def get_filestore_auth(django_user):
    verify = True
    if os.environ["HOSTNAME"] == 'localhost':
        host = "host.docker.internal"
        verify = False
    else:
        host = os.environ["HOSTNAME"]

    try:
        r_admin = requests.post(f'https://{host}/storemng/api/login',
                                data=json.dumps({'username': os.environ["STORE_ADMIN_USERNAME"],
                                                 'password': os.environ["STORE_ADMIN_PASSWORD"]}), verify=verify)
    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as err:
        print("{0}: ".format(err))
        return None
    print(r_admin.text)
    admin_cookie = r_admin.text

    try:
        headers = {"Cookie": f"auth={admin_cookie}", "X-Auth": admin_cookie}
        r_users = requests.get(
            f'https://{host}/storemng/api/users', cookies={'auth': admin_cookie}, headers=headers, verify=verify)
    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as err:
        print("{0}: ".format(err))
        return None
    print(r_users.text)
    users = r_users.json()
    # User doesn't exist, create first
    if len([user for user in users if user['username'] == django_user]) == 0:
        ADDUSER_OPTS["data"]["username"] = django_user
        ADDUSER_OPTS["data"]["password"] = ''
        try:
            headers = {"Cookie": f"auth={admin_cookie}",
                       "X-Auth": admin_cookie}
            r_adduser = requests.post(f'https://{host}/storemng/api/users',
                                      data=json.dumps(ADDUSER_OPTS), cookies={'auth': admin_cookie}, headers=headers, verify=verify)
        except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as err:
            print("{0}: ".format(err))
            return None
        print(r_adduser.text)

    try:
        r_userlogin = requests.post(f'https://{host}/storemng/api/login', data=json.dumps(
            {'username': django_user, 'password': ''}), verify=verify)
    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as err:
        print("{0}: ".format(err))
        return None
    # request.set_cookie('auth', r_userlogin.text)
    print(r_userlogin.text)
    return r_userlogin.text
