#!/bin/bash
cd /home/user/Muhammed/blender/Tsunami2004_v001
B=/opt/blender/blender-5.2.2-linux-x64/blender
OUT=/home/user/Muhammed/blender/Tsunami2004_v005
mkdir -p "$OUT" review
cp beats.json "$OUT"/
$B -b film.blend --python ../pipeline/clip_scan.py -- $PWD/review/clip_scan_v005.json 6 > /tmp/claude-0/cs.log 2>&1
$B -b film.blend --python scripts/hand_audit.py -- $PWD/review/hand_audit_v005.txt 2 > /tmp/claude-0/ha5.log 2>&1
rm -rf /tmp/claude-0/shrink && $B -b film.blend --python scripts/05_shrink_textures.py -- /tmp/claude-0/shrink $PWD/film_small.blend > /tmp/claude-0/sh5.log 2>&1
$B -b film_small.blend --python ../pipeline/package_for_farm.py -- "$OUT"/Tsunami2004_v005_60fps.blend > /tmp/claude-0/pk5.log 2>&1
rm -f /home/user/Muhammed/blender/Tsunami2004_v005/Tsunami2004_v005_60fps.blend1
$B -b --factory-startup "$OUT"/Tsunami2004_v005_60fps.blend --python-expr "import bpy;print('UNPACKED',[i.name for i in bpy.data.images if i.source=='FILE' and not i.packed_file]);print('CAMS',[o.name for o in bpy.data.objects if o.type=='CAMERA']);print('FMT',bpy.context.scene.render.image_settings.file_format)" > /tmp/claude-0/vf5.log 2>&1
rm -rf /tmp/claude-0/H5 && $B -b --factory-startup "$OUT"/Tsunami2004_v005_60fps.blend --python ../pipeline/stills.py -- /tmp/claude-0/H5 0.5 > /tmp/claude-0/H5.log 2>&1
for i in 0 1; do python3 -I ../pipeline/contact_sheet.py /tmp/claude-0/H5 review/after_v005_0.5s_part$((i+1)).jpg 10 2 $((i*40)) $((i*40+40)); done
rm -rf /tmp/claude-0/hcu5 && $B -b --factory-startup "$OUT"/Tsunami2004_v005_60fps.blend --python scripts/hand_closeups.py -- /tmp/claude-0/hcu5 > /tmp/claude-0/hc5.log 2>&1
python3 -c "
from PIL import Image, ImageDraw; import glob
fs=sorted(glob.glob('/tmp/claude-0/hcu5/*.jpg')); S=Image.new('RGB',(270*7,480*2))
for i,f in enumerate(fs):
    im=Image.open(f); ImageDraw.Draw(im).rectangle((0,0,270,12),fill=(0,0,0)); ImageDraw.Draw(im).text((2,1),f.split('/')[-1][:-4],fill=(255,255,0)); S.paste(im,((i%7)*270,(i//7)*480))
S.save('review/hand_closeups_v005.jpg',quality=85)"
echo V005_DONE
