#!/bin/bash
# full rebuild: chars -> sets -> anim -> lights -> look.  bash build_all.sh [timing.json]
set -e
B=/opt/blender/blender-5.2.2-linux-x64/blender; D=$(cd "$(dirname "$0")" && pwd)
BD=/tmp/claude-0/-home-user-Muhammed/0b019bde-e3b5-5ca9-9067-8cf46a4c300e/scratchpad/build
$B -b $BD/cast.blend --python $D/01_chars.py 2>&1 | grep -E "ISLANDS|rror" || true
$B -b $BD/chars.blend --python $D/02_sets.py 2>&1 | grep -E "SETS|rror" || true
$B -b $BD/sets.blend --python $D/03_anim.py ${1:+-- $1} 2>&1 | grep -E "ANIM|rror|line [0-9]" || true
$B -b $BD/anim.blend --python $D/04_lights.py 2>&1 | grep -E "LIT|rror" | grep -v CUEW || true
$B -b $BD/lit.blend --python $D/../../pipeline/anim_look.py -- $BD/look.blend --no-sky 2>&1 | grep -E "saved|rror" || true
