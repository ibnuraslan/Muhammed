#!/bin/bash
# Build + board-render every shot of a part:  tools/batch.sh P1 [S01 S02 ...]
D=$(cd "$(dirname "$0")/.." && pwd); PART=$1; shift
IDS=${@:-$(python3 -c "import re;print(' '.join(re.findall(r'\(\"([A-Z]\d+)\"', open('$D/scenes/${PART,,}.py').read())))")}
mkdir -p "$D/out/${PART,,}/logs"
for s in $IDS; do
  L="$D/out/${PART,,}/logs/$s.log"
  PREVIEW=${PREVIEW:-0.25} HAIR=${HAIR:-0.5} blender -b --python "$D/tools/shot.py" -- $PART $s > "$L" 2>&1
  echo "$s $(grep -oE 'CLIPCHECK[^,]*' "$L" | head -1) $(grep -c Traceback "$L") tb $(grep -oE '"render_s": [0-9.]+' "$L")"
done
