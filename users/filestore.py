import json
import os

import requests
from django.contrib.auth.models import User


def get_rest_host():
    verify = True
    if os.environ["HOSTNAME"] == "localhost":
        host = "host.docker.internal"
        verify = False
    else:
        host = os.environ["HOSTNAME"]
    return verify, host


def get_user_scope(user: User):
    return f"./users/{user.username}"


def use_filestore_auth(user: User):
    if not user.is_authenticated:
        return None
    verify, host = get_rest_host()
    if user.username == os.environ["STORE_ADMIN_USERNAME"]:
        password = os.environ["STORE_ADMIN_PASSWORD"]
    else:
        password = user.password
    user_login = {"username": user.username,
                  "password": password}
    try:
        r_userlogin = requests.post(f"https://{host}/storemng/api/login",
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
    admin_login = {"username": os.environ["STORE_ADMIN_USERNAME"],
                   "password": os.environ["STORE_ADMIN_PASSWORD"]}
    try:
        r_admin = requests.post(f"https://{host}/storemng/api/login",
                                data=json.dumps(admin_login), verify=verify)
        r_admin.raise_for_status()
    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as err:
        print("{0}: ".format(err))
        return None
    admin_token = r_admin.text
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
    if not user.is_superuser:
        fs_user["data"]["scope"] = get_user_scope(user)
    # add new user to filestore db
    try:
        r_useradd = requests.post(f"https://{host}/storemng/api/users",
                                  data=json.dumps(fs_user), headers={"X-Auth": admin_token}, verify=verify)
        r_useradd.raise_for_status()
    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as err:
        print("{0}: ".format(err))
        return None

    return use_filestore_auth(user)


def delete_filestore_user(user: User):
    if not user.is_authenticated:
        return False
    if user.username == os.environ["STORE_ADMIN_USERNAME"]:
        return False  # root admin not allowed delete
    verify, host = get_rest_host()
    # get auth for removing user
    admin_login = {"username": os.environ["STORE_ADMIN_USERNAME"],
                   "password": os.environ["STORE_ADMIN_PASSWORD"]}
    try:
        r_admin = requests.post(f"https://{host}/storemng/api/login",
                                data=json.dumps(admin_login), verify=verify)
        r_admin.raise_for_status()
    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as err:
        print("{0}: ".format(err))
        return False
    admin_token = r_admin.text
    # find user in list
    try:
        r_users = requests.get(f"https://{host}/storemng/api/users",
                               headers={"X-Auth": admin_token}, verify=verify)
        r_users.raise_for_status()
    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as err:
        print("{0}: ".format(err))
        return False
    fsusers = r_users.json()
    for fsuser in fsusers:
        if fsuser["username"]:
            del_user = fsuser
        else:
            return False
    # get auth for removing files
    fs_user_token = use_filestore_auth(user)
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
