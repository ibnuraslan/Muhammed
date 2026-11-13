"""Thumbnail set: the man in the black leather jacket at a table under one hard light, head bowed, hands at his head;
behind him in the dark, four women standing, dimly side-lit. No likeness is attempted."""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
from human import Human, add_asset, pose_sit, fingers_curl, reach, _world_verts
from people import man

EXPOSURE = 0.0


def _ground(h, z=0.0):
    bpy.context.view_layer.update()
    w = np.concatenate([_world_verts(o) for o in h.parts if o.type == 'MESH'])
    h.arm.location.z += z - w[:, 2].min(); bpy.context.view_layer.update()


def woman_standing(name, loc, rot, hair, suit, skin, years):
    h = Human(name, gender=0.0, years=years, muscle=0.45, weight=0.4, height=0.5,
              skin=skin, eyebrows="eyebrow001", eyelashes="eyelashes01")
    add_asset(h, "clothes", suit, hue=0.5, sat=0.1, val=0.14, rough=0.6, sheen=0.3)
    add_asset(h, "clothes", "shoes02", val=0.2, rough=0.3)
    add_asset(h, "hair", hair, val=0.3, rough=0.4)
    for sd, sg in (("L", 1), ("R", -1)):
        h.aim(f"upperarm01.{sd}", (0.16 * sg, 0.02, -1)); h.aim(f"upperarm02.{sd}", (0.16 * sg, 0.02, -1))
        h.aim(f"lowerarm01.{sd}", (0.06 * sg, -0.12, -1)); h.aim(f"lowerarm02.{sd}", (0.06 * sg, -0.12, -1))
        h.aim(f"wrist.{sd}", (0.02 * sg, -0.05, -1))
    fingers_curl(h, 20)
    h.arm.location = loc; h.arm.rotation_euler = (0, 0, rot)
    _ground(h)
    return h


def build(variant=None):
    world_flat((0.003, 0.0032, 0.0035), 1.0)
    char = pbr("Charcoal", (0.018, 0.018, 0.02), 0.85)
    box("Floor", (0, 0, -0.01), (14, 14, 0.02), char)
    box("Back", (0, 5.0, 2.5), (14, 0.05, 5), char)
    walnut = wood("Walnut", (0.018, 0.009, 0.005), (0.06, 0.03, 0.015), scale=(9, 0.35, 0.35), rough=0.3, coat=0.8)
    box("Table", (0, -0.25, 0.74), (1.8, 0.9, 0.05), walnut, bevel=0.01)
    box("TableBase", (0, -0.2, 0.36), (1.2, 0.5, 0.7), pbr("Base", (0.01, 0.01, 0.012), 0.5))
    # the man, seated behind the table facing the camera (-Y), elbows on the table, hands at his head
    h = man()
    pose_sit(h, lean=30)
    h.rot("neck01", (1, 0, 0), 10); h.rot("head", (1, 0, 0), 22)
    h.arm.location = (0, 0.55, 0.0); bpy.context.view_layer.update()
    _ground(h, 0.0)
    h.arm.location.z += 0.08; bpy.context.view_layer.update()       # sitting on a stool hidden behind the table
    hd = h.bone_head("head"); ht = h.bone_tail("head")
    c = hd + (ht - hd) * 0.55
    for sd, sg in (("L", 1), ("R", -1)):
        reach(h, sd, c + Vector((0.095 * sg, -0.02, 0.0)), (0.3 * sg, -0.2, -1.0), hand_dir=(-0.2 * sg, 0.1, 1.0))
    fingers_curl(h, 25, thumb=5)
    # four women behind him in the dark
    W = [((-1.05, 2.2, 0), 0.25, "long01", "female_elegantsuit01", "middleage_lightskinned_female_diffuse.png", 38),
         ((-0.35, 2.9, 0), 0.08, "bob02", "female_casualsuit02", "young_lightskinned_female_diffuse.png", 30),
         ((0.45, 3.0, 0), -0.08, "ponytail01", "female_elegantsuit01", "middleage_lightskinned_female_diffuse.png", 44),
         ((1.15, 2.3, 0), -0.25, "long01", "female_casualsuit01", "young_lightskinned_female_diffuse.png", 34)]
    women = [woman_standing(f"W{k}", *w) for k, w in enumerate(W)]
    # light: one hard key over him, a dim cold side light on the women, one lime rim on the front-left woman
    def spot(n, loc, tgt, e, col, deg, blend, soft):
        l = bpy.data.lights.new(n, 'SPOT'); l.energy = e; l.color = col; l.spot_size = math.radians(deg)
        l.spot_blend = blend; l.shadow_soft_size = soft
        o = bpy.data.objects.new(n, l); bpy.context.collection.objects.link(o); o.location = loc; point_at(o, tgt); return o
    spot("Key", (0.25, 0.0, 3.2), (0, 0.45, 1.0), 2600, (1.0, 0.93, 0.84), 28, 0.35, 0.08)
    spot("WomenSide", (-3.5, 2.0, 2.4), (0, 2.6, 1.4), 900, (0.62, 0.72, 0.9), 30, 0.7, 0.3)
    spot("WomenSide2", (3.5, 2.2, 2.2), (0.6, 2.8, 1.4), 300, (0.62, 0.72, 0.9), 30, 0.7, 0.3)
    spot("Lime", (-1.6, 3.6, 2.3), (-1.05, 2.2, 1.4), 400, (0.88, 0.97, 0.0), 14, 0.4, 0.05)
    return dict(h=h, women=women, head=c)


MOVES = {"front": dict(kind="plate", cam=lambda c, t: ((0, -3.6, 1.55), (0, 1.0, 1.25), 40))}
