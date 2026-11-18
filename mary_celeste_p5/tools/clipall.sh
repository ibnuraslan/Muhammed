#!/bin/bash
# clipping check (no render) on every shot with characters; summary in out/clip/summary.txt
D=$(cd "$(dirname "$0")/.." && pwd); B=${BLENDER:-/opt/blender/blender-5.2.2-linux-x64/blender}
mkdir -p "$D/out/clip"; : > "$D/out/clip/summary.txt"
run() { sc=$1; shift; for s in "$@"; do
  CLIPONLY=1 PREVIEW=0.5 HAIR=0.0 SHOT=$s OUT=/tmp/clip_$s.png "$B" -b --python "$D/scenes/$sc.py" > "$D/out/clip/$s.log" 2>&1
  l=$(grep -E "^CLIPCHECK|Traceback" "$D/out/clip/$s.log" | head -1); echo "$s $l" | tee -a "$D/out/clip/summary.txt"; done; }
run sc5_sea ${SEA:-S01 S02 S04 S05 S06 S07 S08 S27}
run sc5_parlour ${PAR:-S22 S23 S26 S20 S21}
echo CLIPALL_DONE
