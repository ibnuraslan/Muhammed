"""B17 copy of bpc_fast (B01): adds (1) the cockpit shell window mask (windows there are shader cut-outs, so a leg
through the open captain windscreen is not a crossing) and (2) an occlusion test (a crossing hidden behind the 737 skin is 'off').
Body parts passing THROUGH thin props (bars, bin walls, flaps, doors, tables, chair frames).

blender -b Film.blend --python blender/pipeline/body_prop_cross.py -- out.json STEP Prop1,Prop2,... [Rig1,Rig2]

The client rejected legs passing through a bin's iron chute bar and a hand poking out through a bin wall.
Inside/outside tests miss thin walls, so this ray-casts every body/clothes/shoe EDGE near the props
against the props' surfaces. An edge that crosses a prop surface = a body part through the prop.
Reports per frame: {"part|prop|VIS/off": count}. Visible crossings must be 0 before delivery.
"""
import bpy, sys, json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view

a = sys.argv[sys.argv.index("--") + 1:]
OUT, STEP, PROPS = a[0], int(a[1]), [p for p in a[2].split(",") if p]
sc = bpy.context.scene
for o in bpy.data.objects:
    for m in getattr(o, "modifiers", []):
        if m.type in ("SUBSURF", "MULTIRES", "MASK"):   # keep evaluated vertex order = original (labels)
            m.show_viewport = False
RIGS = [bpy.data.objects[n] for n in a[3].split(",")] if len(a) > 3 else \
       [o for o in bpy.data.objects if o.type == 'ARMATURE' and "upperarm01.L" in o.pose.bones]
WEAR = []           # (mesh, per-vertex bone label)
BODYN = {c.name for r in RIGS for c in r.children_recursive}
for r in RIGS:
    for c in r.children_recursive:
        if c.type != 'MESH' or c.hide_render:
            continue
        bones = {b.name for b in r.data.bones}
        gi = {g.index: g.name for g in c.vertex_groups}
        lab = []
        for v in c.data.vertices:
            gs = [g for g in v.groups if gi.get(g.group) in bones]
            lab.append(gi[max(gs, key=lambda g: g.weight).group] if gs else c.name)
        WEAR.append((c, lab))
import os
def in_window(p):
    x, y, z = p
    ws = z > 1.03 and y > 1.93 and z < 1.80 and abs(x) > 0.03 and abs(abs(x) - 0.62) > 0.025
    sw = 1.10 < z < 1.64 and 0.93 < y < 1.90 and abs(y - 1.42) > 0.02
    return ws or sw
def visible(cam, p, prop_name, body_names):
    o = cam.matrix_world.translation; d = p - o; L = d.length
    hit, loc, n, i, ob, M = sc.ray_cast(bpy.context.evaluated_depsgraph_get(), o, d / L, distance=L - 0.03)
    return (not hit) or ob.name == prop_name or ob.name in body_names
res = {}
_fr = os.environ.get('BPC_FR')
_a, _b = (map(int, _fr.split(':')) if _fr else (sc.frame_start, sc.frame_end))
for f in range(_a, _b + 1, STEP):
    sc.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    mk = [m for m in sc.timeline_markers if m.frame <= f]
    if mk and max(mk, key=lambda m: m.frame).camera: sc.camera = max(mk, key=lambda m: m.frame).camera
    cam = sc.camera
    trees, lo, hi = [], Vector((1e9,) * 3), Vector((-1e9,) * 3)
    for n in PROPS:
        o = bpy.data.objects.get(n)
        if o is None or o.hide_render:
            continue
        if o.type != 'MESH' or not any(((o.matrix_world @ Vector(c)) - cam.matrix_world.translation).length < 8.0 for c in o.bound_box):
            continue
        e = o.evaluated_get(dg); me = e.to_mesh(); mw = e.matrix_world
        vs = [mw @ v.co for v in me.vertices]; ps = [tuple(p.vertices) for p in me.polygons]
        e.to_mesh_clear()
        if not ps:
            continue
        for p in vs:
            lo = Vector(map(min, lo, p)); hi = Vector(map(max, hi, p))
        trees.append((n, BVHTree.FromPolygons(vs, ps)))
    hits = {}
    for c, lab in WEAR:
        if c.parent and (c.parent.matrix_world @ c.parent.pose.bones[0].head - cam.matrix_world.translation).length > 8.0:
            continue
        e = c.evaluated_get(dg); me = e.to_mesh(); mw = e.matrix_world
        vs = [mw @ v.co for v in me.vertices]
        near = {i for i, p in enumerate(vs) if all(lo[k] - 0.05 <= p[k] <= hi[k] + 0.05 for k in range(3))}
        for ed in me.edges:
            i, j = ed.vertices
            if i not in near and j not in near:
                continue
            p, q = vs[i], vs[j]; d = q - p; L = d.length
            if L < 1e-6:
                continue
            for bn, t in trees:
                loc = t.ray_cast(p, d / L, L)[0]
                if loc is not None:
                    if bn == "COCKPIT_SHELL" and in_window(loc): continue
                    cv = world_to_camera_view(sc, cam, loc)
                    vis = 0 <= cv.x <= 1 and 0 <= cv.y <= 1 and cv.z > 0 and visible(cam, loc, bn, BODYN)
                    k = "%s|%s|%s" % (lab[i] if i < len(lab) else c.name, bn, "VIS" if vis else "off")
                    hits[k] = hits.get(k, 0) + 1
        e.to_mesh_clear()
    if hits:
        res[f] = hits
    print("BPC", f, len(hits), [k for k in hits if k.endswith("VIS")][:8], flush=True)
vis = sorted(int(f) for f, h in res.items() if any(k.endswith("VIS") for k in h))
json.dump({"visible_frames": vis, "frames": res}, open(OUT, "w"), indent=0)
print("BPC_DONE visible crossing frames:", len(vis), vis[:40])
