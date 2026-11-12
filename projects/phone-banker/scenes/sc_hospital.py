"""HOSPITALS, Moscow 1995 (dramatization; no patient is ever seen). One file, several variants:
  corridor : Hospital 1, green-painted corridor; a bed-trolley wheeled through swinging doors (Ch1 4A)
  ward     : Hospital 1 ward by day; a monitor beside a curtained bed, a nurse checks the drip (Ch1 4B)
  night    : the same ward at night; ventilator bellows rise and fall, a doctor at the monitor (Ch1 8A/8B)
  arrive   : Hospital 2 entrance at dusk; an ambulance van pulls up, its beacon turning (Ch1 5A)
  dawn     : Hospital 2 corridor at dawn; the clock at six, a nurse slowly draws a curtain (Ch1 5B)
  path     : the pathologist's room; he reads the file, then closes it and switches off the theatre light (Ch1 6A/6B)
"""
import os, math
import numpy as np
import bpy
from mathutils import Vector, Matrix
from kit import *
import ph
from pbkit import joinm, masonry_facade, image_plane
from pbpeople import person, medic, stand, seat, walk_at, nod, look, hold_flat, hand_to, hide, recolor, fwd
from sc_bankoffice import retint, plastic

EXPOSURE = 1.2
BOUNCES = 6
GEN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "generated")
DUR = {"gurney": 5.5, "ward": 5.5, "arrive": 5.0, "dawn": 6.0, "path_read": 6.0, "path_light": 5.5, "nightward": 7.0, "doctor": 6.0}
VARIANT_FOR = {"gurney": "corridor", "ward": "ward", "arrive": "arrive", "dawn": "dawn", "path_read": "path", "path_light": "path",
               "nightward": "night", "doctor": "night"}
rng = np.random.default_rng(7)


# ============================================================================ materials and props
def two_tone(name, low=(0.22, 0.36, 0.3), high=(0.72, 0.72, 0.68), dado=1.5):
    """Soviet hospital paint: gloss oil paint to the dado line, whitewash above (world z)."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    geo = N.new("ShaderNodeNewGeometry"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs['Position'], sep.inputs[0])
    lt = N.new("ShaderNodeMath"); lt.operation = 'LESS_THAN'; lt.inputs[1].default_value = dado; L.new(sep.outputs['Z'], lt.inputs[0])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 3; nz.inputs['Detail'].default_value = 8; L.new(geo.outputs['Position'], nz.inputs['Vector'])
    c1 = N.new("ShaderNodeMix"); c1.data_type = 'RGBA'; L.new(lt.outputs[0], c1.inputs['Factor'])
    c1.inputs[6].default_value = (*high, 1); c1.inputs[7].default_value = (*low, 1)
    gr = N.new("ShaderNodeMix"); gr.data_type = 'RGBA'; gr.blend_type = 'MULTIPLY'; gr.inputs['Factor'].default_value = 0.18
    L.new(c1.outputs[2], gr.inputs[6]); L.new(nz.outputs['Color'], gr.inputs[7]); L.new(gr.outputs[2], p.inputs['Base Color'])
    r = N.new("ShaderNodeMix"); r.data_type = 'FLOAT'; L.new(lt.outputs[0], r.inputs['Factor']); r.inputs[2].default_value = 0.85; r.inputs[3].default_value = 0.25
    L.new(r.outputs[0], p.inputs['Roughness'])
    return m


def ecg_image(path, W=1024, H=256):
    if os.path.exists(path):
        return path
    from PIL import Image, ImageDraw, ImageFilter
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im = Image.new("RGB", (W, H), (4, 14, 8)); d = ImageDraw.Draw(im)
    for x in range(0, W, 32):
        d.line([(x, 0), (x, H)], fill=(8, 26, 14))
    pts = []
    for x in range(W):
        u = (x % 256) / 256
        y = 0.0
        if 0.30 < u < 0.33: y = -0.12 * math.sin((u - 0.30) / 0.03 * math.pi)
        if 0.40 < u < 0.42: y = 0.15
        if 0.42 < u < 0.45: y = -0.75 + (u - 0.42) / 0.03 * 0.95
        if 0.45 < u < 0.47: y = 0.2 - (u - 0.45) / 0.02 * 0.2
        if 0.58 < u < 0.66: y = -0.18 * math.sin((u - 0.58) / 0.08 * math.pi)
        pts.append((x, H * 0.55 + y * H * 0.4))
    d.line(pts, fill=(90, 255, 140), width=3)
    im = im.filter(ImageFilter.GaussianBlur(0.8))
    im.save(path); return path


def monitor_screen(name, w, h, loc, rot, speed=0.004):
    """CRT trace: the ECG image scrolls left (frame driver on the texture offset)."""
    img = ecg_image(os.path.join(GEN, "ecg_trace.png"))
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping")
    t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(img); t.extension = 'REPEAT'
    L.new(tc.outputs['UV'], mp.inputs['Vector']); L.new(mp.outputs[0], t.inputs['Vector'])
    d = mp.inputs['Location'].driver_add("default_value", 0).driver; d.type = 'SCRIPTED'; d.expression = f"frame * {speed}"
    em = N.new("ShaderNodeEmission"); em.inputs['Strength'].default_value = 2.2; L.new(t.outputs['Color'], em.inputs['Color'])
    L.new(em.outputs[0], out.inputs['Surface'])
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name; o.scale = (w, h, 1); o.data.materials.append(m)
    return o


def hospital_bed(loc, rot_z, occupied=True, blanket=(0.6, 0.62, 0.66)):
    """Iron bed (scanned frame) with mattress, pillow and a blanket (a shape under it when occupied; no face shown)."""
    r, ms = ph.model("old_bed_frame", loc=loc, rot_z=rot_z)
    retint(ms, (0.85, 0.88, 0.86))
    top = 0.5
    M = Matrix.Translation(Vector(loc)) @ Matrix.Rotation(rot_z, 4, 'Z')
    mat = fabric("Mattress", (0.7, 0.7, 0.66), 0.9, 0.3, 300)
    bl = fabric("Blanket", blanket, 0.95, 0.5, 300)
    parts = [box("Mattress", (0, 0, top + 0.07), (0.84, 1.9, 0.14), mat, bevel=0.04),
             box("Pillow", (0, 0.78, top + 0.19), (0.6, 0.32, 0.12), fabric("Pillow", (0.85, 0.85, 0.82), 0.9, 0.3, 300), bevel=0.05)]
    o = joinm(parts, "BedLinen"); o.matrix_world = M
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=20, y_subdivisions=30, size=1, location=(0, -0.15, top + 0.16))
    b = bpy.context.active_object; b.name = "BlanketCover"; b.scale = (1.0, 1.45, 1)
    bpy.ops.object.transform_apply(scale=True)
    for v in b.data.vertices:
        ex = max(0.0, abs(v.co.x) - 0.42)
        v.co.z -= ex * 1.8                                                      # drapes over the sides
        if occupied:
            v.co.z += 0.13 * math.exp(-(v.co.x / 0.2) ** 2) * (1 if v.co.y < 0.45 else math.exp(-((v.co.y - 0.45) / 0.1) ** 2))
    sub = b.modifiers.new("s", 'SUBSURF'); sub.levels = 1; sub.render_levels = 2
    so = b.modifiers.new("t", 'SOLIDIFY'); so.thickness = 0.015
    b.data.materials.append(bl); b.matrix_world = M @ b.matrix_world
    for p_ in b.data.polygons:
        p_.use_smooth = True
    return r


def iv_stand(loc):
    steel = pbr("Steel", (0.7, 0.7, 0.72), 0.25, 1.0)
    parts = [cyl("IVPole", (0, 0, 0.95), 0.012, 1.9, steel, verts=12), box("IVHook", (0, 0, 1.9), (0.3, 0.015, 0.015), steel)]
    for k in range(4):
        a = k * math.pi / 2
        parts.append(box("IVFoot", (0.15 * math.cos(a), 0.15 * math.sin(a), 0.03), (0.3, 0.025, 0.02), steel, rot=(0, 0, a)))
    o = joinm(parts, "IVStand"); o.location = loc
    bag = box("IVBag", (loc[0] + 0.12, loc[1], 1.72), (0.1, 0.03, 0.18), pbr("IVBagM", (0.9, 0.92, 0.95), 0.1, 0.0, **{'Transmission Weight': 0.7}), bevel=0.02)
    tube = cyl("IVTube", (loc[0] + 0.12, loc[1], 1.35), 0.003, 0.6, pbr("Tube", (0.9, 0.9, 0.9), 0.2), verts=8)
    return o, bag


def ventilator(loc, rot_z=0.0):
    """A 1980s ward ventilator on a stand: a box unit with a glass column whose bellows rise and fall (frame driver)."""
    cream = plastic("VentCream", (0.66, 0.64, 0.58), 0.45)
    parts = [box("VentBase", (0, 0, 0.06), (0.5, 0.45, 0.08), cream, bevel=0.01),
             box("VentBody", (0, 0, 0.8), (0.45, 0.4, 0.5), cream, bevel=0.02),
             box("VentPanel", (0, -0.205, 0.85), (0.38, 0.01, 0.3), pbr("VentPanelDark", (0.1, 0.12, 0.12), 0.4))]
    for k in range(4):
        parts.append(cyl("Knob", (-0.12 + k * 0.08, -0.215, 0.75), 0.018, 0.02, pbr("KnobBlack", (0.03, 0.03, 0.03), 0.4), verts=12, rot=(math.radians(90), 0, 0)))
    for x in (-0.2, 0.2):
        parts.append(cyl("VentLeg", (x, 0, 0.32), 0.015, 0.5, pbr("Steel2", (0.6, 0.6, 0.62), 0.3, 1.0), verts=10))
    unit = joinm(parts, "Ventilator"); unit.location = loc; unit.rotation_euler = (0, 0, rot_z)
    col = cyl("BellowsGlass", (0, 0, 1.33), 0.11, 0.55, glass("VentGlass", (0.95, 0.97, 0.98), 0.03), verts=32)
    col.parent = unit
    bel = cyl("Bellows", (0, 0, 0.0), 0.085, 1.0, pbr("BellowsBlue", (0.3, 0.45, 0.6), 0.5), verts=24)
    # accordion folds
    bel.data.materials[0].node_tree.nodes["Principled BSDF"].inputs['Roughness'].default_value = 0.5
    bel.parent = unit; bel.location = (0, 0, 1.06)
    bel.scale = (1, 1, 0.3)
    d = bel.driver_add("scale", 2).driver; d.type = 'SCRIPTED'; d.expression = "0.22 + 0.16 * (0.5 + 0.5 * sin(frame * 0.2))"
    d2 = bel.driver_add("location", 2).driver; d2.type = 'SCRIPTED'; d2.expression = "1.06 + 0.5 * (0.22 + 0.16 * (0.5 + 0.5 * sin(frame * 0.2)))"
    led = box("VentLED", (0.12, -0.212, 0.95), (0.02, 0.005, 0.02), None); led.parent = unit
    lm = bpy.data.materials.new("VentLED"); lm.use_nodes = True
    Nn = lm.node_tree.nodes; Nn.clear(); o = Nn.new("ShaderNodeOutputMaterial"); e = Nn.new("ShaderNodeEmission"); e.inputs['Color'].default_value = (0.2, 1.0, 0.3, 1)
    v = Nn.new("ShaderNodeValue"); dd = v.outputs[0].driver_add("default_value").driver; dd.type = 'SCRIPTED'; dd.expression = "6 * (0.5 + 0.5 * sin(frame * 0.2))"
    lm.node_tree.links.new(v.outputs[0], e.inputs['Strength']); lm.node_tree.links.new(e.outputs[0], o.inputs['Surface']); led.data.materials.append(lm)
    return unit


def monitor_cart(loc, rot_z):
    r, ms = ph.model("tool_cart", loc=loc, rot_z=rot_z)
    r2, tv = ph.model("television_02", loc=(loc[0], loc[1], 0.96), rot_z=rot_z)
    M = Matrix.Translation(Vector((loc[0], loc[1], 0.96))) @ Matrix.Rotation(rot_z, 4, 'Z')
    p = M @ Vector((0.0, -0.125, 0.215))
    scr = monitor_screen("ECG", 0.27, 0.2, tuple(p), (math.radians(90), 0, rot_z))
    return r, scr


def privacy_curtain(x0, x1, y, h=1.95, col=(0.55, 0.66, 0.7), name="Curtain"):
    """A cloth curtain hanging from a ceiling rail along X from x0 to x1 (gathered folds, a slow stir)."""
    m = fabric(name + "M", col, 0.9, 0.5, 300)
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=60, y_subdivisions=20, size=1, location=((x0 + x1) / 2, y, 0.25 + h / 2), rotation=(math.radians(90), 0, 0))
    o = bpy.context.active_object; o.name = name; o.scale = (abs(x1 - x0), h, 1)
    bpy.ops.object.transform_apply(scale=True)
    for v in o.data.vertices:
        v.co.y += 0.05 * math.sin(v.co.x * 2 * math.pi * 3.5)
    wv = o.modifiers.new("stir", 'WAVE'); wv.use_normal = True; wv.use_x = False; wv.use_y = False; wv.height = 0.015; wv.width = 1.2; wv.speed = 0.01
    o.data.materials.append(m)
    box(name + "Rail", ((x0 + x1) / 2, y, 0.25 + h + 0.05), (abs(x1 - x0) + 0.2, 0.03, 0.03), pbr("RailSteel", (0.7, 0.7, 0.72), 0.3, 1.0))
    return o


def fluorescents(xs, ys, z, energy, col=(0.9, 0.97, 1.0), drivers=None):
    for x in xs:
        for y in ys:
            ph.model("mounted_fluorescent_lights", loc=(x, y, z), rot_z=math.radians(90))
            l = area_light((x, y, z - 0.1), (0, 0, 0), 1.0, energy, col); l.visible_camera = False


def window_light(x, y, rot_z, energy, col):
    l = area_light((x, y, 1.8), (0, math.radians(90), rot_z), 1.6, energy, col)
    l.visible_camera = False; l.visible_glossy = False; l.visible_transmission = False
    return l


# ============================================================================ build
def build(variant=None):
    variant = variant or "corridor"
    c = {"variant": variant}
    if variant == "arrive":
        return build_exterior(c)
    night = variant == "night"
    dawn = variant == "dawn"
    world_flat((0.02, 0.03, 0.06) if night else ((0.55, 0.6, 0.7) if dawn else (0.5, 0.55, 0.62)), 1.0)
    lino = ph.texture("old_linoleum_flooring_01", scale=0.6)
    low = (0.2, 0.34, 0.3) if variant != "dawn" else (0.3, 0.42, 0.52)                 # hospital 2 is painted blue-grey
    walls = two_tone("Walls" + variant, low=low)
    ceil = pbr("Ceil", (0.7, 0.7, 0.68), 0.9)
    if variant in ("corridor", "dawn"):
        build_corridor(c, lino, walls, ceil, dawn)
    elif variant in ("ward", "night"):
        build_ward(c, lino, walls, ceil, night)
    elif variant == "path":
        build_path(c, lino, ceil)
    animate(c, 0.0, None)
    return c


def build_corridor(c, lino, walls, ceil, dawn):
    W, L_, H = 2.6, 22.0, 3.1
    box("Floor", (0, 0, -0.01), (W, L_, 0.02), lino)
    box("Ceiling", (0, 0, H), (W, L_, 0.04), ceil)
    for sx in (-1, 1):
        box("Wall", (sx * (W / 2 + 0.05), 0, H / 2), (0.1, L_, H), walls)
        for k in range(6):                                                     # ward doors along both sides
            y = -9 + k * 3.6 + (0.8 if sx > 0 else 0)
            frame_m = pbr("DoorWhite", (0.78, 0.78, 0.74), 0.4)
            box("DoorFrame", (sx * (W / 2 - 0.01), y, 1.05), (0.04, 1.0, 2.15), frame_m)
            box("DoorLeaf", (sx * (W / 2 - 0.02), y, 1.03), (0.04, 0.9, 2.05), pbr("DoorLeafM", (0.7, 0.7, 0.66), 0.45))
            box("DoorGlass", (sx * (W / 2 - 0.045), y, 1.55), (0.01, 0.6, 0.7), pbr("Frosted", (0.75, 0.78, 0.78), 0.3, 0.0, **{'Emission Color': (0.9, 0.95, 1.0, 1), 'Emission Strength': 0.4}))
        for k in range(3):
            ph.model("painted_wooden_bench", loc=(sx * (W / 2 - 0.28), -6 + k * 6.5, 0), rot_z=math.radians(-90 * sx))
    # swinging double doors across the corridor at y = -4 (glazed), the trolley comes through them
    leaves = []
    for sx in (-1, 1):
        lf = joinm([box("Swing", (sx * -0.6, 0, 1.05), (1.2, 0.05, 2.1), pbr("SwingM", (0.7, 0.72, 0.68), 0.45)),
                    box("SwingGlass", (sx * -0.6, -0.03, 1.5), (0.7, 0.01, 0.8), glass("SwingGlassM", (0.9, 0.93, 0.94), 0.05))], "SwingDoor")
        lf.location = (sx * 1.25, -4.0, 0); leaves.append(lf)
    c["swing"] = leaves
    box("SwingHead", (0, -4.0, 2.6), (W, 0.12, 1.0), walls)
    # a window at the far end
    box("EndWall", (0, -L_ / 2 - 0.05, H / 2), (W, 0.1, H), walls)
    box("EndWin", (0, -L_ / 2, 1.8), (1.4, 0.02, 1.6), pbr("EndWinGlow", (0.8, 0.85, 0.9), 0.3, 0.0, **{'Emission Color': (0.85, 0.9, 1.0, 1), 'Emission Strength': 2.5 if not dawn else 4.0}))
    box("EndWall2", (0, L_ / 2 + 0.05, H / 2), (W, 0.1, H), walls)
    fluorescents([0.0], [-8.0, -3.0, 2.0, 7.0], H - 0.02, 0 if dawn else 28)
    if dawn:                                                   # dawn: cool daylight from the far window, one light still on
        l = area_light((0, -L_ / 2 + 0.4, 1.8), (math.radians(-90), 0, 0), 2.0, 600, (0.85, 0.88, 1.0)); l.visible_camera = False
        l2 = area_light((0, 4.0, H - 0.15), (0, 0, 0), 0.8, 40, (1.0, 0.85, 0.65)); l2.visible_camera = False
        r, clk = ph.model("wall_clock", loc=(-W / 2 + 0.01, 1.2, 2.25), rot_z=math.radians(-90))
        for o in clk:                                           # six o'clock: hour hand straight down, minute hand up
            if "hours" in o.name:
                o.rotation_euler = (0, -math.pi, 0)
            elif "minute" in o.name:
                o.rotation_euler = (0, 0, 0)
            elif "second" in o.name:
                c["second_hand"] = o
        # a ward bay opening on the right with its curtain the nurse draws
        c["curtain"] = privacy_curtain(-0.1, 1.2, 0.3, col=(0.6, 0.68, 0.72), name="DawnCurtain")
        c["nurse"] = medic("Nurse2", 0.0, 34, "bob02")
    else:
        bed = hospital_bed((0, 0, 0), 0.0, occupied=True, blanket=(0.82, 0.83, 0.8))
        c["bed"] = [o for o in bpy.data.objects if o.name.startswith(("old_bed_frame", "BedLinen", "BlanketCover"))]
        c["bed_root"] = bpy.data.objects.new("BedRig", None); bpy.context.collection.objects.link(c["bed_root"])
        for o in c["bed"]:
            if o.parent is None:
                o.parent = c["bed_root"]
        iv, bag = iv_stand((0.55, 0.6, 0)); iv.parent = c["bed_root"]; bag.parent = c["bed_root"]
        c["orderlies"] = [medic("Orderly1", 1.0, 30, "short02"), medic("Orderly2", 1.0, 45, "short04"), medic("Doctor1", 0.0, 40, "ponytail01")]


def build_ward(c, lino, walls, ceil, night):
    W, D, H = 7.0, 6.0, 3.1
    box("Floor", (0, 0, -0.01), (W, D, 0.02), lino); box("Ceiling", (0, 0, H), (W, D, 0.04), ceil)
    box("WallBack", (0, D / 2 + 0.05, H / 2), (W, 0.1, H), walls); box("WallFront", (0, -D / 2 - 0.05, H / 2), (W, 0.1, H), walls)
    box("WallR", (W / 2 + 0.05, 0, H / 2), (0.1, D, H), walls)
    # left wall: two windows
    for (y0, y1) in ((-D / 2, -1.9), (-0.3, 0.6), (2.2, D / 2)):
        box("WallL", (-W / 2 - 0.05, (y0 + y1) / 2, H / 2), (0.1, y1 - y0, H), walls)
    for y in (-1.1, 1.4):
        box("WinUnder", (-W / 2 - 0.05, y, 0.45), (0.1, 1.6, 0.9), walls); box("WinOver", (-W / 2 - 0.05, y, 2.85), (0.1, 1.6, 0.5), walls)
        box("WinGlass", (-W / 2 - 0.06, y, 1.75), (0.01, 1.6, 1.7), glass("WGlass", (0.92, 0.95, 0.96), 0.02))
        box("WinBar", (-W / 2 - 0.03, y, 1.75), (0.05, 0.05, 1.7), pbr("WinFrameW", (0.8, 0.8, 0.76), 0.4))
        if night:
            window_light(-W / 2 - 0.5, y, 0, 12, (0.4, 0.5, 0.85))
        else:
            window_light(-W / 2 - 0.5, y, 0, 170, (0.9, 0.94, 1.0))
    box("Outside", (-W / 2 - 18, 0, 8), (1, 40, 20), masonry_facade("WardOpp", (0.55, 0.52, 0.45), 3.2, 2.6, 1.2, 1.6, 0.3 if night else 0.0, lit_strength=1.2))
    # four beds along the back wall, heads to the wall; the near one (x = 1.6) is the curtained one
    xs = (-2.4, -0.8, 0.8, 2.4)
    for k, x in enumerate(xs):
        hospital_bed((x, D / 2 - 1.1, 0), math.pi if False else 0.0, occupied=(k != 0), blanket=(0.62, 0.64, 0.68) if k % 2 else (0.7, 0.66, 0.6))
        r, _ = ph.model("ClassicNightstand_01", loc=(x + 0.62, D / 2 - 0.35, 0), rot_z=math.pi)
    c["hero_bed"] = Vector((xs[2], D / 2 - 1.1, 0))
    c["curtain"] = privacy_curtain(xs[2] - 0.75, xs[2] + 0.75, D / 2 - 2.3, col=(0.55, 0.65, 0.68), name="BedCurtain")
    c["curtain"].location.x += 0.0
    iv, bag = iv_stand((xs[2] - 0.65, D / 2 - 0.9, 0)); c["iv_bag"] = bag
    mon, scr = monitor_cart((xs[2] + 0.9, D / 2 - 1.6, 0), math.radians(200 if not night else 60)); c["screen"] = scr
    if night:
        c["vent"] = ventilator((xs[2] - 0.95, D / 2 - 1.9, 0.0), math.radians(160))
        c["curtain"].scale.x = 0.35; c["curtain"].location.x += 0.5                  # curtain pushed back at night
        for x in xs:                                           # dim night lights over the beds
            l = bpy.data.lights.new("NightLamp", 'SPOT'); l.energy = 25; l.spot_size = math.radians(80); l.color = (1.0, 0.78, 0.5)
            o = bpy.data.objects.new("NightLamp", l); bpy.context.collection.objects.link(o); o.location = (x, D / 2 - 0.2, 2.2); point_at(o, (x, D / 2 - 1.2, 0.6))
        box("DoorGlow", (W / 2 - 0.01, -1.8, 1.05), (0.02, 0.9, 2.05), emissive("CorridorGlow", (1.0, 0.85, 0.65), 1.2))
        c["doctor"] = medic("NightDoctor", 1.0, 50, "short04")
    else:
        fluorescents([-1.6, 1.6], [-0.5, 1.5], H - 0.02, 18)
        c["nurse"] = medic("WardNurse", 0.0, 29, "ponytail01")


def build_path(c, lino, ceil):
    W, D, H = 5.0, 5.0, 3.0
    tile = ph.texture("long_white_tiles", scale=1.0) if True else None
    box("Floor", (0, 0, -0.01), (W, D, 0.02), ph.texture("worn_tile_floor", scale=0.8)); box("Ceiling", (0, 0, H), (W, D, 0.04), ceil)
    for (loc, size) in (((0, D / 2 + 0.05, H / 2), (W, 0.1, H)), ((0, -D / 2 - 0.05, H / 2), (W, 0.1, H)), ((W / 2 + 0.05, 0, H / 2), (0.1, D, H))):
        box("Tiles", loc, size, tile)
    for (y0, y1) in ((-D / 2, -0.8), (0.8, D / 2)):
        box("TilesL", (-W / 2 - 0.05, (y0 + y1) / 2, H / 2), (0.1, y1 - y0, H), tile)
    box("WinUnder", (-W / 2 - 0.05, 0, 0.5), (0.1, 1.6, 1.0), tile); box("WinOver", (-W / 2 - 0.05, 0, 2.75), (0.1, 1.6, 0.5), tile)
    box("WinGlass", (-W / 2 - 0.06, 0, 1.75), (0.01, 1.6, 1.5), pbr("PathFrost", (0.75, 0.78, 0.8), 0.3, 0.0, **{'Emission Color': (0.75, 0.82, 0.95, 1), 'Emission Strength': 1.2}))
    window_light(-W / 2 - 0.4, 0, 0, 90, (0.8, 0.86, 1.0))
    # his desk by the window, the empty steel table under the theatre lamp at the back
    r, desk = ph.model("metal_office_desk", loc=(-1.2, -1.2, 0), rot_z=math.radians(90))
    retint(desk, (0.85, 0.9, 0.88))
    r, ch = ph.model("SchoolChair_01", loc=(-0.45, -1.2, 0), rot_z=math.radians(90))
    r, lmp = ph.model("desk_lamp_arm_01", loc=(-1.45, -0.6, 0.79), rot_z=math.radians(-30)); retint(lmp, (0.2, 0.25, 0.22))
    dl = bpy.data.lights.new("PathDeskLamp", 'SPOT'); dl.energy = 30; dl.spot_size = math.radians(70); dl.color = (1.0, 0.82, 0.6)
    do = bpy.data.objects.new("PathDeskLamp", dl); bpy.context.collection.objects.link(do); do.location = (-1.3, -0.95, 1.35); point_at(do, (-1.05, -1.2, 0.8))
    import paper_tex
    pages = paper_tex.make_all()["pages"]
    for k in range(3):
        image_plane("DeskPage", pages[k], (-1.3 + k * 0.08, -1.55 + k * 0.05, 0.792 + k * 0.001), (0.21, 0.28), (0, 0, math.radians(90 + k * 7)), rough=0.75)
    r, cart = ph.model("tool_cart", loc=(1.2, 1.4, 0), rot_z=0.0)
    retint(cart, (0.8, 0.85, 0.85))
    r, lamp = ph.model("hanging_industrial_lamp", loc=(1.2, 1.4, H), rot_z=0.0)
    tl = bpy.data.lights.new("TheatreLamp", 'SPOT'); tl.spot_size = math.radians(60); tl.spot_blend = 0.4; tl.color = (0.95, 0.97, 1.0)
    to = bpy.data.objects.new("TheatreLamp", tl); bpy.context.collection.objects.link(to); to.location = (1.2, 1.4, H - 1.4); point_at(to, (1.2, 1.4, 0))
    c["theatre"] = tl
    box("Switch", (W / 2 - 0.01, 0.2, 1.4), (0.02, 0.08, 0.12), plastic("SwitchM", (0.8, 0.78, 0.72), 0.4))
    r, _ = ph.model("vintage_cabinet_01", loc=(1.0, D / 2 - 0.35, 0)); 
    r, _ = ph.model("vintage_microscope", loc=(-1.0, -1.65, 0.79), rot_z=1.0)
    r, rad = ph.model("vintage_radio_transceiver", loc=(-1.35, -2.0, 0.79), rot_z=math.radians(80))
    fluorescents([0.0], [0.0], H - 0.02, 25)
    c["doctor"] = medic("Pathologist", 1.0, 56, "short04")
    folder = joinm([box("PFolder", (0, 0, 0), (0.31, 0.235, 0.004), pbr("PManila", (0.6, 0.48, 0.28), 0.8), bevel=0.001)], "PathFolder")
    pg = image_plane("PathPage", pages[0], (0, 0, 0.0025), (0.29, 0.215), (0, 0, math.radians(90)), rough=0.75); pg.parent = folder
    c["folder"] = folder


def build_exterior(c):
    world_sky(sun_elev_deg=-3.0, sun_rot_deg=250, strength=2.4, tint=(0.62, 0.74, 1.0))
    pave = ph.texture("concrete_pavers", scale=0.8); road = ph.texture("asphalt_02", scale=0.25)
    box("Forecourt", (0, -6, -0.01), (60, 14, 0.02), road)
    box("Kerb", (0, -0.6, 0.06), (60, 1.2, 0.14), pave)
    fac = masonry_facade("HospFacade", (0.7, 0.66, 0.52), 3.2, 2.8, 1.3, 1.8, 0.35, lit_strength=1.1)
    box("Hospital", (0, 7, 8), (40, 14, 16), fac)
    # entrance porch with a canopy and lit doors
    box("Canopy", (0, -0.8, 3.0), (6, 3.2, 0.25), pbr("CanopyConcrete", (0.55, 0.54, 0.5), 0.8))
    for x in (-2.7, 2.7):
        box("CanopyPost", (x, -2.2, 1.45), (0.25, 0.25, 2.9), pbr("Post", (0.6, 0.58, 0.54), 0.8))
    box("EntranceGlow", (0, -0.01, 1.3), (2.6, 0.02, 2.4), emissive("EntranceLight", (1.0, 0.86, 0.66), 1.6))
    l = area_light((0, -1.0, 2.8), (0, 0, 0), 2.0, 200, (1.0, 0.85, 0.65)); l.visible_camera = False
    for x in (-12, 12):
        ph.model("street_lamp_01", loc=(x, -1.5, 0), rot_z=0.0)
        sl = bpy.data.lights.new("Lamp", 'POINT'); sl.energy = 160; sl.color = (1.0, 0.8, 0.6)
        o = bpy.data.objects.new("Lamp", sl); bpy.context.collection.objects.link(o); o.location = (x, -1.5, 3.75)
    for x in (-8.0, 7.5, 15.0):
        ph.model("tree_small_02", loc=(x, -2.0, 0), rot_z=rng.uniform(0, 6.28), scale=1.2)
    c["van"] = ambulance_van()
    c["medic"] = medic("Paramedic", 1.0, 35, "short02")
    animate(c, 0.0, None)
    return c


def ambulance_van():
    """A late-Soviet ambulance van (UAZ-452 type): rounded box, white with a red band and a turning blue beacon."""
    from pbkit import kit_vehicle
    van = kit_vehicle("van_1990s", "Ambulance", (0.82, 0.82, 0.8), lamps=True)
    top = van.dimensions.z
    bm = bpy.data.materials.new("VanBeacon"); bm.use_nodes = True
    N = bm.node_tree.nodes; L = bm.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); em = N.new("ShaderNodeEmission"); em.inputs['Color'].default_value = (0.15, 0.35, 1.0, 1)
    v = N.new("ShaderNodeValue"); d = v.outputs[0].driver_add("default_value").driver; d.type = 'SCRIPTED'; d.expression = "12 * (1 if (frame % 14) < 7 else 0.1)"
    L.new(v.outputs[0], em.inputs['Strength']); L.new(em.outputs[0], out.inputs['Surface'])
    bc = cyl("VanBeacon", (0, 0, 0), 0.08, 0.14, bm, verts=20); bc.parent = van; bc.location = (1.2, 0, top + 0.07)
    l = bpy.data.lights.new("VanBeaconL", 'POINT'); l.color = (0.2, 0.4, 1.0)
    dl = l.driver_add("energy").driver; dl.type = 'SCRIPTED'; dl.expression = "150 * (1 if (frame % 14) < 7 else 0.02)"
    lo = bpy.data.objects.new("VanBeaconL", l); bpy.context.collection.objects.link(lo); lo.parent = van; lo.location = (1.2, 0, top + 0.3)
    return van


# ============================================================================ animation
def animate(c, sec, move):
    fn = ANIM.get(move)
    if fn:
        fn(c, sec)
    bpy.context.view_layer.update()


def a_gurney(c, sec):
    """Two orderlies push the bed toward camera through the swinging doors; a doctor walks alongside."""
    y = -8.0 + 1.0 * sec
    root = c["bed_root"]; root.location = (0, y, 0); root.rotation_euler = (0, 0, 0)
    o1, o2, dr = c["orderlies"]
    for k, h in enumerate((o1, o2)):                                       # at the foot end, pushing (+Y)
        walk_at(h, sec * 0.9 + k * 0.5, (-0.25 + 0.5 * k, y - 1.35, 0), math.pi, stride=20, swing=4)
        nod(h, "spine04", 8)
        hand_to(h, "R" if k else "L", Vector((-0.25 + 0.5 * k, y - 0.98, 1.0)), curl=55)
        hand_to(h, "L" if k else "R", Vector((-0.1 + 0.3 * k, y - 0.98, 1.0)), curl=55)
    walk_at(dr, sec * 0.9 + 0.2, (0.85, y - 0.3, 0), math.pi, stride=20, swing=10)
    look(dr, Vector((0, y + 0.6, 0.7)), 0.8); nod(dr, "head", 12)
    # the doors swing open as the bed passes y = -4, and keep swinging, damped
    hit = max(0.0, sec - 4.0 + 8.0 - 4.0 - 0.0)
    tt = (y - (-4.0 - 1.0))
    for k, lf in enumerate(c["swing"]):
        a = 0.0 if tt < 0 else 80 * math.exp(-0.5 * tt) * math.cos(1.2 * tt) * (1 if tt < 2.2 else 1)
        lf.rotation_euler = (0, 0, math.radians(a * (1 if k == 0 else -1)))


def a_ward(c, sec):
    """A nurse at the curtained bed checks the drip; the monitor trace runs."""
    n = c["nurse"]; hb = c["hero_bed"]
    stand(n, (hb.x - 0.95, hb.y - 0.25, 0), math.radians(180 - 30))
    bag = c["iv_bag"].matrix_world.translation
    look(n, bag, 1.0); n.rot("neck01", (0, 0, 1), 0)
    k = 0.5 + 0.5 * math.sin(sec * 0.8)
    nod(n, "head", -10)
    hand_to(n, "R", bag + Vector((0.0, -0.05, -0.08 + 0.03 * k)), curl=30)
    hand_to(n, "L", n.bone_head("spine03") + fwd(n) * 0.2 + Vector((0, 0, -0.15)), curl=30)


def a_night(c, sec):
    hide(c["doctor"], True)


def a_doctor(c, sec):
    d = c["doctor"]; hb = c["hero_bed"]
    stand(d, (hb.x + 0.55, hb.y - 1.45, 0), math.radians(180 + 40))
    look(d, c["screen"].matrix_world.translation, 1.0); nod(d, "head", 8)
    hand_to(d, "L", Vector((hb.x + 0.42, hb.y - 0.7, 0.72)), hand_dir=Vector((0, 0, -1)), curl=50)        # hand on the bed rail
    hand_to(d, "R", d.bone_head("spine03") + fwd(d) * 0.15 + Vector((0, 0, -0.25)), curl=30)


def a_arrive(c, sec):
    van = c["van"]
    stop = 3.2
    x0, x1 = -24.0, -1.0
    if sec < stop:
        e = sec / stop; x = x0 + (x1 - x0) * (2 * e - e * e)
    else:
        x = x1
    van.location = (x, -3.6, 0); van.rotation_euler = (0, 0, 0)
    m = c["medic"]
    if sec > stop + 0.3:
        walk_at(m, (sec - stop) * 0.9, (x1 - 1.6, -2.5 + 0.6 * (sec - stop - 0.3), 0), math.pi, stride=20, swing=14)
    else:
        hide(m, True)


def a_dawn(c, sec):
    """The clock reads six; a nurse draws the curtain across the bay, slowly."""
    k = ease(min(1.0, max(0.0, (sec - 0.8) / 4.0)))
    cu = c["curtain"]; cu.scale.x = 0.25 + 0.75 * k; cu.location.x = -0.1 * (1 - k)
    n = c["nurse"]
    edge_x = -0.1 + 1.3 * (0.25 + 0.75 * k)
    stand(n, (edge_x + 0.35, -0.2, 0), math.radians(-90 + 20))
    nod(n, "head", 18); nod(n, "neck01", 8)
    hand_to(n, "R", Vector((edge_x + 0.05, 0.3, 1.45)), curl=50)
    hand_to(n, "L", n.bone_head("spine03") + fwd(n) * 0.15 + Vector((0, 0, -0.3)), curl=20)
    if "second_hand" in c:
        c["second_hand"].rotation_euler = (0, -int(sec) / 60 * 2 * math.pi, 0)


def a_path(c, sec, close=0.0):
    d = c["doctor"]
    seat(d, (-0.5, -1.2, 0), math.radians(90), lean=16)                     # faces -X: his desk
    if close <= 0:
        nod(d, "neck01", 10); nod(d, "head", 16)
        hold_flat(d, c["folder"], dist=0.32, drop=0.0, tilt_deg=50, spread=0.13, wobble=0.006 * math.sin(sec * 0.7))
        c["theatre"].energy = 220
    else:
        # 6B: he closes the file on the desk, stands and switches the theatre lamp off at the wall
        k = ease(min(1.0, sec / 1.5))
        c["folder"].location = Vector((-1.0, -1.2, 0.8)); c["folder"].rotation_euler = (0, 0, math.radians(90))
        if sec < 2.0:
            hand_to(d, "R", Vector((-1.0, -1.25, 0.84)), curl=20); hand_to(d, "L", Vector((-1.0, -1.05, 0.84)), curl=20)
            nod(d, "head", 20)
            c["theatre"].energy = 220
        else:
            w = min(1.0, (sec - 2.0) / 2.2)
            p = Vector((-0.4, -1.2, 0)).lerp(Vector((2.1, 0.2, 0)), w)
            if w < 1:
                walk_at(d, (sec - 2.0) * 0.9, p, math.radians(-90 + 30), stride=18, swing=8)
                c["theatre"].energy = 220
            else:
                stand(d, (2.1, 0.2, 0), math.radians(-90))
                hand_to(d, "L", Vector((2.48, 0.2, 1.42)), curl=40)
                c["theatre"].energy = 0 if sec > 4.6 else 220
                look(d, Vector((1.2, 1.4, 1.0)), 0.6)


ANIM = {"gurney": a_gurney, "ward": a_ward, "nightward": a_night, "doctor": a_doctor, "arrive": a_arrive, "dawn": a_dawn,
        "path_read": a_path, "path_light": lambda c, s: a_path(c, s, 1.0)}


def _anim(move):
    return lambda c, t: animate(c, t * DUR[move], move)


def _push(a, b, ta, tb, lens):
    return lambda c, t: (Vector(a).lerp(Vector(b), ease(t)), Vector(ta).lerp(Vector(tb), ease(t)), lens)


def cam_gurney(c, t):
    y = -8.0 + DUR["gurney"] * t
    return (Vector((0.6, y + 4.2, 1.35)), Vector((0.0, y, 0.9)), 30)


MOVES = {
    "gurney": dict(kind="anim", dof=4.0, far=30.0, anim=_anim("gurney"), cam=cam_gurney, focus=lambda c, t: c["bed_root"].location + Vector((0, 0, 0.9))),
    "ward": dict(kind="anim", dof=3.2, far=20.0, anim=_anim("ward"), cam=_push((-1.6, -1.6, 1.55), (-1.3, -1.25, 1.52), (0.5, 1.8, 1.2), (0.6, 1.85, 1.2), 30),
                 focus=lambda c, t: Vector((-0.15, 1.65, 1.4))),
    "nightward": dict(kind="anim", dof=4.0, far=20.0, anim=_anim("nightward"), cam=_push((-3.0, -1.4, 1.5), (-1.0, -1.6, 1.5), (-1.0, 2.0, 0.9), (0.6, 1.9, 1.0), 26),
                      focus=lambda c, t: Vector((-0.4, 1.0, 1.0)).lerp(Vector((0.4, 1.0, 1.0)), ease(t))),
    "doctor": dict(kind="anim", dof=3.2, far=20.0, anim=_anim("doctor"), cam=_push((2.9, -1.0, 1.55), (2.65, -0.75, 1.52), (1.3, 1.2, 1.25), (1.25, 1.25, 1.25), 32),
                   focus=lambda c, t: Vector((1.35, 0.45, 1.5))),
    "arrive": dict(kind="anim", dof=5.6, far=60.0, anim=_anim("arrive"), cam=_push((-9.0, -12.0, 1.6), (-7.5, -11.5, 1.65), (-4.0, -2.0, 1.8), (-1.5, -2.0, 1.8), 30),
                   focus=lambda c, t: c["van"].location + Vector((0, 0, 1.2))),
    "dawn": dict(kind="anim", dof=3.6, far=30.0, anim=_anim("dawn"), cam=_push((-0.7, 5.5, 1.6), (-0.6, 4.7, 1.58), (0.2, 0.0, 1.5), (0.4, 0.0, 1.4), 30),
                 focus=lambda c, t: Vector((0.6, 0.2, 1.4))),
    "path_read": dict(kind="anim", dof=3.2, far=12.0, anim=_anim("path_read"), cam=_push((0.9, -2.2, 1.5), (0.7, -2.05, 1.48), (-0.7, -1.2, 1.2), (-0.65, -1.2, 1.2), 32),
                      focus=lambda c, t: Vector((-0.6, -1.2, 1.3))),
    "path_light": dict(kind="anim", dof=4.0, far=12.0, anim=_anim("path_light"), cam=_push((-1.9, -2.2, 1.6), (-1.8, -1.9, 1.6), (0.6, 0.5, 1.3), (1.4, 0.6, 1.4), 26),
                       focus=lambda c, t: Vector((0.0, -0.5, 1.3)).lerp(Vector((2.1, 0.2, 1.4)), ease(t))),
}
