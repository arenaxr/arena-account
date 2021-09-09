import os
import socket


def get_rest_host():
    verify = True
    hostname = os.environ["HOSTNAME"]
    hostip = socket.gethostbyname(socket.gethostname())
    if hostname == "localhost" and hostip.startswith("172."):
        host = "host.docker.internal"
        verify = False
    else:
        host = hostname
    return verify, host
