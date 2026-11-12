"""CH1: the hospital ward, 1941. A long sunny ward of white iron beds, tall windows, a nurse; Helen with her broken hip.
  nurse  (A): Helen lies in a white iron bed as a nurse adjusts her blanket; slow push.
  visit  (B): Philip sits beside her holding his hat; the camera pulls slowly back down the ward.
"""
import math
import bpy
from mathutils import Vector
from kit import *
import house as H
from house import reset_pose
from human import pose_sit, reach, fingers_curl, lay_down

DUR = {"nurse": 5.0, "visit": 5.0}
VARIANT_FOR = {"nurse": "nurse", "visit": "visit"}


def iron_bed(x, y, white):
    parts = []
    for sy, hgt in ((-1, 1.05), (1, 0.8)):
        yy = y + sy * 1.0
        for sx in (-1, 1):
            parts.append(cyl("BedPost", (x + sx * 0.45, yy, hgt / 2), 0.02, hgt, white, 12))
        parts.append(cyl("BedRail", (x, yy, hgt - 0.02), 0.015, 0.9, white, 12, rot=(0, math.radians(90), 0)))
        for k in range(5):
            parts.append(cyl("BedBar", (x - 0.3 + k * 0.15, yy, hgt * 0.62), 0.008, hgt * 0.6, white, 8))
    parts.append(box("Mattress", (x, y, 0.55), (0.88, 2.0, 0.16), H.fabric_white() if hasattr(H, "fabric_white") else fabric("Sheet", (0.86, 0.86, 0.84), 0.9, 0.3, 600), bevel=0.04))
    parts.append(box("Pillow", (x, y - 0.8, 0.68), (0.6, 0.3, 0.1), fabric("Pillow", (0.9, 0.9, 0.88), 0.9, 0.3, 600), bevel=0.04))
    return join(parts, "IronBed")


def build(variant=None):
    c = {}
    world_sky(sun_elev_deg=30, sun_rot_deg=110, strength=0.5, tint=(0.95, 0.97, 1.0))
    sun(30, 80, energy=3.0, color=(1.0, 0.93, 0.82), angle_deg=1.5)
    bpy.context.scene.view_settings.exposure = -0.2
    pl = pbr("WardPaint", (0.72, 0.74, 0.66), 0.75); low = pbr("WardDado", (0.38, 0.46, 0.4), 0.5)
    box("Floor", (0, 6, -0.02), (8, 22, 0.04), H.mat("lino"))
    box("Ceil", (0, 6, 4.0), (8, 22, 0.1), pl)
    H.wall_y("WinWall", -5, 17, 3.6, 0, 4.0, 0.25, pl, [(y - 0.6, y + 0.6, 1.0, 3.3) for y in range(-3, 17, 3)])
    for y in range(-3, 17, 3):
        p, g = H.window_unit('y', y, 1.2, 3.6, 1.0, 3.3)
    box("WallL", (-3.6, 6, 2.0), (0.2, 22, 4.0), pl)
    box("DadoL", (-3.48, 6, 0.6), (0.04, 22, 1.2), low)
    box("EndWall", (0, -5, 2.0), (8, 0.2, 4.0), pl); box("EndWall2", (0, 17, 2.0), (8, 0.2, 4.0), pl)
    white = pbr("BedWhite", (0.85, 0.85, 0.82), 0.35)
    beds = []
    for k, y in enumerate(range(-2, 16, 3)):
        for x in (-2.4, 2.2):
            b = iron_bed(x, y + 0.5, white); beds.append(b)
            b.rotation_euler = (0, 0, math.radians(90) if False else 0)
    # Helen's bed: first on the left, blanket over her
    blanket = box("Blanket", (-2.4, 1.1, 0.68), (0.95, 1.3, 0.08), fabric("WardBlanket", (0.62, 0.6, 0.52), 0.9, 0.4, 300), bevel=0.03)
    c["blanket"] = blanket
    for y in (2, 8):
        H.point((0, y, 3.6), 30, (1.0, 0.85, 0.65), 0.2)
    H.day_fill((2.6, 3, 2.4), 3.0, 150, (0.95, 0.96, 1.0), rot=(0, math.radians(-90), 0))
    c["haze"] = haze((0, 6, 2.0), (7.2, 22, 4.0), density=0.006, color=(1.0, 0.97, 0.9), anis=0.6)
    # Helen lying (in bed), nurse / Philip
    hl = H.person("Helen", "helen")
    reset_pose(hl); lay_down(hl, face_up=True, z=0.0)
    hl.arm.location = (-2.4, -0.4, 0.0); bpy.context.view_layer.update()
    # turn her end for end onto her own bed: head on its pillow (y ~0.85), feet toward 2.4
    hl.arm.rotation_euler.z += math.pi; bpy.context.view_layer.update()
    hd0 = hl.bone_head("head"); hl.arm.location += Vector((-2.4 - hd0.x, 0.85 - hd0.y, 0)); bpy.context.view_layer.update()
    w = H.np.concatenate([H._world_verts(o) for o in hl.parts if o.type == 'MESH'])
    hl.arm.location.z += 0.63 - w[:, 2].min(); bpy.context.view_layer.update()
    H.rotl(hl, "head", (1, 0, 0), -15)
    c["helen"] = hl
    # under the blanket, propped on two pillows
    blanket.hide_render = True
    hd = hl.bone_head("head")
    box("PillowUp", (hd.x, hd.y, 0.72), (0.6, 0.35, 0.16), fabric("Pillow2", (0.9, 0.9, 0.88), 0.9, 0.3, 600), bevel=0.06)
    beds_ = [o for o in bpy.data.objects if o.name.startswith("PillowUp")]
    c["blanket"] = H.blanket_drape(hl, beds_, 0.63, head_clear=0.22, width=1.0, name="WardBlanket")
    c["blanket"]["home"] = tuple(c["blanket"].location)
    if variant == "nurse":
        c["nurse"] = H.person("Nurse", "nurse")
    else:
        c["philip"] = H.person("Philip", "philip")
        c["hat"] = box("Hat", (0, 0, 0), (0.3, 0.3, 0.12), pbr("Felt", (0.12, 0.1, 0.08), 0.8), bevel=0.05)
        ch, _ = H.ph.model("dining_chair_02", loc=(-1.5, 0.9, 0), rot_z=math.radians(-90)); c["chair"] = ch
    return c


def anim_nurse(c, t):
    sec = t * DUR["nurse"]
    n = c["nurse"]
    H.stand_at(n, (-1.65, 1.0, 0), math.radians(-90))
    tug = 0.06 * math.sin(2 * math.pi * 0.5 * sec)
    c["blanket"].location = Vector(c["blanket"]["home"]) + Vector((0, tug * 0.15, 0))
    reach(n, "R", Vector((-2.0, 0.7 + tug, 0.78)), Vector((0, 0, -1)), Vector((-1, 0, -0.3)))
    reach(n, "L", Vector((-2.0, 1.3 + tug, 0.78)), Vector((0, 0, -1)), Vector((-1, 0, -0.3)))
    H.rotl(n, "spine03", (1, 0, 0), 18); H.look(n, 0, 20)


def anim_visit(c, t):
    sec = t * DUR["visit"]
    p = c["philip"]
    reset_pose(p); pose_sit(p, lean=14)
    p.arm.rotation_euler = (0, 0, math.radians(-90)); p.arm.location = (-1.5, 0.9, 0); bpy.context.view_layer.update(); H.ground_to(p, 0.0)
    knee = (p.bone_tail("upperleg02.L") + p.bone_tail("upperleg02.R")) / 2
    c["hat"].location = knee + Vector((-0.12, 0, 0.12 + 0.01 * math.sin(sec)))
    c["hat"].rotation_euler = (0, math.radians(70), 0)
    reach(p, "R", c["hat"].location + Vector((0.02, -0.12, 0)), Vector((0, -0.3, -1)), Vector((-1, 0, 0)))
    reach(p, "L", c["hat"].location + Vector((0.02, 0.12, 0)), Vector((0, 0.3, -1)), Vector((-1, 0, 0)))
    H.look(p, 0, 15)


MOVES = {
    "nurse": dict(kind="anim", dof=None, far=30, anim=anim_nurse,
                  cam=lambda c, t: (Vector((0.4, 4.2, 1.6)).lerp(Vector((-0.1, 3.4, 1.5)), ease(t)), Vector((-2.2, 0.7, 0.9)), 32)),
    "visit": dict(kind="anim", dof=None, far=30, anim=anim_visit,
                  cam=lambda c, t: (Vector((0.0, 3.4, 1.5)).lerp(Vector((0.4, 7.0, 1.7)), ease(t)), Vector((-1.9, 0.6, 0.9)), 34)),
}
