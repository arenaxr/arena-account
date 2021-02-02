import datetime
import json
import os

import jwt
import requests
from django.conf import settings
from requests.exceptions import HTTPError


def delete_scene_objects(scene, token: jwt):
    # delete scene from persist
    config = settings.PUBSUB
    host = config['mqtt_server']['host']
    # in docker on localhost this url will fail
    url = f'https://{host}/persist/{scene}'
    result = _urlopen(url, token, 'DELETE')
    return result


def get_persist_scenes(token: jwt):
    # request all _scenes from persist
    config = settings.PUBSUB
    host = config['mqtt_server']['host']
    # in docker on localhost this url will fail
    url = f'https://{host}/persist/!allscenes'
    result = _urlopen(url, token, 'GET')
    if result:
        return json.loads(result)
    return []


def scenes_read_token():
    config = settings.PUBSUB
    privkeyfile = settings.MQTT_TOKEN_PRIVKEY
    if not os.path.exists(privkeyfile):
        print('Error: keyfile not found' + privkeyfile)
        return None
    print('Using keyfile at: ' + privkeyfile)
    with open(privkeyfile) as privatefile:
        private_key = privatefile.read()
    payload = {
        'sub': config['mqtt_username'],
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=5),
        'subs': [f"{config['mqtt_realm']}/s/#"],
    }
    token = jwt.encode(payload, private_key, algorithm='RS256')
    return token


def _urlopen(url, token: jwt, method):
    if not token:
        print("Error: mqtt_token for persist not available")
        return None
    headers = {"Cookie": f"mqtt_token={token.decode('utf-8')}"}
    cookies = {'mqtt_token': token.decode('utf-8')}
    verify = not settings.DEBUG
    try:
        if method == 'GET':
            response = requests.get(
                url, headers=headers, cookies=cookies, verify=verify)
        elif method == 'DELETE':
            response = requests.delete(
                url, headers=headers, cookies=cookies, verify=verify)
        return response.text
    except (requests.exceptions.ConnectionError, HTTPError) as err:
        print("{0}: ".format(err)+url)
    except ValueError as err:
        print(f"{response.text} {0}: ".format(err)+url)
    return None
