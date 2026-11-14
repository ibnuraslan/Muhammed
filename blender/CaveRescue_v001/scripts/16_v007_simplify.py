"""v007 simplify (LESSONS 2.15): shots that stayed faulty after one clearance retry are re-staged simpler.
- Underwater passage, 1700-1735: the camera ran low along the guide rope (rope filling the lens) and then crossed the rock
  between the tunnel and the passage with no cover. The camera (with its aim) is lifted 25 cm over 1700-1724, eased in
  and out, and the rock crossing gets the same rock-wipe as the other scale moves (J = 1726: at most 4 black frames).
blender -b in.blend --python 16_v007_simplify.py -- out.blend"""
import bpy, sys
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; cam = sc.camera; aim = cam.constraints[0].target
def fcs(o):
    ad = o.animation_data
    return sorted([fc for lay in ad.action.layers for st in lay.strips for cb in st.channelbags for fc in cb.fcurves if fc.data_path == "location"], key=lambda f: f.array_index)
F0, F1, RAMP, LIFT = 1696, 1728, 8, 0.25
for o in (cam, aim):
    fz = fcs(o)[2]
    for kp in fz.keyframe_points:
        f = int(round(kp.co.x))
        if F0 <= f <= F1:
            e = min(1.0, (f - F0) / RAMP, (F1 - f) / RAMP); e = e * e * (3 - 2 * e)
            kp.co.y += LIFT * e; kp.handle_left.y += LIFT * e; kp.handle_right.y += LIFT * e
    fz.update()
wv = bpy.data.materials["M_RockWipe"].node_tree.nodes["Wipe"].outputs[0]
J = 1726
for f, v in ((J - 7, 0.0), (J - 1, 1.0), (J + 2, 1.0), (J + 8, 0.0)):
    wv.default_value = v; wv.keyframe_insert("default_value", frame=f)
print("SIMPLIFY lift", F0, F1, "wipe", J)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SIMPLIFY_OK")
