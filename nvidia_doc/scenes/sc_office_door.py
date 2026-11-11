"""Reconstruction: a locked frameless glass door on an office floor; beyond it a dim reception with two gray
armchairs and the company's name on the wall in plain letters (no logo)."""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *

EXPOSURE = 0.9
DOOR_Y = 0.0          # glass line; corridor is y < 0, reception y > 0


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


MOVES = {
    "phone_ring": dict(kind="anim", dof=2.0, far=20.0,
                       cam=lambda c, t: (Vector((1.1, DOOR_Y - 0.5, 1.32)).lerp(Vector((1.15, DOOR_Y - 0.3, 1.3)), ease(t)), c["phone"], 70),
                       focus=lambda c, t: c["phone"]),
    "door_push": dict(kind="anim", dof=2.8, far=20.0,
                      cam=lambda c, t: (Vector((0.55, -3.4, 1.45)).lerp(Vector((0.3, -1.25, 1.3)), ease(t)), (0.05, 0.0, 1.05), 32),
                      focus=lambda c, t: (0.07, 0.0, 1.05)),
    "through_glass": dict(kind="plate", dof=2.8, far=20.0,
                          cam=lambda c, t: ((-0.9, -1.2, 1.25), (-1.4, 2.4, 0.5), 38), focus=lambda c, t: (-1.4, 2.4, 0.5)),
    "nameplate": dict(kind="plate", dof=2.4, far=20.0,
                      cam=lambda c, t: ((0.35, -0.9, 1.6), c["name"] + Vector((0, 0, -0.25)), 50), focus=lambda c, t: c["name"]),
}
