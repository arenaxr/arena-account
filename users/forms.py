from datetime import date as datetime_date

from allauth.account.forms import SignupForm as _SignupForm
from allauth.socialaccount.forms import SignupForm as _SocialSignupForm
from django import forms
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import Scene


# class GoogleSignUpForm(SignupForm):
#     privacy_policy = forms.BooleanField(
#         required=True,
#         label=('I accept the privacy policy and rules '),
#         help_text=(
#             'You need to accept this to proceed with setting-up your account')
#     )

#     #def __init__(self, sociallogin=None, **kwargs):
#         #super(GoogleSignUpForm, self).__init__(**kwargs)
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)

#         terms_and_conditions = reverse_lazy('privacy')
#         self.fields['privacy_policy'].label = mark_safe((
#             "I have read and agree with the "
#             "<a href='%s'>Terms and Conditions</a>")) % (
#             terms_and_conditions)

#     def save(self):
#         user = super(GoogleSignUpForm, self).save()
#         return user

class SocialSignupForm(_SocialSignupForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.sociallogin and \
           self.sociallogin.account.provider in ('google'):
            name = self.sociallogin.account.extra_data['email'].split('@')[0]
            self.fields['username'].widget.attrs.update({'value': name})

    # TODO: (mwfarb): reject usernames in form on signup: settings.USERNAME_RESERVED:

    # def save(self):
    #     user = super(SocialSignupForm, self).save()
    #     return user


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
