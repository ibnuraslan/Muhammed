#!/bin/bash
# quick layout check: tools/quick.sh f1 B 0.5  -> out/quick/f1_B.png (25%, 12 spp, no hair)
cd "$(dirname "$0")/.." && mkdir -p out/quick
NODOF=1 PCT=25 SPP=12 HAIR=0 /opt/blender/blender-5.2.2-linux-x64/blender -b --factory-startup -P films/run.py -- $1 $2 ${3:-0.5} out/quick/$1_$2.png > out/quick/$1_$2.log 2>&1
grep -E "RENDERED|Traceback|Error:|line [0-9]" out/quick/$1_$2.log | grep -v CUEW | tail -5
