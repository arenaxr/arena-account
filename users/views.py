import json
import logging
import os
import secrets

import coreapi
from allauth.socialaccount import helpers
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.views import SignupView as SocialSignupViewDefault
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import BadHeaderError, send_mail
from django.db import transaction
from django.db.models.query_utils import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from google.auth.transport import requests
from google.oauth2 import id_token
from rest_framework import permissions, status
from rest_framework.compat import coreapi
from rest_framework.decorators import api_view, permission_classes, schema
from rest_framework.parsers import JSONParser
from rest_framework.schemas import AutoSchema

from .forms import (
    SceneForm,
    SocialSignupForm,
    UpdateSceneForm,
    UpdateStaffForm
)
from .models import Scene
from .mqtt import generate_mqtt_token
from .persistence import (delete_scene_objects, get_persist_scenes,
                          scenes_read_token)
from .serializers import SceneNameSerializer, SceneSerializer

STAFF_ACCTNAME = "public"

logger = logging.getLogger(__name__)
logger.info("views.py load test...")


def index(request):
    # index is treated as login
    if request.user.is_authenticated:
        return redirect("scenes")
    else:
        return redirect("login")


def login_request(request):
    if request.user.is_authenticated:
        return redirect("scenes")
    else:
        if request.method == "POST":
            form = AuthenticationForm(request, data=request.POST)
            if form.is_valid():
                username = form.cleaned_data.get("username")
                password = form.cleaned_data.get("password")
                user = authenticate(username=username, password=password)
                if user is not None:
                    login(request, user)
                    messages.info(request, f"You are now logged in as {username}.")
                    return redirect("login_callback")
                else:
                    messages.error(request, "Invalid username or password.")
            else:
                messages.error(request, "Invalid username or password.")
        form = AuthenticationForm()
        return render(
            request=request, template_name="users/login.html", context={"login_form": form}
        )


def logout_request(request):
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect("login")


@permission_classes([permissions.IsAuthenticated])
def profile_update_scene(request):
    """
    Update existing scene permissions the user has access to.
    """
    if request.method != "POST":
        return JsonResponse({}, status=status.HTTP_400_BAD_REQUEST)
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Not authenticated."}, status=status.HTTP_403_FORBIDDEN
        )
    form = UpdateSceneForm(request.POST)
    if not form.is_valid():
        return JsonResponse(
            {"error": "Invalid parameters"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    if "edit" in request.POST:
        name = form.cleaned_data["edit"]
        return redirect(f"profile/scenes/{name}")

    return redirect("user_profile")


def scene_perm_detail(request, pk):
    if not scene_permission(user=request.user, scene=pk):
        return JsonResponse({"error": f"User does not have permission for: {pk}."}, status=status.HTTP_400_BAD_REQUEST)
    # now, make sure scene exists before the other commands are tried
    try:
        scene = Scene.objects.get(name=pk)
    except Scene.DoesNotExist:
        return JsonResponse({"message": "The scene does not exist"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'POST':
        if "save" in request.POST:
            form = SceneForm(instance=scene, data=request.POST)
            if form.is_valid():
                form.save()
                return redirect("user_profile")
        elif "delete" in request.POST:
            # delete account scene data
            scene.delete()
            # delete persist scene data
            token = generate_mqtt_token(
                user=request.user, username=request.user.username)
            delete_scene_objects(pk, token)
            return redirect("user_profile")
    else:
        form = SceneForm(instance=scene)

    return render(request=request, template_name="users/scene_perm_detail.html",
                  context={"scene": scene, "form": form})


@api_view(["POST", "GET", "PUT", "DELETE"])
@permission_classes([permissions.IsAuthenticated])
def scene_detail(request, pk):
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
    Toggle the user's is_staff true/false status.
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
    is_staff = form.cleaned_data["is_staff"]
    if (
        request.user.is_superuser
        and User.objects.filter(username=staff_username).exists()
    ):
        print(f"Setting user {staff_username}, is_staff={is_staff}")
        user = User.objects.get(username=staff_username)
        user.is_staff = is_staff
        user.save()

    return redirect("user_profile")


@api_view(["GET"])
def my_scenes(request):
    """
    Request a list of scenes this user can write to.
    """
    serializer = SceneNameSerializer(get_my_scenes(request.user), many=True)
    return JsonResponse(serializer.data, safe=False)


def get_my_scenes(user):
    # update scene list from object persistance db
    token = scenes_read_token()
    p_scenes = get_persist_scenes(token)
    a_scenes = Scene.objects.values_list("name", flat=True)
    for p_scene in p_scenes:
        if p_scene not in a_scenes:
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
    return (scenes | editor_scenes).order_by("name")


def scene_permission(user, scene):
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


def scene_landing(request):
    my_scenes = get_my_scenes(request.user)
    public_scenes = Scene.objects.filter(name__startswith=f"public/")
    return render(
        request=request,
        template_name="users/scene_landing.html",
        context={"user": request.user, "my_scenes": my_scenes,
                 "public_scenes": public_scenes, },
    )


def user_profile(request):
    # load updated list of staff users
    scenes = get_my_scenes(request.user)
    staff = None
    if request.user.is_staff:  # admin/staff
        staff = User.objects.filter(is_staff=True)
    return render(
        request=request,
        template_name="users/user_profile.html",
        context={"user": request.user, "scenes": scenes, "staff": staff},
    )


def login_callback(request):
    return render(request=request, template_name="users/login_callback.html")


class SocialSignupView(SocialSignupViewDefault):
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

    @transaction.atomic
    def form_valid(self, social_form):
        self.request.session.pop("socialaccount_sociallogin", None)
        user = social_form.save(self.request)
        name = self.sociallogin.account.extra_data.get("name", "")
        return helpers.complete_social_signup(self.request, self.sociallogin)


@api_view(["GET", "POST"])
def user_state(request):
    """
    Request the user's authenticated status, username, name, email.
    """
    user = request.user
    if request.method == "POST":
        gid_token = request.POST.get("id_token", None)
        if gid_token:
            try:
                user = get_user_from_id_token(gid_token)
            except (ValueError, SocialAccount.DoesNotExist) as err:
                return JsonResponse(
                    {"error": "{0}".format(err)}, status=status.HTTP_403_FORBIDDEN
                )

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
            },
            status=status.HTTP_200_OK,
        )
    else:  # AnonymousUser
        return JsonResponse(
            {"authenticated": user.is_authenticated, }, status=status.HTTP_200_OK
        )


class MqttTokenSchema(AutoSchema):
    def __init__(self):
        super(MqttTokenSchema, self).__init__()

    def get_manual_fields(self, path, method):
        extra_fields = [
            coreapi.Field(
                "username",
                required=True,
                location="body",
                type="string",
                description="ARENA user database username, or like 'anonymous-[name]'.",
            ),
            coreapi.Field(
                "id_token",
                required=False,
                location="body",
                type="string",
                description="JWT id_token from social account authentication service, \
                                    if forwarding from remote client like arena-py.",
            ),
            coreapi.Field(
                "realm",
                required=False,
                location="body",
                type="string",
                description="Name of the ARENA realm used in the topic string (default: 'realm').",
            ),
            coreapi.Field(
                "scene",
                required=False,
                location="body",
                type="string",
                description="Name of the ARENA scene: '[namespace]/[scene]'.",
            ),
            coreapi.Field(
                "userid",
                required=False,
                location="body",
                type="string",
                description="Name of the user's ARENA web client id.",
            ),
            coreapi.Field(
                "camid",
                required=False,
                location="body",
                type="string",
                description="Name of the user's ARENA camera object id.",
            ),
            coreapi.Field(
                "ctrlid1",
                required=False,
                location="body",
                type="string",
                description="Name of the user's ARENA controller object 1, like vive left.",
            ),
            coreapi.Field(
                "ctrlid2",
                required=False,
                location="body",
                type="string",
                description="Name of the user's ARENA controller object 2, like vive right.",
            ),
        ]
        manual_fields = super().get_manual_fields(path, method)
        return manual_fields + extra_fields


def get_user_from_id_token(gid_token):
    if not gid_token:
        raise ValueError("Missing token.")
    gclient_ids = [os.environ["GAUTH_CLIENTID"],
                   os.environ["GAUTH_INSTALLED_CLIENTID"]]
    idinfo = id_token.verify_oauth2_token(gid_token, requests.Request())
    if idinfo["aud"] not in gclient_ids:
        raise ValueError("Could not verify audience.")
    # ID token is valid. Get the user's Google Account ID from the decoded token.
    userid = idinfo["sub"]
    g_user = SocialAccount.objects.get(uid=userid)
    if not g_user:
        raise ValueError("Database error.")

    return User.objects.get(username=g_user.user)


def _field_requested(request, field):
    # field value could vary: true/false, or another string
    # only missing field should evaluate to False
    value = request.POST.get(field, False)
    if value:
        return True
    return False


@api_view(["POST"])
# @schema(MqttTokenSchema())  # TODO: schema not working yet
def mqtt_token(request):
    """
    Request a MQTT JWT token with permissions for an anonymous or authenticated user given incoming parameters.
    """
    user = request.user
    gid_token = request.POST.get("id_token", None)
    if gid_token:
        try:
            user = get_user_from_id_token(gid_token)
        except (ValueError, SocialAccount.DoesNotExist) as err:
            return JsonResponse(
                {"error": "{0}".format(err)}, status=status.HTTP_403_FORBIDDEN
            )

    # TODO: (mwfarb) fix me
    # if not username:
    #     return JsonResponse(
    #         {"error": "Invalid parameters"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
    #     )

    if user.is_authenticated:
        username = user.username
    else:  # AnonymousUser
        username = request.POST.get("username", None)

    # produce nonce with 32-bits secure randomness
    nonce = str(secrets.randbits(32))
    # define user object_ids server-side to prevent spoofing
    userid = camid = ctrlid1 = ctrlid2 = None
    if _field_requested(request, "userid"):
        userid = f"{nonce}_{username}"
    if _field_requested(request, "camid"):
        camid = f"camera_{nonce}_{username}"
    if _field_requested(request, "ctrlid1"):
        ctrlid1 = f"viveLeft_{nonce}_{username}"
    if _field_requested(request, "ctrlid2"):
        ctrlid2 = f"viveRight_{nonce}_{username}"
    token = generate_mqtt_token(
        user=user,
        username=username,
        realm=request.POST.get("realm", "realm"),
        scene=request.POST.get("scene", None),
        camid=camid,
        userid=userid,
        ctrlid1=ctrlid1,
        ctrlid2=ctrlid2,
    )
    if not token:
        return JsonResponse(
            {"error": "Authentication required for this scene."}, status=status.HTTP_403_FORBIDDEN
        )
    data = {
        "username": username,
        "token": token.decode("utf-8"),
        "ids": {},
    }
    if userid:
        data["ids"]["userid"] = userid
    if camid:
        data["ids"]["camid"] = camid
    if ctrlid1:
        data["ids"]["ctrlid1"] = ctrlid1
    if ctrlid2:
        data["ids"]["ctrlid2"] = ctrlid2
    response = HttpResponse(json.dumps(data), content_type="application/json")
    response.set_cookie(
        "mqtt_token",
        token.decode("utf-8"),
        max_age=86400000,
        httponly=True,
        secure=True,
    )
    return response
