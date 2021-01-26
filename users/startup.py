import datetime
import json
import logging
import os
import ssl
from urllib import request
from urllib.error import HTTPError, URLError

import jwt
from django.conf import settings
from django.contrib.sites.models import Site

logger = logging.getLogger(__name__)
logger.info("startup.py load test...")


def setup_socialapps():
    # add host to Sites if not there already
    host = os.getenv('HOSTNAME')
    hc = Site.objects.filter(id=settings.SITE_ID)
    if hc.exists():
        hc = Site.objects.get(id=settings.SITE_ID)
        hc.name = host
        hc.domain = host
    else:
        hc = Site(id=settings.SITE_ID, name=host, domain=host)
    hc.save()


def get_persist_scenes():
    # TODO (mwfarb): relpace with mongo lookup
    p_scenes = []
    config = settings.PUBSUB
    privkeyfile = settings.MQTT_TOKEN_PRIVKEY

    # get key for persist
    if os.path.exists(privkeyfile):
        print('Using keyfile at: ' + privkeyfile)
        with open(privkeyfile) as privatefile:
            private_key = privatefile.read()
        payload = {
            'sub': config['mqtt_username'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1),
            'subs': [f"{config['mqtt_realm']}/s/#"],
        }
        token = jwt.encode(payload, private_key, algorithm='RS256')

        # request all _scenes from persist
        host = config['mqtt_server']['host']
        # in docker on localhost this url will fail
        url = f'https://{host}/persist/!allscenes'
        try:
            req = request.Request(url)
            req.add_header("Cookie", f"mqtt_token={token.decode('utf-8')}")
            if settings.DEBUG:
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                res = request.urlopen(req, context=context)
            else:
                res = request.urlopen(req)
            result = res.read().decode('utf-8')
            p_scenes = json.loads(result)
        except (URLError, HTTPError) as err:
            print("{0}: ".format(err)+url)
        except ValueError as err:
            print(f"{result} {0}: ".format(err)+url)

    return p_scenes
