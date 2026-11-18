#!/bin/bash
# Final look frames, 2560x1440 Cycles (CPU). Run from anywhere.
D=$(cd "$(dirname "$0")/.." && pwd); mkdir -p "$D/out"; B=${BLENDER:-/opt/blender/blender-5.2.2-linux-x64/blender}
for s in ${@:-sc_b_cabin sc_c_rail sc_a_sighting}; do
  echo "== $s $(date +%T)"; "$B" -b --python "$D/scenes/$s.py" > "$D/out/$s.log" 2>&1; grep -E "RENDERED|Error" "$D/out/$s.log"
done
