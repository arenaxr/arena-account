import json
import os

import requests

ADDUSER_OPTS = {
    "what": "user",
    "which": [],
    "data": {
        "locale": "en",
        "lockPassword": True,
        "viewMode": "mosaic",
        "perm": {
            "admin": False,
            "execute": True,
            "create": True,
            "rename": True,
            "modify": True,
            "delete": True,
            "share": True,
            "download": True
        },
        "commands": [],
        "sorting": {
            "by": "name",
            "asc": False
        },
        "rules": [],
        "hideDotfiles": False,
        "singleClick": False,
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
    admin_token = r_admin.text

    try:
        r_users = requests.get(
            f'https://{host}/storemng/api/users', headers={"X-Auth": admin_token}, verify=verify)
    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as err:
        print("{0}: ".format(err))
        return None
    print(r_users.text)
    users = r_users.json()
    # User doesn't exist, create first
    if len([user for user in users if user['username'] == django_user]) == 0:
        ADDUSER_OPTS["data"]["username"] = django_user
        ADDUSER_OPTS["data"]["password"] = django_user
        try:
            r_adduser = requests.post(f'https://{host}/storemng/api/users',
                                      data=json.dumps(ADDUSER_OPTS), headers={"X-Auth": admin_token}, verify=verify)
        except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as err:
            print("{0}: ".format(err))
            return None
        print(r_adduser.text)

    try:
        r_userlogin = requests.post(f'https://{host}/storemng/api/login', data=json.dumps(
            {'username': django_user, 'password': django_user}), verify=verify)
    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as err:
        print("{0}: ".format(err))
        return None
    print(r_userlogin.text)
    return r_userlogin.text
