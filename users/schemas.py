from datetime import datetime
from typing import List, Optional

from ninja import Schema

from users.models import (
    SCENE_ANON_USERS_DEF,
    SCENE_PUBLIC_READ_DEF,
    SCENE_PUBLIC_WRITE_DEF,
    SCENE_USERS_DEF,
    SCENE_VIDEO_CONF_DEF,
)


class NamespaceSchema(Schema):
    name: str
    editors: List[str] = []
    viewers: List[str] = []


class NamespaceNameSchema(Schema):
    name: str


class SceneSchema(Schema):
    name: str
    summary: Optional[str] = None
    editors: List[str] = []
    viewers: List[str] = []
    creation_date: Optional[datetime] = None
    public_read: bool = SCENE_PUBLIC_READ_DEF
    public_write: bool = SCENE_PUBLIC_WRITE_DEF
    anonymous_users: bool = SCENE_ANON_USERS_DEF
    video_conference: bool = SCENE_VIDEO_CONF_DEF
    users: bool = SCENE_USERS_DEF


class SceneNameSchema(Schema):
    name: str
