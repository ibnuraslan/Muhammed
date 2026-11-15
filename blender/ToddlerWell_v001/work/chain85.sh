B=/opt/blender/blender-5.2.2-linux-x64/blender
cd /home/user/Muhammed/blender/ToddlerWell_v001
$B -b work/scene.blend --python scripts/03_animate.py -- work/anim.blend > work/a85.log 2>&1
$B -b work/anim.blend --python scripts/04_camera.py -- work/film_raw.blend > work/c85.log 2>&1
$B -b work/film_raw.blend --python ../pipeline/anim_look.py -- work/film85.blend > work/l85.log 2>&1
$B -b work/film85.blend --python work/clip_range.py -- work/clip85a.json 2 1290 1330 > work/clip85a.log 2>&1 &
$B -b work/film85.blend --python work/clip_range.py -- work/clip85b.json 2 1760 1850 > work/clip85b.log 2>&1
wait
grep -h "BAD_RANGES" work/clip85a.log work/clip85b.log
echo CHAIN85_DONE
B=/opt/blender/blender-5.2.2-linux-x64/blender
$B -b work/film85.blend --python scripts/05_package.py -- ../ToddlerWell_v006/ToddlerWell_v006_60fps.blend > work/pk85.log 2>&1
grep "PROBLEMS\|SAVED" work/pk85.log
