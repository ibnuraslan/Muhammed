"""Empty boardroom at night: long walnut table, leather chairs, glass wall to a city skyline, one folder."""
import os, math
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
    ctx = dict(folder=Vector((0.15, 1.2, 0.78)), head=Vector((0, 3.55, 0.9)))
    if variant == "board":
        bpy.data.objects["Folder"].hide_render = True; bpy.data.objects["Paper"].hide_render = True
        from human import Human, add_asset, pose_sit, aim_bone, fingers_curl, rotate_bone, _world_verts
        members = []
        seats = [(-1.05, -1.5, 1), (-1.05, -0.5, 0), (-1.05, 0.5, 1), (1.05, -1.0, 0), (1.05, 0.0, 1), (1.05, 1.0, 1)]
        for k, (x, y, g) in enumerate(seats):
            h = Human(f"Member{k}", gender=g, years=55 + 3 * k, muscle=0.45, weight=0.5, height=0.45, eyelashes=None)
            add_asset(h, "clothes", "male_elegantsuit01" if g else "female_elegantsuit01", val=0.35, rough=0.6)
            add_asset(h, "hair", ["short02", "short04", "short01"][k % 3] if g else "bob02", sat=0.2, val=0.45 + 0.1 * (k % 3))
            pose_sit(h, lean=6)
            for sd, sg in (("L", 1), ("R", -1)):
                aim_bone(h.arm, f"upperarm01.{sd}", (0.1 * sg, -0.4, -0.9)); aim_bone(h.arm, f"lowerarm01.{sd}", (-0.3 * sg, -0.95, 0.05))
            fingers_curl(h, 30)
            rotate_bone(h.arm, "head", (0, 0, 1), 25 if x < 0 else -25)          # heads turned toward the head of the table
            h.arm.rotation_euler = (0, 0, -math.pi / 2 if x < 0 else math.pi / 2)  # facing the table
            h.arm.location = (x * 1.02, y, 0); bpy.context.view_layer.update()
            w = np.concatenate([_world_verts(o) for o in h.parts if o.type == 'MESH'])
            h.arm.location.z -= w[:, 2].min() - 0.0; bpy.context.view_layer.update()
            members.append(h)
        # the folder with its cover, slid along the table toward the head chair
        cover = bpy.data.materials.new("Cover"); cover.use_nodes = True
        N = cover.node_tree.nodes; L = cover.node_tree.links; t_ = N.new("ShaderNodeTexImage")
        t_.image = bpy.data.images.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "generated", "folder_cover.png"))
        L.new(t_.outputs['Color'], N["Principled BSDF"].inputs['Base Color']); N["Principled BSDF"].inputs['Roughness'].default_value = 0.7
        bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0.778))
        f = bpy.context.active_object; f.name = "Dossier"; f.scale = (0.24, 0.32, 1); f.data.materials.append(cover)
        body = box("DossierBody", (0, 0, 0.7735), (0.24, 0.32, 0.008), pbr("Manila", (0.45, 0.33, 0.18), 0.75))
        ctx["dossier"] = f; ctx["dossier_body"] = body; ctx["members"] = members
    return ctx


def _slide(c, t):
    f = c["dossier"]; e = 1 - (1 - min(1.0, t * 1.4)) ** 3        # decelerating slide
    f.location = Vector((0.1, -1.6, 0.778)).lerp(Vector((0.0, 2.55, 0.778)), e)
    f.rotation_euler = (0, 0, 0.5 * (1 - e) + 0.05)
    b = c["dossier_body"]; b.location = (f.location.x, f.location.y, 0.7735); b.rotation_euler = f.rotation_euler


VARIANT_FOR = {"board_slide": "board"}
MOVES = {
    "board_slide": dict(kind="anim", dof=5.6, far=40.0,
                        cam=lambda c, t: (Vector((0.5, -3.6, 1.5)).lerp(Vector((0.15, 1.75, 1.22)), ease(t)),
                                          Vector((0, 2.6, 0.85)).lerp(Vector((0.0, 2.55, 0.78)), ease(t)), 35 + 10 * ease(t)),
                        focus=lambda c, t: c["dossier"].location, anim=_slide),
    "slow_push": dict(kind="plate", dof=2.8, far=40.0, cam=lambda c, t: ((0.6, -3.8, 1.35), (0, 3.0, 0.95), 32), focus=lambda c, t: (0, 1.0, 0.8)),
    "empty_chair": dict(kind="plate", dof=2.8, far=40.0, cam=lambda c, t: ((0.35, 0.6, 1.05), c["head"], 50), focus=lambda c, t: c["head"]),
    "dossier": dict(kind="plate", dof=2.4, far=40.0, cam=lambda c, t: ((0.6, 0.55, 1.2), c["folder"], 45), focus=lambda c, t: c["folder"]),
}
