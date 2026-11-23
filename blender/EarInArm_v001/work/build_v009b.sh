set -e
cd /home/user/Muhammed/blender/EarInArm_v001
B=/opt/bin/blender; P=/tmp/claude-0/-home-user-Muhammed/57d1db37-7198-5f29-90d1-ee7231358f7c/scratchpad
if [ "$2" = "anim" ]; then rm -f work/anim_v009.blend; $B -b work/sets.blend --python scripts/03_animate.py -- work/anim_v009.blend 2>&1 | grep -E "ANIM_DONE|rror|line [0-9]"; test -f work/anim_v009.blend || { echo "ANIM FAILED"; exit 1; }; fi
if [ "$2" = "anim" ] || [ "$2" = "hands" ]; then rm -f work/anim.blend; $B -b work/anim_v009.blend --python scripts/03b_hands_v009b.py -- work/anim.blend 2>&1 | grep -E "HANDS_DONE|rror|line [0-9]"; test -f work/anim.blend || { echo "HANDS FAILED"; exit 1; }; $B -b work/anim.blend --python scripts/03c_dress_v009d.py -- work/anim.blend 2>&1 | grep -E "DRESS_DONE|rror:|line [0-9]"; $B -b work/anim.blend --python scripts/03d_v012_looks.py -- work/anim.blend 2>&1 | grep -E "LOOKS_DONE|TROUSERS|rror|line [0-9]" | tee /tmp/claude-0/-home-user-Muhammed/57d1db37-7198-5f29-90d1-ee7231358f7c/scratchpad/looks.log; grep -q LOOKS_DONE /tmp/claude-0/-home-user-Muhammed/57d1db37-7198-5f29-90d1-ee7231358f7c/scratchpad/looks.log || { echo "LOOKS FAILED"; exit 1; }; fi
python3 -c "import ast;ast.parse(open('scripts/04_camera_fx.py').read())" || { echo CAMERA_SCRIPT_BROKEN; exit 1; }
rm -f work/film.blend; $B -b work/anim.blend --python scripts/04_camera_fx.py -- work/film.blend 2>&1 | grep -E "CAMERA_DONE|rror:|line [0-9]" ; test -f work/film.blend || { echo CAMERA_FAILED; exit 1; }
$B -b work/film.blend --python ../pipeline/anim_look.py -- work/film_anim.blend 2>&1 | grep -c "anim_look\]" >/dev/null
$B -b work/film_anim.blend --python scripts/05_anim_look_fix.py -- work/film_anim.blend 2>&1 | grep -E "ANIMFIX|rror:"
rm -f $P/prev/fr_*; $B -b work/film_anim.blend --python $P/frames.py -- $P/prev/fr $1 2>&1 | grep -i "error" || true
python3 $P/sheet.py $P/prev/fr $P/prev/fr.jpg 10
