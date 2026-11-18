#!/bin/bash
D=$(cd "$(dirname "$0")/.." && pwd)
while pgrep -f "sb.sh sc5_sea S01" > /dev/null; do sleep 5; done
"$D/tools/sb.sh" sc5_cabin S09 S10 S12 S13 S14
"$D/tools/sb.sh" sc5_cabin_reuse S11
"$D/tools/sb.sh" sc5_parlour S15 S16 S17 S18 S19 S20 S21 S22 S23 S26
"$D/tools/sb.sh" sc5_ports S24 S25
"$D/tools/sb.sh" sc5_sea S01 S02 S03 S04
