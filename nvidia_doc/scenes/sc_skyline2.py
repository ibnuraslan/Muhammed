"""CH4/CH5 redo city shots (generic, no landmarks).
  singapore  CH4 8A (333 f) dusk over the water: the sc_city Singapore skyline, but with wind-rippled water (no mirror
             artefact), haze between the towers and the camera gliding low over the water toward the city
  beijing    CH5 5B (262 f) night CBD: generic towers with sparse lit floors (warm/cool), a few lit crowns, an elevated
             ring road with moving light trails (white heading one way, red the other), city-glow haze; slow drift
"""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
from common import area_light, world_flat
import sc_city

EXPOSURE = 0.0
VARIANT_FOR = {"singapore": "singapore", "beijing": "beijing"}
FRAMES = {"singapore": 333, "beijing": 262}


def trail_material(name, col, speed, strength=6.0, dash=0.35):
    """Emissive streaks moving along +x (speed m/frame, sign = direction): light trails of traffic."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); em = N.new("ShaderNodeEmission"); em.inputs['Color'].default_value = (*col, 1)
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); L.new(tc.outputs['Object'], mp.inputs['Vector'])
    d = mp.inputs['Location'].driver_add("default_value", 0).driver; d.type = 'SCRIPTED'; d.expression = f"-frame * {speed}"
    sp = N.new("ShaderNodeSeparateXYZ"); L.new(mp.outputs[0], sp.inputs[0])
    nz = N.new("ShaderNodeTexNoise"); nz.noise_dimensions = '1D'; nz.inputs['Scale'].default_value = 0.08; nz.inputs['Detail'].default_value = 2
    L.new(sp.outputs[0], nz.inputs['W'])
    th = N.new("ShaderNodeMapRange"); th.inputs['From Min'].default_value = 0.5 - dash * 0.3; th.inputs['From Max'].default_value = 0.62
    L.new(nz.outputs['Fac'], th.inputs['Value'])
    st = N.new("ShaderNodeMath"); st.operation = 'MULTIPLY'; st.inputs[1].default_value = strength; L.new(th.outputs[0], st.inputs[0])
    L.new(st.outputs[0], em.inputs['Strength'])
    tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader")
    L.new(th.outputs[0], mx.inputs[0]); L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs['Surface'])
    return m


def build(variant=None):
    c = {}
    if variant == "singapore":
        c = sc_city.build("sgdusk")
        w = bpy.data.materials.get("Water")
        if w:
            p = w.node_tree.nodes["Principled BSDF"]; p.inputs['Roughness'].default_value = 0.16
            for nd in w.node_tree.nodes:
                if nd.bl_idname == "ShaderNodeBump":
                    nd.inputs['Strength'].default_value = 0.45
                if nd.bl_idname == "ShaderNodeTexWave":
                    nd.inputs['Scale'].default_value = 0.35
        haze((0, 900, 60), (6000, 1600, 160), density=0.00022, color=(1.0, 0.82, 0.7), anis=0.55)
        from common import world_sky
        world_sky(sun_elev_deg=0.6, sun_rot_deg=20, strength=0.28, tint=(1.0, 0.72, 0.62), aerosol=3.5)   # later dusk
        for o in bpy.data.objects:
            if o.type == 'LIGHT' and o.data.type == 'SUN':
                o.data.energy = 0.6
        for m in bpy.data.materials:                              # the city's lights coming on: stronger windows
            p2 = m.node_tree.nodes.get("Principled BSDF") if m.use_nodes else None
            if p2 is None: continue
            for l in m.node_tree.links:
                if l.to_socket == p2.inputs['Emission Strength'] and l.from_node.bl_idname == "ShaderNodeMath" and l.from_node.operation == 'MULTIPLY':
                    try: l.from_node.inputs[1].default_value *= 3.0
                    except Exception: pass
        return c
    # ------------------------------------------------------------------ beijing night CBD
    world_flat((0.012, 0.016, 0.035), 1.0)
    rng = np.random.default_rng(21)
    ground = pbr("Ground", (0.02, 0.02, 0.022), 0.7)
    box("Ground", (0, 600, -0.5), (6000, 3000, 1), ground)
    streets = emissive("StreetGlow", (1.0, 0.6, 0.3), 0.8)
    for k in range(-25, 26):
        box("StreetX", (0, 300 + k * 90, 0.05), (6000, 3, 0.1), streets)
        box("StreetY", (k * 110, 600, 0.05), (3, 3000, 0.1), streets)
    warm = window_material("WinWarm", lit=(1.0, 0.8, 0.55), density=0.35, floor=4.0, bay=9.0, strength=1.5, glass_col=(0.02, 0.025, 0.035))
    cool = window_material("WinCool", lit=(0.75, 0.88, 1.0), density=0.3, floor=4.2, bay=11.0, strength=1.7, glass_col=(0.018, 0.024, 0.034))
    crown_m = emissive("Crown", (0.9, 0.95, 1.0), 3.0)
    for k in range(140):                                         # CBD cluster beyond the ring road
        x = rng.normal(0, 420); y = 420 + abs(rng.normal(0, 320))
        h = max(50.0, 330 * math.exp(-abs(x) / 520) * rng.uniform(0.3, 1.0))
        w_, d_ = rng.uniform(32, 60), rng.uniform(32, 60)
        m = warm if rng.random() < 0.55 else cool
        if rng.random() < 0.25 and h > 160:                       # tapering hero tower with a lit crown
            box("Tower", (x, y, h * 0.4), (w_, d_, h * 0.8), m)
            box("Tower", (x, y, h * 0.8 + h * 0.08), (w_ * 0.72, d_ * 0.72, h * 0.16), m)
            box("Crown", (x, y, h * 0.96 + 3), (w_ * 0.5, d_ * 0.5, 6), crown_m)
        else:
            box("Tower", (x, y, h / 2), (w_, d_, h), m)
            if rng.random() < 0.4:
                box("RoofLight", (x, y, h + 1), (1.2, 1.2, 1.2), emissive("Aviation", (1.0, 0.15, 0.1), 40))
    for k in range(500):                                         # low-rise fabric around it
        x = rng.uniform(-2000, 2000); y = rng.uniform(120, 1800)
        h = rng.uniform(15, 50)
        box("Low", (x, y, h / 2), (rng.uniform(25, 60), rng.uniform(25, 60), h), warm if k % 2 else cool)
    # the elevated ring road sweeping across the foreground, with light trails both ways
    deck = pbr("Deck", (0.06, 0.06, 0.065), 0.6)
    box("Deck", (0, 210, 14), (5000, 34, 1.4), deck)
    for k in range(-60, 61):
        box("Pier", (k * 40, 210, 6.5), (3, 6, 13), deck)
    box("Barrier", (0, 193.5, 15.2), (5000, 0.4, 1.0), pbr("Barrier", (0.15, 0.15, 0.16), 0.6))
    box("Barrier", (0, 226.5, 15.2), (5000, 0.4, 1.0), pbr("Barrier", (0.15, 0.15, 0.16), 0.6))
    white = trail_material("TrailWhite", (1.0, 0.92, 0.8), 1.4, 9.0)
    red = trail_material("TrailRed", (1.0, 0.12, 0.05), -1.2, 7.0)
    for k, (yy, m) in enumerate(((198, white), (202, white), (206, white), (214, red), (218, red), (222, red))):
        box(f"Trail{k}", (0, yy, 14.9), (5000, 0.5, 0.15), m)
    for k in range(-40, 41):                                     # deck lamps
        box("DeckLamp", (k * 60, 210, 22), (0.6, 6, 0.2), emissive("DeckLamp", (1.0, 0.75, 0.45), 18))
    haze((0, 700, 80), (6000, 1800, 200), density=0.0016, color=(0.75, 0.68, 0.6), anis=0.4)
    return c


def cam_sg(c, t):
    sc_city.anim_boats(c, t, FRAMES["singapore"] / 24)
    e = ease(t)
    return (Vector((70, 120, 4.5)).lerp(Vector((40, 260, 6.0)), e), Vector((0, 1500, 110)).lerp(Vector((0, 1500, 125)), e), 32)


def cam_bj(c, t):
    e = ease(t)
    return (Vector((-330, -260, 92)).lerp(Vector((-240, -240, 98)), e), Vector((40, 520, 70)), 34)


MOVES = {"singapore": dict(kind="anim", far=6000.0, cam=cam_sg),
         "beijing": dict(kind="anim", far=6000.0, cam=cam_bj)}
