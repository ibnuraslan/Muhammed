"""Poses for Part 2 (chairs, tables, writing, holding), on top of the shared poses.py.
Rig frame: the person faces -Y, their left is +X, feet on z = 0. Targets given in world space are brought into the
rig frame with Mi = place.inverted() before posing; finish_live() then moves the posed rig to `place`."""
import math
from mathutils import Vector, Matrix
import human as H
import poses as P


def chain(h, pairs):
    for b, d in pairs:
        h.aim(b, Vector(d))


def sit_chair(h, lean=6.0, knee_out=0.08, shin_fwd=0.05, feet=0.0):
    """Upright on a chair: thighs level and forward, shins down, a slight lean from the hips."""
    for sd, sg in H.SIDE.items():
        chain(h, [(f"upperleg01.{sd}", (knee_out * sg, -1, -0.04)), (f"upperleg02.{sd}", (knee_out * sg, -1, -0.04)),
                  (f"lowerleg01.{sd}", (0.02 * sg, -shin_fwd - feet * (0.3 if sd == "L" else -0.2), -1)),
                  (f"lowerleg02.{sd}", (0.02 * sg, -shin_fwd - feet * (0.3 if sd == "L" else -0.2), -1)),
                  (f"foot.{sd}", (0.08 * sg, -1, -0.25))])
    for b, k in (("spine05", 0.1), ("spine04", 0.3), ("spine03", 0.3), ("spine02", 0.2), ("spine01", 0.1)):
        h.rot(b, (1, 0, 0), lean * k)


def seat_offset(h, seat_z):
    """Translation (rig frame z) that puts the sitting bones on a seat at height seat_z."""
    hip = (h.bone_head("upperleg01.L") + h.bone_head("upperleg01.R")) / 2
    return seat_z + 0.085 - hip.z, hip


def sit_place(h, seat_world, yaw_deg, seat_z):
    """World matrix for a seated rig: hips over seat_world (x, y), facing yaw (0 = facing -Y)."""
    dz, hip = seat_offset(h, seat_z)
    R = Matrix.Rotation(math.radians(yaw_deg), 4, 'Z')
    hip_xy = Vector((hip.x, hip.y + 0.02, 0))
    return Matrix.Translation(Vector((seat_world[0], seat_world[1], dz))) @ R @ Matrix.Translation(-hip_xy)


def stand_place(pos, yaw_deg, z=0.0):
    return Matrix.Translation(Vector((pos[0], pos[1], z))) @ Matrix.Rotation(math.radians(yaw_deg), 4, 'Z')


def write(h, Mi, paper_w, side="R", other_on_table=None, lean=20.0, head_pitch=26.0):
    """Seated, writing: the pen hand on the paper (fingers in a pen grip), the other forearm resting on the table."""
    sg = H.SIDE[side]; os_ = "L" if side == "R" else "R"; so = H.SIDE[os_]
    for b, k in (("spine04", 0.35), ("spine03", 0.35), ("spine02", 0.3)):
        h.rot(b, (1, 0, 0), lean * k)
    P.head(h, pitch=head_pitch, yaw=-4 * sg)
    tgt = Mi @ Vector(paper_w)
    P.hand_reach(h, side, tgt + Vector((0.02 * sg, 0.06, 0.075)), elbow=(0.9 * sg, 0.4, 0.45))
    h.aim(f"wrist.{side}", Vector((-0.35 * sg, -0.8, -0.45)))
    pen_grip(h, side)
    if other_on_table is not None:
        P.hand_reach(h, os_, Mi @ Vector(other_on_table) + Vector((0, 0.03, 0.05)), elbow=(0.9 * so, 0.5, 0.45))
        h.aim(f"wrist.{os_}", Vector((0.25 * so, -0.95, -0.2)))      # palm down, hand flat on the page
        P.rest_hand(h, os_, curl=8)


def pen_grip(h, side):
    """Thumb, index and middle pinched round a pen; ring and little finger curled under."""
    sg = H.SIDE[side]
    for k, d in ((1, 30), (2, 35), (3, 25)):
        h.rot(f"finger2-{k}.{side}", (1, 0, 0), d)
        h.rot(f"finger3-{k}.{side}", (1, 0, 0), d + 8)
    for f in (4, 5):
        for k in (1, 2, 3):
            h.rot(f"finger{f}-{k}.{side}", (1, 0, 0), 62 if k == 1 else 70)
    h.rot(f"finger1-2.{side}", (0, 0, sg), 18); h.rot(f"finger1-3.{side}", (1, 0, 0), 15)


def hands_in_lap(h, Mi=None, lap_w=None):
    for sd, sg in H.SIDE.items():
        knee = (h.bone_head(f"upperleg01.{sd}") + h.bone_tail(f"upperleg02.{sd}")) / 2
        tgt = knee + Vector((-0.06 * sg, -0.05, 0.11))
        P.hand_reach(h, sd, tgt, elbow=(0.6 * sg, 0.6, -0.5))
        h.aim(f"wrist.{sd}", Vector((-0.6 * sg, -0.75, -0.2)))
        P.rest_hand(h, sd, curl=26)


def hold_up(h, side, tgt_rig, elbow=None):
    sg = H.SIDE[side]
    P.hand_reach(h, side, tgt_rig, elbow=elbow or (0.7 * sg, 0.3, -0.6))
    P.grip(h, side, 0.75)


def hand_to_temple(h, side="R"):
    """Fingertips pressed to the temple, elbow out on the table: weary."""
    sg = H.SIDE[side]
    eye = h.bone_head(f"eye.{side}") if f"eye.{side}" in h.arm.pose.bones else h.bone_head("head") + Vector((0.03 * sg, -0.08, 0.1))
    tgt = eye + Vector((0.06 * sg, 0.06, -0.06))
    P.hand_reach(h, side, tgt, elbow=(0.6 * sg, -0.5, -0.8))
    h.aim(f"wrist.{side}", Vector((-0.3 * sg, 0.2, 1.0)))
    P.rest_hand(h, side, curl=14)


def yaw_to(frm, to):
    """stand_place yaw (deg) that turns a rig (rest: facing -Y) at `frm` to face `to` (xy only)."""
    dx, dy = to[0] - frm[0], to[1] - frm[1]
    return math.degrees(math.atan2(dx, -dy))


def feet_to_floor(h, Mw, floor_z=0.0, tries=None):
    """Seated: swing the shins (about the knee) until the ankles sit at their standing height above the floor.
    Mw = the world matrix the rig will be placed with."""
    ank0 = h.joint("foot.L____head")[2]                 # rest ankle height above the sole
    for sd, sg in H.SIDE.items():
        best = None
        for fwd in [i * 0.05 for i in range(0, 30)]:
            d = Vector((0.02 * sg, -fwd, -1))
            h.aim(f"lowerleg01.{sd}", d); h.aim(f"lowerleg02.{sd}", d)
            h.aim(f"foot.{sd}", Vector((0.08 * sg, -1, -0.25)))
            z = (Mw @ h.bone_head(f"foot.{sd}")).z - ank0 - floor_z
            if best is None or abs(z) < abs(best[1]):
                best = (fwd, z)
            if z > 0.004:
                break
        d = Vector((0.02 * sg, -best[0], -1))
        h.aim(f"lowerleg01.{sd}", d); h.aim(f"lowerleg02.{sd}", d)
        h.aim(f"foot.{sd}", Vector((0.08 * sg, -1, -0.25)))
        if best[1] > 0.008:          # legs too short for the chair: point the toes down to the floor
            for k in range(1, 12):
                h.aim(f"foot.{sd}", Vector((0.08 * sg, -1, -0.25 - 0.18 * k)))
                toe = Mw @ h.bone_tail(f"foot.{sd}")
                if toe.z - floor_z < 0.03:
                    break


def hand_low(h, side, Mw):
    """Lowest world z of the skin of one hand (vertices weighted to its wrist / finger / metacarpal bones), posed."""
    import bpy, numpy as np
    body = h.body
    names = [g.name for g in body.vertex_groups if g.name.endswith("." + side) and
             g.name.split(".")[0].startswith(("wrist", "finger", "metacarpal"))]
    gi = {body.vertex_groups[n].index for n in names}
    idx = [v.index for v in body.data.vertices if any(g.group in gi and g.weight > 0.5 for g in v.groups)]
    sub = [m for m in body.modifiers if m.type == 'SUBSURF']
    for m in sub:
        m.show_viewport = False
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    oe = body.evaluated_get(dg); me = oe.to_mesh()
    z = min((Mw @ (oe.matrix_world @ me.vertices[i].co)).z for i in idx)
    oe.to_mesh_clear()
    for m in sub:
        m.show_viewport = True
    return z


def settle_hand(h, side, pose_fn, Mw, surface_z, gap=0.002, tries=14):
    """pose_fn(dz) poses the hand with its target raised by dz (rig frame); find dz so the hand's lowest skin point
    rests `gap` above surface_z (world): touching, not floating, not through."""
    import os
    dz = 0.0; best = None
    for i in range(tries):
        pose_fn(dz)
        err = hand_low(h, side, Mw) - (surface_z + gap)
        if os.environ.get("SETTLEDBG"):
            print("SETTLE", side, i, round(dz, 4), round(err, 4), flush=True)
        if best is None or abs(err) < abs(best[1]):
            best = (dz, err)
        if abs(err) < 0.0012:
            break
        dz -= 0.55 * err                 # damped: raising the target also moves the elbow and turns the hand
    if abs(best[1]) >= 0.0012:
        pose_fn(best[0])
        # the arm solution jumps near contact: finish with the wrist alone (continuous), tilting the hand
        # about its side axis until the lowest skin point meets the surface
        import bpy
        pb = h.arm.pose.bones[f"wrist.{side}"]; base = pb.matrix_basis.copy()
        d = (h.bone_tail(f"wrist.{side}") - h.bone_head(f"wrist.{side}")).normalized()
        ax = d.cross(Vector((0, 0, 1))).normalized()
        cand = None
        for step in range(0, 41):
            for sgn in (1, -1):
                deg = sgn * step * 0.5
                pb.matrix_basis = base; bpy.context.view_layer.update()
                if deg:
                    h.rot(f"wrist.{side}", ax, deg)
                e = hand_low(h, side, Mw) - (surface_z + gap)
                if cand is None or abs(e) < abs(cand[1]):
                    cand = (deg, e)
            if abs(cand[1]) < 0.0012:
                break
        pb.matrix_basis = base; bpy.context.view_layer.update()
        if cand[0]:
            h.rot(f"wrist.{side}", ax, cand[0])
        if os.environ.get("SETTLEDBG"):
            print("SETTLE wrist", side, cand, flush=True)
    return best[0]


def _hand_pts(h, side, Mw):
    import bpy, numpy as np
    body = h.body
    if not hasattr(h, "_hidx"):
        h._hidx = {}
    if side not in h._hidx:
        gi = {g.index for g in body.vertex_groups if g.name.endswith("." + side) and
              g.name.split(".")[0].startswith(("wrist", "finger", "metacarpal"))}
        th = {g.index for g in body.vertex_groups if g.name.endswith("." + side) and g.name.startswith("finger1")}
        h._hidx[side] = ([v.index for v in body.data.vertices if any(g.group in gi and g.weight > 0.5 for g in v.groups)],
                         [v.index for v in body.data.vertices if any(g.group in th and g.weight > 0.5 for g in v.groups)])
    idx, tidx = h._hidx[side]
    sub = [m for m in body.modifiers if m.type == 'SUBSURF']
    for m in sub:
        m.show_viewport = False
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    oe = body.evaluated_get(dg); me = oe.to_mesh()
    co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    oe.to_mesh_clear()
    for m in sub:
        m.show_viewport = True
    return co[idx], co[tidx]


def flat_hand(h, side, thumb_dir, fwd=(0, -1), pitches=(-0.45, -0.3, -0.18, -0.08, 0.0, 0.1, 0.2, 0.32, 0.45),
              rolls=range(-180, 180, 15)):
    """Lay the hand flat: search the wrist's pitch (aim along fwd, rig frame) and its roll about its own axis for the
    pose whose hand skin is flattest (least height), palm down with the thumb toward thumb_dir. Fingers posed first."""
    import os
    import numpy as np
    pb = h.arm.pose.bones[f"wrist.{side}"]
    best = None
    for pz in pitches:
        h.aim(f"wrist.{side}", Vector((fwd[0], fwd[1], pz)))
        base = pb.matrix_basis.copy()
        for deg in rolls:
            pb.matrix_basis = base
            ax = (h.bone_tail(f"wrist.{side}") - h.bone_head(f"wrist.{side}")).normalized()
            h.rot(f"wrist.{side}", ax, deg)
            Pp, T = _hand_pts(h, side, Matrix.Identity(4))
            span = float(Pp[:, 2].max() - Pp[:, 2].min())
            t = T.mean(0) - Pp.mean(0)
            ok = float(np.dot(t[:2], np.array(thumb_dir[:2]))) > 0
            score = span + (0 if ok else 1.0)
            if best is None or score < best[0]:
                best = (score, pz, deg, pb.matrix_basis.copy())
    pb.matrix_basis = best[3]
    import bpy
    bpy.context.view_layer.update()
    if os.environ.get("FLATDBG"):
        print("FLATBEST", round(best[0], 4), best[1], best[2], flush=True)
    return best[:3]


# palm normal of the MakeHuman hand in the wrist bone's own frame (measured: plane of the metacarpals, toward the curl)
PALM_LOCAL = {"L": Vector((-0.886, 0.263, -0.382)), "R": Vector((0.886, 0.263, -0.382))}


def orient_hand(h, side, fwd, palm):
    """Turn the hand (wrist bone, rig frame) so it points along fwd (wrist -> knuckles) with the palm facing palm."""
    import bpy
    bpy.context.view_layer.update()
    pb = h.arm.pose.bones[f"wrist.{side}"]
    M0 = pb.matrix.copy(); R0 = M0.to_3x3().normalized(); head = M0.to_translation()
    kn = [h.bone_head(f"finger{k}-1.{side}") for k in (2, 3, 4, 5) if f"finger{k}-1.{side}" in h.arm.pose.bones]
    f_l = (R0.inverted() @ ((sum(kn, Vector()) / len(kn)) - head)).normalized()
    n_l = PALM_LOCAL[side].normalized()
    a2 = (n_l - f_l * n_l.dot(f_l)).normalized(); a3 = f_l.cross(a2)
    b1 = Vector(fwd).normalized(); b2 = (Vector(palm) - b1 * Vector(palm).dot(b1)).normalized(); b3 = b1.cross(b2)
    A = Matrix((f_l, a2, a3)).transposed(); B = Matrix((b1, b2, b3)).transposed()
    R = B @ A.transposed()
    pb.matrix = Matrix.Translation(head) @ R.to_4x4()
    bpy.context.view_layer.update()


def relaxed_flat(h, side, curl=6):
    """Fingers almost straight, a little apart, thumb alongside: a hand at rest on a surface."""
    sg = 1 if side == "L" else -1
    for f in (2, 3, 4, 5):
        for k, d in ((1, curl), (2, curl + 4), (3, curl + 2)):
            b = f"finger{f}-{k}.{side}"
            if b in h.arm.pose.bones:
                h.rot(b, h.bone_tail(b) - h.bone_head(b), 0)      # no-op keeps API symmetrical
    import poses as P
    P.rest_hand(h, side, curl=curl)


def pen_grip2(h, side):
    """A writer's grip: thumb, index and middle finger meet on the pen; ring and little finger curled under."""
    import poses as P
    P.rest_hand(h, side, curl=0)
    sg = 1 if side == "L" else -1
    for k, d in ((1, 28), (2, 30), (3, 18)):
        h.rot(f"finger2-{k}.{side}", (1, 0, 0), d)
    for k, d in ((1, 38), (2, 40), (3, 25)):
        h.rot(f"finger3-{k}.{side}", (1, 0, 0), d)
    for f in (4, 5):
        for k, d in ((1, 62), (2, 75), (3, 55)):
            h.rot(f"finger{f}-{k}.{side}", (1, 0, 0), d)
    h.rot(f"finger1-2.{side}", (0, 0, sg), 14); h.rot(f"finger1-3.{side}", (1, 0, 0), 12)


def palm_normal(h, side):
    import bpy
    bpy.context.view_layer.update()
    R = h.arm.pose.bones[f"wrist.{side}"].matrix.to_3x3().normalized()
    return (R @ PALM_LOCAL[side]).normalized()


def curl(h, bone, deg, palm):
    """Bend a finger bone toward the palm by deg (about its own knuckle axis)."""
    d = (h.bone_tail(bone) - h.bone_head(bone)).normalized()
    ax = d.cross(palm)
    if ax.length < 1e-4:
        return
    h.rot(bone, ax.normalized(), deg)


def hand_shape(h, side, fingers, thumb=(0, 0, 0)):
    """fingers: {2: (d1, d2, d3), 3: ..., 4: ..., 5: ...} curl per joint (deg) toward the palm, from the hand's
    straight rest; thumb: curl of finger1-1..3."""
    import poses as P
    P.rest_hand(h, side, curl=0)
    pn = palm_normal(h, side)
    for f, ds in fingers.items():
        for k, d in enumerate(ds, 1):
            b = f"finger{f}-{k}.{side}"
            if b in h.arm.pose.bones and d:
                curl(h, b, d, pn)
    for k, d in enumerate(thumb, 1):
        b = f"finger1-{k}.{side}"
        if b in h.arm.pose.bones and d:
            curl(h, b, d, pn)
