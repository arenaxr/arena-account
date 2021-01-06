import datetime
import json
import os
import ssl
from urllib import parse, request
from urllib.error import HTTPError, URLError

import jwt
from django.conf import settings

from .models import Scene

# TODO: this file can be removed when user/scene reservation is supported


def migrate_persist():
    print('starting persist name migrate')
    config = settings.PUBSUB
    privkeyfile = settings.MQTT_TOKEN_PRIVKEY

    # get key for persist
    if not os.path.exists(privkeyfile):
        privkeyfile = '../data/keys/pubsubkey.pem'
    print('Using keyfile at: ' + privkeyfile)
    with open(privkeyfile) as privatefile:
        private_key = privatefile.read()

    payload = {
        'sub': config['mqtt_username'],
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1),
        'subs': [f"{config['mqtt_realm']}/s/#"],
    }
    token = jwt.encode(payload, private_key, algorithm='RS256')

    # request all _scenes from persist
    host = config['mqtt_server']['host']
    # in docker on localhost this url will fail
    url = f'https://{host}/persist/!allscenes'
    context = None
    p_scenes = []
    try:
        req = request.Request(url)
        req.add_header("Cookie", f"mqtt_token={token}")
        if settings.DEBUG:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        res = request.urlopen(req, context=context)
        p_scenes = res.read().decode('utf-8')
    except (URLError, HTTPError) as err:
        print("{0}: ".format(err)+url)

    # add only-missing scenes to scene database
    print(f'persist scenes: {p_scenes}')
    a_scenes = Scene.objects.values_list('name', flat=True)
    print(f'account scenes: {a_scenes}')
    for p_scene in p_scenes:
        print(f'persist scene test: {p_scene}')
        if p_scene not in a_scenes:
            s = Scene(
                name=p_scene,
                summary='Existing scene name migrated from persistence database.',
            )
            print(f'Adding scene to account database: {p_scene}')
            s.save()

    print('ending persist name migrate')
