"""Night skyline across a river (illustration for 'Shanghai's investment world'): generic towers, not landmarks."""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *

EXPOSURE = 0.3


def build(variant=None):
    world_flat((0.012, 0.018, 0.035), 1.0)
    win = window_material("Win", lit=(1.0, 0.85, 0.62), density=0.35, floor=3.8, bay=1.8, strength=1.2)
    win_cool = window_material("WinCool", lit=(0.7, 0.85, 1.0), density=0.3, floor=4.2, bay=2.0, strength=1.4)
    body = pbr("Body", (0.01, 0.012, 0.015), 0.3, 0.5)
    skyline(11, (0, 900, 0), (700, 260), 120, (60, 280), body, win, footprint=(30, 70))
    skyline(12, (150, 1150, 0), (500, 200), 60, (150, 420), body, win_cool, footprint=(35, 60))
    # two tall hero towers with rooftop beacons
    for (x, y, h, w) in ((-120, 820, 520, 60), (90, 870, 460, 52)):
        box("Hero", (x, y, h / 2), (w, w, h), win_cool)
        box("Beacon", (x, y, h + 4), (w * 0.3, w * 0.3, 8), emissive("Beacon", (1.0, 0.3, 0.25), 30))
    box("Bank", (0, 700, -2), (3000, 400, 4), pbr("Bank", (0.01, 0.01, 0.012), 0.7))
    # river: dark, slightly rough mirror that streaks the lights
    water = box("River", (0, 300, -0.5), (4000, 800, 1), pbr("Water", (0.004, 0.006, 0.008), 0.06, 0.0, **{'Specular IOR Level': 0.8}))
    nt = water.data.materials[0].node_tree; N = nt.nodes; L = nt.links; tc = N.new("ShaderNodeTexCoord")
    mp = N.new("ShaderNodeMapping"); mp.inputs['Scale'].default_value = (0.02, 0.4, 1); L.new(tc.outputs['Object'], mp.inputs['Vector'])
    n = N.new("ShaderNodeTexNoise"); n.inputs['Scale'].default_value = 3; n.inputs['Detail'].default_value = 8; L.new(mp.outputs[0], n.inputs['Vector'])
    b = N.new("ShaderNodeBump"); b.inputs['Strength'].default_value = 0.25; L.new(n.outputs['Fac'], b.inputs['Height']); L.new(b.outputs['Normal'], N["Principled BSDF"].inputs['Normal'])
    haze((0, 900, 120), (3000, 900, 240), density=0.0012, color=(0.6, 0.65, 0.8), anis=0.2)
    return {}


MOVES = {"night_drift": dict(kind="plate", far=3000.0, cam=lambda c, t: ((-60 + 40 * t, -120, 22), (0, 900, 140), 40))}
