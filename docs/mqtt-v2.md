# Sample MQTT JWT Topic Permissions v2

## Specific Scene Context
- Page (3d scene), Python, Unity
- Scene = mwfarb/test

### Scene Unprivileged

User: anonymous-mike

MQTT Publish topics:
- $NETWORK/latency
- realm/g/mwfarb/p/+
- realm/s/mwfarb/test/+/anonymous-mike_0799265009_web/anonymous-mike_0799265009
- realm/s/mwfarb/test/+/anonymous-mike_0799265009_web/anonymous-mike_0799265009/+
- realm/s/mwfarb/test/u/anonymous-mike_0799265009_web/handLeft_anonymous-mike_0799265009
- realm/s/mwfarb/test/u/anonymous-mike_0799265009_web/handLeft_anonymous-mike_0799265009/+
- realm/s/mwfarb/test/u/anonymous-mike_0799265009_web/handRight_anonymous-mike_0799265009
- realm/s/mwfarb/test/u/anonymous-mike_0799265009_web/handRight_anonymous-mike_0799265009/+

MQTT Subscribe topics:
- realm/g/mwfarb/p/+
- realm/s/mwfarb/test/+/+/+
- realm/s/mwfarb/test/+/+/+/anonymous-mike_0799265009/#

### Scene Privileged

User: mwfarbnook

MQTT Publish topics:
- $NETWORK/latency
- realm/d/mwfarbnook/#
- realm/g/mwfarb/p/+
- realm/s/mwfarb/test/+/mwfarbnook_0799265009_web/mwfarbnook_0799265009
- realm/s/mwfarb/test/+/mwfarbnook_0799265009_web/mwfarbnook_0799265009/+
- realm/s/mwfarb/test/u/mwfarbnook_0799265009_web/handLeft_mwfarbnook_0799265009
- realm/s/mwfarb/test/u/mwfarbnook_0799265009_web/handLeft_mwfarbnook_0799265009/+
- realm/s/mwfarb/test/u/mwfarbnook_0799265009_web/handRight_mwfarbnook_0799265009
- realm/s/mwfarb/test/u/mwfarbnook_0799265009_web/handRight_mwfarbnook_0799265009/+
- realm/s/mwfarbnook/+/o/mwfarbnook_0799265009_web/#
- realm/s/mwfarbnook/+/p/+/#

MQTT Subscribe topics:
- realm/d/mwfarbnook/#
- realm/g/mwfarb/p/+
- realm/s/mwfarb/test/+/+/+
- realm/s/mwfarb/test/+/+/+/mwfarbnook_0799265009/#
- realm/s/mwfarbnook/+/p/+/#

## General Context
- Page (scenes, build, network)
- Scene = None

### General Unprivileged

User: anonymous-mike

MQTT Publish topics:
- $NETWORK/latency

MQTT Subscribe topics:
- $NETWORK
- realm/s/public/+/+/+/+
- realm/s/public/+/+/+/+/anonymous-mike_0799265009/#

### General Privileged

User: mwfarbnook

MQTT Publish topics:
- $NETWORK/latency
- realm/s/mwfarb/allow-editors/o/mwfarbnook_0799265009_web/#
- realm/s/mwfarb/allow-editors/p/+/#
- realm/s/mwfarb/json8/o/mwfarbnook_0799265009_web/#
- realm/s/mwfarb/json8/p/+/#
- realm/s/mwfarbnook/+/o/mwfarbnook_0799265009_web/#
- realm/s/mwfarbnook/+/p/+/#

MQTT Subscribe topics:
- $NETWORK
- realm/s/mwfarb/allow-editors/p/+/#
- realm/s/mwfarb/json8/p/+/#
- realm/s/mwfarbnook/+/p/+/#
- realm/s/public/+/+/+/+
- realm/s/public/+/+/+/+/mwfarbnook_0799265009/#
