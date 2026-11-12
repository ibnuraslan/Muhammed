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
  CAMJUMP    (every frame) a camera switch, or the camera teleports >0.25 m in one frame (or turns >60 deg): a hard cut.
             The film is ONE continuous camera; only a fully covered wipe may hide a jump.
  PROPMOVE   a hand-sized prop moves with no hand within 10 cm (a prop moving by itself: floating pen, tool)
  ATTACH     a worn item (mask, cap, hat, glasses) drifts more than 2 cm off the head it sits on
  ROLL       the horizon is tilted more than ~20 deg (upside-down / sideways frame from an aim constraint).
A clean film reports 0 for every category except intended, listed exceptions.
Hidden (hide_render / not visible) and see-through props are ignored; HOVER tests the nearest visible prop only;
a deliberate point / trigger finger / writing grip is not a CLAW.
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
    mids = [bend(r, "finger%d-2.%s" % (i, s)) for i in range(2, 6)]
    curled = sum(mids) / 4 > 30
    pointing = sum(1 for m in mids if m < 15) in (1, 2) and sum(1 for m in mids if m > 40) >= 2   # point / trigger / tripod
    return (bad >= 2 or (fan > 30 and curled)) and not pointing

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
            # nearest VISIBLE, opaque prop to the wrist (hidden / see-through FX and parked props are ignored)
            best = None
            for o in PROPS:
                if o.hide_render or not o.visible_get() or see_through(o): continue
                if (o.matrix_world.translation - w).length > 3.0: continue
                bvh = prop_bvh(o, dg, f)
                if bvh is None: continue
                d_wrist = bvh.find_nearest(w, 0.12)
                if d_wrist[0] is None: continue
                if best is None or d_wrist[3] < best[2]: best = (o, bvh, d_wrist[3])
            if best:
                o, bvh, _ = best
                dmin = min((bvh.find_nearest(t, 0.2)[3] or 9) for t in tips)
                if dmin > 0.012 and not touching: flag(f, "HOVER", "%s.%s near %s (%.1f cm)" % (r.name, s, o.name, dmin * 100))
            hd = wpos(r, "head");
            if min((t - hd).length for t in tips) < 0.07: flag(f, "FACEPRESS", "%s.%s hand on face" % (r.name, s))
    if f % 120 == 1: print("QA", f, res["frames"].get(str(f)))

# CAMJUMP: the film must be ONE continuous camera. Every frame (not STEP): a camera switch (markers), or a
# one-frame move/turn that is a step, not motion: >0.25 m (or a turn >60 deg: a whip pan up to 60 deg/frame is style) AND >3x the neighbouring frames' speed
# (a fast fly-over moves a lot every frame; a cut moves a lot in one frame). Only a fully covered wipe
# (black / cloud frame) may hide one; list those in ACTING_notes.md.
P = []
for f in range(sc.frame_start, sc.frame_end + 1):
    sc.frame_set(f); P.append((f, sc.camera, sc.camera.matrix_world.copy()))
D = [(0.0, 0.0)] + [((P[k][2].translation - P[k-1][2].translation).length,
       (lambda a: min(a, 360 - a))(math.degrees(P[k-1][2].to_quaternion().rotation_difference(P[k][2].to_quaternion()).angle))) for k in range(1, len(P))]
for k in range(1, len(P)):
    f, c, m = P[k]
    if c != P[k-1][1]: flag(f, "CAMJUMP", "camera switch %s -> %s" % (P[k-1][1].name, c.name)); continue
    nb = [D[x] for x in range(max(1, k-3), min(len(D), k+4)) if x != k]
    vd = sorted(x[0] for x in nb)[len(nb)//2] if nb else 0; va = sorted(x[1] for x in nb)[len(nb)//2] if nb else 0
    d, ang = D[k]
    if (d > 0.25 and d > 3 * vd + 0.02) or (ang > 60 and ang > 3 * va + 1):
        flag(f, "CAMJUMP", "cut: %.2f m, %.0f deg in one frame (neighbours %.2f m, %.0f deg)" % (d, ang, vd, va))

# ROLL: the horizon must stay level (no upside-down / sideways frames from Damped Track or aim flips). The camera's
# world X axis must stay near horizontal: |x.z| > 0.34 (about 20 deg of roll) is flagged; a deliberate dutch angle
# must be listed. Skipped while the camera looks almost straight up/down (the horizon is not in frame then).
for (f, c, m) in P[::max(1, STEP // 2)]:
    x = m.col[0].xyz.normalized(); fwd = (-m.col[2].xyz).normalized()
    if abs(fwd.z) < 0.85 and abs(x.z) > 0.34:
        flag(f, "ROLL", "horizon tilted %.0f deg" % math.degrees(math.asin(min(1.0, abs(x.z)))))

# PROPMOVE: "props never move by themselves". A hand-sized prop (bbox under 1.5 m) that moves more than 5 mm
# between samples while in view must have a fingertip or palm of some visible character within 3 cm of its
# bounding box, i.e. a hand is ON it. This catches a pen or tool that follows the wrist at an offset and floats
# beside the hand. Props parented to a rig or to another object move with their carrier and are skipped.
# Falling or thrown props are allowed only when listed in ACTING_notes.md.
# ATTACH: worn items (mask, cap, hat, glasses, goggles, helmet, headlamp, visor) must sit ON the skin: the
# median distance of their vertices to the wearer's body surface must be 1.5 cm or less (catches a mask that
# hangs below the nose or floats off the face).
import re
WORN = {"mask", "cap", "hat", "glasses", "goggles", "helmet", "headlamp", "visor", "spectacles"}
def _tokens(n): return set(t for t in re.split(r"[^a-z]+", re.sub(r"([a-z])([A-Z])", r"\1 \2", n).lower()) if t)
def _bbox(o, dg):
    e = o.evaluated_get(dg); mw = e.matrix_world
    pts = [mw @ Vector(c) for c in e.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi
def _box_dist(lo, hi, p):
    return Vector((max(lo.x - p.x, 0, p.x - hi.x), max(lo.y - p.y, 0, p.y - hi.y), max(lo.z - p.z, 0, p.z - hi.z))).length
HANDB = [("wrist", False)] + [("finger%d-%d" % (k, j), True) for k in (1, 2, 3, 4, 5) for j in (2, 3)]
MOVERS = [o for o in PROPS if o.parent is None]
worn = [o for o in bpy.data.objects if o.type == 'MESH' and _tokens(o.name) & WORN]
prevc = {}; nsamp = 0
for f in range(sc.frame_start, sc.frame_end + 1, STEP):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get(); nsamp += 1
    live = [r for r in RIGS if not hidden(r)]
    hands = []
    for r in live:
        for side in ("L", "R"):
            for b, tl in HANDB:
                n = b + "." + side
                if n in r.pose.bones: hands.append(wpos(r, n, tail=tl))
    for o in MOVERS:
        if o.hide_render or not o.visible_get(): prevc.pop(o.name, None); continue
        lo, hi = _bbox(o, dg)
        if (hi - lo).length > 1.5: continue
        c = (lo + hi) / 2; pc = prevc.get(o.name); prevc[o.name] = c
        if pc is None or (c - pc).length < 0.005 or not visible(c): continue
        dmin = min((_box_dist(lo, hi, h) for h in hands), default=9)
        if dmin > 0.03: flag(f, "PROPMOVE", "%s moves %.1f cm with no hand on it (nearest finger %.0f cm)" % (o.name, (c - pc).length * 100, dmin * 100))
    if nsamp % 4 != 1: continue
    for o in worn:
        if o.hide_render or not o.visible_get() or not live: continue
        lo, hi = _bbox(o, dg); c = (lo + hi) / 2
        if not visible(c): continue
        r = min(live, key=lambda q: (wpos(q, "head") - c).length)
        b = BODY.get(r.name)
        if b is None: continue
        eb = b.evaluated_get(dg); mb = eb.to_mesh(); mw = eb.matrix_world
        bvh = BVHTree.FromPolygons([mw @ v.co for v in mb.vertices], [tuple(p.vertices) for p in mb.polygons]); eb.to_mesh_clear()
        ew = o.evaluated_get(dg); mwm = ew.to_mesh(); ow = ew.matrix_world
        ds = sorted((bvh.find_nearest(ow @ v.co, 0.5)[3] or 0.5) for v in mwm.vertices); ew.to_mesh_clear()
        lim = 0.04 if _tokens(o.name) & {"cap", "hat", "helmet"} else 0.015   # caps and hats sit on hair, not skin
        if ds and ds[len(ds) // 2] > lim: flag(f, "ATTACH", "%s is %.1f cm off %s's skin (median)" % (o.name, ds[len(ds) // 2] * 100, r.name))

json.dump(res, open(OUT, "w"), indent=1)
print("QA_COUNTS", res["counts"])
