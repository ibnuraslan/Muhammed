"""Re-key every hand-audit hit (client hands rule, Nov 11 23:00 UTC).
blender -b in.blend --python hand_fix.py -- out.blend [rounds]
For each flagged frame the hand's IK target gets a key that pushes it out of what it hit:
  own body / own shirt / other character: along the hit surface normal (nearest point), 1.2 cm per round
  hand vs hand: both hands apart along the L-R line, 1 cm each
Rounds repeat (audit at every 2nd frame) until nothing is hit or the rounds run out."""
import sys, collections, bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]
OUT = a[0]; ROUNDS = int(a[1]) if len(a) > 1 else 4
sc = bpy.context.scene
HAND = ("wrist", "finger", "metacarpal"); TORSO = ("spine", "neck", "head", "breast", "pelvis", "clavicle", "jaw")
def region_faces(ob, me):
    arm_ = next((p for p in [ob.parent, getattr(ob.parent, "parent", None)] if p and p.type == "ARMATURE"), None)
    bones = set(arm_.data.bones.keys()) if arm_ else set()
    vg = {g.index: g.name for g in ob.vertex_groups if g.name in bones}
    dom = []
    for v in me.vertices:
        best = max((g for g in v.groups if g.group in vg), key=lambda g: g.weight, default=None)
        dom.append(vg.get(best.group, "") if best else "")
    reg = []
    for p in me.polygons:
        names = [dom[i] for i in p.vertices]
        if all(n.startswith(HAND) for n in names): reg.append("hand" + ("L" if names[0].endswith(".L") else "R"))
        elif all(n.startswith(TORSO) for n in names): reg.append("torso")
        else: reg.append(None)
    return reg
def bvh(me, Mw, reg, want):
    vs = [Mw @ v.co for v in me.vertices]
    polys = [list(p.vertices) for i, p in enumerate(me.polygons) if reg[i] in want]
    if not polys: return None, None
    used = sorted({i for p in polys for i in p}); ctr = sum((vs[i] for i in used), Vector()) / len(used)
    return BVHTree.FromPolygons(vs, polys, epsilon=0.0), ctr
REG = {}
def gather(dg):
    T = {}
    for nm in ("Boy", "Teen", "Man", "Mom"):
        arm = bpy.data.objects[nm]; body = bpy.data.objects[nm + "_Body"]
        if arm.hide_render or body.hide_render: continue
        meshes = [body] + [o for o in arm.children_recursive if o.type == "MESH" and "suit" in o.name and not o.hide_render]
        t = dict(L=None, R=None, cL=None, cR=None, solids=[])
        for ob in meshes:
            e = ob.evaluated_get(dg); me = e.to_mesh()
            key = (ob.name, len(me.polygons))
            if key not in REG: REG[key] = region_faces(ob, me)
            reg = REG[key]; Mw = e.matrix_world
            if ob is body:
                t["L"], t["cL"] = bvh(me, Mw, reg, ("handL",)); t["R"], t["cR"] = bvh(me, Mw, reg, ("handR",))
            tb, _ = bvh(me, Mw, reg, ("torso",))
            if tb: t["solids"].append(tb)
            e.to_mesh_clear()
        T[nm] = t
    return T
HELD = (("Brick_Big", "Boy", "R", 1, 131), ("Brick_Small", "Boy", "R", 336, 712), ("Prop_Tweezers", "Mom", "R", 960, 1145),
        ("Prop_Inhaler", "Man", "R", 1606, 1720), ("Prop_Tissue", "Man", "R", 1515, 1582), ("Prop_Gamepad", "Teen", "R", 1395, 1439), ("Prop_Phone", "Man", "R", 1440, 1469))
def push(nm, s, f, delta):
    arm = bpy.data.objects[nm]; n = "IK_hand." + s; pb = arm.pose.bones[n]
    d_arm = arm.matrix_world.to_3x3().inverted() @ delta
    d_loc = arm.data.bones[n].matrix_local.to_3x3().inverted() @ d_arm
    pb.location = pb.location + d_loc; pb.keyframe_insert("location", frame=f, group=n)
def hand_frame(nm, s):
    a = bpy.data.objects[nm]; P = lambda b, t=False: a.matrix_world @ (a.pose.bones[b].tail if t else a.pose.bones[b].head)
    wr = P("wrist." + s); d = (P("finger3-1." + s) - wr).normalized(); ax = (P("finger2-1." + s) - P("finger5-1." + s)).normalized()
    n_ = d.cross(ax).normalized(); ax = n_.cross(d).normalized()
    from mathutils import Matrix
    pin = (P("finger1-3." + s, True) + P("finger2-3." + s, True)) / 2
    return Matrix.Translation(pin) @ Matrix((ax, d, n_)).transposed().to_4x4()
# held props: remember each prop relative to its hand before any push, re-bake after
REL = {}
for prop, nm, s, f0, f1 in HELD:
    if prop not in bpy.data.objects: continue
    for f in range(f0, f1 + 1, 2):
        sc.frame_set(f); REL[(prop, f)] = hand_frame(nm, s).inverted() @ bpy.data.objects[prop].matrix_world
    REL[(prop, f1)] = REL.get((prop, f1)) or (sc.frame_set(f1) or hand_frame(nm, s).inverted() @ bpy.data.objects[prop].matrix_world)
frames = list(range(sc.frame_start, sc.frame_end + 1, 2))
history = []
for rnd in range(ROUNDS):
    fixes = []; count = collections.Counter()
    for f in frames:
        sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
        T = gather(dg)
        for nm, t in T.items():
            if t["L"] and t["R"] and t["L"].overlap(t["R"]):
                d = (t["cL"] - t["cR"]); d = d.normalized() if d.length > 1e-6 else Vector((1, 0, 0))
                fixes.append((f, nm, "L", d * 0.018)); fixes.append((f, nm, "R", -d * 0.018)); count["hand-hand"] += 1
            for s in "LR":
                h, c = t[s], t["c" + s]
                if not h: continue
                for on, ot in T.items():
                    for solid in ot["solids"]:
                        if h.overlap(solid):
                            loc, nrm, idx, dist = solid.find_nearest(c)
                            dirv = (c - loc) if loc is not None and (c - loc).length > 1e-4 else (nrm if nrm is not None else Vector((0, 0, 1)))
                            fixes.append((f, nm, s, dirv.normalized() * 0.02)); count["hand-" + ("own" if on == nm else on)] += 1
                            break
    history.append((rnd, len(fixes), dict(count)))
    print("ROUND", rnd, "hits", sum(count.values()), dict(count))
    if not fixes: break
    # apply: evaluate the current (fcurve) location at each frame, add the push, key it
    for f, nm, s, delta in fixes:
        sc.frame_set(f); push(nm, s, f, delta)
for prop, nm, s, f0, f1 in HELD:
    if prop not in bpy.data.objects: continue
    o = bpy.data.objects[prop]; o.rotation_mode = "QUATERNION"
    ad = o.animation_data
    if ad and ad.action:                      # drop the old baked keys inside the held range (avoid interleaved spikes)
        for l in getattr(ad.action, "layers", []):
            for st in l.strips:
                for cb in st.channelbags:
                    for fc in cb.fcurves:
                        if fc.data_path in ("location", "rotation_quaternion"):
                            for kp in [k for k in fc.keyframe_points if f0 <= k.co.x <= f1][::-1]:
                                fc.keyframe_points.remove(kp)
    for f in sorted(set(list(range(f0, f1 + 1, 2)) + [f1])):
        sc.frame_set(f); M_ = hand_frame(nm, s) @ REL[(prop, f)]
        loc, rot, sca = M_.decompose()
        if o.parent: 
            M_ = o.parent.matrix_world.inverted() @ M_; loc, rot, sca = M_.decompose()
        o.location = loc; o.keyframe_insert("location", frame=f)
        if o.rotation_quaternion.dot(rot) < 0: rot = -rot
        o.rotation_quaternion = rot; o.keyframe_insert("rotation_quaternion", frame=f)
print("HELD props re-baked to the moved hands")
open(OUT.replace(".blend", "_handfix.txt"), "w").write("\n".join("round %d: %d pushes %s" % h for h in history) + "\n")
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("HAND_FIX saved", OUT)
