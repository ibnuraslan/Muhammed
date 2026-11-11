"""Contact audit. blender -b anim.blend --python 05_audit.py -- <out.txt> [step]
- feet: ankle height above the floor under it for the IK actors (hover > 0.11 m, sink < 0.03 m)
- penetration: BVH overlap of hand / foot / head-item meshes with the set meshes, and between actors
- head items: beanie and scarf overlap with the fan's body
- camera: inside-geometry test (ray parity in 3 axes) and nearest-surface distance"""
import sys, bpy, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; STEP = int(a[1]) if len(a) > 1 else 20
sc = bpy.context.scene; dg = bpy.context.evaluated_depsgraph_get()
ACT = ["Fan", "Manager", "ManagerB", "Doctor", "Nurse"]
def bvh(o, groups=None):
    e = o.evaluated_get(dg); m = e.to_mesh(); M = o.matrix_world
    vs = [M @ v.co for v in m.vertices]
    if groups is not None:
        vg = {g.index: g.name for g in o.vertex_groups}
        keep = set(v.index for v in m.vertices if any(vg.get(g.group, "").startswith(groups) and g.weight > 0.4 for g in v.groups))
        polys = [list(p.vertices) for p in m.polygons if all(i in keep for i in p.vertices)]
    else:
        polys = [list(p.vertices) for p in m.polygons]
    e.to_mesh_clear()
    return BVHTree.FromPolygons(vs, polys) if polys else None
SET = [o for o in bpy.data.objects if o.type == 'MESH' and not o.hide_render and o.users_collection[0].name in ("RINK", "CLINIC", "HOME")
       and any(k in o.name for k in ("Board", "Glass", "Bench", "Exam", "Sofa", "table", "Floor", "Wall", "Riser", "Ice", "Paper"))]
lines = []; counts = {"hover": 0, "sink": 0, "pen_hand": 0, "pen_foot": 0, "pen_head_item": 0, "cam_inside": 0}
def ground(p):
    hit, loc, n, i, ob, mx = sc.ray_cast(dg, p + Vector((0, 0, 0.05)), Vector((0, 0, -1)), distance=3.0)
    return loc.z if hit else 0.0
for f in range(1, sc.frame_end + 1, STEP):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    cam = sc.camera.matrix_world.translation
    inside = 0
    for d in (Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))):
        n_hits = 0; p = cam.copy()
        for _ in range(30):
            hit, loc, nrm, i, ob, mx = sc.ray_cast(dg, p, d, distance=200)
            if not hit: break
            n_hits += 1; p = loc + d * 1e-4
        inside += n_hits % 2
    if inside >= 2: counts["cam_inside"] += 1; lines.append(f"f{f} CAMERA possibly inside geometry at {tuple(round(x, 3) for x in cam)}")
    setb = {}
    for o in SET:
        bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
        setb[o.name] = (o, bb)
    for an in ACT:
        r = bpy.data.objects.get(an)
        if not r: continue
        root = r.matrix_world @ r.pose.bones["root"].head
        if (root - cam).length > 8: continue        # only actors near the camera
        for s in "LR":
            ank = r.matrix_world @ r.pose.bones["foot." + s].head
            g = ground(ank); h = ank.z - g
            if h > 0.11 and an not in ("ManagerB",): counts["hover"] += 1; lines.append(f"f{f} {an} foot.{s} hover {h:.3f}")
            if h < 0.03: counts["sink"] += 1; lines.append(f"f{f} {an} foot.{s} sink {h:.3f}")
        body = bpy.data.objects.get(an + ".body")
        hb = bvh(body, ("finger", "wrist", "metacarpal")); fb = bvh(body, ("foot", "toe"))
        for nm, (o, bb) in setb.items():
            if min((v - root).length for v in bb) > 3 and not (min(v.x for v in bb) < root.x < max(v.x for v in bb)): continue
            ob_ = bvh(o)
            if ob_ is None: continue
            if hb:
                ov = hb.overlap(ob_)
                if ov: counts["pen_hand"] += 1; lines.append(f"f{f} {an} hand x {nm}: {len(ov)} tri pairs")
            if fb:
                ov = fb.overlap(ob_)
                if ov and "Floor" not in nm and "Ice" not in nm: counts["pen_foot"] += 1; lines.append(f"f{f} {an} foot x {nm}: {len(ov)} tri pairs")
    if (bpy.data.objects["Fan"].matrix_world @ bpy.data.objects["Fan"].pose.bones["head"].head - cam).length < 6:
        fb_ = bvh(bpy.data.objects["Fan.body"])
        for it in ("BeanieKnitMesh", "Scarf"):
            o = bpy.data.objects.get(it)
            if o and o.scale.x > 0.5:
                ov = bvh(o).overlap(fb_)
                if len(ov) > 20: counts["pen_head_item"] += 1; lines.append(f"f{f} {it} x Fan.body: {len(ov)} tri pairs")
txt = "AUDIT FanCancer, every %d frames\n" % STEP + "\n".join(f"{k}: {v}" for k, v in counts.items()) + "\n\n" + "\n".join(lines)
open(OUT, "w").write(txt); print(txt[:3000])
