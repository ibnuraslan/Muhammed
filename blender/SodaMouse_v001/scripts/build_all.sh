#!/bin/bash
# full rebuild: chars -> sets -> anim -> lights -> look.  bash build_all.sh [timing.json]
set -e
B=/opt/blender/blender-5.2.2-linux-x64/blender; D=$(cd "$(dirname "$0")" && pwd)
BD=/tmp/claude-0/-home-user-Muhammed/42cd8012-c585-5c92-a02e-905559899f7c/scratchpad/build
$B -b --python $D/01_chars.py 2>&1 | grep -E "SLEEVE|LOGO|rror" || true
$B -b $BD/chars.blend --python $D/02_sets.py 2>&1 | grep -E "MOUSE|SETS|rror" || true
$B -b $BD/sets.blend --python $D/03_anim.py ${1:+-- $1} 2>&1 | grep -E "ANIM|rror|line [0-9]" || true
$B -b $BD/anim.blend --python $D/04_lights.py 2>&1 | grep -E "rror" | grep -v CUEW || true
$B -b $BD/lit.blend --python $D/../../pipeline/anim_look.py -- $BD/look.blend 2>&1 | grep -E "saved|rror" || true
