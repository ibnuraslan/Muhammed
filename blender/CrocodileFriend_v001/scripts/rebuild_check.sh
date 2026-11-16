#!/bin/bash
# Rebuild film -> look into work/look2.blend and re-run body_prop_cross on the given ranges (name:f0:f1 ...)
set -e
cd "$(dirname "$0")/.."
B=${BLENDER:-/opt/blender/blender-5.2.2-linux-x64/blender}
$B -b work/sets.blend -P scripts/04_anim.py -- work/film2.blend 2>&1 | grep -E "DONE|rror" || true
$B -b work/film2.blend --python ../pipeline/anim_look.py -- work/look_base2.blend --no-sky 2>&1 | grep -i error || true
$B -b work/look_base2.blend -P scripts/05_look.py -- work/look2.blend 2>&1 | grep -E "LOOK|rror" || true
P=$($B -b work/look2.blend --python-expr "import bpy; print('PROPS', ','.join(o.name for o in bpy.data.objects if o.type=='MESH' and o.name.startswith(('Croc_body','Bucket','Rail','Crate','Easel','LogoSign_Board','PortraitFrame','Meat'))))" 2>/dev/null | grep PROPS | cut -d' ' -f2)
for spec in "$@"; do
  IFS=: read n f0 f1 <<< "$spec"
  ($B -b work/look2.blend --python-expr "import bpy; s=bpy.context.scene; s.frame_start=$f0; s.frame_end=$f1" \
     --python ../pipeline/body_prop_cross.py -- review/bpc_$n.json 3 "$P" Keeper 2>&1 | grep BPC_DONE | sed "s/^/$n /") &
done
wait
