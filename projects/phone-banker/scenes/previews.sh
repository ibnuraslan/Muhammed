#!/bin/bash
# usage: previews.sh <name> <listfile>   list lines: "<label>|<set>|<move>|<t>"   -> out/<name>/<n>.png and review/<name>.jpg
cd /home/user/Muhammed
source ~/render_env/env.sh
export PYTHONPATH=projects/phone-banker/scenes:nvidia_doc/scenes
name=$1; list=$2; out=projects/phone-banker/out/$name; mkdir -p $out
args=()
i=0
while IFS='|' read -r label set move t; do
  [ -z "$label" ] && continue
  i=$((i+1)); d=$out/$(printf %02d $i)_${set}_${move}
  if [ ! -f $d/plate.png ]; then
    python nvidia_doc/scenes/run.py $set $move --still --t $t --pct ${PCT:-50} --samples ${SAMPLES:-20} --out $d > $d.log 2>&1 || echo "FAIL $set $move"
  fi
  args+=("$label" "$d/plate.png")
done < $list
python projects/phone-banker/scenes/titled_sheet.py projects/phone-banker/review/${name}.jpg "${args[@]}"
echo "SHEET projects/phone-banker/review/${name}.jpg"
