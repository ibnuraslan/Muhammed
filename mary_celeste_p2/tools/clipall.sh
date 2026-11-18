#!/bin/bash
# Clip check (no render) for every character shot. Prints one CLIPCHECK line per shot + the CLIP lines.
export PATH=/opt/blender/blender-5.2.2-linux-x64:$PATH CLIP=1 CLIPONLY=1 HAIR=${HAIR:-0.02}
D=$(cd "$(dirname "$0")/.." && pwd)
run() { sc=$1; shift; for s in "$@"; do blender -b --python $D/scenes/$sc.py -- SHOT=$s 2>&1 | grep -E "^CLIP|Traceback|Error:" | grep -v CUEW; done; }
run sc_cabin ${CABIN:-02 03 07 08 11 12 14 17 19 23 30 34 35 36 38 39}
run sc_pier ${PIER:-01 04 06 15}
run sc_sea ${SEA:-22 25 29 37 43 44 45}
run sc_rooms ${ROOMS:-09 10 16 18}
