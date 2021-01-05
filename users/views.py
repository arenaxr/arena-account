import base64
import datetime
import json
import os

import jwt
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

from .forms import NewUserForm, SocialSignupForm, UpdateStaffForm
from .models import Scene

STAFF_ACCTNAME = "scene"


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


def update_staff(request):
    # update staff status if allowed
    if request.method != 'POST':
        return JsonResponse({}, status=400)
    form = UpdateStaffForm(request.POST)
    if form.is_valid() and request.user.is_authenticated:
        staff_username = form.cleaned_data['staff_username']
        is_staff = form.cleaned_data['is_staff']
        if request.user.is_authenticated and request.user.is_superuser and User.objects.filter(username=staff_username).exists():
            print(f"Setting user {staff_username}, is_staff={is_staff}")
            user = User.objects.get(username=staff_username)
            user.is_staff = is_staff
            user.save()

    return redirect("user_profile")


def user_profile(request):
    # load list of scenes this user can edit
    # load updated list of staff users
    scenes = None
    staff = None
    if request.user.is_staff:  # admin/staff
        scenes = Scene.objects.all()
        staff = User.objects.filter(is_staff=True)
    elif request.user.is_authenticated:  # google/github
        scenes = Scene.objects.filter(editors=request.user)
    return render(request=request, template_name="users/user_profile.html",
                  context={"user": request.user, "scenes": scenes, "staff": staff})


def login_callback(request):
    return render(request=request, template_name="users/login_callback.html")


def socialaccount_signup(request):
    form = SocialSignupForm()
    return render(request, "users/social_signup.html", {"form": form})


def user_state(request):
    if request.method != 'POST':
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


def mqtt_token(request):
    if request.method != 'POST':
        return JsonResponse({}, status=400)

    if request.user.is_authenticated:
        username = request.user.username
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
    if request.user.is_authenticated:
        subs.append(f"{realm}/s/#")
        if request.user.is_staff:
            # staff/admin have rights to all scene objects
            pubs.append(f"{realm}/s/#")
        else:
            # scene owners have rights to their scene objects only
            pubs.append(f"{realm}/s/{username}/#")
            scenes = Scene.objects.filter(editors=request.user)
            for scene in scenes:
                pubs.append(f"{realm}/s/{scene.name}/#")
        pubs.append(f"{realm}/g/a/#")
    if scene:
        # anon/non-owners have rights to view scene objects only
        subs.append(f"{realm}/s/{scene}/#")
        if camid:  # probable web browser write
            pubs.append(f"{realm}/s/{scene}/{camid}")
            pubs.append(f"{realm}/s/{scene}/{camid}/#")
            pubs.append(f"{realm}/g/a/{camid}")
            pubs.append(f"topic/vio/{camid}")
            # TODO: remove later, needed for clicks
            pubs.append(f"{realm}/s/{scene}/#")
        else:  # probable cli client write
            pubs.append(f"{realm}/s/{scene}")
            pubs.append(f"{realm}/s/{scene}/#")
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
    subs.append(f"$NETWORK")
    pubs.append(f"$NETWORK/latency")
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
