"""Shared pieces for The Kidnapper Who Only Played a Radio Jingle (Bavaria, 1981). Chat B reuses these for Ch3-5.

  mat(key)                 cached materials (Poly Haven scans + procedural)
  wall_x / wall_y          walls with rectangular holes; window_unit, door_leaf
  sky(kind)                cinematic skies + one hard key: "grey", "lowsun", "sunset", "dusk", "night", "mist", "interior_night"
  person(role)             unnamed 1981 figures: mother, father, brother, sister, uncle, aunt, neighbour, officer, detective,
                           tech, firefighter, diver, postman, expert ; all MakeHuman, period colours
  rotary_phone, reel_deck, headphones, teddy, kitchen_radio, portable_radio, bicycle, upright_piano, torch, wall_clock
  driven(idblock, path, expr)   frame-driven property (plays in any render, no scripts)

Conventions: metres, Z up. A person's rotation z = th faces (sin th, -cos th).
"""
import math, os
import numpy as np
import bpy
from mathutils import Vector, Matrix
from kit import pbr, box, cyl, join, glass, emissive, area_light, point_at, wood, fabric
import ph
import rjp
from rjp import recolor, two_tone, stand, seat, walk, work, forward, ground, upright, face, model_fit, tint_model, hide, person_objs
from human import Human, add_asset, reset_pose, fingers_curl, pose_walk, pose_sit, reach, _world_verts, SIDE

_MAT = {}


# ============================================================================ materials
def window_glass():
    """Reflective for the camera, transparent to shadow rays so daylight reaches the rooms cleanly."""
    m = bpy.data.materials.new("WinGlass"); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); lp = N.new("ShaderNodeLightPath")
    tr = N.new("ShaderNodeBsdfTransparent"); gl = N.new("ShaderNodeBsdfGlossy"); gl.inputs['Roughness'].default_value = 0.03
    fr = N.new("ShaderNodeFresnel"); fr.inputs['IOR'].default_value = 1.6
    refl = N.new("ShaderNodeMixShader"); L.new(fr.outputs[0], refl.inputs[0]); L.new(tr.outputs[0], refl.inputs[1]); L.new(gl.outputs[0], refl.inputs[2])
    mx = N.new("ShaderNodeMixShader"); L.new(lp.outputs['Is Shadow Ray'], mx.inputs[0])
    L.new(refl.outputs[0], mx.inputs[1]); L.new(tr.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs['Surface'])
    return m


def frosted_glass():
    m = pbr("Frosted", (0.85, 0.85, 0.82), 0.35, 0.0, **{'Transmission Weight': 1.0, 'IOR': 1.5})
    return m


def net_curtain():
    """Sheer net curtain: a soft translucent veil to the camera (fine weave pattern), and lets daylight and shadow
    rays through, so a window still works as the key light."""
    m = bpy.data.materials.new("NetCurtain"); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); lp = N.new("ShaderNodeLightPath")
    tr = N.new("ShaderNodeBsdfTransparent")
    tl = N.new("ShaderNodeBsdfTranslucent"); tl.inputs['Color'].default_value = (0.85, 0.83, 0.78, 1)
    tc = N.new("ShaderNodeTexCoord"); wv = N.new("ShaderNodeTexWave"); wv.inputs['Scale'].default_value = 60; wv.inputs['Distortion'].default_value = 2
    L.new(tc.outputs['Object'], wv.inputs['Vector'])
    mr = N.new("ShaderNodeMapRange"); mr.inputs['To Min'].default_value = 0.45; mr.inputs['To Max'].default_value = 0.7
    L.new(wv.outputs['Fac'], mr.inputs['Value'])
    veil = N.new("ShaderNodeMixShader"); L.new(mr.outputs[0], veil.inputs[0]); L.new(tr.outputs[0], veil.inputs[1]); L.new(tl.outputs[0], veil.inputs[2])
    mx = N.new("ShaderNodeMixShader"); L.new(lp.outputs['Is Shadow Ray'], mx.inputs[0])
    L.new(veil.outputs[0], mx.inputs[1]); L.new(tr.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs['Surface'])
    return m


def retint(m, mul=(1, 1, 1), sat=1.0, val=1.0):
    N = m.node_tree.nodes; L = m.node_tree.links
    p = next((n for n in N if n.type == 'BSDF_PRINCIPLED'), None)
    if p is None:
        return m
    src = p.inputs['Base Color'].links[0].from_socket if p.inputs['Base Color'].links else None
    hs = N.new("ShaderNodeHueSaturation"); hs.inputs['Saturation'].default_value = sat; hs.inputs['Value'].default_value = val
    if src is not None:
        L.new(src, hs.inputs['Color'])
    else:
        hs.inputs['Color'].default_value = p.inputs['Base Color'].default_value
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
    L.new(hs.outputs[0], mx.inputs[6]); mx.inputs[7].default_value = (*mul, 1)
    L.new(mx.outputs[2], p.inputs['Base Color'])
    return m


def wallpaper(name, ground, stripe, scale=6.0):
    """Faded 1970s wallpaper: soft vertical stripes with a small leaf noise, slightly worn."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    geo = N.new("ShaderNodeNewGeometry")
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs['Position'], sep.inputs[0])
    add = N.new("ShaderNodeMath"); add.operation = 'ADD'; L.new(sep.outputs['X'], add.inputs[0]); L.new(sep.outputs['Y'], add.inputs[1])
    wv = N.new("ShaderNodeTexWave"); wv.wave_type = 'BANDS'; wv.inputs['Scale'].default_value = 1.0
    cm = N.new("ShaderNodeCombineXYZ"); mul = N.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = scale
    L.new(add.outputs[0], mul.inputs[0]); L.new(mul.outputs[0], cm.inputs[0]); L.new(cm.outputs[0], wv.inputs['Vector'])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 40; L.new(geo.outputs['Position'], nz.inputs['Vector'])
    rr = N.new("ShaderNodeMapRange"); rr.inputs['From Min'].default_value = 0.35; rr.inputs['From Max'].default_value = 0.75
    L.new(wv.outputs['Fac'], rr.inputs['Value'])
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; L.new(rr.outputs[0], mx.inputs['Factor'])
    mx.inputs[6].default_value = (*ground, 1); mx.inputs[7].default_value = (*stripe, 1)
    wear = N.new("ShaderNodeMix"); wear.data_type = 'RGBA'; wear.blend_type = 'MULTIPLY'; wear.inputs['Factor'].default_value = 0.25
    L.new(mx.outputs[2], wear.inputs[6]); L.new(nz.outputs['Color'], wear.inputs[7])
    L.new(wear.outputs[2], p.inputs['Base Color']); p.inputs['Roughness'].default_value = 0.8
    return m


def mat(key):
    if key in _MAT and _MAT[key].name in bpy.data.materials:
        return _MAT[key]
    T_ = lambda aid, sc, tint=None: ph.texture(aid, scale=sc, name=key, tint=tint)
    table = {
        "plaster": lambda: T_("painted_plaster_wall", 0.4, (0.86, 0.80, 0.68)),
        "plaster_ext": lambda: T_("painted_plaster_wall", 0.3, (0.92, 0.88, 0.80)),
        "paper": lambda: wallpaper("Wallpaper", (0.62, 0.55, 0.42), (0.52, 0.44, 0.32)),
        "paper_hall": lambda: wallpaper("WallpaperHall", (0.58, 0.56, 0.46), (0.50, 0.47, 0.38), scale=8.0),
        "parquet": lambda: T_("wood_floor", 0.6, (0.75, 0.6, 0.45)),
        "floor": lambda: T_("old_wood_floor", 0.5, (0.8, 0.7, 0.6)),
        "tiles": lambda: T_("floor_tiles_08", 0.6, (0.75, 0.68, 0.6)),
        "lino": lambda: T_("old_linoleum_flooring_01", 0.5, (0.8, 0.72, 0.6)),
        "roof": lambda: T_("roof_tiles", 0.35, (0.55, 0.38, 0.32)),
        "gravel": lambda: T_("gravel_floor_02", 1.6, (0.85, 0.82, 0.76)),
        "forest": lambda: T_("forest_ground_04", 0.35),
        "leafy": lambda: T_("forrest_ground_01", 0.3),
        "grass": lambda: T_("leafy_grass", 0.25, (0.7, 0.75, 0.6)),
        "mud": lambda: T_("brown_mud_02", 0.4),
        "soil": lambda: T_("brown_mud_leaves_01", 0.45),
        "asphalt": lambda: T_("asphalt_02", 0.12, (0.8, 0.8, 0.8)),
        "conc": lambda: T_("concrete_floor_02", 0.3),
        "planks": lambda: T_("wood_planks_grey", 0.5, (0.75, 0.65, 0.55)),
        "rawwood": lambda: T_("raw_plank_wall", 0.6, (0.85, 0.75, 0.6)),
        "trim": lambda: pbr("Trim", (0.72, 0.68, 0.58), 0.45),
        "darkwood": lambda: wood("DarkWood", (0.035, 0.018, 0.01), (0.11, 0.06, 0.03), scale=(0.3, 6, 6), rough=0.35, coat=0.4),
        "oak": lambda: wood("Oak", (0.12, 0.07, 0.035), (0.30, 0.18, 0.09), scale=(0.3, 6, 6), rough=0.45, coat=0.25),
        "pine": lambda: wood("Pine", (0.28, 0.17, 0.08), (0.5, 0.34, 0.18), scale=(0.3, 6, 6), rough=0.5, coat=0.15),
        "piano": lambda: wood("PianoWood", (0.02, 0.01, 0.006), (0.075, 0.035, 0.018), scale=(0.3, 5, 5), rough=0.18, coat=0.9),
        "chrome": lambda: pbr("Chrome", (0.75, 0.75, 0.77), 0.15, 1.0),
        "steel": lambda: pbr("Steel", (0.45, 0.46, 0.47), 0.35, 1.0),
        "black": lambda: pbr("BlackPlastic", (0.012, 0.012, 0.013), 0.4),
        "ivory": lambda: pbr("Ivory", (0.78, 0.75, 0.66), 0.25, 0.0, **{'Coat Weight': 0.5}),
        "glass": lambda: window_glass(),
        "frosted": lambda: frosted_glass(),
        "phone": lambda: pbr("PhonePlastic", (0.30, 0.33, 0.28), 0.3, 0.0, **{'Coat Weight': 0.5, 'Coat Roughness': 0.15}),   # Bundespost grey-green
        "curtain": lambda: fabric("Curtain", (0.42, 0.34, 0.24), 0.85, 0.5),
        "net": lambda: net_curtain(),
        "rug": lambda: fabric("Rug", (0.30, 0.12, 0.08), 0.95, 0.4, 300),
        "bike_red": lambda: pbr("BikeRed", (0.42, 0.03, 0.025), 0.3, 0.2, **{'Coat Weight': 0.8, 'Coat Roughness': 0.12}),
        "tyre": lambda: pbr("BikeTyre", (0.015, 0.015, 0.015), 0.7),
        "fur": lambda: fabric("ToyFur", (0.40, 0.26, 0.14), 0.95, 1.0, 1500),
        "fur2": lambda: fabric("ToyFur2", (0.62, 0.58, 0.52), 0.95, 1.0, 1500),
        "uniform": lambda: fabric("PoliceGreen", (0.055, 0.075, 0.045), 0.85, 0.3),
    }
    _MAT[key] = table[key]()
    return _MAT[key]


def apply_rot(o):
    """kit.join keeps the first part's rotation as the object's own: bake it into the mesh so local axes are world axes."""
    for ob in bpy.context.selected_objects:
        ob.select_set(False)
    o.select_set(True); bpy.context.view_layer.objects.active = o
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    return o


def driven(idblock, path, expr, index=-1):
    """Frame-driven property: plays in any render of the .blend (simple expression, no Python)."""
    fc = idblock.driver_add(path, index) if index >= 0 else idblock.driver_add(path)
    d = fc.driver; d.type = 'SCRIPTED'; d.expression = expr
    return d


def emission_driven(m, expr):
    p = m.node_tree.nodes["Principled BSDF"]
    return driven(p.inputs['Emission Strength'], "default_value", expr)


# ============================================================================ walls / openings
def _wall_cells(u0, u1, z0, z1, holes):
    cuts = sorted({u0, u1} | {h[0] for h in holes if u0 < h[0] < u1} | {h[1] for h in holes if u0 < h[1] < u1})
    cells = []
    for ua, ub in zip(cuts[:-1], cuts[1:]):
        um = (ua + ub) / 2
        hz = sorted((h[2], h[3]) for h in holes if h[0] <= um <= h[1])
        cz = z0
        for (za, zb) in hz:
            if za > cz:
                cells.append((ua, ub, cz, min(za, z1)))
            cz = max(cz, zb)
        if z1 > cz:
            cells.append((ua, ub, cz, z1))
    merged = []
    for c in cells:
        if merged and merged[-1][1] == c[0] and merged[-1][2:] == c[2:]:
            merged[-1] = (merged[-1][0], c[1], c[2], c[3])
        else:
            merged.append(c)
    return [c for c in merged if c[1] - c[0] > 1e-4 and c[3] - c[2] > 1e-4]


def wall_x(name, x0, x1, y, z0, z1, t, m, holes=()):
    """Wall along X at y (thickness t along Y). holes: (xa, xb, za, zb)."""
    return [box(name, ((a + b) / 2, y, (za + zb) / 2), (b - a, t, zb - za), m) for (a, b, za, zb) in _wall_cells(x0, x1, z0, z1, holes)]


def wall_y(name, y0, y1, x, z0, z1, t, m, holes=()):
    return [box(name, (x, (a + b) / 2, (za + zb) / 2), (t, b - a, zb - za), m) for (a, b, za, zb) in _wall_cells(y0, y1, z0, z1, holes)]


def window_unit(axis, u, w, pos, za, zb, depth=0.14, inward=1, curtains=True, frame_m=None):
    """A casement window filling a hole: white-painted wooden frame, a centre mullion, a transom, glass,
    and (inside) net curtains plus heavy side curtains. axis 'x': wall along X at y=pos ; 'y': wall along Y at x=pos.
    inward: +1 / -1, which side of the wall is the room (along the wall normal)."""
    fr = frame_m or pbr("WinFrame", (0.74, 0.72, 0.66), 0.4)
    parts = []

    def B(nm, cu, cz, su, sz, sd, mm, off=0.0):
        if axis == 'x':
            return box(nm, (cu, pos + off, cz), (su, sd, sz), mm)
        return box(nm, (pos + off, cu, cz), (sd, su, sz), mm)
    f = 0.07
    parts += [B("WF", u, za + f / 2, w, f, depth, fr), B("WF", u, zb - f / 2, w, f, depth, fr),
              B("WF", u - w / 2 + f / 2, (za + zb) / 2, f, zb - za, depth, fr), B("WF", u + w / 2 - f / 2, (za + zb) / 2, f, zb - za, depth, fr),
              B("WMull", u, (za + zb) / 2, 0.06, zb - za, depth * 0.8, fr), B("WTran", u, zb - (zb - za) * 0.28, w, 0.05, depth * 0.8, fr)]
    g = B("WGlass", u, (za + zb) / 2, w - 2 * f, zb - za - 2 * f, 0.006, mat("glass"))
    parts.append(B("WSill", u, za - 0.025, w + 0.12, 0.04, depth + 0.16, fr, off=inward * 0.06))
    cur = []
    if curtains:
        cur.append(B("WNet", u, (za + zb) / 2 + 0.02, w - 0.1, zb - za - 0.05, 0.01, mat("net"), off=inward * 0.11))
        for k in (-1, 1):
            cur.append(B("WCurt", u + k * (w / 2 + 0.12), (za + zb) / 2 + 0.15, 0.32, zb - za + 0.45, 0.04, mat("curtain"), off=inward * 0.16))
        cur.append(B("WRod", u, zb + 0.32, w + 0.7, 0.03, 0.03, mat("darkwood"), off=inward * 0.17))
    return parts, g, cur


def door_leaf(name, hinge, width, height, m, axis='x', glass_panel=False, thick=0.045):
    """A door panel parented to a hinge empty (rotate the empty about Z to open). Two raised panels or a glass pane."""
    e = bpy.data.objects.new(name + "Hinge", None); bpy.context.collection.objects.link(e); e.location = hinge
    hx, hy, hz = hinge
    def B(nm, du, dz, su, sz, st, mm, dn=0.0):
        if axis == 'x':
            return box(nm, (hx + du, hy + dn, hz + dz), (su, st, sz), mm, bevel=0.003)
        return box(nm, (hx + dn, hy + du, hz + dz), (st, su, sz), mm, bevel=0.003)
    parts = [B(name, width / 2, height / 2, width, height, thick, m)]
    if glass_panel:
        gp = B(name + "Glass", width / 2, height * 0.66, width * 0.6, height * 0.42, thick + 0.004, mat("frosted"))
        parts.append(gp)
    else:
        for zc in (0.27, 0.7):
            for s in (-1, 1):
                parts.append(B(name + "Pan", width / 2, height * zc, width * 0.66, height * 0.33, 0.012, m, dn=s * thick / 2))
    for s in (-1, 1):
        if axis == 'x':
            parts.append(cyl(name + "Knob", (hx + width - 0.07, hy + s * (thick / 2 + 0.03), hz + 1.0), 0.012, 0.06, mat("chrome"), 12, rot=(math.radians(90), 0, 0)))
        else:
            parts.append(cyl(name + "Knob", (hx + s * (thick / 2 + 0.03), hy + width - 0.07, hz + 1.0), 0.012, 0.06, mat("chrome"), 12, rot=(0, math.radians(90), 0)))
    dj = join(parts, name)
    dj.parent = e; dj.matrix_parent_inverse = e.matrix_world.inverted()
    return e


# ============================================================================ skies (cinematic: one hard key, dark fill)
SKIES = {
    #             horizon              zenith               sun elev/az  sun col              energy  angle  bg strength  cloud
    "grey":     ((0.36, 0.40, 0.44), (0.20, 0.24, 0.30), 14, 210, (0.95, 0.92, 0.86), 1.2, 12, 0.55, 0.85),
    "lowsun":   ((0.70, 0.52, 0.34), (0.20, 0.28, 0.40), 6, 260, (1.0, 0.62, 0.32), 5.0, 1.0, 0.45, 0.4),
    "sunset":   ((0.80, 0.42, 0.20), (0.14, 0.18, 0.30), 2, 275, (1.0, 0.45, 0.18), 4.0, 1.0, 0.35, 0.35),
    "dusk":     ((0.24, 0.24, 0.34), (0.05, 0.07, 0.14), -3, 280, (0.55, 0.6, 0.9), 0.0, 8, 0.45, 0.4),
    "bluehour": ((0.26, 0.30, 0.44), (0.07, 0.10, 0.20), 20, 150, (0.5, 0.6, 1.0), 0.25, 3, 1.0, 0.35),
    "night":    ((0.020, 0.026, 0.045), (0.004, 0.006, 0.014), 30, 140, (0.55, 0.65, 0.95), 0.06, 1.0, 1.0, 0.3),
    "mist":     ((0.50, 0.53, 0.55), (0.30, 0.34, 0.38), 9, 110, (1.0, 0.86, 0.68), 1.8, 4, 0.6, 0.8),
}


def sky(kind="grey", rot=0.0):
    """World gradient + broken cloud + one sun. Returns (world, sun object or None). rot turns the sun (degrees)."""
    bpy.context.scene.cycles.sample_clamp_indirect = 3.0
    hor, zen, el, az, scol, en, ang, strength, cover = SKIES[kind]
    w = bpy.data.worlds.new("Sky"); bpy.context.scene.world = w; w.use_nodes = True
    N = w.node_tree.nodes; L = w.node_tree.links; N.clear()
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs['Generated'], sep.inputs[0])
    mr = N.new("ShaderNodeMapRange"); mr.inputs['From Min'].default_value = -0.05; mr.inputs['From Max'].default_value = 0.6
    L.new(sep.outputs['Z'], mr.inputs['Value'])
    ramp = N.new("ShaderNodeValToRGB"); L.new(mr.outputs[0], ramp.inputs['Fac'])
    ramp.color_ramp.elements[0].color = (*hor, 1); ramp.color_ramp.elements[1].color = (*zen, 1)
    # sun-side glow on the horizon
    bg = N.new("ShaderNodeBackground"); bg.inputs['Strength'].default_value = strength
    L.new(ramp.outputs['Color'], bg.inputs['Color'])
    out = N.new("ShaderNodeOutputWorld"); L.new(bg.outputs[0], out.inputs['Surface'])
    if cover > 0:
        rjp.cloud_sky(w, cover=cover, color=tuple(min(1.0, c * 1.35 + 0.03) for c in hor), scale=2.0)
    s = None
    if en > 0:
        from common import sun
        s = sun(el, az + rot, en, scol, ang)
    return w, s


def haze_box(loc, size, density=0.015, color=(0.75, 0.8, 0.85), anis=0.4):
    from kit import haze
    return haze(loc, size, density, color, anis)


def finish_scene():
    sc = bpy.context.scene
    if os.environ.get("RJ_DEBUG"):                       # layout checks: flat bright light everywhere
        sc.view_settings.exposure = 1.0
        for k, (x, y) in enumerate(((0, 0), (-4, 0), (0, 5), (5, -5), (-5, 5))):
            l = bpy.data.lights.new("DbgL", 'POINT'); l.energy = 900; l.shadow_soft_size = 2
            o = bpy.data.objects.new("DbgL", l); sc.collection.objects.link(o); o.location = (x, y, 2.3)
    sc.cycles.sample_clamp_indirect = 3.0
    sc.cycles.blur_glossy = 1.0


# ============================================================================ people (unnamed; 1981 clothes)
ROLES = {
    # 1981 clothes (garment meshes checked in a lineup render): suit+tie = male_elegantsuit01, knit jumper =
    # male_casualsuit02, collared shirt = male_casualsuit01/03, field/uniform jacket = male_casualsuit05,
    # women: long-sleeved blouse + knee skirt = female_elegantsuit01.
    #              gender years  cloth                 hair       hair val  hue   sat  val   height weight
    "mother":     (0.0, 42, "female_elegantsuit01", "long01", 0.22, 0.08, 0.18, 0.55, 0.45, 0.45),
    "father":     (1.0, 46, "male_casualsuit01", "short02", 0.30, 0.10, 0.12, 0.45, 0.5, 0.5),
    "brother":    (1.0, 19, "male_casualsuit02", "short04", 0.28, 0.58, 0.20, 0.40, 0.55, 0.38),
    "sister":     (0.0, 10, "male_casualsuit02", "ponytail01", 0.42, 0.0, 0.0, 0.5, 0.15, 0.38),
    "uncle":      (1.0, 50, "male_casualsuit05", "short03", 0.45, 0.07, 0.15, 0.40, 0.5, 0.55),
    "aunt":       (0.0, 45, "female_elegantsuit01", "bob01", 0.30, 0.95, 0.15, 0.55, 0.45, 0.5),
    "neighbour":  (0.0, 58, "female_elegantsuit01", "bob01", 0.6, 0.05, 0.12, 0.6, 0.4, 0.55),
    "officer":    (1.0, 38, "male_casualsuit05", "short01", 0.25, 0.28, 0.35, 0.25, 0.55, 0.5),
    "officer2":   (1.0, 30, "male_casualsuit05", "short03", 0.30, 0.28, 0.35, 0.25, 0.5, 0.45),
    "officer3":   (1.0, 45, "male_casualsuit05", "short02", 0.40, 0.28, 0.35, 0.25, 0.5, 0.55),
    "plainclothes": (1.0, 40, "male_elegantsuit01", "short01", 0.25, 0.09, 0.18, 0.38, 0.55, 0.5),
    "detective":  (1.0, 44, "male_elegantsuit01", "short02", 0.30, 0.09, 0.18, 0.38, 0.5, 0.5),
    "tech":       (1.0, 34, "male_casualsuit03", "short04", 0.25, 0.55, 0.12, 0.35, 0.5, 0.45),
    "firefighter":(1.0, 36, "male_casualsuit05", "short01", 0.25, 0.62, 0.40, 0.14, 0.55, 0.55),
    "diver":      (1.0, 32, "male_casualsuit02", "short01", 0.25, 0.60, 0.05, 0.03, 0.55, 0.45),
    "postman":    (1.0, 52, "male_casualsuit05", "short02", 0.45, 0.60, 0.22, 0.30, 0.5, 0.5),
    "expert":     (1.0, 55, "male_elegantsuit01", "short02", 0.55, 0.58, 0.08, 0.30, 0.5, 0.5),
    "expert2":    (0.0, 47, "female_elegantsuit01", "bob02", 0.30, 0.58, 0.10, 0.40, 0.48, 0.45),
}

# outfits: top colour above, bottom below a split (fraction of the person's height); plain period fabrics
OUTFITS = {
    "sister": ((0.30, 0.30, 0.29), (0.035, 0.07, 0.04), 0.53),          # grey cardigan-jumper, dark green trousers
    "officer": ((0.07, 0.10, 0.06), (0.30, 0.27, 0.20), 0.50),          # green uniform jacket, beige trousers
    "officer2": ((0.07, 0.10, 0.06), (0.30, 0.27, 0.20), 0.50),
    "officer3": ((0.07, 0.10, 0.06), (0.30, 0.27, 0.20), 0.50),
    "plainclothes": ((0.16, 0.12, 0.08), (0.14, 0.12, 0.10), 0.50),     # brown sports jacket, light shirt, tie (mesh)
    "detective": ((0.11, 0.10, 0.09), (0.11, 0.10, 0.09), 0.50),        # grey-brown suit
    "firefighter": ((0.03, 0.04, 0.07), (0.03, 0.04, 0.07), 0.5),
    "diver": ((0.012, 0.012, 0.014), (0.012, 0.012, 0.014), 0.5),
    "postman": ((0.12, 0.16, 0.24), (0.10, 0.12, 0.17), 0.50),
    "mother": ((0.30, 0.26, 0.20), (0.10, 0.08, 0.07), 0.56),           # oatmeal knit blouse, dark brown skirt
    "aunt": ((0.10, 0.12, 0.18), (0.12, 0.12, 0.14), 0.56),
    "neighbour": ((0.10, 0.14, 0.12), (0.20, 0.17, 0.15), 0.56),
    "expert2": ((0.07, 0.07, 0.09), (0.10, 0.10, 0.12), 0.56),
    "expert": ((0.08, 0.09, 0.11), (0.08, 0.09, 0.11), 0.50),
    "father": ((0.22, 0.20, 0.17), (0.11, 0.11, 0.12), 0.53),           # check-shirt brown, dark trousers
    "brother": ((0.05, 0.07, 0.15), (0.10, 0.12, 0.18), 0.53),          # navy knit jumper, jeans
    "uncle": ((0.15, 0.13, 0.09), (0.12, 0.11, 0.10), 0.50),
    "tech": ((0.40, 0.45, 0.52), (0.10, 0.10, 0.11), 0.53),
}


def person(role, name=None, cap=True):
    g, yrs, cloth, hair, hv, hue, sat, val, hgt, wgt = ROLES[role]
    h = rjp.person(name or role.capitalize(), g, yrs, cloth, hair, hv=hv, cval=val, hue=hue, sat=sat, height=hgt, weight=wgt)
    h.role = role
    if role in OUTFITS:
        top, bot, frac = OUTFITS[role]
        split = frac * float(np.max(rj_height(h)))
        h.outfit = (top, bot, split)
        for o in h.parts:
            if o.type == 'MESH' and cloth in o.name:
                _two_tone_local(o, split, top, bot)
    hair_matte(h)
    if role in ("officer", "officer2", "officer3") and cap:
        h.cap = police_cap(h)
    if role == "firefighter":
        h.cap = fire_helmet(h)
    if role == "diver":
        h.cap = diver_hood(h)
    if role == "postman" and cap:
        h.cap = police_cap(h, crown=(0.10, 0.13, 0.2), band=(0.06, 0.07, 0.1))
    return h


def rj_height(h):
    from human import to_bl
    return to_bl(h.hc)[:, 2].max()


def _two_tone_local(o, split, top, bottom):
    """Top/trousers split on the garment's REST height (object coordinates follow the rig), so it holds when the
    person walks, sits or bends. Plain fabric: the stock MakeHuman texture (prints, logos) is dropped; a fine knit
    noise gives the weave. Light collars/shirts keep the mesh's shading."""
    for m in o.data.materials:
        N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
        tc = N.new("ShaderNodeAttribute"); tc.attribute_name = "rest_z"; tc.attribute_type = 'GEOMETRY'
        gt = N.new("ShaderNodeMath"); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = split; L.new(tc.outputs['Fac'], gt.inputs[0])
        mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; L.new(gt.outputs[0], mx.inputs['Factor'])
        mx.inputs[6].default_value = (*bottom, 1); mx.inputs[7].default_value = (*top, 1)
        co = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 900; nz.inputs['Detail'].default_value = 2
        L.new(co.outputs['Object'], nz.inputs['Vector'])
        wv = N.new("ShaderNodeMapRange"); wv.inputs['To Min'].default_value = 0.85; wv.inputs['To Max'].default_value = 1.1
        L.new(nz.outputs['Fac'], wv.inputs['Value'])
        mul = N.new("ShaderNodeMix"); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs['Factor'].default_value = 1.0
        L.new(mx.outputs[2], mul.inputs[6]); L.new(wv.outputs[0], mul.inputs[7])
        out_col = mul.outputs[2]
        img = next((n for n in N if n.type == 'TEX_IMAGE'), None)
        if img is not None and "elegantsuit" in o.name:          # keep the light shirt / collar / tie areas of the suit
            bw = N.new("ShaderNodeRGBToBW"); L.new(img.outputs['Color'], bw.inputs[0])
            mr = N.new("ShaderNodeMapRange"); mr.inputs['From Min'].default_value = 0.45; mr.inputs['From Max'].default_value = 0.65
            L.new(bw.outputs[0], mr.inputs['Value'])
            sh = N.new("ShaderNodeMix"); sh.data_type = 'RGBA'; L.new(mr.outputs[0], sh.inputs['Factor'])
            L.new(out_col, sh.inputs[6]); sh.inputs[7].default_value = (0.62, 0.60, 0.55, 1)
            out_col = sh.outputs[2]
        L.new(out_col, p.inputs['Base Color'])
        bp = N.new("ShaderNodeBump"); bp.inputs['Strength'].default_value = 0.15; L.new(nz.outputs['Fac'], bp.inputs['Height'])
        if not p.inputs['Normal'].is_linked:
            L.new(bp.outputs['Normal'], p.inputs['Normal'])
        p.inputs['Roughness'].default_value = 0.85
        p.inputs['Sheen Weight'].default_value = 0.4
    me = o.data
    co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("co", co)
    at = me.attributes.get("rest_z") or me.attributes.new("rest_z", 'FLOAT', 'POINT')
    at.data.foreach_set("value", co.reshape(-1, 3)[:, 2].copy())


def hair_matte(h):
    """Matte, softer hair: high roughness, no clear-coat shine (MakeHuman hair reads as a plastic helmet otherwise)."""
    for o in h.parts:
        if o.type == 'MESH' and any(k in o.name for k in ("long01", "bob0", "short0", "ponytail", "braid", "afro")):
            for m in o.data.materials:
                p = m.node_tree.nodes.get("Principled BSDF")
                if p:
                    p.inputs['Roughness'].default_value = 0.82
                    p.inputs['Specular IOR Level'].default_value = 0.25
                    p.inputs['Sheen Weight'].default_value = 0.5


def _head_hat(h, objs, name):
    """Parent hat parts to the head bone, placed on the skull top."""
    hat = join(objs, name)
    top = h.bone_tail("head"); hd = h.bone_head("head")
    hat.location = (0, 0, 0)
    bpy.context.view_layer.update()
    mw = Matrix.Translation(hd + (top - hd) * 0.92 + Vector((0, 0.005, 0)))
    hat.matrix_world = mw
    hat.parent = h.arm; hat.parent_type = 'BONE'; hat.parent_bone = "head"
    hat.matrix_world = mw
    h.parts.append(hat)
    return hat


def police_cap(h, crown=(0.06, 0.08, 0.05), band=(0.03, 0.035, 0.03)):
    """Generic peaked service cap (no crest): green crown, dark band, black visor."""
    cm = pbr("CapCrown", crown, 0.7); bm = pbr("CapBand", band, 0.6); vm = pbr("CapVisor", (0.01, 0.01, 0.01), 0.15, 0.0, **{'Coat Weight': 1.0})
    parts = [cyl("CapBand", (0, 0, -0.005), 0.096, 0.05, bm, verts=32)]
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=12, radius=1.0, location=(0, 0.005, 0.03))
    t = bpy.context.active_object; t.scale = (0.125, 0.12, 0.03); t.data.materials.append(cm); bpy.ops.object.transform_apply(scale=True); parts.append(t)
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.09, depth=0.006, location=(0, -0.08, -0.03))
    v = bpy.context.active_object; v.scale = (1.0, 0.55, 1); v.rotation_euler = (math.radians(-20), 0, 0); v.data.materials.append(vm); parts.append(v)
    return _head_hat(h, parts, h.name + "_cap")


def fire_helmet(h):
    m = pbr("FireHelmet", (0.62, 0.62, 0.6), 0.2, 0.6, **{'Coat Weight': 1.0})
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=1.0, location=(0, 0, 0.0))
    t = bpy.context.active_object; t.scale = (0.125, 0.14, 0.12); t.data.materials.append(m); bpy.ops.object.transform_apply(scale=True)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.object.mode_set(mode='OBJECT')
    import bmesh
    bm = bmesh.new(); bm.from_mesh(t.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -0.035], context='VERTS'); bm.to_mesh(t.data); bm.free()
    sol = t.modifiers.new("s", 'SOLIDIFY'); sol.thickness = 0.006
    brim = cyl("Brim", (0, 0.03, -0.03), 0.15, 0.008, m, verts=32); brim.scale = (1.0, 1.12, 1); bpy.ops.object.transform_apply(scale=True)
    return _head_hat(h, [t, brim], h.name + "_helmet")


def diver_hood(h):
    m = pbr("Neoprene", (0.01, 0.01, 0.012), 0.5)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=1.0, location=(0, 0.0, -0.04))
    t = bpy.context.active_object; t.scale = (0.11, 0.12, 0.14); t.data.materials.append(m); bpy.ops.object.transform_apply(scale=True)
    mask = box("Mask", (0, -0.11, -0.07), (0.12, 0.03, 0.07), pbr("MaskGlass", (0.05, 0.06, 0.07), 0.05, 0.0, **{'Coat Weight': 1.0}), bevel=0.02)
    return _head_hat(h, [t, mask], h.name + "_hood")


def hide_person(h, on=True):
    hide(person_objs(h), on)


# ============================================================================ props
def rotary_phone(name="Phone"):
    """A 1970s West German rotary desk phone (tan): sloped body, finger dial, handset on the cradle, coiled cord.
    Returns (root, handset, dial). Local: front of the dial faces -Y, origin on the table."""
    r = bpy.data.objects.new(name, None); bpy.context.collection.objects.link(r)
    pm = mat("phone"); dk = pbr("PhoneDark", (0.06, 0.05, 0.04), 0.3); wh = pbr("DialFace", (0.8, 0.78, 0.72), 0.35)
    # body: a tapered block (front lower than back)
    import bmesh
    me = bpy.data.meshes.new(name + "Body"); bm = bmesh.new()
    pts = [(-0.11, -0.11, 0), (0.11, -0.11, 0), (0.11, 0.1, 0), (-0.11, 0.1, 0),
           (-0.09, -0.08, 0.075), (0.09, -0.08, 0.075), (0.09, 0.08, 0.10), (-0.09, 0.08, 0.10)]
    vs = [bm.verts.new(p) for p in pts]
    for f in ((0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
        bm.faces.new([vs[i] for i in f])
    bm.normal_update(); bm.to_mesh(me); bm.free()
    body = bpy.data.objects.new(name + "Body", me); bpy.context.collection.objects.link(body); body.data.materials.append(pm)
    bv = body.modifiers.new("b", 'BEVEL'); bv.width = 0.02; bv.segments = 4
    sub = body.modifiers.new("s", 'SUBSURF'); sub.levels = 1; sub.render_levels = 2
    body.parent = r
    # dial: on the sloped front face
    slope = math.atan2(0.025, 0.16)
    dial = bpy.data.objects.new(name + "Dial", None); bpy.context.collection.objects.link(dial); dial.parent = r
    dial.location = (0, -0.035, 0.092); dial.rotation_euler = (slope, 0, 0)
    for o in (cyl("DialPlate", (0, 0, 0), 0.052, 0.006, wh, 40), cyl("DialRing", (0, 0, 0.005), 0.05, 0.006, pbr("DialClear", (0.9, 0.9, 0.9), 0.05, 0.0, **{'Transmission Weight': 0.85}), 40),
              cyl("DialHub", (0, 0, 0.009), 0.016, 0.004, dk, 24)):
        o.parent = dial
    for k in range(10):
        a = math.radians(60 + k * 27)
        hole = cyl("Hole", (0.037 * math.cos(a), 0.037 * math.sin(a), 0.009), 0.0075, 0.003, dk, 12); hole.parent = dial
    stop = box("Stop", (0.045, -0.03, 0.01), (0.012, 0.004, 0.004), mat("chrome")); stop.parent = dial
    # cradle forks
    for x in (-0.07, 0.07):
        cr = box("Cradle", (x, 0.045, 0.115), (0.03, 0.03, 0.03), pm, bevel=0.01); cr.parent = r
    # handset: lies across the cradles along X
    hs = bpy.data.objects.new(name + "Handset", None); bpy.context.collection.objects.link(hs); hs.parent = r
    hs.location = (0, 0.045, 0.14)
    hp = [box("Grip", (0, 0, 0.004), (0.15, 0.042, 0.03), pm, bevel=0.012)]
    for sx in (-1, 1):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=1.0, location=(sx * 0.095, 0, -0.012))
        cup = bpy.context.active_object; cup.scale = (0.045, 0.04, 0.03); cup.data.materials.append(pm)
        bpy.ops.object.transform_apply(scale=True); bpy.ops.object.shade_smooth(); hp.append(cup)
        hp.append(cyl("CupFace", (sx * 0.095, 0, -0.038), 0.032, 0.006, pbr("CupGrille", (0.12, 0.13, 0.11), 0.5), 24))
    hj = apply_rot(join(hp, name + "HandsetM")); hj.parent = hs; hj.location = (0, 0, 0)
    bpy.ops.object.shade_smooth()
    # coiled cord from the body's side to the handset's mouth end: 9 hooked points, moved by phone_cord()
    n = 9
    cu = bpy.data.curves.new(name + "Cord", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.0045; cu.bevel_resolution = 3
    sp = cu.splines.new('NURBS'); sp.points.add(n - 1); sp.order_u = 3; sp.use_endpoint_u = True
    cm = pbr("CordCoil", (0.30, 0.33, 0.28), 0.35)
    N = cm.node_tree.nodes; Lk = cm.node_tree.links; tc = N.new("ShaderNodeTexCoord"); wv = N.new("ShaderNodeTexWave")
    wv.wave_type = 'RINGS'; wv.inputs['Scale'].default_value = 120.0; Lk.new(tc.outputs['Generated'], wv.inputs['Vector'])
    bp = N.new("ShaderNodeBump"); bp.inputs['Strength'].default_value = 0.8; Lk.new(wv.outputs['Fac'], bp.inputs['Height']); Lk.new(bp.outputs['Normal'], N["Principled BSDF"].inputs['Normal'])
    co = bpy.data.objects.new(name + "Cord", cu); bpy.context.collection.objects.link(co); co.data.materials.append(cm)
    hooks = []
    for k in range(n):
        sp.points[k].co = (0, 0, 0, 1)
        e = bpy.data.objects.new(name + f"CordH{k}", None); bpy.context.collection.objects.link(e)
        hk = co.modifiers.new(f"h{k}", 'HOOK'); hk.object = e
        hooks.append(e)
    co["hooks"] = [e.name for e in hooks]
    r["cord"] = co.name
    for k, e in enumerate(hooks):               # point k follows empty k: assign through edit mode
        pass
    bpy.context.view_layer.objects.active = co
    for ob in bpy.context.selected_objects:
        ob.select_set(False)
    co.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    for k in range(n):
        for q, pt in enumerate(co.data.splines[0].points):
            pt.select = (q == k)
        bpy.ops.object.hook_assign(modifier=f"h{k}")
        bpy.ops.object.hook_reset(modifier=f"h{k}")
    bpy.ops.object.mode_set(mode='OBJECT')
    return r, hs, dial


def phone_cord(phone_root, handset):
    """Lay the coiled cord from the phone body's left side to the handset's mouth end, sagging between them."""
    co = bpy.data.objects[phone_root["cord"]]; hooks = [bpy.data.objects[n] for n in co["hooks"]]
    bpy.context.view_layer.update()
    a = phone_root.matrix_world @ Vector((-0.11, 0.0, 0.03))
    b = handset.matrix_world @ Vector((-0.11, 0, -0.012))
    n = len(hooks); L_ = (b - a).length
    for k, e in enumerate(hooks):
        t = k / (n - 1)
        sag = 0.25 * math.sin(math.pi * t) * max(0.15, 0.45 - L_ * 0.3) + 0.04 * math.sin(math.pi * t)
        e.location = a.lerp(b, t) + Vector((0, 0, -sag))


def reel_deck(name="Deck", scale=1.0):
    """Police reel-to-reel recorder (generic portable, no brand): grey case, two 18 cm reels that spin, a tape path
    between them over the head block, a lit VU meter whose needle is a child object (animate needle.rotation z).
    Returns dict(root, reels=[L, R], needle, tape)."""
    r = bpy.data.objects.new(name, None); bpy.context.collection.objects.link(r)
    case = pbr("DeckCase", (0.30, 0.31, 0.30), 0.4, 0.4); dark = pbr("DeckDark", (0.025, 0.025, 0.028), 0.35)
    alu = pbr("DeckAlu", (0.6, 0.6, 0.6), 0.3, 1.0)
    parts = [box("Case", (0, 0, 0.055), (0.44, 0.36, 0.11), case, bevel=0.012), box("Plate", (0, 0, 0.1115), (0.42, 0.34, 0.004), dark),
             box("HeadBlock", (0, -0.1, 0.125), (0.09, 0.035, 0.03), alu, bevel=0.004), box("Keys", (0, -0.155, 0.118), (0.22, 0.03, 0.012), alu, bevel=0.003)]
    for k in range(5):
        parts.append(box("Key", (-0.08 + 0.04 * k, -0.155, 0.127), (0.03, 0.025, 0.008), dark if k != 2 else pbr("KeyRed", (0.4, 0.03, 0.02), 0.4), bevel=0.002))
    for x in (0.12, 0.165):
        parts.append(cyl("Knob", (x, -0.155, 0.12), 0.012, 0.02, alu, 16))
    body = join(parts, name + "Body"); body.parent = r
    vu_m = pbr("VUFace", (0.85, 0.72, 0.42), 0.4, 0.0, **{'Emission Color': (1.0, 0.72, 0.38, 1), 'Emission Strength': 0.35})
    vu = box("VU", (-0.14, -0.105, 0.116), (0.07, 0.035, 0.004), vu_m); vu.parent = r
    for k in range(9):                                          # meter scale ticks (no numbers)
        a_ = math.radians(-40 + k * 10)
        tk = box("VUTick", (-0.14 + 0.024 * math.sin(a_), -0.12 + 0.024 * math.cos(a_), 0.1185), (0.0012, 0.005 if k % 2 else 0.008, 0.0008),
                 pbr("VUInk", (0.4, 0.05, 0.03) if k > 6 else (0.02, 0.02, 0.02), 0.5), rot=(0, 0, -a_))
        tk.parent = r
    needle = bpy.data.objects.new(name + "Needle", None); bpy.context.collection.objects.link(needle); needle.parent = r
    needle.location = (-0.14, -0.12, 0.119)
    nd = box("NeedleM", (0, 0.014, 0), (0.0012, 0.028, 0.0012), pbr("NeedleBlk", (0.01, 0.01, 0.01), 0.5)); nd.parent = needle; nd.location = (0, 0.014, 0)
    reels = []
    flange = pbr("ReelFlange", (0.55, 0.57, 0.6), 0.25, 0.6)
    tape = pbr("Tape", (0.10, 0.06, 0.035), 0.35)
    for x, rad in ((-0.105, 0.062), (0.105, 0.045)):
        hub = bpy.data.objects.new(name + "Reel", None); bpy.context.collection.objects.link(hub); hub.parent = r; hub.location = (x, 0.035, 0.12)
        for o in (cyl("Flange", (0, 0, 0), 0.088, 0.003, flange, 48), cyl("Pack", (0, 0, 0.007), rad, 0.009, tape, 48),
                  cyl("FlangeTop", (0, 0, 0.0135), 0.088, 0.002, pbr("ReelClear", (0.6, 0.62, 0.66), 0.1, 0.0, **{'Transmission Weight': 0.7}), 48),
                  cyl("Hub", (0, 0, 0.016), 0.012, 0.006, alu, 16)):
            o.parent = hub
        for k in range(3):                          # three windows in the top flange read as rotation
            w_ = box("Spoke", (0.05 * math.cos(k * 2.094), 0.05 * math.sin(k * 2.094), 0.016), (0.05, 0.012, 0.002), dark, rot=(0, 0, k * 2.094)); w_.parent = hub
        reels.append(hub)
    # tape run: from the left pack down to the head block and up to the right pack
    tp = [(-0.105 + 0.0, 0.035 - 0.062, 0.127), (-0.04, -0.1, 0.127), (0.04, -0.1, 0.127), (0.105, 0.035 - 0.045, 0.127)]
    cu = bpy.data.curves.new(name + "TapeRun", 'CURVE'); cu.dimensions = '3D'; cu.extrude = 0.0045; cu.bevel_depth = 0.0
    sp = cu.splines.new('POLY'); sp.points.add(len(tp) - 1)
    for p, q in zip(sp.points, tp):
        p.co = (*q, 1)
    tr = bpy.data.objects.new(name + "TapeRun", cu); bpy.context.collection.objects.link(tr); tr.data.materials.append(tape); tr.parent = r
    r.scale = (scale, scale, scale)
    return dict(root=r, reels=reels, needle=needle, vu=vu_m)


def spin_reels(deck, sec, rate=1.2, on=True):
    if not on:
        return
    deck["reels"][0].rotation_euler.z = -sec * rate * 2 * math.pi * 0.75
    deck["reels"][1].rotation_euler.z = -sec * rate * 2 * math.pi


def headphones(name="Headphones"):
    """Closed-back 1970s headphones (two cups on a band). Origin at the band top; cups along X."""
    m = pbr("HPMetal", (0.55, 0.55, 0.57), 0.3, 0.9); pad = pbr("HPPad", (0.06, 0.05, 0.045), 0.7)
    parts = []
    for k in range(13):
        a = math.radians(-90 + k * 15)
        parts.append(box("Band", (0.095 * math.sin(a), 0, 0.095 * math.cos(a) - 0.085), (0.026, 0.032, 0.012), m, rot=(0, a, 0)))
    for sx in (-1, 1):
        parts.append(cyl("Cup", (sx * 0.098, 0, -0.105), 0.048, 0.04, pbr("HPCup", (0.16, 0.16, 0.17), 0.35, 0.3), 24, rot=(0, math.radians(90), 0)))
        parts.append(cyl("Pad", (sx * 0.07, 0, -0.105), 0.042, 0.012, pad, 24, rot=(0, math.radians(90), 0)))
    return apply_rot(join(parts, name))


def head_top(h):
    """World position of the top of the skull (from the posed body mesh: highest vertex weighted to the head bone)."""
    idx = h.vertex_region(["head"], 0.5)
    w = _world_verts(h.body) if False else None
    dg = bpy.context.evaluated_depsgraph_get(); oe = h.body.evaluated_get(dg); me = oe.to_mesh()
    co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    M = np.array(oe.matrix_world); co = co @ M[:3, :3].T + M[:3, 3]
    lv = np.empty(len(me.loops), np.int32); me.loops.foreach_get("vertex_index", lv)
    oe.to_mesh_clear()
    idx = np.intersect1d(idx[idx < len(co)], np.unique(lv))          # skip MakeHuman's loose helper vertices
    p = co[idx]; k = int(np.argmax(p[:, 2]))
    return Vector(p[k].tolist())


def wear_headphones(h, hp):
    """Set the headphones on the head for the current pose (call every frame after posing): cups over the ears,
    band over the crown, following the head's tilt."""
    hd = h.bone_head("head"); tl = h.bone_tail("head"); bone_up = (tl - hd).normalized()
    bpy.context.view_layer.update()
    Mb = h.arm.matrix_world @ h.arm.pose.bones["head"].matrix
    top = Mb @ h.hp_off if hasattr(h, "hp_off") else hd + bone_up * 0.2   # the crown, carried by the head bone
    up = (bone_up + Vector((0, 0, 1))).normalized()                 # the band sits level on the crown
    right = forward(h).cross(Vector((0, 0, 1))).normalized()
    right = (right - up * right.dot(up)).normalized(); Y = up.cross(right)
    M = Matrix((right, Y, up)).transposed().to_4x4(); M.translation = top
    hp.matrix_world = M


def put_headphones(h, hp):
    t = head_top(h) + Vector((0, 0, 0.012)); h.head_len = (t - h.bone_head("head")).length
    bpy.context.view_layer.update()
    h.hp_off = (h.arm.matrix_world @ h.arm.pose.bones["head"].matrix).inverted() @ t
    h.parts.append(hp)
    return hp


def _put_headphones_old(h, hp):
    """Place headphones over a person's ears, parented to the head bone."""
    top = head_top(h)
    bpy.context.view_layer.update()
    rot = h.arm.matrix_world.to_3x3().to_4x4()
    hp.matrix_world = Matrix.Translation(top + Vector((0, 0, 0.012))) @ rot
    mw = hp.matrix_world.copy()
    hp.parent = h.arm; hp.parent_type = 'BONE'; hp.parent_bone = "head"; hp.matrix_world = mw
    h.parts.append(hp)
    return hp


def teddy(name="Teddy", fur="fur", size=0.28, sitting=True):
    """A worn plush bear sitting up (ellipsoids with a short fuzzy fabric, button eyes)."""
    m = mat(fur); eye = pbr("ToyEye", (0.01, 0.01, 0.01), 0.1, 0.0, **{'Coat Weight': 1.0})
    s = size / 0.28
    def ell(nm, c, r):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=16, radius=1.0, location=tuple(v * s for v in c))
        o = bpy.context.active_object; o.name = nm; o.scale = tuple(v * s for v in r); o.data.materials.append(m)
        bpy.ops.object.transform_apply(scale=True); bpy.ops.object.shade_smooth()
        return o
    parts = [ell("Body", (0, 0, 0.075), (0.065, 0.055, 0.08)), ell("Head", (0, -0.005, 0.185), (0.055, 0.05, 0.05)),
             ell("Snout", (0, -0.05, 0.175), (0.024, 0.02, 0.018))]
    for sx in (-1, 1):
        parts += [ell("Ear", (sx * 0.04, 0.0, 0.228), (0.018, 0.01, 0.018)), ell("Arm", (sx * 0.065, -0.02, 0.09), (0.02, 0.022, 0.05)),
                  ell("Leg", (sx * 0.035, -0.06, 0.025), (0.025, 0.05, 0.024))]
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=0.0065 * s, location=(sx * 0.018 * s, -0.046 * s, 0.198 * s))
        e = bpy.context.active_object; e.data.materials.append(eye); parts.append(e)
    o = join(parts, name)
    disp = o.modifiers.new("fuzz", 'DISPLACE'); tx = bpy.data.textures.new("Fuzz", 'CLOUDS'); tx.noise_scale = 0.004; disp.texture = tx; disp.strength = 0.002
    return o


def plush_rabbit(name="Rabbit"):
    m = mat("fur2")
    def ell(nm, c, r):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=16, radius=1.0, location=c)
        o = bpy.context.active_object; o.name = nm; o.scale = r; o.data.materials.append(m)
        bpy.ops.object.transform_apply(scale=True); bpy.ops.object.shade_smooth()
        return o
    parts = [ell("Body", (0, 0, 0.07), (0.055, 0.05, 0.07)), ell("Head", (0, -0.01, 0.165), (0.045, 0.042, 0.045))]
    for sx in (-1, 1):
        parts += [ell("Ear", (sx * 0.02, 0.0, 0.24), (0.012, 0.008, 0.055)), ell("Foot", (sx * 0.03, -0.05, 0.015), (0.022, 0.04, 0.016)),
                  ell("Arm", (sx * 0.055, -0.015, 0.08), (0.016, 0.018, 0.045))]
    eye = pbr("ToyEye2", (0.01, 0.01, 0.01), 0.1)
    for sx in (-1, 1):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=0.006, location=(sx * 0.016, -0.046, 0.175))
        e = bpy.context.active_object; e.data.materials.append(eye); parts.append(e)
    return join(parts, name)


def kitchen_radio(name="Radio"):
    """A late-1970s mains radio (no brand): walnut-veneer case, fabric speaker grille, a lit horizontal tuning
    scale with plain ticks (no station names), two knobs. Front faces -Y, origin on the shelf.
    Returns (root, dial_material)."""
    case = mat("oak"); grille = fabric("RadioGrille", (0.16, 0.13, 0.09), 0.9, 0.3, 500)
    scale_m = bpy.data.materials.new("RadioScale"); scale_m.use_nodes = True
    N = scale_m.node_tree.nodes; L = scale_m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs['Object'], sep.inputs[0])
    mul = N.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = 180; L.new(sep.outputs['X'], mul.inputs[0])
    fr = N.new("ShaderNodeMath"); fr.operation = 'FRACT'; L.new(mul.outputs[0], fr.inputs[0])
    tick = N.new("ShaderNodeMath"); tick.operation = 'LESS_THAN'; tick.inputs[1].default_value = 0.12; L.new(fr.outputs[0], tick.inputs[0])
    low = N.new("ShaderNodeMath"); low.operation = 'LESS_THAN'; low.inputs[1].default_value = -0.004; L.new(sep.outputs['Z'], low.inputs[0])
    tk = N.new("ShaderNodeMath"); tk.operation = 'MULTIPLY'; L.new(tick.outputs[0], tk.inputs[0]); L.new(low.outputs[0], tk.inputs[1])
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; L.new(tk.outputs[0], mx.inputs['Factor'])
    mx.inputs[6].default_value = (0.9, 0.78, 0.5, 1); mx.inputs[7].default_value = (0.05, 0.04, 0.03, 1)
    L.new(mx.outputs[2], p.inputs['Base Color']); L.new(mx.outputs[2], p.inputs['Emission Color'])
    p.inputs['Emission Strength'].default_value = 1.5
    parts = [box("RCase", (0, 0, 0.085), (0.36, 0.13, 0.17), case, bevel=0.012),
             box("RGrille", (-0.06, -0.0655, 0.095), (0.2, 0.002, 0.12), grille),
             box("RKnobPanel", (0.115, -0.0655, 0.085), (0.1, 0.002, 0.14), pbr("RPanel", (0.55, 0.52, 0.46), 0.3, 0.8))]
    for z in (0.12, 0.05):
        parts.append(cyl("RKnob", (0.115, -0.075, z), 0.017, 0.018, pbr("RKnobM", (0.05, 0.04, 0.035), 0.3), 24, rot=(math.radians(90), 0, 0)))
    body = join(parts, name + "Body")
    sc = box("RScale", (-0.06, -0.067, 0.162), (0.2, 0.002, 0.018), scale_m)
    ptr = box("RPointer", (-0.03, -0.069, 0.162), (0.002, 0.002, 0.018), pbr("RPointerM", (0.5, 0.05, 0.03), 0.3, 0.0, **{'Emission Color': (1, 0.2, 0.1, 1), 'Emission Strength': 2.0}))
    r = bpy.data.objects.new(name, None); bpy.context.collection.objects.link(r)
    for o in (body, sc, ptr):
        o.parent = r
    return r, scale_m


def portable_radio(name="PortRadio"):
    """A small 1970s portable transistor radio (black leatherette, chrome grille, carry strap, no brand).
    Front faces -Y. Returns (root, dial_material)."""
    case = pbr("Leatherette", (0.025, 0.022, 0.02), 0.6); chrome = mat("chrome")
    dial = pbr("PRDial", (0.85, 0.75, 0.5), 0.3, 0.0, **{'Emission Color': (1.0, 0.75, 0.4, 1), 'Emission Strength': 0.0})
    parts = [box("PRCase", (0, 0, 0.075), (0.24, 0.07, 0.15), case, bevel=0.012),
             box("PRGrille", (-0.04, -0.0355, 0.08), (0.13, 0.002, 0.1), pbr("PRGrilleM", (0.55, 0.55, 0.56), 0.3, 1.0)),
             box("PRTrim", (0, -0.036, 0.145), (0.22, 0.002, 0.008), chrome)]
    for z in (0.11, 0.05):
        parts.append(cyl("PRKnob", (0.085, -0.04, z), 0.014, 0.012, chrome, 20, rot=(math.radians(90), 0, 0)))
    for k in range(9):                                         # strap
        a = math.radians(k * 22.5)
        parts.append(box("Strap", (0.09 * math.cos(a), 0, 0.15 + 0.05 * math.sin(a)), (0.012, 0.02, 0.006), case, rot=(0, -a + math.pi / 2, 0)))
    body = join(parts, name + "Body")
    d = box("PRDialM", (0.085, -0.036, 0.135), (0.05, 0.002, 0.012), dial)
    r = bpy.data.objects.new(name, None); bpy.context.collection.objects.link(r)
    body.parent = r; d.parent = r
    return r, dial


def wall_clock(name="WallClock"):
    """A round kitchen/hall wall clock with a swinging pendulum box below (Black Forest style, no text).
    Face toward -Y. Returns (root, hands dict(h, m), pendulum)."""
    r = bpy.data.objects.new(name, None); bpy.context.collection.objects.link(r)
    w = mat("darkwood"); face_m = pbr("ClockFace", (0.82, 0.78, 0.68), 0.4); blk = pbr("ClockHand", (0.02, 0.02, 0.02), 0.4)
    parts = [box("Case", (0, 0.04, -0.12), (0.26, 0.08, 0.62), w, bevel=0.01), cyl("Face", (0, -0.002, 0.07), 0.1, 0.01, face_m, 48, rot=(math.radians(90), 0, 0)),
             box("Window", (0, -0.002, -0.24), (0.16, 0.006, 0.3), mat("glass"))]
    for k in range(12):
        a = k * math.pi / 6
        parts.append(box("Tick", (0.085 * math.sin(a), -0.009, 0.07 + 0.085 * math.cos(a)), (0.006, 0.002, 0.016 if k % 3 == 0 else 0.009), blk, rot=(0, -a, 0)))
    body = join(parts, name + "Body"); body.parent = r
    hands = {}
    for nm, L_, wd in (("h", 0.05, 0.007), ("m", 0.075, 0.005)):
        e = bpy.data.objects.new(name + nm, None); bpy.context.collection.objects.link(e); e.parent = r; e.location = (0, -0.012, 0.07)
        hm = box("Hand" + nm, (0, 0, L_ / 2), (wd, 0.002, L_), blk); hm.parent = e; hm.location = (0, 0, L_ / 2)
        hands[nm] = e
    pend = bpy.data.objects.new(name + "Pend", None); bpy.context.collection.objects.link(pend); pend.parent = r; pend.location = (0, 0.02, -0.05)
    rod = box("Rod", (0, 0, -0.14), (0.006, 0.004, 0.28), mat("chrome")); rod.parent = pend; rod.location = (0, 0, -0.14)
    bob = cyl("Bob", (0, 0, -0.28), 0.03, 0.006, pbr("Brass", (0.75, 0.55, 0.25), 0.25, 1.0), 32, rot=(math.radians(90), 0, 0)); bob.parent = pend; bob.location = (0, 0, -0.28)
    return r, hands, pend


def upright_piano(name="Piano"):
    """An upright piano (dark polished wood) with a keyboard, a music desk with an open score, pedals and a bench.
    Keys face -Y (the player sits at y < 0). Origin on the floor at the middle of the front of the case.
    Returns dict(root, bench, keys_z, score, score_pages)."""
    pw = mat("piano"); ivory = mat("ivory"); ebony = pbr("Ebony", (0.01, 0.01, 0.01), 0.25, 0.0, **{'Coat Weight': 0.6})
    W = 1.48; D = 0.6; H = 1.25
    parts = [box("Case", (0, D / 2, H / 2), (W, D, H), pw, bevel=0.012),
             box("Top", (0, D / 2 - 0.01, H + 0.012), (W + 0.04, D + 0.03, 0.025), pw, bevel=0.006),
             box("KeyBed", (0, -0.13, 0.7), (W - 0.06, 0.32, 0.06), pw, bevel=0.006),
             box("CheekL", (-W / 2 + 0.04, -0.13, 0.76), (0.08, 0.3, 0.12), pw, bevel=0.01),
             box("CheekR", (W / 2 - 0.04, -0.13, 0.76), (0.08, 0.3, 0.12), pw, bevel=0.01),
             box("Fall", (0, 0.04, 0.83), (W - 0.18, 0.06, 0.08), pw, bevel=0.01),
             box("Desk", (0, 0.02, 0.97), (W - 0.2, 0.05, 0.22), pw, bevel=0.008),
             box("Toe", (0, -0.12, 0.05), (W, 0.06, 0.1), pw, bevel=0.006)]
    for sx in (-1, 1):
        parts.append(box("Leg", (sx * (W / 2 - 0.05), -0.22, 0.34), (0.06, 0.06, 0.68), pw, bevel=0.01))
    for k in range(3):
        parts.append(box("Pedal", (-0.08 + 0.08 * k, -0.18, 0.06), (0.03, 0.12, 0.012), mat("chrome")))
    case = join(parts, name + "Case")
    # keys: 52 white, black keys in the 2-3 pattern
    kparts = []; n = 52; kw = (W - 0.18) / n
    for k in range(n):
        kparts.append(box("WK", (-(W - 0.18) / 2 + kw * (k + 0.5), -0.15, 0.745), (kw * 0.94, 0.15, 0.022), ivory))
    bk = []
    for k in range(n - 1):
        if k % 7 in (0, 1, 3, 4, 5):
            bk.append(box("BK", (-(W - 0.18) / 2 + kw * (k + 1), -0.115, 0.765), (kw * 0.55, 0.095, 0.02), ebony))
    keys = join(kparts + bk, name + "Keys")
    # open score on the desk (blank staves only, nothing readable)
    sm = bpy.data.materials.new("Score"); sm.use_nodes = True
    N = sm.node_tree.nodes; L = sm.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs['Object'], sep.inputs[0])
    mz = N.new("ShaderNodeMath"); mz.operation = 'MULTIPLY'; mz.inputs[1].default_value = 260; L.new(sep.outputs['Z'], mz.inputs[0])
    fz = N.new("ShaderNodeMath"); fz.operation = 'FRACT'; L.new(mz.outputs[0], fz.inputs[0])
    ln = N.new("ShaderNodeMath"); ln.operation = 'LESS_THAN'; ln.inputs[1].default_value = 0.14; L.new(fz.outputs[0], ln.inputs[0])
    grp = N.new("ShaderNodeMath"); grp.operation = 'MULTIPLY'; grp.inputs[1].default_value = 26; L.new(sep.outputs['Z'], grp.inputs[0])
    gf = N.new("ShaderNodeMath"); gf.operation = 'FRACT'; L.new(grp.outputs[0], gf.inputs[0])
    gl = N.new("ShaderNodeMath"); gl.operation = 'LESS_THAN'; gl.inputs[1].default_value = 0.5; L.new(gf.outputs[0], gl.inputs[0])
    nt = N.new("ShaderNodeTexNoise"); nt.inputs['Scale'].default_value = 120; L.new(tc.outputs['Object'], nt.inputs['Vector'])
    dots = N.new("ShaderNodeMath"); dots.operation = 'GREATER_THAN'; dots.inputs[1].default_value = 0.68; L.new(nt.outputs['Fac'], dots.inputs[0])
    lines = N.new("ShaderNodeMath"); lines.operation = 'MAXIMUM'; L.new(ln.outputs[0], lines.inputs[0]); L.new(dots.outputs[0], lines.inputs[1])
    ink = N.new("ShaderNodeMath"); ink.operation = 'MULTIPLY'; L.new(lines.outputs[0], ink.inputs[0]); L.new(gl.outputs[0], ink.inputs[1])
    mxc = N.new("ShaderNodeMix"); mxc.data_type = 'RGBA'; L.new(ink.outputs[0], mxc.inputs['Factor'])
    mxc.inputs[6].default_value = (0.78, 0.74, 0.64, 1); mxc.inputs[7].default_value = (0.08, 0.07, 0.06, 1)
    L.new(mxc.outputs[2], p.inputs['Base Color']); p.inputs['Roughness'].default_value = 0.8
    score = bpy.data.objects.new(name + "Score", None); bpy.context.collection.objects.link(score)
    pages = []
    for k, x in enumerate((-0.11, 0.11)):
        pg = box("Page", (x, 0, 0), (0.21, 0.002, 0.28), sm); pg.location = (x, 0, 0); pg.parent = score
        pages.append(pg)
    # a turning page: hinged at the spine (x = 0), parented to its own empty
    turn = bpy.data.objects.new(name + "TurnPage", None); bpy.context.collection.objects.link(turn); turn.parent = score
    tp = box("PageT", (0.105, -0.002, 0), (0.21, 0.002, 0.28), sm); tp.parent = turn; tp.location = (0.105, -0.002, 0)
    score.location = (0, -0.005, 1.03); score.rotation_euler = (math.radians(-12), 0, 0)
    # bench (two players fit side by side)
    bparts = [box("BenchTop", (0, 0, 0.47), (0.95, 0.36, 0.05), pw, bevel=0.01), box("BenchSeat", (0, 0, 0.5), (0.9, 0.32, 0.03), fabric("BenchCushion", (0.10, 0.04, 0.03), 0.9, 0.4))]
    for sx in (-1, 1):
        for sy in (-1, 1):
            bparts.append(box("BenchLeg", (sx * 0.42, sy * 0.14, 0.225), (0.045, 0.045, 0.45), pw, bevel=0.006))
    bench = join(bparts, name + "Bench")
    root = bpy.data.objects.new(name, None); bpy.context.collection.objects.link(root)
    for o in (case, keys, score):
        o.parent = root
    bench.parent = root; bench.location = (0, -0.75, 0)
    return dict(root=root, bench=bench, keys=keys, score=score, turn=turn, W=W)


def torch(name="Torch", on=True, energy=40.0, cone=22.0, color=(1.0, 0.86, 0.62)):
    """A 1970s hand torch: black body, chrome head; a spot light (local -Y beam) and a lit lens.
    Origin at the grip; the beam points along local -Y."""
    r = bpy.data.objects.new(name, None); bpy.context.collection.objects.link(r)
    body = cyl("TBody", (0, 0.06, 0), 0.016, 0.16, pbr("TorchBody", (0.03, 0.03, 0.03), 0.4), 16, rot=(math.radians(90), 0, 0))
    head = cyl("THead", (0, -0.035, 0), 0.026, 0.05, mat("chrome"), 20, rot=(math.radians(90), 0, 0))
    lens = cyl("TLens", (0, -0.061, 0), 0.023, 0.003, emissive("TorchLens", color, 30.0 if on else 0.0), 20, rot=(math.radians(90), 0, 0))
    for o in (body, head, lens):
        o.parent = r
    if on:
        ld = bpy.data.lights.new(name + "L", 'SPOT'); ld.energy = energy; ld.spot_size = math.radians(cone); ld.spot_blend = 0.45
        ld.color = color; ld.shadow_soft_size = 0.01
        lo = bpy.data.objects.new(name + "L", ld); bpy.context.collection.objects.link(lo); lo.parent = r
        lo.location = (0, -0.065, 0); lo.rotation_euler = (math.radians(90), 0, 0)
        r["light"] = lo.name
    return r


def bicycle(name="Bike", frame_m=None, lying=False):
    """A 1970s girl's bicycle (step-through frame, red), 24-inch wheels with spokes, mudguards, carrier, saddle and
    a basket-less handlebar. Forward is local +X, origin on the ground between the wheels.
    Returns dict(root, wheels=[front, rear], crank)."""
    fm = frame_m or mat("bike_red"); ch = mat("chrome"); ty = mat("tyre"); blk = pbr("BikeBlack", (0.02, 0.02, 0.02), 0.5)
    R = 0.31; wb = 1.02
    root = bpy.data.objects.new(name, None); bpy.context.collection.objects.link(root)
    def tube(nm, a, b, r=0.014, m=fm):
        a = Vector(a); b = Vector(b); d = b - a
        o = cyl(nm, (a + b) / 2, r, d.length, m, 12)
        o.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
        return o
    fx, rx = wb / 2, -wb / 2
    bb = Vector((0.02, 0, 0.27)); seat_t = Vector((-0.17, 0, 0.82)); head_b = Vector((0.36, 0, 0.62)); head_t = Vector((0.33, 0, 0.78))
    parts = [tube("SeatTube", bb, seat_t), tube("DownTube", head_b, bb, 0.016), tube("LowTube", head_b + Vector((-0.02, 0, 0.08)), bb + Vector((0.0, 0, 0.12)), 0.013),
             tube("HeadTube", head_b, head_t, 0.018)]
    for sy in (-1, 1):
        parts += [tube("Chain", bb + Vector((0, sy * 0.05, 0)), Vector((rx, sy * 0.055, R)), 0.008),
                  tube("SeatStay", seat_t + Vector((0, sy * 0.02, -0.06)), Vector((rx, sy * 0.055, R)), 0.008),
                  tube("Fork", head_b + Vector((0, sy * 0.03, 0.02)), Vector((fx, sy * 0.05, R)), 0.01)]
        parts.append(tube("CarrierStay", Vector((-0.2, sy * 0.08, 0.7)), Vector((rx, sy * 0.06, R)), 0.006, ch))
    parts.append(box("Carrier", (-0.37, 0, 0.71), (0.36, 0.15, 0.012), ch))
    parts.append(tube("SeatPost", seat_t, seat_t + Vector((-0.03, 0, 0.1)), 0.011, ch))
    sad = box("Saddle", (-0.2, 0, 0.94), (0.24, 0.14, 0.05), blk, bevel=0.02); parts.append(sad)
    stem = tube("Stem", head_t, head_t + Vector((-0.02, 0, 0.18)), 0.011, ch); parts.append(stem)
    hb = head_t + Vector((-0.02, 0, 0.18))
    for sy in (-1, 1):
        parts.append(tube("Bar", hb, hb + Vector((-0.12, sy * 0.27, 0.05)), 0.011, ch))
        parts.append(tube("Grip", hb + Vector((-0.12, sy * 0.27, 0.05)), hb + Vector((-0.2, sy * 0.29, 0.06)), 0.016, blk))
    for x, ln in ((fx, 0.5), (rx, 0.6)):                       # mudguards: arcs over the wheels
        for k in range(10):
            a0 = math.radians(20 + k * 14); a1 = math.radians(20 + (k + 1) * 14)
            sgn = 1 if x > 0 else -1
            p0 = Vector((x + sgn * (R + 0.03) * math.cos(a0) * (1 if k < 9 else 1), 0, R + (R + 0.03) * math.sin(a0)))
            p1 = Vector((x + sgn * (R + 0.03) * math.cos(a1), 0, R + (R + 0.03) * math.sin(a1)))
            parts.append(box("Guard", (p0 + p1) / 2, ((p1 - p0).length + 0.004, 0.05, 0.004), ch, rot=(0, -math.atan2(p1.z - p0.z, p1.x - p0.x), 0)))
    lamp = cyl("Lamp", (fx + 0.12, 0, 0.62), 0.04, 0.06, ch, 20, rot=(0, math.radians(90), 0)); parts.append(lamp)
    parts.append(cyl("Chainring", (bb.x, 0.06, bb.z), 0.09, 0.006, ch, 32, rot=(math.radians(90), 0, 0)))
    frame = join(parts, name + "Frame"); frame.parent = root
    wheels = []
    for x in (fx, rx):
        w = bpy.data.objects.new(name + "Wheel", None); bpy.context.collection.objects.link(w); w.parent = root; w.location = (x, 0, R)
        bpy.ops.mesh.primitive_torus_add(major_radius=R - 0.018, minor_radius=0.019, major_segments=48, minor_segments=10, location=(0, 0, 0), rotation=(math.radians(90), 0, 0))
        t = bpy.context.active_object; t.data.materials.append(ty); bpy.ops.object.shade_smooth()
        bpy.ops.mesh.primitive_torus_add(major_radius=R - 0.04, minor_radius=0.008, major_segments=48, minor_segments=6, location=(0, 0, 0), rotation=(math.radians(90), 0, 0))
        rim = bpy.context.active_object; rim.data.materials.append(ch)
        sp = []
        for k in range(28):
            a = k * 2 * math.pi / 28
            sp.append(box("Spoke", (0.135 * math.cos(a), 0.012 * (1 if k % 2 else -1), 0.135 * math.sin(a)), (0.27, 0.0018, 0.0018), ch, rot=(0, -a, 0)))
        sp.append(cyl("Hub", (0, 0, 0), 0.02, 0.09, ch, 16, rot=(math.radians(90), 0, 0)))
        wj = join([t, rim] + sp, name + "WheelM"); wj.parent = w; wj.location = (0, 0, 0)
        w["radius"] = R
        wheels.append(w)
    crank = bpy.data.objects.new(name + "Crank", None); bpy.context.collection.objects.link(crank); crank.parent = root; crank.location = bb
    for sy in (-1, 1):
        arm = box("CrankArm", (0, sy * 0.075, -0.08 * sy), (0.02, 0.012, 0.17), ch); arm.parent = crank; arm.location = (0, sy * 0.075, -0.08 * sy)
        ped = box("Pedal", (0, sy * 0.11, -0.165 * sy), (0.09, 0.06, 0.02), blk); ped.parent = crank; ped.location = (0, sy * 0.11, -0.165 * sy)
    root["R"] = R
    return dict(root=root, wheels=wheels, crank=crank, frame=frame, saddle=Vector((-0.2, 0, 0.97)), bars=hb + Vector((-0.2, 0, 0.06)), bb=bb)


def roll_bike(bk, dist):
    for w in bk["wheels"]:
        w.rotation_euler.y = dist / w["radius"]
    bk["crank"].rotation_euler.y = dist / w["radius"] * 0.45


def ride_pose(h, bk, dist):
    """Rider on the bike (bike root already placed): seat on the saddle, hands on the grips, feet on the pedals."""
    from human import ik2
    upright(h); reset_pose(h)
    rw = bk["root"].matrix_world
    heading = bk["root"].rotation_euler.z
    th = heading + math.pi / 2                 # person faces +X of the bike
    h.arm.rotation_euler = (0, 0, th)
    saddle = rw @ bk["saddle"]
    hip = h.bone_head("upperleg01.L").lerp(h.bone_head("upperleg01.R"), 0.5)
    h.arm.location = Vector(h.arm.location) + (saddle - hip) + Vector((0, 0, 0.06))
    bpy.context.view_layer.update()
    fwdv = Vector((math.cos(heading), math.sin(heading), 0)); left = Vector((-math.sin(heading), math.cos(heading), 0))
    side_r = -left
    for b, a in (("spine05", 4), ("spine04", 5), ("spine03", 5), ("spine02", 4)):
        h.rot(b, side_r, -24 * a / 18)                 # lean forward over the bars
    ang = dist / bk["root"]["R"] * 0.45
    for sd, sg in SIDE.items():
        side_v = left * (sg * 1.0)
        ph_ = ang + (0 if sd == "L" else math.pi)
        ped = rw @ (bk["bb"] + Vector((0.165 * math.sin(ph_), sg * 0.11, -0.165 * math.cos(ph_)))) + Vector((0, 0, 0.06))
        ik2(h, f"upperleg01.{sd}", f"lowerleg01.{sd}", ped, fwdv + Vector((0, 0, 0.6)))
        h.aim(f"foot.{sd}", fwdv + Vector((0, 0, -0.25)))
        grip = rw @ (bk["bars"] + Vector((0, sg * 0.28, 0)))
        reach(h, sd, grip, side_v * 0.5 + Vector((0, 0, -1.0)) - fwdv * 0.4, fwdv)
    fingers_curl(h, 45)
    h.rot("neck01", side_r, 8); h.rot("head", side_r, 10)          # look ahead along the path


def ph_instances(aid, placements, pick=None):
    """Import a Poly Haven model once and place linked copies: placements = [(loc, rot_z, scale)]."""
    root, ms = ph.model(aid)
    if pick:
        keep = [o for o in ms if pick in o.name]
        for o in ms:
            if o not in keep:
                me = o.data; bpy.data.objects.remove(o, do_unlink=True); bpy.data.meshes.remove(me)
        ms = keep
    out = []
    for (loc, rz, sc) in placements:
        r = bpy.data.objects.new(aid + "_inst", None); bpy.context.collection.objects.link(r)
        for o in ms:
            n = o.copy(); bpy.context.collection.objects.link(n); n.parent = r
            n.matrix_parent_inverse = o.matrix_parent_inverse.copy()
        r.location = loc; r.rotation_euler = (0, 0, rz); r.scale = (sc, sc, sc)
        out.append(r)
    root.location = (0, 0, -1000); root.hide_render = True
    for o in ms:
        o.hide_render = True
    return out


def birch_bark():
    bark = bpy.data.materials.get("BirchBark")
    if bark is None:
        bark = bpy.data.materials.new("BirchBark"); bark.use_nodes = True
        N = bark.node_tree.nodes; L = bark.node_tree.links; p = N["Principled BSDF"]
        tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.inputs['Scale'].default_value = (3.0, 3.0, 28.0)
        L.new(tc.outputs['Object'], mp.inputs['Vector'])
        nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 2.5; nz.inputs['Detail'].default_value = 3; L.new(mp.outputs[0], nz.inputs['Vector'])
        ramp = N.new("ShaderNodeValToRGB"); L.new(nz.outputs['Fac'], ramp.inputs['Fac'])
        ramp.color_ramp.elements[0].position = 0.62; ramp.color_ramp.elements[0].color = (0.62, 0.61, 0.56, 1)
        ramp.color_ramp.elements[1].position = 0.7; ramp.color_ramp.elements[1].color = (0.04, 0.04, 0.035, 1)
        L.new(ramp.outputs['Color'], p.inputs['Base Color']); p.inputs['Roughness'].default_value = 0.6
    return bark


def birch_template():
    """One birch (scanned small tree, bark swapped for birch bark, leaves lighter); returns its meshes for instancing."""
    r, ms = ph.model("tree_small_02")
    bark = birch_bark()
    for o in ms:
        for s in getattr(o, "material_slots", []):
            if s.material is None:
                continue
            nm = s.material.name.lower()
            if "trunk" in nm or "branch" in nm or "bark" in nm:
                s.material = bark
            elif "lea" in nm:
                m = s.material
                if not m.get("birch"):
                    retint(m, (1.05, 1.1, 0.7), sat=0.8); m["birch"] = 1
    return r, ms


def sway(objs, sec, amp=0.012, rate=0.6, seed=0):
    """Slow wind sway: small rotation on tree/plant roots (their base stays put)."""
    for k, o in enumerate(objs):
        ph_ = (k * 1.7 + seed) % 6.28
        o.rotation_euler.x = amp * math.sin(sec * rate * 2 * math.pi + ph_)
        o.rotation_euler.y = amp * 0.7 * math.sin(sec * rate * 1.3 * 2 * math.pi + ph_ * 1.3)


# ============================================================================ sitting on real furniture
def leg_reach(h, side, ankle_target, pole):
    """Two-segment IK for a leg (upperleg01+02 / lowerleg01+02): ankle at the target, knee toward `pole`."""
    b = h.arm.data.bones
    a = b[f"upperleg01.{side}"].length + b[f"upperleg02.{side}"].length
    c = b[f"lowerleg01.{side}"].length + b[f"lowerleg02.{side}"].length
    S = h.bone_head(f"upperleg01.{side}"); T = Vector(ankle_target)
    dv = T - S; d = min(max(dv.length, abs(a - c) + 1e-3), (a + c) * 0.999); u = dv.normalized()
    cosA = (a * a + d * d - c * c) / (2 * a * d); sinA = math.sqrt(max(0.0, 1 - cosA * cosA))
    p = Vector(pole); p = (p - u * p.dot(u)).normalized()
    E = S + u * (a * cosA) + p * (a * sinA)
    h.aim(f"upperleg01.{side}", E - S); h.aim(f"upperleg02.{side}", E - S)
    T2 = S + u * d
    h.aim(f"lowerleg01.{side}", T2 - E); h.aim(f"lowerleg02.{side}", T2 - E)


def sit_on(h, seat_pt, face_z, seat_z, lean=10, feet=0.42, knees_apart=0.11):
    """Sit squarely on a chair/bench: pelvis on the seat (seat_pt xy, seat_z), thighs level, shins down to the floor
    `feet` metres in front of the hips. Face_z as everywhere (0 faces -Y)."""
    upright(h); reset_pose(h)
    h.arm.rotation_euler = (0, 0, face_z); h.arm.location = (0, 0, 0)
    bpy.context.view_layer.update()
    hip = (h.bone_head("upperleg01.L") + h.bone_head("upperleg01.R")) * 0.5
    off = Vector((seat_pt[0], seat_pt[1], seat_z + 0.085)) - hip
    h.arm.location = off
    bpy.context.view_layer.update()
    fwd = forward(h); side = fwd.cross(Vector((0, 0, 1))).normalized()          # character's right
    for sd, sg in SIDE.items():
        hp = h.bone_head(f"upperleg01.{sd}")
        lat = -side * sg * knees_apart * 0.5                                    # L is the character's left (-side)
        ankle = Vector((hp.x, hp.y, 0.0)) + fwd * feet + lat + Vector((0, 0, 0.085))
        leg_reach(h, sd, ankle, fwd + Vector((0, 0, 0.4)))
        h.aim(f"foot.{sd}", fwd + Vector((0, 0, -0.35)))
    for b, a in (("spine05", 4), ("spine04", 5), ("spine03", 5), ("spine02", 4), ("spine01", 3)):
        h.rot(b, side, -lean * a / 21)
    for sd, sg in SIDE.items():                       # arms relaxed, hands on the thighs
        knee = h.bone_tail(f"upperleg02.{sd}")
        reach(h, sd, knee.lerp(h.bone_head(f"upperleg01.{sd}"), 0.45) + Vector((0, 0, 0.1)), -side * sg * 0.5 + Vector((0, 0, -1)) - fwd * 0.3,
              fwd + Vector((0, 0, -0.9)))
    fingers_curl(h, 25)


# ============================================================================ search dog (German shepherd)
def _meta_mesh(name, elems, m, res=0.025):
    """Organic shape from metaball ellipsoids, converted to a mesh. elems: [(co, radius, (sx, sy, sz))]."""
    mb = bpy.data.metaballs.new(name); mb.resolution = res; mb.render_resolution = res; mb.threshold = 0.6
    for co, r, sc in elems:
        e = mb.elements.new(); e.type = 'ELLIPSOID'; e.co = co; e.radius = r
        e.size_x, e.size_y, e.size_z = sc
    o = bpy.data.objects.new(name, mb); bpy.context.collection.objects.link(o)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
    bpy.data.objects.remove(o, do_unlink=True)
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob)
    me.materials.append(m)
    for p in me.polygons:
        p.use_smooth = True
    return ob


def dog_fur():
    m = bpy.data.materials.get("DogFur")
    if m:
        return m
    m = bpy.data.materials.new("DogFur"); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs['Object'], sep.inputs[0])
    # black saddle on the back, tan below and on the legs
    mr = N.new("ShaderNodeMapRange"); mr.inputs['From Min'].default_value = 0.5; mr.inputs['From Max'].default_value = 0.62
    L.new(sep.outputs['Z'], mr.inputs['Value'])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 9; L.new(tc.outputs['Object'], nz.inputs['Vector'])
    add = N.new("ShaderNodeMath"); add.operation = 'MULTIPLY_ADD'; add.inputs[1].default_value = 0.3; L.new(nz.outputs['Fac'], add.inputs[0]); L.new(mr.outputs[0], add.inputs[2])
    ramp = N.new("ShaderNodeValToRGB"); L.new(add.outputs[0], ramp.inputs['Fac'])
    ramp.color_ramp.elements[0].position = 0.45; ramp.color_ramp.elements[0].color = (0.28, 0.15, 0.06, 1)
    ramp.color_ramp.elements[1].position = 0.8; ramp.color_ramp.elements[1].color = (0.018, 0.014, 0.012, 1)
    L.new(ramp.outputs['Color'], p.inputs['Base Color']); p.inputs['Roughness'].default_value = 0.75
    p.inputs['Sheen Weight'].default_value = 0.8; p.inputs['Sheen Roughness'].default_value = 0.4
    fz = N.new("ShaderNodeTexNoise"); fz.inputs['Scale'].default_value = 900; L.new(tc.outputs['Object'], fz.inputs['Vector'])
    mp = N.new("ShaderNodeMapping"); mp.inputs['Scale'].default_value = (1, 1, 14); L.new(tc.outputs['Object'], mp.inputs['Vector'])
    fz2 = N.new("ShaderNodeTexNoise"); fz2.inputs['Scale'].default_value = 120; L.new(mp.outputs[0], fz2.inputs['Vector'])
    b = N.new("ShaderNodeBump"); b.inputs['Strength'].default_value = 0.35; L.new(fz2.outputs['Fac'], b.inputs['Height']); L.new(b.outputs['Normal'], p.inputs['Normal'])
    return m


def dog(name="Dog"):
    """A German shepherd, about 0.62 m at the shoulder. Forward is local +X, origin on the ground under the chest.
    Returns dict(root, body, head, tail, legs=[(hip, knee)] x4 (FL, FR, HL, HR))."""
    fur = dog_fur(); dark = pbr("DogNose", (0.01, 0.01, 0.01), 0.3, 0.0, **{'Coat Weight': 0.7})
    root = bpy.data.objects.new(name, None); bpy.context.collection.objects.link(root)
    body = _meta_mesh(name + "Body", [((0.22, 0, 0.6), 0.2, (1.25, 0.7, 0.95)), ((-0.05, 0, 0.6), 0.2, (1.3, 0.72, 0.9)),
                                      ((-0.3, 0, 0.58), 0.19, (1.0, 0.75, 0.9)), ((0.36, 0, 0.74), 0.12, (1.1, 0.75, 1.2)),
                                      ((0.12, 0, 0.5), 0.15, (1.6, 0.6, 0.6))], fur)
    body.parent = root
    head = bpy.data.objects.new(name + "HeadPivot", None); bpy.context.collection.objects.link(head); head.parent = root; head.location = (0.44, 0, 0.82)
    hm = _meta_mesh(name + "Head", [((0.06, 0, 0.04), 0.1, (1.0, 0.85, 0.85)), ((0.17, 0, 0.0), 0.06, (1.4, 0.65, 0.6)),
                                    ((0.23, 0, -0.01), 0.04, (1.2, 0.6, 0.5))], fur)
    hm.parent = head
    for sy in (-1, 1):
        bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.04, radius2=0.004, depth=0.11, location=(0.02, sy * 0.045, 0.14), rotation=(sy * -0.25, -0.15, 0))
        ear = bpy.context.active_object; ear.data.materials.append(fur); ear.parent = head
    nose = cyl("Nose", (0.27, 0, -0.005), 0.016, 0.02, dark, 12, rot=(0, math.radians(90), 0)); nose.parent = head
    tail = bpy.data.objects.new(name + "TailPivot", None); bpy.context.collection.objects.link(tail); tail.parent = root; tail.location = (-0.47, 0, 0.62)
    tm = _meta_mesh(name + "Tail", [((-0.08, 0, -0.05), 0.06, (1.0, 0.6, 0.6)), ((-0.18, 0, -0.17), 0.055, (0.8, 0.55, 0.9)), ((-0.24, 0, -0.3), 0.05, (0.7, 0.5, 0.9))], fur)
    tm.parent = tail
    legs = []
    for (x, y, front) in ((0.3, 0.1, True), (0.3, -0.1, True), (-0.32, 0.1, False), (-0.32, -0.1, False)):
        hip = bpy.data.objects.new(name + "Hip", None); bpy.context.collection.objects.link(hip); hip.parent = root; hip.location = (x, y, 0.55)
        up = _meta_mesh(name + "Thigh", [((0, 0, -0.06), 0.09 if not front else 0.07, (0.9, 0.6, 1.4)), ((0.0 if front else -0.03, 0, -0.17), 0.05, (0.7, 0.55, 1.4))], fur)
        up.parent = hip
        knee = bpy.data.objects.new(name + "Knee", None); bpy.context.collection.objects.link(knee); knee.parent = hip; knee.location = (0.0 if front else -0.05, 0, -0.26)
        lo = _meta_mesh(name + "Shin", [((0, 0, -0.1), 0.035, (0.7, 0.7, 2.2)), ((0.03, 0, -0.27), 0.035, (1.4, 0.8, 0.6))], fur)
        lo.parent = knee
        legs.append((hip, knee, front))
    return dict(root=root, body=body, head=head, tail=tail, legs=legs)


def dog_walk(d, dist, pull=0.0, sniff=0.0, sec=0.0):
    """Trot cycle for `dist` metres travelled; pull leans the dog forward on the leash; sniff lowers the head."""
    ph = dist / 1.1 * 2 * math.pi
    for k, (hip, knee, front) in enumerate(d["legs"]):
        off = (0.0, math.pi, math.pi, 0.0)[k]                 # diagonal pairs (trot)
        a = math.sin(ph + off)
        hip.rotation_euler.y = -0.45 * a
        knee.rotation_euler.y = (0.5 * max(0.0, math.sin(ph + off + 1.2))) * (-1 if front else 1) + (0.0 if front else -0.25)
    d["root"].rotation_euler.y = math.radians(-3 * pull)
    d["head"].rotation_euler.y = math.radians(15 + 30 * sniff + 4 * math.sin(ph * 2))
    d["tail"].rotation_euler.z = 0.25 * math.sin(sec * 5.0)
    d["body"].location.z = 0.012 * math.sin(ph * 2)


# ============================================================================ light tree cache
LOW = {"fir_a": ("fir_tree_01", "_a", 120000), "fir_b": ("fir_tree_01", "_b", 120000), "birch": ("tree_small_02", "LOD0", 100000)}
_LOWOBJ = {}


def low_template(key):
    """A cached, decimated single tree (see mklow.py); returns its template object (hidden, at the origin)."""
    if key in _LOWOBJ and _LOWOBJ[key].name in bpy.data.objects:
        return _LOWOBJ[key]
    aid, pick, tgt = LOW[key]
    path = os.path.join(ph.ROOT, "_low", f"{aid}_{pick}.blend")
    if not os.path.exists(path):
        import subprocess, sys
        subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "mklow.py"), aid, pick, str(tgt)], check=True)
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.objects = list(src.objects)
    o = dst.objects[0]
    if key == "birch":
        bark = birch_bark()
        for s in o.material_slots:
            nm = (s.material.name if s.material else "").lower()
            if "trunk" in nm or "branch" in nm or "bark" in nm:
                s.material = bark
            elif s.material and not s.material.get("birch"):
                retint(s.material, (1.05, 1.1, 0.7), sat=0.8); s.material["birch"] = 1
    o.name = "TPL_" + key
    _LOWOBJ[key] = o
    return o


def low_instances(key, placements):
    """Linked copies of a cached tree: placements [(loc, rot_z, scale)]. The template itself is not rendered."""
    tpl = low_template(key)
    out = []
    for (loc, rz, s) in placements:
        o = bpy.data.objects.new(key, tpl.data); bpy.context.collection.objects.link(o)
        o.location = loc; o.rotation_euler = (0, 0, rz); o.scale = (s, s, s)
        out.append(o)
    return out


# ============================================================================ "Court reconstruction" label (chat B's style, shared)
GEN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "nvidia_doc", "assets", "generated")


def label_image(text, path, W=1920, H=816):
    import skia
    from PIL import Image
    from scipy.ndimage import gaussian_filter
    s = skia.Surface(W, H); cv = s.getCanvas(); cv.clear(skia.Color4f(0, 0, 0, 0))
    p = skia.Paint(AntiAlias=True); p.setColor4f(skia.Color4f(1, 1, 1, 1))
    f = skia.Font(skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"), 34)
    x, y = 96, H - 84
    cv.drawRect(skia.Rect.MakeXYWH(x, y - 30, 4, 38), p)                 # a thin bar before the words
    tx = x + 18
    for ch in text.upper():                                              # letter-spaced caps
        cv.drawString(ch, tx, y, f, p); tx += f.measureText(ch) + 4
    a = s.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType).astype(np.float32) / 255
    al = a[..., 3]
    sh = gaussian_filter(al, 4) * 0.6
    out = np.zeros_like(a); out[..., :3] = 1.0
    out[..., 3] = np.clip(al * 0.92 + sh * (1 - al), 0, 1)
    rgb = out[..., :3] * al[..., None] + 0.0 * (1 - al[..., None])     # shadow is black, letters white
    out[..., :3] = np.where(al[..., None] > 0.01, 1.0, 0.0)
    Image.fromarray((out * 255).astype(np.uint8), "RGBA").save(path)
    return path


def label(c, text, f_in=6, fade=12):
    """Camera-parented plane with a small lower-left caption (fades in by frame driver). Idempotent."""
    if c.get("_label") or "cam" not in c:
        return
    cam = c["cam"]
    path = os.path.join(GEN, "b_label_" + text.lower().replace(" ", "_") + ".png")
    if not os.path.exists(path):
        label_image(text, path)
    m = bpy.data.materials.new("Label"); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); tc = N.new("ShaderNodeTexCoord")
    tex = N.new("ShaderNodeTexImage"); tex.image = bpy.data.images.load(path); tex.image.alpha_mode = 'STRAIGHT'
    L.new(tc.outputs['UV'], tex.inputs['Vector'])
    em = N.new("ShaderNodeEmission"); L.new(tex.outputs['Color'], em.inputs['Color']); em.inputs['Strength'].default_value = 0.9
    tr = N.new("ShaderNodeBsdfTransparent")
    fv = N.new("ShaderNodeValue")
    d = fv.outputs[0].driver_add("default_value").driver; d.type = 'SCRIPTED'; d.expression = f"min(1, max(0, (frame - {f_in}) / {fade}))"
    mul = N.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'; L.new(tex.outputs['Alpha'], mul.inputs[0]); L.new(fv.outputs[0], mul.inputs[1])
    mx = N.new("ShaderNodeMixShader"); L.new(mul.outputs[0], mx.inputs[0]); L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], out.inputs['Surface'])
    dist = 0.5; cd = cam.data; sensor = cd.sensor_width
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0)); o = bpy.context.active_object; o.name = "ReconLabel"
    o.data.materials.append(m); o.parent = cam; o.location = (0, 0, -dist)
    for axis, k in ((0, 1.0), (1, 816 / 1920)):
        dd = o.driver_add("scale", axis).driver; dd.type = 'SCRIPTED'
        v = dd.variables.new(); v.name = "lens"; v.targets[0].id_type = 'CAMERA'; v.targets[0].id = cd; v.targets[0].data_path = "lens"
        dd.expression = f"{dist} * {sensor} / lens * {k}"
    o.visible_shadow = False; o.visible_diffuse = False; o.visible_glossy = False; o.visible_transmission = False
    o.visible_volume_scatter = False
    c["_label"] = o


