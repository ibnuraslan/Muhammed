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
    add_asset(h, "clothes", cloth, val=cval, rough=0.7, hue=hue, sat=sat)
    add_asset(h, "clothes", "shoes02", val=0.2, rough=0.4)
    if hair:
        add_asset(h, "hair", hair, val=hv, rough=0.45)
    return h


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
