"""Night: looking up a tall glass office tower among others (illustration; a generic tower, not a replica)."""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *

EXPOSURE = 0.2


def build(variant=None):
    world_flat((0.01, 0.016, 0.032), 1.0)
    hero = window_material("HeroWin", lit=(0.95, 0.9, 0.8), density=0.6, floor=4.2, bay=1.6, strength=1.1, glass_col=(0.015, 0.025, 0.035))
    others = window_material("Others", lit=(1.0, 0.82, 0.6), density=0.2, floor=3.8, bay=1.8, strength=1.3)
    body = pbr("Body", (0.01, 0.012, 0.015), 0.3, 0.5)
    tower = box("Hero", (0, 60, 125), (48, 40, 250), hero)
    box("Crown", (0, 60, 252), (40, 32, 6), emissive("Crown", (0.8, 0.9, 1.0), 6))
    box("Podium", (0, 40, 12), (90, 70, 24), window_material("Podium", lit=(1.0, 0.9, 0.7), density=0.5, floor=4.5, bay=1.6, strength=0.7))
    skyline(21, (0, 160, 0), (260, 120), 40, (60, 230), body, others, footprint=(25, 45), avoid=(0, 60, 60))
    box("Street", (0, 0, -0.5), (900, 900, 1), pbr("Asphalt", (0.02, 0.02, 0.022), 0.35))
    for k in range(14):
        box("Lamp", (-60 + k * 9, -10, 6), (0.6, 0.6, 0.3), emissive("Lamp", (1.0, 0.7, 0.4), 40))
    haze((0, 60, 60), (600, 400, 120), density=0.002, color=(0.6, 0.7, 0.9), anis=0.3)
    # the 7th floor (~25-29 m): a faintly brighter band we can hint at in the edit
    return dict(floor7=Vector((0, 40, 27)))


MOVES = {"tower_tilt": dict(kind="plate", far=800.0, cam=lambda c, t: ((24, -40, 3), (0, 60, 115 - 40 * t), 22))}
