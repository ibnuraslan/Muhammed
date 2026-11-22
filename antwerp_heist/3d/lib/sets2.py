"""More sets for the Antwerp film: offices, the security room (and the alarm monitoring centre), the street outside
the Diamond Center, the Turin flat / workshop, the building maquette, and the soft orange 'ripple' bands.
Each builder returns a dict of anchors (world points / matrices) for the shots."""
import math, random
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix
import ship as S
import ph
from sets import (flat, emit, enamel, steel_paint, brushed, tex, paper_mat, gold, box, light_area, light_point,
                  light_spot, world, _bm_obj)


def _ph(aid, loc, rot_z=0.0, scale=1.0):
    try:
        return ph.model(aid, loc=loc, rot_z=rot_z, scale=scale)
    except Exception as e:
        print("ph model fallback", aid, e)
        return None, []


def plane(name, c, size, mat, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_plane_add(size=1, location=c, rotation=rot)
    o = bpy.context.active_object; o.name = name; o.scale = (size[0], size[1], 1)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if mat:
        o.data.materials.append(mat)
    return o


def image_mat(name, path, strength=1.0, emissive=True):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(path, check_existing=True)
    if emissive:
        N.remove(N["Principled BSDF"]); e = N.new("ShaderNodeEmission"); e.inputs['Strength'].default_value = strength
        L.new(t.outputs['Color'], e.inputs['Color']); L.new(e.outputs[0], N["Material Output"].inputs['Surface'])
    else:
        L.new(t.outputs['Color'], N["Principled BSDF"].inputs['Base Color'])
    return m


def crt_mat(name, tint=(0.35, 0.45, 0.4), strength=2.5, scale=3.0, seed=0.0):
    """A CCTV monitor showing a grey-green camera picture (noise + scan lines), for monitors far from camera."""
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    N.remove(N["Principled BSDF"])
    tc = N.new("ShaderNodeTexCoord")
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = 3
    nz.noise_dimensions = '4D'; nz.inputs['W'].default_value = seed
    L.new(tc.outputs['Generated'], nz.inputs['Vector'])
    wv = N.new("ShaderNodeTexWave"); wv.wave_type = 'BANDS'; wv.bands_direction = 'Y'; wv.inputs['Scale'].default_value = 120
    L.new(tc.outputs['Generated'], wv.inputs['Vector'])
    mx = N.new("ShaderNodeMath"); mx.operation = 'MULTIPLY'; L.new(nz.outputs['Fac'], mx.inputs[0])
    mr = N.new("ShaderNodeMapRange"); mr.inputs['To Min'].default_value = 0.75; L.new(wv.outputs['Fac'], mr.inputs['Value'])
    L.new(mr.outputs[0], mx.inputs[1])
    e = N.new("ShaderNodeEmission"); e.inputs['Color'].default_value = (*tint, 1)
    sc = N.new("ShaderNodeMath"); sc.operation = 'MULTIPLY'; sc.inputs[1].default_value = strength; L.new(mx.outputs[0], sc.inputs[0])
    L.new(sc.outputs[0], e.inputs['Strength']); L.new(e.outputs[0], N["Material Output"].inputs['Surface'])
    return m


def blueprint_mat(name="blueprint"):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    br = N.new("ShaderNodeTexBrick"); br.inputs['Scale'].default_value = 9; br.inputs['Mortar Size'].default_value = 0.008
    br.inputs['Color1'].default_value = (0.04, 0.12, 0.38, 1); br.inputs['Color2'].default_value = (0.05, 0.14, 0.42, 1)
    br.inputs['Mortar'].default_value = (0.75, 0.8, 0.9, 1); br.offset = 0.0; br.squash = 1.0
    L.new(tc.outputs['UV'], br.inputs['Vector'])
    gr = N.new("ShaderNodeTexBrick"); gr.inputs['Scale'].default_value = 40; gr.inputs['Mortar Size'].default_value = 0.01
    gr.inputs['Color1'].default_value = (1, 1, 1, 1); gr.inputs['Color2'].default_value = (1, 1, 1, 1); gr.inputs['Mortar'].default_value = (0.8, 0.85, 1, 1)
    L.new(tc.outputs['UV'], gr.inputs['Vector'])
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 0.25
    L.new(br.outputs['Color'], mx.inputs[6]); L.new(gr.outputs['Color'], mx.inputs[7])
    L.new(mx.outputs[2], p.inputs['Base Color']); p.inputs['Roughness'].default_value = 0.9
    return m


def blinds(name, x0, x1, y, z0, z1, mat, tilt=35.0, gap=0.035):
    """Venetian blind slats across a window (tilt in degrees)."""
    z = z1
    k = 0
    while z > z0:
        box(f"{name}_slat", ((x0 + x1) / 2, y, z), (x1 - x0, 0.025, 0.002), mat, rot=(math.radians(tilt), 0, 0)); z -= gap; k += 1
    return k


def chair(name, loc, yaw, mat_seat, mat_frame, seat_h=0.46, back=True):
    """A simple four-legged chair (kitchen / office visitor): seat top at seat_h, facing yaw (deg, 0 = +x)."""
    root = bpy.data.objects.new(name, None); bpy.context.scene.collection.objects.link(root)
    parts = [box(name + "_seat", (0, 0, seat_h - 0.02), (0.44, 0.42, 0.04), mat_seat, bevel=0.008)]
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(S.cyl(name + "_leg", (sx * 0.19, sy * 0.18, 0), (sx * 0.19, sy * 0.18, seat_h - 0.04), 0.014, mat=mat_frame, verts=10))
    if back:
        for sy in (-1, 1):
            parts.append(S.cyl(name + "_post", (-0.19, sy * 0.18, seat_h - 0.04), (-0.21, sy * 0.18, seat_h + 0.42), 0.014, mat=mat_frame, verts=10))
        parts.append(box(name + "_backrest", (-0.205, 0, seat_h + 0.3), (0.025, 0.4, 0.18), mat_seat, bevel=0.006))
    for o in parts:
        o.parent = root
    root.location = loc; root.rotation_euler = (0, 0, math.radians(yaw))
    return root


def office_chair(name, loc, yaw, seat_h=0.445):
    """Swivel office chair: padded seat (top at seat_h, 1 cm under the sitter's seat point), tall padded back,
    gas column on a five-star base. Faces yaw (deg, 0 = +x)."""
    up = flat(name + "_uph", (0.05, 0.04, 0.035), 0.75); mt = flat(name + "_metal", (0.05, 0.05, 0.055), 0.35, metal=0.8)
    root = bpy.data.objects.new(name, None); bpy.context.scene.collection.objects.link(root)
    parts = [box(name + "_seat", (0.02, 0, seat_h - 0.04), (0.46, 0.46, 0.08), up, bevel=0.025),
             box(name + "_back", (-0.24, 0, seat_h + 0.3), (0.07, 0.44, 0.5), up, bevel=0.03),
             S.cyl(name + "_spine", (-0.24, 0, seat_h - 0.05), (-0.22, 0, seat_h + 0.06), 0.02, mat=mt, verts=10),
             S.cyl(name + "_column", (0, 0, 0.08), (0, 0, seat_h - 0.08), 0.025, mat=mt, verts=16)]
    for k in range(5):
        a = 2 * math.pi * k / 5
        parts.append(S.cyl(name + "_leg", (0, 0, 0.08), (0.3 * math.cos(a), 0.3 * math.sin(a), 0.05), 0.016, mat=mt, verts=8))
        parts.append(S.cyl(name + "_castor", (0.3 * math.cos(a), 0.3 * math.sin(a), 0.05), (0.3 * math.cos(a), 0.3 * math.sin(a), 0.0), 0.022, mat=mt, verts=10))
    for o in parts:
        o.parent = root
    root.location = loc; root.rotation_euler = (0, 0, math.radians(yaw))
    return root


def table(name, c, size, top_mat, leg_mat, h=0.76):
    root = bpy.data.objects.new(name, None); bpy.context.scene.collection.objects.link(root)
    parts = [box(name + "_top", (0, 0, h - 0.02), (size[0], size[1], 0.04), top_mat, bevel=0.006),
             box(name + "_apron", (0, 0, h - 0.07), (size[0] - 0.2, size[1] - 0.2, 0.06), top_mat)]
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(box(name + "_leg", (sx * (size[0] / 2 - 0.06), sy * (size[1] / 2 - 0.06), (h - 0.04) / 2), (0.05, 0.05, h - 0.04), leg_mat))
    for o in parts:
        o.parent = root
    root.location = c
    return root


def phone(name, loc, yaw=0.0):
    """A 1990s office desk phone (base + handset on its cradle)."""
    m = flat(name + "_plastic", (0.08, 0.08, 0.085), 0.4)
    root = bpy.data.objects.new(name, None); bpy.context.scene.collection.objects.link(root)
    a = box(name + "_base", (0, 0, 0.03), (0.2, 0.22, 0.06), m, bevel=0.015)
    b = box(name + "_handset", (-0.06, 0, 0.075), (0.05, 0.21, 0.035), m, bevel=0.014)
    k = box(name + "_keys", (0.04, -0.02, 0.062), (0.08, 0.1, 0.006), flat(name + "_keys", (0.4, 0.4, 0.38), 0.5))
    for o in (a, b, k):
        o.parent = root
    root.location = loc; root.rotation_euler = (0, 0, math.radians(yaw))
    return root


# ----------------------------------------------------------------------------- ripple bands (house rule)
def ripple_bands(center, normal, radii, width=0.06, color=(1.0, 0.45, 0.12), strength=3.0, alpha=0.55, name="ripple"):
    """Filled, soft orange bands (annuli) around a point: the only way we draw a sensor's field or a signal.
    Each band fades from its middle to its edges (no hard lines)."""
    mat = bpy.data.materials.new(name + "_mat"); mat.use_nodes = True; N = mat.node_tree.nodes; L = mat.node_tree.links
    N.remove(N["Principled BSDF"])
    tc = N.new("ShaderNodeTexCoord")
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs['UV'], sep.inputs[0])
    # UV.y runs 0 (inner edge) .. 1 (outer edge): bell profile
    m1 = N.new("ShaderNodeMath"); m1.operation = 'SUBTRACT'; m1.inputs[1].default_value = 0.5; L.new(sep.outputs['Y'], m1.inputs[0])
    m2 = N.new("ShaderNodeMath"); m2.operation = 'ABSOLUTE'; L.new(m1.outputs[0], m2.inputs[0])
    m3 = N.new("ShaderNodeMapRange"); m3.inputs['From Min'].default_value = 0.0; m3.inputs['From Max'].default_value = 0.5
    m3.inputs['To Min'].default_value = alpha; m3.inputs['To Max'].default_value = 0.0; L.new(m2.outputs[0], m3.inputs['Value'])
    e = N.new("ShaderNodeEmission"); e.inputs['Color'].default_value = (*color, 1); e.inputs['Strength'].default_value = strength
    tr = N.new("ShaderNodeBsdfTransparent")
    mx = N.new("ShaderNodeMixShader"); L.new(m3.outputs[0], mx.inputs[0]); L.new(tr.outputs[0], mx.inputs[1]); L.new(e.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], N["Material Output"].inputs['Surface'])
    mat.blend_method = 'BLEND' if hasattr(mat, "blend_method") else None
    objs = []
    n = Vector(normal).normalized(); q = n.to_track_quat('Z', 'Y')
    for r in radii:
        bm = bmesh.new(); seg = 96
        uvl = bm.loops.layers.uv.new("UVMap")
        inner = [bm.verts.new((math.cos(2 * math.pi * k / seg) * (r - width / 2), math.sin(2 * math.pi * k / seg) * (r - width / 2), 0)) for k in range(seg)]
        outer = [bm.verts.new((math.cos(2 * math.pi * k / seg) * (r + width / 2), math.sin(2 * math.pi * k / seg) * (r + width / 2), 0)) for k in range(seg)]
        for k in range(seg):
            f = bm.faces.new((inner[k], inner[(k + 1) % seg], outer[(k + 1) % seg], outer[k]))
            for l, uv in zip(f.loops, ((k / seg, 0), ((k + 1) / seg, 0), ((k + 1) / seg, 1), (k / seg, 1))):
                l[uvl].uv = uv
        o = _bm_obj(name, bm, mat); bpy.context.scene.collection.objects.link(o)
        o.location = center; o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = q
        o.visible_shadow = False
        objs.append(o)
    return objs


# ----------------------------------------------------------------------------- office
def office(kind="leonardo", hour="day"):
    """A 1990s office on an upper floor of the Diamond Center: 5 x 4.2 m, ribbon window along y = +2.1 with blinds,
    metal desk facing the door (the person behind it sits with his back to the window), a visitor chair, a filing
    cabinet. kind: "leasing" (the building's rental office) | "leonardo" (his office, later with blueprints)."""
    A = {}
    RX, RY, RZ = 2.5, 2.1, 2.75
    carpet = tex("dirty_carpet", 1.5, tint=(0.55, 0.32, 0.22) if kind == "leonardo" else (0.3, 0.32, 0.38), name="carpet")
    wall = enamel("office_wall", (0.5, 0.44, 0.36) if kind == "leonardo" else (0.46, 0.44, 0.4), rough=0.85, var=0.08, scale=2)
    ceil = flat("office_ceil", (0.45, 0.43, 0.4), 0.9)
    box("off_floor", (0, 0, -0.05), (2 * RX + 0.4, 2 * RY + 0.4, 0.1), carpet)
    box("off_ceil", (0, 0, RZ + 0.05), (2 * RX + 0.4, 2 * RY + 0.4, 0.1), ceil)
    box("off_wall_door", (0, -RY - 0.1, RZ / 2), (2 * RX + 0.4, 0.2, RZ), wall)
    for sg in (1, -1):
        box("off_wall_side", (sg * (RX + 0.1), 0, RZ / 2), (0.2, 2 * RY + 0.4, RZ), wall)
    # window wall: sill 0.85, head 2.35, mullions
    WZ0, WZ1 = 0.85, 2.35
    box("off_win_sill", (0, RY + 0.1, WZ0 / 2), (2 * RX + 0.4, 0.2, WZ0), wall)
    box("off_win_head", (0, RY + 0.1, (WZ1 + RZ) / 2), (2 * RX + 0.4, 0.2, RZ - WZ1), wall)
    alu = flat("alu", (0.25, 0.24, 0.22), 0.35, metal=0.8)
    for k in range(5):
        x = -RX + k * (2 * RX) / 4
        box("off_mullion", (x, RY + 0.02, (WZ0 + WZ1) / 2), (0.06, 0.08, WZ1 - WZ0), alu)
    glass = bpy.data.materials.new("win_glass"); glass.use_nodes = True; gp = glass.node_tree.nodes["Principled BSDF"]
    gp.inputs['Transmission Weight'].default_value = 1.0; gp.inputs['Roughness'].default_value = 0.02; gp.inputs['IOR'].default_value = 1.05
    box("off_glass", (0, RY + 0.03, (WZ0 + WZ1) / 2), (2 * RX, 0.008, WZ1 - WZ0), glass)
    box("off_sill_board", (0, RY - 0.08, WZ0 + 0.01), (2 * RX, 0.22, 0.03), flat("sill", (0.3, 0.28, 0.25), 0.4))
    slat = flat("slat", (0.62, 0.56, 0.46), 0.5)
    blinds("blind", -RX + 0.05, -0.2, RY - 0.03, WZ0 + 0.55, WZ1 - 0.02, slat, tilt=40)          # left half: blinds half down
    box("blind_rail", (-(RX - 0.05 + 0.2) / 2 - 0.0, RY - 0.03, WZ1 - 0.01), (RX - 0.25, 0.05, 0.03), slat)
    # the view: the facade across the street (Antwerp brick + stone), daylight beyond
    brick = tex("red_brick_03", 3.0, tint=(0.9, 0.7, 0.55), name="far_brick")
    box("far_facade", (0, RY + 14, 6), (40, 0.5, 30), brick)
    winm = flat("far_win", (0.06, 0.07, 0.08), 0.15, metal=0.3)
    for ix in range(-6, 7):
        for iz in range(-1, 5):
            box("far_window", (ix * 2.4, RY + 13.7, 1.8 + iz * 3.2), (1.2, 0.1, 1.8), winm)
    # furniture
    desk_y = 0.75
    _ph("metal_office_desk", (0.0, desk_y, 0.0), rot_z=math.radians(180))
    A["desk_top"] = Vector((0, desk_y, 0.79)); A["desk_y"] = desk_y
    office_chair("boss_chair", (0.0, desk_y + 0.8, 0.0), -90)
    A["seat_behind"] = Vector((0, desk_y + 0.8, 0.46)); A["face_behind"] = -90.0        # faces -y (toward the door)
    A["seat_visitor"] = Vector((0.15, desk_y - 1.05, 0.46)); A["face_visitor"] = 90.0
    chair("visitor_chair", (0.15, desk_y - 1.05, 0), 90, flat("vchair_seat", (0.15, 0.08, 0.05), 0.6), flat("vchair_frame", (0.05, 0.05, 0.05), 0.3, 0.7))
    _ph("drawer_cabinet", (RX - 0.3, -0.6, 0), rot_z=math.radians(90))
    _ph("desk_lamp_arm_01", (-0.75, desk_y + 0.1, 0.79), rot_z=math.radians(200))
    phone("desk_phone", (0.65, desk_y + 0.1, 0.79), yaw=200)
    A["lamp"] = Vector((-0.75, desk_y - 0.2, 1.2))
    pm = paper_mat()
    for i, (x, y, r) in enumerate([(0.25, desk_y - 0.1, 0.1), (0.33, desk_y - 0.05, -0.2), (-0.3, desk_y + 0.05, 0.3)]):
        box("desk_paper", (x, y, 0.792), (0.21, 0.297, 0.0012), pm, rot=(0, 0, r))
    if kind == "leonardo":
        bp = blueprint_mat()
        box("blueprint", (-0.05, desk_y - 0.08, 0.7935), (1.1, 0.72, 0.0012), bp, rot=(0, 0, 0.04))
        box("blueprint2", (0.2, desk_y + 0.12, 0.7955), (0.9, 0.6, 0.0012), bp, rot=(0, 0, -0.12))
        A["blueprint"] = Vector((-0.05, desk_y - 0.08, 0.795))
    else:
        # leasing office: a key ring with two keys and an access card on the desk; a closed file
        brass = gold("key_brass", (0.7, 0.52, 0.25))
        bpy.ops.mesh.primitive_torus_add(major_radius=0.018, minor_radius=0.0018, location=(0.05, desk_y - 0.32, 0.7935))
        bpy.context.active_object.data.materials.append(brass)
        for k in range(2):
            box("key", (0.08 + 0.02 * k, desk_y - 0.34 - 0.01 * k, 0.7935), (0.055, 0.016, 0.002), brass, rot=(0, 0, 0.4 + 0.3 * k))
        box("access_card", (-0.06, desk_y - 0.3, 0.7935), (0.085, 0.054, 0.001), flat("card", (0.75, 0.72, 0.6), 0.4))
        box("file_closed", (-0.45, desk_y + 0.1, 0.81), (0.24, 0.32, 0.03), flat("file", (0.5, 0.12, 0.08), 0.6))
        A["keys"] = Vector((0.06, desk_y - 0.33, 0.795))
    # door (to the corridor) with frame
    box("off_door", (-1.6, -RY + 0.02, 1.0), (0.9, 0.04, 2.05), enamel("door_wood", (0.22, 0.12, 0.06), rough=0.5))
    # light: daylight through the window (the key), ceiling panel off, desk lamp warm
    sun = hour == "day"
    light_area("win_key", (0, RY + 0.8, 1.7), (0, -1, 0.8), 4.5, 380 if sun else 120, (1.0, 0.92, 0.8) if sun else (0.5, 0.6, 0.9),
               size_y=1.6)
    l = bpy.data.lights.new("off_sun", 'SUN'); l.energy = 3.2 if sun else 0.0; l.color = (1.0, 0.82, 0.6); l.angle = math.radians(1.5)
    so = bpy.data.objects.new("off_sun", l); bpy.context.scene.collection.objects.link(so)
    so.rotation_euler = (math.radians(62), 0, math.radians(200)); A["sun"] = so
    light_point("lamp_bulb", (-0.68, desk_y - 0.1, 1.15), 18 if sun else 35, (1.0, 0.7, 0.42), radius=0.03)
    # sky beyond the window
    w = world((0.55, 0.62, 0.72) if sun else (0.03, 0.04, 0.07), 0.22)
    A["window"] = Vector((0, RY, 1.6)); A["door"] = Vector((-1.6, -RY, 1.0)); A["RX"] = RX; A["RY"] = RY
    return A


# ----------------------------------------------------------------------------- security room (+ lobby door)
def security_room(kind="building", screen_images=None):
    """kind "building": the Diamond Center's security room upstairs: a wall of CCTV monitors over a console, the
    VCR rack recording every camera (the recordings stay in the building), a door to the lobby with a badge
    reader. kind "alarm": the alarm company's monitoring centre (night shift): consoles, a status board."""
    A = {}
    RX, RY, RZ = 2.6, 2.2, 2.7
    alarm = kind == "alarm"
    floor = tex("floor_tiles_06" if not alarm else "rubber_tiles", 1.2, tint=(0.5, 0.45, 0.38) if not alarm else (0.25, 0.27, 0.3), name="sec_floor")
    wall = enamel("sec_wall", (0.36, 0.33, 0.28) if not alarm else (0.18, 0.2, 0.22), rough=0.85, var=0.1)
    box("sec_floor", (0, 0, -0.05), (2 * RX + 0.4, 2 * RY + 0.4, 0.1), floor)
    box("sec_ceil", (0, 0, RZ + 0.05), (2 * RX + 0.4, 2 * RY + 0.4, 0.1), flat("sec_ceil", (0.3, 0.3, 0.29), 0.9))
    box("sec_wall_back", (0, RY + 0.1, RZ / 2), (2 * RX + 0.4, 0.2, RZ), wall)
    box("sec_wall_front", (0, -RY - 0.1, RZ / 2), (2 * RX + 0.4, 0.2, RZ), wall)
    box("sec_wall_R", (RX + 0.1, 0, RZ / 2), (0.2, 2 * RY + 0.4, RZ), wall)
    # left wall with the lobby door opening at y in [-1.4, -0.4]
    box("sec_wall_L_a", (-RX - 0.1, (0.0 - 0.4 + RY) / 2 + 0.0, RZ / 2), (0.2, RY + 0.4, RZ), wall)
    box("sec_wall_L_b", (-RX - 0.1, (-1.4 - RY) / 2, RZ / 2), (0.2, RY - 1.4, RZ), wall)
    box("sec_wall_L_top", (-RX - 0.1, -0.9, (2.1 + RZ) / 2), (0.2, 1.0, RZ - 2.1), wall)
    # monitor wall: 3 x 2 CRTs on a steel shelf + one big CRT in the console
    shelf = steel_paint("sec_shelf", (0.12, 0.12, 0.13), 0.4)
    box("mon_shelf_lo", (0, RY - 0.3, 1.05), (2.3, 0.55, 0.04), shelf)
    box("mon_shelf_hi", (0, RY - 0.3, 1.58), (2.3, 0.55, 0.04), shelf)
    for sx in (-1.15, 1.15):
        box("mon_upright", (sx, RY - 0.3, 1.1), (0.04, 0.55, 2.2), shelf)
    screens = []
    k = 0
    for row, z in enumerate((1.07, 1.6)):
        for col_, x in enumerate((-0.72, 0.0, 0.72)):
            root, ms = _ph("Television_01", (x, RY - 0.3, z), rot_z=math.radians(180))
            if screen_images and k < len(screen_images) and screen_images[k]:
                sm = image_mat(f"screen{k}", screen_images[k], 2.2)
            else:
                sm = crt_mat(f"screen{k}", tint=(0.36, 0.46, 0.4) if not alarm else (0.3, 0.42, 0.55), seed=k * 1.7)
            s = plane(f"crt_screen{k}", (x, RY - 0.3 - 0.215, z + 0.235), (0.43, 0.33), sm, rot=(math.radians(90), 0, 0))
            screens.append(s); k += 1
    A["screens"] = screens
    # console desk
    box("console", (0, RY - 0.88, 0.38), (2.4, 0.36, 0.76), steel_paint("console_paint", (0.2, 0.19, 0.17), 0.45))   # knee/toe space under the top
    box("console_top", (0, RY - 1.05, 0.775), (2.45, 0.75, 0.03), flat("console_top", (0.08, 0.075, 0.07), 0.35))
    # buttons / gate release on the console: a row of lit push buttons
    ledg = emit("btn_green", (0.1, 1.0, 0.25), 8); ledr = emit("btn_red", (1.0, 0.1, 0.05), 8)
    for i in range(6):
        box("console_btn", (-0.4 + i * 0.09, RY - 1.2, 0.795), (0.04, 0.04, 0.012), ledg if i % 3 else ledr)
    A["gate_button"] = Vector((-0.4, RY - 1.2, 0.8))
    office_chair("sec_chair", (0.2, 0.15, 0.0), 90)
    A["seat"] = Vector((0.2, 0.15, 0.47)); A["face"] = 90.0
    phone("sec_phone", (0.85, RY - 1.0, 0.79), yaw=180)
    # VCR rack on the right wall: time-lapse recorders and stacked tapes
    rack = steel_paint("rack", (0.06, 0.06, 0.065), 0.5)
    box("vcr_rack", (RX - 0.3, -0.9, 0.9), (0.55, 0.9, 1.8), rack)
    vcr = flat("vcr", (0.03, 0.03, 0.032), 0.4)
    for i in range(6):
        z = 0.25 + i * 0.26
        box("vcr", (RX - 0.58, -0.9, z), (0.02, 0.43, 0.09), vcr)
        box("vcr_led", (RX - 0.59, -0.75, z + 0.02), (0.004, 0.012, 0.006), ledr if i % 2 == 0 else ledg)
        box("vcr_slot", (RX - 0.59, -0.95, z), (0.004, 0.2, 0.01), flat("slot", (0, 0, 0), 0.5))
    tape = flat("tape", (0.02, 0.02, 0.02), 0.3); label = paper_mat("tape_label", (0.8, 0.78, 0.7))
    for i in range(14):
        box("vhs", (RX - 0.25, -1.3 + i * 0.03, 1.92), (0.19, 0.025, 0.105), tape)
        box("vhs_label", (RX - 0.25 - 0.096, -1.3 + i * 0.03, 1.92), (0.002, 0.02, 0.06), label)
    A["vcr"] = Vector((RX - 0.58, -0.9, 1.0))
    # lobby beyond the door: stone floor, glass entrance, badge reader on the door frame
    lob = tex("marble_01", 1.0, tint=(0.8, 0.75, 0.68), name="lobby_floor")
    box("lobby_floor", (-RX - 2.5, -0.9, -0.05), (5.0, 6.0, 0.1), lob)
    box("lobby_wall", (-RX - 5.0, -0.9, 1.6), (0.2, 6.0, 3.2), enamel("lobby_wall", (0.55, 0.5, 0.42), 0.6))
    box("lobby_ceil", (-RX - 2.5, -0.9, 3.25), (5.0, 6.0, 0.1), flat("lobby_ceil", (0.4, 0.38, 0.35), 0.8))
    for sg in (1, -1):
        box("lobby_side", (-RX - 2.5, -0.9 + sg * 3.0, 1.6), (5.0, 0.2, 3.2), enamel("lobby_wall2", (0.45, 0.4, 0.33), 0.6))
    reader = box("badge_reader", (-RX - 0.21, -1.52, 1.2), (0.03, 0.08, 0.12), flat("reader", (0.05, 0.05, 0.05), 0.4), bevel=0.005)
    box("badge_led", (-RX - 0.23, -1.52, 1.25), (0.006, 0.012, 0.006), ledg)
    A["badge_reader"] = Vector((-RX - 0.23, -1.52, 1.2)); A["lobby_door"] = Vector((-RX - 0.1, -0.9, 1.0))
    # light
    if not alarm:
        light_area("sec_ceiling", (0, 0, RZ - 0.05), (0, 0, 0), 1.2, 160, (1.0, 0.85, 0.65))
        light_area("lobby_light", (-RX - 2.5, -0.9, 3.15), (-RX - 2.5, -0.9, 0), 2.0, 420, (1.0, 0.88, 0.7))
    else:
        # status board on the back wall above the monitors: a grid of lamps, all green
        for i in range(10):
            for j in range(3):
                box("status_lamp", (-1.0 + i * 0.22, RY - 0.02, 2.1 + j * 0.15), (0.06, 0.01, 0.06), ledg)
        light_area("alarm_ceiling", (0, -0.5, RZ - 0.05), (0, -0.5, 0), 1.0, 40, (0.8, 0.85, 1.0))
    light_area("screen_glow", (0, RY - 0.7, 1.35), (0, -2, 1.1), 1.8, 25 if not alarm else 40, (0.6, 0.85, 0.75), size_y=0.9)
    world((0.01, 0.01, 0.01), 0.3)
    A["RX"] = RX; A["RY"] = RY
    return A


# ----------------------------------------------------------------------------- the street
def exterior(hour="dawn"):
    """Outside the Diamond Center (Schupstraat, Antwerp): a 1970s office block, stone-clad with ribbon windows over a
    recessed glazed entrance; bollards; the street and the houses opposite. The facade runs along x at y = 0,
    the street is y < 0. hour: "dawn" (the Monday morning) | "day" (2000)."""
    import look
    A = {}
    stone = enamel("dc_stone", (0.62, 0.55, 0.45), rough=0.8, var=0.12, scale=0.3)
    glassd = flat("dc_glass", (0.12, 0.15, 0.17), 0.08, metal=0.5)
    frame = flat("dc_frame", (0.1, 0.1, 0.1), 0.35, metal=0.8)
    L = 60.0; H_ = 24.0
    box("dc_block", (0, 6, H_ / 2 + 4.0), (L, 12, H_), stone)
    for iz in range(7):
        z = 5.2 + iz * 3.3
        box("dc_ribbon", (0, -0.03, z), (L - 2, 0.1, 1.6), glassd)
        box("dc_band", (0, -0.12, z - 1.0), (L - 1.5, 0.25, 0.25), stone)
        for ix in range(-14, 15):
            box("dc_mullion", (ix * 2.0, -0.1, z), (0.08, 0.1, 1.6), frame)
    # ground floor: recessed glazed entrance and a canopy
    box("dc_base_l", (-17.0, 3.0, 2.0), (26, 6, 4.0), stone); box("dc_base_r", (17.0, 3.0, 2.0), (26, 6, 4.0), stone)
    box("dc_entr_back", (0, 3.6, 2.0), (8.0, 0.2, 4.0), glassd)
    for ix in range(-4, 5):
        box("dc_entr_mull", (ix * 1.0, 3.45, 1.6), (0.06, 0.08, 3.2), frame)
    box("dc_canopy", (0, -0.6, 3.6), (9.0, 3.0, 0.25), frame)
    box("dc_entr_floor", (0, 1.6, 0.02), (8, 4.0, 0.04), tex("granite_tile", 1.0, tint=(0.6, 0.55, 0.5), name="entr_floor"))
    warm = emit("dc_lobby_glow", (1.0, 0.75, 0.45), 3.0)
    box("dc_lobby_glow", (0, 3.75, 1.8), (7.8, 0.02, 3.4), warm)
    # pavement, kerb, street, bollards, lamp posts
    box("pavement", (0, -2.5, -0.05), (L + 40, 5.0, 0.1), tex("concrete_pavers", 1.2, tint=(0.6, 0.55, 0.5), name="pavers"))
    box("kerb", (0, -5.05, 0.0), (L + 40, 0.2, 0.15), flat("kerb", (0.35, 0.34, 0.32), 0.7))
    box("street", (0, -10.0, -0.12), (L + 80, 10.0, 0.1), tex("asphalt_02", 3.0, tint=(0.55, 0.52, 0.5), name="asphalt"))
    box("pavement2", (0, -17.5, -0.05), (L + 40, 5.0, 0.1), tex("concrete_pavers", 1.2, tint=(0.6, 0.55, 0.5), name="pavers2"))
    bol = steel_paint("bollard", (0.08, 0.08, 0.09), 0.4)
    for ix in range(-12, 13):
        S.cyl("bollard", (ix * 2.2, -4.6, 0), (ix * 2.2, -4.6, 0.9), 0.1, mat=bol, verts=20)
    lampm = steel_paint("lamppost", (0.05, 0.06, 0.06), 0.45)
    for ix in (-20, 0, 20):
        S.cyl("lamppost", (ix, -4.8, 0), (ix, -4.8, 6.5), 0.08, mat=lampm, verts=16)
        box("lamphead", (ix, -5.6, 6.5), (0.4, 1.6, 0.15), lampm)
        if hour == "dawn":
            box("lamp_glass", (ix, -5.8, 6.41), (0.3, 0.6, 0.02), emit("sodium", (1.0, 0.55, 0.2), 25))
            light_spot("street_lamp", (ix, -5.8, 6.35), (ix, -6.0, 0), 900, angle=110, color=(1.0, 0.55, 0.22), radius=0.2)
    # houses opposite: brick terraces
    brick = tex("red_brick_03", 3.0, tint=(0.85, 0.62, 0.48), name="opp_brick")
    for ix in range(-6, 7):
        h = 11 + (ix * 7 % 5)
        box("opp_house", (ix * 7.5, -26.0, h / 2), (7.4, 12, h), brick)
        for k in range(3):
            for j in range(int(h // 3.2)):
                box("opp_win", (ix * 7.5 - 2.2 + k * 2.2, -19.95, 2.0 + j * 3.2), (1.1, 0.1, 1.6),
                    emit("opp_win_lit", (1.0, 0.72, 0.42), 2.0) if (hour == "dawn" and (ix + j + k) % 4 == 0) else flat("opp_win", (0.05, 0.06, 0.07), 0.1))
    if hour == "dawn":
        look.day_light("dusk", azim=120)
    else:
        import os as _os
        look.day_light("low_sun", azim=float(_os.environ.get("DAY_AZIM", "300")), elev=48, sky="blue", exposure=1.0)
    A["entrance"] = Vector((0, 1.0, 0)); A["door"] = Vector((0, 3.4, 1.2))
    return A


# ----------------------------------------------------------------------------- Turin
def turin_flat(hour="evening"):
    """A Turin flat: terracotta floor, ochre plaster, tall window with green louvred shutters, a kitchen table under a
    pendant lamp; by the second window a jeweller's bench (Leonardo's trade). Room x in [-3, 3], y in [-2.5, 2.5]."""
    A = {}
    RX, RY, RZ = 3.0, 2.5, 3.1
    floor = tex("terracotta_floor_tiles", 1.0, tint=(0.85, 0.6, 0.45), name="cotto")
    plaster = enamel("ochre", (0.55, 0.33, 0.14), rough=0.9, var=0.22, scale=1.0)
    box("t_floor", (0, 0, -0.05), (2 * RX + 0.4, 2 * RY + 0.4, 0.1), floor)
    box("t_ceil", (0, 0, RZ + 0.05), (2 * RX + 0.4, 2 * RY + 0.4, 0.1), flat("t_ceil", (0.45, 0.4, 0.33), 0.9))
    for sg in (1, -1):
        box("t_wall_x", (sg * (RX + 0.1), 0, RZ / 2), (0.2, 2 * RY + 0.4, RZ), plaster)
    box("t_wall_front", (0, -RY - 0.1, RZ / 2), (2 * RX + 0.4, 0.2, RZ), plaster)
    # back wall (y = +RY) with two tall windows at x = -1.4 and +1.6
    wins = (-1.4, 1.6); WW = 1.0; WZ0, WZ1 = 0.75, 2.55
    xs = sorted([(-RX - 0.2, wins[0] - WW / 2), (wins[0] + WW / 2, wins[1] - WW / 2), (wins[1] + WW / 2, RX + 0.2)])
    for a, b in xs:
        box("t_wall_back", ((a + b) / 2, RY + 0.1, RZ / 2), (b - a, 0.2, RZ), plaster)
    for x in wins:
        box("t_win_sill", (x, RY + 0.1, WZ0 / 2), (WW, 0.2, WZ0), plaster)
        box("t_win_head", (x, RY + 0.1, (WZ1 + RZ) / 2), (WW, 0.2, RZ - WZ1), plaster)
    green = enamel("shutter_green", (0.06, 0.16, 0.08), rough=0.6, var=0.15)
    wood = tex("wood_table_worn", 1.0, tint=(0.75, 0.55, 0.38), name="t_wood")
    for x in wins:
        # shutters folded half open outside, louvres
        for sg in (1, -1):
            px = x + sg * (WW / 2 - 0.12)
            box("shutter", (px, RY + 0.34, (WZ0 + WZ1) / 2), (0.25, 0.03, WZ1 - WZ0), green, rot=(0, 0, math.radians(sg * 60)))
        box("t_win_frame", (x, RY + 0.02, (WZ0 + WZ1) / 2), (WW, 0.06, 0.05), wood)
    # the city beyond: warm evening haze
    box("t_far", (0, RY + 12, 6), (40, 0.5, 20), tex("yellow_plaster", 3.0, tint=(0.9, 0.65, 0.4), name="t_far"))
    # kitchen table under a pendant lamp; chairs
    table("t_table", (0, 0.2, 0), (1.6, 0.9), wood, wood)
    A["table_top"] = Vector((0, 0.2, 0.76))
    seat = flat("rush", (0.35, 0.22, 0.1), 0.85); fr = flat("chair_wood", (0.12, 0.06, 0.03), 0.6)
    A["seats"] = {}
    for nm, (x, y, yaw) in {"W": (-1.27, 0.2, 0), "E": (1.27, 0.2, 180), "S": (0.1, -0.82, 90)}.items():
        chair("t_chair_" + nm, (x, y, 0), yaw, seat, fr)
        A["seats"][nm] = (Vector((x, y, 0.46)), yaw)
    S.cyl("pendant_cord", (0, 0.2, RZ), (0, 0.2, 1.75), 0.004, mat=flat("cord", (0.02, 0.02, 0.02), 0.5), verts=6)
    shade = flat("shade", (0.3, 0.12, 0.05), 0.5)
    S.cyl("pendant_shade", (0, 0.2, 1.75), (0, 0.2, 1.55), 0.06, 0.24, mat=shade, verts=32, caps=False)
    box("pendant_bulb", (0, 0.2, 1.6), (0.05, 0.05, 0.05), emit("bulb", (1.0, 0.7, 0.4), 40))
    light_point("pendant", (0, 0.2, 1.55), 120, (1.0, 0.68, 0.4), radius=0.05)
    A["lamp"] = Vector((0, 0.2, 1.55))
    # jeweller's bench by the right window
    bx = 1.6; by = RY - 0.45
    box("bench_top", (bx, by, 0.92), (1.1, 0.55, 0.05), wood)
    box("bench_body", (bx, by + 0.1, 0.45), (1.1, 0.35, 0.9), wood)
    box("bench_pin", (bx, by - 0.3, 0.92), (0.06, 0.12, 0.025), wood)
    box("bench_tray", (bx, by - 0.2, 0.7), (0.9, 0.3, 0.02), flat("leather_skin", (0.25, 0.12, 0.05), 0.7))
    au = gold()
    for i in range(5):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.008 + 0.002 * i, minor_radius=0.0015, location=(bx - 0.25 + i * 0.05, by - 0.05, 0.947))
        bpy.context.active_object.data.materials.append(au)
    for i in range(3):
        S.cyl("chain", (bx + 0.1 + i * 0.04, by - 0.15, 0.948), (bx + 0.25 + i * 0.03, by + 0.05, 0.948), 0.0025, mat=au, verts=8)
    A["bench"] = Vector((bx, by, 0.95)); A["bench_seat"] = Vector((bx, by - 0.75, 0.55))
    _ph("magnifying_glass_01", (bx - 0.35, by - 0.1, 0.945), rot_z=0.4)
    light_point("bench_lamp", (bx + 0.3, by, 1.6), 25, (1.0, 0.78, 0.5), radius=0.04)
    # evening light through the windows
    for x in wins:
        light_area("t_window", (x, RY + 0.6, 1.8), (x - 0.3, -1.0, 0.6), 1.0, 160 if hour == "evening" else 400,
                   (1.0, 0.62, 0.35) if hour == "evening" else (1.0, 0.9, 0.78), size_y=1.6)
    world((0.25, 0.18, 0.12), 0.25)
    A["RX"] = RX; A["RY"] = RY; A["windows"] = wins
    return A


# ----------------------------------------------------------------------------- maquette
def maquette():
    """An architect's model of the Diamond Center, cut open down the middle: seven office floors over the street,
    two floors underground, and the vault at the bottom (the only warm-lit room). Sits on a dark table; scale ~1:100."""
    A = {}
    card = flat("card", (0.78, 0.74, 0.66), 0.7)
    cut = flat("cut_face", (0.62, 0.58, 0.5), 0.75)
    dark = flat("table_dark", (0.03, 0.025, 0.02), 0.4)
    box("maq_table", (0, 0, -0.03), (2.4, 1.6, 0.06), dark)
    s = 0.01                       # 1 m -> 1 cm
    W_, D_ = 30 * s, 14 * s
    zg = 0.06 * 1                  # the street level sits up on a plinth so the basements show
    # ground around the footprint (cut away under the building so both basements show in section)
    for (cx, cy, sx, sy) in ((-(W_ / 2 + 0.03), 0.05, 0.06, D_ + 0.2), ((W_ / 2 + 0.03), 0.05, 0.06, D_ + 0.2),
                             (0, D_ / 2 + 0.05 + 0.0, W_, 0.1)):
        box("maq_ground", (cx, cy, zg / 2), (sx, sy, zg), cut)
    box("maq_ground_base", (0, 0.05, 0.003), (W_ + 0.12, D_ + 0.2, 0.006), cut)
    floors = 7; fh = 3.3 * s
    for f in range(floors):
        z = zg + f * fh
        box("maq_slab", (0, 0, z + 0.0015), (W_, D_, 0.003), card)
        for x in (-W_ / 2 + 0.003, W_ / 2 - 0.003):
            box("maq_col", (x, 0, z + fh / 2), (0.006, D_, fh), card)
        box("maq_back", (0, D_ / 2 - 0.0015, z + fh / 2), (W_, 0.003, fh), card)
        for k in range(6):
            box("maq_wall", (-W_ / 2 + (k + 0.5) * W_ / 6, 0.02, z + fh / 2), (0.002, D_ * 0.7, fh * 0.9), card)
    box("maq_roof", (0, 0, zg + floors * fh), (W_, D_, 0.004), card)
    # basements: -1 (garage) and -2 (vault level), cut open at the front (y = -D/2)
    b1 = zg - 3.0 * s; b2 = zg - 5.7 * s
    box("maq_b_slab1", (0, 0, b1), (W_, D_, 0.003), card); box("maq_b_slab2", (0, 0, b2), (W_, D_, 0.003), card)
    # carve: hollow the plinth where the basements are (front cut face)
    for x in (-W_ / 2, W_ / 2):
        box("maq_b_wall", (x, 0, (b2 + zg) / 2), (0.006, D_, zg - b2), card)
    box("maq_b_back", (0, D_ / 2, (b2 + zg) / 2), (W_, 0.006, zg - b2), card)
    # the vault room (lit warm) and its door
    vx, vw, vd = 0.04, 6 * s, 4.6 * s
    box("maq_vault_floor", (vx, 0.0, b2 + 0.002), (vw, vd, 0.002), flat("vault_floor_m", (0.55, 0.45, 0.32), 0.6))
    for (cx, cy, sx, sy) in ((vx - vw / 2, 0, 0.004, vd), (vx + vw / 2, 0, 0.004, vd), (vx, vd / 2, vw, 0.004)):
        box("maq_vault_wall", (cx, cy, b2 + 1.25 * s), (sx, sy, 2.5 * s), flat("maq_vault_wall", (0.62, 0.42, 0.22), 0.5))
    glow = emit("maq_vault_glow", (1.0, 0.62, 0.3), 6.0)
    box("maq_vault_light", (vx, 0.0, b2 + 2.4 * s), (vw * 0.8, vd * 0.6, 0.001), glow)
    light_point("maq_vault_lamp", (vx, -0.01, b2 + 2.0 * s), 0.5, (1.0, 0.6, 0.3), radius=0.005)
    A["vault"] = Vector((vx, 0, b2 + 1.2 * s)); A["street"] = Vector((0, -D_ / 2, zg)); A["top"] = Vector((0, 0, zg + floors * fh))
    # tiny cars and street level in front
    box("maq_street", (0, -D_ / 2 - 0.1, zg - 0.002), (W_ + 0.12, 0.2, 0.004), flat("maq_street", (0.2, 0.2, 0.2), 0.8))
    # a lamp over the model (warm key) and a cool rim
    light_spot("maq_key", (-0.5, -0.7, 0.9), (0, 0, 0.1), 60, angle=40, color=(1.0, 0.85, 0.65), radius=0.15)
    light_area("maq_rim", (0.6, 0.6, 0.5), (0, 0, 0.1), 0.6, 8, (0.7, 0.8, 1.0))
    world((0.02, 0.018, 0.016), 0.4)
    A["scale"] = s
    return A
