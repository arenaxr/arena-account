import json
import os

import requests
from django.contrib.auth.models import User

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


def get_rest_host():
    verify = True
    if os.environ["HOSTNAME"] == 'localhost':
        host = "host.docker.internal"
        verify = False
    else:
        host = os.environ["HOSTNAME"]
    return verify, host


def use_filestore_auth(user: User):
    verify, host = get_rest_host()
    try:
        r_userlogin = requests.post(f'https://{host}/storemng/api/login', data=json.dumps(
            {'username': user.username, 'password': user.password}), verify=verify)
        r_userlogin.raise_for_status()
    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as err:
        print("{0}: ".format(err))
        return None
    return r_userlogin.text


def add_filestore_auth(user: User):
    verify, host = get_rest_host()
    # get auth for setting new user
    try:
        r_admin = requests.post(f'https://{host}/storemng/api/login',
                                data=json.dumps({'username': os.environ["STORE_ADMIN_USERNAME"],
                                                 'password': os.environ["STORE_ADMIN_PASSWORD"]}), verify=verify)
        r_admin.raise_for_status()
    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as err:
        print("{0}: ".format(err))
        return None
    admin_token = r_admin.text

    # set new user options
    ADDUSER_OPTS["data"]["username"] = user.username
    ADDUSER_OPTS["data"]["password"] = user.password
    ADDUSER_OPTS["data"]["perm"]["admin"] = user.is_superuser
    if user.is_superuser:
        ADDUSER_OPTS["data"]["scope"] = "."
    else:
        ADDUSER_OPTS["data"]["scope"] = f"./users/{user.username}"

    # add new user to filestore db
    try:
        r_useradd = requests.post(f'https://{host}/storemng/api/users',
                                  data=json.dumps(ADDUSER_OPTS), headers={"X-Auth": admin_token}, verify=verify)
        r_useradd.raise_for_status()
    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as err:
        print("{0}: ".format(err))
        return None

    return use_filestore_auth(user)


def delete_filestore_auth(user: User):
    verify, host = get_rest_host()
    # get auth for removing user
    try:
        r_admin = requests.post(f'https://{host}/storemng/api/login',
                                data=json.dumps({'username': os.environ["STORE_ADMIN_USERNAME"],
                                                 'password': os.environ["STORE_ADMIN_PASSWORD"]}), verify=verify)
        r_admin.raise_for_status()
    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as err:
        print("{0}: ".format(err))
        return False
    admin_token = r_admin.text

    try:
        r_users = requests.get(
            f'https://{host}/storemng/api/users', headers={"X-Auth": admin_token}, verify=verify)
        r_users.raise_for_status()
    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as err:
        print("{0}: ".format(err))
        return False
    print(r_users.text)
    fsusers = r_users.json()
    # find user in list
    for fsuser in fsusers:
        if fsuser['username']:
            del_userid = fsuser.id
        else:
            return False
    # delete user from filestore db
    try:
        r_userdel = requests.delete(f'https://{host}/storemng/api/users',
                                    data=json.dumps({"raw": del_userid}), headers={"X-Auth": admin_token}, verify=verify)
        r_userdel.raise_for_status()
    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as err:
        print("{0}: ".format(err))
        return False

    return True
