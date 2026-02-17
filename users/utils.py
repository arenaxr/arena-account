import datetime
import os
import re
import secrets
import socket
from operator import itemgetter

from django.conf import settings
from django.contrib.auth.models import User
from google.auth.transport import requests as grequests
from google.oauth2 import id_token
from ninja.errors import HttpError

from allauth.socialaccount.models import SocialAccount

from users.persistence import (
    read_persist_ns_all,
    read_persist_scenes_all,
    read_persist_scenes_by_namespace,
    read_persist_scene_objects,
    delete_persist_scene_objects,
    delete_persist_namespace_objects,
)
from users.models import (
    Device,
    Namespace,
    NamespaceDefault,
    Scene,
    SceneDefault,
)
from users.mqtt import (
    ANON_REGEX,
    API_V2,
    CLIENT_REGEX,
    TOPIC_SUPPORTED_API_VERSIONS,
    PUBLIC_NAMESPACE,
    generate_arena_token,
)


def get_rest_host():
    verify = True
    hostname = os.environ["HOSTNAME"]
    hostip = socket.gethostbyname(socket.gethostname())
    if hostname == "localhost" and hostip.startswith("172."):
        host = "host.docker.internal"
        verify = False
    else:
        host = hostname
    return verify, host


def serialize_user_list(users):
    return [user.username for user in users.all()]


def serialize_namespace(namespace):
    return {
        "name": namespace.name,
        "editors": serialize_user_list(namespace.editors),
        "viewers": serialize_user_list(namespace.viewers),
    }


def serialize_scene(scene):
    return {
        "name": scene.name,
        "summary": scene.summary,
        "editors": serialize_user_list(scene.editors),
        "viewers": serialize_user_list(scene.viewers),
        "creation_date": scene.creation_date,
        "public_read": scene.public_read,
        "public_write": scene.public_write,
        "anonymous_users": scene.anonymous_users,
        "video_conference": scene.video_conference,
        "users": scene.users,
    }


def get_my_edit_namespaces(user, version):
    """
    Internal method to update namespace permissions table:
    Requests and returns list of user's editable namespaces from namespace permissions table.
    """
    # load list of namespaces this user can edit
    my_namespaces = Namespace.objects.none()
    editor_namespaces = Namespace.objects.none()
    if user.is_authenticated:
        if user.is_staff:  # admin/staff
            my_namespaces = Namespace.objects.all()
        else:  # standard user
            my_namespaces = Namespace.objects.filter(name=user.username)
            editor_namespaces = Namespace.objects.filter(editors=user)
    # merge 'my' namespaced namespaces and extras namespaces granted
    merged_namespaces = (my_namespaces | editor_namespaces).distinct()

    ns_out = [serialize_namespace(ns) for ns in merged_namespaces]

    if user.is_authenticated:
        # always add current user's namespace
        existing_names = {d.get("name") for d in ns_out}
        if user.username not in existing_names:
            ns_out.append(vars(NamespaceDefault(name=user.username)))
            existing_names.add(user.username)
        # for staff, add any non-user namespaces in persist db
        if user.is_staff:  # admin/staff
            p_nss = read_persist_ns_all()
            for p_ns in p_nss:
                if p_ns not in existing_names:
                    if not User.objects.filter(username=p_ns).exists():
                        ns_out.append(vars(NamespaceDefault(name=p_ns)))
                        existing_names.add(p_ns)

    # count persisted
    all_names = [ns["name"] for ns in ns_out]
    existing_users = set(User.objects.filter(username__in=all_names).values_list("username", flat=True))
    for ns in ns_out:
        ns["account"] = ns["name"] in existing_users

    ns_out = [ns for ns in ns_out if ns.get("name")]
    return sorted(ns_out, key=itemgetter("name"))


def get_my_view_namespaces(user):
    """
    Internal method to update namespace permissions table:
    Requests and returns list of user's viewable namespaces from namespace permissions table.
    """
    # load list of namespaces this user can view
    viewer_namespaces = Namespace.objects.none()
    if user.is_authenticated:
        if not user.is_staff:  # admin/staff
            viewer_namespaces = Namespace.objects.filter(viewers=user)

    ns_out = [serialize_namespace(ns) for ns in viewer_namespaces]

    ns_out = [ns for ns in ns_out if ns.get("name")]
    return sorted(ns_out, key=itemgetter("name"))


def get_my_edit_scenes(user, version):
    """
    Internal method to request edit scenes from persist and permissions:
    1. Requests list of any scenes with objects saved from /persist/!allscenes.
    2. Requests and returns list of user's editable scenes from scene permissions table.
    """
    # load list of scenes this user can edit
    my_scenes = Scene.objects.none()
    editor_scenes = Scene.objects.none()
    editor_namespaces = Namespace.objects.none()
    if user.is_authenticated:
        if user.is_staff:  # admin/staff
            my_scenes = Scene.objects.all()
        else:  # standard user
            my_scenes = Scene.objects.filter(name__startswith=f"{user.username}/")
            editor_scenes = Scene.objects.filter(editors=user)
            editor_namespaces = Namespace.objects.filter(editors=user)
            for editor_namespace in editor_namespaces:
                editor_ns_scenes = Scene.objects.filter(name__startswith=f"{editor_namespace}/")
                editor_scenes = editor_scenes | editor_ns_scenes
    # merge 'my' scenes and extras scenes granted
    merged_scenes = (my_scenes | editor_scenes).distinct()

    sc_out = [serialize_scene(sc) for sc in merged_scenes]

    if user.is_authenticated:
        # update scene list from object persistence db
        p_scenes = []
        if user.is_staff:  # admin/staff
            p_scenes = read_persist_scenes_all()
        else:  # standard user
            # batch query for all namespaces
            req_namespaces = [user.username]
            for editor_namespace in editor_namespaces:
                req_namespaces.append(editor_namespace.name)
            p_scenes = read_persist_scenes_by_namespace(req_namespaces)

        existing_names = {d.get("name") for d in sc_out}
        for p_scene in p_scenes:
            # always add queried persisted scenes
            if p_scene not in existing_names:
                sc_out.append(vars(SceneDefault(name=p_scene)))
                existing_names.add(p_scene)
        if user.is_staff:  # admin/staff
            # count persisted
            p_scenes_set = set(p_scenes)
            for sc in sc_out:
                sc["persisted"] = sc["name"] in p_scenes_set

    sc_out = [sc for sc in sc_out if sc.get("name")]
    return sorted(sc_out, key=itemgetter("name"))


def get_my_view_scenes(user, version):
    """
    Internal method to request view scenes from persist and permissions:
    1. Requests and returns list of user's viewable scenes from scene permissions table.
    """
    # load list of scenes this user can view
    viewer_scenes = Scene.objects.none()
    viewer_namespaces = Namespace.objects.none()
    if user.is_authenticated:
        if not user.is_staff:  # admin/staff
            viewer_scenes = Scene.objects.filter(viewers=user)
            viewer_namespaces = Namespace.objects.filter(viewers=user)
            for viewer_namespace in viewer_namespaces:
                viewer_ns_scenes = Scene.objects.filter(name__startswith=f"{viewer_namespace}/")
                viewer_scenes = viewer_scenes | viewer_ns_scenes
    # merge 'my' scenes and extras scenes granted
    merged_scenes = (viewer_scenes).distinct()

    sc_out = [serialize_scene(sc) for sc in merged_scenes]

    if user.is_authenticated:
        # update scene list from object persistence db
        p_scenes = []
        if not user.is_staff:  # admin/staff
            req_namespaces = []
            for viewer_namespace in viewer_namespaces:
                req_namespaces.append(viewer_namespace.name)
            p_scenes = read_persist_scenes_by_namespace(req_namespaces)

        existing_names = {d.get("name") for d in sc_out}
        for p_scene in p_scenes:
            # always add queried persisted scenes
            if p_scene not in existing_names:
                sc_out.append(vars(SceneDefault(name=p_scene)))
                existing_names.add(p_scene)

    sc_out = [sc for sc in sc_out if sc.get("name")]
    return sorted(sc_out, key=itemgetter("name"))


def namespace_edit_permission(user, namespace):
    """
    Internal method to check if 'user' can edit 'namespace'.
    """
    if not user.is_authenticated:  # anon
        return False
    elif user.is_staff:  # admin/staff
        return True
    elif namespace == user.username:  # ns owner
        return True
    else:
        editor_namespace = None
        try:
            editor_namespace = Namespace.objects.get(name=namespace, editors=user)  # ns editor
        except Namespace.DoesNotExist:
            pass
        finally:
            return bool(editor_namespace)


def scene_edit_permission(user, scene):
    """
    Internal method to check if 'user' can edit 'scene'.
    """
    if not user.is_authenticated:  # anon
        return False
    elif user.is_staff:  # admin/staff
        return True
    elif scene.startswith(f"{user.username}/"):  # s owner
        return True
    else:
        editor_scene = None
        editor_namespace = None
        try:
            editor_scene = Scene.objects.get(name=scene, editors=user)  # s editor
            editor_namespace = Namespace.objects.get(name=scene.split("/")[0], editors=user)  # ns editor
        except (Scene.DoesNotExist, Namespace.DoesNotExist):
            pass
        finally:
            return bool(editor_scene or editor_namespace)


def get_user_from_id_token(gid_token):
    """
    Internal method to validate id_tokens from remote authentication.
    """
    if not gid_token:
        raise ValueError("Missing token.")
    gclient_ids = [os.environ["GAUTH_CLIENTID"],
                   os.environ["GAUTH_INSTALLED_CLIENTID"],
                   os.environ["GAUTH_DEVICE_CLIENTID"]]
    idinfo = id_token.verify_oauth2_token(gid_token, grequests.Request())
    if idinfo["aud"] not in gclient_ids:
        raise ValueError("Could not verify audience.")
    # ID token is valid. Get the user's Google Account ID from the decoded token.
    userid = idinfo["sub"]
    g_user = SocialAccount.objects.get(uid=userid)
    if not g_user:
        raise ValueError("Database error.")

    return User.objects.get(username=g_user.user)


def _field_requested(request, field):
    value = request.POST.get(field, False)
    if value:
        return True
    return False
