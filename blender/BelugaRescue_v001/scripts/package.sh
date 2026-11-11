#!/bin/bash
# Checkpoint D: pack film.blend for the farm into ../BelugaRescue_v00N/ and verify it in factory Blender.
# usage (from blender/BelugaRescue_v001): scripts/package.sh 002
set -e
N=${1:-002}; B=${BLENDER:-/opt/bin/blender}
OUTD=../BelugaRescue_v$N; mkdir -p $OUTD
OUT=$PWD/$OUTD/BelugaRescue_v${N}_60fps.blend
$B -b work/film.blend --python ../pipeline/package_for_farm.py -- $OUT 2>&1 | grep -E "FARM|PROBLEMS|SAVED|rror"
cp beats.json camera_path.json CREDITS.md $OUTD/
# verify: factory startup, nothing unpacked, settings read back
$B -b --factory-startup $OUT --python-expr "
import bpy
sc=bpy.context.scene; r=sc.render; c=sc.cycles
print('VERIFY unpacked', [i.name for i in bpy.data.images if i.source=='FILE' and not i.packed_file])
print('VERIFY images', len(bpy.data.images), 'cams', [o.name for o in bpy.data.objects if o.type=='CAMERA'], 'markers', len(sc.timeline_markers))
print('VERIFY', r.resolution_x, r.resolution_y, r.resolution_percentage, r.fps, r.fps_base, sc.frame_start, sc.frame_end, r.engine, c.samples, c.adaptive_threshold, c.use_denoising, r.use_motion_blur, r.motion_blur_shutter, sc.view_settings.view_transform, sc.view_settings.look, r.filepath)
print('VERIFY libs', len(bpy.data.libraries), 'missing', [i.name for i in bpy.data.images if i.source=='FILE' and not i.packed_file and not i.has_data])
" 2>&1 | grep VERIFY
# low-res proof frame from the packed file in factory Blender (20 %, 4 samples)
$B -b --factory-startup $OUT --python-expr "
import bpy
sc=bpy.context.scene; sc.render.resolution_percentage=20; sc.cycles.samples=4; sc.render.use_motion_blur=False
sc.frame_set(880); sc.render.filepath='$PWD/$OUTD/package_check_f880_lowres.png'; sc.render.image_settings.file_format='PNG'
bpy.ops.render.render(write_still=True)" 2>&1 | grep -E "Saved|rror"
ls -la $OUTD
