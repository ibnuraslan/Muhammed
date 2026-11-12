set -e
cd /home/user/Muhammed/blender
B=/opt/blender/blender-5.2.2-linux-x64/blender; S=/tmp/claude-0/-home-user-Muhammed/60302108-5c41-54cc-ade1-198d9ab30d69/scratchpad
V=ElectricianPolice_v001
$B -b $V/build/film.blend --python $V/scripts/05_hands.py -- $V/build/film_hands.blend $V/review/v007_hand_audit.txt > $V/build/hands.log 2>&1
$B -b $V/build/film_hands.blend --python pipeline/anim_look.py -- $V/build/film_hands_anim.blend > /dev/null 2>&1
$B -b $V/build/film_hands_anim.blend --python $V/scripts/04_anim_tune.py -- $V/build/film_v7.blend > /dev/null 2>&1
rm -rf $V/build/after $V/build/hc
$B -b $V/build/film_v7.blend --python pipeline/stills.py -- $V/build/after 0.5 > /dev/null 2>&1
python3 -I pipeline/contact_sheet.py $V/build/after $V/review/ACTING_after_v007_0.5s_a.jpg 9 2 0 27
python3 -I pipeline/contact_sheet.py $V/build/after $V/review/ACTING_after_v007_0.5s_b.jpg 9 2 27 52
$B -b $V/build/film_v7.blend --python $V/scripts/hand_closeups.py -- $V/build/hc > /dev/null 2>&1
python3 -I pipeline/contact_sheet.py $V/build/hc $V/review/v007_hand_closeups.jpg 8 1
$B -b $V/build/film_v7.blend --python pipeline/clip_scan.py -- $V/review/v007_clip_scan.json 2>&1 | grep BAD_RANGES > $V/build/scan_stock.txt
$B -b $V/build/film_v7.blend --python $V/scripts/clip_scan_ep.py -- $V/review/v007_clip_scan_ep.json 2>&1 | grep BAD_RANGES > $V/build/scan_ep.txt
rm -rf $S/slimtex
$B -b $V/build/film_v7.blend --python $V/scripts/slim_textures.py -- $S/slimtex $V/build/film_v7_slim.blend > /dev/null 2>&1
$B -b $V/build/film_v7_slim.blend --python pipeline/package_for_farm.py -- ElectricianPolice_v007/ElectricianPolice_v007_60fps.blend 2>&1 | grep -E "PROBLEMS|SAVED" > $V/build/pkg7.txt
$B -b --factory-startup ElectricianPolice_v007/ElectricianPolice_v007_60fps.blend --python-expr "import bpy; print('UNPACKED', [i.name for i in bpy.data.images if i.source=='FILE' and not i.packed_file], [o.name for o in bpy.data.objects if o.type=='CAMERA'], bpy.context.scene.view_settings.look)" 2>&1 | grep UNPACKED >> $V/build/pkg7.txt
rm -rf $V/build/pk; $B -b --factory-startup ElectricianPolice_v007/ElectricianPolice_v007_60fps.blend --python $V/scripts/frames.py -- $V/build/pk 262 > /dev/null 2>&1
cp $V/build/pk/f0262.jpg ElectricianPolice_v007/package_check_f0262_lowres.jpg
echo CHAIN_DONE >> $V/build/pkg7.txt
