#!/bin/bash
# Full rebuild: people.blend must exist (01_build_people.py, needs MPFB2).
set -e
cd /home/user/Muhammed/blender/Tsunami2004_v001
B=/opt/blender/blender-5.2.2-linux-x64/blender
$B -b --factory-startup --python scripts/02_scene.py -- $PWD/scene.blend
$B -b scene.blend --python scripts/03_anim.py -- $PWD/anim.blend
$B -b anim.blend --python scripts/04_camera.py -- $PWD/film_real.blend
$B -b film_real.blend --python ../pipeline/anim_look.py -- $PWD/film.blend
