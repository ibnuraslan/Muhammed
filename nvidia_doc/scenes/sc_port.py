"""Container terminal at dusk (illustration for the Indonesia shipments): container stacks, gantry cranes, quay, water."""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *

EXPOSURE = -1.6
L20, W8, H8 = 12.19, 2.44, 2.59     # 40 ft container


def container_material(name, color):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); oi = N.new("ShaderNodeObjectInfo")
    # corrugation along the length
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs['Object'], sep.inputs[0])
    mul = N.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = 2 * math.pi / 0.28; L.new(sep.outputs['X'], mul.inputs[0])
    sn = N.new("ShaderNodeMath"); sn.operation = 'SINE'; L.new(mul.outputs[0], sn.inputs[0])
    bp = N.new("ShaderNodeBump"); bp.inputs['Strength'].default_value = 0.5; bp.inputs['Distance'].default_value = 0.03
    L.new(sn.outputs[0], bp.inputs['Height']); L.new(bp.outputs['Normal'], p.inputs['Normal'])
    # per-container colour variation + rust/dirt
    hs = N.new("ShaderNodeHueSaturation"); hs.inputs['Color'].default_value = (*color, 1)
    hv = N.new("ShaderNodeMath"); hv.operation = 'MULTIPLY_ADD'; hv.inputs[1].default_value = 0.12; hv.inputs[2].default_value = 0.44
    L.new(oi.outputs['Random'], hv.inputs[0]); L.new(hv.outputs[0], hs.inputs['Hue'])
    vv = N.new("ShaderNodeMath"); vv.operation = 'MULTIPLY_ADD'; vv.inputs[1].default_value = 0.6; vv.inputs[2].default_value = 0.7
    L.new(oi.outputs['Random'], vv.inputs[0]); L.new(vv.outputs[0], hs.inputs['Value'])
    n = N.new("ShaderNodeTexNoise"); n.inputs['Scale'].default_value = 1.5; n.inputs['Detail'].default_value = 8; L.new(tc.outputs['Object'], n.inputs['Vector'])
    dirt = N.new("ShaderNodeMix"); dirt.data_type = 'RGBA'; dirt.blend_type = 'MULTIPLY'; dirt.inputs['Factor'].default_value = 0.6
    L.new(hs.outputs['Color'], dirt.inputs[6]); L.new(n.outputs['Color'], dirt.inputs[7]); L.new(dirt.outputs[2], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.55; p.inputs['Metallic'].default_value = 0.35
    return m


def crane(x, y, mat, h=52, boom=70):
    parts = []
    for dx in (-8, 8):
        for dy in (-11, 11):
            parts.append(box("Leg", (x + dx, y + dy, h / 2), (1.4, 1.4, h), mat))
    parts.append(box("Beam", (x, y, h), (18, 24, 2.5), mat))
    parts.append(box("Boom", (x, y - boom / 2 + 10, h + 6), (2.2, boom + 30, 2.2), mat))
    parts.append(box("Mast", (x, y + 4, h + 18), (2.0, 2.0, 24), mat))
    for k in range(6):
        parts.append(box("Brace", (x + (k % 2 * 2 - 1) * 8, y, h * (0.2 + 0.12 * k)), (0.6, 22, 0.6), mat, rot=(math.radians(25 * (1 if k % 2 else -1)), 0, 0)))
    return join(parts, "Crane")


def build(variant=None):
    world_sky(sun_elev_deg=2.5, sun_rot_deg=70, strength=0.5, tint=(1.0, 0.85, 0.75), aerosol=3.0)
    sun(2.5, 160, energy=2.5, color=(1.0, 0.55, 0.32), angle_deg=1.5)
    r = np.random.default_rng(21)
    colors = [(0.45, 0.07, 0.05), (0.05, 0.16, 0.32), (0.08, 0.22, 0.12), (0.55, 0.35, 0.08), (0.35, 0.36, 0.38), (0.6, 0.6, 0.58)]
    mats = [container_material(f"Cont{k}", c) for k, c in enumerate(colors)]
    protos = [box(f"ContP{k}", (0, 0, -50), (L20, W8, H8), m, bevel=0.06) for k, m in enumerate(mats)]
    yard = []
    for row in range(16):
        for bay in range(9):
            x0 = -60 + bay * (L20 + 1.8); y0 = 20 + row * (W8 * 6 + 6)
            for lane in range(6):
                height = int(r.integers(1, 6)) if r.random() > 0.08 else 0
                for lvl in range(height):
                    yard.append(instance(protos[int(r.integers(0, len(protos)))], (x0, y0 + lane * (W8 + 0.15), H8 / 2 + lvl * H8)))
    steel = pbr("CraneSteel", (0.05, 0.065, 0.085), 0.75, 0.0)   # matte painted steel
    for k in range(4):
        crane(-40 + k * 38, -6, steel)
    box("Quay", (0, 190, -1), (900, 420, 2), pbr("Concrete", (0.12, 0.115, 0.11), 0.85))   # quay edge at y = -20
    water = box("Sea", (0, -300, -2.5), (3000, 600, 1), pbr("Sea", (0.01, 0.018, 0.025), 0.08))
    nt = water.data.materials[0].node_tree; N = nt.nodes; L = nt.links; tc = N.new("ShaderNodeTexCoord")
    n = N.new("ShaderNodeTexNoise"); n.inputs['Scale'].default_value = 0.08; n.inputs['Detail'].default_value = 10; L.new(tc.outputs['Object'], n.inputs['Vector'])
    b = N.new("ShaderNodeBump"); b.inputs['Strength'].default_value = 0.3; L.new(n.outputs['Fac'], b.inputs['Height']); L.new(b.outputs['Normal'], N["Principled BSDF"].inputs['Normal'])
    # quay lights coming on
    lamp = emissive("Sodium", (1.0, 0.62, 0.3), 60)
    for k in range(14):
        box("Pole", (-80 + k * 14, 8, 15), (0.4, 0.4, 30), steel)
        box("Lamp", (-80 + k * 14, 8, 30.2), (1.6, 1.0, 0.4), lamp)
    haze((0, 160, 40), (900, 400, 80), density=0.00025, color=(1.0, 0.85, 0.75), anis=0.5)
    return dict(stack=Vector((-4, 40, 6)))


MOVES = {
    "crane_rise": dict(kind="plate", far=1200.0, cam=lambda c, t: ((95, -175, 5 + 6 * t), (-5, 10, 24), 32)),
    "container_push": dict(kind="plate", dof=4.0, far=600.0, cam=lambda c, t: ((14, 4, 3.2), (-10, 28, 5), 40), focus=lambda c, t: (-2, 23, 4)),
}
