"""The hero object: a generic 1970s-80s golf-ball electric typewriter (no logo, no brand).

Local frame: origin at the centre of the base, on the desk; the typist sits on -Y; +Z up; metres.
    tw = make("TW", loc, rot_z, color=..., bugged=False, text="...")
    type_at(tw, sec, script)    poses everything for time `sec` (keys, ball tilt/turn, strike, carrier step,
                                carriage return, paper feed, the selection arms under the keyboard)

Moving parts are separate objects (keys, carrier, rocker, tilt ring, ball, arms, the paper-feed empty), so
bake.py keys them every frame. The typed text on the paper is revealed by drivers that read the carrier and
paper-feed transforms (no scripts needed), so the page always agrees with where the ball has been.
"""
import os, math
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix
from kit import pbr, box, cyl, brushed_metal, join

GEN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "generated")
MONO = "/usr/share/fonts/truetype/freefont/FreeMono.ttf"
MONO_B = "/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf"

# ---------------------------------------------------------------- geometry constants (metres)
W = 0.40                       # body width
PLATEN_Y, PLATEN_Z, PLATEN_R = 0.045, 0.128, 0.021
BALL_R = 0.0165
BALL_REST_GAP = 0.0035         # ball face to paper at rest; the rocker closes it on a strike
BALL_Y = PLATEN_Y - PLATEN_R - 0.0012 - BALL_REST_GAP - BALL_R
BALL_Z = PLATEN_Z
PAGE_W, PAGE_H = 0.2159, 0.2794
PAGE_LEFT = -PAGE_W / 2
PITCH = 0.00254                # 10 characters per inch
LINE = 0.00423                 # 6 lines per inch
MARGIN = 0.0254                # 1 inch left margin
TOP = 0.03                     # first line 3 cm from the top of the page
DECK = ((-0.19, 0.066), (-0.065, 0.100))       # keyboard slope (y, z) front -> back
BAR_Y, BAR_Z, BAR_L = -0.112, 0.026, 0.355     # the long support bar under the keyboard
ARM_X0, ARM_DX = -0.05, 0.02                   # six selection arms above the bar

LOWER = "abcdefghijklmnopqrstuvwxyz1234567890-=;',./"
UPPER = "ABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%&*()_+:\"?<>"
ROWS = ("1234567890-=", "qwertyuiop", "asdfghjkl;'", "zxcvbnm,./")


def deck_z(y):
    (y0, z0), (y1, z1) = DECK
    return z0 + (z1 - z0) * (y - y0) / (y1 - y0)


DECK_ANG = math.atan2(DECK[1][1] - DECK[0][1], DECK[1][0] - DECK[0][0])


# ---------------------------------------------------------------- mesh helpers
def extrude(name, pts, x0, x1, mat, bevel=0.004, segs=3):
    """Prism from a (y, z) outline extruded along X, with rounded edges."""
    bm = bmesh.new()
    a = [bm.verts.new((x0, y, z)) for y, z in pts]
    b = [bm.verts.new((x1, y, z)) for y, z in pts]
    n = len(pts)
    bm.faces.new(a[::-1]); bm.faces.new(b)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((a[i], a[j], b[j], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o)
    if bevel:
        bv = o.modifiers.new("bevel", 'BEVEL'); bv.width = bevel; bv.segments = segs; bv.limit_method = 'ANGLE'
        bv.angle_limit = math.radians(25); bv.harden_normals = False
    me.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = True
    o.modifiers.new("wn", 'WEIGHTED_NORMAL').keep_sharp = True
    return o


def paper_mesh(name, mat):
    """The sheet: wraps the platen front, leaves it at 25 degrees and leans back. UV = (u, s) in metres:
    u across the page from its left edge, s along the sheet from the print line (+ is up)."""
    r = PLATEN_R + 0.0006; th_t = math.radians(25.0)
    s_lo, s_t, s_hi = -0.06, r * th_t, 0.235
    ss = list(np.linspace(s_lo, s_t, 26)) + list(np.linspace(s_t, s_hi, 30))[1:]
    us = np.linspace(0, PAGE_W, 24)
    def pos(s):
        if s <= s_t:
            th = s / r
            return PLATEN_Y - r * math.cos(th), PLATEN_Z + r * math.sin(th)
        y0, z0 = PLATEN_Y - r * math.cos(th_t), PLATEN_Z + r * math.sin(th_t)
        d = s - s_t
        return y0 + d * math.sin(th_t), z0 + d * math.cos(th_t)
    bm = bmesh.new(); uv = bm.loops.layers.uv.new("UVMap")
    grid = [[bm.verts.new((PAGE_LEFT + u, *pos(s))) for u in us] for s in ss]
    for i in range(len(ss) - 1):
        for j in range(len(us) - 1):
            f = bm.faces.new((grid[i][j], grid[i][j + 1], grid[i + 1][j + 1], grid[i + 1][j]))
            for lp, (ii, jj) in zip(f.loops, ((i, j), (i, j + 1), (i + 1, j + 1), (i + 1, j))):
                lp[uv].uv = (us[jj], ss[ii])
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o)
    me.materials.append(mat)
    return o


# ---------------------------------------------------------------- generated page
def page_image(text, path, dpi=220, seed=3):
    """The typed page (alpha = ink). Lines start TOP from the top edge, MARGIN from the left, 10 pitch."""
    import skia
    from PIL import Image, ImageFilter
    pw, phh = int(8.5 * dpi), int(11 * dpi)
    s = skia.Surface(pw, phh); cv = s.getCanvas(); cv.clear(skia.Color4f(0, 0, 0, 0))
    f = skia.Font(skia.Typeface.MakeFromFile(MONO_B), dpi * 0.165)
    p = skia.Paint(AntiAlias=True)
    rng = np.random.default_rng(seed)
    px_m = dpi / 0.0254
    for li, line in enumerate(text.split("\n")):
        yb = (TOP + li * LINE) * px_m + dpi * 0.05
        for ci, ch in enumerate(line):
            if ch == " ":
                continue
            k = rng.uniform(0.75, 1.0)                     # uneven ribbon impressions
            p.setColor4f(skia.Color4f(0, 0, 0, k))
            x = (MARGIN + ci * PITCH) * px_m - f.measureText(ch) / 2 + rng.uniform(-0.6, 0.6)
            cv.drawString(ch, x, yb + rng.uniform(-0.5, 0.5), f, p)
    a = s.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)
    im = Image.fromarray(a, "RGBA").filter(ImageFilter.GaussianBlur(0.6))
    os.makedirs(os.path.dirname(path), exist_ok=True); im.save(path)
    return path


def paper_material(name, img_path, carrier, feed):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    uvn = N.new("ShaderNodeUVMap"); uvn.uv_map = "UVMap"
    sp = N.new("ShaderNodeSeparateXYZ"); L.new(uvn.outputs[0], sp.inputs[0])
    fv = N.new("ShaderNodeValue"); fv.name = "Feed"
    cu = N.new("ShaderNodeValue"); cu.name = "CarrierU"
    for node, obj, expr in ((fv, feed, "v"), (cu, carrier, f"v - ({PAGE_LEFT})")):
        d = node.outputs[0].driver_add("default_value").driver; d.type = 'SCRIPTED'
        var = d.variables.new(); var.name = "v"; var.type = 'TRANSFORMS'
        var.targets[0].id = obj; var.targets[0].transform_type = 'LOC_Z' if obj is feed else 'LOC_X'
        var.targets[0].transform_space = 'LOCAL_SPACE'
        d.expression = expr
    # page coordinate of this point: w = feed - s (from the page top), image v = 1 - w / H
    w_ = N.new("ShaderNodeMath"); w_.operation = 'SUBTRACT'; L.new(fv.outputs[0], w_.inputs[0]); L.new(sp.outputs[1], w_.inputs[1])
    iv = N.new("ShaderNodeMath"); iv.operation = 'MULTIPLY_ADD'; iv.inputs[1].default_value = -1 / PAGE_H; iv.inputs[2].default_value = 1.0
    L.new(w_.outputs[0], iv.inputs[0])
    iu = N.new("ShaderNodeMath"); iu.operation = 'MULTIPLY'; iu.inputs[1].default_value = 1 / PAGE_W; L.new(sp.outputs[0], iu.inputs[0])
    cmb = N.new("ShaderNodeCombineXYZ"); L.new(iu.outputs[0], cmb.inputs[0]); L.new(iv.outputs[0], cmb.inputs[1])
    tex = N.new("ShaderNodeTexImage"); tex.image = bpy.data.images.load(img_path, check_existing=True); tex.extension = 'CLIP'
    tex.interpolation = 'Cubic'
    L.new(cmb.outputs[0], tex.inputs['Vector'])
    # typed already: lines above the print line, or this line left of the carrier
    up = N.new("ShaderNodeMath"); up.operation = 'GREATER_THAN'; up.inputs[1].default_value = LINE * 0.5; L.new(sp.outputs[1], up.inputs[0])
    ab = N.new("ShaderNodeMath"); ab.operation = 'ABSOLUTE'; L.new(sp.outputs[1], ab.inputs[0])
    onl = N.new("ShaderNodeMath"); onl.operation = 'LESS_THAN'; onl.inputs[1].default_value = LINE * 0.5; L.new(ab.outputs[0], onl.inputs[0])
    lft = N.new("ShaderNodeMath"); lft.operation = 'LESS_THAN'; L.new(sp.outputs[0], lft.inputs[0]); L.new(cu.outputs[0], lft.inputs[1])
    cur = N.new("ShaderNodeMath"); cur.operation = 'MULTIPLY'; L.new(onl.outputs[0], cur.inputs[0]); L.new(lft.outputs[0], cur.inputs[1])
    msk = N.new("ShaderNodeMath"); msk.operation = 'MAXIMUM'; L.new(up.outputs[0], msk.inputs[0]); L.new(cur.outputs[0], msk.inputs[1])
    ink = N.new("ShaderNodeMath"); ink.operation = 'MULTIPLY'; L.new(tex.outputs['Alpha'], ink.inputs[0]); L.new(msk.outputs[0], ink.inputs[1])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 900; L.new(uvn.outputs[0], nz.inputs['Vector'])
    base = N.new("ShaderNodeMapRange"); base.inputs['To Min'].default_value = 0.80; base.inputs['To Max'].default_value = 0.86
    L.new(nz.outputs['Fac'], base.inputs['Value'])
    pc = N.new("ShaderNodeCombineColor"); L.new(base.outputs[0], pc.inputs[0]); L.new(base.outputs[0], pc.inputs[1])
    b2 = N.new("ShaderNodeMath"); b2.operation = 'MULTIPLY'; b2.inputs[1].default_value = 0.95; L.new(base.outputs[0], b2.inputs[0]); L.new(b2.outputs[0], pc.inputs[2])
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; L.new(ink.outputs[0], mx.inputs['Factor'])
    L.new(pc.outputs[0], mx.inputs[6]); mx.inputs[7].default_value = (0.012, 0.012, 0.016, 1)
    L.new(mx.outputs[2], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.85
    p.inputs['Subsurface Weight'].default_value = 0.0
    p.inputs['Transmission Weight'].default_value = 0.0
    try:
        p.inputs['Sheen Weight'].default_value = 0.2
    except Exception:
        pass
    return m


# ---------------------------------------------------------------- materials
def materials(color):
    M = {}
    M["body"] = pbr("TW_Body", color, 0.42, 0.0, **{'Coat Weight': 0.25, 'Coat Roughness': 0.35})
    n = M["body"].node_tree.nodes; l = M["body"].node_tree.links
    tc = n.new("ShaderNodeTexCoord"); nz = n.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 2500; nz.inputs['Detail'].default_value = 3
    l.new(tc.outputs['Object'], nz.inputs['Vector'])
    bp = n.new("ShaderNodeBump"); bp.inputs['Strength'].default_value = 0.06; l.new(nz.outputs['Fac'], bp.inputs['Height'])
    l.new(bp.outputs['Normal'], n["Principled BSDF"].inputs['Normal'])
    M["dark"] = pbr("TW_DarkPlastic", (0.025, 0.026, 0.028), 0.45)
    M["key"] = pbr("TW_Key", (0.72, 0.69, 0.61), 0.32, 0.0, **{'Coat Weight': 0.4, 'Coat Roughness': 0.2})
    M["key_dark"] = pbr("TW_KeyDark", (0.05, 0.055, 0.06), 0.35, 0.0, **{'Coat Weight': 0.4, 'Coat Roughness': 0.2})
    M["legend"] = pbr("TW_Legend", (0.03, 0.03, 0.035), 0.5)
    M["legend_l"] = pbr("TW_LegendLight", (0.75, 0.74, 0.7), 0.5)
    M["chrome"] = pbr("TW_Chrome", (0.86, 0.87, 0.88), 0.12, 1.0)
    M["ball"] = pbr("TW_Ball", (0.80, 0.81, 0.83), 0.2, 1.0)
    M["rubber"] = pbr("TW_Platen", (0.018, 0.018, 0.02), 0.62)
    M["cast"] = brushed_metal("TW_Cast", (0.42, 0.43, 0.45), (0.3, 0.45), 0.3)
    M["steel"] = brushed_metal("TW_Steel", (0.6, 0.61, 0.63), (0.2, 0.32), 0.6)
    M["alu"] = brushed_metal("TW_Alu", (0.72, 0.73, 0.75), (0.22, 0.34), 0.7, axis=(280, 1, 1))
    M["ribbon"] = pbr("TW_Ribbon", (0.01, 0.01, 0.012), 0.3)
    M["magnet"] = pbr("TW_Magnet", (0.05, 0.05, 0.055), 0.3, 0.8)
    M["pcb"] = pbr("TW_PCB", (0.08, 0.16, 0.09), 0.35, 0.0, **{'Coat Weight': 0.8})
    M["chip"] = pbr("TW_Chip", (0.02, 0.02, 0.022), 0.4)
    M["copper"] = pbr("TW_Copper", (0.8, 0.45, 0.25), 0.3, 1.0)
    M["well"] = pbr("TW_Well", (0.07, 0.075, 0.08), 0.5, 0.3)
    return M


def _parent(o, p):
    o.parent = p
    o.matrix_parent_inverse = Matrix.Identity(4)


def _glyph(ch, size, mat, font_path=MONO_B, extrude=0.0003):
    cu = bpy.data.curves.new("g_" + ch, 'FONT'); cu.body = ch; cu.size = size; cu.extrude = extrude
    cu.font = bpy.data.fonts.load(font_path, check_existing=True); cu.align_x = 'CENTER'; cu.align_y = 'CENTER'
    o = bpy.data.objects.new("Glyph", cu); bpy.context.collection.objects.link(o)
    o.data.materials.append(mat)
    return o


# ---------------------------------------------------------------- ball layout
def ball_slot(ch):
    """(row 0..3, column 0..21) on the ball. Lower case on one half, capitals on the other."""
    if ch in LOWER:
        k = LOWER.index(ch); half = 0
    elif ch in UPPER:
        k = UPPER.index(ch); half = 1
    else:
        k = 0; half = 0
    return k // 11, (k % 11) + 11 * half


ROW_LAT = [math.radians(a) for a in (24, 8, -8, -24)]


def ball_angles(ch):
    r, col = ball_slot(ch)
    return -ROW_LAT[r], -col * 2 * math.pi / 22      # tilt about X, rotate about Z (brings the glyph to the platen)


def arm_pattern(ch):
    """Which of the six selection arms move for this character (tilt bits + rotate bits)."""
    r, col = ball_slot(ch)
    rot = col % 11; half = col // 11
    return [r & 1, (r >> 1) & 1, rot & 1, (rot >> 1) & 1, (rot >> 2) & 1, half | ((rot >> 3) & 1)]


# ---------------------------------------------------------------- build
def make(name="TW", loc=(0, 0, 0), rot_z=0.0, color=(0.20, 0.25, 0.30), bugged=False, text="", glyphs=True,
         legends=True, mechanism=True, seed=3):
    M = materials(color)
    c = {"M": M, "bugged": bugged}
    root = bpy.data.objects.new(name, None); bpy.context.collection.objects.link(root)
    c["root"] = root
    shell = []
    # lower case: base and the sloping keyboard deck, the well floor behind it
    (dy0, dz0), (dy1, dz1) = DECK
    lower = extrude(name + "_Lower", [(-0.205, 0.0), (0.205, 0.0), (0.205, 0.075), (0.03, 0.075), (0.03, 0.058),
                                      (-0.052, 0.058), (-0.052, 0.104), (dy1, dz1), (dy0, dz0), (-0.205, 0.05)],
                    -W / 2, W / 2, M["body"], bevel=0.006)
    shell.append(lower)
    # side towers that close the well at the ends of the carrier travel
    for sx in (-1, 1):
        t = extrude(name + "_Side", [(-0.055, 0.05), (0.03, 0.05), (0.03, 0.118), (-0.03, 0.118), (-0.055, 0.104)],
                    sx * 0.178, sx * W / 2, M["body"], bevel=0.005)
        shell.append(t)
    # top cover behind the platen (hinged at the back: c["lid"])
    lid = extrude(name + "_Lid", [(0.07, 0.072), (0.205, 0.072), (0.205, 0.11), (0.192, 0.138), (0.15, 0.152),
                                  (0.095, 0.15), (0.07, 0.132)], -W / 2 + 0.004, W / 2 - 0.004, M["body"], bevel=0.008)
    hinge = bpy.data.objects.new(name + "_LidHinge", None); bpy.context.collection.objects.link(hinge)
    _parent(hinge, root); hinge.location = (0, 0.2, 0.1)
    lid.parent = hinge; lid.matrix_parent_inverse = Matrix.Translation((0, -0.2, -0.1))
    c["lid"] = hinge; shell.append(lid)
    # front scale / margin strip on the well lip, the dark well floor
    box(name + "_Scale", (0, -0.049, 0.1035), (0.35, 0.004, 0.006), M["key"]).parent = root
    box(name + "_WellFloor", (0, -0.011, 0.0595), (0.356, 0.082, 0.003), M["well"])
    for o in shell:
        if o.parent is None:
            _parent(o, root)
    c["shell"] = shell + [lid]
    for o in bpy.data.objects:
        if o.name.startswith(name + "_WellFloor") and o.parent is None:
            _parent(o, root)
    # rubber feet
    for fx in (-0.17, 0.17):
        for fy in (-0.18, 0.18):
            _parent(cyl(name + "_Foot", (fx, fy, 0.003), 0.012, 0.006, M["dark"], verts=16), root)
    # ---------------------------------------------------------------- platen, knobs, paper, bail
    pl = cyl(name + "_Platen", (0, PLATEN_Y, PLATEN_Z), PLATEN_R, 0.43, M["rubber"], verts=48, rot=(0, math.radians(90), 0))
    _parent(pl, root); c["platen"] = pl
    for sx in (-1, 1):
        k = cyl(name + "_Knob", (sx * 0.232, PLATEN_Y, PLATEN_Z), 0.019, 0.026, M["dark"], verts=40, rot=(0, math.radians(90), 0))
        b = k.modifiers.new("bevel", 'BEVEL'); b.width = 0.004; b.segments = 3
        _parent(k, root)
        _parent(cyl(name + "_Hub", (sx * 0.212, PLATEN_Y, PLATEN_Z), 0.008, 0.02, M["chrome"], verts=24, rot=(0, math.radians(90), 0)), root)
    # paper rest behind (a thin chrome wire frame) and the bail across the page
    th = math.radians(25)
    for s_ in (0.055,):
        r = PLATEN_R + 0.004
        y0, z0 = PLATEN_Y - r * math.cos(th), PLATEN_Z + r * math.sin(th)
        _parent(cyl(name + "_Bail", (0, y0 + s_ * math.sin(th) - 0.0035, z0 + s_ * math.cos(th)), 0.0018, 0.33, M["chrome"],
                    verts=12, rot=(0, math.radians(90), 0)), root)
        for bx in (-0.06, 0.06):
            _parent(cyl(name + "_BailRoll", (bx, y0 + s_ * math.sin(th) - 0.0035, z0 + s_ * math.cos(th)), 0.0042, 0.012,
                        M["dark"], verts=16, rot=(0, math.radians(90), 0)), root)
    rest = box(name + "_PaperRest", (0, 0.14, 0.22), (0.25, 0.003, 0.14), M["chrome"], rot=(math.radians(-25), 0, 0))
    _parent(rest, root)
    # ---------------------------------------------------------------- carrier, rocker, tilt ring, ball
    for ry, rz in ((-0.012, 0.066), (0.024, 0.07)):
        _parent(cyl(name + "_Rail", (0, ry, rz), 0.0035, 0.356, M["steel"], verts=16, rot=(0, math.radians(90), 0)), root)
    car = bpy.data.objects.new(name + "_Carrier", None); bpy.context.collection.objects.link(car)
    _parent(car, root); car.location = (PAGE_LEFT + MARGIN, 0, 0)
    c["carrier"] = car
    cb = join([box("cb1", (0, 0.004, 0.077), (0.055, 0.05, 0.022), M["cast"], bevel=0.003),
               box("cb2", (0, -0.006, 0.095), (0.03, 0.022, 0.018), M["cast"], bevel=0.003)], name + "_CarrierBody")
    _parent(cb, car)
    # ribbon cartridge sits on the carrier to the left of the ball; the ribbon runs between ball and paper
    cart = box(name + "_Cartridge", (-0.042, 0.004, 0.1), (0.034, 0.05, 0.016), M["dark"], bevel=0.003)
    _parent(cart, car)
    rib_y = PLATEN_Y - PLATEN_R - 0.0016
    rib = box(name + "_Ribbon", (0.0, rib_y, BALL_Z), (0.026, 0.0004, 0.0072), M["ribbon"])
    _parent(rib, car)
    for gx in (-0.014, 0.014):
        _parent(box(name + "_RibGuide", (gx, rib_y - 0.002, BALL_Z - 0.006), (0.004, 0.006, 0.018), M["chrome"]), car)
    rocker = bpy.data.objects.new(name + "_Rocker", None); bpy.context.collection.objects.link(rocker)
    _parent(rocker, car); rocker.location = (0, BALL_Y, 0.075)            # pivot low in the carrier
    c["rocker"] = rocker
    post = cyl(name + "_Post", (0, 0, (BALL_Z - 0.075) / 2), 0.004, BALL_Z - 0.075 - BALL_R * 0.6, M["chrome"], verts=16)
    _parent(post, rocker)
    tilt = bpy.data.objects.new(name + "_Tilt", None); bpy.context.collection.objects.link(tilt)
    _parent(tilt, rocker); tilt.location = (0, 0, BALL_Z - 0.075)
    c["tilt"] = tilt
    ring = cyl(name + "_TiltRing", (0, 0, -BALL_R * 0.55), 0.007, 0.005, M["cast"], verts=24)
    _parent(ring, tilt)
    ball = bpy.data.objects.new(name + "_Ball", None); bpy.context.collection.objects.link(ball)
    _parent(ball, tilt); c["ball"] = ball
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=BALL_R, location=(0, 0, 0))
    sph = bpy.context.active_object; sph.name = name + "_BallShell"; bpy.ops.object.shade_smooth()
    bm = bmesh.new(); bm.from_mesh(sph.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z > BALL_R * 0.78 or v.co.z < -BALL_R * 0.72], context='VERTS')
    bm.to_mesh(sph.data); bm.free()
    sph.modifiers.new("solid", 'SOLIDIFY').thickness = 0.0012
    sph.data.materials.append(M["ball"]); _parent(sph, ball)
    cap = cyl(name + "_BallCap", (0, 0, BALL_R * 0.78), BALL_R * 0.63, 0.002, M["ball"], verts=48); _parent(cap, ball)
    knob = join([cyl("kb", (0, 0, BALL_R * 0.78 + 0.003), 0.0062, 0.005, M["dark"], verts=24),
                 box("kl", (0, 0, BALL_R * 0.78 + 0.0065), (0.012, 0.0028, 0.0035), M["dark"], bevel=0.001)], name + "_BallKnob")
    _parent(knob, ball)
    if glyphs:
        for chars, half in ((LOWER, 0), (UPPER, 1)):
            for k, ch in enumerate(chars[:44]):
                r, col = k // 11, (k % 11) + 11 * half
                lat = ROW_LAT[r]; lon = col * 2 * math.pi / 22
                d = Vector((-math.sin(lon) * math.cos(lat), math.cos(lon) * math.cos(lat), math.sin(lat)))
                up = Vector((math.sin(lon) * math.sin(lat), -math.cos(lon) * math.sin(lat), math.cos(lat)))
                x = up.cross(d)
                g = _glyph(ch, 0.0042, M["ball"])
                g.matrix_world = Matrix.LocRotScale(d * (BALL_R + 0.0001), Matrix((x, up, d)).transposed().to_quaternion(), (-1, 1, 1))
                mw = g.matrix_world.copy(); g.parent = ball; g.matrix_parent_inverse = Matrix.Identity(4); g.matrix_local = mw
    # ---------------------------------------------------------------- keys
    keys = {}
    ky = [-0.088, -0.108, -0.128, -0.148]
    kx0 = [-0.112, -0.103, -0.098, -0.089]
    for ri, row in enumerate(ROWS):
        for ci, ch in enumerate(row):
            x = kx0[ri] + ci * 0.0195; y = ky[ri]
            keys[ch] = _key(name, ch, x, y, 0.0165, M["key"], M["legend"] if legends else None, root)
    for nm, x, y, w_, dark in (("TAB", -0.137, -0.108, 0.03, True), ("LOCK", -0.132, -0.128, 0.04, True),
                               ("SHIFT", -0.128, -0.148, 0.05, True), ("SHIFTR", 0.118, -0.148, 0.05, True),
                               ("RETURN", 0.126, -0.118, 0.034, True), ("BKSP", 0.13, -0.088, 0.03, True),
                               ("MAR", -0.145, -0.088, 0.02, True), ("IDX", 0.15, -0.108, 0.02, True)):
        keys[nm] = _key(name, nm, x, y, w_, M["key_dark"], None, root)
    keys[" "] = _key(name, " ", 0.0, -0.17, 0.16, M["key"], None, root, depth=0.017)
    c["keys"] = keys
    # on/off rocker switch, right side of the deck
    sw = box(name + "_Switch", (0.168, -0.07, deck_z(-0.07) + 0.006), (0.014, 0.022, 0.008), M["key_dark"], bevel=0.002,
             rot=(DECK_ANG, 0, 0))
    _parent(sw, root)
    # ---------------------------------------------------------------- mechanism inside (seen with covers off or in X-ray)
    mech = []
    if mechanism:
        mech += _mechanism(name, c, M, root, bugged)
    c["mech"] = mech
    # ---------------------------------------------------------------- paper
    feed = bpy.data.objects.new(name + "_PaperFeed", None); bpy.context.collection.objects.link(feed)
    _parent(feed, root); feed.location = (0, 0, TOP)                  # z = page distance of the print line from the page top
    c["feed"] = feed
    txt = text or " "
    img = page_image(txt, os.path.join(GEN, "typewriter", f"{name}_page_{abs(hash(txt)) % 100000}.png"), seed=seed)
    pm = paper_material(name + "_Paper", img, car, feed)
    paper = paper_mesh(name + "_Sheet", pm); _parent(paper, root)
    c["paper"] = paper; c["text"] = text
    root.location = loc; root.rotation_euler = (0, 0, rot_z)
    bpy.context.view_layer.update()
    c["rest"] = {k: Vector(o.location) for k, o in keys.items()}
    return c


def _key(name, ch, x, y, w_, mat, legend_mat, root, depth=0.016):
    """One key: a cap on a short stem, sitting on the deck slope. Its object origin is the cap top centre."""
    z = deck_z(y) + 0.011
    stem = box("stem", (0, 0.0, -0.007), (0.006, 0.006, 0.012), mat)
    cap = box("cap", (0, 0, -0.0035), (w_, depth, 0.008), mat, bevel=0.0025)
    k = join([cap, stem], f"{name}_Key_{ch}")
    k.data = k.data.copy()
    _parent(k, root); k.location = (x, y, z); k.rotation_euler = (DECK_ANG, 0, 0)
    if legend_mat is not None and len(ch) == 1:
        g = _glyph(ch.upper(), 0.0062, legend_mat, font_path="/usr/share/fonts/truetype/freefont/FreeSans.ttf", extrude=0.0)
        _parent(g, k); g.location = (0, 0.0005, 0.00015)
    return k


def _mechanism(name, c, M, root, bugged):
    out = []
    def P(o):
        _parent(o, root); out.append(o); return o
    P(box(name + "_Frame", (0, 0.0, 0.012), (0.37, 0.36, 0.004), M["cast"]))
    for sx in (-0.175, 0.175):
        P(box(name + "_SidePlate", (sx, 0.02, 0.045), (0.004, 0.3, 0.06), M["cast"]))
    P(cyl(name + "_Motor", (-0.12, 0.13, 0.042), 0.026, 0.07, M["steel"], verts=32, rot=(0, math.radians(90), 0)))
    P(cyl(name + "_MotorCap", (-0.081, 0.13, 0.042), 0.02, 0.008, M["dark"], verts=32, rot=(0, math.radians(90), 0)))
    P(cyl(name + "_Pulley", (-0.07, 0.13, 0.042), 0.012, 0.006, M["cast"], verts=24, rot=(0, math.radians(90), 0)))
    P(cyl(name + "_OpShaft", (0, 0.06, 0.03), 0.003, 0.34, M["steel"], verts=12, rot=(0, math.radians(90), 0)))
    P(cyl(name + "_CycShaft", (0, 0.0, 0.04), 0.0035, 0.34, M["steel"], verts=12, rot=(0, math.radians(90), 0)))
    P(cyl(name + "_ArmShaft", (0, -0.06, 0.05), 0.0025, 0.34, M["steel"], verts=12, rot=(0, math.radians(90), 0)))
    # interposers: thin steel blades under every key row
    for k in range(22):
        P(box(name + "_Interposer", (-0.11 + k * 0.0105, -0.115, 0.044), (0.0012, 0.12, 0.008), M["steel"]))
    # the long support bar under the front of the keyboard: a U-channel and a lid (the lid slides off in Ch2)
    bar = P(box(name + "_Bar", (0, BAR_Y, BAR_Z), (BAR_L, 0.022, 0.016), M["alu"], bevel=0.0008))
    bar_lid = box(name + "_BarLid", (0, BAR_Y, BAR_Z + 0.0085), (BAR_L, 0.022, 0.0015), M["alu"])
    P(bar_lid)
    c["bar"] = bar; c["bar_lid"] = bar_lid
    # the six selection arms: steel strips pivoting on the arm shaft, tips over the bar
    arms = []
    for k in range(6):
        pv = bpy.data.objects.new(name + f"_ArmPivot{k}", None); bpy.context.collection.objects.link(pv)
        _parent(pv, root); pv.location = (ARM_X0 + k * ARM_DX, -0.06, 0.05)
        a = box(name + f"_Arm{k}", (0, -0.026, -0.006), (0.004, 0.054, 0.0025), M["steel"], rot=(math.radians(14), 0, 0))
        _parent(a, pv)
        hub = cyl(name + "_ArmHub", (0, 0, 0), 0.0045, 0.006, M["cast"], verts=16, rot=(0, math.radians(90), 0)); _parent(hub, pv)
        tip = cyl(name + f"_ArmTip{k}", (0, -0.052, -0.0125), 0.0028 if bugged else 0.0018, 0.004, M["magnet"] if bugged else M["steel"],
                  verts=16)
        _parent(tip, pv)
        arms.append(pv); out += [a, hub, tip]
    c["arms"] = arms
    # the power switch: a small block with a coil (the altered machine carries one more coil)
    P(box(name + "_SwitchBody", (0.162, -0.07, 0.05), (0.018, 0.02, 0.018), M["dark"], bevel=0.001))
    coils = [cyl(name + "_Coil", (0.162, -0.07 + dy, 0.035), 0.004, 0.009, M["copper"], verts=16) for dy in ((-0.004,) if not bugged else (-0.004, 0.006))]
    for o in coils:
        P(o)
    c["coil_extra"] = coils[-1] if bugged else None
    # inside the bar: the hidden board (altered machines only), sensors under each arm tip
    inside = []
    if bugged:
        inside.append(box(name + "_BugPCB", (0, BAR_Y, BAR_Z - 0.003), (BAR_L - 0.02, 0.016, 0.0012), M["pcb"]))
        rng = np.random.default_rng(7)
        for k in range(16):
            x = -0.16 + k * 0.021 + rng.uniform(-0.002, 0.002)
            w_ = rng.uniform(0.008, 0.016)
            inside.append(box(name + "_BugChip", (x, BAR_Y + rng.uniform(-0.002, 0.002), BAR_Z - 0.0015), (w_, 0.008, 0.0022), M["chip"]))
        for k in range(6):
            inside.append(cyl(name + "_BugSensor", (ARM_X0 + k * ARM_DX, BAR_Y + 0.006, BAR_Z + 0.002), 0.0022, 0.004, M["copper"], verts=12))
        inside.append(cyl(name + "_BugAntenna", (0.06, BAR_Y - 0.004, BAR_Z - 0.0005), 0.0012, 0.18, M["copper"], verts=8,
                          rot=(0, math.radians(90), 0)))
        for o in inside:
            P(o)
    c["bug_parts"] = inside
    return out


# ---------------------------------------------------------------- animation
def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def schedule(text, start=0.0, cps=6.0, cr_time=0.9):
    """Events: (t0, t1, kind, ch, column, line). One per character; a carriage return takes cr_time."""
    ev = []; t = start; col = 0; line = 0
    for ch in text:
        if ch == "\n":
            ev.append((t, t + cr_time, "cr", ch, col, line)); t += cr_time; col = 0; line += 1
        else:
            ev.append((t, t + 1.0 / cps, "space" if ch == " " else "char", ch, col, line)); t += 1.0 / cps; col += 1
    return ev


def type_at(c, sec, text=None, start=0.0, cps=6.0, key_hold=0.35):
    """Pose the typewriter for time `sec` (seconds) while typing `text` from `start`."""
    text = c["text"] if text is None else text
    ev = schedule(text, start, cps)
    car = c["carrier"]; rk = c["rocker"]; tl = c["tilt"]; bl = c["ball"]; feed = c["feed"]
    for k, o in c["keys"].items():
        o.location = c["rest"][k]
    for a in c.get("arms", []):
        a.rotation_euler = (0, 0, 0)
    tilt, rot = 0.0, 0.0                                  # home orientation
    col_pos = 0.0; line_pos = 0.0; strike = 0.0
    pressed = None; press = 0.0; arms_on = None; arm_amt = 0.0
    for (t0, t1, kind, ch, col, line) in ev:
        if sec < t0:
            break
        f = (min(sec, t1) - t0) / (t1 - t0)
        if kind == "cr":
            col_pos = col * (1 - ease(f / 0.8)); line_pos = line + ease(f / 0.8)
            pressed, press = "RETURN", math.sin(math.pi * min(1.0, f / 0.4)) if f < 0.4 else 0.0
            continue
        col_pos = col; line_pos = line
        key = ch.lower() if ch.lower() in c["keys"] else (" " if ch == " " else None)
        if ch in UPPER and ch.lower() not in c["keys"]:
            key = None
        pressed = key; press = math.sin(math.pi * min(1.0, f / key_hold)) if f < key_hold else 0.0
        if kind == "char":
            nt, nr = ball_angles(ch)
            # turn the short way round
            d = (nr - rot + math.pi) % (2 * math.pi) - math.pi
            g = ease((f - 0.05) / 0.38)
            tilt = tilt + (nt - tilt) * g; rot = rot + d * g
            strike = math.sin(math.pi * min(1.0, max(0.0, (f - 0.45) / 0.16))) if 0.45 <= f <= 0.61 else 0.0
            arms_on = arm_pattern(ch); arm_amt = math.sin(math.pi * min(1.0, max(0.0, (f - 0.02) / 0.5))) if f < 0.52 else 0.0
            if f < 0.45:
                arms_on = arms_on
        else:
            strike = 0.0; arm_amt = 0.0
        col_pos = col + ease((f - 0.62) / 0.2)            # escapement: one step after the strike (space bar too)
    car.location.x = PAGE_LEFT + MARGIN + col_pos * PITCH
    feed.location.z = TOP + line_pos * LINE
    rk.rotation_euler = (math.radians(-3.9) * strike, 0, 0)     # the ball swings into the ribbon
    tl.rotation_euler = (tilt, 0, 0)
    bl.rotation_euler = (0, 0, rot)
    if pressed in c["keys"]:
        k = c["keys"][pressed]
        n = Matrix.Rotation(DECK_ANG, 3, 'X') @ Vector((0, 0, -1))
        k.location = c["rest"][pressed] + n * 0.004 * press
    if arms_on:
        for a, on in zip(c.get("arms", []), arms_on):
            a.rotation_euler = (math.radians(-9) * arm_amt * on, 0, 0)
    c["platen"].rotation_euler = (line_pos * 2 * math.pi * LINE / (2 * math.pi * PLATEN_R), math.radians(90), 0)
    bpy.context.view_layer.update()


def strike_point(c):
    """World position of the print point (where the ball meets the paper)."""
    car = c["carrier"]
    return c["root"].matrix_world @ Vector((car.location.x, PLATEN_Y - PLATEN_R, PLATEN_Z))


def world(c, p):
    return c["root"].matrix_world @ Vector(p)


def set_cover(c, open_deg=0.0, hide=False):
    c["lid"].rotation_euler = (math.radians(open_deg), 0, 0)
    for o in c["shell"]:
        o.hide_render = hide
