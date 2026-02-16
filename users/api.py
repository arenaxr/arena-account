import secrets
import re
import datetime
from typing import List, Optional

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, JsonResponse
from ninja import NinjaAPI, Form, Schema
from ninja.security import django_auth

from allauth.socialaccount.models import SocialAccount
from users.models import Namespace, Scene, SceneDefault, NamespaceDefault, Device
from users.schemas import NamespaceSchema, SceneSchema, SceneNameSchema
from users.utils import (
    get_my_edit_namespaces,
    get_my_view_namespaces,
    get_my_edit_scenes,
    get_my_view_scenes,
    get_user_from_id_token,
    scene_edit_permission,
    login_filestore_user,
    generate_arena_token,
    serialize_scene,
    ANON_REGEX,
    CLIENT_REGEX,
    API_V2,
    TOPIC_SUPPORTED_API_VERSIONS,
)


api = NinjaAPI(
    title="ARENA Users API",
    version="v1",
    description="ARENA Users Django site endpoints.",
)


class UserStateSchema(Schema):
    authenticated: bool
    username: Optional[str] = None
    fullname: Optional[str] = None
    email: Optional[str] = None
    type: Optional[str] = None
    is_staff: Optional[bool] = None


class HealthSchema(Schema):
    result: str


class StoreLoginSchema(Schema):
    error: Optional[str] = None


class MQTTAuthSchema(Schema):
    username: str
    token: str
    ids: dict


class ErrorSchema(Schema):
    error: str


class MessageSchema(Schema):
    message: str


@api.api_operation(["GET", "POST"], "/user_state", response={200: UserStateSchema, 403: ErrorSchema})
def user_state(request, id_token: str = Form(None)):
    user = request.user
    if request.method == "POST" and id_token:
        try:
            user = get_user_from_id_token(id_token)
        except (ValueError, SocialAccount.DoesNotExist) as err:
            return 403, {"error": str(err)}

    if user.is_authenticated:
        auth_type = "arena" if user.username.startswith("admin") else "google"
        return 200, {
            "authenticated": True,
            "username": user.username,
            "fullname": user.get_full_name(),
            "email": user.email,
            "type": auth_type,
            "is_staff": user.is_staff,
        }
    else:
        return 200, {"authenticated": False}


@api.api_operation(["GET", "POST"], "/storelogin", response={200: StoreLoginSchema, 403: ErrorSchema})
def storelogin(request, id_token: str = Form(None)):
    user = request.user
    if request.method == "POST" and id_token:
        try:
            user = get_user_from_id_token(id_token)
        except (ValueError, SocialAccount.DoesNotExist) as err:
            return 403, {"error": str(err)}

    fs_user_token = login_filestore_user(user)
    response = HttpResponse()
    if fs_user_token:
        response.set_cookie("auth", fs_user_token)
    else:
        response.delete_cookie("auth")
    return response


@api.post("/mqtt_auth", response={200: MQTTAuthSchema, 400: ErrorSchema, 401: ErrorSchema, 403: ErrorSchema, 426: ErrorSchema})
def mqtt_auth(
    request,
    id_token: str = Form(None),
    username: str = Form(None),
    id_auth: str = Form(None),
    realm: str = Form(None),
    scene: str = Form(None),
    client: str = Form(None),
    camid: bool = Form(False),
    handleftid: bool = Form(False),
    handrightid: bool = Form(False),
    renderfusionid: bool = Form(False),
    environmentid: bool = Form(False),
):
    version = getattr(request, "version", TOPIC_SUPPORTED_API_VERSIONS[0])
    if version not in TOPIC_SUPPORTED_API_VERSIONS:
         return 426, {"error": f"ARENA User API {TOPIC_SUPPORTED_API_VERSIONS[0]} token required."}

    user = request.user
    if id_token:
        try:
            user = get_user_from_id_token(id_token)
        except (ValueError, SocialAccount.DoesNotExist) as err:
            return 403, {"error": str(err)}

    if user.is_authenticated:
        username = user.username
        if not username:
            return 401, {"error": "Invalid parameters"}
    else:
        if not username or not re.match(ANON_REGEX, username):
            return 400, {"error": "Invalid form parameter: 'username'"}

    if not client or not re.match(CLIENT_REGEX, client):
         return 400, {"error": "Invalid form parameter: 'client'"}

    nonce = f"{secrets.randbits(32):010d}"
    if version == API_V2:
        userid = f"{username}_{nonce}"
    else:
        userid = f"{nonce}_{username}"

    ids = {}
    ids["userid"] = userid
    ids["userclient"] = f"{userid}_{client}"

    if camid:
        ids["camid"] = userid if version == API_V2 else f"camera_{userid}"
    if handleftid:
        ids["handleftid"] = f"handLeft_{userid}"
    if handrightid:
        ids["handrightid"] = f"handRight_{userid}"
    if renderfusionid:
        ids["renderfusionid"] = "-"
    if environmentid:
        ids["environmentid"] = "-"

    if user.is_authenticated:
        duration = datetime.timedelta(days=1)
    else:
        duration = datetime.timedelta(hours=6)

    token = generate_arena_token(
        user=user,
        username=username,
        realm=realm,
        ns_scene=scene,
        ids=ids,
        duration=duration,
        version=version,
    )

    if not token:
        return 403, {"error": "Authentication required for this scene."}

    data = {
        "username": username,
        "token": token,
        "ids": ids,
    }

    response = JsonResponse(data)
    if len(token) < 4096:
        response.set_cookie(
            "mqtt_token",
            token,
            max_age=86400000,
            httponly=True,
            secure=True,
        )
    return response


@api.get("/health", response=HealthSchema)
def health_state(request):
    return {"result": "success"}


@api.api_operation(["GET", "POST"], "/my_namespaces", response={200: List[NamespaceSchema], 403: ErrorSchema, 426: ErrorSchema})
def list_my_namespaces(request, id_token: str = Form(None)):
    version = getattr(request, "version", TOPIC_SUPPORTED_API_VERSIONS[0])
    if version not in TOPIC_SUPPORTED_API_VERSIONS:
         return 426, {"error": f"ARENA User API {TOPIC_SUPPORTED_API_VERSIONS[0]} token required."}

    user = request.user
    if request.method == "POST" and id_token:
        try:
            user = get_user_from_id_token(id_token)
        except (ValueError, SocialAccount.DoesNotExist) as err:
            return 403, {"error": str(err)}

    edit_namespaces = get_my_edit_namespaces(user, version)
    view_namespaces = get_my_view_namespaces(user)
    # merged_map keyed by name to deduplicate if needed, though they should be distinct lists typically
    merged_map = {ns["name"]: ns for ns in edit_namespaces + view_namespaces}
    return 200, sorted(list(merged_map.values()), key=lambda x: x["name"])


@api.api_operation(["GET", "POST"], "/my_scenes", response={200: List[SceneSchema], 403: ErrorSchema, 426: ErrorSchema})
def list_my_scenes(request, id_token: str = Form(None)):
    version = getattr(request, "version", TOPIC_SUPPORTED_API_VERSIONS[0])
    if version not in TOPIC_SUPPORTED_API_VERSIONS:
         return 426, {"error": f"ARENA User API {TOPIC_SUPPORTED_API_VERSIONS[0]} token required."}

    user = request.user
    if request.method == "POST" and id_token:
        try:
            user = get_user_from_id_token(id_token)
        except (ValueError, SocialAccount.DoesNotExist) as err:
            return 403, {"error": str(err)}

    edit_scenes = get_my_edit_scenes(user, version)
    view_scenes = get_my_view_scenes(user, version)
    merged_map = {sc["name"]: sc for sc in edit_scenes + view_scenes}
    return 200, sorted(list(merged_map.values()), key=lambda x: x["name"])


@api.api_operation(["GET", "POST", "PUT", "DELETE"], "/scenes/{path:scene_name}", response={200: SceneSchema, 201: SceneSchema, 200: MessageSchema, 400: ErrorSchema, 404: ErrorSchema})
def scene_detail(request, scene_name: str, payload: SceneSchema = None):
    # check permissions model for namespace
    try:
        # Check permissions first? The helper might need existing object or checks string regex?
        # scene_edit_permission handles string check and existence check for editor role.
        if not scene_edit_permission(user=request.user, scene=scene_name):
            return 400, {"error": f"User does not have edit permission for scene: {scene_name}."}
    except Exception as e:
        return 400, {"error": str(e)}

    username = request.user.username

    if request.method == "POST":
        if Scene.objects.filter(name=scene_name).exists():
            return 400, {"error": f"Unable to claim existing scene: {scene_name}, use PUT."}

        if payload:
            s = Scene(name=scene_name) # Ensure name from URL is used or validated
            for key, value in payload.dict().items():
                if hasattr(s, key) and value is not None:
                     if key not in ["editors", "viewers", "users", "name"]:
                         setattr(s, key, value)
            s.save()

            if payload.editors:
                users = User.objects.filter(username__in=payload.editors)
                s.editors.set(users)
            if payload.viewers:
                users = User.objects.filter(username__in=payload.viewers)
                s.viewers.set(users)

            return 201, serialize_scene(s)
        else:
            s = Scene(
                name=scene_name,
                summary=f"User {username} adding new scene {scene_name} to account database.",
            )
            s.save()
            return 201, serialize_scene(s)

    try:
        scene = Scene.objects.get(name=scene_name)
    except Scene.DoesNotExist:
        return 404, {"error": "The scene does not exist"}

    if request.method == "GET":
        return 200, serialize_scene(scene)

    if request.method == "PUT":
        if payload:
             # Update fields
             for key, value in payload.dict().items():
                if hasattr(scene, key) and value is not None:
                     if key not in ["editors", "viewers", "name"]: # Name should not change via PUT usually?
                         setattr(scene, key, value)
             scene.save()
             if payload.editors:
                users = User.objects.filter(username__in=payload.editors)
                scene.editors.set(users)
             if payload.viewers:
                users = User.objects.filter(username__in=payload.viewers)
                scene.viewers.set(users)
             return 200, serialize_scene(scene)
        return 400, {"error": "Invalid parameters"}

    if request.method == "DELETE":
        scene.delete()
        return 200, {"message": "Scene was deleted successfully!"}

    return 400, {"error": "Method not allowed"}
