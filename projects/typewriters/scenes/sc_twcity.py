"""MOSCOW AT NIGHT, 1984: a generic tapering concrete TV tower over a sea of low apartment blocks and pitched roofs,
every roof crowded with TV aerials. Sodium street light, a few lit windows, thin haze. (Generic: not a landmark replica.)

Ch3 5A  tower      slow push toward the tower over rooftops full of antennas; its red lamps blink
Ch3 4B  antenna    across the rooftops: a small antenna on a nearby roof, the embassy's lit windows beyond (later)
Ch4 10B pullback   slow pull back and up over the rooftops toward the tower (end of the film)
"""
import math
import numpy as np
import bpy
from mathutils import Vector, Matrix
from kit import *
import ph
import twp

EXPOSURE = 0.3
DUR = {"tower": 5.0, "antenna": 4.5, "pullback": 6.0}
TOWER = Vector((0.0, 420.0, 0.0))


def win_mat(name, lit=(1.0, 0.7, 0.42), density=0.3, strength=0.7):
    """Lit flat windows with something inside them: curtains and lamp falloff break up each cell (no flat glowing
    rectangles), the light fades toward the head of the window, and each window gets its own warmth."""
    m = window_material(name, lit=lit, density=density, floor=2.8, bay=1.4, strength=strength, glass_col=(0.02, 0.022, 0.025))
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    es = p.inputs['Emission Strength'].links[0].from_socket
    geo = next(n for n in N if n.bl_idname == "ShaderNodeNewGeometry")
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 0.9; nz.inputs['Detail'].default_value = 4.0
    L.new(geo.outputs['Position'], nz.inputs['Vector'])
    cr = N.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].position = 0.38; cr.color_ramp.elements[0].color = (0.08, 0.08, 0.08, 1)
    cr.color_ramp.elements[1].position = 0.62; cr.color_ramp.elements[1].color = (1, 1, 1, 1); L.new(nz.outputs['Fac'], cr.inputs[0])
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs['Position'], sep.inputs[0])
    fz = N.new("ShaderNodeMath"); fz.operation = 'WRAP'; fz.inputs[1].default_value = 2.8; fz.inputs[2].default_value = 0.0; L.new(sep.outputs[2], fz.inputs[0])
    gz = N.new("ShaderNodeMapRange"); gz.inputs['From Min'].default_value = 0.4; gz.inputs['From Max'].default_value = 2.6
    gz.inputs['To Min'].default_value = 1.0; gz.inputs['To Max'].default_value = 0.35; L.new(fz.outputs[0], gz.inputs['Value'])
    m1 = N.new("ShaderNodeMath"); m1.operation = 'MULTIPLY'; L.new(es, m1.inputs[0]); L.new(cr.outputs[0], m1.inputs[1])
    m2 = N.new("ShaderNodeMath"); m2.operation = 'MULTIPLY'; L.new(m1.outputs[0], m2.inputs[0]); L.new(gz.outputs[0], m2.inputs[1])
    L.new(m2.outputs[0], p.inputs['Emission Strength'])
    hue = N.new("ShaderNodeTexNoise"); hue.inputs['Scale'].default_value = 0.35; L.new(geo.outputs['Position'], hue.inputs['Vector'])
    hr = N.new("ShaderNodeValToRGB"); hr.color_ramp.elements[0].color = (*[x * 0.9 for x in lit], 1); hr.color_ramp.elements[1].color = (1.0, 0.85, 0.62, 1)
    hr.color_ramp.elements[0].position = 0.35; hr.color_ramp.elements[1].position = 0.65
    L.new(hue.outputs['Fac'], hr.inputs[0]); L.new(hr.outputs[0], p.inputs['Emission Color'])
    return m


def aerial(x, y, z, rng, m):
    h = rng.uniform(1.2, 2.6)
    parts = [cyl("AMast", (0, 0, h / 2), 0.02, h, m, verts=6)]
    for j in range(rng.integers(1, 4)):
        L = rng.uniform(0.6, 1.4); zz = h * (0.55 + 0.15 * j)
        parts.append(box("ABoom", (0, 0, zz), (L, 0.015, 0.015), m))
        for k in range(5):
            parts.append(box("AEl", (-L / 2 + k * L / 4, 0, zz), (0.012, rng.uniform(0.35, 0.6), 0.012), m))
    o = join(parts, "Aerial"); o.location = (x, y, z); o.rotation_euler = (0, 0, rng.uniform(-0.5, 0.5))
    return o


def tower(m_conc, lamp_m):
    """Tapering concrete shaft on splayed legs, a pod near the top, a steel mast with red lamps."""
    parts = []
    bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=16, radius2=4.5, depth=330, location=(0, 0, 165))
    shaft = bpy.context.active_object; shaft.data.materials.append(m_conc); bpy.ops.object.shade_smooth(); parts.append(shaft)
    for k in range(10):
        a = k / 10 * 2 * math.pi
        bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=6, radius2=1.5, depth=70, location=(22 * math.cos(a), 22 * math.sin(a), 30))
        leg = bpy.context.active_object; leg.rotation_euler = (0.25 * math.sin(a), -0.25 * math.cos(a), 0); leg.data.materials.append(m_conc); parts.append(leg)
    for z, r, h in ((328, 13, 9), (350, 9, 5)):
        parts.append(cyl("Pod", (0, 0, z), r, h, m_conc, verts=48))
    win = win_mat("PodWin", lit=(0.9, 0.85, 0.75), density=0.85, strength=4.0)
    parts.append(cyl("PodGlass", (0, 0, 328), 13.1, 3.0, win, verts=48))
    steel = pbr("TowerSteel", (0.5, 0.2, 0.15), 0.5, 0.6)
    parts.append(cyl("Mast", (0, 0, 430), 2.2, 160, steel, verts=16))
    t = join(parts, "Tower")
    lamps = []
    for z in (180, 260, 360, 450, 508):
        for k in range(4):
            a = k * math.pi / 2
            r = max(2.6, 16 - z * 0.035) if z < 330 else 2.6
            bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=0.9, location=(r * math.cos(a), r * math.sin(a), z))
            o = bpy.context.active_object; o.data.materials.append(lamp_m); o.parent = t; lamps.append(o)
    return t, lamps


def night_gradient(world):
    nt = world.node_tree; N = nt.nodes
    bg = next(n for n in N if n.type == 'BACKGROUND')
    tc = N.new("ShaderNodeTexCoord"); sp = N.new("ShaderNodeSeparateXYZ"); ramp = N.new("ShaderNodeValToRGB")
    nt.links.new(tc.outputs["Generated"], sp.inputs[0]); nt.links.new(sp.outputs["Z"], ramp.inputs[0])
    el = ramp.color_ramp.elements
    el[0].position = 0.0; el[0].color = (0.05, 0.035, 0.03, 1)        # sodium glow sitting on the horizon
    el[1].position = 0.35; el[1].color = (0.004, 0.006, 0.014, 1)     # deep night overhead
    m = el.new(0.06); m.color = (0.025, 0.025, 0.04, 1)
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"]); bg.inputs["Strength"].default_value = 1.0


def build(variant=None):
    c = {}
    rng = np.random.default_rng(1984)
    w = world_flat((0.018, 0.026, 0.05), 1.0)
    night_gradient(bpy.context.scene.world)                     # smooth dark sky: city glow at the horizon to deep blue overhead
    # low moonlit sky gradient: a big inverted dome would be heavy; a dim area light from above suffices
    moon = bpy.data.lights.new("Moon", 'SUN'); moon.energy = 0.35; moon.color = (0.55, 0.65, 1.0); moon.angle = math.radians(1)
    mo = bpy.data.objects.new("Moon", moon); bpy.context.collection.objects.link(mo); mo.rotation_euler = (math.radians(50), 0, math.radians(30))
    ground = ph.texture("asphalt_02", scale=0.05, name="CityGround", tint=(0.5, 0.5, 0.5))
    box("Ground", (0, 200, -0.1), (1200, 1200, 0.2), ground)
    conc = ph.texture("concrete_wall_008", scale=0.03, name="TowerConc", tint=(0.8, 0.8, 0.78))
    lamp = pbr("TowerLamp", (0.4, 0.02, 0.01), 0.3, 0.0, **{'Emission Color': (1.0, 0.08, 0.03, 1), 'Emission Strength': 0.0})
    d = lamp.node_tree.nodes["Principled BSDF"].inputs['Emission Strength'].driver_add("default_value").driver
    d.type = 'SCRIPTED'; d.expression = "60 * (1 if (frame % 36) < 18 else 0.05)"
    t, lamps = tower(conc, lamp); t.location = TOWER
    for k in range(3):
        fl = bpy.data.lights.new("TowerWash", 'SPOT'); fl.energy = 3.0e6; fl.spot_size = math.radians(18); fl.color = (1.0, 0.8, 0.6)
        fo = bpy.data.objects.new("TowerWash", fl); bpy.context.collection.objects.link(fo)
        a = k * 2.1; fo.location = TOWER + Vector((80 * math.cos(a), 80 * math.sin(a), 2)); point_at(fo, TOWER + Vector((0, 0, 200)))
    # ---------------------------------------------------------------- the city: blocks and pitched-roof houses, aerials on everything
    plaster = [ph.texture("painted_plaster_wall", scale=0.12, name=f"BlockPlaster{k}", tint=col) for k, col in
               enumerate(((0.6, 0.55, 0.45), (0.5, 0.5, 0.48), (0.55, 0.45, 0.38)))]
    roof_m = ph.texture("grey_roof_tiles", scale=0.25, name="RoofTiles", tint=(0.55, 0.55, 0.55))
    metal_roof = ph.texture("corrugated_iron", scale=0.2, name="MetalRoof", tint=(0.45, 0.48, 0.46))
    ant = pbr("AerialM", (0.35, 0.35, 0.36), 0.4, 0.9)
    wins = [win_mat(f"CityWin{k}", density=d_) for k, d_ in enumerate((0.3, 0.42, 0.25))]
    c["roofs"] = []
    for gx in range(-9, 10):
        for gy in range(0, 26):
            x = gx * 24 + rng.uniform(-4, 4); y = gy * 16 + rng.uniform(-3, 3)
            if (Vector((x, y, 0)) - TOWER).length < 60:
                continue
            kind = rng.random()
            if kind < 0.55:                    # five/nine-storey block with a flat roof
                H = rng.choice([14.0, 15.0, 26.0]) * rng.uniform(0.95, 1.05); W_ = rng.uniform(14, 20); D_ = rng.uniform(9, 11)
                b = box("Block", (x, y, H / 2), (W_, D_, H), wins[int(rng.integers(0, 3))])
                box("BlockCap", (x, y, H + 0.4), (W_ + 0.3, D_ + 0.3, 0.8), plaster[int(rng.integers(0, 3))])
                top = H + 0.8
                for k in range(rng.integers(3, 8) if y < 140 else 0):
                    aerial(x + rng.uniform(-W_ / 2 + 1, W_ / 2 - 1), y + rng.uniform(-D_ / 2 + 1, D_ / 2 - 1), top, rng, ant)
                c["roofs"].append((x, y, top))
            else:                              # old pitched-roof house
                H = rng.uniform(7, 11); W_ = rng.uniform(10, 16); D_ = rng.uniform(8, 10)
                box("House", (x, y, H / 2), (W_, D_, H), wins[2])
                for sy in (-1, 1):
                    box("Pitch", (x, y + sy * D_ / 4, H + 1.5), (W_ + 0.6, D_ / 2 / math.cos(0.55) + 0.3, 0.2), roof_m if rng.random() < 0.6 else metal_roof,
                        rot=(-sy * 0.55, 0, 0))
                for k in range(rng.integers(1, 4) if y < 140 else 0):
                    aerial(x + rng.uniform(-W_ / 3, W_ / 3), y + rng.uniform(-1, 1), H + 2.6, rng, ant)
                cyl("Chimney", (x + W_ * 0.3, y + 1, H + 2.6), 0.5, 2.5, plaster[1], verts=8)
    # sodium street lamps glowing along a few streets (point lights low, no emissive strips)
    for gy in range(0, 26, 3):
        for gx in range(-9, 10, 2):
            l = bpy.data.lights.new("Sodium", 'POINT'); l.energy = 2500; l.color = (1.0, 0.6, 0.3); l.shadow_soft_size = 0.3
            o = bpy.data.objects.new("Sodium", l); bpy.context.collection.objects.link(o); o.location = (gx * 24 + 12, gy * 16 + 8, 7)
    haze((0, 250, 30), (500, 600, 60), density=0.00025, color=(0.65, 0.7, 0.85), anis=0.4)
    # the near rooftop (for the close shots): a pitched roof with a cluster of aerials, a chimney stack
    NR = Vector((6.0, -14.0, 18.0)); c["near"] = NR
    box("NearBlock", (NR.x, NR.y - 2, NR.z / 2), (22, 14, NR.z), win_mat("NearWin", lit=(0.85, 0.5, 0.28), density=0.15, strength=0.5))
    box("NearRoof", (NR.x, NR.y - 2, NR.z + 0.3), (22.4, 14.4, 0.6), ph.texture("roof_tiles" if False else "asphalt_02", scale=0.3, name="NearFelt"))
    box("NearParapet", (NR.x, NR.y + 5.1, NR.z + 0.9), (22.4, 0.3, 0.9), plaster[0])
    c["near_aerials"] = []
    for k in range(7):
        c["near_aerials"].append(aerial(NR.x - 8 + k * 2.6 + rng.uniform(-0.5, 0.5), NR.y + rng.uniform(-3, 3.5), NR.z + 0.6, rng, ant))
    for k in range(3):
        cyl("Vent", (NR.x - 5 + k * 5, NR.y - 4, NR.z + 1.2), 0.3, 1.2, plaster[2], verts=12)
    animate(c, 0.0)
    return c


def animate(c, sec):
    for k, a in enumerate(c["near_aerials"]):                   # aerials tremble in the night wind
        a.rotation_euler.x = 0.012 * math.sin(sec * 2.3 + k)
    bpy.context.view_layer.update()


def cam_tower(c, t):
    e = ease(t); N = c["near"]
    return (N + Vector((-2.0, -6.0, 2.6)).lerp(Vector((-1.2, -3.5, 2.4)), e), TOWER + Vector((0, 0, 230)), 32)


def cam_pull(c, t):
    e = ease(t); N = c["near"]
    return (N + Vector((0.0, -3.0, 4.0)).lerp(Vector((-4.0, -18.0, 22.0)), e), TOWER + Vector((0, 0, 150)), 28)


def cam_antenna(c, t):
    e = ease(t); a = c["near_aerials"][3].location
    return (a + Vector((2.4, -4.0, 1.2)).lerp(Vector((1.9, -3.4, 1.1)), e), a + Vector((0, 0, 1.6)), 35)


MOVES = {
    "antenna": dict(kind="anim", dof=None, cam=cam_antenna, anim=lambda c, t: animate(c, t * DUR["antenna"])),
    "tower": dict(kind="anim", dof=None, cam=cam_tower, anim=lambda c, t: animate(c, t * DUR["tower"])),
    "pullback": dict(kind="anim", dof=None, cam=cam_pull, anim=lambda c, t: animate(c, t * DUR["pullback"])),
}
