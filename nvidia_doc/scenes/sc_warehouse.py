"""A logistics warehouse, house style.
  forklift  (CH1 10B): a forklift carries a pallet of crates down the aisle toward the doorway of a dark data hall
  lights_off (CH2 6A): shelves of boxed chips; the high-bay lights switch off row by row (frame drivers)
"""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
import ph

EXPOSURE = -0.3
DUR = {"forklift": 5.0, "lights_off": 5.0, "forklift_real": 11.0}       # estimates until the voiceover arrives
ROWS = 6


def build(variant=None):
    c = {}
    rng = np.random.default_rng(9)
    world_flat((0.01, 0.012, 0.015), 1.0)
    fl = pbr("WarehouseFloor", (0.32, 0.33, 0.34), 0.45, 0.0, **{'Coat Weight': 0.25})
    N = fl.node_tree.nodes; L = fl.node_tree.links; tc = N.new("ShaderNodeTexCoord")
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 0.8; nz.inputs['Detail'].default_value = 8; L.new(tc.outputs['Object'], nz.inputs['Vector'])
    rp = N.new("ShaderNodeValToRGB"); rp.color_ramp.elements[0].color = (0.26, 0.27, 0.28, 1); rp.color_ramp.elements[1].color = (0.38, 0.39, 0.4, 1)
    L.new(nz.outputs['Fac'], rp.inputs['Fac']); L.new(rp.outputs['Color'], N["Principled BSDF"].inputs['Base Color'])
    box("Floor", (0, 12, -0.01), (30, 40, 0.02), fl)
    paint = pbr("Line", (0.8, 0.65, 0.1), 0.6)
    for x in (-1.6, 1.6):
        box("AisleLine", (x, 12, 0.002), (0.1, 38, 0.004), paint)
    box("Ceiling", (0, 12, 9.0), (30, 40, 0.1), pbr("Roof", (0.15, 0.15, 0.16), 0.8))
    wall = pbr("Wall", (0.42, 0.43, 0.44), 0.85)
    box("WallEnd", (0, 31, 4.5), (30, 0.2, 9), wall)
    box("WallStart", (0, -7, 4.5), (30, 0.2, 9), wall)
    # pallet racking: orange beams, blue uprights, boxes on every level
    up = pbr("Upright", (0.05, 0.14, 0.35), 0.5, 0.4); beam = pbr("Beam", (0.8, 0.35, 0.05), 0.45, 0.3)
    card = [pbr(f"Carton{k}", col, 0.85) for k, col in enumerate(((0.55, 0.42, 0.26), (0.5, 0.38, 0.22), (0.62, 0.5, 0.33)))]
    label = pbr("Label", (0.9, 0.9, 0.88), 0.7)
    box_t = [box(f"CartonT{k}", (0, 0, -60), (0.55, 0.4, 0.35), m, bevel=0.01) for k, m in enumerate(card)]
    lab_t = box("LabelT", (0, 0, -60), (0.002, 0.2, 0.12), label)
    up_t = box("UpT", (0, 0, -70), (0.08, 0.08, 7.2), up); beam_t = box("BeamT", (0, 0, -70), (0.06, 2.7, 0.12), beam)
    for side in (-1, 1):
        x = side * 3.0
        for k in range(10):
            y = k * 2.8
            for dy in (-1.35, 1.35):
                instance(up_t, (x, y + dy, 3.6)); instance(up_t, (x + side * 1.1, y + dy, 3.6))
            for lvl in range(5):
                z = 0.15 + lvl * 1.45
                instance(beam_t, (x, y, z)); instance(beam_t, (x + side * 1.1, y, z))
                for j in range(4):
                    if rng.random() < 0.88:
                        bx = instance(box_t[rng.integers(3)], (x + side * 0.55, y - 1.0 + j * 0.66, z + 0.24), rot=(0, 0, rng.uniform(-0.05, 0.05)))
                        instance(lab_t, (x + side * 0.55 - side * 0.276, y - 1.0 + j * 0.66, z + 0.24))
    # high-bay lights in rows along the aisle; each row switches off at its own frame (lights_off)
    rows = []
    for r in range(ROWS):
        y = 1.0 + r * 4.6
        fix = box("HighBay", (0, y, 8.7), (0.8, 0.8, 0.12), pbr("Fixture", (0.3, 0.3, 0.32), 0.4, 0.8))
        m = bpy.data.materials.new(f"BayGlow{r}"); m.use_nodes = True
        Nn = m.node_tree.nodes; Ll = m.node_tree.links; Nn.clear()
        out = Nn.new("ShaderNodeOutputMaterial"); em = Nn.new("ShaderNodeEmission"); em.inputs['Color'].default_value = (1.0, 0.96, 0.9, 1)
        v = Nn.new("ShaderNodeValue")
        off_at = 1e6 if variant != "dark" else 30 + (ROWS - 1 - r) * 14
        expr = f"12 * (1 if frame < {off_at} else 0.0)"
        d = v.outputs[0].driver_add("default_value").driver; d.type = 'SCRIPTED'; d.expression = expr
        Ll.new(v.outputs[0], em.inputs['Strength']); Ll.new(em.outputs[0], out.inputs['Surface'])
        box("BayLens", (0, y, 8.63), (0.7, 0.7, 0.01), m)
        l = bpy.data.lights.new(f"Bay{r}", 'SPOT'); l.spot_size = math.radians(120); l.spot_blend = 0.6; l.color = (1.0, 0.95, 0.88)
        dl = l.driver_add("energy").driver; dl.type = 'SCRIPTED'; dl.expression = f"2600 * (1 if frame < {off_at} else 0.0)"
        o = bpy.data.objects.new(f"Bay{r}", l); bpy.context.collection.objects.link(o); o.location = (0, y, 8.6)
        rows.append(o)
    c["rows"] = rows
    # far end: a doorway into a dark data hall (a few status lights glowing inside)
    box("DoorFrame", (0, 30.9, 2.2), (3.6, 0.3, 4.4), pbr("DoorFrame", (0.1, 0.1, 0.11), 0.5, 0.6))
    box("Doorway", (0, 30.85, 2.0), (3.0, 0.3, 4.0), pbr("DarkHall", (0.004, 0.004, 0.006), 0.9))
    led = emissive("HallLed", (0.3, 1.0, 0.5), 8)
    for k in range(40):
        box("HallLed", (rng.uniform(-1.3, 1.3), 30.69, rng.uniform(0.5, 3.6)), (0.01, 0.002, 0.01), led)
    # the forklift with a pallet of crates
    yellow = pbr("ForkYellow", (0.8, 0.55, 0.05), 0.4, 0.2); black = pbr("ForkBlack", (0.03, 0.03, 0.03), 0.6)
    parts = [box("FBody", (0, 0, 0.75), (1.1, 1.8, 0.9), yellow, bevel=0.08),
             box("FCounter", (0, 0.75, 0.75), (1.15, 0.4, 0.95), yellow, bevel=0.08),
             box("FSeat", (0, 0.25, 1.35), (0.5, 0.5, 0.3), black, bevel=0.05),
             box("FMast", (0, -1.0, 1.5), (0.9, 0.12, 2.9), black),
             box("FRoofL", (-0.5, 0, 2.15), (0.06, 1.4, 0.06), black), box("FRoofR", (0.5, 0, 2.15), (0.06, 1.4, 0.06), black),
             box("FRoof", (0, 0, 2.2), (1.1, 1.4, 0.04), black)]
    for sx in (-0.5, 0.5):
        for sy in (-0.6, 0.6):
            parts.append(cyl("FWheel", (sx * 1.1, sy, 0.3), 0.3, 0.25, black, verts=24, rot=(0, math.radians(90), 0)))
    for sx in (-0.25, 0.25):
        parts.append(box("Fork", (sx, -1.65, 0.2), (0.12, 1.2, 0.05), black))
    parts.append(box("Pallet", (0, -1.65, 0.3), (1.0, 1.2, 0.14), pbr("PalletWood", (0.45, 0.34, 0.2), 0.8)))
    for j in range(2):
        for k in range(2):
            parts.append(box("Crate", (-0.25 + 0.5 * j, -1.95 + 0.6 * k, 0.65), (0.48, 0.55, 0.56), card[(j + k) % 3], bevel=0.01))
    fk = join(parts, "Forklift"); fk.location = (0, 2.0, 0)
    if variant in ("dark", "nofork", "realfork"):  # empty aisle / no toy vehicle (the block forklift was rejected)
        fk.hide_render = True; fk.hide_viewport = True
    c["forklift"] = fk
    if variant == "realfork":                      # CH5 8B: the realistic forklift from vehicles.py, a pallet of crates on its forks
        import vehicles
        real = vehicles.make("forklift", loc=(0, 2.0, 0), heading_deg=90)
        pal = box("RPallet", (0, 0, 0), (1.2, 1.0, 0.14), pbr("PalletWood", (0.45, 0.34, 0.2), 0.8))
        pal.parent = real; pal.location = (1.35, 0, 0.22)
        for j in range(2):
            for k in range(2):
                cr = box("RCrate", (0, 0, 0), (0.55, 0.48, 0.5), card[(j + k) % 3], bevel=0.01)
                cr.parent = real; cr.location = (1.08 + 0.56 * j, -0.25 + 0.5 * k, 0.55)
        c["forklift"] = real; c["fork_rot"] = math.pi / 2
    return c


VARIANT_FOR = {"lights_off": "dark", "crates": "nofork", "forklift_real": "realfork"}


def anim_forklift(c, t):
    sec = t * DUR["forklift"]
    c["forklift"].location = (0.0, 2.0 + (1.6 if c.get("fork_rot") else 3.2) * sec, 0.0)   # drives off toward the data-hall doorway
    c["forklift"].rotation_euler = (0, 0, c.get("fork_rot", math.pi))


MOVES = {
    "forklift": dict(kind="anim", dof=4.0, far=60.0, anim=anim_forklift,
                     cam=lambda c, t: (Vector((-1.2, -4.0, 1.6)).lerp(Vector((-0.8, -2.5, 1.7)), ease(t)), c["forklift"].location + Vector((0, 4, 1.0)), 32),
                     focus=lambda c, t: c["forklift"].location + Vector((0, 0, 1.0))),
    "lights_off": dict(kind="anim", dof=5.6, far=60.0,
                       cam=lambda c, t: (Vector((-0.5, -5.0, 2.2)).lerp(Vector((-0.3, -3.8, 2.3)), ease(t)), Vector((0, 20, 2.6)), 28),
                       focus=lambda c, t: Vector((0, 10, 2.5))),
    # CH5 8B: the realistic forklift drives its pallet of crates off down the aisle (camera follows, behind)
    "forklift_real": dict(kind="anim", dof=4.0, far=60.0, anim=lambda c, t: anim_forklift(c, t * DUR["forklift_real"] / DUR["forklift"]),
                          cam=lambda c, t: (Vector((-1.4, -3.2, 1.7)).lerp(Vector((-1.0, 0.5, 1.8)), ease(t)), c["forklift"].location + Vector((0, 3.5, 1.0)), 32),
                          focus=lambda c, t: c["forklift"].location + Vector((0, 0, 1.0))),
    # CH5 6B: a slow track along the loaded racking (stacked chip crates); the forklift idles across the far aisle
    "crates": dict(kind="anim", dof=3.5, far=60.0, anim=anim_forklift,
                   cam=lambda c, t: (Vector((-2.3, 1.0, 1.9)).lerp(Vector((-2.3, 6.5, 2.0)), ease(t)), Vector((3.0, 9.0, 2.0)), 34),
                   focus=lambda c, t: Vector((3.0, 7.5, 2.0))),
}
