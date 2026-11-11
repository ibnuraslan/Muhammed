#!/bin/bash
# usage: stills.sh outdir set:move[:t] ...   (25% res, 8 samples; skips existing)
OUT0=$(realpath -m "$1"); cd /home/user/Muhammed; source ~/render_env/env.sh
OUT=$OUT0; shift; mkdir -p $OUT
for sm in "$@"; do
  IFS=: read set mv t <<< "$sm"; t=${t:-0.5}
  d=$OUT/${set}_${mv}; [ -f $d/plate.png ] && continue
  PYTHONPATH=projects/killer-in-house/scenes:nvidia_doc/scenes python nvidia_doc/scenes/run.py $set $mv --still --t $t --pct ${PCT:-25} --samples ${SAMPLES:-8} --out $d > $d.log 2>&1 || echo "FAIL $sm"
  grep -q "Traceback" $d.log && { echo "ERR $sm"; grep -A3 "Error" $d.log | tail -4; }
  echo "done $sm"
done
