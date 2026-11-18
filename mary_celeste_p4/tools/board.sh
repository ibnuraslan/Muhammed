#!/bin/bash
# Render storyboard frames: tools/board.sh S01 S02 ...   (env PREVIEW, SPP, T)
D=$(cd "$(dirname "$0")/.." && pwd); B=${BLENDER:-/opt/blender/blender-5.2.2-linux-x64/blender}
mkdir -p "$D/out/board" "$D/out/logs"
for s in "$@"; do
  "$B" -b --python "$D/shots/board.py" -- $s ${T:-0.5} > "$D/out/logs/$s.log" 2>&1
  echo "$s $(grep -c RENDERED $D/out/logs/$s.log) $(grep -E 'Error|Traceback' $D/out/logs/$s.log | grep -v CUEW | head -2)"
done
