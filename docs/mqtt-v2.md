# Sample MQTT JWT Topic Permissions v2

## Specific Scene Context
Page (3d scene), Python, Unity

### Scene Unprivileged

User: anonymous-mike

MQTT Publish topics:
- $NETWORK/latency
- realm/g/mwfarbnook/p/+
- realm/s/mwfarbnook/test/c/0799265009_anonymous-mike
- realm/s/mwfarbnook/test/c/0799265009_anonymous-mike/+
- realm/s/mwfarbnook/test/d/0799265009_anonymous-mike/-
- realm/s/mwfarbnook/test/e/0799265009_anonymous-mike/-
- realm/s/mwfarbnook/test/p/0799265009_anonymous-mike
- realm/s/mwfarbnook/test/p/0799265009_anonymous-mike/+
- realm/s/mwfarbnook/test/r/0799265009_anonymous-mike/-
- realm/s/mwfarbnook/test/u/0799265009_anonymous-mike
- realm/s/mwfarbnook/test/u/0799265009_anonymous-mike/+
- realm/s/mwfarbnook/test/u/handLeft_0799265009_anonymous-mike
- realm/s/mwfarbnook/test/u/handLeft_0799265009_anonymous-mike/+
- realm/s/mwfarbnook/test/u/handRight_0799265009_anonymous-mike
- realm/s/mwfarbnook/test/u/handRight_0799265009_anonymous-mike/+
- realm/s/mwfarbnook/test/x/0799265009_anonymous-mike
- realm/s/mwfarbnook/test/x/0799265009_anonymous-mike/+

MQTT Subscribe topics:
- realm/g/mwfarbnook/p/+
- realm/s/mwfarbnook/test/+/+
- realm/s/mwfarbnook/test/+/+/0799265009_anonymous-mike/#

### Scene Privileged

User: mwfarbnook

MQTT Publish topics:
- $NETWORK/latency
- realm/d/mwfarbnook/#
- realm/g/mwfarbnook/p/+
- realm/s/mwfarbnook/+/o/+
- realm/s/mwfarbnook/+/o/+/+
- realm/s/mwfarbnook/+/r/-
- realm/s/mwfarbnook/+/r/-/+
- realm/s/mwfarbnook/test/c/0799265009_mwfarbnook
- realm/s/mwfarbnook/test/c/0799265009_mwfarbnook/+
- realm/s/mwfarbnook/test/d/0799265009_mwfarbnook/-
- realm/s/mwfarbnook/test/e/0799265009_mwfarbnook/-
- realm/s/mwfarbnook/test/p/0799265009_mwfarbnook
- realm/s/mwfarbnook/test/p/0799265009_mwfarbnook/+
- realm/s/mwfarbnook/test/r/0799265009_mwfarbnook/-
- realm/s/mwfarbnook/test/u/0799265009_mwfarbnook
- realm/s/mwfarbnook/test/u/0799265009_mwfarbnook/+
- realm/s/mwfarbnook/test/u/handLeft_0799265009_mwfarbnook
- realm/s/mwfarbnook/test/u/handLeft_0799265009_mwfarbnook/+
- realm/s/mwfarbnook/test/u/handRight_0799265009_mwfarbnook
- realm/s/mwfarbnook/test/u/handRight_0799265009_mwfarbnook/+
- realm/s/mwfarbnook/test/x/0799265009_mwfarbnook
- realm/s/mwfarbnook/test/x/0799265009_mwfarbnook/+

MQTT Subscribe topics:
- realm/d/mwfarbnook/#
- realm/g/mwfarbnook/p/+
- realm/s/mwfarbnook/+/+/+
- realm/s/mwfarbnook/+/+/+/0799265009_mwfarbnook/#
- realm/s/mwfarbnook/+/r/+/-/#

## General Context
Page (scenes, build, network)

### General Unprivileged

User: anonymous-mike

MQTT Publish topics:
- $NETWORK/latency

MQTT Subscribe topics:
- $NETWORK
- realm/s/public/+/o/+

### General Privileged

User: mwfarbnook

MQTT Publish topics:
- $NETWORK/latency
- realm/s/mwfarb/allow-editors/o/+
- realm/s/mwfarb/json8/o/+
- realm/s/mwfarbnook/+/o/+

MQTT Subscribe topics:
- $NETWORK
- realm/s/mwfarb/allow-editors/+/+
- realm/s/mwfarb/json8/+/+
- realm/s/mwfarbnook/+/+/+
- realm/s/public/+/o/+
