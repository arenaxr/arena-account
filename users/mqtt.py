import base64
import datetime
import os
import re

import jwt
from django.conf import settings

from .versioning import API_V1, API_V2, SUPPORTED_API_VERSIONS
from .models import (
    SCENE_ANON_USERS_DEF,
    SCENE_PUBLIC_READ_DEF,
    SCENE_PUBLIC_WRITE_DEF,
    SCENE_USERS_DEF,
    SCENE_VIDEO_CONF_DEF,
    Namespace,
    Scene,
)
from .mqtt_match import topic_matches_sub
from .topics import ADMIN_TOPICS, PUBLISH_TOPICS, SUBSCRIBE_TOPICS

PUBLIC_NAMESPACE = "public"
ANON_REGEX = "anonymous-(?=.*?[a-zA-Z].*?[a-zA-Z])"
CLIENT_REGEX = r"^[a-zA-Z]+[\w\-\:\.]*$"
DEF_JWT_DURATION = datetime.timedelta(minutes=1)


def generate_arena_token(
    *,
    user,
    username,
    realm=None,
    ns_scene=None,
    ns_device=None,
    ids=None,
    duration=DEF_JWT_DURATION,
    version=API_V2,
):
    """MQTT Token Constructor.

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
    if ns_scene and "camid" in ids and perm["users"] and perm["video"]:
        host = os.getenv("HOSTNAME")
        headers = {"kid": host}
        payload["aud"] = "arena"
        payload["iss"] = "arena-account"
        # we use the scene name as the jitsi room name, handle RFC 3986 reserved chars as = '_'
        roomname = re.sub(r"[!#$&'()*+,\/:;=?@[\]]", "_", ns_scene.lower())
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
            pubs, subs = set_scene_perms_api_v2(user, username, realm, namespace, sceneid, ids, perm)
        else:
            pubs, subs = set_scene_perms_api_v1(user, username, realm, namespace, sceneid, ids, perm)

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
    # global network metrics
    # only non-specific scene/device should monitor latency data
    if not sceneid and not deviceid:
        subs.append("$NETWORK")
    # every client can/should publish latency data
    pubs.append("$NETWORK/latency")

    # consolidate topics and issue token
    if len(pubs) > 0:
        payload["publ"] = clean_topics(pubs)
    if len(subs) > 0:
        payload["subs"] = clean_topics(subs)

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
    """V1 Topic Notes:
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
        if perm["users"]:
            if "camid" in ids:
                pubs.append(f"{realm}/s/{namespace}/{sceneid}/{ids['camid']}")
                pubs.append(f"{realm}/s/{namespace}/{sceneid}/{ids['camid']}/#")
            if "handleftid" in ids:
                pubs.append(f"{realm}/s/{namespace}/{sceneid}/{ids['handleftid']}")
            if "handrightid" in ids:
                pubs.append(f"{realm}/s/{namespace}/{sceneid}/{ids['handrightid']}")
    # chat messages
    if sceneid and "userid" in ids and perm["users"]:
        userhandle = ids["userid"] + base64.b64encode(ids["userid"].encode()).decode()
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
    # scene runtime manager
    if sceneid:
        subs.append(f"{realm}/proc/#")
        pubs.append(f"{realm}/proc/#")

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
    """V2 Topic Notes:
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
            topicv2_add_scene_reader(pubs, subs, realm, "+", "+", ids)
            topicv2_add_scene_writer(pubs, subs, realm, "+", "+", ids)
        else:
            # objectid - o
            # scene owners have rights to their scene objects only
            topicv2_add_scene_reader(pubs, subs, realm, username, "+", ids)
            topicv2_add_scene_writer(pubs, subs, realm, username, "+", ids)

            # add namespaces that have been granted by other owners
            e_namespaces = Namespace.objects.filter(editors=user)
            for u_namespace in e_namespaces:
                if not sceneid or u_namespace.name == f"{namespace}":
                    topicv2_add_scene_reader(pubs, subs, realm, u_namespace.name, "+", ids)
                    topicv2_add_scene_writer(pubs, subs, realm, u_namespace.name, "+", ids)
            v_namespaces = Namespace.objects.filter(viewers=user)
            for u_namespace in v_namespaces:
                if not sceneid or u_namespace.name == f"{namespace}":
                    topicv2_add_scene_reader(pubs, subs, realm, u_namespace.name, "+", ids)

            # add scenes that have been granted by other owners
            e_scenes = Scene.objects.filter(editors=user)
            for u_scene in e_scenes:
                if not sceneid or (sceneid and u_scene.name == f"{namespace}/{sceneid}"):
                    topicv2_add_scene_reader(pubs, subs, realm, u_scene.namespace, u_scene.sceneid, ids)
                    topicv2_add_scene_writer(pubs, subs, realm, u_scene.namespace, u_scene.sceneid, ids)
            v_scenes = Scene.objects.filter(viewers=user)
            for u_scene in v_scenes:
                if not sceneid or (sceneid and u_scene.name == f"{namespace}/{sceneid}"):
                    topicv2_add_scene_reader(pubs, subs, realm, u_scene.namespace, u_scene.sceneid, ids)
    # anon/non-owners have rights to view scene objects only
    if sceneid:
        # did the user set specific public read or public write?
        if not user.is_authenticated and not perm["anonymous_users"]:
            return pubs, subs  # anonymous not permitted
        # objectid - o
        if perm["public_read"]:
            topicv2_add_scene_reader(pubs, subs, realm, namespace, sceneid, ids)
        if perm["public_write"]:
            topicv2_add_scene_writer(pubs, subs, realm, namespace, sceneid, ids)
    # (all) everyone should be able to read all public scenes
    if not sceneid:
        topicv2_add_scene_reader(pubs, subs, realm, PUBLIC_NAMESPACE, "+", ids)
    # (all) user presence/chat
    if sceneid and "userid" in ids and perm["users"]:
        # users enabled, so all message types for uuid = userid/idtag are enabled
        pubs.append(f"{realm}/s/{namespace}/{sceneid}/+/{ids['userclient']}/{ids['userid']}")
        pubs.append(f"{realm}/s/{namespace}/{sceneid}/+/{ids['userclient']}/{ids['userid']}/+")
        # userobjectid - u
        if perm["users"]:
            if "camid" in ids:
                pubs.append(f"{realm}/s/{namespace}/{sceneid}/u/{ids['userclient']}/{ids['camid']}")
                pubs.append(f"{realm}/s/{namespace}/{sceneid}/u/{ids['userclient']}/{ids['camid']}/+")
            if "handleftid" in ids:
                pubs.append(f"{realm}/s/{namespace}/{sceneid}/u/{ids['userclient']}/{ids['handleftid']}")
                pubs.append(f"{realm}/s/{namespace}/{sceneid}/u/{ids['userclient']}/{ids['handleftid']}/+")
            if "handrightid" in ids:
                pubs.append(f"{realm}/s/{namespace}/{sceneid}/u/{ids['userclient']}/{ids['handrightid']}")
                pubs.append(f"{realm}/s/{namespace}/{sceneid}/u/{ids['userclient']}/{ids['handrightid']}/+")
    # (all) render-fusion/env/debug
    if sceneid and "userid" in ids:
        # to-many/pseudo-group sub and pub special permission
        # idtag - r/e/d
        pubs.append(f"{realm}/s/{namespace}/{sceneid}/r/{ids['userclient']}/{ids['userid']}/-")
        pubs.append(f"{realm}/s/{namespace}/{sceneid}/e/{ids['userclient']}/{ids['userid']}/-")
        pubs.append(f"{realm}/s/{namespace}/{sceneid}/d/{ids['userclient']}/{ids['userid']}/-")
    # scene runtime manager
    # sub (client): {runtime_realm}/g/<ns>/p/{runtime_uuid}
    if namespace:
        subs.append(f"{realm}/g/{namespace}/p/+")
        pubs.append(f"{realm}/g/{namespace}/p/+")
    # pub (client): {runtime_realm}/s/<ns>/<scene>/p/{idTag}
    if sceneid and "userid" in ids:
        pubs.append(f"{realm}/s/{namespace}/{sceneid}/p/{ids['userclient']}/{ids['userid']}")

    return pubs, subs


def topicv2_add_scene_reader(pubs, subs, realm, namespaceid, sceneid, ids):
    subs.append(f"{realm}/s/{namespaceid}/{sceneid}/+/+/+")
    if "userid" in ids:
        subs.append(f"{realm}/s/{namespaceid}/{sceneid}/+/+/+/{ids['userid']}/#")


def topicv2_add_scene_writer(pubs, subs, realm, namespaceid, sceneid, ids):
    pubs.append(f"{realm}/s/{namespaceid}/{sceneid}/o/{ids['userclient']}/#")
    pubs.append(f"{realm}/s/{namespaceid}/{sceneid}/p/{ids['userclient']}/+")
    if "userid" in ids:
        pubs.append(f"{realm}/s/{namespaceid}/{sceneid}/o/{ids['userclient']}/+/+")
        if sceneid and "renderfusionid" in ids:
            topicv2_add_rrhost(pubs, subs, realm, namespaceid, sceneid, ids["userclient"])
        if sceneid and "environmentid" in ids:
            topicv2_add_evhost(pubs, subs, realm, namespaceid, sceneid, ids["userclient"])
    # scene runtime manager
    # pub (editor): {runtime_realm}/s/<ns>/<scene>/p/{runtime_uuid}/{module_uuid}/-/stdin
    # sub (editor): {runtime_realm}/s/<ns>/<scene>/p/{runtime_uuid}/{module_uuid}/-/out|err
    pubs.append(f"{realm}/s/{namespaceid}/{sceneid}/p/+/#")
    subs.append(f"{realm}/s/{namespaceid}/{sceneid}/p/+/#")


def topicv2_add_rrhost(pubs, subs, realm, namespaceid, sceneid, userclient):
    subs.append(f"{realm}/s/{namespaceid}/{sceneid}/r/+/+/-/#")
    pubs.append(f"{realm}/s/{namespaceid}/{sceneid}/r/{userclient}/-")
    pubs.append(f"{realm}/s/{namespaceid}/{sceneid}/r/{userclient}/-/+")


def topicv2_add_evhost(pubs, subs, realm, namespaceid, sceneid, userclient):
    subs.append(f"{realm}/s/{namespaceid}/{sceneid}/e/+/+/-/#")
    pubs.append(f"{realm}/s/{namespaceid}/{sceneid}/e/{userclient}/-")
    pubs.append(f"{realm}/s/{namespaceid}/{sceneid}/e/{userclient}/-/+")


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
