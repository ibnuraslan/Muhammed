"""Contact audit: hover/sink/slide of planted feet, hand grips, BVH penetration (hands, feet, head items vs scene props),
camera inside geometry.  blender -b anim.blend --python audit.py -- report.json [step]"""
import sys, json, math
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; STEP = int(a[1]) if len(a) > 1 else 4
sc = bpy.context.scene; H = bpy.data.objects["Hero"]; body = bpy.data.objects["Hero.body"]
shoes = next(o for o in H.children if "shoes" in o.name)
CUT = (460, 1205)          # inside the x-ray dome: camera is meant to be inside the (ghosted) body
def visible(o, f): return not o.hide_render
def bvh(o, dg, verts_filter=None):
    e = o.evaluated_get(dg); me = e.to_mesh(); M = o.matrix_world
    vs = [M @ v.co for v in me.vertices]; ps = [tuple(p.vertices) for p in me.polygons]
    e.to_mesh_clear(); return BVHTree.FromPolygons(vs, ps), vs
# body vertex groups for hands / feet
def group_idx(prefixes):
    gi = {g.index for g in body.vertex_groups if g.name.startswith(prefixes)}
    return [v.index for v in body.data.vertices if any(g.group in gi and g.weight > 0.5 for g in v.groups)]
HB_ = [b.name for b in H.data.bones if b.name.startswith(("finger", "wrist", "metacarpal"))]
def hand_pts(s):   # finger-surface proxy: points along every finger/wrist bone, offset 7 mm toward the palm side is ignored (bone axis = finger core)
    out = []
    for n in HB_:
        if not n.endswith("." + s): continue
        pb = H.pose.bones[n]; h_ = H.matrix_world @ pb.head; t_ = H.matrix_world @ pb.tail
        out += [h_.lerp(t_, u) for u in (0.0, 0.5, 1.0)]
    return out
PROPS = ["GrabRail", "GrabPostA", "GrabPostB", "PodiumBody", "PodiumTop", "PodiumBase", "HeroHat", "Stage"] + \
        [o.name for o in bpy.data.objects if o.type == "MESH" and o.parent and o.parent.name == "Car" and ("seat" in o.name or "body" in o.name or "door" in o.name)]
HEAD_ITEMS = [o.name for o in bpy.data.objects if o.name.startswith(("SpecRim", "SpecLens", "SpecArm", "SpecBridge", "Moustache"))]
rep = {"feet": [], "hands": [], "penetration": [], "head_items": [], "camera": [], "counts": {}}
prev_plant = {}
n_pen = 0
for f in range(sc.frame_start, sc.frame_end + 1, STEP):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    # ---- feet: lowest shoe point per side vs floor z = 0 (car floor and stage share it)
    e = shoes.evaluated_get(dg); me = e.to_mesh(); M = shoes.matrix_world
    for s, sx in (("L", 1), ("R", -1)):
        pts = [M @ v.co for v in me.vertices if (M @ v.co).x * sx > 0]
        zmin = min(p.z for p in pts)
        lifted = H.pose.bones["IK_foot." + s].location.length > 0 and False
        planted = not (s == "R" and 200 <= f <= 222)
        if planted and (zmin > 0.015 or zmin < -0.015): rep["feet"].append((f, s, "hover" if zmin > 0 else "sink", round(zmin, 3)))
        c = sum((p for p in pts), Vector()) / len(pts)
        if planted and s in prev_plant and f - prev_plant[s][0] == STEP and not (1150 <= f <= 1172):
            d = (c.to_2d() - prev_plant[s][1].to_2d()).length
            if d > 0.01: rep["feet"].append((f, s, "slide", round(d, 3)))
        prev_plant[s] = (f, c)
    e.to_mesh_clear()
    # ---- hero body BVH
    tb, vs = bvh(body, dg)
    # hands vs props (penetration depth by vertex-inside test via nearest + normal)
    for pn in PROPS:
        po = bpy.data.objects.get(pn)
        if not po or po.hide_render: continue
        tp, pvs = bvh(po, dg)
        for s in "LR":
            hv = hand_pts(s)
            inside = 0
            for v in hv[::3]:
                loc, nrm, idx, dist = tp.find_nearest(v)
                if loc is not None and dist < 0.03 and (v - loc).dot(nrm) < -0.004: inside += 1
            if inside: rep["penetration"].append((f, "hand." + s, pn, inside)); n_pen += 1
        # feet vs props (car body / seats only)
        if "seat" in pn or "door" in pn:
            sv = [M @ v.co for v in shoes.evaluated_get(dg).to_mesh().vertices]; shoes.evaluated_get(dg).to_mesh_clear()
            ins = sum(1 for v in sv[::5] if (lambda r: r[0] is not None and r[3] < 0.03 and (v - r[0]).dot(r[1]) < -0.002)(tp.find_nearest(v)))
            if ins: rep["penetration"].append((f, "feet", pn, ins)); n_pen += 1
    # ---- grip gaps: hand within reach of what it holds
    def gap(s, pn):
        po = bpy.data.objects[pn]; tp, _ = bvh(po, dg)
        return min(tp.find_nearest(v)[3] for v in hand_pts(s))
    if 200 <= f <= 1150: rep["hands"].append((f, "L-rail", round(gap("L", "GrabRail"), 3)))
    if 1216 <= f <= 1500: rep["hands"].append((f, "R-manuscript", round(gap("R", "Sheet49"), 3)))
    if 1195 <= f <= 1285 and not bpy.data.objects["PodiumTop"].hide_render: rep["hands"].append((f, "L-podium", round(gap("L", "PodiumTop"), 3)))
    if f < 168: rep["hands"].append((f, "R-hat", round(gap("R", "HeroHat"), 3)))
    # ---- head items: gap/penetration vs the face
    for hn in HEAD_ITEMS:
        ho = bpy.data.objects[hn]; th, hvs = bvh(ho, dg)
        ov = tb.overlap(th)
        if ov and not hn.startswith("Moustache"): rep["head_items"].append((f, hn, "overlap", len(ov))); n_pen += 1
        if hn.startswith("Moustache"):
            dmin = min(tb.find_nearest(v)[3] for v in hvs[::7])
            if dmin > 0.006: rep["head_items"].append((f, hn, "floating", round(dmin, 4)))
    # ---- camera inside geometry (outside the cutaway)
    cam = sc.camera.matrix_world.to_translation()
    if not (CUT[0] <= f <= CUT[1]):
        hits = 0
        for o in bpy.data.objects:
            if o.type != "MESH" or o.hide_render or o.name.startswith(("StudioDome", "GunSmoke")): continue
            bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
            if not all(min(p[i] for p in bb) - 0.02 <= cam[i] <= max(p[i] for p in bb) + 0.02 for i in range(3)): continue
            to, _ = bvh(o, dg); loc, nrm, idx, dist = to.find_nearest(cam)
            if loc is not None and (dist < 0.02 or (cam - loc).dot(nrm) < 0 and dist < 0.3): rep["camera"].append((f, o.name, round(dist, 3))); hits += 1
rep["counts"] = {k: len(v) for k, v in rep.items() if isinstance(v, list)}
rep["counts"]["penetration_events"] = n_pen
json.dump(rep, open(OUT, "w"), indent=0)
print("AUDIT", rep["counts"])
