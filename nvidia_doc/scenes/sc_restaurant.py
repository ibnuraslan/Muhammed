"""A private dining room (reconstruction backdrop for the Taipei footage): round table, glass lazy susan, dishes,
empty chairs, warm pendant. Seen from an elevated TV-camera angle. No people."""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *

EXPOSURE = 0.3


def build(variant=None):
    world_flat((0.01, 0.008, 0.006), 1.0)
    r = np.random.default_rng(22)
    box("Floor", (0, 0, -0.01), (12, 12, 0.02), wood("Floorboards", (0.04, 0.022, 0.012), (0.11, 0.06, 0.03), scale=(0.5, 6, 6), rough=0.4, coat=0.3))
    panel = wood("Panel", (0.05, 0.025, 0.012), (0.14, 0.07, 0.03), scale=(6, 6, 0.4), rough=0.4, coat=0.4)
    for (x, y, sx, sy) in ((0, 3.2, 7, 0.1), (0, -3.2, 7, 0.1), (3.2, 0, 0.1, 7), (-3.2, 0, 0.1, 7)):
        box("Wall", (x, y, 1.6), (sx, sy, 3.2), panel)
    cloth = fabric("Tablecloth", (0.82, 0.8, 0.76), 0.85, 0.3, 300)
    t = cyl("Table", (0, 0, 0.74), 0.95, 0.04, cloth, verts=96)
    cyl("Skirt", (0, 0, 0.55), 0.97, 0.38, cloth, verts=96)
    cyl("LazySusan", (0, 0, 0.775), 0.5, 0.012, glass("Susan", (0.9, 0.95, 0.94), 0.02), verts=96)
    porcelain = pbr("Porcelain", (0.9, 0.9, 0.88), 0.12, 0.0, **{'Coat Weight': 0.6})
    for k in range(5):   # shared dishes on the turntable
        a = k / 5 * 2 * math.pi + 0.3
        cyl("Dish", (0.28 * math.cos(a), 0.28 * math.sin(a), 0.79), 0.12, 0.02, porcelain, verts=48)
        cyl("Food", (0.28 * math.cos(a), 0.28 * math.sin(a), 0.805), 0.09, 0.02, pbr("Food", tuple(r.uniform(0.1, 0.5, 3) * (1, 0.6, 0.3)), 0.4), verts=32)
    seat = fabric("SeatRed", (0.25, 0.04, 0.03), 0.8, 0.4, 500)
    chair_wood = wood("ChairWood", (0.03, 0.015, 0.008), (0.09, 0.045, 0.02), rough=0.35)
    for k in range(9):
        a = k / 9 * 2 * math.pi
        x, y = 1.3 * math.cos(a), 1.3 * math.sin(a)
        cyl("Plate", (0.82 * math.cos(a), 0.82 * math.sin(a), 0.765), 0.11, 0.01, porcelain, verts=48)
        cyl("Cup", (0.72 * math.cos(a + 0.2), 0.72 * math.sin(a + 0.2), 0.79), 0.03, 0.05, porcelain, verts=24)
        for d in (-1, 1):
            box("Chopstick", (0.82 * math.cos(a + 0.18) + d * 0.01, 0.82 * math.sin(a + 0.18), 0.77), (0.006, 0.006, 0.23), chair_wood, rot=(math.radians(90), 0, a))
        ch = join([box("CSeat", (0, 0, 0.46), (0.48, 0.48, 0.07), seat, bevel=0.02),
                   box("CBack", (0, 0.22, 0.85), (0.46, 0.05, 0.7), chair_wood, bevel=0.01),
                   box("CLegs", (0, 0, 0.22), (0.42, 0.42, 0.44), chair_wood)], "Chair")
        ch.location = (x, y, 0); ch.rotation_euler = (0, 0, a + math.pi / 2)
    shade = pbr("Shade", (0.9, 0.7, 0.4), 0.6, 0.0, **{'Emission Color': (1.0, 0.7, 0.4, 1), 'Emission Strength': 2.0})
    cyl("Pendant", (0, 0, 2.3), 0.45, 0.25, shade, verts=48)
    l = bpy.data.lights.new("Pend", 'SPOT'); l.energy = 900; l.spot_size = math.radians(110); l.spot_blend = 0.7; l.color = (1.0, 0.75, 0.48)
    o = bpy.data.objects.new("Pend", l); bpy.context.collection.objects.link(o); o.location = (0, 0, 2.2)
    fill = area_light((-2.5, -2.5, 2.4), (0, 0, 0), 1.5, 30, (1.0, 0.85, 0.7)); point_at(fill, (0, 0, 0.8))
    box("Ceiling", (0, 0, 3.2), (7, 7, 0.05), pbr("Ceil", (0.12, 0.1, 0.08), 0.8))
    return dict(table=Vector((0, 0, 0.8)))


MOVES = {"tv_zoom": dict(kind="plate", dof=6.0, far=20.0, cam=lambda c, t: ((2.4, -2.5, 2.3), c["table"], 30), focus=lambda c, t: c["table"])}
