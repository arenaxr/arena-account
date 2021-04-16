import logging
import os

from django.conf import settings
from django.contrib.sites.models import Site

logger = logging.getLogger(__name__)
logger.info("startup.py load test...")


def setup_socialapps():
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
                host_inst.delete()
            # update proper site_id with host
            id_inst.name = host
            id_inst.domain = host
            id_inst.save()
    else:
        id_inst = Site(id=site_id, name=host, domain=host)
