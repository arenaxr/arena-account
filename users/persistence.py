import datetime
import json
import os
import ssl
from urllib import request
from urllib.error import HTTPError, URLError

import jwt
from django.conf import settings


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
    if os.path.exists(privkeyfile):
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
    try:
        req = request.Request(url)
        req.method = method
        req.add_header("Cookie", f"mqtt_token={token.decode('utf-8')}")
        if settings.DEBUG:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            res = request.urlopen(req, context=context)
        else:
            res = request.urlopen(req)
        result = res.read().decode('utf-8')
        return result
    except (URLError, HTTPError) as err:
        print("{0}: ".format(err)+url)
    except ValueError as err:
        print(f"{result} {0}: ".format(err)+url)
    return None
