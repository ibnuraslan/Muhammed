#!/bin/bash
# Day-brightness check: render every day shot's storyboard frame again with the old (plain) light, then compare
# mean luminance of look vs plain -> review/daycheck.txt
cd /home/user/Muhammed/projects/phone-banker
source ~/render_env/env.sh
export PYTHONPATH=scenes:../../nvidia_doc/scenes
grep -vE ' (night|dusk|arrive)$' out/daycheck_list.txt | while read -r part name st mv secs rec var; do
  d=out/storyboard_plain/$part/$name; mkdir -p $d
  [ -f $d/plate.png ] || python edit/pb_exec.py $secs run $st $mv --still --t 0.5 --pct 25 --samples 12 --plain --out $d > $d.log 2>&1 || echo "FAIL $name"
  echo "done $name"
done
python3 - <<'PY'
from PIL import Image, ImageStat
import os
rows=[]
for line in open("out/daycheck_list.txt"):
    part,name,st,mv,secs,rec,var=line.split()
    if rec=="night" or var in ("dusk","arrive"): continue
    def L(p):
        im=Image.open(p).convert("RGB"); r,g,b=[c/255 for c in ImageStat.Stat(im).mean]
        return 0.2126*r+0.7152*g+0.0722*b
    lk=L(f"out/storyboard/{part}/{name}/plate.png"); pl=L(f"out/storyboard_plain/{part}/{name}/plate.png")
    flag = "LOW" if lk<0.18 else ""
    if lk < pl-0.02: flag += " DARKER"
    rows.append(f"{name:36s} {rec:5s} look {lk:.3f}  plain {pl:.3f}  {flag}")
open("review/daycheck.txt","w").write("\n".join(rows)+"\n"); print("\n".join(rows))
PY
