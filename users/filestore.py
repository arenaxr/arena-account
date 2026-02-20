import base64
import hashlib
import hmac
import json
import os
import re

import requests
from django.contrib.auth.models import User

from .utils import get_rest_host

# FILESTORE LOGIN FLOW:
# 1. Attempt standard user login (`use_filestore_auth`) -> returns token on success.
# 2. If login fails (403):
#    a. Authenticate as Admin (`get_admin_login`).
#    b. Check if the user exists in Filebrowser (`get_filestore_user_json`).
#    c. If user exists: Password is out of sync. Force update password (`set_filestore_pass`).
#    d. If user does not exist: Create new user (`add_filestore_auth`).
#
# FILESTORE DELETE FLOW:
# 1. Authenticate as Admin (`get_admin_login`).
# 2. Find user ID in Filebrowser (`get_filestore_user_json`).
# 3. If user ID is found: Delete user's files/directory using Admin token (`/api/resources/...`).
# 4. If user ID is found: Delete user account using Admin token and Admin password.
# 5. If user ID is not found: Assume user is already deleted, return True.

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


def get_fs_password(user: User):
    """ Helper method to generate a consistent password for FileStore based on username.
    Args:
        user (User): The User model this action is for.

    Returns:
        password (string): The generated password.
    """
    secret = os.environ.get("SECRET_KEY", "django-insecure-secret")

    # Create HMAC using the secret key and username
    signature = hmac.new(
        secret.encode("utf-8"),
        user.username.encode("utf-8"),
        hashlib.sha256
    ).digest()
    # Encode to base64 and strip newlines/padding to make it password-friendly
    return base64.urlsafe_b64encode(signature).decode("utf-8").rstrip("=")


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
        password = get_fs_password(user)

    user_login = {"username": user.username if user.username != os.environ["STORE_ADMIN_USERNAME"] else user.username,
                  "password": password}
    return user_login


def get_filestore_health():
    """ Helper method of to test filebrowser system will respond."""
    verify, host = get_rest_host()
    try:
        r_users = requests.get(f"https://{host}/storemng", verify=verify, timeout=FS_API_TIMEOUT)
        r_users.raise_for_status()
        return True
    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as err:
        print(err)
        return False


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
        # print(err) # Don't print everything, login failure is common
        return None, r_userlogin.status_code
    return r_userlogin.text, r_userlogin.status_code


def login_filestore_user(user: User):
    """ Uses the filebrowser api to login the user.username's filebrowser account and return their auth jwt.
    Handles multiple situations: valid login, add new filebrowser user, update from django password reset.

    Args:
        user (User): The User model this action is for.

    Returns:
        fs_user_token (string): Updated filebrowser api jwt for user.username.
    """

    fs_user_token = None
    if not user.is_authenticated:
        return None
    # try user auth
    fs_user_token, status = use_filestore_auth(user)
    if status == 403: # Login failed
        # unable to login, new user or old?
        if user.username == os.environ["STORE_ADMIN_USERNAME"]:
            return None  # root admin not allowed to alter scope or other properties of itself
        verify, host = get_rest_host()
        admin_login = get_admin_login()
        admin_token, status = get_filestore_token(admin_login, host, verify)
        if not admin_token:
            return None

        # Check if user exists in FileStore
        fs_user_json = get_filestore_user_json(user, host, verify, admin_token)

        if fs_user_json:
            # User exists but password incorrect -> likely needs update (e.g. from django reset or just out of sync)
            fs_user_token = set_filestore_pass(user, host, verify, admin_token, fs_user_json)
        elif not fs_user_token:
            # otherwise user needs to be added
            fs_user_token = add_filestore_auth(user, host, verify, admin_token)

    return fs_user_token


def get_filestore_user_json(user: User, host, verify, admin_token):
    # find user, they may not have a valid password, loop through all
    try:
        r_users = requests.get(f"https://{host}/storemng/api/users",
                               headers={"X-Auth": admin_token}, verify=verify, timeout=FS_API_TIMEOUT)
        r_users.raise_for_status()
    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as err:
        print(err)
        return None
    for r_user in json.loads(r_users.text):
        # print(f"Checking user: {r_user['username']}")
        if r_user["username"] == user.username:
            return r_user

    print(f"User {user.username} not found in FileStore user list: {[u['username'] for u in json.loads(r_users.text)]}")
    return None


def set_filestore_pass(user: User, host, verify, admin_token, fs_user_json):
    """ Uses the filebrowser api to reset the user.username's filebrowser account password and return their auth jwt.

    Args:
        user (User): The User model this action is for.

    Returns:
        fs_user_token (string): Updated filebrowser api jwt for user.username.
    """

    admin_password = os.environ.get("STORE_ADMIN_PASSWORD", "")

    # Minimal payload for password update
    update_data = {
         "password": get_fs_password(user),
         "lockPassword": True,
    }

    fs_user = {
        "what": "user",
        "which": ["password", "lockPassword"],
        "data": update_data,
        "current_password": admin_password  # Add admin password to authorize the change
    }

    try:
        r_userupd = requests.put(f"https://{host}/storemng/api/users/{fs_user_json['id']}",
                                 data=json.dumps(fs_user), headers={"X-Auth": admin_token}, verify=verify, timeout=FS_API_TIMEOUT)
        r_userupd.raise_for_status()
    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as err:
        print(f"Error updating filebrowser password: {err}")
        if hasattr(r_userupd, 'text'):
            print(f"Response: {r_userupd.text}")
        return None

    fs_user_token, status = get_filestore_token(get_user_login(user), host, verify)
    return fs_user_token


def add_filestore_auth(user: User, host, verify, admin_token):
    """ Uses the filebrowser api to add the user.username's filebrowser account and return their auth jwt.

    Args:
        user (User): The User model this action is for.

    Returns:
        fs_user_token (string): Updated filebrowser api jwt for user.username.
    """
    admin_password = os.environ.get("STORE_ADMIN_PASSWORD", "")
    try:
        r_settings = requests.get(f"https://{host}/storemng/api/settings", headers={"X-Auth": admin_token}, verify=verify, timeout=FS_API_TIMEOUT)
        r_settings.raise_for_status()
        settings = r_settings.json()
    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as err:
        print(f"Error fetching filebrowser settings: {err}")
        return None

    fs_user = {
        "what": "user",
        "which": [],
        "data": settings.get("defaults", {}),
        "current_password": admin_password  # Add admin password to authorize creation
    }

    fs_user["data"]["username"] = user.username
    fs_user["data"]["password"] = get_fs_password(user)
    fs_user["data"]["lockPassword"] = True

    # perm dictionary might not exist if defaults is totally empty, ensure it's there
    if "perm" not in fs_user["data"]:
        fs_user["data"]["perm"] = {}

    fs_user["data"]["perm"]["admin"] = user.is_superuser

    # setting scope in users POST will generate user dir
    fs_user["data"]["scope"] = get_user_scope(user)

    # add new user to filestore db
    try:
        r_useradd = requests.post(f"https://{host}/storemng/api/users",
                                  data=json.dumps(fs_user), headers={"X-Auth": admin_token}, verify=verify, timeout=FS_API_TIMEOUT)
        r_useradd.raise_for_status()
        print(f"Created FileStore user: {user.username}")
    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as err:
        print(f"FileStore user creation failed for {user.username}: {err}")
        if hasattr(r_useradd, 'text'):
            print(f"Response: {r_useradd.text}")
        return None

    if user.is_staff:  # admin and staff get root scope
        set_filestore_scope(user)

    fs_user_token, status = get_filestore_token(get_user_login(user), host, verify)
    return fs_user_token


def set_filestore_scope(user: User):
    """ Uses the filebrowser api to reset the user.username's filebrowser account scope and return their auth jwt.

    Args:
        user (User): The User model this action is for.

    Returns:
        bool: True when user.username's filebrowser account scope/permissions are updated.
    """
    verify, host = get_rest_host()
    admin_login = get_admin_login()
    admin_token, status = get_filestore_token(admin_login, host, verify)
    if not admin_token:
        return False

    fs_user_json = get_filestore_user_json(user, host, verify, admin_token)
    if not fs_user_json:
        return False

    # Minimal payload for scope/perm update
    update_data = {}

    # update user scope
    if user.is_staff:
        update_data["scope"] = "."
    else:
        update_data["scope"] = get_user_scope(user)

    update_data["perm"] = fs_user_json["perm"]
    update_data["perm"]["admin"] = user.is_superuser

    fs_user = {
        "what": "user",
        "which": ["scope", "perm"],
        "data": update_data,
        "current_password": os.environ.get("STORE_ADMIN_PASSWORD", "") # Might be needed here too
    }

    try:
        r_userupd = requests.put(f"https://{host}/storemng/api/users/{fs_user_json['id']}",
                                 data=json.dumps(fs_user), headers={"X-Auth": admin_token}, verify=verify, timeout=FS_API_TIMEOUT)
        r_userupd.raise_for_status()
    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as err:
        print(f"Error updating filebrowser scope: {err}")
        if hasattr(r_userupd, 'text'):
             print(f"Response: {r_userupd.text}")
        return False

    return True


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
    admin_token, _ = get_filestore_token(admin_login, host, verify)
    if not admin_token:
        return False
    # find the user's filebrowser ID
    fs_user_json = get_filestore_user_json(user, host, verify, admin_token)

    if not fs_user_json:
        print(f"delete_filestore_user: User '{user.username}' does not exist in filestore (checked admin list), returning true.")
        return True

    user_id_to_delete = fs_user_json['id']

    # Delete the user's files and directory
    if fs_user_json['scope'] == get_user_scope(user):
        try:  # only user scope files can be removed, not root
            # Filebrowser resource path expects the path without the leading './'
            resource_path = get_user_scope(user).lstrip('./')
            r_filesdel = requests.delete(f"https://{host}/storemng/api/resources/{resource_path}",
                                        headers={"X-Auth": admin_token}, verify=verify, timeout=FS_API_TIMEOUT)
            r_filesdel.raise_for_status()
            print(f"Deleted files for user: {user.username}")
        except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as err:
            print(f"Delete files failed: {err}")
            if 'r_filesdel' in locals() and hasattr(r_filesdel, 'text'):
                print(f"Response: {r_filesdel.text}")
            # Proceed with deleting the account even if folder deletion fails or was already deleted

    # Admin password required for user delete
    admin_pass = os.environ.get("STORE_ADMIN_PASSWORD", "")
    r_userdel = None
    try:
        payload = {"current_password": admin_pass}
        r_userdel = requests.delete(f"https://{host}/storemng/api/users/{user_id_to_delete}",
                                    data=json.dumps(payload),
                                    headers={"X-Auth": admin_token}, verify=verify, timeout=FS_API_TIMEOUT)
        r_userdel.raise_for_status()
        return True
    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as err:
        print(f"Delete failed: {err}")
        if r_userdel is not None and hasattr(r_userdel, 'text'):
            print(f"Response: {r_userdel.text}")
        return False

    return True
