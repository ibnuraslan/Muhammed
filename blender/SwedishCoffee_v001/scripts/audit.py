"""SwedishCoffee contact / penetration audit.
blender -b film.blend --python audit.py -- <report.txt> [step]
Per sampled frame, for every rendered character in the visible set:
  FOOT_HOVER / FOOT_SINK  shoe sole vs the surface below it (ray cast against set geometry, not people); hover = the LOWER foot is off the surface (swing feet are normal)
  HAND_PEN / FOOT_PEN     finger/wrist and toe/foot bone points (inside the skin by ~1 cm) more than 8 mm inside set props/furniture/floors (BVH nearest + normal); >2 points flags
  HEADITEM_GAP            hat / wig / mask whose nearest vertex is more than 3 cm from the head surface (floating)
  CAMERA_INSIDE           camera within 3 cm of / inside set geometry
"""
import sys, bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; STEP = int(a[1]) if len(a) > 1 else 30
sc = bpy.context.scene
issues = {}
def flag(k, f, m): issues.setdefault(k, []).append((f, m))
arms = [o for o in bpy.data.objects if o.type == 'ARMATURE' and o.users_collection[0].name.startswith("S")]
def setcoll(o):
    c = o.users_collection[0]; return c.name
HANDVG = ("wrist", "finger", "metacarpal"); FOOTVG = ("foot", "toe")
def region_verts(body, keys):
    idx = {g.index for g in body.vertex_groups if any(g.name.startswith(k) for k in keys)}
    return [v.index for v in body.data.vertices if any(g.group in idx and g.weight > 0.5 for g in v.groups)][::3]
cache = {}
for f in range(sc.frame_start, sc.frame_end + 1, STEP):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    vis = [o for o in arms if not o.hide_render]
    if not vis: continue
    cn = setcoll(vis[0])
    scene_objs = [o for o in bpy.data.collections[cn].all_objects if o.type == 'MESH' and not o.hide_render and not o.constraints
                  and not (o.parent and o.parent.type == 'ARMATURE') and o.data.materials and not any(m and m.node_tree and "Volume" in [n.type for n in m.node_tree.nodes] for m in o.data.materials)
                  and o.modifiers.get("beans") is None and "steam" not in o.name.lower() and "blanket" not in o.name]
    trees = []
    for o in scene_objs:
        try: trees.append((o, BVHTree.FromObject(o, dg)))
        except Exception: pass
    def to_local(o, p): return o.matrix_world.inverted() @ p
    def ground_below(p):
        best = None
        for o, t in trees:
            lo = to_local(o, p + Vector((0, 0, 0.3))); d = (o.matrix_world.inverted().to_3x3() @ Vector((0, 0, -1))).normalized()
            hit, nrm, i, dist = t.ray_cast(lo, d, 3.0)
            if hit is not None:
                z = (o.matrix_world @ hit).z
                if best is None or z > best: best = z
        return best
    def inside(p, tol=0.004):
        for o, t in trees:
            lo = to_local(o, p); loc, nrm, i, dist = t.find_nearest(lo, 0.05)
            if loc is not None and (lo - loc).dot(nrm) < -tol: return o.name
        return None
    # camera
    cam = sc.camera; cp = cam.matrix_world.translation
    for o, t in trees:
        lo = to_local(o, cp); loc, nrm, i, dist = t.find_nearest(lo, 0.03)
        if loc is not None:
            flag("CAMERA_INSIDE", f, o.name); break
    for arm in vis:
        body = next((c for c in arm.children if c.name.endswith(".body")), None)
        if body is None: continue
        if body.hide_render: continue
        gaps = {}
        for s in "LR":
            ft = arm.matrix_world @ arm.pose.bones["foot." + s].head
            g = ground_below(ft)
            if g is not None: gaps[s] = (ft.z - 0.072 - g, ft.z - g)
        if gaps:
            lo_s = min(gaps, key=lambda k: gaps[k][0]); gap, h = gaps[lo_s]
            if gap > 0.04 and h < 0.25: flag("FOOT_HOVER", f, "%s lower foot %s %.1f cm (both feet off the surface)" % (arm.name, lo_s, gap * 100))
            for s_, (gp, hh) in gaps.items():
                if gp < -0.03: flag("FOOT_SINK", f, "%s %s %.1f cm" % (arm.name, s_, -gp * 100))
        P = arm.pose.bones; mwa = arm.matrix_world
        hpts = [mwa @ P[n].tail for n in P.keys() if n.startswith(("finger", "wrist"))] + [mwa @ P[n].head for n in P.keys() if n.startswith("finger")]
        fpts = [mwa @ P[n].tail for n in P.keys() if n.startswith(("toe", "foot."))]
        nh = sum(1 for p in hpts if inside(p, 0.008)); nf = sum(1 for p in fpts if inside(p, 0.008))
        if nh > 2: flag("HAND_PEN", f, "%s %d verts" % (arm.name, nh))
        if nf > 2: flag("FOOT_PEN", f, "%s %d verts" % (arm.name, nf))
    for o in bpy.data.collections[cn].all_objects:
        for c in o.constraints:
            if c.type == 'CHILD_OF' and c.subtarget == "head" and not o.hide_render:
                body = next((ch for ch in c.target.children if ch.name.endswith(".body")), None)
                if body is None: continue
                bt = BVHTree.FromObject(body, dg); inv = body.matrix_world.inverted()
                ev = o.evaluated_get(dg); me = ev.to_mesh()
                ds = []
                for v in list(me.vertices)[::max(1, len(me.vertices) // 300)]:
                    loc, nrm, i, d = bt.find_nearest(inv @ (o.matrix_world @ v.co))
                    if loc is not None: ds.append(d)
                ev.to_mesh_clear()
                if ds and min(ds) > 0.03: flag("HEADITEM_GAP", f, "%s nearest %.1f cm from the head" % (o.name, min(ds) * 100))
lines = ["SwedishCoffee audit, step %d frames" % STEP]
for k in ("FOOT_HOVER", "FOOT_SINK", "HAND_PEN", "FOOT_PEN", "HEADITEM_GAP", "CAMERA_INSIDE"):
    v = issues.get(k, []); lines.append("%-14s %4d" % (k, len(v)))
    for f, m in v[:40]: lines.append("    f%04d %s" % (f, m))
open(OUT, "w").write("\n".join(lines) + "\n"); print("\n".join(lines))
