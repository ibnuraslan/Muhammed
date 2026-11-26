"""Camera clearance + face-occlusion audit (run on the animated or packed file).
blender -b film.blend --python camcheck.py -- out.json [step=2] [min_set_m=0.08] [min_body_m=0.18]
Per sampled frame:
  SET   the lens is closer than min_set_m to any set mesh (cabin/cockpit), or inside one
  BODY  the lens is closer than min_body_m to any character's evaluated body/clothes/hair
  FACE  the hero's eyes are hidden behind set geometry from the lens (a lens blocker in front of the face)
Ranges are merged and printed; 0 SET/BODY ranges is the pass mark."""
import bpy, sys, json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]
OUT = a[0]; STEP = int(a[1]) if len(a) > 1 else 2
MIN_SET = float(a[2]) if len(a) > 2 else 0.08; MIN_BODY = float(a[3]) if len(a) > 3 else 0.18
sc = bpy.context.scene; cam = sc.camera
SET = [o for c in ("CABIN", "COCKPIT") for o in bpy.data.collections[c].all_objects if o.type in ('MESH', 'CURVE')]
CHAR = [o for o in bpy.data.collections["CHARACTERS"].objects if o.type == 'MESH']
def bvh(objs):
    dg = bpy.context.evaluated_depsgraph_get(); V = []; P = []
    for o in objs:
        if o.hide_render: continue
        e = o.evaluated_get(dg)
        try: me = e.to_mesh()
        except Exception: continue
        if me is None: continue
        Mw = o.matrix_world; k = len(V)
        V += [Mw @ v.co for v in me.vertices]; P += [[k + i for i in p.vertices] for p in me.polygons]; e.to_mesh_clear()
    return BVHTree.FromPolygons(V, P) if P else None
STATIC = [o for o in SET if not (o.animation_data or (o.parent and o.parent.animation_data))]
MOVING = [o for o in SET if o not in STATIC]
sc.frame_set(1); B_STATIC = bvh(STATIC)
hero = bpy.data.objects["HERO"]
res = {"SET": [], "BODY": [], "FACE": []}
for f in range(sc.frame_start, sc.frame_end + 1, STEP):
    sc.frame_set(f); p = cam.matrix_world.translation.copy()
    ds = B_STATIC.find_nearest(p)[3] if B_STATIC else 9
    bm = bvh(MOVING); dm = bm.find_nearest(p)[3] if bm else 9
    dset = min(ds or 9, dm or 9)
    if dset < MIN_SET: res["SET"].append((f, round(dset, 3)))
    if f % (STEP * 2) == 1 or STEP > 2:
        bc = bvh(CHAR); db = bc.find_nearest(p)[3] if bc else 9
        if db is not None and db < MIN_BODY: res["BODY"].append((f, round(db, 3)))
    eyes = (hero.matrix_world @ hero.pose.bones["eye.L"].head + hero.matrix_world @ hero.pose.bones["eye.R"].head) / 2
    d = eyes - p
    h = B_STATIC.ray_cast(p, d.normalized(), d.length - 0.05)
    hm = bm.ray_cast(p, d.normalized(), d.length - 0.05) if bm else (None,)
    # only counts when the face is inside the view cone
    fwd = cam.matrix_world.to_3x3() @ Vector((0, 0, -1))
    if (h[0] is not None or hm[0] is not None) and d.normalized().dot(fwd) > 0.8:
        res["FACE"].append(f)
def ranges(fr):
    out = []
    for f in fr:
        f = f[0] if isinstance(f, tuple) else f
        if out and f - out[-1][1] <= STEP * 3: out[-1][1] = f
        else: out.append([f, f])
    return out
summary = {k: ranges(v) for k, v in res.items()}
json.dump({"summary": summary, "detail": res}, open(OUT, "w"), indent=0)
for k, v in summary.items(): print("CAMCHECK", k, len(v), v)
