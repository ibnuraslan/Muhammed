#!/bin/bash
# renders sections in order; waits for any running cap3 first
cd "$(dirname "$0")"
for s in "$@"; do
  while pgrep -f "node cap3.js [0-9]+ out " >/dev/null; do sleep 20; done
  node cap3.js $s out 4 all > sec$s.log 2>&1
done
