import base64
import datetime
import os
import re

import jwt
from django.conf import settings

from .models import (SCENE_ANON_USERS_DEF, SCENE_PUBLIC_READ_DEF,
                     SCENE_PUBLIC_WRITE_DEF, Scene)

PUBLIC_NAMESPACE = "public"
ANON_REGEX = "anonymous-(?=.*?[a-zA-Z].*?[a-zA-Z])"


def all_scenes_read_token():
    config = settings.PUBSUB
    privkeyfile = settings.MQTT_TOKEN_PRIVKEY
    if not os.path.exists(privkeyfile):
        print("Error: keyfile not found" + privkeyfile)
        return None
    print("Using keyfile at: " + privkeyfile)
    with open(privkeyfile) as privatefile:
        private_key = privatefile.read()
    payload = {
        "sub": config["mqtt_username"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=5),
        "subs": [f"{config['mqtt_realm']}/s/#"],
    }
    token = jwt.encode(payload, private_key, algorithm="RS256")
    return token


def generate_arena_token(
    *,
    user,
    username,
    realm="realm",
    scene=None,
    camid=None,
    userid=None,
    ctrlid1=None,
    ctrlid2=None,
):
    subs = []
    pubs = []
    privkeyfile = settings.MQTT_TOKEN_PRIVKEY
    if not os.path.exists(privkeyfile):
        print("Error: keyfile not found")
        return None
    print("Using keyfile at: " + privkeyfile)
    with open(privkeyfile) as privatefile:
        private_key = privatefile.read()
    if user.is_authenticated:
        duration = datetime.timedelta(days=1)
    else:
        duration = datetime.timedelta(hours=6)
    payload = {}
    payload["sub"] = username
    payload["exp"] = datetime.datetime.utcnow() + duration
    headers = None

    # add jitsi server params if a/v scene
    if scene and camid:
        host = os.getenv("HOSTNAME")
        headers = {"kid": host}
        if user.is_authenticated:
            display_name = user.get_full_name()
        else:
            display_name = username
        payload["context"] = {"user": {}}
        if display_name:
            payload["context"]["user"]["name"] = display_name
            payload["context"]["user"]["arenaDisplayName"] = display_name
        if userid:
            payload["context"]["user"]["name"] += f"#4r3n4_{userid}"
            payload["context"]["user"]["arenaId"] = userid
        if camid:
            payload["context"]["user"]["arenaCameraName"] = camid
        payload["aud"] = "arena"
        payload["iss"] = "arena-account"
        # we use the scene name as the jitsi room name, handle RFC 3986 reserved chars as = '_'
        roomname = re.sub(r"[!#$&'()*+,\/:;=?@[\]]", '_', scene.lower())
        payload["room"] = roomname

    # everyone should be able to read all public scenes
    subs.append(f"{realm}/s/{PUBLIC_NAMESPACE}/#")
    # user presence objects
    if user.is_authenticated:
        if user.is_staff:
            # staff/admin have rights to all scene objects
            subs.append(f"{realm}/s/#")
            pubs.append(f"{realm}/s/#")
            # vio experiments, staff only
            if scene:
                pubs.append(f"{realm}/vio/{scene}/#")
        else:
            # scene owners have rights to their scene objects only
            subs.append(f"{realm}/s/{username}/#")
            pubs.append(f"{realm}/s/{username}/#")
            # add scenes that have granted by other owners
            u_scenes = Scene.objects.filter(editors=user)
            for u_scene in u_scenes:
                subs.append(f"{realm}/s/{u_scene.name}/#")
                pubs.append(f"{realm}/s/{u_scene.name}/#")
    # anon/non-owners have rights to view scene objects only
    if scene and not user.is_staff:
        scene_opt = Scene.objects.filter(name=scene)
        if scene_opt.exists():
            # did the user set specific public read or public write?
            scene_opt = Scene.objects.get(name=scene)
            if not user.is_authenticated and not scene_opt.anonymous_users:
                return None  # anonymous not permitted
            if scene_opt.public_read:
                subs.append(f"{realm}/s/{scene}/#")
            if scene_opt.public_write:
                pubs.append(f"{realm}/s/{scene}/#")
        else:
            # otherwise, use public access defaults
            if not user.is_authenticated and not SCENE_ANON_USERS_DEF:
                return None  # anonymous not permitted
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
    if scene and userid:
        namespace = scene.split("/")[0]
        userhandle = userid + base64.b64encode(userid.encode()).decode()
        # receive private messages: Read
        subs.append(f"{realm}/c/{namespace}/p/{userid}/#")
        # receive open messages to everyone and/or scene: Read
        subs.append(f"{realm}/c/{namespace}/o/#")
        # send open messages (chat keepalive, messages to all/scene): Write
        pubs.append(f"{realm}/c/{namespace}/o/{userhandle}")
        # private messages to user: Write
        pubs.append(f"{realm}/c/{namespace}/p/+/{userhandle}")

    # apriltags
    subs.append(f"{realm}/g/a/#")
    pubs.append(f"{realm}/g/a/#")
    # runtime
    subs.append(f"{realm}/proc/#")
    pubs.append(f"{realm}/proc/#")
    # network graph
    subs.append("$NETWORK")
    pubs.append("$NETWORK/latency")
    if len(subs) > 0:
        payload["subs"] = clean_topics(subs)
    if len(pubs) > 0:
        payload["publ"] = clean_topics(pubs)

    return jwt.encode(payload, private_key, algorithm="RS256", headers=headers)


def clean_topics(topics):
    """
    Sort and remove list duplicates.
    """
    topics = list(dict.fromkeys(topics))
    topics.sort()
    # after sort, collapse overlapping topic levels to reduce size
    _topics = []
    high_topic = ""
    for i, topic in enumerate(topics):
        add = True
        if i > 0 and high_topic.endswith("/#"):
            if topic.startswith(high_topic[0:-1]):
                add = False  # higher topic level already granted
        if add:
            high_topic = topic
            _topics.append(topic)
    return _topics
