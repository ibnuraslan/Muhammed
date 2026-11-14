"""CH5 redo: a moody police interview room (Singapore), house style. Dark walls (painted concrete), one lamp hanging
low over a steel table, a two-way mirror along one wall (dark glass that faintly shows the observation room
behind it), a door with a small wired-glass window, a ceiling camera with a red light, a wall clock whose second
hand turns, a digital recorder with a red record light, files and the passport in the pool of lamplight.
Nobody is shown: Alice is the empty near chair; the passport moves on its own (taken, returned).

  passport_slide  CH5 1A (215 f) + CHAPTER 5 title (same card/layout as the delivered master, so the overlay aligns)
  question        CH5 2A (155 f) the passport slides away from the empty chair
  warning         CH5 4B (248 f) the empty chair under the lamp, slow push; the mirror behind
  passport_back   CH5 5A (136 f) the passport slides back toward the empty chair
"""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
from common import area_light, world_flat

EXPOSURE = 0.0
VARIANT_FOR = {"question": "lift", "warning": "lift", "passport_back": "lift"}   # c5_01 (title) unchanged
TH = 0.75
NEAR_Y, FAR_Y = -0.85, 0.85


def chair(name, y, facing, m_seat, m_frame):
    parts = [box(name + "Pan", (0, y, 0.46), (0.44, 0.44, 0.05), m_seat, bevel=0.01),
             box(name + "Back", (0, y - facing * 0.21, 0.74), (0.42, 0.03, 0.42), m_seat, bevel=0.01)]
    for sx in (-0.19, 0.19):
        for sy in (-0.19, 0.19):
            parts.append(cyl(name + "Leg", (sx, y + sy, 0.23), 0.012, 0.46, m_frame, verts=10))
        parts.append(cyl(name + "Post", (sx, y - facing * 0.2, 0.62), 0.012, 0.32, m_frame, verts=10))
    return join(parts, name)


def build(variant=None):
    c = {}
    world_flat((0.002, 0.002, 0.003), 1.0)
    # painted concrete walls: dark green-grey with a subtle mottle; dark vinyl floor
    wall = pbr("Wall", (0.07, 0.08, 0.075), 0.85)
    N = wall.node_tree.nodes; L = wall.node_tree.links; tc = N.new("ShaderNodeTexCoord")
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 3.0; nz.inputs['Detail'].default_value = 8
    L.new(tc.outputs['Object'], nz.inputs['Vector'])
    rp = N.new("ShaderNodeValToRGB"); rp.color_ramp.elements[0].color = (0.10, 0.115, 0.108, 1); rp.color_ramp.elements[1].color = (0.16, 0.175, 0.165, 1)
    L.new(nz.outputs['Fac'], rp.inputs['Fac']); L.new(rp.outputs['Color'], N["Principled BSDF"].inputs['Base Color'])
    floor = pbr("Floor", (0.06, 0.06, 0.065), 0.4, 0.0, **{'Coat Weight': 0.2})
    box("Floor", (0, 0, -0.02), (6, 6, 0.04), floor)
    box("WallBack", (0, 2.3, 1.5), (6, 0.1, 3.0), wall)
    box("WallFront", (0, -2.6, 1.5), (6, 0.1, 3.0), wall)
    box("WallR", (2.4, 0, 1.5), (0.1, 6, 3.0), wall)
    box("Ceil", (0, 0, 2.8), (6, 6, 0.1), pbr("Ceil", (0.05, 0.05, 0.05), 0.9))
    # left wall: a two-way mirror in a steel frame (dark glass; a dim observation room behind it)
    box("WallL_lo", (-2.4, 0, 0.45), (0.1, 6, 0.9), wall)
    box("WallL_hi", (-2.4, 0, 2.55), (0.1, 6, 0.5), wall)
    box("WallL_a", (-2.4, -2.05, 1.5), (0.1, 1.9, 3.0), wall)
    box("WallL_b", (-2.4, 2.05, 1.5), (0.1, 1.9, 3.0), wall)
    mirror = glass("TwoWay", (0.35, 0.38, 0.4), 0.02)                 # tinted see-through glass: reflects + faint room behind
    box("Mirror", (-2.36, 0, 1.6), (0.01, 2.2, 1.4), mirror)
    steel = pbr("Steel", (0.35, 0.36, 0.38), 0.35, 0.9)
    for z in (0.88, 2.32):
        box("MirFrame", (-2.34, 0, z), (0.04, 2.3, 0.05), steel)
    for y in (-1.12, 1.12):
        box("MirFrame", (-2.34, y, 1.6), (0.04, 0.05, 1.5), steel)
    box("ObsRoom", (-3.4, 0, 1.4), (0.05, 2.6, 2.0), emissive("ObsGlow", (0.3, 0.38, 0.48), 0.35))   # dim observation room
    for k, y in enumerate((-0.6, 0.5)):                                # two dark silhouettes of chairs/desk behind the glass
        box("ObsDesk", (-3.0, y, 0.75 + 0.1 * k), (0.5, 0.7, 0.05), pbr("ObsDesk", (0.02, 0.02, 0.02), 0.6))
    # door on the back wall with a small wired-glass window and a steel kick plate
    box("Door", (1.55, 2.24, 1.05), (0.95, 0.06, 2.1), pbr("Door", (0.16, 0.17, 0.18), 0.5, 0.3), bevel=0.01)
    box("DoorWin", (1.55, 2.205, 1.55), (0.25, 0.01, 0.35), emissive("DoorWin", (0.7, 0.75, 0.8), 0.6))
    box("Kick", (1.55, 2.205, 0.15), (0.9, 0.01, 0.25), steel)
    cyl("Knob", (1.2, 2.18, 1.0), 0.03, 0.06, steel, verts=16, rot=(math.radians(90), 0, 0))
    # clock (second hand turns) and a ceiling camera with a red light
    cyl("ClockRim", (-0.3, 2.24, 2.1), 0.16, 0.04, pbr("ClockRim", (0.03, 0.03, 0.03), 0.4), verts=40, rot=(math.radians(90), 0, 0))
    cyl("ClockFace", (-0.3, 2.215, 2.1), 0.145, 0.01, emissive("ClockFace", (0.85, 0.85, 0.82), 0.35), verts=40, rot=(math.radians(90), 0, 0))
    hand = box("SecondHand", (-0.3, 2.205, 2.1), (0.006, 0.004, 0.24), pbr("Hand", (0.6, 0.05, 0.03), 0.4))
    hand.rotation_mode = 'XYZ'
    d = hand.driver_add("rotation_euler", 1).driver; d.type = 'SCRIPTED'; d.expression = "frame * 0.2618 / 24 * 6"
    box("HourHand", (-0.3, 2.206, 2.13), (0.012, 0.004, 0.09), pbr("Hand2", (0.02, 0.02, 0.02), 0.4), rot=(0, math.radians(35), 0))
    box("CamBody", (2.2, 2.1, 2.6), (0.16, 0.24, 0.1), pbr("CamBody", (0.8, 0.8, 0.8), 0.4), bevel=0.02, rot=(math.radians(-25), 0, math.radians(35)))
    rl = bpy.data.materials.new("CamLed"); rl.use_nodes = True
    n_ = rl.node_tree.nodes; l_ = rl.node_tree.links; n_.clear(); o_ = n_.new("ShaderNodeOutputMaterial"); em = n_.new("ShaderNodeEmission")
    em.inputs['Color'].default_value = (1.0, 0.05, 0.03, 1); v = n_.new("ShaderNodeValue")
    dd = v.outputs[0].driver_add("default_value").driver; dd.type = 'SCRIPTED'; dd.expression = "12 * (1 if (frame % 48) < 30 else 0.1)"
    l_.new(v.outputs[0], em.inputs['Strength']); l_.new(em.outputs[0], o_.inputs['Surface'])
    box("CamLed", (2.12, 2.0, 2.55), (0.015, 0.015, 0.015), rl)
    # steel table, two chairs (near one empty: Alice)
    top = brushed_metal("TableTop", (0.42, 0.43, 0.45), (0.25, 0.4), 0.6)
    box("TableTop", (0, 0, TH), (1.5, 0.85, 0.035), top, bevel=0.004)
    for sx in (-0.68, 0.68):
        box("TLeg", (sx, 0, TH / 2), (0.05, 0.75, 0.05), steel)
        box("TFoot", (sx, 0, 0.02), (0.06, 0.8, 0.04), steel)
    box("Ring", (0.55, 0.32, TH + 0.025), (0.06, 0.02, 0.02), steel)            # restraint ring bolted to the table
    seat = pbr("Seat", (0.09, 0.095, 0.1), 0.45)
    c["near_chair"] = chair("NearChair", NEAR_Y, +1, seat, steel)
    chair("FarChair", FAR_Y, -1, seat, steel)
    # props in the lamp pool
    c["passport"] = box("Passport", (0.0, -0.22, TH + 0.024), (0.125, 0.088, 0.012), pbr("Passport", (0.2, 0.03, 0.04), 0.45), bevel=0.004)
    box("FolderA", (0.42, 0.12, TH + 0.025), (0.24, 0.32, 0.016), pbr("FolderA", (0.45, 0.35, 0.18), 0.8), bevel=0.003, rot=(0, 0, 0.12))
    box("FolderB", (0.47, 0.1, TH + 0.04), (0.23, 0.31, 0.012), pbr("FolderB", (0.15, 0.2, 0.3), 0.7), bevel=0.003, rot=(0, 0, -0.08))
    for k in range(3):
        box("Sheet", (0.22 + 0.02 * k, -0.08 + 0.015 * k, TH + 0.019 + 0.001 * k), (0.21, 0.297, 0.001), pbr("Sheet", (0.85, 0.84, 0.8), 0.8), rot=(0, 0, 0.25 - 0.1 * k))
    rec = pbr("Rec", (0.02, 0.02, 0.022), 0.4)
    box("Recorder", (-0.38, 0.18, TH + 0.04), (0.17, 0.09, 0.04), rec, bevel=0.008, rot=(0, 0, -0.2))
    box("RecScreen", (-0.4, 0.17, TH + 0.061), (0.06, 0.035, 0.002), emissive("RecScreen", (0.4, 0.8, 1.0), 1.2), rot=(0, 0, -0.2))
    lm = bpy.data.materials.new("RecLed"); lm.use_nodes = True
    n_ = lm.node_tree.nodes; l_ = lm.node_tree.links; n_.clear(); o_ = n_.new("ShaderNodeOutputMaterial"); em = n_.new("ShaderNodeEmission")
    em.inputs['Color'].default_value = (1.0, 0.08, 0.04, 1); v = n_.new("ShaderNodeValue")
    dd = v.outputs[0].driver_add("default_value").driver; dd.type = 'SCRIPTED'; dd.expression = "10 * (1 if (frame % 36) < 24 else 0.15)"
    l_.new(v.outputs[0], em.inputs['Strength']); l_.new(em.outputs[0], o_.inputs['Surface'])
    box("RecLed", (-0.32, 0.165, TH + 0.062), (0.01, 0.01, 0.004), lm)
    cyl("Cup", (-0.55, -0.15, TH + 0.06), 0.035, 0.1, pbr("Cup", (0.85, 0.85, 0.83), 0.6), verts=24)
    cyl("Pen", (0.12, -0.32, TH + 0.022), 0.004, 0.14, pbr("Pen", (0.02, 0.02, 0.025), 0.3, 0.8), verts=10, rot=(math.radians(90), 0, 0.6))
    # the one lamp: a steel shade low over the table (warm spot) + a faint cool fill so the walls read
    bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=0.24, radius2=0.06, depth=0.2, location=(0, 0, 1.9))
    sh = bpy.context.active_object; sh.data.materials.append(pbr("Shade", (0.08, 0.09, 0.09), 0.35, 0.8))
    sm = sh.modifiers.new("s", 'SOLIDIFY'); sm.thickness = 0.004; sh.visible_shadow = False
    cyl("Cord", (0, 0, 2.35), 0.006, 0.9, pbr("Cord", (0.02, 0.02, 0.02), 0.5), verts=8)
    cyl("Bulb", (0, 0, 1.82), 0.04, 0.05, emissive("Bulb", (1.0, 0.85, 0.65), 25), verts=16)
    lift = variant == "lift"                       # c5_04/07/09: about +0.5 stop, a touch of fill on chair and mirror
    lamp = bpy.data.lights.new("Lamp", 'SPOT'); lamp.energy = 370 if lift else 260; lamp.spot_size = math.radians(70); lamp.spot_blend = 0.6
    lamp.color = (1.0, 0.86, 0.68); lamp.shadow_soft_size = 0.05
    lo = bpy.data.objects.new("Lamp", lamp); bpy.context.collection.objects.link(lo); lo.location = (0, 0, 1.8); point_at(lo, (0, 0, 0))
    area_light((1.6, -1.8, 2.6), (0, 0, 0), 2.0, 80 if lift else 55, (0.6, 0.72, 0.9)).visible_camera = False
    if lift:
        cf = area_light((1.1, -1.9, 1.3), (0, 0, 0), 0.8, 22, (0.85, 0.88, 0.95)); point_at(cf, (0, NEAR_Y, 0.7))
        cf.visible_camera = False; cf.visible_glossy = False
        mf = area_light((-1.2, 0.0, 2.6), (0, 0, 0), 1.2, 30, (0.6, 0.7, 0.85)); point_at(mf, (-2.36, 0, 1.6))
        mf.visible_camera = False; mf.visible_glossy = False
    box("ExitLamp", (1.55, 2.2, 2.35), (0.3, 0.04, 0.1), emissive("ExitLamp", (0.4, 1.0, 0.55), 3.0))
    l2 = area_light((1.55, 2.0, 2.3), (math.radians(30), 0, 0), 0.4, 6, (0.4, 1.0, 0.55)); l2.visible_camera = False
    haze((0, 0, 1.4), (4.6, 4.6, 2.8), density=0.02, color=(1.0, 0.95, 0.9), anis=0.5)
    c["table"] = Vector((0, 0, TH + 0.03))
    return c


def _slide(c, a, b, t):
    c["passport"].location = (0.0, a + (b - a) * ease(t), TH + 0.024)


MOVES = {
    "passport_slide": dict(kind="anim", far=12.0, anim=lambda c, t: _slide(c, -0.24, -0.2, t),
                           title=("CHAPTER 5", "THE PASSPORT AND THE PAPER TRAIL", 18, 120, 0.75),
                           cam=lambda c, t: (Vector((1.75, -2.2, 1.55)).lerp(Vector((1.45, -1.85, 1.45)), ease(t)), Vector((-0.25, 0.3, 0.95)), 30)),
    "question": dict(kind="anim", dof=2.0, far=12.0, anim=lambda c, t: _slide(c, -0.26, 0.3, t),
                     cam=lambda c, t: (Vector((0.95, -1.35, 1.25)).lerp(Vector((0.8, -1.15, 1.2)), ease(t)), Vector((0.0, 0.05, TH + 0.03)), 45),
                     focus=lambda c, t: c["passport"].location),
    "warning": dict(kind="anim", dof=2.6, far=12.0, anim=lambda c, t: _slide(c, 0.3, 0.3, t),
                    cam=lambda c, t: (Vector((1.6, -2.15, 1.3)).lerp(Vector((1.3, -1.85, 1.22)), ease(t)), Vector((-0.9, -0.2, 0.95)), 30),
                    focus=lambda c, t: Vector((0.0, NEAR_Y, 0.6))),
    "passport_back": dict(kind="anim", dof=2.0, far=12.0, anim=lambda c, t: _slide(c, 0.3, -0.24, t),
                          cam=lambda c, t: (Vector((-0.9, -1.3, 1.22)).lerp(Vector((-0.75, -1.1, 1.18)), ease(t)), Vector((0.0, -0.05, TH + 0.03)), 45),
                          focus=lambda c, t: c["passport"].location),
}
