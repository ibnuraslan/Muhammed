"""A generic classical courthouse facade under overcast sky (illustration for the shareholder lawsuit)."""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *

EXPOSURE = -4.2


def build(variant=None):
    world_sky(sun_elev_deg=20, sun_rot_deg=150, strength=0.35, tint=(0.85, 0.9, 1.0), aerosol=6.0)
    stone = pbr("Limestone", (0.62, 0.6, 0.56), 0.6)
    nt = stone.node_tree; N = nt.nodes; L = nt.links; tc = N.new("ShaderNodeTexCoord")
    n = N.new("ShaderNodeTexNoise"); n.inputs['Scale'].default_value = 1.5; n.inputs['Detail'].default_value = 10
    L.new(tc.outputs['Object'], n.inputs['Vector'])
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 0.35
    mx.inputs[6].default_value = (0.62, 0.6, 0.56, 1); L.new(n.outputs['Color'], mx.inputs[7]); L.new(mx.outputs[2], N["Principled BSDF"].inputs['Base Color'])
    box("Body", (0, 12, 11), (44, 20, 22), stone)
    col = cyl("ColP", (0, 0, -100), 0.85, 15, stone, verts=32)
    for k in range(8):
        x = -15.75 + k * 4.5
        instance(col, (x, 0, 3.6 + 7.5))
        box("Base", (x, 0, 3.4), (2.2, 2.2, 0.4), stone); box("Capital", (x, 0, 18.7), (2.2, 2.2, 0.6), stone)
    box("Stylobate", (0, 1.5, 1.6), (40, 9, 3.2), stone)
    for k in range(10):
        box("Step", (0, -3.5 - k * 0.45, 0.16 + (9 - k) * 0.32 * 0.0), (38 + k * 0.4, 0.45, 3.2 - k * 0.32), stone)
    box("Entablature", (0, 0.5, 20.0), (40, 6, 2.2), stone)
    box("Frieze", (0, -2.45, 20.0), (34, 0.1, 1.0), pbr("Frieze", (0.5, 0.48, 0.45), 0.6))
    bpy.ops.mesh.primitive_cone_add(vertices=3, radius1=21, depth=6, location=(0, 0.5, 22.4), rotation=(math.radians(90), 0, 0))
    ped = bpy.context.active_object; ped.scale = (1, 0.3, 1); ped.data.materials.append(stone)
    door = pbr("Door", (0.05, 0.035, 0.025), 0.5, 0.3)
    box("Doorway", (0, 2.2, 7.0), (4.2, 0.2, 7.6), door)
    box("Plaza", (0, -40, -0.1), (200, 70, 0.2), pbr("Plaza", (0.3, 0.29, 0.28), 0.7))
    for k in range(8):
        cyl("Lamp", (-14 + k * 4, -18, 2.2), 0.06, 4.4, pbr("Iron", (0.02, 0.02, 0.02), 0.5, 0.8), verts=12)
    return dict(door=Vector((0, 2.0, 6)))


MOVES = {
    "steps_rise": dict(kind="plate", far=400.0, cam=lambda c, t: ((-6, -34, 1.2 + 4 * t), (0, 0, 9), 28)),
    "slow_push": dict(kind="plate", far=400.0, cam=lambda c, t: ((10, -42, 6), (-6, 0, 12), 35)),
    "columns_drift": dict(kind="plate", dof=3.2, far=400.0, cam=lambda c, t: ((-14, -9, 4), (2, 0, 12), 40), focus=lambda c, t: (-11.25, 0, 10)),
}
