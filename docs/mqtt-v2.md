# Sample MQTT JWT Topic Permissions v2

## Specific Scene Context
Page (3d scene), Python, Unity

### Scene Unprivileged

User: anonymous-mike

MQTT Publish topics:
- $NETWORK/latency
- realm/proc/#
- realm/s/mwfarbnook/test/c/+/0799265009_anonymous-mike
- realm/s/mwfarbnook/test/c/0799265009_anonymous-mike
- realm/s/mwfarbnook/test/d/+/0799265009_anonymous-mike
- realm/s/mwfarbnook/test/e/+/0799265009_anonymous-mike
- realm/s/mwfarbnook/test/p/+/0799265009_anonymous-mike
- realm/s/mwfarbnook/test/p/0799265009_anonymous-mike
- realm/s/mwfarbnook/test/r/+/0799265009_anonymous-mike
- realm/s/mwfarbnook/test/u/+/0799265009_anonymous-mike
- realm/s/mwfarbnook/test/u/0799265009_anonymous-mike
- realm/s/mwfarbnook/test/u/handLeft_0799265009_anonymous-mike
- realm/s/mwfarbnook/test/u/handRight_0799265009_anonymous-mike
- realm/s/mwfarbnook/test/x/+/0799265009_anonymous-mike
- realm/s/mwfarbnook/test/x/0799265009_anonymous-mike

MQTT Subscribe topics:
- realm/proc/#
- realm/s/mwfarbnook/test/+/+
- realm/s/mwfarbnook/test/+/+/0799265009_anonymous-mike

### Scene Privileged

User: mwfarbnook

MQTT Publish topics:
- $NETWORK/latency
- realm/d/mwfarbnook/#
- realm/proc/#
- realm/s/mwfarbnook/+/+/+
- realm/s/mwfarbnook/+/+/+/+

MQTT Subscribe topics:
- realm/d/mwfarbnook/#
- realm/proc/#
- realm/s/mwfarbnook/+/+/+
- realm/s/mwfarbnook/+/+/+/0799265009_mwfarbnook

## General Context
Page (scenes, build, network)

### General Unprivileged

User: anonymous-mike

MQTT Publish topics:
- $NETWORK/latency

MQTT Subscribe topics:
- $NETWORK
- realm/s/public/+/+/+

### General Privileged

User: mwfarbnook

MQTT Publish topics:
- $NETWORK/latency
- realm/s/mwfarb/allow-editors/+/+
- realm/s/mwfarb/json8/+/+
- realm/s/mwfarbnook/+/+/+

MQTT Subscribe topics:
- $NETWORK
- realm/s/mwfarb/allow-editors/+/+
- realm/s/mwfarb/json8/+/+
- realm/s/mwfarbnook/+/+/+
- realm/s/public/+/+/+
