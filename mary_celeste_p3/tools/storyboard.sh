#!/bin/bash
# Storyboard stills: one real Cycles frame per shot (low samples), into review/.
D=$(cd "$(dirname "$0")/.." && pwd); B=${BLENDER:-/opt/blender/blender-5.2.2-linux-x64/blender}
mkdir -p "$D/review" "$D/out/logs"
SH=${@:-$(cd "$D" && python3 -c "import re;print(' '.join(re.findall(r'@shot\(\"(p3_[0-9a-z]+)\"', open('shots.py').read())))")}
for s in $SH; do
  T=0.5; [ "$s" = "p3_22" ] && T=0.4
  [ -f "$D/review/$s.png" ] && [ -z "$FORCE" ] && continue
  PREVIEW=${PREVIEW:-0.5} SPP=${SPP:-32} OUT="$D/review/$s.png" "$B" -b --python "$D/render.py" -- $s $T > "$D/out/logs/$s.log" 2>&1
  echo "$s $(grep -oE 'RENDERED .* [0-9]+s' "$D/out/logs/$s.log" | awk '{print $NF}') $(grep -c Error "$D/out/logs/$s.log")"
done
