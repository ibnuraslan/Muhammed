"""Hand-to-prop contact pass (v006, matches pipeline/qa_check.py HOVER): every STEP frames, for every visible hand whose
wrist is within 12 cm of a solid prop, either the nearest fingertip is snapped onto the surface (it rests on it) or, when
the hand is clearly not meant to touch it (fingertips > 7 cm away), the hand is moved clear (wrist 13 cm from it).
Non-solid props (flame, smoke, light, spill) and props carried by that same rig are skipped.
blender -b film.blend --python 04b_contact_snap.py -- <out.blend> [f0] [f1] [step]"""
import sys, bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
a = sys.argv[sys.argv.index("--") + 1:]
OUT = a[0]; F0 = int(a[1]) if len(a) > 1 else 1; F1 = int(a[2]) if len(a) > 2 else bpy.context.scene.frame_end
STEP = int(a[3]) if len(a) > 3 else 6
sc = bpy.context.scene; O = bpy.data.objects
RIGS = [o for o in O if o.type == 'ARMATURE' and "head" in o.pose.bones and "finger2-1.L" in o.pose.bones and "IK_hand.L" in o.pose.bones]
CHAR = {c.name for r in RIGS for c in r.children_recursive}
SOFT = ("flame", "smoke", "light", "spill", "wipe", "cloud", "puff", "glow", "fuse")
PROPS = [o for o in O if o.type == 'MESH' and o.name not in CHAR and len(o.data.polygons) < 200000
         and not any(k in o.name.lower() for k in ("ground", "floor", "terrain", "sky", "backdrop", "water", "ocean", "pile", "heap"))
         and not any(k in o.name.lower() for k in SOFT)]
def carried_by(o, r):
    for c in o.constraints:
        if c.type == 'CHILD_OF' and c.target == r and c.influence > 0.5: return True
    return False
def visible(p, m=0.05):
    c = world_to_camera_view(sc, sc.camera, p); return -m <= c.x <= 1 + m and -m <= c.y <= 1 + m and c.z > 0
def tips(r, s):
    return [r.matrix_world @ r.pose.bones["finger%d-3.%s" % (i, s)].tail for i in range(1, 6)]
cache = {}
def static(o):
    while o is not None:
        if o.animation_data or o.constraints: return False
        o = o.parent
    return True
STATIC = {o.name for o in PROPS if static(o)}
def bvh(o, dg, f):
    k = o.name if o.name in STATIC else (o.name, f)
    if k not in cache:
        if len(cache) > 4000:
            for kk in [kk for kk in cache if not isinstance(kk, str)]: del cache[kk]
        ev = o.evaluated_get(dg); me = ev.to_mesh(); mw = o.matrix_world
        cache[k] = BVHTree.FromPolygons([mw @ v.co for v in me.vertices], [tuple(p.vertices) for p in me.polygons]) if me.polygons else None
        ev.to_mesh_clear()
    return cache[k]
n_snap = n_clear = 0
for it in range(1):
    for f in range(F0, F1 + 1, STEP):
        sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
        for r in RIGS:
            if r.hide_render: continue
            for s in "LR":
                pb = r.pose.bones["IK_hand." + s]
                w = r.matrix_world @ r.pose.bones["wrist." + s].head
                if not visible(w): continue
                off = None
                for o in PROPS:
                    if (o.matrix_world.translation - w).length > 3.0 or carried_by(o, r): continue
                    t = bvh(o, dg, f)
                    if t is None: continue
                    nw = t.find_nearest(w, 0.12)
                    if nw[0] is None: continue
                    best = None
                    for tp in tips(r, s):
                        loc, nrm, _, d = t.find_nearest(tp, 0.3)
                        if loc is not None and (best is None or d < best[0]): best = (d, loc, tp, nrm)
                    if best is None or best[0] <= 0.010: continue
                    if best[0] < 0.07:
                        d, loc, tp, nrm = best
                        off = (loc - tp) * (1 - 0.005 / d); n_snap += 1
                    else:
                        v = w - nw[0]
                        off = (v.normalized() if v.length > 1e-4 else nw[1]) * (0.135 - v.length); n_clear += 1
                    break
                if off is None: continue
                M = r.matrix_world @ pb.matrix; M.translation += off
                pb.matrix = r.matrix_world.inverted() @ M
                bpy.context.view_layer.update()
                pb.keyframe_insert("location", frame=f, group="IK_hand." + s)
                pb.keyframe_insert("rotation_quaternion", frame=f, group="IK_hand." + s)
print("SNAP", n_snap, "CLEAR", n_clear)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SNAP_SAVED", OUT)
