#!/bin/bash
# Phase 1 rebuild: bash build_all.sh <build_dir>   (textures are read from <build_dir>/../tex; copy scripts/tex there)
set -e
B=/opt/blender/blender-5.2.2-linux-x64/blender; D=$(cd "$(dirname "$0")" && pwd); R=$D/../../..; BD=$1
mkdir -p $BD $BD/../tex && cp $D/tex/*.png $BD/../tex/
$B -b $R/blender/NoPilotPlane_v011/NoPilotPlane_v011_60fps.blend --python $D/01_base.py -- $BD
$B -b $BD/base.blend --python $D/02_anim.py -- $BD
