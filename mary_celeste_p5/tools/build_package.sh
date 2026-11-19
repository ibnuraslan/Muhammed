#!/bin/bash
# Build the RenderStreet farm package for Part 5 (as Part 1's tools/build_package.sh): one compressed .blend per shot
# (built, animated to the VO timing, clip-checked) + shared textures (2K max) + README + CapCut shot list, zipped and
# split into parts under 500 MB.
#   tools/build_package.sh [PKG_DIR] [S01 S02 ...]
D=$(cd "$(dirname "$0")/.." && pwd); B=${BLENDER:-/opt/blender/blender-5.2.2-linux-x64/blender}
PKG=${1:-$D/out/farm/mary_celeste_p5}; shift
export TIMINGS=${TIMINGS:-$D/vo/vo_timings.json}
mkdir -p "$PKG/shots" "$PKG/textures" "$D/out/logs"
IDS=${@:-$(python3 -c "import sys; sys.path.insert(0,'$D'); from shots import SHOTS; print(' '.join(s[0] for s in SHOTS))")}
for s in $IDS; do
  EXPORT="$PKG" PREVIEW=0 "$B" -b --python "$D/tools/run_anim5.py" -- $s > "$D/out/logs/export_$s.log" 2>&1
  echo "$s $(ls -la "$PKG/shots/$s.blend" 2>/dev/null | awk '{print $5}') $(grep -m1 -E 'CLIPRESULT|ABORT|Traceback|Error:' "$D/out/logs/export_$s.log" | grep -v CUEW)"
done
python3 "$D/tools/farm_docs5.py" "$PKG" "$TIMINGS"
du -sh "$PKG"
cd "$(dirname "$PKG")" && rm -f "$(basename "$PKG")".zip* && zip -qr -9 "$(basename "$PKG").zip" "$(basename "$PKG")" \
  && split -b 300m -d -a 2 "$(basename "$PKG").zip" "$(basename "$PKG").zip.part" && ls -la "$(basename "$PKG")".zip*
