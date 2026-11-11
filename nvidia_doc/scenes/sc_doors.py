"""Illustration: a long ceremonial corridor ending in tall double doors to a lit room. 'doors_close' swings them
shut until only a sliver of warm light remains."""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *

EXPOSURE = 0.3
END = 18.0


def build(variant=None):
    world_flat((0.003, 0.003, 0.004), 1.0)
    marble = pbr("Marble", (0.5, 0.48, 0.45), 0.12, 0.0, **{'Coat Weight': 0.4, 'Coat Roughness': 0.05})
    nt = marble.node_tree; N = nt.nodes; L = nt.links; tc = N.new("ShaderNodeTexCoord")
    ck = N.new("ShaderNodeTexChecker"); ck.inputs['Scale'].default_value = 1.0
    ck.inputs['Color1'].default_value = (0.5, 0.48, 0.45, 1); ck.inputs['Color2'].default_value = (0.08, 0.075, 0.07, 1)
    mp = N.new("ShaderNodeMapping"); mp.inputs['Scale'].default_value = (0.9, 0.9, 0.9); L.new(tc.outputs['Object'], mp.inputs['Vector'])
    L.new(mp.outputs[0], ck.inputs['Vector']); L.new(ck.outputs['Color'], N["Principled BSDF"].inputs['Base Color'])
    box("Floor", (0, END / 2, -0.01), (4.2, END + 6, 0.02), marble)
    panel = wood("WallPanel", (0.04, 0.02, 0.01), (0.12, 0.06, 0.03), scale=(1, 1, 6), rough=0.35, coat=0.5)
    for sx in (-1, 1):
        box("Wall", (sx * 2.1, END / 2, 2.5), (0.1, END + 6, 5.0), panel)
        for k in range(7):   # sconces
            y = 1.5 + k * 2.4
            box("Sconce", (sx * 2.02, y, 2.4), (0.06, 0.12, 0.22), emissive("SconceGlow", (1.0, 0.75, 0.45), 8))
            l = bpy.data.lights.new("Sc", 'POINT'); l.energy = 25; l.color = (1.0, 0.75, 0.45); l.shadow_soft_size = 0.08
            o = bpy.data.objects.new("Sc", l); bpy.context.collection.objects.link(o); o.location = (sx * 1.9, y, 2.45)
    box("Ceiling", (0, END / 2, 5.0), (4.2, END + 6, 0.05), pbr("Ceil", (0.25, 0.22, 0.18), 0.7))
    box("EndWall", (0, END + 0.1, 2.5), (4.2, 0.2, 5.0), panel)
    # the room beyond (warm, bright)
    box("Room", (0, END + 3.5, 2.5), (6, 6, 5), emissive("RoomGlow", (1.0, 0.82, 0.6), 3.5))
    oak = wood("Door", (0.05, 0.026, 0.012), (0.16, 0.085, 0.04), scale=(1, 1, 5), rough=0.35, coat=0.6)
    brass = brushed_metal("Brass", (0.8, 0.6, 0.32), (0.15, 0.3), 0.3)
    leaves = []
    for sx in (-1, 1):
        # hinge at the frame edge: parent the leaf to an empty at the hinge so it swings
        hinge = bpy.data.objects.new(f"Hinge{sx}", None); bpy.context.collection.objects.link(hinge)
        hinge.location = (sx * 1.0, END, 0)
        leaf = box(f"Leaf{sx}", (sx * 1.0 - sx * 0.5, END, 1.9), (0.98, 0.09, 3.8), oak, bevel=0.01)
        for z in (1.0, 2.8):
            box("Panel", (sx * 0.5, END - 0.05, z), (0.7, 0.02, 1.3), oak, bevel=0.01)
        handle = cyl("Handle", (sx * 0.1, END - 0.08, 1.15), 0.016, 0.5, brass, verts=16)
        for o in [o for o in bpy.context.scene.objects if o.name.startswith(("Leaf", "Panel", "Handle")) and o.parent is None and abs(o.location.x - sx * 0.5) < 0.6 and o.location.y > END - 0.2]:
            mw = o.matrix_world.copy(); o.parent = hinge; o.matrix_world = mw
        leaves.append((hinge, sx))
    box("Frame", (0, END - 0.02, 4.0), (2.3, 0.15, 0.25), brass)
    haze((0, END / 2, 2.5), (4.0, END + 4, 5.0), density=0.0015, color=(1.0, 0.92, 0.82), anis=0.6)
    return dict(leaves=leaves, door=Vector((0, END, 1.9)))


def _close(c, t):
    ang = math.radians(75 * (1 - ease(min(1.0, t * 1.1))) + 0.8)   # ends with a sliver open
    for hinge, sx in c["leaves"]:
        hinge.rotation_euler = (0, 0, -sx * ang)


MOVES = {
    "corridor_push": dict(kind="plate", far=40.0, cam=lambda c, t: ((0.0, 1.0, 1.6), (0, END, 1.8), 30), anim=lambda c, t: _close(c, 0.0)),
    "doors_close": dict(kind="anim", far=40.0, cam=lambda c, t: (Vector((0, 4.0, 1.6)).lerp(Vector((0, 7.5, 1.65)), ease(t)), (0, END, 1.8), 32), anim=_close),
}
