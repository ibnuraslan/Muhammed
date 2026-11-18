#!/bin/bash
# P5's clipping check on every P4 shot with a character (no render). Summary: out/clip/summary.txt
D=$(cd "$(dirname "$0")/.." && pwd); B=${BLENDER:-/opt/blender/blender-5.2.2-linux-x64/blender}
mkdir -p "$D/out/clip"; : > "$D/out/clip/summary.txt"
for s in ${@:-S03 S09 S10 S16 S17 S21 S31 S33 S35}; do
  for t in 0.0 0.5 1.0; do
    CLIPONLY=1 PREVIEW=0.25 HAIR=0 "$B" -b --python "$D/shots/board.py" -- $s $t > "$D/out/clip/${s}_$t.log" 2>&1
    l=$(grep -E "^CLIPCHECK|Traceback" "$D/out/clip/${s}_$t.log" | head -1); echo "$s t=$t $l" | tee -a "$D/out/clip/summary.txt"
  done
done
echo CLIPALL_DONE
