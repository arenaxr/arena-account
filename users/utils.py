import os
import socket


def get_rest_host():
    verify = True
    hostname = os.environ["HOSTNAME"]
    hostip = socket.gethostbyname(socket.gethostname())
    if hostname == "localhost" and hostip != "127.0.0.1":
        host = "host.docker.internal"
        verify = False
    else:
        host = hostname
    return verify, host
