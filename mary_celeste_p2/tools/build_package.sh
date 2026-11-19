#!/bin/bash
# Build the RenderStreet farm package for Part 2: one compressed .blend per shot (animated, VO-timed) + shared textures
# (2K max) + README + CapCut shot list, zipped and split into parts under 500 MB.
#   tools/build_package.sh [PKG_DIR] [01 02 ...]        (no ids: every shot in shots.py)
#   ZIP=0 to skip the zip step (export only).
D=$(cd "$(dirname "$0")/.." && pwd); B=${BLENDER:-/opt/blender/blender-5.2.2-linux-x64/blender}
PKG=${1:-$D/out/farm/mary_celeste_p2}; shift
mkdir -p "$PKG/shots" "$PKG/textures" "$D/out/logs"
IDS=${@:-$(cd "$D" && python3 -c "import shots;print(' '.join(s[0] for s in shots.SHOTS))")}
for s in $IDS; do
  sc=$(cd "$D" && python3 -c "import shots;print([x[1] for x in shots.SHOTS if x[0]=='$s'][0])")
  ANIM=$s EXPORT="$PKG" PREVIEW=0 "$B" -b --python "$D/scenes/$sc.py" -- SHOT=$s > "$D/out/logs/export_$s.log" 2>&1
  echo "$s $(ls -la "$PKG/shots/$s.blend" 2>/dev/null | awk '{print $5}') $(grep -m1 -E 'CLIPRESULT|ABORT|Traceback|Error:' "$D/out/logs/export_$s.log" | grep -v CUEW)"
done
python3 "$D/tools/farm_docs.py" "$PKG"
du -sh "$PKG"
[ "${ZIP:-1}" = "0" ] && exit 0
cd "$(dirname "$PKG")" && rm -f "$(basename "$PKG")".zip* && zip -qr -9 "$(basename "$PKG").zip" "$(basename "$PKG")" \
  && split -b 450m -d -a 2 "$(basename "$PKG").zip" "$(basename "$PKG").zip.part" && ls -la "$(basename "$PKG")".zip*
