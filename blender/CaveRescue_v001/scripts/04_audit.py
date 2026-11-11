"""CaveRescue contact audit.
blender -b anim.blend --python 04_audit.py -- <report.txt> [step]
- feet: planted-foot hover/sink vs the set floor (ankle height above ground minus the rest ankle height)
- BVH penetration: hand + foot regions of every on-set character vs the sets, props and the other characters;
  head items (torches, dive masks) vs their own head and the sets
- camera inside geometry (first hit along 6 axes is a back face), ignoring the rock-wipe frames
"""
import sys, math
import bpy, bmesh
from mathutils import Vector as V
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]
OUT = a[0]; STEP = int(a[1]) if len(a) > 1 else 12
sc = bpy.context.scene
CX = sc["CX"]
TERR, TUNL, LEDGE = bpy.data.objects["S1_Terrain"], bpy.data.objects["S2_Tunnel"], bpy.data.objects["S4_Ledge"]
SETS = [bpy.data.objects[n] for n in ("S1_Terrain", "S2_Tunnel", "S4_Ledge", "S4_Cavern", "S5_Passage", "S3_Mountain")]
SOLIDS = ("S1_Terrain", "S4_Ledge", "S3_Mountain")
def _ray(o, x, y, z0):
    hit, loc, nrm, idx = o.ray_cast(V((x, y, z0)), V((0, 0, -1))); return loc.z if hit else None
TUN = [V(p) for p in sc["TUN"]]
def ground_z(x, y):
    if x > 300:
        z = _ray(LEDGE, x, y, 3.0); return z if z is not None else -3.0
    if y > -2.6:
        i = min(range(len(TUN)), key=lambda k: (TUN[k].x - x) ** 2 + (TUN[k].y - y) ** 2)
        z = _ray(TUNL, x, y, TUN[i].z + 1.6)
        if z is not None: return z
    z = _ray(TERR, x, y, 60.0); return z if z is not None else 0.0
RIGS = [o for o in bpy.data.objects if o.type == 'ARMATURE']
SKIP_FEET = {"Boy3": [(1705, 2016)], "DiverA": [(1715, 2406)], "DiverB": [(1714, 2406)], "Boy2": [(2407, 2570)], "Boy4": [(2725, 3090)]}   # kneeling: feet lie flat by design
WIPES = [(576, 590), (1005, 1024), (2550, 2586), (2718, 2730)]
def skip(n, f):
    return any(a_ <= f <= b_ for a_, b_ in SKIP_FEET.get(n, []))
HAND = ("wrist", "finger", "metacarpal"); FOOT = ("foot", "toe")
REG = {r.name: bpy.data.objects.get(r.name + ".body") for r in RIGS if bpy.data.objects.get(r.name + ".body")}
def bvh_of(o, dg, prefixes=None):
    ev = o.evaluated_get(dg); me = ev.to_mesh()
    M = o.matrix_world
    keep = None
    if prefixes:
        gi = {g.index for g in o.vertex_groups if any(g.name.startswith(p) for p in prefixes)}
        keep = set()
        for v in me.vertices:
            for g in v.groups:
                if g.group in gi and g.weight > 0.5: keep.add(v.index); break
    verts = [M @ v.co for v in me.vertices]
    polys = [tuple(p.vertices) for p in me.polygons if keep is None or all(i in keep for i in p.vertices)]
    ev.to_mesh_clear()
    if not polys: return None
    return BVHTree.FromPolygons(verts, polys)
def on_set(r):
    return (r.matrix_world @ r.pose.bones["root"].head).z > -40
# body meshes without subsurf for the region test (MPFB body: armature + mask + subsurf; disable subsurf while auditing)
for r in RIGS:
    for ch in r.children:
        for m in ch.modifiers:
            if m.type == 'SUBSURF': m.show_viewport = False
props = [o for o in bpy.data.objects if o.type == 'MESH' and (o.name.startswith("Prop_") or "_Tank" in o.name or o.name.startswith("Bike_"))]
headitems = [o for o in bpy.data.objects if o.type == 'MESH' and (o.name.endswith("_HeadTorch") or o.name.endswith("_Mask") or o.name == "Prop_FullFaceMask")]
lines = []; hover = []; pen = []; camin = []
frames = list(range(1, sc.frame_end + 1, STEP))
dg = bpy.context.evaluated_depsgraph_get()
set_bvh = {o.name: bvh_of(o, dg) for o in SETS}
prev_ank = {}
for f in frames:
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    live = [r for r in RIGS if on_set(r)]
    # ---- feet
    for r in live:
        rb = r.pose.bones["root"]; up = (r.matrix_world.to_3x3() @ rb.matrix.to_3x3() @ V((0, 1, 0))).normalized()
        if up.z < 0.8 or skip(r.name, f): continue
        for s in "LR":
            fb = r.pose.bones["foot." + s]; ank = r.matrix_world @ fb.head
            rest = r.data.bones["foot." + s].head_local.z
            key = (r.name, s); mv = (ank - prev_ank[key]).length / STEP if key in prev_ank else 0
            prev_ank[key] = ank.copy()
            if mv > 0.004: continue                 # swinging foot
            h = ank.z - ground_z(ank.x, ank.y) - rest
            if abs(h) > 0.03: hover.append((f, r.name, s, round(h, 3)))
    # ---- penetration (hands/feet vs sets, props, other characters)
    char_bvh = {}
    for r in live:
        if r.name not in REG: continue
        body = REG[r.name]
        char_bvh[r.name] = (bvh_of(body, dg, HAND), bvh_of(body, dg, FOOT), bvh_of(body, dg))
    prop_bvh = {o.name: bvh_of(o, dg) for o in props if not o.hide_render}
    for n, (hb, fb, whole) in char_bvh.items():
        for part, b in (("hand", hb), ("foot", fb)):
            if b is None: continue
            for sn, sb in list(set_bvh.items()) + list(prop_bvh.items()):
                if sb is None or sn.startswith(n + "_"): continue      # own worn gear touches the body by design
                k = len(b.overlap(sb))
                if k: pen.append((f, n, part, sn, k))
            for m, (_, _, w2) in char_bvh.items():
                if m != n and w2 is not None:
                    k = len(b.overlap(w2))
                    if k: pen.append((f, n, part, m, k))
    for o in headitems:
        if o.hide_render: continue
        ob = bvh_of(o, dg)
        own = o.name.split("_")[0]
        if own in char_bvh and ob:
            k = len(ob.overlap(char_bvh[own][2]))
            if k: pen.append((f, o.name, "head-item", own + " body", k))
    # ---- camera inside geometry
    if not any(a_ <= f <= b_ for a_, b_ in WIPES):
        cp = sc.camera.matrix_world.translation
        inside = 0
        for d in (V((1, 0, 0)), V((-1, 0, 0)), V((0, 1, 0)), V((0, -1, 0)), V((0, 0, 1)), V((0, 0, -1))):
            best = None
            for sn, sb in set_bvh.items():
                if sn not in SOLIDS: continue
                hit = sb.ray_cast(cp, d)
                if hit[0] is not None and (best is None or hit[3] < best[1]): best = (hit[1], hit[3])
            if best and best[0].dot(d) > 0: inside += 1
        if inside >= 5: camin.append((f, tuple(round(x, 2) for x in cp)))
lines.append("CaveRescue audit, %d frames sampled every %d" % (len(frames), STEP))
lines.append("FEET hover/sink > 3 cm on planted feet: %d" % len(hover))
lines += ["  f%d %s.%s %+.3f m" % h for h in hover[:80]]
lines.append("PENETRATION overlapping triangle pairs (hand/foot/head-item vs set/prop/character): %d events, %d pairs" % (len(pen), sum(p[4] for p in pen)))
import collections
agg = collections.Counter(); first = {}
for p in pen:
    k = (p[1], p[2], p[3]); agg[k] += p[4]; first.setdefault(k, p[0])
lines += ["  %6d pairs  %s %s -> %s (first f%d)" % (v, k[0], k[1], k[2], first[k]) for k, v in agg.most_common()]
lines.append("CAMERA inside geometry (outside rock wipes): %d" % len(camin))
lines += ["  f%d %s" % c for c in camin]
open(OUT, "w").write("\n".join(lines) + "\n")
print("\n".join(lines[:6]))
print("AUDIT_DONE")
