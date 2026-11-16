#!/bin/bash
# bash build.sh [beats]  -> work/look.blend
set -e
B=/opt/blender/blender-5.2.2-linux-x64/blender; D=$(cd "$(dirname "$0")" && pwd)
W=/tmp/claude-0/-home-user-Muhammed/80503e31-c2cf-50aa-88df-299f2fd2a88d/scratchpad/work
$B -b $W/sets.blend --python $D/03_anim.py -- $W/anim.blend $1 2>&1 | grep -E "PINCH .* err [1-9]|ANIM_OK|Error|rror|line [0-9]" || true
$B -b $W/anim.blend --python $D/04_lights.py -- $W/lit.blend 2>&1 | grep -E "rror" || true
$B -b $W/lit.blend --python $D/../../pipeline/anim_look.py -- $W/look.blend 2>&1 | grep -E "saved|rror" || true
