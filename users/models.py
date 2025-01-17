from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.urls import reverse

# Scene permissions defaults
SCENE_PUBLIC_READ_DEF = True
SCENE_PUBLIC_WRITE_DEF = False
SCENE_ANON_USERS_DEF = True
SCENE_VIDEO_CONF_DEF = True
SCENE_USERS_DEF = True

RE_NS = r"^[a-zA-Z0-9_-]*$"
RE_NS_SLASH_ID = r"^[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+$"

ns_regex = RegexValidator(RE_NS, "Only alphanumeric, underscore, hyphen allowed.")
ns_slash_id_regex = RegexValidator(
    RE_NS_SLASH_ID, "Only alphanumeric, underscore, hyphen, in namespace/idname format allowed."
)


class NamespaceDefault:
    def __init__(self, name=""):
        self.name = name
        self.owners = []
        self.editors = []
        self.viewers = []

    def __getitem__(self, item):
        return getattr(self, item)


class Namespace(models.Model):
    """Model representing a namespace's permissions."""

    name = models.CharField(max_length=100, blank=False, unique=True, validators=[ns_regex])
    owners = models.ManyToManyField(User, blank=True, related_name="namespace_owners")
    editors = models.ManyToManyField(User, blank=True, related_name="namespace_editors")
    viewers = models.ManyToManyField(User, blank=True, related_name="namespace_viewers")

    def save(self, *args, **kwargs):
        self.full_clean()  # performs regular validation then clean()
        super(Namespace, self).save(*args, **kwargs)

    def clean(self):
        if self.name == "":
            raise ValidationError("Empty namespace name!")
        self.name = self.name.strip()

    def __str__(self):
        """String for representing the namespace object by name."""
        return self.name

    @property
    def is_default(self):
        return self.editors.count() == 0 and self.viewers.count() == 0


class Scene(models.Model):
    """Model representing a namespace/scene's permissions."""

    name = models.CharField(max_length=200, blank=False, unique=True, validators=[ns_slash_id_regex])
    summary = models.TextField(max_length=1000, blank=True)
    owners = models.ManyToManyField(User, blank=True, related_name="scene_owners")
    editors = models.ManyToManyField(User, blank=True, related_name="scene_editors")
    viewers = models.ManyToManyField(User, blank=True, related_name="scene_viewers")
    creation_date = models.DateTimeField(auto_now_add=True)
    public_read = models.BooleanField(default=SCENE_PUBLIC_READ_DEF, blank=True)
    public_write = models.BooleanField(default=SCENE_PUBLIC_WRITE_DEF, blank=True)
    anonymous_users = models.BooleanField(default=SCENE_ANON_USERS_DEF, blank=True)
    video_conference = models.BooleanField(default=SCENE_VIDEO_CONF_DEF, blank=True)
    users = models.BooleanField(default=SCENE_USERS_DEF, blank=True)

    def save(self, *args, **kwargs):
        self.full_clean()  # performs regular validation then clean()
        super(Scene, self).save(*args, **kwargs)

    def clean(self):
        if self.name == "":
            raise ValidationError("Empty namespace/scene name!")
        self.name = self.name.strip()

    def __str__(self):
        """String for representing the scene object by name."""
        return self.name

    def get_absolute_url(self):
        """Returns the url to access a detail record for this scene."""
        return reverse("scene-detail", args=[str(self.name)])

    @property
    def namespace(self):
        return self.name.split("/")[0]

    @property
    def sceneid(self):
        return self.name.split("/")[1]

    @property
    def is_default(self):
        return (
            self.public_read is SCENE_PUBLIC_READ_DEF
            and self.public_write is SCENE_PUBLIC_WRITE_DEF
            and self.anonymous_users is SCENE_ANON_USERS_DEF
            and self.video_conference is SCENE_VIDEO_CONF_DEF
            and self.users is SCENE_USERS_DEF
            and self.editors.count() == 0
            and self.viewers.count() == 0
        )


class Device(models.Model):
    """Model representing a namespace/device's permissions."""

    name = models.CharField(max_length=200, blank=False, unique=True, validators=[ns_slash_id_regex])
    summary = models.TextField(max_length=1000, blank=True)
    creation_date = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.full_clean()  # performs regular validation then clean()
        super(Device, self).save(*args, **kwargs)

    def clean(self):
        if self.name == "":
            raise ValidationError("Empty namespace/device name!")
        self.name = self.name.strip()

    def __str__(self):
        """String for representing the device object by name."""
        return self.name

    @property
    def namespace(self):
        return self.name.split("/")[0]

    @property
    def deviceid(self):
        return self.name.split("/")[1]
