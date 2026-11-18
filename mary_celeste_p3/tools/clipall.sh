#!/bin/bash
# Clipping check (no render) on every Part 3 shot with characters (P5's clipcheck). Summary: out/clip/summary.txt
D=$(cd "$(dirname "$0")/.." && pwd); B=${BLENDER:-/opt/blender/blender-5.2.2-linux-x64/blender}
mkdir -p "$D/out/clip"; : > "$D/out/clip/summary.txt"
SH=${@:-$(cd "$D" && python3 -c "import re;print(' '.join(re.findall(r'@shot\(\"(p3_[0-9a-z]+)\"', open('shots.py').read())))")}
for s in $SH; do
  for T in ${TS:-0.0 0.5 1.0}; do
    CLIPONLY=1 HAIR=0.05 PREVIEW=0.1 OUT=/tmp/clip.png "$B" -b --python "$D/render.py" -- $s $T > "$D/out/clip/${s}_$T.log" 2>&1
    l=$(grep -E "^CLIPCHECK|Traceback|Error:" "$D/out/clip/${s}_$T.log" | grep -v CUEW | head -1); echo "$s t=$T $l" | tee -a "$D/out/clip/summary.txt"
  done
done
echo CLIPALL_DONE
