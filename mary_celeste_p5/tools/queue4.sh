#!/bin/bash
# all remaining storyboard stills (fixed shots re-rendered)
D=$(cd "$(dirname "$0")/.." && pwd)
"$D/tools/sb.sh" sc5_parlour S22 S23 S26 S20 S21 S15 S16 S17
"$D/tools/sb.sh" sc5_cabin S09 S10 S12 S13 S14
"$D/tools/sb.sh" sc5_cabin_reuse S11
"$D/tools/sb.sh" sc5_ports S24 S25
"$D/tools/sb.sh" sc5_sea S01 S02 S03 S04 S06 S07 S27 S28
echo QUEUE_DONE
