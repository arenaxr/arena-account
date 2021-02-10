import logging
import os

from django.conf import settings
from django.contrib.sites.models import Site

logger = logging.getLogger(__name__)
logger.info("startup.py load test...")


def setup_socialapps():
    # add host to Sites if not there already
    host = os.getenv("HOSTNAME")
    hc = Site.objects.filter(id=settings.SITE_ID)
    if hc.exists():
        hc = Site.objects.get(id=settings.SITE_ID)
        if hc.domain != host:
            hc.name = host
            hc.domain = host
            hc.save()
    else:
        hc = Site(id=settings.SITE_ID, name=host, domain=host)
