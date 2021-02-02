from rest_framework import serializers
from users.models import Scene


class SceneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scene
        fields = [
            'name',
            'summary',
            'editors',
            'creation_date',
            'public_read',
            'public_write',
        ]


class SceneNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scene
        fields = [
            'name',
        ]
