#!/bin/bash
# Rebuild the Phase-1 scene from the source packages and assets. Run from MosquitoDoctor_v001/.
set -e
B=/opt/blender/blender-5.2.2-linux-x64/blender
mkdir -p work
$B -b --factory-startup --python scripts/01_chars.py -- work/chars.blend 2>&1 | grep -E "EYEFIX|CHAR|rror" || true
$B -b work/chars.blend --python scripts/02_set.py -- work/scene.blend 2>&1 | grep -E "SET done|rror" || true
$B -b work/scene.blend --python scripts/03_anim.py -- work/anim.blend 2>&1 | grep -E "REACH|LAND|ANIM|rror" || true
$B -b work/anim.blend --python scripts/04_cams.py -- work/cams.blend 2>&1 | grep -E "CAMS|LOGO|rror" || true
