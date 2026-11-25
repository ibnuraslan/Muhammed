#!/bin/bash
# Full rebuild of the BeethovenDeaf v011 package + preview.
# build_all.sh <scratch_dir>   (needs scratch/src_assets.blend from extract.py and the MPFB garment packs from fetch_assets.sh)
set -e
W=${1:?scratch dir}; HERE=$(cd "$(dirname "$0")" && pwd); PKG=$(dirname "$HERE"); BL=/opt/blender/blender-5.2.2-linux-x64/blender
BR=$HERE/../../assets/brand; VO=$PKG/BeethovenDeaf_v011_VO.mp3
$BL -b --python $HERE/01_build.py -- $W/src_assets.blend $BR/DaKrasFilms_logo_dark.png $BR/DaKrasFilms_logo_white.png $W/stageA.blend 2>&1 | grep -E "BUILD_OK|Error|Traceback" 
$BL -b $W/stageA.blend --python $HERE/02_animate.py -- $VO $W/stageB.blend $W/src_assets.blend 2>&1 | grep -E "^LOG|ANIM_OK|Error|Traceback" | grep -v "pad verts" > $W/anim.log
grep -E "ANIM_OK|Error|Traceback|misses|MISS \(" $W/anim.log
$BL -b $W/stageB.blend --python $HERE/../../pipeline/package_for_farm.py -- $PKG/BeethovenDeaf_v011_60fps.blend 2>&1 | grep -E "FARM|PROBLEMS|SAVED|Error"
echo BUILD_ALL_DONE
