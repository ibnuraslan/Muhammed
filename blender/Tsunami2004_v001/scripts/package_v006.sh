#!/bin/bash
# vNEXT (v006): rebuild, checks, package, moving preview of the packed file
cd /home/user/Muhammed/blender/Tsunami2004_v001
B=/opt/blender/blender-5.2.2-linux-x64/blender
OUT=/home/user/Muhammed/blender/Tsunami2004_v006
bash scripts/build_all.sh > /tmp/claude-0/b6.log 2>&1 || { echo BUILD_FAIL; exit 1; }
echo BUILT
mkdir -p "$OUT" review; cp beats.json "$OUT"/
$B -b film.blend --python ../pipeline/clip_scan.py -- $PWD/review/clip_scan_v006.json 6 > /tmp/claude-0/cs6.log 2>&1
rm -rf /tmp/claude-0/shrink && $B -b film.blend --python scripts/05_shrink_textures.py -- /tmp/claude-0/shrink $PWD/film_small.blend > /tmp/claude-0/sh6.log 2>&1
$B -b film_small.blend --python ../pipeline/package_for_farm.py -- "$OUT"/Tsunami2004_v006_60fps.blend > /tmp/claude-0/pk6.log 2>&1
rm -f /home/user/Muhammed/blender/Tsunami2004_v006/Tsunami2004_v006_60fps.blend1
$B -b --factory-startup "$OUT"/Tsunami2004_v006_60fps.blend --python-expr "import bpy;print('UNPACKED',[i.name for i in bpy.data.images if i.source=='FILE' and not i.packed_file]);print('CAMS',[o.name for o in bpy.data.objects if o.type=='CAMERA']);print('FMT',bpy.context.scene.render.image_settings.file_format)" > /tmp/claude-0/vf6.log 2>&1
$B -b "$OUT"/Tsunami2004_v006_60fps.blend --python ../pipeline/qa_check.py -- $PWD/review/qa_v006.json 6 "$OUT"/beats.json > /tmp/claude-0/qa6.log 2>&1
echo PACKED
rm -rf /tmp/claude-0/P6 && mkdir -p /tmp/claude-0/P6 && $B -b "$OUT"/Tsunami2004_v006_60fps.blend --python ../pipeline/preview.py -- /tmp/claude-0/P6 5 > /tmp/claude-0/p6.log 2>&1
bash ../pipeline/watch_pages.sh /tmp/claude-0/P6 5
echo V006_DONE
