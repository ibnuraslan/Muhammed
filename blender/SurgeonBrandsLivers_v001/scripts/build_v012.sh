#!/bin/bash
# v012 build chain on the director's v011 package (VO timing). Usage: build_v012.sh <v011.blend> <workdir>
set -e
S=$(cd "$(dirname "$0")" && pwd); IN=$1; W=$2; B=${BLENDER:-/opt/bin/blender}
$B -b $IN --python $S/20_v012_or.py -- $W/a_or.blend
$B -b $W/a_or.blend --python $S/21_v012_looks.py -- $W/b_looks.blend
$B -b $W/b_looks.blend --python $S/25_v014b_garments.py -- $W/b2_cloth.blend
$B -b $W/b2_cloth.blend --python $S/22_v012_anim.py -- $W/c_anim.blend
$B -b $W/c_anim.blend --python $S/24_v014_brand.py -- $W/c2_brand.blend
$B -b $W/c2_brand.blend --python $S/23_v012_camera.py -- $W/d_cam.blend
