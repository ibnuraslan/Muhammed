#!/bin/bash
# Storyboard stills: tools/sb.sh SCENE SHOT [SHOT...]   (half-res 1280x720, low samples)
D=$(cd "$(dirname "$0")/.." && pwd); B=${BLENDER:-/opt/blender/blender-5.2.2-linux-x64/blender}
sc=$1; shift; mkdir -p "$D/out/logs" "$D/out/frames"
for s in "$@"; do
  t=$(date +%s); PREVIEW=${PREVIEW:-0.5} SPP=${SPP:-240} HAIR=${HAIR:-0.7} SHOT=$s "$B" -b --python "$D/scenes/$sc.py" > "$D/out/logs/$s.log" 2>&1
  echo "$s $(( $(date +%s) - t ))s $(grep -cE "Traceback" "$D/out/logs/$s.log") errors $(grep -oE "CLIPCHECK [^:]*: [0-9]+ clipping" "$D/out/logs/$s.log")"
done
