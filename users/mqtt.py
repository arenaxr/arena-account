import base64
import datetime
import os
import re

import jwt
from django.conf import settings

from .models import (SCENE_ANON_USERS_DEF, SCENE_PUBLIC_READ_DEF,
                     SCENE_PUBLIC_WRITE_DEF, SCENE_USERS_DEF, SCENE_VIDEO_CONF_DEF, Scene)

PUBLIC_NAMESPACE = "public"
ANON_REGEX = "anonymous-(?=.*?[a-zA-Z].*?[a-zA-Z])"
DEF_JWT_DURATION = datetime.timedelta(minutes=1)


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
    device=None,
    camid=None,
    userid=None,
    handleftid=None,
    handrightid=None,
    duration=DEF_JWT_DURATION
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
    payload = {}
    payload["sub"] = username
    payload["exp"] = datetime.datetime.utcnow() + duration
    headers = None

    p_public_read = SCENE_PUBLIC_READ_DEF
    p_public_write = SCENE_PUBLIC_WRITE_DEF
    p_anonymous_users = SCENE_ANON_USERS_DEF
    p_video = SCENE_VIDEO_CONF_DEF
    p_users = SCENE_USERS_DEF
    if scene and Scene.objects.filter(name=scene).exists():
        scene_perm = Scene.objects.get(name=scene)
        p_public_read = scene_perm.public_read
        p_public_write = scene_perm.public_write
        p_anonymous_users = scene_perm.anonymous_users
        p_video = scene_perm.video_conference
        p_users = scene_perm.users

    # add jitsi server params if a/v scene
    if scene and camid and p_users and p_video:
        host = os.getenv("HOSTNAME")
        headers = {"kid": host}
        payload["aud"] = "arena"
        payload["iss"] = "arena-account"
        # we use the scene name as the jitsi room name, handle RFC 3986 reserved chars as = '_'
        roomname = re.sub(r"[!#$&'()*+,\/:;=?@[\]]", '_', scene.lower())
        payload["room"] = roomname

    # everyone should be able to read all public scenes
    if not device:  # scene token scenario
        subs.append(f"{realm}/s/{PUBLIC_NAMESPACE}/#")
    # user presence objects
    if user.is_authenticated:
        if device:  # device token scenario
            # device owners have rights to their device objects only
            subs.append(f"{realm}/d/{device}/#")
            pubs.append(f"{realm}/d/{device}/#")
        elif p_users:  # scene token scenario
            # scene rights default by namespace
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
                # add scenes that have been granted by other owners
                if scene:
                    u_scenes = Scene.objects.filter(editors=user)
                    for u_scene in u_scenes:
                        subs.append(f"{realm}/s/{u_scene.name}/#")
                        pubs.append(f"{realm}/s/{u_scene.name}/#")
            # device rights default by namespace
            if user.is_staff:
                # staff/admin have rights to all device objects
                subs.append(f"{realm}/d/#")
                pubs.append(f"{realm}/d/#")
            else:
                # device owners have rights to their device objects only
                subs.append(f"{realm}/d/{username}/#")
                pubs.append(f"{realm}/d/{username}/#")
    # anon/non-owners have rights to view scene objects only
    if scene and not user.is_staff:
        # did the user set specific public read or public write?
        if not user.is_authenticated and not p_anonymous_users:
            return None  # anonymous not permitted
        if p_public_read:
            subs.append(f"{realm}/s/{scene}/#")
        if p_public_write and p_users:
            pubs.append(f"{realm}/s/{scene}/#")
        # user presence objects
        if camid and p_users:  # probable web browser write
            pubs.append(f"{realm}/s/{scene}/{camid}")
            pubs.append(f"{realm}/s/{scene}/{camid}/#")
        if handleftid and p_users:
            pubs.append(f"{realm}/s/{scene}/{handleftid}")
        if handrightid and p_users:
            pubs.append(f"{realm}/s/{scene}/{handrightid}")
    # chat messages
    if scene and userid and p_users:
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
    if scene:
        subs.append(f"{realm}/g/a/#")
        pubs.append(f"{realm}/g/a/#")
    # arts runtime-mngr
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
