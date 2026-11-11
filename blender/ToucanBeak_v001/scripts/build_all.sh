#!/bin/bash
# full rebuild: bird, vets, sets, animation, animated-CG look pass
set -e
cd "$(dirname "$0")/.."
B=${BLENDER:-/opt/blender/blender-5.2.2-linux-x64/blender}
[ "$1" == "full" ] && $B -b --factory-startup -P scripts/01_build_bird.py -- work/bird.blend && $B -b -P scripts/02_build_vets.py -- work/vets.blend
[ "$1" == "full" -o "$1" == "sets" ] && $B -b -P scripts/03_sets.py -- work/sets.blend
$B -b work/sets.blend -P scripts/04_anim.py -- work/film.blend
$B -b work/film.blend --python ../pipeline/anim_look.py -- work/look_base.blend
$B -b work/look_base.blend -P scripts/05_look.py -- work/look.blend
