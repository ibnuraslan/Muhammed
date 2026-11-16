#!/bin/bash
# Full 3-frame sheet + body_prop_cross (man, tourists, guests) from work/look.blend
cd "$(dirname "$0")/.."
B=${BLENDER:-/opt/blender/blender-5.2.2-linux-x64/blender}
P=$($B -b work/look.blend --python-expr "import bpy; print('PROPS', ','.join(o.name for o in bpy.data.objects if o.type=='MESH' and o.name.startswith(('Croc_body','Bucket','Rail','Crate','Easel','LogoSign_Board','PortraitFrame','Meat'))))" 2>/dev/null | grep PROPS | cut -d' ' -f2)
rm -rf review/p1 review/body_prop_cross*.json review/bpc_*.json
($B -b work/look.blend -P scripts/sheet3.py -- review/p1 540 > /dev/null 2>&1; python3 scripts/montage.py review/p1 review/P1_sheet_3frames.jpg 3) &
run() { $B -b work/look.blend --python-expr "import bpy; s=bpy.context.scene; s.frame_start=$2; s.frame_end=$3" \
        --python ../pipeline/body_prop_cross.py -- review/body_prop_cross_$1.json 3 "$P" $4 2>&1 | grep BPC_DONE | sed "s/^/$1 /"; }
run man_a 1 1950 Keeper &
run man_b 1951 3900 Keeper &
run tourists 2731 3120 SpecA,SpecB,SpecC,SpecD,SpecE,SpecF,SpecG &
wait
run guests 3341 3900 Crowd1,Crowd2,Crowd3,Crowd4,SpecB,SpecE
echo ALL_DONE
