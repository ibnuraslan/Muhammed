"""ElectricianPolice v011 stage 2: the world (one street, built so ONE camera can travel through it), props, look.
blender -b people.blend --python 02_set.py -- <src_assets.blend> <logo_dark.png> <logo_white.png> <out_set.blend>

Layout (metres; the road runs along +Y):
  road x -4..4, sidewalks to +-6.5 (0.15 high)
  EAST  (x > 6.5): the POLICE STATION (y -5..5) with a real room behind window W_CAM (y 2.0), shops north and south
  WEST  (x < -6.5): the CONTROL ROOM building (y 0..8, real room behind its big street window at y 2.8), shops south
        the SUBSTATION yard north of it (y 11..34), pylons and lines running west over the rooftops
  poles with wires along both sidewalks; a pole transformer at y 4 on the east side (Ravi glances up at it)."""
import bpy, bmesh, sys, os, math, random
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "lib.py")).read())
a = sys.argv[sys.argv.index("--") + 1:]
SRC, LOGO_D, LOGO_W, OUT = a
random.seed(14)
sc.frame_start, sc.frame_end = 1, 1446
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, 100

# ------------------------------------------------------------------ assets (CC-BY / CC0, see CREDITS.md), appended from the v010 asset library
with bpy.data.libraries.load(SRC, link=False) as (src, dst):
    dst.objects = [n for n in src.objects if n.startswith("SRC_") or n.startswith("StationFan") or n == "ClockRoot"]
LIB = {}
for o in dst.objects:
    if o is None: continue
    LIB[o.name] = o
clock_parts = [o for o in dst.objects if o is not None and (o.name == "ClockRoot" or (o.parent and o.parent.name == "ClockRoot"))]
def inst(name, loc, rot_z=0.0, scale=1.0, newname=None, parent=None):
    s = LIB[name]
    o = s.copy(); o.data = s.data; o.animation_data_clear()
    o.name = newname or name.replace("SRC_", "P_"); sc.collection.objects.link(o)
    o.location = loc; o.rotation_euler = (0, 0, rot_z); o.scale = (scale,) * 3
    o.hide_render = o.hide_viewport = False
    if parent is not None: o.parent = parent
    return o

def soften(o, sat=1.15, rough_min=0.38):
    for m in o.data.materials:
        if not m or not m.use_nodes: continue
        for p in [n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED']:
            p.inputs["Roughness"].default_value = max(rough_min, p.inputs["Roughness"].default_value)

# ------------------------------------------------------------------ materials (deep, saturated, clean)
def plaster(name, col, scale=6.0):
    m = mat(name, col, rough=0.75)
    nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = scale; nz.inputs["Detail"].default_value = 6
    ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.elements[0].color = (*[c * 0.86 for c in col], 1); ramp.color_ramp.elements[1].color = (*[min(1, c * 1.06) for c in col], 1)
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"]); nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"]); nt.links.new(ramp.outputs["Color"], p.inputs["Base Color"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.12; nt.links.new(nz.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], p.inputs["Normal"])
    return m
M = {}
M["asphalt"] = plaster("M_Asphalt", (0.07, 0.075, 0.09), scale=60)
M["line"] = mat("M_RoadLine", (0.95, 0.85, 0.30), rough=0.5)
M["pave"] = tiles("M_Pavers", (0.62, 0.26, 0.14), (0.55, 0.22, 0.12), (0.30, 0.18, 0.12), scale=3.0, w=0.5, h=0.25, rough=0.6, coat=0.0)
M["curb"] = mat("M_Curb", (0.85, 0.82, 0.70), rough=0.6)
M["curb_y"] = mat("M_CurbYellow", (0.95, 0.70, 0.05), rough=0.5)
M["frame"] = mat("M_WinFrame", (0.95, 0.93, 0.86), rough=0.4)
M["dark"] = mat("M_ShopDark", (0.05, 0.04, 0.04), rough=0.8)
M["glass"] = mat("M_Glass", (0.30, 0.50, 0.60), rough=0.08, spec=0.6)
M["metal"] = mat("M_Metal", (0.55, 0.57, 0.60), rough=0.35, metal=0.9)
M["blackm"] = mat("M_BlackMetal", (0.03, 0.03, 0.035), rough=0.4, metal=0.6)
M["wood"] = wood("M_Wood", (0.40, 0.18, 0.07), (0.25, 0.10, 0.04))
M["concrete"] = plaster("M_Pole", (0.62, 0.60, 0.56), scale=20)
M["wire"] = mat("M_Wire", (0.02, 0.02, 0.02), rough=0.5)
M["insul"] = mat("M_Insulator", (0.75, 0.30, 0.12), rough=0.25, coat=0.5)
M["tank"] = mat("M_WaterTank", (0.03, 0.03, 0.04), rough=0.5)
M["gravel"] = plaster("M_Gravel", (0.38, 0.36, 0.33), scale=90)
WALLS = [(0.02, 0.45, 0.50), (0.70, 0.22, 0.10), (0.85, 0.55, 0.05), (0.40, 0.12, 0.50), (0.85, 0.30, 0.45), (0.10, 0.40, 0.75), (0.20, 0.55, 0.25), (0.90, 0.75, 0.55)]
AWN = [(0.85, 0.05, 0.05), (0.05, 0.35, 0.80), (0.95, 0.60, 0.0), (0.05, 0.55, 0.30), (0.60, 0.05, 0.55)]

# ------------------------------------------------------------------ ground
def plane(name, x0, x1, y0, y1, z, material, cuts=0):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    vs = [bm.verts.new((x0, y0, z)), bm.verts.new((x1, y0, z)), bm.verts.new((x1, y1, z)), bm.verts.new((x0, y1, z))]
    bm.faces.new(vs)
    if cuts: bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=cuts, use_grid_fill=True)
    bm.to_mesh(me); bm.free(); o = bpy.data.objects.new(name, me); sc.collection.objects.link(o); me.materials.append(material)
    return o
Y0, Y1 = -70.0, 90.0
plane("Road", -4.0, 4.0, Y0, Y1, 0.0, M["asphalt"])
for k in range(int((Y1 - Y0) / 6)):
    y = Y0 + k * 6 + 1
    box("RoadDash%d" % k, (0.14, 3.0, 0.004), (0, y + 1.5, 0.002), M["line"], bevel=0)
for sx in (1, -1):
    box("Sidewalk_%d" % sx, (2.5, Y1 - Y0, 0.15), (sx * 5.25, (Y0 + Y1) / 2, 0.075), M["pave"], bevel=0.0)
    box("Curb_%d" % sx, (0.14, Y1 - Y0, 0.16), (sx * 4.07, (Y0 + Y1) / 2, 0.08), M["curb"], bevel=0.01)
    for k in range(int((Y1 - Y0) / 1.0)):
        if k % 2: box("CurbP_%d_%d" % (sx, k), (0.145, 0.5, 0.165), (sx * 4.07, Y0 + k * 1.0 + 0.5, 0.083), M["curb_y"], bevel=0.0)
plane("Ground_far", -400, 400, -400, 400, -0.02, plaster("M_Dirt", (0.55, 0.36, 0.18), scale=3))

# ------------------------------------------------------------------ building kit
def window(name, x, y, z, w, h, face, wall_m, shutter_col=None, lit=None, parent=None, glass=True, mullion=True):
    """a framed window on a facade facing `face` (+1: +x, -1: -x); returns the glass/emitter object"""
    fx = x + face * 0.06
    objs = []
    objs.append(box(name + "_fr_t", (0.10, w + 0.12, 0.06), (fx, y, z + h / 2 + 0.03), M["frame"], bevel=0.008))
    objs.append(box(name + "_fr_b", (0.16, w + 0.20, 0.06), (fx + face * 0.03, y, z - h / 2 - 0.03), M["frame"], bevel=0.008))
    objs.append(box(name + "_fr_l", (0.10, 0.06, h), (fx, y - w / 2 - 0.03, z), M["frame"], bevel=0.008))
    objs.append(box(name + "_fr_r", (0.10, 0.06, h), (fx, y + w / 2 + 0.03, z), M["frame"], bevel=0.008))
    if mullion: objs.append(box(name + "_fr_m", (0.06, 0.04, h), (fx, y, z), M["frame"], bevel=0.005))
    g = None
    if glass:
        g = box(name + "_gl", (0.02, w, h), (x + face * 0.01, y, z), lit if lit is not None else M["glass"], bevel=0)
        objs.append(g)
    if shutter_col is not None:
        sm = mat("M_Shut_%s" % name, shutter_col, rough=0.5)
        for s_ in (-1, 1):
            objs.append(box(name + "_sh%d" % s_, (0.04, w / 2, h), (fx + face * 0.02, y + s_ * (w * 0.75 + 0.06), z), sm, bevel=0.01))
    if parent is not None:
        for o in objs: o.parent = parent
    return g

def awning(name, x, y, w, z, face, col):
    """a sloped fabric awning with stripes and a scalloped valance"""
    m = bpy.data.materials.new("M_" + name); m.use_nodes = True; nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); wv = nt.nodes.new("ShaderNodeTexWave"); wv.wave_profile = 'SAW'
    wv.inputs["Scale"].default_value = 3.0; wv.bands_direction = 'Y'
    ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.interpolation = 'CONSTANT'
    ramp.color_ramp.elements[0].color = (*col, 1); ramp.color_ramp.elements[1].position = 0.5; ramp.color_ramp.elements[1].color = (0.95, 0.93, 0.85, 1)
    nt.links.new(tc.outputs["Object"], wv.inputs["Vector"]); nt.links.new(wv.outputs["Fac"], ramp.inputs["Fac"]); nt.links.new(ramp.outputs["Color"], p.inputs["Base Color"])
    p.inputs["Roughness"].default_value = 0.8; p.inputs["Sheen Weight"].default_value = 0.3
    d = 1.3
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    v = [bm.verts.new((x, y - w / 2, z)), bm.verts.new((x, y + w / 2, z)), bm.verts.new((x + face * d, y + w / 2, z - 0.55)), bm.verts.new((x + face * d, y - w / 2, z - 0.55))]
    bm.faces.new(v); bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=10, use_grid_fill=True)
    for vv in bm.verts:
        t = abs(vv.co.x - x) / d; vv.co.z -= 0.08 * math.sin(math.pi * t)
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o); me.materials.append(m)
    so = o.modifiers.new("s", 'SOLIDIFY'); so.thickness = 0.015
    for p_ in me.polygons: p_.use_smooth = True
    # valance
    me2 = bpy.data.meshes.new(name + "_val"); bm = bmesh.new(); n = int(w / 0.25)
    top = []; bot = []
    for k in range(n * 4 + 1):
        yy = y - w / 2 + w * k / (n * 4)
        top.append(bm.verts.new((x + face * d, yy, z - 0.55)))
        bot.append(bm.verts.new((x + face * d, yy, z - 0.72 + 0.06 * abs(math.sin(math.pi * k / 4)))))
    for k in range(n * 4):
        bm.faces.new((top[k], top[k + 1], bot[k + 1], bot[k]))
    bm.to_mesh(me2); bm.free()
    o2 = bpy.data.objects.new(name + "_val", me2); sc.collection.objects.link(o2); me2.materials.append(m)
    so = o2.modifiers.new("s", 'SOLIDIFY'); so.thickness = 0.01
    return o

def signboard(name, x, y, z, w, h, face, col, emblem=None):
    b = box(name, (0.08, w, h), (x + face * 0.06, y, z), mat("M_" + name, col, rough=0.4, coat=0.3), bevel=0.02)
    bo = box(name + "_border", (0.06, w + 0.08, h + 0.08), (x + face * 0.03, y, z), mat("M_" + name + "_b", (0.95, 0.85, 0.2), rough=0.3, metal=0.6), bevel=0.02)
    return b

def logo_plane(name, path, center, size_w, face_dir, up=(0, 0, 1), emit=0.0):
    img = bpy.data.images.load(path); aspect = img.size[1] / img.size[0]
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    hw, hh = size_w / 2, size_w * aspect / 2
    vs = [bm.verts.new((-hw, -hh, 0)), bm.verts.new((hw, -hh, 0)), bm.verts.new((hw, hh, 0)), bm.verts.new((-hw, hh, 0))]
    f = bm.faces.new(vs); uv = bm.loops.layers.uv.new()
    for l, c in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): l[uv].uv = c
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o)
    m = bpy.data.materials.new("M_" + name); m.use_nodes = True; nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = img; tx.extension = 'CLIP'; tx.interpolation = 'Cubic'
    nt.links.new(tx.outputs["Color"], p.inputs["Base Color"]); nt.links.new(tx.outputs["Alpha"], p.inputs["Alpha"])
    p.inputs["Roughness"].default_value = 0.5
    if emit:
        nt.links.new(tx.outputs["Color"], p.inputs["Emission Color"]); p.inputs["Emission Strength"].default_value = emit
    me.materials.append(m)
    z = Vector(face_dir).normalized(); yv = Vector(up); yv = (yv - z * yv.dot(z)).normalized(); xv = yv.cross(z)
    o.matrix_world = Matrix((xv, yv, z)).transposed().to_4x4(); o.location = center
    return o, aspect

def building(name, x_face, face, y0, y1, height, wall_col, floors=2, shop=True, awn_col=None, sign_col=None, depth=8.0, rooftank=True, ac=True):
    """a street building: plaster body, ground-floor shop (dark recess + goods or a roller shutter), awning, blank sign,
    framed upper windows with shutters, a balcony, parapet, AC unit, rooftop water tank"""
    w = y1 - y0; yc = (y0 + y1) / 2
    xc = x_face - face * depth / 2
    wm = plaster("M_" + name, wall_col)
    body = box(name, (depth, w - 0.06, height), (xc, yc, height / 2), wm, bevel=0.0)
    trim = mat("M_%s_trim" % name, tuple(min(1, c * 0.6 + 0.35) for c in wall_col), rough=0.5)
    box(name + "_band", (0.12, w, 0.18), (x_face + face * 0.06, yc, 3.3), trim, bevel=0.01)
    box(name + "_parapet", (0.25, w, 0.35), (x_face + face * 0.02, yc, height + 0.17), trim, bevel=0.02)
    if shop:
        if random.random() < 0.6:
            box(name + "_recess", (0.2, w - 1.2, 2.5), (x_face + face * 0.02, yc, 1.4), M["dark"], bevel=0)
            for k in range(int((w - 1.6) / 0.7)):
                gy = y0 + 0.9 + k * 0.7
                c_ = random.choice([(0.9, 0.1, 0.05), (0.95, 0.75, 0.05), (0.2, 0.6, 0.1), (0.95, 0.45, 0.05), (0.1, 0.3, 0.8)])
                box(name + "_goods%d" % k, (0.5, 0.6, 0.35), (x_face + face * 0.35, gy, 0.42), mat("M_%s_g%d" % (name, k), c_, rough=0.6), bevel=0.04)
                cyl(name + "_fruit%d" % k, 0.22, 0.12, (x_face + face * 0.35, gy, 0.66), mat("M_%s_f%d" % (name, k), c_, rough=0.4), verts=16, bevel=0.03)
        else:
            for k in range(max(1, int((w - 1.2) / 1.1))):
                inst("SRC_shutter", (x_face + face * 0.1, y0 + 0.9 + k * 1.1 + 0.5, 0.15), rot_z=(math.pi / 2 if face < 0 else -math.pi / 2), newname=name + "_shutter%d" % k)
        if awn_col: awning(name + "_awning", x_face, yc, w - 0.8, 3.05, face, awn_col)
        if sign_col: signboard(name + "_sign", x_face, yc, 3.75, w - 1.4, 0.65, face, sign_col)
    for fl in range(1, floors):
        zc = 3.3 + (fl - 1) * 3.1 + 1.55
        nwin = max(1, int(w / 2.6))
        for k in range(nwin):
            wy = y0 + (k + 0.5) * w / nwin
            window(name + "_w%d_%d" % (fl, k), x_face, wy, zc, 1.0, 1.25, face, wm, shutter_col=random.choice(AWN))
        if fl == 1 and random.random() < 0.6:
            by = yc; bw = min(3.0, w - 1.0)
            box(name + "_balc", (0.9, bw, 0.12), (x_face + face * 0.45, by, zc - 0.95), trim, bevel=0.02)
            for k in range(int(bw / 0.12)):
                cyl(name + "_bal%d" % k, 0.012, 0.85, (x_face + face * 0.85, by - bw / 2 + 0.06 + k * 0.12, zc - 0.47), M["blackm"], verts=8)
            box(name + "_balrail", (0.05, bw, 0.05), (x_face + face * 0.85, by, zc - 0.03), M["blackm"], bevel=0.01)
        if ac and random.random() < 0.5:
            inst("SRC_aircon", (x_face + face * 0.2, y0 + 0.7, zc - 0.9), rot_z=(math.pi / 2 if face < 0 else -math.pi / 2), scale=0.8, newname=name + "_ac%d" % fl)
    if rooftank:
        cyl(name + "_tank", 0.55, 1.1, (xc, yc, height + 0.55), M["tank"], verts=24, bevel=0.02)
    box(name + "_pipe", (0.08, 0.08, height), (x_face + face * 0.05, y0 + 0.15, height / 2), mat("M_Pipe", (0.85, 0.85, 0.82), rough=0.4), bevel=0.01)
    return body

# EAST side (face -x at x = 6.5)
EX = 6.5
east = [(-46, -38), (-38, -31), (-31, -24), (-24, -17), (-17, -11), (-11, -5.2), (5.2, 11), (11, 18), (18, 25), (25, 33), (33, 41), (41, 50)]
for i, (y0, y1) in enumerate(east):
    building("BE%d" % i, EX, -1, y0, y1, random.choice([7.0, 7.6, 10.1]), WALLS[i % len(WALLS)], floors=random.choice([2, 3]),
             awn_col=AWN[i % len(AWN)], sign_col=random.choice(AWN))
# WEST side (face +x at x = -6.5): shops south of the control room, one block north of the yard
WX = -6.5
west = [(-46, -39), (-39, -32), (-32, -25), (-25, -18), (-18, -11), (-11, -4.5), (36, 43), (43, 50)]
for i, (y0, y1) in enumerate(west):
    building("BW%d" % i, WX, 1, y0, y1, random.choice([7.0, 7.6, 10.1]), WALLS[(i + 3) % len(WALLS)], floors=random.choice([2, 3]),
             awn_col=AWN[(i + 2) % len(AWN)], sign_col=random.choice(AWN))
# far backdrop rows (rooftops seen from the crane): simple-but-detailed blocks with parapets and tanks
for k in range(40):
    bx = -random.uniform(18, 90); by = random.uniform(-60, 80)
    if -32 < bx and 8 < by < 36: continue
    h = random.choice([4.5, 7.0, 7.0, 10.0])
    bw_, bd_ = random.uniform(5, 9), random.uniform(5, 9)
    col = WALLS[k % len(WALLS)]
    box("Town%d" % k, (bd_, bw_, h), (bx, by, h / 2), plaster("M_Town%d" % k, col), bevel=0)
    box("Town%d_par" % k, (bd_ + 0.2, bw_ + 0.2, 0.3), (bx, by, h + 0.15), mat("M_Town%d_p" % k, tuple(min(1, c * 0.6 + 0.35) for c in col)), bevel=0.02)
    if random.random() < 0.6: cyl("Town%d_tank" % k, 0.5, 1.0, (bx + 1, by, h + 0.5), M["tank"], verts=16)
for k in range(30):
    bx = random.uniform(16, 60); by = random.uniform(-60, 80); h = random.choice([4.5, 7.0, 10.0])
    bw_, bd_ = random.uniform(5, 9), random.uniform(5, 9); col = WALLS[(k + 2) % len(WALLS)]
    box("TownE%d" % k, (bd_, bw_, h), (bx, by, h / 2), plaster("M_TownE%d" % k, col), bevel=0)

# ------------------------------------------------------------------ the POLICE STATION (east, y -5..5), a real room behind window W_CAM
SY0, SY1 = -5.0, 5.0
st_m = plaster("M_Station", (0.93, 0.90, 0.80)); st_blue = mat("M_StationBlue", (0.04, 0.12, 0.55), rough=0.45); st_red = mat("M_StationRed", (0.70, 0.04, 0.04), rough=0.5)
ROOM = dict(x0=EX + 0.25, x1=EX + 5.2, y0=SY0 + 0.25, y1=SY1 - 0.25, h=3.2)
# facade wall with openings: door (y -1.0..0.4), window W_CAM (y 1.2..3.0, z 0.95..2.35), window W2 (y -3.8..-2.4)
def wall_with_holes(name, x, y0, y1, z0, z1, holes, material, th=0.25, face=-1):
    """a wall in the plane x (thickness th, into +x) with rectangular holes [(ya, yb, za, zb)]"""
    ys = sorted({y0, y1} | {h[0] for h in holes} | {h[1] for h in holes}); zs = sorted({z0, z1} | {h[2] for h in holes} | {h[3] for h in holes})
    parts = []
    for i in range(len(ys) - 1):
        for j in range(len(zs) - 1):
            ya, yb, za, zb = ys[i], ys[i + 1], zs[j], zs[j + 1]
            cy, cz = (ya + yb) / 2, (za + zb) / 2
            if any(h[0] <= cy <= h[1] and h[2] <= cz <= h[3] for h in holes): continue
            parts.append(box("%s_%d_%d" % (name, i, j), (th, yb - ya, zb - za), (x + th / 2 * (-face), cy, cz), material, bevel=0))
    bpy.ops.object.select_all(action='DESELECT')
    for p in parts: p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]; bpy.ops.object.join(); parts[0].name = name
    bm = bmesh.new(); bm.from_mesh(parts[0].data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4); bm.to_mesh(parts[0].data); bm.free()
    return parts[0]
W_CAM = (1.15, 3.05, 0.95, 2.40)
W_ST2 = (-3.9, -2.4, 1.0, 2.3)
DOOR = (-1.1, 0.3, 0.15, 2.4)
UP = [(-3.9, -2.4, 4.3, 5.6), (-0.9, 0.6, 4.3, 5.6), (1.6, 3.1, 4.3, 5.6)]
wall_with_holes("Station_front", EX, SY0, SY1, 0.0, 7.2, [W_CAM, W_ST2, DOOR] + UP, st_m)
box("Station_body", (7.5, SY1 - SY0, 7.2), (EX + 0.25 + 3.75 + 5.0, 0, 3.6), st_m, bevel=0)    # the block behind the room
box("Station_sideN", (5.0, 0.25, 7.2), (EX + 2.75, SY1 - 0.125, 3.6), st_m, bevel=0)
box("Station_sideS", (5.0, 0.25, 7.2), (EX + 2.75, SY0 + 0.125, 3.6), st_m, bevel=0)
box("Station_back", (0.25, SY1 - SY0, 7.2), (ROOM["x1"] + 0.125, 0, 3.6), plaster("M_StationIn", (0.18, 0.42, 0.55)), bevel=0)
box("Station_ceil", (5.0, SY1 - SY0, 0.25), (EX + 2.75, 0, ROOM["h"] + 0.125), plaster("M_StationCeil", (0.85, 0.85, 0.80)), bevel=0)
box("Station_upper_floor", (5.0, SY1 - SY0, 0.2), (EX + 2.75, 0, 3.75), st_m, bevel=0)
box("Station_floor", (ROOM["x1"] - ROOM["x0"], SY1 - SY0 - 0.5, 0.05), ((ROOM["x0"] + ROOM["x1"]) / 2, 0, 0.025), tiles("M_StFloor", (0.55, 0.50, 0.42), (0.45, 0.40, 0.33), (0.3, 0.27, 0.22), scale=1.5, w=0.5, h=0.5), bevel=0)
# interior wall paint (inside faces of the front and sides): thin inner skins
in_m = plaster("M_StationIn", (0.18, 0.42, 0.55))
box("Station_inN", (ROOM["x1"] - ROOM["x0"], 0.02, ROOM["h"]), ((ROOM["x0"] + ROOM["x1"]) / 2, SY1 - 0.26, ROOM["h"] / 2), in_m, bevel=0)
box("Station_inS", (ROOM["x1"] - ROOM["x0"], 0.02, ROOM["h"]), ((ROOM["x0"] + ROOM["x1"]) / 2, SY0 + 0.26, ROOM["h"] / 2), in_m, bevel=0)
box("Station_band", (0.14, SY1 - SY0, 0.35), (EX - 0.07, 0, 3.45), st_blue, bevel=0.01)
box("Station_band2", (0.14, SY1 - SY0, 0.10), (EX - 0.07, 0, 0.08), st_red, bevel=0.0)
box("Station_parapet", (0.3, SY1 - SY0 + 0.2, 0.45), (EX - 0.05, 0, 7.4), st_blue, bevel=0.02)
signboard("Station_sign", EX, 0.0, 6.55, 4.6, 0.75, -1, (0.04, 0.12, 0.55))
# a generic star emblem (no text) on the sign, gold
def star(name, c, r0, r1, n=5, face=-1, th=0.03, material=None):
    me = bpy.data.meshes.new(name); bm = bmesh.new(); pts = []
    for k in range(n * 2):
        r = r1 if k % 2 == 0 else r0; a_ = math.pi / 2 + k * math.pi / n
        pts.append(bm.verts.new((0, r * math.cos(a_), r * math.sin(a_))))
    bm.faces.new(pts); bmesh.ops.extrude_face_region(bm, geom=bm.faces[:])
    for v in bm.verts:
        if abs(v.co.x) < 1e-6 and v.select: pass
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o); me.materials.append(material)
    so = o.modifiers.new("s", 'SOLIDIFY'); so.thickness = th
    o.location = c; return o
gold = mat("M_Gold", (1.0, 0.72, 0.15), rough=0.25, metal=1.0)
star("Station_star", (EX - 0.14, 0, 6.55), 0.11, 0.27, material=gold)
cyl("Station_starRing", 0.33, 0.02, (EX - 0.12, 0, 6.55), gold, rot=(0, math.pi / 2, 0), verts=40)
# door: two dark-blue panels ajar, steps, canopy, lamps
box("Station_door", (0.06, 1.4, 2.25), (EX + 0.1, (DOOR[0] + DOOR[1]) / 2, 1.27), mat("M_StDoor", (0.05, 0.10, 0.35), rough=0.4), bevel=0.01)
box("Station_step", (0.5, 2.2, 0.15), (EX - 0.25, (DOOR[0] + DOOR[1]) / 2, 0.225), M["curb"], bevel=0.01)
box("Station_canopy", (1.2, 2.4, 0.12), (EX - 0.6, (DOOR[0] + DOOR[1]) / 2, 2.75), st_blue, bevel=0.02)
# windows: frames; W_CAM has NO glass (the camera flies through it); others glass with an interior glow card
ST_WIN_LIT = mat("M_StWinLit", (1.0, 0.85, 0.55), emit=((1.0, 0.82, 0.5), 0.0))
window("StW_cam", EX, (W_CAM[0] + W_CAM[1]) / 2, (W_CAM[2] + W_CAM[3]) / 2, W_CAM[1] - W_CAM[0], W_CAM[3] - W_CAM[2], -1, st_m, glass=False, mullion=False)
box("StW_cam_sill", (0.30, W_CAM[1] - W_CAM[0] + 0.2, 0.06), (EX - 0.05, (W_CAM[0] + W_CAM[1]) / 2, W_CAM[2] - 0.03), M["frame"], bevel=0.01)
GLOWS = []
for nm_, hh in (("StW_2", W_ST2),) + tuple(("StW_up%d" % i, u) for i, u in enumerate(UP)):
    g = window(nm_, EX, (hh[0] + hh[1]) / 2, (hh[2] + hh[3]) / 2, hh[1] - hh[0], hh[3] - hh[2], -1, st_m, lit=None)
    lm = mat("M_" + nm_ + "_glow", (1.0, 0.85, 0.55), emit=((1.0, 0.80, 0.45), 2.5))
    gl = box(nm_ + "_glow", (0.02, hh[1] - hh[0], hh[3] - hh[2]), (EX + 0.35, (hh[0] + hh[1]) / 2, (hh[2] + hh[3]) / 2), lm, bevel=0)
    GLOWS.append(gl)
sc["ST_GLOWS"] = [g.name for g in GLOWS]
for k, yy in enumerate((-2.0, 2.4)):
    cyl("Station_lamp%d" % k, 0.09, 0.22, (EX - 0.15, yy - 0.6 if k == 0 else yy + 0.9, 2.95), mat("M_StLamp%d" % k, (1, 0.9, 0.6), emit=((1, 0.85, 0.55), 0.0)), verts=16)

# station room interior: desk, chair, cabinet, wall clock, notice board, ceiling fan, candle, files
RX = ROOM
desk_x = RX["x0"] + 1.85; desk_y = 2.1
desk = inst("SRC_metal_office_desk", (desk_x, desk_y, 0.05), rot_z=math.pi / 2, newname="St_Desk")   # long side along y, faces -x
soften(desk)
dz = max((desk.matrix_world @ Vector(c)).z for c in desk.bound_box); sc["ST_DESK_TOP"] = dz; sc["ST_DESK"] = (desk_x, desk_y)
inst("SRC_drawer_cabinet", (RX["x1"] - 0.3, -1.6, 0.05), rot_z=math.pi / 2, newname="St_Cabinet")
inst("SRC_potted_plant_01", (RX["x0"] + 0.4, -0.2 + 3.2, 0.05), newname="St_Plant")
inst("SRC_plastic_monobloc_chair_01", (RX["x0"] + 1.1, -2.6, 0.05), rot_z=0.4, newname="St_Chair")
# files on the desk (rest ON the desk top)
for k, (dx_, dy_, col) in enumerate(((0.10, -0.45, (0.85, 0.15, 0.10)), (0.12, -0.42, (0.10, 0.35, 0.80)), (-0.05, 0.55, (0.95, 0.70, 0.05)))):
    box("St_File%d" % k, (0.24, 0.32, 0.03), (desk_x + dx_, desk_y + dy_, dz + 0.015 + 0.03 * (k == 1)), mat("M_StFile%d" % k, col, rough=0.6), bevel=0.004)
# candle on a saucer, on the desk (the only light after the power cut)
CANDLE_P = Vector((desk_x - 0.18, desk_y - 0.05, dz))
cyl("St_Saucer", 0.07, 0.012, CANDLE_P + Vector((0, 0, 0.006)), mat("M_Saucer", (0.9, 0.9, 0.85), rough=0.3), verts=24, bevel=0.003)
cyl("St_Candle", 0.022, 0.12, CANDLE_P + Vector((0, 0, 0.012 + 0.06)), mat("M_Candle", (0.97, 0.95, 0.88), rough=0.4, sss=0.3), verts=16)
flame = sphere("St_Flame", 0.012, CANDLE_P + Vector((0, 0, 0.012 + 0.12 + 0.018)), mat("M_Flame", (1, 0.6, 0.15), emit=((1.0, 0.55, 0.12), 25.0)), segs=12)
flame.scale = (0.8, 0.8, 2.0)
sc["CANDLE"] = list(CANDLE_P + Vector((0, 0, 0.17)))
# wall clock on the back wall (behind the officer), facing -x; hands keyed later
CLOCK_C = Vector((RX["x1"] - 0.02, desk_y, 2.25))
clock_bg = cyl("St_Clock", 0.24, 0.05, CLOCK_C, mat("M_ClockFace", (0.97, 0.96, 0.92), rough=0.3), rot=(0, math.pi / 2, 0), verts=48, bevel=0.01)
torus_m = mat("M_ClockRim", (0.75, 0.05, 0.05), rough=0.3, coat=0.5)
bpy.ops.mesh.primitive_torus_add(major_radius=0.245, minor_radius=0.025, location=CLOCK_C, rotation=(0, math.pi / 2, 0)); rim = bpy.context.active_object; rim.name = "St_ClockRim"; rim.data.materials.append(torus_m)
for k in range(12):
    a_ = k * math.pi / 6
    box("St_ClockTick%d" % k, (0.01, 0.012, 0.04 if k % 3 else 0.06), CLOCK_C + Vector((-0.03, 0.20 * math.sin(a_), 0.20 * math.cos(a_))), M["blackm"], bevel=0, rot=(-a_, 0, 0))
def hand_obj(name, length, width):
    piv = empty(name + "_piv", CLOCK_C + Vector((-0.035, 0, 0)))
    h = box(name, (0.008, width, length), CLOCK_C + Vector((-0.035, 0, length / 2 - 0.02)), M["blackm"], bevel=0)
    h.parent = piv; h.matrix_parent_inverse = piv.matrix_world.inverted()
    return piv
HOUR = hand_obj("St_ClockHour", 0.13, 0.018); MINUTE = hand_obj("St_ClockMin", 0.19, 0.012)
sc["CLOCK"] = [HOUR.name, MINUTE.name]
# notice board (blank coloured papers, no text) and a framed generic star on the back wall
box("St_Notice", (0.03, 1.2, 0.8), (RX["x1"] - 0.02, desk_y - 1.6, 1.7), M["wood"], bevel=0.01)
for k in range(6):
    box("St_NoticeP%d" % k, (0.01, 0.2, 0.26), (RX["x1"] - 0.04, desk_y - 2.05 + (k % 3) * 0.32, 1.85 - (k // 3) * 0.34), mat("M_NP%d" % k, random.choice([(1, 1, 0.9), (1, 0.9, 0.5), (0.8, 0.95, 1)])), bevel=0)
fan = [o for o in dst.objects if o is not None and o.name.startswith("StationFan")]
for o in fan:
    sc.collection.objects.link(o) if o.name not in sc.collection.objects else None
    o.location = Vector((desk_x + 0.9, desk_y - 0.9, ROOM["h"] - 0.02)) + (o.location - Vector((-12.5, 57.0, 2.48)))
    o.hide_render = o.hide_viewport = False
FAN_BLADES = [o for o in fan if "blades" in o.name][0]; FAN_BLADES.animation_data_clear(); FAN_BLADES.name = "St_FanBlades"
sc["FAN"] = FAN_BLADES.name
# station tube light (on until the cut), keyed later
tube = box("St_Tube", (0.06, 1.2, 0.05), (RX["x0"] + 2.6, desk_y - 0.4, ROOM["h"] - 0.06), mat("M_StTube", (1, 1, 1), emit=((1, 0.98, 0.92), 0.0)), bevel=0.01)
sc["ST_TUBE"] = tube.name

# ------------------------------------------------------------------ the CONTROL ROOM building (west, y 0..8): utility office with a big street window
CY0, CY1 = 0.0, 8.0
cr_m = plaster("M_Control", (0.02, 0.50, 0.52)); cr_trim = mat("M_ControlTrim", (0.98, 0.78, 0.05), rough=0.45)
W_CR = (1.7, 3.9, 0.95, 2.35)           # big window, camera enters here (no glass)
DOOR_CR = (5.2, 6.4, 0.15, 2.4)
wall_with_holes("Control_front", WX, CY0, CY1, 0.0, 4.2, [W_CR, DOOR_CR], cr_m, face=1)
# the wall_with_holes places the slab into -x for face=+1
bpy.data.objects["Control_front"].location.x += 0.0
CR = dict(x0=WX - 7.0, x1=WX - 0.25, y0=1.3, y1=CY1 - 0.25, h=3.0)
box("Control_body", (7.5, CY1 - CY0, 4.2), (WX - 3.75 - 0.25, (CY0 + CY1) / 2, 2.1), cr_m, bevel=0)
bpy.data.objects["Control_body"].hide_render = True; bpy.data.objects["Control_body"].hide_viewport = True   # placeholder volume not used
crin = plaster("M_ControlIn", (0.85, 0.36, 0.08))
box("Control_inBack", (0.2, CR["y1"] - CR["y0"], CR["h"]), (CR["x0"] - 0.1, (CR["y0"] + CR["y1"]) / 2, CR["h"] / 2), crin, bevel=0)
box("Control_inS", (CR["x1"] - CR["x0"] + 0.25, 0.2, CR["h"]), ((CR["x0"] + CR["x1"]) / 2, CR["y0"] - 0.1, CR["h"] / 2), crin, bevel=0)
box("Control_inN", (CR["x1"] - CR["x0"] + 0.25, 0.2, CR["h"]), ((CR["x0"] + CR["x1"]) / 2, CR["y1"] + 0.1, CR["h"] / 2), crin, bevel=0)
box("Control_ceil", (CR["x1"] - CR["x0"] + 0.25, CR["y1"] - CR["y0"] + 0.4, 0.2), ((CR["x0"] + CR["x1"]) / 2, (CR["y0"] + CR["y1"]) / 2, CR["h"] + 0.1), plaster("M_CtrlCeil", (0.95, 0.93, 0.88)), bevel=0)
box("Control_floor", (CR["x1"] - CR["x0"], CR["y1"] - CR["y0"], 0.05), ((CR["x0"] + CR["x1"]) / 2, (CR["y0"] + CR["y1"]) / 2, 0.025), tiles("M_CtrlFloor", (0.10, 0.25, 0.45), (0.85, 0.85, 0.80), (0.2, 0.2, 0.2), scale=1.2, w=0.5, h=0.5), bevel=0)
box("Control_outerS", (7.4, 0.25, 4.2), (WX - 3.7, CY0 + 0.125, 2.1), cr_m, bevel=0)
box("Control_outerN", (7.4, 0.25, 4.2), (WX - 3.7, CY1 - 0.125, 2.1), cr_m, bevel=0)
box("Control_roof", (7.4, CY1 - CY0, 0.25), (WX - 3.7, (CY0 + CY1) / 2, 4.2), cr_m, bevel=0)
box("Control_band", (0.14, CY1 - CY0, 0.30), (WX + 0.07, (CY0 + CY1) / 2, 3.0), cr_trim, bevel=0.01)
box("Control_parapet", (0.3, CY1 - CY0 + 0.2, 0.4), (WX + 0.05, (CY0 + CY1) / 2, 4.35), cr_trim, bevel=0.02)
window("CrW", WX, (W_CR[0] + W_CR[1]) / 2, (W_CR[2] + W_CR[3]) / 2, W_CR[1] - W_CR[0], W_CR[3] - W_CR[2], 1, cr_m, glass=False, mullion=False)
box("CrW_sill", (0.30, W_CR[1] - W_CR[0] + 0.2, 0.06), (WX + 0.05, (W_CR[0] + W_CR[1]) / 2, W_CR[2] - 0.03), M["frame"], bevel=0.01)
box("Control_door", (0.06, 1.2, 2.25), (WX - 0.1, (DOOR_CR[0] + DOOR_CR[1]) / 2, 1.27), mat("M_CrDoor", (0.85, 0.10, 0.05), rough=0.4), bevel=0.01)
signboard("Control_sign", WX, (CY0 + CY1) / 2, 3.7, 5.5, 0.6, 1, (0.98, 0.78, 0.05))
# lightning-bolt emblem (generic, no text) on the sign
bolt_m = mat("M_Bolt", (0.85, 0.05, 0.02), rough=0.3)
me = bpy.data.meshes.new("Bolt"); bm = bmesh.new()
pts = [(0, 0.10, 0.25), (0, -0.06, 0.0), (0, 0.04, 0.0), (0, -0.10, -0.25), (0, 0.08, 0.04), (0, -0.02, 0.04)]
bm.faces.new([bm.verts.new(p) for p in pts]); bm.to_mesh(me); bm.free()
bolt = bpy.data.objects.new("Control_bolt", me); sc.collection.objects.link(bolt); me.materials.append(bolt_m); bolt.location = (WX + 0.15, (CY0 + CY1) / 2 - 2.0, 3.7)
so = bolt.modifiers.new("s", 'SOLIDIFY'); so.thickness = 0.03
bolt2 = bolt.copy(); sc.collection.objects.link(bolt2); bolt2.location.y += 4.0
# console counter (standing height), laptop, switchgear cabinet with a big knife-switch lever, shelf, poster wall
CON = dict(x=WX - 1.9, y0=1.95, y1=3.75, top=1.02, depth=0.62)
cmat = mat("M_Counter", (0.55, 0.08, 0.06), rough=0.45, coat=0.3)
box("Ctrl_counter_top", (CON["depth"], CON["y1"] - CON["y0"], 0.05), (CON["x"], (CON["y0"] + CON["y1"]) / 2, CON["top"] - 0.025), mat("M_CounterTop", (0.92, 0.90, 0.85), rough=0.3), bevel=0.008)
box("Ctrl_counter_body", (CON["depth"] - 0.08, CON["y1"] - CON["y0"] - 0.06, CON["top"] - 0.07), (CON["x"] + 0.04, (CON["y0"] + CON["y1"]) / 2, (CON["top"] - 0.05) / 2), cmat, bevel=0.01)
sc["CON"] = [CON["x"], CON["y0"], CON["y1"], CON["top"], CON["depth"]]
LAP_C = Vector((CON["x"] - 0.02, 2.80, CON["top"]))
lap = inst("SRC_classic_laptop", LAP_C, rot_z=-math.pi / 2, scale=0.7, newname="Ctrl_Laptop"); soften(lap)
bpy.context.view_layer.update()
bb = [lap.matrix_world @ Vector(c) for c in lap.bound_box]
print("LAPTOP_BB", [round(min(v[i] for v in bb), 3) for i in range(3)], [round(max(v[i] for v in bb), 3) for i in range(3)])
sc["LAP_BB"] = [min(v[i] for v in bb) for i in range(3)] + [max(v[i] for v in bb) for i in range(3)]
SWG_P = Vector((WX - 2.35, CR["y0"] + 0.22, 0.05))
swg = inst("SRC_switchgear", SWG_P, rot_z=0.0, newname="Ctrl_Switchgear"); soften(swg)
bpy.context.view_layer.update()
bb = [swg.matrix_world @ Vector(c) for c in swg.bound_box]
sc["SWG_BB"] = [min(v[i] for v in bb) for i in range(3)] + [max(v[i] for v in bb) for i in range(3)]
print("SWG_BB", sc["SWG_BB"])
inst("SRC_drawer_cabinet", (CR["x0"] + 0.35, 5.6, 0.05), rot_z=-math.pi / 2, newname="Ctrl_Drawers")
inst("SRC_potted_plant_01", (CR["x1"] - 0.5, CR["y1"] - 0.5, 0.05), newname="Ctrl_Plant")
inst("SRC_wooden_crate_01", (CR["x0"] + 0.8, 7.2, 0.05), newname="Ctrl_Crate")
# a big wiring diagram poster (lines and coloured blocks, no text) on the back wall
poster = box("Ctrl_Poster", (0.02, 1.6, 1.0), (CR["x0"] + 0.02, 3.6, 1.75), mat("M_Poster", (0.97, 0.97, 0.94), rough=0.5), bevel=0)
for k in range(9):
    box("Ctrl_PosterL%d" % k, (0.01, random.uniform(0.2, 1.2), 0.025), (CR["x0"] + 0.04, 3.6 + random.uniform(-0.3, 0.3), 1.35 + k * 0.09), mat("M_PL%d" % k, random.choice([(0.85, 0.1, 0.05), (0.05, 0.3, 0.85), (0.1, 0.6, 0.2)])), bevel=0)
# DA KRAS FILMS logo #1: a sticker on the back of the laptop lid (faces the street window / the camera's way in)
sc["LOGO_DARK"] = LOGO_D; sc["LOGO_WHITE"] = LOGO_W
# DA KRAS FILMS logo #2: a framed print on the control room wall beside the window, faces into the room
lg2, asp = logo_plane("Logo_CtrlWall", LOGO_D, Vector((WX - 0.27, 5.0, 1.75)), 1.0, (-1, 0, 0))
box("Logo_CtrlWall_bg", (0.02, 1.12, 1.0 * asp + 0.12), (WX - 0.26, 5.0, 1.75), mat("M_LogoBg", (0.98, 0.97, 0.93), rough=0.4), bevel=0.005)
# DA KRAS FILMS logo #3: on the shop sign right next to the station (seen in the opening)
# (no logo on the shop sign: it was only ever seen cropped)
# ceiling tube lights in the control room (stay ON: only the police station loses power)
for k, yy in enumerate((3.0, 6.0)):
    box("Ctrl_Tube%d" % k, (0.06, 1.2, 0.05), (WX - 2.5, yy, CR["h"] - 0.06), mat("M_CtrlTube", (1, 1, 1), emit=((1, 0.98, 0.92), 6.0)), bevel=0.01)

# ------------------------------------------------------------------ the SUBSTATION yard (west, y 11..34) and the grid
YD = dict(x0=-30.0, x1=WX - 0.3, y0=11.0, y1=34.0)
plane("Yard_gravel", YD["x0"], YD["x1"], YD["y0"], YD["y1"], 0.01, M["gravel"])
fence_n = 0
def fence_line(p0, p1):
    global fence_n
    p0 = Vector(p0); p1 = Vector(p1); L = (p1 - p0).length; n = max(1, int(round(L / 1.91)))
    ang = math.atan2(p1.y - p0.y, p1.x - p0.x)
    for k in range(n):
        c = p0.lerp(p1, (k + 0.5) / n)
        inst("SRC_fence", (c.x, c.y, 0.0), rot_z=ang, newname="Fence%d" % fence_n); fence_n += 1
        q = p0.lerp(p1, k / n); inst("SRC_fencepost", (q.x, q.y, 0.0), newname="FencePost%d" % fence_n)
fence_line((WX - 0.3, YD["y0"]), (WX - 0.3, YD["y1"]))
fence_line((YD["x0"], YD["y0"]), (WX - 0.3, YD["y0"]))
fence_line((YD["x0"], YD["y1"]), (WX - 0.3, YD["y1"]))
TR = []
for k, (tx, ty) in enumerate(((-12.5, 16.0), (-12.5, 23.5), (-19.5, 16.0), (-19.5, 23.5))):
    box("TransPad%d" % k, (3.4, 4.2, 0.2), (tx, ty, 0.1), M["curb"], bevel=0.02)
    t = inst("SRC_transformer", (tx, ty, 0.2), rot_z=0.0, newname="Transformer%d" % k); soften(t); TR.append(t)
inst("SRC_utility_box_02", (WX - 1.2, 13.0, 0.0), rot_z=math.pi / 2, newname="Yard_UtilBox")
inst("SRC_powerbox", (WX - 0.45, 14.5, 1.0), rot_z=math.pi / 2, newname="Yard_PowerBox")
# warning sign on the fence: yellow triangle with a red bolt (no text)
tri_m = mat("M_WarnSign", (0.98, 0.80, 0.02), rough=0.35)
me = bpy.data.meshes.new("Warn"); bm = bmesh.new(); bm.faces.new([bm.verts.new(p) for p in ((0, -0.3, -0.25), (0, 0.3, -0.25), (0, 0, 0.27))]); bm.to_mesh(me); bm.free()
ws = bpy.data.objects.new("Yard_WarnSign", me); sc.collection.objects.link(ws); me.materials.append(tri_m); ws.location = (WX - 0.2, 18.5, 1.5)
so = ws.modifiers.new("s", 'SOLIDIFY'); so.thickness = 0.02
b3 = bolt.copy(); b3.modifiers.clear(); sc.collection.objects.link(b3); b3.location = (WX - 0.17, 18.5, 1.48); b3.scale = (0.7, 0.7, 0.7); b3.name = "Yard_WarnBolt"
so = b3.modifiers.new("s", 'SOLIDIFY'); so.thickness = 0.01
# pylons: one in the yard, then lines running west and north-west over the rooftops
pyl_src = LIB["SRC_pylon"]
pv = [pyl_src.matrix_world @ v.co for v in pyl_src.data.vertices]
tips = sorted([v for v in pv if abs(v.x) > 7.0], key=lambda v: v.z)
TIP_LOCAL = []
for side in (1, -1):
    vv = [v for v in pv if v.x * side > 6.6]
    if vv:
        zmin = min(v.z for v in vv); TIP_LOCAL.append(Vector((side * 7.4, 0, zmin - 0.6)))
top_arm = [v for v in pv if abs(v.x) > 3.5 and abs(v.x) < 5.5 and v.z > max(p.z for p in pv) - 4.5]
if top_arm:
    TIP_LOCAL.append(Vector((4.4, 0, min(v.z for v in top_arm) - 0.6))); TIP_LOCAL.append(Vector((-4.4, 0, min(v.z for v in top_arm) - 0.6)))
print("PYLON tips", [tuple(round(x, 2) for x in t) for t in TIP_LOCAL])
PYL = []
def pylon(name, loc, yaw):
    o = inst("SRC_pylon", loc, rot_z=yaw, newname=name); soften(o); PYL.append(o); return o
lineA = [Vector((-24.0, 22.5, 0)), Vector((-62.0, 30.0, 0)), Vector((-100.0, 37.0, 0)), Vector((-138.0, 44.0, 0)), Vector((-176.0, 51.0, 0))]
lineB = [Vector((-24.0, 22.5, 0)), Vector((-50.0, -8.0, 0)), Vector((-76.0, -38.0, 0)), Vector((-102.0, -68.0, 0))]
lineC = [Vector((-24.0, 22.5, 0)), Vector((-40.0, 62.0, 0)), Vector((-56.0, 101.0, 0)), Vector((-72.0, 140.0, 0))]
P0 = pylon("Pylon_yard", lineA[0], math.atan2(lineA[1].y - lineA[0].y, lineA[1].x - lineA[0].x) + math.pi / 2)
for L_, tag in ((lineA, "A"), (lineB, "B"), (lineC, "C")):
    objs = [P0]
    for k, p in enumerate(L_[1:]):
        d = (p - L_[k]); objs.append(pylon("Pylon%s%d" % (tag, k), p, math.atan2(d.y, d.x) + math.pi / 2))
    for a_, b_ in zip(objs, objs[1:]):
        for t in TIP_LOCAL:
            pa = a_.matrix_world @ t; pb = b_.matrix_world @ t
            mid = (pa + pb) / 2 - Vector((0, 0, 0.06 * (pb - pa).length))
            curve_tube("Line_%s_%s_%d" % (a_.name, b_.name, TIP_LOCAL.index(t)), [pa, mid, pb], 0.025, M["wire"], res=10)
# yard -> pylon feed from the transformers (short catenaries)
bpy.context.view_layer.update()
for k, t in enumerate(TR[:2]):
    p_ = t.location + Vector((0, 0, 2.3)); q_ = P0.matrix_world @ TIP_LOCAL[0]
    curve_tube("Feed%d" % k, [p_, (p_ + q_) / 2 - Vector((0, 0, 1.2)), q_], 0.02, M["wire"], res=10)
sc["PYLON_YARD"] = P0.name

# ------------------------------------------------------------------ street poles + wires (both sidewalks), the pole transformer above the bike stop
POLES = {1: [], -1: []}
for sx in (1, -1):
    for k in range(-3, 5):
        y = k * 14.0 + (3.0 if sx == 1 else -4.0)
        if sx == -1 and 9 < y < 36: continue
        x = sx * 4.5
        cyl("Pole_%d_%d" % (sx, k), 0.11, 8.5, (x, y, 4.25 + 0.15), M["concrete"], verts=12)
        box("PoleArm_%d_%d" % (sx, k), (1.4, 0.10, 0.10), (x - sx * 0.3, y, 8.0), M["concrete"], bevel=0.01)
        for j, dx in enumerate((-0.55, 0.0, 0.55)):
            cyl("PoleIns_%d_%d_%d" % (sx, k, j), 0.035, 0.14, (x - sx * 0.3 + dx, y, 8.12), M["insul"], verts=10)
        POLES[sx].append([Vector((x - sx * 0.3 + dx, y, 8.18)) for dx in (-0.55, 0.0, 0.55)])
        lamp = inst("SRC_street_lamp_01", (x, y + 0.2, 0.15), rot_z=(math.pi if sx > 0 else 0.0), newname="StreetLamp_%d_%d" % (sx, k))
for sx in (1, -1):
    for a_, b_ in zip(POLES[sx], POLES[sx][1:]):
        for j in range(3):
            pa, pb = a_[j], b_[j]; mid = (pa + pb) / 2 - Vector((0, 0, 0.45))
            curve_tube("SWire_%d_%d_%d" % (sx, int(pa.y), j), [pa, mid, pb], 0.008, M["wire"], res=12)
# cross-street service drops (to the station and the control room)
curve_tube("Drop_station", [POLES[1][3][0], Vector((5.6, 2.6, 6.6)), Vector((EX - 0.05, 3.8, 6.2))], 0.007, M["wire"], res=10)
curve_tube("Drop_cross", [POLES[1][3][1], Vector((0, 3.4, 7.2)), POLES[-1][3][1] if len(POLES[-1]) > 3 else Vector((-4.5, 3, 8))], 0.007, M["wire"], res=12)
# the pole transformer (grey can on a bracket) on the pole by the bike stop
PT = POLES[1][3][1] - Vector((0, 0, 1.6))
cyl("PoleTransformer", 0.32, 0.85, PT + Vector((0.25, 0, 0)), mat("M_PoleTrans", (0.45, 0.55, 0.60), rough=0.35, metal=0.4), verts=24, bevel=0.02)
for j in range(3):
    cyl("PoleTransIns%d" % j, 0.03, 0.12, PT + Vector((0.12 + j * 0.13, 0, 0.5)), M["insul"], verts=10)
sc["POLE_TRANS"] = list(PT + Vector((0.25, 0, 0)))

# ------------------------------------------------------------------ street life (all resting ON the ground)
stall_spots = [(-5.4, -14.0, 0.0), (5.6, -20.0, math.pi), (-5.5, -26.0, 0.0), (5.5, 14.5, math.pi), (-5.4, -36.0, 0.0), (5.5, 28.0, math.pi)]
for k, (x, y, r) in enumerate(stall_spots):
    o = inst("SRC_stall", (x, y, 0.15), rot_z=r + math.pi / 2, newname="Stall%d" % k); soften(o)
for k, (x, y, r) in enumerate(((-5.2, -20.0, 0.3), (5.3, 9.0, 2.9), (-5.3, 38.5, 0.0))):
    o = inst("SRC_cart", (x, y, 0.15), rot_z=r, newname="Cart%d" % k); soften(o)
for k, (x, y, r) in enumerate(((-3.0, -18.0, 0.0), (-3.0, 16.0, 0.0), (3.2, 20.0, math.pi), (-3.1, -40.0, 0.0))):
    o = inst("SRC_rickshaw", (x, y, 0.0), rot_z=r, newname="Rick%d" % k); soften(o)
for k, (x, y, r) in enumerate(((-2.2, 42.0, 0.8), (-5.0, -48.0, 0.2))):
    inst("SRC_cow", (x, y, 0.0 if abs(x) < 4 else 0.15), rot_z=r, newname="Cow%d" % k)
inst("SRC_dog", (5.8, -2.8, 0.15), rot_z=0.4, newname="Dog")
for k, (x, y) in enumerate(((5.9, -4.4), (-5.9, 9.2))):
    inst("SRC_potted_plant_01", (x, y, 0.15), newname="Pot%d" % k)
inst("SRC_trash", (-5.9, -3.8, 0.15), rot_z=1.2, newname="Trash")
for k, (x, y) in enumerate(((5.6, -9.0), (5.6, -9.9))):
    inst("SRC_plastic_crate_01", (x, y, 0.15), newname="Crate%d" % k)
# moving traffic: two rickshaws keyed along the road (west lane going -y, east lane going +y), wheels hidden by bodywork
for k, (x, ya, yb, r) in enumerate(((-2.2, 60.0, -30.0, math.pi), (2.0, -55.0, 10.0, 0.0))):
    o = inst("SRC_rickshaw", (x, ya, 0.0), rot_z=r, newname="RickMove%d" % k); soften(o)
    o.keyframe_insert("location", frame=1); o.location.y = yb; o.keyframe_insert("location", frame=900)
    for fc in iter_fcurves(o.animation_data.action):
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
# bunting across the street (small coloured flags on a string)
for yy in (-12.0, 22.0):
    pa = Vector((-6.4, yy, 5.6)); pb = Vector((6.4, yy, 5.6)); mid = (pa + pb) / 2 - Vector((0, 0, 0.6))
    curve_tube("Bunting_%d" % int(yy), [pa, mid, pb], 0.004, M["wire"], res=12)
    for k in range(24):
        t = (k + 0.5) / 24; p = (1 - t) ** 2 * pa + 2 * (1 - t) * t * (mid + (mid - (pa + pb) / 2)) + t * t * pb
        p = pa.lerp(pb, t); p.z = 5.6 - 0.6 * 4 * t * (1 - t)
        me = bpy.data.meshes.new("flag"); bm = bmesh.new(); bm.faces.new([bm.verts.new(q) for q in ((0, -0.12, 0), (0, 0.12, 0), (0, 0, -0.26))]); bm.to_mesh(me); bm.free()
        fo = bpy.data.objects.new("Flag_%d_%d" % (int(yy), k), me); sc.collection.objects.link(fo); fo.location = p
        me.materials.append(mat("M_Flag%d" % (k % 5), AWN[k % 5], rough=0.7))

# ------------------------------------------------------------------ the bike: his motorcycle (wheels split out so they can spin)
bike = inst("SRC_motorcycle", (2.3, -10.0, 0.0), newname="Bike"); soften(bike)
bpy.context.view_layer.objects.active = bike
for o in bpy.context.selected_objects: o.select_set(False)
bike.select_set(True)
bike.data = bike.data.copy()
bm = bmesh.new(); bm.from_mesh(bike.data); bm.verts.ensure_lookup_table()
wi = [i for i, m in enumerate(bike.data.materials) if m and m.name.startswith("Wheels")]
WHEELS = {}
for tag, cy_ in (("F", 0.705), ("R", -0.64)):
    geo = set()
    for f in bm.faces:
        if f.material_index in wi and all(abs(v.co.y - cy_) < 0.34 and v.co.z < 0.56 for v in f.verts): geo.add(f)
    WHEELS[tag] = geo
for tag, cy_ in (("F", 0.705), ("R", -0.64)):
    faces = list(WHEELS[tag])
    if not faces: continue
    nb = bmesh.new(); vmap = {}
    for f in faces:
        vs = []
        for v in f.verts:
            if v not in vmap: vmap[v] = nb.verts.new(v.co - Vector((0, cy_, 0.26)))
            vs.append(vmap[v])
        try: nb.faces.new(vs).material_index = f.material_index
        except ValueError: pass
    me = bpy.data.meshes.new("Bike_wheel" + tag); nb.to_mesh(me); nb.free()
    for m_ in bike.data.materials: me.materials.append(m_)
    w_ = bpy.data.objects.new("Bike_wheel" + tag, me); sc.collection.objects.link(w_); w_.parent = bike; w_.location = (0, cy_, 0.26)
    for p_ in me.polygons: p_.use_smooth = True
bmesh.ops.delete(bm, geom=list(WHEELS["F"] | WHEELS["R"]), context='FACES')
bm.to_mesh(bike.data); bm.free()
sc["BIKE"] = bike.name
# small logo on the bike's tank? no: keep the bike clean (the logos sit on the shop sign, the laptop and the office wall)

# ------------------------------------------------------------------ look: AgX Punchy, deep saturated, fast render settings, day -> dusk keyed in 03
sc.view_settings.view_transform = 'AgX'
try: sc.view_settings.look = 'AgX - Punchy'
except Exception: pass
sc.view_settings.exposure = 0.0
sc.render.engine = 'CYCLES'
sc.cycles.samples = 64; sc.cycles.adaptive_threshold = 0.04; sc.cycles.use_adaptive_sampling = True; sc.cycles.use_denoising = True
sc.cycles.denoiser = 'OPENIMAGEDENOISE'
try:
    sc.view_layers[0].cycles.denoising_store_passes = False
except Exception: pass
sc.cycles.max_bounces = 6; sc.cycles.diffuse_bounces = 3; sc.cycles.glossy_bounces = 3; sc.cycles.transmission_bounces = 6
sc.cycles.transparent_max_bounces = 16; sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
sc.render.use_persistent_data = True
sc.render.use_simplify = True; sc.render.simplify_subdivision_render = 2; sc.cycles.texture_limit_render = '2048'
sc.render.use_motion_blur = False
w = bpy.data.worlds.new("World"); sc.world = w; w.use_nodes = True; nt = w.node_tree
bg = nt.nodes["Background"]
lp = nt.nodes.new("ShaderNodeLightPath"); tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ")
nt.links.new(tc.outputs["Generated"], sep.inputs[0])
ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.name = "SkyRamp"
ramp.color_ramp.elements[0].position = 0.5; ramp.color_ramp.elements[0].color = (0.80, 0.92, 1.0, 1)
ramp.color_ramp.elements[1].position = 0.85; ramp.color_ramp.elements[1].color = (0.10, 0.48, 0.95, 1)
nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
cam_bg = nt.nodes.new("ShaderNodeBackground"); cam_bg.name = "SkyCam"; cam_bg.inputs["Strength"].default_value = 1.0
nt.links.new(ramp.outputs["Color"], cam_bg.inputs["Color"])
bg.name = "SkyLight"; bg.inputs["Color"].default_value = (0.55, 0.70, 0.95, 1); bg.inputs["Strength"].default_value = 0.9
mix = nt.nodes.new("ShaderNodeMixShader"); nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs[0])
nt.links.new(bg.outputs[0], mix.inputs[1]); nt.links.new(cam_bg.outputs[0], mix.inputs[2])
nt.links.new(mix.outputs[0], nt.nodes["World Output"].inputs["Surface"])
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 4.0; sun.data.angle = math.radians(3); sun.data.color = (1.0, 0.95, 0.86)
sun.rotation_euler = (math.radians(42), math.radians(-18), math.radians(-60))
def area(name, loc, target, power, size, col):
    ld = bpy.data.lights.new(name, 'AREA'); ld.energy = power; ld.size = size; ld.color = col; ld.shape = 'DISK'
    o = bpy.data.objects.new(name, ld); sc.collection.objects.link(o); o.location = loc
    d = Vector(target) - Vector(loc); o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return o
# control room: bright interior key + fill (room is lit all film)
area("Ctrl_Key", (WX - 1.0, 2.6, 2.85), (WX - 2.6, 2.6, 1.3), 260, 1.2, (1.0, 0.95, 0.88))
area("Ctrl_Fill", (WX - 4.5, 3.5, 2.6), (WX - 2.0, 2.6, 1.4), 180, 1.6, (1.0, 0.90, 0.80))
area("Ctrl_Back", (WX - 5.5, 6.0, 2.7), (WX - 6.8, 4.0, 1.4), 120, 1.6, (1.0, 0.92, 0.85))
area("Ctrl_WinWall", (WX - 3.6, 4.5, 2.5), (WX - 0.3, 3.5, 1.6), 170, 1.8, (1.0, 0.92, 0.85))
area("Ctrl_Deep1", (WX - 4.5, 2.5, 2.8), (WX - 6.8, 2.5, 1.0), 160, 1.6, (1.0, 0.90, 0.80))
area("Ctrl_Deep2", (WX - 6.0, 4.5, 2.8), (WX - 7.0, 5.0, 1.0), 140, 1.6, (1.0, 0.90, 0.80))
# station room: tube-light key (keyed OFF at the cut), moonlight through the window and the candle (keyed ON) in 03
area("St_Key", (RX["x0"] + 2.4, desk_y - 0.4, ROOM["h"] - 0.15), (desk_x + 0.5, desk_y, 1.0), 240, 1.2, (1.0, 0.97, 0.90))
area("St_Moon", (EX - 1.5, desk_y + 0.4, 2.4), (desk_x + 0.8, desk_y, 1.3), 0.0, 1.4, (0.45, 0.60, 1.0))
cl_ = bpy.data.lights.new("St_CandleLight", 'POINT'); cl_.energy = 0.0; cl_.color = (1.0, 0.62, 0.25); cl_.shadow_soft_size = 0.05
co_ = bpy.data.objects.new("St_CandleLight", cl_); sc.collection.objects.link(co_); co_.location = CANDLE_P + Vector((0, 0, 0.2))
# street lamps at dusk: one point light under each lamp head, keyed on in 03
SL = []
for o in [o for o in bpy.data.objects if o.name.startswith("StreetLamp_")]:
    ld = bpy.data.lights.new(o.name + "_L", 'POINT'); ld.energy = 0.0; ld.color = (1.0, 0.75, 0.40); ld.shadow_soft_size = 0.2
    lo = bpy.data.objects.new(o.name + "_L", ld); sc.collection.objects.link(lo)
    lo.location = o.location + Vector((-0.5 if o.location.x > 0 else 0.5, 0.0, 3.6)); SL.append(lo.name)
sc["STREET_LIGHTS"] = SL
sc["EX"] = EX; sc["WX"] = WX; sc["ROOM"] = [ROOM["x0"], ROOM["x1"], ROOM["y0"], ROOM["y1"], ROOM["h"]]; sc["CR"] = [CR["x0"], CR["x1"], CR["y0"], CR["y1"], CR["h"]]
sc["W_CAM"] = list(W_CAM); sc["W_CR"] = list(W_CR)
# hide the asset templates (they stay only as mesh data users)
for o in LIB.values():
    if o.name.startswith("SRC_") and o.name in sc.collection.objects: sc.collection.objects.unlink(o)
for c in list(bpy.data.collections):
    if c.name == "_lib": bpy.data.collections.remove(c)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SET_OK", OUT, len(bpy.data.objects), "objects")
