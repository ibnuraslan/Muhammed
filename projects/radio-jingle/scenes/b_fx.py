"""Chat B storyboard-v2 devices: facts written into the set, measure lines, drawn curves (a line that draws itself),
an object-on-black stage, red string, a stylised map system (charcoal paper, brick-red line, cream labels), number
stencils. Real colours, mood from one hard light (look v5); no teal.
"""
import math
import numpy as np
import bpy
import bmesh
from mathutils import Vector
from kit import *
import b_common as B

CREAM = (0.86, 0.80, 0.66)
BRICK = (0.55, 0.085, 0.06)
CHARCOAL = (0.045, 0.043, 0.040)
FONT_SLAB = "/home/user/Muhammed/nvidia_doc/assets/fonts/RobotoSlab-Bold.ttf"
FONT_SANS = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"


# ------------------------------------------------------------------ materials
def ink(name, color, glow=0.0):
    """Printed / painted ink: matte, with an optional faint self-light so thin lines read on dark paper."""
    m = pbr(name, color, 0.6)
    if glow:
        p = m.node_tree.nodes["Principled BSDF"]
        p.inputs['Emission Color'].default_value = (*color, 1); p.inputs['Emission Strength'].default_value = glow
    return m


def paper(name, color=CHARCOAL, scale=60.0):
    """Matte paper with a fine fibre bump."""
    m = pbr(name, color, 0.85)
    N = m.node_tree.nodes; L = m.node_tree.links
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = 8
    bm = N.new("ShaderNodeBump"); bm.inputs['Strength'].default_value = 0.08
    L.new(nz.outputs['Fac'], bm.inputs['Height']); L.new(bm.outputs['Normal'], N["Principled BSDF"].inputs['Normal'])
    return m


# ------------------------------------------------------------------ curves that draw themselves
def curve(name, pts, mat, bevel=0.01, closed=False, res=2, smooth=False):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'
    cu.bevel_depth = bevel; cu.bevel_resolution = res; cu.use_fill_caps = True
    cu.bevel_factor_mapping_end = 'SPLINE'; cu.bevel_factor_mapping_start = 'SPLINE'
    if smooth:
        sp = cu.splines.new('NURBS'); sp.points.add(len(pts) - 1); sp.order_u = 3; sp.use_endpoint_u = True
    else:
        sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = (p[0], p[1], p[2], 1)
    sp.use_cyclic_u = closed
    o = bpy.data.objects.new(name, cu); bpy.context.collection.objects.link(o)
    o.data.materials.append(mat)
    return o


def draw(o, u, start=0.0):
    """Reveal a curve from its start (u in 0..1). Hidden entirely at u <= 0."""
    u = max(0.0, min(1.0, u))
    o.hide_render = u <= 0.001
    o.data.bevel_factor_start = max(0.0, min(start, u))
    o.data.bevel_factor_end = max(0.002, u)


# ------------------------------------------------------------------ text written into the set
def fact_text(name, s, loc, size, color=CREAM, rot=(0, 0, 0), font=FONT_SLAB, glow=0.0, align='CENTER', extrude=0.0015):
    t = text_obj(name, s, loc, size, ink(name + "Ink", color, glow), rot=rot, extrude=extrude, font_path=font, align=align)
    return t


def show(o, u):
    """Fade-in for small set pieces: scale up from 0 (keeps the materials simple and the bakes deterministic)."""
    u = max(0.0, min(1.0, u)); e = u * u * (3 - 2 * u)
    if "s0" not in o:
        o["s0"] = tuple(o.scale)
    s0 = o["s0"]
    o.scale = (s0[0] * e, s0[1] * e, s0[2] * e); o.hide_render = e < 0.01


def measure_line(name, a, b, label, color=BRICK, width=0.004, stake_h=0.5, tag_size=(0.16, 0.09), font_size=0.045, up=Vector((0, 0, 1))):
    """A surveyor's line, as a real object: two wooden stakes, a taut red string between their tops and a paper
    tag tied at the middle with the measurement written on it (no floating graphics)."""
    a = Vector(a); b = Vector(b)
    wood_m = pbr(name + "Stake", (0.42, 0.3, 0.17), 0.8)
    stakes = [cyl(name + "StakeA", a + Vector((0, 0, stake_h / 2)), 0.018, stake_h, wood_m, verts=8),
              cyl(name + "StakeB", b + Vector((0, 0, stake_h / 2)), 0.018, stake_h, wood_m, verts=8)]
    ta, tb = a + Vector((0, 0, stake_h - 0.03)), b + Vector((0, 0, stake_h - 0.03))
    line = curve(name + "Line", [ta.lerp(tb, i / 40) - Vector((0, 0, 0.012 * math.sin(math.pi * i / 40) * (tb - ta).length / 10)) for i in range(41)],
                 pbr(name + "StringM", color, 0.7), bevel=width)
    mid = (ta + tb) / 2 - Vector((0, 0, 0.012 * (tb - ta).length / 10))
    d = (tb - ta); ang = math.atan2(d.y, d.x)
    tag = card_plane(name + "Tag", mid - Vector((0, 0, tag_size[1] / 2 + 0.01)), tag_size[0], tag_size[1],
                     paper(name + "TagP", (0.85, 0.8, 0.66), 120), rot=(math.radians(90), 0, ang))
    txt = fact_text(name + "Label", label, mid - Vector((0, 0, tag_size[1] / 2 + 0.018)), font_size, color=(0.08, 0.07, 0.06),
                    rot=(math.radians(90), 0, ang))
    n = d.normalized().cross(Vector((0, 0, 1)))
    txt.location -= n * 0.002; tag.location += n * 0.0005
    return dict(line=line, ticks=stakes, text=txt, tag=tag)


def measure_draw(ms, u):
    """Stakes stand, the string runs from a to b, the tag lands at the end."""
    for tk in ms["ticks"]:
        show(tk, min(1.0, u * 6))
    draw(ms["line"], (u - 0.1) / 0.6)
    show(ms["text"], (u - 0.65) / 0.3); show(ms["tag"], (u - 0.65) / 0.3)


# ------------------------------------------------------------------ object-on-black stage
def void_stage(c, top=(0, 0, 3.2), target=(0, 0, 0.9), energy=320, size=1.2, floor_col=(0.03, 0.03, 0.032), radius=3.0, warm=True):
    """Black world; a dark satin floor that falls off to black away from the pool of light; one hard-ish top light."""
    from common import world_flat
    world_flat((0.0, 0.0, 0.0), 1.0)
    m = pbr("VoidFloor", floor_col, 0.35, **{'Coat Weight': 0.25})
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); gr = N.new("ShaderNodeTexGradient"); gr.gradient_type = 'SPHERICAL'
    mp = N.new("ShaderNodeMapping"); mp.inputs['Scale'].default_value = (1 / radius, 1 / radius, 1)
    L.new(tc.outputs['Object'], mp.inputs['Vector']); L.new(mp.outputs[0], gr.inputs['Vector'])
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'
    mx.inputs[6].default_value = (0, 0, 0, 1); mx.inputs[7].default_value = (*floor_col, 1)
    L.new(gr.outputs['Fac'], mx.inputs['Factor']); L.new(mx.outputs[2], p.inputs['Base Color'])
    fl = box("VoidFloor", (target[0], target[1], -0.01), (40, 40, 0.02), m)
    k = area_light(top, (0, 0, 0), size, energy, (1.0, 0.9, 0.78) if warm else (0.95, 0.96, 1.0))
    point_at(k, target); k.visible_camera = False
    c["void_key"] = k
    B.preview_cap()
    return fl


# ------------------------------------------------------------------ red string (cork-board device, made physical)
def string(name, a, b, sag=0.04, color=(0.55, 0.04, 0.03), n=24):
    a = Vector(a); b = Vector(b)
    pts = [a.lerp(b, i / (n - 1)) - Vector((0, 0, sag * math.sin(math.pi * i / (n - 1)))) for i in range(n)]
    return curve(name, pts, pbr(name + "M", color, 0.7), bevel=0.0025, smooth=True)


def string_sag(o, a, b, sag):
    a = Vector(a); b = Vector(b); sp = o.data.splines[0]; n = len(sp.points)
    for i in range(n):
        p = a.lerp(b, i / (n - 1)) - Vector((0, 0, sag * math.sin(math.pi * i / (n - 1))))
        sp.points[i].co = (p.x, p.y, p.z, 1)


# ------------------------------------------------------------------ map system
# Simplified outline of West Germany (1949-1990), lon/lat. Stylised, not survey-grade.
WG = [(9.4, 54.8), (10.0, 54.55), (10.9, 54.4), (11.1, 54.05), (10.85, 53.9), (10.65, 53.45), (11.3, 53.1), (10.95, 52.8),
      (11.05, 52.35), (10.6, 51.95), (10.6, 51.6), (10.15, 51.3), (9.95, 51.05), (10.1, 50.6), (10.7, 50.38), (11.3, 50.45),
      (11.95, 50.3), (12.3, 50.15), (12.5, 49.95), (12.4, 49.7), (12.95, 49.3), (13.8, 48.8), (13.45, 48.55), (13.0, 48.25),
      (12.9, 47.75), (13.0, 47.5), (12.2, 47.65), (11.1, 47.4), (10.2, 47.3), (9.6, 47.55), (8.6, 47.7), (7.6, 47.58),
      (7.6, 48.2), (8.2, 48.95), (7.4, 49.2), (6.4, 49.45), (6.5, 49.8), (6.1, 50.2), (6.0, 50.8), (5.95, 51.05),
      (6.2, 51.5), (6.0, 51.85), (6.8, 52.1), (7.05, 52.6), (7.2, 53.25), (7.0, 53.6), (8.0, 53.62), (8.6, 53.9),
      (8.95, 54.3), (8.6, 54.9)]
CITIES = {"munich": (11.58, 48.14), "ammersee": (11.1, 48.0), "augsburg": (10.9, 48.37), "nuremberg": (11.08, 49.45),
          "stuttgart": (9.18, 48.78), "frankfurt": (8.68, 50.11), "cologne": (6.96, 50.94), "dusseldorf": (6.78, 51.23),
          "dortmund": (7.47, 51.51), "hanover": (9.73, 52.37), "bremen": (8.8, 53.08), "hamburg": (10.0, 53.55),
          "kiel": (10.13, 54.32), "schlei": (9.93, 54.66), "kassel": (9.48, 51.31), "mannheim": (8.47, 49.49),
          "saarbrucken": (6.99, 49.24), "freiburg": (7.85, 47.99), "regensburg": (12.1, 49.01), "wurzburg": (9.93, 49.79),
          "bonn": (7.1, 50.73), "essen": (7.01, 51.45), "munster": (7.63, 51.96), "kempten": (10.31, 47.73),
          "passau": (13.43, 48.57), "lubeck": (10.69, 53.87), "osnabruck": (8.05, 52.28), "karlsruhe": (8.4, 49.0),
          "ulm": (9.99, 48.4), "bielefeld": (8.53, 52.02), "brunswick": (10.52, 52.27), "gottingen": (9.93, 51.53)}


GEO = "/home/user/Muhammed/nvidia_doc/assets/geo/ne_50m_admin_0_countries"
# the inner-German border (1949-1990), north to south, approximate; everything west of it inside Germany = West Germany
INNER = [(10.75, 54.3), (10.9, 53.95), (10.75, 53.55), (11.25, 53.2), (11.6, 53.05), (11.25, 52.85), (10.95, 52.75),
         (11.05, 52.45), (10.97, 52.15), (10.6, 51.95), (10.62, 51.6), (10.2, 51.35), (9.95, 51.05), (10.1, 50.85),
         (10.05, 50.58), (10.6, 50.35), (11.2, 50.45), (11.6, 50.4), (11.95, 50.3), (12.15, 50.3), (12.3, 50.15)]


def _read_countries():
    """Minimal ESRI shapefile + dBase reader (no extra packages): {name: [rings of (lon, lat)]}."""
    import struct
    with open(GEO + ".dbf", "rb") as f:
        db = f.read()
    nrec, hlen, rlen = struct.unpack("<IHH", db[4:12])
    fields, off = [], 32
    while db[off] != 0x0D:
        nm = db[off:off + 11].split(b"\0")[0].decode(); ln = db[off + 16]
        fields.append((nm, ln)); off += 32
    names = []
    for r in range(nrec):
        o = hlen + r * rlen + 1; row = {}
        for nm, ln in fields:
            row[nm] = db[o:o + ln].decode("latin-1").replace("\x00", "").strip(); o += ln
        names.append(row.get("ADMIN") or row.get("NAME"))
    with open(GEO + ".shp", "rb") as f:
        sh = f.read()
    out, off, i = {}, 100, 0
    while off < len(sh):
        clen = struct.unpack(">I", sh[off + 4:off + 8])[0] * 2; c = off + 8
        st = struct.unpack("<i", sh[c:c + 4])[0]
        if st == 5:
            npart, npt = struct.unpack("<ii", sh[c + 36:c + 44])
            parts = list(struct.unpack(f"<{npart}i", sh[c + 44:c + 44 + 4 * npart])) + [npt]
            pts = np.frombuffer(sh[c + 44 + 4 * npart:c + 44 + 4 * npart + 16 * npt], dtype="<f8").reshape(-1, 2)
            out[names[i]] = [pts[parts[k]:parts[k + 1]] for k in range(npart)]
        off = c + clen; i += 1
    return out


MAP_BOX = (4.6, 15.2, 46.8, 55.4)


def map_png(W=2048, H=2600):
    """A printed paper map of West Germany as an image: pale sea, grey neighbours (incl. the GDR), cream land,
    a dark border, faint graticule, town dots. No names. Real outlines from Natural Earth 1:50m."""
    import os
    from PIL import Image, ImageDraw, ImageFilter
    path = os.path.join(B.GEN, "b_map_wg.png")
    if os.path.exists(path):
        return path
    lon0, lon1, lat0, lat1 = MAP_BOX

    def px(lon, lat):
        return ((lon - lon0) / (lon1 - lon0) * W, (lat1 - lat) / (lat1 - lat0) * H)
    C = _read_countries()
    im = Image.new("RGB", (W, H), (172, 194, 204)); d = ImageDraw.Draw(im)
    for nm, rings in C.items():
        for rg in rings:
            if rg[:, 0].max() < lon0 - 3 or rg[:, 0].min() > lon1 + 3 or rg[:, 1].max() < lat0 - 3 or rg[:, 1].min() > lat1 + 3:
                continue
            d.polygon([px(*p) for p in rg], fill=(192, 191, 184), outline=(150, 148, 140))
    # West Germany = Germany ∩ (west of the inner border)
    gm = Image.new("L", (W, H), 0); ImageDraw.Draw(gm).polygon([px(*p) for rg in C["Germany"] for p in rg[:1]], fill=0)
    gd = ImageDraw.Draw(gm)
    for rg in C["Germany"]:
        gd.polygon([px(*p) for p in rg], fill=255)
    wm = Image.new("L", (W, H), 0)
    ImageDraw.Draw(wm).polygon([px(*p) for p in INNER] + [px(lon1 + 1, INNER[-1][1]), px(lon1 + 1, lat0 - 1), px(lon0 - 1, lat0 - 1),
                                                         px(lon0 - 1, lat1 + 1), px(INNER[0][0], lat1 + 1)], fill=255)
    west = Image.fromarray((np.asarray(gm) & np.asarray(wm)).astype(np.uint8))
    im.paste((240, 232, 210), mask=west)
    for lon in np.arange(5, 16, 1.0):
        d.line([px(lon, lat0), px(lon, lat1)], fill=(196, 192, 182), width=2)
    for lat in np.arange(47, 56, 1.0):
        d.line([px(lon0, lat), px(lon1, lat)], fill=(196, 192, 182), width=2)
    edge = np.asarray(west.filter(ImageFilter.MaxFilter(7))).astype(int) - np.asarray(west.filter(ImageFilter.MinFilter(3))).astype(int)
    im.paste((92, 72, 62), mask=Image.fromarray((edge > 0).astype(np.uint8) * 255))
    for name, (lon, lat) in CITIES.items():
        x, y = px(lon, lat); d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=(70, 60, 55))
    im = im.filter(ImageFilter.GaussianBlur(0.7))
    im.save(path)
    return path


def map_on_desk(c, origin=(0, 0, 0.76), width=0.62):
    """A printed map sheet lying on a wooden incident-room desk, gently curled, lit by whatever the scene adds.
    c['geo'](lon, lat, z) -> world point on the paper."""
    W, H = 2048, 2600
    lon0, lon1, lat0, lat1 = MAP_BOX
    w, h = width, width * H / W
    ox, oy, oz = origin
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=40, y_subdivisions=48, size=1, location=(ox, oy, oz + 0.002))
    sheet = bpy.context.active_object; sheet.name = "MapSheet"; sheet.scale = (w, h, 1)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    for v in sheet.data.vertices:                                   # soft curl at the edges and two fold creases
        x, y = v.co.x / w, v.co.y / h
        v.co.z = 0.012 * max(0.0, abs(x) - 0.38) * 8 + 0.004 * abs(math.sin(y * math.pi * 2)) + 0.002 * (abs(x) < 0.01)
    for f in sheet.data.polygons:
        f.use_smooth = True
    m = pbr("MapPrint", (1, 1, 1), 0.75)
    N = m.node_tree.nodes; L = m.node_tree.links
    tex = N.new("ShaderNodeTexImage"); tex.image = bpy.data.images.load(map_png(), check_existing=True)
    L.new(tex.outputs['Color'], N["Principled BSDF"].inputs['Base Color'])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 300; bm = N.new("ShaderNodeBump"); bm.inputs['Strength'].default_value = 0.05
    L.new(nz.outputs['Fac'], bm.inputs['Height']); L.new(bm.outputs['Normal'], N["Principled BSDF"].inputs['Normal'])
    sheet.data.materials.append(m)
    box("Desk", (ox, oy, oz - 0.025), (w * 2.2, h * 1.6, 0.05), B.tex_mat("DeskOak", "oak_veneer_01", scale=0.6, tint=(0.55, 0.42, 0.3)))

    def geo(lon, lat, z=0.0):
        u = (lon - lon0) / (lon1 - lon0) - 0.5; v = 0.5 - (lat1 - lat) / (lat1 - lat0)
        return Vector((ox + u * w, oy + v * h, oz + 0.003 + z))
    c["geo"] = geo
    c["sheet"] = sheet
    return geo


def push_pin(name, p, color=(0.62, 0.06, 0.04)):
    """A real push pin standing in the paper: a domed head on a short steel needle."""
    head = pbr(name + "Head", color, 0.25, **{'Coat Weight': 0.6})
    parts = [cyl(name + "Needle", Vector(p) + Vector((0, 0, 0.006)), 0.0009, 0.012, pbr("PinSteel", (0.7, 0.7, 0.72), 0.2, 1.0), verts=8),
             cyl(name + "Grip", Vector(p) + Vector((0, 0, 0.016)), 0.004, 0.012, head, verts=16)]
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=0.0065, location=Vector(p) + Vector((0, 0, 0.025)))
    dome = bpy.context.active_object; dome.scale = (1, 1, 0.7); dome.data.materials.append(head); bpy.ops.object.shade_smooth()
    parts.append(dome)
    o = join(parts, name)
    return o


# ------------------------------------------------------------------ stencilled numbers / tags on objects
def stencil(name, s, loc, size, rot, color=(0.85, 0.83, 0.78)):
    return fact_text(name, s, loc, size, color=color, rot=rot, font=FONT_SANS, glow=0.0, extrude=0.0005)


# ------------------------------------------------------------------ procedural fingerprint (seeded; no real person's print)
def fingerprint_png(seed=0, size=512):
    """Dark ridges on a transparent card (RGBA PNG under assets/generated). Whorl/loop-like pattern."""
    import os
    from PIL import Image
    path = os.path.join(B.GEN, f"b_print_{seed}.png")
    if os.path.exists(path):
        return path
    rng = np.random.default_rng(seed + 11)
    y, x = np.mgrid[0:size, 0:size] / size - 0.5
    cx, cy = rng.uniform(-0.05, 0.05), rng.uniform(-0.12, -0.02)
    xx, yy = x - cx, y - cy
    from scipy.ndimage import gaussian_filter
    n = gaussian_filter(rng.standard_normal((size, size)), 8)
    n = n / (np.abs(n).max() + 1e-6)
    # a loop: closed ridges around the core blend into broad arches toward the lower pad
    r = np.sqrt((xx * 1.15) ** 2 + yy ** 2)
    arch = yy * 0.9 + 0.35 * xx ** 2 * rng.uniform(1.5, 3.0)
    w = np.clip((yy + 0.02) / 0.3, 0, 1); w = w * w * (3 - 2 * w)                          # 0 near core .. 1 below (smooth)
    arch = arch + (r - np.abs(arch)) * 0.0
    phase = r * (1 - w) + (np.abs(arch) + np.median(r) * 0.0 + 0.11) * w + 0.012 * n + 0.01 * np.sin(2 * np.arctan2(yy, xx) + rng.uniform(0, 6))
    f = rng.uniform(52, 60)
    ridge = 0.5 + 0.5 * np.sin(2 * np.pi * phase * f)
    ridge = (ridge > 0.62).astype(np.float32)
    pad = (xx / 0.3) ** 2 + ((y - 0.0) / 0.43) ** 2
    ridge *= pad < 1.0
    ridge *= np.clip((1.0 - pad) * 6, 0, 1) > rng.random((size, size)) * 0.6               # ragged edge
    breaks = gaussian_filter(rng.random((size, size)), 1.0) > 0.46                       # pores / breaks
    a = gaussian_filter(ridge * breaks, 0.6)
    img = np.zeros((size, size, 4), np.float32); img[..., :3] = 0.05; img[..., 3] = np.clip(a * 1.3, 0, 1)
    Image.fromarray((img * 255).astype(np.uint8), "RGBA").save(path)
    return path


def print_mat(name, seed, base=(0.86, 0.83, 0.74), ink_col=(0.04, 0.04, 0.045), reveal=None, aspect=1.0, zoom=1.0):
    """Card / tape material with a fingerprint overlay. reveal: a node input you can drive (0..1) to fade the print in."""
    m = pbr(name, base, 0.7)
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tex = N.new("ShaderNodeTexImage"); tex.image = bpy.data.images.load(fingerprint_png(seed), check_existing=True)
    tex.extension = 'CLIP'
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping")
    mp.inputs['Scale'].default_value = (aspect * zoom, zoom, 1)                    # keep the print's proportions on a long strip
    mp.inputs['Location'].default_value = ((1 - aspect * zoom) / 2, (1 - zoom) / 2, 0)
    L.new(tc.outputs['UV'], mp.inputs['Vector']); L.new(mp.outputs[0], tex.inputs['Vector'])
    fac = N.new("ShaderNodeMath"); fac.operation = 'MULTIPLY'; fac.name = "Reveal"; fac.inputs[1].default_value = 1.0
    L.new(tex.outputs['Alpha'], fac.inputs[0])
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'
    mx.inputs[6].default_value = (*base, 1); mx.inputs[7].default_value = (*ink_col, 1)
    L.new(fac.outputs[0], mx.inputs['Factor']); L.new(mx.outputs[2], p.inputs['Base Color'])
    return m


def card_plane(name, loc, w, h, mat, rot_z=0.0, rot=None):
    """A flat card with clean 0..1 UVs (box() UVs crop a texture)."""
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot or (0, 0, rot_z))
    o = bpy.context.active_object; o.name = name; o.scale = (w, h, 1)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(mat)
    return o


def marker_tent(name, loc, num, face_z=0.0, size=0.11):
    """A numbered yellow evidence marker tent (folded card, black number on both faces)."""
    loc = Vector(loc)
    m = pbr(name + "Card", (0.85, 0.65, 0.05), 0.5)
    r = bpy.data.objects.new(name, None); bpy.context.collection.objects.link(r)
    parts = []
    for s_ in (1, -1):
        bpy.ops.mesh.primitive_plane_add(size=1, location=(0, s_ * size * 0.22, size * 0.45), rotation=(s_ * math.radians(-90 + 24), 0, 0))
        p = bpy.context.active_object; p.scale = (size * 0.9, size, 1); p.data.materials.append(m); parts.append(p)
        t = fact_text(name + f"N{s_}", str(num), (0, s_ * size * 0.24, size * 0.42), size * 0.55, color=(0.03, 0.03, 0.03),
                      rot=(s_ * math.radians(90 - 24) if s_ > 0 else math.radians(90 + 24), 0, 0 if s_ < 0 else math.pi), font=FONT_SANS)
        t.location.y += s_ * 0.002; parts.append(t)
    for p in parts:
        p.parent = r
    r.location = loc; r.rotation_euler = (0, 0, face_z)
    return r


def survey_flag(name, loc, h=0.55):
    """A thin stake with a small red-white plastic flag (as used to mark a traced line in the field)."""
    loc = Vector(loc)
    st = cyl(name + "Rod", loc + Vector((0, 0, h / 2)), 0.004, h, pbr("FlagRod", (0.6, 0.6, 0.62), 0.3, 0.8), verts=6)
    fl = box(name + "Flag", loc + Vector((0.045, 0, h - 0.04)), (0.09, 0.002, 0.06), pbr(name + "FlagM", (0.75, 0.08, 0.05), 0.5))
    wh = box(name + "Flag2", loc + Vector((0.045, -0.0012, h - 0.04)), (0.09, 0.001, 0.02), pbr("FlagW", (0.9, 0.9, 0.88), 0.5))
    o = join([st, fl, wh], name)
    return o
