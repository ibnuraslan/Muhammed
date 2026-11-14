"""v008f: limb_check (director 9a0a692) ARMBODY: arms inside their own torso / another body.
blender -b in.blend --python arm_fix.py -- out.blend [rounds] [step]
Same test as limb_check (bone-axis points of upperarm01/02, lowerarm01/02 and the wrist tail, >3 cm under the torso surface
(spine/pelvis/clavicle/breast/neck/root/shoulder faces) or under another character's skin), but the shoulder joint itself
(upperarm01 at 0 and 1/4) is skipped: it always sits in the open arm hole of the torso shell. For each flagged frame the IK hand
is pushed along the mean surface normal (out of the body) by depth + 2 cm and the elbow pole 10 cm out to that side; repeated.
Held props move with the hand (HELD)."""
import bpy, sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; ROUNDS = int(a[1]) if len(a) > 1 else 6; STEP = int(a[2]) if len(a) > 2 else 2
sc = bpy.context.scene
TORSO_G = ("spine", "pelvis", "clavicle", "breast", "neck", "root", "shoulder")
ARM = ["upperarm01", "upperarm02", "lowerarm01", "lowerarm02"]
HELD = (("Brick_Big", "Boy", "R", 1, 150), ("Brick_Small", "Boy", "R", 336, 744), ("Prop_Tweezers", "Mom", "R", 960, 1145), ("Brick_Big", "Mom", "R", 1042, 1145),
        ("Prop_Inhaler", "Man", "R", 1606, 1720), ("Prop_Tissue", "Man", "R", 1515, 1582), ("Prop_Gamepad", "Teen", "R", 1395, 1439), ("Prop_Phone", "Man", "R", 1440, 1469), ("Brick_Small", "Man", "L", 2152, 2310))
RIGS = [o for o in bpy.data.objects if o.type == "ARMATURE" and "upperarm01.L" in o.pose.bones and "IK_hand.L" in o.pose.bones]
BODY = {r.name: max([c for c in r.children_recursive if c.type == "MESH" and "body" in c.name.lower()], key=lambda c: len(c.data.vertices)) for r in RIGS}
masks = []
for r in RIGS:
    for m in BODY[r.name].modifiers:
        if m.type in ("MASK", "SUBSURF", "MULTIRES"): masks.append((m, m.show_viewport)); m.show_viewport = False
CLS = {}
for r in RIGS:
    b = BODY[r.name]; gi = {g.index: g.name.lower() for g in b.vertex_groups}; bones = {bn.name.lower() for bn in r.data.bones}
    torso, skin = set(), set()
    for v in b.data.vertices:
        gs = [g for g in v.groups if g.weight > 0.05]
        if any(gi.get(g.group, "").startswith(("helper", "joint")) and g.weight > 0.5 for g in gs): continue
        skin.add(v.index); gs = [g for g in gs if gi.get(g.group, "") in bones]
        if gs and any(gi[max(gs, key=lambda g: g.weight).group].startswith(k) for k in TORSO_G): torso.add(v.index)
    CLS[r.name] = (torso, skin)
def W(r, n, tail=False): pb = r.pose.bones[n]; return r.matrix_world @ (pb.tail if tail else pb.head)
def fcs(o): return [fc for l in o.animation_data.action.layers for st in l.strips for cb in st.channelbags for fc in cb.fcurves] if o.animation_data and o.animation_data.action else []
def shift_loc(o, path, f, d_local):
    for fc in [c for c in fcs(o) if c.data_path == path]: fc.keyframe_points.insert(f, fc.evaluate(f) + d_local[fc.array_index], options={"FAST"})
def push_bone(r, n, f, d_world):
    dl = r.data.bones[n].matrix_local.to_3x3().inverted() @ (r.matrix_world.to_3x3().inverted() @ d_world)
    shift_loc(r, 'pose.bones["%s"].location' % n, f, dl)
def armpts(r, s):
    pts = []
    for bn in ARM:
        n = bn + "." + s; h, t = W(r, n), W(r, n, True)
        for k in range(5):
            if bn == "upperarm01" and k < 2: continue
            pts.append(h.lerp(t, k / 4))
    return pts + [W(r, "wrist." + s, True)]
def scan(frames):
    hits = {}
    for f in frames:
        sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
        live = [r for r in RIGS if not r.hide_render and not BODY[r.name].hide_render]
        T = {}
        for r in live:
            e = BODY[r.name].evaluated_get(dg); me = e.to_mesh(); mw = e.matrix_world
            vs = [mw @ v.co for v in me.vertices]; ps = [tuple(p.vertices) for p in me.polygons]; e.to_mesh_clear()
            tor, sk = CLS[r.name]
            T[r.name] = (BVHTree.FromPolygons(vs, [p for p in ps if all(i in tor for i in p)]), BVHTree.FromPolygons(vs, [p for p in ps if all(i in sk for i in p)]))
        for r in live:
            for s in "LR":
                deep, nsum, cnt = 0.0, Vector(), 0
                for p in armpts(r, s):
                    for tree in [T[r.name][0]] + [T[o.name][1] for o in live if o is not r]:
                        loc, nr, _, d = tree.find_nearest(p, 0.12)
                        if loc is not None and d > 0.03 and (p - loc).dot(nr) < 0: deep = max(deep, d); nsum += nr; cnt += 1; break
                if cnt >= 2: hits[(r.name, s, f)] = (deep, nsum.normalized())
    return hits
frames = list(range(sc.frame_start, sc.frame_end + 1, STEP))
for rnd in range(ROUNDS):
    hits = scan(frames if rnd == 0 else sorted({k[2] for k in prev}))
    print("ARMFIX round", rnd, "hits", len(hits), sorted({(k[0], k[1]) for k in hits}))
    if not hits: break
    for (rn, s, f), (deep, n) in hits.items():
        r = bpy.data.objects[rn]; sc.frame_set(f)
        side = (W(r, "upperarm01." + s) - W(r, "upperarm01." + ("R" if s == "L" else "L"))).normalized()
        d = (n * (deep + 0.02)) + side * 0.01
        push_bone(r, "IK_hand." + s, f, d); push_bone(r, "Pole_elbow." + s, f, side * 0.1 + n * 0.05)
        for pn, cn, cs, f0, f1 in HELD:
            if cn == rn and cs == s and f0 <= f <= f1 and pn in bpy.data.objects:
                o = bpy.data.objects[pn]; shift_loc(o, "location", f, (o.parent.matrix_world.inverted().to_3x3() @ d) if o.parent else d)
    for o in RIGS + [bpy.data.objects[h[0]] for h in HELD if h[0] in bpy.data.objects]:
        for fc in fcs(o): fc.update()
    prev = hits
for m, v in masks: m.show_viewport = v
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True); print("ARMFIX saved", OUT)
