"""A dark glass corporate HQ at night (generic architecture, no logo). Variants:
  dim   : the building after hours, a few windows lit
  lit   : same camera, one high floor fully lit (the board convenes) -> revealed in post with a wipe
  watch : seen from a dark room across the street, through a rain-streaked window with blinds (being watched)
"""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *

EXPOSURE = 0.4
VARIANT_FOR = {"night_dim": "dim", "night_lit": "lit", "watch": "watch", "dusk_push": "dusk", "watch_clear": "watch_clear"}
LIT_FLOOR = 9


def ceiling_panels(name, strength, color=(1.0, 0.9, 0.78)):
    """Office ceiling seen from outside: a grid of rectangular light panels."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); geo = N.new("ShaderNodeNewGeometry")
    br = N.new("ShaderNodeTexBrick"); br.inputs['Scale'].default_value = 0.45; br.offset = 0.0
    br.inputs['Brick Width'].default_value = 1.2; br.inputs['Row Height'].default_value = 0.6; br.inputs['Mortar Size'].default_value = 0.35
    br.inputs['Color1'].default_value = (1, 1, 1, 1); br.inputs['Color2'].default_value = (1, 1, 1, 1); br.inputs['Mortar'].default_value = (0, 0, 0, 1)
    L.new(geo.outputs['Position'], br.inputs['Vector'])
    inv = N.new("ShaderNodeMath"); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0
    L.new(br.outputs['Fac'], inv.inputs[1])            # brick Fac = 1 on mortar: the panels are where it is 0
    st = N.new("ShaderNodeMath"); st.operation = 'MULTIPLY'; st.inputs[1].default_value = strength
    L.new(inv.outputs[0], st.inputs[0])
    p.inputs['Base Color'].default_value = (0.12, 0.12, 0.12, 1); p.inputs['Emission Color'].default_value = (*color, 1)
    L.new(st.outputs[0], p.inputs['Emission Strength'])
    return m


def build(variant=None):
    if variant in ("dusk", "watch_clear"):
        # blue-hour establishing: a graded sky behind the tower, brighter than the night variants so the
        # CHAPTER 4 title reads over it. A few floors stay lit, including the board floor.
        from common import world_sky, sun
        world_sky(sun_elev_deg=3.5, sun_rot_deg=295, strength=1.15, tint=(1.0, 0.86, 0.72), aerosol=5.0)
        sun(elev_deg=4.0, azim_deg=295, energy=2.0, color=(1.0, 0.72, 0.5), angle_deg=2.0)
    else:
        world_flat((0.008, 0.012, 0.024), 1.0)
    r = np.random.default_rng(3)
    W_, D_, FLOORS, FH = 64.0, 30.0, 11, 4.0
    x0, y0 = 0.0, 58.0           # building centre; front face at y = y0 - D_/2 = 43
    front = y0 - D_ / 2
    curtain = pbr("Curtain", (0.6, 0.66, 0.7), 0.02, 0.0, **{'Transmission Weight': 1.0, 'IOR': 1.45})
    box("CurtainWall", (x0, front - 0.02, FLOORS * FH / 2), (W_, 0.03, FLOORS * FH), curtain)
    slab = pbr("Slab", (0.06, 0.062, 0.065), 0.6)
    dark_ceil = ceiling_panels("CeilDark", 0.0)
    lit_ceils = [ceiling_panels(f"CeilLit{k}", s_) for k, s_ in enumerate((0.08, 0.15, 0.3))]
    board_ceil = ceiling_panels("CeilBoard", 2.5, (1.0, 0.84, 0.62))
    core = pbr("Core", (0.03, 0.03, 0.032), 0.7)
    box("Core", (x0, y0 + 4, FLOORS * FH / 2), (W_ * 0.5, 6, FLOORS * FH), core)
    for f in range(FLOORS):
        z = f * FH
        box("Slab", (x0, y0, z + 0.15), (W_ - 0.2, D_ - 0.2, 0.3), slab)
        if variant in ("lit", "watch", "watch_clear", None) and f == LIT_FLOOR:
            cm = board_ceil
        else:
            cm = lit_ceils[int(r.integers(0, 3))] if r.random() < 0.12 else dark_ceil
        box("Ceiling", (x0, y0, z + FH - 0.35), (W_ - 0.3, D_ - 0.3, 0.05), cm)
        box("Spandrel", (x0, front - 0.06, z + 0.15), (W_ + 0.2, 0.08, 0.5), pbr("Span", (0.07, 0.075, 0.08), 0.35, 0.6))
    # the boardroom: long table + chairs inside the lit floor
    if variant in ("lit", "watch", "watch_clear", None):
        z = LIT_FLOOR * FH + 0.3
        box("Table", (x0, front + 5, z + 0.75), (18, 2.4, 0.08), wood("Table", (0.02, 0.01, 0.006), (0.07, 0.035, 0.018), rough=0.25))
        for j in range(10):
            for side in (-1, 1):
                box("Chair", (x0 - 8 + j * 1.8, front + 5 + side * 1.6, z + 0.55), (0.55, 0.55, 1.1), pbr("Chair", (0.02, 0.02, 0.02), 0.4), bevel=0.05)
        l = bpy.data.lights.new("BoardL", 'AREA'); l.energy = 4000; l.shape = 'RECTANGLE'; l.size = 20; l.size_y = 4; l.color = (1.0, 0.86, 0.68)
        o = bpy.data.objects.new("BoardL", l); bpy.context.collection.objects.link(o); o.location = (x0, front + 5, z + 3.2)
        o.visible_camera = False
    mull = pbr("Mull", (0.35, 0.37, 0.4), 0.3, 0.8)
    mp = box("MullP", (0, 0, -100), (0.12, 0.25, FLOORS * FH), mull)
    for k in range(int(W_ / 1.6) + 1):
        instance(mp, (x0 - W_ / 2 + k * 1.6, front - 0.1, FLOORS * FH / 2))
    box("Roof", (x0, y0, FLOORS * FH + 0.4), (W_ + 0.4, D_ + 0.4, 0.8), pbr("Roof", (0.06, 0.06, 0.065), 0.5, 0.4))
    box("RoofEdge", (x0, front - 0.25, FLOORS * FH + 0.85), (W_ + 0.4, 0.12, 0.08), emissive("Edge", (0.85, 0.92, 1.0), 10))
    box("Lobby", (x0, front + 2.0, 2.0), (W_ - 2, 0.1, 3.4), emissive("Lobby", (1.0, 0.9, 0.75), 1.6))
    for k in range(11):
        l = bpy.data.lights.new("Up", 'SPOT'); l.energy = 450; l.spot_size = math.radians(14); l.spot_blend = 0.5; l.color = (0.75, 0.85, 1.0)
        o = bpy.data.objects.new("Up", l); bpy.context.collection.objects.link(o); o.location = (x0 - 30 + k * 6, front - 1.6, 0.2); point_at(o, (x0 - 30 + k * 6, front, 30))
    # plaza, street, neighbours
    box("Plaza", (0, 30, -0.05), (300, 30, 0.1), pbr("Wet", (0.012, 0.012, 0.014), 0.06, 0.0, **{'Specular IOR Level': 0.8}))
    win = window_material("Neighbour", lit=(1.0, 0.82, 0.55), density=0.12, floor=3.6, bay=1.6, strength=0.35)
    skyline(51, (0, 170, 0), (260, 70), 35, (40, 150), None, win, footprint=(20, 40))
    for k in range(10):
        box("Lamp", (-60 + k * 13, 22, 6), (0.8, 0.4, 0.2), emissive("Sodium", (1.0, 0.62, 0.3), 40))
    ctx = dict(focus=Vector((x0, front, LIT_FLOOR * FH + 2)))
    if variant in ("watch", "watch_clear"):
        rain = glass("RainGlass", (0.9, 0.93, 0.95), 0.0)
        nt = rain.node_tree; N = nt.nodes; L = nt.links; tc = N.new("ShaderNodeTexCoord")
        vor = N.new("ShaderNodeTexVoronoi"); vor.inputs['Scale'].default_value = 55; vor.feature = 'F1'
        L.new(tc.outputs['Object'], vor.inputs['Vector'])
        # discrete drops: a smooth cap where the cell distance is small, flat clean glass elsewhere
        cap = N.new("ShaderNodeMapRange"); cap.inputs['From Min'].default_value = 0.0; cap.inputs['From Max'].default_value = 0.32
        cap.inputs['To Min'].default_value = 1.0; cap.inputs['To Max'].default_value = 0.0
        L.new(vor.outputs['Distance'], cap.inputs['Value'])
        sel = N.new("ShaderNodeMath"); sel.operation = 'GREATER_THAN'; sel.inputs[1].default_value = 0.45 if variant == "watch" else 0.86
        sep = N.new("ShaderNodeSeparateColor"); L.new(vor.outputs['Color'], sep.inputs[0]); L.new(sep.outputs[0], sel.inputs[0])
        dome = N.new("ShaderNodeMath"); dome.operation = 'SQRT'; L.new(cap.outputs[0], dome.inputs[0])
        hm = N.new("ShaderNodeMath"); hm.operation = 'MULTIPLY'; L.new(dome.outputs[0], hm.inputs[0]); L.new(sel.outputs[0], hm.inputs[1])
        bp = N.new("ShaderNodeBump"); bp.inputs['Strength'].default_value = 0.9; bp.inputs['Distance'].default_value = 0.0015
        L.new(hm.outputs[0], bp.inputs['Height']); L.new(bp.outputs['Normal'], N["Principled BSDF"].inputs['Normal'])
        WY = -30.0
        box("RainPane", (-20, WY, 8.0), (3.0, 0.01, 2.4), rain)
        frame = pbr("Frame", (0.01, 0.01, 0.012), 0.5)
        for x in (-21.5, -18.5):
            box("Jamb", (x, WY, 8.0), (0.08, 0.1, 2.5), frame)
        box("Sill", (-20, WY - 0.2, 6.75), (3.2, 0.5, 0.06), frame)
        for k in range(10):
            box("Slat", (-20, WY - 0.08, 9.15 - k * 0.07), (3.0, 0.03, 0.012), pbr("Slat", (0.1, 0.1, 0.1), 0.6), rot=(math.radians(35), 0, 0))
        box("RoomWallL", (-23.0, WY - 2, 8), (3, 0.1, 5), pbr("RoomW", (0.02, 0.02, 0.02), 0.8))
    return ctx


MOVES = {
    "night_dim": dict(kind="plate", far=300.0, cam=lambda c, t: ((-48, -40, 1.7), (0, 43, 22), 30)),
    "night_lit": dict(kind="plate", far=300.0, cam=lambda c, t: ((-48, -40, 1.7), (0, 43, 22), 30)),
    "watch": dict(kind="plate", dof=1.8, far=300.0, cam=lambda c, t: ((-19.9, -30.55, 8.0), (0, 43, 36), 50),
                  focus=lambda c, t: (-19.85, -30.0, 8.2)),
    # CH4 1A: slow dusk push toward the tower, CHAPTER 4 title over it (two-line card + scrim, via bake.py)
    # CH4 7D: the same window, far fewer drops, focus on the tower: the lit board floor reads clearly through the glass
    "watch_clear": dict(kind="anim", dof=8.0, far=300.0,
                        cam=lambda c, t: (Vector((-19.9, -30.6, 8.0)).lerp(Vector((-19.8, -30.45, 8.05)), ease(t)), (0, 43, 34), 42),
                        focus=lambda c, t: (0, 43, 34)),
    "dusk_push": dict(kind="anim", far=400.0, title=("CHAPTER 4", "THE SECOND EMPLOYEE", 18, 120, 0.55),
                      cam=lambda c, t: (Vector((-34, -60, 4.0)).lerp(Vector((-30, -52, 5.2)), ease(t)), (0, 43, 23), 30)),
}
