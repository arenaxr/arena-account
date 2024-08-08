import base64
import datetime
import os
import re

import jwt
from django.conf import settings

from .models import (SCENE_ANON_USERS_DEF, SCENE_PUBLIC_READ_DEF,
                     SCENE_PUBLIC_WRITE_DEF, SCENE_USERS_DEF,
                     SCENE_VIDEO_CONF_DEF, Scene)

PUBLIC_NAMESPACE = "public"
ANON_REGEX = "anonymous-(?=.*?[a-zA-Z].*?[a-zA-Z])"
DEF_JWT_DURATION = datetime.timedelta(minutes=1)

# version constants
API_V1 = "v1"  # url /user/, first version
API_V2 = "v2"  # url /user/v2/, full topic structure refactor
TOPIC_SUPPORTED_API_VERSIONS = [API_V1, API_V2]  # TODO (mwfarb): remove v1


def all_scenes_read_token(version):
    config = settings.PUBSUB
    privkeyfile = settings.MQTT_TOKEN_PRIVKEY
    if not os.path.exists(privkeyfile):
        print("Error: keyfile not found" + privkeyfile)
        return None
    with open(privkeyfile) as privatefile:
        private_key = privatefile.read()

    realm = config["mqtt_realm"]
    username = config["mqtt_username"]

    payload = {}
    payload["sub"] = username
    payload["exp"] = datetime.datetime.utcnow() + DEF_JWT_DURATION

    if version == API_V2:
        payload["subs"] = [f"{realm}/s/+/+/o/#"]  # v2
    else:
        payload["subs"] = [f"{realm}/s/#"]  # v1

    token = jwt.encode(payload, private_key, algorithm="RS256")
    return token


def generate_arena_token(
    *,
    user,
    username,
    realm=None,
    ns_scene=None,
    ns_device=None,
    ids=None,
    duration=DEF_JWT_DURATION
):
    """ MQTT Token Constructor.

    Returns:
        str: JWT or None
    """
    config = settings.PUBSUB
    if not realm:
        realm = config["mqtt_realm"]
    privkeyfile = settings.MQTT_TOKEN_PRIVKEY
    if not os.path.exists(privkeyfile):
        print("Error: keyfile not found")
        return None
    with open(privkeyfile) as privatefile:
        private_key = privatefile.read()
    payload = {}
    payload["sub"] = username
    payload["exp"] = datetime.datetime.utcnow() + duration
    headers = None

    perm = {
        "public_read": SCENE_PUBLIC_READ_DEF,
        "public_write": SCENE_PUBLIC_WRITE_DEF,
        "anonymous_users": SCENE_ANON_USERS_DEF,
        "video": SCENE_VIDEO_CONF_DEF,
        "users": SCENE_USERS_DEF,
    }
    if ns_scene and Scene.objects.filter(name=ns_scene).exists():
        p = Scene.objects.get(name=ns_scene)
        perm["public_read"] = p.public_read
        perm["public_write"] = p.public_write
        perm["anonymous_users"] = p.anonymous_users
        perm["video"] = p.video_conference
        perm["users"] = p.users

    # add jitsi server params if a/v scene
    if ns_scene and ids and perm["users"] and perm["video"]:
        host = os.getenv("HOSTNAME")
        headers = {"kid": host}
        payload["aud"] = "arena"
        payload["iss"] = "arena-account"
        # we use the scene name as the jitsi room name, handle RFC 3986 reserved chars as = '_'
        roomname = re.sub(r"[!#$&'()*+,\/:;=?@[\]]", '_', ns_scene.lower())
        payload["room"] = roomname

    pubs, subs = get_pubsub_topics_api_v1(
        user,
        username,
        realm,
        ns_scene,
        ns_device,
        ids,
        perm,
    )
    if len(subs) > 0:
        payload["subs"] = clean_topics(subs)
    if len(pubs) > 0:
        payload["publ"] = clean_topics(pubs)

    return jwt.encode(payload, private_key, algorithm="RS256", headers=headers)


def get_pubsub_topics_api_v1(
        user,
        username,
        realm,
        ns_scene,
        ns_device,
        ids,
        perm,
):
    """ V1 Topic Notes:
        /s/: virtual scene objects
        /d/: device inter-process
        /env/: physical environment detection
    """
    pubs = []
    subs = []
    # everyone should be able to read all public scenes
    if not ns_device:  # scene token scenario
        subs.append(f"{realm}/s/{PUBLIC_NAMESPACE}/#")
        # And transmit env data
        pubs.append(f"{realm}/env/{PUBLIC_NAMESPACE}/#")
    # user presence objects
    if user.is_authenticated:
        if ns_device:  # device token scenario
            # device owners have rights to their device objects only
            subs.append(f"{realm}/d/{ns_device}/#")
            pubs.append(f"{realm}/d/{ns_device}/#")
        else:  # scene token scenario
            # scene rights default by namespace
            if user.is_staff:
                # staff/admin have rights to all scene objects
                subs.append(f"{realm}/s/#")
                pubs.append(f"{realm}/s/#")
                # env data for all scenes
                subs.append(f"{realm}/env/#")
                pubs.append(f"{realm}/env/#")
                # vio experiments, staff only
                if ns_scene:
                    pubs.append(f"{realm}/vio/{ns_scene}/#")
            else:
                # scene owners have rights to their scene objects only
                subs.append(f"{realm}/s/{username}/#")
                pubs.append(f"{realm}/s/{username}/#")
                # scene owners have rights to their scene env only
                subs.append(f"{realm}/env/{username}/#")
                pubs.append(f"{realm}/env/{username}/#")
                # add scenes that have been granted by other owners
                u_scenes = Scene.objects.filter(editors=user)
                for u_scene in u_scenes:
                    if not ns_scene or (ns_scene and u_scene.name == ns_scene):
                        subs.append(f"{realm}/s/{u_scene.name}/#")
                        pubs.append(f"{realm}/s/{u_scene.name}/#")
                        subs.append(f"{realm}/env/{u_scene.name}/#")
                        pubs.append(f"{realm}/env/{u_scene.name}/#")
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
    if ns_scene and not user.is_staff:
        # did the user set specific public read or public write?
        if not user.is_authenticated and not perm["anonymous_users"]:
            return None  # anonymous not permitted
        if perm["public_read"]:
            subs.append(f"{realm}/s/{ns_scene}/#")
            # Interactivity to extent of viewing objects is similar to publishing env
            pubs.append(f"{realm}/env/{ns_scene}/#")
        if perm["public_write"]:
            pubs.append(f"{realm}/s/{ns_scene}/#")
        # user presence objects
        if ids and perm["users"]:  # probable web browser write
            pubs.append(f"{realm}/s/{ns_scene}/{ids['camid']}")
            pubs.append(f"{realm}/s/{ns_scene}/{ids['camid']}/#")
            pubs.append(f"{realm}/s/{ns_scene}/{ids['handleftid']}")
            pubs.append(f"{realm}/s/{ns_scene}/{ids['handrightid']}")
    # chat messages
    if ns_scene and ids and perm["users"]:
        namespace = ns_scene.split("/")[0]
        userhandle = ids["userid"] + \
            base64.b64encode(ids["userid"].encode()).decode()
        # receive private messages: Read
        subs.append(f"{realm}/c/{namespace}/p/{ids['userid']}/#")
        # receive open messages to everyone and/or scene: Read
        subs.append(f"{realm}/c/{namespace}/o/#")
        # send open messages (chat keepalive, messages to all/scene): Write
        pubs.append(f"{realm}/c/{namespace}/o/{userhandle}")
        # private messages to user: Write
        pubs.append(f"{realm}/c/{namespace}/p/+/{userhandle}")
    # apriltags
    if ns_scene:
        subs.append(f"{realm}/g/a/#")
        pubs.append(f"{realm}/g/a/#")
    # arts runtime-mngr
    subs.append(f"{realm}/proc/#")
    pubs.append(f"{realm}/proc/#")
    # network graph
    subs.append("$NETWORK")
    pubs.append("$NETWORK/latency")
    return pubs, subs


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
