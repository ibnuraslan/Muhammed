"""Re-key shot cameras in place (camera-only change). blender -b look.blend -P rekey_cams.py -- out.blend"""
import bpy, sys, json, os
from mathutils import Vector
HX = 45.0; sc = bpy.context.scene
S = {s["name"]: s for s in json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "shots.json")))}
NEW = {"S20_Sing": (((HX + 0.25, -2.4, 2.0), (HX + 0.25, 2.5, 1.3)), ((HX + 0.25, -2.0, 1.95), (HX + 0.2, 2.5, 1.3)), 26),
       "S21_HallWide": (((HX + 3.4, 3.4, 2.4), (HX - 0.6, 0.6, 1.0)), ((HX + 3.0, 3.6, 2.35), (HX - 0.7, 0.6, 1.0)), 20)}
for n, (k0, k1, lens) in NEW.items():
    c = bpy.data.objects["CAM_" + n]; c.animation_data_clear(); c.data.lens = lens
    for f, (l, t) in ((S[n]["f0"], k0), (S[n]["f1"], k1)):
        c.location = Vector(l); c.rotation_euler = (Vector(t) - Vector(l)).to_track_quat('-Z', 'Y').to_euler()
        c.keyframe_insert("location", frame=f); c.keyframe_insert("rotation_euler", frame=f)
bpy.ops.wm.save_as_mainfile(filepath=sys.argv[-1])
