"""Scene kit for the Nvidia documentary: materials, building blocks, plate + depth rendering, run harness.

Every scene module defines:
    build(variant)  -> dict of named objects / data the camera moves need
    MOVES           -> {move_name: dict(kind="plate"|"anim", cam=fn(ctx, t) -> (location, target, lens), anim=fn(ctx, t))}
Run:  python scenes/run.py <scene> <move> [--still | --anim N] [--samples S] [--lowres] [--out DIR]
  plate : one frame at t=0.5 of the move + a depth map, animated later in 2.5D by the assembler
  anim  : N frames of a true 3D move (hero shots: chip sweep, data-center dolly, door push, doors closing)
"""
import os, sys, math
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix
from common import reset, nodes_of, world_flat, world_sky, sun, area_light, camera, point_at, ease, lerp

RES = (1920, 1080)


# ============================================================================ materials
def pbr(name, color, rough=0.5, metal=0.0, **kw):
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal
    for k, v in kw.items():
        p.inputs[k].default_value = v
    return m


def _noise(N, L, tc, scale, detail=6, vec_from=None):
    n = N.new("ShaderNodeTexNoise"); n.inputs['Scale'].default_value = scale; n.inputs['Detail'].default_value = detail
    L.new(vec_from if vec_from is not None else tc.outputs['Object'], n.inputs['Vector'])
    return n


def brushed_metal(name, color=(0.62, 0.64, 0.67), rough=(0.18, 0.34), aniso=0.7, axis=(1, 280, 1), bump=0.02):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    mp = N.new("ShaderNodeMapping"); mp.inputs['Scale'].default_value = axis; L.new(tc.outputs['Object'], mp.inputs['Vector'])
    br = _noise(N, L, tc, 6, 8, mp.outputs[0])
    sm = _noise(N, L, tc, 2.5, 4)
    rr = N.new("ShaderNodeMapRange"); rr.inputs['To Min'].default_value = rough[0]; rr.inputs['To Max'].default_value = rough[1]
    mix = N.new("ShaderNodeMath"); mix.operation = 'MULTIPLY_ADD'; mix.inputs[1].default_value = 0.5
    L.new(br.outputs['Fac'], mix.inputs[0]); L.new(sm.outputs['Fac'], mix.inputs[2])
    L.new(mix.outputs[0], rr.inputs['Value']); L.new(rr.outputs[0], p.inputs['Roughness'])
    p.inputs['Base Color'].default_value = (*color, 1); p.inputs['Metallic'].default_value = 1.0
    p.inputs['Anisotropic'].default_value = aniso
    b = N.new("ShaderNodeBump"); b.inputs['Strength'].default_value = bump; L.new(br.outputs['Fac'], b.inputs['Height']); L.new(b.outputs['Normal'], p.inputs['Normal'])
    return m


def glass(name, tint=(0.92, 0.96, 0.97), rough=0.0, ior=1.5):
    return pbr(name, tint, rough, 0.0, **{'Transmission Weight': 1.0, 'IOR': ior})


def emissive(name, color, strength=5.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs['Base Color'].default_value = (0, 0, 0, 1)
    p.inputs['Emission Color'].default_value = (*color, 1); p.inputs['Emission Strength'].default_value = strength
    return m


def blinking_leds(name, color=(0.3, 0.9, 1.0), strength=12.0, rate=6.0, duty=0.55):
    """Per-object random blinking (Object Info random + time-driven noise W). Set m['time'] each frame."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    oi = N.new("ShaderNodeObjectInfo"); tc = N.new("ShaderNodeTexCoord")
    n = N.new("ShaderNodeTexNoise"); n.noise_dimensions = '4D'; n.inputs['Scale'].default_value = 40.0; n.inputs['Detail'].default_value = 0
    L.new(tc.outputs['Object'], n.inputs['Vector'])
    wadd = N.new("ShaderNodeMath"); wadd.operation = 'MULTIPLY_ADD'; wadd.inputs[1].default_value = 37.0
    L.new(oi.outputs['Random'], wadd.inputs[0]); wadd.inputs[2].default_value = 0.0
    L.new(wadd.outputs[0], n.inputs['W'])
    thr = N.new("ShaderNodeMath"); thr.operation = 'GREATER_THAN'; thr.inputs[1].default_value = 1 - duty
    L.new(n.outputs['Fac'], thr.inputs[0])
    hue = N.new("ShaderNodeMix"); hue.data_type = 'RGBA'
    L.new(oi.outputs['Random'], hue.inputs['Factor']); hue.inputs[6].default_value = (*color, 1); hue.inputs[7].default_value = (0.35, 1.0, 0.5, 1)
    st = N.new("ShaderNodeMath"); st.operation = 'MULTIPLY'; st.inputs[1].default_value = strength
    L.new(thr.outputs[0], st.inputs[0])
    p.inputs['Base Color'].default_value = (0.02, 0.02, 0.02, 1)
    L.new(hue.outputs[2], p.inputs['Emission Color']); L.new(st.outputs[0], p.inputs['Emission Strength'])
    m["time_node"] = wadd.name
    return m


def set_led_time(mat, t):
    mat.node_tree.nodes[mat["time_node"]].inputs[2].default_value = t


def silicon(name):
    """Polished die: mirror-dark with thin-film interference and a fine interconnect grid."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    p.inputs['Base Color'].default_value = (0.05, 0.055, 0.07, 1); p.inputs['Metallic'].default_value = 0.85
    p.inputs['Roughness'].default_value = 0.08
    p.inputs['Thin Film Thickness'].default_value = 420.0; p.inputs['Thin Film IOR'].default_value = 1.9
    # floorplan blocks (brick) + fine routing (high-frequency brick) modulate thickness and roughness
    b1 = N.new("ShaderNodeTexBrick"); b1.inputs['Scale'].default_value = 9; b1.inputs['Mortar Size'].default_value = 0.01
    b1.inputs['Color1'].default_value = (0.2, 0.2, 0.2, 1); b1.inputs['Color2'].default_value = (0.8, 0.8, 0.8, 1)
    L.new(tc.outputs['Object'], b1.inputs['Vector'])
    b2 = N.new("ShaderNodeTexBrick"); b2.inputs['Scale'].default_value = 140; b2.inputs['Mortar Size'].default_value = 0.08
    b2.inputs['Brick Width'].default_value = 1.6; b2.inputs['Row Height'].default_value = 0.12
    L.new(tc.outputs['Object'], b2.inputs['Vector'])
    th = N.new("ShaderNodeMath"); th.operation = 'MULTIPLY_ADD'; th.inputs[1].default_value = 220.0; th.inputs[2].default_value = 300.0
    L.new(b1.outputs['Fac'], th.inputs[0]); L.new(th.outputs[0], p.inputs['Thin Film Thickness'])
    rr = N.new("ShaderNodeMath"); rr.operation = 'MULTIPLY_ADD'; rr.inputs[1].default_value = 0.12; rr.inputs[2].default_value = 0.05
    L.new(b2.outputs['Fac'], rr.inputs[0]); L.new(rr.outputs[0], p.inputs['Roughness'])
    bp = N.new("ShaderNodeBump"); bp.inputs['Strength'].default_value = 0.08; L.new(b2.outputs['Fac'], bp.inputs['Height']); L.new(bp.outputs['Normal'], p.inputs['Normal'])
    return m


def pcb(name, color=(0.012, 0.016, 0.014)):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    tr = N.new("ShaderNodeTexBrick"); tr.inputs['Scale'].default_value = 60; tr.inputs['Mortar Size'].default_value = 0.02
    tr.inputs['Brick Width'].default_value = 3.0; tr.inputs['Row Height'].default_value = 0.08
    L.new(tc.outputs['Object'], tr.inputs['Vector'])
    p.inputs['Base Color'].default_value = (*color, 1); p.inputs['Roughness'].default_value = 0.35
    p.inputs['Coat Weight'].default_value = 0.8; p.inputs['Coat Roughness'].default_value = 0.12
    bp = N.new("ShaderNodeBump"); bp.inputs['Strength'].default_value = 0.15; L.new(tr.outputs['Fac'], bp.inputs['Height']); L.new(bp.outputs['Normal'], p.inputs['Normal'])
    return m


def wood(name, dark=(0.03, 0.017, 0.01), light=(0.13, 0.07, 0.035), scale=(1, 18, 18), rough=0.35, coat=0.6):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    mp = N.new("ShaderNodeMapping"); mp.inputs['Scale'].default_value = scale; L.new(tc.outputs['Object'], mp.inputs['Vector'])
    wv = N.new("ShaderNodeTexWave"); wv.inputs['Scale'].default_value = 2.5; wv.inputs['Distortion'].default_value = 3.5; wv.inputs['Detail'].default_value = 6
    L.new(mp.outputs[0], wv.inputs['Vector'])
    cr = N.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (*dark, 1); cr.color_ramp.elements[1].color = (*light, 1)
    L.new(wv.outputs['Fac'], cr.inputs['Fac']); L.new(cr.outputs['Color'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = rough; p.inputs['Coat Weight'].default_value = coat; p.inputs['Coat Roughness'].default_value = 0.08
    return m


def fabric(name, color, rough=0.9, sheen=0.6, scale=900):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); n = _noise(N, L, tc, scale, 2)
    bp = N.new("ShaderNodeBump"); bp.inputs['Strength'].default_value = 0.25; L.new(n.outputs['Fac'], bp.inputs['Height']); L.new(bp.outputs['Normal'], p.inputs['Normal'])
    p.inputs['Base Color'].default_value = (*color, 1); p.inputs['Roughness'].default_value = rough
    p.inputs['Sheen Weight'].default_value = sheen
    return m


def perforated(name, color=(0.12, 0.13, 0.14), pitch=0.012, hole=0.35, metal=0.9, rough=0.35):
    """Perforated steel (alpha cut holes on a grid): rack doors, floor tiles."""
    m = brushed_metal(name, color, (rough * 0.7, rough * 1.3), 0.3)
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]; tc = N.new("ShaderNodeTexCoord")
    sc = N.new("ShaderNodeVectorMath"); sc.operation = 'SCALE'; sc.inputs['Scale'].default_value = 1 / pitch; L.new(tc.outputs['Object'], sc.inputs[0])
    fr = N.new("ShaderNodeVectorMath"); fr.operation = 'FRACTION'; L.new(sc.outputs[0], fr.inputs[0])
    sb = N.new("ShaderNodeVectorMath"); sb.operation = 'SUBTRACT'; sb.inputs[1].default_value = (0.5, 0.5, 0.5); L.new(fr.outputs[0], sb.inputs[0])
    sp = N.new("ShaderNodeSeparateXYZ"); L.new(sb.outputs[0], sp.inputs[0])
    # holes in the X/Z plane (vertical panels) and X/Y (floor) both work: use the two largest axes
    c1 = N.new("ShaderNodeCombineXYZ"); L.new(sp.outputs[0], c1.inputs[0]); L.new(sp.outputs[2], c1.inputs[1])
    ln = N.new("ShaderNodeVectorMath"); ln.operation = 'LENGTH'; L.new(c1.outputs[0], ln.inputs[0])
    gt = N.new("ShaderNodeMath"); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = hole * 0.5
    L.new(ln.outputs['Value'], gt.inputs[0]); L.new(gt.outputs[0], p.inputs['Alpha'])
    p.inputs['Metallic'].default_value = metal
    return m


# ============================================================================ geometry helpers
def box(name, loc, size, mat=None, bevel=0.0, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)   # keep the origin at loc
    if bevel:
        b = o.modifiers.new("bevel", 'BEVEL'); b.width = bevel; b.segments = 3; b.limit_method = 'ANGLE'
    if mat:
        o.data.materials.append(mat)
    return o


def cyl(name, loc, r, depth, mat=None, verts=32, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name
    if mat:
        o.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    return o


def instance(src, loc, rot=(0, 0, 0), scale=(1, 1, 1), name=None):
    """Linked duplicate (shares mesh data): cheap for arrays of racks, containers, chairs..."""
    o = bpy.data.objects.new(name or src.name + "_i", src.data)
    bpy.context.collection.objects.link(o)
    o.location = loc; o.rotation_euler = rot; o.scale = scale
    for m in src.modifiers:
        mm = o.modifiers.new(m.name, m.type)
        for attr in ("width", "segments", "limit_method", "levels", "render_levels", "thickness", "offset"):
            if hasattr(m, attr):
                try:
                    setattr(mm, attr, getattr(m, attr))
                except Exception:
                    pass
    return o


def join(objs, name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    o = bpy.context.active_object; o.name = name
    # parts are modelled around the world origin: put the object origin there, so setting .location places it
    bpy.context.scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    return o


def text_obj(name, s, loc, size, mat, rot=(math.radians(90), 0, 0), extrude=0.002, font_path="/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", align='CENTER', spacing=1.0):
    cu = bpy.data.curves.new(name, 'FONT'); cu.body = s; cu.size = size; cu.extrude = extrude
    cu.font = bpy.data.fonts.load(font_path); cu.align_x = align; cu.space_character = spacing
    o = bpy.data.objects.new(name, cu); bpy.context.collection.objects.link(o)
    o.location = loc; o.rotation_euler = rot; o.data.materials.append(mat)
    return o


def skyline(seed, origin, extent, n, h_range, mat_body, mat_win, footprint=(14, 40), avoid=None, z0=0.0):
    """Procedural city block: towers with emissive window grids (window shader keyed off object coords)."""
    r = np.random.default_rng(seed)
    out = []
    for k in range(n):
        x = origin[0] + r.uniform(-extent[0], extent[0]); y = origin[1] + r.uniform(-extent[1], extent[1])
        if avoid and math.hypot(x - avoid[0], y - avoid[1]) < avoid[2]:
            continue
        w_ = r.uniform(*footprint); d_ = r.uniform(*footprint); h_ = r.uniform(*h_range) * (1.8 if r.random() < 0.12 else 1)
        o = box(f"Tower{k}", (x, y, z0 + h_ / 2), (w_, d_, h_), mat_win)   # facade shader covers the whole tower
        out.append(o)
    return out


def window_material(name, lit=(1.0, 0.82, 0.55), density=0.45, floor=3.6, bay=2.4, strength=3.0, glass_col=(0.02, 0.03, 0.04)):
    """Curtain-wall facade: glossy glass with a random subset of lit window cells (object/world coords)."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); geo = N.new("ShaderNodeNewGeometry")
    mp = N.new("ShaderNodeMapping"); mp.inputs['Scale'].default_value = (1 / bay, 1 / bay, 1 / floor)
    L.new(geo.outputs['Position'], mp.inputs['Vector'])
    fl = N.new("ShaderNodeVectorMath"); fl.operation = 'FLOOR'; L.new(mp.outputs[0], fl.inputs[0])
    wn = N.new("ShaderNodeTexWhiteNoise"); wn.noise_dimensions = '3D'; L.new(fl.outputs[0], wn.inputs['Vector'])
    on = N.new("ShaderNodeMath"); on.operation = 'GREATER_THAN'; on.inputs[1].default_value = 1 - density; L.new(wn.outputs['Value'], on.inputs[0])
    # mullions: dark frame lines between cells
    frc = N.new("ShaderNodeVectorMath"); frc.operation = 'FRACTION'; L.new(mp.outputs[0], frc.inputs[0])
    sp = N.new("ShaderNodeSeparateXYZ"); L.new(frc.outputs[0], sp.inputs[0])
    mz = N.new("ShaderNodeMath"); mz.operation = 'LESS_THAN'; mz.inputs[1].default_value = 0.16; L.new(sp.outputs[2], mz.inputs[0])
    mx = N.new("ShaderNodeMath"); mx.operation = 'LESS_THAN'; mx.inputs[1].default_value = 0.12; L.new(sp.outputs[0], mx.inputs[0])
    my = N.new("ShaderNodeMath"); my.operation = 'LESS_THAN'; my.inputs[1].default_value = 0.12; L.new(sp.outputs[1], my.inputs[0])
    # vertical mullions only along the axis that actually varies across this wall (face normal decides)
    nsep = N.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs['Normal'], nsep.inputs[0])
    nxa = N.new("ShaderNodeMath"); nxa.operation = 'ABSOLUTE'; L.new(nsep.outputs[0], nxa.inputs[0])
    nya = N.new("ShaderNodeMath"); nya.operation = 'ABSOLUTE'; L.new(nsep.outputs[1], nya.inputs[0])
    mxw = N.new("ShaderNodeMath"); mxw.operation = 'MULTIPLY'; L.new(mx.outputs[0], mxw.inputs[0]); L.new(nya.outputs[0], mxw.inputs[1])
    myw = N.new("ShaderNodeMath"); myw.operation = 'MULTIPLY'; L.new(my.outputs[0], myw.inputs[0]); L.new(nxa.outputs[0], myw.inputs[1])
    m1 = N.new("ShaderNodeMath"); m1.operation = 'MAXIMUM'; L.new(mz.outputs[0], m1.inputs[0]); L.new(mxw.outputs[0], m1.inputs[1])
    m2 = N.new("ShaderNodeMath"); m2.operation = 'MAXIMUM'; L.new(m1.outputs[0], m2.inputs[0]); L.new(myw.outputs[0], m2.inputs[1])
    # whole floors switch on/off together sometimes (offices), so the pattern reads as buildings, not noise
    flz = N.new("ShaderNodeSeparateXYZ"); L.new(fl.outputs[0], flz.inputs[0])
    fwn = N.new("ShaderNodeTexWhiteNoise"); fwn.noise_dimensions = '1D'; L.new(flz.outputs[2], fwn.inputs['W'])
    fon = N.new("ShaderNodeMath"); fon.operation = 'GREATER_THAN'; fon.inputs[1].default_value = 0.55; L.new(fwn.outputs['Value'], fon.inputs[0])
    keep = N.new("ShaderNodeMath"); keep.operation = 'SUBTRACT'; keep.inputs[0].default_value = 1.0; L.new(m2.outputs[0], keep.inputs[1])
    lit0 = N.new("ShaderNodeMath"); lit0.operation = 'MULTIPLY'; L.new(on.outputs[0], lit0.inputs[0]); L.new(fon.outputs[0], lit0.inputs[1])
    lit_on = N.new("ShaderNodeMath"); lit_on.operation = 'MULTIPLY'; L.new(lit0.outputs[0], lit_on.inputs[0]); L.new(keep.outputs[0], lit_on.inputs[1])
    var = N.new("ShaderNodeMath"); var.operation = 'MULTIPLY_ADD'; var.inputs[1].default_value = 0.8; var.inputs[2].default_value = 0.4
    wn2 = N.new("ShaderNodeTexWhiteNoise"); wn2.noise_dimensions = '3D'; L.new(fl.outputs[0], wn2.inputs['Vector'])
    L.new(wn2.outputs['Value'], var.inputs[0])
    es = N.new("ShaderNodeMath"); es.operation = 'MULTIPLY'; L.new(lit_on.outputs[0], es.inputs[0]); L.new(var.outputs[0], es.inputs[1])
    es2 = N.new("ShaderNodeMath"); es2.operation = 'MULTIPLY'; es2.inputs[1].default_value = strength; L.new(es.outputs[0], es2.inputs[0])
    p.inputs['Base Color'].default_value = (*glass_col, 1); p.inputs['Roughness'].default_value = 0.06; p.inputs['Metallic'].default_value = 0.6
    p.inputs['Emission Color'].default_value = (*lit, 1); L.new(es2.outputs[0], p.inputs['Emission Strength'])
    return m


def haze(loc, size, density=0.02, color=(0.6, 0.75, 1.0), anis=0.3):
    """Uniform volumetric haze box (light shafts, atmosphere)."""
    o = box("Haze", loc, size)
    m = bpy.data.materials.new("Haze"); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); v = N.new("ShaderNodeVolumePrincipled")
    v.inputs['Density'].default_value = density; v.inputs['Color'].default_value = (*color, 1); v.inputs['Anisotropy'].default_value = anis
    L.new(v.outputs[0], out.inputs['Volume']); o.data.materials.append(m)
    o.visible_shadow = False
    return o


# ============================================================================ depth pass + harness
def render_depth(path, near=0.1, far=60.0):
    """Linear depth (0 near .. 1 far) via a material override, for 2.5D parallax in the assembler."""
    s = bpy.context.scene
    m = bpy.data.materials.new("DepthOverride"); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); cam = N.new("ShaderNodeCameraData")
    mr = N.new("ShaderNodeMapRange"); mr.inputs['From Min'].default_value = near; mr.inputs['From Max'].default_value = far
    L.new(cam.outputs['View Distance'], mr.inputs['Value'])
    em = N.new("ShaderNodeEmission"); L.new(mr.outputs[0], em.inputs['Color'])
    L.new(em.outputs[0], out.inputs['Surface'])
    vl = s.view_layers[0]; old = vl.material_override; vl.material_override = m
    w = s.world; s.world = bpy.data.worlds.new("DepthWorld")
    s.world.use_nodes = True; s.world.node_tree.nodes["Background"].inputs['Color'].default_value = (1, 1, 1, 1)
    samples, den, vt = s.cycles.samples, s.cycles.use_denoising, s.view_settings.view_transform
    s.cycles.samples = 4; s.cycles.use_denoising = False; s.view_settings.view_transform = 'Standard'
    hidden = [o for o in s.objects if o.name.startswith("Haze") and not o.hide_render]
    for o in hidden:
        o.hide_render = True
    s.render.filepath = path; bpy.ops.render.render(write_still=True)
    for o in hidden:
        o.hide_render = False
    vl.material_override = old; s.world = w
    s.cycles.samples, s.cycles.use_denoising, s.view_settings.view_transform = samples, den, vt


def apply_cam(cam, ctx, spec, t):
    loc, tgt, lens = spec["cam"](ctx, t)
    cam.location = Vector(loc); point_at(cam, tuple(tgt)); cam.data.lens = lens
    if cam.data.dof.use_dof:
        cam.data.dof.focus_distance = (Vector(loc) - Vector(spec.get("focus", lambda c, t: tgt)(ctx, t))).length
    if spec.get("anim"):
        spec["anim"](ctx, t)
