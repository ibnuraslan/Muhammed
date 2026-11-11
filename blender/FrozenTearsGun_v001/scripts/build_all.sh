#!/bin/bash
# Full rebuild: humans -> sets/props -> animation. Run from blender/FrozenTearsGun_v001.
set -e
B=${B:-/opt/blender/blender-5.2.2-linux-x64/blender}
mkdir -p work
python3 -I ../pipeline/fetch_polyhaven.py assets/ph 1k WoodenTable_03 bench_vice_01 desk_lamp_arm_01 old_drill_press metal_tool_chest wooden_bookshelf_worn hand_plane_no4 pliers adjustable_wrench cross_pein_hammer screwdrivers_02 magnifying_glass_01 cardboard_box_01 small_oil_can_01 metal_office_desk modern_arm_chair_01 potted_plant_01 office_notepads book_encyclopedia_set_01 hanging_picture_frame_01 concrete_floor_02 plastered_wall_04 wood_table_001 red_brick_03 laminate_floor_02
python3 -I ../pipeline/fetch_polyhaven.py assets/ph 2k studio_small_09
$B -b --python scripts/01_build_humans.py -- work/humans.blend
$B -b work/humans.blend --python scripts/02_build_scene.py -- work/scene.blend
$B -b work/scene.blend --python scripts/03_animate.py -- work/film.blend
