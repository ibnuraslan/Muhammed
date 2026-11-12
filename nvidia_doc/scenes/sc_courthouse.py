"""A generic classical courthouse facade under overcast sky (illustration for the shareholder lawsuit)."""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
import look

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
    ctx = dict(door=Vector((0, 2.0, 6)))
    from human import Human, add_asset, pose_walk
    h = Human("Lawyer", gender=1.0, years=50, muscle=0.5, weight=0.5, height=0.52, eyelashes=None)
    add_asset(h, "clothes", "male_elegantsuit01", val=0.12, rough=0.55); add_asset(h, "clothes", "shoes02", val=0.1); add_asset(h, "hair", "short04", val=0.25)
    bc = box("Briefcase", (0, 0, -30), (0.42, 0.1, 0.32), pbr("Briefcase", (0.06, 0.035, 0.02), 0.4, 0.0, **{'Coat Weight': 0.5}), bevel=0.01)
    ctx.update(lawyer=h, briefcase=bc)
    # house look: moody overcast, a soft key from the left rakes the columns, thin haze over the plaza
    look.day_light("overcast", azim=287, haze_box=((0, -25, 13), (160, 100, 28)), haze_density=0.0015)
    return ctx


def step_z(y):
    if y < -7.75:
        return 0.0
    k = max(0.0, (-3.5 - y) / 0.45)
    return max(0.0, 1.76 - 0.16 * k) if y < -3.5 else 1.76


def anim_climb(c, t):
    from sc_corp import arms_down
    from human import pose_walk
    h = c["lawyer"]; sec = t * 5.0
    y = -12.0 + 1.25 * sec
    bob = pose_walk(h, (1.25 * sec / 1.3) % 1.0, stride=22, arm_swing=10)
    h.arm.rotation_euler = (0, 0, math.pi); h.arm.location = (-1.0, y, step_z(y) + bob); bpy.context.view_layer.update()
    arms_down(h, (1.25 * sec / 1.3) % 1.0, 10)
    c["briefcase"].location = h.bone_tail("wrist.R") + Vector((0, 0, -0.2))
    c["p"] = Vector((-1.0, y, step_z(y) + 1.2))


MOVES = {
    "lawyer_climb": dict(kind="anim", far=400.0, dof=4.0, anim=anim_climb,
                         cam=lambda c, t: (Vector((-0.2, -21.0 + 5.0 * ease(t), 1.6)), c["p"] + Vector((0.2, 6.0, 1.0)), 40), focus=lambda c, t: c["p"]),
    "steps_rise": dict(kind="plate", far=400.0, cam=lambda c, t: ((-6, -34, 1.2 + 4 * t), (0, 0, 9), 28)),
    "slow_push": dict(kind="plate", far=400.0, cam=lambda c, t: ((10, -42, 6), (-6, 0, 12), 35)),
    "columns_drift": dict(kind="plate", dof=3.2, far=400.0, cam=lambda c, t: ((-14, -9, 4), (2, 0, 12), 40), focus=lambda c, t: (-11.25, 0, 10)),
}
