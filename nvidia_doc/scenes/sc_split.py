"""CH4 1A redo (249 f): split screen, composed in the patch's master scene from two scenes rendered full frame with the
subject centred (each strip cropped to the middle 960 px and offset to its half), plus the CHAPTER 4 card on top
from its own transparent scene (same card, layout and timing as the delivered master, so the overlay still aligns).
  office    LEFT: night, a high office; the man (recurring figure, from behind) stands at the window, phone at his ear
  newsroom  RIGHT: a reporter at a newsroom desk (from behind / three-quarter back), desk-phone handset at his ear,
            monitors with a generic news page, rows of desks and lights beyond
  title     the CHAPTER 4 card alone (transparent film)
"""
import os, math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
from common import area_light, world_flat
from human import reach, fingers_curl, pose_walk, _world_verts

HERE = os.path.dirname(os.path.abspath(__file__))
GEN = os.path.join(HERE, "..", "assets", "generated")
EXPOSURE = 0.0
VARIANT_FOR = {"office": "office", "newsroom": "newsroom", "title": "title"}
FRAMES = {"office": 249, "newsroom": 249, "title": 249}
TITLE = ("CHAPTER 4", "THE SECOND EMPLOYEE", 18, 120, 0.55)        # identical to the delivered c4_01 card


def _fwd(h):
    return (h.arm.matrix_world.to_3x3() @ Vector((0, -1, 0))).normalized()


def phone_to_ear(h, side, phone):
    fwd = _fwd(h); up = Vector((0, 0, 1)); right = fwd.cross(up).normalized()
    s = 1 if side == "R" else -1
    hd = h.bone_head("head")
    ear = hd + up * 0.06 + right * (0.08 * s)
    wrist = ear - up * 0.16 + fwd * 0.03 + right * (0.03 * s)       # just below the jaw, phone held up to the ear
    reach(h, side, wrist, right * s * 0.8 - up * 0.8 - fwd * 0.1, (up * 0.95 - right * (0.25 * s)).normalized())
    fingers_curl(h, 55, side=(side,), thumb=25)
    bpy.context.view_layer.update()
    phone.location = ear + right * (0.02 * s) + fwd * 0.03 - up * 0.04
    phone.rotation_euler = (0, 0, math.atan2(fwd.y, fwd.x))


def build(variant=None):
    c = {}
    if variant == "title":
        world_flat((0, 0, 0), 0.0)
        bpy.context.scene.render.film_transparent = True
        return c
    if variant == "office":
        world_flat((0.008, 0.012, 0.024), 1.0)
        floor = fabric("Carpet", (0.04, 0.04, 0.045), 0.95, 0.2, 400)
        box("Floor", (0, 0, -0.01), (12, 12, 0.02), floor)
        box("Ceil", (0, 0, 3.0), (12, 12, 0.05), pbr("Ceil", (0.04, 0.04, 0.045), 0.9))
        box("WallL", (-4, 0, 1.5), (0.1, 12, 3.0), pbr("Wall", (0.07, 0.065, 0.06), 0.8))
        gl = glass("Window", (0.9, 0.94, 0.96), 0.01)
        box("Window", (0, 3.0, 1.5), (8, 0.02, 3.0), gl)
        for k in range(6):
            box("Mullion", (-3 + k * 1.4, 2.99, 1.5), (0.05, 0.06, 3.0), pbr("Mull", (0.02, 0.02, 0.022), 0.4, 0.8))
        body = pbr("TowerBody", (0.01, 0.012, 0.016), 0.3, 0.5)
        win = window_material("Windows", density=0.2, floor=3.6, bay=1.8, strength=1.3)
        skyline(5, (0, 700, 0), (900, 500), 220, (30, 190), body, win, footprint=(25, 60), z0=-140)
        box("CityGround", (0, 800, -141), (4000, 2400, 1), window_material("Streets", lit=(1.0, 0.7, 0.4), density=0.08, floor=40, bay=40, strength=1.4))
        wal = wood("Desk", (0.03, 0.018, 0.01), (0.08, 0.045, 0.025), scale=(8, 0.4, 0.4), rough=0.3, coat=0.6)
        box("Desk", (-1.6, 0.0, 0.74), (1.8, 0.9, 0.05), wal, bevel=0.01)
        lamp = bpy.data.lights.new("DeskLamp", 'POINT'); lamp.energy = 25; lamp.color = (1.0, 0.75, 0.5); lamp.shadow_soft_size = 0.1
        lo = bpy.data.objects.new("DeskLamp", lamp); bpy.context.collection.objects.link(lo); lo.location = (-2.2, 0.2, 1.2)
        box("LampShade", (-2.2, 0.2, 1.22), (0.25, 0.25, 0.18), emissive("Shade", (1.0, 0.75, 0.5), 2.5))
        rim = area_light((1.5, 2.6, 2.2), (0, 0, 0), 1.5, 40, (0.55, 0.7, 1.0)); point_at(rim, (0.2, 1.8, 1.5))
        rim.visible_camera = False; rim.visible_glossy = False; rim.visible_transmission = False
        from people import man
        h = man("ExecPhone")
        pose_walk(h, 0.0, stride=0.0, arm_swing=0.0)
        h.arm.rotation_euler = (0, 0, math.pi); h.arm.location = (0.2, 2.2, 0); bpy.context.view_layer.update()   # faces +Y: the window
        w = np.concatenate([_world_verts(o) for o in h.parts if o.type == 'MESH'])
        h.arm.location.z -= w[:, 2].min(); bpy.context.view_layer.update()
        ph = box("Phone", (0, 0, 0), (0.075, 0.012, 0.15), pbr("Phone", (0.02, 0.02, 0.022), 0.3), bevel=0.004)
        c.update(h=h, phone=ph, target=Vector((0.2, 2.2, 1.45)))
        phone_to_ear(h, "R", ph)
        return c
    # ---------------------------------------------------------------------- newsroom
    world_flat((0.01, 0.012, 0.016), 1.0)
    from sc_newsdesk import news_page, screen_mat, screen_plane
    os.makedirs(GEN, exist_ok=True)
    box("Floor", (0, 6, -0.01), (16, 24, 0.02), fabric("Carpet", (0.05, 0.055, 0.06), 0.95, 0.2, 400))
    box("Ceil", (0, 6, 3.2), (16, 24, 0.05), pbr("Ceil", (0.12, 0.12, 0.12), 0.9))
    box("WallBack", (0, 17, 1.6), (16, 0.1, 3.2), pbr("Wall", (0.15, 0.16, 0.17), 0.8))
    desk = pbr("DeskTop", (0.6, 0.6, 0.58), 0.4)
    bez = pbr("Bezel", (0.02, 0.02, 0.022), 0.4)
    pages = [news_page(os.path.join(GEN, f"news_page_{k}.png"), 40 + k) for k in range(3)]
    smats = [screen_mat(f"News{k}", pages[k], strength=1.1) for k in range(3)]
    for row in range(4):                                         # rows of desks with monitors receding
        for col in range(-2, 3):
            x, y = col * 2.6, 1.2 + row * 3.2
            box("Desk", (x, y, 0.74), (1.8, 0.8, 0.04), desk)
            box("DeskLeg", (x, y, 0.37), (1.7, 0.05, 0.72), pbr("Leg", (0.15, 0.15, 0.16), 0.4, 0.6))
            for j, dx in enumerate((-0.35, 0.35)):
                box("Mon", (x + dx, y + 0.25, 1.05), (0.56, 0.03, 0.33), bez)
                screen_plane("Scr", (x + dx, y + 0.233, 1.05), (0.53, 0.3), (math.radians(90), 0, 0), smats[(row + col + j) % 3])
    for k in range(5):                                           # overhead light rows
        box("Light", (0, 1 + k * 3.2, 3.15), (10, 0.25, 0.04), emissive("Fluoro", (0.95, 0.97, 1.0), 4.0))
        area_light((0, 1 + k * 3.2, 3.1), (0, 0, 0), 2.0, 60, (0.95, 0.97, 1.0)).visible_camera = False
    # the reporter (generic, not a named person), seated at the nearest desk, handset to his ear
    from sc_invest import person, seat_person, office_chair
    r = person("Reporter", 1.0, 34, "male_casualsuit03", "short02", hv=0.2)
    seat_person(r, (0.0, 0.55, 0), math.pi, lean=8)               # faces +Y: his monitors
    office_chair((0.0, 0.47, 0), math.pi, fabric("ChairFab", (0.08, 0.09, 0.1), 0.85, 0.3, 300), pbr("Leg", (0.05, 0.05, 0.05), 0.4, 0.8))
    hs = box("Handset", (0, 0, 0), (0.05, 0.035, 0.2), pbr("Handset", (0.03, 0.03, 0.033), 0.35), bevel=0.012)
    box("DeskPhone", (0.55, 1.05, 0.79), (0.22, 0.2, 0.05), pbr("Handset", (0.03, 0.03, 0.033), 0.35), bevel=0.01)
    # the other hand rests on the desk
    bpy.context.view_layer.update()
    reach(r, "R", Vector((-0.15, 1.0, 0.8)), Vector((-0.6, -0.2, -0.7)), Vector((0, 1, -0.2)))
    c.update(h=r, phone=hs, target=Vector((0.0, 0.8, 1.2)))
    phone_to_ear(r, "L", hs)
    return c


def anim_office(c, t):
    h = c["h"]
    h.rot("head", (0, 0, 1), 6 * math.sin(t * 4.0))              # listening, a slight turn of the head
    h.rot("spine03", (1, 0, 0), 2 * math.sin(t * 2.2))
    bpy.context.view_layer.update()
    phone_to_ear(h, "R", c["phone"])


def anim_news(c, t):
    h = c["h"]
    h.rot("head", (1, 0, 0), 3 * math.sin(t * 5.0))
    bpy.context.view_layer.update()
    phone_to_ear(h, "L", c["phone"])


MOVES = {
    "office": dict(kind="anim", dof=3.0, far=2000.0, anim=anim_office,
                   cam=lambda c, t: (Vector((-0.55, -1.9, 1.55)).lerp(Vector((-0.4, -1.35, 1.55)), ease(t)), c["target"] + Vector((0, 1.0, 0.0)), 35),
                   focus=lambda c, t: c["target"]),
    "newsroom": dict(kind="anim", dof=2.8, far=40.0, anim=anim_news,
                     cam=lambda c, t: (Vector((-1.1, -1.2, 1.45)).lerp(Vector((-0.85, -0.9, 1.42)), ease(t)), c["target"] + Vector((0.1, 0.5, 0)), 32),
                     focus=lambda c, t: c["target"]),
    "title": dict(kind="anim", far=10.0, title=TITLE, cam=lambda c, t: ((0, -5, 1.5), (0, 0, 1.5), 35)),
}
