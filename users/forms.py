from allauth.account.forms import PasswordField, SetPasswordField
from allauth.socialaccount.forms import SignupForm
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Scene


class NewUserForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email',
                  'username', 'password1', 'password2')


class SocialSignupForm(SignupForm):

    def __init__(self, **kwargs):
        super(SocialSignupForm, self).__init__(**kwargs)

    def save(self, request):
        # Ensure you call the parent class's save.
        # .save() returns a User object.
        user = super(SocialSignupForm, self).save(request)
        # Add your own processing here.
        # You must return the original result.
        return user


class UpdateStaffForm(forms.Form):
    staff_username = forms.CharField(
        label='staff_username',
        required=True)
    is_staff = forms.BooleanField(
        label='is_staff',
        required=False,
        initial=False)


class NewSceneForm(forms.Form):
    scene = forms.CharField(
        label='scene',
        required=True)
    is_public = forms.BooleanField(
        label='is_public',
        required=False,
        initial=False)


class UpdateSceneForm(forms.Form):
    save = forms.CharField(
        label='save',
        required=False)
    delete = forms.CharField(
        label='delete',
        required=False)
    public_read = forms.BooleanField(
        label='public_read',
        required=False,
        initial=True)
    public_write = forms.BooleanField(
        label='public_write',
        required=False,
        initial=True)
