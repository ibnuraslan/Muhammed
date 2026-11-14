#!/bin/bash
# finalize.sh N : anim$N.blend -> anim$N_final.blend (anim look, eye fix, haze off, f/8)
set -e
B=/opt/blender/blender-5.2.2-linux-x64/blender
$B -b /tmp/claude-0/-home-user-Muhammed/36b615a4-4776-5fc2-8a38-7ced289ad229/scratchpad/anim$1.blend --python /home/user/Muhammed/blender/pipeline/anim_look.py -- /tmp/claude-0/-home-user-Muhammed/36b615a4-4776-5fc2-8a38-7ced289ad229/scratchpad/anim$1_look.blend 2>&1 | grep saved
$B -b /tmp/claude-0/-home-user-Muhammed/36b615a4-4776-5fc2-8a38-7ced289ad229/scratchpad/anim$1_look.blend --python-expr "
import bpy
_NO_SAVE=True
exec(open(''+__import__('os').path.dirname(__import__('os').path.abspath('$0'))+'/eye_fix.py').read())
for n in ('CellHaze','ShrineHaze'):
  o=bpy.data.objects[n]; o.hide_render=True; o.hide_viewport=True
for c in bpy.data.cameras: c.dof.aperture_fstop = max(8.0, c.dof.aperture_fstop)
bpy.ops.wm.save_as_mainfile(filepath='/tmp/claude-0/-home-user-Muhammed/36b615a4-4776-5fc2-8a38-7ced289ad229/scratchpad/anim$1_final.blend')" 2>&1 | grep -E "EYEFIX|Error"
