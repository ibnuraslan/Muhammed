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
    sec = t * DUR["presses"]; anim_common(c, sec)
    H.stand_at(c["man"], (4.2, -2.4, 0), math.radians(-30))


def anim_stacks(c, t):
    sec = t * DUR["stacks"]; anim_common(c, sec)
    h = c["man"]; H.stand_at(h, (3.6, -4.3, 0), math.radians(180))
    reach(h, "R", Vector((3.4, -3.55, 1.0)), Vector((0, 0, -1)), Vector((0, 1, -0.5)))
    reach(h, "L", Vector((3.8, -3.55, 1.0)), Vector((0, 0, -1)), Vector((0, 1, -0.5)))
    H.rotl(h, "spine03", (1, 0, 0), 15); H.look(h, 0, 25)


MOVES = {
    "presses": dict(kind="anim", dof=None, far=40, anim=anim_presses,
                    cam=lambda c, t: (Vector((-7.5, -3.0, 1.2)).lerp(Vector((-2.5, -2.8, 1.4)), ease(t)), Vector((-4.0, 0.0, 1.5)).lerp(Vector((1.0, 0.0, 1.6)), ease(t)), 26)),
    "stacks": dict(kind="anim", dof=2.8, far=20, anim=anim_stacks,
                   cam=lambda c, t: (Vector((1.2, -4.6, 1.45)).lerp(Vector((1.6, -4.5, 1.4)), ease(t)), Vector((2.4, -3.4, 0.95)), 32),
                   focus=lambda c, t: Vector((2.4, -3.4, 0.95))),
}
