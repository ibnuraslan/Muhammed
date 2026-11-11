"""Sarajevo 1914 set: riverside quay (along X), side street (+Y) at x=0 by the stone bridge, café on the corner,
facades with windows, bunting and flags, river, hills, sky. Generic: no signs, no text, no brands.
blender -b <humans.blend> --python 02_build_set.py -- <out.blend>"""
import sys, os
import bpy, bmesh
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "00_lib.py")).read())
OUT = sys.argv[sys.argv.index("--") + 1]
random.seed(1914)
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, 100
sc.render.fps, sc.render.fps_base = 60, 1.0
sc.frame_start, sc.frame_end = 1, 2130
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
CS = coll("Set"); CB = coll("Buildings", CS); CD = coll("Dressing", CS)

# ------------------------------------------------------------------ materials
M_COB = pbr("Cobbles", "cobblestone_floor_08", 0.42, rough_mul=1.0, bump=0.8)
M_SIDE = pbr("Sidewalk", "grey_plaster_02", 0.5, tint=(0.85, 0.82, 0.78))
M_STONE = pbr("BridgeStone", "castle_brick_07", 0.35, tint=(0.95, 0.9, 0.82))
M_QUAY = pbr("QuayWall", "plaster_stone_wall_01", 0.25, tint=(0.8, 0.78, 0.72))
WALLS = [pbr("Wall_Beige", "beige_wall_001", 0.3), pbr("Wall_Yellow", "yellow_plaster_02", 0.3, tint=(1.0, 0.93, 0.78)),
         pbr("Wall_White", "white_stucco", 0.3, tint=(0.95, 0.93, 0.88)), pbr("Wall_Red", "red_plaster_weathered", 0.3, tint=(0.95, 0.75, 0.65)),
         pbr("Wall_Grey", "grey_plaster_02", 0.3, tint=(0.88, 0.86, 0.82))]
M_TRIM = pbr("Trim", "white_stucco", 0.6, tint=(0.92, 0.9, 0.84))
M_GLASS = flat("WindowGlass", (0.03, 0.04, 0.05), rough=0.08)
M_FRAME = flat("WindowFrame", (0.35, 0.25, 0.18), rough=0.5)
M_ROOF = pbr("RoofTiles", "red_plaster_weathered", 0.8, tint=(0.62, 0.3, 0.2))
M_SHOP = flat("ShopGlass", (0.05, 0.045, 0.04), rough=0.15)
M_IRON = flat("Iron", (0.03, 0.03, 0.03), rough=0.45, metal=0.8)
M_FLAG = {k: flat("Cloth_" + k, rgb, rough=0.8) for k, rgb in
          (("Black", (0.02, 0.02, 0.02)), ("Yellow", (0.85, 0.62, 0.05)), ("Red", (0.6, 0.03, 0.03)), ("White", (0.85, 0.84, 0.8)),
           ("Green", (0.08, 0.3, 0.12)), ("Cream", (0.9, 0.82, 0.62)))}

# water
M_WATER = bpy.data.materials.new("River"); n, l = nodes_of(M_WATER)
bs = n["Principled BSDF"]; bs.inputs['Base Color'].default_value = (0.04, 0.09, 0.08, 1); bs.inputs['Roughness'].default_value = 0.06
tc = n.new('ShaderNodeTexCoord'); nz = n.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 1.6; nz.inputs['Detail'].default_value = 6
mp = n.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (0.6, 1.8, 1.0); bump = n.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.25
l.new(tc.outputs['Object'], mp.inputs[0]); l.new(mp.outputs[0], nz.inputs['Vector']); l.new(nz.outputs['Fac'], bump.inputs['Height']); l.new(bump.outputs[0], bs.inputs['Normal'])
mp.name = "WaterFlow"

# ------------------------------------------------------------------ ground
X0, X1 = -70.0, 160.0
def slab(name, mn, mx, mat, c=CS):
    bm = bmesh.new(); add_box(bm, mn, mx, 0); return mesh_obj(name, bm, [mat], c)
slab("Road_Quay", V(X0, -5.5, -0.3), V(X1, 6.0, 0.0), M_COB)
slab("Road_Side", V(-2.5, 6.0, -0.3), V(2.5, 90, 0.0), M_COB)
slab("Walk_Quay_N_W", V(X0, 6.0, -0.3), V(-2.5, 8.0, 0.15), M_SIDE)
slab("Walk_Quay_N_E", V(2.5, 6.0, -0.3), V(X1, 8.0, 0.15), M_SIDE)
slab("Walk_Side_W", V(-4.5, 8.0, -0.3), V(-2.5, 90, 0.15), M_SIDE)
slab("Walk_Side_E", V(2.5, 8.0, -0.3), V(4.5, 90, 0.15), M_SIDE)
slab("Walk_River", V(X0, -7.0, -0.3), V(X1, -5.5, 0.15), M_SIDE)
slab("QuayWall_N", V(X0, -7.6, -4.5), V(X1, -7.0, 0.15), M_QUAY)
slab("QuayWall_S", V(X0, -30.6, -4.5), V(X1, -30.0, 0.15), M_QUAY)
slab("Walk_Far", V(X0, -36.0, -0.3), V(X1, -30.0, 0.15), M_SIDE)
slab("Road_Far", V(X0, -44.0, -0.3), V(X1, -36.0, 0.0), M_COB)
slab("RiverBed", V(X0, -30.0, -4.6), V(X1, -7.6, -4.3), M_QUAY)
wt = slab("River", V(X0, -30.0, -3.6), V(X1, -7.6, -3.5), M_WATER)
# kerbs
for nm, mn, mx in (("Kerb_N_W", V(X0, 5.85, -0.05), V(-2.5, 6.05, 0.16)), ("Kerb_N_E", V(2.5, 5.85, -0.05), V(X1, 6.05, 0.16)),
                   ("Kerb_R", V(X0, -5.6, -0.05), V(X1, -5.45, 0.16)), ("Kerb_SW", V(-2.6, 8.0, -0.05), V(-2.45, 90, 0.16)),
                   ("Kerb_SE", V(2.45, 8.0, -0.05), V(2.6, 90, 0.16))):
    slab(nm, mn, mx, M_STONE)

# railing along the river
bm = bmesh.new()
x = X0
while x < X1:
    if not (-11.5 < x < -4.5):
        add_box(bm, V(x - 0.05, -7.35, 0.15), V(x + 0.05, -7.25, 1.1), 0)
    x += 2.0
for z in (0.55, 1.05):
    for a, b in ((X0, -11.5), (-4.5, X1)):
        add_box(bm, V(a, -7.33, z - 0.03), V(b, -7.27, z + 0.03), 0)
mesh_obj("Railing", bm, [M_IRON], CD)

# ------------------------------------------------------------------ stone bridge (humped, three arches) at x -11..-5
BX0, BX1, BY0, BY1 = -11.0, -5.0, -30.6, -7.0
bm = bmesh.new(); N = 90
ys = [BY0 + (BY1 - BY0) * i / N for i in range(N + 1)]
def ztop(y): return 0.15 + 1.6 * math.sin(math.pi * (y - BY0) / (BY1 - BY0))
ARCH = [(-25.0, 3.0), (-18.8, 2.6), (-12.6, 3.0)]
def zbot(y):
    for c, r in ARCH:
        if abs(y - c) < r: return -3.2 + 0.9 * math.sqrt(r * r - (y - c) ** 2)
    return -4.4
cols = []
for y in ys:
    cols.append([bm.verts.new((x_, y, z_)) for x_, z_ in ((BX0, zbot(y)), (BX0, ztop(y)), (BX1, ztop(y)), (BX1, zbot(y)))])
for a, b in zip(cols, cols[1:]):
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((a[i], b[i], b[j], a[j]))
for cc in (cols[0], cols[-1]): bm.faces.new(cc)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
mesh_obj("Bridge", bm, [M_STONE], CS)
bm = bmesh.new()
for x_ in (BX0, BX1 - 0.4):
    for y0, y1 in zip(ys[::3], ys[3::3]):
        z0 = min(ztop(y0), ztop(y1))
        add_box(bm, V(x_, y0, z0 - 0.1), V(x_ + 0.4, y1 + 0.02, max(ztop(y0), ztop(y1)) + 0.75), 0)
mesh_obj("Bridge_Parapet", bm, [M_STONE], CS)

# ------------------------------------------------------------------ buildings
def building(name, w, d, h, floors_up, wall, M, style, flags=True, shop=True, awning=None):
    """local frame: facade in plane y=0 facing -Y, x 0..w, depth +Y.  M = world matrix."""
    bm = bmesh.new()
    G = 4.4
    add_box(bm, V(0, 0, -0.3), V(w, d, h), 0)
    fh = (h - G - 0.8) / floors_up
    ncol = max(2, int(w / 2.7)); dx = w / ncol
    for f in range(floors_up):
        z0 = G + f * fh + 0.55
        wh = min(1.95, fh - 1.0)
        for c in range(ncol):
            cx = dx * (c + 0.5)
            add_box(bm, V(cx - 0.62, -0.02, z0), V(cx + 0.62, 0.02, z0 + wh), 2)                  # glass
            for (a, b) in (((cx - 0.75, z0 - 0.12), (cx - 0.6, z0 + wh + 0.12)), ((cx + 0.6, z0 - 0.12), (cx + 0.75, z0 + wh + 0.12)),
                           ((cx - 0.75, z0 + wh), (cx + 0.75, z0 + wh + 0.15))):
                add_box(bm, V(a[0], -0.09, a[1]), V(b[0], 0.0, b[1]), 1)                           # surround
            add_box(bm, V(cx - 0.02, -0.05, z0), V(cx + 0.02, 0.0, z0 + wh), 3)                   # mullion
            add_box(bm, V(cx - 0.62, -0.05, z0 + wh * 0.62), V(cx + 0.62, 0.0, z0 + wh * 0.62 + 0.04), 3)
            add_box(bm, V(cx - 0.82, -0.18, z0 - 0.16), V(cx + 0.82, 0.0, z0 - 0.04), 1)          # sill
            if style % 2 == 0 and f == 0:
                add_box(bm, V(cx - 0.85, -0.16, z0 + wh + 0.15), V(cx + 0.85, 0.0, z0 + wh + 0.4), 1)   # pediment
        add_box(bm, V(-0.05, -0.14, G + f * fh - 0.1), V(w + 0.05, 0.0, G + f * fh + 0.15), 1)     # floor band
    add_box(bm, V(-0.25, -0.5, h - 0.15), V(w + 0.25, d, h + 0.35), 1)                             # cornice
    add_box(bm, V(-0.1, -0.2, h - 0.45), V(w + 0.1, 0.0, h - 0.15), 1)
    # ground floor shopfronts / doors
    if shop:
        nshop = max(1, int(w / 4.5)); sw = w / nshop
        for s in range(nshop):
            cx = sw * (s + 0.5)
            add_box(bm, V(cx - sw * 0.36, -0.03, 0.5), V(cx + sw * 0.36, 0.03, 3.3), 4)
            add_box(bm, V(cx - sw * 0.4, -0.12, 0.15), V(cx + sw * 0.4, 0.0, 0.55), 1)
            add_box(bm, V(cx - sw * 0.4, -0.12, 3.3), V(cx + sw * 0.4, 0.0, 3.6), 3)
            add_box(bm, V(cx - 0.03, -0.06, 0.5), V(cx + 0.03, 0.0, 3.3), 3)
    else:
        for c in range(ncol):
            cx = dx * (c + 0.5)
            add_box(bm, V(cx - 0.55, -0.03, 0.9), V(cx + 0.55, 0.03, 3.0), 2)
            add_box(bm, V(cx - 0.7, -0.1, 0.8), V(cx + 0.7, 0.0, 0.9), 1)
    add_box(bm, V(-0.05, -0.1, -0.3), V(w + 0.05, 0.0, 0.6), 1)                                  # plinth
    # roof: gable along x
    r0 = len(bm.verts)
    rh = 2.2 + 0.6 * (style % 3)
    p = [bm.verts.new(v) for v in ((-0.2, -0.45, h + 0.35), (w + 0.2, -0.45, h + 0.35), (w + 0.2, d + 0.2, h + 0.35), (-0.2, d + 0.2, h + 0.35),
                                   (0.6, d * 0.5, h + 0.35 + rh), (w - 0.6, d * 0.5, h + 0.35 + rh))]
    for fc in ((0, 1, 5, 4), (2, 3, 4, 5), (1, 2, 5), (3, 0, 4)):
        f = bm.faces.new([p[i] for i in fc]); f.material_index = 5
    o = mesh_obj(name, bm, [wall, M_TRIM, M_GLASS, M_FRAME, M_SHOP, M_ROOF], CB)
    o.matrix_world = M
    o["ncol"] = ncol; o["fh"] = fh; o["w"] = w
    return o

def row(prefix, x_start, x_end, M_of, gaps=(), flags=True, hmin=13.0, hmax=19.0, avoid=()):
    x = x_start; i = 0; out = []
    while x < x_end:
        w = random.choice((9.0, 10.5, 12.0, 13.5, 15.0))
        if any(a - w < x < b for a, b in avoid):
            x = next(b for a, b in avoid if a - w < x < b); continue
        h = random.uniform(hmin, hmax); fl = 3 if h < 15.5 else 4
        o = building(f"{prefix}_{i:02d}", w, 14.0, h, fl, random.choice(WALLS), M_of(x, w), i, flags=flags)
        out.append((o, x, w, h, fl)); x += w + random.choice((0.0, 0.0, 0.2)); i += 1
    return out

Rz = lambda a: Matrix.Rotation(R_(a), 4, 'Z')
T = Matrix.Translation
CAFE_X0, CAFE_W = 4.5, 13.5
quayN = row("BldQuayN", X0 + 2, X1 - 4, lambda x, w: T(V(x, 8.0, 0.0)), avoid=((-4.5, 4.5), (CAFE_X0, CAFE_X0 + CAFE_W)))
cafe = building("Cafe_Building", CAFE_W, 18.0, 15.0, 3, WALLS[1], T(V(CAFE_X0, 8.0, 0.0)), 2)
farS = row("BldFar", X0 + 1, X1 - 4, lambda x, w: T(V(x + w, -36.0, 0.0)) @ Rz(180), hmin=11, hmax=17)
# side street: west side faces +X (facade plane x=-4.5), east side faces -X (x=+4.5)
def side_row(prefix, sign, y0, y1):
    y = y0; i = 0; out = []
    while y < y1:
        w = random.choice((10.5, 12.0, 13.5)); h = random.uniform(13, 18)
        if sign < 0:   # west, facade faces +X: local -Y -> world +X  => rotate +90
            M = T(V(-4.5, y, 0)) @ Rz(90)
        else:          # east, facade faces -X
            M = T(V(4.5, y + w, 0)) @ Rz(-90)
        o = building(f"{prefix}_{i:02d}", w, 14.0, h, 3 if h < 15.5 else 4, random.choice(WALLS), M, i + 7)
        out.append((o, y, w, h)); y += w; i += 1
    return out
sideW = side_row("BldSideW", -1, 8.0 + 0.0, 80)
sideE = side_row("BldSideE", 1, 26.0, 80)
# café's side-street facade (x = 4.5, y 8..26)
cafe_side = building("Cafe_Side", 18.0, 13.0, 15.0, 3, WALLS[1], T(V(4.5, 26.0, 0)) @ Rz(-90), 2)

# café awning (striped, no text) along the side-street facade, y 10..24, and dressing
def awning(name, length, depth, drop, M, colors=("Green", "Cream")):
    bm = bmesh.new(); nst = int(length / 0.45)
    for i in range(nst):
        x0, x1 = i * length / nst, (i + 1) * length / nst
        vs = [bm.verts.new(v) for v in ((x0, 0, 0), (x1, 0, 0), (x1, -depth, -drop), (x0, -depth, -drop),
                                         (x0, -depth, -drop - 0.3), (x1, -depth, -drop - 0.3))]
        f = bm.faces.new((vs[0], vs[1], vs[2], vs[3])); f.material_index = i % 2
        f = bm.faces.new((vs[3], vs[2], vs[5], vs[4])); f.material_index = i % 2
    o = mesh_obj(name, bm, [M_FLAG[colors[0]], M_FLAG[colors[1]]], CD); o.matrix_world = M
    return o
awning("Cafe_Awning", 14.0, 2.0, 0.7, T(V(4.5, 24.0, 3.7)) @ Rz(-90))
awning("Cafe_Awning_Quay", 12.0, 2.0, 0.7, T(V(CAFE_X0 + 0.8, 8.0, 3.7)))
# a few awnings on quay shops (red/cream, plain)
for o, x, w, h, fl in quayN[::3]:
    awning(o.name + "_Awn", w - 1.0, 1.6, 0.6, T(V(x + 0.5, 8.0, 3.65)), ("Red", "Cream"))

# café tables + chairs (Poly Haven, CC0)
def ph_model(asset):
    d = os.path.join(ASSETS, asset); f = next(x for x in os.listdir(d) if x.endswith(".blend"))
    with bpy.data.libraries.load(os.path.join(d, f), link=False) as (src, dst):
        dst.objects = list(src.objects)
    return [o for o in dst.objects if o and o.type == 'MESH']
CHAIR = ph_model("gallinera_chair"); TABLE = ph_model("gallinera_table")
def place_copy(objs, loc, rot, c=CD, name="Prop"):
    root = bpy.data.objects.new(name, None); c.objects.link(root); root.location = loc; root.rotation_euler = (0, 0, R_(rot))
    for ob in objs:
        cp = bpy.data.objects.new(ob.name + "_" + name, ob.data); c.objects.link(cp); cp.matrix_world = ob.matrix_world.copy(); cp.parent = root
    return root
for i, y in enumerate((16.0, 19.0, 22.0)):
    place_copy(TABLE, V(3.7, y, 0.15), 0, name=f"CafeTable{i}")
    place_copy(CHAIR, V(3.7, y - 0.75, 0.15), 0, name=f"CafeChairA{i}")
    place_copy(CHAIR, V(3.7, y + 0.75, 0.15), 180, name=f"CafeChairB{i}")
for i, x in enumerate((7.0, 10.5, 14.0)):
    place_copy(TABLE, V(x, 7.0, 0.15), 0, name=f"CafeQTable{i}")
    place_copy(CHAIR, V(x - 0.75, 7.0, 0.15), -90, name=f"CafeQChairA{i}")
for ob in CHAIR + TABLE:
    for c_ in list(ob.users_collection): c_.objects.unlink(ob)

# ------------------------------------------------------------------ bunting + hanging flags (flutter via Wave modifier)
def bunting(name, pts, sag, n_per_m=2.2):
    bm = bmesh.new()
    for a, b in zip(pts, pts[1:]):
        L = (b - a).length; n = max(2, int(L * n_per_m)); d = (b - a).normalized()
        for i in range(n):
            t0, t1 = i / n, (i + 0.8) / n
            def P(t): return a.lerp(b, t) - V(0, 0, sag * 4 * t * (1 - t))
            p0, p1 = P(t0), P(t1); m = (p0 + p1) / 2 - V(0, 0, 0.32)
            f = bm.faces.new((bm.verts.new(p0), bm.verts.new(p1), bm.verts.new(m))); f.material_index = i % 3
        # string
    o = mesh_obj(name, bm, [M_FLAG["Red"], M_FLAG["White"], M_FLAG["Yellow"]], CD)
    wv = o.modifiers.new("Flutter", 'WAVE'); wv.use_normal = False; wv.height = 0.05; wv.width = 1.5; wv.speed = 0.06; wv.narrowness = 1.0
    return o
# along quay facades at ~5.3 m, plus strings across the side street
for k, (o, x, w, h, fl) in enumerate(quayN):
    if k % 2 == 0: bunting(f"Bunting_Q{k}", [V(x + 0.3, 7.9, 5.4), V(x + w / 2, 7.9, 5.4), V(x + w - 0.3, 7.9, 5.4)], 0.6)
for k, y in enumerate((12.0, 20.0, 30.0)):
    bunting(f"Bunting_S{k}", [V(-4.4, y, 7.0), V(4.4, y + 1.0, 7.0)], 0.9)
for k, x in enumerate(range(int(X0) + 8, int(X1), 14)):
    bunting(f"Bunting_R{k}", [V(x, -7.3, 4.2), V(x + 14, -7.3, 4.2)], 1.2)   # along the lamp line by the river

def banner(name, loc, M_rot, w, hgt, cols):
    bm = bmesh.new(); ns = len(cols); nseg = 10
    for s in range(ns):
        for j in range(nseg):
            z0, z1 = -hgt * (s * nseg + j) / (ns * nseg), -hgt * (s * nseg + j + 1) / (ns * nseg)
            f = bm.faces.new([bm.verts.new(v) for v in ((0, 0, z0), (w, 0, z0), (w, 0, z1), (0, 0, z1))]); f.material_index = s
    o = mesh_obj(name, bm, [M_FLAG[c] for c in cols], CD); o.matrix_world = T(loc) @ M_rot
    wv = o.modifiers.new("Flutter", 'WAVE'); wv.use_normal = True; wv.height = 0.06; wv.width = 1.2; wv.speed = 0.05
    wv.use_x = False; wv.use_y = False
    return o
FLAGSETS = (("Black", "Yellow"), ("Red", "White", "Red"), ("Yellow", "Black"))
for k, (o, x, w, h, fl) in enumerate(quayN):
    if k % 2 == 1:
        for j in range(2):
            banner(f"Banner_Q{k}_{j}", V(x + w * (0.3 + 0.4 * j), 7.85, h - 1.2), Matrix.Identity(4), 1.0, 3.2, FLAGSETS[(k + j) % 3])
for k, (o, y, w, h) in enumerate(sideW):
    banner(f"Banner_SW{k}", V(-4.35, y + w / 2, h - 1.5), Rz(90), 1.0, 3.0, FLAGSETS[k % 3])
for k, (o, y, w, h) in enumerate(sideE):
    banner(f"Banner_SE{k}", V(4.35, y + w / 2, h - 1.5), Rz(-90), 1.0, 3.0, FLAGSETS[(k + 1) % 3])
# roof flag poles
for k, (o, x, w, h, fl) in enumerate(quayN[1::2]):
    bm = bmesh.new(); add_box(bm, V(-0.04, -0.04, 0), V(0.04, 0.04, 4.0), 0)
    pole = mesh_obj(f"FlagPole_{k}", bm, [M_IRON], CD); pole.location = (x + w / 2, 8.2, h + 0.3)
    bm = bmesh.new(); cols = FLAGSETS[k % 3]; nseg = 12
    for j in range(nseg):
        for s in range(len(cols)):
            z0, z1 = 3.9 - 1.2 * s / len(cols), 3.9 - 1.2 * (s + 1) / len(cols)
            x0_, x1_ = 1.8 * j / nseg, 1.8 * (j + 1) / nseg
            f = bm.faces.new([bm.verts.new(v) for v in ((x0_, 0, z0), (x1_, 0, z0), (x1_, 0, z1), (x0_, 0, z1))]); f.material_index = s
    fl_ = mesh_obj(f"RoofFlag_{k}", bm, [M_FLAG[c] for c in cols], CD); fl_.location = pole.location
    wv = fl_.modifiers.new("Flutter", 'WAVE'); wv.use_normal = False; wv.use_x = False; wv.use_y = True
    wv.height = 0.25; wv.width = 1.0; wv.speed = 0.12; wv.start_position_x = 0.0; wv.falloff_radius = 0

# ------------------------------------------------------------------ street lamps (CC-BY) by the river
lroot, lnew = import_glb(os.path.join(MODELS, "lamp.glb"), CD, "Lamp_Src")
lmeshes = [o for o in lnew if o.type == 'MESH']
bpy.context.view_layer.update()
for k, x in enumerate(range(int(X0) + 8, int(X1), 14)):
    r = bpy.data.objects.new(f"Lamp_{k}", None); CD.objects.link(r); r.location = (x, -6.9, 0.15); r.scale = (1.9,) * 3
    for ob in lmeshes:
        cp = bpy.data.objects.new(f"Lamp_{k}_{ob.name}", ob.data); CD.objects.link(cp); cp.matrix_world = ob.matrix_world.copy(); cp.parent = r
for ob in lnew: bpy.data.objects.remove(ob)
bpy.data.objects.remove(lroot)

# ------------------------------------------------------------------ hills around the valley
bm = bmesh.new(); NG = 90; SZ = 1600.0
grid = {}
for i in range(NG + 1):
    for j in range(NG + 1):
        x_, y_ = -SZ / 2 + SZ * i / NG + 45, -SZ / 2 + SZ * j / NG
        dy = abs(y_ - 0) ; r = max(0.0, dy - 70)
        z = -1.0 + 0.0025 * r * r * (0.6 + 0.4 * math.sin(x_ * 0.011) * math.cos(y_ * 0.013)) + 12 * math.sin(x_ * 0.03 + y_ * 0.02)
        z = min(z, 260); z = max(z, -1.0) if r > 0 else -8.0
        grid[i, j] = bm.verts.new((x_, y_, z))
for i in range(NG):
    for j in range(NG):
        bm.faces.new((grid[i, j], grid[i + 1, j], grid[i + 1, j + 1], grid[i, j + 1]))
M_HILL = bpy.data.materials.new("Hills"); n, l = nodes_of(M_HILL)
bs = n["Principled BSDF"]; bs.inputs['Roughness'].default_value = 0.9
nz = n.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 0.08; nz.inputs['Detail'].default_value = 10
tc = n.new('ShaderNodeTexCoord'); l.new(tc.outputs['Object'], nz.inputs['Vector'])
cr = n.new('ShaderNodeValToRGB'); cr.color_ramp.elements[0].color = (0.05, 0.1, 0.03, 1); cr.color_ramp.elements[1].color = (0.22, 0.24, 0.12, 1)
l.new(nz.outputs['Fac'], cr.inputs[0]); l.new(cr.outputs[0], bs.inputs['Base Color'])
hills = mesh_obj("Hills", bm, [M_HILL], CS); shade_smooth(hills)
# far town blocks on the lower slopes (cheap boxes with roofs)
bm = bmesh.new()
for k in range(260):
    x_ = random.uniform(-300, 400); side = random.choice((-1, 1)); y_ = side * random.uniform(60 if side > 0 else 55, 160)
    if -50 < y_ < 95: continue
    r = max(0.0, abs(y_) - 70); z0 = -1.0 + 0.0025 * r * r * 0.6
    w_, d_, h_ = random.uniform(8, 16), random.uniform(8, 14), random.uniform(7, 14)
    add_box(bm, V(x_, y_, z0 - 2), V(x_ + w_, y_ + d_, z0 + h_), random.randint(0, 1))
mesh_obj("FarTown", bm, [WALLS[2], M_ROOF], CS)

# ------------------------------------------------------------------ sky + sun
w = sc.world or bpy.data.worlds.new("World"); sc.world = w
n, l = nodes_of(w); n.clear()
sky = n.new('ShaderNodeTexSky'); sky.sky_type = 'MULTIPLE_SCATTERING'
try:
    sky.sun_elevation = R_(52); sky.sun_rotation = R_(150); sky.altitude = 500
except Exception as e: print("SKY", e)
bg = n.new('ShaderNodeBackground'); bg.name = "SkyStrength"; bg.inputs['Strength'].default_value = 0.14
out = n.new('ShaderNodeOutputWorld'); l.new(sky.outputs[0], bg.inputs[0]); l.new(bg.outputs[0], out.inputs[0])
sun = bpy.data.objects.new("Key_Sun", bpy.data.lights.new("Key_Sun", 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 3.6; sun.data.angle = R_(1.5); sun.data.color = (1.0, 0.95, 0.88)
sun.rotation_euler = (R_(38), 0, R_(150))
sc.view_settings.view_transform = 'AgX'; sc.view_settings.exposure = -0.7
try: sc.view_settings.look = 'AgX - Medium High Contrast'
except Exception: pass

for k, v in dict(CAFE_X0=CAFE_X0, BX0=BX0, BX1=BX1, X0=X0, X1=X1).items(): sc[k] = v
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SET_DONE", len(bpy.data.objects), "objects")
