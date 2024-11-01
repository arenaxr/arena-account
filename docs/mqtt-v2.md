# Sample MQTT JWT Topic Permissions v2

## Specific Scene Context
Page (3d scene), Python, Unity

### Scene Unprivileged

User: anonymous-mike

MQTT Publish topics:
- $NETWORK/latency
- realm/g/mwfarbnook/p/+
- realm/s/mwfarbnook/test/c/anonymous-mike_0799265009_web/anonymous-mike_0799265009
- realm/s/mwfarbnook/test/c/anonymous-mike_0799265009_web/anonymous-mike_0799265009/+
- realm/s/mwfarbnook/test/d/anonymous-mike_0799265009_web/anonymous-mike_0799265009/-
- realm/s/mwfarbnook/test/e/anonymous-mike_0799265009_web/anonymous-mike_0799265009/-
- realm/s/mwfarbnook/test/p/anonymous-mike_0799265009_web/anonymous-mike_0799265009
- realm/s/mwfarbnook/test/p/anonymous-mike_0799265009_web/anonymous-mike_0799265009/+
- realm/s/mwfarbnook/test/r/anonymous-mike_0799265009_web/anonymous-mike_0799265009/-
- realm/s/mwfarbnook/test/u/anonymous-mike_0799265009_web/anonymous-mike_0799265009
- realm/s/mwfarbnook/test/u/anonymous-mike_0799265009_web/anonymous-mike_0799265009/+
- realm/s/mwfarbnook/test/u/anonymous-mike_0799265009_web/handLeft_anonymous-mike_0799265009
- realm/s/mwfarbnook/test/u/anonymous-mike_0799265009_web/handLeft_anonymous-mike_0799265009/+
- realm/s/mwfarbnook/test/u/anonymous-mike_0799265009_web/handRight_anonymous-mike_0799265009
- realm/s/mwfarbnook/test/u/anonymous-mike_0799265009_web/handRight_anonymous-mike_0799265009/+
- realm/s/mwfarbnook/test/x/anonymous-mike_0799265009_web/anonymous-mike_0799265009
- realm/s/mwfarbnook/test/x/anonymous-mike_0799265009_web/anonymous-mike_0799265009/+

MQTT Subscribe topics:
- realm/g/mwfarbnook/p/+
- realm/s/mwfarbnook/test/+/+/+
- realm/s/mwfarbnook/test/+/+/+/anonymous-mike_0799265009/#

### Scene Privileged

User: mwfarbnook

MQTT Publish topics:
- $NETWORK/latency
- realm/d/mwfarbnook/#
- realm/g/mwfarbnook/p/+
- realm/s/mwfarbnook/+/o/mwfarbnook_0799265009_web/+
- realm/s/mwfarbnook/+/o/mwfarbnook_0799265009_web/+/+
- realm/s/mwfarbnook/+/r/mwfarbnook_0799265009_web/-
- realm/s/mwfarbnook/+/r/mwfarbnook_0799265009_web/-/+
- realm/s/mwfarbnook/test/c/mwfarbnook_0799265009_web/mwfarbnook_0799265009
- realm/s/mwfarbnook/test/c/mwfarbnook_0799265009_web/mwfarbnook_0799265009/+
- realm/s/mwfarbnook/test/d/mwfarbnook_0799265009_web/mwfarbnook_0799265009/-
- realm/s/mwfarbnook/test/e/mwfarbnook_0799265009_web/mwfarbnook_0799265009/-
- realm/s/mwfarbnook/test/p/mwfarbnook_0799265009_web/mwfarbnook_0799265009
- realm/s/mwfarbnook/test/p/mwfarbnook_0799265009_web/mwfarbnook_0799265009/+
- realm/s/mwfarbnook/test/r/mwfarbnook_0799265009_web/mwfarbnook_0799265009/-
- realm/s/mwfarbnook/test/u/mwfarbnook_0799265009_web/mwfarbnook_0799265009
- realm/s/mwfarbnook/test/u/mwfarbnook_0799265009_web/mwfarbnook_0799265009/+
- realm/s/mwfarbnook/test/u/mwfarbnook_0799265009_web/handLeft_mwfarbnook_0799265009
- realm/s/mwfarbnook/test/u/mwfarbnook_0799265009_web/handLeft_mwfarbnook_0799265009/+
- realm/s/mwfarbnook/test/u/mwfarbnook_0799265009_web/handRight_mwfarbnook_0799265009
- realm/s/mwfarbnook/test/u/mwfarbnook_0799265009_web/handRight_mwfarbnook_0799265009/+
- realm/s/mwfarbnook/test/x/mwfarbnook_0799265009_web/mwfarbnook_0799265009
- realm/s/mwfarbnook/test/x/mwfarbnook_0799265009_web/mwfarbnook_0799265009/+

MQTT Subscribe topics:
- realm/d/mwfarbnook/#
- realm/g/mwfarbnook/p/+
- realm/s/mwfarbnook/+/+/+/+
- realm/s/mwfarbnook/+/+/+/+/mwfarbnook_0799265009/#
- realm/s/mwfarbnook/+/r/+/+/-/#

## General Context
Page (scenes, build, network)

### General Unprivileged

User: anonymous-mike

MQTT Publish topics:
- $NETWORK/latency

MQTT Subscribe topics:
- $NETWORK
- realm/s/public/+/o/+/+

### General Privileged

User: mwfarbnook

MQTT Publish topics:
- $NETWORK/latency
- realm/s/mwfarb/allow-editors/o/mwfarbnook_0799265009_web/+
- realm/s/mwfarb/json8/o/mwfarbnook_0799265009_web/+
- realm/s/mwfarbnook/+/o/mwfarbnook_0799265009_web/+

MQTT Subscribe topics:
- $NETWORK
- realm/s/mwfarb/allow-editors/+/+/+
- realm/s/mwfarb/json8/+/+/+
- realm/s/mwfarbnook/+/+/+/+
- realm/s/public/+/o/+/+
