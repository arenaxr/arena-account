import datetime
import json
import os
import re
import secrets

from allauth.socialaccount import helpers
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.views import SignupView as SocialSignupViewDefault
from dal import autocomplete
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from google.auth.transport import requests as grequests
from google.oauth2 import id_token
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import JSONParser

from .filestore import delete_filestore_user, login_filestore_user, set_filestore_scope
from .forms import (
    DeviceForm,
    SceneForm,
    SocialSignupForm,
    UpdateDeviceForm,
    UpdateSceneForm,
    UpdateStaffForm,
)
from .models import Device, Scene
from .mqtt import (
    ANON_REGEX,
    API_V2,
    CLIENT_REGEX,
    PUBLIC_NAMESPACE,
    TOPIC_SUPPORTED_API_VERSIONS,
    all_scenes_read_token,
    generate_arena_token,
)
from .persistence import (
    delete_scene_objects,
    get_persist_scenes_all,
    get_persist_scenes_ns,
)
from .serializers import SceneNameSerializer, SceneSerializer

# namespaced scene regular expression
NS_REGEX = re.compile(r'^[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+$')


def index(request):
    """
    Root page load, index is treated as Login page.
    """
    return redirect("users:login")


def login_request(request):
    """
    Login page load, handles user/pass login if required.
    """
    if request.user.is_authenticated:
        return redirect(f"https://{request.get_host()}/scenes")
    else:
        if request.method == "POST":
            form = AuthenticationForm(request, data=request.POST)
            if form.is_valid():
                username = form.cleaned_data.get("username")
                password = form.cleaned_data.get("password")
                user = authenticate(username=username, password=password)
                if user is not None:
                    login(request, user)
                    messages.info(
                        request, f"You are now logged in as {username}.")
                    return redirect("users:login_callback")
                else:
                    messages.error(request, "Invalid username or password.")
            else:
                messages.error(request, "Invalid username or password.")
        form = AuthenticationForm()
        return render(
            request=request, template_name="users/login.html", context={"login_form": form}
        )


def logout_request(request):
    """
    Removes ID and flushes session data, shows login page.
    """
    logout(request)  # revoke django auth
    response = redirect("users:login")
    response.delete_cookie("auth")  # revoke fs auth
    return response


@ permission_classes([permissions.IsAuthenticated])
def profile_update_scene(request):
    """
    Handle User Profile page, scene post submit requests.
    """
    if request.method != "POST":
        return JsonResponse({}, status=status.HTTP_400_BAD_REQUEST)
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Not authenticated."}, status=status.HTTP_403_FORBIDDEN
        )
    form = UpdateSceneForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Invalid parameters")
        return redirect("users:user_profile")
    if "add" in request.POST:
        scenename = request.POST.get("scenename", None)
        s = Scene(
            name=f"{request.user.username}/{scenename}",
            summary=f"User {request.user.username} adding new scene {scenename} to account database.",
        )
        s.save()
        messages.success(
            request, f"Created scene {request.user.username}/{scenename}")
        return redirect("users:user_profile")
    elif "edit" in request.POST:
        name = form.cleaned_data["edit"]
        return redirect(f"profile/scenes/{name}")

    return redirect("users:user_profile")


@ permission_classes([permissions.IsAuthenticated])
def profile_update_device(request):
    """
    Handle User Profile page, device post submit requests.
    """
    if request.method != "POST":
        return JsonResponse({}, status=status.HTTP_400_BAD_REQUEST)
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Not authenticated."}, status=status.HTTP_403_FORBIDDEN
        )
    form = UpdateDeviceForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Invalid parameters")
        return redirect("users:user_profile")
    if "add" in request.POST:
        devicename = request.POST.get("devicename", None)
        s = Device(
            name=f"{request.user.username}/{devicename}",
        )
        s.save()
        messages.success(
            request, f"Created device {request.user.username}/{devicename}")
        return redirect("users:user_profile")
    elif "edit" in request.POST:
        name = form.cleaned_data["edit"]
        return redirect(f"profile/devices/{name}")

    return redirect("users:user_profile")


def scene_perm_detail(request, pk):
    """
    Handle Scene Permissions Edit page, get page load and post submit requests.
    - Handles scene permissions changes and deletes.
    """
    if not scene_permission(user=request.user, scene=pk):
        messages.error(request, f"User does not have permission for: {pk}.")
        return redirect("users:user_profile")
    # now, make sure scene exists before the other commands are tried
    try:
        scene = Scene.objects.get(name=pk)
    except Scene.DoesNotExist:
        messages.error(request, "The scene does not exist")
        return redirect("users:user_profile")
    if request.method == 'POST':
        if "save" in request.POST:
            form = SceneForm(instance=scene, data=request.POST)
            if form.is_valid():
                form.save()
                return redirect("users:user_profile")
        elif "delete" in request.POST:
            token = generate_arena_token(
                user=request.user, username=request.user.username, version=request.version)
            # delete account scene data
            scene.delete()
            # delete persist scene data
            if not delete_scene_objects(pk, token):
                messages.error(
                    request, f"Unable to delete {pk} objects from persistance database.")

            return redirect("users:user_profile")
    else:
        form = SceneForm(instance=scene)

    return render(request=request, template_name="users/scene_perm_detail.html",
                  context={"scene": scene, "form": form})


def device_perm_detail(request, pk):
    """
    Handle Device Permissions Edit page, get page load and post submit requests.
    - Handles device permissions changes and deletes.
    """
    if not device_permission(user=request.user, device=pk):
        messages.error(request, f"User does not have permission for: {pk}.")
        return redirect("users:user_profile")
    # now, make sure device exists before the other commands are tried
    try:
        device = Device.objects.get(name=pk)
    except Device.DoesNotExist:
        messages.error(request, "The device does not exist")
        return redirect("users:user_profile")
    token = None
    if request.method == 'POST':
        if "save" in request.POST:
            form = DeviceForm(instance=device, data=request.POST)
            if form.is_valid():
                form.save()
                return redirect("users:user_profile")
        elif "delete" in request.POST:
            # delete account device data
            device.delete()
            return redirect("users:user_profile")
        elif "token" in request.POST:
            token = generate_arena_token(
                user=request.user,
                username=request.user.username,
                ns_device=device.name,
                duration=datetime.timedelta(days=30),
                version=request.version
            )

    form = DeviceForm(instance=device)
    return render(request=request, template_name="users/device_perm_detail.html",
                  context={"device": device, "token": token, "form": form})


class UserAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated:
            return User.objects.none()

        qs = User.objects.all()

        if self.q:
            qs = qs.filter(username__istartswith=self.q)

        return qs


@ api_view(["POST", "GET", "PUT", "DELETE"])
@ permission_classes([permissions.IsAuthenticated])
def scene_detail(request, pk):
    """
    Scene Permissions headless endpoint for editing permission: POST, GET, PUT, DELETE.
    """
    # check permissions model for namespace
    if not scene_permission(user=request.user, scene=pk):
        return JsonResponse(
            {"error": f"User does not have permission for: {pk}."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    username = request.user.username

    # try POST first, since it doesn't/shouldn't exist yet
    if request.method == "POST":
        if Scene.objects.filter(name=pk).exists():
            return JsonResponse(
                {"error": f"Unable to claim existing scene: {pk}, use PUT."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if request.body:
            scene_serializer = SceneSerializer(data=scene_data)
            if scene_serializer.is_valid():
                scene_serializer.save()
                return JsonResponse(
                    scene_serializer.data, status=status.HTTP_201_CREATED
                )
            return JsonResponse(
                scene_serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )
        else:
            s = Scene(
                name=pk,
                summary=f"User {username} adding new scene {pk} to account database.",
            )
            s.save()
            return JsonResponse(
                {"message": f"Scene {pk} added successfully!"},
                status=status.HTTP_200_OK,
            )

    # now, make sure scene exists before the other commands are tried
    try:
        scene = Scene.objects.get(name=pk)
    except Scene.DoesNotExist:
        return JsonResponse(
            {"message": "The scene does not exist"}, status=status.HTTP_404_NOT_FOUND
        )

    if request.method == "GET":
        scene_serializer = SceneSerializer(scene)
        return JsonResponse(scene_serializer.data)

    elif request.method == "PUT":
        scene_data = JSONParser().parse(request)
        scene_serializer = SceneSerializer(scene, data=scene_data)
        if scene_serializer.is_valid():
            scene_serializer.save()
            return JsonResponse(scene_serializer.data)
        return JsonResponse(scene_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == "DELETE":
        scene.delete()
        return JsonResponse(
            {"message": "Scene was deleted successfully!"}, status=status.HTTP_200_OK
        )


@permission_classes([permissions.IsAdminUser])
def profile_update_staff(request):
    """
    Profile page GET/POST handler for editing Staff permissions.
    """
    # update staff status if allowed
    if request.method != "POST":
        return JsonResponse({}, status=status.HTTP_400_BAD_REQUEST)
    form = UpdateStaffForm(request.POST)
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Not authenticated."}, status=status.HTTP_403_FORBIDDEN
        )
    if not form.is_valid():
        return JsonResponse(
            {"error": "Invalid parameters"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    staff_username = form.cleaned_data["staff_username"]
    if (request.user.is_superuser and User.objects.filter(username=staff_username).exists()):
        is_staff = bool(form.cleaned_data["is_staff"])
        print(f"Setting Django user {staff_username}, staff={is_staff}")
        user = User.objects.get(username=staff_username)
        user.is_staff = is_staff
        user.save()
        print(f"Setting Filebrowser user {staff_username}, staff={is_staff}")
        if not set_filestore_scope(user):
            messages.error(
                request, "Unable to update user's filestore status.")
            return redirect("users:user_profile")

    return redirect("users:user_profile")


@ api_view(["GET"])
def my_namespaces(request):
    """
    Editable entire namespaces headless endpoint for requesting a list of namespaces this user can write to: GET.
    """
    namespaces = []
    if request.user.is_authenticated:
        namespaces.append(request.user.username)
    if request.user.is_staff:  # admin/staff
        namespaces.append(PUBLIC_NAMESPACE)
    # TODO: when entire namespaces are shared, they should be added here
    namespaces.sort()
    return JsonResponse({"namespaces": namespaces})


@ api_view(["GET", "POST"])
def my_scenes(request):
    """
    Editable scenes headless endpoint for requesting a list of scenes this user can write to: GET/POST.
    - POST requires id_token for headless clients like Python apps.
    """
    if request.version not in TOPIC_SUPPORTED_API_VERSIONS:
        return deprecated_token()

    user = request.user
    if request.method == "POST":
        gid_token = request.POST.get("id_token", None)
        if gid_token:
            try:
                user = get_user_from_id_token(gid_token)
            except (ValueError, SocialAccount.DoesNotExist) as err:
                return JsonResponse({"error": err}, status=status.HTTP_403_FORBIDDEN)

    serializer = SceneNameSerializer(
        get_my_scenes(user, request.version), many=True)
    return JsonResponse(serializer.data, safe=False)


def get_my_scenes(user, version):
    """
    Internal method to update scene permissions table:
    1. Requests list of any scenes with objects saved from /persist/!allscenes to add to scene permissions table.
    2. Requests and returns list of user's editable scenes from scene permissions table.
    """
    # update scene list from object persistance db
    if user.is_authenticated:
        token = all_scenes_read_token(version)
        if user.is_staff:  # admin/staff
            p_scenes = get_persist_scenes_all(token)
        else:  # standard user
            p_scenes = get_persist_scenes_ns(token, user.username)
        a_scenes = Scene.objects.values_list("name", flat=True)

        for p_scene in p_scenes:
            if NS_REGEX.match(p_scene) and p_scene not in a_scenes:
                s = Scene(
                    name=p_scene,
                    summary="Existing scene name migrated from persistence database.",
                )
                s.save()

    # load list of scenes this user can edit
    scenes = Scene.objects.none()
    editor_scenes = Scene.objects.none()
    if user.is_authenticated:
        if user.is_staff:  # admin/staff
            scenes = Scene.objects.all()
        else:  # standard user
            scenes = Scene.objects.filter(name__startswith=f"{user.username}/")
            editor_scenes = Scene.objects.filter(editors=user)
    # merge 'my' namespaced scenes and extras scenes granted
    merged_scenes = (scenes | editor_scenes).distinct().order_by("name")
    return merged_scenes


def get_my_devices(user):
    """
    Internal method to update device permissions table:
    Requests and returns list of user's editable devices from device permissions table.
    """
    # load list of devices this user can edit
    devices = Device.objects.none()
    if user.is_authenticated:
        if user.is_staff:  # admin/staff
            devices = Device.objects.all()
        else:  # standard user
            devices = Device.objects.filter(
                name__startswith=f"{user.username}/")
    public_devices = Device.objects.filter(
        name__startswith=f"{PUBLIC_NAMESPACE}/")
    # merge 'my' namespaced devices and extras devices granted
    merged_devices = (devices | public_devices).distinct().order_by("name")
    return merged_devices


def scene_permission(user, scene):
    """
    Internal method to check if 'user' can edit 'scene'.
    """
    if not user.is_authenticated:  # anon
        return False
    elif user.is_staff:  # admin/staff
        return True
    elif scene.startswith(f"{user.username}/"):  # owner
        return True
    else:
        try:
            editor_scene = Scene.objects.get(
                name=scene, editors=user)  # editor
        except Scene.ObjectDoesNotExist:
            return False
        return True


def device_permission(user, device):
    """
    Internal method to check if 'user' can edit 'device'.
    """
    if not user.is_authenticated:  # anon
        return False
    elif user.is_staff:  # admin/staff
        return True
    elif device.startswith(f"{user.username}/"):  # owner
        return True


def user_profile(request):
    """
    User Profile listing page GET handler.
    - Shows Admin functions, based on superuser status.
    - Shows scenes that the user has permissions to edit and a button to edit them.
    - Handles account deletes.
    """
    version = TOPIC_SUPPORTED_API_VERSIONS[0]  # TODO (mwfarb): resolve missing request.version

    if request.method == 'POST':
        # account delete request
        confirm_text = f'delete {request.user.username} account and scenes'
        if confirm_text in request.POST:
            token = generate_arena_token(
                user=request.user, username=request.user.username, version=version)
            u_scenes = Scene.objects.filter(
                name__startswith=f'{request.user.username}/')
            for scene in u_scenes:
                # delete account scene data
                scene.delete()
                # delete persist scene data
                if not delete_scene_objects(scene.name, token):
                    messages.error(
                        request, f"Unable to delete {scene.name} objects from persistance database.")
                    return redirect("users:user_profile")

            # delete filestore files/account
            if not delete_filestore_user(request.user):
                messages.error(
                    request, "Unable to delete account/files from the filestore.")
                return redirect("users:user_profile")

            # Be careful of foreign keys, in that case this is suggested:
            # user.is_active = False
            # user.save()
            try:
                # delete account
                user = request.user
                user.delete()
                return logout_request(request)
            except User.DoesNotExist:
                messages.error(request, "Unable to complete account delete.")

    scenes = get_my_scenes(request.user, version)
    devices = get_my_devices(request.user)
    staff = None
    if request.user.is_staff:  # admin/staff
        staff = User.objects.filter(is_staff=True)
    return render(
        request=request,
        template_name="users/user_profile.html",
        context={"user": request.user, "scenes": scenes,
                 "devices": devices, "staff": staff},
    )


def login_callback(request):
    """
    Callback page endpoint for successful social auth login, and handles some submit errors.
    """
    return render(request=request, template_name="users/login_callback.html")


class SocialSignupView(SocialSignupViewDefault):
    """
    Signup page handler for the Social Auth signup registration with account email/username.
    """

    def get(self, request, *args, **kwargs):
        social_form = SocialSignupForm(sociallogin=self.sociallogin)
        return render(
            request,
            "users/social_signup.html",
            {"form": social_form, "account": self.sociallogin.account},
        )

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        social_form = self.get_form(form_class)
        if social_form.is_valid():
            return self.form_valid(social_form)
        return render(
            request,
            "users/social_signup.html",
            {"form": social_form, "account": self.sociallogin.account},
        )

    @ transaction.atomic
    def form_valid(self, social_form):
        self.request.session.pop("socialaccount_sociallogin", None)
        user = social_form.save(self.request)
        name = self.sociallogin.account.extra_data.get("name", "")
        return helpers.complete_social_signup(self.request, self.sociallogin)


@ api_view(["GET", "POST"])
def user_state(request):
    """
    Endpoint request for the user's authenticated status, username, name, email: GET/POST.
    - POST requires id_token for headless clients like Python apps.
    """
    user = request.user
    if request.method == "POST":
        gid_token = request.POST.get("id_token", None)
        if gid_token:
            try:
                user = get_user_from_id_token(gid_token)
            except (ValueError, SocialAccount.DoesNotExist) as err:
                return JsonResponse({"error": err}, status=status.HTTP_403_FORBIDDEN)

    if user.is_authenticated:
        if user.username.startswith("admin"):
            authType = "arena"
        else:
            authType = "google"

        return JsonResponse(
            {
                "authenticated": user.is_authenticated,
                "username": user.username,
                "fullname": user.get_full_name(),
                "email": user.email,
                "type": authType,
                "is_staff": user.is_staff,
            },
            status=status.HTTP_200_OK,
        )
    else:  # AnonymousUser
        return JsonResponse(
            {"authenticated": user.is_authenticated, }, status=status.HTTP_200_OK
        )


@ api_view(["GET", "POST"])
def storelogin(request):
    """
    Endpoint request for the user's file store token: GET/POST.
    - POST requires id_token for headless clients like Python apps.
    """
    user = request.user
    if request.method == "POST":
        gid_token = request.POST.get("id_token", None)
        if gid_token:
            try:
                user = get_user_from_id_token(gid_token)
            except (ValueError, SocialAccount.DoesNotExist) as err:
                return JsonResponse({"error": err}, status=status.HTTP_403_FORBIDDEN)

    fs_user_token = login_filestore_user(user)

    response = HttpResponse()
    if fs_user_token:
        response.set_cookie("auth", fs_user_token)
    else:
        response.delete_cookie("auth")  # revoke fs auth
    return response


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
    """
    Internal handler to accommodate backward compatible token requests.
    - Field value could vary: true/false, or another string.
    - Only missing field should evaluate to False.
    """
    value = request.POST.get(field, False)
    if value:
        return True
    return False


def deprecated_token():
    return JsonResponse(
        {"error": f"ARENA User API {TOPIC_SUPPORTED_API_VERSIONS[0]} token required. You may need to update your client's ARENA library, see https://docs.arenaxr.org/content/migration."},
        status=status.HTTP_426_UPGRADE_REQUIRED
    )


@ api_view(["POST"])
def arena_token(request):
    """
    Endpoint to request an ARENA token with permissions for an anonymous or authenticated user for
    MQTT and Jitsi resources given incoming parameters.
    - POST requires id_token for headless clients like Python apps.

    Payload form data:
        username(string): ARENA account username, only used for anonymous.
        id_auth(string): Authentication type: "google" or "anonymous".
        realm(string): ARENA realm.
        scene(string): ARENA namespaced scene.
        client(string): Client type for reference, e.g. "webScene", "py1.2.3", "unity".
        userid(boolean): true to request user context. (deprecated: always true in v2)
        camid(boolean): true to request permission for camera.
        handleftid(boolean): true to request permission for left controller.
        handrightid(boolean): true to request permission for right controller.
    """
    if request.version not in TOPIC_SUPPORTED_API_VERSIONS:
        return deprecated_token()

    user = request.user
    gid_token = request.POST.get("id_token", None)
    if gid_token:
        try:
            user = get_user_from_id_token(gid_token)
        except (ValueError, SocialAccount.DoesNotExist) as err:
            return JsonResponse({"error": err}, status=status.HTTP_403_FORBIDDEN)

    if user.is_authenticated:
        username = user.username
        if not username:
            return JsonResponse(
                {"error": "Invalid parameters"}, status=status.HTTP_401_UNAUTHORIZED
            )
    else:  # AnonymousUser
        username = request.POST.get("username", None)
        if not username or not re.match(ANON_REGEX, username):
            return JsonResponse(
                {"error": "Invalid form parameter: 'username'"}, status=status.HTTP_400_BAD_REQUEST
            )

    client = request.POST.get("client", None)
    if not client or not re.match(CLIENT_REGEX, client):
        return JsonResponse(
            {"error": "Invalid form parameter: 'client'"}, status=status.HTTP_400_BAD_REQUEST
        )

    # produce nonce with 32-bits secure randomness
    nonce = f"{secrets.randbits(32):010d}"
    # define user object_ids server-side to prevent spoofing
    ids = None
    # always include userid in responses for user_client origin checking
    if request.version == API_V2:
        userid = f"{username}_{nonce}"  # v2
    else:
        userid = f"{nonce}_{username}"  # v1
    ids = {}
    ids["userid"] = userid
    ids["userclient"] = f"{userid}_{client}"
    # add avatar object if requested
    if _field_requested(request, "camid"):
        if request.version == API_V2:
            ids["camid"] = userid  # v2
        else:
            ids["camid"] = f"camera_{userid}"  # v1
    if _field_requested(request, "handleftid"):
        ids["handleftid"] = f"handLeft_{userid}"
    if _field_requested(request, "handrightid"):
        ids["handrightid"] = f"handRight_{userid}"
    if _field_requested(request, "renderfusionid"):
        ids["renderfusionid"] = "-"
    if _field_requested(request, "environmentid"):
        ids["environmentid"] = "-"

    if user.is_authenticated:
        duration = datetime.timedelta(days=1)
    else:
        duration = datetime.timedelta(hours=6)
    token = generate_arena_token(
        user=user,
        username=username,
        realm=request.POST.get("realm", None),
        ns_scene=request.POST.get("scene", None),
        ids=ids,
        duration=duration,
        version=request.version
    )
    if not token:
        return JsonResponse(
            {"error": "Authentication required for this scene."}, status=status.HTTP_403_FORBIDDEN
        )
    data = {
        "username": username,
        "token": token,
        "ids": ids,
    }
    response = HttpResponse(json.dumps(data), content_type="application/json")
    response.set_cookie(
        "mqtt_token",
        token,
        max_age=86400000,
        httponly=True,
        secure=True,
    )
    return response


@ api_view(["GET"])
def health_state(request):
    """
    Endpoint request for the arena-account system health: GET.
    """

    return JsonResponse(
        {"result": "success"}, status=status.HTTP_200_OK
    )
