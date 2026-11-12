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


def velvet_cloth(name="VelvetCloth"):
    """Black velvet over the table: a softly rippled top and a skirt hanging on all four sides in loose folds."""
    import bmesh
    bm = bmesh.new()
    def patch(fn, nu, nv):
        vs = [[bm.verts.new(fn(u / nu, v / nv)) for v in range(nv + 1)] for u in range(nu + 1)]
        for u in range(nu):
            for v in range(nv):
                bm.faces.new((vs[u][v], vs[u + 1][v], vs[u + 1][v + 1], vs[u][v + 1]))
    X, Y, drop = TL / 2 + 0.1, TW / 2 + 0.1, 0.62
    patch(lambda u, v: Vector((-X + 2 * X * u, -Y + 2 * Y * v, TZ + 0.002 * math.sin(u * 37) * math.sin(v * 11))), 140, 30)
    for sy in (-1, 1):                       # long sides
        patch(lambda u, v, sy=sy: Vector((-X + 2 * X * u, sy * (Y + 0.01 + v * 0.03 + 0.03 * v * math.sin(u * 2 * X * 9 + sy)), TZ - drop * v)), 160, 10)
    for sx in (-1, 1):                       # ends
        patch(lambda u, v, sx=sx: Vector((sx * (X + 0.01 + v * 0.03 + 0.03 * v * math.sin(u * 2 * Y * 9 + sx)), -Y + 2 * Y * u, TZ - drop * v)), 40, 10)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for f in me.polygons:
        f.use_smooth = True
    me.materials.append(dd.black_velvet())
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o)
    return o


def stand_obj(name, loc, mat):
    o = cyl(name, loc + Vector((0, 0, 0.015)), 0.022, 0.03, mat, verts=20)
    return o


def build(variant=None):
    c = {}
    v = variant or "count"
    world_flat((0.004, 0.005, 0.007), 1.0)
    rng = np.random.default_rng(41)
    B = dd.Builder("EvidenceRoom")
    B.box((0, 0, -0.05), (16, 10, 0.1), dd.tex_mat("concrete_floor_02", 0.6, tint=(0.5, 0.5, 0.5), name="ERFloor", sat=0.3))
    wall = pbr("ERWall", (0.16, 0.17, 0.18), 0.8)
    B.box((0, 4.0, 1.5), (16, 0.1, 3.0), wall).box((-7.5, 0, 1.5), (0.1, 10, 3.0), wall)
    B.box((0, -4.6, 1.5), (16, 0.1, 3.0), wall).box((7.5, 0, 1.5), (0.1, 10, 3.0), wall).box((0, 0, 3.05), (16, 10, 0.1), wall)
    B.box((0, 0, TZ - 0.025), (TL, TW, 0.04), pbr("TableTop", (0.1, 0.08, 0.06), 0.6))
    for sx in (-1, 1):
        for sy in (-1, 1):
            B.box((sx * TL / 2, sy * TW / 2, TZ / 2), (0.05, 0.05, TZ), pbr("Leg", (0.3, 0.3, 0.32), 0.4, 0.8))
    B.done()
    velvet_cloth()
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
        cone_m = dd.black_velvet()
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
        # the closing image: rows of EMPTY displays on black velvet (ring cones, necklace busts, earring T-bars), a few
        # with evidence tags; one small cluster of recovered pieces at the far end; the big diamond alone on its cone
        vel = dd.black_velvet(); M = dd.jewel_mats()
        D = dd.Builder("EmptyDisplays")
        rod = pbr("StandRod", (0.55, 0.55, 0.57), 0.3, 1.0)
        mid_i, mid_j = NX // 2, 1
        for i in range(NX):
            for j in range(NY):
                p = grid[i * NY + j]
                if (i, j) == (mid_i, mid_j):
                    continue
                kind = (i + 2 * j) % 3
                recovered = i <= 1
                if kind == 0:                                        # ring cone (rounded tip)
                    D.cone(p + Vector((0, 0, 0.022)), 0.022, 0.01, 0.044, vel, verts=24)
                    D.cyl(p + Vector((0, 0, 0.046)), 0.01, 0.004, vel, verts=16)
                    if recovered:
                        dd.ring(f"Rec{i}_{j}", p + Vector((0, 0, 0.0565)), stone_r=float(rng.uniform(0.005, 0.007)),
                                band="gold" if j % 2 else "plat", stone=("sapphire", "diamond", "ruby", "diamond")[j % 4])
                elif kind == 1:                                      # necklace bust
                    D.cone(p + Vector((0, 0, 0.09)), 0.065, 0.024, 0.18, vel, verts=24, scale=(0.6, 1.0, 1.0))
                    D.cyl(p + Vector((0, 0, 0.19)), 0.022, 0.025, vel, verts=16)
                    if recovered:
                        for q in range(22):
                            a_ = math.pi * q / 21
                            cyl(f"RecN{i}{j}", p + Vector((0.036 * math.cos(a_), -0.014 - 0.032 * math.sin(a_), 0.16 - 0.055 * math.sin(a_))),
                                0.003, 0.004, M["plat"], verts=8)
                        dd.earring(f"RecP{i}{j}", p + Vector((0, -0.05, 0.1)), 0.007, "diamond")
                else:                                                # earring tree: rod, two crossbars
                    D.cyl(p + Vector((0, 0, 0.003)), 0.026, 0.006, vel, verts=20)
                    D.cyl(p + Vector((0, 0, 0.075)), 0.003, 0.14, rod, verts=8)
                    for zb, wb in ((0.145, 0.08), (0.1, 0.06)):
                        D.box(p + Vector((0, 0, zb)), (wb, 0.005, 0.005), rod)
                    if recovered:
                        for zb, wb in ((0.13, 0.035), (0.085, 0.026)):
                            for sx in (-wb, wb):
                                dd.earring(f"RecE{i}{j}{sx}{zb}", p + Vector((sx, 0, zb)), 0.005, ("diamond", "sapphire")[j % 2])
                if abs(i - mid_i) > 2:          # a small paper tag on a string for each stand
                    D.box(p + Vector((0.02, -0.1, 0.002)), (0.045, 0.028, 0.002), tagm, rot=(0, 0, 0.1 * float(rng.uniform(-1, 1))))
                    D.box(p + Vector((0.01, -0.06, 0.002)), (0.002, 0.05, 0.001), pbr("String", (0.75, 0.7, 0.6), 0.8), rot=(0, 0, 0.3))
        D.done()
        mid = grid[mid_i * NY + mid_j]
        c["hero_at"] = mid
        bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=0.03, radius2=0.009, depth=0.08, location=mid + Vector((0, 0, 0.04)))
        bpy.context.active_object.data.materials.append(vel)
        dd.ring("HeroRing", mid + Vector((0, 0, 0.08 + 0.0105 - 0.003)), stone_r=0.0105, band="plat", band_r=0.0105)
        sp = bpy.data.lights.new("Sparkle", 'POINT'); sp.energy = 6; sp.shadow_soft_size = 0.005; sp.color = (0.95, 0.97, 1.0)
        so = bpy.data.objects.new("Sparkle", sp); bpy.context.collection.objects.link(so); so.location = mid + Vector((0.25, -0.2, 0.45))
        # motes in the lamp light (slowly drifting, frame-driven)
        hz = box("Motes", (0, 0, 1.6), (TL, 3, 1.6))
        m = bpy.data.materials.new("Motes"); m.use_nodes = True
        N = m.node_tree.nodes; L = m.node_tree.links; N.clear()
        out = N.new("ShaderNodeOutputMaterial"); vol = N.new("ShaderNodeVolumePrincipled"); vol.inputs['Density'].default_value = 0.02
        L.new(vol.outputs[0], out.inputs['Volume']); hz.data.materials.append(m); hz.visible_shadow = False
    # lighting: a long softbox over the table and two practical lamp pools
    a = bpy.data.lights.new("Soft", 'AREA'); a.shape = 'RECTANGLE'; a.size = TL; a.size_y = 1.2; a.energy = 420 if v == "count" else 50; a.color = (0.82, 0.9, 1.0)
    ao = bpy.data.objects.new("Soft", a); bpy.context.collection.objects.link(ao); ao.location = (0, 0, 2.8)
    box("Tube", (0, 0, 2.9), (TL, 0.15, 0.04), emissive("TubeE", (0.9, 0.95, 1.0), 6))
    if v != "count":
        ct = bpy.data.lights.new("CoolTop", 'SPOT'); ct.energy = 1600; ct.spot_size = math.radians(110); ct.spot_blend = 1.0
        ct.color = (0.8, 0.88, 1.0); ct.shadow_soft_size = 0.6
        cto = bpy.data.objects.new("CoolTop", ct); bpy.context.collection.objects.link(cto); cto.location = (-2.2, 0, 2.7); point_at(cto, (-0.5, 0, TZ))
    if v == "count":                           # small hard glints so the stones sparkle at the low angle
        for q in range(4):
            gl_ = bpy.data.lights.new("Glint", 'POINT'); gl_.energy = 30; gl_.shadow_soft_size = 0.01; gl_.color = (1.0, 0.97, 0.92)
            go = bpy.data.objects.new("Glint", gl_); bpy.context.collection.objects.link(go); go.location = (-3.0 + q * 2.0, 0.9, 1.6)
    k = bpy.data.lights.new("Key", 'SPOT'); k.energy = 260; k.spot_size = math.radians(40); k.spot_blend = 0.6; k.color = (1.0, 0.9, 0.75)
    ko = bpy.data.objects.new("Key", k); bpy.context.collection.objects.link(ko); c["key"] = ko
    return c


def anim_layout(c, t):
    sec = t * DUR["layout"]
    h = c["counter"]
    walk_to(h, Vector((-TL / 2 - 0.3, -TW / 2 - 0.32, 0)), Vector((TL / 2, -TW / 2 - 0.32, 0)), sec, speed=0.5, cadence=1.1)
    h.rot("neck01", (1, 0, 0), -10); h.rot("head", (1, 0, 0), -12)        # natural walk, eyes on the rows as he goes
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
                   cam=lambda c, t: (Vector((-TL / 2 - 0.4 + 1.4 * ease(t), -0.95, 1.0)), Vector((-TL / 2 + 1.8 + 1.4 * ease(t), 0.1, TZ + 0.02)), 40),
                   focus=lambda c, t: Vector((-TL / 2 + 1.0 + 1.4 * ease(t), 0.0, TZ))),
    "tags": dict(kind="anim", dof=5.6, anim=anim_tags,
                 cam=lambda c, t: (Vector((c["counter"].arm.location.x - 1.8, 2.3, 1.95)), Vector((c["counter"].arm.location.x + 0.4, -0.7, 1.0)), 30),
                 focus=lambda c, t: c["counter"].arm.location + Vector((0, 0, 1.0))),
    "alone": dict(kind="anim", dof=2.0, anim=anim_final,
                  cam=lambda c, t: (c["hero_at"] + Vector((0.0, -0.16, 0.12)).lerp(Vector((0.0, -0.55, 0.3)), ease(t)), c["hero_at"] + Vector((0, 0, 0.085)), 70),
                  focus=lambda c, t: c["hero_at"] + Vector((0, 0, 0.09))),
    "empty": dict(kind="anim", dof=5.6, anim=anim_final,
                  cam=lambda c, t: (Vector((-TL / 2 - 0.35, -0.08, TZ + 0.16)).lerp(Vector((-TL / 2 - 1.7, -0.2, TZ + 0.42)), ease(t)), Vector((TL / 2, 0.1, TZ + 0.02)), 40),
                  focus=lambda c, t: Vector((-TL / 2 + 0.45, 0.0, TZ + 0.06))),
}
