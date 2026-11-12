"""People helpers for the banker film: build, stand, sit, walk, nod, look, hold. Unnamed figures only (no likeness).
Facing: rotation z = theta turns the rest pose (facing -Y) to face (sin theta, -cos theta).
Bones rotate about WORLD axes, so poses are built in the rest orientation, then the rig is turned and placed."""
import math
import numpy as np
import bpy
from mathutils import Vector, Matrix
from common import ease
from human import Human, add_asset, reset_pose, fingers_curl, pose_walk, pose_sit, _world_verts, reach
import ph

SKIN = {("m", "mid"): "middleage_lightskinned_male_diffuse.png", ("m", "old"): "old_lightskinned_male_diffuse.png",
        ("f", "mid"): "middleage_lightskinned_female_diffuse.png", ("f", "young"): "young_lightskinned_female_diffuse.png"}


PALETTE = [(0.16, 0.16, 0.17), (0.3, 0.3, 0.31), (0.22, 0.14, 0.08), (0.36, 0.27, 0.17), (0.08, 0.1, 0.17),
           (0.19, 0.2, 0.13), (0.2, 0.25, 0.32), (0.35, 0.28, 0.22), (0.26, 0.24, 0.27)]
DARK_CLOTHES = ("male_elegantsuit01", "female_elegantsuit01", "male_casualsuit05", "male_casualsuit01")


def person(name, gender, years, cloth, hair, cval=0.25, hv=0.3, hue=0.5, sat=1.0, skin=None, weight=0.5, height=0.5, col=None):
    """A MakeHuman figure. Dark suits and jackets get a muted period colour (charcoal, grey, brown, camel, navy...)
    chosen from the name unless `col` is given, so nobody reads as an all-black silhouette."""
    if skin is None:
        skin = SKIN[("f", "mid")] if gender < 0.5 else (SKIN[("m", "old")] if years > 55 else SKIN[("m", "mid")])
    h = Human(name, gender=gender, years=years, muscle=0.5, weight=weight, height=height, eyelashes="eyelashes01", skin=skin)
    add_asset(h, "clothes", cloth, val=cval, hue=hue, sat=sat, rough=0.7)
    add_asset(h, "clothes", "shoes02", val=0.15, rough=0.4)
    if hair:
        add_asset(h, "hair", hair, val=hv, rough=0.45)
    if col is None and cloth in DARK_CLOTHES:
        import zlib
        col = PALETTE[zlib.crc32(name.encode()) % len(PALETTE)]
    if col is not None:
        recolor(h, cloth, col, 0.75)
    return h


def militia(name, years, hv=0.25):
    """1995 militia officer: a grey-blue uniform jacket and trousers, a peaked cap."""
    h = person(name, 1.0, years, "male_casualsuit05", "short02", hv=hv, col=(0.3, 0.35, 0.43))
    militia_cap(h)
    return h


def militia_cap(h):
    from kit import cyl, box, pbr
    from pbkit import joinm
    stand(h, (0, 0, 0), 0.0)
    tl = h.bone_tail("head"); hd = h.bone_head("head")
    up = (tl - hd).normalized()
    c = tl - up * 0.045 + Vector((0, 0.005, 0))
    cloth = pbr(h.name + "CapCloth", (0.28, 0.33, 0.41), 0.75); band = pbr(h.name + "CapBand", (0.45, 0.06, 0.06), 0.6)
    visor = pbr(h.name + "Visor", (0.02, 0.02, 0.02), 0.25, 0.0, **{'Coat Weight': 0.8})
    parts = [cyl("CapCrown", (c.x, c.y, c.z + 0.035), 0.118, 0.03, cloth, verts=32),
             cyl("CapBody", (c.x, c.y, c.z + 0.0), 0.098, 0.05, cloth, verts=32),
             cyl("CapBand", (c.x, c.y, c.z - 0.012), 0.1, 0.022, band, verts=32),
             box("CapVisor", (c.x, c.y - 0.11, c.z - 0.022), (0.15, 0.07, 0.008), visor, rot=(math.radians(-12), 0, 0)),
             cyl("CapBadge", (c.x, c.y - 0.1, c.z + 0.0), 0.012, 0.004, pbr("Badge", (0.7, 0.55, 0.2), 0.3, 1.0), verts=12, rot=(math.radians(90), 0, 0))]
    cap = joinm(parts, h.name + "Cap")
    parent_keep(cap, h, "head")
    return cap


def _rest(h):
    h.arm.rotation_euler = (0, 0, 0); h.arm.location = (0, 0, 0); bpy.context.view_layer.update()


def _ground(h, z=0.0):
    w = np.concatenate([_world_verts(o) for o in h.parts if o.type == 'MESH'])
    h.arm.location.z += z - w[:, 2].min(); bpy.context.view_layer.update()


def stand(h, loc, face_z, ground=True):
    """Standing, legs straight, arms relaxed."""
    _rest(h)
    pose_walk(h, 0.0, stride=0.0, arm_swing=0.0)
    for sd in ("L", "R"):
        for b in (f"upperleg01.{sd}", f"lowerleg01.{sd}", f"foot.{sd}"):
            h.arm.pose.bones[b].matrix_basis = Matrix.Identity(4)
    h.rot("spine05", (1, 0, 0), 6)
    h.arm.rotation_euler = (0, 0, face_z); h.arm.location = loc; bpy.context.view_layer.update()
    if ground:
        _ground(h, loc[2] if len(loc) > 2 else 0.0)


def seat(h, loc, face_z, lean=12, floor_z=0.0):
    """Seated (chair height from the pose), feet on the floor at floor_z."""
    _rest(h); reset_pose(h); pose_sit(h, lean=lean)
    h.arm.rotation_euler = (0, 0, face_z); h.arm.location = (loc[0], loc[1], 0); bpy.context.view_layer.update()
    _ground(h, floor_z)


def walk_at(h, phase, loc, face_z, stride=24, swing=16):
    _rest(h)
    bob = pose_walk(h, phase % 1.0, stride=stride, arm_swing=swing)
    h.arm.rotation_euler = (0, 0, face_z); h.arm.location = (loc[0], loc[1], 0); bpy.context.view_layer.update()
    _ground(h, (loc[2] if len(loc) > 2 else 0.0) + bob * 0.3)


def fwd(h):
    return (h.arm.matrix_world.to_3x3() @ Vector((0, -1, 0))).normalized()


def side(h):
    """The person's own left (unit vector): up x forward."""
    return Vector((0, 0, 1)).cross(fwd(h)).normalized()


def nod(h, bone, deg):
    """Bend a spine/neck/head bone forward (down) by deg, whichever way the person faces."""
    f = fwd(h); h.rot(bone, Vector((0, 0, 1)).cross(f).normalized(), deg)


def look(h, target, amount=1.0, limit=70):
    """Turn neck and head toward a world point (yaw only)."""
    f = fwd(h); d = Vector(target) - h.bone_head("head"); d.z = 0
    if d.length < 1e-4:
        return
    ang = math.degrees(math.atan2(f.x * d.y - f.y * d.x, f.x * d.x + f.y * d.y)) * amount
    ang = max(-limit, min(limit, ang))
    h.rot("neck01", (0, 0, 1), ang * 0.4); h.rot("head", (0, 0, 1), ang * 0.6)


def turn_torso(h, deg):
    h.rot("spine03", (0, 0, 1), deg * 0.5); h.rot("spine04", (0, 0, 1), deg * 0.5)


def hold_flat(h, obj, dist=0.33, drop=0.08, tilt_deg=55, spread=0.15, wobble=0.0):
    """Both hands hold a flat object (folder, papers, photo) in front of the chest, tipped toward the eyes."""
    f = fwd(h); s = Vector((0, 0, 1)).cross(f).normalized()
    hold = h.bone_head("spine03") + f * dist + Vector((0, 0, -drop + wobble))
    obj.location = hold
    obj.rotation_mode = 'XYZ'; obj.rotation_euler = (math.radians(tilt_deg), 0, math.atan2(f.y, f.x) + math.pi / 2)
    bpy.context.view_layer.update()
    for sd, sg in (("L", 1), ("R", -1)):
        reach(h, sd, hold + s * (spread * sg) + Vector((0, 0, -0.02)), Vector((sg * s.x, sg * s.y, -0.8)), f + Vector((0, 0, 0.2)))
    fingers_curl(h, 30, thumb=15)
    return hold


def hand_to(h, sd, target, pole=None, hand_dir=None, curl=35):
    f = fwd(h); s = Vector((0, 0, 1)).cross(f).normalized() * (1 if sd == "L" else -1)
    reach(h, sd, Vector(target), pole or (s * 0.6 + Vector((0, 0, -0.7)) - f * 0.2), hand_dir)
    fingers_curl(h, curl, side=(sd,), thumb=20)


def attach(h, obj, bone, offset=(0, 0, 0)):
    """Parent a prop to a bone (offset in the bone's space, from its tail)."""
    obj.parent = h.arm; obj.parent_type = 'BONE'; obj.parent_bone = bone
    obj.location = offset


def hide(h, flag=True):
    for o in [h.arm] + list(h.parts):
        o.hide_render = flag
    for o in bpy.data.objects:
        if o.parent == h.arm:
            o.hide_render = flag


def parent_keep(obj, h, bone):
    bpy.context.view_layer.update()
    mw = obj.matrix_world.copy()
    obj.parent = h.arm; obj.parent_type = 'BONE'; obj.parent_bone = bone
    bpy.context.view_layer.update(); obj.matrix_world = mw


def protective_gear(h, suit=(0.86, 0.87, 0.85)):
    """A white hood and a half-face respirator with two filter cartridges, following the head.
    Call right after building the person, while it stands in the rest orientation at the origin."""
    from kit import box, cyl, pbr
    from pbkit import joinm
    stand(h, (0, 0, 0), 0.0)
    hd = h.bone_head("head"); tl = h.bone_tail("head")
    c = (hd + tl) / 2
    hood_m = pbr(h.name + "Hood", suit, 0.75, 0.0, **{'Sheen Weight': 0.4})
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=0.112, location=(c.x, c.y + 0.02, c.z + 0.01))
    hood = bpy.context.active_object; hood.name = h.name + "Hood"; hood.scale = (0.9, 1.0, 1.08)
    kill = [v.index for v in hood.data.vertices if v.co.y < -0.035 and v.co.z < 0.07]      # the face opening
    import bmesh
    bm = bmesh.new(); bm.from_mesh(hood.data); bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.verts[i] for i in kill], context='VERTS'); bm.to_mesh(hood.data); bm.free()
    so = hood.modifiers.new("t", 'SOLIDIFY'); so.thickness = 0.006
    # the hood runs down to the shoulders as a collar
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.09, depth=0.12, location=(c.x, c.y + 0.025, c.z - 0.13))
    col = bpy.context.active_object; col.name = h.name + "Collar"; col.data.materials.append(hood_m)
    parent_keep(col, h, "neck01")
    bpy.ops.object.shade_smooth(); hood.data.materials.append(hood_m)
    parent_keep(hood, h, "head")
    rub = pbr(h.name + "Resp", (0.07, 0.075, 0.08), 0.6)
    face = Vector((c.x, c.y - 0.112, c.z - 0.022))
    parts = [box("RespBody", tuple(face), (0.075, 0.05, 0.06), rub, bevel=0.018)]
    for sx in (-1, 1):
        parts.append(cyl("Cartridge", (face.x + sx * 0.055, face.y + 0.005, face.z - 0.012), 0.03, 0.025, pbr("Filter", (0.2, 0.21, 0.18), 0.5), verts=24,
                         rot=(math.radians(90), 0, math.radians(sx * 35))))
    resp = joinm(parts, h.name + "Respirator")
    parent_keep(resp, h, "head")
    return hood, resp


def recolor(h, cloth, col, rough=0.7):
    """Replace a clothes texture with a flat colour (white coats, coveralls, uniforms)."""
    for o in h.parts:
        for ms in getattr(o, "material_slots", []):
            if ms.material and cloth in ms.material.name:
                pb = ms.material.node_tree.nodes.get("Principled BSDF")
                for l_ in list(pb.inputs['Base Color'].links):
                    ms.material.node_tree.links.remove(l_)
                pb.inputs['Base Color'].default_value = (*col, 1); pb.inputs['Roughness'].default_value = rough


def medic(name, gender, years, hair, coat=(0.86, 0.87, 0.85)):
    """Doctor or nurse in a white coat (long-sleeved top and trousers in white)."""
    cloth = "female_elegantsuit01" if gender < 0.5 else "male_casualsuit01"
    h = person(name, gender, years, cloth, hair, hv=0.25)
    recolor(h, cloth, coat)
    return h
