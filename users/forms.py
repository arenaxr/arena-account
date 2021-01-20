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
    name = forms.CharField(
        label='name',
        required=True)
    public_read = forms.BooleanField(
        label='public_read',
        required=False,
        initial=True)
    public_write = forms.BooleanField(
        label='public_write',
        required=False,
        initial=True)
