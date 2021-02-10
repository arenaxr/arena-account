from allauth.socialaccount.forms import SignupForm as _SocialSignupForm
from django import forms
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


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


class NewUserForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "email",
            "username",
            "password1",
            "password2",
        )


class UpdateStaffForm(forms.Form):
    staff_username = forms.CharField(label="staff_username", required=True)
    is_staff = forms.BooleanField(label="is_staff", required=False, initial=False)


class NewSceneForm(forms.Form):
    scene = forms.CharField(label="scene", required=True)
    is_public = forms.BooleanField(label="is_public", required=False, initial=False)


class UpdateSceneForm(forms.Form):
    save = forms.CharField(label="save", required=False)
    delete = forms.CharField(label="delete", required=False)
    public_read = forms.BooleanField(label="public_read", required=False, initial=True)
    public_write = forms.BooleanField(
        label="public_write", required=False, initial=True
    )
