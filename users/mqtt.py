import base64
import datetime

import jwt
from django.conf import settings

from .models import SCENE_PUBLIC_READ_DEF, SCENE_PUBLIC_WRITE_DEF, Scene


def generate_mqtt_token(
    *,
    user,
    username,
    realm='realm',
    scene=None,
    camid=None,
    userid=None,
    ctrlid1=None,
    ctrlid2=None
):
    subs = []
    pubs = []
    with open(settings.MQTT_TOKEN_PRIVKEY) as privatefile:
        private_key = privatefile.read()
    if user.is_authenticated:
        duration = datetime.timedelta(days=1)
    else:
        duration = datetime.timedelta(hours=6)
    payload = {
        'sub': username,
        'exp': datetime.datetime.utcnow() + duration
    }
    # user presence objects
    subs.append(f"{realm}/g/a/#")
    if user.is_authenticated:
        pubs.append(f"{realm}/g/a/#")
        subs.append(f"{realm}/s/#")  # allows !allscenes for all auth users
        if user.is_staff:
            # staff/admin have rights to all scene objects
            pubs.append(f"{realm}/s/#")
        else:
            # scene owners have rights to their scene objects only
            subs.append(f"{realm}/s/{username}/#")
            pubs.append(f"{realm}/s/{username}/#")
            # add scenes that have granted by other owners
            u_scenes = Scene.objects.filter(editors=user)
            for u_scene in u_scenes:
                subs.append(f"{realm}/s/{u_scene.name}/#")
                pubs.append(f"{realm}/s/{u_scene.name}/#")
    # vio or test cameras
    if scene and camid:
        pubs.append(f"{realm}/vio/{scene}/{camid}")
        pubs.append(f"{realm}/g/a/{camid}")
    # anon/non-owners have rights to view scene objects only
    if scene and not user.is_staff:
        scene_opt = Scene.objects.filter(name=scene)
        if scene_opt.exists():
            # did the user set specific public read or public write?
            scene_opt = Scene.objects.get(name=scene)
            if scene_opt.public_read:
                subs.append(f"{realm}/s/{scene}/#")
            if scene_opt.public_write:
                pubs.append(f"{realm}/s/{scene}/#")
        else:
            # otherwise, use public access defaults
            if SCENE_PUBLIC_READ_DEF:
                subs.append(f"{realm}/s/{scene}/#")
            if SCENE_PUBLIC_WRITE_DEF:
                pubs.append(f"{realm}/s/{scene}/#")
        if camid:  # probable web browser write
            pubs.append(f"{realm}/s/{scene}/{camid}")
            pubs.append(f"{realm}/s/{scene}/{camid}/#")
        if ctrlid1:
            pubs.append(f"{realm}/s/{scene}/{ctrlid1}")
        if ctrlid2:
            pubs.append(f"{realm}/s/{scene}/{ctrlid2}")
    # chat messages
    if userid:
        userhandle = userid + base64.b64encode(userid.encode()).decode()
        # receive private messages: Read
        subs.append(f"{realm}/g/c/p/{userid}/#")
        # receive open messages to everyone and/or scene: Read
        subs.append(f"{realm}/g/c/o/#")
        # send open messages (chat keepalive, messages to all/scene): Write
        pubs.append(f"{realm}/g/c/o/{userhandle}")
        # private messages to user: Write
        pubs.append(f"{realm}/g/c/p/+/{userhandle}")
    # runtime
    subs.append(f"{realm}/proc/#")
    pubs.append(f"{realm}/proc/#")
    # network graph
    subs.append("$NETWORK")
    pubs.append("$NETWORK/latency")
    if len(subs) > 0:
        subs.sort()
        payload['subs'] = subs
    if len(pubs) > 0:
        pubs.sort()
        payload['publ'] = pubs
    return jwt.encode(payload, private_key, algorithm='RS256')
