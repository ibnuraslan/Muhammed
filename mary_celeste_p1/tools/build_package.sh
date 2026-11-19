#!/bin/bash
# Build the RenderStreet farm package for Part 1: one compressed .blend per shot + shared textures + README + CapCut shot list,
# zipped and split into parts under 500 MB.
#   TIMINGS=vo_timings.json tools/build_package.sh [PKG_DIR] [S01 S02 ...]
# TIMINGS (optional): {"S01": 2.31, ...} VO-retimed durations in seconds. FARM_SPP (default 128).
D=$(cd "$(dirname "$0")/.." && pwd); B=${BLENDER:-/opt/blender/blender-5.2.2-linux-x64/blender}
PKG=${1:-$D/out/farm/mary_celeste_p1}; shift
mkdir -p "$PKG/shots" "$PKG/textures" "$D/out/logs"
IDS=${@:-$(python3 -c "import re;print(' '.join(re.findall(r'@shot\(\"(S\d+[a-z]?)\"', open('$D/shots.py').read())))")}
WIDE="S01 S13 S15 S18 S20 S25 S30 S41"
for s in $IDS; do
  if [[ " $WIDE " == *" $s "* ]]; then R=18; P=3; else R=14; P=2; fi
  EXPORT="$PKG" PREVIEW=0 OCEAN_RES=$R OCEAN_REPEAT=$P "$B" -b --python "$D/run_anim.py" -- $s > "$D/out/logs/export_$s.log" 2>&1
  echo "$s $(ls -la "$PKG/shots/$s.blend" 2>/dev/null | awk '{print $5}') $(grep -m1 -E 'CLIPRESULT|ABORT|Traceback|Error:' "$D/out/logs/export_$s.log" | grep -v CUEW)"
done
python3 "$D/tools/farm_docs.py" "$PKG"
du -sh "$PKG"
cd "$(dirname "$PKG")" && rm -f "$(basename "$PKG")".zip* && zip -qr -9 "$(basename "$PKG").zip" "$(basename "$PKG")" \
  && split -b 450m -d -a 2 "$(basename "$PKG").zip" "$(basename "$PKG").zip.part" && ls -la "$(basename "$PKG")".zip*
