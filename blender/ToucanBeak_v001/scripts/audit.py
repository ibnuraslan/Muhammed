"""Contact / penetration audit for ToucanBeak.   blender -b film.blend -P audit.py -- <report.txt> [step]
BIRD_HOVER / BIRD_SINK   toucan toes vs the support it stands on (perch / towel / platform)
HAND_IN_BIRD             glove (hand) vertices inside the toucan body/beak (BVH overlap pairs)
HAND_FLOAT               VetA's cradling hands more than 2.5 cm from the bird while holding
HEAD_ITEM                none worn (no masks/caps/headsets in this film) - reported as n/a
CAMERA_INSIDE            camera inside a mesh (ray parity in 6 directions)
PROP_FLOAT               fig on the platform / in the beak off its contact"""
import sys, math
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; STEP = int(a[1]) if len(a) > 1 else 20
sc = bpy.context.scene; OB = bpy.data.objects
issues = {}; counts = {}
def flag(k, f, m): issues.setdefault(k, []).append((f, m))
def tree(o, dg, sel=None):
    ev = o.evaluated_get(dg); me = ev.to_mesh(); mw = o.matrix_world
    vs = [mw @ v.co for v in me.vertices]
    polys = [tuple(p.vertices) for p in me.polygons if sel is None or sel(p)]
    ev.to_mesh_clear()
    return BVHTree.FromPolygons(vs, polys, all_triangles=False), vs
def support(f):
    if f < 528: return OB["Perch"]
    if f < 1976: return OB["Towel"]
    return OB["Feeding_platform"]
body = OB["Toucan_body"]; rig = OB["ToucanRig"]
gloveA = OB["VetA.body"]; gloveB = OB["VetB.body"]
def glove_sel(o):
    gi = [i for i, m in enumerate(o.data.materials) if m and m.name.startswith("Nitrile")]
    return (lambda p: p.material_index in gi)
EXCL = {"Wall_patch", "Monitor_back", "Void_front", "Void_box", "Mote_emitter", "Extrude_cutter", "Print_clip"}
dirs = [Vector(d) for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))]
F0 = int(a[2]) if len(a) > 2 else sc.frame_start; F1 = int(a[3]) if len(a) > 3 else sc.frame_end
frames = list(range(F0, F1 + 1, STEP))
for f in frames:
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    # ---- toes vs support
    ev = body.evaluated_get(dg); me = ev.to_mesh(); mw = body.matrix_world
    toes = [mw @ v.co for v in me.vertices if v.co.z < 0.012 and v.co.y > -0.075]
    ev.to_mesh_clear()
    sup = support(f); st, _ = tree(sup, dg)
    gaps = []
    for p in toes[::3]:
        h = st.ray_cast(p + Vector((0, 0, 0.08)), Vector((0, 0, -1)), 0.3)
        if h[0] is not None: gaps.append(p.z - h[0].z)
    if gaps:
        lo = min(gaps)
        counts["toe_samples"] = counts.get("toe_samples", 0) + 1
        if lo > 0.015: flag("BIRD_HOVER", f, "lowest toe %.1f cm above %s" % (lo * 100, sup.name))
        if lo < -0.02: flag("BIRD_SINK", f, "toe %.1f cm inside %s" % (-lo * 100, sup.name))
    # ---- hands vs bird (clinic)
    if 540 <= f <= 1960:
        bt, bv = tree(body, dg)
        beak = OB["Prosthetic_beak"] if f >= 1692 else OB["Toucan_beak_upper_broken"]
        kt, _ = tree(beak, dg)
        if 1515 <= f < 1692:     # held prosthetic: light finger contact only
            pt_, _ = tree(OB["Prosthetic_beak"], dg); gt_, _ = tree(gloveB, dg, glove_sel(gloveB))
            n_ = len(gt_.overlap(pt_))
            if n_ > 40: flag("HAND_IN_PROP", f, "VetB glove into held prosthetic %d" % n_)
        for nm, g in (("VetA", gloveA), ("VetB", gloveB)):
            ht, hv = tree(g, dg, glove_sel(g))
            n = len(ht.overlap(bt)) + len(ht.overlap(kt))
            if n > 0: flag("HAND_IN_BIRD", f, "%s glove/bird triangle overlaps: %d" % (nm, n))
            counts["hand_checks"] = counts.get("hand_checks", 0) + 1
        # VetA cradling distance
        gi = [i for i, m in enumerate(gloveA.data.materials) if m and m.name.startswith("Nitrile")]
        ev = gloveA.evaluated_get(dg); me = ev.to_mesh(); mw = gloveA.matrix_world
        hv = [mw @ v.co for v in me.vertices][::25]; ev.to_mesh_clear()
        dmin = min((bt.find_nearest(p)[3] for p in hv if bt.find_nearest(p)[0] is not None), default=9)
        if dmin > 0.025: flag("HAND_FLOAT", f, "VetA nearest glove point %.1f cm from bird" % (dmin * 100))
    # ---- hands rule: hand vs other hand, own torso/clothes/head, other characters (clinic, people visible)
    if 530 <= f <= 1975:
        P_ = {}
        for nm in ("VetA", "VetB", "Assist"):
            rg = OB[nm]; bo = OB[nm + ".body"]
            ev = bo.evaluated_get(dg); me = ev.to_mesh(); mw = bo.matrix_world; vs = [mw @ v.co for v in me.vertices]
            wr = {s_: rg.matrix_world @ rg.pose.bones["wrist." + s_].head for s_ in "LR"}
            ch = rg.matrix_world @ rg.pose.bones["spine03"].head; hd = rg.matrix_world @ rg.pose.bones["head"].head
            hand = {s_: [tuple(p.vertices) for p in me.polygons if (mw @ p.center - wr[s_]).length < 0.11] for s_ in "LR"}
            torso = [tuple(p.vertices) for p in me.polygons if (mw @ p.center - ch).length < 0.22 or (mw @ p.center - hd).length < 0.12]
            ev.to_mesh_clear()
            cl = [c for c in rg.children if c.type == 'MESH' and ("suit" in c.name)]
            ct = []
            for c in cl:
                e2 = c.evaluated_get(dg); m2 = e2.to_mesh(); w2 = c.matrix_world
                v2 = [w2 @ v.co for v in m2.vertices]; p2 = [tuple(p.vertices) for p in m2.polygons if (w2 @ p.center - ch).length < 0.22]
                ct.append(BVHTree.FromPolygons(v2, p2)); e2.to_mesh_clear()
            P_[nm] = dict(L=BVHTree.FromPolygons(vs, hand["L"]), R=BVHTree.FromPolygons(vs, hand["R"]), torso=BVHTree.FromPolygons(vs, torso), cloth=ct, all=BVHTree.FromPolygons(vs, [tuple(p.vertices) for p in me.polygons]) if False else None)
        for nm, d in P_.items():
            n = len(d["L"].overlap(d["R"]))
            if n:
                rg_ = OB[nm]; dw = (rg_.matrix_world @ rg_.pose.bones["wrist.L"].head - rg_.matrix_world @ rg_.pose.bones["wrist.R"].head).length
                flag("HAND_HAND", f, "%s L/R hands overlap %d (wrists %.2f m apart)" % (nm, n, dw))
            for s_ in "LR":
                n = len(d[s_].overlap(d["torso"])) + sum(len(d[s_].overlap(t)) for t in d["cloth"])
                if n: flag("HAND_SELF", f, "%s %s hand into own torso/clothes/head %d" % (nm, s_, n))
                for on, od in P_.items():
                    if on == nm: continue
                    n = len(d[s_].overlap(od["torso"])) + len(d[s_].overlap(od["L"])) + len(d[s_].overlap(od["R"]))
                    if n: flag("HAND_OTHER", f, "%s %s hand into %s %d" % (nm, s_, on, n))
        counts["hand_rule_frames"] = counts.get("hand_rule_frames", 0) + 1
    # ---- camera inside geometry
    cam = sc.camera.matrix_world.translation
    back = 0
    for d in dirs:
        r = sc.ray_cast(dg, cam, d, distance=50)
        if r[0] and r[4].name not in EXCL and r[2].dot(d) > 0: back += 1
    if back >= 4: flag("CAMERA_INSIDE", f, "camera at %s inside a mesh (%d/6 back-face hits)" % (tuple(round(x, 2) for x in cam), back))
    # ---- enclosure fig
    if 1976 <= f < 2030:
        fe = OB["Fig_enclosure"]; pt, _ = tree(OB["Feeding_platform"], dg)
        h = pt.ray_cast(fe.matrix_world.translation, Vector((0, 0, -1)), 0.2)
        if h[0] is not None:
            gap = fe.matrix_world.translation.z - 0.024 - h[0].z
            if abs(gap) > 0.01: flag("PROP_FLOAT", f, "fig %.1f cm off the platform" % (gap * 100))
with open(OUT, "w") as fo:
    fo.write("ToucanBeak audit, every %d frames (%d samples)\n" % (STEP, len(frames)))
    fo.write("HEAD_ITEM: n/a (no head-worn items in this film)\n")
    for k in ("BIRD_HOVER", "BIRD_SINK", "HAND_IN_BIRD", "HAND_IN_PROP", "HAND_FLOAT", "HAND_HAND", "HAND_SELF", "HAND_OTHER", "CAMERA_INSIDE", "PROP_FLOAT"):
        L = issues.get(k, [])
        fo.write("%-14s %3d  %s\n" % (k, len(L), "; ".join("f%d %s" % x for x in L[:12])))
    fo.write("counts %s\n" % counts)
print(open(OUT).read())
