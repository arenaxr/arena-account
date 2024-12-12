# Sample MQTT JWT Topic Permissions v1 (deprecated)

## Specific Scene Context
Pages (3d scene, build3d), Python, Unity

### Scene Unprivileged
Scene: mwfarb/test

Editor: None

User: anonymous-mike

MQTT Publish topics:
- $NETWORK/latency
- realm/c/mwfarb/o/2559945886_anonymous-mikeMjU1OTk0NTg4Nl9hbm9ueW1vdXMtbWlrZQ==
- realm/c/mwfarb/p/+/2559945886_anonymous-mikeMjU1OTk0NTg4Nl9hbm9ueW1vdXMtbWlrZQ==
- realm/env/mwfarb/test/#
- realm/env/public/#
- realm/g/a/#
- realm/proc/#
- realm/s/mwfarb/test/camera_2559945886_anonymous-mike
- realm/s/mwfarb/test/camera_2559945886_anonymous-mike/#
- realm/s/mwfarb/test/handLeft_2559945886_anonymous-mike
- realm/s/mwfarb/test/handRight_2559945886_anonymous-mike

MQTT Subscribe topics:
- realm/c/mwfarb/o/#
- realm/c/mwfarb/p/2559945886_anonymous-mike/#
- realm/g/a/#
- realm/proc/#
- realm/s/mwfarb/test/#
- realm/s/public/#

### Scene Privileged
Scene: mwfarb/test

Editor: mwfarbnook/+, mwfarb/allow-editors

User: mwfarbnook

MQTT Publish topics:
- $NETWORK/latency
- realm/c/mwfarb/o/3368381823_mwfarbnookMzM2ODM4MTgyM19td2ZhcmJub29r
- realm/c/mwfarb/p/+/3368381823_mwfarbnookMzM2ODM4MTgyM19td2ZhcmJub29r
- realm/d/mwfarbnook/#
- realm/env/mwfarb/test/#
- realm/env/mwfarbnook/#
- realm/env/public/#
- realm/g/a/#
- realm/proc/#
- realm/s/mwfarb/test/camera_3368381823_mwfarbnook
- realm/s/mwfarb/test/camera_3368381823_mwfarbnook/#
- realm/s/mwfarb/test/handLeft_3368381823_mwfarbnook
- realm/s/mwfarb/test/handRight_3368381823_mwfarbnook
- realm/s/mwfarbnook/#

MQTT Subscribe topics:
- realm/c/mwfarb/o/#
- realm/c/mwfarb/p/3368381823_mwfarbnook/#
- realm/d/mwfarbnook/#
- realm/env/mwfarbnook/#
- realm/g/a/#
- realm/proc/#
- realm/s/mwfarb/test/#
- realm/s/mwfarbnook/#
- realm/s/public/#

## General Context
Pages (scenes, build, network)

### General Unprivileged
Scene: None

Editor: None

User: anonymous-mike

MQTT Publish topics:
- $NETWORK/latency
- realm/env/public/#

MQTT Subscribe topics:
- $NETWORK
- realm/s/public/#

### General Privileged
Scene: None

Editor: mwfarbnook/+, mwfarb/allow-editors

User: mwfarbnook

MQTT Publish topics:
- $NETWORK/latency
- realm/env/mwfarb/allow-editors/#
- realm/env/mwfarbnook/#
- realm/env/public/#
- realm/s/mwfarb/allow-editors/#
- realm/s/mwfarbnook/#

MQTT Subscribe topics:
- $NETWORK
- realm/env/mwfarb/allow-editors/#
- realm/env/mwfarbnook/#
- realm/s/mwfarb/allow-editors/#
- realm/s/mwfarbnook/#
- realm/s/public/#
