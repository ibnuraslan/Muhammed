#!/bin/bash
# Full rebuild. Usage: bash build.sh <work_dir>   (assets are fetched into <work_dir>/assets)
set -e
W=${1:-/tmp/sws}; B=/opt/blender/blender-5.2.2-linux-x64/blender; H=$(cd "$(dirname "$0")" && pwd); P=$H/../../pipeline
mkdir -p $W/assets
python3 -I $P/fetch_polyhaven.py $W/assets 1k ArmChair_01 vintage_grandfather_clock_01 vintage_oil_lamp mantel_clock_01 Sofa_01 tea_set_01 round_wooden_table_01 hanging_picture_frame_01 potted_plant_01 vintage_cabinet_01 book_encyclopedia_set_01 wooden_candlestick WoodenChair_01 island_tree_01 herringbone_parquet painted_plaster_wall dark_wood fabric_pattern_05 quatrefoil_jacquard_fabric
python3 -I $P/fetch_polyhaven.py $W/assets 2k belfast_farmhouse
python3 -I $P/find_models.py get $W/objv $W/assets/glb Dog=a89b49b3d9c647a8805d8d5287f47f48
$B -b --factory-startup --python $P/rig_quadruped.py -- $W/assets/glb/Dog.glb Dog 0.55 $W/dog.blend
python3 -I $P/find_models.py get $W/objv $W/assets/glb2 HandSkeleton=efd1df50e4a2457d91045a1727db7679 Larynx=a0d7f8420e8140acbb75d2afc69e66fb Footstool=bbc26fe77dd24364bd48123f17d3a722 OpenBook=cd8df095f5db4fa38fe7d8799822cfc3
$B -b --factory-startup --python $H/01c_prep_models.py -- $W/assets/glb2 $W/models.blend
$B -b --python $H/01_build_humans.py -- $W/humans.blend
$B -b --factory-startup --python $H/02_build_scene.py -- $W $W/assets $W/scene.blend
$B -b $W/scene.blend --python $H/03_animate.py -- $W/anim_pre.blend      # also runs 03b_fx_camera.py
$B -b $W/anim_pre.blend --python $P/anim_look.py -- $W/anim.blend         # animated-CG look (client, Nov 11 22:45)
# farm package (<95 MB, plain git file):
# $B -b $W/anim.blend --python $H/04_shrink_textures.py -- $W/jpgtex $W/anim_small.blend
# $B -b $W/anim_small.blend --python $P/package_for_farm.py -- <repo>/blender/SpeakWithoutSight_v002/SpeakWithoutSight_v002_60fps.blend
