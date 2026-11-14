"""Limb-through-body scan (Connect01, EarInArm v009d): the arm bone AXES (upperarm, forearm, hand/metacarpals) of every
character are sampled and tested against every body's skin, including the character's own torso/head/legs.
clip_scan only probes hand vertices; an arm whose centre line is inside a torso is the worst kind of clip.

blender -b film.blend --python limb_scan.py -- out.json [step=4] [depth_cm=1.5] [maxdepth_cm=12]

A sample counts as inside when it lies behind the nearest skin face (normal test) by more than depth_cm and less than
maxdepth_cm (beyond that the nearest face is not the surface it is in). Own-body targets exclude the arm itself, the
shoulder/clavicle region and the hands. Frames are reported per character/side with the worst bone and depth, and
whether the sample is in the camera view."""
import bpy, sys, json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view

a = sys.argv[sys.argv.index("--") + 1:]
OUT = a[0]; STEP = int(a[1]) if len(a) > 1 else 4
DEPTH = (float(a[2]) if len(a) > 2 else 1.5) / 100.0
MAXD = (float(a[3]) if len(a) > 3 else 12.0) / 100.0
sc = bpy.context.scene; cam = sc.camera

ARMB = ["upperarm01", "upperarm02", "lowerarm01", "lowerarm02", "wrist", "metacarpal2", "metacarpal3", "metacarpal4"]
SELF_T = ("head", "neck", "jaw", "spine", "pelvis", "upperleg", "lowerleg", "foot", "toe", "root", "glute", "breast", "pectoral")
SKIP = ("upperarm", "lowerarm", "wrist", "hand", "finger", "metacarpal", "thumb", "clavicle", "shoulder", "scapula", "deltoid")

CH = []
for r in bpy.data.objects:
    if r.type != 'ARMATURE': continue
    body = [c for c in r.children_recursive if c.type == 'MESH' and c.name.endswith(".body")]
    if not body: continue
    body = body[0]
    for m in body.modifiers:
        if m.type in ('MASK', 'SUBSURF', 'MULTIRES'): m.show_viewport = False
    gi = {g.index: g.name for g in body.vertex_groups}; bones = {b.name for b in r.data.bones}
    helper = {i for i, n in gi.items() if n.lower().startswith(("helper", "joint")) or n in ("HelperGeometry", "JointCubes")}
    skin, selft = set(), set()
    for v in body.data.vertices:
        if any(g.group in helper and g.weight > 0.5 for g in v.groups): continue
        skin.add(v.index)
        gs = [g for g in v.groups if gi.get(g.group) in bones]
        if not gs: continue
        n = gi[max(gs, key=lambda g: g.weight).group].lower()
        if any(k in n for k in SKIP): continue
        if any(k in n for k in SELF_T): selft.add(v.index)
    CH.append((r, body, skin, selft))

def bvh(body, keep, dg):
    ev = body.evaluated_get(dg); me = ev.to_mesh(); mw = body.matrix_world
    vs = [mw @ v.co for v in me.vertices]
    ps = [tuple(p.vertices) for p in me.polygons if all(i in keep for i in p.vertices)]
    ev.to_mesh_clear()
    return BVHTree.FromPolygons(vs, ps) if ps else None

def depth_in(t, p):
    loc, nrm, _, d = t.find_nearest(p, MAXD)
    if loc is None or (p - loc).dot(nrm) >= 0: return 0.0
    return d

res = {"step": STEP, "depth_cm": DEPTH * 100, "frames": {}}
for f in range(sc.frame_start, sc.frame_end + 1, STEP):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    vis = [c for c in CH if not c[1].hide_render and not c[0].hide_render]
    T = {c[0].name: (bvh(c[1], c[2], dg), bvh(c[1], c[3], dg)) for c in vis}
    fr = {}
    for r, body, skin, selft in vis:
        for s in "LR":
            worst = (0.0, None, None, False)
            for bn in ARMB:
                pb = r.pose.bones.get(bn + "." + s)
                if not pb: continue
                h = r.matrix_world @ pb.head; t_ = r.matrix_world @ pb.tail
                for u in ((0.7, 0.9) if bn == "upperarm01" else (0.15, 0.4, 0.65, 0.9)):   # upperarm01 starts inside the shoulder
                    p = h.lerp(t_, u)
                    for on, (full, own) in T.items():
                        tgt = own if on == r.name else full
                        if tgt is None: continue
                        d = depth_in(tgt, p)
                        if d > DEPTH and d > worst[0]:
                            c = world_to_camera_view(sc, cam, p)
                            worst = (d, bn, on, 0.0 <= c.x <= 1.0 and 0.0 <= c.y <= 1.0 and c.z > 0.05)
            if worst[1]:
                fr["%s.%s" % (r.name, s)] = {"bone": worst[1], "into": worst[2], "depth_cm": round(worst[0] * 100, 1), "visible": worst[3]}
    if fr: res["frames"][f] = fr
    if f % 200 == 1: print("LIMB", f, fr)
bad = sorted(int(f) for f, d in res["frames"].items() if any(v["visible"] for v in d.values()))
ranges = []
for f in bad:
    if ranges and f - ranges[-1][1] <= STEP * 2: ranges[-1][1] = f
    else: ranges.append([f, f])
res["bad_ranges"] = ranges
json.dump(res, open(OUT, "w"), indent=1)
print("LIMB_RANGES", ranges)
