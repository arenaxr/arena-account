import datetime
import os

import jwt
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

from .forms import NewUserForm
from .models import Scene


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


def user_profile(request, username):
    user = User.objects.get(username=username)
    return render(request=request, template_name="users/user_profile.html", context={"user": user})


def login_callback(request):
    return render(request=request, template_name="users/login_callback.html")


def user_state(request):
    if request.method != 'POST':
        return JsonResponse({}, status=400)
    if request.user.is_authenticated:
        return JsonResponse({
            "authenticated": request.user.is_authenticated,
            "username": request.user.username,
            "fullname": request.user.get_full_name(),
            "email": request.user.email,
            "type": "email",  # TODO: should also lookup social account link
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

    secret = os.environ['SECRET_KEY_BASE64']
    payload = {
        'sub': username,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1),
    }
    # user presence objects
    subs.append(f"{realm}/s/#")
    subs.append(f"{realm}/g/a/#")
    if request.user.is_authenticated and request.user.is_staff:
        pubs.append(f"{realm}/s/#")
    else:  # AnonymousUser
        if camid:
            pubs.append(f"{realm}/s/{scene}/{camid}/#")
            pubs.append(f"{realm}/g/a/{camid}/#")
            pubs.append(f"topic/vio/{camid}/#")
        if ctrlid1:
            pubs.append(f"{realm}/s/{scene}/{ctrlid1}/#")
        if ctrlid2:
            pubs.append(f"{realm}/s/{scene}/{ctrlid2}/#")
    # runtime
    pubs.append(f"{realm}/proc/#")
    subs.append(f"{realm}/proc/#")
    # network graph
    pubs.append("$NETWORK/#")
    subs.append("$NETWORK/#")
    # chat messages
    if userid:
        # receive private messages: Read
        subs.append(f"{realm}/g/c/p/{userid}/#")
        # receive open messages to everyone and/or scene: Read
        subs.append(f"{realm}/g/c/o/#")
        # send open messages (chat keepalive, messages to all/scene): Write
        pubs.append(f"{realm}/g/c/o/{userid}")
        # private messages to user: Write
        pubs.append(f"{realm}/g/c/p/+/{userid}")
    if len(subs) > 0:
        payload['subs'] = subs
    if len(pubs) > 0:
        payload['publ'] = pubs
    token = jwt.encode(payload, secret, algorithm='HS256')
    return JsonResponse({
        "username": username,
        "token": token.decode("utf-8"),
    }, status=200)
