"""Thumbnail 2 - FLASH. A dark hotel lounge. The man and the woman sit side by side on a sofa, caught in a camera
flash: hard white light, their shadows thrown on the panelled wall. In the foreground on the low table, a bare AI
accelerator board glows green. Left third: dark panelled wall for the title."""
import math
import bpy
from mathutils import Vector
from kit import pbr, emissive, box, cyl, haze, world_flat
import ph
from sc_gpu_module import build_module
from people import man, woman
from human import reach, fingers_curl, rotate_bone, aim_bone
from thumbkit import *

EXPOSURE = 0.0
VIGNETTE = 0.7
SOFA = Vector((0.75, 0.55, 0))


def room():
    world_flat((0.003, 0.004, 0.006), 1.0)
    floor = ph.texture("herringbone_parquet", scale=0.6, tint=(0.35, 0.3, 0.28))
    box("Floor", (0, 0, -0.01), (14, 14, 0.02), floor)
    wall = ph.texture("dark_paneled_wood", scale=0.35, tint=(0.06, 0.055, 0.06))
    box("BackWall", (0, 1.45, 1.6), (14, 0.1, 3.2), wall)
    box("SideWall", (-3.2, 0, 1.6), (0.1, 8, 3.2), wall)


def build(variant=None):
    room()
    sofa, sm, lo, hi = asset("sofa_02", (SOFA.x, SOFA.y, 0), 0, floor=0.0)
    # push it back against the wall
    sofa.location.y += (1.38 - hi.y); bpy.context.view_layer.update(); lo, hi = ph.bounds(sm)
    tab, tm, tlo, thi = asset("modern_coffee_table_01", (SOFA.x + 0.05, -0.3, 0), 90, floor=0.0)
    plant, pm, plo, phi = asset("potted_plant_02", (hi.x + 0.45, 1.0, 0), 30, floor=0.0)
    seat_y = lo.y + 0.32
    sx_m, sx_w = SOFA.x - 0.38, SOFA.x + 0.36
    zm = surface_z(sx_m, seat_y, 1.0) or 0.45
    zw = surface_z(sx_w, seat_y, 1.0) or 0.45
    top = surface_z(tab.location.x, tab.location.y, 1.5) or 0.4
    # ---- the two of them
    m = man("Man"); sit_on(m, (sx_m, seat_y), zm, 0, lean=-4)
    w = woman("Woman"); sit_on(w, (sx_w, seat_y), zw, 0, lean=-2)
    cam_loc = Vector((0.5, -1.75, 0.76))
    for h, other, sd in ((m, w, "L"), (w, m, "R")):
        # forearms rest on the thighs, hands loose
        for s_, sg in (("L", 1), ("R", -1)):
            knee = h.bone_tail(f"upperleg02.{s_}")
            hip = h.bone_head(f"upperleg01.{s_}")
            reach(h, s_, hip.lerp(knee, 0.62) + Vector((0, 0, 0.09)), Vector((sg * 0.6, 0.4, -0.6)), Vector((0, -1, -0.4)))
        fingers_curl(h, 30, thumb=10)
    # he turns his head away from the flash, eyes on the lens; she looks at him, guarded
    look_at(m, cam_loc + Vector((0.6, 0, 0.2)), 0.55); gaze(m, cam_loc)
    look_at(w, m.bone_head("head") + Vector((0, -0.25, 0.05)), 0.7); gaze(w, m.bone_head("head") + Vector((0, -0.2, 0.08)))
    # ---- the glowing board on the table, in the foreground
    pk = build_module((0, 0, 0), passives=False)
    board_objs = [o for o in bpy.data.objects if o.name.startswith(("Board", "Substrate", "Interposer", "Die", "HBM", "Underfill", "Frame", "Pad", "Inductor", "Cap2"))
                  and o.type == 'MESH']
    holder = bpy.data.objects.new("BoardRoot", None); bpy.context.collection.objects.link(holder)
    for o in board_objs:
        if o.parent is None:
            o.parent = holder
    bx, by = tab.location.x + 0.32, tab.location.y - 0.16
    holder.location = (bx, by, top + 0.001); holder.rotation_euler = (0, 0, math.radians(-24)); holder.scale = (2.2, 2.2, 2.2)
    edge = box("BoardGlowEdge", (bx, by, top + 0.002), (0.33, 0.25, 0.002), emissive("GreenEdge", (0.2, 1.0, 0.35), 18),
               rot=(0, 0, math.radians(-24)))
    edge.visible_camera = False
    point((bx, by, top + 0.06), 6, (0.25, 1.0, 0.4), 0.05, "ChipGlow")
    soft((bx, by - 0.1, top + 0.03), (sx_m + 0.35, seat_y, 1.1), 40, (0.2, 1.0, 0.35), size=0.3, name="GreenUp")
    # ---- the flash: hard light from the photographer's camera (just left of ours), and a soft fill
    flash = spot(cam_loc + Vector((-0.35, 0.3, 0.3)), Vector((SOFA.x, seat_y, 0.95)), 1100, (0.95, 0.97, 1.0), 95, 0.35, 0.015, "Flash")
    soft(Vector((2.4, 1.1, 1.9)), Vector((SOFA.x + 0.3, seat_y, 1.1)), 120, (0.45, 0.6, 1.0), size=0.6, name="CoolRim")
    soft(Vector((-1.6, 0.9, 2.6)), Vector((SOFA.x - 0.4, seat_y, 1.2)), 70, (1.0, 0.2, 0.15), size=0.6, name="RedBack")
    haze((0, 0, 1.6), (12, 6, 3.2), density=0.015, color=(0.9, 0.95, 1.0), anis=0.4)
    c = dict(m=m, w=w)
    tgt = Vector((SOFA.x - 0.55, seat_y - 0.2, 0.74))
    c["cam"] = (cam_loc, tgt, 35)
    c["focus"] = (m.bone_head("head") + w.bone_head("head")) / 2
    c["fstop"] = 2.8
    return c
