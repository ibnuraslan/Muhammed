"""GYM: a quiet suburban boxing gym: brick walls, rubber floor, heavy bags on chains, a ring rope corner, lockers.
  bag     (ch3 2A): track past the punching bags as a man works a heavy bag
  lockers (ch3 2B): two men talk by the lockers while a third walks over to join them (wide)
"""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
import dd
from dd import person, place, face_to, walk_to, arms_relaxed, zero, ground
from human import reach, pose_walk

EXPOSURE = 0.0
DUR = {"bag": 9.0, "lockers": 9.0}
BAGS = [Vector((-3.2 + k * 1.6, 3.0, 0)) for k in range(5)] + [Vector((-2.4 + k * 1.6, 5.2, 0)) for k in range(4)]


def heavy_bag(name):
    leather = dd.tex_mat("brown_leather", 1.5, tint=(0.4, 0.15, 0.1), name="BagLeather", sat=0.8)
    leather.node_tree.nodes["Principled BSDF"].inputs['Coat Weight'].default_value = 0.3
    Bd = dd.Builder(name)
    Bd.cyl((0, 0, -0.75), 0.17, 1.0, leather, verts=24).cyl((0, 0, -0.24), 0.15, 0.04, leather, verts=24).cyl((0, 0, -1.26), 0.15, 0.04, leather, verts=24)
    for k in range(4):
        Bd.cyl((0, 0, 0.1 - k * 0.09), 0.012, 0.08, pbr("Chain", (0.5, 0.5, 0.52), 0.3, 1.0), verts=6)
    o = Bd.done(); bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
    bpy.ops.object.shade_smooth()
    return o


def build(variant=None):
    c = {}
    world_flat((0.06, 0.06, 0.07), 1.0)
    B = dd.Builder("Gym")
    B.box((0, 3, -0.05), (12, 10, 0.1), dd.tex_mat("rubber_tiles", 0.8, tint=(0.35, 0.35, 0.36), name="GymFloor", sat=0.3))
    brick = dd.tex_mat("painted_brick", 0.8, tint=(0.8, 0.8, 0.78), name="GymBrick", sat=0.5)
    B.box((0, 8.05, 2.0), (12, 0.1, 4.0), brick).box((-6.05, 3, 2.0), (0.1, 10, 4.0), brick).box((6.05, 3, 2.0), (0.1, 10, 4.0), brick)
    B.box((0, 3, 4.05), (12, 10, 0.1), pbr("GymCeil", (0.25, 0.25, 0.26), 0.8))
    for k in range(4):                                                     # steel beam carrying the bags
        B.box((0, 3.0, 3.6), (8.0, 0.15, 0.2), pbr("Beam", (0.12, 0.13, 0.14), 0.5, 0.8))
    # lockers along the right wall, a bench in front
    lk = pbr("Locker", (0.32, 0.38, 0.42), 0.45, 0.6)
    for k in range(10):
        B.box((5.8, 0.5 + k * 0.42, 0.95), (0.45, 0.4, 1.9), lk)
        B.box((5.56, 0.5 + k * 0.42, 1.5), (0.01, 0.2, 0.2), pbr("Vent", (0.1, 0.1, 0.1), 0.6))
        B.box((5.56, 0.65 + k * 0.42, 1.05), (0.02, 0.03, 0.12), pbr("LHandle", (0.6, 0.6, 0.6), 0.3, 1.0))
    B.box((4.9, 2.4, 0.45), (0.4, 3.0, 0.06), dd.tex_mat("oak_veneer_01", 1.0, name="BenchW"))
    # a ring corner on the left
    B.box((-4.5, 6.2, 0.5), (3.0, 3.0, 1.0), pbr("RingApron", (0.1, 0.12, 0.25), 0.7))
    for z in (1.4, 1.75, 2.1):
        B.box((-4.5, 4.75, z), (3.0, 0.05, 0.05), pbr("Rope", (0.6, 0.05, 0.04), 0.7)).box((-3.05, 6.2, z), (0.05, 3.0, 0.05), pbr("Rope", (0.6, 0.05, 0.04), 0.7))
    B.cyl((-3.0, 4.7, 1.6), 0.06, 1.3, pbr("Post", (0.6, 0.6, 0.62), 0.3, 0.9), verts=12)
    B.done()
    c["bags"] = []
    for k, p in enumerate(BAGS):
        b = heavy_bag(f"Heavy{k}"); b.location = p + Vector((0, 0, 1.95)); c["bags"].append(b)
        ch = cyl(f"Chain{k}", p + Vector((0, 0, 2.75)), 0.008, 1.6, pbr("ChainL", (0.5, 0.5, 0.52), 0.3, 1.0), verts=6); ch.parent = b
        ch.location = (0, 0, 0.8)
    for x in (-4.0, -1.3, 1.3, 4.0):
        for y in (1.2, 4.6):
            flick = "1.0 - 0.35 * max(0, sin(frame * 0.9 + %d) - 0.92) * 12" % int(x * 7 + y)      # a slight, irregular flicker
            tm = bpy.data.materials.new("GymTube"); tm.use_nodes = True
            N = tm.node_tree.nodes; L = tm.node_tree.links; N.clear()
            out = N.new("ShaderNodeOutputMaterial"); em = N.new("ShaderNodeEmission"); em.inputs['Color'].default_value = (0.92, 0.96, 1.0, 1)
            fv = dd.frame_value(N, "6 * (%s)" % flick, "Flicker"); L.new(fv.outputs[0], em.inputs['Strength']); L.new(em.outputs[0], out.inputs['Surface'])
            box("GymTube", (x, y, 3.97), (0.12, 1.3, 0.04), tm)
            a = bpy.data.lights.new("GymL", 'AREA'); a.shape = 'RECTANGLE'; a.size = 0.2; a.size_y = 1.3; a.color = (0.92, 0.96, 1.0)
            d = a.driver_add("energy").driver; d.type = 'SCRIPTED'; d.expression = "200 * (%s)" % flick
            o = bpy.data.objects.new("GymL", a); bpy.context.collection.objects.link(o); o.location = (x, y, 3.9)
    # a mirror wall, mats, a weight rack with dumbbells
    box("Mirror", (-5.98, 3.0, 1.4), (0.02, 6.0, 2.0), pbr("MirrorM", (0.9, 0.9, 0.9), 0.02, 1.0))
    box("MirrorFrame", (-5.99, 3.0, 2.42), (0.03, 6.1, 0.05), pbr("MirFrame", (0.2, 0.2, 0.2), 0.4, 0.8))
    for k in range(3):
        box("Mat", (-1.0 + k * 1.3, 0.2, 0.012), (1.2, 2.0, 0.025), pbr("MatM", (0.08, 0.1, 0.16), 0.8))
    dd.model_h("steel_frame_shelves_03", (2.6, 7.5, 0), 1.2, rot_z=math.pi)
    for k in range(10):
        cyl("Dumbbell", (2.0 + 0.13 * k, 7.5, 0.25 + 0.4 * (k % 2)), 0.04, 0.24, pbr("DBM", (0.08, 0.08, 0.09), 0.4, 0.7), verts=12,
            rot=(math.radians(90), 0, 0))
    # a high window strip with grey daylight
    box("HighWin", (0, 8.0, 3.3), (8, 0.02, 0.5), emissive("Daylight", (0.75, 0.8, 0.9), 2.0))
    dd.model_h("metal_trash_can", (-5.5, 1.0, 0), 0.7)
    dd.model_h("plastic_bottle_gallon", (5.0, 3.6, 0.48), 0.3)
    c["boxer"] = person("Boxer", 1.0, 31, "male_casualsuit01", "short01", cval=1.2, tint=(0.6, 0.6, 0.62), sat=0.2)
    c["talk"] = [person("TalkA", 1.0, 42, "male_casualsuit05", "short02", cval=1.3, tint=(0.8, 0.75, 0.7)),
                 person("TalkB", 1.0, 36, "male_casualsuit03", "short04", cval=1.1)]
    c["joiner"] = person("Joiner", 1.0, 39, "male_casualsuit01", "short03", cval=1.0)
    # 3-4 people training in the background: two on bags, one skipping-in-place stance, one on a mat
    c["trainees"] = []
    for k, (cl, hr, tn) in enumerate((("male_casualsuit01", "short04", (0.5, 0.5, 0.5)), ("male_casualsuit03", "short01", (0.8, 0.8, 0.85)),
                                      ("female_elegantsuit01", "ponytail01", (0.25, 0.25, 0.28)), ("male_casualsuit03", "short02", (1, 1, 1)))):
        c["trainees"].append(person(f"Train{k}", 0.0 if k == 2 else 1.0, 24 + 5 * k, cl, hr, cval=1.1, tint=tn, sat=0.4))
    return c


def anim_trainees(c, sec):
    from human import reach as _reach
    for k, h in enumerate(c["trainees"]):
        if k < 2:                                             # working a bag in the back row
            bag = BAGS[6 + k]; sp = bag + Vector((0.0, -0.7, 0))
            zero(h); pose_walk(h, 0.0, stride=0.0, arm_swing=0.0); place(h, sp, face_to(sp, bag))
            M = h.arm.matrix_world.to_3x3()
            for sd, ph_ in (("L", 0.0), ("R", 0.5)):
                u = max(0.0, math.sin(2 * math.pi * (sec * 1.1 + ph_ + 0.3 * k))) ** 3
                sh = h.bone_head(f"upperarm01.{sd}")
                _reach(h, sd, (sh + M @ Vector((0.0, -0.2, 0.05))).lerp(bag + Vector((0, -0.17, 1.35)), u * 0.85), M @ Vector((1 if sd == "L" else -1, 0.3, -0.6)))
        elif k == 2:                                          # light skipping: a small hop on the spot
            zero(h); pose_walk(h, 0.0, stride=0.0, arm_swing=0.0); place(h, (3.6, 1.0, 0), math.radians(200))
            h.arm.location.z += 0.06 * abs(math.sin(sec * 7.0)); arms_relaxed(h)
        else:                                                 # stretching on the mat
            from dd import pose_kneel
            pose_kneel(h, lean=10 + 8 * math.sin(sec * 0.8)); place(h, (-4.6, 0.8, 0.025), math.radians(100), z=0.025)


def anim_bag(c, t):
    sec = t * DUR["bag"]
    h = c["boxer"]; zero(h); pose_walk(h, 0.0, stride=0.0, arm_swing=0.0)
    bag = BAGS[1]; sp = bag + Vector((0.0, -0.75, 0)); place(h, sp, face_to(sp, bag))
    M = h.arm.matrix_world.to_3x3()
    for sd, ph_ in (("L", 0.0), ("R", 0.5)):
        u = max(0.0, math.sin(2 * math.pi * (sec * 0.9 + ph_))) ** 3          # jab rhythm
        sh = h.bone_head(f"upperarm01.{sd}")
        guard_ = sh + M @ Vector((0.12 if sd == "R" else -0.12, -0.2, 0.05))
        hit = bag + Vector((0.0, -0.17, 1.35))
        reach(h, sd, guard_.lerp(hit, u * 0.85), M @ Vector((1 if sd == "L" else -1, 0.3, -0.6)))
    fingers_curl_fist(h)
    for k, b in enumerate(c["bags"]):
        sw = (0.12 if k in (1, 6, 7) else 0.03) * math.sin(sec * 2.1 + k)
        b.rotation_euler = (sw, 0.02 * math.sin(sec * 1.3 + k), 0)
    for h2 in c["talk"] + [c["joiner"]]:
        h2.arm.location = (0, 0, -60)
    anim_trainees(c, sec)


def fingers_curl_fist(h):
    from human import fingers_curl
    fingers_curl(h, 80, thumb=40)


def anim_lockers(c, t):
    sec = t * DUR["lockers"]
    a, b = c["talk"]
    for h, sp, tgt in ((a, Vector((4.5, 1.2, 0)), Vector((4.5, 2.2, 0))), (b, Vector((4.6, 2.3, 0)), Vector((4.5, 1.2, 0)))):
        zero(h); pose_walk(h, 0.0, stride=0.0, arm_swing=0.0); place(h, sp, face_to(sp, tgt)); arms_relaxed(h)
    a.rot("head", (0, 0, 1), 6 * math.sin(sec * 0.8)); b.rot("head", (1, 0, 0), 4 * math.sin(sec * 0.6))
    walk_to(c["joiner"], Vector((-2.0, 0.0, 0)), Vector((3.7, 1.7, 0)), sec - 0.5, speed=0.9)
    c["boxer"].arm.location = (0, 0, -60)
    for k, b_ in enumerate(c["bags"]):
        b_.rotation_euler = ((0.12 if k in (6, 7) else 0.03) * math.sin(sec * 2.1 + k), 0, 0)
    anim_trainees(c, sec)


MOVES = {
    "bag": dict(kind="anim", dof=4.0, anim=anim_bag,
                cam=lambda c, t: (Vector((-3.2 + 2.0 * ease(t), 0.2, 1.6)), BAGS[1] + Vector((0.0, -0.3, 1.25)), 30),
                focus=lambda c, t: BAGS[1] + Vector((0, -0.6, 1.3))),
    "lockers": dict(kind="anim", dof=5.6, anim=anim_lockers,
                    cam=lambda c, t: (Vector((-2.8, -1.6, 1.7)).lerp(Vector((-2.2, -1.2, 1.65)), ease(t)), Vector((4.3, 2.0, 1.2)), 28),
                    focus=lambda c, t: Vector((4.5, 1.8, 1.4))),
}
