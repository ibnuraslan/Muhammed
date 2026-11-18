#!/bin/bash
# usage: tools_run.sh scene shot [shot...]   (env PREVIEW, SPP, HAIR pass through)
export PATH=/opt/blender/blender-5.2.2-linux-x64:$PATH
D=$(cd "$(dirname "$0")" && pwd); sc=$1; shift; mkdir -p $D/out/logs
for s in "$@"; do
  blender -b --python $D/scenes/$sc.py -- SHOT=$s > $D/out/logs/$s.log 2>&1
  if grep -q "^RENDERED" $D/out/logs/$s.log; then echo "ok $s"; else echo "FAIL $s"; grep -E "Error|Traceback" -A8 $D/out/logs/$s.log | grep -v CUEW | head -14; fi
done
