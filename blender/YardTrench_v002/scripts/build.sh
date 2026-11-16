#!/bin/bash
# Full rebuild of the package from scripts: bash scripts/build.sh   (run inside the version folder)
set -e
B=/opt/blender/blender-5.2.2-linux-x64/blender; V=$(basename "$PWD")
$B -b --factory-startup -P scripts/01_chars.py -- work/chars.blend
$B -b work/chars.blend -P scripts/02_sets.py -- work/sets.blend
$B -b work/sets.blend -P scripts/03_anim.py -- work/film.blend timing_vo.json
$B -b work/film.blend -P ../pipeline/anim_look.py -- work/film_look.blend --no-sky
$B -b work/film_look.blend -P scripts/04_finish.py -- work/film_fin.blend "$PWD/${V}_VO.mp3"
$B -b work/film_fin.blend -P ../pipeline/package_for_farm.py -- "$PWD/${V}_60fps.blend"
