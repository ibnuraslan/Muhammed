#!/bin/bash
# Slim every shot file in place (edit/slim_shot.py); two workers: SLIM_WORKER=0|1 takes every other file.
cd /home/user/Muhammed/projects/phone-banker; source ~/render_env/env.sh
i=0
for f in out/blend/{intro,sting,ch1,ch2,ch3}/*.blend; do
  if [ $((i % 2)) -eq ${SLIM_WORKER:-0} ]; then
    python edit/slim_shot.py "$f" 2>&1 | grep -E "^\[(mesh|tex)\]|Error|Traceback" || echo "FAIL $f"
  fi
  i=$((i+1))
done
echo SLIM_DONE ${SLIM_WORKER:-0}
