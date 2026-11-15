#!/bin/bash
# Rebuild the Phase-1 scene from the source packages and assets. Run from BatBite_v001/.
set -e
B=/opt/blender/blender-5.2.2-linux-x64/blender
$B -b --factory-startup --python scripts/01_chars.py -- work/chars_raw.blend 2>&1 | grep -E "EYEFIX|rror" || true
$B -b work/chars_raw.blend --python scripts/02_chars_fix.py -- work/chars.blend 2>&1 | grep -E "SCALE|SHOES|EYEFIX|rror" || true
$B -b work/chars.blend --python scripts/03_bat.py -- work/chars_bat.blend 2>&1 | grep -E "BAT|rror" || true
$B -b work/chars_bat.blend --python scripts/04_set.py -- work/scene.blend 2>&1 | grep -E "SET|rror" || true
$B -b work/scene.blend --python scripts/05_anim.py -- work/anim.blend 2>&1 | grep -E "GRIP|LAND|REACH|MATT|MASK|ANIM|rror|line [0-9]" || true
