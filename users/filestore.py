import json
import os

import jwt
import requests
from django.contrib.auth.models import User

from .utils import get_rest_host

FS_API_TIMEOUT = 15  # 15 seconds


def get_user_scope(user: User):
    """ Helper method to construct single user filebrowser scope.
    Args:
        user (User): The User model this action is for.

    Returns:
        path (string): The single user scope path relative to root filebrowser path.
    """
    return f"./users/{user.username}"


def get_admin_login():
    """ Helper method to construct admin filebrowser login json string.

    Returns:
        admin_login (string): The admin login json string.
    """
    admin_login = {"username": os.environ["STORE_ADMIN_USERNAME"],
                   "password": os.environ["STORE_ADMIN_PASSWORD"]}
    return admin_login


def get_user_login(user: User):
    """ Helper method to construct user.username's filebrowser login json string.

    Args:
        user (User): The User model this action is for.

    Returns:
        user_login (string): The user login json string.
    """
    if user.username == os.environ["STORE_ADMIN_USERNAME"]:
        password = os.environ["STORE_ADMIN_PASSWORD"]
    else:
        password = user.password
    user_login = {"username": user.username,
                  "password": password}
    return user_login


def use_filestore_auth(user: User):
    """ Helper method of to login to user.username's filebrowser account.

    Args:
        user (User): The User model this action is for.

    Returns:
        fs_user_token (string): Updated filebrowser api jwt for user.username.
        http_status (integer): HTTP status code from filebrowser api login.
    """
    if not user.is_authenticated:
        return None
    verify, host = get_rest_host()
    user_login = get_user_login(user)
    user_token, status = get_filestore_token(user_login, host, verify)
    if not user_token:
        return None, status
    return user_token, status


def get_filestore_token(user_login, host, verify):
    """ Uses the filebrowser api to login the user.username's filebrowser account and return their auth jwt.

    Args:
        user_login (string): The user login json string.
        host (string): The django runtime hostname.
        verify (bool): True to verify the hostname tls certificate.

    Returns:
        fs_user_token (string): Updated filebrowser api jwt for user.username.
        http_status (integer): HTTP status code from filebrowser api login.
    """
    try:
        r_userlogin = requests.get(f"https://{host}/storemng/api/login",
                                   data=json.dumps(user_login), verify=verify, timeout=FS_API_TIMEOUT)
        r_userlogin.raise_for_status()
    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as err:
        print(err)
        return None, r_userlogin.status_code
    return r_userlogin.text, r_userlogin.status_code


def add_filestore_auth(user: User):
    """ Uses the filebrowser api to add the user.username's filebrowser account and return their auth jwt.

    Args:
        user (User): The User model this action is for.

    Returns:
        fs_user_token (string): Updated filebrowser api jwt for user.username.
    """
    if not user.is_authenticated:
        return None
    verify, host = get_rest_host()
    # get auth for setting new user
    admin_login = get_admin_login()
    admin_token, status = get_filestore_token(admin_login, host, verify)
    if not admin_token:
        return None
    # get user defaults from global settings
    try:
        r_gset = requests.get(f"https://{host}/storemng/api/settings",
                              headers={"X-Auth": admin_token}, verify=verify, timeout=FS_API_TIMEOUT)
        r_gset.raise_for_status()
    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as err:
        print(err)
        return None
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
                                  data=json.dumps(fs_user), headers={"X-Auth": admin_token}, verify=verify, timeout=FS_API_TIMEOUT)
        r_useradd.raise_for_status()
    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as err:
        print(err)
        return None

    if user.is_staff:  # admin and staff get root scope
        set_filestore_scope(user)

    fs_user_token, status = use_filestore_auth(user)
    return fs_user_token


def set_filestore_scope(user: User):
    """ Uses the filebrowser api to reset the user.username's filebrowser account scope and return their auth jwt.

    Args:
        user (User): The User model this action is for.

    Returns:
        fs_user_token (string): Updated filebrowser api jwt for user.username.
    """
    verify, host = get_rest_host()
    # get auth for setting new user
    admin_login = get_admin_login()
    admin_token, status = get_filestore_token(admin_login, host, verify)
    if not admin_token:
        return None
    # find user
    fs_user_token, status = use_filestore_auth(user)
    if not fs_user_token:
        return None
    payload = jwt.decode(fs_user_token, options={"verify_signature": False})
    try:
        r_user = requests.get(f"https://{host}/storemng/api/users/{payload['user']['id']}",
                              headers={"X-Auth": admin_token}, verify=verify, timeout=FS_API_TIMEOUT)
        r_user.raise_for_status()
    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as err:
        print(err)
        return None
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
                                     data=json.dumps(fs_user), headers={"X-Auth": admin_token}, verify=verify, timeout=FS_API_TIMEOUT)
            r_useradd.raise_for_status()
        except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as err:
            print(err)
            return None

    fs_user_token, status = use_filestore_auth(user)
    return fs_user_token


def set_filestore_pass(user: User):
    """ Uses the filebrowser api to reset the user.username's filebrowser account password and return their auth jwt.

    Args:
        user (User): The User model this action is for.

    Returns:
        fs_user_token (string): Updated filebrowser api jwt for user.username.
    """
    if not user.is_authenticated:
        return None
    if user.username == os.environ["STORE_ADMIN_USERNAME"]:
        return None  # root admin not allowed pass renew
    verify, host = get_rest_host()
    # get auth for removing user
    admin_login = get_admin_login()
    admin_token, status = get_filestore_token(admin_login, host, verify)
    if not admin_token:
        return None
    # find user without valid pass, loop through all
    edit_user = {}
    try:
        r_users = requests.get(f"https://{host}/storemng/api/users",
                               headers={"X-Auth": admin_token}, verify=verify, timeout=FS_API_TIMEOUT)
        r_users.raise_for_status()
    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as err:
        print(err)
        return False
    print(r_users.text)
    for r_user in json.loads(r_users.text):
        if r_user["username"] == user.username:
            edit_user = r_user
            break
    print(edit_user)
    # return False
    edit_user["password"] = user.password
    fs_user = {
        "what": "user",
        "which": ["all"],
        "data": edit_user,
    }
    try:
        r_useradd = requests.put(f"https://{host}/storemng/api/users/{edit_user['id']}",
                                 data=json.dumps(fs_user), headers={"X-Auth": admin_token}, verify=verify, timeout=FS_API_TIMEOUT)
        r_useradd.raise_for_status()
    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as err:
        print(err)
        return None

    fs_user_token, status = use_filestore_auth(user)
    return fs_user_token


def delete_filestore_user(user: User):
    """ Uses the filebrowser api to delete the user.username's filebrowser account and files.

    Args:
        user (User): The User model this action is for.

    Returns:
        bool: True when user.username's filebrowser account and files are both removed.
    """
    if not user.is_authenticated:
        return False
    if user.username == os.environ["STORE_ADMIN_USERNAME"]:
        return False  # root admin not allowed delete
    verify, host = get_rest_host()
    # get auth for removing user
    admin_login = get_admin_login()
    admin_token, status = get_filestore_token(admin_login, host, verify)
    if not admin_token:
        return False
    # find user
    fs_user_token, status = use_filestore_auth(user)
    if not fs_user_token:
        return False
    payload = jwt.decode(fs_user_token, options={"verify_signature": False})
    try:
        r_user = requests.get(f"https://{host}/storemng/api/users/{payload['user']['id']}",
                              headers={"X-Auth": admin_token}, verify=verify, timeout=FS_API_TIMEOUT)
        r_user.raise_for_status()
    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as err:
        print(err)
        return False
    del_user = r_user.json()
    # remove user scope files
    if del_user['scope'] == get_user_scope(user):
        try:  # only user scope files can be removed, not root
            r_filesdel = requests.delete(f"https://{host}/storemng/api/resources",
                                         headers={"X-Auth": fs_user_token}, verify=verify, timeout=FS_API_TIMEOUT)
            r_filesdel.raise_for_status()
        except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as err:
            print(err)
            return False
    # delete user from filestore db
    try:
        r_userdel = requests.delete(f"https://{host}/storemng/api/users/{del_user['id']}",
                                    headers={"X-Auth": fs_user_token}, verify=verify, timeout=FS_API_TIMEOUT)
        r_userdel.raise_for_status()
    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as err:
        print(err)
        return False

    return True
