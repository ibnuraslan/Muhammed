#!/bin/bash
# v006 chain: scene -> animate -> animated look -> look fixes -> hands pass
set -e
B=${B:-/opt/blender/blender-5.2.2-linux-x64/blender}
$B -b work/humans.blend --python scripts/02_build_scene.py -- work/scene3.blend
$B -b work/scene3.blend --python scripts/03_animate.py -- work/film3.blend
$B -b work/film3.blend --python ../pipeline/anim_look.py -- work/film4a.blend
$B -b work/film4a.blend --python scripts/05_anim_look_fix.py -- work/film4.blend
$B -b work/film4.blend --python scripts/06_hands_pass.py -- work/film6.blend
