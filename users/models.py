from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse

# Scene permissions defaults
SCENE_PUBLIC_READ_DEF = True
SCENE_PUBLIC_WRITE_DEF = False
SCENE_ANON_USERS_DEF = True
SCENE_VIDEO_CONF_DEF = True
SCENE_USERS_DEF = True


class ArenaUser(models.Model):
    """Model representing ARENA app specific user data outside the User model."""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    editors = models.ManyToManyField(User, related_name='editors', blank=True)
    owners = models.ManyToManyField(User, related_name='owners', blank=True)
    creation_date = models.DateTimeField(auto_now_add=True)


class Scene(models.Model):
    """Model representing a scene's permissions."""

    name = models.CharField(max_length=200, blank=False, unique=True)
    summary = models.TextField(max_length=1000, blank=True)
    editors = models.ManyToManyField(User, blank=True)
    creation_date = models.DateTimeField(auto_now_add=True)
    public_read = models.BooleanField(
        default=SCENE_PUBLIC_READ_DEF, blank=True)
    public_write = models.BooleanField(
        default=SCENE_PUBLIC_WRITE_DEF, blank=True)
    anonymous_users = models.BooleanField(
        default=SCENE_ANON_USERS_DEF, blank=True)
    video_conference = models.BooleanField(
        default=SCENE_VIDEO_CONF_DEF, blank=True)
    users = models.BooleanField(
        default=SCENE_USERS_DEF, blank=True)

    def save(self, *args, **kwargs):
        self.full_clean()  # performs regular validation then clean()
        super(Scene, self).save(*args, **kwargs)

    def clean(self):
        if self.name == "":
            raise ValidationError("Empty scene name!")
        self.name = self.name.strip()

    def __str__(self):
        """String for representing the scene object by name."""
        return self.name

    @property
    def namespace(self):
        return self.name.split("/")[0]


class Device(models.Model):
    """Model representing a device's permissions."""

    name = models.CharField(max_length=200, blank=False, unique=True)
    summary = models.TextField(max_length=1000, blank=True)
    creation_date = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.full_clean()  # performs regular validation then clean()
        super(Device, self).save(*args, **kwargs)

    def clean(self):
        if self.name == "":
            raise ValidationError("Empty device name!")
        self.name = self.name.strip()

    def __str__(self):
        """String for representing the device object by name."""
        return self.name

    @property
    def namespace(self):
        return self.name.split("/")[0]
