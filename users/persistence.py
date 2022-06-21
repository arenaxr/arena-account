import json

import jwt
import requests
from requests.exceptions import HTTPError

from .utils import get_rest_host


def delete_scene_objects(scene, token: jwt):
    # delete scene from persist
    verify, host = get_rest_host()
    url = f"https://{host}/persist/{scene}"
    result = _urlopen(url, token, "DELETE", verify)
    return result


def get_persist_scenes_all(token: jwt):
    # request all scenes from persist
    verify, host = get_rest_host()
    url = f"https://{host}/persist/!allscenes"
    result = _urlopen(url, token, "GET", verify)
    if result:
        return json.loads(result)
    return []


def get_persist_scenes_ns(token: jwt, namespace):
    # request all namespace scenes from persist
    verify, host = get_rest_host()
    url = f"https://{host}/persist/{namespace}/!allscenes"
    result = _urlopen(url, token, "GET", verify)
    if result:
        return json.loads(result)
    return []


def _urlopen(url, token: jwt, method, verify):
    if not token:
        print("Error: mqtt_token for persist not available")
        return None
    headers = {"Cookie": f"mqtt_token={token.decode('utf-8')}"}
    cookies = {"mqtt_token": token.decode("utf-8")}
    try:
        if method == "GET":
            response = requests.get(
                url, headers=headers, cookies=cookies, verify=verify
            )
        elif method == "DELETE":
            response = requests.delete(
                url, headers=headers, cookies=cookies, verify=verify
            )
        return response.text
    except (requests.exceptions.ConnectionError, HTTPError) as err:
        print("{0}: ".format(err) + url)
    except ValueError as err:
        print(f"{response.text} {0}: ".format(err) + url)
    return None
