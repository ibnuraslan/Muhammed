#!/bin/bash
# re-render after the clipping fixes, the approved character and the weathered paint
D=$(cd "$(dirname "$0")/.." && pwd)
"$D/tools/sb.sh" sc5_sea S01 S02 S03 S04 S05 S06 S07 S08 S27
"$D/tools/sb.sh" sc5_parlour S22 S23 S26 S21 S15
"$D/tools/sb.sh" sc5_ports S24 S25
"$D/tools/sb.sh" sc5_cabin_reuse S11
"$D/tools/sb.sh" sc5_cabin S12
echo QUEUE6_DONE
