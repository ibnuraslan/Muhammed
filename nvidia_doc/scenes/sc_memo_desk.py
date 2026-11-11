"""Illustration: a desk at night, a lamp pooling light on a folder. The pages are generated textures of
redaction bars only (no invented text). Variant 'letter' shows a letterhead page for the House letter."""
import os, math
import numpy as np
import bpy
from mathutils import Vector
from PIL import Image, ImageDraw
from kit import *

VARIANT_FOR = {"letter_push": "letter"}
EXPOSURE = 0.2
HERE = os.path.dirname(os.path.abspath(__file__))


def page_texture(path, kind="memo", seed=0):
    """A4-ish page image: only rules and black redaction bars."""
    W_, H_ = 1240, 1754
    im = Image.new("RGB", (W_, H_), (236, 232, 223)); d = ImageDraw.Draw(im)
    r = np.random.default_rng(seed)
    y = 140
    if kind == "letter":
        d.rectangle([W_ / 2 - 60, 90, W_ / 2 + 60, 150], fill=(60, 60, 64))      # seal placeholder
        y = 230
        d.line([(120, y), (W_ - 120, y)], fill=(80, 80, 84), width=3); y += 60
    else:
        d.rectangle([120, y, 520, y + 34], fill=(40, 40, 44)); y += 90
        d.line([(120, y), (W_ - 120, y)], fill=(60, 60, 64), width=2); y += 50
    while y < H_ - 180:
        if r.random() < 0.12:
            y += 40; continue
        x = 120
        lw = r.uniform(0.6, 1.0) * (W_ - 240)
        while x < 120 + lw:
            seg = r.uniform(50, 200)
            seg = min(seg, 120 + lw - x)
            if kind == "memo" and r.random() < 0.45:
                d.rectangle([x, y - 10, x + seg, y + 18], fill=(14, 14, 16))
            else:
                d.rectangle([x, y + 2, x + seg, y + 8], fill=(120, 118, 112))
            x += seg + 14
        y += 42
    im.save(path)
    return path


def paper_mat(name, tex):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(tex)
    L.new(t.outputs['Color'], p.inputs['Base Color']); p.inputs['Roughness'].default_value = 0.85
    p.inputs['Subsurface Weight'].default_value = 0.1
    return m


def page(name, loc, rot, tex):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=(0, 0, rot))
    o = bpy.context.active_object; o.name = name; o.scale = (0.21, 0.297, 1)
    o.data.materials.append(paper_mat(name, tex))
    return o


def build(variant=None):
    world_flat((0.004, 0.005, 0.008), 1.0)
    tex_dir = os.path.join(HERE, "..", "assets", "generated"); os.makedirs(tex_dir, exist_ok=True)
    memo = page_texture(os.path.join(tex_dir, "page_memo.png"), "memo", 4)
    memo2 = page_texture(os.path.join(tex_dir, "page_memo2.png"), "memo", 9)
    letter = page_texture(os.path.join(tex_dir, "page_letter.png"), "letter", 6)
    desk = box("Desk", (0, 0, 0.72), (1.8, 0.9, 0.04), wood("Desk", (0.02, 0.012, 0.007), (0.07, 0.04, 0.02), scale=(8, 0.4, 0.4), rough=0.3, coat=0.7))
    box("Room", (0, 0, 1.5), (8, 8, 3.0), pbr("Room", (0.02, 0.02, 0.025), 0.9)).data.polygons.foreach_set("use_smooth", [False] * 6)
    bpy.data.objects["Room"].data.flip_normals() if hasattr(bpy.data.objects["Room"].data, "flip_normals") else None
    manila = pbr("Manila", (0.52, 0.38, 0.2), 0.75)
    box("FolderBack", (-0.05, 0.02, 0.742), (0.25, 0.33, 0.003), manila, rot=(0, 0, 0.06))
    box("FolderFront", (-0.33, 0.04, 0.742), (0.25, 0.33, 0.003), manila, rot=(0, 0, -0.04))
    top = page("Page1", (-0.04, 0.0, 0.7465), 0.08, letter if variant == "letter" else memo)
    page("Page2", (-0.06, 0.03, 0.7455), 0.03, memo2)
    cyl("Pen", (0.22, -0.12, 0.748), 0.005, 0.14, pbr("Pen", (0.02, 0.02, 0.025), 0.2, 0.8), verts=16, rot=(math.radians(90), 0, 0.5))
    mug = cyl("Mug", (0.45, 0.18, 0.79), 0.045, 0.1, pbr("Mug", (0.6, 0.6, 0.62), 0.3), verts=32)
    # brass lamp: base, arm, conical shade with a spot inside
    brass = brushed_metal("Brass", (0.75, 0.55, 0.3), (0.2, 0.35), 0.3)
    cyl("LampBase", (-0.55, 0.3, 0.75), 0.09, 0.02, brass, verts=32)
    arm = box("LampArm", (-0.47, 0.22, 1.0), (0.02, 0.02, 0.5), brass, rot=(math.radians(-20), math.radians(18), 0)); arm.visible_shadow = False
    bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=0.12, radius2=0.04, depth=0.16, location=(-0.36, 0.12, 1.2), rotation=(math.radians(-150), math.radians(25), 0))
    shade = bpy.context.active_object; shade.data.materials.append(pbr("Shade", (0.05, 0.12, 0.07), 0.35, 0.6))
    sh = shade.modifiers.new("s", 'SOLIDIFY'); sh.thickness = 0.003
    shade.visible_shadow = False
    lamp = bpy.data.lights.new("Lamp", 'SPOT'); lamp.energy = 90; lamp.spot_size = math.radians(70); lamp.spot_blend = 0.5
    lamp.color = (1.0, 0.82, 0.6); lamp.shadow_soft_size = 0.03
    lo = bpy.data.objects.new("Lamp", lamp); bpy.context.collection.objects.link(lo); lo.location = (-0.33, 0.1, 1.15); point_at(lo, (-0.05, 0.0, 0.74))
    moon = area_light((1.5, 2.5, 2.2), (0, 0, 0), 1.5, 4, (0.45, 0.6, 1.0)); point_at(moon, (0, 0, 0.74))
    haze((0, 0, 1.4), (3, 3, 1.4), density=0.03, color=(1.0, 0.95, 0.9), anis=0.5)
    return dict(lamp=lamp, page=Vector((-0.04, 0.0, 0.747)))


def _lamp_on(c, t):
    c["lamp"].energy = 90 * (0.0 if t < 0.15 else min(1.0, (t - 0.15) / 0.08) * (1 - 0.15 * math.exp(-(t - 0.23) * 20) if t > 0.23 else 1))


MOVES = {
    "lamp_on": dict(kind="anim", dof=3.2, far=6.0, cam=lambda c, t: (Vector((0.9, -1.1, 1.25)).lerp(Vector((0.75, -0.9, 1.15)), ease(t)), c["page"], 40),
                    focus=lambda c, t: c["page"], anim=_lamp_on),
    "memo_push": dict(kind="plate", dof=3.5, far=6.0, cam=lambda c, t: ((0.35, -0.55, 1.15), c["page"], 45), focus=lambda c, t: c["page"]),
    "memo_close": dict(kind="plate", dof=2.8, far=6.0, cam=lambda c, t: ((0.12, -0.28, 0.92), c["page"] + Vector((0.02, 0.05, 0)), 60), focus=lambda c, t: c["page"] + Vector((0.02, 0.05, 0))),
    "memo_close2": dict(kind="plate", dof=2.8, far=6.0, cam=lambda c, t: ((-0.2, -0.32, 0.9), c["page"] + Vector((-0.03, -0.04, 0)), 60), focus=lambda c, t: c["page"] + Vector((-0.03, -0.04, 0))),
    "letter_push": dict(kind="plate", dof=3.5, far=6.0, cam=lambda c, t: ((0.25, -0.6, 1.2), c["page"], 45), focus=lambda c, t: c["page"]),
}
