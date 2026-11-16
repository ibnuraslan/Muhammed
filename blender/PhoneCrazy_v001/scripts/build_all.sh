#!/bin/bash
# full rebuild of the Phase-1 file (about 3 min). Run from blender/PhoneCrazy_v001. Optional $1 = timing.json (Phase 2)
set -e
B=/opt/blender/blender-5.2.2-linux-x64/blender
python3 -I scripts/00_screens.py assets_src/screens.png
$B -b --factory-startup --python scripts/01_chars.py -- work/chars.blend
$B -b work/chars.blend --python scripts/02_sets.py -- work/sets.blend
$B -b work/sets.blend --python scripts/03_anim.py -- work/anim.blend $1
$B -b work/anim.blend --python ../pipeline/anim_look.py -- work/look.blend --no-sky
$B -b work/look.blend --python scripts/04_finish.py -- work/p1.blend
