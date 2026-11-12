#!/bin/bash
# Build the GoatOwner farm package from scratch.
#   bash 05_package.sh <assets_root> <work_dir> <out_dir>
# assets_root: ph/ (Poly Haven, fetch_polyhaven.py) and objv/ (find_models.py GLBs + truck_base_clean.png)
set -e
A=$1; W=$2; OUT=$3
B=${BLENDER:-/opt/blender/blender-5.2.2-linux-x64/blender}
HERE=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$W" "$OUT"
$B -b --factory-startup --python "$HERE/rig_quadruped.py" -- "$A/objv/goat.glb" Goat 0.85 "$W/goat_rig.blend"
$B -b --python "$HERE/01_build_humans.py" -- "$W/humans.blend"
$B -b "$W/humans.blend" --python "$HERE/02_build_scene.py" -- "$A" "$W" "$W/scene.blend"
$B -b "$W/scene.blend" --python "$HERE/03_animate.py" -- "$W/anim.blend"
$B -b "$W/anim.blend" --python "$HERE/04_shrink.py" -- "$W/tex_small" "$W/shrunk.blend"
$B -b "$W/shrunk.blend" --python "$HERE/../../pipeline/package_for_farm.py" -- "$OUT/GoatOwner_v002_60fps.blend"
