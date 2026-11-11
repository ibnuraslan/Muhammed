"""SwedishCoffee contact / penetration audit.
blender -b film.blend --python audit.py -- <report.txt> [step]
Per sampled frame, for every rendered character in the visible set:
  FOOT_HOVER / FOOT_SINK  shoe sole vs the surface below it (ray cast against set geometry, not people)
  HAND_PEN / FOOT_PEN     hand- and foot-region skin vertices inside set props/furniture (BVH nearest + normal test)
  HEADITEM_GAP            hat / wig / mask further than 6 cm from the head bone
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
        walking = False
        for s in "LR":
            ft = arm.matrix_world @ arm.pose.bones["foot." + s].head
            g = ground_below(ft)
            if g is None: continue
            gap = ft.z - 0.072 - g
            if gap > 0.04 and ft.z - g < 0.25: flag("FOOT_HOVER", f, "%s %s %.1f cm" % (arm.name, s, gap * 100))
            if gap < -0.03: flag("FOOT_SINK", f, "%s %s %.1f cm" % (arm.name, s, -gap * 100))
        key = body.name
        if key not in cache: cache[key] = (region_verts(body, HANDVG), region_verts(body, FOOTVG))
        hv, fv = cache[key]
        ev = body.evaluated_get(dg); me = ev.to_mesh(); mw = body.matrix_world
        nh = sum(1 for i in hv if inside(mw @ me.vertices[i].co))
        nf = sum(1 for i in fv[::2] if inside(mw @ me.vertices[i].co))
        ev.to_mesh_clear()
        if nh > 3: flag("HAND_PEN", f, "%s %d verts" % (arm.name, nh))
        if nf > 3: flag("FOOT_PEN", f, "%s %d verts" % (arm.name, nf))
    for o in bpy.data.collections[cn].all_objects:
        for c in o.constraints:
            if c.type == 'CHILD_OF' and c.subtarget == "head" and not o.hide_render:
                hp = c.target.matrix_world @ c.target.pose.bones["head"].tail
                dmin = min(((o.matrix_world @ Vector(b)) - hp).length for b in o.bound_box)
                if dmin > 0.12: flag("HEADITEM_GAP", f, "%s %.1f cm" % (o.name, dmin * 100))
lines = ["SwedishCoffee audit, step %d frames" % STEP]
for k in ("FOOT_HOVER", "FOOT_SINK", "HAND_PEN", "FOOT_PEN", "HEADITEM_GAP", "CAMERA_INSIDE"):
    v = issues.get(k, []); lines.append("%-14s %4d" % (k, len(v)))
    for f, m in v[:40]: lines.append("    f%04d %s" % (f, m))
open(OUT, "w").write("\n".join(lines) + "\n"); print("\n".join(lines))
