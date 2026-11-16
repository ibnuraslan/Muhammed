#!/bin/bash
# full rebuild: chars -> sets -> anim -> look.  bash build_all.sh [timing.json]
set -e
B=/opt/blender/blender-5.2.2-linux-x64/blender; D=$(cd "$(dirname "$0")" && pwd)
BD=/tmp/claude-0/-home-user-Muhammed/afc59c0d-b246-5d2b-9c60-d9e8e627f8a2/scratchpad/build
$B -b --python $D/01_chars.py 2>&1 | grep -E "MASK|HAT|LOGO|EYEFIX|rror" || true
$B -b $BD/chars.blend --python $D/02_sets.py 2>&1 | grep -E "SKEL|SETS|WALL|rror" || true
$B -b $BD/sets.blend --python $D/03_anim.py ${1:+-- $1} 2>&1 | grep -E "ANIM saved|rror|line [0-9]" || true
$B -b $BD/anim.blend --python $D/../../pipeline/anim_look.py -- $BD/look.blend --no-sky 2>&1 | grep -E "saved|rror" || true
