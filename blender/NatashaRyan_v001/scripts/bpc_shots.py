"""body_prop_cross per shot (same edge-vs-surface ray test as pipeline/body_prop_cross.py), restricted to each shot's set props
and the characters actually rendered at that frame, so hidden rigs and other sets cannot report false crossings.
blender -b film.blend --python bpc_shots.py -- out.json STEP shots.json"""
import bpy, sys, json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
a = sys.argv[sys.argv.index("--") + 1:]; OUT, STEP, SHOTS = a[0], int(a[1]), json.load(open(a[2]))
sc = bpy.context.scene
for o in bpy.data.objects:
    for m in getattr(o, "modifiers", []):
        if m.type in ("SUBSURF", "MULTIRES", "MASK"): m.show_viewport = False
PREF = {"port": ("Port_Stool",), "school": ("Mom_Car", "Delivery_Van", "Nat_Backpack", "Mem_", "School_Fence", "School_Kerb"),
        "home": ("Home_Kerb", "Police_", "Home_LampPost"), "field": (), "kitchen": ("Kit_",), "station": ("Stn_",),
        "court": ("Crt_Bench", "Crt_Lectern", "Crt_Rail", "Crt_Table", "Crt_CounselChair", "Crt_JudgeChair", "Crt_Dais"),
        "bedroom": ("Ward_", "Bed_Bed", "Bed_Nightstand")}
RIGS = [o for o in bpy.data.objects if o.type == 'ARMATURE' and "upperarm01.L" in o.pose.bones]
LAB = {}
for r in RIGS:
    bones = {b.name for b in r.data.bones}
    for c in r.children_recursive:
        if c.type != 'MESH': continue
        gi = {g.index: g.name for g in c.vertex_groups}
        lab = []
        for v in c.data.vertices:
            gs = [g for g in v.groups if gi.get(g.group) in bones]
            lab.append(gi[max(gs, key=lambda g: g.weight).group] if gs else c.name)
        LAB[c.name] = (r, c, lab)
res = {}; checked = []
for s in SHOTS:
    frames = sorted(set(list(range(s["f0"], s["f1"] + 1, STEP)) + [s["f0"], (s["f0"] + s["f1"]) // 2, s["f1"]]))
    props = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith(PREF[s["set"]]) and not any(k in o.name for k in ("Floor", "Ground", "Ceiling"))] if PREF[s["set"]] else []
    for f in frames:
        sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get(); cam = sc.camera
        trees = []
        for o in props:
            if o.hide_render: continue
            e = o.evaluated_get(dg); me = e.to_mesh(); mw = e.matrix_world
            vs = [mw @ v.co for v in me.vertices]; ps = [tuple(p.vertices) for p in me.polygons]; e.to_mesh_clear()
            if ps:
                lo = Vector([min(p[k] for p in vs) for k in range(3)]); hi = Vector([max(p[k] for p in vs) for k in range(3)])
                trees.append((o.name, BVHTree.FromPolygons(vs, ps), lo, hi))
        hits = {}
        for nm, (r, c, lab) in LAB.items():
            if c.hide_render or r.hide_render: continue
            e = c.evaluated_get(dg); me = e.to_mesh(); mw = e.matrix_world
            vs = [mw @ v.co for v in me.vertices]
            for bn, t, lo, hi in trees:
                near = {i for i, p in enumerate(vs) if all(lo[k] - 0.05 <= p[k] <= hi[k] + 0.05 for k in range(3))}
                if not near: continue
                for ed in me.edges:
                    i, j = ed.vertices
                    if i not in near and j not in near: continue
                    p, q = vs[i], vs[j]; d = q - p; L = d.length
                    if L < 1e-6: continue
                    loc = t.ray_cast(p, d / L, L)[0]
                    if loc is not None:
                        cv = world_to_camera_view(sc, cam, loc)
                        vis = 0 <= cv.x <= 1 and 0 <= cv.y <= 1 and cv.z > 0
                        k = "%s|%s|%s|%s" % (c.name, lab[i] if i < len(lab) else c.name, bn, "VIS" if vis else "off")
                        hits[k] = hits.get(k, 0) + 1
            e.to_mesh_clear()
        checked.append(f)
        if hits: res[f] = hits
        print("BPC", s["shot"], f, len(props), sum(1 for k in hits if k.endswith("VIS")), flush=True)
vis = sorted(int(f) for f, h in res.items() if any(k.endswith("VIS") for k in h))
json.dump({"step": STEP, "frames_checked": checked, "visible_frames": vis, "frames": res}, open(OUT, "w"), indent=0)
print("BPC_DONE visible crossing frames:", len(vis), vis)
