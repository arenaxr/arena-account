from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import (AuthenticationForm, PasswordResetForm,
                                       UserCreationForm)
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import BadHeaderError, send_mail
from django.db.models.query_utils import Q
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .forms import NewUserForm
from .models import Scene


def register_request(request):
    if request.method == "POST":
        form = NewUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful.")
            return redirect("login_callback")
        messages.error(
            request, "Unsuccessful registration. Invalid information.")
    form = NewUserForm
    return render(request=request, template_name="users/register.html", context={"register_form": form})


def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f"New account created: {username}")
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect("login_callback")
        else:
            messages.error(request, "Account creation failed")

    form = UserCreationForm()
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
                        # TODO (mwfarb): update domain for production
                        'domain': '127.0.0.1:8000',
                        'site_name': 'ARENA Website',
                        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                        "user": user,
                        'token': default_token_generator.make_token(user),
                        'protocol': 'http',
                    }
                    email = render_to_string(email_template_name, c)
                    try:  # TODO (mwfarb): update 'from' email for production
                        send_mail(subject, email, 'admin@arena.andrew.cmu.edu',
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
