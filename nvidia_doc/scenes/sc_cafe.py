"""Title background (dramatization): night, rain. A warm cafe seen from the street through a rain-covered window.
The man in the black leather jacket and the woman sit side by side at a small table, cups between them.
The camera pushes slowly toward the glass while focus racks from the raindrops to the two of them."""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
from human import pose_sit, fingers_curl, rotate_bone, aim_bone, reset_pose, _world_verts
from people import man, woman

EXPOSURE = 0.5
GLASS_Y = 0.0          # window line; street is y < 0, cafe interior y > 0


def seated(h, x, y, rot_z, lean=6, cup_hand="R", turn=0.0):
    pose_sit(h, lean=lean)
    # forearms forward onto the table top, hands near the cup
    for sd, sg in (("L", 1), ("R", -1)):
        aim_bone(h.arm, f"upperarm01.{sd}", (0.12 * sg, -0.45, -0.88)); aim_bone(h.arm, f"upperarm02.{sd}", (0.12 * sg, -0.45, -0.88))
        aim_bone(h.arm, f"lowerarm01.{sd}", (-0.35 * sg, -0.94, 0.05)); aim_bone(h.arm, f"lowerarm02.{sd}", (-0.35 * sg, -0.94, 0.05))
        aim_bone(h.arm, f"wrist.{sd}", (-0.3 * sg, -0.95, -0.1))
    fingers_curl(h, 35, thumb=15)
    if turn:
        rotate_bone(h.arm, "neck01", (0, 0, 1), turn * 0.4); rotate_bone(h.arm, "head", (0, 0, 1), turn * 0.6)
    h.arm.rotation_euler = (0, 0, rot_z)
    h.arm.location = (x, y, 0)
    bpy.context.view_layer.update()
    w = np.concatenate([_world_verts(o) for o in h.parts if o.type == 'MESH'])
    h.arm.location.z -= w[:, 2].min()
    bpy.context.view_layer.update()


def build(variant=None):
    world_flat((0.006, 0.008, 0.014), 1.0)
    # ------------------------------------------------------------------ the cafe interior
    floor = box("Floor", (0, 3, -0.01), (12, 8, 0.02), wood("Floor", (0.04, 0.022, 0.012), (0.11, 0.06, 0.03), scale=(0.5, 6, 6), rough=0.35, coat=0.3))
    brick = pbr("Brick", (0.22, 0.1, 0.06), 0.8)
    nt = brick.node_tree; N = nt.nodes; L = nt.links; tc = N.new("ShaderNodeTexCoord")
    bt = N.new("ShaderNodeTexBrick"); bt.inputs['Scale'].default_value = 4.0
    bt.inputs['Color1'].default_value = (0.25, 0.11, 0.06, 1); bt.inputs['Color2'].default_value = (0.16, 0.07, 0.04, 1); bt.inputs['Mortar'].default_value = (0.3, 0.27, 0.24, 1)
    mpb = N.new("ShaderNodeMapping"); mpb.inputs['Rotation'].default_value = (math.radians(90), 0, 0)   # courses run horizontally on vertical walls
    L.new(tc.outputs['Object'], mpb.inputs['Vector']); L.new(mpb.outputs[0], bt.inputs['Vector'])
    L.new(bt.outputs['Color'], N["Principled BSDF"].inputs['Base Color'])
    bb = N.new("ShaderNodeBump"); bb.inputs['Strength'].default_value = 0.5; L.new(bt.outputs['Fac'], bb.inputs['Height']); L.new(bb.outputs['Normal'], N["Principled BSDF"].inputs['Normal'])
    box("BackWall", (0, 6.0, 1.6), (12, 0.1, 3.2), brick)
    box("Ceiling", (0, 3, 3.2), (12, 8, 0.05), pbr("Ceil", (0.05, 0.04, 0.035), 0.8))
    # bar counter with backlit shelves and bottles
    box("Counter", (1.8, 4.8, 0.55), (5, 0.7, 1.1), wood("Counter", (0.03, 0.015, 0.008), (0.09, 0.045, 0.02), rough=0.25, coat=0.6), bevel=0.01)
    box("Shelf", (1.8, 5.9, 1.7), (5, 0.2, 1.0), emissive("ShelfGlow", (1.0, 0.7, 0.4), 0.3))
    rng = np.random.default_rng(4)
    for k in range(30):
        cyl("Bottle", (-0.6 + k * 0.165, 5.75, 1.45 + 0.42 * (k % 2)), 0.035, 0.28, pbr("BottleG", tuple(rng.uniform(0.1, 0.6, 3)), 0.05, 0.0, **{'Transmission Weight': 0.9}), verts=16)
    # pendant lamps (warm pools), a plant, other tables
    for x, y in ((-1.6, 1.1), (0.6, 1.1), (2.8, 1.4), (-0.4, 3.2)):
        cyl("Cord", (x, y, 2.75), 0.004, 0.9, pbr("Cord", (0.02, 0.02, 0.02), 0.5), verts=8)
        bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=0.2, radius2=0.04, depth=0.22, location=(x, y, 2.2))
        shade = bpy.context.active_object; shade.data.materials.append(pbr("Shade", (0.6, 0.45, 0.25), 0.35, 1.0))
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=0.05, location=(x, y, 2.1))
        bpy.context.active_object.data.materials.append(emissive("Bulb", (1.0, 0.75, 0.45), 40))
        l = bpy.data.lights.new("Pend", 'SPOT'); l.energy = 140; l.spot_size = math.radians(80); l.spot_blend = 0.6; l.color = (1.0, 0.72, 0.42)
        o = bpy.data.objects.new("Pend", l); bpy.context.collection.objects.link(o); o.location = (x, y, 2.06)
    marble = pbr("Marble", (0.75, 0.73, 0.7), 0.15, 0.0, **{'Coat Weight': 0.5})
    iron = pbr("Iron", (0.02, 0.02, 0.02), 0.4, 0.8)
    for x, y in ((0.6, 1.1), (2.8, 1.4), (-0.4, 3.2)):
        cyl("TableTop", (x, y, 0.75), 0.38, 0.03, marble, verts=48); cyl("TableLeg", (x, y, 0.37), 0.03, 0.74, iron, verts=16)
    # their table: by the window, a bench along the side wall
    box("Bench", (-1.6, 1.75, 0.23), (1.6, 0.5, 0.46), fabric("BenchFab", (0.25, 0.05, 0.04), 0.7, 0.5, 400), bevel=0.04)
    box("BenchBack", (-1.6, 2.02, 0.75), (1.6, 0.12, 0.6), fabric("BenchFab2", (0.22, 0.045, 0.035), 0.7, 0.5, 400), bevel=0.04)
    cyl("TheirTable", (-1.6, 1.1, 0.75), 0.42, 0.03, marble, verts=48); cyl("TheirLeg", (-1.6, 1.1, 0.37), 0.03, 0.74, iron, verts=16)
    porcelain = pbr("Porcelain", (0.92, 0.92, 0.9), 0.12, 0.0, **{'Coat Weight': 0.6})
    for x in (-1.82, -1.4):
        cyl("Cup", (x, 1.02, 0.81), 0.04, 0.08, porcelain, verts=32); cyl("Saucer", (x, 1.02, 0.772), 0.07, 0.008, porcelain, verts=32)
        cyl("Coffee", (x, 1.02, 0.845), 0.036, 0.004, pbr("Coffee", (0.05, 0.02, 0.01), 0.1), verts=32)
    box("SideWall", (-2.6, 3, 1.6), (0.1, 8, 3.2), brick)
    # ------------------------------------------------------------------ the two of them, side by side, facing the window
    # warm key over their table + soft fill so faces read as shapes, not detail
    k = bpy.data.lights.new("TheirLamp", 'SPOT'); k.energy = 260; k.spot_size = math.radians(70); k.spot_blend = 0.7; k.color = (1.0, 0.72, 0.45)
    ko = bpy.data.objects.new("TheirLamp", k); bpy.context.collection.objects.link(ko); ko.location = (-1.6, 1.0, 2.1); point_at(ko, (-1.6, 1.5, 0.9))
    f = area_light((0.5, 0.2, 1.6), (0, 0, 0), 1.2, 25, (1.0, 0.8, 0.6)); point_at(f, (-1.6, 1.6, 1.1)); f.visible_camera = False; f.visible_glossy = False; f.visible_transmission = False
    m = man("Man"); seated(m, -1.95, 1.7, math.radians(8), lean=6, turn=12)
    w = woman("Woman"); seated(w, -1.25, 1.72, math.radians(-10), lean=4, turn=-6)
    # ------------------------------------------------------------------ the window and the street outside
    box("Glass", (0, GLASS_Y, 1.5), (6, 0.012, 2.6), rain_glass("Window", 70, 0.62))
    frame = pbr("WinFrame", (0.02, 0.025, 0.022), 0.4, 0.5)
    for x in (-3.0, 3.0):
        box("Jamb", (x, GLASS_Y, 1.5), (0.12, 0.14, 2.8), frame)
    box("Head", (0, GLASS_Y, 2.85), (6.2, 0.14, 0.12), frame); box("Sill", (0, GLASS_Y - 0.05, 0.12), (6.2, 0.25, 0.24), frame)
    sign = text_obj("CafeSign", "CAFE", (1.9, GLASS_Y - 0.02, 2.5), 0.32, emissive("SignTxt", (1.0, 0.8, 0.5), 6),
                    rot=(math.radians(90), 0, 0), font_path="/usr/share/fonts/opentype/inter/Inter-Light.otf", spacing=1.6)
    box("Pavement", (0, -2.5, -0.02), (14, 5, 0.04), pbr("WetPave", (0.03, 0.03, 0.032), 0.04, 0.0, **{'Specular IOR Level': 0.8}))
    # the building: brick facade around the window, upper floors, an awning, a lamp post on the kerb
    for x0, x1 in ((-9.0, -3.06), (3.06, 9.0)):
        box("Facade", ((x0 + x1) / 2, GLASS_Y + 0.12, 3.6), (x1 - x0, 0.24, 7.2), brick)
    box("FacadeTop", (0, GLASS_Y + 0.12, 5.05), (6.12, 0.24, 4.3), brick)
    upper = window_material("UpperWin", lit=(1.0, 0.8, 0.55), density=0.35, floor=2.6, bay=1.4, strength=0.6)
    for x in (-6.0, -2.0, 2.0, 6.0):
        box("UpperWin", (x, GLASS_Y - 0.01, 4.6), (1.3, 0.03, 1.5), upper)
    awning = fabric("Awning", (0.06, 0.12, 0.09), 0.8, 0.3, 300)
    box("Awning", (0, GLASS_Y - 0.6, 3.15), (6.6, 1.2, 0.06), awning, rot=(math.radians(-14), 0, 0))
    for x in (-7.5, 7.5):
        box("Door", (x * 0.62, GLASS_Y - 0.01, 1.15), (1.0, 0.04, 2.3), pbr("DoorWood", (0.05, 0.03, 0.02), 0.5))
    pole = pbr("LampPole", (0.03, 0.03, 0.03), 0.4, 0.8)
    cyl("LampPost", (3.8, -4.6, 2.2), 0.06, 4.4, pole, verts=12)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=0.22, location=(3.8, -4.6, 4.5))
    bpy.context.active_object.data.materials.append(emissive("LampGlobe", (1.0, 0.75, 0.45), 14))
    ll = bpy.data.lights.new("PostLight", 'POINT'); ll.energy = 400; ll.color = (1.0, 0.72, 0.42); ll.shadow_soft_size = 0.2
    lo = bpy.data.objects.new("PostLight", ll); bpy.context.collection.objects.link(lo); lo.location = (3.8, -4.6, 4.45)
    box("Road", (0, -9.0, -0.06), (40, 8, 0.1), pbr("WetRoad", (0.02, 0.02, 0.022), 0.05, 0.0, **{'Specular IOR Level': 0.8}))
    box("KerbC", (0, -5.0, 0.0), (40, 0.25, 0.14), pbr("KerbStone", (0.25, 0.25, 0.24), 0.4))
    # rain: curtains of streaks between the camera and the window, scrolled down every frame
    c_rain = []
    rm = bpy.data.materials.new("RainStreaks"); rm.use_nodes = True; 
    N = rm.node_tree.nodes; L = rm.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); tc = N.new("ShaderNodeTexCoord")
    mp = N.new("ShaderNodeMapping"); mp.inputs['Scale'].default_value = (14 * 45, 7 * 3.5, 1)          # ~2 cm x 28 cm streaks
    wn = N.new("ShaderNodeTexWhiteNoise"); wn.noise_dimensions = '2D'
    fl = N.new("ShaderNodeMath"); fl.operation = 'FLOOR'
    L.new(tc.outputs['Object'], mp.inputs['Vector']); L.new(mp.outputs[0], wn.inputs['Vector'])
    gt = N.new("ShaderNodeMath"); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = 0.93; L.new(wn.outputs['Value'], gt.inputs[0])
    sc = N.new("ShaderNodeMath"); sc.operation = 'MULTIPLY'; sc.inputs[1].default_value = 0.35; L.new(gt.outputs[0], sc.inputs[0])
    tr = N.new("ShaderNodeBsdfTransparent"); gl = N.new("ShaderNodeEmission"); gl.inputs['Color'].default_value = (0.75, 0.8, 0.9, 1); gl.inputs['Strength'].default_value = 0.6
    mx = N.new("ShaderNodeMixShader"); L.new(sc.outputs[0], mx.inputs[0]); L.new(tr.outputs[0], mx.inputs[1]); L.new(gl.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], out.inputs['Surface'])
    for k, y in enumerate((-0.7, -2.0, -3.4, -5.2, -7.2)):
        for j in range(2):
            bpy.ops.mesh.primitive_plane_add(size=1, location=(0, y, 3.5 + j * 7.0), rotation=(math.radians(90), 0, 0))
            o = bpy.context.active_object; o.name = "Rain"; o.scale = (14, 7.0, 1); o.data.materials.append(rm)
            o.visible_shadow = False; o.visible_diffuse = False; o.visible_glossy = False
            c_rain.append((o, y, j))
    # neon behind the camera, for reflections in the glass
    for k, col in enumerate(((1.0, 0.2, 0.4), (0.2, 0.8, 1.0), (1.0, 0.6, 0.2))):
        nl = area_light((-3 + k * 3, -11, 3.0), (0, 0, 0), 1.6, 120, col); point_at(nl, (-3 + k * 3, 0, 1.5))
        nl.visible_camera = False; nl.visible_glossy = False; nl.visible_transmission = False   # coloured street light, never seen as a shape
    return dict(m=m, w=w, couple=Vector((-1.6, 1.6, 1.05)), glass=Vector((-1.4, GLASS_Y, 1.15)), rain=c_rain)


DUR = {"title_push": 2.84, "pull_back": 4.17}       # from the voiceover: 20.50-23.34 / 23.34-26.51 + 1 s tail


def rain_fall(c, sec):
    for o, y, j in c.get("rain", []):
        z = 3.5 + j * 7.0 - (sec * 7.5 * (1 + 0.15 * (y % 1))) % 7.0       # each curtain pair scrolls down and wraps
        o.location = (0.3 * (y % 0.7), y, z)


def anim_push(c, t):
    rain_fall(c, t * DUR["title_push"])


def anim_pull(c, t):
    rain_fall(c, DUR["title_push"] + t * DUR["pull_back"])


def _cam_pull(c, t):
    e = ease(t)
    start = Vector((-0.95, -1.55, 1.2)); end = Vector((0.6, -8.6, 1.75))
    tgt = (c["couple"] + Vector((0.3, 0, -0.05))).lerp(Vector((0.0, 0.0, 2.6)), e)
    return (start.lerp(end, e), tgt, 40 - 12 * e)


def _cam(c, t):
    e = ease(t)
    loc = Vector((-0.55, -2.6, 1.25)).lerp(Vector((-0.95, -1.55, 1.2)), e)
    return (loc, c["couple"] + Vector((0.3, 0, -0.05)), 40)


def _focus(c, t):
    k = ease((t - 0.25) / 0.5)                 # rack: raindrops -> the couple
    return c["glass"].lerp(c["couple"], k)


MOVES = {"title_push": dict(kind="anim", dof=2.2, far=20.0, cam=_cam, focus=_focus, anim=anim_push),
         "pull_back": dict(kind="anim", dof=4.0, far=30.0, cam=_cam_pull,
                           focus=lambda c, t: c["couple"].lerp(Vector((0.0, 0.0, 2.0)), ease(t)), anim=anim_pull)}
