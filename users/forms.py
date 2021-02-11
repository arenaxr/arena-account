from allauth.socialaccount.forms import SignupForm as _SocialSignupForm
from django import forms
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.forms import ModelForm

from .models import Scene


class SocialSignupForm(_SocialSignupForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.sociallogin and self.sociallogin.account.provider in ("google"):
            name = self.sociallogin.account.extra_data["email"].split("@")[0]
            self.fields["username"].widget.attrs.update({"value": name})

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        # reject usernames in form on signup: settings.USERNAME_RESERVED
        if username in settings.USERNAME_RESERVED:
            msg = f"Sorry, {username} is a reserved word for usernames."
            self.add_error("username", msg)


class UpdateStaffForm(forms.Form):
    staff_username = forms.CharField(label="staff_username", required=True)
    is_staff = forms.BooleanField(
        label="is_staff", required=False, initial=False)


class UpdateSceneForm(forms.Form):
    edit = forms.CharField(label="edit", required=False)


class SceneForm(forms.ModelForm):
    editors = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.SelectMultiple(attrs={"class": "form-select"}), required=False)
    public_read = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}), required=False)
    public_write = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}), required=False)
    anonymous_users = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}), required=False)

    class Meta:
        model = Scene
        fields = ("public_read", "public_write", "anonymous_users", "editors")
