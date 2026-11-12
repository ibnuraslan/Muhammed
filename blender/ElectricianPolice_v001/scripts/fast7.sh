set -e
cd /home/user/Muhammed/blender
B=/opt/blender/blender-5.2.2-linux-x64/blender; S=/tmp/claude-0/-home-user-Muhammed/60302108-5c41-54cc-ade1-198d9ab30d69/scratchpad
V=ElectricianPolice_v001; P=ElectricianPolice_v007/ElectricianPolice_v007_60fps.blend
$B -b $V/build/film_hands.blend --python pipeline/anim_look.py -- $V/build/film_hands_anim.blend > /dev/null 2>&1
$B -b $V/build/film_hands_anim.blend --python $V/scripts/04_anim_tune.py -- $V/build/film_v7.blend > /dev/null 2>&1
echo TUNED $(date -u +%H:%M) >> $V/build/fast7.txt
rm -rf $V/build/after $V/build/hc $S/slimtex
( $B -b $V/build/film_v7.blend --python pipeline/stills.py -- $V/build/after 0.5 > /dev/null 2>&1
  python3 -I pipeline/contact_sheet.py $V/build/after $V/review/ACTING_after_v007_0.5s_a.jpg 9 2 0 27
  python3 -I pipeline/contact_sheet.py $V/build/after $V/review/ACTING_after_v007_0.5s_b.jpg 9 2 27 52; echo SHEET $(date -u +%H:%M) >> $V/build/fast7.txt ) &
( $B -b $V/build/film_v7.blend --python $V/scripts/hand_closeups.py -- $V/build/hc > /dev/null 2>&1
  python3 -I pipeline/contact_sheet.py $V/build/hc $V/review/v007_hand_closeups.jpg 8 1; echo HC $(date -u +%H:%M) >> $V/build/fast7.txt ) &
( $B -b $V/build/film_v7.blend --python $V/scripts/slim_textures.py -- $S/slimtex $V/build/film_v7_slim.blend > /dev/null 2>&1
  $B -b $V/build/film_v7_slim.blend --python pipeline/package_for_farm.py -- $P 2>&1 | grep -E "PROBLEMS|SAVED" >> $V/build/fast7.txt
  $B -b $P --python pipeline/qa_check.py -- $V/review/qa_v007.json 6 ElectricianPolice_v007/beats.json 2>&1 | grep QA_COUNTS >> $V/build/fast7.txt
  echo QA $(date -u +%H:%M) >> $V/build/fast7.txt ) &
( $B -b $V/build/film_v7.blend --python $V/scripts/clip_scan_ep.py -- $V/review/v007_clip_scan_ep.json 2>&1 | grep BAD_RANGES >> $V/build/fast7.txt; echo SCAN $(date -u +%H:%M) >> $V/build/fast7.txt ) &
wait
echo FAST_DONE >> $V/build/fast7.txt
