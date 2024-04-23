import json
import os

import jwt
import requests
from django.contrib.auth.models import User

from .utils import get_rest_host


def get_user_scope(user: User):
    return f"./users/{user.username}"


def get_admin_login():
    admin_login = {"username": os.environ["STORE_ADMIN_USERNAME"],
                   "password": os.environ["STORE_ADMIN_PASSWORD"]}
    return admin_login


def get_user_login(user: User):
    if user.username == os.environ["STORE_ADMIN_USERNAME"]:
        password = os.environ["STORE_ADMIN_PASSWORD"]
    else:
        password = user.password
    user_login = {"username": user.username,
                  "password": password}
    return user_login


def use_filestore_auth(user: User):
    if not user.is_authenticated:
        return None
    verify, host = get_rest_host()
    user_login = get_user_login(user)
    return get_filestore_token(user_login, host, verify)


def get_filestore_token(user_login, host, verify):
    try:
        r_userlogin = requests.get(f"https://{host}/storemng/api/login",
                                   data=json.dumps(user_login), verify=verify)
        r_userlogin.raise_for_status()
    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as err:
        print("{0}: ".format(err))
        return None
    return r_userlogin.text


def add_filestore_auth(user: User):
    if not user.is_authenticated:
        return None
    verify, host = get_rest_host()
    # get auth for setting new user
    admin_login = get_admin_login()
    admin_token = get_filestore_token(admin_login, host, verify)
    if not admin_token:
        return False
    # get user defaults from global settings
    try:
        r_gset = requests.get(f"https://{host}/storemng/api/settings",
                              headers={"X-Auth": admin_token}, verify=verify)
        r_gset.raise_for_status()
    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as err:
        print("{0}: ".format(err))
        return False
    settings = r_gset.json()
    # set new user options
    fs_user = {
        "what": "user",
        "which": [],
        "data": settings["defaults"],
    }
    fs_user["data"]["username"] = user.username
    fs_user["data"]["password"] = user.password
    fs_user["data"]["lockPassword"] = True
    fs_user["data"]["perm"]["admin"] = user.is_superuser
    # setting scope in users POST will generate user dir
    fs_user["data"]["scope"] = get_user_scope(user)

    # add new user to filestore db
    try:
        r_useradd = requests.post(f"https://{host}/storemng/api/users",
                                  data=json.dumps(fs_user), headers={"X-Auth": admin_token}, verify=verify)
        r_useradd.raise_for_status()
    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as err:
        print("{0}: ".format(err))
        return None

    if user.is_staff:  # admin and staff get root scope
        set_filestore_scope(user)

    return use_filestore_auth(user)


def set_filestore_scope(user: User):
    verify, host = get_rest_host()
    # get auth for setting new user
    admin_login = get_admin_login()
    admin_token = get_filestore_token(admin_login, host, verify)
    if not admin_token:
        return False
    # find user
    fs_user_token = use_filestore_auth(user)
    # TODO: dev1 jwt.exceptions.DecodeError: Invalid token type. Token must be a <class 'bytes'>
    payload = jwt.decode(fs_user_token, options={"verify_signature": False})
    try:
        r_user = requests.get(f"https://{host}/storemng/api/users/{payload['user']['id']}",
                              headers={"X-Auth": admin_token}, verify=verify)
        r_user.raise_for_status()
    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as err:
        print("{0}: ".format(err))
        return False
    edit_user = r_user.json()
    if user.is_staff:  # admin and staff get root scope
        scope = "."
    else:
        scope = get_user_scope(user)
    if edit_user["scope"] != scope:
        edit_user["scope"] = scope
        fs_user = {
            "what": "user",
            "which": ["all"],
            "data": edit_user,
        }
        try:
            r_useradd = requests.put(f"https://{host}/storemng/api/users/{edit_user['id']}",
                                     data=json.dumps(fs_user), headers={"X-Auth": admin_token}, verify=verify)
            r_useradd.raise_for_status()
        except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as err:
            print("{0}: ".format(err))
            return False

    return True


def delete_filestore_user(user: User):
    if not user.is_authenticated:
        return False
    if user.username == os.environ["STORE_ADMIN_USERNAME"]:
        return False  # root admin not allowed delete
    verify, host = get_rest_host()
    # get auth for removing user
    admin_login = get_admin_login()
    admin_token = get_filestore_token(admin_login, host, verify)
    if not admin_token:
        return False
    # find user
    fs_user_token = use_filestore_auth(user)
    payload = jwt.decode(fs_user_token, options={"verify_signature": False})
    try:
        r_user = requests.get(f"https://{host}/storemng/api/users/{payload['user']['id']}",
                              headers={"X-Auth": admin_token}, verify=verify)
        r_user.raise_for_status()
    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as err:
        print("{0}: ".format(err))
        return False
    del_user = r_user.json()
    # remove user scope files
    if del_user['scope'] == get_user_scope(user):
        try:  # only user scope files can be removed, not root
            r_filesdel = requests.delete(f"https://{host}/storemng/api/resources",
                                         headers={"X-Auth": fs_user_token}, verify=verify)
            r_filesdel.raise_for_status()
        except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as err:
            print("{0}: ".format(err))
            return False
    # delete user from filestore db
    try:
        r_userdel = requests.delete(f"https://{host}/storemng/api/users/{del_user['id']}",
                                    headers={"X-Auth": fs_user_token}, verify=verify)
        r_userdel.raise_for_status()
    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as err:
        print("{0}: ".format(err))
        return False

    return True
