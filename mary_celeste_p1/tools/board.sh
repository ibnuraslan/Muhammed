#!/bin/bash
# Storyboard frames: each shot in its own Blender process (PREVIEW res, low samples). Usage: tools/board.sh [S01 S02 ...]
D=$(cd "$(dirname "$0")/.." && pwd); B=${BLENDER:-/opt/blender/blender-5.2.2-linux-x64/blender}
mkdir -p "$D/out/board" "$D/out/logs"
IDS=${@:-$(python3 -c "import re;print(' '.join(re.findall(r'@shot\(\"(S\d+[a-z]?)\"', open('$D/shots.py').read())))")}
for s in $IDS; do
  t0=$(date +%s)
  PREVIEW=${PREVIEW:-0.5} SPP=${SPP:-24} OCEAN_RES=${OCEAN_RES:-18} "$B" -b --python "$D/run.py" -- $s > "$D/out/logs/$s.log" 2>&1
  echo "$s $(( $(date +%s) - t0 ))s $(grep -c RENDERED "$D/out/logs/$s.log") $(grep -m1 -E 'Error:|Exception|Traceback' -A0 "$D/out/logs/$s.log")"
done
