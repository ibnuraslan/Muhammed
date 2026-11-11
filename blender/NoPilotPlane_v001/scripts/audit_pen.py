"""Numeric penetration check (client clipping check).  blender -b anim.blend --python audit_pen.py -- report.txt [step]
BVH overlap, sampled every <step> frames (default 10):
- YOU hand vertices (finger*/wrist weight > 0.5) inside props: yokes, handset, throttles, pedestal/seats/panel, door, FO and captain bodies
- YOU shoe vertices below the floor / inside the footrests, seats, captain
- YOU body inside the FO body during the haul
- FO / captain shoe and body vertices below the floor
A vertex counts when it is more than 5 mm inside a closed surface (nearest-face normal test)."""
import sys, bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]; out = a[0]; STEP = int(a[1]) if len(a) > 1 else 10
sc = bpy.context.scene; O = bpy.data.objects
bpy.context.view_layer.layer_collection.children["PASSENGERS"].exclude = True
body = O["YOU.body"]; shoes = [o for o in O["YOU"].children if "shoes" in o.name][0]
gi = {g.index: g.name for g in body.vertex_groups}
hand_idx = [v.index for v in body.data.vertices if any((gi[g.group].startswith("finger") or gi[g.group].startswith("wrist")) and g.weight > 0.5 for g in v.groups)]
PROPS = ["YOKE_L", "YOKE_R", "HANDSET", "THROTTLE_0", "THROTTLE_1", "COCKPIT_FIXED", "PEDESTAL_ITEMS", "PEDESTAL_FWD", "DOOR", "FO.body", "FO.male_elegantsuit01",
         "CAPT.body", "CAPT.male_elegantsuit01", "CABIN_FIXED", "GLARESHIELD_AP"]
PROPS = [p for p in PROPS if p in O]
def bvh(o, dg):
    e = o.evaluated_get(dg); me = e.to_mesh(); M = o.matrix_world
    t = BVHTree.FromPolygons([M @ v.co for v in me.vertices], [tuple(p.vertices) for p in me.polygons]); e.to_mesh_clear(); return t
def world_verts(o, dg, idx=None):
    e = o.evaluated_get(dg); me = e.to_mesh(); M = o.matrix_world
    vs = [M @ me.vertices[i].co for i in idx] if idx is not None else [M @ v.co for v in me.vertices]
    e.to_mesh_clear(); return vs
def inside(t, p):
    loc, n, i, d = t.find_nearest(p, 0.08)
    return loc is not None and d > 0.005 and (p - loc).dot(n) < 0
tot = {}; worst = {}
def add(k, f, n):
    if n:
        tot[k] = tot.get(k, 0) + n
        if n > worst.get(k, (0, 0))[1]: worst[k] = (f, n)
frames = list(range(1, sc.frame_end + 1, STEP)); hits_frames = 0
for f in frames:
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    T = {p: bvh(O[p], dg) for p in PROPS}
    hv = world_verts(body, dg, hand_idx)
    hit = 0
    for p, t in T.items():
        n = sum(1 for v in hv[::2] if inside(t, v))
        add("hand>" + p, f, n); hit += n
    sv = world_verts(shoes, dg)[::3]
    n = sum(1 for v in sv if v.z < -0.01); add("YOU foot>floor", f, n); hit += n
    for p in ("COCKPIT_FIXED", "CAPT.body", "CAPT.male_elegantsuit01", "CABIN_FIXED"):
        if p in T:
            n = sum(1 for v in sv if inside(T[p], v)); add("YOU foot>" + p, f, n); hit += n
    if 1600 <= f <= 2060:
        bv = world_verts(body, dg)[::25]
        n = sum(1 for v in bv if inside(T["FO.body"], v)); add("YOU body>FO.body", f, n); hit += n
    for ch in ("FO", "CAPT"):
        for o in O[ch].children:
            if o.type == 'MESH' and ("shoes" in o.name or o.name.endswith(".body")):
                n = sum(1 for v in world_verts(o, dg)[::9] if v.z < -0.01); add(ch + " %s>floor" % o.name.split(".")[-1], f, n); hit += n
    hits_frames += 1 if hit else 0
L = ["PENETRATION (sampled every %d frames, %d samples; vertices >5 mm inside a surface)" % (STEP, len(frames)),
     "frames with any penetration: %d of %d" % (hits_frames, len(frames)),
     "total penetrating vertex samples: %d" % sum(tot.values())]
for k in sorted(tot, key=lambda k: -tot[k]):
    L.append("  %-40s %6d   worst at %.1f s (%d verts)" % (k, tot[k], (worst[k][0] - 1) / 60, worst[k][1]))
open(out, "w").write("\n".join(L) + "\n"); print("\n".join(L))
