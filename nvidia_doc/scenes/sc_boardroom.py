"""Empty boardroom at night: long walnut table, leather chairs, glass wall to a city skyline, one folder."""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *

EXPOSURE = 0.2


def chair(loc, rot, mat_seat, mat_metal):
    parts = [box("Seat", (0, 0, 0.47), (0.52, 0.5, 0.09), mat_seat, bevel=0.03),
             box("Back", (0, 0.24, 0.82), (0.5, 0.08, 0.62), mat_seat, bevel=0.035),
             box("ArmL", (-0.27, 0.0, 0.66), (0.05, 0.42, 0.04), mat_metal, bevel=0.01),
             box("ArmR", (0.27, 0.0, 0.66), (0.05, 0.42, 0.04), mat_metal, bevel=0.01),
             cyl("Stem", (0, 0, 0.24), 0.03, 0.42, mat_metal)]
    for k in range(5):
        a = k / 5 * 2 * math.pi
        parts.append(box("Leg", (0.17 * math.cos(a), 0.17 * math.sin(a), 0.04), (0.34, 0.04, 0.03), mat_metal, rot=(0, 0, a)))
    c = join(parts, "Chair")
    c.location = loc; c.rotation_euler = (0, 0, rot)
    return c


def build(variant=None):
    world_flat((0.006, 0.010, 0.022), 1.0)
    walnut = wood("Walnut", (0.018, 0.009, 0.005), (0.06, 0.03, 0.015), scale=(9, 0.35, 0.35), rough=0.25, coat=0.9)
    leather = pbr("Leather", (0.012, 0.011, 0.011), 0.42, 0.0, **{'Coat Weight': 0.3, 'Coat Roughness': 0.3})
    alu = brushed_metal("Alu", (0.7, 0.71, 0.73), (0.15, 0.3), 0.5)
    box("Floor", (0, 0, -0.01), (14, 14, 0.02), fabric("Carpet", (0.025, 0.026, 0.03), 0.95, 0.2, 400))
    table = box("Table", (0, 0, 0.74), (1.4, 6.0, 0.06), walnut, bevel=0.01)
    for y in (-2.0, 2.0):
        box("Pedestal", (0, y, 0.37), (0.5, 0.9, 0.72), pbr("Ped", (0.01, 0.01, 0.012), 0.4, 0.6), bevel=0.01)
    chairs = []
    for side in (-1, 1):
        for k in range(6):
            chairs.append(chair((side * 1.05, -2.5 + k * 1.0, 0), math.pi / 2 * side, leather, alu))
    head = chair((0, 3.55, 0), math.pi, leather, alu)
    # the folder on the table
    manila = pbr("Manila", (0.55, 0.42, 0.24), 0.75)
    fold = box("Folder", (0.15, 1.2, 0.774), (0.24, 0.32, 0.006), manila, rot=(0, 0, 0.12))
    paper = pbr("Paper", (0.85, 0.83, 0.78), 0.8)
    box("Paper", (0.16, 1.19, 0.778), (0.21, 0.29, 0.002), paper, rot=(0, 0, 0.16))
    # glass wall + night city beyond
    gl = glass("WallGlass", (0.9, 0.95, 0.97), 0.02)
    box("GlassWall", (0, 5.2, 1.5), (8, 0.02, 3.0), gl)
    for k in range(9):
        box("Mullion", (-4 + k * 1.0, 5.19, 1.5), (0.04, 0.05, 3.0), pbr("Mull", (0.02, 0.02, 0.022), 0.4, 0.8))
    body = pbr("TowerBody", (0.01, 0.012, 0.016), 0.3, 0.5)
    win = window_material("Windows", density=0.17, floor=3.6, bay=1.6, strength=1.3)
    # we are ~150 m up: the city spreads out below, horizon and night sky above
    skyline(5, (0, 900, 0), (900, 650), 260, (30, 190), body, win, footprint=(25, 60), z0=-150)
    streets = window_material("Streets", lit=(1.0, 0.7, 0.4), density=0.08, floor=40, bay=40, strength=1.5)
    box("CityGround", (0, 1000, -151), (4000, 2400, 1), streets)
    box("Ceiling", (0, 0, 3.0), (14, 14, 0.02), pbr("Ceil", (0.03, 0.03, 0.033), 0.8))
    pend = emissive("Pendant", (1.0, 0.85, 0.65), 6.0)
    box("Linear", (0, 0, 2.3), (0.12, 4.2, 0.03), pend)
    wa = bpy.data.lights.new("Over", 'AREA'); wa.energy = 140; wa.color = (1.0, 0.86, 0.68); wa.shape = 'RECTANGLE'; wa.size = 0.3; wa.size_y = 4.4
    o = bpy.data.objects.new("Over", wa); bpy.context.collection.objects.link(o); o.location = (0, 0, 2.28)
    cool = area_light((-3.5, 4.5, 2.0), (0, 0, 0), 2.0, 60, (0.45, 0.6, 1.0)); point_at(cool, (0, 0, 0.8))
    return dict(folder=Vector((0.15, 1.2, 0.78)), head=Vector((0, 3.55, 0.9)))


MOVES = {
    "slow_push": dict(kind="plate", dof=2.8, far=40.0, cam=lambda c, t: ((0.6, -3.8, 1.35), (0, 3.0, 0.95), 32), focus=lambda c, t: (0, 1.0, 0.8)),
    "empty_chair": dict(kind="plate", dof=2.8, far=40.0, cam=lambda c, t: ((0.35, 0.6, 1.05), c["head"], 50), focus=lambda c, t: c["head"]),
    "dossier": dict(kind="plate", dof=2.4, far=40.0, cam=lambda c, t: ((0.6, 0.55, 1.2), c["folder"], 45), focus=lambda c, t: c["folder"]),
}
