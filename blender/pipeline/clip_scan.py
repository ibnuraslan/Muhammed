"""Director clipping scan: forearms/hands/fingers going INTO heads, necks, torsos, legs,
clothes or other characters. Independent of each chat's own audit.

blender -b film.blend --python clip_scan.py -- out.json [step=6] [depth_cm=2.0] [cam_radius_m=7]

For each sampled frame and each MPFB character near the camera:
  probes  = evaluated body vertices whose dominant group is a lower-arm / wrist / hand / finger bone
  targets = (a) same body, head/neck/spine/pelvis/leg regions; (b) same character's clothes;
            (c) every other nearby character's body + clothes
  a probe counts as inside when it is deeper than depth_cm under the target surface
  (nearest-point + normal test on a BVH of the target).
Writes per-frame hit counts per character and target kind, plus merged bad frame ranges."""
import bpy, sys, json, bmesh
from mathutils.bvhtree import BVHTree
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

a = sys.argv[sys.argv.index("--") + 1:]
OUT = a[0]; STEP = int(a[1]) if len(a) > 1 else 6
DEPTH = (float(a[2]) if len(a) > 2 else 2.0) / 100.0
CAMR = float(a[3]) if len(a) > 3 else 7.0
sc = bpy.context.scene; cam = sc.camera

ARM = ("hand", "finger", "metacarpal", "thumb", "palm")
SKIP = ("lowerarm", "wrist", "upperarm", "clavicle", "shoulder", "deltoid", "breast", "pectoral", "scapula")   # too close to torso to judge
SELF_T = ("head", "neck", "jaw", "spine", "pelvis", "upperleg", "lowerleg", "thigh", "calf", "foot", "toe", "root", "eye", "ear", "nose", "lip", "oris", "brow", "cheek", "temporal", "tongue", "levator", "risorius", "special", "orbicularis", "glute")

def chars():
    out = []
    for r in bpy.data.objects:
        if r.type != 'ARMATURE' or not r.visible_get(): continue
        kids = [c for c in r.children_recursive if c.type == 'MESH' and c.visible_get() and not c.hide_render]
        body = [c for c in kids if c.name.endswith(".body") or "body" in c.name.lower() and len(c.data.vertices) > 8000]
        if not body: continue
        body = max(body, key=lambda c: len(c.data.vertices))
        for m in body.modifiers:                      # keep base topology so vertex indices match
            if m.type in ('MASK', 'SUBSURF', 'MULTIRES'): m.show_viewport = False
        cloth = [c for c in kids if c is not body and len(c.data.vertices) > 200 and not any(k in c.name.lower() for k in ("eye", "brow", "lash", "teeth", "tongue", "hair", "glove", "cuff", "watch", "ring", "high-poly", "low-poly", "long0", "short0", "bob0", "ponytail", "braid", "afro", "shoe", "boot", "sneaker", "proxy"))]
        out.append((r, body, cloth))
    return out

CH = chars()
print("CHARACTERS", len(CH), [c[0].name for c in CH][:20])
# vertex classes from rest data (dominant group)
cls = {}
for r, body, _ in CH:
    bones = {b.name for b in r.data.bones}
    gi = {g.index: g.name for g in body.vertex_groups}
    helper = {i for i, n in gi.items() if n.lower().startswith(("helper", "joint")) or n in ("HelperGeometry", "JointCubes")}
    probe, selft = [], []
    for v in body.data.vertices:
        if any(g.group in helper and g.weight > 0.5 for g in v.groups): continue
        dg_ = [g for g in v.groups if gi.get(g.group) in bones]
        if not dg_: continue
        g = max(dg_, key=lambda x: x.weight); n = gi[g.group].lower()
        if any(k in n for k in SKIP): continue
        if any(k in n for k in ARM): probe.append(v.index)
        elif any(k in n for k in SELF_T): selft.append(v.index)
    cls[body.name] = (probe, set(selft))
    print("CLASS", body.name, "probes", len(probe), "self-targets", len(selft))

def bvh_of(obj, dg, keep=None):
    ev = obj.evaluated_get(dg); me = ev.to_mesh()
    mw = obj.matrix_world
    verts = [mw @ v.co for v in me.vertices]
    if keep is None:
        polys = [tuple(p.vertices) for p in me.polygons]
    else:
        polys = [tuple(p.vertices) for p in me.polygons if all(i in keep for i in p.vertices)]
    ev.to_mesh_clear()
    if not polys: return None, verts
    return BVHTree.FromPolygons(verts, polys), verts

def inside(bvh, p):
    loc, nrm, _, d = bvh.find_nearest(p, 0.5)
    if loc is None: return False
    return d > DEPTH and (p - loc).dot(nrm) < 0

res = {"frames": {}, "step": STEP, "depth_cm": DEPTH * 100}
dg = bpy.context.evaluated_depsgraph_get()
for f in range(sc.frame_start, sc.frame_end + 1, STEP):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    cpos = cam.matrix_world.translation
    near = [c for c in CH if (c[0].matrix_world.translation - cpos).length < CAMR]
    if not near: continue
    built = {}
    for r, body, cloth in near:
        probe, selft = cls[body.name]
        bb, verts = bvh_of(body, dg)
        sb, _ = bvh_of(body, dg, keep=selft)
        cb = []
        pts = []
        for i in probe:
            p = verts[i]; c = world_to_camera_view(sc, cam, p)
            if 0.0 <= c.x <= 1.0 and 0.0 <= c.y <= 1.0 and c.z > 0.05: pts.append(p)   # only what the camera can see
        built[r.name] = (bb, sb, [x for x in cb if x], pts)
    fr = {}
    for name, (bb, sb, cbs, pts) in built.items():
        hs = sum(1 for p in pts if sb and inside(sb, p))
        hc = 0   # open garment meshes give false positives at cuffs/hems; a hand through a shirt also enters the body below
        ho = 0
        for on, (obb, _, ocb, _) in built.items():
            if on == name: continue
            ho += sum(1 for p in pts if obb and inside(obb, p))
        if hs + hc + ho > 0: fr[name] = {"self": hs, "clothes": hc, "other": ho}
    if fr: res["frames"][f] = fr
    if f % 120 == 1: print("FRAME", f, fr)

# merge into ranges (frames whose worst character has >= 25 probe verts inside)
bad = sorted(int(f) for f, d in res["frames"].items() if max(sum(v.values()) for v in d.values()) >= 25)
ranges = []
for f in bad:
    if ranges and f - ranges[-1][1] <= STEP * 2: ranges[-1][1] = f
    else: ranges.append([f, f])
res["bad_ranges"] = ranges
res["fps"] = sc.render.fps
json.dump(res, open(OUT, "w"), indent=1)
print("BAD_RANGES", [(a_, b_, f"{a_/sc.render.fps:.1f}-{b_/sc.render.fps:.1f}s") for a_, b_ in ranges])
