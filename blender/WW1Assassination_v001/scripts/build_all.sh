#!/bin/bash
# Full rebuild of WW1Assassination from scratch. Run from blender/WW1Assassination_v001/.
# Needs assets fetched (see README) in $WW1_ASSETS and $WW1_MODELS, Natural Earth geojson in $WW1_NE.
set -e
B=${BLENDER:-/opt/blender/blender-5.2.2-linux-x64/blender}
mkdir -p work
step() { echo "== $1"; }
[ "$1" == "fromanim" ] || {
step humans; $B -b --python scripts/01_build_humans.py -- work/humans.blend 2>&1 | grep -E "SAVED|Error|Traceback" || true
step set;    $B -b work/humans.blend --python scripts/02_build_set.py -- work/set.blend 2>&1 | grep -E "SET_DONE|Error|Traceback" || true
step props;  $B -b work/set.blend --python scripts/03_props.py -- work/props.blend 2>&1 | grep -E "PROPS_DONE|Error|Traceback" || true
}
step anim;   $B -b work/props.blend --python scripts/04_anim.py -- work/anim.blend 2>&1 | grep -E "CROWD |ANIM_DONE|Error|Traceback|line [0-9]" || true
step horses; [ -f work/horse.blend ] || $B -b --factory-startup --python ../pipeline/rig_quadruped.py -- $WW1_MODELS/horse.glb Horse 2.1 work/horse.blend
$B -b work/anim.blend --python scripts/04b_horses.py -- work/horse.blend work/anim_h.blend 2>&1 | grep -E "HORSES|Error|Traceback" || true
step map;    [ -f work/map.npz ] || python3 -I scripts/06a_map_raster.py $WW1_NE work/map.npz
$B -b work/anim_h.blend --python scripts/06b_map.py -- work/map.npz work/map.blend 2>&1 | grep -E "MAP_DONE|Error|Traceback|line [0-9]" || true
step camfx;  $B -b work/map.blend --python scripts/05_camera_fx.py -- work/film.blend 2>&1 | grep -E "CAMFX|WHITE|Error|Traceback|line [0-9]" || true
echo BUILD_DONE
