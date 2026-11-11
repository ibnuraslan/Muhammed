"""Shared helpers for YouTube thumbnails (16:9 stills, no text). Reusable for any film in this pipeline.

A thumbnail module `th_<name>.py` defines
    EXPOSURE (optional), LOOK (optional AgX look name)
    build(variant) -> ctx dict with at least
        cam   = (location, target, lens)          camera placement
        focus = Vector                            focus point (DOF)
        fstop = float                             aperture (small = blurrier background)
Run with  python thumb.py <name> [--pct 25] [--samples 32] [--out DIR]   (see thumb.py)

People: use people.man() / people.woman() from nvidia_doc/scenes (or a future film's people module) and pose them
with the helpers here: stand(), sit_on(), look_at(), gaze(), hold_phone().
"""
import math
import numpy as np
import bpy
from mathutils import Vector, Matrix, Quaternion
from kit import pbr, emissive, box, cyl, area_light, point_at, glass, haze
from human import reset_pose, fingers_curl, rotate_bone, aim_bone, reach, pose_walk, pose_sit, _world_verts, SIDE

THUMB_RES = (3840, 2160)


# ============================================================================ lights
def spot(loc, target, energy, color=(1, 1, 1), size_deg=40, blend=0.5, radius=0.05, name="Spot"):
    d = bpy.data.lights.new(name, 'SPOT'); d.energy = energy; d.color = color
    d.spot_size = math.radians(size_deg); d.spot_blend = blend; d.shadow_soft_size = radius
    o = bpy.data.objects.new(name, d); bpy.context.collection.objects.link(o); o.location = loc; point_at(o, target)
    return o


def soft(loc, target, energy, color=(1, 1, 1), size=0.5, size_y=None, hidden=True, name="Soft"):
    """Area light aimed at target; invisible to camera/reflections by default (a 'film light')."""
    o = area_light(loc, (0, 0, 0), size, energy, color); o.name = name
    if size_y:
        o.data.shape = 'RECTANGLE'; o.data.size_y = size_y
    point_at(o, target)
    if hidden:
        o.visible_camera = False; o.visible_glossy = False; o.visible_transmission = False
    return o


def point(loc, energy, color=(1, 1, 1), radius=0.1, name="Point"):
    d = bpy.data.lights.new(name, 'POINT'); d.energy = energy; d.color = color; d.shadow_soft_size = radius
    o = bpy.data.objects.new(name, d); bpy.context.collection.objects.link(o); o.location = loc
    return o


def light_only(o, objs):
    """Light linking: this light only lights `objs` (keeps a face light off the background)."""
    coll = bpy.data.collections.new(o.name + "_rx")
    for ob in objs:
        coll.objects.link(ob)
    try:
        o.light_linking.receiver_collection = coll
    except Exception:
        pass
    return coll


# ============================================================================ people
def ground(h, z=0.0):
    bpy.context.view_layer.update()
    w = np.concatenate([_world_verts(o) for o in h.parts if o.type == 'MESH'])
    h.arm.location.z += z - w[:, 2].min()
    bpy.context.view_layer.update()


def place(h, loc, face_deg):
    """Rotation z = θ makes the rest pose (facing −Y) face (sin θ, −cos θ)."""
    h.arm.rotation_euler = (0, 0, math.radians(face_deg)); h.arm.location = loc
    bpy.context.view_layer.update()


def face_dir(deg):
    a = math.radians(deg)
    return Vector((math.sin(a), -math.cos(a), 0))


def stand(h, weight_shift=0.0):
    """Relaxed standing pose: legs straight, arms down close to the body."""
    reset_pose(h)
    for sd, sg in SIDE.items():
        h.rot(f"upperarm01.{sd}", (0, 1, 0), sg * 34)
        h.rot(f"lowerarm01.{sd}", (1, 0, 0), -10)
    h.rot("upperleg01.L", (1, 0, 0), -3 * weight_shift); h.rot("upperleg01.R", (1, 0, 0), 4 * weight_shift)
    h.rot("lowerleg01.R", (1, 0, 0), 6 * weight_shift)
    fingers_curl(h, 22, thumb=8)


def sit_on(h, seat_xy, seat_z, face_deg, lean=6, hip_above=0.1):
    """Seated pose; hips placed over seat_xy, bottom of thighs on seat_z."""
    reset_pose(h)
    pose_sit(h, lean=lean)
    place(h, (seat_xy[0], seat_xy[1], 0), face_deg)
    bpy.context.view_layer.update()
    # shift so the hip joint sits over the seat point and the thighs rest on the seat
    hip = (h.bone_head("upperleg01.L") + h.bone_head("upperleg01.R")) / 2
    h.arm.location.x += seat_xy[0] - hip.x; h.arm.location.y += seat_xy[1] - hip.y
    bpy.context.view_layer.update()
    hip = (h.bone_head("upperleg01.L") + h.bone_head("upperleg01.R")) / 2
    h.arm.location.z += seat_z + hip_above - hip.z       # hip joint sits ~10 cm above the cushion surface
    bpy.context.view_layer.update()


def look_at(h, target, amount=1.0, neck=0.35):
    """Turn neck + head toward a world point (yaw then pitch)."""
    bpy.context.view_layer.update()
    hd = h.bone_head("head") + Vector((0, 0, 0.08))
    d = Vector(target) - hd
    yaw_body = h.arm.rotation_euler.z
    fwd = Vector((math.sin(yaw_body), -math.cos(yaw_body), 0))
    flat = Vector((d.x, d.y, 0)).normalized()
    yaw = math.degrees(math.atan2(fwd.cross(flat).z, fwd.dot(flat))) * amount
    pitch = math.degrees(math.atan2(d.z, Vector((d.x, d.y)).length)) * amount
    rotate_bone(h.arm, "neck01", (0, 0, 1), yaw * neck); rotate_bone(h.arm, "head", (0, 0, 1), yaw * (1 - neck))
    side = Vector((-flat.y, flat.x, 0))            # pitch about the horizontal axis across the look direction
    rotate_bone(h.arm, "neck01", side, -pitch * neck); rotate_bone(h.arm, "head", side, -pitch * (1 - neck))


def gaze(h, target):
    """Point both eyeballs at a world point (iris = local −Y of the eye sphere)."""
    bpy.context.view_layer.update()
    for e in h.eyes:
        c = e.matrix_world.to_translation()
        q = (Vector(target) - c).normalized().to_track_quat('-Y', 'Z')
        e.matrix_world = Matrix.Translation(c) @ q.to_matrix().to_4x4()


def brow_down(h, deg=6):
    """A guarded, frowning tilt: chin down a touch so the brow shadows the eyes."""
    rotate_bone(h.arm, "head", Vector(h.arm.matrix_world.to_3x3() @ Vector((1, 0, 0))), deg)


# ============================================================================ props
def phone(screen_col=(0.55, 0.8, 1.0), strength=6.0):
    """A plain modern phone (no brand): dark glass slab, rounded, glowing screen. Origin at centre, screen +Z."""
    body = box("PhoneBody", (0, 0, 0), (0.072, 0.152, 0.008), pbr("PhoneBody", (0.02, 0.02, 0.022), 0.25, 0.8), bevel=0.006)
    scr_m = bpy.data.materials.new("PhoneScreen"); scr_m.use_nodes = True
    N = scr_m.node_tree.nodes; L = scr_m.node_tree.links; p = N["Principled BSDF"]
    p.inputs['Base Color'].default_value = (0, 0, 0, 1); p.inputs['Roughness'].default_value = 0.05
    tc = N.new("ShaderNodeTexCoord"); gr = N.new("ShaderNodeTexGradient"); gr.gradient_type = 'LINEAR'
    mp = N.new("ShaderNodeMapping"); mp.inputs['Rotation'].default_value = (0, 0, math.radians(90))
    L.new(tc.outputs['Generated'], mp.inputs['Vector']); L.new(mp.outputs[0], gr.inputs['Vector'])
    cr = N.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (*[c * 0.5 for c in screen_col], 1); cr.color_ramp.elements[1].color = (*screen_col, 1)
    L.new(gr.outputs['Fac'], cr.inputs['Fac']); L.new(cr.outputs['Color'], p.inputs['Emission Color'])
    p.inputs['Emission Strength'].default_value = strength
    scr = box("PhoneScreen", (0, 0, 0.0041), (0.066, 0.144, 0.0004), scr_m, bevel=0.004)
    scr.parent = body
    return body, scr


def rain_curtains(ys, width=16, height=8, x0=0.0, density=0.93, strength=0.6, color=(0.75, 0.8, 0.9), axis="y", z0=0.0):
    """Vertical planes of fine rain streaks (camera-visible only), at distances `ys` along the view axis."""
    rm = bpy.data.materials.new("RainStreaks"); rm.use_nodes = True
    N = rm.node_tree.nodes; L = rm.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); tc = N.new("ShaderNodeTexCoord")
    mp = N.new("ShaderNodeMapping"); mp.inputs['Scale'].default_value = (width * 45, height * 3.5, 1)
    wn = N.new("ShaderNodeTexWhiteNoise"); wn.noise_dimensions = '2D'
    L.new(tc.outputs['UV'], mp.inputs['Vector']); L.new(mp.outputs[0], wn.inputs['Vector'])
    gt = N.new("ShaderNodeMath"); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = density; L.new(wn.outputs['Value'], gt.inputs[0])
    sc = N.new("ShaderNodeMath"); sc.operation = 'MULTIPLY'; sc.inputs[1].default_value = 0.4; L.new(gt.outputs[0], sc.inputs[0])
    tr = N.new("ShaderNodeBsdfTransparent"); gl = N.new("ShaderNodeEmission"); gl.inputs['Color'].default_value = (*color, 1); gl.inputs['Strength'].default_value = strength
    mx = N.new("ShaderNodeMixShader"); L.new(sc.outputs[0], mx.inputs[0]); L.new(tr.outputs[0], mx.inputs[1]); L.new(gl.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], out.inputs['Surface'])
    planes = []
    for k, y in enumerate(ys):
        if axis == "y":
            bpy.ops.mesh.primitive_plane_add(size=1, location=(x0, y, z0 + height / 2), rotation=(math.radians(90), 0, 0))
        else:
            bpy.ops.mesh.primitive_plane_add(size=1, location=(y, x0, z0 + height / 2), rotation=(math.radians(90), 0, math.radians(90)))
        o = bpy.context.active_object; o.name = "Rain"; o.scale = (width, height, 1); o.data.materials.append(rm)
        o.visible_shadow = False; o.visible_diffuse = False; o.visible_glossy = False; o.visible_volume_scatter = False
        planes.append(o)
    return planes


def glow_card(loc, size, color, strength, rot=(0, 0, 0), name="Glow"):
    """A soft emissive card (practical light source shape, e.g. a sign seen out of focus)."""
    return box(name, loc, size, emissive(name, color, strength), rot=rot)


def strip_lettering():
    """Thumbnails carry no words: hide every text object from the reused sets and put a plain glowing panel
    (same colour, same footprint) in its place, so the sign still reads as light out of focus."""
    bpy.context.view_layer.update()
    for o in [o for o in bpy.data.objects if o.type == 'FONT']:
        mat = o.data.materials[0] if o.data.materials else None
        col, st = (1, 0.8, 0.6), 6.0
        if mat and mat.use_nodes and "Principled BSDF" in mat.node_tree.nodes:
            p = mat.node_tree.nodes["Principled BSDF"]
            col = tuple(p.inputs['Emission Color'].default_value)[:3]; st = p.inputs['Emission Strength'].default_value
        pts = [o.matrix_world @ Vector(b) for b in o.bound_box]
        lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
        hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
        size = tuple(max(0.02, v) for v in (hi - lo))
        o.hide_render = True; o.hide_viewport = True
        box("Glow", tuple((lo + hi) / 2), size, emissive("GlowPanel", col, st * 0.35))


def surface_z(x, y, z_from=2.0, ignore=()):
    """Height of the first surface below (x, y, z_from) - e.g. a Poly Haven sofa cushion or table top."""
    dg = bpy.context.evaluated_depsgraph_get()
    o = Vector((x, y, z_from))
    for _ in range(8):
        hit, loc, n, i, ob, m = bpy.context.scene.ray_cast(dg, o, Vector((0, 0, -1)))
        if not hit:
            return None
        if ob.name not in ignore and not ob.name.startswith(("Rain", "Haze")):
            return loc.z
        o = loc - Vector((0, 0, 0.001))
    return None


def asset(aid, loc=(0, 0, 0), rot_deg=0.0, scale=1.0, floor=None, fit=None):
    """Poly Haven model, optionally rested on z=floor and/or scaled so its largest footprint side = fit (m)."""
    import ph
    root, meshes = ph.model(aid, loc=loc, rot_z=math.radians(rot_deg), scale=scale)
    lo, hi = ph.bounds(meshes)
    if fit:
        k = fit / max(hi.x - lo.x, hi.y - lo.y); root.scale = (scale * k,) * 3
        bpy.context.view_layer.update(); lo, hi = ph.bounds(meshes)
    if floor is not None:
        root.location.z += floor - lo.z
        bpy.context.view_layer.update(); lo, hi = ph.bounds(meshes)
    return root, meshes, lo, hi
