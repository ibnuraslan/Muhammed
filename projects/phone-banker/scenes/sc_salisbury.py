"""AN ENGLISH STREET, March 2018 (dramatization; a generic street of brick houses, not a likeness of any real house).
  street : a quiet street under grey sky, a cathedral spire beyond, police tape stirring (Ch3 5A)
  suits  : two investigators in protective suits at a house's front door (Ch3 5B)
  handle : a slow push to the front-door handle (Ch3 6A)
  path   : pull back down the garden path to the cordoned street (Ch3 6B)"""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
import ph
from pbkit import joinm, ph_instances
from pbpeople import person, stand, nod, look, hand_to, protective_gear, recolor

EXPOSURE = 0.3
BOUNCES = 6
DUR = {"street": 6.0, "suits": 5.5, "handle": 6.0, "path": 6.0}
VARIANT_FOR = {"street": None, "suits": None, "handle": None, "path": None}
DOOR = Vector((0.0, 0.0, 0.0))        # the house's front door (its threshold); the garden and street are toward -Y
rng = np.random.default_rng(2018)


def house_row(x0, n, w=5.5, brick=None, stone=None):
    """Two-storey brick houses with white sash windows, a door each, a slate roof."""
    for k in range(n):
        x = x0 + k * w
        box("House", (x, 4.0, 3.3), (w - 0.05, 8.0, 6.6), brick)
        box("Roof", (x, 4.0, 7.3), (w + 0.1, 8.4, 1.6), pbr("Slate", (0.18, 0.19, 0.21), 0.6))
        for (dx, z) in ((-1.4, 1.6), (1.2, 1.6), (-1.4, 4.6), (1.2, 4.6)):
            if k == 0 and dx > 0 and z < 2:
                continue                                        # that is where the front door is
            box("Sash", (x + dx, -0.02, z), (1.1, 0.06, 1.5), pbr("SashWhite", (0.85, 0.85, 0.82), 0.4))
            box("SashGlass", (x + dx, -0.05, z), (0.95, 0.02, 1.35), pbr("SashGlass", (0.04, 0.05, 0.06), 0.05, 0.0, **{'Coat Weight': 1.0}))
            box("SashBar", (x + dx, -0.07, z), (0.95, 0.02, 0.04), pbr("SashWhite2", (0.85, 0.85, 0.82), 0.4))
            box("Lintel", (x + dx, -0.04, z + 0.85), (1.3, 0.1, 0.18), stone)
        box("Chimney", (x + 2.0, 6.0, 8.6), (0.8, 0.6, 1.4), brick)


def build(variant=None):
    c = {}
    world_flat((0.62, 0.65, 0.7), 1.0)
    brick = ph.texture("red_brick_03", scale=1.0)
    stone = pbr("Portland", (0.7, 0.68, 0.62), 0.7)
    house_row(-1.2, 1, brick=brick, stone=stone)                       # our house: door at x = 0
    house_row(-12.2, 2, brick=brick, stone=stone); house_row(4.3, 3, brick=brick, stone=stone)
    # the front door: painted, a brass lever handle, a fanlight and a step
    door_m = pbr("FrontDoor", (0.12, 0.18, 0.22), 0.35, 0.0, **{'Coat Weight': 0.6})
    box("DoorLeafF", (0.0, -0.04, 1.05), (0.95, 0.06, 2.1), door_m, bevel=0.01)
    for (dz, hh) in ((0.55, 0.7), (1.5, 0.8)):
        for dx in (-0.22, 0.22):
            box("DoorPanel", (dx, -0.075, dz), (0.32, 0.01, hh), door_m, bevel=0.01)
    box("Fanlight", (0, -0.03, 2.3), (0.95, 0.04, 0.3), pbr("FanGlass", (0.05, 0.06, 0.07), 0.05, 0.0, **{'Coat Weight': 1.0}))
    box("DoorStep", (0, -0.35, 0.08), (1.3, 0.6, 0.16), stone)
    brass = pbr("HandleBrass", (0.62, 0.48, 0.24), 0.25, 1.0)
    handle = joinm([box("Rose", (0.0, 0.0, 0.0), (0.05, 0.012, 0.16), brass, bevel=0.004),
                    cyl("LeverNeck", (0.0, -0.025, 0.04), 0.008, 0.04, brass, verts=12, rot=(math.radians(90), 0, 0)),
                    box("Lever", (-0.055, -0.045, 0.04), (0.12, 0.018, 0.018), brass, bevel=0.006)], "DoorHandle")
    handle.location = (0.36, -0.08, 1.0)
    c["handle"] = handle.location.copy()
    box("Number", (0, -0.075, 1.75), (0.12, 0.005, 0.12), brass)
    # front garden: low brick wall, gate gap, path, hedges and shrubs (scanned)
    box("Path", (0, -2.5, 0.01), (1.1, 4.6, 0.02), ph.texture("concrete_pavers", scale=0.8))
    box("Garden", (0, -2.5, 0.0), (16, 4.6, 0.02), ph.texture("forest_floor" if False else "gravel_floor", scale=0.6))
    for (x0, x1) in ((-8.0, -0.7), (0.7, 8.0)):
        box("GardenWall", ((x0 + x1) / 2, -4.85, 0.45), (x1 - x0, 0.3, 0.9), brick)
    ph_instances("shrub_02", [((-2.2, -3.2, 0), 0.4, 1.0), ((2.4, -3.0, 0), 2.0, 1.1), ((-4.5, -1.5, 0), 1.0, 0.9), ((4.2, -1.8, 0), 3.0, 1.0)])
    ph_instances("shrub_04", [((-1.5, -1.0, 0), 0.0, 0.8), ((1.6, -1.2, 0), 1.0, 0.8)])
    # pavement, road, the far side; a spire beyond the roofs
    box("Pave", (0, -6.0, -0.01), (60, 2.0, 0.12), ph.texture("concrete_pavers", scale=0.8))
    box("Road", (0, -10.0, -0.08), (60, 6.0, 0.1), ph.texture("asphalt_02", scale=0.25))
    from pbkit import masonry_facade                                       # the houses across the road
    box("OppositeRow", (0, -18.0, 3.3), (60, 8, 6.6), masonry_facade("OppBrick", (0.45, 0.24, 0.17), 3.2, 2.75, 1.1, 1.5, 0.0, frame_col=(0.85, 0.85, 0.82)))
    box("OppRoofs", (0, -18.0, 7.3), (60, 8.4, 1.6), pbr("Slate2", (0.18, 0.19, 0.21), 0.6))
    tower = pbr("CathedralStone", (0.62, 0.6, 0.55), 0.8)
    box("Tower", (-30.0, 80.0, 25.0), (8, 8, 50), tower)
    bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=4.5, radius2=0.1, depth=52, location=(-30.0, 80.0, 76.0))
    sp = bpy.context.active_object; sp.name = "Spire"; sp.data.materials.append(tower)
    haze((-20, 50, 20), (120, 80, 60), density=0.004, color=(0.8, 0.84, 0.9), anis=0.2)
    # police tape across the gate and along the wall, stirring (wave modifier)
    tm = bpy.data.materials.new("PoliceTape"); tm.use_nodes = True
    N = tm.node_tree.nodes; L = tm.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); ck = N.new("ShaderNodeTexChecker"); ck.inputs['Scale'].default_value = 40
    L.new(tc.outputs['UV'], ck.inputs['Vector']); ck.inputs['Color1'].default_value = (0.04, 0.1, 0.45, 1); ck.inputs['Color2'].default_value = (0.85, 0.85, 0.85, 1)
    L.new(ck.outputs['Color'], p.inputs['Base Color']); p.inputs['Roughness'].default_value = 0.35
    for (x0, x1, y) in ((-1.0, 1.0, -4.9), (-8.0, 8.0, -5.25)):
        bpy.ops.mesh.primitive_grid_add(x_subdivisions=80, y_subdivisions=2, size=1, location=((x0 + x1) / 2, y, 1.0), rotation=(math.radians(90), 0, 0))
        t = bpy.context.active_object; t.name = "Tape"; t.scale = (x1 - x0, 0.06, 1); t.data.materials.append(tm)
        wv = t.modifiers.new("flutter", 'WAVE'); wv.use_normal = True; wv.height = 0.03; wv.width = 0.6; wv.speed = 0.04
        for x in (x0, x1):
            cyl("TapePost", (x, y, 0.5), 0.02, 1.0, pbr("PostM", (0.3, 0.3, 0.3), 0.5), verts=8)
    for k, x in enumerate((-6.0, 6.0)):
        ph.model("street_lamp_01", loc=(x, -6.6, 0))
    # investigators in protective suits
    c["suits"] = []
    for k in range(2):
        h = person(f"UKSuit{k}", 1.0 if k == 0 else 0.0, 38, "male_casualsuit01" if k == 0 else "female_elegantsuit01", None)
        recolor(h, "casualsuit01" if k == 0 else "elegantsuit01", (0.84, 0.85, 0.82))
        protective_gear(h)
        c["suits"].append(h)
    animate(c, 0.0, "street")
    return c


def animate(c, sec, move):
    s0, s1 = c["suits"]
    if move in ("street", "handle"):
        for h in (s0, s1):
            for o in [h.arm] + list(h.parts):
                o.hide_render = True
            for o in bpy.data.objects:
                if o.parent == h.arm:
                    o.hide_render = True
    else:
        for h in (s0, s1):
            for o in [h.arm] + list(h.parts):
                o.hide_render = False
            for o in bpy.data.objects:
                if o.parent == h.arm:
                    o.hide_render = False
        stand(s0, (0.45, -0.75, 0.16), math.radians(180 - 10))           # at the door, facing it (+Y)
        nod(s0, "spine04", 16); nod(s0, "head", 16)
        hand_to(s0, "R", c["handle"] + Vector((0.0, -0.12, -0.02)), curl=30)
        stand(s1, (-0.55, -1.6, 0.0), math.radians(180 + 20))
        hand_to(s1, "L", s1.bone_head("spine03") + Vector((0.15, -0.3, -0.1)), curl=40)
        look(s1, c["handle"], 0.8)
    bpy.context.view_layer.update()


def _push(a, b, ta, tb, lens):
    return lambda c, t: (Vector(a).lerp(Vector(b), ease(t)), Vector(ta).lerp(Vector(tb), ease(t)), lens)


def _anim(move):
    return lambda c, t: animate(c, t * DUR[move], move)


H = Vector((0.36, -0.1, 1.0))
MOVES = {
    "street": dict(kind="anim", dof=8.0, far=200.0, anim=_anim("street"), cam=_push((4.0, -13.5, 1.8), (2.5, -13.0, 1.85), (-10.0, 10.0, 7.0), (-9.0, 10.0, 7.5), 26),
                   focus=lambda c, t: Vector((0, -4.9, 1.0))),
    "suits": dict(kind="anim", dof=4.0, far=40.0, anim=_anim("suits"), cam=_push((2.6, -5.6, 1.6), (2.2, -5.0, 1.6), (0.0, -0.5, 1.3), (0.0, -0.4, 1.3), 32),
                  focus=lambda c, t: Vector((0.2, -0.8, 1.3))),
    "handle": dict(kind="anim", dof=1.4, far=6.0, anim=_anim("handle"), cam=_push((H.x - 0.6, H.y - 1.3, H.z + 0.25), (H.x - 0.22, H.y - 0.5, H.z + 0.08), tuple(H), tuple(H), 50),
                   focus=lambda c, t: H),
    "path": dict(kind="anim", dof=5.6, far=40.0, anim=_anim("path"), cam=_push((0.2, -1.6, 1.6), (0.3, -7.2, 1.7), (0.0, 0.0, 1.2), (0.0, -1.0, 1.2), 30),
                 focus=lambda c, t: Vector((0.0, -1.0, 1.2))),
}
