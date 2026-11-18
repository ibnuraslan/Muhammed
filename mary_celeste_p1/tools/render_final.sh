#!/bin/bash
# Final animated render of Part 1 shots (resumable: finished frames are skipped).
#   tools/render_final.sh [S01 S02 ...]        env: PREVIEW (0 = full 2560x1440), SPP (default 32)
# Aboard / interior shots use a lighter FFT sea (it is seen past rails); sea-level wides keep the full one.
D=$(cd "$(dirname "$0")/.." && pwd); B=${BLENDER:-/opt/blender/blender-5.2.2-linux-x64/blender}
mkdir -p "$D/out/logs"
IDS=${@:-$(python3 -c "import re;print(' '.join(re.findall(r'@shot\(\"(S\d+[a-z]?)\"', open('$D/shots.py').read())))")}
WIDE="S01 S13 S15 S18 S20 S25 S30 S41"
for s in $IDS; do
  if [[ " $WIDE " == *" $s "* ]]; then R=18; P=3; else R=14; P=2; fi
  t0=$(date +%s)
  PREVIEW=${PREVIEW:-0} SPP=${SPP:-32} OCEAN_RES=$R OCEAN_REPEAT=$P "$B" -b --python "$D/run_anim.py" -- $s > "$D/out/logs/final_$s.log" 2>&1
  echo "$s $(( $(date +%s) - t0 ))s $(ls "$D/out/frames/$s" 2>/dev/null | wc -l) frames $(grep -m1 -E 'Traceback|Error:' "$D/out/logs/final_$s.log")"
done
