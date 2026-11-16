"""Camera-only fixes on the packaged v002 (single baked camera): re-key S10/S11 paths; hide S20 guests cut by the frame edge.
blender -b CrocodileFriend_v002_60fps.blend -P 08_fix_cams.py -- out.blend"""
import bpy, sys, math
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
sc = bpy.context.scene; cam = sc.camera; OB = bpy.data.objects
def smooth(x): x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)
NEW = {}   # S10/S11 cameras now set in 04_anim.py
for (a, b), ((l0, t0), (l1, t1), lens) in NEW.items():
    for f in range(a, b + 1):
        u = smooth((f - a) / (b - a)); l = Vector(l0).lerp(Vector(l1), u); t = Vector(t0).lerp(Vector(t1), u)
        cam.location = l; cam.rotation_euler = (t - l).to_track_quat('-Z', 'Y').to_euler(); cam.data.lens = lens
        cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f); cam.data.keyframe_insert("lens", frame=f)
# S20 (1785-1895): hide any guest whose head or hands leave the frame (no half-bodies at the edge)
hidden = []
for o in [o for o in OB if o.type == 'ARMATURE' and o.name.startswith(("Crowd", "Spec"))]:
    cut = False
    for f in (1785, 1840, 1895):
        sc.frame_set(f)
        if o.hide_render: break
        for bn in ("head", "wrist.L", "wrist.R", "upperarm01.L", "upperarm01.R", "foot.L"):
            p = world_to_camera_view(sc, cam, o.matrix_world @ o.pose.bones[bn].head)
            if p.z > 0 and (-0.02 < p.x < 0.05 or 0.95 < p.x < 1.25): cut = True
    if cut:
        hidden.append(o.name)
        for ob in [o] + list(o.children):
            for f, h in ((1785, True), (1896, ob.hide_render)):
                pass
            sc.frame_set(1785); ob.hide_render = ob.hide_viewport = True
            ob.keyframe_insert("hide_render", frame=1785); ob.keyframe_insert("hide_viewport", frame=1785)
print("FIXCAMS hidden", hidden)
bpy.ops.wm.save_as_mainfile(filepath=sys.argv[-1], compress=True)
