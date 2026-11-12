#!/bin/bash
# usage: looksheet.sh <outname> <list>   list lines "label|set|move|t" -> plain + cinematic EXR stills, then review/<outname>.jpg
cd /home/user/Muhammed
source ~/render_env/env.sh
export PYTHONPATH=projects/phone-banker/scenes:nvidia_doc/scenes
name=$1; list=$2; out=projects/phone-banker/out/$name; mkdir -p $out
args=()
i=0
while IFS='|' read -r label set move t; do
  [ -z "$label" ] && continue
  i=$((i+1)); d=$out/$(printf %02d $i)_${set}_${move}
  for mode in plain cine; do
    dd=${d}_$mode; flag=""; [ $mode = plain ] && flag="--plain"
    if [ ! -f $dd/plate.exr ]; then
      python nvidia_doc/scenes/run.py $set $move --still --t $t --pct ${PCT:-25} --samples ${SAMPLES:-12} --exr $flag --out $dd > $dd.log 2>&1 || echo "FAIL $set $move $mode"
    fi
  done
  args+=("$label" "${d}_plain" "${d}_cine")
done < $list
python nvidia_doc/scenes/look_sheet.py projects/phone-banker/review/$name.jpg "${args[@]}"
echo SHEET projects/phone-banker/review/$name.jpg
