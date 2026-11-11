"""SET 1 / HOME (dramatization). Blue-hour dawn. A living room with floor-to-ceiling windows onto wooded hills and a
road in the valley below. The man in the black leather jacket sits on a low sofa, phone in both hands.

Everything is animated per frame:
  - breathing (spine/shoulders), small head motion
  - thumbs: a simple IK that aims the thumb bones at key positions on the screen keyboard (taps), then at Send
  - the email itself is the phone's screen texture (rendered per frame), so the thumb occludes it correctly
  - shot 4: arm brings the phone down to the coffee table (face down), he leans back, hand to his face
  - outside: trees sway, a car's headlights travel along the valley road, the sky brightens slowly

Moves (seconds at 12 fps):  wide 3.0 | shoulder 2.4 | thumb 1.2 | side 2.2
"""
import os, sys, math
import numpy as np
import bpy
from mathutils import Vector, Matrix, Quaternion
from kit import *
from common import grid_mesh
from human import reset_pose, fingers_curl, rotate_bone, aim_bone, _world_verts, SIDE, reach, ik2
from people import man

HERE = os.path.dirname(os.path.abspath(__file__))

EXPOSURE = -1.2
WIN_Y = -2.6                      # window wall in front of him; he faces -Y, out toward the city
HDRI_ROT = 0.0
UI_DIR = os.path.join(HERE, "..", "out", "ui_frames")
LINE = "I was unfaithful to my wife."


# ============================================================================ materials
def haze_mix(m, color=(0.42, 0.52, 0.68), start=80.0, end=4200.0, strength=0.7):
    """Aerial perspective: blend the surface toward the dawn haze with camera distance (cheap, no volumes)."""
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]; out = N["Material Output"]
    cd = N.new("ShaderNodeCameraData")
    mr = N.new("ShaderNodeMapRange"); mr.inputs['From Min'].default_value = start; mr.inputs['From Max'].default_value = end
    mr.inputs['To Max'].default_value = strength
    L.new(cd.outputs['View Distance'], mr.inputs['Value'])
    em = N.new("ShaderNodeEmission"); em.inputs['Color'].default_value = (*color, 1); em.inputs['Strength'].default_value = 1.0
    mx = N.new("ShaderNodeMixShader"); L.new(mr.outputs[0], mx.inputs[0])
    L.new(p.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs['Surface'])
    return m


def window_glass():
    """Real reflections for the camera, but transparent to shadow rays so the sky lights the room cleanly."""
    m = bpy.data.materials.new("WinGlass"); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); lp = N.new("ShaderNodeLightPath")
    tr = N.new("ShaderNodeBsdfTransparent"); gl = N.new("ShaderNodeBsdfGlossy"); gl.inputs['Roughness'].default_value = 0.02
    fr = N.new("ShaderNodeFresnel"); fr.inputs['IOR'].default_value = 1.5
    refl = N.new("ShaderNodeMixShader"); L.new(fr.outputs[0], refl.inputs[0]); L.new(tr.outputs[0], refl.inputs[1]); L.new(gl.outputs[0], refl.inputs[2])
    mx = N.new("ShaderNodeMixShader"); L.new(lp.outputs['Is Shadow Ray'], mx.inputs[0])
    L.new(refl.outputs[0], mx.inputs[1]); L.new(tr.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs['Surface'])
    return m


def plaster(name, col):
    m = pbr(name, col, 0.85)
    N = m.node_tree.nodes; L = m.node_tree.links; tc = N.new("ShaderNodeTexCoord")
    n = N.new("ShaderNodeTexNoise"); n.inputs['Scale'].default_value = 18; n.inputs['Detail'].default_value = 8
    L.new(tc.outputs['Object'], n.inputs['Vector'])
    b = N.new("ShaderNodeBump"); b.inputs['Strength'].default_value = 0.04; L.new(n.outputs['Fac'], b.inputs['Height'])
    L.new(b.outputs['Normal'], N["Principled BSDF"].inputs['Normal'])
    return m


def screen_material():
    m = bpy.data.materials.new("PhoneScreen"); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); tex = N.new("ShaderNodeTexImage"); tex.name = "UI"; tex.interpolation = 'Cubic'
    os.makedirs(UI_DIR, exist_ok=True)
    tex.image = bpy.data.images.new("UIImg", 540, 1170); tex.image.colorspace_settings.name = 'sRGB'
    L.new(tc.outputs['UV'], tex.inputs['Vector'])
    L.new(tex.outputs['Color'], p.inputs['Emission Color']); p.inputs['Emission Strength'].default_value = 0.55
    p.inputs['Base Color'].default_value = (0.004, 0.004, 0.005, 1); p.inputs['Roughness'].default_value = 0.08
    p.inputs['Coat Weight'].default_value = 1.0; p.inputs['Coat Roughness'].default_value = 0.03
    return m


def set_ui(c, t_sec, typed, sent):
    """Render the mail UI for this frame (Skia) and load it as the screen texture."""
    sys.path.insert(0, os.path.join(HERE, "..", "edit"))
    from intro_cut import phone_ui
    from PIL import Image
    img = phone_ui(t_sec, typed, sent)
    path = os.path.join(UI_DIR, f"ui_{int(typed * 1000):04d}_{int(sent * 1000):04d}_{int(t_sec * 2) % 2}.png")
    if not os.path.exists(path):
        Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).save(path)
    tex = c["screen_mat"].node_tree.nodes["UI"]
    old = tex.image; tex.image = bpy.data.images.load(path, check_existing=True); tex.image.colorspace_settings.name = 'sRGB'
    if old is not None and old.users == 0:
        bpy.data.images.remove(old)


# ============================================================================ furniture
def sofa(x, y, seat_z, mat, leg_mat):
    """Low modern sofa facing -Y. Returns the parts. seat_z = top of the seat cushions."""
    W_, D_ = 2.3, 0.98
    parts = []
    base_top = seat_z - 0.16
    parts.append(box("SofaBase", (x, y, (0.12 + base_top) / 2), (W_, D_, base_top - 0.12), mat, bevel=0.03))
    for k in (-1, 1):
        parts.append(box("SofaArm", (x + k * (W_ / 2 - 0.1), y, (0.12 + seat_z + 0.18) / 2), (0.2, D_, seat_z + 0.06), mat, bevel=0.05))
    parts.append(box("SofaBack", (x, y + D_ / 2 - 0.11, (base_top + seat_z + 0.5) / 2), (W_ - 0.36, 0.22, seat_z + 0.5 - base_top), mat, bevel=0.06))
    for k in (-1, 1):       # two seat cushions and two back cushions, softened
        c1 = box("SeatCushion", (x + k * 0.49, y - 0.06, base_top + 0.08), (0.96, D_ - 0.3, 0.17), mat, bevel=0.06)
        c2 = box("BackCushion", (x + k * 0.49, y + D_ / 2 - 0.3, seat_z + 0.24), (0.94, 0.2, 0.46), mat, bevel=0.08, rot=(math.radians(-9), 0, 0))
        for o in (c1, c2):
            s = o.modifiers.new("s", 'SUBSURF'); s.levels = 2; s.render_levels = 2
        parts += [c1, c2]
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(cyl("SofaLeg", (x + sx * (W_ / 2 - 0.12), y + sy * (D_ / 2 - 0.1), 0.06), 0.02, 0.12, leg_mat, verts=12))
    return parts


def floor_lamp(loc):
    brass = pbr("LampBrass", (0.55, 0.42, 0.25), 0.28, 1.0)
    x, y = loc
    cyl("LampFoot", (x, y, 0.01), 0.16, 0.02, brass, verts=48)
    cyl("LampPole", (x, y, 0.78), 0.012, 1.55, brass, verts=16)
    bpy.ops.mesh.primitive_cone_add(vertices=64, radius1=0.24, radius2=0.17, depth=0.3, location=(x, y, 1.62), end_fill_type='NOTHING')
    sh = bpy.context.active_object; sh.modifiers.new("s", 'SOLIDIFY').thickness = 0.004
    shade = pbr("LampShade", (0.85, 0.78, 0.66), 0.9, 0.0, **{'Transmission Weight': 0.0, 'Subsurface Weight': 0.6})
    p = shade.node_tree.nodes["Principled BSDF"]; p.inputs['Emission Color'].default_value = (1.0, 0.68, 0.38, 1); p.inputs['Emission Strength'].default_value = 1.4
    sh.data.materials.append(shade)
    l = bpy.data.lights.new("LampBulb", 'POINT'); l.energy = 55; l.shadow_soft_size = 0.08; l.color = (1.0, 0.66, 0.38)
    o = bpy.data.objects.new("LampBulb", l); bpy.context.collection.objects.link(o); o.location = (x, y, 1.6)


def bookshelf(x0, y0, mat, axis="y"):
    """Open shelving with books. axis = the direction the shelf runs along."""
    rng = np.random.default_rng(3)
    made = []
    for k in range(6):
        made.append(box("Shelf", (0, 0, 0.3 + k * 0.38), (0.32, 2.2, 0.025), mat))
    for sgn in (-1, 1):
        made.append(box("ShelfSide", (0, sgn * 1.1, 1.25), (0.32, 0.025, 2.5), mat))
    cols = [(0.35, 0.33, 0.3), (0.12, 0.14, 0.18), (0.5, 0.45, 0.38), (0.22, 0.12, 0.1), (0.6, 0.6, 0.58), (0.16, 0.2, 0.17)]
    bm = [pbr(f"Book{i}", c_, 0.7) for i, c_ in enumerate(cols)]
    for k in range(5):
        y = -1.05
        while y < 1.0:
            w = rng.uniform(0.025, 0.05); hh = rng.uniform(0.2, 0.3)
            if rng.random() < 0.12:
                y += 0.15; continue
            made.append(box("Book", (-0.02, y + w / 2, 0.3 + k * 0.38 + 0.0125 + hh / 2), (rng.uniform(0.17, 0.23), w * 0.95, hh), bm[rng.integers(len(bm))]))
            y += w
    rz = math.radians(90) if axis == "x" else 0.0
    for o in made:
        p_ = o.location.copy()
        o.location = (x0 + p_.x * math.cos(rz) - p_.y * math.sin(rz), y0 + p_.x * math.sin(rz) + p_.y * math.cos(rz), p_.z)
        o.rotation_euler = (o.rotation_euler.x, o.rotation_euler.y, o.rotation_euler.z + rz)


def plant(loc, seed=5):
    rng = np.random.default_rng(seed)
    x, y = loc
    cyl("Pot", (x, y, 0.22), 0.2, 0.44, pbr("Pot", (0.55, 0.52, 0.48), 0.75), verts=48)
    cyl("Soil", (x, y, 0.43), 0.18, 0.01, pbr("Soil", (0.03, 0.02, 0.015), 0.95), verts=32)
    leaf_m = pbr("Leaf", (0.05, 0.12, 0.04), 0.45, 0.0, **{'Subsurface Weight': 0.2, 'Coat Weight': 0.3})
    for k in range(14):        # fiddle-leaf style: stems with broad tilted leaves
        a = rng.uniform(0, 2 * math.pi); r = rng.uniform(0.02, 0.12); hgt = rng.uniform(0.7, 1.55)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=0.14, location=(x + r * math.cos(a), y + r * math.sin(a), hgt))
        lf = bpy.context.active_object; lf.scale = (1.0, 0.55, 0.05); lf.rotation_euler = (rng.uniform(-0.7, 0.7), rng.uniform(-0.5, 0.5), a)
        lf.data.materials.append(leaf_m)
        cyl("Stem", (x + r * math.cos(a) * 0.5, y + r * math.sin(a) * 0.5, (0.44 + hgt) / 2), 0.006, hgt - 0.44, leaf_m, verts=6)


# ============================================================================ the view: a CG American downtown, morning
def facade(name, glass_col, frame_col, floor=3.9, bay=1.6, lit_frac=0.0, refl=0.25):
    """Curtain wall: reflective glass panes in a mullion grid, horizontal spandrel bands at each floor."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    geo = N.new("ShaderNodeNewGeometry"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs['Position'], sep.inputs[0])
    nrm = N.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs['Normal'], nrm.inputs[0])
    # horizontal coordinate along the wall: x on Y-facing walls, y on X-facing walls
    ax = N.new("ShaderNodeMath"); ax.operation = 'ABSOLUTE'; L.new(nrm.outputs['X'], ax.inputs[0])
    gt = N.new("ShaderNodeMath"); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = 0.5; L.new(ax.outputs[0], gt.inputs[0])
    hmix = N.new("ShaderNodeMix"); hmix.data_type = 'FLOAT'; L.new(gt.outputs[0], hmix.inputs['Factor'])
    L.new(sep.outputs['X'], hmix.inputs[2]); L.new(sep.outputs['Y'], hmix.inputs[3])
    def frac_line(src, period, width):
        d = N.new("ShaderNodeMath"); d.operation = 'DIVIDE'; d.inputs[1].default_value = period; L.new(src, d.inputs[0])
        f = N.new("ShaderNodeMath"); f.operation = 'FRACT'; L.new(d.outputs[0], f.inputs[0])
        lt = N.new("ShaderNodeMath"); lt.operation = 'LESS_THAN'; lt.inputs[1].default_value = width; L.new(f.outputs[0], lt.inputs[0])
        return lt, d
    vline, _ = frac_line(hmix.outputs[0], bay, 0.06)
    hline, fz = frac_line(sep.outputs['Z'], floor, 0.24)
    frame = N.new("ShaderNodeMath"); frame.operation = 'MAXIMUM'; L.new(vline.outputs[0], frame.inputs[0]); L.new(hline.outputs[0], frame.inputs[1])
    roof = N.new("ShaderNodeMath"); roof.operation = 'GREATER_THAN'; roof.inputs[1].default_value = 0.7; L.new(nrm.outputs['Z'], roof.inputs[0])
    solid = N.new("ShaderNodeMath"); solid.operation = 'MAXIMUM'; L.new(frame.outputs[0], solid.inputs[0]); L.new(roof.outputs[0], solid.inputs[1])
    col = N.new("ShaderNodeMix"); col.data_type = 'RGBA'; L.new(solid.outputs[0], col.inputs['Factor'])
    col.inputs[6].default_value = (*glass_col, 1); col.inputs[7].default_value = (*frame_col, 1)
    L.new(col.outputs[2], p.inputs['Base Color'])
    rough = N.new("ShaderNodeMapRange"); rough.inputs['To Min'].default_value = 0.06; rough.inputs['To Max'].default_value = 0.7
    L.new(solid.outputs[0], rough.inputs['Value']); L.new(rough.outputs[0], p.inputs['Roughness'])
    met = N.new("ShaderNodeMapRange"); met.inputs['To Min'].default_value = refl; met.inputs['To Max'].default_value = 0.0
    L.new(solid.outputs[0], met.inputs['Value']); L.new(met.outputs[0], p.inputs['Metallic'])
    if lit_frac > 0:            # a few offices with lights on (cells, not glitter)
        cell = N.new("ShaderNodeCombineXYZ"); L.new(hmix.outputs[0], cell.inputs[0]); L.new(sep.outputs['Z'], cell.inputs[1])
        sc = N.new("ShaderNodeVectorMath"); sc.operation = 'MULTIPLY'; sc.inputs[1].default_value = (1 / (bay * 4), 1 / floor, 1)
        L.new(cell.outputs[0], sc.inputs[0])
        wn = N.new("ShaderNodeTexWhiteNoise"); wn.noise_dimensions = '2D'; L.new(sc.outputs[0], wn.inputs['Vector'])
        on = N.new("ShaderNodeMath"); on.operation = 'LESS_THAN'; on.inputs[1].default_value = lit_frac; L.new(wn.outputs['Value'], on.inputs[0])
        nf = N.new("ShaderNodeMath"); nf.operation = 'SUBTRACT'; nf.inputs[0].default_value = 1.0; L.new(solid.outputs[0], nf.inputs[1])
        em = N.new("ShaderNodeMath"); em.operation = 'MULTIPLY'; L.new(on.outputs[0], em.inputs[0]); L.new(nf.outputs[0], em.inputs[1])
        es = N.new("ShaderNodeMath"); es.operation = 'MULTIPLY'; es.inputs[1].default_value = 0.6; L.new(em.outputs[0], es.inputs[0])
        p.inputs['Emission Color'].default_value = (1.0, 0.86, 0.68, 1); L.new(es.outputs[0], p.inputs['Emission Strength'])
    return m


def city_view(c):
    """Downtown across the valley: ~70 towers (glass, stone, setbacks, crowns), mid-rise sprawl, freeway, far ridge.
    The house sits on a hillside ~90 m above the valley floor."""
    rng = np.random.default_rng(42)
    Z0 = -90.0
    gm = haze_mix(pbr("Valley", (0.11, 0.115, 0.11), 0.95), color=HAZE, start=150, end=3800, strength=0.8)
    box("ValleyFloor", (0, -3200, Z0 - 0.5), (9000, 6400, 1.0), gm)
    # scrub/oak clumps on the slope (soft rounded crowns, not cones)
    oak = haze_mix(pbr("Oak", (0.05, 0.07, 0.04), 0.9), color=HAZE, start=150, end=3800, strength=0.8)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1.0, location=(0, 0, 0))
    crown = bpy.context.active_object; crown.data.materials.append(oak)
    tx = bpy.data.textures.new("Crown", 'CLOUDS'); tx.noise_scale = 0.45
    dm = crown.modifiers.new("d", 'DISPLACE'); dm.texture = tx; dm.strength = 0.35; bpy.ops.object.modifier_apply(modifier=dm.name)
    crown.location = (0, 0, -900)
    # our own hillside just below the balcony, dry grass and scrub (it falls away toward the city)
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=120, y_subdivisions=60, size=1, location=(0, WIN_Y - 160, 0))
    hill = bpy.context.active_object; hill.scale = (900, 320, 1); bpy.ops.object.transform_apply(scale=True)
    for v in hill.data.vertices:
        d = max(0.0, (WIN_Y - 3.5) - v.co.y)
        v.co.z = -3.5 - (d / 300.0) ** 1.2 * 90.0 * min(1, d / 30) + 2.0 * math.sin(v.co.x / 23.0) * math.sin(d / 17.0)
    hm = haze_mix(pbr("Scrub", (0.16, 0.14, 0.09), 0.95), color=HAZE, start=150, end=3800, strength=0.8)
    N = hm.node_tree.nodes; L = hm.node_tree.links; tc = N.new("ShaderNodeTexCoord")
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 0.08; L.new(tc.outputs['Object'], nz.inputs['Vector'])
    rp = N.new("ShaderNodeValToRGB"); rp.color_ramp.elements[0].color = (0.08, 0.09, 0.06, 1); rp.color_ramp.elements[1].color = (0.24, 0.2, 0.13, 1)
    L.new(nz.outputs['Fac'], rp.inputs['Fac']); L.new(rp.outputs['Color'], N["Principled BSDF"].inputs['Base Color'])
    hill.data.materials.append(hm); bpy.ops.object.shade_smooth()
    for k in range(160):
        x = rng.uniform(-260, 260); d = rng.uniform(25, 420); y = WIN_Y - 3.5 - d
        z = -3.5 - (d / 300.0) ** 1.2 * 90.0 * min(1, d / 30)
        s_ = rng.uniform(2.5, 5.5)
        instance(crown, (x, y, z + s_ * 0.6), scale=(s_ * 1.3, s_ * 1.1, s_ * 0.8))
    # downtown towers
    glass_types = [facade("GlassBlue", (0.05, 0.075, 0.1), (0.42, 0.44, 0.46), lit_frac=0.04, refl=0.35),
                   facade("GlassGreen", (0.06, 0.09, 0.085), (0.5, 0.5, 0.48), lit_frac=0.03, refl=0.3),
                   facade("Stone", (0.08, 0.085, 0.09), (0.62, 0.58, 0.52), floor=3.6, bay=1.4, lit_frac=0.05, refl=0.1),
                   facade("DarkGlass", (0.025, 0.03, 0.04), (0.18, 0.19, 0.2), lit_frac=0.03, refl=0.4)]
    for m in glass_types:
        haze_mix(m, color=HAZE, start=150, end=3800, strength=0.8)
    cx, cy = -120.0, -1900.0
    for k in range(70):
        r = abs(rng.normal(0, 1)) * 260 + 20; a = rng.uniform(0, 2 * math.pi)
        x = cx + r * math.cos(a) * 1.6; y = cy + r * math.sin(a) * 0.7
        hgt = max(40.0, 250 * math.exp(-r / 260) * rng.uniform(0.55, 1.15))
        w = rng.uniform(26, 48); d = rng.uniform(26, 48)
        m = glass_types[rng.integers(len(glass_types))]
        kind = rng.random()
        if kind < 0.35 and hgt > 120:                 # setback tower: three stacked tiers
            z = Z0
            for tier, (fw, fh) in enumerate(((1.0, 0.55), (0.8, 0.3), (0.6, 0.15))):
                box("Tower", (x, y, z + hgt * fh / 2), (w * fw, d * fw, hgt * fh), m); z += hgt * fh
            box("Crown", (x, y, z + 6), (w * 0.35, d * 0.35, 12), m)
        elif kind < 0.55:                             # cylinder-ish tower
            cyl("Tower", (x, y, Z0 + hgt / 2), w * 0.5, hgt, m, verts=24)
        else:
            box("Tower", (x, y, Z0 + hgt / 2), (w, d, hgt), m)
            box("Roof", (x, y, Z0 + hgt + 2.5), (w * 0.5, d * 0.5, 5), pbr("RoofPlant", (0.3, 0.3, 0.3), 0.8))
        if hgt > 180 and rng.random() < 0.5:
            cyl("Mast", (x, y, Z0 + hgt + 22), 0.6, 40, pbr("Mast", (0.5, 0.5, 0.5), 0.5, 0.8), verts=8)
    # mid-rise sprawl around downtown and along the valley
    low = [facade("LowA", (0.09, 0.1, 0.11), (0.55, 0.52, 0.48), floor=3.4, bay=2.0, lit_frac=0.03, refl=0.05),
           facade("LowB", (0.07, 0.08, 0.09), (0.66, 0.64, 0.6), floor=3.4, bay=2.2, lit_frac=0.03, refl=0.05)]
    for m in low:
        haze_mix(m, color=HAZE, start=150, end=3800, strength=0.8)
    for k in range(520):
        x = rng.uniform(-2600, 2400); y = rng.uniform(-3600, -700)
        if (x - cx) ** 2 / 1.6 ** 2 + ((y - cy) / 0.7) ** 2 < 300 ** 2:
            continue
        hgt = rng.uniform(8, 36) * (1.6 if abs(y - cy) < 600 else 1.0)
        box("Low", (x, y, Z0 + hgt / 2), (rng.uniform(25, 70), rng.uniform(25, 70), hgt), low[rng.integers(2)])
    # a freeway across the valley, with a few vehicles that move
    road = haze_mix(pbr("Freeway", (0.18, 0.18, 0.19), 0.7), color=HAZE, start=150, end=3800, strength=0.8)
    box("Freeway", (0, -1100, Z0 + 6), (9000, 28, 1.2), road)
    car_m = [haze_mix(pbr(f"Car{k}", col, 0.3, 0.6), color=HAZE, start=150, end=3800, strength=0.6)
             for k, col in enumerate(((0.6, 0.6, 0.62), (0.05, 0.05, 0.06), (0.3, 0.05, 0.04), (0.8, 0.8, 0.78)))]
    cars = []
    for k in range(40):
        lane = (k % 4) - 1.5; dirn = 1 if lane > 0 else -1
        o = box("Vehicle", (0, -1100 + lane * 6, Z0 + 7.7), (4.6, 1.9, 1.5), car_m[k % 4])
        cars.append((o, rng.uniform(-1500, 1500), dirn * rng.uniform(26, 33)))
    c["cars"] = cars
    # the far ridge behind the city
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=300, y_subdivisions=2, size=1, location=(0, -5200, Z0))
    ridge = bpy.context.active_object; ridge.scale = (14000, 1, 1); bpy.ops.object.transform_apply(scale=True)
    for v in ridge.data.vertices:
        if v.co.y > 0:
            v.co.z = 420 + 160 * math.sin(v.co.x / 900) + 70 * math.sin(v.co.x / 310 + 1) + 30 * math.sin(v.co.x / 97)
    ridge.rotation_euler = (math.radians(90), 0, 0)
    ridge.data.materials.append(haze_mix(pbr("Ridge", (0.15, 0.16, 0.16), 0.9), color=HAZE, start=150, end=3800, strength=0.85))


HAZE = (0.62, 0.68, 0.76)


# ============================================================================ the man and his phone
HOLD = dict(lean=24, head=16)


def pose_man(c, sec, phase):
    """Pose the man for this moment. phase: dict with typing/send/down/back weights."""
    h = c["h"]; reset_pose(h)
    breathe = math.sin(2 * math.pi * sec / 3.6)
    back = phase.get("back", 0.0)                 # 0 = leaning forward over the phone, 1 = sitting back
    lean = HOLD["lean"] * (1 - back) - 15 * back + (0.8 + 1.4 * back) * breathe
    for sd, sg in SIDE.items():
        for b, d in ((f"upperleg01.{sd}", (0.16 * sg, -1, -0.08)), (f"upperleg02.{sd}", (0.16 * sg, -1, -0.08)),
                     (f"lowerleg01.{sd}", (0.06 * sg, -0.32, -1)), (f"lowerleg02.{sd}", (0.06 * sg, -0.32, -1)),
                     (f"foot.{sd}", (0.1 * sg, -1, -0.3))):
            h.aim(b, d)
    for b, a in (("spine05", 4), ("spine04", 5), ("spine03", 5), ("spine02", 4), ("spine01", 3)):
        h.rot(b, (1, 0, 0), lean * a / 21)
    for sd in ("L", "R"):
        h.rot(f"clavicle.{sd}", (1, 0, 0), -1.2 * breathe)
    if c.get("base_loc") is not None:             # sitting back = sliding the hips back into the cushions
        h.arm.location = c["base_loc"] + Vector((0, 0.24 * back, 0.01 * back)); bpy.context.view_layer.update()
    down = phase.get("down", 0.0)                 # 0 = phone held in front of the chest, 1 = arm out to the table
    hand_face = phase.get("face", 0.0)
    if down > 0 or hand_face > 0 or phase.get("left_rest", 0) > 0:
        head_pose(h, sec, back); arms_ik(c, phase); return
    for sd, sg in SIDE.items():
        hold_up = (0.1 * sg, -0.5, -0.86); hold_lo = (-0.55 * sg, -0.75, 0.25); hold_wr = (-0.3 * sg, -0.6, 0.6)
        if sd == "R":
            reach_up = (-0.05, -0.75, -0.65); reach_lo = (0.05, -0.8, -0.6); reach_wr = (0.0, -0.4, -0.9)
            face_up = (0.15 * sg, -0.45, -0.3); face_lo = (-0.45 * sg, -0.25, 0.88); face_wr = (-0.3 * sg, 0.2, 0.9)
            mix = lambda a, b, k: tuple(x * (1 - k) + y * k for x, y in zip(a, b))
            up = mix(mix(hold_up, reach_up, down), face_up, hand_face); lo = mix(mix(hold_lo, reach_lo, down), face_lo, hand_face)
            wr = mix(mix(hold_wr, reach_wr, down), face_wr, hand_face)
        else:
            rest_up = (0.15, -0.35, -0.92); rest_lo = (-0.2, -0.95, -0.1); rest_wr = (-0.2, -0.95, -0.2)
            k = phase.get("left_rest", 0.0)
            mix = lambda a, b, k: tuple(x * (1 - k) + y * k for x, y in zip(a, b))
            up, lo, wr = mix(hold_up, rest_up, k), mix(hold_lo, rest_lo, k), mix(hold_wr, rest_wr, k)
        h.aim(f"upperarm01.{sd}", up); h.aim(f"upperarm02.{sd}", up)
        h.aim(f"lowerarm01.{sd}", lo); h.aim(f"lowerarm02.{sd}", lo); h.aim(f"wrist.{sd}", wr)
    fingers_curl(h, 20, thumb=8)          # fingers flat behind the phone
    head_pose(h, sec, back)


def head_pose(h, sec, back):
    h.rot("neck01", (1, 0, 0), 4 * (1 - back)); h.rot("head", (1, 0, 0), HOLD["head"] * (1 - back) - 22 * back + 1.2 * math.sin(sec * 1.3))
    h.rot("head", (0, 0, 1), 2.5 * math.sin(sec * 0.7))
    bpy.context.view_layer.update()


def arms_ik(c, phase):
    """Shot 4 arms: right hand carries the phone to the table then goes to his face; left hand settles on the thigh."""
    h = c["h"]
    eye = (h.eyes[0].matrix_world.to_translation() + h.eyes[1].matrix_world.to_translation()) / 2
    down, face, rest = phase.get("down", 0.0), phase.get("face", 0.0), phase.get("left_rest", 0.0)
    sh = h.bone_head("upperarm01.R")
    hold = sh + Vector((0.12, -0.38, -0.22))
    table = c["table_spot"] + Vector((0.0, 0.05, 0.07))
    seat = h.bone_head("upperleg01.R") + Vector((-0.3, 0.12, -0.02))          # on the cushion beside his hip
    T = hold.lerp(table, down).lerp(seat, face)
    hand = Vector((0, -0.3, -1)).lerp(Vector((-0.2, -0.6, -0.75)), face)
    reach(h, "R", T, Vector((-0.8, 0.4, -0.3)), hand)
    thigh = (h.bone_head("upperleg02.L") + h.bone_tail("upperleg02.L")) / 2 + Vector((0.0, -0.02, 0.1))
    holdL = h.bone_head("upperarm01.L") + Vector((-0.12, -0.38, -0.22))
    reach(h, "L", holdL.lerp(thigh, rest), Vector((0.7, 0.2, -1.0)), Vector((-0.1, -1, -0.35)))
    fingers_curl(h, 30, thumb=10)
    bpy.context.view_layer.update()


def place_phone(c, phase):
    """Phone between the hands while held; on the coffee table (face down) once put down."""
    h = c["h"]; ph = c["phone"]
    tl, tr = h.bone_head("finger1-2.L"), h.bone_head("finger1-2.R")
    eye = (h.eyes[0].matrix_world.to_translation() + h.eyes[1].matrix_world.to_translation()) / 2
    mid = (tl + tr) / 2
    xa = (tr - tl).normalized()                            # screen +x = his right (viewer right)
    n = (eye - mid).normalized(); n = (n - xa * n.dot(xa)).normalized()
    ya = n.cross(xa).normalized()
    if ya.dot(Vector((0, 0, 1))) < 0:                      # screen "up" points away from him / upward
        xa = -xa; ya = n.cross(xa).normalized()
    grip = phase.get("grip", 0.0)                          # 0 = typing grip, 1 = shifted up to reach Send
    held_c = mid - n * 0.016 + ya * (0.045 - 0.042 * grip)
    q_held = Matrix((xa, ya, n)).transposed().to_quaternion()
    down = phase.get("down", 0.0); placed = phase.get("placed", 0.0)
    hr = h.bone_tail("wrist.R")
    if down > 0:                          # in the right hand on the way down, then flipped onto the table
        held_c = held_c.lerp(hr + Vector((0, -0.06, 0.02)), min(1, down * 1.5))
    table_c = c["table_spot"]; q_table = Quaternion((0, 1, 0), math.pi) @ Quaternion((0, 0, 1), math.radians(12))   # face down
    loc = held_c.lerp(table_c, placed); q = q_held.slerp(q_table, placed)
    ph.location = loc; ph.rotation_mode = 'QUATERNION'; ph.rotation_quaternion = q
    bpy.context.view_layer.update()


def thumb_to(c, side, target, press):
    """Aim the thumb's distal bones at a point just above (press=0) or on (press=1) the screen."""
    h = c["h"]; n = c["screen"].matrix_world.to_3x3() @ Vector((0, 0, 1))
    tgt = target + n * (0.012 * (1 - press) + 0.0015)
    ik2(h, f"finger1-2.{side}", f"finger1-3.{side}", tgt, n)


def screen_point(c, u, v):
    """Point on the screen: u in [-1,1] across, v in [-1,1] up the screen."""
    return c["screen"].matrix_world @ Vector((u * 0.033, v * 0.072, 0.0))


# keyboard targets (u, v) for the two thumbs, and the Send button
KEYS_L = [(-0.6, -0.45), (-0.25, -0.62), (-0.45, -0.3), (-0.75, -0.6), (-0.15, -0.4)]
KEYS_R = [(0.35, -0.5), (0.65, -0.35), (0.2, -0.62), (0.55, -0.62), (0.8, -0.45)]
SEND = (0.74, 0.79)


def animate(c, sec, phase):
    if "send_reach" in phase:
        phase.setdefault("grip", ease(min(1.0, phase["send_reach"] * 1.5)))
    pose_man(c, sec, phase); place_phone(c, phase)
    typed = phase.get("typed", 1.0); sent = phase.get("sent", 0.0)
    if phase.get("down", 0) < 0.05:
        if phase.get("typing", False):          # alternate thumbs, ~6 taps a second
            k = int(sec * 6); f = (sec * 6) % 1.0; press = max(0.0, math.sin(math.pi * min(f / 0.6, 1)))
            side = "L" if k % 2 == 0 else "R"; keys = KEYS_L if side == "L" else KEYS_R
            u, v = keys[k % len(keys)]
            thumb_to(c, side, screen_point(c, u, v), press)
            o = "R" if side == "L" else "L"; ou, ov = (KEYS_R if o == "R" else KEYS_L)[(k + 2) % 5]
            thumb_to(c, o, screen_point(c, ou, ov), 0.0)
        elif "send_reach" in phase:             # right thumb travels up to Send and presses
            r = phase["send_reach"]; pr = phase.get("send_press", 0.0)
            u = -0.05 + (SEND[0] + 0.05) * r; v = -0.4 + (SEND[1] + 0.4) * r
            thumb_to(c, "R", screen_point(c, u, v), pr); thumb_to(c, "L", screen_point(c, -0.5, -0.45), 0.0)
        else:
            thumb_to(c, "R", screen_point(c, 0.4, -0.5), 0.0); thumb_to(c, "L", screen_point(c, -0.5, -0.45), 0.0)
    set_ui(c, sec, typed, sent)
    for o, x0, v in c.get("cars", []):
        o.location.x = ((x0 + v * sec + 4500) % 9000) - 4500


# ============================================================================ build
# Layout: he sits on the sofa facing -Y, toward the window wall (WIN_Y < 0) and the real dawn city beyond it.
def build(variant=None):
    import ph
    c = {}
    w = world_sky(sun_elev_deg=14, sun_rot_deg=0, strength=0.55, tint=(0.82, 0.88, 1.0), air=1.3, aerosol=1.6)
    sunl = bpy.data.lights.new("Sun", 'SUN'); sunl.energy = 0.9; sunl.angle = math.radians(3); sunl.color = (1.0, 0.86, 0.7)
    so_ = bpy.data.objects.new("Sun", sunl); bpy.context.collection.objects.link(so_); so_.rotation_euler = (math.radians(-76), 0, 0)      # sun behind the house: front-lights the city, stays out of the room
    # ---------------------------------------------------------------- room shell
    floor = box("Floor", (0, 0, -0.01), (6.6, 6.0, 0.02), ph.texture("herringbone_parquet", scale=0.6))
    wall = plaster("Plaster", (0.55, 0.53, 0.5))
    box("WallBack", (0, 2.9, 1.5), (6.6, 0.12, 3.0), wall)
    box("WallL", (-3.3, 0, 1.5), (0.12, 6.0, 3.0), wall)
    box("WallR", (3.3, 0, 1.5), (0.12, 6.0, 3.0), wall)
    box("Ceiling", (0, 0, 3.02), (6.6, 6.0, 0.04), plaster("Ceil", (0.62, 0.61, 0.59)))
    frame_m = pbr("BlackSteel", (0.015, 0.015, 0.016), 0.35, 0.8)
    box("WinGlass", (0, WIN_Y, 1.5), (6.5, 0.012, 2.98), window_glass())
    for k in range(4):
        box("Mullion", (-3.25 + k * 2.1667, WIN_Y, 1.5), (0.05, 0.06, 3.0), frame_m)
    box("Transom", (0, WIN_Y, 2.98), (6.6, 0.07, 0.06), frame_m); box("Sill", (0, WIN_Y, 0.02), (6.6, 0.09, 0.04), frame_m)
    pt = bpy.data.lights.new("Portal", 'AREA'); pt.shape = 'RECTANGLE'; pt.size = 6.5; pt.size_y = 2.98; pt.cycles.is_portal = True
    po = bpy.data.objects.new("Portal", pt); bpy.context.collection.objects.link(po); po.location = (0, WIN_Y - 0.05, 1.5); po.rotation_euler = (math.radians(90), 0, 0)
    city_view(c)
    # balcony outside; the city sits beyond the rail
    box("Deck", (0, WIN_Y - 1.6, -0.06), (6.6, 3.2, 0.1), ph.texture("wood_floor_deck", scale=0.8))
    box("Balustrade", (0, WIN_Y - 3.2, 0.5), (6.6, 0.02, 1.0), glass("Bal", (0.9, 0.93, 0.95)))
    box("Rail", (0, WIN_Y - 3.2, 1.0), (6.6, 0.06, 0.04), frame_m)
    box("Rug", (0, -0.6, 0.004), (3.0, 2.4, 0.008), fabric("Rug", (0.36, 0.34, 0.31), 0.95, 0.4, 700))
    # ---------------------------------------------------------------- the man, then the sofa fitted under him
    h = man("Man"); c["h"] = h
    h.arm.location = (0.0, 0.05, 0.0); bpy.context.view_layer.update()
    pose_man(c, 0.0, {"typing": True})
    wv = np.concatenate([_world_verts(o) for o in h.parts if o.type == 'MESH'])
    h.arm.location.z -= wv[:, 2].min(); bpy.context.view_layer.update()
    c["base_loc"] = Vector(h.arm.location)
    hips_z = (h.bone_head("upperleg02.L").z + h.bone_head("upperleg02.R").z) / 2
    hips_y = h.bone_head("upperleg01.L").y
    root, ms = ph.model("sofa_02")
    lo, hi = ph.bounds(ms)
    seat_h = 0.44                                   # sofa_02 seat cushion height (measured from the model)
    k = (hips_z - 0.07) / seat_h
    root.scale = (1.15, k, k); bpy.context.view_layer.update()
    lo, hi = ph.bounds(ms)
    root.location = (0.25, hips_y + 0.16 - (lo.y + hi.y) / 2 + 0.0, 0.0); bpy.context.view_layer.update()
    c["sofa"] = ms
    t_root, t_ms = ph.model("modern_coffee_table_02", loc=(0.05, -0.95, 0.0))
    tl, th = ph.bounds(t_ms)
    c["table_spot"] = Vector((0.2, -0.7, th.z + 0.0045))
    ph.model("side_table_01", loc=(-1.25, 0.15, 0.0))
    ph.model("ceramic_vase_01", loc=(-1.3, 0.12, 0.55))
    ph.model("potted_plant_02", loc=(1.75, 0.35, 0.0), scale=1.35)
    bookshelf(0.0, 2.7, wood("ShelfOak", (0.12, 0.08, 0.05), (0.22, 0.15, 0.09), rough=0.4, coat=0.2), axis="x")
    box("Frame", (-3.22, 1.0, 1.65), (0.03, 1.3, 0.9), frame_m)
    box("Print", (-3.2, 1.0, 1.65), (0.01, 1.2, 0.8), pbr("Print", (0.6, 0.58, 0.54), 0.9))
    floor_lamp((-1.5, 1.6))
    # ---------------------------------------------------------------- the phone
    phone = box("Phone", (0, 0, 0), (0.072, 0.152, 0.008), pbr("PhoneBody", (0.02, 0.02, 0.022), 0.25, 0.8), bevel=0.006)
    sm = screen_material(); c["screen_mat"] = sm
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0.0041)); scr = bpy.context.active_object; scr.name = "Screen"
    scr.scale = (0.066, 0.144, 1); bpy.ops.object.transform_apply(scale=True); scr.data.materials.append(sm)
    scr.parent = phone
    sl = bpy.data.lights.new("ScreenLight", 'AREA'); sl.energy = 0.7; sl.size = 0.07; sl.color = (0.8, 0.88, 1.0)
    so = bpy.data.objects.new("ScreenLight", sl); bpy.context.collection.objects.link(so); so.parent = phone; so.location = (0, 0, 0.012)
    so.visible_camera = False; so.visible_glossy = False
    c.update(phone=phone, screen=scr, screen_light=sl)
    animate(c, 0.0, {"typing": True, "typed": 0.2})
    return c


# ============================================================================ moves
# A (3.5 s) "I was unfaithful to my wife."  -- from behind him, creeping past his right shoulder to the phone
# B (5.5 s) "That's what Nvidia CEO ... November eighth." -- from the front, low across the table; he presses send
LEAD = 2.5                                  # picture only before the first word (viewers settle in)
DUR = {"behind": LEAD + 3.25, "front": 4.65}  # from the voiceover (shifted by LEAD): 0.00-5.75 / 5.75-10.40


def _chest(c):
    return (c["h"].bone_head("spine03") + c["h"].bone_head("neck01")) / 2


def _eyes(c):
    bpy.context.view_layer.update()
    return c["h"].bone_head("head") + Vector((0, -0.09, 0.07))


def anim_behind(c, t):
    s = t * DUR["behind"]
    v = s - LEAD                              # voiceover time; he is already typing quietly during the lead-in
    animate(c, s, {"typing": v < 2.3, "typed": min(1.0, 0.1 + 0.9 * max(0.0, v + 1.0) / 3.2)})


def anim_front(c, t):
    s = t * DUR["front"]
    ph = {"typed": 1.0}
    if s < 1.4:                                  # hesitates, thumb hovering
        ph["send_reach"] = 0.0
    elif s < 2.4:                                # thumb travels to Send
        ph["send_reach"] = ease((s - 1.4) / 1.0)
    else:                                        # presses, the message goes
        ph["send_reach"] = 1.0; ph["send_press"] = max(0.0, math.sin(math.pi * min((s - 2.4) / 0.45, 1.0))) if s < 2.85 else 0.0
        ph["sent"] = min(1.0, max(0.0, (s - 2.7) / 0.9))
    ph["back"] = 0.35 * ease(max(0.0, (s - 3.6) / 1.6))       # afterwards he straightens up a little, looks out
    animate(c, LEAD + 3.25 + s, ph)


def cam_behind(c, t):
    """Over his right shoulder, close on the phone as he types (the whole shot). Gentle creep in."""
    e = ease(t)
    sh = c["h"].bone_head("upperarm01.R"); phn = c["phone"].location
    start = sh + Vector((-0.21, 0.35, 0.34)); end = sh + Vector((-0.17, 0.27, 0.32))
    return (start.lerp(end, e), phn, 48 + 2 * e)


def cam_front(c, t):
    e = ease(t)
    hd = c["h"].bone_head("head")
    loc = hd + Vector((-0.95, -2.1, -0.32)).lerp(Vector((-0.75, -1.75, -0.26)), e)    # his right-front, low: screen edge + face
    tgt = hd.lerp(c["phone"].location, 0.55)
    return (loc, tgt, 45)


def focus_front(c, t):
    k = ease(min(1.0, max(0.0, (t - 0.45) / 0.25)))          # rack from the phone to his face as he sends
    return c["phone"].location.lerp(_eyes(c), k)


MOVES = {
    "behind": dict(kind="anim", dof=2.4, far=12.0, cam=cam_behind, focus=lambda c, t: c["phone"].location, anim=anim_behind),
    "front": dict(kind="anim", dof=2.0, far=12.0, cam=cam_front, focus=focus_front, anim=anim_front),
}
