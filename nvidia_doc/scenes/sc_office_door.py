"""Reconstruction: a locked frameless glass door on an office floor; beyond it a dim reception with two gray
armchairs and the company's name on the wall in plain letters (no logo)."""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *

EXPOSURE = 0.9
DOOR_Y = 0.0          # glass line; corridor is y < 0, reception y > 0
VARIANT_FOR = {"door_push": "day"}      # CH1 12B: the reporters' daytime visit (the night set stays for the other moves)


def armchair(loc, rot, fab, leg):
    parts = [box("Seat", (0, 0, 0.36), (0.74, 0.7, 0.16), fab, bevel=0.04),
             box("Back", (0, 0.3, 0.62), (0.74, 0.14, 0.46), fab, bevel=0.05),
             box("ArmL", (-0.36, 0.0, 0.5), (0.12, 0.7, 0.32), fab, bevel=0.04),
             box("ArmR", (0.36, 0.0, 0.5), (0.12, 0.7, 0.32), fab, bevel=0.04)]
    for dx in (-0.3, 0.3):
        for dy in (-0.27, 0.27):
            parts.append(cyl("Leg", (dx, dy, 0.13), 0.018, 0.26, leg, verts=12))
    c = join(parts, "Armchair"); c.location = loc; c.rotation_euler = (0, 0, rot)
    for p in c.data.polygons:
        p.use_smooth = True
    sub = c.modifiers.new("sub", 'SUBSURF'); sub.levels = 1; sub.render_levels = 2
    return c


def build(variant=None):
    if variant == "day":
        return build_day()
    world_flat((0.004, 0.005, 0.007), 1.0)
    stone = pbr("Stone", (0.38, 0.37, 0.35), 0.12, 0.0, **{'Coat Weight': 0.3, 'Coat Roughness': 0.05})
    nt = stone.node_tree; N = nt.nodes; L = nt.links; tc = N.new("ShaderNodeTexCoord")
    tl = N.new("ShaderNodeTexBrick"); tl.inputs['Scale'].default_value = 1 / 0.6; tl.offset = 0.0
    tl.inputs['Brick Width'].default_value = 1.2; tl.inputs['Row Height'].default_value = 0.6; tl.inputs['Mortar Size'].default_value = 0.002
    tl.inputs['Color1'].default_value = (0.36, 0.355, 0.34, 1); tl.inputs['Color2'].default_value = (0.30, 0.295, 0.285, 1)
    L.new(tc.outputs['Object'], tl.inputs['Vector']); L.new(tl.outputs['Color'], N["Principled BSDF"].inputs['Base Color'])
    box("Floor", (0, 0, -0.01), (12, 16, 0.02), stone)
    wall = pbr("Wall", (0.55, 0.55, 0.54), 0.7)
    ceil_m = pbr("Ceil", (0.6, 0.6, 0.6), 0.8)
    box("Ceiling", (0, 0, 2.8), (12, 16, 0.02), ceil_m)
    # corridor side walls (behind camera, give the glass something to reflect)
    box("CorrWallL", (-3.2, -4, 1.4), (0.05, 8, 2.8), wall); box("CorrWallR", (3.2, -4, 1.4), (0.05, 8, 2.8), wall)
    for k in range(4):
        box("Downlight", (0, -1.2 - k * 2.0, 2.78), (0.2, 0.2, 0.01), emissive("DL", (1.0, 0.93, 0.85), 30))
        l = bpy.data.lights.new("DLl", 'SPOT'); l.energy = 120; l.spot_size = math.radians(100); l.spot_blend = 0.6; l.color = (1.0, 0.92, 0.82)
        o = bpy.data.objects.new("DLl", l); bpy.context.collection.objects.link(o); o.location = (0, -1.2 - k * 2.0, 2.76); o.rotation_euler = (0, 0, 0)
    # glass partition and the double door
    gl = glass("DoorGlass", (0.93, 0.97, 0.98), 0.0)
    for x in (-2.2, 2.2):
        box("SidePanel", (x, DOOR_Y, 1.38), (2.2, 0.012, 2.76), gl)
    doorL = box("DoorL", (-0.53, DOOR_Y, 1.2), (1.02, 0.012, 2.4), gl)
    doorR = box("DoorR", (0.53, DOOR_Y, 1.2), (1.02, 0.012, 2.4), gl)
    box("Transom", (0, DOOR_Y, 2.58), (2.1, 0.012, 0.36), gl)
    ss = brushed_metal("Steel", (0.75, 0.76, 0.78), (0.12, 0.25), 0.6, axis=(1, 1, 300))
    for x in (-0.07, 0.07):
        for side in (-1, 1):
            cyl("Handle", (x, DOOR_Y + side * 0.06, 1.05), 0.014, 1.2, ss, verts=24)
            for z in (0.5, 1.6):
                cyl("Standoff", (x, DOOR_Y + side * 0.03, z), 0.009, 0.06, ss, verts=16, rot=(math.radians(90), 0, 0))
    # patch fittings + the floor lock
    for x in (-1.0, 1.0):
        box("PatchTop", (x * 0.98, DOOR_Y, 2.37), (0.18, 0.05, 0.08), ss, bevel=0.01)
        box("PatchBot", (x * 0.98, DOOR_Y, 0.05), (0.18, 0.05, 0.08), ss, bevel=0.01)
    box("Lock", (0.0, DOOR_Y, 0.06), (0.22, 0.06, 0.09), ss, bevel=0.012)
    cyl("Cylinder", (0.0, DOOR_Y - 0.035, 0.065), 0.013, 0.01, pbr("Brass", (0.8, 0.6, 0.3), 0.3, 1.0), rot=(math.radians(90), 0, 0))
    # reception beyond
    box("BackWall", (0, 5.0, 1.4), (8, 0.05, 2.8), pbr("Panel", (0.08, 0.075, 0.07), 0.45, 0.0))
    box("SideWallL", (-3.5, 2.5, 1.4), (0.05, 5, 2.8), wall); box("SideWallR", (3.5, 2.5, 1.4), (0.05, 5, 2.8), wall)
    desk_m = pbr("Desk", (0.75, 0.74, 0.72), 0.3, 0.0, **{'Coat Weight': 0.4})
    box("Desk", (0.9, 3.6, 0.55), (2.2, 0.7, 1.1), desk_m, bevel=0.02)
    letters = brushed_metal("Letters", (0.78, 0.79, 0.8), (0.15, 0.3), 0.5)
    name = text_obj("Nameplate", "MEGASPEED", (0.0, 4.97, 1.85), 0.24, letters, rot=(math.radians(90), 0, math.radians(180)), extrude=0.01,
                    font_path="/usr/share/fonts/opentype/inter/Inter-Medium.otf", spacing=1.3)
    name.rotation_euler = (math.radians(90), 0, 0)
    gray = fabric("GrayFabric", (0.20, 0.205, 0.21), 0.92, 0.5, 700)
    leg = brushed_metal("LegMetal", (0.2, 0.2, 0.21), (0.3, 0.4), 0.2)
    ch1 = armchair((-2.05, 2.4, 0), math.radians(12), gray, leg)
    ch2 = armchair((-0.75, 2.4, 0), math.radians(-12), gray, leg)
    dark = pbr("TableTop", (0.03, 0.03, 0.032), 0.3, 0.2)
    cyl("CoffeeTable", (-1.4, 2.3, 0.4), 0.26, 0.025, dark, verts=48); cyl("CTLeg", (-1.4, 2.3, 0.2), 0.018, 0.4, leg)
    # after hours: a couple of dim lights left on inside, an exit sign glow
    for (x, y) in ((-1.3, 2.4), (1.0, 3.6)):
        l = bpy.data.lights.new("In", 'SPOT'); l.energy = 55; l.spot_size = math.radians(80); l.spot_blend = 0.8; l.color = (1.0, 0.85, 0.7)
        o = bpy.data.objects.new("In", l); bpy.context.collection.objects.link(o); o.location = (x, y, 2.76)
    wash = bpy.data.lights.new("Wash", 'AREA'); wash.energy = 12; wash.size = 3; wash.color = (0.8, 0.88, 1.0)
    o = bpy.data.objects.new("Wash", wash); bpy.context.collection.objects.link(o); o.location = (0, 4.5, 2.7)
    box("Exit", (2.8, 4.9, 2.4), (0.3, 0.02, 0.12), emissive("Exit", (0.3, 1.0, 0.5), 8))
    # CH2 7B: a desk phone on the reception desk; its line light blinks while it rings, unanswered
    phone_m = pbr("PhoneBody", (0.03, 0.03, 0.033), 0.35)
    box("DeskPhone", (1.4, 3.45, 1.13), (0.22, 0.2, 0.05), phone_m, bevel=0.01, rot=(math.radians(-10), 0, math.radians(-15)))
    box("Handset", (1.33, 3.43, 1.17), (0.06, 0.2, 0.035), phone_m, bevel=0.012, rot=(math.radians(-10), 0, math.radians(-15)))
    lm = bpy.data.materials.new("RingLight"); lm.use_nodes = True
    N = lm.node_tree.nodes; L = lm.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); em = N.new("ShaderNodeEmission"); em.inputs['Color'].default_value = (1.0, 0.35, 0.15, 1)
    v = N.new("ShaderNodeValue"); d = v.outputs[0].driver_add("default_value").driver; d.type = 'SCRIPTED'
    d.expression = "8 * (1 if (frame % 24) < 12 else 0.02)"
    L.new(v.outputs[0], em.inputs['Strength']); L.new(em.outputs[0], out.inputs['Surface'])
    box("RingLED", (1.47, 3.38, 1.16), (0.025, 0.012, 0.01), lm, rot=(math.radians(-10), 0, math.radians(-15)))
    rl = bpy.data.lights.new("RingGlow", 'POINT'); rl.color = (1.0, 0.4, 0.2); rl.shadow_soft_size = 0.02
    dl = rl.driver_add("energy").driver; dl.type = 'SCRIPTED'; dl.expression = "3 * (1 if (frame % 24) < 12 else 0.02)"
    ro = bpy.data.objects.new("RingGlow", rl); bpy.context.collection.objects.link(ro); ro.location = (1.47, 3.36, 1.2)
    return dict(door=Vector((0, DOOR_Y, 1.1)), chairs=Vector((-1.3, 2.0, 0.55)), name=Vector((0, 4.95, 1.95)), phone=Vector((1.4, 3.45, 1.15)))


# ============================================================================ CH1 12B: daytime, two reporters at the locked door
def _grey(root_meshes, val=0.32):
    """Re-colour a scanned model to a mid grey fabric (keeps its texture detail as value only)."""
    for o in root_meshes:
        for m in o.data.materials:
            if not m or not m.use_nodes:
                continue
            N = m.node_tree.nodes; L = m.node_tree.links
            p = next((n for n in N if n.type == 'BSDF_PRINCIPLED'), None)
            if p is None:
                continue
            src = p.inputs['Base Color'].links[0].from_socket if p.inputs['Base Color'].links else None
            hs = N.new("ShaderNodeHueSaturation"); hs.inputs['Saturation'].default_value = 0.0; hs.inputs['Value'].default_value = 1.0
            if src is not None:
                L.new(src, hs.inputs['Color'])
            else:
                hs.inputs['Color'].default_value = p.inputs['Base Color'].default_value
            g = N.new("ShaderNodeMix"); g.data_type = 'RGBA'; g.blend_type = 'MULTIPLY'; g.inputs['Factor'].default_value = 1.0
            L.new(hs.outputs['Color'], g.inputs[6]); g.inputs[7].default_value = (val * 1.6, val * 1.62, val * 1.66, 1)
            L.new(g.outputs[2], p.inputs['Base Color'])


def _stand(h, loc, face):
    from human import pose_walk, _world_verts
    pose_walk(h, 0.0, stride=0.0, arm_swing=0.0)
    h.arm.rotation_euler = (0, 0, face); h.arm.location = (loc[0], loc[1], 0); bpy.context.view_layer.update()
    if not hasattr(h, "foot0"):
        w = np.concatenate([_world_verts(o) for o in h.parts if o.type == 'MESH'])
        h.foot0 = -float(w[:, 2].min())
    h.arm.location.z = h.foot0; bpy.context.view_layer.update()


def build_day():
    from human import Human, add_asset
    import ph
    c = {}
    bpy.context.scene.view_settings.exposure = -0.6           # the module exposure is set for the night set
    world_sky(sun_elev_deg=38, sun_rot_deg=200, strength=0.6, tint=(0.95, 0.97, 1.0))
    # ---------------------------------------------------------------- shell: corridor (y < 0) along X, reception (y > 0)
    floor_m = pbr("CorrFloor", (0.62, 0.61, 0.58), 0.25, 0.0, **{'Coat Weight': 0.3, 'Coat Roughness': 0.12})
    nt = floor_m.node_tree; N = nt.nodes; L = nt.links; tc = N.new("ShaderNodeTexCoord")
    tl = N.new("ShaderNodeTexBrick"); tl.inputs['Scale'].default_value = 1 / 0.6; tl.offset = 0.0
    tl.inputs['Brick Width'].default_value = 1.2; tl.inputs['Row Height'].default_value = 0.6; tl.inputs['Mortar Size'].default_value = 0.0015
    tl.inputs['Color1'].default_value = (0.64, 0.63, 0.6, 1); tl.inputs['Color2'].default_value = (0.6, 0.59, 0.56, 1); tl.inputs['Mortar'].default_value = (0.45, 0.44, 0.42, 1)
    L.new(tc.outputs['Object'], tl.inputs['Vector']); L.new(tl.outputs['Color'], N["Principled BSDF"].inputs['Base Color'])
    box("Floor", (0, 0, -0.01), (16, 14, 0.02), floor_m)
    wall = pbr("WallWarm", (0.72, 0.71, 0.68), 0.75)
    ceil_m = pbr("Ceil", (0.8, 0.8, 0.79), 0.85)
    box("Ceiling", (0, 0, 2.8), (16, 14, 0.04), ceil_m)
    box("CorrWallFar", (0, -3.85, 1.4), (16, 0.1, 2.8), wall)                    # behind the camera
    box("CorrWallL", (-2.2 - 2.45, 0.0, 1.4), (4.9, 0.12, 2.8), wall)           # solid walls either side of the glass front
    box("CorrWallR", (2.2 + 2.45, 0.0, 1.4), (4.9, 0.12, 2.8), wall)
    # corridor end window on the left: the city in daylight beyond
    box("EndWallLow", (-7.0, -1.9, 0.4), (0.12, 3.8, 0.8), wall); box("EndWallHigh", (-7.0, -1.9, 2.65), (0.12, 3.8, 0.3), wall)
    box("EndGlass", (-7.0, -1.9, 1.65), (0.02, 3.8, 1.7), glass("EndGlass", (0.9, 0.94, 0.96), 0.0))
    frame = pbr("WinFrameAlu", (0.55, 0.56, 0.58), 0.35, 0.9)
    for yy in (-3.75, -1.9, -0.05):
        box("WinMull", (-7.0, yy, 1.65), (0.08, 0.05, 1.7), frame)
    bm_ = pbr("CityBody", (0.62, 0.64, 0.66), 0.5, 0.2)
    win = window_material("CityWin", lit=(0.8, 0.85, 0.9), density=0.0, floor=3.6, bay=1.8, strength=0.0, glass_col=(0.18, 0.24, 0.3))
    skyline(5, (-60, -10), (25, 40), 18, (40, 160), bm_, win, footprint=(14, 30), z0=-25)
    # skirting + downlights (round cans; the light comes from area lights you don't see)
    skirt = pbr("Skirt", (0.25, 0.25, 0.26), 0.4)
    box("SkirtFar", (0, -3.79, 0.05), (16, 0.02, 0.1), skirt)
    rim = pbr("DLRim", (0.85, 0.85, 0.85), 0.3, 0.6)
    for k in range(-3, 4):
        x = k * 2.0
        cyl("DLCan", (x, -1.9, 2.775), 0.09, 0.012, rim, verts=24)
        cyl("DLLens", (x, -1.9, 2.768), 0.07, 0.003, emissive("DLLens", (1.0, 0.96, 0.9), 4.0), verts=24)
        l = bpy.data.lights.new("CorrL", 'AREA'); l.energy = 140; l.size = 0.9; l.color = (1.0, 0.95, 0.88)
        o = bpy.data.objects.new("CorrL", l); bpy.context.collection.objects.link(o); o.location = (x, -1.9, 2.74); o.visible_camera = False
    sun_ = bpy.data.lights.new("WinSun", 'AREA'); sun_.energy = 900; sun_.size = 2.4; sun_.color = (1.0, 0.96, 0.9)
    so = bpy.data.objects.new("WinSun", sun_); bpy.context.collection.objects.link(so); so.location = (-6.8, -1.3, 1.7)
    point_at(so, (-4.5, -1.3, 0.6)); so.visible_camera = False
    # ---------------------------------------------------------------- frameless glass front and double door
    gl = glass("DoorGlass", (0.94, 0.97, 0.98), 0.0)
    frost = pbr("Frost", (0.9, 0.92, 0.93), 0.35, 0.0, **{'Transmission Weight': 0.85, 'Alpha': 0.55})
    for x in (-1.64, 1.64):
        box("SidePanel", (x, DOOR_Y, 1.38), (1.1, 0.012, 2.76), gl)
        box("Manifest", (x, DOOR_Y - 0.008, 1.05), (1.1, 0.002, 0.07), frost)
    ss = brushed_metal("Steel", (0.75, 0.76, 0.78), (0.12, 0.25), 0.6, axis=(1, 1, 300))
    doors = []
    for sx in (-1, 1):
        parts = [box("DoorLeaf", (sx * 0.545, 0, 1.2), (1.07, 0.012, 2.4), gl),
                 box("DoorFrost", (sx * 0.545, -0.008, 1.05), (1.07, 0.002, 0.07), frost)]
        for side in (-1, 1):
            parts.append(cyl("Handle", (sx * 0.07, side * 0.06, 1.05), 0.014, 1.0, ss, verts=24))
            for z in (0.6, 1.5):
                parts.append(cyl("Standoff", (sx * 0.07, side * 0.03, z), 0.009, 0.06, ss, verts=16, rot=(math.radians(90), 0, 0)))
        parts.append(box("PatchTop", (sx * 0.98, 0, 2.37), (0.18, 0.05, 0.08), ss, bevel=0.01))
        parts.append(box("PatchBot", (sx * 0.98, 0, 0.05), (0.18, 0.05, 0.08), ss, bevel=0.01))
        d = join(parts, f"Door{sx}"); d.location = (0, DOOR_Y, 0)
        doors.append(d)
    box("Transom", (0, DOOR_Y, 2.6), (2.2, 0.012, 0.36), gl)
    box("Lock", (0.0, DOOR_Y, 0.06), (0.22, 0.06, 0.09), ss, bevel=0.012)
    c["door"] = doors[0]                                     # the left leaf (handle at x = -0.07) is the one he pulls
    # ---------------------------------------------------------------- reception beyond: bright, empty, daylit
    rwall = pbr("RecWall", (0.78, 0.77, 0.74), 0.7)
    box("RecSideL", (-3.6, 2.6, 1.4), (0.1, 5.2, 2.8), rwall)
    # feature wall: light oak slats behind the nameplate
    oak = wood("Oak", dark=(0.32, 0.2, 0.1), light=(0.55, 0.38, 0.22), scale=(1, 26, 26), rough=0.4, coat=0.2)
    box("FeatureWall", (0.3, 5.05, 1.4), (6.0, 0.1, 2.8), oak)
    for k in range(40):
        box("Slat", (-2.6 + k * 0.15, 4.97, 1.4), (0.05, 0.06, 2.8), oak)
    letters = brushed_metal("Letters", (0.72, 0.73, 0.75), (0.12, 0.25), 0.5)
    name = text_obj("Nameplate", "MEGASPEED", (0.3, 4.9, 1.95), 0.26, letters, extrude=0.012,
                    font_path="/usr/share/fonts/opentype/inter/Inter-Medium.otf", spacing=1.3)
    name.rotation_euler = (math.radians(90), 0, 0)
    # reception counter: white stone top on a rounded oak front
    top_m = pbr("CounterTop", (0.86, 0.86, 0.84), 0.15, 0.0, **{'Coat Weight': 0.5})
    box("Counter", (1.25, 3.6, 0.54), (2.4, 0.7, 1.08), pbr("CounterFront", (0.82, 0.81, 0.78), 0.3, 0.0, **{"Coat Weight": 0.3}), bevel=0.06)
    box("CounterTop", (1.25, 3.58, 1.1), (2.5, 0.8, 0.04), top_m, bevel=0.012)
    box("CounterKick", (1.25, 3.6, 0.05), (2.3, 0.6, 0.1), pbr("Kick", (0.12, 0.12, 0.12), 0.4))
    # two gray armchairs (scanned), a low table, a plant
    for (x, y, rz) in ((-1.5, 1.75, 90 - 15), (-1.45, 3.0, 90 + 15)):
        root, ms = ph.model("modern_arm_chair_01", loc=(x, y, 0), rot_z=math.radians(rz))
        _grey(ms, 0.42)
    ph.model("modern_coffee_table_01", loc=(-1.3, 2.38, 0), rot_z=math.radians(90))
    ph.model("potted_plant_02", loc=(-3.1, 4.5, 0), scale=1.4)
    # reception window wall on the left lets daylight in; soft ceiling fill
    rs = bpy.data.lights.new("RecDay", 'AREA'); rs.energy = 600; rs.size = 4.5; rs.color = (0.95, 0.97, 1.0)
    ro = bpy.data.objects.new("RecDay", rs); bpy.context.collection.objects.link(ro); ro.location = (-3.45, 2.6, 1.8)
    point_at(ro, (0.5, 2.6, 0.8)); ro.visible_camera = False
    for (x, y) in ((-1.5, 1.5), (1.5, 1.5), (-1.5, 3.8), (1.5, 3.8)):
        l = bpy.data.lights.new("RecL", 'AREA'); l.energy = 150; l.size = 1.0; l.color = (1.0, 0.95, 0.88)
        o = bpy.data.objects.new("RecL", l); bpy.context.collection.objects.link(o); o.location = (x, y, 2.74); o.visible_camera = False
        cyl("DLCan", (x, y, 2.775), 0.09, 0.012, rim, verts=24)
        cyl("DLLens", (x, y, 2.768), 0.07, 0.003, emissive("DLLens2", (1.0, 0.96, 0.9), 4.0), verts=24)
    # ---------------------------------------------------------------- the two reporters
    w = Human("ReporterW", gender=0.0, years=31, muscle=0.45, weight=0.4, height=0.5, eyelashes="eyelashes01",
              skin="middleage_lightskinned_female_diffuse.png")
    add_asset(w, "clothes", "female_elegantsuit01", tint=(0.75, 0.72, 0.68), sat=0.3, val=0.9, rough=0.7)
    add_asset(w, "clothes", "shoes02", val=0.2, rough=0.4)
    add_asset(w, "hair", "ponytail01", val=0.18, rough=0.45)
    m = Human("ReporterM", gender=1.0, years=38, muscle=0.5, weight=0.45, height=0.5, eyelashes="eyelashes01",
              skin="middleage_lightskinned_male_diffuse.png")
    add_asset(m, "clothes", "male_casualsuit03", tint=(0.45, 0.5, 0.62), sat=0.3, val=0.7, rough=0.7)
    add_asset(m, "clothes", "shoes02", val=0.2, rough=0.4)
    add_asset(m, "hair", "short03", val=0.15, rough=0.45)
    c["w"], c["m"] = w, m
    _stand(w, (-1.2, -0.75), math.pi)                 # both face +Y, the glass
    _stand(m, (0.3, -0.5), math.pi + 0.25)
    # props: her notebook, his camera on a strap
    pad = pbr("Notebook", (0.85, 0.84, 0.8), 0.7)
    nb = join([box("Pad", (0, 0, 0), (0.1, 0.15, 0.008), pad, bevel=0.002),
               box("PadCover", (0, 0, -0.0045), (0.102, 0.152, 0.002), pbr("PadCover", (0.12, 0.14, 0.2), 0.5))], "Notebook")
    c["nb"] = nb
    camb = pbr("CamBody", (0.03, 0.03, 0.032), 0.45)
    cam_obj = join([box("CamBody", (0, 0, 0), (0.13, 0.075, 0.09), camb, bevel=0.012),
                    cyl("CamLens", (0, -0.075, -0.005), 0.033, 0.08, camb, verts=32, rot=(math.radians(90), 0, 0)),
                    cyl("CamRing", (0, -0.112, -0.005), 0.035, 0.008, pbr("LensRing", (0.2, 0.2, 0.21), 0.3, 0.8), verts=32, rot=(math.radians(90), 0, 0))], "PressCamera")
    c["camera_prop"] = cam_obj
    animate_day(c, 0.0)
    # strap: from his left shoulder across the back to the camera at his right hip (static on his torso)
    sh = m.bone_head("clavicle.L") + Vector((0, 0, 0.03))
    p1 = cam_obj.location + Vector((0, 0, 0.05))
    cu = bpy.data.curves.new("Strap", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.008; cu.bevel_resolution = 1
    sp = cu.splines.new('BEZIER'); sp.bezier_points.add(2)
    fwd = Vector((math.sin(m.arm.rotation_euler.z), -math.cos(m.arm.rotation_euler.z), 0))
    mid = m.bone_head("spine03") - fwd * 0.16 + Vector((0, 0, 0.02))   # across his back
    for bp, pt in zip(sp.bezier_points, (sh, mid, p1)):
        bp.co = pt; bp.handle_left_type = bp.handle_right_type = 'AUTO'
    so_ = bpy.data.objects.new("Strap", cu); bpy.context.collection.objects.link(so_); so_.data.materials.append(pbr("StrapM", (0.02, 0.02, 0.02), 0.6))
    for o in bpy.data.objects:
        if o.type == 'LIGHT' and o.data.type == 'AREA':
            o.visible_camera = False; o.visible_glossy = False; o.visible_transmission = False
    c.update(chairs=Vector((-2.4, 2.35, 0.5)), name=Vector((0.3, 4.9, 1.95)), glass=Vector((-0.1, 0.0, 1.35)))
    return c


def animate_day(c, t):
    """He tries the handle twice (a small pull; the locked leaf only clicks); she holds her notebook, writes a word."""
    from human import reach, fingers_curl
    w, m = c["w"], c["m"]
    _stand(w, (-1.2, -0.75), math.pi); _stand(m, (0.3, -0.5), math.pi + 0.25)
    # --- her: notebook at chest height, pen hand moving a little
    fw = Vector((0, 1, 0)); sd_w = fw.cross(Vector((0, 0, 1)))                # her right is -X
    chest = w.bone_head("spine03")
    padc = chest + fw * 0.3 + Vector((0, 0, -0.12))
    reach(w, "L", padc + Vector((0.07, -0.02, -0.01)), Vector((0.6, 0, -0.8)), Vector((-0.6, 0.6, 0.3)))
    wr = 0.012 * math.sin(t * 40) * (1 if 0.2 < t < 0.7 else 0)
    reach(w, "R", padc + Vector((-0.05 + wr, 0.0, 0.03)), Vector((-0.6, 0, -0.8)), Vector((0.3, 0.8, -0.4)))
    fingers_curl(w, 35, thumb=20)
    w.rot("head", Vector((1, 0, 0)), -12)
    nb = c["nb"]; nb.location = padc; nb.rotation_euler = (math.radians(-35), 0, 0)
    # --- him: left hand to the handle (x = -0.07, corridor side), two short pulls, then lets go
    h_at = Vector((-0.07, DOOR_Y - 0.06 - 0.025, 1.05))
    reach_k = ease(min(1.0, max(0.0, (t - 0.08) / 0.2))) * (1 - ease(min(1.0, max(0.0, (t - 0.66) / 0.16))))
    pull = 0.03 * (max(0.0, math.sin(min(1.0, max(0.0, (t - 0.32) / 0.12)) * math.pi)) +
                   max(0.0, math.sin(min(1.0, max(0.0, (t - 0.52) / 0.1)) * math.pi)))
    rest = m.bone_head("upperarm01.L") + Vector((0.02, 0.05, -0.55))
    hand = rest.lerp(h_at + Vector((0, -pull, 0)), reach_k) + Vector((0, -0.05, 0)) * reach_k
    reach(m, "L", hand, Vector((-0.4, -0.3, -0.8)), Vector((0.35, 1, 0)).normalized().lerp(Vector((0, 0.2, -1)), 1 - reach_k))
    fingers_curl(m, 15 + 45 * reach_k, side=("L",), thumb=20)
    reach(m, "R", m.bone_head("upperarm01.R") + Vector((0.03, 0.0, -0.53)), Vector((0, -1, -0.3)), Vector((0, 0.15, -1)))
    fingers_curl(m, 20, side=("R",), thumb=10)
    m.rot("head", Vector((0, 0, 1)), 8 * reach_k)
    # the locked leaf only clicks against its bolt (+ an invisible 0.1 mm drift so a bake's 3-sample check keys it)
    c["door"].location.y = DOOR_Y - 0.003 * min(1.0, pull / 0.03) - 0.0001 * t
    # camera hangs at his right hip
    mf = Vector((math.sin(m.arm.rotation_euler.z), -math.cos(m.arm.rotation_euler.z), 0)); ms_ = mf.cross(Vector((0, 0, 1)))
    hip = m.bone_head("upperleg01.R")
    cp = c["camera_prop"]; cp.location = hip + ms_ * 0.11 - mf * 0.03 + Vector((0, 0, 0.06))
    cp.rotation_euler = (0, 0, m.arm.rotation_euler.z + 0.3)
    bpy.context.view_layer.update()


def cam_day(c, t):
    e = ease(t)
    # from behind their shoulders, then on between them (his hand is back at his side by then) to the glass
    loc = Vector((0.45, -3.45, 1.6)).lerp(Vector((-0.42, -0.32, 1.48)), e)
    tgt = Vector((-0.5, 2.4, 1.2)).lerp(Vector((-0.78, 3.0, 1.22)), e)
    return (loc, tgt, 28 - 2 * e)


MOVES = {
    "phone_ring": dict(kind="anim", dof=2.0, far=20.0,
                       cam=lambda c, t: (Vector((1.1, DOOR_Y - 0.5, 1.32)).lerp(Vector((1.15, DOOR_Y - 0.3, 1.3)), ease(t)), c["phone"], 70),
                       focus=lambda c, t: c["phone"]),
    "door_push": dict(kind="anim", dof=4.0, far=20.0, cam=cam_day, anim=animate_day,
                      focus=lambda c, t: Vector((-0.2, -0.4, 1.3)).lerp(Vector((-1.0, 2.6, 0.8)), ease(min(1.0, max(0.0, (t - 0.35) / 0.6))))),
    "through_glass": dict(kind="plate", dof=2.8, far=20.0,
                          cam=lambda c, t: ((-0.9, -1.2, 1.25), (-1.4, 2.4, 0.5), 38), focus=lambda c, t: (-1.4, 2.4, 0.5)),
    "nameplate": dict(kind="plate", dof=2.4, far=20.0,
                      cam=lambda c, t: ((0.35, -0.9, 1.6), c["name"] + Vector((0, 0, -0.25)), 50), focus=lambda c, t: c["name"]),
}
