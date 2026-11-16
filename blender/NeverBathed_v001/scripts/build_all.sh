#!/bin/bash
# build_all.sh <work_dir> <models_dir> <shots.json>   (run from blender/NeverBathed_v001/scripts)
set -eo pipefail
W=$1; M=$2; SH=$3; B=/opt/blender/blender-5.2.2-linux-x64/blender; R=$(cd ../..; pwd)
$B -b --factory-startup --python 01_chars.py -- $R $W/chars.blend 2>&1 | grep -E "Traceback|Error|_OK" 
$B -b $W/chars.blend --python 02_sets.py -- $M $R/assets/brand/DaKrasFilms_logo_white.png $W/sets.blend 2>&1 | grep -E "Traceback|Error|TUB|_OK"
cat 03_head.py 03_tail_fn.py 03_body.py 03_build.py > 03_shots.py
$B -b $W/sets.blend --python 03_shots.py -- $W/shots.blend $SH 2>&1 | grep -E "Traceback|Error|line [0-9]|_OK"
