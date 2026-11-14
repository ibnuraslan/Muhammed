"""CH4 (chat B): a flea market as a hazy memory (the man's account of where the recorder came from; shown as an
unanchored impression, no identifiable people). Overcast, thick soft haze, slow drift.
  flea (B): a stall of old radios and household junk with a reel-to-reel among them; shoppers drift past, soft
"""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
from common import world_flat, ease
import ph
import b_common as B
import b_props as P

EXPOSURE = 0.3
DUR = {"flea": 6.0, "empty": 6.0}
VARIANT_FOR = {"flea": "flea", "empty": "empty"}


def build(variant=None):
    c = {}
    rng = np.random.default_rng(77)
    try:
        import rj
        rj.sky("grey")
    except Exception:
        world_flat((0.5, 0.52, 0.55), 1.0)
    box("Ground", (0, 0, -0.05), (80, 80, 0.1), B.tex_mat("Lot", "asphalt_02", scale=0.2, tint=(0.5, 0.5, 0.5)))
    tarp = [pbr(f"Tarp{k}", col, 0.8) for k, col in enumerate(((0.2, 0.3, 0.45), (0.5, 0.45, 0.35), (0.35, 0.15, 0.1)))]
    for k in range(5):
        x = -6 + k * 3.0
        ph.model("WoodenTable_03", loc=(x, 2.0, 0), rot_z=0)
        box("Awning", (x, 2.2, 2.2), (2.2, 1.6, 0.03), tarp[k % 3], rot=(math.radians(-8), 0, 0))
        for sx in (-1, 1):
            cyl("AwPole", (x + sx * 1.05, 2.9, 1.1), 0.02, 2.2, pbr("AwP", (0.4, 0.4, 0.42), 0.4, 0.8), verts=8)
    top = 0.83
    items = [("boombox", 0.45), ("Television_01", 0.7), ("cassette_player", 1.0), ("mantel_clock_01", 1.0), ("vintage_stapler", 1.0),
             ("brass_pot_01", 1.0), ("vintage_flashlight", 1.0), ("alarm_clock_01", 1.0), ("vintage_oil_lamp", 1.0)]
    for k, (aid, sc) in enumerate(items):
        x = -6.4 + (k % 5) * 3.0 + rng.uniform(-0.3, 0.3)
        try:
            ph.model(aid, loc=(x + (0.45 if k >= 5 else 0.0), 2.0 + rng.uniform(-0.1, 0.1), top), rot_z=rng.uniform(-0.6, 0.6), scale=sc)
        except Exception as e:
            print("[flea] skip", aid, e)
    if variant == "empty":                                   # 4-12B: nobody remembers the sale: an empty stall at dawn
        for o in list(bpy.data.objects):
            if o.location.z > top - 0.01 and abs(o.location.y - 2.0) < 0.5 and o.type in ('MESH', 'EMPTY') and not o.name.startswith(("Awning", "AwPole", "Ground")):
                if o.parent is None and o.name not in ("Crate",):
                    o.hide_render = True
                    for ch in o.children_recursive:
                        ch.hide_render = True
        # a dusty cloth on the middle table with one clean rectangle where something stood for a long time
        dm = pbr("Dust", (0.5, 0.48, 0.45), 0.95)
        N = dm.node_tree.nodes; L = dm.node_tree.links; pbsdf = N["Principled BSDF"]
        tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs['Object'], sep.inputs[0])
        def rng_mask(axis, half):
            a_ = N.new("ShaderNodeMath"); a_.operation = 'ABSOLUTE'; L.new(sep.outputs[axis], a_.inputs[0])
            lt = N.new("ShaderNodeMath"); lt.operation = 'LESS_THAN'; lt.inputs[1].default_value = half; L.new(a_.outputs[0], lt.inputs[0])
            return lt
        mx_ = rng_mask('X', 0.21); my_ = rng_mask('Y', 0.16)
        rect = N.new("ShaderNodeMath"); rect.operation = 'MULTIPLY'; L.new(mx_.outputs[0], rect.inputs[0]); L.new(my_.outputs[0], rect.inputs[1])
        nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 60; L.new(tc.outputs['Object'], nz.inputs['Vector'])
        inv = N.new("ShaderNodeMath"); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0; L.new(rect.outputs[0], inv.inputs[1])
        al = N.new("ShaderNodeMath"); al.operation = 'MULTIPLY'; L.new(nz.outputs['Fac'], al.inputs[0]); L.new(inv.outputs[0], al.inputs[1])
        L.new(al.outputs[0], pbsdf.inputs['Alpha'])
        box("Cloth", (0.0, 2.0, top + 0.002), (1.5, 0.75, 0.004), fabric("StallCloth", (0.06, 0.07, 0.1), 0.9, 0.4, 260))
        bpy.ops.mesh.primitive_plane_add(size=1, location=(0.35, 1.95, top + 0.0045), rotation=(0, 0, 0.25))
        dust = bpy.context.active_object; dust.scale = (1.3, 0.65, 1); dust.data.materials.append(dm)
        c["shoppers"] = []
        for o in bpy.data.objects:
            if o.name.startswith("Shopper"):
                o.hide_render = True
        B.key_spot((-6.0, -4.0, 2.0), (0.3, 2.0, 0.8), 700, 30, (1.0, 0.72, 0.45), soft=0.1, name="DawnSun")
        B.room_haze((0, 0, 3), (40, 30, 6), density=0.02, color=(0.92, 0.85, 0.78))
        return c
    c["rec"] = P.reel_recorder("FleaRec", (0.35, 1.95, top), rot_z=0.25, spin=0.0)
    for k in range(10):
        box("Crate", (-6.5 + k * 1.4, 2.9, 0.15), (0.5, 0.35, 0.3), pbr("CrateW", (0.4, 0.3, 0.2), 0.8), rot=(0, 0, rng.uniform(-0.2, 0.2)))
    c["shoppers"] = []
    for k in range(4):
        h = B.person(f"Shopper{k}", 1.0 if k % 2 else 0.0, 30 + 9 * k, "male_casualsuit05" if k % 2 else "female_elegantsuit01",
                     ["long01", "short02", "bob02", "short04"][k], hue=0.5 + 0.06 * k, sat=0.3, val=0.35, hair_val=0.35)
        c["shoppers"].append(h)
    B.key_sun(25, 220, 2.5, color=(1.0, 0.9, 0.78), angle=4.0)
    B.room_haze((0, 0, 3), (40, 30, 6), density=0.05, color=(0.92, 0.92, 0.9))
    return c


def anim(c, t, move):
    sec = t * DUR[move]
    if move == "empty":
        bpy.context.view_layer.update(); return
    for k, h in enumerate(c["shoppers"]):
        d = 1 if k % 2 == 0 else -1
        x0 = -8.0 * d + k * 0.7; u = (sec / 14.0 + k * 0.23) % 1.0
        B.walk_to(h, (x0, 3.7 + 0.6 * (k % 2), 0), (x0 + 16 * d, 3.7 + 0.6 * (k % 2), 0), u, 10.0 * u, stride=18, swing=10)
    bpy.context.view_layer.update()


MOVES = {
    "empty": dict(kind="anim", dof=2.8, cam=lambda c, t: (Vector((1.0, 0.6, 1.25)).lerp(Vector((0.7, 1.05, 1.15)), ease(t)), Vector((0.35, 1.95, 0.83)), 40),
                  anim=lambda c, t: anim(c, t, "empty"), focus=lambda c, t: Vector((0.35, 1.95, 0.83))),
    "flea": dict(kind="anim", dof=1.6, cam=lambda c, t: (Vector((1.5, -1.0, 1.45)).lerp(Vector((1.0, -0.6, 1.4)), ease(t)), Vector((0.35, 1.95, 0.95)), 45),
                 anim=lambda c, t: anim(c, t, "flea"), focus=lambda c, t: Vector((0.35, 1.95, 0.95))),
}
