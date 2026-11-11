"""Hero shot: a rainy night street of Singapore-style shophouses (covered five-foot-way arcades, neon signs),
wet asphalt full of reflections. A woman in a dark coat walks under an umbrella, filmed on a long lens from
across the street, foreground traffic and pillars sliding through frame. No real brands on the signs."""
import math
import numpy as np
import bpy
from mathutils import Vector, Matrix
from kit import *
from human import Human, add_asset, pose_walk, reset_pose, fingers_curl, rotate_bone, _world_verts

EXPOSURE = 0.5
BOUNCES = 8
STREET_W = 9.0            # kerb to kerb
SIDEWALK = 2.2            # open pavement between the kerb and the arcade line
ARCADE_D = 3.0            # five-foot-way depth
WALK_SPEED = 1.15         # m/s (real), shown in slow motion by the camera move timing
rng = np.random.default_rng(31)

NEON = [(1.0, 0.18, 0.35), (0.2, 0.85, 1.0), (1.0, 0.55, 0.12), (0.55, 0.3, 1.0), (0.3, 1.0, 0.55), (1.0, 0.95, 0.8)]


def wet_asphalt(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    puddle = N.new("ShaderNodeTexNoise"); puddle.inputs['Scale'].default_value = 0.35; puddle.inputs['Detail'].default_value = 6
    L.new(tc.outputs['Object'], puddle.inputs['Vector'])
    pm = N.new("ShaderNodeMapRange"); pm.inputs['From Min'].default_value = 0.48; pm.inputs['From Max'].default_value = 0.56
    L.new(puddle.outputs['Fac'], pm.inputs['Value'])
    grit = N.new("ShaderNodeTexNoise"); grit.inputs['Scale'].default_value = 140; grit.inputs['Detail'].default_value = 8
    L.new(tc.outputs['Object'], grit.inputs['Vector'])
    rr = N.new("ShaderNodeMapRange"); rr.inputs['To Min'].default_value = 0.16; rr.inputs['To Max'].default_value = 0.38
    L.new(grit.outputs['Fac'], rr.inputs['Value'])
    rough = N.new("ShaderNodeMix"); rough.data_type = 'FLOAT'
    L.new(pm.outputs[0], rough.inputs['Factor']); L.new(rr.outputs[0], rough.inputs[2]); rough.inputs[3].default_value = 0.015
    L.new(rough.outputs[0], p.inputs['Roughness'])
    col = N.new("ShaderNodeMix"); col.data_type = 'RGBA'
    L.new(pm.outputs[0], col.inputs['Factor']); col.inputs[6].default_value = (0.022, 0.022, 0.024, 1); col.inputs[7].default_value = (0.006, 0.006, 0.007, 1)
    L.new(col.outputs[2], p.inputs['Base Color'])
    # rain ripples in the puddles (fine noise bump only where wet)
    rip = N.new("ShaderNodeTexNoise"); rip.noise_dimensions = '4D'; rip.inputs['Scale'].default_value = 60; rip.inputs['Detail'].default_value = 2
    L.new(tc.outputs['Object'], rip.inputs['Vector'])
    bs = N.new("ShaderNodeMath"); bs.operation = 'MULTIPLY'; bs.inputs[1].default_value = 0.25
    L.new(pm.outputs[0], bs.inputs[0])
    gb = N.new("ShaderNodeMath"); gb.operation = 'SUBTRACT'; gb.inputs[0].default_value = 0.6; L.new(pm.outputs[0], gb.inputs[1])
    hsum = N.new("ShaderNodeMath"); hsum.operation = 'MULTIPLY_ADD'
    L.new(rip.outputs['Fac'], hsum.inputs[0]); L.new(bs.outputs[0], hsum.inputs[1])
    g2 = N.new("ShaderNodeMath"); g2.operation = 'MULTIPLY'; L.new(grit.outputs['Fac'], g2.inputs[0]); L.new(gb.outputs[0], g2.inputs[1])
    L.new(g2.outputs[0], hsum.inputs[2])
    b = N.new("ShaderNodeBump"); b.inputs['Strength'].default_value = 0.35; b.inputs['Distance'].default_value = 0.01
    L.new(hsum.outputs[0], b.inputs['Height']); L.new(b.outputs['Normal'], p.inputs['Normal'])
    p.inputs['Specular IOR Level'].default_value = 0.7
    m["ripple"] = rip.name
    return m


def plaster(name, color):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); oi = N.new("ShaderNodeObjectInfo")
    n = N.new("ShaderNodeTexNoise"); n.inputs['Scale'].default_value = 2.5; n.inputs['Detail'].default_value = 10
    L.new(tc.outputs['Object'], n.inputs['Vector'])
    hs = N.new("ShaderNodeHueSaturation"); hs.inputs['Color'].default_value = (*color, 1)
    hv = N.new("ShaderNodeMath"); hv.operation = 'MULTIPLY_ADD'; hv.inputs[1].default_value = 0.25; hv.inputs[2].default_value = 0.38
    L.new(oi.outputs['Random'], hv.inputs[0]); L.new(hv.outputs[0], hs.inputs['Hue'])
    stain = N.new("ShaderNodeMix"); stain.data_type = 'RGBA'; stain.blend_type = 'MULTIPLY'; stain.inputs['Factor'].default_value = 0.55
    L.new(hs.outputs['Color'], stain.inputs[6]); L.new(n.outputs['Color'], stain.inputs[7]); L.new(stain.outputs[2], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.75
    # wet sheen streaks
    mp = N.new("ShaderNodeMapping"); mp.inputs['Scale'].default_value = (8, 8, 0.5); L.new(tc.outputs['Object'], mp.inputs['Vector'])
    st = N.new("ShaderNodeTexNoise"); st.inputs['Scale'].default_value = 3; L.new(mp.outputs[0], st.inputs['Vector'])
    rr = N.new("ShaderNodeMapRange"); rr.inputs['To Min'].default_value = 0.25; rr.inputs['To Max'].default_value = 0.8
    L.new(st.outputs['Fac'], rr.inputs['Value']); L.new(rr.outputs[0], p.inputs['Roughness'])
    return m


def interior_material(col):
    m = bpy.data.materials.new("Interior"); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    br = N.new("ShaderNodeTexBrick"); br.inputs['Scale'].default_value = 2.5; br.inputs['Mortar Size'].default_value = 0.05
    br.inputs['Color1'].default_value = (0.6, 0.55, 0.5, 1); br.inputs['Color2'].default_value = (0.25, 0.22, 0.2, 1)
    L.new(tc.outputs['Object'], br.inputs['Vector'])
    gr = N.new("ShaderNodeTexGradient"); L.new(tc.outputs['Generated'], gr.inputs['Vector'])
    mul = N.new("ShaderNodeMix"); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs['Factor'].default_value = 1.0
    L.new(br.outputs['Color'], mul.inputs[6]); mul.inputs[7].default_value = (*col, 1)
    L.new(mul.outputs[2], p.inputs['Emission Color']); p.inputs['Emission Strength'].default_value = 0.45
    p.inputs['Base Color'].default_value = (0.05, 0.05, 0.05, 1)
    return m


SIGN_WORDS = ["NOODLE HOUSE", "KOPI", "24 HOURS", "HOTEL", "DIM SUM", "PHARMACY", "BAR", "LAUNDRY", "KARAOKE", "TEA"]


def neon_word(word, loc, size, col, side, vertical=False):
    mat = emissive("NeonTxt", col, 22)
    rot = (math.radians(90), 0, 0 if side > 0 else math.radians(180))    # side>0: row across the street, read from -Y
    o = text_obj("Neon", word, loc, size, mat, rot=rot, extrude=0.02, font_path="/usr/share/fonts/opentype/inter/Inter-Bold.otf")
    if vertical:
        o.rotation_euler = (math.radians(90), math.radians(-90), 0 if side > 0 else math.radians(180))
    return o


def sign_material(name, color, strength, flicker=False):
    m = emissive(name, color, strength)
    return m


def shophouse_row(y0, side, n, mats):
    """A row of 2-3 storey shophouses along X, facing the street; ground floor recessed behind an arcade."""
    face_y = y0                    # facade line (upper floors)
    out = dict(pillars=[], signs=[])
    x = -n * 2.8
    win_lit = window_material("ShopWin", lit=(1.0, 0.78, 0.5), density=0.45, floor=3.2, bay=1.3, strength=1.2, glass_col=(0.02, 0.02, 0.025))
    shutter = brushed_metal("Shutter", (0.07, 0.075, 0.08), (0.45, 0.6), 0.2, axis=(1, 1, 60))
    pillar_m = plaster("Pillar", (0.18, 0.16, 0.13))
    for k in range(n):
        w = rng.uniform(4.6, 6.2); h = rng.uniform(7.5, 11.0)
        cx = x + w / 2
        body = mats[k % len(mats)]
        d = 12.0
        # upper storeys overhang the arcade
        box("Upper", (cx, face_y + side * d / 2, 3.6 + (h - 3.6) / 2), (w - 0.05, d, h - 3.6), body)
        box("UpperWin", (cx, face_y - side * 0.01, 3.6 + (h - 3.6) / 2), (w * 0.82, 0.02, (h - 3.6) * 0.7), win_lit)
        box("Cornice", (cx, face_y - side * 0.15, h + 0.1), (w, 0.5, 0.3), body)
        box("ArcadeCeil", (cx, face_y + side * ARCADE_D / 2, 3.55), (w, ARCADE_D, 0.1), body)
        # shop front, recessed by the arcade depth: glowing interior or shutter
        sf_y = face_y + side * ARCADE_D
        if rng.random() < 0.7:
            col = (1.0, 0.85, 0.65) if rng.random() < 0.6 else (0.85, 0.95, 1.0)
            box("ShopBack", (cx, sf_y + side * 2.6, 1.6), (w * 0.86, 0.05, 2.8), interior_material(col))
            for q in range(3):     # shelves / counter silhouettes inside
                box("Shelf", (cx + rng.uniform(-1.6, 1.6), sf_y + side * rng.uniform(0.8, 2.2), rng.uniform(0.4, 1.0)),
                    (rng.uniform(0.6, 1.6), 0.5, rng.uniform(0.8, 2.0)), pbr("ShelfM", (0.04, 0.035, 0.03), 0.6))
            box("ShopCeil", (cx, sf_y + side * 1.3, 3.2), (w * 0.6, 0.15, 0.04), emissive("Tube", col, 5))

        else:
            box("Shutter", (cx, sf_y, 1.6), (w * 0.9, 0.06, 3.0), shutter)
        # arcade pillars on the facade line
        for px in (x + 0.25, x + w - 0.25):
            out["pillars"].append(box("Pillar", (px, face_y + side * 0.25, 1.8), (0.5, 0.5, 3.6), pillar_m, bevel=0.03))
        # neon / lightbox signs: vertical blade signs and horizontal boards
        c = NEON[int(rng.integers(0, len(NEON)))]
        if rng.random() < 0.6:
            s = box("Blade", (cx + rng.uniform(-1.5, 1.5), face_y - side * 0.6, rng.uniform(4.8, 6.5)), (0.12, 0.7, rng.uniform(1.6, 2.6)),
                    sign_material("Neon", c, rng.uniform(8, 18)))
            out["signs"].append(s)
        if rng.random() < 0.7:
            s = box("Board", (cx, face_y - side * 0.05, 3.95), (w * 0.7, 0.08, 0.55), sign_material("Board", c, rng.uniform(3, 7)))
            out["signs"].append(s)
        if rng.random() < 0.75:
            word = SIGN_WORDS[int(rng.integers(0, len(SIGN_WORDS)))]
            neon_word(word, (cx, face_y - side * 0.12, rng.uniform(4.3, 5.6)), rng.uniform(0.45, 0.7), NEON[int(rng.integers(0, len(NEON)))], side)
        # warm arcade downlight
        if rng.random() < 0.8:
            l = bpy.data.lights.new("ArcadeL", 'POINT'); l.energy = 60; l.color = (1.0, 0.75, 0.45); l.shadow_soft_size = 0.2
            o = bpy.data.objects.new("ArcadeL", l); bpy.context.collection.objects.link(o); o.location = (cx, face_y + side * ARCADE_D / 2, 3.35)
        x += w
    return out


def umbrella(radius=0.55):
    """Dark canopy (8 ribs) on a shaft, modelled at the origin, canopy top at z=0."""
    parts = []
    bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=radius, radius2=0.02, depth=0.28, location=(0, 0, -0.14))
    can = bpy.context.active_object
    can.data.materials.append(pbr("Canopy", (0.012, 0.012, 0.014), 0.3, 0.0, **{'Coat Weight': 0.8, 'Coat Roughness': 0.05}))
    sol = can.modifiers.new("s", 'SOLIDIFY'); sol.thickness = 0.004
    parts.append(can)
    shaft = cyl("Shaft", (0, 0, -0.45), 0.008, 0.85, pbr("ShaftM", (0.6, 0.6, 0.62), 0.25, 1.0), verts=12)
    parts.append(shaft)
    return parts


def build(variant=None):
    world_flat((0.006, 0.008, 0.014), 1.0)
    asphalt = wet_asphalt("Asphalt")
    box("Road", (0, 0, -0.05), (300, STREET_W, 0.1), asphalt)
    kerb = pbr("Kerb", (0.18, 0.18, 0.17), 0.3, 0.0, **{'Coat Weight': 0.5, 'Coat Roughness': 0.05})
    pave = wet_asphalt("Pavement"); pave.node_tree.nodes["Principled BSDF"].inputs['Base Color'].default_value = (0.05, 0.05, 0.05, 1)
    for side in (-1, 1):
        y = side * (STREET_W / 2 + (SIDEWALK + ARCADE_D) / 2)
        box("Pavement", (0, y, 0.08), (300, SIDEWALK + ARCADE_D, 0.16), pave)
        box("Kerb", (0, side * STREET_W / 2, 0.08), (300, 0.2, 0.17), kerb)
    bodies = [plaster(f"Body{k}", c) for k, c in enumerate([(0.20, 0.15, 0.11), (0.12, 0.16, 0.15), (0.22, 0.19, 0.15), (0.16, 0.11, 0.10), (0.15, 0.15, 0.17)])]
    far_row = shophouse_row(STREET_W / 2 + SIDEWALK, 1, 20, bodies)       # the side the woman walks along (y > 0)
    near_row = shophouse_row(-STREET_W / 2 - SIDEWALK, -1, 20, bodies)    # behind camera: reflections
    # streetlamps with sodium light + glow
    lampm = emissive("Lamp", (1.0, 0.62, 0.3), 40)
    for k in range(9):
        x = -44.5 + k * 10
        cyl("Pole", (x, -STREET_W / 2 + 0.4, 3.5), 0.06, 7.0, pbr("Pole", (0.03, 0.03, 0.03), 0.4, 0.8), verts=12)   # opposite kerb
        box("LampHead", (x, -STREET_W / 2 + 1.2, 7.0), (0.7, 0.3, 0.12), lampm)
        l = bpy.data.lights.new("Street", 'SPOT'); l.energy = 900; l.spot_size = math.radians(95); l.spot_blend = 0.6; l.color = (1.0, 0.65, 0.35)
        o = bpy.data.objects.new("Street", l); bpy.context.collection.objects.link(o); o.location = (x, -STREET_W / 2 + 1.2, 6.9)
    # distant towers closing the street, glowing
    tw = window_material("FarWin", lit=(0.9, 0.85, 0.75), density=0.3, floor=3.6, bay=1.6, strength=0.6)
    skyline(41, (125, 0, 0), (45, 90), 30, (40, 180), None, tw, footprint=(18, 35))   # beyond the junction, off the street
    # parked / passing cars for foreground occlusion
    paints = [(0.02, 0.02, 0.025), (0.5, 0.52, 0.55), (0.25, 0.02, 0.02)]
    cars = []
    for k, x in enumerate((-11.0, 6.5, 16.0)):
        paint = pbr(f"Paint{k}", paints[k], 0.25, 0.6, **{'Coat Weight': 1.0, 'Coat Roughness': 0.03})
        body = box("CarBody", (x, -STREET_W / 2 + 1.3, 0.75), (4.4, 1.8, 0.75), paint, bevel=0.25)
        cabin = box("CarCabin", (x - 0.2, -STREET_W / 2 + 1.3, 1.35), (2.4, 1.6, 0.6), glass("CarGlass", (0.2, 0.22, 0.25), 0.05), bevel=0.2)
        for dx in (-1.4, 1.4):
            for dy in (-0.85, 0.85):
                cyl("Wheel", (x + dx, -STREET_W / 2 + 1.3 + dy, 0.35), 0.35, 0.25, pbr("Tyre", (0.01, 0.01, 0.01), 0.6), rot=(math.radians(90), 0, 0))
        box("Tail", (x + 2.2, -STREET_W / 2 + 1.3, 0.85), (0.04, 1.5, 0.12), emissive("Tail", (1.0, 0.05, 0.03), 12))
        cars.append(body)
    # lantern strings across the street, overhead cables, distant traffic lights
    lant = pbr("Lantern", (0.6, 0.05, 0.03), 0.5, 0.0, **{'Emission Color': (1.0, 0.2, 0.08, 1), 'Emission Strength': 6.0, 'Subsurface Weight': 0.5})
    cable_m = pbr("Cable", (0.01, 0.01, 0.01), 0.5)
    for k in range(10):
        x = -6 + k * 5.5
        y0, y1 = -STREET_W / 2 - SIDEWALK + 0.2, STREET_W / 2 + SIDEWALK - 0.2
        box("Cable", (x, 0, 5.6), (0.015, y1 - y0, 0.015), cable_m)
        for j in range(6):
            y = y0 + (j + 0.5) * (y1 - y0) / 6
            sag = 0.35 * (1 - ((y - (y0 + y1) / 2) / ((y1 - y0) / 2)) ** 2)
            bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=10, radius=0.2, location=(x, y, 5.5 - sag))
            o = bpy.context.active_object; o.scale = (1, 1, 1.25); o.data.materials.append(lant)
    for k in range(6):   # head/tail lights far down the street
        x = 30 + k * 9; y = rng.choice([-2.2, 2.2])
        col = (1.0, 0.95, 0.85) if y < 0 else (1.0, 0.06, 0.03)
        for dy in (-0.7, 0.7):
            bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=0.09, location=(x, y + dy, 0.7))
            bpy.context.active_object.data.materials.append(emissive("CarLight", col, 60))
    # the street ends at a bright junction: a lit tower with big screens (generic colour fields, no brands), traffic signals
    tw2 = window_material("EndWin", lit=(0.95, 0.88, 0.75), density=0.3, floor=3.0, bay=1.2, strength=0.12)
    box("EndTower", (72, 0, 40), (20, 30, 80), tw2)
    for k, (z, col) in enumerate(((14, (0.2, 0.6, 1.0)), (24, (1.0, 0.3, 0.5)), (8, (1.0, 0.75, 0.3)))):
        box("Screen", (61.8, -4 + 6 * (k % 2), z), (0.2, 10, 5), emissive("Screen", col, 1.1))
    for y in (-STREET_W / 2 + 0.5, STREET_W / 2 - 0.5):
        cyl("SignalPole", (55, y, 2.5), 0.08, 5.0, pbr("Pole", (0.03, 0.03, 0.03), 0.4, 0.8))
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=0.16, location=(54.8, y, 4.6))
        bpy.context.active_object.data.materials.append(emissive("Signal", (1.0, 0.08, 0.05), 80))
    box("Cross", (66, 0, -0.04), (14, 60, 0.1), asphalt)
    if variant == "haze":
        haze((0, 0, 6), (200, 40, 12), density=0.0035, color=(0.75, 0.8, 0.9), anis=0.6)

    # ------------------------------------------------------------------ the woman
    h = Human("Walker", gender=0.0, years=38, muscle=0.45, weight=0.38, height=0.52,
              skin="middleage_lightskinned_female_diffuse.png", eyebrows="eyebrow001", eyelashes="eyelashes01")
    add_asset(h, "clothes", "female_elegantsuit01", hue=0.5, sat=0.2, val=0.18, rough=0.55, sheen=0.4)
    add_asset(h, "clothes", "shoes02", val=0.3, rough=0.3)
    add_asset(h, "hair", "long01", val=0.35, rough=0.4)
    um = umbrella()
    ctx = dict(h=h, umbrella=um, asphalt=asphalt, cars=cars)
    ctx["walk_y"] = STREET_W / 2 + 0.9                     # open pavement, in the rain and the sign light
    return ctx


def place_walker(c, t, x0=-3.0, seconds=6.0):
    """Pose and place the woman at time t in [0,1] of the shot (walking toward +X)."""
    h = c["h"]
    dist = WALK_SPEED * t * seconds * 0.5          # slow motion: half real speed over the shot
    stride = 1.3
    h.arm.rotation_euler = (0, 0, 0); h.arm.location = (0, 0, 0)
    reset_pose(h)
    pose_walk(h, (dist / stride) % 1.0, stride=20, arm_swing=10)
    # right arm up holding the umbrella shaft near the shoulder
    from human import aim_bone
    aim_bone(h.arm, "upperarm01.R", (-0.15, -0.55, -0.82)); aim_bone(h.arm, "upperarm02.R", (-0.15, -0.55, -0.82))
    aim_bone(h.arm, "lowerarm01.R", (0.25, -0.75, 0.6)); aim_bone(h.arm, "lowerarm02.R", (0.25, -0.75, 0.6))
    fingers_curl(h, 70, side=("R",), thumb=40)
    rotate_bone(h.arm, "head", (1, 0, 0), 10)
    h.arm.rotation_euler = (0, 0, math.radians(90))     # rest pose faces -Y; turn to walk along +X
    h.arm.location = (x0 + dist, c["walk_y"], 0.16)
    bpy.context.view_layer.update()
    hand = h.bone_tail("wrist.R")
    head = h.bone_head("head")
    top = Vector((hand.x + 0.05, hand.y - 0.05, head.z + 0.42))
    can, shaft = c["umbrella"]
    can.location = top + Vector((0, 0, -0.14)); shaft.location = top + Vector((0, 0, -0.45))
    can.rotation_euler = (math.radians(-8), math.radians(6), 0); shaft.rotation_euler = can.rotation_euler
    nodes = c["asphalt"].node_tree.nodes
    nodes[c["asphalt"]["ripple"]].inputs['W'].default_value = t * 4.0
    return Vector((h.arm.location.x, h.arm.location.y, 1.2))


def place_walker_toward(c, t):
    """She walks toward -X (toward the camera) along her pavement."""
    p = place_walker(c, t, x0=8.0)
    h = c["h"]
    # mirror the walk direction: turn the rig to face -X and run the distance backwards
    dist = h.arm.location.x - 8.0
    h.arm.rotation_euler = (0, 0, math.radians(-90)); h.arm.location.x = 8.0 - dist
    bpy.context.view_layer.update()
    # the shaft runs up from her closed hand; the canopy tilts forward into the rain (and over her face)
    grip = h.bone_head("finger3-1.R").lerp(h.bone_tail("wrist.R"), 0.5)
    can, shaft = c["umbrella"]
    tilt = Matrix.Rotation(math.radians(-14), 3, 'Y') @ Matrix.Rotation(math.radians(-5), 3, 'X')
    up = tilt @ Vector((0, 0, 1))
    top = grip + up * 0.85
    shaft.location = grip + up * 0.425; shaft.rotation_euler = tilt.to_euler()
    can.location = top - up * 0.14; can.rotation_euler = tilt.to_euler()
    return Vector((h.arm.location.x, h.arm.location.y, 1.2))


def _cam_long(c, t):
    p = place_walker_toward(c, t)
    cam = Vector((-12.0 - 0.6 * t, STREET_W / 2 - 1.4, 1.55))        # down the street, long lens: signs stack up behind her
    return (cam, p + Vector((0, -0.4, 0.25)), 85)


def _cam_puddle(c, t):
    p = place_walker_toward(c, 0.45 + 0.25 * t)     # she keeps walking; the low camera holds, she passes through
    cam = Vector((5.0 - 3.4 - 0.6 * t, p.y - 0.35, 0.24))       # just above the wet pavement, in her path, creeping back
    return (cam, Vector((p.x, p.y, 0.55)), 32)


MOVES = {
    "puddle": dict(kind="anim", dof=2.0, far=80.0, cam=_cam_puddle, focus=lambda c, t: place_walker_toward(c, 0.45 + 0.25 * t) + Vector((0, 0, -0.7))),
    "slowmo_walk": dict(kind="anim", dof=2.8, far=80.0, cam=_cam_long, focus=lambda c, t: place_walker_toward(c, t)),
}
