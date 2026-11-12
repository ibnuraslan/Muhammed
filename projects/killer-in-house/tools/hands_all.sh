#!/bin/bash
# hand QA over every shot of every chapter (one lane): out/hands/<set>_<move>/hand_*.png
cd /home/user/Muhammed; source ~/render_env/env.sh
python3 -c "
import sys; sys.path.insert(0,'projects/killer-in-house/scenes'); import shots
seen=set()
for ch in ('intro','ch1','ch2','ch3'):
    for s,m,t,l in shots.CHAPTERS[ch]:
        if (s,m) in seen: continue
        seen.add((s,m)); print(s,m,t)
" | while read s m t; do
  d=projects/killer-in-house/out/hands/${s}_${m}; [ -f $d/plate.png ] && continue
  PYTHONPATH=projects/killer-in-house/scenes:nvidia_doc/scenes python projects/killer-in-house/tools/hand_check.py $s $m $t projects/killer-in-house/out/hands > /tmp/claude-0/-home-user-Muhammed/77d3c258-23a4-527f-9325-3fee51066791/scratchpad/hand_${s}_${m}.log 2>&1 || echo "FAIL $s $m"
  grep "\[hands\]" /tmp/claude-0/-home-user-Muhammed/77d3c258-23a4-527f-9325-3fee51066791/scratchpad/hand_${s}_${m}.log
done
