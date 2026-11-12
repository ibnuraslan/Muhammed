#!/bin/bash
# Storyboard: one still per shot (at the middle of its cut, timed like the bake), a labelled sheet per part.
#   edit/storyboard.sh [part ...]   -> review/storyboard_<part>.jpg
cd /home/user/Muhammed/projects/phone-banker
source ~/render_env/env.sh
export PYTHONPATH=scenes:../../nvidia_doc/scenes
parts=${@:-intro ch1 ch2 ch3}
for part in $parts; do
  out=out/storyboard/$part; mkdir -p $out
  python3 - "$part" > $out/jobs.txt <<'PY'
import json, sys
T = json.load(open("vo/timing.json"))[sys.argv[1]]
for r in T["shots"]:
    sid, desc = r["label"].split(" ", 1)
    print(r["name"], r["set"], r["move"], r["seconds"], f'{sid}  at {r["start"]:.1f}s  len {r["seconds"]:.1f}s  {desc}')
PY
  args=()
  while read -r name st mv secs label; do
    d=$out/$name
    if [ ! -f $d/plate.png ]; then
      python edit/pb_exec.py $secs run $st $mv --still --t 0.5 --pct ${PCT:-25} --samples ${SAMPLES:-12} --out $d > $d.log 2>&1 || echo "FAIL $name"
    fi
    args+=("$label" "$d/plate.png")
  done < $out/jobs.txt
  python scenes/titled_sheet.py review/storyboard_$part.jpg "${args[@]}" 2>/dev/null || python scenes/sheet.py review/storyboard_$part.jpg "${args[@]}"
  echo "SHEET review/storyboard_$part.jpg"
done
