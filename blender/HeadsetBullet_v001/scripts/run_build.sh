#!/bin/bash
# build order: 02 scene -> 03 animate (+03a headset) -> 03b effects -> 03c camera
cd /home/user/Muhammed/blender/HeadsetBullet_v001
/opt/bin/blender -b work/scene.blend --python scripts/03_animate.py -- work/anim.blend 2>&1 | grep -E "Traceback|Error|HEADFIT|^[A-Z]+ " -A6 | grep -v CUEW
