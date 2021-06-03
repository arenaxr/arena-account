from allauth.socialaccount.forms import SignupForm as _SocialSignupForm
from dal import autocomplete, forward
from django import forms
from django.conf import settings
from django.contrib.auth.models import User

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


class UpdateSceneForm(forms.Form):
    edit = forms.CharField(label="edit", required=False)


class SceneForm(forms.ModelForm):
    editors = forms.ModelMultipleChoiceField(
        queryset=User.objects.all().order_by('username'),
        widget=autocomplete.ModelSelect2Multiple(
            url='user-autocomplete',
            forward=(forward.Self(), ),
            attrs={'data-minimum-input-length': 2},
        ), required=False)
    public_read = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}), required=False)
    public_write = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}), required=False)
    anonymous_users = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}), required=False)
    video_conference = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}), required=False)

    class Meta:
        model = Scene
        fields = ("public_read", "public_write",
                  "anonymous_users", "video_conference", "editors")
