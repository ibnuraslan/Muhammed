"""RAID: June 2009, dawn raids across the suburbs.
  arrive (ch3 4A): dawn on a pavillon street: unmarked cars pull up and officers walk fast to a front door
  stairs (ch3 4B): inside the house, the panel under the staircase lifts away: jewels on small display stands in a torch beam
"""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
import dd
from dd import officer, place, face_to, walk_to, arms_relaxed, zero, ground

EXPOSURE = 0.0
DUR = {"arrive": 9.0, "stairs": 9.0}
VARIANT_FOR = {"arrive": "street", "stairs": "hall"}


def build_street(c):
    world_sky(sun_elev_deg=3, sun_rot_deg=80, strength=1.3, tint=(0.85, 0.9, 1.0))
    sun(3, 80, energy=1.0, color=(1.0, 0.75, 0.55), angle_deg=2.0)
    road = dd.wet(dd.tex_mat("asphalt_02", 0.4, tint=(0.55, 0.55, 0.57), name="RaidRoad", sat=0.4), 0.3, 0.3, ripples=False)
    box("Road", (0, 0, -0.06), (90, 8, 0.1), road)
    pave = dd.tex_mat("concrete_floor_02", 0.5, tint=(0.6, 0.6, 0.58), name="RaidPave", sat=0.3)
    for sy in (-1, 1):
        box("Pave", (0, sy * 5.0, 0.0), (90, 2.0, 0.12), pave)
        box("Kerb", (0, sy * 4.0, 0.0), (90, 0.2, 0.13), pbr("Kerb", (0.4, 0.4, 0.4), 0.6))
    lawn = dd.tex_mat("leafy_grass", 0.5, tint=(0.7, 0.78, 0.62), name="RaidLawn", sat=0.7)
    box("Front", (0, 10, -0.03), (90, 8, 0.06), lawn)
    box("FrontOpp", (0, -10, -0.03), (90, 8, 0.06), lawn)
    for k, x in enumerate((-24, -12, 0, 12, 24)):
        dd.pavillon((x, 12.0, 0), w=8.5, d=8.0, floors=2, name=f"H{k}", stone=(k % 2 == 0), shutters=((0.9, 0.9, 0.0, 0.5, 0.9), (1.0, 0.6, 0.0))[k % 2])
        dd.pavillon((x + 5, -12.0, 0), w=8.5, d=8.0, floors=2, rot_z=math.pi, name=f"O{k}", stone=(k % 2 == 1))
        box("Wall", (x, 6.2, 0.45), (8.0, 0.25, 0.9), dd.tex_mat("plastered_wall_03", 0.6, tint=(0.88, 0.85, 0.78), name="RaidWall", sat=0.6))
        dd.model_h("shrub_02", (x - 3.0, 7.5, 0), 1.3) if k % 2 else None
    box("Path", (0, 9.0, 0.0), (1.2, 6.0, 0.02), dd.tex_mat("gravel_floor", 0.8, tint=(0.75, 0.73, 0.7), name="RaidGravel", sat=0.5))
    for k in range(4):
        dd.model_h("jacaranda_tree", (-30 + k * 18, 7.6, 0), 8.0, rot_z=k)
    c["cars"] = []
    for k, col in enumerate(((0.08, 0.09, 0.1), (0.4, 0.41, 0.43), (0.12, 0.14, 0.2))):
        cr = dd.sedan(f"Unmarked{k}", col, lights=True, variant="unmarked"); c["cars"].append(cr)
    c["officers"] = [officer(f"Raid{k}", 32 + 5 * k, seed=k) for k in range(4)]
    for k in range(2):
        dd.sedan(f"Parked{k}", ((0.6, 0.6, 0.6), (0.3, 0.05, 0.05))[k], lights=False).location = (-18 + 30 * k, -2.6, 0)


def build_hall(c):
    """A pavillon hallway: a timber staircase, under it a panelled cupboard whose panel lifts away."""
    world_flat((0.01, 0.01, 0.012), 1.0)
    B = dd.Builder("Hall")
    B.box((0, 0, -0.05), (6, 6, 0.1), dd.tex_mat("herringbone_parquet", 0.6, tint=(0.7, 0.6, 0.5), name="HallFloor", sat=0.7))
    wallp = dd.tex_mat("beige_wall_001", 0.6, tint=(0.85, 0.8, 0.7), name="HallWall", sat=0.6)
    B.box((0, 2.6, 1.4), (6, 0.1, 2.8), wallp).box((-2.6, 0, 1.4), (0.1, 6, 2.8), wallp).box((0, 0, 2.85), (6, 6, 0.1), pbr("HallCeil", (0.8, 0.78, 0.74), 0.9))
    oak = dd.tex_mat("oak_veneer_01", 1.2, tint=(0.75, 0.62, 0.48), name="StairOak", sat=0.8, coat=0.3)
    for k in range(14):                          # stairs rising along the back wall toward +x
        B.box((-1.6 + k * 0.26, 2.1, 0.09 + k * 0.19), (0.27, 0.9, 0.04), oak)
        B.box((-1.6 + k * 0.26 - 0.13, 2.1, k * 0.19 + 0.05), (0.02, 0.9, 0.19), oak)
    B.box((0.1, 1.64, 1.4), (3.7, 0.08, 0.08), oak, rot=(0, -math.atan2(0.19, 0.26), 0))
    for k in range(12):
        B.box((-1.4 + k * 0.28, 1.64, 0.55 + k * 0.205 + 0.45), (0.035, 0.035, 0.9), oak)
    # the closed side under the stairs: panelled; one panel is the hidden door
    B.box((0.6, 1.66, 0.6), (2.6, 0.04, 1.2), dd.tex_mat("wooden_panels", 0.6, tint=(0.75, 0.68, 0.58), name="UnderPanel", sat=0.8))
    B.box((0.6, 2.1, 0.6), (1.0, 0.8, 1.15), pbr("Cavity", (0.03, 0.025, 0.02), 0.8))
    B.done()
    # inside: small display stands with jewels
    stand = pbr("DispStand", (0.85, 0.84, 0.8), 0.5)
    for k in range(5):
        p = Vector((0.25 + k * 0.17, 1.95 + 0.08 * (k % 2), 0.05))
        cyl("Stand", p + Vector((0, 0, 0.06)), 0.035, 0.12, stand, verts=20)
        dd.ring(f"HidRing{k}", p + Vector((0, 0, 0.14)), stone_r=0.0045, band="plat" if k % 2 else "gold", stone=("diamond", "sapphire", "diamond", "ruby", "diamond")[k])
    for k in range(3):
        box("NeckBust", (0.35 + k * 0.3, 2.3, 0.2), (0.12, 0.08, 0.3), fabric("BustVel", (0.08, 0.08, 0.1), 0.9, 0.6, 300))
    pnl = dd.Builder("HiddenPanel"); pnl.box((0, 0, 0), (0.95, 0.04, 1.1), dd.tex_mat("wooden_panels", 0.6, tint=(0.75, 0.68, 0.58), name="HidPanel", sat=0.8))
    c["panel"] = pnl.done((0.6, 1.62, 0.58))
    tl = bpy.data.lights.new("RaidTorch", 'SPOT'); tl.energy = 40; tl.spot_size = math.radians(22); tl.spot_blend = 0.4; tl.color = (1.0, 0.95, 0.85)
    to = bpy.data.objects.new("RaidTorch", tl); bpy.context.collection.objects.link(to); c["torch"] = to
    dawn = bpy.data.lights.new("DawnWin", 'AREA'); dawn.size = 1.5; dawn.energy = 60; dawn.color = (0.7, 0.8, 1.0)
    do = bpy.data.objects.new("DawnWin", dawn); bpy.context.collection.objects.link(do); do.location = (2.5, -2.0, 2.0); point_at(do, (0, 1, 0.5))
    c["officer"] = officer("Searcher", 39, seed=2)


def build(variant=None):
    c = {}
    {"street": build_street, "hall": build_hall}[variant or "street"](c)
    return c


def anim_arrive(c, t):
    sec = t * DUR["arrive"]
    for k, cr in enumerate(c["cars"]):
        stop = -5.0 + 6.5 * k; t0 = 0.6 * k; T = 3.0
        u = min(1.0, max(0.0, (sec - t0) / T))
        x = stop - 22.0 * (1 - u) ** 2
        cr.location = (x, 2.2, 0); cr.rotation_euler = (0, 0, 0)
    door = Vector((-0.3, 11.6, 0))
    for k, h in enumerate(c["officers"]):
        a = Vector((-4.5 + 2.2 * k, 3.2, 0.12)); b = door + Vector((-0.6 + 0.4 * k, -1.6 - 0.9 * k, 0))
        walk_to(h, a, b, max(0.0, sec - 3.2 - 0.35 * k), speed=1.6, cadence=2.2)
        ground(h, 0.12 if h.arm.location.y < 6.0 else 0.0)


def anim_stairs(c, t):
    sec = t * DUR["stairs"]
    u = ease(min(1.0, max(0.0, (sec - 1.0) / 2.5)))
    p = c["panel"]; p.location = (0.6 - 0.25 * u, 1.62 - 0.55 * u, 0.58 + 0.15 * u); p.rotation_euler = (0, 0, math.radians(-25 * u))
    h = c["officer"]; sp = Vector((-0.9, 0.2, 0)); place(h, sp, face_to(sp, (0.6, 2.0))); arms_relaxed(h)
    to = c["torch"]; to.location = h.bone_head("upperarm01.R") + Vector((0.25, 0.25, -0.15))
    point_at(to, Vector((0.55 + 0.25 * math.sin(sec * 0.5), 2.0, 0.2)))


MOVES = {
    "arrive": dict(kind="anim", dof=8.0, anim=anim_arrive,
                   cam=lambda c, t: (Vector((14.0, -6.5, 2.4)).lerp(Vector((12.0, -6.0, 2.2)), ease(t)), Vector((-1.0, 6.0, 1.0)), 30),
                   focus=lambda c, t: Vector((-1.0, 5.0, 1.0))),
    "stairs": dict(kind="anim", dof=2.8, anim=anim_stairs,
                   cam=lambda c, t: (Vector((-0.2, -0.6, 0.95)).lerp(Vector((0.0, -0.3, 0.8)), ease(t)), Vector((0.6, 2.0, 0.3)), 30),
                   focus=lambda c, t: Vector((0.6, 2.0, 0.25))),
}
