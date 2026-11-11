"""Night aerial over a dense business district (generic towers). Two plates from the same camera:
  dark : late-night city, sparse windows        lit : many more office windows on
The edit reveals `lit` over `dark` with a spreading, per-window wipe (the email landing)."""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *

EXPOSURE = 0.3
VARIANT_FOR = {"aerial_dark": "dark", "aerial_lit": "lit"}


def build(variant=None):
    world_flat((0.006, 0.01, 0.022), 1.0)
    dens = 0.10 if variant == "dark" else 0.42
    warm = window_material("Warm", lit=(1.0, 0.82, 0.58), density=dens, floor=3.6, bay=1.5, strength=0.9)
    cool = window_material("Cool", lit=(0.8, 0.9, 1.0), density=dens * 0.9, floor=3.8, bay=1.6, strength=1.0)
    rng = np.random.default_rng(12)
    for k in range(260):
        x = rng.uniform(-500, 500); y = rng.uniform(-200, 900)
        w = rng.uniform(25, 55); d = rng.uniform(25, 55)
        h = rng.uniform(25, 120) * (2.2 if rng.random() < 0.12 else 1.0) * (1.0 + 0.6 * math.exp(-((x / 260) ** 2 + ((y - 350) / 300) ** 2)))
        box("Tower", (x, y, h / 2), (w, d, h), warm if rng.random() < 0.6 else cool)
        if rng.random() < 0.35:
            for cx_, cy_ in ((-1, -1), (1, 1)):
                box("RoofLight", (x + cx_ * w * 0.45, y + cy_ * d * 0.45, h + 0.5), (0.8, 0.8, 0.8), emissive("Aviation", (1.0, 0.15, 0.1), 30))
    # avenues: glowing grid of streets
    streets = emissive("Street", (1.0, 0.62, 0.3), 1.2)
    for k in range(-10, 11):
        box("AveX", (k * 60, 350, 0.05), (4, 1400, 0.1), streets)
    for k in range(-4, 20):
        box("AveY", (0, k * 60, 0.05), (1400, 4, 0.1), streets)
    box("Ground", (0, 350, -0.5), (1600, 1600, 1), pbr("Ground", (0.01, 0.012, 0.015), 0.7))
    haze((0, 350, 120), (1600, 1600, 240), density=0.0006, color=(0.6, 0.68, 0.85), anis=0.3)
    return {}


CAM = lambda c, t: ((-80, -420, 230 - 10 * t), (40, 380, 40), 35)
MOVES = {"aerial_dark": dict(kind="plate", far=2000.0, cam=CAM), "aerial_lit": dict(kind="plate", far=2000.0, cam=CAM)}
