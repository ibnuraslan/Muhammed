"""Hand audit (client rule, Nov 11 23:00): every 2 frames, for each main actor within 4 m of the camera:
hand L vs hand R, each hand vs own torso/legs/head (arm vertices excluded), vs own clothes, vs other actors.
blender -b anim.blend --python 05b_hand_audit.py -- <out.txt> [step]"""
import sys, bpy
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; STEP = int(a[1]) if len(a) > 1 else 2
sc = bpy.context.scene
for _o in bpy.data.objects:
    for _m in getattr(_o, "modifiers", []):
        if _m.type == "SUBSURF": _m.show_viewport = False
ACT = ["Fan", "Manager", "ManagerB", "Doctor", "Nurse"]
ARM = ("upperarm", "lowerarm", "wrist", "finger", "metacarpal", "clavicle", "shoulder")
HAND = ("wrist", "finger", "metacarpal")
def mesh_parts(o, dg):
    e = o.evaluated_get(dg); m = e.to_mesh(); M = o.matrix_world
    vs = [M @ v.co for v in m.vertices]
    bones = set(o.parent.data.bones.keys()) if o.parent and o.parent.type == 'ARMATURE' else set()
    vg = {g.index: g.name for g in o.vertex_groups if g.name in bones}
    side = {}
    for v in o.data.vertices:
        best = max((g for g in v.groups if g.group in vg), key=lambda g: g.weight, default=None)
        side[v.index] = vg.get(best.group, "") if best else ""
    polys = [list(p.vertices) for p in m.polygons]
    e.to_mesh_clear()
    return vs, polys, side
def tree(vs, polys, keep):
    ps = [p for p in polys if keep(p)]
    return BVHTree.FromPolygons(vs, ps) if ps else None
counts = {"hand_hand": 0, "hand_self": 0, "hand_clothes": 0, "hand_other": 0}; lines = []
frames = 0
for f in range(1, sc.frame_end + 1, STEP):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get(); cam = sc.camera.matrix_world.translation
    near = [n for n in ACT if bpy.data.objects.get(n) and ((bpy.data.objects[n].matrix_world @ bpy.data.objects[n].pose.bones["head"].head) - cam).length < 4.0]
    if not near: continue
    frames += 1
    bodies = {}
    for n in near:
        b = bpy.data.objects[n + ".body"]; vs, polys, side = mesh_parts(b, dg)
        isg = lambda p, pre, s=None: all(side[i].startswith(pre) and (s is None or side[i].endswith(s)) for i in p)
        hL = tree(vs, polys, lambda p: all(side[i].startswith(HAND) and side[i].endswith(".L") for i in p))
        hR = tree(vs, polys, lambda p: all(side[i].startswith(HAND) and side[i].endswith(".R") for i in p))
        core = tree(vs, polys, lambda p: not any(side[i].startswith(ARM) for i in p))
        full = BVHTree.FromPolygons(vs, polys)
        bodies[n] = (hL, hR, core, full)
        if hL and hR and hL.overlap(hR): counts["hand_hand"] += 1; lines.append(f"f{f} {n} hand L x hand R")
        for s, h in (("L", hL), ("R", hR)):
            if h and core:
                ov = h.overlap(core)
                if len(ov) > 2: counts["hand_self"] += 1; lines.append(f"f{f} {n} hand {s} x own body: {len(ov)}")
        for c in [c for c in bpy.data.objects[n].children if "suit" in c.name and c.type == 'MESH' and not c.hide_render]:
            cv, cp, cs = mesh_parts(c, dg)
            ct = tree(cv, cp, lambda p: not any(cs[i].startswith(ARM) for i in p))
            for s, h in (("L", hL), ("R", hR)):
                if h and ct:
                    ov = h.overlap(ct)
                    if len(ov) > 2: counts["hand_clothes"] += 1; lines.append(f"f{f} {n} hand {s} x own clothes: {len(ov)}")
    for n in near:
        for m in near:
            if m == n: continue
            for s, h in (("L", bodies[n][0]), ("R", bodies[n][1])):
                if h and h.overlap(bodies[m][3]): counts["hand_other"] += 1; lines.append(f"f{f} {n} hand {s} x {m}")
txt = f"HAND AUDIT FanCancer: every {STEP} frames, {frames} frames with a main actor within 4 m of camera\n" + \
      "\n".join(f"{k}: {v}" for k, v in counts.items()) + f"\nTOTAL {sum(counts.values())}\n\n" + "\n".join(lines)
open(OUT, "w").write(txt); print(txt[:4000])
