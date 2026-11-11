"""CH1 SET 11B (dramatization): night rain in Singapore. A police car pulls up outside the lit glass lobby of an office
tower; its light bar flashes red and blue across the wet road (frame drivers, plays in any render)."""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
from sc_home import facade
from sc_street import car, wet_asphalt

EXPOSURE = 0.3
DUR = {"pull_up": 4.5}      # estimate until the chapter 1 voiceover arrives


def flash_material(name, col, phase):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); em = N.new("ShaderNodeEmission"); em.inputs['Color'].default_value = (*col, 1)
    v = N.new("ShaderNodeValue"); d = v.outputs[0].driver_add("default_value").driver; d.type = 'SCRIPTED'
    d.expression = f"60 * (1 if ((frame + {phase}) % 12) < 6 else 0.03)"
    L.new(v.outputs[0], em.inputs['Strength']); L.new(em.outputs[0], out.inputs['Surface'])
    return m


def build(variant=None):
    c = {}
    world_flat((0.008, 0.01, 0.016), 1.0)
    road = wet_asphalt("Road")
    box("Road", (0, 0, -0.05), (200, 14, 0.1), road)
    pave = wet_asphalt("Pave"); pave.node_tree.nodes["Principled BSDF"].inputs['Base Color'].default_value = (0.06, 0.06, 0.06, 1)
    box("Pavement", (0, 11, 0.08), (200, 8, 0.16), pave)
    box("Kerb", (0, 7, 0.08), (200, 0.25, 0.17), pbr("Kerb", (0.25, 0.25, 0.24), 0.3, 0.0, **{'Coat Weight': 0.5}))
    # the tower: a tall glass lobby (lit, warm) under a dark curtain wall rising out of frame
    box("LobbyBack", (0, 22, 4), (40, 0.2, 8), pbr("LobbyStone", (0.5, 0.47, 0.43), 0.5))
    box("LobbyGlow", (0, 21.8, 4), (36, 0.05, 7.5), emissive("LobbyLight", (1.0, 0.88, 0.7), 1.2))
    box("LobbyGlass", (0, 15, 4), (40, 0.03, 8), glass("LobbyGlass", (0.9, 0.93, 0.95), 0.02))
    for k in range(11):
        box("Fin", (-20 + k * 4, 15, 4), (0.15, 0.4, 8), pbr("Fin", (0.12, 0.12, 0.13), 0.4, 0.8))
    tw = facade("TowerNight", (0.03, 0.04, 0.05), (0.14, 0.15, 0.16), floor=4.0, bay=1.6, lit_frac=0.12, refl=0.4)
    box("Tower", (0, 26, 8 + 120), (44, 24, 240), tw)
    box("Canopy", (0, 13.5, 6.2), (16, 4, 0.3), pbr("Canopy", (0.1, 0.1, 0.11), 0.4, 0.7))
    for k in range(6):
        l = bpy.data.lights.new("CanopyL", 'POINT'); l.energy = 80; l.color = (1.0, 0.85, 0.65)
        o = bpy.data.objects.new("CanopyL", l); bpy.context.collection.objects.link(o); o.location = (-6 + k * 2.4, 13.5, 5.9)
    # police car: white body, blue stripe, light bar flashing
    pc = car("Police", (0.8, 0.8, 0.82))
    stripe = box("Stripe", (0, 0, 0.62), (4.3, 1.87, 0.12), pbr("PoliceBlue", (0.02, 0.06, 0.25), 0.3, 0.2))
    stripe.parent = pc
    for k, (col, ph) in enumerate((((1.0, 0.05, 0.05), 0), ((0.1, 0.25, 1.0), 6))):
        lb = box("LightBar", (0.0, -0.35 + 0.7 * k, 1.42), (0.25, 0.6, 0.1), flash_material(f"Flash{k}", col, ph)); lb.parent = pc
        l = bpy.data.lights.new(f"FlashL{k}", 'POINT'); l.color = col; l.shadow_soft_size = 0.05
        dl = l.driver_add("energy").driver; dl.type = 'SCRIPTED'; dl.expression = f"600 * (1 if ((frame + {ph}) % 12) < 6 else 0.02)"
        lo = bpy.data.objects.new(f"FlashL{k}", l); bpy.context.collection.objects.link(lo); lo.parent = pc; lo.location = (0.0, -0.35 + 0.7 * k, 1.6)
    c["car"] = pc
    # rain: falling streak curtains (as in the cafe)
    rm = bpy.data.materials.new("Rain"); rm.use_nodes = True
    N = rm.node_tree.nodes; L = rm.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); tc = N.new("ShaderNodeTexCoord")
    mp = N.new("ShaderNodeMapping"); mp.inputs['Scale'].default_value = (30 * 45, 8 * 3.5, 1)
    wn = N.new("ShaderNodeTexWhiteNoise"); wn.noise_dimensions = '2D'
    L.new(tc.outputs['Object'], mp.inputs['Vector']); L.new(mp.outputs[0], wn.inputs['Vector'])
    gt = N.new("ShaderNodeMath"); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = 0.94; L.new(wn.outputs['Value'], gt.inputs[0])
    sc = N.new("ShaderNodeMath"); sc.operation = 'MULTIPLY'; sc.inputs[1].default_value = 0.35; L.new(gt.outputs[0], sc.inputs[0])
    tr = N.new("ShaderNodeBsdfTransparent"); gl = N.new("ShaderNodeEmission"); gl.inputs['Color'].default_value = (0.75, 0.8, 0.9, 1); gl.inputs['Strength'].default_value = 0.6
    mx = N.new("ShaderNodeMixShader"); L.new(sc.outputs[0], mx.inputs[0]); L.new(tr.outputs[0], mx.inputs[1]); L.new(gl.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], out.inputs['Surface'])
    rain = []
    for k, y in enumerate((-6, -2, 3, 8)):
        for j in range(2):
            bpy.ops.mesh.primitive_plane_add(size=1, location=(0, y, 4 + j * 8), rotation=(math.radians(90), 0, 0))
            o = bpy.context.active_object; o.name = "Rain"; o.scale = (30, 8, 1); o.data.materials.append(rm)
            o.visible_shadow = False; o.visible_diffuse = False; o.visible_glossy = False
            rain.append((o, y, j))
    c["rain"] = rain
    for x in (-14, 14):
        cyl("Lamp", (x, 7.6, 3.5), 0.06, 7, pbr("Pole", (0.03, 0.03, 0.03), 0.4, 0.8), verts=12)
        l = bpy.data.lights.new("Street", 'SPOT'); l.energy = 700; l.spot_size = math.radians(100); l.color = (1.0, 0.7, 0.42)
        o = bpy.data.objects.new("Street", l); bpy.context.collection.objects.link(o); o.location = (x, 6.6, 6.9)
    return c


def anim_pull(c, t):
    sec = t * DUR["pull_up"]
    stop = 2.6
    x = -26 + 12.0 * min(sec, stop) - 12.0 * min(sec, stop) ** 2 / (2 * stop) if sec < stop else -26 + 12.0 * stop / 2
    c["car"].location = (x, 4.2, 0.0)
    for o, y, j in c["rain"]:
        o.location = (0, y, 4 + j * 8 - (sec * 8.0) % 8.0)


def cam_pull(c, t):
    e = ease(t)
    return (Vector((-6, -12, 1.2)).lerp(Vector((-5, -11.5, 1.25)), e), Vector((-9, 8, 2.2)), 40)


MOVES = {"pull_up": dict(kind="anim", dof=2.8, far=60.0, cam=cam_pull, focus=lambda c, t: c["car"].location + Vector((0, 0, 1.0)), anim=anim_pull)}
