"""Romand film: animation layer on top of the storyboard shot builders.
  cam_move(kind, frames, amt)   camera moves from the shot list: push, pull, crane_up, crane_down, orbit, track, whip, creep
  walk(fig, f0, f1, ...)        planted-foot walk (ported from thumbnails_am/scenes/style_anim.py, upright): the stance
                                foot is pinned every frame and the root moves by its drift, so feet never slide
  key_path(obj, f0, f1, p0, p1) eased move of any object (car rolling, notes sliding)
  clip_check(f0, f1)            per-frame BVH overlap of every figure against every other mesh: 0 clipping allowed
Every shot keeps its storyboard composition as the move's START frame unless noted."""
import math, random, json, os
import bpy
import numpy as np
from mathutils import Vector, Matrix, Quaternion
from mathutils.bvhtree import BVHTree
import rk

X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))


def ease(t, kind="inout"):
    t = max(0.0, min(1.0, t))
    if kind == "out":
        return 1 - (1 - t) ** 3
    if kind == "in":
        return t ** 3
    if kind == "lin":
        return t
    return t * t * (3 - 2 * t)


# ------------------------------------------------------------------------------------------------- camera
def _cam_frame():
    cam = bpy.context.scene.camera
    bpy.context.view_layer.update()
    loc = cam.matrix_world.translation.copy()
    fwd = (cam.matrix_world.to_3x3() @ Vector((0, 0, -1))).normalized()
    dist = cam.data.dof.focus_distance if cam.data.dof.use_dof and cam.data.dof.focus_distance > 0 else 8.0
    return cam, loc, fwd, dist


def _look(cam, loc, tgt, roll=0.0):
    q = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y')
    if roll:
        q = q @ Quaternion((0, 0, 1), math.radians(roll))
    cam.rotation_mode = 'QUATERNION'; cam.location = loc; cam.rotation_quaternion = q


def cam_move(kind, f0, f1, amt=None, target_dist=None, easing="inout", seed=0):
    """Animate the scene camera from its current (storyboard) placement. amt meaning per kind:
    push/pull: distance factor at the end (0.8 = 20 % closer) | crane_up/down: degrees of elevation change |
    orbit: degrees of azimuth (+ = counter-clockwise) | track: metres along the camera's right vector |
    whip: degrees of yaw over the first 6 frames (starts off-target, lands on it) | creep: push with handheld noise."""
    cam, loc, fwd, dist = _cam_frame()
    d = target_dist or dist
    tgt = loc + fwd * d
    right = fwd.cross(Z).normalized()
    rng = random.Random(seed)
    frames = list(range(f0, f1 + 1))
    for f in frames:
        t = (f - f0) / max(1, f1 - f0); e = ease(t, easing)
        L, T, roll = loc.copy(), tgt.copy(), 0.0
        if kind in ("push", "pull", "creep"):
            k = 1 + ((amt or (0.85 if kind != "pull" else 1.2)) - 1) * e
            L = tgt + (loc - tgt) * k
            if kind == "creep":
                L += Vector((math.sin(f * 0.37 + seed) * 0.03, math.sin(f * 0.23 + 1) * 0.02, math.sin(f * 0.31 + 2) * 0.02))
                roll = math.sin(f * 0.19) * 0.6
        elif kind in ("crane_up", "crane_down"):
            a = math.radians((amt or 12) * (1 if kind == "crane_up" else -1)) * e
            v = loc - tgt; ax = v.cross(Z).normalized()
            L = tgt + Matrix.Rotation(-a, 3, ax) @ v
        elif kind == "orbit":
            a = math.radians(amt or 15) * e
            L = tgt + Matrix.Rotation(a, 3, 'Z') @ (loc - tgt)
        elif kind == "track":
            L = loc + right * (amt or 1.0) * e; T = tgt + right * (amt or 1.0) * e
        elif kind == "whip":
            tw = ease((f - f0) / 6.0, "out")
            yaw = math.radians(amt or 35) * (1 - tw)
            T = tgt + (Matrix.Rotation(yaw, 3, 'Z') @ (tgt - loc)) - (tgt - loc)
            L = loc + (tgt - loc) * 0.06 * e
        _look(cam, L, T, roll)
        cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_quaternion", frame=f)
    # keep focus on the subject during pushes
    if cam.data.dof.use_dof:
        for f in (f0, f1):
            t = (f - f0) / max(1, f1 - f0)
            k = 1 + ((amt or 0.85) - 1) * ease(t) if kind in ("push", "pull", "creep") else 1.0
            cam.data.dof.focus_distance = d * k; cam.data.dof.keyframe_insert("focus_distance", frame=f)


# ------------------------------------------------------------------------------------------------- objects
def key_path(obj, f0, f1, p0, p1, easing="inout", rot0=None, rot1=None):
    for f in range(f0, f1 + 1):
        e = ease((f - f0) / max(1, f1 - f0), easing)
        obj.location = Vector(p0).lerp(Vector(p1), e); obj.keyframe_insert("location", frame=f)
        if rot0 is not None:
            obj.rotation_euler.z = rot0 + (rot1 - rot0) * e; obj.keyframe_insert("rotation_euler", frame=f)


def key_value(obj, path, index, f0, f1, v0, v1, easing="inout"):
    for f in range(f0, f1 + 1):
        e = ease((f - f0) / max(1, f1 - f0), easing)
        getattr(obj, path)[index] = v0 + (v1 - v0) * e
        obj.keyframe_insert(path, index=index, frame=f)


# ------------------------------------------------------------------------------------------------- walk (planted feet)
LEGS = (("L", "upperleg_l_074", "lowerleg_l_075", "foot_l_076", "upperarm_l_024", "lowerarm_l_025"),
        ("R", "upperleg_r_081", "lowerleg_r_082", "foot_r_083", "upperarm_r_049", "lowerarm_r_050"))


def _walk_pose(arm, Rh, phase, stride, swing, carry=False):
    for pb in arm.pose.bones:
        pb.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()
    Xc, Yc = Rh @ X, Rh @ Y
    rk._rot(arm, "spine_01_03", Xc, 3); rk._rot(arm, "neck_06", Xc, 4)
    for sd, ul, ll, ft, ua, la in LEGS:
        u = (phase + (0.0 if sd == "L" else 0.5)) % 1.0
        if u < 0.5:
            hip = stride * (1.0 - 4.0 * u); knee = 6.0 + 4.0 * math.sin(math.pi * u * 2.0); foot = hip - knee
        else:
            s = (u - 0.5) / 0.5
            hip = -stride + 2.0 * stride * (0.5 - 0.5 * math.cos(math.pi * s))
            knee = 6.0 + 50.0 * math.sin(math.pi * min(1.0, s * 1.15)) ** 1.2
            foot = hip - knee * 0.55 + 12.0 * math.sin(math.pi * s)
        rk._rot(arm, ul, Xc, -hip - 2); rk._rot(arm, ll, Xc, knee + 2); rk._rot(arm, ft, Xc, -foot * 0.6 - 2)
        side = 1 if sd == "L" else -1
        if carry and sd == "R":
            rk._rot(arm, ua, Yc, -36); rk._rot(arm, la, Xc, -4)
        else:
            a = swing * math.sin(2 * math.pi * (u + 0.5) - math.pi / 2)
            rk._rot(arm, ua, Yc, side * 38); rk._rot(arm, ua, Xc, -a); rk._rot(arm, la, Xc, -10 - max(0, a) * 0.5)


SOLE = ("ball_l_077", "ball_r_084", "foot_end_l_078", "foot_end_r_085", "foot_l_076", "foot_r_083")


def _sole_z(arm):
    """Lowest point of the evaluated (posed) body mesh: the true sole height, toes included."""
    body = max((o for o in arm.children if o.type == 'MESH'), key=lambda o: len(o.data.vertices))
    dg = bpy.context.evaluated_depsgraph_get(); oe = body.evaluated_get(dg); me = oe.to_mesh()
    co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("co", co); oe.to_mesh_clear()
    co = co.reshape(-1, 3); Mw = np.array(oe.matrix_world)
    return float((co @ Mw[:3, :3].T + Mw[:3, 3])[:, 2].min())


def walk(fig, f0, f1, heading_deg, period=30, stride=16.0, swing=14.0, carry=False, phase0=0.0):
    """Walk the figure from its current spot along heading (0 = -Y), keyframing every frame. The stance foot is
    pinned: the pivot moves by the stance foot's drift, so there is no sliding. Returns the end location."""
    arm, pv = fig["arm"], fig["pivot"]
    pv.rotation_euler.z = math.radians(heading_deg); Rh = Matrix.Rotation(math.radians(heading_deg), 3, 'Z')
    bones = ("foot_l_076", "foot_r_083")
    plant, side = None, None
    bpy.context.view_layer.update()
    sole0 = _sole_z(arm) + 0.004  # the ground the figure stands on (+4 mm): held every frame, no sinking, no lift
    for f in range(f0, f1 + 1):
        bpy.context.scene.frame_set(f)
        phase = phase0 + (f - f0) / period
        _walk_pose(arm, Rh, phase, stride, swing, carry)
        bpy.context.view_layer.update()
        sd = 0 if (phase % 1.0) < 0.5 else 1
        ank = arm.matrix_world @ arm.pose.bones[bones[sd]].head
        if sd != side:
            side, plant = sd, ank.copy()
        else:
            dlt = plant - ank; pv.location += Vector((dlt.x, dlt.y, 0.0)); bpy.context.view_layer.update()
        dz = sole0 - _sole_z(arm)
        if abs(dz) > 1e-4:
            pv.location.z += dz; bpy.context.view_layer.update()
            if plant is not None:
                plant.z += dz
        pv.keyframe_insert("location", frame=f); pv.keyframe_insert("rotation_euler", frame=f)
        for pb in arm.pose.bones:
            pb.keyframe_insert("rotation_quaternion", frame=f); pb.keyframe_insert("location", frame=f)
    return pv.location.copy()


def hold_pose(fig, f0, f1):
    """Key the figure's current pose at the shot's ends (static but keyed, so later edits don't drift)."""
    for f in (f0, f1):
        fig["pivot"].keyframe_insert("location", frame=f)


# ------------------------------------------------------------------------------------------------- clip check
FLOORISH = ("floor", "slab", "road", "verge", "lawn", "ground", "court", "plaza", "pavement", "street", "drive", "mat", "rug")
SEATISH = ("seat", "chair", "rearseat", "sofa", "back_", "bench", "dock")


def _bvh(o, dg):
    oe = o.evaluated_get(dg); me = oe.to_mesh()
    if len(me.vertices) == 0:
        oe.to_mesh_clear(); return None, None
    co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    Mw = np.array(oe.matrix_world); w = co @ Mw[:3, :3].T + Mw[:3, 3]
    me.calc_loop_triangles()
    tri = np.empty(len(me.loop_triangles) * 3, np.int32); me.loop_triangles.foreach_get("vertices", tri)
    oe.to_mesh_clear()
    T = tri.reshape(-1, 3)
    _CEN[o.name] = w[T].mean(1)
    return BVHTree.FromPolygons(w.tolist(), T.tolist(), all_triangles=True), (w.min(0), w.max(0))


_CEN = {}


def clip_check(sid, f0, f1, out_dir, step=1, seat_allow=60, floor_allow=40):
    """Every figure part (body, clothes, egg head, skirt) against every other mesh, on every frame f0..f1.
    A figure's own parts overlap by design and are skipped. Feet on the floor / hips on a seat are contacts with a
    small allowance; anything else is clipping (> 4 triangle pairs of tolerance for coplanar touching)."""
    sc = bpy.context.scene
    figs = {pv.name: [o for o in pv.children_recursive if o.type == 'MESH' and not o.hide_render] for pv in rk.STATE["figs"]}
    for pv in rk.STATE["figs"]:
        figs[pv.name] += [o for o in bpy.data.objects if o.type == 'MESH' and o.parent and o.parent.type == 'ARMATURE'
                          and o.parent in pv.children_recursive and o not in figs[pv.name]]
    fig_objs = {o.name for v in figs.values() for o in v}
    others = [o for o in sc.objects if o.type == 'MESH' and not o.hide_render and o.name not in fig_objs and o.visible_camera
              and o.visible_shadow and not any(k in o.name for k in ("beam", "mist"))]   # light beams are not matter
    bad, contacts = [], 0
    static_cache = {}
    for f in range(f0, f1 + 1, step):
        sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
        ftrees = {}
        for pn, parts in figs.items():
            for o in parts:
                t, bb = _bvh(o, dg)
                if t:
                    ftrees[o.name] = (pn, t, bb)
        if not ftrees:
            break
        lo = np.min([v[2][0] for v in ftrees.values()], 0) - 0.3; hi = np.max([v[2][1] for v in ftrees.values()], 0) + 0.3
        otrees = {}
        for o in others:
            anim = o.animation_data is not None or (o.parent is not None and any(p.animation_data for p in [o.parent] + list(o.parent.children_recursive)[:0]))
            key = o.name
            if key in static_cache and not anim:
                t, bb = static_cache[key]
            else:
                t, bb = _bvh(o, dg)
                if not anim:
                    static_cache[key] = (t, bb)
            if t is None or (bb[1] < lo).any() or (bb[0] > hi).any():
                continue
            otrees[o.name] = (t, bb)
        names = list(ftrees)
        for i, a in enumerate(names):
            pn, ta, ba = ftrees[a]
            targets = [(b, v[0]) for b, v in otrees.items()] + [(b, ftrees[b][1]) for b in names[i + 1:] if ftrees[b][0] != pn]
            for b, tb in targets:
                ov = ta.overlap(tb); n = len(ov)
                if n == 0:
                    continue
                lb = b.lower()
                allow = floor_allow if any(k in lb for k in FLOORISH) else seat_allow if any(k in lb for k in SEATISH) else 4
                if n <= allow:
                    contacts += 1
                else:
                    c = _CEN[a][np.array([q[0] for q in ov])].mean(0)
                    bad.append(dict(frame=f, part=a, other=b, pairs=n, at=[round(float(v), 2) for v in c]))
    os.makedirs(out_dir, exist_ok=True)
    rep = dict(shot=sid, frames=[f0, f1], step=step, clipping=len(bad), contacts=contacts, bad=bad[:200])
    json.dump(rep, open(os.path.join(out_dir, sid + "_clip.json"), "w"), indent=1)
    print(f"CLIPCHECK {sid}: frames {f0}-{f1} step {step}: {len(bad)} clipping, {contacts} allowed contacts")
    for b in bad[:12]:
        print("  CLIP", b)
    return bad


def overlaps(objs_a, objs_b):
    dg = bpy.context.evaluated_depsgraph_get(); n = 0
    ta = [t for t in (_bvh(o, dg)[0] for o in objs_a) if t]
    tb = [t for t in (_bvh(o, dg)[0] for o in objs_b) if t]
    for a in ta:
        for b in tb:
            n += len(a.overlap(b))
    return n


def fig_parts(pv):
    return [o for o in pv.children_recursive if o.type == 'MESH' and not o.hide_render]


def _overlap_at(parts, o):
    dg = bpy.context.evaluated_depsgraph_get()
    tb, _ = _bvh(o, dg); cs = []
    if tb is None:
        return 0, None
    for p in parts:
        ta, _ = _bvh(p, dg)
        if ta is None:
            continue
        ov = ta.overlap(tb)
        if ov:
            cs.append(_CEN[p.name][np.array([q[0] for q in ov])])
    if not cs:
        return 0, None
    c = np.concatenate(cs)
    return len(c), Vector(c.mean(0).tolist())


def seat_fit(f, car_prefix="car", tol=4, max_steps=60, objs=None):
    """Resolve a seated figure until nothing of it intersects the seat and its surroundings (the car interior by
    default, or `objs`: chair, table, tableware, ground). Overlaps low under the hips lift them 1 cm; overlaps behind
    (a seat back) move the figure forward 1 cm; overlaps up at a roof recline the torso; overlaps ahead (dash, wheel,
    table edge, a glass) fold the forearms up and the shins back; overlaps at the sides bring the upper arms in."""
    pv, arm = f["pivot"], f["arm"]
    if objs is None:
        objs = [o for o in bpy.data.objects if o.type == 'MESH' and not o.hide_render and
                (o.name.startswith(car_prefix + "_") or "1994_405" in o.name)]
    parts = fig_parts(pv)
    R = pv.matrix_world.to_3x3().normalized(); Xc = R @ X; Yc = R @ Y; ahead = R @ Vector((0, -1, 0))
    hip0 = (arm.matrix_world @ arm.pose.bones["hip_02"].head).z
    bad = {}
    for step in range(max_steps):
        bpy.context.view_layer.update()
        bad = {}
        for o in objs:
            n, at = _overlap_at(parts, o)
            if n > tol:
                bad[o.name] = (n, at)
        if not bad:
            print("SEATFIT", pv.name, "ok after", step, "steps"); return True
        hip = arm.matrix_world @ arm.pose.bones["hip_02"].head
        moved = set()
        for nm, (n, at) in bad.items():
            rel = at - hip; fwd = rel.dot(ahead)
            if at.z > hip.z + 0.55 and fwd < 0.25 and "roof" not in moved:              # roof / header
                rk._rot(arm, "spine_01_03", Xc, -3); rk._rot(arm, "neck_06", Xc, 3); moved.add("roof")
            elif (at.z < hip.z + 0.12 or at.z < 0.08) and "lift" not in moved and hip.z < hip0 + 0.1:   # seat, floor, ground
                pv.location.z += 0.01; moved.add("lift")
            elif fwd < -0.08 and "fwd" not in moved:                                     # a seat back behind
                pv.location += ahead * 0.01; moved.add("fwd")
            elif fwd > 0.2 and "fold" not in moved:                                      # dash, wheel, table, glass
                if at.z > hip.z + 0.1:          # arms / hands up on the table or the dash
                    for b in ("lowerarm_l_025", "lowerarm_r_050"):
                        rk._rot(arm, b, Xc, -6)
                else:                            # knees / shins
                    for b in ("lowerleg_l_075", "lowerleg_r_082"):
                        rk._rot(arm, b, Xc, 3)
                moved.add("fold")
            elif "in" not in moved:
                rk._rot(arm, "upperarm_l_024", Yc, 2); rk._rot(arm, "upperarm_r_049", Yc, -2); moved.add("in")
    print("SEATFIT", pv.name, "unresolved", {k: v[0] for k, v in bad.items()}); return False


def near_objs(pv, radius=1.4, extra=()):
    """Meshes (not figures) within radius of the figure: what a seated figure must not intersect."""
    c = pv.matrix_world.translation
    figs = {o.name for p in rk.STATE["figs"] for o in p.children_recursive}
    return [o for o in bpy.context.scene.objects if o.type == 'MESH' and not o.hide_render and o.name not in figs
            and o.visible_shadow and ((o.matrix_world.translation - c).xy.length < radius or any(k in o.name for k in extra))]
