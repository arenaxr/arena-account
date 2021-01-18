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


class SceneListForm(forms.ModelForm):
    editors = forms.ModelMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple(),
        required=False,
        label='',
        help_text='Selection is not required',
        queryset=User.objects.all().order_by('username'))

    class Meta:
        model = Scene
        fields = ['editors', 'public_read', 'public_write']
        #labels = {'post_subject': 'Post subject'}
