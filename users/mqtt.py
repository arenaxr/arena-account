import base64
import datetime
import os
import re

import jwt
from django.conf import settings

from .models import (SCENE_ANON_USERS_DEF, SCENE_PUBLIC_READ_DEF,
                     SCENE_PUBLIC_WRITE_DEF, SCENE_USERS_DEF,
                     SCENE_VIDEO_CONF_DEF, Scene)
from .mqtt_match import topic_matches_sub
from .topics import ADMIN_TOPICS, PUBLISH_TOPICS, SUBSCRIBE_TOPICS

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
        payload["subs"] = [f"{realm}/s/+/+/o/+"]  # v2
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
    duration=DEF_JWT_DURATION,
    # TODO(mwfarb): /mqtt_auth/ is versioned now, but need to correct upstream version for all request types
    version=API_V1,
):
    """ MQTT Token Constructor.

    Returns:
        str: JWT or None
    """
    # TODO: realm cannot contain any /
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

    # ns_scene, ns_device can/must contain only one '/'
    namespace = sceneid = deviceid = None
    if ns_scene:
        parts = ns_scene.split("/")
        if len(parts) != 2:
            return None
        namespace = parts[0]
        sceneid = parts[1]
    elif ns_device:
        parts = ns_device.split("/")
        if len(parts) != 2:
            return None
        namespace = parts[0]
        deviceid = parts[1]

    pubs = []
    subs = []

    # -- VERSIONED API TOPICS --
    # scene and user session permissions
    if not deviceid:
        if version == API_V2:
            pubs, subs = set_scene_perms_api_v2(
                user, username, realm, namespace, sceneid, ids, perm)
        else:
            pubs, subs = set_scene_perms_api_v1(
                user, username, realm, namespace, sceneid, ids, perm)

    # -- NON-VERSIONED API TOPICS --
    # device permissions
    if user.is_authenticated:
        if deviceid:  # device token scenario
            # device owners have rights to their device objects only
            subs.append(f"{realm}/d/{namespace}/{deviceid}/#")
            pubs.append(f"{realm}/d/{namespace}/{deviceid}/#")
        elif sceneid:  # scene token scenario
            # device rights default by namespace
            if user.is_staff:
                # staff/admin have rights to all device objects
                subs.append(f"{realm}/d/#")
                pubs.append(f"{realm}/d/#")
            else:
                # device owners have rights to their device objects only
                subs.append(f"{realm}/d/{username}/#")
                pubs.append(f"{realm}/d/{username}/#")
    # scene runtime manager
    if sceneid:
        subs.append(f"{realm}/proc/#")
        pubs.append(f"{realm}/proc/#")
    # global network metrics
    # only non-specific scene/device should monitor latency data
    if not sceneid and not deviceid:
        subs.append("$NETWORK")
    # every client can/should publish latency data
    pubs.append("$NETWORK/latency")

    # consolidate topics and issue token
    if len(subs) > 0:
        payload["subs"] = clean_topics(subs)
    if len(pubs) > 0:
        payload["publ"] = clean_topics(pubs)

    return jwt.encode(payload, private_key, algorithm="RS256", headers=headers)


def set_scene_perms_api_v1(
        user,
        username,
        realm,
        namespace,
        sceneid,
        ids,
        perm,
):
    """ V1 Topic Notes:
        Does _NOT_ use ./topics.py
        /s/: virtual scene objects
        /d/: device inter-process
        /env/: physical environment detection
    """
    pubs = []
    subs = []
    # user presence objects
    if user.is_authenticated:
        # scene rights default by namespace
        if user.is_staff:
            # staff/admin have rights to all scene objects
            subs.append(f"{realm}/s/#")
            pubs.append(f"{realm}/s/#")
            # env data for all scenes
            subs.append(f"{realm}/env/#")
            pubs.append(f"{realm}/env/#")
            # vio experiments, staff only
            if sceneid:
                pubs.append(f"{realm}/vio/{namespace}/{sceneid}/#")
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
                if not sceneid or (sceneid and u_scene.name == f"{namespace}/{sceneid}"):
                    subs.append(f"{realm}/s/{u_scene.name}/#")
                    pubs.append(f"{realm}/s/{u_scene.name}/#")
                    subs.append(f"{realm}/env/{u_scene.name}/#")
                    pubs.append(f"{realm}/env/{u_scene.name}/#")
    # everyone should be able to read all public scenes
    subs.append(f"{realm}/s/{PUBLIC_NAMESPACE}/#")
    # And transmit env data
    pubs.append(f"{realm}/env/{PUBLIC_NAMESPACE}/#")
    # anon/non-owners have rights to view scene objects only
    if sceneid and not user.is_staff:
        # did the user set specific public read or public write?
        if not user.is_authenticated and not perm["anonymous_users"]:
            return pubs, subs  # anonymous not permitted
        if perm["public_read"]:
            subs.append(f"{realm}/s/{namespace}/{sceneid}/#")
            # Interactivity to extent of viewing objects is similar to publishing env
            pubs.append(f"{realm}/env/{namespace}/{sceneid}/#")
        if perm["public_write"]:
            pubs.append(f"{realm}/s/{namespace}/{sceneid}/#")
        # user presence objects
        if ids and perm["users"]:  # probable web browser write
            pubs.append(f"{realm}/s/{namespace}/{sceneid}/{ids['camid']}")
            pubs.append(f"{realm}/s/{namespace}/{sceneid}/{ids['camid']}/#")
            pubs.append(f"{realm}/s/{namespace}/{sceneid}/{ids['handleftid']}")
            pubs.append(
                f"{realm}/s/{namespace}/{sceneid}/{ids['handrightid']}")
    # chat messages
    if sceneid and ids and perm["users"]:
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
    # scene apriltags/render-fusion
    if sceneid:
        subs.append(f"{realm}/g/a/#")
        pubs.append(f"{realm}/g/a/#")

    return pubs, subs


def set_scene_perms_api_v2(
        user,
        username,
        realm,
        namespace,
        sceneid,
        ids,
        perm,
):
    """ V2 Topic Notes:
        See ./topics.py
    """
    # TODO (mwfarb): subs.append(SUBSCRIBE_TOPICS.SCENE_PUBLIC.substitute(
    #     {"realm": realm, "nameSpace": PUBLIC_NAMESPACE, "sceneName": "+"}
    # ))
    pubs = []
    subs = []
    # (privilege) scene objects
    if user.is_authenticated:
        # scene rights default by namespace
        if user.is_staff:
            # objectid - o
            # staff/admin have rights to all scene data
            subs.append(f"{realm}/s/+/+/o/+")
            pubs.append(f"{realm}/s/+/+/o/+")
            if ids:
                # subs.append(f"{realm}/s/+/+/o/+/{ids['userid']}")
                pubs.append(f"{realm}/s/+/+/o/+/+")
        else:
            # objectid - o
            # scene owners have rights to their scene objects only
            subs.append(f"{realm}/s/{username}/+/o/+")
            pubs.append(f"{realm}/s/{username}/+/o/+")
            if ids:
                # subs.append(f"{realm}/s/{username}/+/o/+/{ids['userid']}")
                pubs.append(f"{realm}/s/{username}/+/o/+/+")
            # add scenes that have been granted by other owners
            u_scenes = Scene.objects.filter(editors=user)
            for u_scene in u_scenes:
                if not sceneid or (sceneid and u_scene.name == f"{namespace}/{sceneid}"):
                    subs.append(f"{realm}/s/{u_scene.name}/o/+")
                    pubs.append(f"{realm}/s/{u_scene.name}/o/+")
                    if ids:
                        # subs.append(f"{realm}/s/{u_scene.name}/o/+/{ids['userid']}")
                        pubs.append(f"{realm}/s/{u_scene.name}/o/+/+")
    # anon/non-owners have rights to view scene objects only
    if sceneid and not user.is_staff:
        # did the user set specific public read or public write?
        if not user.is_authenticated and not perm["anonymous_users"]:
            return pubs, subs  # anonymous not permitted
        # objectid - o
        if perm["public_read"]:
            subs.append(f"{realm}/s/{namespace}/{sceneid}/o/+")
            if ids:
                subs.append(f"{realm}/s/{namespace}/{sceneid}/o/+/{ids['userid']}")
        if perm["public_write"]:
            pubs.append(f"{realm}/s/{namespace}/{sceneid}/o/+")
            if ids:
                pubs.append(f"{realm}/s/{namespace}/{sceneid}/o/+/+")
    # (all) everyone should be able to read all public scenes
    if not sceneid:
        subs.append(f"{realm}/s/{PUBLIC_NAMESPACE}/+/o/+")
    # (all) sub: public all categories, private all categories to self
    if sceneid:
        subs.append(f"{realm}/s/{namespace}/{sceneid}/+/+")
        if ids:
            subs.append(f"{realm}/s/{namespace}/{sceneid}/+/+/{ids['userid']}")
    # (all) user presence/chat
    if sceneid and ids and perm["users"]:
        # idtag - x/c/p
        pubs.append(f"{realm}/s/{namespace}/{sceneid}/x/{ids['userid']}")
        pubs.append(f"{realm}/s/{namespace}/{sceneid}/x/{ids['userid']}/+")
        pubs.append(f"{realm}/s/{namespace}/{sceneid}/c/{ids['userid']}")
        pubs.append(f"{realm}/s/{namespace}/{sceneid}/c/{ids['userid']}/+")
        pubs.append(f"{realm}/s/{namespace}/{sceneid}/p/{ids['userid']}")
        pubs.append(f"{realm}/s/{namespace}/{sceneid}/p/{ids['userid']}/+")
        # userobjectid - u
        for userobj in ids:
            pubs.append(f"{realm}/s/{namespace}/{sceneid}/u/{ids[userobj]}")
            pubs.append(f"{realm}/s/{namespace}/{sceneid}/u/{ids[userobj]}/+")
    # (all) render-fusion/env/debug
    if sceneid and ids:
        # to-many/pseudo-group sub and pub special permission
        # idtag - r/e/d
        pubs.append(f"{realm}/s/{namespace}/{sceneid}/r/{ids['userid']}/-")
        pubs.append(f"{realm}/s/{namespace}/{sceneid}/e/{ids['userid']}/-")
        pubs.append(f"{realm}/s/{namespace}/{sceneid}/d/{ids['userid']}/-")

    return pubs, subs


def clean_topics(topics):
    """
    Sort and remove list redundancies.
    """
    topics = list(dict.fromkeys(topics))
    topics.sort()
    # after sort, collapse overlapping topic levels to reduce size
    _topics = []
    for topic in topics:
        add = True
        for have in _topics:
            if topic_matches_sub(have, topic):
                add = False
        if add:
            _topics.append(topic)
    return _topics
