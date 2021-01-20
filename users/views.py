import base64
import datetime
import json
import os

import coreapi
import coreschema
import jwt
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.views import SignupView
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import (AuthenticationForm, PasswordResetForm,
                                       UserCreationForm)
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import BadHeaderError, send_mail
from django.db.models.query_utils import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from drf_yasg.utils import swagger_auto_schema
from google.auth.transport import requests
from google.oauth2 import id_token
from rest_framework import permissions, response
from rest_framework.compat import coreapi
from rest_framework.decorators import (api_view, permission_classes,
                                       renderer_classes, schema)
from rest_framework.schemas import AutoSchema, ManualSchema

from .forms import (NewSceneForm, NewUserForm, SocialSignupForm,
                    UpdateSceneForm, UpdateStaffForm)
from .models import Scene
from .serializers import SceneSerializer

STAFF_ACCTNAME = "public"


def index(request):
    # index is treated as login
    return redirect("login")


def register_request(request):
    if request.method == "POST":
        form = NewUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            messages.success(request, f"New account created: {username}")
            user = authenticate(username=username, password=password)
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect("login_callback")
        else:
            messages.error(request, "Account creation failed")

    form = NewUserForm()
    return render(request, "users/register.html", {"form": form})


def login_request(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
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
    return render(request=request, template_name="users/login.html", context={"login_form": form})


def logout_request(request):
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect("login")


def password_reset_request(request):
    if request.method == "POST":
        password_reset_form = PasswordResetForm(request.POST)
        if password_reset_form.is_valid():
            data = password_reset_form.cleaned_data['email']
            associated_users = User.objects.filter(Q(email=data))
            if associated_users.exists():
                for user in associated_users:
                    subject = "Password Reset Requested"
                    email_template_name = "users/password/password_reset_email.txt"
                    c = {
                        "email": user.email,
                        'domain': os.environ['HOSTNAME'],
                        'site_name': 'ARENA Website',
                        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                        "user": user,
                        'token': default_token_generator.make_token(user),
                        'protocol': 'https',
                    }
                    email = render_to_string(email_template_name, c)
                    try:
                        send_mail(subject, email, os.environ['EMAIL'],
                                  [user.email], fail_silently=False)
                    except BadHeaderError:
                        return HttpResponse('Invalid header found.')
                    return redirect("/password_reset/done/")
                    # messages.success(
                    #     request, 'A message with reset password instructions has been sent to your inbox.')
                    # return redirect("/")
    password_reset_form = PasswordResetForm()
    return render(request=request, template_name="users/password/password_reset.html", context={"password_reset_form": password_reset_form})


class NewSceneSchema(AutoSchema):
    def __init__(self):
        super(NewSceneSchema, self).__init__()

    def get_manual_fields(self, path, method):
        extra_fields = [
            coreapi.Field("scene", required=True, location="form", type="string",
                          description="The scene name, without slash '/' or namespace."),
            coreapi.Field("is_public", required=False, location="form", type="boolean",
                          description="True to use 'public' namespace, False for user namespace."),
        ]
        manual_fields = super().get_manual_fields(path, method)
        return manual_fields + extra_fields


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@schema(NewSceneSchema())  # TODO: schema not working yet
def new_scene(request):
    """
    Add a new scene to the known scenes table, either 'public' or user namespaced.
    """
    # add new scene editor
    if request.method != 'POST':
        return JsonResponse({}, status=400)
    form = NewSceneForm(request.POST)
    if not request.user.is_authenticated:
        return JsonResponse({'error': f"Not authenticated."}, status=403)
    if not form.is_valid():
        return JsonResponse({'error': f"Invalid parameters"}, status=500)
    username = request.user.username
    scene = form.cleaned_data['scene']
    is_public = form.cleaned_data['is_public']
    if scene in settings.USERNAME_RESERVED:
        return JsonResponse({'error': f"Rejecting reserved name for scene: {scene}"}, status=400)
    if is_public and request.user.is_staff:
        scene = f'{STAFF_ACCTNAME}/{scene}'  # public namespace
    else:
        scene = f'{username}/{scene}'  # user namespace for normal users
    if Scene.objects.filter(name=scene).exists():
        return JsonResponse({'error': f"Unable to claim existing scene: {scene}, use admin panel"}, status=400)
    if User.objects.filter(username=username).exists():
        s = Scene(name=scene,
                  summary=f'User {username} adding new scene {scene} to account database.')
        s.save()

    return redirect("user_profile")


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def update_scene(request):
    """
    Update existing scene permissions the user has access to.
    """
    if request.method != 'POST':
        return JsonResponse({}, status=400)
    form = UpdateSceneForm(request.POST)
    if not request.user.is_authenticated:
        return JsonResponse({'error': f"Not authenticated."}, status=403)
    if not form.is_valid():
        return JsonResponse({'error': f"Invalid parameters"}, status=500)
    username = request.user.username
    name = form.cleaned_data['name']
    public_read = form.cleaned_data['public_read']
    public_write = form.cleaned_data['public_write']
    if not Scene.objects.filter(name=name).exists():
        return JsonResponse({'error': f"Unable to update existing scene: {name}, not found"}, status=500)
    scene = Scene.objects.get(name=name)
    if scene not in user_scenes(request):
        return JsonResponse({'error': f"User does not have permission for: {name}."}, status=400)
    scene.public_read = public_read
    scene.public_write = public_write
    scene.save()

    return redirect("user_profile")


@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def update_staff(request):
    """
    Toggle the user's is_staff true/false status.
    """
    # update staff status if allowed
    if request.method != 'POST':
        return JsonResponse({}, status=400)
    form = UpdateStaffForm(request.POST)
    if not request.user.is_authenticated:
        return JsonResponse({'error': f"Not authenticated."}, status=403)
    if not form.is_valid():
        return JsonResponse({'error': f"Invalid parameters"}, status=500)
    staff_username = form.cleaned_data['staff_username']
    is_staff = form.cleaned_data['is_staff']
    if request.user.is_superuser and User.objects.filter(username=staff_username).exists():
        print(f"Setting user {staff_username}, is_staff={is_staff}")
        user = User.objects.get(username=staff_username)
        user.is_staff = is_staff
        user.save()

    return redirect("user_profile")


@api_view(['GET'])
def my_scenes(request):
    """
    Request a list of scenes this user can write to.
    """
    if request.method != 'GET':
        return JsonResponse({}, status=400)
    serializer = SceneSerializer(user_scenes(request), many=True)
    return JsonResponse(serializer.data, safe=False)


def user_scenes(request):
    # load list of scenes this user can edit
    scenes = Scene.objects.none()
    ext_scenes = Scene.objects.none()
    if request.user.is_staff:  # admin/staff
        scenes = Scene.objects.all()
    elif request.user.is_authenticated:  # standard user
        scenes = Scene.objects.filter(
            name__startswith=f'{request.user.username}/')
        ext_scenes = Scene.objects.filter(editors=request.user)
        # merge 'my' namespaced scenes and extras scenes granted
    return (scenes | ext_scenes).order_by('name')


def user_profile(request):
    # load updated list of staff users
    scenes = user_scenes(request)
    staff = None
    if request.user.is_staff:  # admin/staff
        staff = User.objects.filter(is_staff=True)
    return render(request=request, template_name="users/user_profile.html",
                  context={"user": request.user, "scenes": scenes, "staff": staff})


def login_callback(request):
    return render(request=request, template_name="users/login_callback.html")


def socialaccount_signup(request):
    form = SocialSignupForm()
    return render(request, "users/social_signup.html", {"form": form})


@api_view(['GET'])
def user_state(request):
    """
    Request the user's authenticated status, username, name, email.
    """
    if request.method != 'GET':
        return JsonResponse({}, status=400)
    if request.user.is_authenticated:
        # TODO: should also lookup social account link
        if request.user.username.startswith("admin"):
            authType = "arena"
        else:
            authType = "google"

        return JsonResponse({
            "authenticated": request.user.is_authenticated,
            "username": request.user.username,
            "fullname": request.user.get_full_name(),
            "email": request.user.email,
            "type": authType,
        }, status=200)
    else:  # AnonymousUser
        return JsonResponse({
            "authenticated": request.user.is_authenticated,
        }, status=200)


class MqttTokenSchema(AutoSchema):
    def __init__(self):
        super(MqttTokenSchema, self).__init__()

    def get_manual_fields(self, path, method):
        extra_fields = [
            coreapi.Field("username", required=True, location="body", type="string",
                          description="ARENA user database username, or like 'anonymous-[name]'."),
            coreapi.Field("id_token", required=False, location="body", type="string",
                          description="JWT id_token from social account authentication service, \
                                    if forwarding from remote client like arena-py."),
            coreapi.Field("realm", required=False, location="body", type="string",
                          description="Name of the ARENA realm used in the topic string (default: 'realm')."),
            coreapi.Field("scene", required=False, location="body", type="string",
                          description="Name of the ARENA scene: '[namespace]/[scene]'."),
            coreapi.Field("userid", required=False, location="body", type="string",
                          description="Name of the user's ARENA web client id."),
            coreapi.Field("camid", required=False, location="body", type="string",
                          description="Name of the user's ARENA camera object id."),
            coreapi.Field("ctrlid1", required=False, location="body", type="string",
                          description="Name of the user's ARENA controller object 1, like vive left."),
            coreapi.Field("ctrlid2", required=False, location="body", type="string",
                          description="Name of the user's ARENA controller object 2, like vive right."),
        ]
        manual_fields = super().get_manual_fields(path, method)
        return manual_fields + extra_fields


@api_view(['POST'])
@schema(MqttTokenSchema())  # TODO: schema not working yet
def mqtt_token(request):
    """
    Request a MQTT JWT token with permissions for an anonymous or authenticated user given incoming parameters.
    """
    if request.method != 'POST':
        return JsonResponse({}, status=400)

    user = request.user
    gid_token = request.POST.get("id_token", None)
    if gid_token:
        gclient_ids = [os.environ['GAUTH_CLIENTID'],
                       os.environ['GAUTH_INSTALLED_CLIENTID']]
        try:
            idinfo = id_token.verify_oauth2_token(
                gid_token, requests.Request())
            if idinfo['aud'] not in gclient_ids:
                raise ValueError('Could not verify audience.')
            # ID token is valid. Get the user's Google Account ID from the decoded token.
            userid = idinfo['sub']
        except ValueError as err:
            return JsonResponse({"error": "{0}".format(err)}, status=403)
        g_users = SocialAccount.objects.filter(uid=userid)
        if len(g_users) != 1:
            return JsonResponse({"error": "Database error"}, status=400)
        try:
            user = User.objects.get(username=g_users[0].user)
        except User.DoesNotExist:
            return JsonResponse({"error": "Website login required first"}, status=403)

    if user.is_authenticated:
        username = user.username
    else:  # AnonymousUser
        username = request.POST.get("username", None)

    realm = request.POST.get("realm", "realm")
    scene = request.POST.get("scene", None)
    camid = request.POST.get("camid", None)
    userid = request.POST.get("userid", None)
    ctrlid1 = request.POST.get("ctrlid1", None)
    ctrlid2 = request.POST.get("ctrlid2", None)
    subs = []
    pubs = []

    privkeyfile = settings.MQTT_TOKEN_PRIVKEY
    with open(privkeyfile) as privatefile:
        private_key = privatefile.read()
    payload = {
        'sub': username,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1),
    }
    # user presence objects
    subs.append(f"{realm}/g/a/#")
    if user.is_authenticated:
        pubs.append(f"{realm}/g/a/#")
        if user.is_staff:
            # staff/admin have rights to all scene objects
            subs.append(f"{realm}/s/#")
            pubs.append(f"{realm}/s/#")
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
            # did the user request sub or pub to be private?
            scene_opt = Scene.objects.get(name=scene)
            if scene_opt.public_read:
                subs.append(f"{realm}/s/{scene}/#")
            if scene_opt.public_write:
                # TODO (mwfarb): publishing objects and object events should be separated in topics
                pubs.append(f"{realm}/s/{scene}/#")
        else:
            # otherwise, assume public access to scene, fail open
            subs.append(f"{realm}/s/{scene}/#")
            # TODO (mwfarb): publishing objects and object events should be separated in topics
            pubs.append(f"{realm}/s/{scene}/#")
        if camid:  # probable web browser write
            pubs.append(f"{realm}/s/{scene}/{camid}")
            pubs.append(f"{realm}/s/{scene}/{camid}/#")
            pubs.append(f"{realm}/g/a/{camid}")
            pubs.append(f"topic/vio/{camid}")
        else:  # probable cli client write
            pubs.append(f"{realm}/s/{scene}")
        if ctrlid1:
            pubs.append(f"{realm}/s/{scene}/{ctrlid1}")
        if ctrlid2:
            pubs.append(f"{realm}/s/{scene}/{ctrlid2}")
    # chat messages
    if userid:
        userhandle = userid + base64.b64encode(userid.encode()).decode()
        # receive private messages: Read
        subs.append(f"{realm}/g/c/p/{userhandle}")
        # receive open messages to everyone and/or scene: Read
        subs.append(f"{realm}/g/c/o/#")
        # send open messages (chat keepalive, messages to all/scene): Write
        pubs.append(f"{realm}/g/c/o/{userhandle}")
        # private messages to user: Write
        pubs.append(f"{realm}/g/c/p/+/{userhandle}")
    # runtime
    subs.append(f"{realm}/proc/#")
    pubs.append(f"{realm}/proc/#")
    # network graph
    subs.append("$NETWORK")
    pubs.append("$NETWORK/latency")
    if len(subs) > 0:
        subs.sort()
        payload['subs'] = subs
    if len(pubs) > 0:
        pubs.sort()
        payload['publ'] = pubs
    token = jwt.encode(payload, private_key, algorithm='RS256')
    response = HttpResponse(json.dumps({
        "username": username,
        "token": token.decode("utf-8"),
    }), content_type='application/json')
    response.set_cookie('mqtt_token', token.decode("utf-8"), max_age=86400000,
                        httponly=True, secure=True)
    return response
