"""Seldom channel logo sting (5 s, 2.35:1), four crime-vibe concepts. Each move is one concept:
  torch : a dark concrete wall; a flashlight sweeps in and finds the logo, which then glows like neon
  board : evidence board; red strings pull tight from photos to the centre pin, the logo card at the hub
  bag   : an evidence bag drops onto a steel table under a hard top light; the logo card inside, EVIDENCE seal
  tape  : night rain, police lights; yellow crime-scene tape whips across and settles in front of the logo
The logo art is brand/seldom_logo.png (transparent). Render: run.py logo <move> --anim 120
"""
import math, os
import numpy as np
import bpy
from mathutils import Vector
from kit import *
from common import world_flat, area_light, ease
import ph

EXPOSURE = 0.0
DUR = {"torch": 5.0, "board": 5.0, "bag": 5.0, "tape": 5.0}
VARIANT_FOR = {"torch": "torch", "board": "board", "bag": "bag", "tape": "tape"}
LOGO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "brand", "seldom_logo.png")
ASPECT = 1361 / 404
YELLOW = (0.62, 1.0, 0.0)


def _val(N, v=0.0):
    n = N.new("ShaderNodeValue"); n.outputs[0].default_value = v; return n


def logo_material(name, glow_node_holder, base_glow=0.0, rough=0.45):
    """Logo art with alpha; an animated Value node drives an emission glow on the yellow fill."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links
    p = N["Principled BSDF"]; p.inputs['Roughness'].default_value = rough
    t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(os.path.abspath(LOGO), check_existing=True)
    t.extension = 'CLIP'
    L.new(t.outputs['Color'], p.inputs['Base Color']); L.new(t.outputs['Alpha'], p.inputs['Alpha'])
    g = _val(N, base_glow); glow_node_holder.append(g)
    # emission only where the art is bright yellow (the fill), not on the dark outline
    sep = N.new("ShaderNodeSeparateColor"); L.new(t.outputs['Color'], sep.inputs[0])
    mr = N.new("ShaderNodeMapRange"); mr.inputs['From Min'].default_value = 0.55; mr.inputs['From Max'].default_value = 0.8
    L.new(sep.outputs['Green'], mr.inputs['Value'])
    mul = N.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'; L.new(mr.outputs[0], mul.inputs[0]); L.new(g.outputs[0], mul.inputs[1])
    L.new(t.outputs['Color'], p.inputs['Emission Color']); L.new(mul.outputs[0], p.inputs['Emission Strength'])
    return m


def logo_plane(name, loc, width, mat, rot=(math.radians(90), 0, 0)):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name
    o.scale = (width, width / ASPECT, 1); o.data.materials.append(mat)
    return o


# ---------------------------------------------------------------------------------------------------- build
def build(variant=None):
    c = {"glow": []}
    try:
        bpy.context.scene.view_settings.view_transform = "Standard"
    except Exception:
        pass
    v = variant or "torch"
    if v == "torch":
        world_flat((0.002, 0.0025, 0.003), 1.0)
        wall = ph.texture("concrete_floor_02", scale=0.6, name="Wall", tint=(0.55, 0.55, 0.58))
        box("Wall", (0, 0.05, 1.4), (9, 0.1, 5), wall)
        box("Floor", (0, -2.5, -0.02), (9, 5.2, 0.04), ph.texture("concrete_floor_02", scale=0.5, name="Floor", tint=(0.35, 0.35, 0.37)))
        m = logo_material("LogoPaint", c["glow"], rough=0.6)
        c["logo"] = logo_plane("Logo", (0, -0.002, 1.45), 2.2, m)
        # the torch: a narrow spot that sweeps across the wall, plus a faint haze to show the beam
        lt = bpy.data.lights.new("Torch", 'SPOT'); lt.spot_size = math.radians(24); lt.spot_blend = 0.55
        lt.energy = 900; lt.color = (1.0, 0.95, 0.86); lt.shadow_soft_size = 0.02
        to = bpy.data.objects.new("Torch", lt); bpy.context.collection.objects.link(to); to.location = (-0.9, -3.4, 1.55)
        c["torch"] = to
        haze((0, -1.8, 1.6), (8, 3.6, 3.4), density=0.035, color=(0.8, 0.82, 0.85), anis=0.55)
        c["fill"] = area_light((0, -2.0, 2.8), (math.radians(-60), 0, 0), 3.0, 0.0, (0.45, 0.55, 0.8))
        c["fill"].visible_camera = False
    elif v == "board":
        world_flat((0.004, 0.004, 0.005), 1.0)
        box("Wall", (0, 0.2, 1.6), (8, 0.1, 5), pbr("WallPlaster", (0.06, 0.06, 0.065), 0.9))
        cork = pbr("Cork", (0.22, 0.14, 0.08), 0.9)
        N = cork.node_tree.nodes; L = cork.node_tree.links; tc = N.new("ShaderNodeTexCoord")
        nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 260; L.new(tc.outputs['Object'], nz.inputs['Vector'])
        bm = N.new("ShaderNodeBump"); bm.inputs['Strength'].default_value = 0.35; L.new(nz.outputs['Fac'], bm.inputs['Height'])
        L.new(bm.outputs['Normal'], N["Principled BSDF"].inputs['Normal'])
        box("Cork", (0, 0.12, 1.55), (3.6, 0.04, 2.1), cork)
        box("Frame", (0, 0.14, 1.55), (3.72, 0.03, 2.22), wood("BoardFrame"))
        rng = np.random.default_rng(4)
        photo = pbr("Photo", (0.62, 0.62, 0.6), 0.35); paper = pbr("Paper", (0.86, 0.85, 0.8), 0.8)
        pin_m = pbr("Pin", (0.8, 0.06, 0.05), 0.3)
        pins = []
        spots = [(-1.45, 2.3), (-0.75, 2.42), (0.55, 2.4), (1.35, 2.25), (-1.5, 1.05), (-1.25, 0.65), (1.5, 0.95), (1.2, 0.62),
                 (-0.6, 0.7), (0.65, 0.68)]
        for k, (x, z) in enumerate(spots):
            sz = (0.36, 0.27) if k % 2 == 0 else (0.28, 0.36)
            box("Print", (x, 0.095, z), (sz[0], 0.004, sz[1]), photo if k % 3 else paper, rot=(0, math.radians(rng.uniform(-5, 5)), 0))
            cyl("Pin", (x, 0.085, z + sz[1] / 2 - 0.04), 0.012, 0.02, pin_m, verts=12, rot=(math.radians(90), 0, 0))
            pins.append(Vector((x, 0.07, z + sz[1] / 2 - 0.04)))
        card = pbr("Card", (0.05, 0.05, 0.055), 0.6)
        box("LogoCard", (0, 0.092, 1.55), (1.05, 0.004, 0.42), card)
        m = logo_material("LogoCardArt", c["glow"], rough=0.5)
        c["logo"] = logo_plane("Logo", (0, 0.088, 1.55), 0.92, m)
        hubs = [Vector((x, 0.07, z)) for x in (-0.5, 0.5) for z in (1.55 + 0.2, 1.55 - 0.2)]
        for hb in hubs:
            cyl("HubPin", (hb.x, 0.08, hb.z), 0.016, 0.022, pin_m, verts=12, rot=(math.radians(90), 0, 0))
        red = pbr("String", (0.6, 0.02, 0.02), 0.6)
        strings = []
        for k, p0 in enumerate(pins):
            cu = bpy.data.curves.new("String", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.0035; cu.bevel_resolution = 2
            sp = cu.splines.new('POLY'); sp.points.add(8)
            o = bpy.data.objects.new("String", cu); bpy.context.collection.objects.link(o); o.data.materials.append(red)
            hub = min(hubs, key=lambda hb: (hb - p0).length)
            strings.append((o, p0, hub, rng.uniform(0.0, 0.35)))
        c["strings"] = strings
        lamp = bpy.data.lights.new("BoardSpot", 'SPOT'); lamp.spot_size = math.radians(34); lamp.spot_blend = 0.6; lamp.energy = 650
        lamp.color = (1.0, 0.86, 0.66)
        lo = bpy.data.objects.new("BoardSpot", lamp); bpy.context.collection.objects.link(lo); lo.location = (0.6, -2.0, 3.3)
        lo.rotation_euler = (Vector((0, 0.1, 1.5)) - lo.location).to_track_quat('-Z', 'Y').to_euler()
        c["lamp"] = lo
        haze((0, -1.6, 1.8), (7, 3.2, 3.6), density=0.012, color=(0.9, 0.85, 0.8))
    elif v == "bag":
        world_flat((0.003, 0.003, 0.0035), 1.0)
        steel = brushed_metal("Steel", (0.16, 0.17, 0.18), rough=(0.25, 0.45))
        box("Table", (0, 0, 0.9), (2.4, 1.3, 0.04), steel, bevel=0.01)
        box("Floor", (0, 0, -0.01), (10, 10, 0.02), pbr("DarkFloor", (0.02, 0.02, 0.022), 0.7))
        # the bag: thin clear plastic pouch with a white write-on strip and a red seal
        plastic = bpy.data.materials.new("Plastic"); plastic.use_nodes = True
        pp = plastic.node_tree.nodes["Principled BSDF"]
        pp.inputs['Base Color'].default_value = (0.95, 0.96, 0.97, 1); pp.inputs['Roughness'].default_value = 0.18
        pp.inputs['Transmission Weight'].default_value = 0.92; pp.inputs['IOR'].default_value = 1.3
        bag = box("Bag", (0, 0, 0), (0.72, 0.5, 0.012), plastic, bevel=0.005)
        bag.modifiers.new("sub", 'SUBSURF').levels = 2
        strip = box("Strip", (0, 0.19, 0.008), (0.72, 0.1, 0.002), pbr("WhiteStrip", (0.9, 0.9, 0.88), 0.7))
        seal = box("Seal", (0, -0.235, 0.008), (0.72, 0.03, 0.002), pbr("RedSeal", (0.65, 0.03, 0.03), 0.5))
        cardm = pbr("BagCard", (0.04, 0.04, 0.045), 0.6)
        card = box("Card", (0, -0.03, 0.0), (0.56, 0.28, 0.003), cardm)
        m = logo_material("LogoBagArt", c["glow"], rough=0.5)
        logo = logo_plane("Logo", (0, -0.03, 0.0035), 0.5, m, rot=(0, 0, 0))
        txt = text_obj("EvidenceTxt", "EVIDENCE", (0, 0.19, 0.0105), 0.05, pbr("Ink", (0.6, 0.02, 0.02), 0.6), rot=(0, 0, 0),
                       font_path="/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Bold.ttf" if os.path.exists("/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Bold.ttf") else "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")
        root = bpy.data.objects.new("BagRoot", None); bpy.context.collection.objects.link(root)
        for o in (bag, strip, seal, card, logo, txt):
            o.parent = root
        c["bag"] = root
        top = bpy.data.lights.new("TopLight", 'SPOT'); top.spot_size = math.radians(28); top.spot_blend = 0.4; top.energy = 420
        top.color = (1.0, 0.97, 0.92)
        to = bpy.data.objects.new("TopLight", top); bpy.context.collection.objects.link(to); to.location = (0, 0.1, 3.1)
        to.rotation_euler = (0, 0, 0)
        c["top"] = to
        r = area_light((-2.5, -1.5, 1.6), (math.radians(70), 0, math.radians(-55)), 1.5, 25, (0.55, 0.65, 0.9)); r.visible_camera = False
        haze((0, 0, 2.0), (4, 4, 2.4), density=0.02, color=(0.9, 0.9, 0.9), anis=0.5)
    else:  # tape
        world_flat((0.004, 0.005, 0.008), 1.0)
        brick = ph.texture("concrete_floor_02", scale=0.7, name="NightWall", tint=(0.16, 0.16, 0.18))
        box("Wall", (0, 0.6, 1.8), (10, 0.1, 5), brick)
        wet = pbr("WetGround", (0.03, 0.03, 0.035), 0.08, **{'Coat Weight': 0.6})
        box("Ground", (0, -2.5, -0.02), (12, 6.4, 0.04), wet)
        m = logo_material("LogoWall", c["glow"], base_glow=0.0, rough=0.5)
        c["logo"] = logo_plane("Logo", (0, 0.548, 1.5), 2.3, m)
        # tape: a long strip with the classic text, waving in the wind (Wave modifier) and swinging in on a hinge
        tapem = bpy.data.materials.new("Tape"); tapem.use_nodes = True
        N = tapem.node_tree.nodes; L = tapem.node_tree.links; pr = N["Principled BSDF"]
        pr.inputs['Base Color'].default_value = (1.0, 0.72, 0.0, 1); pr.inputs['Roughness'].default_value = 0.35
        tapes = []
        for k, (z, ang) in enumerate(((1.05, -7), (1.95, 9))):
            bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
            tp = bpy.context.active_object; tp.name = "Tape"; tp.scale = (7.0, 0.13, 1); tp.rotation_euler = (math.radians(90), 0, 0)
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
            mod = tp.modifiers.new("sub", 'SUBSURF'); mod.subdivision_type = 'SIMPLE'; mod.levels = 6; mod.render_levels = 6
            wv = tp.modifiers.new("wave", 'WAVE'); wv.use_normal = True; wv.use_x = False; wv.use_y = True
            wv.height = 0.03; wv.width = 0.6; wv.speed = 0.06; wv.narrowness = 1.5
            tp.data.materials.append(tapem)
            txt = text_obj("TapeTxt", "CRIME SCENE   DO NOT CROSS   CRIME SCENE   DO NOT CROSS   CRIME SCENE", (0, -0.045, -0.036), 0.085,
                           pbr("TapeInk", (0.02, 0.02, 0.02), 0.5), rot=(math.radians(90), 0, 0), extrude=0.0)
            txt.parent = tp
            tp.location = (0, -1.4 - 0.25 * k, z); tp.rotation_euler = (0, math.radians(ang), 0)
            tapes.append((tp, z, ang, k))
        c["tapes"] = tapes
        # police lights: red and blue area lights off frame, flickering by frame driver
        for name, col, ph_, x in (("PoliceRed", (1.0, 0.05, 0.03), 0, -3.0), ("PoliceBlue", (0.05, 0.2, 1.0), 3, 3.0)):
            l = bpy.data.lights.new(name, 'AREA'); l.size = 1.2; l.color = col
            d = l.driver_add("energy").driver; d.type = 'SCRIPTED'
            d.expression = f"420 * max(0.0, sin((frame + {ph_}) * 0.55)) ** 6"
            o = bpy.data.objects.new(name, l); bpy.context.collection.objects.link(o); o.location = (x, -2.6, 2.4)
            o.rotation_euler = (Vector((0, 0.5, 1.6)) - o.location).to_track_quat('-Z', 'Y').to_euler()
            o.visible_camera = False
        street = bpy.data.lights.new("StreetLamp", 'SPOT'); street.spot_size = math.radians(70); street.energy = 380
        street.color = (1.0, 0.72, 0.4)
        so = bpy.data.objects.new("StreetLamp", street); bpy.context.collection.objects.link(so); so.location = (1.6, -0.6, 4.2)
        so.rotation_euler = (Vector((0, 0.5, 1.5)) - so.location).to_track_quat('-Z', 'Y').to_euler()
        rain = bpy.data.materials.new("Rain"); rain.use_nodes = True
        rp = rain.node_tree.nodes["Principled BSDF"]; rp.inputs['Base Color'].default_value = (0.8, 0.85, 0.9, 1)
        rp.inputs['Transmission Weight'].default_value = 1.0; rp.inputs['Roughness'].default_value = 0.0
        rng = np.random.default_rng(3); drops = []
        src = cyl("RainSrc", (0, 0, -50), 0.0025, 0.35, rain, verts=6)
        for _ in range(420):
            p = Vector((rng.uniform(-3.6, 3.6), rng.uniform(-3.0, 0.4), rng.uniform(0, 4)))
            drops.append((instance(src, tuple(p)), p, rng.uniform(5.5, 7.5)))
        c["drops"] = drops
        haze((0, -1.4, 1.8), (9, 4.2, 4), density=0.015, color=(0.75, 0.8, 0.9))
    return c


# ---------------------------------------------------------------------------------------------------- animation
def _glow(c, v):
    for g in c["glow"]:
        g.outputs[0].default_value = v


def anim_torch(c, t):
    s = t * DUR["torch"]
    # beam sweeps from far left, overshoots slightly, settles on the logo at ~2.0 s
    u = ease(min(1.0, max(0.0, (s - 0.35) / 1.7)))
    aim = Vector((-3.6, 0, 0.9)).lerp(Vector((0.0, 0, 1.45)), u) + Vector((0.12 * math.sin(s * 2.1) * (1 - u), 0, 0))
    to = c["torch"]; to.rotation_euler = (aim - to.location).to_track_quat('-Z', 'Y').to_euler()
    on = 1.0 if s > 0.3 else 0.0                                   # click on
    flick = 0.25 if 0.3 < s < 0.38 else 1.0
    g = ease(min(1.0, max(0.0, (s - 2.15) / 0.5)))
    to.data.energy = 900 * on * flick * (1 - 0.55 * g)
    _glow(c, 1.25 * g * (1 + 0.04 * math.sin(s * 23)))
    c["fill"].data.energy = 30 * g


def anim_board(c, t):
    s = t * DUR["board"]
    for (o, p0, hub, delay) in c["strings"]:
        u = ease(min(1.0, max(0.0, (s - 0.3 - delay) / 1.6)))
        sag = 0.45 * (1 - u) + 0.01
        mid = (p0 + hub) / 2
        sp = o.data.splines[0]
        for i, pt in enumerate(sp.points):
            a = i / (len(sp.points) - 1)
            q = p0.lerp(hub, a) if u > 0 else p0.lerp(mid + Vector((0, 0, -0.6)), a)
            if u > 0:
                q = q + Vector((0, -0.02 * math.sin(math.pi * a), -sag * math.sin(math.pi * a)))
                # strings start loose (only part-way), then reach the hub
                q = p0.lerp(q, min(1.0, 0.25 + u))
            pt.co = (q.x, q.y, q.z, 1)
    g = ease(min(1.0, max(0.0, (s - 2.3) / 0.6)))
    _glow(c, 1.0 * g)
    c["lamp"].data.energy = 520 * (0.9 + 0.1 * g)


def anim_bag(c, t):
    s = t * DUR["bag"]
    z_table = 0.92 + 0.008
    if s < 0.9:                                   # falls in from above, slightly tilted
        u = s / 0.9
        z = z_table + 1.4 * (1 - u * u); tilt = math.radians(18) * (1 - u)
    else:                                         # two small settle bounces
        k = s - 0.9
        z = z_table + 0.05 * abs(math.sin(k * 9)) * math.exp(-k * 6); tilt = math.radians(2) * math.exp(-k * 5) * math.sin(k * 12)
    c["bag"].location = (0.0, 0.0, z); c["bag"].rotation_euler = (tilt, 0, math.radians(-6))
    g = ease(min(1.0, max(0.0, (s - 1.9) / 0.6)))
    _glow(c, 0.9 * g)
    c["top"].data.energy = 420 * (1.0 if s > 0.15 else 0.0) * (0.35 if 0.15 < s < 0.22 else 1.0)


def anim_tape(c, t):
    s = t * DUR["tape"]
    for (tp, z, ang, k) in c["tapes"]:
        u = ease(min(1.0, max(0.0, (s - 0.2 - 0.35 * k) / 1.1)))
        swing = (1 - u) * 75 * (1 if k == 0 else -1) + 6 * math.sin(s * 3 + k) * (1 - u) ** 0.5
        tp.rotation_euler = (0, math.radians(ang + swing * 0.15), math.radians(swing))
        tp.location = (8 * (1 - u) * (1 if k == 0 else -1), -1.4 - 0.25 * k, z)
    for o, p, v in c["drops"]:
        zz = (p.z - s * v) % 4.0
        o.location = (p.x, p.y, zz)
    g = ease(min(1.0, max(0.0, (s - 1.8) / 0.8)))
    _glow(c, 1.15 * g)


def _cam_torch(c, t):
    return (Vector((0.0, -4.6, 1.5)).lerp(Vector((0.0, -3.7, 1.47)), ease(t)), Vector((0, 0, 1.45)), 40)


def _cam_board(c, t):
    return (Vector((-0.45, -4.4, 1.4)).lerp(Vector((0.0, -2.9, 1.55)), ease(t)), Vector((0, 0.1, 1.55)), 40)


def _cam_bag(c, t):
    e = ease(t)
    return (Vector((0.15, -1.35, 1.35)).lerp(Vector((0.0, -0.95, 1.3)), e), Vector((0, 0.02, 0.93)), 42)


def _cam_tape(c, t):
    return (Vector((0.25, -4.9, 1.45)).lerp(Vector((0.0, -4.2, 1.5)), ease(t)), Vector((0, 0.5, 1.5)), 38)


MOVES = {
    "torch": dict(kind="anim", dof=4.0, far=20.0, anim=anim_torch, cam=_cam_torch, focus=lambda c, t: Vector((0, 0, 1.45))),
    "board": dict(kind="anim", dof=4.0, far=20.0, anim=anim_board, cam=_cam_board, focus=lambda c, t: Vector((0, 0.09, 1.55))),
    "bag": dict(kind="anim", dof=2.8, far=20.0, anim=anim_bag, cam=_cam_bag, focus=lambda c, t: c["bag"].location),
    "tape": dict(kind="anim", dof=2.8, far=20.0, anim=anim_tape, cam=_cam_tape, focus=lambda c, t: Vector((0, 0.5, 1.5))),
}
