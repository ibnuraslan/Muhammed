"""Dramatization: night, a high-floor suite. A man in a black leather jacket sits on the edge of the bed, elbows on
knees, phone in both hands; we look over his shoulder at the screen. City lights through the window behind.
The phone screen renders as a soft glow; the email UI is pinned onto it in post (corners saved with the plate)."""
import os, json, math
import numpy as np
import bpy
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view
from kit import *
from human import Human, add_asset, pose_sit, fingers_curl, rotate_bone, aim_bone, _world_verts

EXPOSURE = 0.6
VARIANT_FOR = {}


def build(variant=None):
    world_flat((0.004, 0.005, 0.008), 1.0)
    floor = box("Floor", (0, 0, -0.01), (10, 10, 0.02), wood("Oak", (0.03, 0.018, 0.01), (0.08, 0.045, 0.025), scale=(0.6, 8, 8), rough=0.3, coat=0.4))
    wall = pbr("Wall", (0.06, 0.055, 0.05), 0.8)
    box("BackWall", (0, 3.0, 1.5), (10, 0.05, 3.0), wall)
    box("SideWall", (-3.0, 0, 1.5), (0.05, 10, 3.0), wall)
    box("Ceiling", (0, 0, 3.0), (10, 10, 0.05), pbr("Ceil", (0.05, 0.05, 0.05), 0.9))
    # bed: frame, mattress, rumpled duvet (subdivided, displaced), pillows
    linen = fabric("Linen", (0.55, 0.53, 0.5), 0.9, 0.5, 600)
    box("BedFrame", (0.2, 1.6, 0.18), (1.9, 2.2, 0.36), pbr("BedFrame", (0.02, 0.018, 0.016), 0.5), bevel=0.02)
    box("Mattress", (0.2, 1.6, 0.47), (1.8, 2.1, 0.22), linen, bevel=0.06)
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=80, y_subdivisions=80, size=1, location=(0.2, 1.45, 0.6))
    duv = bpy.context.active_object; duv.scale = (2.0, 1.9, 1)
    tex = bpy.data.textures.new("Rumple", 'CLOUDS'); tex.noise_scale = 0.35; tex.noise_depth = 3
    d = duv.modifiers.new("d", 'DISPLACE'); d.texture = tex; d.strength = 0.09
    sol = duv.modifiers.new("s", 'SOLIDIFY'); sol.thickness = 0.04
    sub = duv.modifiers.new("sub", 'SUBSURF'); sub.levels = 1; sub.render_levels = 2
    duv.data.materials.append(fabric("Duvet", (0.6, 0.6, 0.58), 0.85, 0.6, 500)); bpy.ops.object.shade_smooth()
    for x in (-0.3, 0.7):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=0.3, location=(x, 2.45, 0.68))
        p = bpy.context.active_object; p.scale = (1.2, 0.5, 0.35); p.data.materials.append(linen); bpy.ops.object.shade_smooth()
    # bedside table + unlit lamp + a glass of water catching the phone glow
    box("Nightstand", (-1.15, 2.1, 0.28), (0.5, 0.45, 0.56), wood("Night", (0.02, 0.012, 0.008), (0.06, 0.035, 0.02), rough=0.3), bevel=0.01)
    cyl("LampBase", (-1.15, 2.15, 0.7), 0.07, 0.28, pbr("Brass", (0.6, 0.45, 0.25), 0.3, 1.0))
    cyl("LampShade", (-1.15, 2.15, 0.95), 0.17, 0.25, pbr("Shade", (0.4, 0.38, 0.34), 0.8))
    g = cyl("Water", (-1.0, 1.98, 0.62), 0.035, 0.12, glass("Tumbler", (0.96, 0.98, 0.99)), verts=32)
    # window wall to the right of frame with the city far below
    box("WindowGlass", (2.6, 0.5, 1.5), (0.02, 6, 3.0), glass("Win", (0.9, 0.94, 0.96), 0.01))
    for k in range(5):
        box("Mullion", (2.6, -2.0 + k * 1.25, 1.5), (0.05, 0.05, 3.0), pbr("Mull", (0.02, 0.02, 0.02), 0.4, 0.6))
    win = window_material("CityWin", lit=(1.0, 0.82, 0.55), density=0.22, floor=3.6, bay=1.6, strength=0.9)
    skyline(77, (260, 0, 0), (140, 300), 120, (30, 200), None, win, footprint=(20, 50), z0=-120)
    box("CityFloor", (300, 0, -121), (600, 800, 1), window_material("Street", lit=(1.0, 0.7, 0.4), density=0.06, floor=30, bay=30, strength=0.8))
    # cold moonlight through the window, very low warm bounce
    moon = area_light((3.2, 0.5, 2.2), (0, 0, 0), 2.0, 70, (0.45, 0.6, 1.0)); point_at(moon, (0.2, 0.6, 0.6))
    rim = area_light((-0.6, 2.8, 1.8), (0, 0, 0), 1.0, 12, (1.0, 0.75, 0.5)); point_at(rim, (0.2, 0.7, 1.0))   # warm city spill behind him

    # ------------------------------------------------------------------ the man
    h = Human("Man", gender=1.0, years=62, muscle=0.5, weight=0.5, height=0.42,
              skin="old_lightskinned_male_diffuse.png", eyebrows="eyebrow002", eyelashes="eyelashes01")
    jacket = add_asset(h, "clothes", "male_casualsuit05", hue=0.5, sat=0.15, val=0.12, rough=0.38, sheen=0.1)
    m = jacket.data.materials[0]; pb = m.node_tree.nodes["Principled BSDF"]
    pb.inputs['Coat Weight'].default_value = 0.6; pb.inputs['Coat Roughness'].default_value = 0.25      # leather sheen
    add_asset(h, "clothes", "shoes02", val=0.2, rough=0.35)
    add_asset(h, "hair", "short02", sat=0.0, val=0.75, rough=0.45)
    pose_sit(h, lean=26)
    sk = h.skin_mat.node_tree.nodes["Principled BSDF"]
    sk.inputs['Subsurface Weight'].default_value = 0.08; sk.inputs['Subsurface Radius'].default_value = (0.5, 0.25, 0.15)
    # forearms in toward the centre so both hands meet around the phone
    for sd, sg in (("L", 1), ("R", -1)):
        aim_bone(h.arm, f"lowerarm01.{sd}", (-0.55 * sg, -0.75, 0.25)); aim_bone(h.arm, f"lowerarm02.{sd}", (-0.55 * sg, -0.75, 0.25))
        aim_bone(h.arm, f"wrist.{sd}", (-0.3 * sg, -0.6, 0.6))
    fingers_curl(h, 40, thumb=10)
    rotate_bone(h.arm, "head", (1, 0, 0), 14)
    h.arm.location = (0.25, 0.75, 0.0)           # on the edge of the bed (bed edge at y ~ 0.55)
    bpy.context.view_layer.update()
    w = np.concatenate([_world_verts(o) for o in h.parts if o.type == 'MESH'])
    h.arm.location.z -= w[:, 2].min()
    bpy.context.view_layer.update()
    # the phone between the hands, screen up toward his face
    hl, hr = h.bone_tail("wrist.L"), h.bone_tail("wrist.R")
    c = (hl + hr) / 2 + Vector((0, -0.05, 0.075))      # held by its lower edge, above the fingers
    eye = (h.eyes[0].matrix_world.to_translation() + h.eyes[1].matrix_world.to_translation()) / 2
    phone = box("Phone", c, (0.072, 0.152, 0.008), pbr("PhoneBody", (0.02, 0.02, 0.022), 0.25, 0.8), bevel=0.006)
    to_eye = (eye - c).normalized()
    phone.rotation_euler = to_eye.to_track_quat('Z', 'Y').to_euler()
    bpy.context.view_layer.update()
    screen = box("Screen", c + to_eye * 0.0045, (0.066, 0.144, 0.0005), emissive("ScreenGlow", (0.85, 0.9, 1.0), 2.5))
    screen.rotation_euler = phone.rotation_euler
    sl = bpy.data.lights.new("ScreenLight", 'AREA'); sl.energy = 3.0; sl.size = 0.07; sl.color = (0.8, 0.88, 1.0)
    so = bpy.data.objects.new("ScreenLight", sl); bpy.context.collection.objects.link(so)
    so.location = c + to_eye * 0.01; so.rotation_euler = phone.rotation_euler
    bpy.context.view_layer.update()
    return dict(h=h, phone=phone, screen=screen, c=c, eye=eye)


def screen_corners(ctx, scene, cam):
    """Screen-space corners (u, v from top-left) of the phone display, for pinning the UI in post."""
    o = ctx["screen"]; bpy.context.view_layer.update()
    M = o.matrix_world
    out = []
    for (x, y) in ((-1, 1), (1, 1), (1, -1), (-1, -1)):     # TL, TR, BR, BL in the phone's own frame (y up the screen)
        p = M @ Vector((x * 0.033, y * 0.072, 0.0003))
        v = world_to_camera_view(scene, cam, p)
        out.append((v.x, 1 - v.y))
    return out


def _over_shoulder(c, t):
    sh = c["h"].bone_head("upperarm01.R")
    cam = sh + Vector((-0.16, 0.24, 0.36)) + Vector((0.02, -0.06, -0.05)) * t      # over his right shoulder
    return (cam, c["c"], 50)


MOVES = {
    "over_shoulder": dict(kind="plate", dof=2.0, far=6.0, cam=_over_shoulder, focus=lambda c, t: c["c"]),
}
