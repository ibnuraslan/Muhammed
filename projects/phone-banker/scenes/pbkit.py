"""Shared pieces for The Phone That Killed a Banker: Moscow masonry facades, period cars (Lada, Volga, UAZ van),
and small helpers. CG in the house style; no brands."""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import box, cyl, join, pbr, emissive, glass


def masonry_facade(name, plaster=(0.5, 0.44, 0.36), floor=3.3, bay=2.4, win_w=0.5, win_h=0.55, lit_frac=0.0,
                   lit_col=(1.0, 0.78, 0.5), lit_strength=2.0, frame_col=(0.75, 0.73, 0.68)):
    """Stucco wall with a grid of punched windows (frames, dark glass, net-curtain glow, a few lit at night).
    Works on X- and Y-facing walls (world coordinates)."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    geo = N.new("ShaderNodeNewGeometry")
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs['Position'], sep.inputs[0])
    nrm = N.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs['Normal'], nrm.inputs[0])
    ax = N.new("ShaderNodeMath"); ax.operation = 'ABSOLUTE'; L.new(nrm.outputs['X'], ax.inputs[0])
    gt = N.new("ShaderNodeMath"); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = 0.5; L.new(ax.outputs[0], gt.inputs[0])
    hmix = N.new("ShaderNodeMix"); hmix.data_type = 'FLOAT'; L.new(gt.outputs[0], hmix.inputs['Factor'])
    L.new(sep.outputs['X'], hmix.inputs[2]); L.new(sep.outputs['Y'], hmix.inputs[3])

    def cell(src, period):
        d = N.new("ShaderNodeMath"); d.operation = 'DIVIDE'; d.inputs[1].default_value = period; L.new(src, d.inputs[0])
        f = N.new("ShaderNodeMath"); f.operation = 'FRACT'; L.new(d.outputs[0], f.inputs[0])
        fl = N.new("ShaderNodeMath"); fl.operation = 'FLOOR'; L.new(d.outputs[0], fl.inputs[0])
        c = N.new("ShaderNodeMath"); c.operation = 'SUBTRACT'; c.inputs[1].default_value = 0.5; L.new(f.outputs[0], c.inputs[0])
        a = N.new("ShaderNodeMath"); a.operation = 'ABSOLUTE'; L.new(c.outputs[0], a.inputs[0])
        return a, fl

    hx, ix = cell(hmix.outputs[0], bay)
    hz, iz = cell(sep.outputs['Z'], floor)

    def lt(src, v):
        o = N.new("ShaderNodeMath"); o.operation = 'LESS_THAN'; o.inputs[1].default_value = v; L.new(src.outputs[0], o.inputs[0]); return o

    def mul(a, b):
        o = N.new("ShaderNodeMath"); o.operation = 'MULTIPLY'; L.new(a.outputs[0], o.inputs[0]); L.new(b.outputs[0], o.inputs[1]); return o

    wall_face = N.new("ShaderNodeMath"); wall_face.operation = 'LESS_THAN'; wall_face.inputs[1].default_value = 0.5
    az = N.new("ShaderNodeMath"); az.operation = 'ABSOLUTE'; L.new(nrm.outputs['Z'], az.inputs[0]); L.new(az.outputs[0], wall_face.inputs[0])
    # thresholds in cell units (the cell coordinate runs 0..0.5 from the cell centre)
    hole = mul(mul(lt(hx, win_w / 2 / bay), lt(hz, win_h / 2 / floor)), wall_face)                       # window opening (incl. frame)
    pane = mul(mul(lt(hx, (win_w / 2 - 0.07) / bay), lt(hz, (win_h / 2 - 0.08) / floor)), wall_face)     # glass inside the frame
    # glass: dark with a pale net-curtain glow, a few warm lit rooms
    comb = N.new("ShaderNodeCombineXYZ"); L.new(ix.outputs[0], comb.inputs[0]); L.new(iz.outputs[0], comb.inputs[1])
    wn = N.new("ShaderNodeTexWhiteNoise"); wn.noise_dimensions = '3D'; L.new(comb.outputs[0], wn.inputs['Vector'])
    on = N.new("ShaderNodeMath"); on.operation = 'LESS_THAN'; on.inputs[1].default_value = lit_frac; L.new(wn.outputs['Value'], on.inputs[0])
    lit = mul(on, pane)
    glass_col = N.new("ShaderNodeMix"); glass_col.data_type = 'RGBA'
    glass_col.inputs[6].default_value = (0.05, 0.055, 0.06, 1); glass_col.inputs[7].default_value = (0.32, 0.32, 0.31, 1)
    L.new(wn.outputs['Value'], glass_col.inputs['Factor'])
    # plaster with grime
    tc = N.new("ShaderNodeTexCoord")
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 0.6; nz.inputs['Detail'].default_value = 8; L.new(geo.outputs['Position'], nz.inputs['Vector'])
    pl = N.new("ShaderNodeMix"); pl.data_type = 'RGBA'; pl.blend_type = 'MULTIPLY'; pl.inputs['Factor'].default_value = 0.45
    pl.inputs[6].default_value = (*plaster, 1); L.new(nz.outputs['Color'], pl.inputs[7])
    c1 = N.new("ShaderNodeMix"); c1.data_type = 'RGBA'; L.new(hole.outputs[0], c1.inputs['Factor'])
    L.new(pl.outputs[2], c1.inputs[6]); c1.inputs[7].default_value = (*frame_col, 1)
    c2 = N.new("ShaderNodeMix"); c2.data_type = 'RGBA'; L.new(pane.outputs[0], c2.inputs['Factor'])
    L.new(c1.outputs[2], c2.inputs[6]); L.new(glass_col.outputs[2], c2.inputs[7])
    L.new(c2.outputs[2], p.inputs['Base Color'])
    r = N.new("ShaderNodeMapRange"); r.inputs['To Min'].default_value = 0.85; r.inputs['To Max'].default_value = 0.12
    L.new(pane.outputs[0], r.inputs['Value']); L.new(r.outputs[0], p.inputs['Roughness'])
    if lit_frac > 0:
        es = N.new("ShaderNodeMath"); es.operation = 'MULTIPLY'; es.inputs[1].default_value = lit_strength; L.new(lit.outputs[0], es.inputs[0])
        p.inputs['Emission Color'].default_value = (*lit_col, 1); L.new(es.outputs[0], p.inputs['Emission Strength'])
    return m


# ============================================================================ cars
def _shell(name, L_, W_, prof, mat, bevel=0.05):
    """Car body as a side-profile extrusion: prof = [(x, z_bottom, z_top)] along the length (x)."""
    verts, faces = [], []
    n = len(prof)
    for i, (x, zb, zt) in enumerate(prof):
        for (y, z) in ((-W_ / 2, zb), (W_ / 2, zb), (W_ / 2, zt), (-W_ / 2, zt)):
            verts.append((x, y, z))
    for i in range(n - 1):
        a = i * 4; b = (i + 1) * 4
        for k in range(4):
            faces.append((a + k, a + (k + 1) % 4, b + (k + 1) % 4, b + k))
    faces.append((3, 2, 1, 0)); faces.append(((n - 1) * 4, (n - 1) * 4 + 1, (n - 1) * 4 + 2, (n - 1) * 4 + 3))
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o); me.materials.append(mat)
    if bevel:
        b = o.modifiers.new("b", 'BEVEL'); b.width = bevel; b.segments = 3; b.limit_method = 'ANGLE'
    return o


def soviet_car_box(name, paint_col, kind="lada", stripe=None, beacon=False, label=None):
    """Boxy late-Soviet sedans: 'lada' (2105/2107 style, 4.13 m) or 'volga' (GAZ-24/31 style, 4.75 m).
    Origin between the wheels on the ground, front toward +X. Returns the joined body (children: lights)."""
    if kind == "volga":
        L_, W_, wb, wr = 4.75, 1.8, 2.8, 0.34
    else:
        L_, W_, wb, wr = 4.13, 1.62, 2.42, 0.31
    paint = pbr(name + "Paint", paint_col, 0.32, 0.25, **{'Coat Weight': 0.8, 'Coat Roughness': 0.12})
    glass_m = pbr(name + "Glass", (0.02, 0.025, 0.03), 0.04, 0.0, **{'Coat Weight': 1.0})
    chrome = pbr("Chrome", (0.75, 0.75, 0.75), 0.2, 1.0)
    black = pbr("Trim", (0.02, 0.02, 0.02), 0.6)
    tyre = pbr("Tyre", (0.02, 0.02, 0.02), 0.85)
    h = L_ / 2
    # lower body: a long box with a slight wedge, bonnet and boot lines
    lower = _shell(name + "Lower", L_, W_, [(-h, 0.24, 0.8), (-h + 0.04, 0.2, 0.86), (h - 0.04, 0.2, 0.84), (h, 0.24, 0.74)], paint, 0.07)
    lower.modifiers["b"].segments = 4
    # wheel arches cut out of the body sides (boolean, applied when the parts are joined)
    for sx in (-1, 1):
        cutter = cyl(name + "ArchCut", (sx * wb / 2, 0, wr), wr + 0.05, W_ + 0.4, None, verts=32, rot=(math.radians(90), 0, 0))
        bo = lower.modifiers.new("arch", 'BOOLEAN'); bo.operation = 'DIFFERENCE'; bo.object = cutter; bo.solver = 'EXACT'
        cutter.hide_render = True; cutter.hide_viewport = True
        cutters = getattr(soviet_car, "_cutters", []); cutters.append(cutter); soviet_car._cutters = cutters
    # inner wheel-well liners (dark) so the cut reads as an arch, not a hole
    wells = []
    for sx in (-1, 1):
        wells.append(cyl("Well", (sx * wb / 2, 0, wr), wr + 0.045, W_ - 0.06, black if False else pbr("WellBlack", (0.015, 0.015, 0.015), 0.9), verts=32, rot=(math.radians(90), 0, 0)))
    # greenhouse: trapezoid (upright Soviet glasshouse)
    fx0, fx1 = (-0.95, 0.75) if kind == "lada" else (-1.15, 0.7)
    cab_bot = 0.86; cab_top = 1.39 if kind == "lada" else 1.42
    cab = _shell(name + "Cabin", 0, W_ - 0.12,
                 [(fx0 - 0.28, cab_bot, cab_bot + 0.01), (fx0, cab_bot, cab_top), (fx1 - 0.35, cab_bot, cab_top), (fx1, cab_bot, cab_bot + 0.01)], glass_m, 0.03)
    roof = _shell(name + "Roof", 0, W_ - 0.1, [(fx0 - 0.02, cab_top - 0.03, cab_top + 0.02), (fx1 - 0.33, cab_top - 0.03, cab_top + 0.02)], paint, 0.02)
    parts = [lower, cab, roof] + wells
    # side crease and chrome belt line, black window surrounds
    for sy in (-1, 1):
        parts.append(box("Crease", (0, sy * (W_ / 2 + 0.002), 0.6), (L_ - 0.35, 0.006, 0.012), pbr("CreaseShade", tuple(v * 0.6 for v in paint_col), 0.4)))
        parts.append(box("Belt", ((fx0 + fx1 - 0.35) / 2 - 0.1, sy * (W_ / 2 - 0.05), cab_bot + 0.02), (fx1 - fx0 + 0.2, 0.02, 0.02), chrome))
    # pillars (B pillar and door frames read as body colour)
    for x in (fx0 + 0.02, (fx0 + fx1 - 0.35) / 2):
        for sy in (-1, 1):
            parts.append(box("Pillar", (x, sy * (W_ / 2 - 0.065), (cab_bot + cab_top) / 2), (0.07, 0.02, cab_top - cab_bot), paint))
    # bumpers, grille, lamps
    for sx in (-1, 1):
        parts.append(box("Bumper", (sx * (h + 0.04), 0, 0.36), (0.07, W_ + 0.02, 0.1), chrome, bevel=0.02))
    parts.append(box("Grille", (h + 0.002, 0, 0.62), (0.02, W_ * 0.62, 0.2), black))
    for sy in (-1, 1):
        if kind == "lada":
            parts.append(box("HeadRect", (h + 0.004, sy * (W_ / 2 - 0.22), 0.62), (0.02, 0.3, 0.16), emissive("HeadOff", (0.9, 0.9, 0.85), 0.15)))
        else:
            parts.append(cyl("HeadRound", (h + 0.004, sy * (W_ / 2 - 0.2), 0.62), 0.085, 0.02, emissive("HeadOff", (0.9, 0.9, 0.85), 0.15), verts=20, rot=(0, math.radians(90), 0)))
        parts.append(box("Tail", (-h - 0.004, sy * (W_ / 2 - 0.2), 0.68), (0.02, 0.28, 0.12), pbr("TailRed", (0.4, 0.02, 0.02), 0.3)))
    parts.append(box("Sill", (0, 0, 0.22), (L_ - 0.5, W_ + 0.005, 0.05), black))
    for sy in (-1, 1):
        parts.append(box("DoorSeam", (fx0 + 0.02, sy * (W_ / 2 + 0.001), 0.55), (0.008, 0.004, 0.6), black))
        parts.append(box("DoorSeam", ((fx0 + fx1 - 0.35) / 2, sy * (W_ / 2 + 0.001), 0.55), (0.008, 0.004, 0.6), black))
        parts.append(box("Handle", ((fx0 + fx1 - 0.35) / 2 - 0.25, sy * (W_ / 2 + 0.008), 0.78), (0.12, 0.015, 0.025), chrome))
        parts.append(box("Mirror", (fx1 - 0.3, sy * (W_ / 2 + 0.06), 0.98), (0.08, 0.1, 0.07), black))
    if stripe:
        for sy in (-1, 1):
            parts.append(box("Stripe", (0, sy * (W_ / 2 + 0.003), 0.58), (L_ - 0.3, 0.004, 0.11), pbr("Stripe", stripe, 0.4)))
    wheels = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            wx = sx * wb / 2
            t = cyl("Tyre", (wx, sy * (W_ / 2 - 0.14), wr), wr, 0.18, tyre, verts=28, rot=(math.radians(90), 0, 0))
            hc = cyl("Hub", (wx, sy * (W_ / 2 - 0.045), wr), wr * 0.55, 0.012, chrome, verts=24, rot=(math.radians(90), 0, 0))
            parts += [t, hc]
    body = joinm(parts, name)
    for ct in getattr(soviet_car, "_cutters", []):
        bpy.data.objects.remove(ct, do_unlink=True)
    soviet_car._cutters = []
    if label:
        from kit import text_obj
        for sy in (-1, 1):
            t = text_obj(name + "Label", label, (-0.2, sy * (W_ / 2 + 0.006), 0.72), 0.13, pbr("LabelBlue", stripe or (0.02, 0.05, 0.25), 0.4),
                         rot=(math.radians(90), 0, 0 if sy < 0 else math.pi), extrude=0.0)
            t.parent = body; t.location = (-0.2, sy * (W_ / 2 + 0.006), 0.72)
    if beacon:
        bm = bpy.data.materials.new(name + "Beacon"); bm.use_nodes = True
        Nn = bm.node_tree.nodes; Ll = bm.node_tree.links; Nn.clear()
        out = Nn.new("ShaderNodeOutputMaterial"); em = Nn.new("ShaderNodeEmission"); em.inputs['Color'].default_value = (0.15, 0.35, 1.0, 1)
        v = Nn.new("ShaderNodeValue"); d = v.outputs[0].driver_add("default_value").driver; d.type = 'SCRIPTED'
        d.expression = "14 * (1 if (frame % 16) < 8 else 0.08)"
        Ll.new(v.outputs[0], em.inputs['Strength']); Ll.new(em.outputs[0], out.inputs['Surface'])
        bc = cyl(name + "Beacon", (0, 0, 0), 0.07, 0.12, bm, verts=20); bc.parent = body; bc.location = (fx0 + 0.45, 0, cab_top + 0.08)
        l = bpy.data.lights.new(name + "BeaconL", 'POINT'); l.color = (0.2, 0.4, 1.0); l.shadow_soft_size = 0.05
        dl = l.driver_add("energy").driver; dl.type = 'SCRIPTED'; dl.expression = "120 * (1 if (frame % 16) < 8 else 0.02)"
        lo = bpy.data.objects.new(name + "BeaconL", l); bpy.context.collection.objects.link(lo); lo.parent = body; lo.location = (fx0 + 0.45, 0, cab_top + 0.25)
    return body


def joinm(objs, name):
    """Join parts into one mesh, applying each part's own modifiers (bevels) first; text curves become meshes."""
    dg = bpy.context.evaluated_depsgraph_get()
    meshes = []
    for o in objs:
        e = o.evaluated_get(dg)
        me = bpy.data.meshes.new_from_object(e, preserve_all_data_layers=True, depsgraph=dg)
        me.transform(o.matrix_world)
        n = bpy.data.objects.new(o.name, me); bpy.context.collection.objects.link(n)
        meshes.append(n)
    for o in objs:
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.ops.object.select_all(action='DESELECT')
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.join()
    o = bpy.context.active_object; o.name = name
    return o


def painting(path, W=600, H=860, seed=3):
    """A muted oil-style landscape (birches by a river under a grey sky): generic office art."""
    import os
    from PIL import Image, ImageFilter, ImageDraw
    if os.path.exists(path):
        return path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    r = np.random.default_rng(seed)
    y = np.linspace(0, 1, H)[:, None] * np.ones((1, W))
    sky = np.stack([0.62 - 0.1 * y, 0.64 - 0.1 * y, 0.62 - 0.06 * y], -1)
    img = (sky * 255).astype(np.uint8)
    im = Image.fromarray(img, "RGB"); d = ImageDraw.Draw(im)
    hz = int(H * 0.55)
    d.rectangle([0, hz, W, H], fill=(86, 92, 64))
    d.rectangle([0, int(H * 0.68), W, int(H * 0.8)], fill=(120, 128, 124))       # the river
    for k in range(260):                                                        # far treeline dabs
        x = r.uniform(0, W); yy = hz - r.uniform(0, 70)
        d.ellipse([x - 14, yy - 10, x + 14, yy + 18], fill=tuple(int(v) for v in (r.uniform(50, 75), r.uniform(62, 85), r.uniform(45, 60))))
    for k in range(9):                                                          # birch trunks
        x = r.uniform(30, W - 30); w = r.uniform(5, 10); top = r.uniform(H * 0.1, H * 0.35)
        d.rectangle([x, top, x + w, hz + r.uniform(10, 60)], fill=(214, 210, 198))
        for j in range(8):
            yy = r.uniform(top, hz); d.rectangle([x, yy, x + w, yy + 3], fill=(40, 38, 34))
        for j in range(30):
            cx = x + r.uniform(-50, 50); cy = top + r.uniform(-30, 80)
            d.ellipse([cx - 9, cy - 7, cx + 9, cy + 7], fill=(int(r.uniform(110, 150)), int(r.uniform(115, 140)), int(r.uniform(50, 70))))
    im = im.filter(ImageFilter.GaussianBlur(1.6))
    a = np.asarray(im).astype(np.float32)
    a += r.normal(0, 6, a.shape)                                                # canvas grain
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(path)
    return path


def image_plane(name, path, loc, size, rot, rough=0.6, emit=0.0):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name; o.scale = (size[0], size[1], 1)
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(path, check_existing=True)
    tc = N.new("ShaderNodeTexCoord"); L.new(tc.outputs['UV'], t.inputs['Vector']); L.new(t.outputs['Color'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = rough
    if emit:
        L.new(t.outputs['Color'], p.inputs['Emission Color']); p.inputs['Emission Strength'].default_value = emit
    o.data.materials.append(m)
    return o


def precip_curtains(kind, x_range=(-30, 30), ys=(-14, -9, -5, -1.5), top=12.0, fall=None):
    """Falling rain or snow: textured vertical planes that drop and wrap by frame drivers (bake-safe, no particles)."""
    snow = kind == "snow"
    m = bpy.data.materials.new("Precip" + kind); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); tc = N.new("ShaderNodeTexCoord")
    mp = N.new("ShaderNodeMapping"); mp.inputs['Scale'].default_value = (900, 180, 1) if snow else (2000, 30, 1)
    wn = N.new("ShaderNodeTexWhiteNoise"); wn.noise_dimensions = '2D'
    L.new(tc.outputs['Object'], mp.inputs['Vector']); L.new(mp.outputs[0], wn.inputs['Vector'])
    gt = N.new("ShaderNodeMath"); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = 0.993 if snow else 0.97; L.new(wn.outputs['Value'], gt.inputs[0])
    sc = N.new("ShaderNodeMath"); sc.operation = 'MULTIPLY'; sc.inputs[1].default_value = 0.9 if snow else 0.45; L.new(gt.outputs[0], sc.inputs[0])
    tr = N.new("ShaderNodeBsdfTransparent"); gl = N.new("ShaderNodeEmission"); gl.inputs['Color'].default_value = (0.95, 0.96, 1.0, 1) if snow else (0.75, 0.8, 0.88, 1)
    gl.inputs['Strength'].default_value = 1.2 if snow else 0.5
    mx = N.new("ShaderNodeMixShader"); L.new(sc.outputs[0], mx.inputs[0]); L.new(tr.outputs[0], mx.inputs[1]); L.new(gl.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], out.inputs['Surface'])
    speed = fall or (1.2 if snow else 8.0)            # metres per second
    objs = []
    for y in ys:
        for j in range(2):
            bpy.ops.mesh.primitive_plane_add(size=1, location=(0, y, top / 2 + j * top), rotation=(math.radians(90), 0, 0))
            o = bpy.context.active_object; o.name = "Precip" + kind; o.scale = (x_range[1] - x_range[0], top, 1)
            o.location.x = (x_range[0] + x_range[1]) / 2
            o.data.materials.append(m); o.visible_shadow = False; o.visible_diffuse = False; o.visible_glossy = False
            d = o.driver_add("location", 2).driver; d.type = 'SCRIPTED'
            d.expression = f"{top / 2 + j * top} - ((frame / 24 * {speed}) % {top})"
            if snow:
                d2 = o.driver_add("location", 0).driver; d2.type = 'SCRIPTED'
                d2.expression = f"{(x_range[0] + x_range[1]) / 2} + 0.4 * sin(frame * 0.03 + {j + y})"
            objs.append(o)
    return objs


def leaves(n, area, seed=5, cols=((0.55, 0.3, 0.06), (0.62, 0.42, 0.1), (0.4, 0.18, 0.05))):
    """Fallen leaves: small curled planes scattered over an area (x0, x1, y0, y1). Returns the objects."""
    rng = np.random.default_rng(seed)
    mats = [pbr(f"Leaf{k}", c_, 0.7, 0.0, **{'Subsurface Weight': 0.2}) for k, c_ in enumerate(cols)]
    out = []
    for k in range(n):
        bpy.ops.mesh.primitive_plane_add(size=1, location=(rng.uniform(area[0], area[1]), rng.uniform(area[2], area[3]), 0.012))
        o = bpy.context.active_object; o.name = "Leaf"; o.scale = (0.06, 0.04, 1); o.rotation_euler = (rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3), rng.uniform(0, 6.28))
        o.data.materials.append(mats[k % len(mats)]); out.append(o)
    return out


def ph_instances(aid, placements, pick=None, decimate=None):
    """Import a Poly Haven model once and place linked copies (shared mesh data): placements = [(loc, rot_z, scale)].
    pick: keep only the sub-mesh whose name contains this (e.g. one tree of a three-tree asset), centred at the origin;
    decimate: collapse ratio applied once to the shared mesh (heavy scans)."""
    import ph
    root, ms = ph.model(aid)
    if pick:
        keep = [o for o in ms if pick in o.name]
        for o in ms:
            if o not in keep:
                me = o.data; bpy.data.objects.remove(o, do_unlink=True); bpy.data.meshes.remove(me)
        ms = keep
        lo, hi = ph.bounds(ms)
        for o in ms:
            o.location.x -= (lo.x + hi.x) / 2; o.location.y -= (lo.y + hi.y) / 2
    if decimate:
        for o in ms:
            d = o.modifiers.new("dec", 'DECIMATE'); d.ratio = decimate
            bpy.context.view_layer.objects.active = o; bpy.ops.object.modifier_apply(modifier="dec")
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


def soviet_car(name, paint_col, kind="lada", stripe=None, beacon=False, label=None, lamps=False):
    """Shared realistic vehicle kit (nvidia_doc/scenes/vehicles.py): a late-Soviet sedan, militia variant with the
    rotating light bar and livery. Front is +X, origin on the ground (same convention as the old placeholder)."""
    import vehicles
    root = vehicles.make("sedan_1990s_soviet", color=None if beacon else paint_col, variant="militia" if beacon else None,
                         lamps=lamps, dirt=0.15)
    root.name = name
    return root


def kit_vehicle(kind, name, color=None, variant=None, lamps=False):
    import vehicles
    root = vehicles.make(kind, color=color, variant=variant, lamps=lamps)
    root.name = name
    return root
