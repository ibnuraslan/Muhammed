"""Limb and prop check: the faults the client found by WATCHING the film, which fingertip checks missed.

blender -b film.blend --python limb_check.py -- out.json [step=2]

Per sampled frame, for every visible MPFB character (only points the camera can see are reported):
  ARMBODY   a point on the upper arm / forearm / wrist bone axis is inside a body:
            inside the character's OWN torso (hand coming out of the chest, arm through the body) or inside
            ANY other character's body (arm through someone else).
  ARMBACK   the arm is bent behind the body: the wrist is more than 15 cm behind the shoulder plane while the
            upper arm is not hanging down (reaching backwards instead of turning the body).
  PROPHEAD  a prop (small mesh, not part of a character) has vertices inside a character's head or neck
            (a tool stuck in the temple, an ear pushed into an eye). Intended contacts must be listed.
Bone axes run inside the limb, so a point of the axis inside a torso means the limb really passes through it.
"""
import bpy, sys, json, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view

a = sys.argv[sys.argv.index("--") + 1:]
OUT = a[0]; STEP = int(a[1]) if len(a) > 1 else 2
sc = bpy.context.scene; cam = sc.camera
for o in bpy.data.objects:            # keep vertex indices stable
    for m in getattr(o, "modifiers", []):
        if m.type in ("MASK", "SUBSURF", "MULTIRES"): m.show_viewport = False

RIGS = [o for o in bpy.data.objects if o.type == 'ARMATURE' and "head" in o.pose.bones and "upperarm01.L" in o.pose.bones]
def body_of(r):
    m = [c for c in r.children_recursive if c.type == 'MESH' and "body" in c.name.lower()]
    return max(m, key=lambda c: len(c.data.vertices)) if m else None
BODY = {r.name: body_of(r) for r in RIGS}
TORSO_G = ("spine", "pelvis", "clavicle", "breast", "neck", "root", "shoulder")
HEAD_G = ("head", "neck", "eye", "jaw", "tongue", "teeth", "ear", "nose", "lip", "cheek", "brow", "temple", "orbicularis", "levator", "oris", "risorius", "special")
CLS = {}
for r in RIGS:
    b = BODY[r.name]
    if b is None: continue
    gi = {g.index: g.name.lower() for g in b.vertex_groups}
    bones = {bn.name.lower() for bn in r.data.bones}
    torso, head, skin = set(), set(), set()
    for v in b.data.vertices:
        gs = [g for g in v.groups if g.weight > 0.05]
        if any(gi.get(g.group, "").startswith(("helper", "joint")) and g.weight > 0.5 for g in gs): continue
        skin.add(v.index)
        gs = [g for g in gs if gi.get(g.group, "") in bones]      # bone groups only (MPFB also has Left/Right/Mid)
        if not gs: continue
        dom = gi.get(max(gs, key=lambda g: g.weight).group, "")
        if any(dom.startswith(k) for k in TORSO_G): torso.add(v.index)
        if any(dom.startswith(k) for k in HEAD_G): head.add(v.index)
    CLS[r.name] = (torso, head, skin)
CHAR = set()
for r in RIGS:
    for c in r.children_recursive: CHAR.add(c.name)
PROPS = [o for o in bpy.data.objects if o.type == 'MESH' and o.name not in CHAR and o.parent not in RIGS
         and 0 < len(o.data.vertices) < 60000]

def bvh(verts, polys, keep):
    ps = [p for p in polys if all(i in keep for i in p)]
    return BVHTree.FromPolygons(verts, ps) if ps else None
def inside(t, p, depth=0.02, rad=0.12):
    if t is None: return False
    loc, nrm, _, d = t.find_nearest(p, rad)
    return loc is not None and d > depth and (p - loc).dot(nrm) < 0
def seen(p):
    c = world_to_camera_view(sc, cam, p); return 0 <= c.x <= 1 and 0 <= c.y <= 1 and c.z > 0.05
def W(r, b, tail=False):
    pb = r.pose.bones[b]; return r.matrix_world @ (pb.tail if tail else pb.head)
ARM = ["upperarm01", "upperarm02", "lowerarm01", "lowerarm02"]

res = {"frames": {}, "counts": {}}
def flag(f, k, w):
    res["frames"].setdefault(str(f), []).append([k, w]); res["counts"][k] = res["counts"].get(k, 0) + 1

for f in range(sc.frame_start, sc.frame_end + 1, STEP):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    live = [r for r in RIGS if not r.hide_render and BODY.get(r.name) is not None and not BODY[r.name].hide_render and r.name in CLS]
    T = {}
    for r in live:
        b = BODY[r.name]; e = b.evaluated_get(dg); me = e.to_mesh(); mw = e.matrix_world
        vs = [mw @ v.co for v in me.vertices]; ps = [tuple(p.vertices) for p in me.polygons]; e.to_mesh_clear()
        torso, head, skin = CLS[r.name]
        T[r.name] = (bvh(vs, ps, torso), bvh(vs, ps, head), bvh(vs, ps, skin))
    for r in live:
        up = (W(r, "neck01") - W(r, "spine05")).normalized()
        for s in ("L", "R"):
            pts = []
            for bn in ARM:
                n = bn + "." + s
                if n not in r.pose.bones: continue
                h, t = W(r, n), W(r, n, True)
                pts += [h.lerp(t, k / 4) for k in range(5)]
            pts.append(W(r, "wrist." + s, True))
            vis = [p for p in pts if seen(p)]
            if not vis: continue
            own = sum(1 for p in vis if inside(T[r.name][0], p, 0.03))
            if own >= 2: flag(f, "ARMBODY", "%s arm.%s inside own torso (%d pts)" % (r.name, s, own))
            for o in live:
                if o is r: continue
                k = sum(1 for p in vis if inside(T[o.name][2], p, 0.03))
                if k >= 2: flag(f, "ARMBODY", "%s arm.%s inside %s (%d pts)" % (r.name, s, o.name, k))
            # behind the body
            shL, shR = W(r, "upperarm01.L"), W(r, "upperarm01.R")
            side = (shR - shL).normalized(); fwd = up.cross(side).normalized()
            if "jaw" in r.pose.bones:
                if (W(r, "jaw", True) - W(r, "head")).dot(fwd) < 0: fwd = -fwd
            sh = W(r, "upperarm01." + s); wr = W(r, "wrist." + s)
            ua = (W(r, "upperarm02." + s, True) - sh).normalized()
            if (wr - sh).dot(fwd) < -0.15 and ua.dot(up) > -0.3 and seen(wr):
                flag(f, "ARMBACK", "%s arm.%s reaches %.0f cm behind the body" % (r.name, s, -(wr - sh).dot(fwd) * 100))
    for o in PROPS:
        if o.hide_render or not o.visible_get(): continue
        e = o.evaluated_get(dg); bb = [e.matrix_world @ Vector(c) for c in e.bound_box]
        dims = max((bb[6] - bb[0]).length, 0.0)
        if dims > 0.6: continue
        c = sum(bb, Vector()) / 8
        if not seen(c): continue
        near = [r for r in live if (W(r, "head") - c).length < 0.4]
        if not near: continue
        me = e.to_mesh(); vs = [e.matrix_world @ v.co for v in me.vertices]; e.to_mesh_clear()
        vs = vs[:: max(1, len(vs) // 150)]
        for r in near:
            k = sum(1 for p in vs if inside(T[r.name][1], p, 0.005, 0.08))
            if k >= 2: flag(f, "PROPHEAD", "%s inside %s's head/face (%d pts)" % (o.name, r.name, k))
    if f % 120 == 1: print("LC", f, res["counts"])
json.dump(res, open(OUT, "w"), indent=1)
print("LC_COUNTS", res["counts"])
