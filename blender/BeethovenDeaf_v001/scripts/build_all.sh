#!/bin/bash
# Full rebuild of BeethovenDeaf_v001.  bash build_all.sh <work_dir>   (needs network once for the assets)
set -e
W=${1:?work dir}; B=${BLENDER:-/opt/blender/blender-5.2.2-linux-x64/blender}; P=../../pipeline
cd "$(dirname "$0")"; mkdir -p "$W"
if [ ! -f "$W/glb/piano.glb" ]; then
  python3 -I $P/find_models.py search "$W/models" "grand piano" >/dev/null
  python3 -I $P/find_models.py get "$W/models" "$W/glb" piano=c7c82e2445544191b541f2240ae8c4e7 skull_a=017c6f4a760f40a0a03de8fae29b306b \
    inner_ear2=92d3fe7b76214170a59875a5d656d595 candelabra=f00558f1fba44a9698a2df0d9feb0d59 bench=d6c16ede20974098899ad5b370e259d5
  for a in herringbone_parquet plastered_wall_02 wood_table_worn dark_wooden_planks velour_velvet old_hall; do python3 -I $P/fetch_polyhaven.py "$W/ph" 2k $a; done
fi
for s in 1 2 3; do python3 -I 00_make_sheet_texture.py ../assets/tex/manuscript_$s.jpg $s; done
$B -b --python 01_build_composer.py -- "$W/composer.blend" short02
$B -b "$W/composer.blend" --python 02_build_scene.py -- "$W" "$W/scene.blend"
$B -b "$W/scene.blend" --python 03_animate.py -- "$W/anim.blend"
$B -b "$W/anim.blend" --python 04_xray_fx.py -- "$W" "$W/xray.blend"
$B -b "$W/xray.blend" --python 05_camera.py -- "$W/film.blend"
$B -b "$W/film.blend" --python 06_audit.py -- ../review/C_audit.txt
echo "BUILT $W/film.blend"
