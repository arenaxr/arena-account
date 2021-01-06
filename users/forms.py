from allauth.account.forms import PasswordField, SetPasswordField
from allauth.socialaccount.forms import SignupForm
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


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
    staff_username = forms.CharField()
    is_staff = forms.BooleanField()


class NewSceneForm(forms.Form):
    username = forms.CharField()
    scene = forms.CharField()
