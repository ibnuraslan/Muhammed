#!/bin/bash
# last storyboard pass: shots fixed while queue4 ran
D=$(cd "$(dirname "$0")/.." && pwd)
while pgrep -f "queue4.sh" > /dev/null; do sleep 5; done
"$D/tools/sb.sh" sc5_sea S01 S02
"$D/tools/sb.sh" sc5_cabin_reuse S11
"$D/tools/sb.sh" sc5_cabin S12
"$D/tools/sb.sh" sc5_parlour S15 S21 S22 S23 S26
"$D/tools/sb.sh" sc5_ports S25
echo QUEUE5_DONE
