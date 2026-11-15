"""CH4 4B v2 (c4_08, 114 f): over the shoulder of an investigator in a dark suit, seated at the desk. He draws a
yellow highlighter along one clause of the code-of-conduct binder; his left hand holds the page flat, his head and
shoulders lean slightly and follow the line. Same desk, binder, clause, lamp and night mood as sc_paper2 'binder'
(the binder sits 15 cm nearer the desk edge so it is within his reach). The camera drifts in slowly.
Highlighter: tripod grip (index on top, thumb on the near side, middle finger under the barrel, ring and little
finger tucked and resting on the page)."""
import os, math
import numpy as np
import bpy
from mathutils import Vector, Matrix, Quaternion
from kit import *
from common import area_light, world_flat
from human import Human, add_asset, reset_pose, pose_sit, _world_verts, reach, ik2, rotate_bone, aim_bone
from sc_paper2 import text_page, tex_mat, plane, desk_room, lamp, DZ, GEN

EXPOSURE = 0.0
VARIANT_FOR = {"ots": "ots"}
FRAMES = 114
DY = -0.15                       # the binder (and everything on it) moves this much toward the desk edge
PAGE_ROT = math.radians(3)       # the right page tilts 3 degrees about Y (as in sc_paper2)
X0, X1 = 0.03, 0.25              # the clause: start and end x of the stroke on the right page


def page_z(x):
    """World z of the right page's top surface at x (the page is rotated +3 deg about Y around x = 0.155)."""
    return DZ + 0.044 - math.tan(PAGE_ROT) * (x - 0.155)


def binder(c):
    pg, rows = text_page(os.path.join(GEN, "coc_page_l.png"), 11, "code")
    pg2, rows2 = text_page(os.path.join(GEN, "coc_page_r.png"), 12)
    Y = 0.35 + DY
    cover = pbr("BinderCover", (0.05, 0.12, 0.28), 0.45, 0.0, **{'Coat Weight': 0.3})
    box("CoverL", (-0.17, Y, DZ + 0.026), (0.32, 0.33, 0.006), cover, bevel=0.003, rot=(0, math.radians(-3), 0))
    box("CoverR", (0.17, Y, DZ + 0.026), (0.32, 0.33, 0.006), cover, bevel=0.003, rot=(0, math.radians(3), 0))
    box("Spine", (0, Y, DZ + 0.03), (0.045, 0.33, 0.012), cover)
    ring = brushed_metal("Ring", (0.75, 0.75, 0.77), (0.15, 0.3), 0.4)
    for y in (0.25, 0.35, 0.45):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.016, minor_radius=0.0025, location=(0, Y + (y - 0.35) * 0.9, DZ + 0.048), rotation=(math.radians(90), 0, 0))
        bpy.context.active_object.data.materials.append(ring)
    for k in range(8):
        box("Stack", (0.155, Y, DZ + 0.033 + k * 0.0012), (0.29, 0.31, 0.001), pbr("PageEdge", (0.85, 0.84, 0.8), 0.8))
    plane("PageL", (-0.155, Y, DZ + 0.034), (0.29, 0.31), (0, math.radians(-3), 0), tex_mat("PgL", pg))
    plane("PageR", (0.155, Y, DZ + 0.044), (0.29, 0.31), (0, PAGE_ROT, 0), tex_mat("PgR", pg2))
    row_y = Y + 0.155 - (rows2[6] + 8) / 1754 * 0.31              # the 7th text row of the right page (the clause)
    hl = bpy.data.materials.new("Highlight"); hl.use_nodes = True
    p = hl.node_tree.nodes["Principled BSDF"]; p.inputs['Base Color'].default_value = (1.0, 0.85, 0.05, 1)
    p.inputs['Alpha'].default_value = 0.55; p.inputs['Roughness'].default_value = 0.6
    # the mark lies on the tilted page, grows from its left end (origin at X0)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(X0, row_y, page_z(X0) + 0.0004), rotation=(0, PAGE_ROT, 0))
    h = bpy.context.active_object; h.name = "HL"; h.data.materials.append(hl)
    h.data.transform(Matrix.Translation((0.5, 0, 0)))
    h.scale = (0.001, 0.009, 1)
    c.update(hl=h, row_y=row_y)


def highlighter():
    body = pbr("HLBody", (0.95, 0.8, 0.05), 0.4); dark = pbr("HLCap", (0.08, 0.08, 0.08), 0.4)
    tipm = pbr("HLTip", (0.9, 0.78, 0.25), 0.7)
    parts = [cyl("HLNose", (0, 0, 0.011), 0.0062, 0.010, dark, verts=20),
             cyl("HLTipF", (0, 0, 0.003), 0.0032, 0.007, tipm, verts=12),
             cyl("HLBarrel", (0, 0, 0.068), 0.0085, 0.106, body, verts=24),
             cyl("HLCapPost", (0, 0, 0.128), 0.0092, 0.03, dark, verts=24)]
    pen = join(parts, "Highlighter")                      # origin at the tip, local +Z up the barrel
    pen.rotation_mode = 'QUATERNION'
    return pen


def _bump(m, scale, strength, distance, stretch=(1, 1, 1), detail=8):
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.inputs['Scale'].default_value = stretch
    L.new(tc.outputs['Object'], mp.inputs['Vector'])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = detail
    L.new(mp.outputs['Vector'], nz.inputs['Vector'])
    bp = N.new("ShaderNodeBump"); bp.inputs['Strength'].default_value = strength; bp.inputs['Distance'].default_value = distance
    L.new(nz.outputs['Fac'], bp.inputs['Height'])
    nm = p.inputs['Normal'].links[0].from_node if p.inputs['Normal'].is_linked else None
    if nm is not None:
        L.new(nm.outputs['Normal'], bp.inputs['Normal'])
    L.new(bp.outputs['Normal'], p.inputs['Normal'])


def wool(m):
    """Matte dark suit wool: no sheen, low specular, a fine weave in the normal."""
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs['Roughness'].default_value = 0.82; p.inputs['Sheen Weight'].default_value = 0.0
    p.inputs['Specular IOR Level'].default_value = 0.25; p.inputs['Coat Weight'].default_value = 0.0
    _bump(m, 900, 0.25, 0.0004, stretch=(1, 1, 3))


def hair_strands(m):
    """Short hair: rougher, slightly darker, with fine strand detail (noise stretched along the head's up axis)."""
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs['Roughness'].default_value = 0.62; p.inputs['Specular IOR Level'].default_value = 0.35
    _bump(m, 140, 0.55, 0.0012, stretch=(14, 14, 1.5), detail=6)


def shirt_cuff(h, sd, mat):
    """A white shirt cuff showing past the jacket sleeve, bone-parented to the forearm so it follows every pose."""
    bpy.context.view_layer.update()
    a = h.bone_head(f"lowerarm02.{sd}"); b = h.bone_tail(f"lowerarm02.{sd}"); ax = (b - a); Lb = ax.length; ax.normalize()
    ws = _world_verts(h.suit); A = np.array(a); X = np.array(ax)
    tt = (ws - A) @ X; rr = np.linalg.norm((ws - A) - np.outer(tt, X), axis=1)
    sleeve = (rr < 0.07) & (tt > -0.05) & (tt < Lb + 0.08)
    t_end = float(tt[sleeve].max())                                   # where the jacket sleeve ends along the forearm
    ring = sleeve & (tt > t_end - 0.012)                              # the sleeve opening: cuff sits just inside it
    r = min(0.032, max(0.024, float(np.median(rr[ring])) - 0.003)) if ring.any() else 0.028
    print(f"[cuff] {sd} sleeve end {t_end:.3f} of {Lb:.3f}, radius {r:.4f}", flush=True)
    ctr = a + ax * (t_end - 0.006)
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=r, depth=0.024, location=ctr, end_fill_type='NOTHING')
    o = bpy.context.active_object; o.name = f"Cuff.{sd}"
    o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = ax.to_track_quat('Z', 'Y')
    sol = o.modifiers.new("t", 'SOLIDIFY'); sol.thickness = 0.0015; sub = o.modifiers.new("s", 'SUBSURF'); sub.levels = 1; sub.render_levels = 2
    o.data.materials.append(mat); bpy.ops.object.shade_smooth()
    bpy.context.view_layer.update(); mw = o.matrix_world.copy()
    o.parent = h.arm; o.parent_type = 'BONE'; o.parent_bone = f"lowerarm02.{sd}"
    bpy.context.view_layer.update(); o.matrix_world = mw
    return o


def investigator():
    h = Human("Investigator", gender=1.0, years=46, muscle=0.5, weight=0.5, height=0.5, eyelashes="eyelashes01",
              skin="middleage_lightskinned_male_diffuse.png")
    suit = add_asset(h, "clothes", "male_elegantsuit01", val=0.14, rough=0.82)
    wool(suit.data.materials[0])
    add_asset(h, "clothes", "shoes02", val=0.15)
    hair = add_asset(h, "hair", "short02", sat=0.3, val=0.24, rough=0.62)
    hair_strands(hair.data.materials[0])
    h.suit = suit
    sk = h.skin_mat.node_tree.nodes["Principled BSDF"]
    sk.inputs['Subsurface Weight'].default_value = 0.1; sk.inputs['Subsurface Radius'].default_value = (0.5, 0.25, 0.15)
    return h


def build(variant=None):
    os.makedirs(GEN, exist_ok=True)
    c = {}
    world_flat((0.004, 0.005, 0.008), 1.0)
    desk_room()
    binder(c)
    c["pen"] = highlighter()
    cyl("Mug", (0.62, 0.62, DZ + 0.06), 0.045, 0.1, pbr("Mug", (0.55, 0.55, 0.57), 0.3), verts=24)
    lamp((-0.6, 0.75, 0), (0.0, 0.35 + DY, DZ))
    area_light((1.2, -0.8, 2.2), (0, 0, 0), 1.5, 6, (0.5, 0.62, 0.9)).visible_camera = False
    rim = area_light((-0.9, 0.9, 1.9), (0, 0, 0), 0.8, 5, (1.0, 0.85, 0.7)); point_at(rim, (0.0, -0.2, 1.15))   # soft kick on his hair/shoulder
    rim.visible_camera = False
    h = investigator()
    reset_pose(h); pose_sit(h, lean=14)
    h.arm.rotation_euler = (0, 0, math.pi); bpy.context.view_layer.update()      # faces +Y (the desk)
    sp = h.bone_head("spine03")
    h.arm.location = (SEAT_X - sp.x, SEAT_Y - sp.y, 0); bpy.context.view_layer.update()
    w = np.concatenate([_world_verts(o) for o in h.parts if o.type == 'MESH'])
    h.arm.location.z -= w[:, 2].min(); bpy.context.view_layer.update()
    c["h"] = h
    cotton = pbr("ShirtCotton", (0.78, 0.78, 0.76), 0.75); _bump(cotton, 700, 0.15, 0.0003)
    for sd in ("R", "L"):
        shirt_cuff(h, sd, cotton)
    chair_m = pbr("ChairLeather", (0.03, 0.02, 0.015), 0.4, 0.0, **{'Coat Weight': 0.4})
    hip = h.bone_head("pelvis") if "pelvis" in h.arm.pose.bones else h.bone_head("spine05")
    box("ChairSeat", (SEAT_X, hip.y - 0.05, hip.z - 0.12), (0.52, 0.5, 0.08), chair_m, bevel=0.03)
    cb = box("ChairBack", (SEAT_X, hip.y - 0.36, hip.z + 0.3), (0.5, 0.1, 0.65), chair_m, bevel=0.05)
    s_ = cb.modifiers.new("s", 'SUBSURF'); s_.levels = 2; s_.render_levels = 2
    c["focus"] = Vector(((X0 + X1) / 2, c["row_y"], page_z((X0 + X1) / 2)))
    return c                     # no anim() here: bake.py snapshots this pose as the per-frame starting pose


SEAT_X, SEAT_Y = -0.02, -0.36

# ------------------------------------------------------------------ hand: tripod grip on the highlighter
# The hand is posed first (fixed finger curls, fixed orientation in the world); the pen is then DEFINED by the hand:
# it rests against the index pad and on the web between thumb and index. The arm is solved so the pen tip lands
# on the line. Thumb and middle finger are closed onto the barrel with small IK chains.
HAND_F = Vector((-0.10, 0.95, -0.05)).normalized()          # wrist -> knuckles: forward, a little inward, down
HAND_BETA = 40.0                                             # palm tilt below horizontal (sets the pen angle)
HAND_N = Vector((-math.cos(math.radians(HAND_BETA)), 0.0, -math.sin(math.radians(HAND_BETA))))  # palm faces his midline
PEN_R = 0.0085
PAD_OFF = 0.0115                                             # index pad surface to barrel surface offset (finger half-thickness)
WEB_N = 0.016
GRIP_L = 0.055                                               # index pad to pen tip, along the barrel


def _bone_dir(h, b):
    return (h.bone_tail(b) - h.bone_head(b)).normalized()


def _reset_fingers(h, sd):
    for pb in h.arm.pose.bones:
        if (pb.name.startswith("finger") or pb.name.startswith("metacarpal")) and pb.name.endswith("." + sd):
            pb.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()


def _palm(h, sd="R"):
    """Current hand axes from the joints: f (wrist -> middle knuckle), k (little -> index knuckle), n (palm normal)."""
    f = (h.bone_head(f"finger3-1.{sd}") - h.bone_head(f"wrist.{sd}")).normalized()
    k = h.bone_head(f"finger2-1.{sd}") - h.bone_head(f"finger5-1.{sd}"); k = (k - f * k.dot(f)).normalized()
    return f, k, (k.cross(f) if sd == "R" else f.cross(k)).normalized()


def page_surface(x):
    """z of the top paper surface under x (right page right of the spine, left page left of it)."""
    if x > 0.0:
        return page_z(x)
    return DZ + 0.034 + math.tan(PAGE_ROT) * (x + 0.155)


def hand_verts(h, sd, r=0.115):
    """Evaluated (posed) vertices of skin and clothes within r of the hand (for contact / clipping checks)."""
    c0 = np.array(h.bone_head(f"finger3-1.{sd}").lerp(h.bone_head(f"wrist.{sd}"), 0.4))
    ws = []
    for o in h.parts:
        if o.type == 'MESH' and ("body" in o.name or "suit" in o.name):
            w = _world_verts(o); ws.append(w[np.linalg.norm(w - c0, axis=1) < r])
    return np.concatenate(ws)


def page_clearance(h, sd):
    w = hand_verts(h, sd)
    if not len(w):
        return 1.0
    floor = np.where(w[:, 0] > 0, DZ + 0.044 - math.tan(PAGE_ROT) * (w[:, 0] - 0.155),
                     DZ + 0.034 + math.tan(PAGE_ROT) * (w[:, 0] + 0.155))
    return float((w[:, 2] - floor).min())


def _curl(h, b, n, deg):
    d = _bone_dir(h, b); ax = d.cross(n)
    if ax.length > 1e-6:
        rotate_bone(h.arm, b, ax.normalized(), deg)


def orient_hand(h, f_want, n_want, sd="R"):
    n_want = (n_want - f_want * n_want.dot(f_want)).normalized()
    for _ in range(3):
        f, k, n = _palm(h, sd)
        ax = f.cross(f_want)
        if ax.length > 1e-6:
            rotate_bone(h.arm, f"wrist.{sd}", ax.normalized(), math.degrees(f.angle(f_want)))
        f, k, n = _palm(h, sd)
        ang = math.degrees(n.angle(n_want)); sgn = 1 if n.cross(n_want).dot(f) > 0 else -1
        rotate_bone(h.arm, f"wrist.{sd}", f, sgn * ang)


# cumulative flexion (degrees toward the palm) of each phalanx, and its sideways lean toward the thumb side
GRIP = {"finger2": ((38, 0.10), (72, 0.08), (64, 0.05)),          # index: on top of the barrel, last joint pressing
        "finger3": ((46, -0.02), (100, -0.05), (118, -0.05)),     # middle: barrel rests on the side of its last joint
        "finger4": ((40, -0.08), (84, -0.10), (104, -0.10)),      # ring: relaxed curl, not a fist
        "finger5": ((44, -0.15), (90, -0.15), (110, -0.15))}      # little finger: relaxed, resting on the page


def _dir(f, k, n, deg, lean):
    a = math.radians(deg)
    return (f * math.cos(a) + n * math.sin(a) + k * lean).normalized()


def hand_pose(h):
    """Fingers in the tripod grip. Returns (pen tip, pen axis) implied by the hand."""
    _reset_fingers(h, "R")
    f, k, n = _palm(h)
    for fg, segs in GRIP.items():
        for j, (deg, lean) in enumerate(segs, 1):
            aim_bone(h.arm, f"{fg}-{j}.R", _dir(f, k, n, deg, lean))
    d3 = _bone_dir(h, "finger2-3.R")
    pad = h.bone_head("finger2-3.R").lerp(h.bone_tail("finger2-3.R"), 0.6)
    pside = (n - d3 * n.dot(d3)).normalized()                 # palmar side of the index's last phalanx
    C = pad + pside * (PEN_R + PAD_OFF)                       # barrel centre under the index pad
    web = h.bone_head("finger2-1.R") + k * 0.026 + n * WEB_N # the web between thumb and index
    axis = (web - C).normalized()
    tip = C - axis * GRIP_L
    # thumb: its pad presses the near side of the barrel, opposite the index
    th = C + axis * 0.004 + (k - axis * k.dot(axis)).normalized() * (PEN_R + 0.0065)
    ik2(h, "finger1-2.R", "finger1-3.R", th, k * 0.6 - n * 0.5 - f * 0.4)
    return tip, axis


def clearance(h, tip, axis):
    """Smallest distance (minus the barrel radius) from each finger bone segment to the barrel axis (metres)."""
    out = {}
    for fg in range(1, 6):
        best = 9.0
        for j in (1, 2, 3):
            A = h.bone_head(f"finger{fg}-{j}.R"); B = h.bone_tail(f"finger{fg}-{j}.R")
            for u in [q / 8 for q in range(9)]:
                P = A.lerp(B, u); v = P - tip; s_ = max(0.0, min(0.15, v.dot(axis)))
                best = min(best, (v - axis * s_).length - PEN_R)
        out[fg] = round(best, 4)
    return out


def pose_right(h, tip_target):
    wt = tip_target - HAND_F * 0.16 + Vector((0.03, -0.02, 0.05))
    for _ in range(5):
        reach(h, "R", wt, Vector((0.55, -0.2, -0.8)))
        orient_hand(h, HAND_F, HAND_N)
        tip, axis = hand_pose(h)
        err = tip_target - tip
        if err.length < 0.0008:
            break
        wt = wt + err
    return tip, axis


def anim(c, t):
    h = c["h"]; ry = c["row_y"]
    k = min(1.0, max(0.0, (t - 0.16) / 0.64))                   # stroke between t = 0.16 and 0.80
    e = ease(k)
    x = X0 + (X1 - X0) * e
    lift = 0.012 * (1 - min(1.0, t / 0.14)) ** 2 + 0.010 * max(0.0, (t - 0.84) / 0.16) ** 1.5
    tgt = Vector((x, ry, page_z(x) + 0.0008 + lift))
    c["hl"].scale = (max(0.001, (X1 - X0) * e / math.cos(PAGE_ROT)), 0.009, 1)
    # torso: a slight lean in as he works along the line, the head turns to follow the tip
    h.rot("spine02", (1, 0, 0), -(1.5 + 2.5 * ease(min(1.0, t / 0.8))))
    h.rot("neck01", (-1, 0, 0), 6); h.rot("head", (-1, 0, 0), 14)
    h.rot("head", (0, 0, 1), -(4 + 10 * e))                     # turns right with the stroke
    h.rot("head", (0, 1, 0), 3 + 3 * e)                         # and tilts toward the line
    tip, axis = pose_right(h, tgt)
    pen = c["pen"]; pen.location = tip; pen.rotation_quaternion = axis.to_track_quat('Z', 'Y')
    c["tip_err"] = (tgt - tip).length; c["clear"] = clearance(h, tip, axis)
    # left hand flat on the left page, holding the binder open (fingers relaxed, resting on the paper)
    dz = c.get("lh_dz", 0.0)                       # contact solve every frame: the lean moves his shoulder,
    for _ in range(2):                             # so the hand is re-seated on the page (changes are < 4 mm)
        pose_left(h, ry, dz); dz += 0.0015 - page_clearance(h, "L")
    pose_left(h, ry, dz); c["lh_dz"] = dz
    bpy.context.view_layer.update()


LH_F = Vector((0.45, 0.89, -0.07)).normalized()
LH_N = Vector((0.08, 0.0, -1.0))
LH_TN = -0.05                                                       # thumb lies alongside, not pressed down
LH_SEGS = ((8, 16, 22), (9, 17, 23), (10, 18, 24), (12, 21, 28))     # cumulative flexion per phalanx, index..little


def pose_left(h, ry, dz):
    lw = Vector((-0.24, ry - 0.06, DZ + 0.06 + dz))
    reach(h, "L", lw, Vector((-1.0, -0.15, -0.35)))          # elbow out to the side: the forearm reads along its length
    orient_hand(h, LH_F, LH_N, "L")
    _reset_fingers(h, "L")
    f, k, n = _palm(h, "L")
    for fg, segs in zip(("finger2", "finger3", "finger4", "finger5"), LH_SEGS):
        for j, deg in enumerate(segs, 1):
            aim_bone(h.arm, f"{fg}-{j}.L", _dir(f, k, n, deg, 0.0))
    aim_bone(h.arm, "finger1-2.L", (f * 0.7 + k * 0.6 + n * LH_TN).normalized())
    aim_bone(h.arm, "finger1-3.L", (f * 0.85 + k * 0.4 + n * LH_TN).normalized())


def cam(c, t):
    e = ease(t)
    loc = Vector((0.50, -0.78, 1.52)).lerp(Vector((0.45, -0.69, 1.47)), e)    # slow push over his right shoulder
    tgt = c["focus"] + Vector((-0.11, -0.12, 0.17))
    return loc, tgt, 30


MOVES = {"ots": dict(kind="anim", dof=2.8, far=6.0, anim=anim, cam=cam, focus=lambda c, t: c["focus"])}
