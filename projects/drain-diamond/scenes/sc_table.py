"""TABLE: the police evidence room. A long table under a grey cloth: the recovered rings laid out in rows on small
stands, numbered tags (blank-faced, no names). For the last shots, the big diamond alone on its stand among many
empty stands for the pieces still missing.
  layout (ch3 9A): overhead push down the table while an officer walks its length
  tags   (ch3 9B): wide/overhead, an officer walks the table setting tags down as he goes (tags appear behind him)
  alone  (ch4 6A): the big diamond alone on its stand, the camera pulling back
  empty  (ch4 6B): pull back wider: the long table of empty stands
"""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
import dd
from dd import officer, walk_to, arms_relaxed

EXPOSURE = 0.0
DUR = {"layout": 9.0, "tags": 9.0, "alone": 9.0, "empty": 9.0}
VARIANT_FOR = {"layout": "count", "tags": "count", "alone": "final", "empty": "final"}
TL, TW, TZ = 7.0, 1.4, 0.78           # table length (along x), width, top height
NX, NY = 22, 4                         # stand grid


def stand_obj(name, loc, mat):
    o = cyl(name, loc + Vector((0, 0, 0.015)), 0.022, 0.03, mat, verts=20)
    return o


def build(variant=None):
    c = {}
    v = variant or "count"
    world_flat((0.02, 0.022, 0.028), 1.0)
    rng = np.random.default_rng(41)
    B = dd.Builder("EvidenceRoom")
    B.box((0, 0, -0.05), (16, 10, 0.1), dd.tex_mat("concrete_floor_02", 0.6, tint=(0.5, 0.5, 0.5), name="ERFloor", sat=0.3))
    wall = pbr("ERWall", (0.42, 0.44, 0.44), 0.8)
    B.box((0, 4.0, 1.5), (16, 0.1, 3.0), wall).box((-7.5, 0, 1.5), (0.1, 10, 3.0), wall)
    B.box((0, -4.6, 1.5), (16, 0.1, 3.0), wall).box((7.5, 0, 1.5), (0.1, 10, 3.0), wall).box((0, 0, 3.05), (16, 10, 0.1), wall)
    B.box((0, 0, TZ - 0.02), (TL + 0.2, TW + 0.2, 0.04), dd.tex_mat("velour_velvet", 2.5, tint=(0.025, 0.025, 0.03), name="TableCloth", sat=0.2))
    for sx in (-1, 1):
        for sy in (-1, 1):
            B.box((sx * TL / 2, sy * TW / 2, TZ / 2), (0.05, 0.05, TZ), pbr("Leg", (0.3, 0.3, 0.32), 0.4, 0.8))
    B.done()
    for k in range(5):                         # evidence shelving with boxes along the back wall
        x = -6.0 + k * 2.6
        dd.model_h("steel_frame_shelves_01", (x, 3.5, 0), 2.1)
        for j in range(3):
            dd.model_h("cardboard_box_01", (x - 0.3 + 0.3 * (j % 2), 3.5, 0.05 + j * 0.62), 0.32, rot_z=0.1 * j)
    dd.model_h("metal_office_desk", (-6.5, -1.5, 0), 0.76, rot_z=math.pi / 2)
    dd.model_h("desk_lamp_arm_01", (-6.5, -1.2, 0.76), 0.5)
    smat = pbr("StandWhite", (0.85, 0.84, 0.8), 0.45)
    tagm = pbr("Tag", (0.9, 0.88, 0.78), 0.7)
    grid = [Vector((-TL / 2 + 0.25 + i * (TL - 0.5) / (NX - 1), -TW / 2 + 0.25 + j * (TW - 0.5) / (NY - 1), TZ)) for i in range(NX) for j in range(NY)]
    c["grid"] = grid
    if v == "count":
        # the haul laid out on black velvet: rows of rings on cones, earring pairs, necklaces laid in U-shapes,
        # each piece with a paper evidence tag on a string
        c["tags"] = []
        cone_m = dd.tex_mat("velour_velvet", 3.0, tint=(0.05, 0.05, 0.06), name="ConeVel", sat=0.2)
        M = dd.jewel_mats()
        stones = ["diamond", "diamond", "sapphire", "ruby", "emerald", "diamond"]
        cols, rows = 16, 3
        for i in range(cols):
            for j in range(rows):
                p = Vector((-TL / 2 + 0.35 + i * (TL - 0.7) / (cols - 1), -TW / 2 + 0.35 + j * (TW - 0.7) / (rows - 1), TZ))
                kind = (i + j) % 3
                if kind == 0:                                        # a ring on a velvet cone
                    bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.018, radius2=0.006, depth=0.05, location=p + Vector((0, 0, 0.025)))
                    cn = bpy.context.active_object; cn.data.materials.append(cone_m)
                    dd.ring(f"R{i}_{j}", p + Vector((0, 0, 0.0565)), stone_r=float(rng.uniform(0.004, 0.007)), band="plat" if i % 2 else "gold",
                            stone=stones[(i + j) % 6], upright=True, rot=(0, 0, float(rng.uniform(-0.4, 0.4))))
                elif kind == 1:                                      # a pair of earrings
                    for sx in (-0.018, 0.018):
                        dd.earring(f"E{i}_{j}{sx}", p + Vector((sx, 0, 0.008)), float(rng.uniform(0.004, 0.006)), stones[(i * 3 + j) % 6])
                else:                                                # a necklace laid in a U, a pendant at the bottom
                    n = 26
                    for q in range(n):
                        a_ = math.pi * q / (n - 1)
                        cyl(f"N{i}_{j}", p + Vector((0.07 * math.cos(a_), 0.05 * math.sin(a_) - 0.02, 0.004)), 0.0032, 0.004,
                            M["plat"] if i % 2 else M["gold"], verts=8)
                    dd.earring(f"Pend{i}_{j}", p + Vector((0, -0.025, 0.008)), 0.007, stones[i % 6])
                tag = box("TagCard", p + Vector((0.0, -0.1, 0.002)), (0.05, 0.032, 0.002), tagm, rot=(0, 0, 0.06 * float(rng.uniform(-1, 1))))
                box("TagString", p + Vector((0.0, -0.06, 0.002)), (0.002, 0.06, 0.001), pbr("String", (0.75, 0.7, 0.6), 0.8))
                c["tags"].append((tag, tag.location.copy()))
        h = officer("Counter", 46, seed=3); c["counter"] = h
        c["held_tag"] = box("HeldTag", (0, 0, -20), (0.05, 0.032, 0.002), tagm)
    else:
        for k, p in enumerate(grid):
            stand_obj("Stand", p, smat)
        mid = grid[(NX // 2) * NY + 1]
        c["hero_at"] = mid
        dd.ring("HeroRing", mid + Vector((0, 0, 0.045)), stone_r=0.0105, band="plat", band_r=0.0105)
        # motes in the lamp light (slowly drifting, frame-driven)
        hz = box("Motes", (0, 0, 1.6), (TL, 3, 1.6))
        m = bpy.data.materials.new("Motes"); m.use_nodes = True
        N = m.node_tree.nodes; L = m.node_tree.links; N.clear()
        out = N.new("ShaderNodeOutputMaterial"); vol = N.new("ShaderNodeVolumePrincipled"); vol.inputs['Density'].default_value = 0.02
        L.new(vol.outputs[0], out.inputs['Volume']); hz.data.materials.append(m); hz.visible_shadow = False
    # lighting: a long softbox over the table and two practical lamp pools
    a = bpy.data.lights.new("Soft", 'AREA'); a.shape = 'RECTANGLE'; a.size = TL; a.size_y = 1.2; a.energy = 420 if v == "count" else 140; a.color = (0.95, 0.97, 1.0)
    ao = bpy.data.objects.new("Soft", a); bpy.context.collection.objects.link(ao); ao.location = (0, 0, 2.8)
    box("Tube", (0, 0, 2.9), (TL, 0.15, 0.04), emissive("TubeE", (0.9, 0.95, 1.0), 6))
    k = bpy.data.lights.new("Key", 'SPOT'); k.energy = 260; k.spot_size = math.radians(40); k.spot_blend = 0.6; k.color = (1.0, 0.9, 0.75)
    ko = bpy.data.objects.new("Key", k); bpy.context.collection.objects.link(ko); c["key"] = ko
    return c


def anim_layout(c, t):
    sec = t * DUR["layout"]
    h = c["counter"]
    walk_to(h, Vector((-TL / 2 - 0.3, -TW / 2 - 0.55, 0)), Vector((TL / 2, -TW / 2 - 0.55, 0)), sec, speed=0.5, cadence=1.1)
    arms_relaxed(h)
    h.rot("neck01", (1, 0, 0), 10); h.rot("head", (1, 0, 0), 16)
    from human import reach
    beat = (sec % 2.2) / 2.2                                   # every 2.2 s a tag goes down on the cloth
    down = math.sin(math.pi * min(1.0, beat / 0.5)) if beat < 0.5 else 0.0
    if down > 0.01:
        sh = h.bone_head("upperarm01.L")
        tgt = Vector((h.arm.location.x + 0.15, -TW / 2 + 0.25, TZ + 0.04))
        reach(h, "L", sh.lerp(tgt, 0.35 + 0.65 * down), Vector((0.5, -0.3, -0.8)))
        if "held_tag" in c:
            c["held_tag"].location = h.bone_tail("wrist.L") + Vector((0, 0, -0.03))
    c["key"].location = (-3 + 6 * t, -1.5, 2.6); point_at(c["key"], (-2 + 6 * t, 0, TZ))


def anim_layout_only(c, t):
    anim_layout(c, t)
    c["counter"].arm.location.z = -60          # nobody in the overhead: just the rows of pieces


def anim_tags(c, t):
    anim_layout(c, t)
    hx = c["counter"].arm.location.x
    for tg, home in c["tags"]:
        tg.location = home if home.x < hx - 0.1 else Vector((0, 0, -20))


def anim_final(c, t):
    m = c["hero_at"]
    c["key"].location = m + Vector((-1.2 + 0.6 * t, -1.0, 1.6)); point_at(c["key"], m)


MOVES = {
    "layout": dict(kind="anim", dof=2.8, anim=anim_layout_only,
                   cam=lambda c, t: (Vector((-TL / 2 - 0.4 + 1.4 * ease(t), -0.9, 1.35)), Vector((-TL / 2 + 1.4 + 1.4 * ease(t), 0.05, TZ)), 40),
                   focus=lambda c, t: Vector((-TL / 2 + 1.0 + 1.4 * ease(t), 0.0, TZ))),
    "tags": dict(kind="anim", dof=5.6, anim=anim_tags,
                 cam=lambda c, t: (Vector((-1.0 + 1.5 * ease(t), 3.4, 2.9)), Vector((0.2 + 1.5 * ease(t), -0.9, 0.7)), 26),
                 focus=lambda c, t: c["counter"].arm.location + Vector((0, 0, 1.0))),
    "alone": dict(kind="anim", dof=2.0, anim=anim_final,
                  cam=lambda c, t: (c["hero_at"] + Vector((0.0, -0.12, 0.09)).lerp(Vector((0.0, -0.55, 0.32)), ease(t)), c["hero_at"] + Vector((0, 0, 0.05)), 60),
                  focus=lambda c, t: c["hero_at"] + Vector((0, 0, 0.05))),
    "empty": dict(kind="anim", dof=4.0, anim=anim_final,
                  cam=lambda c, t: (c["hero_at"] + Vector((0.4, -1.2, 0.7)).lerp(Vector((1.6, -3.4, 2.0)), ease(t)), c["hero_at"] + Vector((-0.3, 0.2, 0.0)), 35),
                  focus=lambda c, t: c["hero_at"]),
}
