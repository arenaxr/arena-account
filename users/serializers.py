from django.contrib.auth.models import User
from rest_framework import serializers

from users.models import Scene


class SceneSerializer(serializers.ModelSerializer):
    editors = serializers.SlugRelatedField(
        queryset=User.objects.all(),
        many=True,
        slug_field='username'
    )

    class Meta:
        model = Scene
        fields = [
            "name",
            "summary",
            "editors",
            "creation_date",
            "public_read",
            "public_write",
            "anonymous_users",
            "video_conference",
            "users",
            "namespace",
        ]


class SceneNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scene
        fields = [
            "name",
        ]
