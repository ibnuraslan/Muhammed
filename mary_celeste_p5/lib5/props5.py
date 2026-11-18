"""Part 5 props and set pieces (new shared assets, built here so nothing in mary_celeste_3d is forked).

  bands(center, radii)       the film's "ripple" device: filled soft orange bands (emissive, soft edges)
  island(center)             Santa Maria (Azores) on the horizon: a low volcanic island, hazed
  slate(...)                 the ship's log slate: wooden frame, dark slate, chalk entry (texture made with PIL)
  package(...), seal(...)    brown-paper parcel with twine and the consul's red wax seal
  reed_organ(...)            a small portable reed organ (melodeon) on its own legs
  doll(...)                  a china-head doll (MakeHuman child body at doll scale, porcelain + cloth dress);
                             broken=True leaves her left forearm off, lying beside her
  stove(...)                 the galley's iron cook stove with its pipe and pots
"""
import os, math
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix
import ship

HERE = os.path.dirname(os.path.abspath(__file__))
try:                                   # Blender's Python ships without Pillow: use the system one (same 3.13 ABI),
    import PIL                         # appended last so Blender's own numpy still wins
except ImportError:
    import sys as _sys, glob as _g
    for _p in _g.glob("/usr/local/lib/python3.13/site-packages") + _g.glob("/usr/lib/python3/dist-packages"):
        if _p not in _sys.path:
            _sys.path.append(_p)
TEX = os.path.join(HERE, "..", "out", "tex")
FONTS = os.path.join(HERE, "..", "..", "mary_celeste", "assets", "fonts")


def _mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    return m, m.node_tree.nodes, m.node_tree.links, m.node_tree.nodes["Principled BSDF"]


# ----------------------------------------------------------------------------- ripple bands
def bands(center, radii, width=3.0, color=(1.0, 0.45, 0.12), strength=2.5, alpha=0.55):
    """Concentric filled bands, soft at both edges (radial gradient), orange. They hover just over the waves."""
    m = bpy.data.materials.new("band"); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial")
    at = N.new("ShaderNodeAttribute"); at.attribute_name = "edge"
    rp = N.new("ShaderNodeMapRange"); rp.inputs['From Min'].default_value = 0.0; rp.inputs['From Max'].default_value = 1.0
    L.new(at.outputs['Fac'], rp.inputs['Value'])
    sm0 = N.new("ShaderNodeMath"); sm0.operation = 'SINE'; L.new(rp.outputs[0], sm0.inputs[0])
    sm = N.new("ShaderNodeMath"); sm.operation = 'POWER'; sm.inputs[1].default_value = 2.0; L.new(sm0.outputs[0], sm.inputs[0])
    sc = N.new("ShaderNodeMath"); sc.operation = 'MULTIPLY'; sc.inputs[1].default_value = alpha; L.new(sm.outputs[0], sc.inputs[0])
    em = N.new("ShaderNodeEmission"); em.inputs['Color'].default_value = (*color, 1); em.inputs['Strength'].default_value = strength
    tr = N.new("ShaderNodeBsdfTransparent")
    mx = N.new("ShaderNodeMixShader"); L.new(sc.outputs[0], mx.inputs[0]); L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], out.inputs['Surface'])
    objs = []
    for r in radii:
        n = 128; V = []; F = []; E = []
        for k in range(n):
            a = 2 * math.pi * k / n
            for j, rr in enumerate((r - width / 2, r, r + width / 2)):
                V.append((center.x + rr * math.cos(a), center.y + rr * math.sin(a), center.z)); E.append((0.0, 0.5, 1.0)[j])
        for k in range(n):
            a0, a1 = k * 3, ((k + 1) % n) * 3
            F.append([a0, a1, a1 + 1, a0 + 1]); F.append([a0 + 1, a1 + 1, a1 + 2, a0 + 2])
        me = bpy.data.meshes.new("band"); me.from_pydata(V, [], F); me.update()
        at_ = me.attributes.new("edge", 'FLOAT', 'POINT'); at_.data.foreach_set("value", [e * math.pi for e in E])
        o = bpy.data.objects.new("band", me); bpy.context.collection.objects.link(o); o.data.materials.append(m)
        o.visible_shadow = False
        objs.append(o)
    return objs


# ----------------------------------------------------------------------------- island
def island(center, length=12000.0, height=500.0, depth=4000.0, seed=3):
    """A low island on the horizon (Santa Maria is ~17 km long, 587 m high): ridge of noise hills, green-brown,
    with aerial haze baked into the material (it sits 10 km off, beyond any volume we could afford)."""
    from mathutils import noise
    nx, ny = 160, 40
    V = []; F = []
    for j in range(ny + 1):
        for i in range(nx + 1):
            u = i / nx; v = j / ny
            x = center.x + (u - 0.5) * length; y = center.y + (v - 0.5) * depth
            prof = math.sin(math.pi * u) ** 1.6 * math.sin(math.pi * v) ** 0.6
            n = noise.noise(Vector((u * 6, v * 3, seed))) * 0.5 + noise.noise(Vector((u * 18, v * 9, seed + 1))) * 0.12
            z = max(-20.0, height * prof * (0.75 + n) - 30)
            V.append((x, y, z))
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            F.append([a, a + 1, a + nx + 2, a + nx + 1])
    me = bpy.data.meshes.new("island"); me.from_pydata(V, [], F); me.update()
    o = bpy.data.objects.new("island", me); bpy.context.collection.objects.link(o)
    m, N, L, p = _mat("island")
    p.inputs['Base Color'].default_value = (0.16, 0.2, 0.12, 1); p.inputs['Roughness'].default_value = 0.95
    # haze: mix toward the horizon colour by a fixed amount (10 km of air)
    em = N.new("ShaderNodeEmission"); em.inputs['Color'].default_value = (0.5, 0.58, 0.7, 1); em.inputs['Strength'].default_value = 0.45
    mx = N.new("ShaderNodeMixShader"); mx.inputs[0].default_value = 0.38
    L.new(p.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], N["Material Output"].inputs['Surface'])
    o.data.materials.append(m)
    for pl in me.polygons:
        pl.use_smooth = True
    return o


# ----------------------------------------------------------------------------- Poly Haven placement helper
def put(aid, at, rot_z=0.0, size=None, axis=2, res="1k"):
    """Import a Poly Haven model and stand it on the point `at` (its lowest point on at.z), optionally scaled so
    its extent along `axis` is `size` metres."""
    import ph
    root, ms = ph.model(aid, res=res)
    lo, hi = ph.bounds(ms); lo, hi = Vector(lo), Vector(hi)
    s = 1.0 if size is None else size / max(1e-6, (hi - lo)[axis])
    c = (lo + hi) / 2
    root.scale = (s, s, s); root.rotation_euler = (0, 0, rot_z)
    bpy.context.view_layer.update()
    lo, hi = ph.bounds(ms); lo, hi = Vector(lo), Vector(hi); c = (lo + hi) / 2
    root.location += Vector((at[0] - c.x, at[1] - c.y, at[2] - lo.z))
    bpy.context.view_layer.update()
    return root, ms


# ----------------------------------------------------------------------------- text textures (PIL)
def text_texture(name, lines, size=(2048, 1536), font="SpecialElite-Regular.ttf", bg=(0, 0, 0, 0), ink=(235, 235, 228, 255),
                 px=110, margin=(120, 140), lead=1.35, chalk=True, seed=1):
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    os.makedirs(TEX, exist_ok=True)
    fp = os.path.join(FONTS, font)
    if not os.path.exists(fp):
        fp = os.path.join(HERE, "..", "..", "nvidia_doc", "assets", "fonts", font)
    im = Image.new("RGBA", size, bg); d = ImageDraw.Draw(im); f = ImageFont.truetype(fp, px)
    rng = np.random.default_rng(seed)
    y = margin[1]
    for ln in lines:
        x = margin[0] + rng.integers(-10, 10)
        for ch in ln:
            d.text((x, y + rng.integers(-4, 5)), ch, font=f, fill=ink)
            x += d.textlength(ch, font=f) * rng.uniform(0.96, 1.04)
        y += int(px * lead)
    if chalk:
        a = np.array(im).astype(np.float32)
        grain = rng.random(a.shape[:2]) ** 0.6
        a[..., 3] *= np.clip(grain * 1.25, 0, 1)
        im = Image.fromarray(a.astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))
    p = os.path.join(TEX, name + ".png"); im.save(p)
    return p


# ----------------------------------------------------------------------------- the log slate
SLATE_TEXT = ["Monday 25th.", "At 5 made the island of", "St. Mary's bearing E.S.E.", "At 8, Eastern point bore", "S.S.W. 6 miles distant."]


def slate(name, at, rot_z=0.0, w=0.36, h=0.27, wet=0.0, text=True):
    """A hinged-free log slate: 8 mm slate in a 22 mm pine frame, lying flat; chalk entry on the face."""
    m, N, L, p = _mat(name + "_slate")
    tc = N.new("ShaderNodeTexCoord")
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 40; nz.inputs['Detail'].default_value = 8
    L.new(tc.outputs['Object'], nz.inputs['Vector'])
    base = N.new("ShaderNodeMix"); base.data_type = 'RGBA'; base.inputs[6].default_value = (0.022, 0.025, 0.028, 1)
    base.inputs[7].default_value = (0.05, 0.055, 0.06, 1); L.new(nz.outputs['Fac'], base.inputs['Factor'])
    col = base.outputs[2]
    if text:
        tp = text_texture(name + "_chalk", SLATE_TEXT)
        ti = N.new("ShaderNodeTexImage"); ti.image = bpy.data.images.load(tp); ti.extension = 'CLIP'
        L.new(tc.outputs['UV'], ti.inputs['Vector'])
        mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; L.new(ti.outputs['Alpha'], mx.inputs['Factor'])
        L.new(col, mx.inputs[6]); mx.inputs[7].default_value = (0.75, 0.75, 0.72, 1); col = mx.outputs[2]
    L.new(col, p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.75 - 0.5 * wet; p.inputs['Coat Weight'].default_value = 0.6 * wet
    R = Matrix.Translation(at) @ Matrix.Rotation(rot_z, 4, 'Z')
    bpy.ops.mesh.primitive_plane_add(size=1)
    o = bpy.context.active_object; o.name = name; o.scale = (w, h, 1); o.data.materials.append(m)
    bpy.ops.object.transform_apply(scale=True)
    so = o.modifiers.new("T", "SOLIDIFY"); so.thickness = 0.008; so.offset = -1
    o.matrix_world = R @ Matrix.Translation((0, 0, 0.012))
    fw = ship.wood("brown_planks_05", 3.0, wet=wet, tint=(1.0, 0.85, 0.65), name=name + "_frame")
    parts = [o]
    for sx, sy, lx, ly in ((0, h / 2 + 0.011, w + 0.044, 0.022), (0, -h / 2 - 0.011, w + 0.044, 0.022),
                           (w / 2 + 0.011, 0, 0.022, h), (-w / 2 - 0.011, 0, 0.022, h)):
        b = ship.box(name + "_fr", (0, 0, 0), (lx, ly, 0.018), fw, bevel=0.003)
        b.matrix_world = R @ Matrix.Translation((sx, sy, 0.009)); parts.append(b)
    # a stub of chalk beside it
    c = ship.cyl(name + "_chalk", Vector((0, 0, 0)), Vector((0.045, 0, 0)), 0.005, mat=None, verts=12)
    cm, _, _, cp = _mat(name + "_chalkm"); cp.inputs['Base Color'].default_value = (0.8, 0.8, 0.76, 1); cp.inputs['Roughness'].default_value = 0.9
    c.data.materials.append(cm); c.matrix_world = R @ Matrix.Translation((w / 2 + 0.06, -h / 2 + 0.02, 0.005)) @ Matrix.Rotation(0.4, 4, 'Z')
    parts.append(c)
    return parts


# ----------------------------------------------------------------------------- galley stove
def stove(name, at, rot_z=0.0, wet=0.0):
    """Ship's cast-iron cook stove: firebox on short legs, a rail round the top, flue up through the deckhead."""
    im = ship.iron(name + "_iron")
    rust = ship.paint(name + "_rust", (0.06, 0.035, 0.022), rough=0.8, grime=0.7, wet=wet, chips=0.4, under=(0.25, 0.1, 0.05))
    R = Matrix.Translation(at) @ Matrix.Rotation(rot_z, 4, 'Z')
    parts = []
    def bx(c, s, m, bev=0.008):
        o = ship.box(name, (0, 0, 0), s, m, bevel=bev); o.matrix_world = R @ Matrix.Translation(c); parts.append(o); return o
    bx((0, 0, 0.45), (0.9, 0.62, 0.62), rust, 0.015)
    bx((0, 0, 0.775), (0.96, 0.68, 0.03), im, 0.006)
    for sx in (-0.4, 0.4):
        for sy in (-0.26, 0.26):
            bx((sx, sy, 0.07), (0.06, 0.06, 0.14), im)
    bx((0.05, -0.315, 0.42), (0.36, 0.02, 0.26), im, 0.004)                       # fire door
    for k, (x, y) in enumerate(((-0.22, 0.0), (0.2, 0.08))):                       # hob lids
        c = ship.cyl(name + "_lid", R @ Vector((x, y, 0.79)), R @ Vector((x, y, 0.8)), 0.12, mat=im, verts=32); parts.append(c)
    fl = ship.cyl(name + "_flue", R @ Vector((0.3, 0.18, 0.8)), R @ Vector((0.3, 0.18, 2.3)), 0.07, mat=rust, verts=24); parts.append(fl)
    for sx in (-1, 1):                                                              # sea rail
        r = ship.cyl(name + "_rail", R @ Vector((sx * 0.5, -0.36, 0.86)), R @ Vector((sx * 0.5, 0.36, 0.86)), 0.008, mat=im, verts=8); parts.append(r)
    for sy in (-1, 1):
        r = ship.cyl(name + "_rail", R @ Vector((-0.5, sy * 0.36, 0.86)), R @ Vector((0.5, sy * 0.36, 0.86)), 0.008, mat=im, verts=8); parts.append(r)
    return parts


def water_floor(name, center, size, depth=0.03, ripple=0.004):
    """Shallow sea water lying on a floor: a thin sheet with small ripples, clear-green, reflective."""
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=120, y_subdivisions=120, size=1)
    o = bpy.context.active_object; o.name = name; o.scale = (size[0], size[1], 1)
    o.location = (center[0], center[1], center[2] + depth)
    tx = bpy.data.textures.new(name + "_rip", 'CLOUDS'); tx.noise_scale = 0.12
    d = o.modifiers.new("Rip", "DISPLACE"); d.texture = tx; d.strength = ripple
    m, N, L, p = _mat(name + "_m")
    p.inputs['Base Color'].default_value = (0.05, 0.07, 0.06, 1); p.inputs['Roughness'].default_value = 0.03
    p.inputs['Transmission Weight'].default_value = 1.0; p.inputs['IOR'].default_value = 1.333
    o.data.materials.append(m)
    bpy.ops.object.shade_smooth()
    return o


def steam(name, at, size=(0.12, 0.12, 0.3), density=1.5):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(at[0], at[1], at[2] + size[2] / 2))
    o = bpy.context.active_object; o.name = name; o.scale = size
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    N.remove(N["Principled BSDF"])
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 4.0; nz.inputs['Detail'].default_value = 3
    L.new(tc.outputs['Generated'], nz.inputs['Vector'])
    sp = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs['Generated'], sp.inputs[0])
    # wisps: thin at the top, thin at the sides
    r = N.new("ShaderNodeMapRange"); r.inputs['From Min'].default_value = 0.5; r.inputs['From Max'].default_value = 0.75
    r.inputs['To Min'].default_value = 0; r.inputs['To Max'].default_value = 1; L.new(nz.outputs['Fac'], r.inputs['Value'])
    fade = N.new("ShaderNodeMath"); fade.operation = 'SUBTRACT'; fade.inputs[0].default_value = 1.0; L.new(sp.outputs['Z'], fade.inputs[1])
    mul = N.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'; L.new(r.outputs[0], mul.inputs[0]); L.new(fade.outputs[0], mul.inputs[1])
    mul2 = N.new("ShaderNodeMath"); mul2.operation = 'MULTIPLY'; mul2.inputs[1].default_value = density; L.new(mul.outputs[0], mul2.inputs[0])
    vol = N.new("ShaderNodeVolumePrincipled"); vol.inputs['Color'].default_value = (0.95, 0.95, 0.95, 1)
    L.new(mul2.outputs[0], vol.inputs['Density']); L.new(vol.outputs[0], N["Material Output"].inputs['Volume'])
    o.data.materials.append(m)
    return o


def mug(name, at, r=0.042, h=0.09, color=(0.82, 0.8, 0.72), rim=(0.05, 0.08, 0.2), fill=(0.09, 0.05, 0.025)):
    """Enamel tin mug with a dark rim and a handle, coffee inside."""
    m, N, L, p = _mat(name)
    tc = N.new("ShaderNodeTexCoord"); sp = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs['Object'], sp.inputs[0])
    gt = N.new("ShaderNodeMath"); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = h - 0.008; L.new(sp.outputs['Z'], gt.inputs[0])
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; L.new(gt.outputs[0], mx.inputs['Factor'])
    mx.inputs[6].default_value = (*color, 1); mx.inputs[7].default_value = (*rim, 1); L.new(mx.outputs[2], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.2; p.inputs['Coat Weight'].default_value = 0.5
    bpy.ops.mesh.primitive_cylinder_add(vertices=40, radius=r, depth=h, location=(0, 0, h / 2))
    o = bpy.context.active_object; o.name = name
    bm = bmesh.new(); bm.from_mesh(o.data)
    top = [f for f in bm.faces if f.normal.z > 0.9]; bmesh.ops.delete(bm, geom=top, context='FACES_ONLY')
    bm.to_mesh(o.data); bm.free()
    so = o.modifiers.new("T", "SOLIDIFY"); so.thickness = 0.002; so.offset = -1
    bv = o.modifiers.new("B", "BEVEL"); bv.width = 0.0015; bv.segments = 2
    o.data.materials.append(m); bpy.ops.object.shade_smooth()
    o.location = at
    bpy.ops.mesh.primitive_torus_add(major_radius=0.019, minor_radius=0.0042, location=(at[0] + r + 0.006, at[1], at[2] + h * 0.55),
                                     rotation=(math.pi / 2, 0, 0))
    hd = bpy.context.active_object; hd.name = name + "_handle"; hd.data.materials.append(m); bpy.ops.object.shade_smooth()
    cm, _, _, cp = _mat(name + "_coffee"); cp.inputs['Base Color'].default_value = (*fill, 1); cp.inputs['Roughness'].default_value = 0.05
    c = ship.cyl(name + "_coffee", Vector(at) + Vector((0, 0, h * 0.7)), Vector(at) + Vector((0, 0, h * 0.7 + 0.001)), r - 0.003, mat=cm, verts=40)
    return [o, hd, c]


# ----------------------------------------------------------------------------- parcels and the consul's seal
def paper_material(name, color=(0.42, 0.3, 0.18), rough=0.85, crease=0.6):
    m, N, L, p = _mat(name)
    tc = N.new("ShaderNodeTexCoord")
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 9; nz.inputs['Detail'].default_value = 6
    L.new(tc.outputs['Object'], nz.inputs['Vector'])
    vo = N.new("ShaderNodeTexVoronoi"); vo.inputs['Scale'].default_value = 7; vo.feature = 'DISTANCE_TO_EDGE'
    L.new(tc.outputs['Object'], vo.inputs['Vector'])
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'OVERLAY'; mx.inputs['Factor'].default_value = 0.35
    mx.inputs[6].default_value = (*color, 1); L.new(nz.outputs['Color'], mx.inputs[7]); L.new(mx.outputs[2], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = rough
    b = N.new("ShaderNodeBump"); b.inputs['Strength'].default_value = crease; b.inputs['Distance'].default_value = 0.002
    L.new(vo.outputs['Distance'], b.inputs['Height']); L.new(b.outputs['Normal'], p.inputs['Normal'])
    return m


def seal_texture():
    """The embossing for the consul's seal: an eagle-ish device is not reproduced; the ring reads
    'CONSULATE OF THE U.S.A. * GIBRALTAR' round a star, as a height map."""
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    os.makedirs(TEX, exist_ok=True)
    S = 1024; im = Image.new("L", (S, S), 0); d = ImageDraw.Draw(im)
    fp = os.path.join(FONTS, "CourierPrime-Bold.ttf"); f = ImageFont.truetype(fp, 64)
    txt = "CONSULATE OF THE U.S.A. * GIBRALTAR * "
    for k, ch in enumerate(txt):
        a = -math.pi / 2 + 2 * math.pi * k / len(txt)
        ci = Image.new("L", (90, 90), 0); ImageDraw.Draw(ci).text((22, 8), ch, font=f, fill=255)
        ci = ci.rotate(-math.degrees(a) - 90, resample=Image.BICUBIC)
        im.paste(255, (int(S / 2 + 370 * math.cos(a) - 45), int(S / 2 + 370 * math.sin(a) - 45)), ci)
    d.ellipse((S / 2 - 300, S / 2 - 300, S / 2 + 300, S / 2 + 300), outline=255, width=14)
    pts = []
    for k in range(10):
        r = 210 if k % 2 == 0 else 85; a = -math.pi / 2 + k * math.pi / 5
        pts.append((S / 2 + r * math.cos(a), S / 2 + r * math.sin(a)))
    d.polygon(pts, fill=255)
    im = im.filter(ImageFilter.GaussianBlur(3)).transpose(Image.FLIP_LEFT_RIGHT)    # UVs run mirrored on the disc
    p = os.path.join(TEX, "seal_height.png"); im.save(p)
    return p


def seal(name, at, normal=(0, 0, 1), r=0.03, rot=0.0):
    """Red sealing wax pressed with the consulate's seal: a blob with an irregular edge and the embossed face."""
    m, N, L, p = _mat(name)
    p.inputs['Base Color'].default_value = (0.32, 0.015, 0.012, 1); p.inputs['Roughness'].default_value = 0.32
    p.inputs['Subsurface Weight'].default_value = 0.2; p.inputs['Coat Weight'].default_value = 0.3
    ti = N.new("ShaderNodeTexImage"); ti.image = bpy.data.images.load(seal_texture()); ti.image.colorspace_settings.name = 'Non-Color'
    ti.extension = 'CLIP'; uv = N.new("ShaderNodeUVMap"); L.new(uv.outputs[0], ti.inputs['Vector'])
    b = N.new("ShaderNodeBump"); b.inputs['Strength'].default_value = 0.9; b.inputs['Distance'].default_value = 0.0008
    L.new(ti.outputs['Color'], b.inputs['Height']); L.new(b.outputs['Normal'], p.inputs['Normal'])
    bpy.ops.mesh.primitive_circle_add(vertices=64, radius=r, fill_type='NGON')
    o = bpy.context.active_object; o.name = name
    bm = bmesh.new(); bm.from_mesh(o.data)
    rng = np.random.default_rng(3)
    for v in bm.verts:
        a = math.atan2(v.co.y, v.co.x); k = 1.0 + 0.12 * math.sin(5 * a + 1) + 0.06 * math.sin(11 * a) + rng.uniform(-0.03, 0.03)
        v.co.x *= k * 1.25; v.co.y *= k * 1.25
    bm.to_mesh(o.data); bm.free()
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.uv.cube_project(cube_size=2.6 * r)
    bpy.ops.object.mode_set(mode='OBJECT')
    so = o.modifiers.new("T", "SOLIDIFY"); so.thickness = 0.005; so.offset = 1
    bv = o.modifiers.new("B", "BEVEL"); bv.width = 0.002; bv.segments = 3; bv.affect = 'EDGES'
    o.data.materials.append(m)
    q = Vector(normal).to_track_quat('Z', 'Y')
    o.matrix_world = Matrix.Translation(at) @ q.to_matrix().to_4x4() @ Matrix.Rotation(rot, 4, 'Z')
    bpy.ops.object.shade_smooth()
    return o


def label_texture(name, lines):
    from PIL import Image
    return text_texture(name, lines, size=(1024, 640), font="CourierPrime-Bold.ttf", bg=(214, 200, 168, 255), ink=(30, 24, 20, 255),
                        px=70, margin=(60, 90), lead=1.4, chalk=False)


def parcel(name, at, size, rot_z=0.0, seal_on=True, label=None, open_top=False, color=(0.42, 0.3, 0.18)):
    """A wooden box wrapped in brown paper, tied with twine both ways, the seal over the knot.
    open_top: the lid off and the paper turned back (the contents are added by the caller, inside)."""
    sx, sy, sz = size
    R = Matrix.Translation(at) @ Matrix.Rotation(rot_z, 4, 'Z')
    pm = paper_material(name + "_paper", color)
    parts = []
    if not open_top:
        b = ship.box(name, (0, 0, 0), size, pm, bevel=0.006); b.matrix_world = R @ Matrix.Translation((0, 0, sz / 2)); parts.append(b)
        tw = ship.tarred_rope(name + "_twine", (0.5, 0.42, 0.28))
        for ax in (0, 1):
            pts = []
            hx, hy = sx / 2 + 0.003, sy / 2 + 0.003
            if ax == 0:
                loop = [(-hx, 0, 0.002), (-hx, 0, sz + 0.003), (hx, 0, sz + 0.003), (hx, 0, 0.002)]
            else:
                loop = [(0, -hy, 0.002), (0, -hy, sz + 0.003), (0, hy, sz + 0.003), (0, hy, 0.002)]
            parts.append(ship.rope(name + "_tw", [R @ Vector(p) for p in loop], 0.0022, tw))
        if seal_on:
            parts.append(seal(name + "_seal", R @ Vector((0, 0, sz + 0.004)), rot=0.3))
        if label:
            lm, N, L, p = _mat(name + "_label")
            ti = N.new("ShaderNodeTexImage"); ti.image = bpy.data.images.load(label_texture(name + "_label", label))
            L.new(ti.outputs['Color'], p.inputs['Base Color']); p.inputs['Roughness'].default_value = 0.8
            bpy.ops.mesh.primitive_plane_add(size=1); lo = bpy.context.active_object; lo.name = name + "_labelq"
            lo.scale = (min(0.16, sx * 0.4), min(0.1, sy * 0.3), 1); lo.data.materials.append(lm)
            lo.matrix_world = R @ Matrix.Translation((sx * 0.22, -sy * 0.22, sz + 0.0015)) @ Matrix.Rotation(0.05, 4, 'Z') @ Matrix.Scale(1, 4)
            lo.scale = (min(0.16, sx * 0.4), min(0.1, sy * 0.3), 1)
            parts.append(lo)
    else:
        wd = ship.wood("brown_planks_05", 2.0, wet=0.0, tint=(1.0, 0.85, 0.65), name=name + "_crate")
        t = 0.014
        for c, s in (((0, 0, t / 2), (sx, sy, t)), ((0, sy / 2 - t / 2, sz / 2), (sx, t, sz)), ((0, -sy / 2 + t / 2, sz / 2), (sx, t, sz)),
                     ((sx / 2 - t / 2, 0, sz / 2), (t, sy, sz)), ((-sx / 2 + t / 2, 0, sz / 2), (t, sy, sz))):
            o = ship.box(name + "_c", (0, 0, 0), s, wd, bevel=0.002); o.matrix_world = R @ Matrix.Translation(c); parts.append(o)
        # brown paper turned back over the sides (a sheet draped out from the rim)
        for sg, (ox, oy, w_, d_) in ((1, (0, sy / 2 + 0.09, sx + 0.1, 0.2)), (-1, (0, -sy / 2 - 0.09, sx + 0.1, 0.2))):
            pa = ship.box(name + "_pp", (0, 0, 0), (w_, d_, 0.002), pm); pa.matrix_world = R @ Matrix.Translation((ox, oy, 0.002)); parts.append(pa)
        tissue = paper_material(name + "_tissue", (0.75, 0.72, 0.64), rough=0.7, crease=1.0)
        ts = ship.box(name + "_tissue", (0, 0, 0), (sx - 2 * t, sy - 2 * t, 0.03), tissue, bevel=0.01)
        tx = bpy.data.textures.new(name + "_crum", 'CLOUDS'); tx.noise_scale = 0.05
        ts.matrix_world = R @ Matrix.Translation((0, 0, sz * 0.35))
        sub = ts.modifiers.new("S", "SUBSURF"); sub.levels = 4; sub.render_levels = 4; sub.subdivision_type = 'SIMPLE'
        dd = ts.modifiers.new("D", "DISPLACE"); dd.texture = tx; dd.strength = 0.02
        parts.append(ts)
    return parts


# ----------------------------------------------------------------------------- Sarah's reed organ
def reed_organ(name, at, rot_z=0.0, lid_open=True):
    """A small portable reed organ (melodeon) of the 1860s: rosewood case 0.72 x 0.32 x 0.2, four octaves of keys
    under a hinged lid, a bellows strap at the back."""
    R = Matrix.Translation(at) @ Matrix.Rotation(rot_z, 4, 'Z')
    case = ship.wood("dark_wooden_planks", 3.5, wet=0.0, tint=(0.55, 0.22, 0.12), name=name + "_rosewood")
    ivory, _, _, ip = _mat(name + "_ivory"); ip.inputs['Base Color'].default_value = (0.78, 0.72, 0.6, 1); ip.inputs['Roughness'].default_value = 0.3
    ebony, _, _, ep = _mat(name + "_ebony"); ep.inputs['Base Color'].default_value = (0.01, 0.008, 0.007, 1); ep.inputs['Roughness'].default_value = 0.25
    felt, _, _, fp = _mat(name + "_felt"); fp.inputs['Base Color'].default_value = (0.25, 0.02, 0.02, 1); fp.inputs['Roughness'].default_value = 1.0
    W_, D_, H_ = 0.72, 0.32, 0.2
    parts = []
    def bx(c, s, m, bev=0.004):
        o = ship.box(name, (0, 0, 0), s, m, bevel=bev); o.matrix_world = R @ Matrix.Translation(c); parts.append(o); return o
    bx((0, 0.04, H_ / 2), (W_, D_ - 0.08, H_), case, 0.006)            # body (bellows chamber behind the keys)
    bx((0, -D_ / 2 + 0.05, 0.035), (W_, 0.1, 0.07), case)               # key bed
    for sx in (-1, 1):
        bx((sx * (W_ / 2 - 0.01), -D_ / 2 + 0.05, 0.075), (0.02, 0.1, 0.07), case)    # cheeks
    bx((0, -D_ / 2 + 0.06, 0.071), (W_ - 0.05, 0.085, 0.004), felt, 0.0)
    nkeys = 29; kw = (W_ - 0.06) / nkeys
    for k in range(nkeys):
        x = -W_ / 2 + 0.03 + kw * (k + 0.5)
        bx((x, -D_ / 2 + 0.055, 0.08), (kw - 0.0015, 0.085, 0.012), ivory, 0.0012)
        if k % 7 not in (2, 6) and k < nkeys - 1:
            bx((x + kw / 2, -D_ / 2 + 0.07, 0.092), (kw * 0.55, 0.05, 0.012), ebony, 0.001)
    # lid: hinged at the back of the key bed, standing open
    lid = bx((0, 0, 0), (W_, 0.11, 0.012), case)
    hinge = Vector((0, -D_ / 2 + 0.1, 0.09))
    ang = math.radians(100 if lid_open else 0)
    lid.matrix_world = R @ Matrix.Translation(hinge) @ Matrix.Rotation(ang, 4, 'X') @ Matrix.Translation((0, -0.055, 0.006))
    # turned knobs (stops) on the fall board
    for k in range(4):
        c = ship.cyl(name + "_stop", R @ Vector((-0.2 + k * 0.13, -D_ / 2 + 0.1, 0.15)), R @ Vector((-0.2 + k * 0.13, -D_ / 2 + 0.07, 0.15)), 0.008, mat=ebony, verts=16)
        parts.append(c)
    return parts


# ----------------------------------------------------------------------------- dolls
def porcelain(name, cheeks=(0.85, 0.45, 0.42)):
    m, N, L, p = _mat(name)
    p.inputs['Base Color'].default_value = (0.86, 0.8, 0.74, 1); p.inputs['Roughness'].default_value = 0.12
    p.inputs['Coat Weight'].default_value = 0.8; p.inputs['Coat Roughness'].default_value = 0.05
    p.inputs['Subsurface Weight'].default_value = 0.15
    return m


def doll(name, at, rot_z=0.0, height=0.36, broken=False, dress=(0.08, 0.16, 0.34), bonnet=(0.6, 0.55, 0.45), seed=0):
    """A china-head doll: MakeHuman child body at doll scale, glazed porcelain, glass-bead eyes, painted
    black hair; a frock and bonnet (lib5.people 'toddler' outfit). Lies face up, head toward +Y (before rot_z).
    broken=True: the left forearm is broken off at the elbow and lies beside her."""
    import people as PP, human as H, poses as P
    p = PP.Person(name, 0.0, 6, muscle=0.5, weight=0.5, height=0.5, outfit="toddler", weather=0.0,
                  hair=dict(beard=False, style="none"), colours=dict(dress=dress, shawl=bonnet))
    h = p.h
    h.body.data.materials[0] = porcelain(name + "_porcelain")
    P.arm_down(h, "L", out=0.18, fwd=0.05, bend=20); P.arm_down(h, "R", out=0.15, fwd=0.03, bend=12)
    P.rest_hand(h, "L", 15); P.rest_hand(h, "R", 15)
    for e in h.eyes:
        e.data.materials.clear()
        em, _, _, ep = _mat(name + "_bead"); ep.inputs['Base Color'].default_value = (0.03, 0.06, 0.16, 1); ep.inputs['Roughness'].default_value = 0.02
        e.data.materials.append(em)
    hb = h.joint("head____head")
    tall = float(np.max(p.rest_co[:, 2])); s = height / tall
    M = (Matrix.Translation(at) @ Matrix.Rotation(rot_z, 4, 'Z') @ Matrix.Translation((0, 0, 0.0)) @
         Matrix.Scale(s, 4) @ Matrix.Rotation(math.radians(-90), 4, 'X'))
    p.finish(look_at=M @ Vector((0, -0.4, 3.0)), place=M, hair=False)
    # lying face up: after the -90 X turn the back is down; drop onto the surface
    objs = p.objects
    lo, hi = H.evaluated_bounds([o for o in objs if o.type == 'MESH'])
    dz = at[2] - lo[2]
    for o in objs:
        if o.parent is None:
            o.location.z += dz
    bpy.context.view_layer.update()
    piece = None
    if broken:
        piece = _break_forearm(p, "L")
    return p, piece


def _break_forearm(p, side):
    """Split the forearm (body + sleeve) off at the elbow and lay it beside the doll, a few cm away."""
    h = p.h
    idx = [i for i, b in enumerate(h.rig.bones) if b.split(".")[0].startswith(("lowerarm", "wrist", "metacarpal", "finger")) and b.endswith("." + side)]
    wv = h.W[:, idx].sum(1)
    sel_parts = []
    for o in [h.body, p.shirt]:
        if o is None:
            continue
        src = list(o["src_verts"]) if "src_verts" in o else None
        w = wv[src] if src is not None else wv[:len(o.data.vertices)]
        bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
        faces = [f for f in bm.faces if all(w[v.index] > 0.5 for v in f.verts)]
        if not faces:
            bm.free(); continue
        dup = bmesh.ops.duplicate(bm, geom=faces)
        nf = [g for g in dup["geom"] if isinstance(g, bmesh.types.BMFace)]
        bmesh.ops.delete(bm, geom=faces, context='FACES')
        # the duplicate goes to its own mesh
        me2 = bpy.data.meshes.new(o.name + "_broken")
        bm2 = bmesh.new()
        vmap = {}
        for f in nf:
            vs = []
            for v in f.verts:
                if v not in vmap:
                    vmap[v] = bm2.verts.new(v.co)
                vs.append(vmap[v])
            try:
                bm2.faces.new(vs)
            except ValueError:
                pass
        bmesh.ops.delete(bm, geom=nf, context='FACES')
        bm.to_mesh(o.data); bm.free(); o.data.update()
        bm2.to_mesh(me2); bm2.free()
        o2 = bpy.data.objects.new(me2.name, me2); bpy.context.collection.objects.link(o2)
        o2.matrix_world = o.matrix_world.copy()
        for m in o.data.materials:
            o2.data.materials.append(m)
        for md in o.modifiers:
            if md.type in ('SUBSURF', 'SOLIDIFY'):
                n = o2.modifiers.new(md.name, md.type)
                for a in ("levels", "render_levels", "thickness", "offset"):
                    if hasattr(md, a):
                        setattr(n, a, getattr(md, a))
        for pl in o2.data.polygons:
            pl.use_smooth = True
        sel_parts.append(o2)
    if not sel_parts:
        return None
    # move the piece out from the body and turn it, so it lies on its own beside her
    import human as H
    lo, hi = H.evaluated_bounds(sel_parts); c = Vector(((lo + hi) / 2).tolist())
    piv = bpy.data.objects.new("forearm_piece", None); bpy.context.collection.objects.link(piv); piv.location = c
    for o in sel_parts:
        mw = o.matrix_world.copy(); o.parent = piv; o.matrix_world = mw
    bpy.context.view_layer.update()
    piv.rotation_euler = (0, 0, math.radians(35))
    piv.location = c + Vector((0.07, -0.03, 0))
    bpy.context.view_layer.update()
    lo, hi = H.evaluated_bounds(sel_parts)
    piv.location.z -= (lo[2] - (c.z - (c.z - lo[2]) if False else lo[2])) * 0
    return piv


# ----------------------------------------------------------------------------- dolls (Sketchfab scans, CC-BY)
DOLLS = {"china": "7c6f3f614592486e9124b0d84e1fde08",        # "China Doll - toy", CMBC (CC-BY)
         "porcelain": "9ce09a8a6b1b45ce90c4479b54b4e003"}    # "A porcelain doll", alicean (CC-BY)


def _split_box(ms, lo_n, hi_n, name):
    """Separate the faces whose centres fall inside a box given in the models' normalised bounds (0..1 per axis)
    into one new object; returns it (or None)."""
    import sketchfab as SF
    lo, hi = SF.bounds(ms); ext = hi - lo
    blo = Vector([lo[i] + ext[i] * lo_n[i] for i in range(3)]); bhi = Vector([lo[i] + ext[i] * hi_n[i] for i in range(3)])
    pieces = []
    for o in ms:
        M = o.matrix_world; bm = bmesh.new(); bm.from_mesh(o.data)
        sel = [f for f in bm.faces if all(blo[i] <= (M @ f.calc_center_median())[i] <= bhi[i] for i in range(3))]
        if not sel:
            bm.free(); continue
        keep = bmesh.new()
        # copy the selected faces into a new mesh (with UVs), delete them from the original
        uvl = bm.loops.layers.uv.active
        vmap = {}; kuv = keep.loops.layers.uv.new("UVMap") if uvl else None
        for f in sel:
            vs = []
            for v in f.verts:
                if v not in vmap:
                    vmap[v] = keep.verts.new(v.co)
                vs.append(vmap[v])
            try:
                nf = keep.faces.new(vs)
            except ValueError:
                continue
            nf.material_index = f.material_index; nf.smooth = f.smooth
            if uvl:
                for l0, l1 in zip(f.loops, nf.loops):
                    l1[kuv].uv = l0[uvl].uv
        bmesh.ops.delete(bm, geom=sel, context='FACES')
        bm.to_mesh(o.data); bm.free(); o.data.update()
        me = bpy.data.meshes.new(name); keep.to_mesh(me); keep.free()
        for m in o.data.materials:
            me.materials.append(m)
        p = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(p); p.matrix_world = M.copy()
        pieces.append(p)
    if not pieces:
        return None
    if len(pieces) > 1:
        bpy.ops.object.select_all(action='DESELECT')
        for p in pieces:
            p.select_set(True)
        bpy.context.view_layer.objects.active = pieces[0]; bpy.ops.object.join()
    return pieces[0]


def doll(name, at, rot_z=0.0, height=0.36, broken=False, kind="china", lie=True, **_):
    """A real antique doll (scan). Lies face up, head toward +Y before rot_z (lie=False: stands).
    broken=True: her left forearm is broken off at the elbow and lies beside her, a few cm out."""
    import sketchfab as SF
    root, ms = SF.model(DOLLS[kind], size=height, axis=2)
    piece = None
    if broken:
        # left forearm + hand of a standing doll facing -Y: her left is +X; elbow ~ 58% height, hand ~ 40%
        piece = _split_box(ms, (0.78, 0.0, 0.40), (1.0, 1.0, 0.585), name + "_forearm")
        if piece:
            ms.append(piece); piece.parent = root; piece.matrix_parent_inverse = root.matrix_world.inverted()
    if lie:
        root.rotation_euler = (math.radians(-90), 0, rot_z)
    else:
        root.rotation_euler = (0, 0, rot_z)
    bpy.context.view_layer.update()
    lo, hi = SF.bounds(ms); c = (lo + hi) / 2
    root.location += Vector((at[0] - c.x, at[1] - c.y, at[2] - lo.z))
    bpy.context.view_layer.update()
    if piece:
        # the broken piece comes away from her side and lies flat on the tissue, turned a little
        mw = piece.matrix_world.copy(); piece.parent = None; piece.matrix_world = mw
        plo, phi = SF.bounds([piece]); pc = (plo + phi) / 2
        ext = phi - plo
        if lie and ext.z > max(ext.x, ext.y):
            # it came away upright: lay it down along her side (long axis horizontal)
            piece.matrix_world = Matrix.Translation(pc) @ Matrix.Rotation(math.radians(-90), 4, 'X') @ Matrix.Translation(-pc) @ piece.matrix_world
            bpy.context.view_layer.update(); plo, phi = SF.bounds([piece]); pc = (plo + phi) / 2
        side = Matrix.Rotation(rot_z, 4, 'Z') @ Vector((1, 0, 0)) if lie else Vector((1, 0, 0))
        R = Matrix.Translation(pc + side * 0.06) @ Matrix.Rotation(math.radians(28), 4, 'Z') @ Matrix.Translation(-pc)
        piece.matrix_world = R @ piece.matrix_world
        plo, phi = SF.bounds([piece]); piece.location.z += at[2] - plo.z
    return root, piece
