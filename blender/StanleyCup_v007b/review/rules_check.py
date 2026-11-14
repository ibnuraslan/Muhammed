"""Director rules 2-4 per frame. ARMOVER: A's arm/hand drawn in front of B's body/face. DETACHED: hand visible, no visible arm, arm not off-frame.
BRUSH: camera within 0.12 m of a character mesh, 0.10 m of the cup/lid/straw, 0.10 m of any other surface."""
import bpy, sys, json, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; ST = int(a[1]); F0 = int(a[2]) if len(a) > 2 else 1; F1 = int(a[3]) if len(a) > 3 else 1530
sc = bpy.context.scene; cam = sc.camera
RIGS = [bpy.data.objects["Woman_rig"], bpy.data.objects["Fiance_rig"]]
OWN = {r.name: {c.name for c in r.children_recursive if c.type == 'MESH'} for r in RIGS}
CUPN = {o.name for o in bpy.data.objects if o.name.startswith("Tumbler")}
def W(r, b, t=False): pb = r.pose.bones[b]; return r.matrix_world @ (pb.tail if t else pb.head)
def infr(p):
    c = world_to_camera_view(sc, cam, p); return 0.0 <= c.x <= 1.0 and 0.0 <= c.y <= 1.0 and c.z > 0.01
def who(o):
    for r in RIGS:
        if o.name in OWN[r.name]: return r.name
    return None
res = {}
def flag(f, k, s): res.setdefault(str(f), []).append([k, s])
DIRS = [Vector(v).normalized() for v in [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1),(1,1,1),(1,1,-1),(1,-1,1),(1,-1,-1),(-1,1,1),(-1,1,-1),(-1,-1,1),(-1,-1,-1)]]
for f in range(F0, F1 + 1, ST):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get(); C = cam.matrix_world.translation.copy()
    for r in RIGS:
        for s in "LR":
            arm = []
            for bn in ("upperarm02", "lowerarm01", "lowerarm02"):
                h, t = W(r, bn + "." + s), W(r, bn + "." + s, True); arm += [h.lerp(t, k / 3) for k in range(4)]
            hand = [W(r, "wrist." + s, True)] + [W(r, "finger%d-3.%s" % (k, s), True) for k in (1, 3, 5)]
            def vis(p):
                if not infr(p): return False
                d = p - C; L = d.length; ok, loc, n, i, ob, M = sc.ray_cast(dg, C, d.normalized(), distance=L + 0.02)
                return ok and who(ob) == r.name and (loc - C).length > L - 0.09
            vh = [p for p in hand if vis(p)]; va = [p for p in arm if vis(p)]
            over = 0
            for p in vh + va:
                d = (p - C).normalized(); ok, loc, n, i, ob, M = sc.ray_cast(dg, p + d * 0.09, d, distance=3.0)
                if ok and who(ob) not in (None, r.name): over += 1
            if over >= 2: flag(f, "ARMOVER", "%s arm.%s in front of the other person (%d pts)" % (r.name[:3], s, over))
            if vh and not va and all(infr(p) for p in arm): flag(f, "DETACHED", "%s hand.%s visible, arm hidden" % (r.name[:3], s))
    best = (9, "")
    for d in DIRS:
        ok, loc, n, i, ob, M = sc.ray_cast(dg, C, d, distance=0.2)
        if ok:
            dist = (loc - C).length; w = who(ob); lim = 0.12 if w else (0.10)
            if dist < lim and dist < best[0]: best = (dist, ob.name)
    if best[0] < 9: flag(f, "BRUSH", "camera %.3f m from %s" % best)
    if f % 150 == 1: print("RULES", f, sum(len(v) for v in res.values()))
json.dump(res, open(OUT, "w"), indent=0); print("RULES_DONE", len(res))
