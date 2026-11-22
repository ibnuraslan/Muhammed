#!/bin/bash
# Farm package for one intro film (rules: FARM_DELIVERY_RULES.md): animated shots exported, each re-saved fully
# self-contained (textures packed), a small MASTER.blend linking them, README + CapCut shot list, one normal zip.
#   tools/package_film.sh f1
set -e
D=$(cd "$(dirname "$0")/.." && pwd); B=${BLENDER:-/opt/blender/blender-5.2.2-linux-x64/blender}
F=$1; NAME=$(python3 -c "print({'f1':'01_lamp_room','f2':'02_dead_letters','f3':'03_the_locksmith','f4':'04_salvage'}['$F'])")
EXP=$D/out/farm/export_$F; PKG=$D/out/farm/seldom_intro_$NAME
mkdir -p "$EXP" "$PKG/shots" "$D/out/logs"
for s in ${SHOTS:-A B C D}; do
  EXPORT="$EXP" "$B" -b --factory-startup -P "$D/run_anim.py" -- $F $s > "$D/out/logs/export_$F$s.log" 2>&1 || true
  echo "$F$s $(grep -E 'CLIPRESULT|SETTLE|ABORT|Traceback|Error:|EXPORTED' "$D/out/logs/export_$F$s.log" | grep -v CUEW | tr '\n' ' ')"
  "$B" -b "$EXP/shots/$F$s.blend" -P "$D/../mary_celeste_p4/tools/pack_shot.py" -- "$PKG/shots/$F$s.blend" 2>&1 | grep -E "PACKED|Error" | grep -v CUEW
done
"$B" -b --factory-startup -P "$D/tools/build_master.py" -- $F "$PKG" 2>&1 | grep -E "STRIP|MASTER|Error|Traceback" | grep -v CUEW
python3 "$D/tools/film_docs.py" $F "$PKG"
cp "$D/CREDITS.txt" "$PKG/"
(cd "$D/out/farm" && rm -f "seldom_intro_$NAME.zip" && zip -qr -0 "seldom_intro_$NAME.zip" "seldom_intro_$NAME" && ls -la "seldom_intro_$NAME.zip")
echo PACKAGE_DONE $F
