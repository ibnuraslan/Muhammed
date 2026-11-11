#!/bin/bash
# full rebuild: people -> scene -> animation -> camera.  W = work dir, A = assets root
set -e
W=${W:-/opt/work/sbl}; A=${A:-/opt/assets/sbl}; B=${BLENDER:-/opt/bin/blender}
cd "$(dirname "$0")"
[ -f $W/people.blend ] || $B -b --python 01_build_people.py -- $W/people.blend
$B -b $W/people.blend --python 02_build_scene.py -- $A $W/scene.blend 2>&1 | grep -E "SCENE_BUILT|Traceback|Error:" || true
$B -b $W/scene.blend --python 03_animate.py -- $W/anim.blend 2>&1 | grep -E "ANIM_DONE|Traceback|Error|line [0-9]" | grep -v CUEW || true
$B -b $W/anim.blend --python 04_camera.py -- $W/film.blend 2>&1 | grep -E "CAMERA_DONE|Traceback|Error|line [0-9]" | grep -v CUEW || true
