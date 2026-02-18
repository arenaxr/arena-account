import datetime
import os
import re
import secrets
from operator import itemgetter

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
from http import HTTPStatus


from .filestore import (
    delete_filestore_user,
    get_filestore_health,
    login_filestore_user,
    set_filestore_scope,
)
from .forms import (
    DeviceForm,
    NamespaceForm,
    SceneForm,
    SocialSignupForm,
    UpdateDeviceForm,
    UpdateNamespaceForm,
    UpdateSceneForm,
    UpdateStaffForm,
)
from .models import (
    RE_NS_SLASH_ID,
    Device,
    Namespace,
    NamespaceDefault,
    Scene,
    SceneDefault,
)
from .mqtt import (
    ANON_REGEX,
    API_V1,
    API_V2,
    CLIENT_REGEX,
    PUBLIC_NAMESPACE,
    clean_topics,
    generate_arena_token,
)
from .versioning import SUPPORTED_API_VERSIONS
from .persistence import (
    delete_persist_namespace_objects,
    delete_persist_scene_objects,
    read_persist_ns_all,
    read_persist_scene_objects,
    read_persist_scenes_all,
    read_persist_scenes_by_namespace,
)

from .utils import (
    get_my_edit_namespaces,
    get_my_view_namespaces,
    get_my_edit_scenes,
    get_my_view_scenes,
    get_user_from_id_token,
    namespace_edit_permission,
    scene_edit_permission,
)
from users.versioning import SUPPORTED_API_VERSIONS

# namespaced scene regular expression
RE_PATTERN_NS_SLASH_ID = re.compile(RE_NS_SLASH_ID)


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


def profile_update_namespace(request):
    """
    Handle User Profile page, namespace post submit requests.
    """
    if request.method != "POST":
        return JsonResponse({}, status=HTTPStatus.BAD_REQUEST)
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Not authenticated."}, status=HTTPStatus.FORBIDDEN)
    form = UpdateNamespaceForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Invalid parameters")
        return redirect("users:user_profile")
    if "add" in request.POST:
        namespacename = request.POST.get("namespacename", None)
        s = Namespace(
            name=f"{namespacename}",
        )
        s.save()
        messages.success(request, f"Created namespace permissions: {namespacename}")
        return redirect("users:user_profile")
    elif "edit" in request.POST:
        name = form.cleaned_data["edit"]
        return redirect(f"profile/namespaces/{name}")

    return redirect("users:user_profile")


def profile_update_scene(request):
    """
    Handle User Profile page, scene post submit requests.
    """
    if request.method != "POST":
        return JsonResponse({}, status=HTTPStatus.BAD_REQUEST)
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Not authenticated."}, status=HTTPStatus.FORBIDDEN
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
            request, f"Created scene permissions: {request.user.username}/{scenename}")
        return redirect("users:user_profile")
    elif "edit" in request.POST:
        name = form.cleaned_data["edit"]
        return redirect(f"profile/scenes/{name}")

    return redirect("users:user_profile")


def profile_update_device(request):
    """
    Handle User Profile page, device post submit requests.
    """
    if request.method != "POST":
        return JsonResponse({}, status=HTTPStatus.BAD_REQUEST)
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Not authenticated."}, status=HTTPStatus.FORBIDDEN
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
            request, f"Created device permissions: {request.user.username}/{devicename}")
        return redirect("users:user_profile")
    elif "edit" in request.POST:
        name = form.cleaned_data["edit"]
        return redirect(f"profile/devices/{name}")

    return redirect("users:user_profile")


def namespace_perm_detail(request, pk):
    """
    Handle Namespace Permissions Edit page, get page load and post submit requests.
    - Handles namespace permissions changes and deletes.
    """
    version = request.version

    if not namespace_edit_permission(user=request.user, namespace=pk):
        messages.error(request, f"User does not have edit permission for namespace: {pk}.")
        return redirect("users:user_profile")
    owners = []
    if User.objects.filter(username=pk).exists():
        owners.append(pk)
    # check if namespace exists before the other commands are tried
    try:
        namespace = Namespace.objects.get(name=pk)
    except Namespace.DoesNotExist:
        namespace = Namespace(name=pk)
    if request.method == "POST":
        if "save" in request.POST:
            form = NamespaceForm(instance=namespace, data=request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, f"Updated namespace permissions: {pk}")
                return redirect("users:user_profile")
        elif "delete" in request.POST:
            # delete account namespace data
            if namespace.pk:
                namespace.delete()
                messages.success(request, f"Removed namespace permissions: {pk}")
            # delete persist objects for this namespace
            if delete_persist_namespace_objects(pk):
                messages.success(request, f"Removed namespace persistence objects: {pk}")

            return redirect("users:user_profile")
    else:
        form = NamespaceForm(instance=namespace)

    return render(
        request=request,
        template_name="users/namespace_perm_detail.html",
        context={"namespace": namespace, "owners": owners, "form": form},
    )


def scene_perm_detail(request, pk):
    """
    Handle Scene Permissions Edit page, get page load and post submit requests.
    - Handles scene permissions changes and deletes.
    """
    version = request.version

    if not scene_edit_permission(user=request.user, scene=pk):
        messages.error(request, f"User does not have edit permission for scene: {pk}.")
        return redirect("users:user_profile")
    owners = [pk.split("/")[0]]
    namespace_editors = []  # TODO: define namespaced_editors
    namespace_viewers = []  # TODO: define namespaced_viewers
    # check if scene exists before the other commands are tried
    try:
        scene = Scene.objects.get(name=pk)
    except Scene.DoesNotExist:
        scene = Scene(name=pk)
    if request.method == "POST":
        if "save" in request.POST:
            form = SceneForm(instance=scene, data=request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, f"Updated scene permissions: {pk}")
                return redirect("users:user_profile")
        elif "delete" in request.POST:
            # delete account scene data
            if scene.pk:
                scene.delete()
                messages.success(request, f"Removed scene permissions: {pk}")
            # delete persist scene data
            namespace, sceneId = pk.split("/")
            if delete_persist_scene_objects(namespace, sceneId):
                messages.success(request, f"Removed scene persisted objects: {pk}")
            else:
                messages.error(request, f"Unable to delete {pk} objects from persistence database.")

            return redirect("users:user_profile")
    else:
        form = SceneForm(instance=scene)

    namespace, sceneId = pk.split("/")
    objects = read_persist_scene_objects(namespace, sceneId)
    objects_updated = None
    if len(objects) > 0:
        updated_ts = sorted(objects, reverse=True, key=itemgetter("updatedAt"))[0]["updatedAt"]
        updated_dt = datetime.datetime.fromisoformat(updated_ts.replace("Z", "+00:00"))
        objects_updated = f"{updated_dt.strftime('%B %d, %Y, %H:%M:%S')} UTC"

    return render(
        request=request,
        template_name="users/scene_perm_detail.html",
        context={
            "scene": scene,
            "owners": owners,
            "namespace_editors": namespace_editors,
            "namespace_viewers": namespace_viewers,
            "objects_length": len(objects),
            "objects_updated": objects_updated,
            "form": form,
        },
    )


def device_perm_detail(request, pk):
    """
    Handle Device Permissions Edit page, get page load and post submit requests.
    - Handles device permissions changes and deletes.
    """
    version = request.version

    if not device_edit_permission(user=request.user, device=pk):
        messages.error(request, f"User does not have edit permission for device: {pk}.")
        return redirect("users:user_profile")
    # now, make sure device exists before the other commands are tried
    try:
        device = Device.objects.get(name=pk)
    except Device.DoesNotExist:
        device = Device(name=pk)
    token = None
    if request.method == "POST":
        if "save" in request.POST:
            form = DeviceForm(instance=device, data=request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, f"Updated device permissions: {pk}")
                return redirect("users:user_profile")
        elif "delete" in request.POST:
            # delete account device data
            if device.pk:
                device.delete()
                messages.success(request, f"Removed device permissions: {pk}")
            return redirect("users:user_profile")
        elif "token" in request.POST:
            token = generate_arena_token(
                user=request.user,
                username=request.user.username,
                ns_device=device.name,
                duration=datetime.timedelta(days=30),
                version=version,
            )

    form = DeviceForm(instance=device)
    return render(
        request=request,
        template_name="users/device_perm_detail.html",
        context={"device": device, "token": token, "form": form},
    )


class UserAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated:
            return User.objects.none()

        qs = User.objects.all()

        if self.q:
            qs = qs.filter(username__istartswith=self.q)

        return qs


def profile_update_staff(request):
    """
    Profile page GET/POST handler for editing Staff permissions.
    """
    # update staff status if allowed
    if request.method != "POST":
        return JsonResponse({}, status=HTTPStatus.BAD_REQUEST)
    form = UpdateStaffForm(request.POST)
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Not authenticated."}, status=HTTPStatus.FORBIDDEN)
    if not form.is_valid():
        return JsonResponse(
            {"error": "Invalid parameters"},
            status=HTTPStatus.INTERNAL_SERVER_ERROR,
        )
    staff_username = form.cleaned_data["staff_username"]
    if request.user.is_superuser and User.objects.filter(username=staff_username).exists():
        is_staff = bool(form.cleaned_data["is_staff"])
        print(f"Setting Django user {staff_username}, staff={is_staff}")
        user = User.objects.get(username=staff_username)
        user.is_staff = is_staff
        user.save()
        print(f"Setting Filebrowser user {staff_username}, staff={is_staff}")
        if not set_filestore_scope(user):
            messages.error(request, "Unable to update user's filestore status.")
            return redirect("users:user_profile")

    return redirect("users:user_profile")


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
            devices = Device.objects.filter(name__startswith=f"{user.username}/")
    public_devices = Device.objects.filter(name__startswith=f"{PUBLIC_NAMESPACE}/")
    # merge 'my' namespaced devices and extras devices granted
    merged_devices = (devices | public_devices).distinct().order_by("name")
    return merged_devices


def device_edit_permission(user, device):
    """
    Internal method to check if 'user' can edit 'device'.
    """
    if not user.is_authenticated:  # anon
        return False
    elif user.is_staff:  # admin/staff
        return True
    elif device.startswith(f"{user.username}/"):  # d owner
        return True


def user_profile(request):
    """
    User Profile listing page GET handler.
    - Shows Admin functions, based on superuser status.
    - Shows scenes that the user has permissions to edit and a button to edit them.
    - Handles account deletes.
    """
    version = getattr(request, "version", SUPPORTED_API_VERSIONS[0])
    if version == API_V1:
        return redirect(f"{API_V2}:user_profile")
    if request.method == 'POST':
        # account delete request
        confirm_text = f'delete {request.user.username} account and scenes'
        if confirm_text in request.POST:
            # delete devices permissions
            u_devices = Device.objects.filter(name__startswith=f"{request.user.username}/")
            del_count, _ = u_devices.delete()
            if del_count > 0:
                messages.success(request, f"Removed {del_count} device permissions.")
            # delete scenes permissions
            u_scenes = Scene.objects.filter(name__startswith=f"{request.user.username}/")
            del_count, _ = u_scenes.delete()
            if del_count > 0:
                messages.success(request, f"Removed {del_count} scene permissions.")
            # delete persist objects for this namespace
            if delete_persist_namespace_objects(request.user.username):
                messages.success(request, f"Removed namespace persistence objects: {request.user.username}")
            # delete namespaces permissions
            u_namespaces = Namespace.objects.filter(name=request.user.username)
            del_count, _ = u_namespaces.delete()
            if del_count > 0:
                messages.success(request, f"Removed {del_count} namespace permissions.")
            # delete filestore files/account
            if get_filestore_health():
                if not delete_filestore_user(request.user):
                    messages.error(request, "Unable to delete account/files from the filestore.")
                    return redirect("users:user_profile")
                else:
                    messages.success(request, f"Removed filestore directory: users/{request.user.username}")

            # Be careful of foreign keys, in that case this is suggested:
            # user.is_active = False
            # user.save()
            try:
                # delete user account
                user = request.user
                user.delete()
                messages.success(request, f"Removed user: {request.user.username}")
                return logout_request(request)
            except User.DoesNotExist:
                messages.error(request, "Unable to complete account delete.")

    namespaces = get_my_edit_namespaces(request.user, version)
    scenes = get_my_edit_scenes(request.user, version)
    devices = get_my_devices(request.user)
    staff = None
    if request.user.is_staff:  # admin/staff
        staff = User.objects.filter(is_staff=True)
    return render(
        request=request,
        template_name="users/user_profile.html",
        context={"user": request.user, "namespaces": namespaces, "scenes": scenes,
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
