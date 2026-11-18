#!/bin/bash
# shots without Sarah/Sophia/Arthur (held for the shared women v2): bring them up to date
D=$(cd "$(dirname "$0")/.." && pwd)
"$D/tools/sb.sh" sc5_parlour S15 S21
"$D/tools/sb.sh" sc5_ports S24 S25
"$D/tools/sb.sh" sc5_cabin_reuse S11
"$D/tools/sb.sh" sc5_cabin S12
echo QUEUE7_DONE
