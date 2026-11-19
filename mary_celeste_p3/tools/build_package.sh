#!/bin/bash
# RenderStreet package for Part 3: one compressed, keyframed .blend per shot + shared textures + README + CapCut list,
# zipped and split into parts under 500 MB.   tools/build_package.sh [PKG_DIR] [p3_01 p3_02 ...]
D=$(cd "$(dirname "$0")/.." && pwd); B=${BLENDER:-/opt/blender/blender-5.2.2-linux-x64/blender}
PKG=${1:-$D/out/farm/mary_celeste_p3}; shift
mkdir -p "$PKG/shots" "$PKG/textures" "$D/out/logs"
IDS=${@:-$(cd "$D" && python3 -c "import re;print(' '.join(re.findall(r'@shot\(\"(p3_[0-9a-z]+)\"', open('shots.py').read())))")}
for s in $IDS; do
  [ -f "$PKG/shots/$s.blend" ] && [ -z "$FORCE" ] && { echo "$s exists"; continue; }
  TIMINGS="$D/vo/vo_timings.json" EXPORT="$PKG" PREVIEW=0 "$B" -b --python "$D/anim_export.py" -- $s > "$D/out/logs/export_$s.log" 2>&1
  echo "$s $(ls -la "$PKG/shots/$s.blend" 2>/dev/null | awk '{print $5}') $(grep -E 'CLIPRESULT|ABORT|Traceback|Error:' "$D/out/logs/export_$s.log" | grep -v CUEW | tr '\n' ' ')"
done
echo EXPORT_DONE
