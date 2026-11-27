"""CaveRescue v012 film-specific checks (on top of the pipeline checks).
blender -b film.blend --python 04_checks.py -- <out.json>
 FRONTPOP  at every cutaway open/close frame: fraction of the frame whose nearest hit is front-half geometry (must be 0)
 TELEPORT  a character switching visibility while its body is inside the frame (frame before/after the switch)
 LENS      stretcher / ambulance / any body closer than 0.6 m to the lens and inside the view (stretcher+ambulance 1.2 m)
 SUBJECT   dive/underwater frames with no diver body or lit lamp inside the frame within 16 m"""
import bpy, sys, json, math
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; cam = sc.camera; O = bpy.data.objects
def fs(f): sc.frame_set(f)
def desc(o):
    r = [o]
    for c in o.children: r += desc(c)
    return r
FRONT = set(desc(O["FRONT_CTL"])) - set(desc(O["Ambulance"]))
res = {"FRONTPOP": [], "TELEPORT": [], "LENS": [], "SUBJECT": [], "JUMP": [], "INSIDE": []}
def rays(nx=18, ny=32):
    dg = bpy.context.evaluated_depsgraph_get(); M = cam.matrix_world
    fr = cam.data.view_frame(scene=sc); tl, bl = fr[3], fr[2]; tr, br = fr[0], fr[1]
    for i in range(nx):
        for j in range(ny):
            u, v = (i + 0.5) / nx, (j + 0.5) / ny
            p = (bl.lerp(br, u)).lerp(tl.lerp(tr, u), v)
            d = (M.to_3x3() @ p).normalized()
            yield sc.ray_cast(dg, M.translation, d, distance=3000)
for f in (558, 559, 560, 561, 954, 955, 994, 995, 996, 2007, 2008, 2009, 2010, 2115, 2116, 2117, 2118):
    fs(f); n = 0; hit_front = 0
    for h in rays():
        n += 1
        if h[0] and h[4] in FRONT and not h[4].name.startswith(("Water",)): hit_front += 1; res.setdefault("FRONTOBJ", []).append((f, h[4].name))
    res["FRONTPOP"].append((f, round(hit_front / n, 3)))
TRANSP = ("Water", "PoolSurf", "FX_Silt", "FX_Bub", "FX_Rain", "FFM_Visor")
def visible_from_cam(p, owner):
    """occlusion-aware: the first opaque hit between the camera and p belongs to the owner rig (or nothing)"""
    dg = bpy.context.evaluated_depsgraph_get(); o = cam.matrix_world.translation; d = (p - o); L = d.length; d.normalize(); t = 0.0
    sec = bpy.data.materials["M_WaterVol"].node_tree.nodes["Section"].inputs["Fac"].default_value
    for _ in range(12):
        h = sc.ray_cast(dg, o + d * t, d, distance=max(0.0, L - t - 0.25))
        if not h[0]: return True
        ob = h[4]; t += (h[1] - (o + d * t)).length + 0.002
        if ob.name.startswith(TRANSP) and not (ob.name.startswith("Water") and sec > 0.5): continue
        top = ob
        while top.parent: top = top.parent
        return top == owner
    return True
def in_view(p, margin=0.0, owner=None):
    c = world_to_camera_view(sc, cam, p); iv = c.z > 0.05 and -margin <= c.x <= 1 + margin and -margin <= c.y <= 1 + margin
    if iv and owner is not None: iv = visible_from_cam(p, owner)
    return iv, c.z
rigs = [o for o in O if o.type == 'ARMATURE' and "home" in o.keys()]
def body_pts(r):
    return [r.matrix_world @ r.pose.bones[b].head for b in ("head", "spine03", "pelvis.L", "foot.L", "foot.R", "wrist.L", "wrist.R") if b in r.pose.bones]
for r in rigs:
    fc = None
    if r.animation_data and r.animation_data.action:
        for c in r.animation_data.action.layers[0].strips[0].channelbags[0].fcurves if hasattr(r.animation_data.action, "layers") else r.animation_data.action.fcurves:
            if c.data_path == "hide_render": fc = c
    if not fc: continue
    for kp in fc.keyframe_points:
        f = int(kp.co.x)
        if f <= 1 or f >= sc.frame_end: continue
        for g in (f - 1, f):
            fs(g)
            if r.hide_render: continue
            if any(in_view(p, owner=r)[0] for p in body_pts(r)): res["TELEPORT"].append((r.name, f, g))
CLOSE = {"Sked": 1.2, "Ambulance": 1.2}
targets = [(O["Sked"], 1.2), (O["Amb_Body"], 1.2)] + [(r, 0.6) for r in rigs]
dg = None
for f in range(1, sc.frame_end + 1, 2):
    fs(f); cp = cam.matrix_world.translation
    for o, lim in targets:
        if o.hide_render: continue
        pts = body_pts(o) if o.type == 'ARMATURE' else [o.matrix_world @ Vector(c) for c in o.bound_box] + [o.matrix_world.translation]
        if o.type == 'ARMATURE':
            pts += [o.matrix_world @ pb.head for pb in o.pose.bones if pb.name.startswith(("lowerarm01", "lowerleg01", "upperarm01", "neck01"))]
        if o.type == 'MESH' and o.name == "Sked":
            me = o.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh(); pts = [o.matrix_world @ v.co for v in list(me.vertices)[::7]]
        for p in pts:
            d = (p - cp).length
            if d < lim and in_view(p, 0.15)[0]:
                res["LENS"].append((f, o.name, round(d, 2))); break
DIVE = [(1060, 1370), (1874, 2010)]
subj_rigs = [O[n] for n in ("Diver1", "Diver2", "Diver3", "Boy1")]
lamps = [O[n + "_TorchLens"] for n in ("Diver1", "Diver2", "Diver3")]
for a, b in DIVE:
    for f in range(a, b + 1, 2):
        fs(f); cp = cam.matrix_world.translation; ok = False
        for r in subj_rigs:
            if r.hide_render: continue
            for p in body_pts(r):
                iv, z = in_view(p)
                if iv and (p - cp).length < 16: ok = True; break
            if ok: break
        if not ok:
            for l in lamps:
                if not l.hide_render and in_view(l.matrix_world.translation)[0]: ok = True; break
        if not ok: res["SUBJECT"].append(f)
prev = {}
for f in range(1, sc.frame_end + 1):
    fs(f)
    for r in rigs:
        hp = r.matrix_world @ r.pose.bones["head"].head
        if not r.hide_render and r.name in prev and prev[r.name] is not None and (hp - prev[r.name]).length > 0.35:
            if in_view(hp, 0.1, r)[0] or in_view(prev[r.name], 0.1, r)[0]: res["JUMP"].append((r.name, f, round((hp - prev[r.name]).length, 2), in_view(hp, 0.1, r)[0], in_view(prev[r.name], 0.1, r)[0]))
        prev[r.name] = None if r.hide_render else hp
DIRS = [Vector(d) for d in ((0, 0, 1), (0, 0, -1), (1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0))]
for f in range(1, sc.frame_end + 1, 2):
    fs(f); dg = bpy.context.evaluated_depsgraph_get(); o = cam.matrix_world.translation; back = 0
    for d in DIRS:
        h = sc.ray_cast(dg, o, d, distance=400)
        if h[0] and h[4].name.startswith("ROCK") and h[2].dot(d) > 0: back += 1
    if back >= 3: res["INSIDE"].append(f)
json.dump(res, open(OUT, "w"), indent=1)
for k, v in res.items(): print("CHK", k, len(v), v[:40])
