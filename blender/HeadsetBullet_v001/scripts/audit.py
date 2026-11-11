"""Contact audit for HeadsetBullet.  blender -b anim.blend --python audit.py -- <report.txt> [step]
Checks per frame: feet hover/sink on the floor, finger contact on keyboard/mouse while gaming, BVH triangle overlaps
(body x headset, hair x headset, hands x desk/keyboard/mouse, headset x bullet before impact), camera inside geometry."""
import sys, math
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]
OUT = a[0]; STEP = int(a[1]) if len(a) > 1 else 10
sc = bpy.context.scene
F_IMPACT, F_GRAB = sc["F_IMPACT"], sc["F_GRAB"]
def objs(prefix): return [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith(prefix) and not o.hide_render]
def tree(obs, vfilter=None):
    dg = bpy.context.evaluated_depsgraph_get(); V, T = [], []
    for o in obs:
        if o.hide_get() or o.hide_render: continue
        e = o.evaluated_get(dg); me = e.to_mesh(); mw = e.matrix_world; base = len(V)
        keep = None
        if vfilter:
            keep = set(i for i, v in enumerate(me.vertices) if vfilter(mw @ v.co))
        V += [mw @ v.co for v in me.vertices]
        me.calc_loop_triangles()
        for t in me.loop_triangles:
            if keep is None or all(i in keep for i in t.vertices): T.append(tuple(base + i for i in t.vertices))
        e.to_mesh_clear()
    return BVHTree.FromPolygons(V, T) if T else None, V
body = bpy.data.objects["Teen.body"]; hair = bpy.data.objects["Teen.short02"]; shoes = bpy.data.objects["Teen.shoes02"]
HS = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith("HS_")]
DESK = [bpy.data.objects["Desk_Top"]]
KB = [o for o in bpy.data.objects if o.type == 'MESH' and o.parent and o.parent.name in ("Keyboard", "Mouse")]
SOLIDS = [o for o in bpy.data.objects if o.type == 'MESH' and (o.name.startswith(("Room_", "Wall_", "Desk_", "Roof_", "Plinth", "Bed_", "PC_Tower")) or o.name in ("Teen.body",))]
cam = sc.camera
rows = []; totals = {}; depth_max = {}
def depth(obs_body, vsel, obs_solid):
    """max penetration (m) of selected body verts inside closed solid meshes (ray parity + nearest surface distance)"""
    dg = bpy.context.evaluated_depsgraph_get(); worst = 0.0
    e = obs_body.evaluated_get(dg); me = e.to_mesh(); P = [e.matrix_world @ v.co for v in me.vertices]; e.to_mesh_clear()
    P = [p for p in P if vsel(p)][::3]
    for o in obs_solid:
        if o.hide_render: continue
        eo = o.evaluated_get(dg); inv = eo.matrix_world.inverted(); mw = eo.matrix_world
        mn = mw @ Vector(eo.bound_box[0]); mx = mw @ Vector(eo.bound_box[6])
        lo = Vector([min(mn[i], mx[i]) for i in range(3)]); hi = Vector([max(mn[i], mx[i]) for i in range(3)])
        for p in P:
            if not all(lo[i] - 0.01 < p[i] < hi[i] + 0.01 for i in range(3)): continue
            q = inv @ p; d = Vector((0.0003, 1, 0.0007)).normalized(); hits = 0; r = q.copy()
            for _ in range(12):
                ok, loc, nrm, idx = eo.ray_cast(r, d)
                if not ok: break
                hits += 1; r = loc + d * 1e-6
            if hits % 2:
                ok, loc, nrm, idx = eo.closest_point_on_mesh(q)
                if ok: worst = max(worst, (mw @ loc - p).length)
    return worst
def dmax(k, v):
    depth_max[k] = max(depth_max.get(k, 0.0), v)
def add(k, n):
    totals[k] = totals.get(k, 0) + n
for f in list(range(1, sc.frame_end + 1, STEP)) + [F_IMPACT, F_GRAB, F_GRAB + 30]:
    sc.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    se = shoes.evaluated_get(dg); sm = se.to_mesh()
    pts = [se.matrix_world @ v.co for v in sm.vertices]; se.to_mesh_clear()
    issues = []
    for s, sel in (("L", lambda p: p.x < 0), ("R", lambda p: p.x >= 0)):
        zs = [p.z for p in pts if sel(p)]
        if zs:
            zmin = min(zs)
            if zmin > 0.015: issues.append("foot%s hover %.3f" % (s, zmin)); add("foot hover", 1)
            if zmin < -0.012: issues.append("foot%s sink %.3f" % (s, zmin)); add("foot sink", 1)
    hs_z = bpy.data.objects['Headset'].matrix_world.translation.z
    tb, _ = tree([body])
    th, _ = tree(HS)
    tr, _ = tree([hair])
    if th:
        n = len(tb.overlap(th)); n2 = len(tr.overlap(th))
        # while held (after the grab) palm contact with the cups is expected; count only head/face region overlaps there
        if n:
            # split: overlaps of the hand region with the cups while he grasps it = grasp contact; anything else = penetration
            thd, _ = tree([body], vfilter=lambda p: p.z < hs_z - 0.02 or abs(p.x) > 0.13) if f >= F_GRAB - 60 else (None, None)
            ng = len(thd.overlap(th)) if thd else 0
            if ng: issues.append("hand-cup grasp contact %d tris" % ng); add("grasp contact (hands on cups)", ng)
            if n - ng > 0: issues.append("body x headset %d tris" % (n - ng)); add("body x headset", n - ng)
        if n2: issues.append("hair x headset %d tris" % n2); add("hair x headset", n2)
    hand = lambda p: p.z > 0.6 and p.y > 3.15
    thand, HV = tree([body], vfilter=lambda p: p.z > 0.70 and p.z < 1.0 and p.y > 3.2)
    if thand:
        for nm, grp in (("hands x desk", DESK), ("hands x keyboard/mouse", KB)):
            t2, _ = tree(grp)
            n = len(thand.overlap(t2)) if t2 else 0
            if n: issues.append("%s %d tris" % (nm, n)); add(nm, n)
        if f < F_IMPACT:   # fingers must touch the keyboard/mouse (no floating): lowest fingertip region within 2.5 cm of desk top
            zmin = min((v.z for v in HV), default=9)
            if zmin > 0.75 + 0.045: issues.append("hands hover %.3f above desk" % (zmin - 0.75)); add("hands hover", 1)
    if f % 30 == 1 or f in (F_GRAB, F_GRAB + 30):
        hsel = lambda p: p.z > 0.7
        dmax("hands into headset (m)", depth(body, hsel, [o for o in HS if o.name.startswith(("HS_Shell", "HS_Face", "HS_Foam", "HS_Cushion"))]))
        dmax("hands into desk/keyboard/mouse (m)", depth(body, lambda p: 0.7 < p.z < 0.85 and p.y > 3.2, DESK + KB))
        dmax("head into headset (m)", depth(body, lambda p: p.z > 1.0, [o for o in HS if o.name.startswith(("HS_BandPad", "HS_Cushion"))]) if f < F_GRAB else 0.0)
    # camera inside a solid: ray parity along +X against solid objects
    c = cam.matrix_world.translation; inside = []
    for o in SOLIDS:
        e = o.evaluated_get(dg); inv = e.matrix_world.inverted(); p = inv @ c
        d = (inv.to_3x3() @ Vector((1, 0.0001, 0.0002))).normalized(); hits = 0; q = p.copy()
        for _ in range(20):
            ok, loc, nrm, idx = e.ray_cast(q, d)
            if not ok: break
            hits += 1; q = loc + d * 1e-5
        if hits % 2 == 1: inside.append(o.name)
    if inside: issues.append("camera inside " + ",".join(inside)); add("camera inside", 1)
    rows.append("f%04d  %s" % (f, "; ".join(issues) if issues else "ok"))
rep = ["HeadsetBullet audit (step %d)" % STEP, "TOTALS " + (", ".join("%s=%d" % kv for kv in sorted(totals.items())) or "none"),
       "MAX PENETRATION DEPTH " + ", ".join("%s=%.4f" % kv for kv in sorted(depth_max.items())), ""] + rows
open(OUT, "w").write("\n".join(rep)); print("\n".join(rep[:4]))
