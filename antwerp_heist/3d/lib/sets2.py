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
                  light_spot, world, _bm_obj, haze_box)


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


def cctv_mat(name, path, strength=1.8):
    """A CCTV monitor showing a recorded picture: grey, contrasty, grainy, with scan lines (no on-screen text)."""
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    N.remove(N["Principled BSDF"])
    tc = N.new("ShaderNodeTexCoord")
    t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(path, check_existing=True)
    bw = N.new("ShaderNodeRGBToBW"); L.new(t.outputs['Color'], bw.inputs['Color'])
    ct = N.new("ShaderNodeMapRange"); ct.inputs['From Min'].default_value = 0.08; ct.inputs['From Max'].default_value = 0.75
    L.new(bw.outputs['Val'], ct.inputs['Value'])
    gr = N.new("ShaderNodeTexNoise"); gr.inputs['Scale'].default_value = 900; gr.inputs['Detail'].default_value = 0
    L.new(tc.outputs['UV'], gr.inputs['Vector'])
    mix = N.new("ShaderNodeMix"); mix.data_type = 'FLOAT'; mix.inputs['Factor'].default_value = 0.22
    L.new(ct.outputs['Result'], mix.inputs['A']); L.new(gr.outputs['Fac'], mix.inputs['B'])
    wv = N.new("ShaderNodeTexWave"); wv.wave_type = 'BANDS'; wv.bands_direction = 'Y'; wv.inputs['Scale'].default_value = 60
    L.new(tc.outputs['UV'], wv.inputs['Vector'])
    sl = N.new("ShaderNodeMapRange"); sl.inputs['To Min'].default_value = 0.78; L.new(wv.outputs['Fac'], sl.inputs['Value'])
    mul = N.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'; L.new(mix.outputs['Result'], mul.inputs[0]); L.new(sl.outputs['Result'], mul.inputs[1])
    tint = N.new("ShaderNodeMix"); tint.data_type = 'RGBA'; tint.blend_type = 'MULTIPLY'; tint.inputs['Factor'].default_value = 1.0
    L.new(mul.outputs['Value'], tint.inputs['A']); tint.inputs['B'].default_value = (0.86, 0.95, 0.9, 1)
    e = N.new("ShaderNodeEmission"); e.inputs['Strength'].default_value = strength
    L.new(tint.outputs['Result'], e.inputs['Color']); L.new(e.outputs[0], N["Material Output"].inputs['Surface'])
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
    import detail as DT
    wall = DT.wall_paint("office_wall", (0.52, 0.48, 0.42) if kind == "leonardo" else (0.48, 0.47, 0.44), rough=0.85, scuff=0.5)
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
    GN = glass.node_tree.nodes; GL = glass.node_tree.links          # sunlight passes the pane (shadow rays see it as clear)
    lp_ = GN.new("ShaderNodeLightPath"); tr_ = GN.new("ShaderNodeBsdfTransparent"); mx_ = GN.new("ShaderNodeMixShader")
    GL.new(lp_.outputs['Is Shadow Ray'], mx_.inputs[0]); GL.new(gp.outputs[0], mx_.inputs[1]); GL.new(tr_.outputs[0], mx_.inputs[2])
    GL.new(mx_.outputs[0], GN["Material Output"].inputs['Surface'])
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
    _ph("desk_lamp_arm_01", (0.8, desk_y + 0.15, 0.79), rot_z=math.radians(160))
    phone("desk_phone", (-0.7, desk_y + 0.1, 0.79), yaw=160)
    A["lamp"] = Vector((0.75, desk_y - 0.15, 1.2))
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
    # light design: soft daylight through the window as the key, the ceiling fluorescents on (an office at work: the room
    # is never a black cave against a white window), a warm desk lamp as the practical. The window sits ~1.5 stops over
    # the room, not 5.
    sun = hour == "day"
    # mood: a warm low window key raking in, the sky's cool fill, the ceiling tubes off by day so the room falls
    # off into its corners; a little dust in the window light
    light_area("win_key", (0.9, RY + 0.6, 1.5), (-0.4, -1, 0.8), 3.0, 260 if sun else 60, (1.0, 0.8, 0.58) if sun else (0.5, 0.6, 0.9),
               size_y=1.2)
    light_area("win_bounce", (0, RY - 0.3, 0.3), (0, -0.5, 1.4), 3.5, 10 if sun else 8, (1.0, 0.86, 0.7), size_y=0.6)   # sill/floor bounce
    if sun:
        haze_box("office_haze", (0, RY - 1.0, 1.5), (2 * RX, 2.2, 2.6), density=0.018, aniso=0.6, color=(1.0, 0.92, 0.82))
    panel = emit("ceil_panel", (1.0, 0.95, 0.86), 0.05 if sun else 4.0)
    for x, y in ((-1.1, -0.6), (1.1, -0.6), (0.0, 0.9)):
        box("ceil_fluo", (x, y, RZ - 0.008), (1.2, 0.6, 0.012), panel)
        if not sun:
            light_area("ceil_light", (x, y, RZ - 0.03), (x, y, 0), 1.0, 110, (1.0, 0.92, 0.8), size_y=0.5)
    l = bpy.data.lights.new("off_sun", 'SUN'); l.energy = 2.2 if sun else 0.0; l.color = (1.0, 0.84, 0.64); l.angle = math.radians(1.5)
    so = bpy.data.objects.new("off_sun", l); bpy.context.scene.collection.objects.link(so)
    so.rotation_euler = (math.radians(58), 0, math.radians(15)); A["sun"] = so     # behind the office: sunlit facade across the street, soft sky light inside
    light_point("lamp_bulb", (0.68, desk_y - 0.1, 1.15), 18 if sun else 35, (1.0, 0.7, 0.42), radius=0.03)
    # sky beyond the window
    w = world((0.42, 0.52, 0.75) if sun else (0.03, 0.04, 0.07), 0.3 if sun else 0.07)      # cool sky fill
    A["window"] = Vector((0, RY, 1.6)); A["door"] = Vector((-1.6, -RY, 1.0)); A["RX"] = RX; A["RY"] = RY
    return A


# ----------------------------------------------------------------------------- security room (+ lobby door)
def security_room(kind="building", screen_images=None, night=False):
    """kind "building": the Diamond Center's security room upstairs: a wall of CCTV monitors over a console, the
    VCR rack recording every camera (the recordings stay in the building), a door to the lobby with a badge
    reader. kind "alarm": the alarm company's monitoring centre (night shift): consoles, a status board."""
    A = {}
    RX, RY, RZ = 2.6, 2.2, 2.7
    alarm = kind == "alarm"
    floor = tex("floor_tiles_06" if not alarm else "rubber_tiles", 1.2, tint=(0.5, 0.45, 0.38) if not alarm else (0.25, 0.27, 0.3), name="sec_floor")
    import detail as DT
    wall = DT.wall_paint("sec_wall", (0.42, 0.4, 0.36) if not alarm else (0.2, 0.21, 0.22), rough=0.85)
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
            root, ms = _ph("Television_01", (x, RY - 0.3, z), rot_z=0.0)        # screen toward the room
            if screen_images and k < len(screen_images) and screen_images[k]:
                sm = image_mat(f"screen{k}", screen_images[k], 2.2)
            else:
                sm = crt_mat(f"screen{k}", tint=(0.36, 0.46, 0.4) if not alarm else (0.3, 0.42, 0.55), seed=k * 1.7)
            s = plane(f"crt_screen{k}", (x - 0.065, RY - 0.3 - 0.214, z + 0.262), (0.4, 0.31), sm, rot=(math.radians(90), 0, 0))
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
    if not alarm and not night:
        light_area("sec_ceiling", (0, 0, RZ - 0.05), (0, 0, 0), 1.2, 160, (1.0, 0.85, 0.65))
        light_area("lobby_light", (-RX - 2.5, -0.9, 3.15), (-RX - 2.5, -0.9, 0), 2.0, 420, (1.0, 0.88, 0.7))
    elif night:
        light_area("lobby_night", (-RX - 2.5, -0.9, 3.15), (-RX - 2.5, -0.9, 0), 1.0, 60, (1.0, 0.7, 0.45))
    else:
        # status board on the back wall above the monitors: a grid of lamps, all green
        for i in range(10):
            for j in range(3):
                box("status_lamp", (-1.0 + i * 0.22, RY - 0.02, 2.1 + j * 0.15), (0.06, 0.01, 0.06), ledg)
        light_area("alarm_ceiling", (0, -0.5, RZ - 0.05), (0, -0.5, 0), 1.0, 40, (0.8, 0.85, 1.0))
    light_area("screen_glow", (0, RY - 0.7, 1.35), (0, -2, 1.1), 1.8, 140 if night else (25 if not alarm else 40), (0.6, 0.85, 0.75), size_y=0.9)
    if night:                                   # the monitors are the room's light at night: their glow on the console, chair and rack
        light_area("screen_glow_low", (0, RY - 0.75, 1.0), (0, 0, 0.5), 1.6, 60, (0.55, 0.8, 0.72), size_y=0.6)
        light_area("screen_glow_rack", (RX - 1.2, -0.9, 1.4), (RX - 0.3, -0.9, 1.0), 0.6, 6, (0.6, 0.85, 0.75))
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
    import detail as DT
    conc = DT.wall_paint("dc_precast", (0.56, 0.53, 0.48), rough=0.88, scuff=0.0, z_dirty=0.6)
    conc2 = DT.wall_paint("dc_precast_dark", (0.36, 0.34, 0.31), rough=0.9, scuff=0.0, z_dirty=0.6)
    glassd = flat("dc_glass", (0.1, 0.12, 0.13), 0.06, metal=0.5)
    frame = flat("dc_frame", (0.09, 0.085, 0.08), 0.35, metal=0.8)
    L = 56.0; floors = 8; fh = 3.2; z0 = 4.4
    H_ = floors * fh
    # body behind the precast skin (windows recessed 0.35 m)
    box("dc_core", (0, 6.4, z0 + H_ / 2), (L, 12, H_), conc2)
    box("dc_glass_plane", (0, 0.36, z0 + H_ / 2), (L - 1, 0.05, H_), glassd)
    for f in range(floors + 1):
        z = z0 + f * fh
        # precast spandrel band: chamfered, heavy 1970s horizontal
        box("dc_spandrel", (0, 0.0, z - 0.45), (L + 0.6, 0.7, 0.9), conc, bevel=0.04)
    # vertical fins every 1.8 m (the facade rhythm), deeper at the corners
    nf = int(L / 1.8)
    for k in range(nf + 1):
        x = -L / 2 + k * (L / nf)
        d = 0.9 if k in (0, nf) else 0.55
        box("dc_fin", (x, 0.1 - d / 2 + 0.35, z0 + H_ / 2), (0.28, d, H_ + 0.1), conc, bevel=0.03)
        # window mullions between fins
        box("dc_mullion", (x + L / nf / 2, 0.33, z0 + H_ / 2), (0.05, 0.06, H_), frame)
    box("dc_roof_edge", (0, 0.1, z0 + H_ + 0.3), (L + 0.8, 0.9, 0.6), conc, bevel=0.04)
    # ground floor: recessed glazed lobby behind square pilotis
    box("dc_gf_back", (0, 4.0, z0 / 2), (L, 0.3, z0), conc2)
    box("dc_gf_glass", (0, 3.8, 1.7), (14.0, 0.06, 3.4), glassd)
    for ix in range(-7, 8):
        box("dc_gf_mull", (ix * 1.0, 3.75, 1.7), (0.05, 0.08, 3.4), frame)
    for k in range(-6, 7):
        box("dc_pilotis", (k * (L / 13), 0.35, z0 / 2), (0.7, 0.7, z0), conc, bevel=0.03)
    box("dc_gf_soffit", (0, 2.0, z0 - 0.15), (L, 4.0, 0.3), conc2)
    box("dc_entr_floor", (0, 2.0, 0.02), (L, 4.0, 0.04), tex("granite_tile", 1.0, tint=(0.6, 0.55, 0.5), name="entr_floor"))
    warm = emit("dc_lobby_glow", (1.0, 0.78, 0.5), 3.0)
    box("dc_lobby_glow", (0, 3.9, 1.8), (13.8, 0.02, 3.3), warm)
    for x in (-4.0, 0.0, 4.0):
        light_point("soffit_light", (x, 1.8, z0 - 0.35), 120, (1.0, 0.8, 0.55), radius=0.2)
    # neighbours: brick and stone houses either side
    nb = tex("red_brick_03", 3.0, tint=(0.7, 0.55, 0.45), name="nb_brick")
    for sx in (-1, 1):
        box("neighbour", (sx * (L / 2 + 6), 5.5, 8.0), (12, 11, 16), nb)
        for j in range(4):
            for k in range(3):
                box("nb_win", (sx * (L / 2 + 2.5 + k * 3.2), -0.02, 2.5 + j * 3.4), (1.2, 0.1, 1.8), flat("nb_win", (0.06, 0.07, 0.08), 0.1))
    # security: steel anti-ram posts with reflective bands along the kerb, a guard cabin, barrier, planters
    post = steel_paint("sec_post", (0.06, 0.065, 0.07), 0.4); refl = flat("reflect", (0.75, 0.72, 0.6), 0.3, metal=0.4)
    for ix in range(-14, 15):
        x = ix * 1.6
        S.cyl("sec_post", (x, -4.55, 0), (x, -4.55, 1.05), 0.11, mat=post, verts=20)
        S.cyl("sec_post_band", (x, -4.55, 0.82), (x, -4.55, 0.9), 0.113, mat=refl, verts=20)
        S.cyl("sec_post_cap", (x, -4.55, 1.05), (x, -4.55, 1.09), 0.09, mat=post, verts=20)
    box("guard_cabin", (-14.0, -3.0, 1.3), (2.2, 1.8, 2.6), steel_paint("cabin", (0.25, 0.27, 0.27), 0.5), bevel=0.04)
    box("guard_cabin_win", (-14.0, -3.92, 1.6), (1.6, 0.04, 0.9), emit("cabin_glow", (1.0, 0.82, 0.6), 1.5))
    box("barrier_arm", (-10.5, -4.0, 1.0), (5.0, 0.08, 0.08), flat("barrier", (0.7, 0.05, 0.04), 0.4))
    for x in (-7.0, 7.0, 18.0, -20.0):
        box("planter", (x, -1.6, 0.3), (1.6, 1.0, 0.6), conc, bevel=0.03)
        box("planter_soil", (x, -1.6, 0.6), (1.5, 0.9, 0.02), flat("soil", (0.05, 0.035, 0.02), 0.9))
        for k in range(5):
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.25, location=(x - 0.5 + k * 0.25, -1.6 + (k % 2) * 0.2 - 0.1, 0.8))
            bpy.context.active_object.data.materials.append(flat("shrub", (0.06, 0.12, 0.04), 0.8))
    DT.sign((-9.0, -0.0, 3.2), (0, -1, 0), kind="notice", w=0.6, h=0.4)
    # pavement, kerb, street, bollards, lamp posts
    box("pavement", (0, -2.5, -0.05), (L + 40, 5.0, 0.1), tex("concrete_pavers", 1.2, tint=(0.6, 0.55, 0.5), name="pavers"))
    box("kerb", (0, -5.05, 0.0), (L + 40, 0.2, 0.15), flat("kerb", (0.35, 0.34, 0.32), 0.7))
    box("street", (0, -10.0, -0.12), (L + 80, 10.0, 0.1), tex("asphalt_02", 3.0, tint=(0.55, 0.52, 0.5), name="asphalt"))
    box("pavement2", (0, -17.5, -0.05), (L + 40, 5.0, 0.1), tex("concrete_pavers", 1.2, tint=(0.6, 0.55, 0.5), name="pavers2"))
    lampm = steel_paint("lamppost", (0.05, 0.06, 0.06), 0.45)
    for ix in (-20, 0, 20):
        S.cyl("lamppost", (ix, -4.8, 0), (ix, -4.8, 6.5), 0.08, mat=lampm, verts=16)
        box("lamphead", (ix, -5.6, 6.5), (0.4, 1.6, 0.15), lampm)
        if hour in ("dawn", "night"):
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
                    emit("opp_win_lit", (1.0, 0.72, 0.42), 2.0) if (hour in ("dawn", "night") and (ix + j + k) % 4 == 0) else flat("opp_win", (0.05, 0.06, 0.07), 0.1))
    if hour == "night":
        import city
        city.sky("night")
        moon = bpy.data.lights.new("moon", 'SUN'); moon.energy = 0.06; moon.color = (0.55, 0.65, 1.0)
        mo = bpy.data.objects.new("moon", moon); bpy.context.scene.collection.objects.link(mo); mo.rotation_euler = (math.radians(50), 0, math.radians(200))
    elif hour == "dawn":
        look.day_light("dusk", azim=120)
    else:
        import os as _os
        look.day_light("low_sun", azim=float(_os.environ.get("DAY_AZIM", "300")), elev=48, sky="blue", exposure=1.0)
    A["entrance"] = Vector((0, 1.0, 0)); A["door"] = Vector((0, 3.8, 1.2))
    return A


# ----------------------------------------------------------------------------- Turin
def turin_flat(hour="evening"):
    """A Turin flat: terracotta floor, ochre plaster, tall window with green louvred shutters, a kitchen table under a
    pendant lamp; by the second window a jeweller's bench (Leonardo's trade). Room x in [-3, 3], y in [-2.5, 2.5]."""
    A = {}
    RX, RY, RZ = 3.0, 2.5, 3.1
    import detail as DT
    floor = tex("terracotta_floor_tiles", 1.0, tint=(0.68, 0.55, 0.46), name="cotto")
    plaster = DT.wall_paint("t_plaster", (0.56, 0.52, 0.45), rough=0.88, scuff=0.4)
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
    green = enamel("shutter_green", (0.13, 0.16, 0.13), rough=0.6, var=0.15)
    wood = tex("wood_table_worn", 1.0, tint=(0.75, 0.55, 0.38), name="t_wood")
    for x in wins:
        # shutters folded half open outside, louvres
        for sg in (1, -1):
            px = x + sg * (WW / 2 - 0.12)
            box("shutter", (px, RY + 0.34, (WZ0 + WZ1) / 2), (0.25, 0.03, WZ1 - WZ0), green, rot=(0, 0, math.radians(sg * 60)))
        box("t_win_frame", (x, RY + 0.02, (WZ0 + WZ1) / 2), (WW, 0.06, 0.05), wood)
    # the city beyond: warm evening haze
    box("t_far", (0, RY + 12, 6), (40, 0.5, 20), tex("yellow_plaster", 3.0, tint=(0.72, 0.64, 0.56), name="t_far"))
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
    light_point("pendant", (0, 0.2, 1.55), 120, (1.0, 0.78, 0.55), radius=0.05)
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
                   (1.0, 0.76, 0.56) if hour == "evening" else (1.0, 0.92, 0.82), size_y=1.6)
    world((0.2, 0.18, 0.16), 0.25)
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
        box("maq_vault_wall", (cx, cy, b2 + 1.25 * s), (sx, sy, 2.5 * s), flat("maq_vault_wall", (0.52, 0.51, 0.48), 0.7))
    # the vault reads as the vault: its walls lined with tiny steel boxes, lit from inside (warm but not a blob)
    steel_m = flat("maq_boxes", (0.6, 0.6, 0.62), 0.35, metal=0.8); seam = flat("maq_seam", (0.15, 0.15, 0.16), 0.5)
    for (cx, cy, sx, sy) in ((vx - vw / 2 + 0.003, 0, 0.001, vd * 0.95), (vx + vw / 2 - 0.003, 0, 0.001, vd * 0.95), (vx, vd / 2 - 0.003, vw * 0.95, 0.001)):
        box("maq_box_wall", (cx, cy, b2 + 1.0 * s), (sx, sy, 1.8 * s), steel_m)
        n = 8
        for r in range(1, 5):
            box("maq_box_seam", (cx, cy, b2 + 0.1 * s + r * 0.36 * s), (max(sx, 0.0012), max(sy, 0.0012), 0.0006), seam)
    box("maq_vault_door", (vx - vw / 2 + 0.012, -vd / 2 + 0.002, b2 + 1.0 * s), (0.016, 0.003, 2.0 * s), flat("maq_door", (0.3, 0.3, 0.32), 0.3, metal=0.9))
    box("maq_vault_light", (vx, 0.0, b2 + 2.45 * s), (vw * 0.5, vd * 0.15, 0.0008), emit("maq_vault_glow", (1.0, 0.85, 0.65), 3.0))
    light_point("maq_vault_lamp", (vx, -0.005, b2 + 2.2 * s), 0.45, (1.0, 0.85, 0.65), radius=0.003)
    A["vault"] = Vector((vx, 0, b2 + 1.2 * s)); A["street"] = Vector((0, -D_ / 2, zg)); A["top"] = Vector((0, 0, zg + floors * fh))
    # tiny cars and street level in front
    box("maq_street", (0, -D_ / 2 - 0.1, zg - 0.002), (W_ + 0.12, 0.2, 0.004), flat("maq_street", (0.2, 0.2, 0.2), 0.8))
    # an architect's model, not a block: acrylic glazing on the uncut faces, white massing of the neighbours, a street
    # with model trees and cars, scale figures in the vault, the garage ramp
    acr = bpy.data.materials.new("acrylic"); acr.use_nodes = True; ap = acr.node_tree.nodes["Principled BSDF"]
    ap.inputs['Transmission Weight'].default_value = 1.0; ap.inputs['Roughness'].default_value = 0.08; ap.inputs['IOR'].default_value = 1.49
    ap.inputs['Base Color'].default_value = (0.85, 0.92, 0.95, 1)
    for x in (-W_ / 2 - 0.0015, W_ / 2 + 0.0015):
        box("maq_acrylic", (x, 0, zg + floors * fh / 2), (0.0015, D_, floors * fh), acr)
    mass = flat("maq_mass", (0.86, 0.84, 0.8), 0.75)
    import random as _r
    rng = _r.Random(2)
    for sx in (-1, 1):
        for k in range(3):
            w = rng.uniform(0.07, 0.11); h = rng.uniform(0.1, 0.2)
            x = sx * (W_ / 2 + 0.09 + k * 0.12)
            box("maq_neighbour", (x, 0.02, zg + h / 2), (w, D_ * 0.9, h), mass)
    fig = flat("maq_figure", (0.9, 0.9, 0.88), 0.6)
    for k, (dx, dy) in enumerate(((-0.012, 0.005), (0.008, -0.006), (0.018, 0.01))):
        S.cyl("maq_fig", (vx + dx, dy, b2 + 0.003), (vx + dx, dy, b2 + 0.016), 0.0018, mat=fig, verts=8)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=6, radius=0.0022, location=(vx + dx, dy, b2 + 0.0185))
        bpy.context.active_object.data.materials.append(fig)
    for k in range(6):                         # the garage ramp down to level -1, in steps of card
        box("maq_ramp", (-0.09, -D_ / 2 + 0.01 + k * 0.012, zg - k * 0.005), (0.06, 0.013, 0.003), card)
    # a lamp over the model (warm key) and a cool rim
    light_spot("maq_key", (-0.5, -0.7, 0.9), (0, 0, 0.1), 60, angle=40, color=(1.0, 0.85, 0.65), radius=0.15)
    light_area("maq_rim", (0.6, 0.6, 0.5), (0, 0, 0.1), 0.6, 8, (0.7, 0.8, 1.0))
    world((0.02, 0.018, 0.016), 0.4)
    A["scale"] = s
    return A


# ----------------------------------------------------------------------------- the underground garage
def garage(hour="night"):
    """The Diamond Center's underground garage (one level down): 22 x 16 m under a 2.5 m slab on a 5 m column grid,
    painted bays, cars under covers, pipes and a cable tray under the slab, a ramp rising toward the street at -y,
    the stairwell door (with its exit sign) at +y. Night: one tube in three on, sodium light spilling down the ramp."""
    import detail as DT, look
    A = {}
    GX, GY0, GY1, GZ = 11.0, -8.0, 8.0, 2.5
    floor = tex("garage_floor", 1.6, tint=(0.55, 0.53, 0.5), name="garage_floor")
    conc = DT.wall_paint("garage_conc", (0.46, 0.45, 0.42), rough=0.9, scuff=0.6, z_dirty=0.5)
    slab = DT.wall_paint("garage_slab", (0.38, 0.37, 0.35), rough=0.92, scuff=0.0)
    yellow = flat("bay_paint", (0.75, 0.6, 0.08), 0.6); white = flat("line_white", (0.75, 0.75, 0.72), 0.6)
    box("g_floor", (0, 0, -0.05), (2 * GX, GY1 - GY0, 0.1), floor)
    box("g_slab", (0, 0, GZ + 0.15), (2 * GX, GY1 - GY0, 0.3), slab)
    for sx in (-1, 1):
        box("g_wall", (sx * (GX + 0.1), 0, GZ / 2), (0.2, GY1 - GY0, GZ), conc)
    box("g_wall_back", (0, GY1 + 0.1, GZ / 2), (2 * GX, 0.2, GZ), conc)
    # front wall with the ramp opening (x in [-2.8, 2.8]) and the ramp rising to the street
    for sx in (-1, 1):
        box("g_wall_front", (sx * (GX + 2.8) / 2, GY0 - 0.1, GZ / 2), (GX - 2.8, 0.2, GZ), conc)
    RL = 10.0
    bpy.ops.mesh.primitive_plane_add(size=1)
    rp = bpy.context.active_object; rp.name = "g_ramp"; rp.scale = (5.6, RL, 1)
    bpy.ops.object.transform_apply(scale=True)
    rp.scale = (1.0, math.hypot(RL, 3.0) / RL, 1.0)
    rp.location = (0, GY0 - RL / 2, 1.5); rp.rotation_euler = (-math.atan2(3.0, RL), 0, 0); rp.data.materials.append(floor)
    so = rp.modifiers.new("t", "SOLIDIFY"); so.thickness = 0.2; so.offset = -1
    for sx in (-1, 1):
        box("g_ramp_wall", (sx * 2.9, GY0 - RL / 2, 1.0), (0.2, RL, 3.4), conc)
    box("g_ramp_roof", (0, GY0 - 2.0, GZ + 1.35), (5.8, 4.0, 0.3), slab)          # 2.3 m clear over the rising ramp
    box("g_ramp_header", (0, GY0 - 0.05, GZ + 0.6), (5.8, 0.3, 1.2), slab)
    # columns, bays, wheel stops
    cols = []
    for ix in range(-2, 3):
        for iy in range(-1, 2):
            x, y = ix * 5.0, iy * 5.0
            if abs(x) < 3 and iy == -1:
                continue
            box("g_column", (x, y, GZ / 2), (0.45, 0.45, GZ), conc, bevel=0.01)
            box("g_column_band", (x, y, 0.5), (0.47, 0.47, 1.0), yellow)
            cols.append(Vector((x, y)))
    A["columns"] = cols
    for side in (-1, 1):
        for k in range(8):
            x = side * (GX - 2.6); y = GY0 + 1.6 + k * 1.75
            box("bay_line", (x, y, 0.002), (5.0, 0.08, 0.004), white)
            box("wheel_stop", (side * (GX - 0.6), y + 0.9, 0.06), (0.15, 1.2, 0.12), yellow)
    box("aisle_arrow", (0, 2.0, 0.002), (0.25, 1.6, 0.004), white)
    # cars under covers in some bays (front toward the aisle)
    for side, k in ((-1, 0), (-1, 2), (-1, 3), (-1, 6), (1, 1), (1, 4), (1, 5), (1, 7)):
        _ph("covered_car", (side * (GX - 2.6), GY0 + 2.48 + k * 1.75, 0), rot_z=math.radians(90 if side < 0 else -90))
    # services under the slab
    DT.cable_tray((-GX + 0.6, GY0 + 0.5), (-GX + 0.6, GY1 - 0.5), GZ - 0.35, n_cables=5)
    pipe = flat("pipe_red", (0.35, 0.04, 0.03), 0.5, coat=0.3); pipe2 = flat("pipe_grey", (0.35, 0.35, 0.36), 0.4, metal=0.5)
    S.cyl("g_sprinkler_main", (-GX, 3.0, GZ - 0.2), (GX, 3.0, GZ - 0.2), 0.06, mat=pipe, verts=16)
    S.cyl("g_sprinkler_main2", (-GX, -3.0, GZ - 0.2), (GX, -3.0, GZ - 0.2), 0.06, mat=pipe, verts=16)
    S.cyl("g_duct", (GX - 1.0, GY0, GZ - 0.25), (GX - 1.0, GY1, GZ - 0.25), 0.18, mat=pipe2, verts=20)
    for x in range(-10, 11, 2):
        for y in (3.0, -3.0):
            S.cyl("sprinkler_head", (x, y, GZ - 0.26), (x, y, GZ - 0.32), 0.012, mat=pipe2, verts=8)
    # stairwell door at the back with exit sign, extinguisher, signage
    door = steel_paint("g_door", (0.12, 0.2, 0.28), 0.45)
    box("g_stair_door", (3.5, GY1 - 0.03, 1.02), (1.0, 0.06, 2.05), door)
    box("g_door_frame", (3.5, GY1 - 0.02, 1.06), (1.15, 0.04, 2.15), flat("frame", (0.1, 0.1, 0.1), 0.4))
    box("g_door_bar", (3.5, GY1 - 0.08, 1.0), (0.8, 0.04, 0.04), brushed())
    DT.sign((3.5, GY1 - 0.005, 2.3), (0, -1, 0), kind="exit")
    DT.extinguisher((2.2, GY1 - 0.005, 0.12), (0, -1, 0))
    DT.sign((-2.0, GY1 - 0.005, 1.6), (0, -1, 0), kind="notice", w=0.5, h=0.35)
    A["stair_door"] = Vector((3.5, GY1 - 0.1, 0))
    # lights: tube fittings on a grid; at night one in three burns
    on = emit("g_tube_on", (0.84, 1.0, 0.9), 9.0); off = flat("g_tube_off", (0.55, 0.55, 0.52), 0.4)   # cool fluorescent vs warm sodium
    k = 0
    for ix in range(-2, 3):
        for iy in (-5.5, -0.5, 4.5):
            x = ix * 5.0 + 2.5 if ix < 2 else ix * 5.0 - 2.5
            lit = (k % 3 == 0) or hour != "night"
            box("g_tube", (x, iy, GZ - 0.04), (0.12, 1.4, 0.06), on if lit else off)
            if lit:
                light_area("g_tube_light", (x, iy, GZ - 0.09), (x, iy, 0), 0.12, 300, (0.82, 1.0, 0.9), size_y=1.4)
            k += 1
    # ramp dressing: a striped height bar on chains, bulkhead lamps (one buzzing on), conduit, painted arrows, a hump
    stripe_y = flat("hb_yellow", (0.8, 0.62, 0.05), 0.5); stripe_k = flat("hb_black", (0.02, 0.02, 0.02), 0.5)
    for k in range(8):
        box("height_bar", (-2.45 + k * 0.7, GY0 + 0.45, 2.24), (0.7, 0.08, 0.12), stripe_y if k % 2 == 0 else stripe_k)
    for sx in (-1, 1):
        S.cyl("hb_chain", (sx * 2.6, GY0 + 0.45, 2.3), (sx * 2.6, GY0 + 0.45, GZ - 0.02), 0.006, mat=brushed(), verts=6)
    bulk = flat("bulkhead", (0.2, 0.2, 0.2), 0.4); bglow = emit("bulk_glow", (1.0, 0.85, 0.6), 6.0)
    for k, (sx, d) in enumerate(((-1, 2.0), (1, 5.0), (-1, 8.0))):
        y = GY0 - d; z = 1.8 + d * 0.3
        box("bulkhead", (sx * 2.76, y, z), (0.08, 0.32, 0.2), bulk, bevel=0.02)
        box("bulkhead_glass", (sx * 2.71, y, z), (0.02, 0.26, 0.14), bglow if k != 2 else flat("bulk_dead", (0.3, 0.3, 0.28), 0.3))
        if k != 2:
            light_point("bulkhead_light", (sx * 2.62, y, z), 35, (1.0, 0.8, 0.55), radius=0.06)
    cond = flat("conduit", (0.45, 0.45, 0.46), 0.4, metal=0.6)
    for sx in (-1, 1):
        S.cyl("conduit", (sx * 2.77, GY0 + 0.2, 2.25), (sx * 2.77, GY0 - RL, 2.25 + RL * 0.3), 0.022, mat=cond, verts=10)
    for k in range(3):
        y = GY0 - 2.5 - k * 3.0
        box("ramp_arrow", (0.9, y, (GY0 - y) * 0.3 + 0.012), (0.22, 1.0, 0.004), white, rot=(-math.atan2(3.0, RL), 0, 0))
    box("speed_hump", (0, GY0 - 0.6, 0.03), (5.4, 0.35, 0.06), stripe_y, bevel=0.02)
    # sodium street light spilling down the ramp
    light_area("ramp_spill", (0, GY0 - RL + 1.0, 4.5), (0, GY0, 0), 4.0, 600 if hour == "night" else 3000, (1.0, 0.6, 0.28))
    box("street_glow", (0, GY0 - RL - 0.5, 3.0), (6.0, 0.1, 4.0), emit("street_glow", (1.0, 0.55, 0.25), 1.2))
    world((0.01, 0.01, 0.01), 0.2)
    # oil stains and damp patches on the floor (glossy where wet), and the dust in the air that makes beams read
    import city
    city.wet_patches(floor, wet=0.6, scale=0.5)
    haze_box("garage_haze", (0, (GY0 + GY1) / 2 - 4, 2.0), (2 * GX, GY1 - GY0 + 10, 4.5), density=0.012, aniso=0.6, color=(1.0, 0.95, 0.9))
    A["ramp_top"] = Vector((0, GY0 - RL + 0.5, 3.0)); A["ramp_foot"] = Vector((0, GY0 + 0.5, 0)); A["GY0"] = GY0; A["GY1"] = GY1
    return A


# ----------------------------------------------------------------------------- the diamond district (maquette)
def district():
    """A planner's model of the diamond district (~1:500) on a dark table: a ring of city blocks, the three short
    streets of the district inside it (Hoveniersstraat, Schupstraat, Rijfstraat) with their gates, the Diamond Center
    block, and the garage ramp opening onto an outside street. Returns anchors: the district streets (for the soft
    orange band that marks police control) and the garage entrance."""
    A = {}
    card = flat("d_card", (0.78, 0.75, 0.68), 0.7); street = flat("d_street", (0.18, 0.17, 0.16), 0.8)
    dc = flat("d_dc", (0.45, 0.43, 0.4), 0.6)
    box("d_table", (0, 0, -0.03), (2.6, 1.8, 0.06), flat("d_table", (0.03, 0.025, 0.02), 0.4))
    box("d_base", (0, 0, 0.005), (1.4, 1.0, 0.01), street)
    s = 1 / 500.0
    rng = random.Random(4)
    # blocks on a skewed grid; the district streets run through the middle
    blocks = []
    for ix in range(-3, 4):
        for iy in range(-2, 3):
            cx, cy = ix * 0.19, iy * 0.19
            if abs(iy) == 0 and abs(ix) <= 1:
                continue                      # Hoveniersstraat corridor
            w = 0.15 + rng.uniform(-0.01, 0.01); h = 0.02 + rng.uniform(0, 0.04)
            o = box("d_block", (cx, cy, 0.01 + h / 2), (w, 0.15, h), card, bevel=0.002); blocks.append(o)
    # the Diamond Center: a tall slab on the north side of the district street
    box("d_dc_block", (0.0, 0.12, 0.01 + 0.06), (0.13, 0.06, 0.12), dc, bevel=0.002)
    box("d_dc_low", (0.0, 0.16, 0.01 + 0.012), (0.16, 0.06, 0.024), dc)
    A["dc"] = Vector((0.0, 0.12, 0.08))
    # district streets (pedestrian, gated): the corridor along y = 0 and two cross streets
    A["district_streets"] = [((-0.28, 0.0), (0.28, 0.0)), ((-0.095, -0.0), (-0.095, 0.2)), ((0.095, -0.2), (0.095, 0.0))]
    gate = flat("d_gate", (0.08, 0.08, 0.08), 0.4)
    for (a, b) in A["district_streets"]:
        for p in (a, b):
            box("d_gate_post", (p[0], p[1], 0.016), (0.01, 0.01, 0.012), gate)
    # garage ramp: opening onto the outer street behind the DC block (north), outside the district
    A["garage_entrance"] = Vector((0.0, 0.29, 0.012))
    box("d_ramp", (0.0, 0.25, 0.008), (0.03, 0.06, 0.004), flat("d_ramp", (0.08, 0.08, 0.08), 0.7))
    light_spot("d_key", (-0.7, -0.8, 1.0), (0, 0, 0), 120, angle=45, color=(1.0, 0.85, 0.65), radius=0.2)
    light_area("d_rim", (0.7, 0.8, 0.6), (0, 0, 0), 0.8, 10, (0.7, 0.8, 1.0))
    world((0.02, 0.018, 0.016), 0.4)
    return A


def soft_strip(p0, p1, z, width, color=(1.0, 0.45, 0.12), strength=2.5, alpha=0.5, name="band_strip"):
    """One filled soft orange band along a line (fades across its width): the house way to mark an area."""
    a, b = Vector((p0[0], p0[1], z)), Vector((p1[0], p1[1], z))
    mat = bpy.data.materials.new(name + "_mat"); mat.use_nodes = True; N = mat.node_tree.nodes; L = mat.node_tree.links
    N.remove(N["Principled BSDF"])
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs['UV'], sep.inputs[0])
    m1 = N.new("ShaderNodeMath"); m1.operation = 'SUBTRACT'; m1.inputs[1].default_value = 0.5; L.new(sep.outputs['Y'], m1.inputs[0])
    m2 = N.new("ShaderNodeMath"); m2.operation = 'ABSOLUTE'; L.new(m1.outputs[0], m2.inputs[0])
    m3 = N.new("ShaderNodeMapRange"); m3.inputs['From Max'].default_value = 0.5; m3.inputs['To Min'].default_value = alpha
    m3.inputs['To Max'].default_value = 0.0; L.new(m2.outputs[0], m3.inputs['Value'])
    e = N.new("ShaderNodeEmission"); e.inputs['Color'].default_value = (*color, 1); e.inputs['Strength'].default_value = strength
    tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader")
    L.new(m3.outputs[0], mx.inputs[0]); L.new(tr.outputs[0], mx.inputs[1]); L.new(e.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], N["Material Output"].inputs['Surface'])
    d = b - a; ln = d.length; yaw = math.atan2(d.y, d.x)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(a + b) / 2)
    o = bpy.context.active_object; o.name = name; o.scale = (ln + width, width, 1); o.rotation_euler = (0, 0, yaw)
    o.data.materials.append(mat); o.visible_shadow = False
    return o
