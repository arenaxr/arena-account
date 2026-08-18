"""RSA key fixture and helpers shared by the MQTT token tests.

The MQTT tokens are RS256 JWTs signed with the key at settings.MQTT_TOKEN_PRIVKEY.
Tests generate a throwaway key pair once per test process and point
MQTT_TOKEN_PRIVKEY at it with @override_settings, so nothing here touches a real
deployment key. This module is deliberately not named test*.py so the test
runner does not try to collect it.
"""

import atexit
import os
import shutil
import tempfile

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

_KEY_DIR = tempfile.mkdtemp(prefix="arena-account-test-keys-")
atexit.register(shutil.rmtree, _KEY_DIR, True)

#: path handed to settings.MQTT_TOKEN_PRIVKEY in tests
PRIVATE_KEY_PATH = os.path.join(_KEY_DIR, "mqtt_private.pem")
#: path that is guaranteed not to exist, for the "no keyfile" branch
MISSING_KEY_PATH = os.path.join(_KEY_DIR, "absent_private.pem")

_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

with open(PRIVATE_KEY_PATH, "wb") as _fh:
    _fh.write(
        _private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )

PUBLIC_KEY_PEM = _private_key.public_key().public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo,
).decode()


def decode_token(token):
    """Verify the token signature with the fixture public key and return claims."""
    return jwt.decode(
        token,
        PUBLIC_KEY_PEM,
        algorithms=["RS256"],
        # 'aud' is only present for a/v scenes and is asserted on explicitly
        options={"verify_aud": False},
    )


def token_header(token):
    return jwt.get_unverified_header(token)


def make_ids(
    username,
    nonce="0000000001",
    client="web",
    camid=False,
    handleftid=False,
    handrightid=False,
    renderfusionid=False,
    environmentid=False,
):
    """Build the 'ids' dict the way users/api.py mqtt_auth builds it for API v2."""
    userid = f"{username}_{nonce}"
    ids = {"userid": userid, "userclient": f"{userid}_{client}"}
    if camid:
        ids["camid"] = userid  # v2 uses the userid itself as the camera object id
    if handleftid:
        ids["handleftid"] = f"handLeft_{userid}"
    if handrightid:
        ids["handrightid"] = f"handRight_{userid}"
    if renderfusionid:
        ids["renderfusionid"] = "-"
    if environmentid:
        ids["environmentid"] = "-"
    return ids
