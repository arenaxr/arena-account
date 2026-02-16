from datetime import datetime
from typing import List, Optional

from ninja import Schema


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
    public_read: bool = False
    public_write: bool = False
    anonymous_users: bool = False
    video_conference: bool = False
    users: bool = False


class SceneNameSchema(Schema):
    name: str
