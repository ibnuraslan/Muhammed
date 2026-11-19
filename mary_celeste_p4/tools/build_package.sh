#!/bin/bash
# RenderStreet package for Part 4 (same layout as Part 1): one compressed .blend per shot + shared 2K textures +
# README + CapCut shot list; zipped and split into parts under 500 MB.   tools/build_package.sh [PKG] [S01 ...]
D=$(cd "$(dirname "$0")/.." && pwd); B=${BLENDER:-/opt/blender/blender-5.2.2-linux-x64/blender}
PKG=${1:-$D/out/farm/mary_celeste_p4}; shift
mkdir -p "$PKG/shots" "$PKG/textures" "$D/out/logs"
IDS=${@:-$(python3 -c "import sys;sys.path.insert(0,'$D/tools');from shots_vo import SHOTS;print(' '.join(s for s,_,_ in SHOTS))")}
for s in $IDS; do
  EXPORT="$PKG" TIMINGS="$D/vo/vo_timings.json" "$B" -b --python "$D/run_anim.py" -- $s > "$D/out/logs/export_$s.log" 2>&1
  echo "$s $(ls -la "$PKG/shots/$s.blend" 2>/dev/null | awk '{print $5}') $(grep -E 'CLIPRESULT|SETTLE|ABORT|Traceback|Error:|settle too' "$D/out/logs/export_$s.log" | grep -v CUEW | tr '\n' ' ')"
done
echo EXPORT_DONE
