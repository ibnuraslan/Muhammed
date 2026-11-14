"""v008f: Mom's forearm/hand passed through the boy's head at 989-997 (her hand going from 'reach' to the chin cradle).
Every frame 982-1002: Mom's forearm/wrist/hand vertices against the boy's head mesh; the IK hand of the side that is inside is
pushed out along the mean surface normal by depth + 2 cm, repeated until clear. blender -b in.blend --python mom_head.py -- out.blend"""
import bpy, sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
OUT = sys.argv[sys.argv.index("--") + 1]; sc = bpy.context.scene
M = bpy.data.objects["Mom"]; MB = bpy.data.objects["Mom_Body"]; BB = bpy.data.objects["Boy_Body"]; Bo = bpy.data.objects["Boy"]
masks = [(m, m.show_viewport) for b in (MB, BB) for m in b.modifiers if m.type in ("MASK", "SUBSURF", "MULTIRES")]
for m, _ in masks: m.show_viewport = False
def dom(b, arm):
    gi = {g.index: g.name for g in b.vertex_groups if g.name in arm.data.bones}; out = []
    for v in b.data.vertices:
        g = max((g for g in v.groups if g.group in gi), key=lambda g: g.weight, default=None); out.append(gi[g.group] if g else "")
    return out
dm = dom(MB, M); db = dom(BB, Bo)
HEAD = ("head", "neck", "jaw", "eye", "ear", "nose", "lip", "cheek", "brow", "temporal", "tongue", "levator", "oris", "risorius", "special", "orbicularis")
probe = {s: [i for i, n in enumerate(dm) if n.endswith("." + s) and n.startswith(("lowerarm", "wrist", "metacarpal", "finger"))] for s in "LR"}
def fcs(o): return [fc for l in o.animation_data.action.layers for st in l.strips for cb in st.channelbags for fc in cb.fcurves]
def push(s, f, d):
    n = "IK_hand." + s; dl = M.data.bones[n].matrix_local.to_3x3().inverted() @ (M.matrix_world.to_3x3().inverted() @ d)
    for fc in [c for c in fcs(M) if c.data_path == 'pose.bones["%s"].location' % n]: fc.keyframe_points.insert(f, fc.evaluate(f) + dl[fc.array_index], options={"FAST"})
    if s == "R":
        for pn in ("Prop_Tweezers", "Brick_Big"):
            o = bpy.data.objects[pn]
            if pn == "Brick_Big" and f < 1042: continue
            for fc in [c for c in fcs(o) if c.data_path == "location"]: fc.keyframe_points.insert(f, fc.evaluate(f) + d[fc.array_index], options={"FAST"})
for rnd in range(10):
    hits = []
    for f in range(982, 1003):
        sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
        e = BB.evaluated_get(dg); me = e.to_mesh(); V = [e.matrix_world @ v.co for v in me.vertices]
        T = BVHTree.FromPolygons(V, [tuple(p.vertices) for p in me.polygons if all(db[i].startswith(HEAD) for i in p.vertices)]); e.to_mesh_clear()
        e = MB.evaluated_get(dg); me = e.to_mesh(); mw = e.matrix_world
        for s in "LR":
            deep, ns = 0.0, Vector()
            for i in probe[s]:
                p = mw @ me.vertices[i].co; loc, n, _, d = T.find_nearest(p, 0.3)
                if loc is not None and (p - loc).dot(n) < 0 and d > 0.003: deep = max(deep, d); ns += n
            if deep > 0: hits.append((s, f, ns.normalized() * (deep + 0.02)))
        e.to_mesh_clear()
    print("MOMHEAD round", rnd, "hits", len(hits), sorted({(s, f) for s, f, _ in hits})[:12])
    if not hits: break
    for s, f, d in hits: push(s, f, d * 0.7)
    for o in (M, bpy.data.objects["Prop_Tweezers"], bpy.data.objects["Brick_Big"]):
        for fc in fcs(o): fc.update()
for m, v in masks: m.show_viewport = v
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True); print("MOMHEAD saved", OUT)
