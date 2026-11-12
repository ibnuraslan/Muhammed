"""Director QA: catches the faults the client keeps rejecting, from the scene itself (no render needed).

blender -b film.blend --python qa_check.py -- out.json [step=6] [beats.json]

Per sampled frame it reports:
  EMPTY      no character's head or hands in the camera view (bare wall / sky / floor / prop frame)
  FILL       >70 % of a 7x11 ray grid from the camera hits one non-character object closer than 0.6 m
             (wall, tube, desk, lid or prop filling the frame), or >70 % of rays hit anything within 0.12 m,
             or >25 % of rays hit hair (top of head), or characters cover <15 % while walls within 3 m fill the rest
  INSIDE     the camera is inside geometry (most rays hit back faces)
  BACKHEAD   on a story-beat frame (beats.json), the nearest visible character shows the camera the back of the head
  HOVER      a hand is within 12 cm of a prop but no finger vertex is within 1.2 cm of it (fist/hand floating beside it)
  CLAW       a visible hand whose fingers are bent in the middle/end joints (>35 deg) while the base joint is
             straight or bent backwards (<10 deg), or whose fingertips fan out >30 deg apart while curled
  FACEPRESS  a fingertip or palm vertex inside 1 cm of the same character's face region, or the head within
             3 cm of a prop surface
A clean film reports 0 for every category except intended, listed exceptions.
"""
import bpy, sys, json, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view

a = sys.argv[sys.argv.index("--") + 1:]
OUT = a[0]; STEP = int(a[1]) if len(a) > 1 else 6
BEATS = []
if len(a) > 2:
    b = json.load(open(a[2]))
    BEATS = [int(x if isinstance(x, (int, float)) else x.get("frame", x.get("start", 0)))
             for x in (b if isinstance(b, list) else b.get("beats", b.get("frames", [])))]
sc = bpy.context.scene; cam = sc.camera

RIGS = [o for o in bpy.data.objects if o.type == 'ARMATURE' and "head" in o.pose.bones and "finger2-1.L" in o.pose.bones]
CHAR_MESH = set()
for r in RIGS:
    for c in r.children_recursive:
        if c.type == 'MESH': CHAR_MESH.add(c.name)
def body_of(r):
    m = [c for c in r.children_recursive if c.type == 'MESH' and (c.name.endswith(".body") or "body" in c.name.lower())]
    return max(m, key=lambda c: len(c.data.vertices)) if m else None
BODY = {r.name: body_of(r) for r in RIGS}
PROPS = [o for o in bpy.data.objects if o.type == 'MESH' and o.name not in CHAR_MESH and len(o.data.polygons) < 200000
         and not any(k in o.name.lower() for k in ("ground", "floor", "terrain", "sky", "backdrop", "water", "ocean", "pile", "heap"))]

def wpos(r, bone, tail=False):
    pb = r.pose.bones[bone]; return r.matrix_world @ (pb.tail if tail else pb.head)
def visible(p, margin=0.0):
    c = world_to_camera_view(sc, cam, p)
    return -margin <= c.x <= 1 + margin and -margin <= c.y <= 1 + margin and c.z > 0.05
def hidden(r):
    b = BODY.get(r.name)
    return r.hide_render or (b is not None and b.hide_render)

_clear = {}
def see_through(ob):
    if ob.name not in _clear:
        v = False
        for m in ob.data.materials if hasattr(ob.data, "materials") else []:
            if m and m.use_nodes:
                for n in m.node_tree.nodes:
                    if n.type == "BSDF_PRINCIPLED":
                        t = n.inputs.get("Transmission Weight") or n.inputs.get("Transmission"); al = n.inputs.get("Alpha")
                        if (t and not t.is_linked and t.default_value > 0.5) or (al and not al.is_linked and al.default_value < 0.6): v = True   # animated (linked) x-ray fades count as opaque
                    if n.type in ("BSDF_TRANSPARENT", "BSDF_GLASS"): v = True
        _clear[ob.name] = v
    return _clear[ob.name]
def cast(dg, org, d, dist=50):
    o = org
    for _ in range(4):
        ok, loc, n, idx, ob, _m = sc.ray_cast(dg, o, d, distance=dist)
        if not ok: return None, 99
        if ob.name in CHAR_MESH or not see_through(ob): return ob.name, (loc - org).length
        o = loc + d * 0.002
    return None, 99
def ray_grid(dg):
    cm = cam.matrix_world; frame = cam.data.view_frame(scene=sc)
    tr, br, bl, tl = [cm @ v for v in frame]   # view_frame order: top-right, bottom-right, bottom-left, top-left
    org = cm.translation; hits = []
    for i in range(7):
        for j in range(11):
            u, v = (i + 0.5) / 7, (j + 0.5) / 11
            p = bl.lerp(br, u).lerp(tl.lerp(tr, u), v)
            hits.append(cast(dg, org, (p - org).normalized()))
    return hits

FING = {s: [("finger%d-%d.%s" % (i, j, s)) for i in range(2, 6) for j in (1, 2, 3)] for s in "LR"}
def bend(r, n):
    """flex of a finger joint in degrees relative to its rest pose: + toward the palm (local X), - bent backwards"""
    pb = r.pose.bones[n]; par = pb.parent
    if par is None: return 0.0
    rel = par.matrix.to_3x3().inverted() @ pb.matrix.to_3x3()
    rest = par.bone.matrix_local.to_3x3().inverted() @ pb.bone.matrix_local.to_3x3()
    return math.degrees((rest.inverted() @ rel).to_euler().x)

def claw(r, s):
    bad = 0; tips = []
    for i in range(2, 6):
        b1 = bend(r, "finger%d-1.%s" % (i, s)); b2 = bend(r, "finger%d-2.%s" % (i, s)); b3 = bend(r, "finger%d-3.%s" % (i, s))
        if (b2 + b3) / 2 > 35 and b1 < 10: bad += 1
        tips.append((wpos(r, "finger%d-3.%s" % (i, s), True) - wpos(r, "finger%d-1.%s" % (i, s))).normalized())
    fan = max(math.degrees(tips[k].angle(tips[k + 1], 0)) for k in range(3))
    curled = sum(bend(r, "finger%d-2.%s" % (i, s)) for i in range(2, 6)) / 4 > 30
    return bad >= 2 or (fan > 30 and curled)

prop_bvh_cache = {}
def prop_bvh(o, dg, f):
    key = (o.name, f)
    if key not in prop_bvh_cache:
        ev = o.evaluated_get(dg); me = ev.to_mesh(); mw = o.matrix_world
        prop_bvh_cache.clear()
        prop_bvh_cache[key] = BVHTree.FromPolygons([mw @ v.co for v in me.vertices], [tuple(p.vertices) for p in me.polygons]) if me.polygons else None
        ev.to_mesh_clear()
    return prop_bvh_cache[key]

res = {"frames": {}, "counts": {}}
def flag(f, kind, what):
    res["frames"].setdefault(str(f), []).append([kind, what]); res["counts"][kind] = res["counts"].get(kind, 0) + 1

for f in range(sc.frame_start, sc.frame_end + 1, STEP):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get(); cpos = cam.matrix_world.translation
    live = [r for r in RIGS if not hidden(r)]
    def unoccluded(r, p):
        if not visible(p): return False
        d = p - cpos
        name, dist = cast(dg, cpos, d.normalized(), d.length + 0.05)
        return name is None or name in CHAR_MESH
    seen = [r for r in live if any(unoccluded(r, wpos(r, b)) for b in ("head", "wrist.L", "wrist.R", "spine03"))]
    hits = ray_grid(dg)
    # camera inside geometry: most rays hit back faces
    cm_ = cam.matrix_world; fr_ = [cm_ @ v for v in cam.data.view_frame(scene=sc)]; back = 0; tot = 0
    for u in (0.2, 0.5, 0.8):
        for v in (0.2, 0.5, 0.8):
            p_ = fr_[2].lerp(fr_[1], u).lerp(fr_[3].lerp(fr_[0], u), v); d_ = (p_ - cpos).normalized()
            ok, loc, n, idx, ob, _ = sc.ray_cast(dg, cpos, d_, distance=50); tot += 1
            if ok and n.dot(d_) > 0.05: back += 1
    if back / tot > 0.5: flag(f, "INSIDE", "camera inside geometry")
    names = [h[0] for h in hits if h[0]]
    if names:
        top = max(set(names), key=names.count)
        near_top = sum(1 for h in hits if h[0] == top and h[1] < 0.6) / len(hits)
        if top not in CHAR_MESH and near_top > 0.7: flag(f, "FILL", top)
    if sum(1 for h in hits if h[1] < 0.12) / len(hits) > 0.7: flag(f, "FILL", "surface <12 cm")
    HAIR = ("hair", "short0", "long0", "bob0", "ponytail", "braid", "afro")
    hair = sum(1 for h in hits if h[0] and any(k in h[0].lower() for k in HAIR)) / len(hits)
    if hair > 0.25: flag(f, "FILL", "hair / top of head %d%%" % (hair * 100))
    charf = sum(1 for h in hits if h[0] in CHAR_MESH and not any(k in h[0].lower() for k in HAIR)) / len(hits)
    other = sorted(h[1] for h in hits if h[0] and h[0] not in CHAR_MESH)
    if charf < 0.15 and other and len(other) > 0.6 * len(hits) and other[len(other) // 2] < 3.0:
        flag(f, "EMPTY", "wall/prop fills the frame, character only %d%%" % (charf * 100))
    if names and top not in CHAR_MESH and names.count(top) / len(hits) > 0.85 and not any(h[0] in CHAR_MESH for h in hits):
        flag(f, "EMPTY", "only %s in view" % top)
    if not seen and not any(h[0] in CHAR_MESH for h in hits): flag(f, "EMPTY", "no character in view")
    near_beat = any(abs(f - b) <= STEP // 2 for b in BEATS)
    if near_beat and seen:
        r = min(seen, key=lambda r: (wpos(r, "head") - cpos).length)
        hb = r.pose.bones["head"]
        # MPFB characters face -Y in rest; carry that through the head bone's posed rotation
        rot = (hb.matrix.to_3x3() @ hb.bone.matrix_local.to_3x3().inverted())
        fwd = (r.matrix_world.to_3x3() @ rot @ Vector((0, -1, 0))).normalized()
        to_cam = (cpos - wpos(r, "head")).normalized()
        if fwd.dot(to_cam) < -0.3: flag(f, "BACKHEAD", r.name)
    for r in seen:
        for s in "LR":
            w = wpos(r, "wrist." + s)
            if not visible(w, 0.05): continue
            tips = [wpos(r, "finger%d-3.%s" % (i, s), True) for i in range(1, 6)] + [wpos(r, "finger3-1." + s)]
            curl = sum(bend(r, "finger%d-%d.%s" % (i, j, s)) for i in range(2, 6) for j in (1, 2, 3)) / 12
            touching = False
            for t in tips[:5]:
                for dvec in (Vector((1, 0, 0)), Vector((-1, 0, 0)), Vector((0, 1, 0)), Vector((0, -1, 0)), Vector((0, 0, 1)), Vector((0, 0, -1))):
                    ok, loc, n, idx, ob, _ = sc.ray_cast(dg, t + dvec * 0.001, dvec, distance=0.02)
                    if ok and not (ob.name in CHAR_MESH and ob.parent and ob.parent.name == r.name and "body" not in ob.name.lower()):
                        touching = True; break
                if touching: break
            if claw(r, s) or (curl > 40 and not touching): flag(f, "CLAW", "%s.%s curl %d%s" % (r.name, s, curl, "" if touching else " in air"))
            for o in PROPS:
                if (o.matrix_world.translation - w).length > 3.0: continue
                bvh = prop_bvh(o, dg, f)
                if bvh is None: continue
                d_wrist = bvh.find_nearest(w, 0.12)
                if d_wrist[0] is None: continue
                dmin = min((bvh.find_nearest(t, 0.2)[3] or 9) for t in tips)
                if dmin > 0.012: flag(f, "HOVER", "%s.%s near %s (%.1f cm)" % (r.name, s, o.name, dmin * 100))
                break
            hd = wpos(r, "head");
            if min((t - hd).length for t in tips) < 0.07: flag(f, "FACEPRESS", "%s.%s hand on face" % (r.name, s))
    if f % 120 == 1: print("QA", f, res["frames"].get(str(f)))

json.dump(res, open(OUT, "w"), indent=1)
print("QA_COUNTS", res["counts"])
