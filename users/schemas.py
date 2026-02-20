from datetime import datetime
from typing import List, Optional

from ninja import Field, Schema
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
    name: str = Field(..., description="Namespaced Scene name: 'ns/sn'.")
    summary: Optional[str] = Field(None, description="Description of the scene permissions.")
    editors: List[str] = Field(
        [], description="List of users with edit permission."
    )
    viewers: List[str] = Field(
        [], description="List of users with view permission."
    )
    creation_date: Optional[datetime] = Field(
        None, description="Creation date of the scene permissions."
    )
    public_read: bool = Field(
        SCENE_PUBLIC_READ_DEF, description="Public read permission."
    )
    public_write: bool = Field(
        SCENE_PUBLIC_WRITE_DEF, description="Public write permission."
    )
    anonymous_users: bool = Field(
        SCENE_ANON_USERS_DEF, description="Allow anonymous users."
    )
    video_conference: bool = Field(
        SCENE_VIDEO_CONF_DEF, description="Enable video conference."
    )
    users: bool = Field(SCENE_USERS_DEF, description="Enable user interactions.")


class SceneNameSchema(Schema):
    name: str


class MQTTAuthRequestSchema(Schema):
    id_token: Optional[str] = Field(None, description="ID token for authentication.")
    username: Optional[str] = Field(None, description="ARENA account username, only used for anonymous.")
    id_auth: Optional[str] = Field(None, description="Authentication type: 'google' or 'anonymous'.")
    realm: Optional[str] = Field(None, description="ARENA realm.")
    scene: Optional[str] = Field(None, description="ARENA namespaced scene name: 'ns/sn'.")
    client:  Optional[str] = Field(None, description="Client type for reference, e.g. 'webScene', 'py1.2.3', 'unity'.")
    camid:  Optional[bool] = Field(False, description="Request permission for camera object.")
    handleftid:  Optional[bool] = Field(False, description="Request permission for left controller object.")
    handrightid:  Optional[bool] = Field(False, description="Request permission for right controller object.")
    renderfusionid:  Optional[bool] = Field(False, description="Request render-fusion host permission.")
    environmentid:  Optional[bool] = Field(False, description="Request environment host permission.")
