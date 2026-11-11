"""Dramatization: a dark room across the street. A camera with a long telephoto lens on a tripod points through
half-open blinds at a lit office floor; on the desk, monitors show grainy feeds. The camera glides along the
lens toward the window, the monitors flicker."""
import os, math
import numpy as np
import bpy
from mathutils import Vector
from kit import *

EXPOSURE = 0.5
HERE = os.path.dirname(os.path.abspath(__file__))
GEN = os.path.join(HERE, "..", "assets", "generated")


def feed_material(k):
    m = bpy.data.materials.new(f"Feed{k}"); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(os.path.join(GEN, f"feed{k}.png"))
    L.new(tc.outputs['UV'], t.inputs['Vector'])
    L.new(t.outputs['Color'], p.inputs['Emission Color']); p.inputs['Emission Strength'].default_value = 1.2
    p.inputs['Base Color'].default_value = (0.01, 0.01, 0.01, 1); p.inputs['Roughness'].default_value = 0.2
    m["strength"] = 1.2
    return m


def build(variant=None):
    world_flat((0.004, 0.005, 0.008), 1.0)
    room = pbr("RoomWall", (0.03, 0.03, 0.033), 0.85)
    box("Floor", (0, 0, -0.01), (8, 8, 0.02), pbr("Concrete", (0.05, 0.05, 0.05), 0.7))
    box("WallWin", (0, 2.0, 1.5), (8, 0.1, 3.0), room)
    # window opening in the wall (two wall pieces around a 2.4 x 1.4 hole)
    for x in (-2.6, 2.6):
        box("WallSide", (x, 1.99, 1.5), (2.8, 0.12, 3.0), room)
    bpy.data.objects["WallWin"].hide_render = True
    box("WallBelow", (0, 1.99, 0.45), (2.4, 0.12, 0.9), room); box("WallAbove", (0, 1.99, 2.65), (2.4, 0.12, 0.7), room)
    box("Glass", (0, 2.0, 1.6), (2.4, 0.01, 1.4), rain_glass("Win", 60, 0.75))
    for k in range(18):          # blinds, lower half pulled up, slats tilted open
        box("Slat", (0, 1.9, 2.28 - k * 0.04), (2.4, 0.035, 0.008), pbr("Slat", (0.06, 0.06, 0.06), 0.6), rot=(math.radians(55), 0, 0))
    # the tripod and the telephoto camera aimed out of the window
    blk = pbr("CamBody", (0.015, 0.015, 0.016), 0.35, 0.2)
    rub = pbr("Rubber", (0.01, 0.01, 0.01), 0.8)
    for k in range(3):
        a = k / 3 * 2 * math.pi
        box("Leg", (0.4 + 0.28 * math.cos(a), 0.6 + 0.28 * math.sin(a), 0.6), (0.025, 0.025, 1.25), blk,
            rot=(math.radians(13) * math.sin(a), -math.radians(13) * math.cos(a), 0))
    box("Head", (0.4, 0.6, 1.24), (0.08, 0.08, 0.06), blk)
    box("Body", (0.4, 0.55, 1.34), (0.14, 0.09, 0.11), blk, bevel=0.01)
    lens = cyl("Lens", (0.4, 0.86, 1.33), 0.055, 0.52, rub, verts=48, rot=(math.radians(90), 0, 0))
    hood = cyl("Hood", (0.4, 1.16, 1.33), 0.068, 0.12, blk, verts=48, rot=(math.radians(90), 0, 0))
    hood.modifiers.new("s", 'SOLIDIFY').thickness = 0.004
    cyl("Glass", (0.4, 1.13, 1.33), 0.05, 0.004, pbr("LensGlass", (0.02, 0.03, 0.05), 0.02, 0.6, **{'Coat Weight': 1.0}), verts=48, rot=(math.radians(90), 0, 0))
    box("Ring", (0.4, 0.75, 1.33), (0.115, 0.03, 0.115), pbr("Ring", (0.6, 0.6, 0.6), 0.3, 1.0))
    # desk with three monitors showing the feeds
    box("Desk", (-1.3, 0.9, 0.73), (1.8, 0.7, 0.04), pbr("Desk", (0.03, 0.03, 0.032), 0.4))
    feeds = []
    for k in range(3):
        x = -2.0 + k * 0.68
        box("Mon", (x, 1.05, 1.05), (0.62, 0.03, 0.38), pbr("Bezel", (0.01, 0.01, 0.01), 0.3))
        bpy.ops.mesh.primitive_plane_add(size=1, location=(x, 1.033, 1.05), rotation=(math.radians(90), 0, 0))
        sc = bpy.context.active_object; sc.scale = (0.58, 0.34, 1); m = feed_material(k); sc.data.materials.append(m); feeds.append(m)
    box("Ashtray", (-0.6, 0.75, 0.77), (0.1, 0.1, 0.02), pbr("Glass2", (0.3, 0.3, 0.3), 0.05, 0.0, **{'Transmission Weight': 0.8}))
    cyl("Cup", (-0.8, 0.7, 0.8), 0.04, 0.1, pbr("PaperCup", (0.7, 0.68, 0.64), 0.7), verts=24)
    # outside: the lit office floor across the street + city
    win = window_material("Across", lit=(1.0, 0.85, 0.65), density=0.15, floor=4.0, bay=1.5, strength=0.6)
    box("Tower", (4, 42, 30), (50, 20, 60), win)
    box("LitFloor", (3, 31.8, 3.2), (24, 0.2, 3.0), emissive("Lit", (1.0, 0.86, 0.66), 2.2))
    skyline(61, (0, 160, 0), (200, 60), 30, (40, 140), None, window_material("Far", density=0.2, strength=0.5), footprint=(20, 40))
    for k in range(8):
        box("StreetLamp", (-40 + k * 12, 20, 6), (0.6, 0.3, 0.2), emissive("Sodium", (1.0, 0.62, 0.3), 30))
    # cold window light raking the lens + the monitors' glow
    l = area_light((1.2, 2.6, 2.2), (0, 0, 0), 1.0, 1.2, (0.5, 0.65, 1.0)); point_at(l, (0.3, 0.6, 1.2))
    return dict(feeds=feeds, lens=Vector((0.4, 1.0, 1.33)))


def _tick(c, t):
    for k, m in enumerate(c["feeds"]):
        f = 1.0 + 0.12 * math.sin(t * 40 + k * 2) + 0.06 * math.sin(t * 97 + k)
        m.node_tree.nodes["Principled BSDF"].inputs['Emission Strength'].default_value = m["strength"] * f


MOVES = {
    "lens_push": dict(kind="anim", dof=2.8, far=200.0,
                      cam=lambda c, t: (Vector((0.72, 0.05, 1.5)).lerp(Vector((0.6, 0.35, 1.45)), ease(t)), Vector((0.25, 2.0, 1.36)), 32),
                      focus=lambda c, t: Vector((0.4, 0.9, 1.33)).lerp(Vector((3, 31.8, 3.2)), ease((t - 0.45) / 0.45)), anim=_tick),
}
