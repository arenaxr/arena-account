import json

import requests
from requests.exceptions import HTTPError

from .utils import get_rest_host

PERSIST_TIMEOUT = 30  # 30 seconds


def get_scene_objects(token, scene):
    # get scene from persist
    verify, host = get_rest_host()
    url = f"https://{host}/persist/{scene}"
    result = _urlopen(url, token, "GET", verify)
    if result:
        return json.loads(result)
    return []


def delete_scene_objects(token, scene):
    # delete scene from persist
    verify, host = get_rest_host()
    url = f"https://{host}/persist/{scene}"
    result = _urlopen(url, token, "DELETE", verify)
    return result


def get_persist_ns_all(token):
    # request all scenes from persist
    verify, host = get_rest_host()
    url = f"https://{host}/persist/!allnamespaces"
    result = _urlopen(url, token, "GET", verify)
    if result:
        return json.loads(result)
    return []


def get_persist_scenes_all(token):
    # request all scenes from persist
    verify, host = get_rest_host()
    url = f"https://{host}/persist/!allscenes"
    result = _urlopen(url, token, "GET", verify)
    if result:
        return json.loads(result)
    return []


def get_persist_scenes_ns(token, namespace):
    # request all namespace scenes from persist
    verify, host = get_rest_host()
    url = f"https://{host}/persist/{namespace}/!allscenes"
    result = _urlopen(url, token, "GET", verify)
    if result:
        return json.loads(result)
    return []


def _urlopen(url, token, method, verify):
    if not token:
        print("Error: mqtt_token for persist not available")
        return None
    headers = {"Cookie": f"mqtt_token={token}"}
    cookies = {"mqtt_token": token}
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, cookies=cookies, verify=verify, timeout=PERSIST_TIMEOUT)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, cookies=cookies, verify=verify, timeout=PERSIST_TIMEOUT)
        return response.text
    except (requests.exceptions.ConnectionError, HTTPError) as err:
        print(f"{err}: {url}")
    except ValueError as err:
        print(f"{response.text} {err}: {url}")
    return None
