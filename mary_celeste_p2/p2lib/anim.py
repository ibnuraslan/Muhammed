"""Part 2 animation layer for the final render (the method of Part 1's p1/anim.py and run_anim.py).

Turned on by env ANIM=<shot id> (tools/build_package.sh sets it). Each shot's duration and frame count come from the
voice-over timings (vo/vo_timings.json). Then:

  cast._SharedLive.finish_live -> live(dv, ...)   the rig is NOT baked. The pose the scene set is kept as the base;
        every 0.25 s an idle layer goes on top (breathing in the chest, a slow weight shift, small head drift, with
        the clavicles counter-turned so hands stay on what they hold), plus blinks every 3-5 s and the shot's
        motivated action (a look up, a turn of the head). Every pose bone is keyed. Clothes, boots and buttons are
        skinned or bone-parented; hair is grown once on the posed surface and rides the head bone, as do the corneas.
  stage.finish -> run(shot)    ships worked by the sea (heave/roll/pitch), whatever stands on them goes with them;
        the FFT sea advances; the tug tows; the dawn sun climbs; the camera makes its move (eased, plus a small
        handheld sway where marked). Clipcheck on the first, middle and last frame: zero clips or the shot aborts.
        Then the grade, motion blur, and either a render of the frame range or (EXPORT=<pkg>) a farm .blend.
Nothing moves without a cause."""
import os, sys, json, math
import numpy as np
import bpy
from mathutils import Vector, Matrix, Quaternion
import human as H

FPS = 24
SHOT = os.environ.get("ANIM", "")
_P2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TIM = json.load(open(os.path.join(_P2, "vo", "vo_timings.json"))) if SHOT else {}


def on():
    return bool(SHOT)


def nframes():
    return int(TIM[SHOT]["frames"]) if SHOT in TIM else int(round(float(os.environ.get("ANIM_DUR", "3")) * FPS))


def dur():
    return nframes() / FPS


def ease(u):
    u = min(max(u, 0.0), 1.0); return u * u * (3 - 2 * u)


def _interp(kind):
    try:
        bpy.context.preferences.edit.keyframe_new_interpolation_type = kind
    except Exception:
        pass


# ----------------------------------------------------------------------------- people
def head_turn(yaw=0.0, pitch=0.0, t0=0.0, t1=None):
    """A motivated head move (degrees, rig frame: yaw about Z, pitch down about X) between t0 and t1."""
    def f(dv, t):
        e = ease((t - t0) / max((t1 or dur()) - t0, 1e-3))
        if pitch:
            dv.h.rot("neck01", (1, 0, 0), 0.4 * pitch * e); dv.h.rot("head", (1, 0, 0), 0.6 * pitch * e)
        if yaw:
            dv.h.rot("neck01", (0, 0, 1), 0.4 * yaw * e); dv.h.rot("head", (0, 0, 1), 0.6 * yaw * e)
    return f


def lean(deg, t0=0.0, t1=None):
    """The upper body leans (forward +) from the waist: the clavicles are counter-turned, so the hands stay put."""
    def f(dv, t):
        e = ease((t - t0) / max((t1 or dur()) - t0, 1e-3))
        _spine(dv, "spine04", (1, 0, 0), deg * e)
    return f


def both(*fs):
    def f(dv, t):
        for g in fs:
            g(dv, t)
    return f


# actions per shot and person (by name); each comes from the script
ACTIONS = {
    "02": {"Briggs": head_turn(pitch=3)},                                     # reads back what he wrote
    "06": {"Briggs": head_turn(pitch=-5, t0=0.6)},                            # looks up into her rigging
    "11": {"Briggs": head_turn(pitch=-6, yaw=4, t0=0.3, t1=1.8)},             # pauses, lifts his eyes from the page
    "12": {"Briggs": head_turn(yaw=-22)},                                     # looks round the crowded cabin
    "17": {"Sarah": head_turn(pitch=-14, yaw=6, t0=0.9, t1=1.6)},             # the bang overhead: she looks up
    "19": {"Sarah": lean(3)},
    "22": {"Briggs": head_turn(pitch=-6, yaw=8, t0=0.8)},                     # watches the pennant
    "29": {},
    "34": {"Deveau": head_turn(yaw=10, t0=1.0)},
    "39": {"Deveau": head_turn(yaw=-8, pitch=4, t0=1.5)},
    "44": {"Deveau": head_turn(pitch=5, t0=1.0)},                             # reads the rod
    "45": {"Deveau": head_turn(pitch=-4, t0=0.5)},                            # squares up to the deck ahead
}


def _spine(dv, bone, axis, deg):
    """Rotate a spine bone and turn both clavicles back by the same amount: the chest moves, the arms keep their aim."""
    h = dv.h
    h.rot(bone, axis, deg)
    for sd in ("L", "R"):
        if f"clavicle.{sd}" in h.arm.pose.bones:
            h.rot(f"clavicle.{sd}", axis, -deg)


def idle(dv, t, seed=0):
    """Breathing (0.25 Hz chest), a slow weight shift (0.08 Hz), small head drift: a person alive and still."""
    if os.environ.get("NOIDLE"):
        return
    rng = np.random.default_rng(seed); p = rng.uniform(0, 6.28, 4)
    _spine(dv, "spine03", (1, 0, 0), -0.7 * math.sin(2 * math.pi * 0.25 * t + p[0]))
    _spine(dv, "spine05", (0, 1, 0), 0.5 * math.sin(2 * math.pi * 0.08 * t + p[1]))
    dv.h.rot("neck02", (0, 0, 1), 1.4 * math.sin(2 * math.pi * 0.11 * t + p[2]))
    dv.h.rot("head", (1, 0, 0), 0.8 * math.sin(2 * math.pi * 0.17 * t + p[3]))


def key_pose(dv, key_every=0.25):
    """Key the posed rig over the shot (rig still at its own frame: placing comes after)."""
    h = dv.h; pb = h.arm.pose.bones; D = dur()
    # the shared bake applies the armature to the base mesh, then displace / subsurf / solidify act on the posed shape:
    # put the armature first in every stack so the live clothes take exactly the approved (baked) shape
    for o in list(h.parts) + list(getattr(dv, "objects", [])):
        mods = getattr(o, "modifiers", None)
        if not mods:
            continue
        for i, m in enumerate(mods):
            if m.type == 'ARMATURE' and i > 0:
                mods.move(i, 0)
                break
    seed = sum(map(ord, dv.name)) % 997
    rng = np.random.default_rng(seed + 11)
    blinks = []; tb = rng.uniform(0.4, 1.6)
    while tb < D:
        blinks.append(tb); tb += rng.uniform(3.0, 5.0)
    bpy.context.view_layer.update()
    for b in pb:
        if b.rotation_mode != 'QUATERNION':
            m = b.matrix_basis.copy(); b.rotation_mode = 'QUATERNION'; b.matrix_basis = m
    base = {b.name: b.matrix_basis.copy() for b in pb}
    act = ACTIONS.get(SHOT, {}).get(dv.name)
    times = sorted(set([round(k * key_every, 4) for k in range(int(D / key_every) + 1)] + [round(D, 4)] +
                       [round(b + d, 4) for b in blinks for d in (-0.07, 0.0, 0.06, 0.14)]))
    _interp('BEZIER')
    for t in times:
        if t < 0 or t > D + 1e-6:
            continue
        for b in pb:
            b.matrix_basis = base[b.name]
        bpy.context.view_layer.update()
        idle(dv, t, seed)
        if act:
            act(dv, t)
        for b in blinks:
            u = (t - b) / 0.07
            if -1.0 < u < 2.0:
                dv.lids(1.4 * max(0.0, 1 - abs(u - 0.5) / 1.5))
        bpy.context.view_layer.update()
        f = 1 + t * FPS
        for b in pb:
            b.keyframe_insert("rotation_quaternion", frame=f); b.keyframe_insert("location", frame=f)
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()


def live(dv, density=1.0, hair=True):
    """Shared-lib cast: key the pose, then the fittings finish() would make after its bake. Hair and corneas ride the head."""
    h = dv.h
    key_pose(dv)
    # fittings the shared finish() makes after its bake, here on the live rig
    dv.wrist_rest = {sd: tuple(h.bone_tail(f"wrist.{sd}")) for sd in ("L", "R")}
    dv._corneas()
    if not getattr(dv, "asset_boots", True) and hasattr(dv, "_sea_boots"):
        _with_posed_data(dv, dv._sea_boots)        # it models each boot on the body's mesh data: give it the posed one
        for o in getattr(dv, "sea_boots", []) or []:
            mw = o.matrix_world.copy(); o.parent = h.arm; o.matrix_world = mw
    if hair:
        _grow_hair(dv, density)
    for c in getattr(dv, "corneas", []) or []:
        mw = c.matrix_world.copy(); c.parent = h.arm; c.parent_type = 'BONE'; c.parent_bone = "head"
        bpy.context.view_layer.update(); c.matrix_world = mw
    if getattr(dv, "shawl", None) is not None and hasattr(dv, "_fringe"):
        before = set(bpy.data.objects.keys())
        dv._fringe(dv.shawl)
        for o in [bpy.data.objects[n] for n in set(bpy.data.objects.keys()) - before]:
            if o.parent is None:
                mw = o.matrix_world.copy(); o.parent = h.arm; o.parent_type = 'BONE'; o.parent_bone = "spine01"
                bpy.context.view_layer.update(); o.matrix_world = mw
    # anything of theirs still loose rides on the rig
    for o in dv.objects:
        if o is not h.arm and o.parent is None:
            mw = o.matrix_world.copy(); o.parent = h.arm; o.matrix_world = mw
    h.arm.hide_render = True
    bpy.context.view_layer.update()


def _with_posed_data(dv, fn):
    """Run fn with the body's mesh data holding the posed vertex positions (what the shared lib's bake would leave),
    the armature modifier off meanwhile; then put the rest positions and the modifier back."""
    body = dv.h.body
    sub = [m for m in body.modifiers if m.type == 'SUBSURF']
    for m in sub:
        m.show_viewport = False
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    oe = body.evaluated_get(dg); me = oe.to_mesh()
    posed = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("co", posed); oe.to_mesh_clear()
    rest = np.empty(len(body.data.vertices) * 3, np.float32); body.data.vertices.foreach_get("co", rest)
    arm = [m for m in body.modifiers if m.type == 'ARMATURE']
    for m in arm:
        m.show_viewport = False
    body.data.vertices.foreach_set("co", posed); body.data.update()
    bpy.context.view_layer.update()
    try:
        fn()
    finally:
        body.data.vertices.foreach_set("co", rest); body.data.update()
        for m in arm + sub:
            m.show_viewport = True
        bpy.context.view_layer.update()


def _grow_hair(dv, density):
    h = dv.h
    head_M = (h.arm.matrix_world @ h.arm.pose.bones["head"].matrix).copy()
    dv.head_R = head_M.to_3x3() @ h.arm.data.bones["head"].matrix_local.to_3x3().inverted()
    sub = [m for m in h.body.modifiers if m.type == 'SUBSURF']
    for m in sub:
        m.show_viewport = False
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    oe = h.body.evaluated_get(dg); me = oe.to_mesh()
    Mb = h.body.matrix_world.copy()
    Pts = np.array([(Mb @ v.co)[:] for v in me.vertices]); oe.to_mesh_clear()
    from mathutils.bvhtree import BVHTree
    bvh = BVHTree.FromObject(h.body, dg)
    for m in sub:
        m.show_viewport = True
    before = set(bpy.data.objects.keys())
    dv._posed_surface = lambda: (Pts, bvh)
    dv._grow_all(density)
    new = [bpy.data.objects[n] for n in set(bpy.data.objects.keys()) - before]
    for o in set(new) | set(o for o in getattr(dv, "hair_objs", []) if o):
        if o.parent is None or o.parent == h.body:
            mw = o.matrix_world.copy(); o.parent = h.arm; o.parent_type = 'BONE'; o.parent_bone = "head"
            bpy.context.view_layer.update(); o.matrix_world = mw


# ----------------------------------------------------------------------------- camera
#   (kind, amount), handheld.  push/pull: fraction of the focus distance; drift: metres (right, up, forward);
#   rise: metres (negative = crane down); tilt: degrees up; pan: degrees left; orbit: degrees about the target.
MOVES = {
    "01": (("rise", -0.9), 0), "02": (("push", 0.06), 0.3), "03": (("push", 0.05), 0.3), "04": (("drift", (0.5, 0, 0)), 0),
    "06": (("push", 0.04), 0.2), "07": (("push", 0.06), 0.2), "08": (("drift", (0.05, 0, 0)), 0.4), "09": (("push", 0.06), 0),
    "10": (("push", 0.05), 0.3), "11": (("push", 0.04), 0.2), "12": (("pan", 6), 0.2), "13": (("hold",), 0),
    "14": (("tilt", 4), 0.2), "15": (("drift", (-0.6, 0, 0)), 0), "16": (("tilt", -4), 0.2), "17": (("push", 0.04), 0.2),
    "18": (("hold",), 0.8), "19": (("push", 0.03), 0.2), "20": (("drift", (0.8, 0, 0)), 0), "21": (("hold",), 0),
    "22": (("push", 0.03), 0.2), "23": (("push", 0.05), 0.2), "24": (("tilt", 3), 0.2), "25": (("push", 0.03), 0.3),
    "26": (("push", 0.05), 0), "28": (("drift", (1.5, 0, 0)), 0), "29": (("push", 0.04), 0.3), "30": (("push", 0.04), 0.2),
    "31": (("push", 0.05), 0), "32": (("hold",), 0), "33": (("push", 0.12), 0), "34": (("drift", (0.15, 0, 0)), 0.3),
    "35": (("push", 0.04), 0.3), "36": (("push", 0.05), 0.2), "37": (("push", 0.03), 0.4), "38": (("push", 0.05), 0.2),
    "39": (("push", 0.05), 0.2), "41": (("orbit", 14), 0), "42": (("push", 0.12), 0), "43": (("drift", (0.3, 0, 0)), 0),
    "44": (("push", 0.04), 0.3), "45": (("push", 0.06), 0.2),
}


def camera_move(cam, move, handheld=0.0, seed=3):
    D = dur(); n = nframes()
    cam.rotation_mode = 'QUATERNION'
    loc0 = cam.location.copy(); q0 = cam.matrix_world.to_quaternion()
    fwd = q0 @ Vector((0, 0, -1)); right = q0 @ Vector((1, 0, 0)); up = q0 @ Vector((0, 1, 0))
    dof = cam.data.dof.use_dof
    dist = cam.data.dof.focus_distance if dof and cam.data.dof.focus_distance > 0 else 6.0
    if dof and cam.data.dof.focus_object is not None:
        dist = (cam.data.dof.focus_object.matrix_world.to_translation() - loc0).length
    tgt0 = loc0 + fwd * dist
    rng = np.random.default_rng(seed); ph = rng.uniform(0, 6.28, 4)
    _interp('BEZIER')
    kind = move[0]
    for i in range(n + 1):
        t = i / FPS; u = ease(t / max(D, 1e-3))
        loc = loc0.copy(); q = q0.copy()
        if kind == "push":
            loc = loc0 + fwd * dist * move[1] * u
        elif kind == "pull":
            loc = loc0 - fwd * dist * move[1] * u
        elif kind == "drift":
            d = move[1]; off = right * d[0] + up * d[1] + fwd * d[2]
            loc = loc0 + off * u
            q = (tgt0 - loc0).rotation_difference(tgt0 + off * u * 0.6 - loc) @ q0
        elif kind == "rise":
            loc = loc0 + Vector((0, 0, move[1] * u))
            q = (tgt0 - loc0).rotation_difference(tgt0 + Vector((0, 0, move[1] * u * 0.5)) - loc) @ q0
        elif kind == "tilt":
            q = Quaternion(right, math.radians(move[1] * u)) @ q0
        elif kind == "pan":
            q = Quaternion((0, 0, 1), math.radians(move[1] * u)) @ q0
        elif kind == "orbit":
            R = Quaternion((0, 0, 1), math.radians(move[1] * u))
            loc = tgt0 + R @ (loc0 - tgt0); q = R @ q0
        if handheld:
            r = q @ Vector((1, 0, 0)); uu = q @ Vector((0, 1, 0)); ff = q @ Vector((0, 0, -1))
            q = Quaternion(uu, math.radians(handheld * 0.18 * math.sin(0.7 * 6.28 * t + ph[0]))) @ \
                Quaternion(r, math.radians(handheld * 0.14 * math.sin(0.53 * 6.28 * t + ph[1]))) @ \
                Quaternion(ff, math.radians(handheld * 0.25 * math.sin(0.37 * 6.28 * t + ph[3]))) @ q
        if cam.parent is not None:
            Mw = Matrix.LocRotScale(loc, q, Vector((1, 1, 1)))
            Ml = cam.parent.matrix_world.inverted() @ Mw
            cam.location = Ml.to_translation(); cam.rotation_quaternion = Ml.to_quaternion()
        else:
            cam.location = loc; cam.rotation_quaternion = q
        cam.keyframe_insert("location", frame=1 + i); cam.keyframe_insert("rotation_quaternion", frame=1 + i)
        if dof and cam.data.dof.focus_object is None and kind in ("push", "pull"):
            cam.data.dof.focus_distance = max(0.2, dist - (loc - loc0).dot(fwd))
            cam.data.dof.keyframe_insert("focus_distance", frame=1 + i)


# ----------------------------------------------------------------------------- sea, ships, light
SEA = {   # shot: ship motion for vessels afloat (pier shots: moored alongside, no motion of their own)
    "anchor": dict(heave=0.10, roll=1.0, pitch=0.4, period=7.5),
    "sail": dict(heave=0.18, roll=1.6, pitch=0.6, period=7.0),
    "boat": dict(heave=0.12, roll=3.0, pitch=1.5, period=4.2),
}
AT_ANCHOR = {"21", "22", "24", "25", "26"}
SKIP = ("Ocean", "FarSea", "far_sea", "Sun", "SeaHaze", "water", "sky", "land", "island", "air", "haze", "dust",
        "World", "harbour", "river", "pier", "street", "smoke", "sea_", "Sea_", "SeaPlane", "SeaSurface")


def _inside(root, p, pad):
    import ship
    q = root.matrix_world.inverted() @ Vector(p)
    if root.name == "MC_root":
        return abs(q.x) < ship.L / 2 + pad and abs(q.y) < ship.B / 2 + pad and -4 < q.z < 30
    return False


def _fits(root, o, pad=2.0):
    """The whole object (all bounding-box corners, children included for rigs) lies on the ship: land, sea and harbour
    meshes whose origin happens to fall inside her box are not taken along."""
    objs = [o] + ([c for c in o.children_recursive if c.type == 'MESH'] if o.type == 'ARMATURE' else [])
    for ob in objs:
        if ob.type not in ('MESH', 'CURVE', 'ARMATURE'):
            continue
        for c in ob.bound_box:
            if not _inside(root, ob.matrix_world @ Vector(c), pad):
                return False
    return True


def ship_motion(root, heave=0.18, roll=1.6, pitch=0.6, period=7.0, seed=0, travel=None):
    base = root.matrix_world.copy(); D = dur()
    rng = np.random.default_rng(seed); p = rng.uniform(0, 6.28, 3); w = 2 * math.pi / period
    root.rotation_mode = 'XYZ'
    _interp('BEZIER')
    for i in range(0, nframes() + 3, 2):
        t = i / FPS
        T = Matrix.Identity(4)
        if travel is not None:
            T = Matrix.Translation(Vector(travel) * (t / D))
        R = Matrix.Translation((0, 0, heave * math.sin(w * t + p[0]))) @ \
            Matrix.Rotation(math.radians(roll * math.sin(w * 0.83 * t + p[1])), 4, 'X') @ \
            Matrix.Rotation(math.radians(pitch * math.sin(w * 1.21 * t + p[2])), 4, 'Y')
        root.matrix_world = T @ base @ R
        root.keyframe_insert("location", frame=1 + i); root.keyframe_insert("rotation_euler", frame=1 + i)
    root.matrix_world = base


def ocean_time(speed=1.0):
    D = dur(); _interp('LINEAR')
    for o in bpy.data.objects:
        md = o.modifiers.get("Ocean") if o.type == 'MESH' else None
        if md is None:
            continue
        t0 = md.time
        md.keyframe_insert("time", frame=1)
        md.time = t0 + D * speed; md.keyframe_insert("time", frame=1 + nframes())
        md.time = t0
    _interp('BEZIER')


def _adopt(root, cam, pad=0.6):
    """Parent to root what stands on the ship (people, props, lanterns), and the camera when it is aboard."""
    aboard = _inside(root, cam.location, 1.2)
    for o in list(bpy.data.objects):
        if o.parent is not None or o is root or o.name.endswith("_root") or o.type == 'LIGHT' and not _inside(root, o.location, 0.0):
            continue
        if any(o.name.startswith(k) or o.name.lower().startswith(k.lower()) for k in SKIP):
            continue
        if o is cam and not aboard:
            continue
        if o is cam or (_inside(root, o.matrix_world.to_translation(), pad) and _fits(root, o)):
            mw = o.matrix_world.copy(); o.parent = root; o.matrix_world = mw
    bpy.context.view_layer.update()


def retag():
    """Hand points for clipcheck from the rigs as they are on this frame (people move with the ship and breathe)."""
    rigs = {}
    for o in bpy.data.objects:
        if "person" in o and o.type == 'MESH':
            r = o.parent
            while r is not None and r.type != 'ARMATURE':
                r = r.parent
            if r is not None:
                rigs.setdefault(o["person"], r)
    for name, arm in rigs.items():
        hp = []
        for sd in ("L", "R"):
            for b in (f"wrist.{sd}", f"finger3-1.{sd}", f"finger3-3.{sd}"):
                if b in arm.pose.bones:
                    hp += list(arm.matrix_world @ arm.pose.bones[b].head)
        for o in bpy.data.objects:
            if o.get("person") == name:
                o["hands"] = hp


def run(shot, cine=None, bloom=0.3):
    sc = bpy.context.scene; cam = sc.camera
    n = nframes(); sc.frame_start = 1; sc.frame_end = n; sc.render.fps = FPS
    bpy.context.view_layer.update()
    roots = [o for o in bpy.data.objects if o.type == 'EMPTY' and o.name.endswith("_root") and not o.name.startswith("MCmodel")]
    afloat = shot in AT_ANCHOR or bpy.data.objects.get("Ocean") is not None and shot not in ("01", "04", "06", "15", "20")
    mc = bpy.data.objects.get("MC_root")
    if mc is not None:                       # a boat on her falls alongside (43) rides with the ship, not on its own
        for r in list(roots):
            if r is not mc and r.name.startswith("yawl") and (r.matrix_world.to_translation() - mc.matrix_world.to_translation()).length < 12:
                mw = r.matrix_world.copy(); r.parent = mc; r.matrix_world = mw; roots.remove(r)
    order = sorted(roots, key=lambda r: r.name == "MC_root")          # boats first, the ship last
    for r in order:
        if r.name == "MC_root":
            if afloat:
                _adopt(r, cam)
                ship_motion(r, seed=7, **(SEA["anchor"] if shot in AT_ANCHOR else SEA["sail"]))
            elif shot == "20":                                       # the tug tows her off the pier
                ship_motion(r, heave=0.02, roll=0.3, pitch=0.1, period=8.0, seed=7,
                            travel=r.matrix_world.to_quaternion() @ Vector((1.6, 0, 0)))
        elif r.name.startswith("tug") and shot == "20":
            ship_motion(r, heave=0.04, roll=0.8, pitch=0.4, period=5.0, seed=3,
                        travel=r.matrix_world.to_quaternion() @ Vector((1.6, 0, 0)))
        elif afloat or r.name.startswith(("pilotboat", "yawl")):
            ship_motion(r, seed=sum(map(ord, r.name)) % 97, **SEA["boat"])
    ocean_time()
    sun = bpy.data.objects.get("Sun")
    if shot == "32" and sun is not None:                              # time passes: the dawn sun climbs and swings
        sun.rotation_mode = 'XYZ'; r0 = sun.rotation_euler.copy(); _interp('LINEAR')
        sun.keyframe_insert("rotation_euler", frame=1)
        sun.rotation_euler = (r0.x - math.radians(6), r0.y, r0.z + math.radians(10)); sun.keyframe_insert("rotation_euler", frame=1 + n)
        sun.rotation_euler = r0; _interp('BEZIER')
    bpy.context.view_layer.update()
    move, hh = MOVES.get(shot, (("push", 0.04), 0.2))
    if move[0] != "hold" or hh:
        camera_move(cam, move if move[0] != "hold" else ("push", 0.0), handheld=hh)
    # clipcheck: first, middle, last frame; zero clips
    if any("person" in o for o in bpy.data.objects):
        import clipcheck
        import stage as S
        bad = 0
        for f in sorted({1, max(1, n // 2), n}):
            sc.frame_set(f); bpy.context.view_layer.update()
            retag()
            bad += len(S.clip(f"{shot}_f{f:04d}") or [])
        print(f"CLIPRESULT {shot} {bad}", flush=True)
        if bad and os.environ.get("CLIP_STRICT", "1") == "1":
            print("ABORT: clipping in", shot, flush=True); sys.exit(2)
        sc.frame_set(1)
    import grade as G
    G.add_grade(sc, bloom=bloom, look="cinematic", cine=cine)
    sc.render.use_motion_blur = os.environ.get("MBLUR", "1") == "1"; sc.render.motion_blur_shutter = 0.4
    for o in bpy.data.objects:
        if o.type == 'MESH' and (o.modifiers.get("Ocean") is not None or o.name.startswith(("FarSea", "far_sea"))):
            o.cycles.use_motion_blur = False
    sc.render.use_persistent_data = True
    if os.environ.get("EXPORT"):
        sys.path.insert(0, os.path.join(_P2, "tools"))
        import farm_export
        farm_export.export(os.environ["EXPORT"], shot)
        print("RENDERED export", shot, flush=True)
        return
    out = os.path.join(_P2, "out", "anim", shot); os.makedirs(out, exist_ok=True)
    sc.render.filepath = os.path.join(out, "f")
    sc.frame_start = int(os.environ.get("FSTART", 1)); sc.frame_end = int(os.environ.get("FEND", n))
    bpy.ops.render.render(animation=True)
    print("RENDERED anim", shot, sc.frame_start, sc.frame_end, flush=True)
