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
    plant, pm, plo, phi = asset("potted_plant_02", (hi.x + 0.45, 1.0, 0), 30, floor=0.0)
    seat_y = lo.y + 0.32
    sx_m, sx_w = SOFA.x - 0.38, SOFA.x + 0.36
    zm = surface_z(sx_m, seat_y, 1.0) or 0.45
    zw = surface_z(sx_w, seat_y, 1.0) or 0.45
    # ---- the two of them
    m = man("Man"); sit_on(m, (sx_m, seat_y), zm, 0, lean=-4)
    w = woman("Woman"); sit_on(w, (sx_w, seat_y), zw, 0, lean=-2)
    cam_loc = Vector((0.2, seat_y - 2.05, 0.95))
    for h, other, sd in ((m, w, "L"), (w, m, "R")):
        # forearms rest on the thighs, hands loose
        for s_, sg in (("L", 1), ("R", -1)):
            knee = h.bone_tail(f"upperleg02.{s_}")
            hip = h.bone_head(f"upperleg01.{s_}")
            reach(h, s_, hip.lerp(knee, 0.62) + Vector((0, 0, 0.09)), Vector((sg * 0.6, 0.4, -0.6)), Vector((0, -1, -0.4)))
        fingers_curl(h, 30, thumb=10)
    # he turns his head away from the flash, eyes on the lens; she looks at him, guarded
    look_at(m, cam_loc + Vector((-1.2, 0.4, 0.1)), 0.6); gaze(m, cam_loc + Vector((-0.4, 0, 0)))
    look_at(w, cam_loc + Vector((-0.3, 0, 0.1)), 0.55); gaze(w, cam_loc)
    # ---- the glowing board, in her lap: she holds it by its edges
    build_module((0, 0, 0), passives=False)
    holder = bpy.data.objects.new("BoardRoot", None); bpy.context.collection.objects.link(holder)
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.parent is None and o.name.startswith(("Board", "Substrate", "Interposer", "Die", "HBM", "Underfill", "Frame", "Pad", "Inductor", "Cap2")):
            o.parent = holder
    lap = (w.bone_tail("upperleg02.L") + w.bone_tail("upperleg02.R")) / 2 * 0.55 + (w.bone_head("upperleg01.L") + w.bone_head("upperleg01.R")) / 2 * 0.45
    bp = lap + Vector((0, 0, 0.11))
    holder.location = bp; holder.rotation_euler = (math.radians(-35), 0, math.radians(4)); holder.scale = (1.6, 1.6, 1.6)
    bpy.context.view_layer.update()
    for s_, sg in (("L", 1), ("R", -1)):
        reach(w, s_, bp + Vector((sg * 0.12, 0.01, 0.0)), Vector((sg * 0.7, 0.3, -0.6)), Vector((-sg * 0.6, -0.5, -0.2)))
    fingers_curl(w, 25, side=("L", "R"), thumb=8)
    glow = box("BoardGlow", tuple(bp + Vector((0, -0.02, -0.01))), (0.2, 0.002, 0.15), emissive("GreenUnder", (0.2, 1.0, 0.35), 14), rot=(math.radians(-35 + 90), 0, 0))
    glow.visible_camera = False
    point(bp + Vector((0, -0.06, 0.04)), 3, (0.25, 1.0, 0.4), 0.05, "ChipGlow")
    soft(bp + Vector((0, -0.08, 0.05)), w.bone_head("head"), 22, (0.2, 1.0, 0.35), size=0.2, name="GreenUp")
    # ---- the flash: hard light from the photographer's camera (just left of ours), and a soft fill
    flash = spot(cam_loc + Vector((-0.35, 0.3, 0.3)), Vector((SOFA.x, seat_y, 0.95)), 260, (0.95, 0.97, 1.0), 95, 0.35, 0.015, "Flash")
    light_only(flash, m.parts + w.parts + sm)
    spot(flash.location, Vector((SOFA.x, seat_y, 0.95)), 160, (0.95, 0.97, 1.0), 95, 0.35, 0.015, "FlashWall")
    soft(Vector((2.4, 1.1, 1.9)), Vector((SOFA.x + 0.3, seat_y, 1.1)), 120, (0.45, 0.6, 1.0), size=0.6, name="CoolRim")
    soft(Vector((-1.6, 0.9, 2.6)), Vector((SOFA.x - 0.4, seat_y, 1.2)), 70, (1.0, 0.2, 0.15), size=0.6, name="RedBack")
    haze((0, 0, 1.6), (12, 6, 3.2), density=0.015, color=(0.9, 0.95, 1.0), anis=0.4)
    c = dict(m=m, w=w)
    tgt = Vector((SOFA.x - 0.45, seat_y, 0.8))
    c["cam"] = (cam_loc, tgt, 32)
    c["focus"] = w.bone_head("head")
    c["fstop"] = 2.8
    return c
