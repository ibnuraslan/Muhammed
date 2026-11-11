"""CH2 SET 1 (dramatization): an after-hours party on a trade-show floor. Server racks on a low stage under clean
coloured stage washes, a crowd with drinks, a lounge corner. No brands.
  crowd  (A): slow track across the crowd toward the stage; CHAPTER 2 / THE MEMO title
  flash  (B): the CEO and the woman sitting side by side on a lounge sofa; a camera flash fires and the moment freezes
"""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
from human import Human, add_asset, reset_pose, pose_walk, pose_sit, fingers_curl, _world_verts, reach
from people import man, woman
from sc_dchall import server_unit, led_material, perforated
from sc_corp import arms_down

EXPOSURE = 0.7
DUR = {"crowd": 6.0, "flash": 5.0}       # estimates until the chapter 2 voiceover arrives
FLASH_FRAME = 70


def build(variant=None):
    c = {}
    rng = np.random.default_rng(24)
    world_flat((0.006, 0.006, 0.01), 1.0)
    box("Floor", (0, 4, -0.01), (40, 30, 0.02), pbr("HallFloor", (0.05, 0.05, 0.055), 0.25, 0.0, **{'Coat Weight': 0.4}))
    box("BackWall", (0, 14, 5), (40, 0.2, 10), pbr("HallWall", (0.03, 0.03, 0.035), 0.7))
    # truss overhead with stage washes (clean, soft) and a warm bar light
    truss = pbr("Truss", (0.4, 0.4, 0.42), 0.35, 0.9)
    for y in (6.0, 11.0):
        box("Truss", (0, y, 6.5), (24, 0.3, 0.3), truss)
    for k, col in enumerate(((0.35, 0.25, 1.0), (0.2, 0.55, 1.0), (1.0, 0.35, 0.55), (0.2, 0.55, 1.0), (0.35, 0.25, 1.0))):
        l = bpy.data.lights.new("Wash", 'SPOT'); l.energy = 3000; l.color = col; l.spot_size = math.radians(40); l.spot_blend = 0.7
        o = bpy.data.objects.new("Wash", l); bpy.context.collection.objects.link(o); o.location = (-8 + k * 4, 11.0, 6.3); point_at(o, (-6 + k * 3, 9.5, 0.5))
    # stage with a row of server racks on display, a backdrop panel with a generic title
    box("Stage", (0, 10.5, 0.3), (14, 4, 0.6), pbr("StageBlack", (0.02, 0.02, 0.022), 0.4))
    frame_m = pbr("RackFrame", (0.03, 0.03, 0.035), 0.4, 0.6); face_m = pbr("ServerFace", (0.16, 0.17, 0.18), 0.35, 0.8)
    handle_m = pbr("Handle", (0.55, 0.56, 0.58), 0.25, 1.0)
    led_g = led_material("LedG", (0.3, 1.0, 0.5)); led_b = led_material("LedB", (0.3, 0.6, 1.0))
    srv, (la, lb) = server_unit("SrvT", frame_m, face_m, handle_m, led_g, led_b)
    for o in (srv, la, lb):
        o.location = (0, 0, -50)
    for k in range(6):
        x = -4.5 + k * 1.8
        box("Rack", (x, 11.2, 0.6 + 1.1), (0.62, 1.0, 2.2), frame_m, bevel=0.005)
        for u in range(18):
            z = 0.75 + u * 0.1
            instance(srv, (x, 10.69, z)); instance(la, (x + 0.19, 10.678, z + 0.028)); instance(lb, (x + 0.205, 10.678, z + 0.028))
    box("Backdrop", (0, 12.8, 3.5), (14, 0.1, 5), pbr("Backdrop", (0.02, 0.025, 0.04), 0.5))
    text_obj("Show", "AI SERVER NIGHT", (0, 12.74, 5.2), 0.55, emissive("ShowTxt", (0.85, 0.9, 1.0), 4), rot=(math.radians(90), 0, 0),
             font_path="/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", spacing=1.3)
    box("Bar", (-11, 6, 0.55), (1.0, 6, 1.1), pbr("BarTop", (0.1, 0.07, 0.05), 0.3, 0.0, **{'Coat Weight': 0.6}), bevel=0.02)
    box("BarGlow", (-11.6, 6, 1.6), (0.1, 6, 1.0), emissive("BarGlow", (1.0, 0.72, 0.4), 0.8))
    for k in range(4):
        l = bpy.data.lights.new("Pin", 'SPOT'); l.energy = 300; l.color = (1.0, 0.8, 0.6); l.spot_size = math.radians(55); l.spot_blend = 0.6
        o = bpy.data.objects.new("Pin", l); bpy.context.collection.objects.link(o); o.location = (-5 + k * 3.4, 2.5, 6.2)
    haze((0, 6, 3.5), (30, 18, 7), density=0.008, color=(0.9, 0.9, 1.0), anis=0.55)
    f1 = area_light((-6, -3, 5), (0, 0, 0), 4.0, 900, (1.0, 0.85, 0.68)); point_at(f1, (0, 5, 1.2)); f1.visible_camera = False
    f2 = area_light((6.0, -0.6, 2.4), (0, 0, 0), 1.5, 160, (1.0, 0.82, 0.62)); point_at(f2, (6.0, 2.0, 0.9)); f2.visible_camera = False
    # the crowd: people standing with drinks, a few walking
    specs = [(1.0, 40, "male_casualsuit01", "short02"), (0.0, 33, "female_casualsuit01", "bob02"), (1.0, 52, "male_elegantsuit01", "short04"),
             (1.0, 29, "male_casualsuit06", "short03"), (0.0, 45, "female_elegantsuit01", "ponytail01"), (1.0, 36, "male_casualsuit03", "short01"),
             (0.0, 27, "female_casualsuit02", "long01"), (1.0, 48, "male_casualsuit04", "short02"), (1.0, 31, "male_worksuit01", "short04")]
    glass_m = glass("Glass", (0.95, 0.97, 0.98))
    crowd = []
    for k, (g, yrs, cl, hr) in enumerate(specs):
        h = Human(f"Guest{k}", gender=g, years=yrs, muscle=0.5, weight=0.45 + 0.05 * (k % 3), height=0.45 + 0.05 * (k % 2), eyelashes=None)
        add_asset(h, "clothes", cl, val=0.2 + 0.08 * (k % 3), rough=0.65); add_asset(h, "clothes", "shoes02", val=0.15); add_asset(h, "hair", hr, val=0.2 + 0.1 * (k % 3))
        x, y = rng.uniform(-6, 6), rng.uniform(3.0, 8.0)
        face = math.atan2(-(0 - x), (5 - y)) + rng.uniform(-1.2, 1.2)
        gl = cyl("Drink", (0, 0, -40), 0.035, 0.12, glass_m, verts=16)
        crowd.append(dict(h=h, x=x, y=y, face=face, walk=(k % 4 == 0), ph=rng.uniform(0, 6), glass=gl))
    c["crowd"] = crowd
    # the lounge corner: a low sofa, the CEO and the woman side by side (shot B)
    sofa_m = fabric("SofaVelvet", (0.06, 0.07, 0.11), 0.85, 0.9, 500)
    box("Sofa", (6.0, 2.0, 0.22), (1.9, 0.85, 0.44), sofa_m, bevel=0.06)
    box("SofaBack", (6.0, 2.38, 0.65), (1.9, 0.16, 0.6), sofa_m, bevel=0.06)
    m = man("CEO"); w = woman("Guest")
    for h, x in ((m, 5.6), (w, 6.4)):
        reset_pose(h); pose_sit(h, lean=4)
        h.arm.rotation_euler = (0, 0, 0); h.arm.location = (x, 1.95, 0); bpy.context.view_layer.update()
        vv = np.concatenate([_world_verts(o) for o in h.parts if o.type == 'MESH'])
        h.arm.location.z -= vv[:, 2].min(); bpy.context.view_layer.update()
    c.update(ceo=m, guest=w)
    fl = bpy.data.lights.new("PhotoFlash", 'POINT'); fl.color = (1.0, 0.97, 0.94); fl.shadow_soft_size = 0.05
    d = fl.driver_add("energy").driver; d.type = 'SCRIPTED'; d.expression = f"9000 * max(0, 1 - abs(frame - {FLASH_FRAME}) / 2.0)"
    fo = bpy.data.objects.new("PhotoFlash", fl); bpy.context.collection.objects.link(fo); fo.location = (6.0, -0.6, 1.4)
    return c


def anim_crowd(c, sec):
    for p in c["crowd"]:
        h = p["h"]
        if p["walk"]:
            d = 0.8 * sec
            bob = pose_walk(h, (d / 1.3 + p["ph"]) % 1.0, stride=22, arm_swing=12)
            h.arm.rotation_euler = (0, 0, math.radians(90)); h.arm.location = (p["x"] + d, p["y"], bob); bpy.context.view_layer.update()
            arms_down(h, (d / 1.3 + p["ph"]) % 1.0, 12)
            p["glass"].location = (0, 0, -40)
        else:
            pose_walk(h, 0.0, stride=0.0, arm_swing=0.0)
            h.arm.rotation_euler = (0, 0, p["face"]); h.arm.location = (p["x"], p["y"], 0); bpy.context.view_layer.update()
            arms_down(h, 0.0, 0)
            chest = h.bone_head("spine03"); fwd = (h.arm.matrix_world.to_3x3() @ Vector((0, -1, 0))).normalized()
            sip = max(0.0, math.sin(sec * 0.9 + p["ph"]))
            hand = chest + fwd * 0.22 + Vector((0, 0, -0.08 + 0.18 * sip ** 4))
            reach(h, "R", hand, Vector((0, 0, -1)) - fwd, Vector((0, 0, 1)))
            fingers_curl(h, 50, side=("R",), thumb=30)
            p["glass"].location = h.bone_tail("wrist.R") + Vector((0, 0, 0.04))
            h.rot("head", (0, 0, 1), 12 * math.sin(sec * 0.6 + p["ph"]))
    bpy.context.view_layer.update()


def anim_flash(c, sec):
    """They talk (small head turns toward each other) until the flash; after it, everything holds still."""
    f = sec * 24
    s_ = min(sec, FLASH_FRAME / 24.0)
    for h, sg in ((c["ceo"], 1), (c["guest"], -1)):
        reset_pose(h); pose_sit(h, lean=4)
        h.rot("neck01", (0, 0, 1), sg * (10 + 6 * math.sin(s_ * 1.2))); h.rot("head", (0, 0, 1), sg * (8 + 5 * math.sin(s_ * 1.5 + 1)))
    bpy.context.view_layer.update()


MOVES = {
    "crowd": dict(kind="anim", dof=2.8, far=40.0, title=("CHAPTER 2", "THE MEMO", 18, 120),
                  cam=lambda c, t: (Vector((-5.5, -1.5, 1.7)).lerp(Vector((-2.0, 0.0, 1.75)), ease(t)), Vector((1.0, 9.0, 1.6)), 32),
                  focus=lambda c, t: Vector((0.0, 5.0, 1.5)), anim=lambda c, t: anim_crowd(c, t * DUR["crowd"])),
    "flash": dict(kind="anim", dof=2.4, far=20.0,
                  cam=lambda c, t: (Vector((6.0, -1.3, 1.15)).lerp(Vector((6.0, -0.95, 1.12)), ease(min(t, FLASH_FRAME / (24 * DUR["flash"])))), Vector((6.0, 2.0, 0.95)), 40),
                  focus=lambda c, t: Vector((6.0, 2.0, 1.0)), anim=lambda c, t: (anim_flash(c, t * DUR["flash"]), anim_crowd(c, min(t * DUR["flash"], FLASH_FRAME / 24.0)))),
}
