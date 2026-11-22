#!/bin/bash
# full-quality key frames (1280x720, 64 spp, hair, DOF): tools/keys.sh f1 "A:0.5 B:0.5 D:0.6 LOGO:1"
cd "$(dirname "$0")/.." && mkdir -p out/key
for st in $2; do s=${st%%:*}; t=${st##*:}
  /opt/blender/blender-5.2.2-linux-x64/blender -b --factory-startup -P films/run.py -- $1 $s $t out/key/$1_$s.png > out/key/$1_$s.log 2>&1
  echo "$1 $s: $(grep -E 'RENDERED|Traceback|Error:' out/key/$1_$s.log | grep -v CUEW | tail -1)"
done
