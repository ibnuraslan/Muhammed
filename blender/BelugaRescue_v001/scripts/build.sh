#!/bin/bash
# full rebuild: people -> scene -> animation -> fx/camera   (run from blender/BelugaRescue_v001)
set -e
B=${BLENDER:-/opt/bin/blender}
[ -f work/people.blend ] || $B -b --python scripts/01_build_people.py -- work/people.blend
$B -b work/people.blend --python scripts/02_build_scene.py -- assets work/scene.blend 2>&1 | grep -E "SCENE_DONE|Error|rror" | grep -v CUEW
$B -b work/scene.blend --python scripts/03_animate.py -- work/anim.blend 2>&1 | grep -E "ANIM_DONE|HOLD|FLOOR|Error|rror" | grep -v CUEW
$B -b work/anim.blend --python scripts/03b_fx_camera.py -- work/film.blend 2>&1 | grep -E "FX_CAM_DONE|CAMERA|Error|rror" | grep -v CUEW
