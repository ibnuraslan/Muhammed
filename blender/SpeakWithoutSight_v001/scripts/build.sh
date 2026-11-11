#!/bin/bash
# Full rebuild. Usage: bash build.sh <work_dir>   (assets are fetched into <work_dir>/assets)
set -e
W=${1:-/tmp/sws}; B=/opt/blender/blender-5.2.2-linux-x64/blender; H=$(cd "$(dirname "$0")" && pwd); P=$H/../../pipeline
mkdir -p $W/assets
python3 -I $P/fetch_polyhaven.py $W/assets 1k ArmChair_01 vintage_grandfather_clock_01 vintage_oil_lamp mantel_clock_01 Sofa_01 tea_set_01 round_wooden_table_01 hanging_picture_frame_01 potted_plant_01 vintage_cabinet_01 book_encyclopedia_set_01 wooden_candlestick WoodenChair_01 island_tree_01 herringbone_parquet painted_plaster_wall dark_wood fabric_pattern_05 quatrefoil_jacquard_fabric
python3 -I $P/fetch_polyhaven.py $W/assets 2k belfast_farmhouse
python3 -I $P/find_models.py get $W/objv $W/assets/glb Dog=a89b49b3d9c647a8805d8d5287f47f48
$B -b --factory-startup --python $P/rig_quadruped.py -- $W/assets/glb/Dog.glb Dog 0.55 $W/dog.blend
$B -b --python $H/01_build_humans.py -- $W/humans.blend
$B -b --factory-startup --python $H/02_build_scene.py -- $W $W/assets $W/scene.blend
$B -b $W/scene.blend --python $H/03_animate.py -- $W/anim.blend      # also runs 03b_fx_camera.py
