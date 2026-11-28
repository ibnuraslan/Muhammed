#!/bin/bash
# Render storyboard key frames, one Blender process per shot (a failing shot doesn't stop the batch).
#   SCRATCH=... OUT=... ./run_sb.sh sb_p1.py P1-01 P1-02 ...   (no IDs = every 3D shot in the file)
SCRIPT=$1; shift
cd "$(dirname "$0")"
IDS="$@"
if [ -z "$IDS" ]; then IDS=$(python3 -c "import re;print(' '.join(re.findall(r'\"(P\d-\d\d)\": s', open('$SCRIPT').read())))"); fi
for s in $IDS; do
  SHOT=$s blender -b --python $SCRIPT > "$OUT/$s.log" 2>&1
  r=$(grep -E "^LUMA" "$OUT/$s.log" || grep -E "Error|rror:" "$OUT/$s.log" | grep -v CUEW | tail -1)
  echo "$s: ${r:-done}"
done
