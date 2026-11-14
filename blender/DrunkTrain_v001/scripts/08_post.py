"""v006 post step (after pipeline/anim_look.py), per blender/LESSONS_LEARNED.md:
- eye_fix.py (from LegoInNose a44130b): no black-hole eyes on MPFB characters
- focus: f/11 on the film camera, so close shots never read as blur
blender -b anim_look.blend --python 08_post.py -- out.blend"""
import bpy, sys, os
_NO_SAVE = True
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "eye_fix.py")).read())
cam = bpy.data.objects["CAM_Film"]
cam.data.dof.aperture_fstop = 11.0
print("POST fstop", cam.data.dof.aperture_fstop, "dof", cam.data.dof.use_dof)
bpy.ops.wm.save_as_mainfile(filepath=sys.argv[sys.argv.index("--") + 1], compress=True)
