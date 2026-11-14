"""v008f: after the arm passes (arm_fix / mom_head / mom_show / misc_limb) moved IK hands, the held props are re-seated:
 1. tweezers: origin keyed onto Mom's right pinch every frame 960-1145 (the brick in the tips follows from 1042)
 2. palm props (Brick_Small in the man's left palm 2152-2310, inhaler 1606-1720): within 0.8 cm of a fingertip (tip_fix 'palm')
 3. tweezers/brick vs Mom's own head (1058-1084): if closer than 2 cm (brick) / inside (tweezers) -> Mom's IK hand is moved away
repeated until 1-3 all hold. blender -b in.blend --python prop_resnap.py -- out.blend"""
import bpy, sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
OUT = sys.argv[sys.argv.index("--") + 1]; sc = bpy.context.scene
def smooth(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)
def fcs(o): return [fc for l in o.animation_data.action.layers for st in l.strips for cb in st.channelbags for fc in cb.fcurves] if o.animation_data and o.animation_data.action else []
def shift(o, path, f, d):
    for fc in [c for c in fcs(o) if c.data_path == path]: fc.keyframe_points.insert(f, fc.evaluate(f) + d[fc.array_index], options={"FAST"})
def upd(*os):
    for o in os:
        for fc in fcs(o): fc.update()
def tips(a, s): return [a.matrix_world @ a.pose.bones["finger%d-3.%s" % (k, s)].tail for k in (1, 2, 3, 4, 5)]
def bbox(o):
    dg = bpy.context.evaluated_depsgraph_get(); pts = []
    for x in [o] + list(o.children_recursive):
        if x.type == "MESH": e = x.evaluated_get(dg); pts += [e.matrix_world @ Vector(c) for c in e.bound_box]
    return Vector([min(p[i] for p in pts) for i in range(3)]), Vector([max(p[i] for p in pts) for i in range(3)])
def bd(lo, hi, p): return Vector((max(lo.x - p.x, 0, p.x - hi.x), max(lo.y - p.y, 0, p.y - hi.y), max(lo.z - p.z, 0, p.z - hi.z))).length
Mo, Ma = bpy.data.objects["Mom"], bpy.data.objects["Man"]; TW, BR = bpy.data.objects["Prop_Tweezers"], bpy.data.objects["Brick_Big"]
MB = bpy.data.objects["Mom_Body"]
masks = [(m, m.show_viewport) for m in MB.modifiers if m.type in ("MASK", "SUBSURF", "MULTIRES")]
for m, _ in masks: m.show_viewport = False
gi = {g.index: g.name for g in MB.vertex_groups if g.name in Mo.data.bones}; dom = []
for v in MB.data.vertices:
    g = max((g for g in v.groups if g.group in gi), key=lambda g: g.weight, default=None); dom.append(gi[g.group].lower() if g else "")
HEAD = ("head", "neck", "jaw", "eye", "ear", "nose", "lip", "cheek", "brow", "temporal", "tongue", "levator", "oris", "risorius", "special", "orbicularis")
TWA = [o for o in bpy.data.objects if o.name.startswith("Prop_TweezerArm")]
for rnd in range(6):
    # 1 tweezers on the pinch (3 passes)
    for it in range(3):
        D = {}
        for f in range(960, 1146):
            sc.frame_set(f); t = tips(Mo, "R"); D[f] = (t[0] + t[1]) / 2 - TW.matrix_world.translation
        for f, d in D.items():
            shift(TW, "location", f, d)
            if f >= 1042: shift(BR, "location", f, d * smooth((f - 1042) / 14.0))
        upd(TW, BR)
    # 2 palm props
    for pn, a, s, f0, f1 in (("Brick_Small", Ma, "L", 2152, 2310), ("Prop_Inhaler", Ma, "R", 1606, 1720)):
        o = bpy.data.objects[pn]
        for it in range(4):
            D = {}
            for f in range(f0, f1 + 1):
                sc.frame_set(f)
                if o.hide_render: continue
                lo, hi = bbox(o); c = (lo + hi) / 2
                d, t = min(((bd(lo, hi, q), q) for q in tips(a, s)), key=lambda x: x[0])
                if d > 0.008: D[f] = (t - c).normalized() * (d - 0.008)
            for f, d in D.items(): shift(o, "location", f, d)
            upd(o)
    # 3 Mom's face
    hits = []
    for f in range(1058, 1085):
        sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
        e = MB.evaluated_get(dg); me = e.to_mesh(); V = [e.matrix_world @ v.co for v in me.vertices]
        T = BVHTree.FromPolygons(V, [tuple(p.vertices) for p in me.polygons if all(dom[i].startswith(HEAD) for i in p.vertices)]); e.to_mesh_clear()
        need = 0.0
        for o in [BR] + TWA:
            eo = o.evaluated_get(dg); mo = eo.to_mesh()
            for v in mo.vertices:
                p = eo.matrix_world @ v.co; loc, n, _, d = T.find_nearest(p, 0.2)
                if loc is None: continue
                sd = d if (p - loc).dot(n) >= 0 else -d; need = max(need, (0.02 if o is BR else 0.005) - sd)
            eo.to_mesh_clear()
        if need > 0:
            hc = Mo.matrix_world @ Mo.pose.bones["head"].head; dirn = BR.matrix_world.translation - hc; dirn.z = 0; hits.append((f, dirn.normalized() * (need + 0.015)))
    print("RESNAP round", rnd, "mom-face frames", len(hits))
    if not hits and rnd > 0: break
    for f, d in hits:
        n = "IK_hand.R"; dl = Mo.data.bones[n].matrix_local.to_3x3().inverted() @ (Mo.matrix_world.to_3x3().inverted() @ d)
        shift(Mo, 'pose.bones["%s"].location' % n, f, dl)
    upd(Mo)
for m, v in masks: m.show_viewport = v
for pn, a, s, f0, f1 in (("Prop_Tweezers", Mo, "R", 960, 1145), ("Brick_Small", Ma, "L", 2152, 2310), ("Prop_Inhaler", Ma, "R", 1606, 1720)):
    o = bpy.data.objects[pn]; ds = []
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        if o.hide_render: continue
        lo, hi = bbox(o); ds.append(min(bd(lo, hi, q) for q in tips(a, s)))
    print("RESNAP", pn, "max bbox-to-fingertip %.2f cm" % (max(ds) * 100))
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True); print("RESNAP saved", OUT)
