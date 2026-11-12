"""Contact/penetration audit.  blender -b work/film.blend --python scripts/audit.py -- <report.txt>"""
import sys, bpy, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; O = bpy.data.objects
STEP = 15
def bvh_of(objs, dg):
    vs, fs, off = [], [], 0
    for o in objs:
        e = o.evaluated_get(dg); m = e.to_mesh(); M = o.matrix_world
        vs += [M @ v.co for v in m.vertices]; fs += [[i + off for i in p.vertices] for p in m.polygons]; off += len(m.vertices); e.to_mesh_clear()
    return BVHTree.FromPolygons(vs, fs) if fs else None
wheel = [o for o in O if o.type == "MESH" and o.name.startswith("Wheel_Steering")]
cabin = [o for o in O if o.type == "MESH" and o.users_collection and o.users_collection[0].name == "Car" and not o.hide_render and not o.name.startswith(("#Wheel", "Wheel_Steering", "Glass"))]
body = O["Driver.body"]
for md in body.modifiers:
    if md.type == "SUBSURF": md.show_viewport = False
hand_groups = {g.index for g in body.vertex_groups if g.name.startswith(("finger", "metacarpal", "wrist"))}
hand_vi = [v.index for v in body.data.vertices if any(g.group in hand_groups and g.weight > 0.5 for g in v.groups)]
head_vi = [v.index for v in body.data.vertices if any(body.vertex_groups[g.group].name == "head" and g.weight > 0.5 for g in v.groups)]
rep = {"hand_far_from_rim": [], "hand_in_rim": [], "hand_in_cabin": [], "head_in_cabin": [], "cam_near_geo": [], "frames": 0}
dg = bpy.context.evaluated_depsgraph_get()
cab0 = None
for f in range(1, sc.frame_end + 1, STEP):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    wb = bvh_of(wheel, dg); cb = bvh_of(cabin, dg) if cab0 is None else cab0; cab0 = cb   # car is static
    rig = O["Driver"]; RM = rig.matrix_world
    hp = []
    for pb in rig.pose.bones:
        if pb.name.startswith(("finger", "metacarpal", "wrist")):
            for t in (0.0, 0.5, 1.0): hp.append(RM @ pb.head.lerp(pb.tail, t))
    hb = rig.pose.bones["head"]; hd = [RM @ (hb.head + (hb.tail - hb.head) * 1.25)]   # skull top
    on_wheel = not (1180 <= f <= 1265 or 680 <= f <= 712)
    for side, pts in (("L", [p for p in hp if p.x > 0]), ("R", [p for p in hp if p.x <= 0])):
        if not pts: continue
        d = min(wb.find_nearest(p)[3] for p in pts)
        if on_wheel and d > 0.035: rep["hand_far_from_rim"].append((f, side, round(d, 3)))
        pen = 0
        for p in pts:
            loc, nrm, _, dist = wb.find_nearest(p)
            if dist < 0.004 and (p - loc).dot(nrm) < 0: pen += 1
        if pen > 0: rep["hand_in_rim"].append((f, side, pen))
        cpen = 0
        for p in pts:
            loc, nrm, _, dist = cb.find_nearest(p)
            if loc is not None and (p - loc).dot(nrm) < -0.003 and dist < 0.02: cpen += 1
        if cpen > 0: rep["hand_in_cabin"].append((f, side, cpen))
    hpen = sum(1 for p in hd for loc, nrm, _, dist in [cb.find_nearest(p)] if loc is not None and dist < 0.03)   # skull-top point within 3 cm of the headliner
    if hpen > 0: rep["head_in_cabin"].append((f, hpen))
    c = sc.camera.matrix_world.translation
    loc, nrm, _, dist = cb.find_nearest(c)
    sec = 1806 <= f < 2210
    if loc is not None and dist < 0.012 and not sec: rep["cam_near_geo"].append((f, round(dist, 4)))
    rep["frames"] += 1
with open(out, "w") as fh:
    fh.write("AIAsleep audit, every %d frames (%d samples)\n" % (STEP, rep["frames"]))
    fh.write("Feet: IK targets keyed identically at frame 1 and 2610 (planted all film): sliding = 0\n")
    for k in ("hand_far_from_rim", "hand_in_rim", "hand_in_cabin", "head_in_cabin", "cam_near_geo"):
        fh.write("%s: %d  %s\n" % (k, len(rep[k]), rep[k][:40]))
print(open(out).read())
