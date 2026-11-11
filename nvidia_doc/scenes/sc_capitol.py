"""A neoclassical domed legislative building (stands in for Washington): dusk and floodlit-night variants."""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *

VARIANT_FOR = {"night_rise": "night", "dawn_push": "dawn"}
DUR = {"dawn_push": 7.5}            # estimate until the chapter 1 voiceover arrives
EXPOSURE = -1.0


def colonnade(x0, y, n, spacing, h, r, mat, along="x"):
    col = cyl("ColP", (0, 0, -100), r, h, mat, verts=24)
    out = []
    for k in range(n):
        p = (x0 + k * spacing, y, h / 2) if along == "x" else (y, x0 + k * spacing, h / 2)
        out.append(instance(col, p))
    return out


def build(variant=None):
    night = variant == "night"
    if night:
        bpy.context.scene.view_settings.exposure = 0.6
        world_flat((0.008, 0.012, 0.03), 1.0)
    else:
        world_sky(sun_elev_deg=3.0, sun_rot_deg=200, strength=0.55, tint=(1.0, 0.9, 0.85), aerosol=2.0)
        sun(3.0, 290, energy=2.2, color=(1.0, 0.6, 0.4), angle_deg=1.0)
    marble = pbr("Marble", (0.72, 0.70, 0.66), 0.45)
    nt = marble.node_tree; N = nt.nodes; L = nt.links; tc = N.new("ShaderNodeTexCoord")
    n = N.new("ShaderNodeTexNoise"); n.inputs['Scale'].default_value = 0.6; n.inputs['Detail'].default_value = 8
    L.new(tc.outputs['Object'], n.inputs['Vector'])
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 0.25
    mx.inputs[6].default_value = (0.72, 0.70, 0.66, 1); L.new(n.outputs['Color'], mx.inputs[7]); L.new(mx.outputs[2], N["Principled BSDF"].inputs['Base Color'])
    winm = window_material("Win", lit=(1.0, 0.8, 0.55), density=0.55 if night else 0.3, floor=5.5, bay=3.2, strength=2.5 if night else 1.2,
                           glass_col=(0.5, 0.48, 0.45))
    # dome on a drum ringed by columns
    cyl("Base", (0, 0, 10), 22, 20, marble, verts=96)
    ring = cyl("ColP", (0, 0, -100), 0.9, 16, marble, verts=20)
    for k in range(36):
        a = k / 36 * 2 * math.pi
        instance(ring, (25 * math.cos(a), 25 * math.sin(a), 28))
    cyl("Peristyle", (0, 0, 20.5), 26.5, 1.0, marble, verts=96)
    cyl("Entab", (0, 0, 36.6), 26.5, 1.4, marble, verts=96)
    cyl("Drum", (0, 0, 28), 21, 16, winm, verts=96)
    cyl("Attic", (0, 0, 40), 21.5, 6, marble, verts=96)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48, radius=21, location=(0, 0, 43))
    dome = bpy.context.active_object; dome.scale = (1, 1, 1.22); dome.data.materials.append(marble); bpy.ops.object.shade_smooth()
    cyl("LanternDrum", (0, 0, 70), 4, 8, winm, verts=32)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=4.2, location=(0, 0, 74)); bpy.context.active_object.data.materials.append(marble)
    cyl("Statue", (0, 0, 80), 0.9, 6, pbr("Bronze", (0.12, 0.09, 0.06), 0.4, 0.8), verts=16)
    # long wings with colonnaded fronts and a central portico
    for side in (-1, 1):
        box("Wing", (side * 75, 4, 12), (110, 46, 24), winm)
        box("WingCornice", (side * 75, 4, 24.6), (112, 48, 1.4), marble)
        box("WingAttic", (side * 75, 4, 27), (106, 42, 3.4), marble)
        colonnade(side * 75 - 50, -19.6, 26, 4.0, 22, 0.7, marble)
        box("WingSteps", (side * 75, -26, 0.6), (40, 10, 1.2), marble)
    box("Portico", (0, -26, 12), (40, 12, 24), marble)
    colonnade(-18, -32.5, 10, 4.0, 22, 0.9, marble)
    bpy.ops.mesh.primitive_cone_add(vertices=3, radius1=24, depth=8, location=(0, -30, 27.5), rotation=(math.radians(90), 0, 0))
    ped = bpy.context.active_object; ped.scale = (1, 0.34, 1); ped.data.materials.append(marble)
    for k in range(10):
        box("Step", (0, -40 - k * 1.2, 0.3 + k * -0.0), (46 - k * 0.0, 1.2, 0.6 + (9 - k) * 0.6), marble)
    lawn = box("Lawn", (0, -200, -0.5), (900, 360, 1), pbr("Lawn", (0.03, 0.05, 0.025), 0.9))
    box("Plaza", (0, -60, -0.45), (240, 40, 1), pbr("Plaza", (0.25, 0.24, 0.22), 0.7))
    if night:
        for (x, y) in ((-40, -110), (40, -110), (0, -120), (-90, -90), (90, -90)):
            l = bpy.data.lights.new("Flood", 'SPOT'); l.energy = 2.5e5; l.spot_size = math.radians(40); l.spot_blend = 0.5; l.color = (1.0, 0.88, 0.7)
            o = bpy.data.objects.new("Flood", l); bpy.context.collection.objects.link(o); o.location = (x, y, 2); point_at(o, (x * 0.3, 0, 45))
        haze((0, -60, 40), (500, 260, 90), density=0.0006, color=(0.7, 0.75, 0.9), anis=0.4)
    ctx = dict(dome=Vector((0, 0, 50)))
    if variant == "dawn":
        ctx.update(dawn_extras())
    return ctx


def flag_image(path):
    """US flag: 13 stripes, a blue canton with 50 stars."""
    from PIL import Image, ImageDraw
    W, H = 1900, 1000
    im = Image.new("RGB", (W, H), (255, 255, 255)); d = ImageDraw.Draw(im)
    for k in range(13):
        if k % 2 == 0:
            d.rectangle([0, k * H / 13, W, (k + 1) * H / 13], fill=(178, 34, 52))
    cw, ch = W * 0.4, H * 7 / 13
    d.rectangle([0, 0, cw, ch], fill=(60, 59, 110))
    for r in range(9):
        n = 6 if r % 2 == 0 else 5
        for k in range(n):
            x = cw * (k * 2 + (1 if r % 2 == 0 else 2)) / 12; y = ch * (r + 1) / 10
            pts = [(x + 18 * math.cos(math.pi / 2 + j * 4 * math.pi / 5), y - 18 * math.sin(math.pi / 2 + j * 4 * math.pi / 5)) for j in range(5)]
            d.polygon(pts, fill=(255, 255, 255))
    im.save(path); return path


def dawn_extras():
    """Autumn trees along the lawn, gravel paths, two flagpoles with waving flags, a few distant walkers."""
    import os
    rng = np.random.default_rng(10)
    out = {}
    gravel = pbr("Gravel", (0.42, 0.39, 0.34), 0.9)
    for x in (-22, 22):
        box("Path", (x, -150, -0.42), (6, 200, 1), gravel)
    box("CrossPath", (0, -95, -0.42), (120, 6, 1), gravel)
    # trees: a scanned tree (Poly Haven, CC0) instanced along both sides of the lawn, leaves turned to autumn
    import ph
    root, ms = ph.model("tree_small_02", loc=(0, 0, -300))
    tree = ms[0]
    for mat in tree.data.materials:
        N = mat.node_tree.nodes; L = mat.node_tree.links; pb = next((n for n in N if n.type == 'BSDF_PRINCIPLED'), None)
        if pb is None or not pb.inputs['Base Color'].links:
            continue
        src = pb.inputs['Base Color'].links[0].from_socket
        hs = N.new("ShaderNodeHueSaturation"); oi = N.new("ShaderNodeObjectInfo")
        mr = N.new("ShaderNodeMapRange"); mr.inputs['To Min'].default_value = 0.29; mr.inputs['To Max'].default_value = 0.42
        L.new(oi.outputs['Random'], mr.inputs['Value']); L.new(mr.outputs[0], hs.inputs['Hue'])
        hs.inputs['Saturation'].default_value = 1.15; hs.inputs['Value'].default_value = 0.9
        L.new(src, hs.inputs['Color']); L.new(hs.outputs['Color'], pb.inputs['Base Color'])
    for side in (-1, 1):
        for k in range(16):
            x = side * rng.uniform(32, 46); y = -60 - k * 13 + rng.uniform(-3, 3); sc_ = rng.uniform(3.4, 4.4)
            instance(tree, (x, y, 0.0), rot=(0, 0, rng.uniform(0, 6.28)), scale=(sc_, sc_, sc_))
    # flagpoles either side of the plaza, flags waving (Wave modifier: animates by itself, no keys)
    import tempfile
    gen = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "generated"); os.makedirs(gen, exist_ok=True)
    fimg = flag_image(os.path.join(gen, "us_flag.png"))
    fm = bpy.data.materials.new("Flag"); fm.use_nodes = True
    N = fm.node_tree.nodes; L = fm.node_tree.links; t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(fimg)
    tc = N.new("ShaderNodeTexCoord"); L.new(tc.outputs['UV'], t.inputs['Vector']); L.new(t.outputs['Color'], N["Principled BSDF"].inputs['Base Color'])
    N["Principled BSDF"].inputs['Roughness'].default_value = 0.8; N["Principled BSDF"].inputs['Sheen Weight'].default_value = 0.4
    pole = pbr("FlagPole", (0.75, 0.75, 0.74), 0.3, 1.0)
    for x in (-60, 60):
        cyl("FlagPole", (x, -75, 13), 0.18, 26, pole, verts=16)
        bpy.ops.mesh.primitive_grid_add(x_subdivisions=60, y_subdivisions=32, size=1, location=(x + 4.0, -75, 23.6), rotation=(math.radians(90), 0, 0))
        f = bpy.context.active_object; f.name = "Flag"; f.scale = (7.6, 4.0, 1); f.data.materials.append(fm)
        wv = f.modifiers.new("wave", 'WAVE'); wv.use_x = True; wv.use_y = False; wv.height = 0.35; wv.width = 2.2; wv.speed = 0.12
        wv.start_position_x = -3.8; wv.falloff_radius = 0.0; wv.narrowness = 1.5
        f.modifiers.new("sub", 'SUBSURF').levels = 1
    # a few people far up the path (small, walking slowly)
    out["walkers"] = []
    return out


def _cam_dawn(c, t):
    """Low over the lawn between the autumn trees, pushing slowly toward the dome."""
    e = ease(t)
    return (Vector((-6, -260, 2.2)).lerp(Vector((-3, -175, 3.0)), e), Vector((0, 0, 40 - 6 * e)), 45)


MOVES = {
    "dawn_push": dict(kind="anim", far=900.0, cam=_cam_dawn, title=("CHAPTER 1", "FOLLOW THE CHIPS", 18, 120)),
    "slow_push": dict(kind="plate", far=900.0, cam=lambda c, t: ((-70, -230, 8), (0, 0, 38), 50)),
    "dusk_push": dict(kind="plate", far=900.0, cam=lambda c, t: ((110, -210, 4), (0, 0, 42), 55)),
    "night_rise": dict(kind="plate", far=900.0, cam=lambda c, t: ((-30, -190, 3 + 12 * t), (0, 0, 45), 45)),
}
