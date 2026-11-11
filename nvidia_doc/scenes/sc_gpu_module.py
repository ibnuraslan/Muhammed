"""A generic data-center accelerator module (no brand features), and a server tray holding several of them."""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
from sc_chip_macro import build_package

VARIANT_FOR = {"server_tray": "tray"}


def build_module(origin=(0, 0, 0), passives=True):
    ox, oy, oz = origin
    board = box("Board", (ox, oy, oz + 0.0009), (0.142, 0.106, 0.0018), pcb("Board", (0.008, 0.012, 0.010)), bevel=0.0005)
    pk = build_package((ox, oy, oz + 0.0018), with_passives=passives)
    steel = brushed_metal("Stiffener", (0.55, 0.57, 0.6), (0.2, 0.32), 0.5)
    for (x, y, w_, d_) in ((0, 0.0305, 0.064, 0.004), (0, -0.0305, 0.064, 0.004), (0.0305, 0, 0.004, 0.064), (-0.0305, 0, 0.004, 0.064)):
        box("Frame", (ox + x, oy + y, oz + 0.0028), (w_, d_, 0.002), steel, bevel=0.0003)
    ind = pbr("Inductor", (0.03, 0.03, 0.032), 0.55, 0.2)
    proto = box("Inductor", (0, 0, -1), (0.0062, 0.0062, 0.0042), ind, bevel=0.0005)
    cer = pbr("Cap2", (0.28, 0.22, 0.14), 0.45)
    cproto = box("Cap2", (0, 0, -1), (0.0016, 0.0008, 0.0008), cer, bevel=0.00005)
    for side in (-1, 1):
        for i in range(8):
            for j in range(2):
                instance(proto, (ox + side * (0.044 + j * 0.0075), oy - 0.035 + i * 0.010, oz + 0.0039))
                for q in range(3):
                    instance(cproto, (ox + side * (0.0405 + j * 0.0075 + 0.0) + side * 0.0035, oy - 0.035 + i * 0.010 + (q - 1) * 0.0022, oz + 0.0022))
    # gold edge fingers / mezzanine pads along one edge
    gold = pbr("Gold", (0.95, 0.68, 0.32), 0.25, 1.0)
    for k in range(40):
        box("Pad", (ox - 0.066 + k * 0.0034, oy - 0.0505, oz + 0.00185), (0.002, 0.004, 0.0001), gold)
    return dict(board=board, pkg=pk)


def heatsink(loc, mat, w_=0.13, d_=0.10, h_=0.06, fins=26):
    base = box("HSBase", (loc[0], loc[1], loc[2] + 0.004), (w_, d_, 0.008), mat, bevel=0.0008)
    fin = box("Fin", (0, 0, -1), (w_ * 0.98, 0.0005, h_), mat)
    for k in range(fins):
        instance(fin, (loc[0], loc[1] - d_ / 2 + 0.002 + k * (d_ - 0.004) / (fins - 1), loc[2] + 0.008 + h_ / 2))
    return base


def build(variant=None):
    world_flat((0.006, 0.007, 0.009), 1.0)
    ctx = {}
    if variant == "tray":
        sheet = brushed_metal("Chassis", (0.42, 0.44, 0.47), (0.25, 0.4), 0.4)
        box("Tray", (0.0, 0.12, -0.002), (0.48, 0.62, 0.004), sheet)
        for sx in (-1, 1):
            box("Wall", (sx * 0.24, 0.12, 0.04), (0.004, 0.62, 0.08), sheet)
        alu = brushed_metal("Alu", (0.8, 0.81, 0.83), (0.15, 0.3), 0.6, axis=(200, 1, 1))
        spots = [(-0.11, 0.0), (0.11, 0.0), (-0.11, 0.2), (0.11, 0.2)]
        for k, (x, y) in enumerate(spots):
            build_module((x, y, 0.0), passives=False)
            if k >= 1:     # first module left open to show the chip; the others wear heatsinks
                heatsink((x, y, 0.0045), alu)
        fan_m = pbr("Fan", (0.02, 0.02, 0.022), 0.5)
        for k in range(6):
            cyl("Fan", (-0.2 + k * 0.08, 0.38, 0.04), 0.035, 0.03, fan_m, rot=(math.radians(90), 0, 0))
            box("FanFrame", (-0.2 + k * 0.08, 0.38, 0.04), (0.078, 0.032, 0.078), pbr("FanFrame", (0.03, 0.03, 0.033), 0.6), bevel=0.003)
        ctx["c"] = Vector((-0.11, 0.0, 0.004))
    else:
        build_module()
        ctx["c"] = Vector((0, 0, 0.004))
    box("Ground", (0, 0, -0.006), (2, 2, 0.002), pbr("Velvet", (0.004, 0.004, 0.005), 0.95))
    key = area_light((-0.25, -0.2, 0.3), (0, 0, 0), 0.15, 6, (0.92, 0.96, 1.0)); point_at(key, tuple(ctx["c"]))
    key.data.shape = 'RECTANGLE'; key.data.size = 0.5; key.data.size_y = 0.06
    rim = area_light((0.3, 0.35, 0.12), (0, 0, 0), 0.15, 3.5, (0.3, 0.85, 1.0)); point_at(rim, tuple(ctx["c"]))
    fill = area_light((0.25, -0.35, 0.15), (0, 0, 0), 0.3, 0.5, (1.0, 0.85, 0.7)); point_at(fill, tuple(ctx["c"]))
    ctx["key"] = key
    return ctx


def _orbit(c, t):
    a = math.radians(-60 + 35 * ease(t))
    return ((0.26 * math.cos(a), 0.26 * math.sin(a), 0.13 - 0.02 * t), c["c"], 60)


MOVES = {
    "hero_orbit": dict(kind="anim", dof=8.0, far=1.0, cam=_orbit, focus=lambda c, t: c["c"]),
    "server_tray": dict(kind="plate", dof=6.0, far=2.0,
                        cam=lambda c, t: ((0.25, -0.32, 0.30), c["c"] + Vector((0.06, 0.12, 0)), 40), focus=lambda c, t: c["c"]),
}
