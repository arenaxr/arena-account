import json
import logging

import requests
from fastapi import FastAPI
from pymongo import MongoClient
from pymongo.database import Database
from requests.exceptions import HTTPError

from .utils import get_rest_host

# https://pymongo.readthedocs.io/en/stable/index.html


PERSIST_TIMEOUT = 30  # 30 seconds

client: MongoClient
db: Database

app = FastAPI()

logging.getLogger("pymongo").setLevel(logging.WARNING)

# connect to mongodb, read-only
client = MongoClient("mongodb://mongodb/arena_persist?readPreference=primaryPreferred")

try:
    dba = client.admin
    server_status = dba.command('serverStatus')
    current_connections = server_status['connections']['current']
    print(f"arena_persist: current connections: {current_connections}")
    total_connections = server_status['connections']['totalCreated']
    print(f"arena_persist: total connections created: {total_connections}")
    dbs = client.list_database_names()
    print(f"arena_persist: database names: {dbs}")
    # arena-account-1  | arena_persist: database names: ['admin', 'arena_persist', 'config', 'local']

except Exception as e:
    print(f"arena_persist: error: {e}")

db = client.arena_persist
print(f"arena_persist: database arena_persist: {db}")
# arena-account-1  | arena_persist: database arena_persist: Database(MongoClient(host=['mongodb:27017'], document_class=dict, tz_aware=False, connect=True, readpreference='primaryPreferred'), 'arena_persist')
collections = db.list_collection_names()
print(f"arena_persist: collections arena_persist: {collections}")
# arena-account-1  | arena_persist: collections arena_persist: ['arenaobjects']

@app.on_event("shutdown")
def close_db_connection():
    global client
    # disconnect from mongodb
    if client:
        print("arena_persist: closing connection")
        client.close()



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
    # request all namespaces from persist
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
