from django.contrib.auth.models import User
from rest_framework import serializers
from users.models import Namespace, Scene


class NamespaceSerializer(serializers.ModelSerializer):
    editors = serializers.SlugRelatedField(queryset=User.objects.all(), many=True, slug_field="username")
    viewers = serializers.SlugRelatedField(queryset=User.objects.all(), many=True, slug_field="username")

    class Meta:
        model = Namespace
        fields = [
            "name",
            "editors",
            "viewers",
        ]


class NamespaceNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Namespace
        fields = [
            "name",
        ]


class SceneSerializer(serializers.ModelSerializer):
    editors = serializers.SlugRelatedField(queryset=User.objects.all(), many=True, slug_field="username")
    viewers = serializers.SlugRelatedField(queryset=User.objects.all(), many=True, slug_field="username")

    class Meta:
        model = Scene
        fields = [
            "name",
            "summary",
            "editors",
            "viewers",
            "creation_date",
            "public_read",
            "public_write",
            "anonymous_users",
            "video_conference",
            "users",
        ]


class SceneNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scene
        fields = [
            "name",
        ]
