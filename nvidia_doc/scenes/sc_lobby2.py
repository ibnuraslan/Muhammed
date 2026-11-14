"""CH4 2B redo (288 f): a richer corporate lobby in the morning. Built on sc_corp's busy lobby (6 employees from
behind/far walking to the gates) plus: a glass-fronted mezzanine along the back with a steel cap rail and a soft
underside light strip, stone-clad columns, linear pendants, an abstract light wall behind reception (no logo),
morning sun shafts through the glass wall (haze), three more people crossing far back. Low, slow push from behind."""
import math
import bpy
from mathutils import Vector
from kit import *
from common import area_light
import sc_corp
from human import Human, add_asset, pose_walk

EXPOSURE = 0.0
FRAMES = {"lobby": 288}


def build(variant=None):
    c = sc_corp.build("busy")
    gl = glass("BalGlass", (0.85, 0.92, 0.95), 0.01)
    steel = brushed_metal("CapRail", (0.7, 0.71, 0.73), (0.15, 0.3), 0.5)
    slab = pbr("Mezz", (0.55, 0.54, 0.52), 0.5)
    box("MezzSlab", (-1.0, 16.0, 4.6), (14.0, 3.0, 0.35), slab)
    box("MezzGlass", (-1.0, 14.5, 5.3), (14.0, 0.02, 1.05), gl)
    box("CapRail", (-1.0, 14.5, 5.85), (14.0, 0.08, 0.05), steel)
    box("MezzStrip", (-1.0, 14.55, 4.4), (14.0, 0.05, 0.04), emissive("MezzStrip", (1.0, 0.9, 0.75), 8))
    stonec = pbr("ColumnStone", (0.62, 0.6, 0.57), 0.45)
    for x in (-6.0, -2.0, 2.0):
        box("Column", (x, 9.0, 4.5), (0.7, 0.7, 9.0), stonec, bevel=0.02)
    pend = emissive("Pendant", (1.0, 0.9, 0.78), 10)
    for k in range(4):
        box("Pendant", (-5.0 + k * 3.2, 6.0, 6.8), (2.4, 0.08, 0.05), pend)
        box("PendWire", (-5.0 + k * 3.2, 6.0, 7.9), (0.005, 0.005, 2.2), pbr("Wire", (0.05, 0.05, 0.05), 0.5))
    # abstract light wall behind reception: soft vertical gradient bands, no text or logo
    m = bpy.data.materials.new("LightWall"); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); em = N.new("ShaderNodeEmission"); tc = N.new("ShaderNodeTexCoord")
    wv = N.new("ShaderNodeTexWave"); wv.inputs['Scale'].default_value = 1.4; wv.inputs['Distortion'].default_value = 2.0
    L.new(tc.outputs['Object'], wv.inputs['Vector'])
    d = wv.inputs['Phase Offset'].driver_add("default_value").driver; d.type = 'SCRIPTED'; d.expression = "frame * 0.02"
    cr = N.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (0.08, 0.16, 0.24, 1); cr.color_ramp.elements[1].color = (0.45, 0.7, 0.85, 1)
    L.new(wv.outputs['Fac'], cr.inputs['Fac']); L.new(cr.outputs['Color'], em.inputs['Color']); em.inputs['Strength'].default_value = 1.6
    L.new(em.outputs[0], out.inputs['Surface'])
    box("LightWall", (-3.5, 17.3, 2.0), (5.5, 0.05, 2.6), m)
    haze((2.0, 6.0, 4.5), (12.0, 24.0, 9.0), density=0.006, color=(1.0, 0.95, 0.88), anis=0.6)
    # three more people far back, crossing in front of the reception (profile at distance)
    extra = []
    for k, (g, yrs, cl, hr, sk, x0, y, v) in enumerate((
            (1.0, 40, "male_casualsuit01", "short01", "middleage_lightskinned_male_diffuse2.png", -5.5, 11.5, 0.9),
            (0.0, 31, "female_casualsuit01", "bob02", "young_lightskinned_female_diffuse3.png", 4.5, 11.9, -0.85),
            (1.0, 45, "male_worksuit01", "short03", "middleage_darkskinned_male_diffuse.png", -7.0, 11.2, 0.8))):
        h = Human(f"Far{k}", gender=g, years=yrs, muscle=0.5, weight=0.45, height=0.5, eyelashes="eyelashes01", skin=sk)
        add_asset(h, "clothes", cl, val=0.25, rough=0.7); add_asset(h, "clothes", "shoes02", val=0.2)
        add_asset(h, "hair", hr, val=0.2, rough=0.45)
        extra.append((h, x0, y, v, k * 0.29))
    c["extra"] = extra
    return c


def anim(c, t):
    sc_corp.anim_busy(c, t)
    sec = t * FRAMES["lobby"] / 24
    for h, x0, y, v, ph_ in c["extra"]:
        d = v * sec
        phase = (abs(d) / 1.3 + ph_) % 1.0
        bob = pose_walk(h, phase, stride=24, arm_swing=14)
        h.arm.rotation_euler = (0, 0, math.pi / 2 if v > 0 else -math.pi / 2)
        h.arm.location = (x0 + d, y, bob)
        sc_corp.arms_down(h, phase, 14)
    bpy.context.view_layer.update()


def cam(c, t):
    e = ease(t)
    return (Vector((-1.6, -6.4, 1.7)).lerp(Vector((-1.0, -4.4, 1.85)), e), Vector((0.0, 12.0, 2.6)), 26)


MOVES = {"lobby": dict(kind="anim", dof=6.0, far=80.0, anim=anim, cam=cam, focus=lambda c, t: Vector((0.3, 6.0, 1.2)))}
