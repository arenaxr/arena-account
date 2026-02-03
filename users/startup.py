import os

from allauth.socialaccount.models import SocialApp
from django.conf import settings
from django.contrib.sites.models import Site
from users.models import (
    SCENE_ANON_USERS_DEF,
    SCENE_PUBLIC_READ_DEF,
    SCENE_PUBLIC_WRITE_DEF,
    SCENE_USERS_DEF,
    SCENE_VIDEO_CONF_DEF,
    Scene,
)


from users.persist_db import get_persist_db

def setup_databases():
    # Force db connection
    get_persist_db()

    # Sites db must have a SITE_ID row that equals our host
    host = os.getenv("HOSTNAME")
    site_id = settings.SITE_ID
    # check that site_id has correct host
    id_inst = Site.objects.filter(id=site_id)
    if id_inst.exists():
        id_inst = Site.objects.get(id=site_id)
        if id_inst.domain != host:
            # check that another site is not using our host, remove
            host_inst = Site.objects.filter(domain=host)
            if host_inst.exists():
                count, _ = host_inst.delete()
                if count > 0:
                    print(f"Deleted Site entries matching host: {count}")
            # update proper site_id with host
            id_inst.name = host
            id_inst.domain = host
            id_inst.save()
    else:
        id_inst = Site(id=site_id, name=host, domain=host)
        id_inst.save()

    # social apps are defined in settings.py, so remove legacy allauth entires that might conflict
    count, _ = SocialApp.objects.filter(provider='google').delete()
    if count > 0:
        print(f"Deleted legacy SocialApp entries: {count}")

    # check for scene permissions where Scene.is_default is True and remove them
    count, _ = Scene.objects.filter(
        public_read=SCENE_PUBLIC_READ_DEF,
        public_write=SCENE_PUBLIC_WRITE_DEF,
        anonymous_users=SCENE_ANON_USERS_DEF,
        video_conference=SCENE_VIDEO_CONF_DEF,
        users=SCENE_USERS_DEF,
        editors__isnull=True,
        viewers__isnull=True,
    ).delete()
    if count > 0:
        print(f"Deleted redundant default Scene permission entries: {count}")
