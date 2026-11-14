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
# x-ray: the forearm/hand muscles do not follow the glass arm when it swings (shards over the belly, a red arm
# pointing away from the glass arm). Show the forearms as glass only: mask every muscle vertex whose dominant
# bone is a forearm, wrist, hand or finger bone.
mus = bpy.data.objects["XrayMuscles"]; rig = bpy.data.objects["Lad"]
bones = {bb.name for bb in rig.data.bones}; gi = {g.index: g.name for g in mus.vertex_groups}
KEY = ("lowerarm", "wrist", "hand", "finger", "metacarpal", "palm", "thumb")
drop = []
for v in mus.data.vertices:
    gs = [g for g in v.groups if gi.get(g.group) in bones]
    if gs and any(k in gi[max(gs, key=lambda g: g.weight).group].lower() for k in KEY): drop.append(v.index)
vg = mus.vertex_groups.get("v006_forearm_mask") or mus.vertex_groups.new(name="v006_forearm_mask")
vg.add(drop, 1.0, 'REPLACE')
mm = mus.modifiers.get("v006_forearm_mask") or mus.modifiers.new("v006_forearm_mask", 'MASK')
mm.vertex_group = vg.name; mm.invert_vertex_group = True
print("POST masked x-ray forearm verts", len(drop), "of", len(mus.data.vertices))
bpy.ops.wm.save_as_mainfile(filepath=sys.argv[sys.argv.index("--") + 1], compress=True)
