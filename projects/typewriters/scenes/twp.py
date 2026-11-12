"""Shared helpers for the typewriter film: people (period office wear), placing, typing poses, room bits."""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import pbr, box, area_light, point_at
from human import Human, add_asset, reset_pose, fingers_curl, pose_walk, pose_sit, _world_verts, reach
import ph

SKIN_F = "middleage_lightskinned_female_diffuse.png"
SKIN_M = "middleage_lightskinned_male_diffuse.png"
SKIN_OLD = "old_lightskinned_male_diffuse.png"


def person(name, gender, years, cloth, hair, hv=0.35, cval=0.3, hue=0.5, sat=0.2, skin=None, height=0.5, weight=0.45):
    h = Human(name, gender=gender, years=years, muscle=0.5, weight=weight, height=height, eyelashes="eyelashes01",
              skin=skin or (SKIN_F if gender < 0.5 else SKIN_M))
    o = add_asset(h, "clothes", cloth, val=1.0, rough=0.7, hue=0.5, sat=1.0)
    recolor(o, hue, sat, cval)
    add_asset(h, "clothes", "shoes02", val=0.2, rough=0.4)
    if hair:
        add_asset(h, "hair", hair, val=hv, rough=0.45)
    return h


def recolor(o, hue, sat, val):
    """Muted solid period colour for a garment (the MakeHuman textures are mostly near-black): base = colour,
    with a little of the texture kept for weave and seams."""
    import colorsys
    col = colorsys.hsv_to_rgb(hue % 1.0, min(0.12 + sat * 1.4, 0.48), 0.05 + 0.26 * val)
    for m in o.data.materials:
        N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
        src = p.inputs['Base Color'].links[0].from_socket
        mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MIX'; mx.inputs['Factor'].default_value = 0.15
        mx.inputs[6].default_value = (*col, 1); L.new(src, mx.inputs[7]); L.new(mx.outputs[2], p.inputs['Base Color'])


def ground(h, z=None):
    """Lowest vertex onto the floor at z (default: the z the rig was placed at)."""
    z = h.arm.location.z if z is None else z
    bpy.context.view_layer.update()
    w = np.concatenate([_world_verts(o) for o in h.parts if o.type == 'MESH'])
    h.arm.location.z -= w[:, 2].min() - z; bpy.context.view_layer.update()


def upright(h):
    """Pose helpers rotate bones about WORLD axes: pose with the rig unrotated, then turn it."""
    h.arm.rotation_euler = (0, 0, 0); bpy.context.view_layer.update()


def face(h, face_z):
    h.arm.rotation_euler = (0, 0, face_z); bpy.context.view_layer.update()


def stand(h, loc, face_z):
    """Standing, arms relaxed. face_z: rotation about Z (0 faces -Y; pi faces +Y; pi/2 faces +X)."""
    upright(h)
    pose_walk(h, 0.0, stride=0.0, arm_swing=0.0)
    from human import SIDE
    for sd, sg in SIDE.items():                       # arms hanging close at the sides, a soft bend at the elbow
        h.rot(f"upperarm01.{sd}", (0, 1, 0), sg * 14)
        h.rot(f"lowerarm01.{sd}", (1, 0, 0), 50)          # forearms hang by the thighs (measured: wrist just ahead of the hip, ~0.9 m)
    fingers_curl(h, 22, thumb=10)                        # relaxed hands, palms toward the thighs
    h.arm.rotation_euler = (0, 0, face_z); h.arm.location = loc; ground(h)


def seat(h, loc, face_z, lean=12, seat_z=None):
    upright(h); reset_pose(h); pose_sit(h, lean=lean)
    h.arm.rotation_euler = (0, 0, face_z); h.arm.location = loc; ground(h)


def walk(h, p0, p1, s, speed=1.2, stride=26, z0=0.0):
    """Walk from p0 toward p1 (world xy), at time s (s), stopping at p1. Faces the walking direction."""
    p0 = Vector((p0[0], p0[1], 0)); p1 = Vector((p1[0], p1[1], 0)); d = p1 - p0; L = d.length
    dist = min(L, s * speed)
    phase = dist / 1.35                         # one stride cycle per ~1.35 m
    moving = dist < L - 1e-3
    upright(h)
    pose_walk(h, phase if moving else 0.0, stride=stride if moving else 0.0, arm_swing=20 if moving else 0.0)
    from human import SIDE
    for sd, sg in SIDE.items():                       # arms in at the sides (MakeHuman's A-pose reads as a puppet)
        h.rot(f"upperarm01.{sd}", (0, 1, 0), sg * 12)
        h.rot(f"lowerarm01.{sd}", (1, 0, 0), 35)
    ang = math.atan2(d.x, -d.y)                 # rotation z that faces direction d
    h.arm.rotation_euler = (0, 0, ang)
    h.arm.location = p0 + d.normalized() * dist; h.arm.location.z = z0; ground(h)
    return moving


def forward(h):
    return (h.arm.matrix_world.to_3x3() @ Vector((0, -1, 0))).normalized()


def type_pose(h, tw, sec, look=0.0):
    """Seated typist: both hands over the home row, fingers tapping in step with the keys going down."""
    import typewriter as T
    fwd = forward(h); side = fwd.cross(Vector((0, 0, 1))).normalized()
    for sd, sg, key in (("L", -1, "f"), ("R", 1, "j")):
        k = tw["keys"][key]; kp = k.matrix_world.translation
        tap = 0.006 * max(0.0, math.sin(sec * 19 + (0 if sd == "L" else 2.1)))
        target = kp + Vector((0, 0, 0.045 - tap)) - fwd * 0.07
        reach(h, sd, target, Vector((sg * side.x, sg * side.y, -0.8)), fwd + Vector((0, 0, -0.55)))
    fingers_curl(h, 38, thumb=12)
    h.rot("neck01", side, 8); h.rot("head", side, 14 + 2 * math.sin(sec * 0.7))      # eyes on the page
    h.rot("head", (0, 0, 1), look)


def hide(objs, on=True):
    for o in objs:
        o.hide_render = on; o.hide_viewport = on


def person_objs(h):
    return [h.arm] + list(h.parts)


def venetian(x0, y0, z0, z1, width, axis, mat, tilt=-50, n=None, slat=0.05):
    """Venetian blind: slats spanning `width` along axis ('y' or 'x'), from z0 to z1."""
    n = n or int((z1 - z0) / slat)
    out = []
    for k in range(n):
        z = z0 + k * slat
        if axis == "y":
            out.append(box("Slat", (x0, y0, z), (0.05, width, 0.004), mat, rot=(0, math.radians(tilt), 0)))
        else:
            out.append(box("Slat", (x0, y0, z), (width, 0.05, 0.004), mat, rot=(math.radians(tilt), 0, 0)))
    return out


def tint_model(meshes, col, keep=0.25):
    """Recolour a scanned model (multiply its base colour toward `col`), e.g. tone down a bright lamp."""
    seen = set()
    for o in meshes:
        for m in o.data.materials:
            if m is None or m.name in seen or not m.use_nodes:
                continue
            seen.add(m.name)
            N = m.node_tree.nodes; L = m.node_tree.links; p = next((n for n in N if n.type == 'BSDF_PRINCIPLED'), None)
            if p is None:
                continue
            src = p.inputs['Base Color'].links[0].from_socket if p.inputs['Base Color'].links else None
            hsv = N.new("ShaderNodeHueSaturation"); hsv.inputs['Saturation'].default_value = keep
            mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
            mx.inputs[7].default_value = (*col, 1)
            if src is not None:
                L.new(src, hsv.inputs['Color'])
            else:
                hsv.inputs['Color'].default_value = p.inputs['Base Color'].default_value
            L.new(hsv.outputs[0], mx.inputs[6]); L.new(mx.outputs[2], p.inputs['Base Color'])


def model_fit(aid, loc, rot_z=0.0, height=None, width=None):
    """Poly Haven model scaled to a real size (height or width in metres), standing on z=loc.z."""
    r, ms = ph.model(aid, loc=(0, 0, 0))
    lo, hi = ph.bounds(ms)
    k = 1.0
    if height:
        k = height / (hi.z - lo.z)
    elif width:
        k = width / max(hi.x - lo.x, hi.y - lo.y)
    r.scale = (k, k, k); r.rotation_euler = (0, 0, rot_z); r.location = Vector(loc) - Vector((0, 0, lo.z * k))
    bpy.context.view_layer.update()
    return r, ms


def cloud_sky(world, cover=0.55, color=(0.82, 0.84, 0.88), scale=2.2):
    """Soft broken cloud over the existing sky texture: noise on the view direction, upper hemisphere only."""
    N = world.node_tree.nodes; L = world.node_tree.links
    bg = next(n for n in N if n.type == 'BACKGROUND')
    src = bg.inputs['Color'].links[0].from_socket
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs['Generated'], sep.inputs[0])
    z = N.new("ShaderNodeMath"); z.operation = 'MAXIMUM'; z.inputs[1].default_value = 0.04; L.new(sep.outputs[2], z.inputs[0])
    dx = N.new("ShaderNodeMath"); dx.operation = 'DIVIDE'; L.new(sep.outputs[0], dx.inputs[0]); L.new(z.outputs[0], dx.inputs[1])
    dy = N.new("ShaderNodeMath"); dy.operation = 'DIVIDE'; L.new(sep.outputs[1], dy.inputs[0]); L.new(z.outputs[0], dy.inputs[1])
    cmb = N.new("ShaderNodeCombineXYZ"); L.new(dx.outputs[0], cmb.inputs[0]); L.new(dy.outputs[0], cmb.inputs[1])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = 10; nz.inputs['Roughness'].default_value = 0.62
    L.new(cmb.outputs[0], nz.inputs['Vector'])
    rr = N.new("ShaderNodeMapRange"); rr.inputs['From Min'].default_value = 1.0 - cover * 0.9; rr.inputs['From Max'].default_value = 1.0 - cover * 0.9 + 0.25
    L.new(nz.outputs['Fac'], rr.inputs['Value'])
    hz = N.new("ShaderNodeMapRange"); hz.inputs['From Min'].default_value = 0.0; hz.inputs['From Max'].default_value = 0.12; L.new(sep.outputs[2], hz.inputs['Value'])
    m = N.new("ShaderNodeMath"); m.operation = 'MULTIPLY'; L.new(rr.outputs[0], m.inputs[0]); L.new(hz.outputs[0], m.inputs[1])
    shade = N.new("ShaderNodeMix"); shade.data_type = 'RGBA'; L.new(nz.outputs['Fac'], shade.inputs['Factor'])
    shade.inputs[6].default_value = (color[0] * 0.75, color[1] * 0.77, color[2] * 0.82, 1); shade.inputs[7].default_value = (*color, 1)
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; L.new(m.outputs[0], mx.inputs['Factor']); L.new(src, mx.inputs[6]); L.new(shade.outputs[2], mx.inputs[7])
    L.new(mx.outputs[2], bg.inputs['Color'])
    return world


def soviet_lamp(loc, rot_z=0.0, height=9.0, arm=2.2, lit=False):
    """Concrete street-lamp mast with a curved steel arm and a cobra-head luminaire (Moscow, 1970s-80s)."""
    from kit import cyl, box, pbr, join
    conc = pbr("LampConcrete", (0.42, 0.41, 0.38), 0.85)
    steel = pbr("LampArm", (0.3, 0.31, 0.3), 0.5, 0.7)
    parts = []
    bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.16, radius2=0.09, depth=height, location=(0, 0, height / 2))
    p = bpy.context.active_object; p.data.materials.append(conc); parts.append(p)
    n = 8
    for k in range(n):                                   # arm: a quarter-circle out from the top
        a0 = k / n * math.pi / 2; a1 = (k + 1) / n * math.pi / 2
        x0, z0 = arm * (1 - math.cos(a0)), height - 0.6 + 0.6 * math.sin(a0) + 0.0
        x1, z1 = arm * (1 - math.cos(a1)), height - 0.6 + 0.6 * math.sin(a1)
        mx_, mz = (x0 + x1) / 2, (z0 + z1) / 2
        L_ = math.hypot(x1 - x0, z1 - z0); ang = math.atan2(z1 - z0, x1 - x0)
        parts.append(cyl("Arm", (mx_, 0, mz + 0.4 * math.sin(math.pi * (k + 0.5) / n)), 0.035, L_ + 0.02, steel, verts=8, rot=(0, math.pi / 2 - ang, 0)))
    head = box("LampHead", (arm + 0.25, 0, height - 0.05), (0.7, 0.32, 0.14), steel, bevel=0.05)
    lens = box("LampLens", (arm + 0.25, 0, height - 0.13), (0.55, 0.24, 0.03), pbr("LampLensM", (0.85, 0.8, 0.7), 0.2, 0.0,
               **{'Emission Color': (1.0, 0.6, 0.3, 1), 'Emission Strength': 6.0 if lit else 0.0}))
    parts += [head, lens]
    o = join(parts, "SovietLamp"); o.location = loc; o.rotation_euler = (0, 0, rot_z)
    return o


def two_tone(o, split_z, top, bottom, stripe=None):
    """Shirt over trousers on a one-piece garment: colour by world height (fine for a figure that stays put),
    optional trouser seam stripe (a thin band by object-space x near the leg sides)."""
    for m in o.data.materials:
        N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
        geo = N.new("ShaderNodeNewGeometry"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs['Position'], sep.inputs[0])
        gt = N.new("ShaderNodeMath"); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = split_z; L.new(sep.outputs[2], gt.inputs[0])
        mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; L.new(gt.outputs[0], mx.inputs['Factor'])
        mx.inputs[6].default_value = (*bottom, 1); mx.inputs[7].default_value = (*top, 1)
        L.new(mx.outputs[2], p.inputs['Base Color'])
        p.inputs['Roughness'].default_value = 0.65


def marine_cap(loc, rot_z=0.0):
    """A white peaked service cover lying on the desk: black band, domed white crown overhanging it, a glossy
    black visor angled down at the front, a gold badge on the band. Visor points along local -Y."""
    from kit import cyl, box, pbr, join
    white = pbr("CoverWhite", (0.86, 0.86, 0.84), 0.35)
    blk = pbr("CoverVisor", (0.01, 0.01, 0.012), 0.1, 0.0, **{'Coat Weight': 1.0})
    gold = pbr("CoverEmblem", (0.8, 0.6, 0.25), 0.3, 1.0)
    parts = [cyl("CoverBand", (0, 0, 0.035), 0.092, 0.07, blk, verts=48)]
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=16, radius=1.0, location=(0, 0.015, 0.078))
    top = bpy.context.active_object; top.scale = (0.135, 0.125, 0.035); top.data.materials.append(white)
    bpy.ops.object.transform_apply(scale=True); parts.append(top)
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.1, depth=0.005, location=(0, -0.075, 0.012))
    v = bpy.context.active_object; v.scale = (0.95, 0.55, 1); v.rotation_euler = (math.radians(-18), 0, 0); v.data.materials.append(blk); parts.append(v)
    parts.append(box("CoverStrap", (0, -0.091, 0.022), (0.15, 0.004, 0.008), blk))
    parts.append(box("Emblem", (0, -0.094, 0.05), (0.03, 0.004, 0.032), gold))
    o = join(parts, "MarineCover"); o.location = loc; o.rotation_euler = (0, 0, rot_z)
    return o


def arm_len(h, side="R"):
    b = h.arm.data.bones
    return sum(b[f"{n}.{side}"].length for n in ("upperarm01", "upperarm02", "lowerarm01", "lowerarm02"))


def bend_to(h, target, frac=0.8, max_deg=36, step=3.0):
    """Lean the upper body forward (spine and a little hip) until `target` is within a relaxed reach of the
    shoulders, so a reach ends in bent elbows instead of stiff outstretched arms."""
    target = Vector(target); L = arm_len(h)
    side = forward(h).cross(Vector((0, 0, 1))).normalized()

    def dist():
        m = (h.bone_head("upperarm01.L") + h.bone_head("upperarm01.R")) * 0.5
        return (target - m).length
    done = 0.0; sgn = -1.0; d0 = dist()
    while d0 > frac * L and done < max_deg:
        for b in ("spine01", "spine02", "spine03"):
            h.rot(b, side, sgn * step / 3)
        d1 = dist()
        if d1 > d0 and done == 0.0:                     # wrong way: undo and flip
            for b in ("spine01", "spine02", "spine03"):
                h.rot(b, side, -sgn * step / 3)
            sgn = -sgn; continue
        d0 = d1; done += step
    return done


def work(h, targets, poles=None, hand_dir=None, head=10, palm=None):
    """Both (or one) hands on something in front: lean in as needed, then IK each arm with the elbows down
    and slightly out. targets: {"L": vec, "R": vec}."""
    from human import SIDE
    mid = sum((Vector(v) for v in targets.values()), Vector()) / len(targets)
    bend_to(h, mid)
    fwd = forward(h); side = fwd.cross(Vector((0, 0, 1))).normalized()     # side = the character's right
    targets = dict(targets)
    if "L" in targets and "R" in targets and (Vector(targets["L"]) - Vector(targets["R"])).dot(side) > 0:
        targets["L"], targets["R"] = targets["R"], targets["L"]                # never cross the arms
    L = arm_len(h)
    for sd, t in targets.items():
        sg = SIDE[sd]                                    # character's left is -side
        sh = h.bone_head(f"upperarm01.{sd}"); t = Vector(t)
        if (t - sh).length > 0.92 * L:                   # never a locked, straight arm
            t = sh + (t - sh).normalized() * 0.92 * L
        pole = (poles or {}).get(sd) or (-side * sg * 0.35 + Vector((0, 0, -1)) - fwd * 0.2)
        reach(h, sd, Vector(t), pole, hand_dir if hand_dir is not None else fwd + Vector((0, 0, -0.6)),
              palm=(palm(sd, side) if callable(palm) else palm))
    fingers_curl(h, 30)
    if head:
        h.rot("head", side, head)


def chest_point(h, fwd_d=0.24, down=0.3):
    """A point in front of the chest, from the shoulders (for things held in both hands)."""
    m = (h.bone_head("upperarm01.L") + h.bone_head("upperarm01.R")) * 0.5
    return m + forward(h) * fwd_d + Vector((0, 0, -down))


def window_plate(center, size, axis="x", top=(0.5, 0.55, 0.6), bottom=(0.26, 0.28, 0.29), strength=1.0, name="WinPlate"):
    """What a window shows: a dim, softly graded exterior just outside the glass (never a flat white square). It casts
    no shadow, so a key light set outside the window still comes through. axis: the wall normal."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); em = N.new("ShaderNodeEmission"); tc = N.new("ShaderNodeTexCoord")
    sp = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs['Generated'], sp.inputs[0])
    cr = N.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (*bottom, 1); cr.color_ramp.elements[1].color = (*top, 1)
    L.new(sp.outputs[2], cr.inputs[0]); L.new(cr.outputs[0], em.inputs['Color']); em.inputs['Strength'].default_value = strength
    L.new(em.outputs[0], out.inputs['Surface'])
    w, h = size
    dims = (0.02, w, h) if axis == "x" else (w, 0.02, h)
    o = box(name, center, dims, m)
    o.visible_shadow = False; o.visible_diffuse = False
    return o


def roll_palm(h, side, palm_dir):
    """Roll the hand about the wrist bone so the palm faces palm_dir (world). aim() sets only the wrist's direction,
    so without this a reached hand can end up rolled 180 deg (thumb on the wrong side, inside-out). Measured on the
    MakeHuman rig: the palm normal is the wrist bone's local -X (left) / +X (right)."""
    import math as _m
    pb = h.arm.pose.bones[f"wrist.{side}"]; bpy.context.view_layer.update()
    M = (h.arm.matrix_world @ pb.matrix).to_3x3()
    y = M.col[1].normalized(); ax = M.col[0] * (-1.0 if side == "L" else 1.0)
    p = Vector(palm_dir); p = p - y * p.dot(y)
    a = ax - y * ax.dot(y)
    if p.length < 1e-4 or a.length < 1e-4:
        return
    p.normalize(); a.normalize()
    ang = _m.atan2(a.cross(p).dot(y), a.dot(p))
    h.rot(f"wrist.{side}", y, _m.degrees(ang))


# every reach in the film ends with the palm rolled the right way up (palm down and a little inward on whatever the
# hand rests on, unless a gesture asks for another palm): patch human.reach once, here
import human as _hm
_reach_raw = getattr(_hm, "_reach_raw", _hm.reach)
_hm._reach_raw = _reach_raw


def _reach_rolled(h, side, wrist_target, pole, hand_dir=None, palm=None):
    _reach_raw(h, side, wrist_target, pole, hand_dir)
    fw = forward(h); right = fw.cross(Vector((0, 0, 1))).normalized()
    inward = right * (-1.0 if side == "R" else 1.0)
    roll_palm(h, side, palm if palm is not None else Vector((0, 0, -1)) + inward * 0.35)


_hm.reach = _reach_rolled
reach = _reach_rolled



def neutral_daylight(warm=(1.0, 0.93, 0.84)):
    """Daylight patches are neutral or slightly warm, never blue: retint any bluish lamp (and the world) in a day
    interior after the look has run."""
    for o in bpy.data.objects:
        if o.type == 'LIGHT':
            r, g, b = o.data.color
            if b > r + 0.04:
                o.data.color = warm
    w = bpy.context.scene.world
    if w and w.use_nodes:
        for n in w.node_tree.nodes:
            if n.bl_idname == "ShaderNodeBackground":
                col = n.inputs['Color']
                if col.is_linked:                       # a blue sky texture seen only through the windows: a neutral warm day
                    for l in list(col.links):
                        w.node_tree.links.remove(l)
                    col.default_value = (0.42, 0.4, 0.37, 1)
                else:
                    r, g, b, a = col.default_value
                    if b > r + 0.04:
                        col.default_value = (*warm, 1)
