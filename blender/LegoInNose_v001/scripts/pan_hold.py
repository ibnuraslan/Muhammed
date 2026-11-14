"""v008f: 22.25 s synced (old 1458-1474): the camera panned across the empty living room before the man (time-lapse jump at 1470)
appeared on the bench. Now the aim holds him on the rug until 1466, then makes a quick eased swing (1466-1475) to the bench framing.
blender -b in.blend --python pan_hold.py -- out.blend"""
import bpy, sys
from mathutils import Vector
OUT = sys.argv[sys.argv.index("--") + 1]; sc = bpy.context.scene; AIM = bpy.data.objects["CAM_Film_Aim"]
def smooth(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)
af = sorted([c for l in AIM.animation_data.action.layers for st in l.strips for cb in st.channelbags for c in cb.fcurves if c.data_path == "location"], key=lambda c: c.array_index)
ev = lambda f: Vector([af[i].evaluate(f) for i in range(3)])
orig = {f: ev(f) for f in range(1456, 1476)}; end = orig[1475]
sc.frame_set(1466); MM = bpy.data.objects["Man"]; rug = MM.matrix_world @ MM.pose.bones["head"].head - Vector((0, 0, 0.15))   # his upper chest on the rug
new = {}
for f in range(1458, 1475):
    if f <= 1466: new[f] = orig[f].lerp(rug, smooth((f - 1457) / 4.0))
    else: new[f] = rug.lerp(end, smooth((f - 1466) / 9.0))
for f, p in new.items():
    for i in range(3): af[i].keyframe_points.insert(f, p[i], options={"FAST"})
for c in af: c.update()
print("PANHOLD ok"); bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
