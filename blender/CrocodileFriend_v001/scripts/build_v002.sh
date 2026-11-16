#!/bin/bash
# Full Phase-2 build: sets.blend -> anim -> look -> trim to VO -> pack -> shrink -> farm package in ../CrocodileFriend_v002/
set -e
cd "$(dirname "$0")/.."
B=${BLENDER:-/opt/blender/blender-5.2.2-linux-x64/blender}
V=$PWD/../CrocodileFriend_v002
$B -b work/sets.blend -P scripts/04_anim.py -- work/film.blend 2>&1 | grep -E "DONE|rror" || true
$B -b work/film.blend --python ../pipeline/anim_look.py -- work/look_base.blend --no-sky 2>&1 | grep -i "error" || true
$B -b work/look_base.blend -P scripts/05_look.py -- work/look.blend 2>&1 | grep -E "LOOK2|rror" || true
$B -b work/look.blend -P scripts/06_to_vo.py -- $V/CrocodileFriend_v002_VO.mp3 work/vo.blend $V/beats.json 2>&1 | grep -E "VO_DONE|rror" || true
$B -b work/vo.blend --python ../pipeline/package_for_farm.py -- $PWD/work/vo_packed.blend 2>&1 | grep -E "PROBLEMS" || true
$B -b work/vo_packed.blend -P scripts/07_shrink.py -- work/vo_small.blend 2>&1 | grep -E "SHRUNK|rror" || true
$B -b work/vo_small.blend --python ../pipeline/package_for_farm.py -- $V/CrocodileFriend_v002_60fps.blend 2>&1 | grep -E "FARM|PROBLEMS|rror" || true
rm -f $V/*.blend1
ls -la $V/CrocodileFriend_v002_60fps.blend
