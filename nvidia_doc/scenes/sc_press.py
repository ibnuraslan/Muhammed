"""CH2 SET 7A (dramatization): a newspaper press hall at night. A long web-offset press: rollers spinning, the
paper web racing through, folded copies riding a conveyor out of the folder. Low dolly along the press."""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
import skia, os

EXPOSURE = 0.0
DUR = {"press_run": 5.0}       # estimate until the chapter 2 voiceover arrives
GEN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "generated")


def newsprint(path, W=1024, H=1400):
    """A generic front page: masthead bar, headline bars, photo block, columns of grey text (nothing readable)."""
    s = skia.Surface(W, H); c = s.getCanvas(); c.clear(skia.Color4f(0.9, 0.89, 0.85, 1))
    p = skia.Paint(AntiAlias=True)
    p.setColor4f(skia.Color4f(0.08, 0.08, 0.09, 1)); c.drawRect(skia.Rect.MakeXYWH(60, 50, W - 120, 90), p)
    c.drawRect(skia.Rect.MakeXYWH(60, 190, W - 120, 46), p); c.drawRect(skia.Rect.MakeXYWH(60, 250, (W - 120) * 0.7, 46), p)
    p.setColor4f(skia.Color4f(0.4, 0.4, 0.42, 1)); c.drawRect(skia.Rect.MakeXYWH(60, 330, 560, 380), p)
    rng = np.random.default_rng(3)
    for col in range(3):
        y = 330 if col == 2 else 740
        while y < H - 60:
            p.setColor4f(skia.Color4f(0.45, 0.45, 0.47, 1)); c.drawRect(skia.Rect.MakeXYWH(60 + col * 310, y, rng.uniform(240, 290), 9), p); y += 22
    s.makeImageSnapshot().save(path, skia.kPNG); return path


def build(variant=None):
    c = {}
    world_flat((0.006, 0.007, 0.01), 1.0)
    os.makedirs(GEN, exist_ok=True)
    np_img = newsprint(os.path.join(GEN, "newsprint.png"))
    box("Floor", (0, 0, -0.01), (40, 20, 0.02), pbr("PressFloor", (0.12, 0.12, 0.125), 0.4, 0.0, **{'Coat Weight': 0.2}))
    box("Wall", (0, 7, 5), (40, 0.2, 10), pbr("PressWall", (0.1, 0.1, 0.11), 0.8))
    steel = pbr("PressSteel", (0.18, 0.2, 0.22), 0.35, 0.8); green = pbr("PressGreen", (0.07, 0.2, 0.16), 0.5, 0.3)
    chrome = pbr("Roller", (0.7, 0.7, 0.72), 0.12, 1.0)
    rollers = []
    for k in range(6):                                  # six printing units in a row along X
        x = -12 + k * 4.2
        box("UnitL", (x, -0.9, 2.2), (2.6, 0.3, 4.4), green, bevel=0.05); box("UnitR", (x, 0.9, 2.2), (2.6, 0.3, 4.4), green, bevel=0.05)
        box("UnitTop", (x, 0, 4.45), (2.6, 2.1, 0.15), steel)
        for j, (dx, z) in enumerate(((-0.6, 1.4), (0.6, 1.4), (-0.6, 2.6), (0.6, 2.6), (0.0, 3.5))):
            r = cyl("Roller", (x + dx, 0, z), 0.32, 1.5, chrome, verts=48, rot=(math.radians(90), 0, 0))
            rollers.append((r, 1 if j % 2 else -1))
        box("Walkway", (x, -1.6, 1.8), (2.6, 0.8, 0.06), pbr("Grate", (0.3, 0.3, 0.32), 0.5, 0.8))
        for sx in (-1.2, 1.2):
            cyl("Rail", (x + sx, -1.95, 2.3), 0.025, 1.0, pbr("RailY", (0.8, 0.6, 0.05), 0.4), verts=8)
    c["rollers"] = rollers
    # the paper web: a long strip threaded through all units; its texture scrolls with the run (object shifts + wraps)
    pm = bpy.data.materials.new("Web"); pm.use_nodes = True
    N = pm.node_tree.nodes; L = pm.node_tree.links; p = N["Principled BSDF"]
    t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(np_img); t.extension = 'REPEAT'
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.inputs['Scale'].default_value = (12, 1, 1)
    L.new(tc.outputs['UV'], mp.inputs['Vector']); L.new(mp.outputs[0], t.inputs['Vector']); L.new(t.outputs['Color'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.85
    sp = N.new("ShaderNodeValue"); d = sp.outputs[0].driver_add("default_value").driver; d.type = 'SCRIPTED'; d.expression = "frame * 0.07"
    cmb = N.new("ShaderNodeCombineXYZ"); L.new(sp.outputs[0], cmb.inputs[0]); L.new(cmb.outputs[0], mp.inputs['Location'])
    bpy.ops.mesh.primitive_plane_add(size=1, location=(-1.5, 0, 2.0), rotation=(math.radians(90), 0, 0))
    web = bpy.context.active_object; web.scale = (25, 1.2, 1); web.data.materials.append(pm)
    # the folder and the conveyor of folded copies
    box("Folder", (11.5, 0, 1.6), (2.2, 2.0, 3.2), green, bevel=0.05)
    box("Conveyor", (15.5, -0.2, 0.9), (6.0, 0.9, 0.08), pbr("Belt", (0.04, 0.04, 0.04), 0.7))
    cm = bpy.data.materials.new("Copy"); cm.use_nodes = True
    Nn = cm.node_tree.nodes; Ll = cm.node_tree.links; tt = Nn.new("ShaderNodeTexImage"); tt.image = bpy.data.images.load(np_img)
    tcc = Nn.new("ShaderNodeTexCoord"); Ll.new(tcc.outputs['UV'], tt.inputs['Vector']); Ll.new(tt.outputs['Color'], Nn["Principled BSDF"].inputs['Base Color'])
    copies = []
    for k in range(18):
        o = box("Copy", (0, 0, 0), (0.42, 0.3, 0.03), cm)
        o.rotation_euler = (0, 0, math.radians(8))
        copies.append((o, k * 0.33))
    c["copies"] = copies
    # work lights over the press, warm, and a cool spill from a doorway
    for k in range(6):
        l = bpy.data.lights.new("Work", 'SPOT'); l.energy = 900; l.spot_size = math.radians(70); l.spot_blend = 0.6; l.color = (1.0, 0.82, 0.6)
        o = bpy.data.objects.new("Work", l); bpy.context.collection.objects.link(o); o.location = (-12 + k * 4.2, -2.5, 7.0); point_at(o, (-12 + k * 4.2, 0, 2.0))
    cool = area_light((18, -6, 3), (0, 0, 0), 4, 400, (0.6, 0.72, 1.0)); point_at(cool, (12, 0, 1.5)); cool.visible_camera = False
    haze((0, 0, 4), (40, 14, 8), density=0.006, color=(0.9, 0.9, 1.0), anis=0.5)
    return c


def anim_press(c, t):
    sec = t * DUR["press_run"]
    for r, sg in c["rollers"]:
        r.rotation_euler = (math.radians(90), sg * sec * 9.0, 0)
    for o, ph in c["copies"]:
        u = (ph + sec * 0.9) % 6.0                           # copies ride the conveyor away from the folder
        o.location = (12.6 + u, -0.2 + 0.02 * math.sin(ph * 7), 0.96 + 0.0)


MOVES = {"press_run": dict(kind="anim", dof=4.0, far=40.0, anim=anim_press,
                           cam=lambda c, t: (Vector((-8.0 + 9.0 * ease(t), -4.2, 1.4)), Vector((-4.0 + 9.0 * ease(t), 0.0, 2.2)), 32),
                           focus=lambda c, t: Vector((-4.0 + 9.0 * ease(t), 0.0, 2.2)))}
