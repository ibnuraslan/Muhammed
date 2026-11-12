#!/bin/bash
# run qa_hands.py over every shot in the chapter lists, one process per set; report in out/qa_hands.txt
cd /home/user/Muhammed
source ~/render_env/env.sh
export PYTHONPATH=projects/phone-banker/scenes:nvidia_doc/scenes
L=projects/phone-banker/scenes
python3 - > /tmp/claude-0/-home-user-Muhammed/f9e50632-c631-5881-82fb-617944a2f28d/scratchpad/qa_jobs.txt <<'PY'
import collections
jobs = collections.OrderedDict()
for f in ("intro", "ch1", "ch2", "ch3"):
    for line in open(f"projects/phone-banker/scenes/{f}.list"):
        if "|" not in line: continue
        label, st, mv, t = line.strip().split("|")
        jobs.setdefault(st, collections.OrderedDict()).setdefault(mv, set()).update(t.split(","))
for st, mvs in jobs.items():
    print(st, " ".join(f"{m}:{','.join(sorted(ts))}" for m, ts in mvs.items()))
PY
out=projects/phone-banker/out/qa_hands.txt; : > $out
while read -r st rest; do
  python $L/qa_hands.py $st $rest 2>&1 | grep -E "^QA|Traceback|Error" >> $out
done < /tmp/claude-0/-home-user-Muhammed/f9e50632-c631-5881-82fb-617944a2f28d/scratchpad/qa_jobs.txt
echo QA_DONE
