import json
import logging
from datetime import datetime

import requests
from bson import ObjectId
from requests.exceptions import HTTPError

from .models import get_arenaobjects_collection
from .utils import get_rest_host

PERSIST_TIMEOUT = 30  # 30 seconds


# Mongo DB PyMongo queries for Persist:
# https://pymongo.readthedocs.io/en/stable/index.html


class MongoJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)  # Convert ObjectId to string
        if isinstance(o, datetime):
            return o.isoformat()  # Convert datetime to ISO format
        return super().default(o)  # Call the default method for other types


def read_all_arenaobjects():
    arenaobjects = get_arenaobjects_collection().find()
    return MongoJSONEncoder().encode(list(arenaobjects))


def read_persist_ns_all():
    arenaobjects = get_arenaobjects_collection().aggregate([{
        "$group": {
            "_id": {
                "namespace": "$namespace",
                }
            }
        }
    ])
    return MongoJSONEncoder().encode(list(arenaobjects))


def read_persist_scenes_all():
    arenaobjects = get_arenaobjects_collection().aggregate([
        {
            "$group": {
                "_id": {
                    "namespace": "$namespace",
                    "sceneId": "$sceneId",
                }
            }
        }
    ])
    unique_scenes = []
    for doc in arenaobjects:
        ns = doc['_id']['namespace']
        sc = doc['_id']['sceneId']
        unique_scenes.append(f"{ns}/{sc}")

    return unique_scenes



def read_persist_scenes_by_namespace(namespaces):
    arenaobjects = get_arenaobjects_collection().aggregate([
        {
            "$match": {
                "namespace": {"$in": namespaces}
            }
        },
        {
            "$group": {
                "_id": {
                    "namespace": "$namespace",
                    "sceneId": "$sceneId",
                }
            }
        }
    ])
    unique_scenes = []
    for doc in arenaobjects:
        ns = doc['_id']['namespace']
        sc = doc['_id']['sceneId']
        unique_scenes.append(f"{ns}/{sc}")

    return unique_scenes



def read_persist_scene_objects(namespace, scene):
    query = {"namespace": namespace, "sceneId": scene}
    arenaobjects = get_arenaobjects_collection().find(query)
    json_str = MongoJSONEncoder().encode(list(arenaobjects))
    return json.loads(json_str)


# Mongo DB REST queries for Persist:


def get_scene_objects(token, scene):
    # get scene objects from persist
    verify, host = get_rest_host()
    url = f"https://{host}/persist/{scene}"
    result = _urlopen(url, token, "GET", verify)
    if result:
        return json.loads(result)
    return []


def delete_scene_objects(token, scene):
    # delete scene objects from persist
    verify, host = get_rest_host()
    url = f"https://{host}/persist/{scene}"
    result = _urlopen(url, token, "DELETE", verify)
    return result


def get_persist_ns_all(token):
    # request all namespace names from persist
    verify, host = get_rest_host()
    url = f"https://{host}/persist/!allnamespaces"
    result = _urlopen(url, token, "GET", verify)
    if result:
        return json.loads(result)
    return []


def get_persist_scenes_all(token):
    # request all scene names from persist
    verify, host = get_rest_host()
    url = f"https://{host}/persist/!allscenes"
    result = _urlopen(url, token, "GET", verify)
    if result:
        return json.loads(result)
    return []


def get_persist_scenes_ns(token, namespace):
    # request all namespace scene names from persist
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
