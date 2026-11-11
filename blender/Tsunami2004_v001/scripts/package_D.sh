#!/bin/bash
# Checkpoint D: rebuild, audits, shrink + pack, factory-startup verify, 1/s sheet from the packed file.
set -e
cd /home/user/Muhammed/blender/Tsunami2004_v001
B=/opt/blender/blender-5.2.2-linux-x64/blender
OUT=/home/user/Muhammed/blender/Tsunami2004_v002
bash scripts/build_all.sh > /tmp/claude-0/D_build.log 2>&1
$B -b film.blend --python scripts/hand_audit.py -- $OUT/hand_audit.txt 2 > /tmp/claude-0/D_ha.log 2>&1
$B -b film.blend --python scripts/audit.py -- $OUT/audit.txt 6 > /tmp/claude-0/D_audit.log 2>&1
rm -rf /tmp/claude-0/shrink && $B -b film.blend --python scripts/05_shrink_textures.py -- /tmp/claude-0/shrink $PWD/film_small.blend > /tmp/claude-0/D_shrink.log 2>&1
$B -b film_small.blend --python ../pipeline/package_for_farm.py -- $OUT/Tsunami2004_v002_60fps.blend > /tmp/claude-0/D_pack.log 2>&1
cp beats.json $OUT/
$B -b --factory-startup $OUT/Tsunami2004_v002_60fps.blend --python-expr "import bpy;print('UNPACKED',[i.name for i in bpy.data.images if i.source=='FILE' and not i.packed_file]);print('CAMS',[o.name for o in bpy.data.objects if o.type=='CAMERA'])" > /tmp/claude-0/D_verify.log 2>&1
$B -b --factory-startup $OUT/Tsunami2004_v002_60fps.blend --python-expr "
import bpy,time
sc=bpy.context.scene; sc.render.resolution_percentage=25; sc.cycles.samples=4; sc.frame_set(1160)
sc.render.image_settings.file_format='JPEG'; sc.render.filepath='$OUT/package_check_f1160_lowres.jpg'
t=time.time(); bpy.ops.render.render(write_still=True); print('CHECKTIME',time.time()-t)" > /tmp/claude-0/D_check.log 2>&1
rm -rf /tmp/claude-0/D_stills && $B -b --factory-startup $OUT/Tsunami2004_v002_60fps.blend --python ../pipeline/stills.py -- /tmp/claude-0/D_stills 1.0 > /tmp/claude-0/D_stills.log 2>&1
python3 -I ../pipeline/contact_sheet.py /tmp/claude-0/D_stills $OUT/D_sheet_1s.jpg 10 1
echo PACKAGE_DONE
