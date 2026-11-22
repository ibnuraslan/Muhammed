"""v012b (client C, list 8): the toy-tub bricks hovered. Each TubBrick (static, lowest first) is dropped straight down until its
bottom rests on the tub floor or on a brick below it (rays from 9 points of its bottom face). Then the yellow brick he picks up
(Brick_Small, resting until the grab) gets a brick under it if it would hang in the air. blender -b in.blend --python settle_tub.py -- out.blend"""
import bpy, sys
from mathutils import Vector
OUT = sys.argv[sys.argv.index("--") + 1]; sc = bpy.context.scene; vl = bpy.context.view_layer
sc.frame_set(250)
tb = [o for o in bpy.data.objects if o.name.startswith("TubBrick")]
def wbb(o): return [o.matrix_world @ Vector(c) for c in o.bound_box]
def drop_to(o):
    bb = wbb(o); x0, x1 = min(v.x for v in bb), max(v.x for v in bb); y0, y1 = min(v.y for v in bb), max(v.y for v in bb); zb = min(v.z for v in bb)
    dg = bpy.context.evaluated_depsgraph_get(); best = None
    for u in (0.15, 0.5, 0.85):
        for w in (0.15, 0.5, 0.85):
            o_ = Vector((x0 + (x1 - x0) * u, y0 + (y1 - y0) * w, zb - 0.0005))
            hit, loc, n, i, ob, _ = sc.ray_cast(dg, o_, Vector((0, 0, -1)), distance=0.5)
            if hit and ob is not o and (best is None or loc.z > best): best = loc.z
    return zb, best
moved = 0; mx = 0.0
NODROP = "--nodrop" in sys.argv        # after settle_tub_rb.py: only lower Brick_Small and his hand onto the pile
for o in ([] if NODROP else sorted(tb, key=lambda o: min(v.z for v in wbb(o)))):
    zb, best = drop_to(o)
    if best is not None and zb - best > 0.0005:
        o.location.z -= (zb - best); vl.update(); moved += 1; mx = max(mx, zb - best)
print("SETTLE moved", moved, "of", len(tb), "max drop %.1f cm" % (mx * 100))
BS = bpy.data.objects["Brick_Small"]
zb, best = drop_to(BS)
def fcs(o): return [fc for l in o.animation_data.action.layers for st in l.strips for cb in st.channelbags for fc in cb.fcurves]
def ramp(f, a, b): return max(0.0, min(1.0, (f - a) / (b - a)))
if best is not None and zb - best > 0.0015:
    gap = zb - best - 0.0005      # lower the brick onto the settled pile, and his reaching hand with it (same weight while he holds it)
    wb = lambda f: 1.0 - ramp(f, 282, 300); wh = lambda f: min(ramp(f, 230, 262), wb(f))
    for fc in fcs(BS):
        if fc.data_path == "location" and fc.array_index == 2:
            for k in fc.keyframe_points:
                d = gap * wb(k.co.x); k.co.y -= d; k.handle_left.y -= d; k.handle_right.y -= d
            fc.update()
    Boy = bpy.data.objects["Boy"]; pb = Boy.pose.bones["IK_hand.R"]
    T = (Boy.matrix_world.to_3x3() @ pb.bone.matrix_local.to_3x3()).inverted(); dl = T @ Vector((0, 0, -1))
    for fc in fcs(Boy):
        if fc.data_path == 'pose.bones["IK_hand.R"].location':
            for k in fc.keyframe_points:
                d = gap * wh(k.co.x) * dl[fc.array_index]; k.co.y += d; k.handle_left.y += d; k.handle_right.y += d
            fc.update()
    print("LOWER Brick_Small and his hand by %.1f cm onto the pile" % (gap * 100))
else: print("SUPPORT none needed", None if best is None else round((zb - best) * 100, 2))
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
