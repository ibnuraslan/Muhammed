"""Thumbnail 3 - THE HANDOFF. A late-night café table by a rain-streaked window. A bare AI accelerator board glows
green in sharp focus on the table; above it, soft, the woman slides it toward the man, who looks at her, wary.
Left third: the dark wet window and street bokeh for the title."""
import math
import bpy
from mathutils import Vector
from kit import pbr, emissive, box, cyl, haze, world_flat, rain_glass
import ph
from sc_gpu_module import build_module
from people import man, woman
from human import reach, fingers_curl, rotate_bone, aim_bone
from thumbkit import *

EXPOSURE = 0.3
VIGNETTE = 0.7
TABLE = Vector((0.0, 0.0, 0.0))


def room():
    world_flat((0.003, 0.004, 0.006), 1.0)
    box("Floor", (0, 0, -0.01), (12, 12, 0.02), ph.texture("herringbone_parquet", scale=0.6, tint=(0.4, 0.33, 0.28)))
    brick = ph.texture("brick_wall_02", scale=0.45, tint=(0.55, 0.45, 0.42))
    # window wall behind them (y = 1.6) with a big rain-covered pane; the street glows beyond
    box("WallL", (-3.2, 1.6, 1.6), (2.4, 0.2, 3.2), brick); box("WallR", (3.2, 1.6, 1.6), (2.4, 0.2, 3.2), brick)
    box("WallTop", (0, 1.6, 2.85), (4.0, 0.2, 0.7), brick); box("WallLow", (0, 1.6, 0.25), (4.0, 0.2, 0.5), brick)
    box("Pane", (0, 1.6, 1.5), (4.0, 0.012, 2.0), rain_glass("RainPane", 70, 0.55))
    frame = pbr("Frame", (0.015, 0.015, 0.016), 0.4, 0.6)
    for x in (-2.0, -0.65, 0.65, 2.0):
        box("Mullion", (x, 1.6, 1.5), (0.06, 0.1, 2.0), frame)
    # the street outside: red and teal glows, far and soft
    for x, z, col, st, sz in ((-1.6, 2.0, (1.0, 0.05, 0.04), 25, (1.6, 0.05, 0.5)), (-0.6, 1.2, (1.0, 0.25, 0.1), 8, (0.5, 0.05, 0.9)),
                              (1.4, 1.9, (0.2, 0.7, 1.0), 6, (1.0, 0.05, 0.4)), (-2.6, 1.0, (1.0, 0.6, 0.3), 6, (0.4, 0.05, 0.4))):
        glow_card((x * 2.5, 9.0, z * 1.6), (sz[0] * 1.2, 0.05, sz[2] * 1.2), col, st * 0.35, name="Street")
    box("Road", (0, 6, -0.05), (30, 8, 0.1), pbr("WetRoad", (0.01, 0.01, 0.012), 0.04, 0.0, **{'Specular IOR Level': 0.9}))
    point((-3, 8, 3), 600, (1.0, 0.1, 0.06), 1.0, "StreetRed")


def build(variant=None):
    room()
    tab, tm, tlo, thi = asset("round_wooden_table_02", (0, 0, 0), 0, floor=0.0)
    top = surface_z(0.0, 0.0, 2.0)
    r = max(thi.x - tlo.x, thi.y - tlo.y) / 2
    M_SEAT, W_SEAT = Vector((0.5, 0.42)), Vector((-0.52, 0.3))
    m_face, w_face = -40, 58
    ch1, *_ = asset("gallinera_chair", (M_SEAT.x + 0.08, M_SEAT.y + 0.1, 0), 180 + m_face, floor=0.0)
    ch2, *_ = asset("gallinera_chair", (W_SEAT.x - 0.1, W_SEAT.y + 0.06, 0), 180 + w_face, floor=0.0)
    zs = surface_z(M_SEAT.x + 0.06, M_SEAT.y + 0.08, 0.6) or 0.45
    zw = surface_z(W_SEAT.x - 0.08, W_SEAT.y + 0.04, 0.6) or 0.45
    lamp, *_ = asset("hanging_industrial_lamp", (0, 0.1, 0), 0)
    bpy.context.view_layer.update(); llo, lhi = ph.bounds(_[0])
    lamp.location.z += 2.05 - llo.z
    m = man("Man"); sit_on(m, M_SEAT, zs, m_face, lean=10)
    w = woman("Woman"); sit_on(w, W_SEAT, zw, w_face, lean=14)
    # ---- the board, centre of the table, sharp
    build_module((0, 0, 0), passives=False)
    holder = bpy.data.objects.new("BoardRoot", None); bpy.context.collection.objects.link(holder)
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.parent is None and o.name.startswith(("Board", "Substrate", "Interposer", "Die", "HBM", "Underfill", "Frame", "Pad", "Inductor", "Cap2")):
            o.parent = holder
    bp = Vector((0.02, -0.12, top + 0.001))
    holder.location = bp; holder.rotation_euler = (0, 0, math.radians(18)); holder.scale = (1.7, 1.7, 1.7)
    bpy.context.view_layer.update()
    # her hand on the board's left edge, pushing it toward him; his hands rest on the table edge
    edge_w = bp + Vector((-0.13, -0.02, 0.03))
    reach(w, "L", edge_w, Vector((-0.5, -0.3, -1)), Vector((0.9, 0.1, -0.35)))
    reach(w, "R", w.bone_head("upperarm01.R") + Vector((0.32, -0.08, -0.38)), Vector((0.2, -0.6, -1)), Vector((0.8, -0.4, -0.3)))
    fingers_curl(w, 18, thumb=6)
    for s_, off in (("L", Vector((-0.12, -0.24, -0.38))), ("R", Vector((-0.2, -0.12, -0.38)))):
        reach(m, s_, m.bone_head(f"upperarm01.{s_}") + off, Vector((0.6, 0.2, -1)), Vector((-0.6, -0.6, -0.3)))
    fingers_curl(m, 40, thumb=10)
    # looks: she watches him; he looks at her, chin down, wary
    look_at(w, m.bone_head("head") + Vector((0, 0, 0.05)), 0.8); gaze(w, m.bone_head("head") + Vector((0, 0, 0.08)))
    look_at(m, w.bone_head("head") + Vector((0, 0, -0.05)), 0.7); gaze(m, w.bone_head("head") + Vector((0, 0, 0.1)))
    # ---- light: the board glows green up into their faces; warm lamp pool; red street rim on them
    glow = box("BoardGlow", tuple(bp + Vector((0, 0, 0.0015))), (0.26, 0.2, 0.002), emissive("GreenUnder", (0.2, 1.0, 0.35), 8), rot=(0, 0, math.radians(18)))
    glow.visible_camera = False
    point(bp + Vector((0, 0, 0.05)), 3, (0.25, 1.0, 0.4), 0.06, "ChipGlow")
    soft(bp + Vector((0, -0.05, 0.02)), Vector((0, 0.3, 1.25)), 10, (0.2, 1.0, 0.35), size=0.25, name="GreenUp")
    spot((0, 0.1, 1.95), (0, 0, top), 260, (1.0, 0.7, 0.45), 70, 0.6, 0.08, "LampPool")
    spot((0.0, 3.5, 2.4), (0, 0.3, 1.2), 380, (1.0, 0.08, 0.05), 40, 0.6, 0.5, "RedRim")
    soft((1.8, -1.6, 1.6), (0.3, 0.3, 1.2), 25, (0.5, 0.65, 1.0), size=1.0, name="CoolFill")
    haze((0, 0.2, 1.5), (6, 3, 3), density=0.02, color=(0.95, 0.95, 1.0), anis=0.4)
    cam = Vector((0.42, -1.05, 0.98))
    c = dict(m=m, w=w)
    c["cam"] = (cam, Vector((-0.1, 0.25, 0.98)), 26)
    c["shift"] = (-0.17, 0.0)
    c["focus"] = bp + Vector((0, 0, 0.01))
    c["fstop"] = 2.2
    return c
