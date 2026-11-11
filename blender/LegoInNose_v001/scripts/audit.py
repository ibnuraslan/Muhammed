"""Contact + camera audit for LegoInNose.  blender -b anim.blend --python audit.py -- <report.txt>"""
import sys, math
import bpy
from mathutils import Vector
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
L = []
def log(*a): L.append(" ".join(str(x) for x in a)); print(*a)
def ground_z(x, y):
    if 7.75 < x < 8.95 and 1.25 < y < 2.35: return 0.06
    if -1.2 < x < 1.4 and -0.9 < y < 1.0: return 0.012
    return 0.0
def vis(o): return not o.hide_render
TUNNEL = [(719, 752), (850, 874), (1099, 1134), (1308, 1334)]
in_tunnel = lambda f: any(a - 2 <= f <= b + 2 for a, b in TUNNEL)
cam = bpy.data.objects["CAM_Film"]
walls = [o for o in bpy.data.objects if o.type == "MESH" and any(k in o.name for k in ("_Wall", "_Floor", "_Ceiling"))]
# --- camera: speed, inside walls
prev = None; speeds = []; inside = []
for f in range(1, sc.frame_end + 1):
    sc.frame_set(f); p = cam.matrix_world.translation.copy()
    if prev is not None: speeds.append((f, (p - prev).length * 60))
    prev = p
    if not in_tunnel(f):
        for w in walls:
            lo = w.matrix_world @ Vector(w.bound_box[0]); hi = w.matrix_world @ Vector(w.bound_box[6])
            if all(min(lo[i], hi[i]) - 0.0 < p[i] < max(lo[i], hi[i]) for i in range(3)):
                inside.append((f, w.name))
mx = max(speeds, key=lambda x: x[1])
log("CAMERA max speed %.1f m/s at f%d (tunnel frames allowed)" % (mx[1], mx[0]))
spikes = [(f, round(s, 1)) for (f, s), (f0, s0) in zip(speeds[1:], speeds) if abs(s - s0) > 3.0 and not in_tunnel(f)]
log("CAMERA speed jumps >3 m/s per frame outside tunnels:", spikes[:20], "count", len(spikes))
runs = []
for f, n in inside:
    if runs and runs[-1][1] == n and f - runs[-1][0][-1] <= 1: runs[-1][0].append(f)
    else: runs.append(([f], n))
log("CAMERA inside wall/floor boxes (outside tunnels):", [(r[0][0], r[0][-1], r[1]) for r in runs] or "none")
# held framing: angle change of the view per second
hold = []
for f in range(1, sc.frame_end - 90, 30):
    sc.frame_set(f); a = cam.matrix_world.copy(); sc.frame_set(f + 90); b = cam.matrix_world.copy()
    dv = (a.to_3x3() @ Vector((0, 0, -1))).angle(b.to_3x3() @ Vector((0, 0, -1)))
    dp = (a.translation - b.translation).length
    if dv < math.radians(4) and dp < 0.03: hold.append(f)
log("FRAMING held >1.5 s (view moved <4 deg and <3 cm):", hold or "none")
# --- feet: hover / sink for visible characters (ankle bone height above its rest height)
for nm in ("Boy", "Teen", "Man", "Mom"):
    a = bpy.data.objects[nm]; bad = []
    rest = {s: a.data.bones["foot." + s].head_local.z for s in "LR"}
    for f in range(1, sc.frame_end + 1, 5):
        sc.frame_set(f)
        if a.hide_render: continue
        for s in "LR":
            p = a.matrix_world @ a.pose.bones["foot." + s].head
            g = ground_z(p.x, p.y)
            if 4.6 < p.x < 5.6 and 0.3 < p.y < 2.4: g = 0.56                       # mattress
            if -1.8 < p.x < -0.6 and 1.75 < p.y < 2.25 and p.z > 0.3: g = 0.47     # bench seat
            d = p.z - g - rest[s]
            pb = a.pose.bones["IK_foot." + s]
            # only judge feet that are meant to be planted (low)
            if d < -0.025: bad.append((f, s, "sink", round(d, 3)))
            elif 0.04 < d < 0.12 and nm != "Man": bad.append((f, s, "hover", round(d, 3)))
    log("FEET", nm, "issues", len(bad), bad[:12])
# --- grip: held props stay at the pinch point
def pinch(nm, s):
    a = bpy.data.objects[nm]
    return (a.matrix_world @ a.pose.bones["finger1-3." + s].tail + a.matrix_world @ a.pose.bones["finger2-3." + s].tail) / 2
for prop, nm, s, f0, f1 in (("Brick_Big", "Boy", "R", 1, 130), ("Brick_Small", "Boy", "R", 340, 710), ("Prop_Inhaler", "Man", "R", 1610, 1715),
                            ("Prop_Tissue", "Man", "R", 1520, 1580), ("Prop_Tweezers", "Mom", "R", 965, 1140)):
    o = bpy.data.objects[prop]; ds = []
    for f in range(f0, f1 + 1, 5):
        sc.frame_set(f); ds.append((o.matrix_world.translation - pinch(nm, s)).length)
    log("GRIP %-14s %s.%s f%d-%d  max %.1f mm  mean %.1f mm" % (prop, nm, s, f0, f1, max(ds) * 1000, sum(ds) / len(ds) * 1000))
# --- the bricks in the palm (shower)
o = bpy.data.objects["Brick_Small"]; a = bpy.data.objects["Man"]
ds = []
for f in range(2152, 2310, 6):
    sc.frame_set(f); ds.append((o.matrix_world.translation - a.matrix_world @ a.pose.bones["finger3-1.L"].head).length)
log("PALM brick to palm centre max %.1f mm" % (max(ds) * 1000))
# --- penetration count: fingertips/toes inside furniture or floors, and characters intersecting each other
dg = bpy.context.evaluated_depsgraph_get()
solids = [o for o in bpy.data.objects if o.type == "MESH" and (o.name.endswith("_Floor") or o.name in ("BR_Mattress", "Prop_Tub", "LR_Rug", "BA_ShowerTray")
          or (o.parent and o.parent.name in ("LR_Sofa", "LR_Bench", "LR_CoffeeTable")))]
def inside(p, o):
    """parity ray test against one evaluated mesh"""
    oe = o.evaluated_get(dg); Mi = oe.matrix_world.inverted(); q = Mi @ p; d = (Mi.to_3x3() @ Vector((0, 0, 1))).normalized()
    n_ = 0; start = q
    for _ in range(12):
        hit, loc, nrm, idx = oe.ray_cast(start + d * 1e-5, d)
        if not hit: break
        n_ += 1; start = loc
    return n_ % 2 == 1
TIPS = ["finger%d-3.%s" % (i, s) for i in range(1, 6) for s in "LR"]
pen = []
chars = [bpy.data.objects[n] for n in ("Boy", "Teen", "Man", "Mom")]
for f in range(1, sc.frame_end + 1, 10):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    vis = [a for a in chars if not a.hide_render]
    for a in vis:
        for b in TIPS:
            p = a.matrix_world @ a.pose.bones[b].tail
            for o in solids:
                lo = o.matrix_world @ Vector(o.bound_box[0]); hi = o.matrix_world @ Vector(o.bound_box[6])
                if all(min(lo[i], hi[i]) - 0.01 < p[i] < max(lo[i], hi[i]) + 0.01 for i in range(3)) and inside(p, o):
                    pen.append((f, a.name, b, o.name))
    for i, a in enumerate(vis):
        for b2 in vis[i + 1:]:
            pa = [a.matrix_world @ pb.head for pb in a.pose.bones if pb.bone.use_deform and not pb.name.startswith(("finger", "tongue", "toe", "orbic", "oris", "levator", "risor", "temporal", "oculi", "special", "jaw", "eye"))]
            pb_ = [b2.matrix_world @ pb.head for pb in b2.pose.bones if pb.bone.use_deform and not pb.name.startswith(("finger", "tongue", "toe", "orbic", "oris", "levator", "risor", "temporal", "oculi", "special", "jaw", "eye"))]
            dmin = min((x - y).length for x in pa for y in pb_)
            if dmin < 0.06: pen.append((f, a.name, "body", b2.name, round(dmin, 3)))
import collections
log("PENETRATION count (fingertips inside furniture/floors + characters' joints <6 cm apart, every 10th frame):", len(pen), "by kind:", dict(collections.Counter((p[1], p[3]) for p in pen)), "examples:", pen[:6])
# --- camera never switches
log("CAMERAS", [o.name for o in bpy.data.objects if o.type == "CAMERA"], "markers bound to cameras:", [m.name for m in sc.timeline_markers if m.camera])
open(OUT, "w").write("\n".join(L) + "\n")
