#!/bin/bash
# usage: testshots.sh <set> <outdir> <t> move1 move2 ...   (quick stills, 25 %, 8 samples) then a contact sheet
cd /home/user/Muhammed
source ~/render_env/env.sh
export PYTHONPATH=projects/phone-banker/scenes:nvidia_doc/scenes
set=$1; out=$2; t=$3; shift 3
args=()
for m in "$@"; do
  python nvidia_doc/scenes/run.py $set $m --still --t $t --pct ${PCT:-25} --samples ${SAMPLES:-8} --out $out/${set}_${m} > $out/${set}_${m}.log 2>&1 || { echo "FAIL $m"; grep -A12 Traceback $out/${set}_${m}.log | tail -14; }
  grep -q Traceback $out/${set}_${m}.log && { echo "ERR $m"; grep -A14 Traceback $out/${set}_${m}.log | tail -16; }
  args+=("$m" "$out/${set}_${m}/plate.png")
done
python projects/phone-banker/scenes/sheet.py $out/${set}_contact.jpg "${args[@]}"
