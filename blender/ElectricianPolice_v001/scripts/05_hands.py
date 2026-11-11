"""Hands audit + fix (client rule, Nov 11 23:00 UTC).
BVH overlap every 2 frames between:
- each hand and the other hand
- each hand and its own torso, head and torso clothing
- each hand and any other character within 1.5 m

Each hit is fixed by re-keying the IK hand target 3.5 cm away from the nearest surface it hit.
The audit then repeats, up to 4 passes.
blender -b film.blend --python 05_hands.py -- <out.blend> <report.txt>"""
import bpy, sys, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]; OUT, REP = a[0], a[1]
sc = bpy.context.scene
ARMS = [o for o in bpy.data.objects if o.type == "ARMATURE" and "IK_hand.L" in o.pose.bones]
def meshes(arm): return [o for o in bpy.data.objects if o.parent == arm and o.type == "MESH"]
def body(arm): return next(o for o in meshes(arm) if ".body" in o.name)
def clothes(arm): return [o for o in meshes(arm) if any(k in o.name for k in ("suit", ".vest"))]
# subdivision off while auditing so evaluated vertex order == base mesh order
for o in bpy.data.objects:
    for md in getattr(o, "modifiers", []):
        if md.type in ("SUBSURF", "MASK"): md.show_viewport = False
def groups(o, prefixes, thr=0.5):
    idx = {g.index: g.name for g in o.vertex_groups}; out = set()
    for v in o.data.vertices:
        w = sum(g.weight for g in v.groups if idx.get(g.group, "").startswith(prefixes))
        if w > thr: out.add(v.index)
    return out
INFO = {}
for arm in ARMS:
    b = body(arm)
    INFO[arm.name] = dict(
        hand={s: groups(b, ("finger", "metacarpal")) & {v.index for v in b.data.vertices if (v.co.x > 0) == (s == "L")} for s in "LR"},
        torso=groups(b, ("spine", "breast", "clavicle", "pelvis", "root")),
        head=groups(b, ("head", "jaw", "neck03")),
        cloth={c.name: groups(c, ("spine", "breast", "clavicle", "pelvis", "root")) for c in clothes(arm)})
def faces_in(me, vset):
    return [tuple(p.vertices) for p in me.polygons if all(i in vset for i in p.vertices)]
def tree(o, dg, vset=None):
    me = o.evaluated_get(dg).to_mesh(); M = o.matrix_world
    vs = [M @ v.co for v in me.vertices]
    fs = faces_in(me, vset) if vset is not None else [tuple(p.vertices) for p in me.polygons]
    o.evaluated_get(dg).to_mesh_clear()
    return (BVHTree.FromPolygons(vs, fs) if fs else None), vs
def vis(o): return not o.hide_render
def audit(fix):
    hits = []
    for f in range(sc.frame_start, sc.frame_end + 1, 2):
        sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
        cam = sc.camera; cp = cam.matrix_world.translation; fwd = cam.matrix_world.to_3x3() @ Vector((0, 0, -1))
        def on_camera(arm):   # only characters the camera can see (in front, within 14 m)
            r = arm.matrix_world @ arm.pose.bones["root"].head + Vector((0, 0, 0.3))
            d = r - cp
            return d.length < 14 and d.normalized().dot(fwd) > 0.35
        live = [arm for arm in ARMS if vis(body(arm)) and on_camera(arm)]
        T = {}
        for arm in live:
            b = body(arm); I = INFO[arm.name]
            full, vs = tree(b, dg)
            T[arm.name] = dict(full=full, vs=vs, hand={s: tree(b, dg, I["hand"][s])[0] for s in "LR"},
                               torso=tree(b, dg, I["torso"])[0], head=tree(b, dg, I["head"])[0],
                               cloth=[tree(c, dg, I["cloth"][c.name])[0] for c in clothes(arm) if vis(c)])
        for arm in live:
            t = T[arm.name]; I = INFO[arm.name]
            for s in "LR":
                h = t["hand"][s]
                if h is None: continue
                ctr = sum((t["vs"][i] for i in I["hand"][s]), Vector()) / max(1, len(I["hand"][s]))
                targets = [("hand-hand", t["hand"]["R" if s == "L" else "L"]), ("hand-torso", t["torso"]), ("hand-head", t["head"])]
                targets += [("hand-clothes", c) for c in t["cloth"]]
                root = arm.matrix_world @ arm.pose.bones["root"].head
                for other in live:
                    if other is arm: continue
                    if (other.matrix_world @ other.pose.bones["root"].head - root).length < 1.5:
                        targets.append(("hand-char:" + other.name, T[other.name]["full"]))
                for kind, tg in targets:
                    if tg is None: continue
                    if h.overlap(tg):
                        hits.append((f, arm.name, s, kind))
                        if fix:
                            near = tg.find_nearest(ctr)
                            d = (ctr - near[0]) if near[0] is not None else Vector((0, 0, 0.0))
                            d = d.normalized() if d.length > 1e-4 else Vector((0, 0, 1))
                            pb = arm.pose.bones["IK_hand." + s]
                            delta = arm.data.bones["IK_hand." + s].matrix_local.to_3x3().inverted() @ (d * 0.035)
                            pb.location = pb.location + delta
                            pb.keyframe_insert("location", frame=f, group="IK_hand." + s)
                        break
    return hits
log = []
for p in range(2):
    hits = audit(fix=True)
    log.append("pass %d: %d hits" % (p + 1, len(hits)))
    print(log[-1], flush=True)
    if not hits: break
final = audit(fix=False)
from collections import Counter
c = Counter((h[1], h[2], h[3]) for h in final)
log.append("FINAL hand-audit hits (every 2 frames): %d" % len(final))
for k, v in c.most_common(): log.append("  %s %s %s: %d frames" % (k[0], k[1], k[2], v))
for h in final[:60]: log.append("  f%d %s %s %s" % h)
for o in bpy.data.objects:
    for md in getattr(o, "modifiers", []):
        if md.type in ("SUBSURF", "MASK"): md.show_viewport = True
open(REP, "w").write("\n".join(log) + "\n"); print("\n".join(log))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
