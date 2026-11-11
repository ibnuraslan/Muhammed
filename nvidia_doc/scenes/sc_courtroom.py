"""CH3 SET 4 (dramatization): an empty federal-style courtroom, house style. Raised wooden bench, a round seal on the
panelled wall behind it (generic, no real emblem), flags either side, counsel tables, gallery benches, tall windows.
  push  (A): slow push down the aisle toward the bench
  clerk (B): a clerk stacks case files on the bench beside the gavel
"""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
from human import Human, add_asset, pose_walk, fingers_curl, _world_verts, reach
from sc_corp import arms_down

EXPOSURE = -0.2
DUR = {"push": 5.0, "clerk": 4.5}         # estimates until the chapter 3 voiceover arrives


def build(variant=None):
    c = {}
    rng = np.random.default_rng(17)
    world_sky(sun_elev_deg=22, sun_rot_deg=100, strength=0.4, tint=(0.95, 0.96, 1.0))
    sun(22, 100, energy=2.2, color=(1.0, 0.94, 0.86), angle_deg=1.2)
    oak = wood("CourtOak", (0.16, 0.09, 0.045), (0.32, 0.19, 0.1), scale=(0.3, 6, 6), rough=0.35, coat=0.35)
    dark = wood("CourtDark", (0.07, 0.04, 0.02), (0.16, 0.09, 0.045), scale=(0.3, 6, 6), rough=0.3, coat=0.4)
    box("Floor", (0, 4, -0.01), (14, 20, 0.02), fabric("CourtCarpet", (0.16, 0.06, 0.05), 0.95, 0.2, 500))
    box("WallBack", (0, 12.5, 4), (14, 0.2, 8), oak)
    box("WallL", (-7, 4, 4), (0.2, 20, 8), pbr("CourtPlaster", (0.62, 0.6, 0.55), 0.85))
    box("Ceiling", (0, 4, 8), (14, 20, 0.2), pbr("CourtCeil", (0.7, 0.68, 0.64), 0.85))
    # right wall: tall windows
    wall = pbr("CourtPlaster2", (0.62, 0.6, 0.55), 0.85)
    for k in range(6):
        box("Pier", (7, -4 + k * 3.2, 4), (0.2, 1.0, 8), wall)
        box("Win", (7.05, -2.4 + k * 3.2, 4.2), (0.02, 2.2, 5.0), glass("CourtGlass", (0.9, 0.93, 0.95), 0.02))
    box("WinLow", (7, 4, 0.8), (0.2, 20, 1.6), wall); box("WinHigh", (7, 4, 7.4), (0.2, 20, 1.2), wall)
    pt = bpy.data.lights.new("Portal", 'AREA'); pt.shape = 'RECTANGLE'; pt.size = 20; pt.size_y = 5; pt.cycles.is_portal = True
    po = bpy.data.objects.new("Portal", pt); bpy.context.collection.objects.link(po); po.location = (7.1, 4, 4.2); po.rotation_euler = (0, math.radians(-90), 0)
    # the bench, the clerk's desk, the witness box
    box("Bench", (0, 10.6, 0.9), (5.0, 1.4, 1.8), dark, bevel=0.02)
    box("BenchTop", (0, 10.6, 1.82), (5.2, 1.5, 0.05), oak)
    box("BenchDais", (0, 11.0, 0.2), (6.0, 2.4, 0.4), oak)
    box("JudgeChair", (0, 11.6, 1.5), (0.8, 0.6, 1.8), pbr("JudgeLeather", (0.04, 0.025, 0.02), 0.4, 0.0, **{'Coat Weight': 0.4}), bevel=0.06)
    box("ClerkDesk", (-3.6, 9.6, 0.55), (2.2, 0.9, 1.1), dark, bevel=0.02)
    box("Witness", (3.6, 9.6, 0.6), (1.6, 1.4, 1.2), dark, bevel=0.02)
    # a generic round seal (concentric rings, no emblem) and two flags on stands
    gold = pbr("SealGold", (0.7, 0.52, 0.22), 0.3, 1.0)
    cyl("Seal", (0, 12.38, 4.6), 1.1, 0.06, pbr("SealBlue", (0.08, 0.12, 0.25), 0.5), verts=96, rot=(math.radians(90), 0, 0))
    for r_ in (1.12, 0.9, 0.45):
        bpy.ops.mesh.primitive_torus_add(major_radius=r_, minor_radius=0.025, location=(0, 12.34, 4.6), rotation=(math.radians(90), 0, 0))
        bpy.context.active_object.data.materials.append(gold)
    import os
    gen = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "generated"); fimg = os.path.join(gen, "us_flag.png")
    if not os.path.exists(fimg):
        import sc_capitol; sc_capitol.flag_image(fimg)
    fm = bpy.data.materials.new("Flag"); fm.use_nodes = True
    N = fm.node_tree.nodes; L = fm.node_tree.links; t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(fimg)
    tc = N.new("ShaderNodeTexCoord"); L.new(tc.outputs['UV'], t.inputs['Vector']); L.new(t.outputs['Color'], N["Principled BSDF"].inputs['Base Color'])
    for x in (-3.0, 3.0):
        cyl("FlagPole", (x, 12.0, 1.6), 0.03, 3.2, gold, verts=12)
        bpy.ops.mesh.primitive_grid_add(x_subdivisions=30, y_subdivisions=20, size=1, location=(x + 0.4, 12.0, 2.7), rotation=(math.radians(90), 0, 0))
        f = bpy.context.active_object; f.scale = (0.8, 1.2, 1); f.data.materials.append(fm)
        wv = f.modifiers.new("wave", 'WAVE'); wv.height = 0.03; wv.width = 0.4; wv.speed = 0.02
    # counsel tables, the bar rail, gallery benches
    for x in (-2.2, 2.2):
        box("Counsel", (x, 6.8, 0.74), (2.6, 1.0, 0.05), oak)
        for sx in (-1.1, 1.1):
            box("CLeg", (x + sx, 6.8, 0.37), (0.06, 0.9, 0.72), dark)
        for k in range(3):
            box("CChair", (x - 0.8 + k * 0.8, 6.0, 0.5), (0.5, 0.5, 0.9), pbr("Chair", (0.05, 0.03, 0.02), 0.4), bevel=0.04)
    box("BarRail", (0, 4.9, 0.5), (12, 0.12, 1.0), dark)
    for k in range(6):
        for x in (-3.2, 3.2):
            box("Pew", (x, 3.8 - k * 1.2, 0.45), (5.0, 0.45, 0.9), oak, bevel=0.03)
    # papers and the gavel on the bench (for the clerk shot)
    paper = pbr("CasePaper", (0.86, 0.85, 0.8), 0.8)
    manila = pbr("CaseFolder", (0.62, 0.5, 0.3), 0.8)
    stack = []
    for k in range(5):
        f_ = box("CaseFile", (0, 0, -30), (0.25, 0.33, 0.03), manila if k % 2 else paper, bevel=0.003)
        stack.append(f_)
    c["stack"] = stack
    cyl("GavelHead", (0.6, 10.3, 1.9), 0.035, 0.12, dark, verts=24, rot=(0, math.radians(90), 0))
    cyl("GavelHandle", (0.6, 10.15, 1.88), 0.012, 0.25, dark, verts=12, rot=(math.radians(90), 0, 0))
    cyl("SoundBlock", (0.6, 10.3, 1.855), 0.06, 0.02, dark, verts=32)
    # the clerk (standing at the bench, side on)
    h = Human("Clerk", gender=0.0, years=48, muscle=0.45, weight=0.45, height=0.5, eyelashes="eyelashes01")
    add_asset(h, "clothes", "female_elegantsuit01", val=0.2, rough=0.6); add_asset(h, "clothes", "shoes02", val=0.2); add_asset(h, "hair", "bob01", val=0.3)
    pose_walk(h, 0.0, stride=0.0, arm_swing=0.0)
    h.arm.rotation_euler = (0, 0, math.pi); h.arm.location = (-0.6, 9.55, 0.4); bpy.context.view_layer.update()     # on the dais, facing the bench
    vv = np.concatenate([_world_verts(o) for o in h.parts if o.type == 'MESH'])
    h.arm.location.z -= vv[:, 2].min() - 0.4; bpy.context.view_layer.update()
    arms_down(h, 0.0, 0)
    c["clerk"] = h
    for x in (-3, 0, 3):
        l = area_light((x, 6, 7.8), (0, 0, 0), 2.0, 160, (1.0, 0.92, 0.82)); l.visible_camera = False
    return c


def anim_clerk(c, t):
    """She sets the case files down one by one into a neat stack beside the gavel."""
    sec = t * DUR["clerk"]
    h = c["clerk"]; base = Vector((-0.55, 10.35, 1.86))
    n = len(c["stack"])
    placed = min(n, int(sec / 0.8) + 1)
    for k, f in enumerate(c["stack"]):
        if k < placed - 1:
            f.location = base + Vector((0, 0, 0.03 * k)); f.rotation_euler = (0, 0, 0.03 * (k % 2))
        elif k == placed - 1:
            u = min(1.0, (sec - 0.8 * k) / 0.8)
            src = Vector((-1.1, 9.9, 1.95)); dst = base + Vector((0, 0, 0.03 * k))
            f.location = src.lerp(dst, ease(u)) + Vector((0, 0, 0.12 * math.sin(math.pi * u))); f.rotation_euler = (0, 0, 0.3 * (1 - u))
        else:
            f.location = (0, 0, -30)
    cur = c["stack"][placed - 1].location
    reach(h, "R", cur + Vector((0.0, -0.12, 0.06)), Vector((0.3, -0.6, -0.6)), Vector((0.2, 1, -0.4)))
    reach(h, "L", cur + Vector((-0.18, -0.1, 0.06)), Vector((-0.6, -0.4, -0.6)), Vector((0.2, 1, -0.4)))
    fingers_curl(h, 30, thumb=15)
    h.rot("head", (-1, 0, 0), 14)
    bpy.context.view_layer.update()


MOVES = {
    "push": dict(kind="anim", dof=5.6, far=40.0, cam=lambda c, t: (Vector((0.0, -3.5, 1.5)).lerp(Vector((0.0, 1.5, 1.6)), ease(t)), Vector((0.0, 11.0, 2.6)), 30),
                 focus=lambda c, t: Vector((0.0, 10.6, 1.8))),
    "clerk": dict(kind="anim", dof=2.8, far=20.0, anim=anim_clerk,
                  cam=lambda c, t: (Vector((-2.6, 8.4, 2.1)).lerp(Vector((-2.3, 8.6, 2.05)), ease(t)), Vector((-0.4, 10.3, 1.85)), 40),
                  focus=lambda c, t: Vector((-0.5, 10.3, 1.9))),
}
