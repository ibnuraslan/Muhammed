#!/bin/bash
D=$(cd "$(dirname "$0")/.." && pwd)
while pgrep -f "queue2.sh" > /dev/null; do sleep 5; done
"$D/tools/sb.sh" sc5_parlour S22 S23 S26 S20 S21 S15 S16 S17
"$D/tools/sb.sh" sc5_cabin S09 S10 S12 S13 S14
"$D/tools/sb.sh" sc5_cabin_reuse S11
"$D/tools/sb.sh" sc5_sea S06 S07 S27 S28
