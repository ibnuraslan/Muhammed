"""CH3 (chat B): police records, 1980s (generic, no crest, no readable names).
Variants:
  cards:    a fingerprint card archive: long aisles of oak card cabinets, a light table at the end.
            aisle  (A): a clerk walks the aisle and pulls a long card drawer open; slow follow
            match  (B): two officers compare cards on a light table; one shakes his head and sets a card aside
  cabinets: the case archive: twelve grey steel filing cabinets in a dim basement room.
            twelve (A): slow track along the twelve cabinets as a clerk slides a drawer shut
            tube   (B): push to a tape box on the last cabinet; the fluorescent tube flickers and dims
"""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
from common import world_flat, ease
from human import reach, fingers_curl
import ph
import b_common as B
import b_props as P

EXPOSURE = 0.3
DUR = {"aisle": 5.5, "match": 5.0, "twelve": 6.0, "tube": 6.0}
VARIANT_FOR = {"aisle": "cards", "match": "cards", "twelve": "cabinets", "tube": "cabinets"}


def card_cabinet(name, oak, brass):
    """Oak cabinet of 5 x 8 small card drawers (1.5 m tall, 0.9 wide), one mesh used for all instances."""
    parts = [box("CCBody", (0, 0.25, 0.75), (0.9, 0.5, 1.5), oak, bevel=0.005)]
    for r in range(8):
        for k in range(5):
            x = -0.36 + k * 0.18; z = 0.12 + r * 0.17
            parts.append(box("CCFront", (x, -0.006, z), (0.165, 0.012, 0.155), oak, bevel=0.003))
            parts.append(box("CCPull", (x, -0.016, z - 0.03), (0.04, 0.01, 0.012), brass))
            parts.append(box("CCLabel", (x, -0.0125, z + 0.035), (0.05, 0.002, 0.022), pbr("CCLab", (0.85, 0.83, 0.75), 0.7)))
    return join(parts, name)


def steel_cabinet(name, steel, chrome):
    parts = [box("SCBody", (0, 0.33, 0.66), (0.47, 0.66, 1.32), steel, bevel=0.005)]
    for k in range(4):
        z = 0.17 + k * 0.32
        parts.append(box("SCFront", (0, -0.006, z), (0.45, 0.014, 0.3), steel, bevel=0.004))
        parts.append(box("SCHandle", (0, -0.025, z + 0.06), (0.16, 0.02, 0.025), chrome, bevel=0.004))
        parts.append(box("SCLabel", (0, -0.014, z + 0.1), (0.09, 0.003, 0.04), pbr("SCLab", (0.85, 0.84, 0.8), 0.8)))
    return join(parts, name)


def build(variant=None):
    variant = variant or "cards"
    c = {"variant": variant}
    rng = np.random.default_rng(20)
    world_flat((0.006, 0.007, 0.01), 1.0)
    floor = B.tex_mat("ArFloor", "old_linoleum_flooring_01" if variant == "cards" else "concrete_floor_worn_001", scale=0.5, tint=(0.6, 0.58, 0.55))
    box("Floor", (0, 0, -0.01), (14, 12, 0.02), floor)
    wall = B.plaster("ArWall", (0.45, 0.45, 0.42), dirt=0.25)
    for (loc, size) in (((0, 6, 1.5), (14, 0.1, 3)), ((0, -6, 1.5), (14, 0.1, 3)), ((7, 0, 1.5), (0.1, 12, 3)), ((-7, 0, 1.5), (0.1, 12, 3))):
        box("ArW", loc, size, wall)
    box("ArCeil", (0, 0, 3.0), (14, 12, 0.05), B.plaster("ArC", (0.4, 0.4, 0.38)))
    B.fill((-5, -5, 2.5), (0, 0, 1), 20, 3, (0.4, 0.5, 0.7))
    if variant == "cards":
        oak = B.tex_mat("CardOak", "oak_veneer_01", scale=0.7, tint=(0.75, 0.6, 0.45)); brass = pbr("Brass", (0.6, 0.45, 0.2), 0.3, 1.0)
        tpl = card_cabinet("CardCab", oak, brass)
        for row in range(3):                                     # three aisles of cabinets (rows along y)
            for k in range(7):
                for side, rz in ((-1, 0.0), (1, math.pi)):
                    x = -3.0 + row * 3.0 + side * 0.75
                    o = instance(tpl, (x, -4.5 + k * 0.92, 0), (0, 0, math.pi / 2 if side < 0 else -math.pi / 2))
        tpl.location = (0, 0, -30)
        # one drawer pulled out (a long tray of cards) in the middle aisle
        tray = join([box("Tray", (0, 0, 0), (0.15, 0.5, 0.1), oak, bevel=0.003)] +
                    [box("Card", (0, -0.22 + j * 0.012, 0.03), (0.13, 0.002, 0.09), B.paper_mat("CardP", (0.88, 0.86, 0.8), lines=False)) for j in range(36)], "Tray")
        c["tray"] = tray
        c["tray_in"] = Vector((-1.0, -4.5 + 3 * 0.92 - 0.36, 0.12 + 4 * 0.17))
        # tubes overhead along the aisles
        for row in range(3):
            for y in (-3.0, 0.5):
                x = -3.0 + row * 3.0
                box("Tube", (x, y, 2.95), (0.1, 1.2, 0.04), emissive("TubeE", (0.9, 0.95, 0.88), 2.5))
                l = area_light((x, y, 2.9), (0, 0, 0), 1.0, 45, (0.88, 0.95, 0.85)); l.visible_camera = False
        # the light table at the end of the middle aisle
        lt = box("LightTable", (0, 3.6, 0.45), (1.4, 0.8, 0.9), pbr("LTBody", (0.3, 0.31, 0.3), 0.5), bevel=0.01)
        box("LightTop", (0, 3.6, 0.905), (1.3, 0.7, 0.01), emissive("LTGlow", (0.95, 0.97, 1.0), 3.0))
        card_m = B.paper_mat("FPCard", (0.9, 0.88, 0.82), lines=True)
        c["cards"] = [B.sheet(f"FPCard{k}", (-0.35 + k * 0.23, 3.55 + 0.05 * (k % 2), 0.913), (0.2, 0.2), card_m, rot=(0, 0, 0.05 * k)) for k in range(4)]
        ph.model("magnifying_glass_01", loc=(0.35, 3.85, 0.912), rot_z=1.0)
        B.key_spot((1.8, 2.4, 2.6), (0, 3.6, 1.0), 220, 30, (1.0, 0.8, 0.58), soft=0.1, name="TableKey")
        clerk = B.person("Clerk", 0.0, 34, "female_elegantsuit01", "bob01", hue=0.52, sat=0.3, val=0.45, hair_val=0.3)
        c["clerk"] = clerk
        o1 = B.person("Officer1", 1.0, 48, "male_elegantsuit01", "short02", hue=0.08, sat=0.25, val=0.3, hair_val=0.9, hair_sat=0.3)
        o2 = B.person("Officer2", 1.0, 36, "male_casualsuit05", "short04", hue=0.1, sat=0.3, val=0.4, hair_val=0.3)
        B.stand(o1, (-0.35, 3.0, 0), math.pi + 0.15); B.stand(o2, (0.4, 3.05, 0), math.pi - 0.2)   # facing +Y, the table
        c["o1"], c["o2"] = o1, o2
        c["rest"] = {k: B.capture(c[k]) for k in ("o1", "o2")}
    else:
        steel = pbr("CabGrey", (0.36, 0.37, 0.38), 0.4, 0.6, **{'Coat Weight': 0.15}); chrome = pbr("Chrome", (0.8, 0.8, 0.8), 0.2, 1.0)
        tpl = steel_cabinet("SteelCab", steel, chrome)
        c["cabs"] = []
        for k in range(12):
            o = instance(tpl, (-3.3 + k * 0.52, 5.25, 0), (0, 0, 0)); c["cabs"].append(o)
        tpl.location = (0, 0, -30)
        drawer = box("OpenDrawer", (0, 0, 0), (0.45, 0.55, 0.28), steel, bevel=0.004)
        c["drawer"] = drawer; c["drawer_x"] = -3.3 + 4 * 0.52
        # tape box (a reel in its card box) on the last cabinet, a stack of files on others
        tb = box("TapeBox", (-3.3 + 11 * 0.52, 5.5, 1.32 + 0.11), (0.2, 0.2, 0.22), pbr("TapeBoxCard", (0.55, 0.45, 0.32), 0.8), bevel=0.003)
        tb.rotation_euler = (math.radians(90), 0, 0.2)
        c["tapebox"] = tb
        for k in (2, 5, 8):
            for j in range(3):
                box("ArchFile", (-3.3 + k * 0.52, 5.5, 1.335 + j * 0.03), (0.24, 0.32, 0.028), pbr(f"AF{k}{j}", (0.55, 0.45, 0.28), 0.8), rot=(0, 0, rng.uniform(-0.1, 0.1)))
        # one flickering fluorescent tube over the row (frame driver), dimming at the end
        tube = box("Tube", (0.0, 4.6, 2.95), (3.0, 0.1, 0.04), emissive("TubeE", (0.9, 0.95, 0.88), 2.5))
        tl = area_light((0.0, 4.6, 2.9), (0, 0, 0), 3.0, 90, (0.88, 0.95, 0.85)); tl.visible_camera = False
        expr = "(1 if (frame < 70 or (frame % 7 > 2 and frame < 110)) else 0.15) * (1 if frame < 120 else 0.15)"
        d = tl.data.driver_add("energy").driver; d.type = 'SCRIPTED'; d.expression = f"90 * {expr}"
        em = tube.data.materials[0].node_tree.nodes["Principled BSDF"].inputs['Emission Strength']
        d = em.driver_add("default_value").driver; d.type = 'SCRIPTED'; d.expression = f"2.5 * {expr}"
        B.key_spot((3.5, 1.0, 2.0), (0.0, 5.3, 0.9), 300, 30, (1.0, 0.75, 0.5), soft=0.2, name="Doorway")
        clerk = B.person("Clerk", 1.0, 52, "male_elegantsuit01", "short02", hue=0.1, sat=0.2, val=0.35, hair_val=1.1, hair_sat=0.2)
        B.stand(clerk, (c["drawer_x"], 4.35, 0), math.pi)
        c["clerk"] = clerk
        c["rest"] = {"clerk": B.capture(clerk)}
    B.room_haze((0, 0, 1.5), (13.8, 11.8, 3.0), density=0.01)
    return c


def anim(c, t, move):
    sec = t * DUR[move]
    v = c["variant"]
    if v == "cards":
        for k in ("o1", "o2"):
            B.apply_pose(c[k], c["rest"][k])
        cl = c["clerk"]
        if move == "aisle":
            u = ease(min(1.0, sec / 3.0))
            B.walk_to(cl, (0.0, -5.0, 0), (-0.05, c["tray_in"].y - 0.65, 0), u, 4.0 * u + 0.001, stride=20, swing=10)
            pull = ease(min(1.0, max(0.0, (sec - 3.2) / 1.2)))
            tr = c["tray"]; tr.location = c["tray_in"] + Vector((0.4 * pull, 0, 0)); tr.rotation_euler = (0, 0, math.pi / 2)
            if sec > 3.0:
                B.stand(cl, (-0.05, c["tray_in"].y - 0.15, 0), -math.pi / 2 + 0.3)
                reach(cl, "R", tr.location + Vector((0.14, 0, 0.06)), Vector((0.3, -0.6, -0.8)), Vector((-1, 0, 0)))
                fingers_curl(cl, 40, side=("R",))
                cl.rot("head", (1, 0, 0), 10)
        else:
            B.hide_person(cl)
            c["tray"].location = (0, 0, -30)
            o1, o2 = c["o1"], c["o2"]
            for h, ph_ in ((o1, 0.0), (o2, 1.3)):
                fwd = B.fwd_of(h); side = fwd.cross(Vector((0, 0, 1))).normalized()
                for sd, sg in (("L", -1), ("R", 1)):
                    reach(h, sd, Vector((h.arm.location.x, 3.42, 0.95)) + side * (0.14 * sg), Vector((sg * side.x, sg * side.y, -0.8)), fwd + Vector((0, 0, -0.6)))
                fingers_curl(h, 30)
                h.rot("spine03", (1, 0, 0), 0); h.rot("head", (-1, 0, 0), 22)
            # o1 slides one card aside and shakes his head
            u = ease(min(1.0, max(0.0, (sec - 1.5) / 1.0)))
            c["cards"][1].location = Vector((-0.12, 3.6, 0.913)).lerp(Vector((-0.55, 3.38, 0.913)), u)
            o1.rot("head", (0, 0, 1), 12 * math.sin(max(0.0, sec - 2.6) * 6.0) * (1 if 2.6 < sec < 4.0 else 0))
    else:
        cl = c["clerk"]; B.apply_pose(cl, c["rest"]["clerk"])
        dr = c["drawer"]
        shut = ease(min(1.0, max(0.0, (sec - 1.0) / 1.0)))
        dr.location = Vector((c["drawer_x"], 5.25 - 0.27 + 0.27 * shut - 0.0, 0.17 + 2 * 0.32))
        if move == "twelve":
            reach(cl, "R", dr.location + Vector((0.05, -0.3, 0.06)), Vector((0.4, -0.6, -0.8)), Vector((0, 1, 0)))
            reach(cl, "L", dr.location + Vector((-0.1, -0.3, 0.06)), Vector((-0.4, -0.6, -0.8)), Vector((0, 1, 0)))
            fingers_curl(cl, 35)
            if sec > 2.3:
                B.apply_pose(cl, c["rest"]["clerk"]); B.arms_down(cl)
        else:
            dr.location.y = 5.25
            B.hide_person(cl)
    bpy.context.view_layer.update()


def cam(a, b, tgt, lens):
    return lambda c, t: (Vector(a).lerp(Vector(b), ease(t)), Vector(tgt), lens)


MOVES = {
    "aisle": dict(kind="anim", dof=4.0, cam=cam((0.15, -6.2 + 0.4, 1.6), (0.1, -4.6, 1.55), (0.0, -1.0, 1.1), 28),
                  anim=lambda c, t: anim(c, t, "aisle"), focus=lambda c, t: c["clerk"].bone_head("spine03")),
    "match": dict(kind="anim", dof=2.8, cam=cam((3.0, 0.9, 2.0), (2.6, 1.2, 1.95), (0.0, 3.4, 1.2), 30),
                  anim=lambda c, t: anim(c, t, "match"), focus=lambda c, t: Vector((0.0, 3.5, 1.0))),
    "twelve": dict(kind="anim", dof=4.0, cam=cam((-4.6, 1.4, 1.55), (-2.2, 1.6, 1.5), (0.0, 5.3, 0.9), 30),
                   anim=lambda c, t: anim(c, t, "twelve"), focus=lambda c, t: Vector((c["drawer_x"], 5.0, 1.0))),
    "tube": dict(kind="anim", dof=2.8, cam=cam((0.2, 2.4, 1.85), (1.3, 3.5, 1.75), (-3.3 + 11 * 0.52, 5.4, 1.25), 35),
                 anim=lambda c, t: anim(c, t, "tube"), focus=lambda c, t: c["tapebox"].location),
}
