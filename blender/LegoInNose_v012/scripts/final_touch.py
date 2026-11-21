"""v012 finishing pass.
 - dark irises on every character (client: 'faces must have dark irises, not pale ones')
 - the blanket a clearer blue
 - hospital bed (1478-1586): the camera holds the man's face (0.55 m out along his face, offset toward his feet so the face reads
   upright), eased in over 1478-1486 and out over 1578-1586.
blender -b in.blend --python final_touch.py -- out.blend"""
import bpy, sys
from mathutils import Vector
OUT = sys.argv[sys.argv.index("--") + 1]; sc = bpy.context.scene
for m in bpy.data.materials:
    if m.name.endswith("high-poly") and m.node_tree:
        for n in m.node_tree.nodes:
            if n.type == "GROUP" and "IrisMajorColor" in n.inputs:
                n.inputs["IrisMajorColor"].default_value = (0.11, 0.055, 0.025, 1); n.inputs["IrisMinorColor"].default_value = (0.035, 0.018, 0.008, 1)
                n.inputs["IrisSection4Color"].default_value = (0.02, 0.01, 0.005, 1); print("IRIS dark", m.name)
bk = bpy.data.materials.get("M_Blanket")
if bk: bk.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.18, 0.32, 0.58, 1)
def smooth(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)
CAM, AIM, M = bpy.data.objects["CAM_Film"], bpy.data.objects["CAM_Film_Aim"], bpy.data.objects["Man"]
def fl(o): return sorted([c for l in o.animation_data.action.layers for st in l.strips for cb in st.channelbags for c in cb.fcurves if c.data_path == "location"], key=lambda c: c.array_index)
cf, af = fl(CAM), fl(AIM); ev = lambda F, f: Vector([F[i].evaluate(f) for i in range(3)])
new = {}
for f in range(1478, 1587):
    sc.frame_set(f); pb = M.pose.bones["head"]
    R = (M.matrix_world @ pb.matrix @ M.data.bones["head"].matrix_local.inverted()).to_3x3().normalized()
    fw = R @ Vector((0, -1, 0)); up = R @ Vector((0, 0, 1)); H = M.matrix_world @ pb.head + up * 0.08
    feet = -up; feet.z = 0; feet = feet.normalized() if feet.length > 1e-3 else Vector((0, -1, 0))
    w = smooth((f - 1478) / 8.0) if f < 1578 else 1 - smooth((f - 1578) / 8.0)
    new[f] = (ev(cf, f).lerp(H + fw * 0.5 + feet * 0.28, w), ev(af, f).lerp(H + fw * 0.02, w))
for f, (c, a_) in new.items():
    for i in range(3): cf[i].keyframe_points.insert(f, c[i], options={"FAST"}); af[i].keyframe_points.insert(f, a_[i], options={"FAST"})
for c in cf + af: c.update()
print("BEDCAM ok")
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
