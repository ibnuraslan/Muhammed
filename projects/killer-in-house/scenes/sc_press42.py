"""CH3: the 1942 press room. A rotary press rolls; folded papers with a 'SPIDER MAN' headline slide past on the
delivery belt (generic paper: no masthead).
  presses (A): low track along the turning press cylinders and the paper web.
  stacks  (B): close-medium on the belt as headline papers slide by; a pressman lifts a bundle.
"""
import os, math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
import house as H
from human import reach

DUR = {"presses": 5.0, "stacks": 4.5}
VARIANT_FOR = {k: k for k in DUR}
GEN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "out", "generated")


def front_page(path):
    import skia
    W, Hh = 900, 1300
    s = skia.Surface(W, Hh); c = s.getCanvas(); c.clear(skia.Color4f(0.88, 0.86, 0.8, 1))
    p = skia.Paint(AntiAlias=True); p.setColor4f(skia.Color4f(0.08, 0.08, 0.08, 1))
    slab = "/home/user/Muhammed/nvidia_doc/assets/fonts/RobotoSlab-ExtraBold.ttf"
    f1 = skia.Font(skia.Typeface.MakeFromFile(slab), 150)
    c.drawRect(skia.Rect.MakeXYWH(40, 60, W - 80, 6), p)
    c.drawString("'SPIDER", 60, 260, f1, p); c.drawString("MAN'", 60, 410, f1, p)
    c.drawRect(skia.Rect.MakeXYWH(40, 450, W - 80, 4), p)
    p.setColor4f(skia.Color4f(0.35, 0.35, 0.35, 1))
    rng = np.random.default_rng(2)
    for col in range(4):
        for k in range(38):
            w = 190 * (0.6 + 0.4 * rng.random()) if k % 9 else 120
            c.drawRect(skia.Rect.MakeXYWH(50 + col * 205, 490 + k * 20, w, 8), p)
    p.setColor4f(skia.Color4f(0.5, 0.5, 0.5, 1)); c.drawRect(skia.Rect.MakeXYWH(470, 500, 380, 300), p)
    s.makeImageSnapshot().save(path, skia.kPNG)
    return path


def paper_mat():
    os.makedirs(GEN, exist_ok=True)
    path = os.path.join(GEN, "spider_front.png")
    if not os.path.exists(path):
        front_page(path)
    m = bpy.data.materials.new("FrontPage"); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; tc = N.new("ShaderNodeTexCoord")
    t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(path); L.new(tc.outputs['UV'], t.inputs['Vector'])
    L.new(t.outputs['Color'], N["Principled BSDF"].inputs['Base Color']); N["Principled BSDF"].inputs['Roughness'].default_value = 0.85
    return m


def build(variant=None):
    if variant == "presses":                 # a dim print shop: a stack of fresh papers on a bench, a bundle drops on
        c = {}
        world_flat((0.01, 0.011, 0.013), 1.0)
        bpy.context.scene.view_settings.exposure = 0.6
        box("Floor", (0, 0, -0.02), (8, 8, 0.04), H.mat("conc"))
        box("WallB", (0, 1.6, 2.0), (8, 0.2, 4), H.mat("brick2"))
        box("Bench", (0, 0.4, 0.86), (2.4, 0.9, 0.06), H.mat("oak"), bevel=0.01)
        for sx in (-1.1, 1.1):
            for sy in (0.05, 0.75):
                box("BLeg", (sx, sy, 0.42), (0.07, 0.07, 0.84), H.mat("oak"))
        pm = paper_mat(); edge = pbr("PaperEdge", (0.82, 0.8, 0.74), 0.9)
        rng = np.random.default_rng(5)
        for k in range(22):                  # the stack: folded papers, slightly fanned; the top one shows the front page
            box("Fold", (0.02 * rng.normal(), 0.35 + 0.02 * rng.normal(), 0.9 + 0.012 * k), (0.42, 0.6, 0.011), edge).rotation_euler = (0, 0, 0.04 * rng.normal())
        bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0.35, 0.9 + 0.012 * 22 + 0.001)); top = bpy.context.active_object
        top.scale = (0.42, 0.6, 1); bpy.ops.object.transform_apply(scale=True); top.data.materials.append(pm)
        twine = pbr("Twine", (0.55, 0.42, 0.25), 0.9)
        bun = join([box("Bundle", (0, 0, 0), (0.6, 0.43, 0.22), edge, bevel=0.01), box("Tw1", (0, 0, 0), (0.62, 0.012, 0.235), twine), box("Tw2", (0, 0, 0), (0.012, 0.45, 0.235), twine)], "Bundle")
        c["bundle"] = bun; c["top_z"] = 0.9 + 0.012 * 22
        cyl("Shade", (0.1, 0.3, 2.2), 0.25, 0.12, pbr("ShadeG", (0.15, 0.2, 0.15), 0.4, 0.6), 24)
        H.point((0.1, 0.3, 2.08), 120, (1.0, 0.82, 0.58), 0.05)
        c["haze"] = haze((0, 0.3, 1.5), (3.0, 2.4, 2.4), density=0.02, color=(1.0, 0.95, 0.85), anis=0.6)
        c["dust"] = []
        mm = emissive("MoteM", (1.0, 0.9, 0.7), 1.5)
        for k in range(120):
            o = cyl("Mote", (rng.uniform(-0.9, 0.9), rng.uniform(-0.2, 0.9), rng.uniform(1.0, 2.0)), 0.0015, 0.003, mm, 6)
            o["p0"] = tuple(o.location); c["dust"].append(o)
    import look
        look.night_interior()
        return c
    c = {}
    world_flat((0.02, 0.022, 0.025), 1.0)
    bpy.context.scene.view_settings.exposure = 0.4
    box("Floor", (0, 0, -0.02), (20, 14, 0.04), H.mat("conc"))
    box("WallB", (0, 6, 3.5), (20, 0.3, 7), H.mat("brick2"))
    for x in range(-8, 9, 4):
        H.point((x, 0, 5.5), 300, (1.0, 0.85, 0.65), 0.3)
        cyl("Shade", (x, 0, 5.7), 0.4, 0.15, pbr("ShadeG", (0.15, 0.2, 0.15), 0.4, 0.6), 24)
    c["haze"] = haze((0, 0, 3), (20, 14, 6), density=0.01, color=(0.95, 0.9, 0.8), anis=0.5)
    ir = H.mat("iron"); steel = brushed_metal("PressSteel", (0.45, 0.46, 0.47))
    green = pbr("PressGreen", (0.07, 0.1, 0.08), 0.45, 0.4)
    c["rolls"] = []
    for k in range(4):                       # press units: side frames + cylinders
        x = -6 + k * 3.2
        for y in (-1.3, 1.3):
            box("Frame", (x, y, 1.4), (2.4, 0.25, 2.8), green, bevel=0.05)
        for j, (z, r) in enumerate(((0.8, 0.35), (1.55, 0.35), (2.3, 0.3))):
            cyl_ = cyl("Roll", (x, 0, z), r, 2.4, steel, 48, rot=(math.radians(90), 0, 0))
            cyl_["r"] = r; c["rolls"].append(cyl_)
        box("Web", (x + 1.6, 0, 1.2), (0.9, 2.2, 0.004), pbr("Newsprint", (0.85, 0.83, 0.77), 0.9), rot=(0, math.radians(-50), 0))
    box("WebTop", (0, 0, 2.62), (13, 2.2, 0.004), pbr("Newsprint2", (0.85, 0.83, 0.77), 0.9))
    # delivery belt with papers
    box("Belt", (2.0, -3.4, 0.9), (10, 0.9, 0.06), pbr("BeltRubber", (0.04, 0.04, 0.04), 0.7))
    for x in (-3, 7):
        box("BeltLeg", (x, -3.4, 0.45), (0.1, 0.8, 0.9), green)
    pm = paper_mat()
    c["papers"] = []
    for k in range(14):
        bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
        o = bpy.context.active_object; o.scale = (0.3, 0.43, 1); bpy.ops.object.transform_apply(scale=True)
        o.data.materials.append(pm); c["papers"].append(o)
    c["man"] = H.person("Pressman", "neighbour_m")
    return c


def anim_common(c, sec):
    for r in c["rolls"]:
        r.rotation_euler = (math.radians(90), sec * 2.2 / r["r"], 0)
    for k, o in enumerate(c["papers"]):
        x = -2.8 + ((sec * 0.9 + k * 0.72) % 10.0)
        o.location = (x, -3.4 + 0.04 * math.sin(k), 0.94 + 0.002 * k); o.rotation_euler = (0, 0, math.radians(90 + 4 * math.sin(k * 1.3)))


def anim_presses(c, t):
    sec = t * DUR["presses"]
    u = min(1.0, max(0.0, (sec - 1.0) / 0.45))
    z = c["top_z"] + 0.11 + 0.9 * (1 - u) ** 2
    bun = c["bundle"]; bun.location = (0.38, 0.3, z); bun.rotation_euler = (0, 0, math.radians(-25))
    for k, o in enumerate(c["dust"]):
        x0, y0, z0 = o["p0"]; kick = 0.03 * max(0.0, sec - 1.45)
        o.location = (x0 + 0.02 * math.sin(0.5 * sec + k), y0, z0 + 0.01 * math.sin(0.7 * sec + k) + kick)


def anim_stacks(c, t):
    sec = t * DUR["stacks"]; anim_common(c, sec)
    h = c["man"]; H.stand_at(h, (3.6, -4.3, 0), math.radians(180))
    reach(h, "R", Vector((3.4, -3.55, 1.0)), Vector((0, 0, -1)), Vector((0, 1, -0.5)))
    reach(h, "L", Vector((3.8, -3.55, 1.0)), Vector((0, 0, -1)), Vector((0, 1, -0.5)))
    H.rotl(h, "spine03", (1, 0, 0), 15); H.look(h, 0, 25)


MOVES = {
    "presses": dict(kind="anim", dof=4.0, far=40, anim=anim_presses,
                    cam=lambda c, t: (Vector((-0.45, -0.75, 1.75)).lerp(Vector((-0.25, -0.4, 1.6)), ease(t)), Vector((-0.05, 0.3, 1.15)), 40),   # slow push onto the headline
                    focus=lambda c, t: Vector((-0.05, 0.3, 1.17))),
    "stacks": dict(kind="anim", dof=2.8, far=20, anim=anim_stacks,
                   cam=lambda c, t: (Vector((1.2, -4.6, 1.45)).lerp(Vector((1.6, -4.5, 1.4)), ease(t)), Vector((2.4, -3.4, 0.95)), 32),
                   focus=lambda c, t: Vector((2.4, -3.4, 0.95))),
}
