#!/bin/bash
# Bake every shot (REVERSE=1 walks each part from the end, so a second worker can run alongside; .lock files) of the film, timed to its cut (vo/timing.json), one at a time (parallel builds run out of memory).
#   edit/bake_all.sh [part ...]   -> out/blend/<part>/<shot>.blend ; the sting -> out/blend/sting/seldom_sting.blend
cd /home/user/Muhammed/projects/phone-banker
source ~/render_env/env.sh
export PYTHONPATH=scenes:../../nvidia_doc/scenes
parts=${@:-sting intro ch1 ch2 ch3}
for part in $parts; do
  out=$PWD/out/blend/$part; mkdir -p $out
  if [ $part = sting ]; then
    [ -f $out/seldom_sting.blend ] || python edit/pb_exec.py 6.0 bake logo bag --out $out --name seldom_sting --samples 32 > $out/seldom_sting.log 2>&1 || echo "FAIL seldom_sting"
    echo "baked seldom_sting"; continue
  fi
  python3 -c "
import json,sys
for r in json.load(open('vo/timing.json'))['$part']['shots']: print(r['name'], r['set'], r['move'], r['seconds'])" > $out/jobs.txt
  while read -r name st mv secs; do
    [ -f $out/$name.blend ] || [ -f $out/$name.lock ] || { touch $out/$name.lock; python edit/pb_exec.py $secs bake $st $mv --out $out --name $name --samples 32 > $out/$name.log 2>&1 || echo "FAIL $name"; rm -f $out/$name.lock; }
    echo "baked $name"
  done < <(if [ -n "$REVERSE" ]; then tac $out/jobs.txt; else cat $out/jobs.txt; fi)
done
