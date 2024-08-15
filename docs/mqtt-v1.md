# Sample MQTT JWT Topic Permissions v1 (deprecated)

## Specific Scene Context
Page (3d scene), Python, Unity

### Scene Unprivileged

User: anonymous-mike

MQTT Publish topics:
- $NETWORK/latency
- realm/c/mwfarbnook/o/2559945886_anonymous-mikeMjU1OTk0NTg4Nl9hbm9ueW1vdXMtbWlrZQ==
- realm/c/mwfarbnook/p/+/2559945886_anonymous-mikeMjU1OTk0NTg4Nl9hbm9ueW1vdXMtbWlrZQ==
- realm/env/mwfarbnook/test/#
- realm/env/public/#
- realm/g/a/#
- realm/proc/#
- realm/s/mwfarbnook/test/camera_2559945886_anonymous-mike
- realm/s/mwfarbnook/test/camera_2559945886_anonymous-mike/#
- realm/s/mwfarbnook/test/handLeft_2559945886_anonymous-mike
- realm/s/mwfarbnook/test/handRight_2559945886_anonymous-mike

MQTT Subscribe topics:
- $NETWORK
- realm/c/mwfarbnook/o/#
- realm/c/mwfarbnook/p/2559945886_anonymous-mike/#
- realm/g/a/#
- realm/proc/#
- realm/s/mwfarbnook/test/#
- realm/s/public/#

### Scene Privileged

User: mwfarbnook

MQTT Publish topics:
- $NETWORK/latency
- realm/c/mwfarbnook/o/3368381823_mwfarbnookMzM2ODM4MTgyM19td2ZhcmJub29r
- realm/c/mwfarbnook/p/+/3368381823_mwfarbnookMzM2ODM4MTgyM19td2ZhcmJub29r
- realm/d/mwfarbnook/#
- realm/env/mwfarbnook/#
- realm/env/public/#
- realm/g/a/#
- realm/proc/#
- realm/s/mwfarbnook/#

MQTT Subscribe topics:
- $NETWORK
- realm/c/mwfarbnook/o/#
- realm/c/mwfarbnook/p/3368381823_mwfarbnook/#
- realm/d/mwfarbnook/#
- realm/env/mwfarbnook/#
- realm/g/a/#
- realm/proc/#
- realm/s/mwfarbnook/#
- realm/s/public/#

## General Context
Page (scenes, build, network)

### General Unprivileged

User: anonymous-mike

MQTT Publish topics:
- $NETWORK/latency
- realm/env/public/#
- realm/proc/#

MQTT Subscribe topics:
- $NETWORK
- realm/proc/#
- realm/s/public/#

### General Privileged

User: mwfarbnook

MQTT Publish topics:
- $NETWORK/latency
- realm/d/mwfarbnook/#
- realm/env/mwfarb/allow-editors/#
- realm/env/mwfarb/json8/#
- realm/env/mwfarbnook/#
- realm/env/public/#
- realm/proc/#
- realm/s/mwfarb/allow-editors/#
- realm/s/mwfarb/json8/#
- realm/s/mwfarbnook/#

MQTT Subscribe topics:
- $NETWORK
- realm/d/mwfarbnook/#
- realm/env/mwfarb/allow-editors/#
- realm/env/mwfarb/json8/#
- realm/env/mwfarbnook/#
- realm/proc/#
- realm/s/mwfarb/allow-editors/#
- realm/s/mwfarb/json8/#
- realm/s/mwfarbnook/#
- realm/s/public/#
