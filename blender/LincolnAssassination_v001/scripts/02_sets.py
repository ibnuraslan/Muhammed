"""Sets for B04: theatre (box over the stage) at the origin, night street at x=100, barn at x=200.
blender -b chars.blend --python 02_sets.py -- <out.blend>"""
import sys, os, math
import bpy, bmesh
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "00_lib.py")).read())
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
BRAND = os.path.join(HERE, "..", "..", "assets", "brand")

def box(name, mn, mx, mat, c, bevel=0.0):
    bm = bmesh.new(); add_box(bm, Vector(mn), Vector(mx)); o = mesh_obj(name, bm, [mat], c)
    if bevel:
        m = o.modifiers.new("Bevel", 'BEVEL'); m.width = bevel; m.segments = 2
    return o

def place(o, loc, yaw=0.0, scale=1.0):
    o.location = loc; o.rotation_euler = (0, 0, R_(yaw)); o.scale = (scale,) * 3
    return o

def recolor(o, rgb, rough=None, keep_tex=True):
    for i, m in enumerate(o.data.materials):
        m = m.copy(); o.data.materials[i] = m
        nt = m.node_tree; bs = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
        src = bs.inputs['Base Color'].links[0].from_socket if bs.inputs['Base Color'].links else None
        if src is not None and keep_tex:
            mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1
            mx.inputs['B'].default_value = (*rgb, 1); nt.links.new(src, mx.inputs['A']); nt.links.new(mx.outputs['Result'], bs.inputs['Base Color'])
        else:
            for l in list(bs.inputs['Base Color'].links): nt.links.remove(l)
            bs.inputs['Base Color'].default_value = (*rgb, 1)
        if rough is not None:
            for l in list(bs.inputs['Roughness'].links): nt.links.remove(l)
            bs.inputs['Roughness'].default_value = rough

def logo_mat(name, which):
    m = bpy.data.materials.new(name); n, l = nodes_of(m)
    bs = next(x for x in n if x.type == 'BSDF_PRINCIPLED'); t = n.new('ShaderNodeTexImage')
    t.image = img(os.path.join(BRAND, "DaKrasFilms_logo_%s.png" % which)); t.extension = 'CLIP'
    l.new(t.outputs['Color'], bs.inputs['Base Color']); l.new(t.outputs['Alpha'], bs.inputs['Alpha'])
    bs.inputs['Roughness'].default_value = 0.6
    try: m.blend_method = 'HASHED'
    except Exception: pass
    return m

def decal(name, w, h, mat, c):
    """plane in local XZ (normal -Y), size w x h, UV 0..1"""
    bm = bmesh.new(); uv = bm.loops.layers.uv.new()
    vs = [bm.verts.new((x, 0, z)) for x, z in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]
    f = bm.faces.new(vs)
    for lp, co in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): lp[uv].uv = co
    return mesh_obj(name, bm, [mat], c)

def swag(name, x0, x1, ztop, depth, n, mat, c, axis='X', fixed=0.0, thick=0.08):
    """scalloped valance (velvet swags) between x0..x1 along `axis` at constant other coord `fixed`"""
    bm = bmesh.new(); W = x1 - x0; N = 24 * n; rows = 10; grid = []
    for j in range(rows + 1):
        v = j / rows; row = []
        for i in range(N + 1):
            u = i / N; s = (u * n) % 1.0
            sag = depth * (0.35 + 0.65 * math.sin(math.pi * s)) * v + depth * 0.15 * v
            fold = 0.05 * math.sin(2 * math.pi * u * n * 6) * (0.3 + v)
            a = x0 + W * u; z = ztop - sag
            row.append(bm.verts.new((a, fixed + fold, z) if axis == 'X' else (fixed + fold, a, z)))
        grid.append(row)
    for j in range(rows):
        for i in range(N):
            bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
    o = mesh_obj(name, bm, [mat], c); shade_smooth(o)
    m = o.modifiers.new("Solid", 'SOLIDIFY'); m.thickness = thick
    return o

def light(name, kind, loc, energy, rgb=(1, 1, 1), size=1.0, rot=(0, 0, 0), c=None):
    L = bpy.data.lights.new(name, kind); L.energy = energy; L.color = rgb
    if kind == 'AREA': L.size = size
    elif kind in ('POINT', 'SPOT'): L.shadow_soft_size = size
    o = bpy.data.objects.new(name, L); (c or sc.collection).objects.link(o); o.location = loc; o.rotation_euler = rot
    return o

# ================================================================== materials
M = dict(
    stage=pbr("StageBoards", "wood_floor_deck", scale=0.45, tint=(1.15, 0.9, 0.65), rough_mul=1.3, bump=0.3),
    planks=pbr("BarnPlanks", "brown_planks_09", scale=0.4, tint=(1.1, 0.85, 0.65), rough_mul=1.2, bump=0.35),
    planks2=pbr("BarnPlanksDark", "brown_planks_05", scale=0.45, tint=(0.8, 0.62, 0.45), rough_mul=1.2, bump=0.35),
    cobble=pbr("Cobbles", "cobblestone_floor_08", scale=0.3, tint=(0.8, 0.85, 1.0), rough_mul=1.1, bump=0.35),
    velvet=flat("Velvet", (0.42, 0.03, 0.05), rough=0.75),
    velvetDark=flat("VelvetDark", (0.25, 0.02, 0.04), rough=0.8),
    gold=flat("GoldTrim", (0.85, 0.62, 0.25), rough=0.35, metal=0.8),
    wallpaper=flat("BoxWallpaper", (0.86, 0.72, 0.42), rough=0.7),
    cream=flat("Cream", (0.93, 0.88, 0.76), rough=0.6),
    white=flat("ColumnWhite", (0.95, 0.94, 0.9), rough=0.45),
    dark=flat("StageDark", (0.22, 0.09, 0.07), rough=0.9),
    carpet=flat("Carpet", (0.35, 0.06, 0.08), rough=0.9),
    flat1=flat("SceneryWall", (0.62, 0.82, 0.74), rough=0.8),
    flat2=flat("SceneryTrim", (0.92, 0.88, 0.75), rough=0.7),
    door=flat("DoorBrown", (0.25, 0.12, 0.06), rough=0.6),
    walk=flat("Sidewalk", (0.42, 0.42, 0.45), rough=0.85),
    dirt=pbr("BarnFloorBoards", "brown_planks_05", scale=0.35, tint=(0.75, 0.6, 0.42), rough_mul=1.3, bump=0.3),
    straw=flat("Straw", (0.85, 0.7, 0.35), rough=0.9),
    paper=flat("PosterPaper", (0.95, 0.9, 0.78), rough=0.8),
    lampglow=flat("LampGlow", (1, 0.8, 0.5), emit=(1.0, 0.75, 0.4), emit_str=6.0),
    ground=flat("NightGround", (0.25, 0.22, 0.18), rough=0.95),
)

# ================================================================== THEATRE
T = coll("Theatre")
box("StageFloor", (-9, -4, -0.2), (13, 9, 0), M["stage"], T)
box("StageFrontFace", (-9, -4.2, -1.3), (13, -4, 0), M["door"], T)
box("PitFloor", (-9, -14, -1.5), (13, -4.2, -1.3), M["carpet"], T)
# painted drawing-room scenery at the back of the stage
box("Backdrop", (-9, 9, 0), (9, 9.2, 9), M["flat1"], T)
box("BackdropWainscot", (-9, 8.95, 0), (9, 9, 1.1), M["flat2"], T)
for i, x in enumerate((-5.5, 0.0, 5.5)):
    box("FlatWindow%d" % i, (x - 1.0, 8.9, 2.0), (x + 1.0, 8.95, 5.0), M["cream"], T)
    box("FlatWindowPane%d" % i, (x - 0.85, 8.88, 2.15), (x + 0.85, 8.9, 4.85), flat("PaintedSky", (0.55, 0.8, 1.0), rough=0.6), T)
box("SceneryDoor", (-2.8, 8.9, 0), (-1.6, 8.95, 2.6), M["door"], T)
box("WingL", (-9.2, -4, 0), (-9, 9, 9), M["dark"], T)
box("WingR", (13, -4, 0), (13.2, 9, 9), M["dark"], T)
box("StageCeiling", (-9.2, -4.5, 9.6), (13.2, 9.2, 9.8), M["dark"], T)
# a small parlour set on the stage (sofa-like bench and table)
box("StageSofa", (-3.4, 5.6, 0), (-0.8, 6.4, 0.45), M["velvetDark"], T, bevel=0.04)
box("StageSofaBack", (-3.4, 6.25, 0.45), (-0.8, 6.45, 1.0), M["velvetDark"], T, bevel=0.04)
box("StageTable", (1.6, 5.4, 0.72), (2.6, 6.2, 0.78), M["door"], T, bevel=0.02)
for dx in (1.7, 2.5):
    for dy in (5.5, 6.1):
        box("StageTableLeg", (dx - 0.03, dy - 0.03, 0), (dx + 0.03, dy + 0.03, 0.72), M["door"], T)
# proscenium: red valance swags and side drapes, gold frame
swag("StageValance", -9, 9, 9.0, 1.4, 4, M["velvet"], T, axis='X', fixed=-3.9)
box("ProsceniumTop", (-9.2, -4.1, 8.9), (9.2, -3.9, 9.6), M["gold"], T)
cur = glb_asset("curtain", T, target_size=8.6, axis=2)
recolor(cur, (0.42, 0.03, 0.05), rough=0.75, keep_tex=False)
place(cur, (-7.6, -3.7, 0), yaw=90, scale=1.0)
cur.scale = (1.0, 0.4, 1.0)
cur2 = cur.copy(); cur2.data = cur.data; T.objects.link(cur2); place(cur2, (7.4, -3.7, 0), yaw=-90); cur2.scale = (1.0, 0.4, 1.0); cur2.name = "CurtainR"
cur.name = "CurtainL"
# footlights
for i in range(12):
    x = -8 + i * 1.45
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=0.07)
    o = mesh_obj("Footlight%d" % i, bm, [M["lampglow"]], T); o.location = (x, -3.75, 0.07)
light("StageKey", 'AREA', (0, 2, 8.5), 6000, (1.0, 0.92, 0.8), size=10, c=T)
light("StageFoot", 'AREA', (0, -3.6, 0.4), 500, (1.0, 0.8, 0.55), size=8, rot=(R_(-70), 0, 0), c=T)

# ---------------------------------------------------------------- the box (above the stage, house right)
BX0, BX1, BY0, BY1, BZ = 9.0, 12.5, -3.5, 0.5, 1.6
box("BoxFloor", (BX0, BY0, BZ - 0.4), (BX1, BY1, BZ), M["carpet"], T)
box("BoxUnderTrim", (BX0 - 0.05, BY0, BZ - 0.45), (BX0 + 0.1, BY1, BZ - 0.3), M["gold"], T)
box("WallBelowBox", (BX0, -4.0, 0), (BX0 + 0.15, 1.2, BZ - 0.4), M["wallpaper"], T)
box("WallBelowBoxDado", (BX0 - 0.03, -4.0, 0), (BX0, 1.2, 1.0), M["door"], T)
# parapet: solid front panel with a 0.4 m wide ledge on top (the gunman stands on it in S07)
box("BoxParapet", (BX0 - 0.15, BY0, BZ), (BX0 + 0.15, BY1, BZ + 0.75), M["cream"], T, bevel=0.02)
box("BoxLedge", (BX0 - 0.2, BY0 - 0.05, BZ + 0.75), (BX0 + 0.2, BY1 + 0.05, BZ + 0.83), M["velvet"], T, bevel=0.02)
for i, (y0, y1) in enumerate(((BY0 + 0.25, -1.65), (-1.35, BY1 - 0.25))):
    box("ParapetPanel%d" % i, (BX0 - 0.17, y0, BZ + 0.15), (BX0 - 0.15, y1, BZ + 0.6), M["gold"], T)
box("BoxWallBack", (BX1, BY0, BZ), (BX1 + 0.15, BY1, BZ + 3.3), M["wallpaper"], T)
box("BoxWallS", (BX0, BY0 - 0.15, BZ), (BX1, BY0, BZ + 3.3), M["wallpaper"], T)
box("BoxWallN", (BX0, BY1, BZ), (BX1, BY1 + 0.15, BZ + 3.3), M["wallpaper"], T)
box("BoxCeiling", (BX0 - 0.3, BY0 - 0.3, BZ + 3.3), (BX1 + 0.2, BY1 + 0.3, BZ + 3.5), M["cream"], T)
box("BoxDoor", (BX1 - 0.02, -3.1, BZ), (BX1, -2.1, BZ + 2.3), M["door"], T)
box("BoxDado", (BX0, BY0, BZ), (BX1, BY0 + 0.02, BZ + 0.9), M["door"], T)
box("BoxDadoN", (BX0, BY1 - 0.02, BZ), (BX1, BY1, BZ + 0.9), M["door"], T)
for i, y in enumerate((BY0, BY1)):
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=0.15, radius2=0.13, depth=3.3)
    for v in bm.verts:
        a = math.atan2(v.co.y, v.co.x); r = Vector((v.co.x, v.co.y)).length
        if r > 0.05: s = 1 - 0.06 * (0.5 + 0.5 * math.cos(8 * a)); v.co.x *= s; v.co.y *= s
    o = mesh_obj("BoxColumn%d" % i, bm, [M["white"]], T); o.location = (BX0, y, BZ + 1.65); shade_smooth(o)
    box("BoxColumnCap%d" % i, (BX0 - 0.22, y - 0.22, BZ + 3.1), (BX0 + 0.22, y + 0.22, BZ + 3.3), M["white"], T, bevel=0.03)
swag("BoxValance", BY0, BY1, BZ + 3.3, 0.75, 2, M["velvet"], T, axis='Y', fixed=BX0 - 0.1)
box("BoxValanceRod", (BX0 - 0.2, BY0, BZ + 3.25), (BX0 - 0.1, BY1, BZ + 3.33), M["gold"], T)
# side drapes tied back at the columns
for i, y in enumerate((BY0 + 0.25, BY1 - 0.25)):
    d = cur.copy(); d.data = cur.data; T.objects.link(d); d.name = "BoxDrape%d" % i
    d.location = (BX0 + 0.12, y, BZ); d.rotation_euler = (0, 0, 0); d.scale = (0.5, 0.07, 0.38)
chair = glb_asset("armchair", T, target_size=1.05, axis=2)
recolor(chair, (0.55, 0.3, 0.75))
chair.name = "BoxChair"
CHAIR_POS = Vector((9.95, -1.2, BZ)); CHAIR_YAW = math.degrees(math.atan2(-10.2, -5.0))
place(chair, CHAIR_POS, yaw=CHAIR_YAW)
chair2 = chair.copy(); chair2.data = chair.data; T.objects.link(chair2); chair2.name = "BoxChair2"
place(chair2, (10.6, 0.0, BZ), yaw=CHAIR_YAW + 10)
light("BoxWarm", 'AREA', (11.4, -1.5, BZ + 3.1), 260, (1.0, 0.85, 0.6), size=2.5, c=T)
light("BoxFill", 'AREA', (8.0, -2.5, BZ + 1.8), 120, (0.85, 0.9, 1.0), size=2.0, rot=(0, R_(-90), 0), c=T)
sc["CHAIR_POS"] = list(CHAIR_POS); sc["CHAIR_YAW"] = CHAIR_YAW; sc["BOX"] = [BX0, BX1, BY0, BY1, BZ]

# ================================================================== STREET (x = 100)
ST = coll("Street")
X0 = 100.0
box("Road", (X0 - 7, -45, -0.05), (X0 + 7, 45, 0), M["cobble"], ST)
box("WalkL", (X0 - 9.6, -45, 0), (X0 - 7, 45, 0.15), M["walk"], ST)
box("WalkR", (X0 + 7, -45, 0), (X0 + 9.6, 45, 0.15), M["walk"], ST)
box("KerbL", (X0 - 7.1, -45, 0), (X0 - 7, 45, 0.16), M["walk"], ST)
box("KerbR", (X0 + 7, -45, 0), (X0 + 7.1, 45, 0.16), M["walk"], ST)
houses = [glb_asset(n, ST) for n in ("house1", "house3", "house5")]
for hsrc in houses: hsrc.hide_render = True; hsrc.hide_viewport = True; hsrc.location = (X0, 60, 0)
y = -42.0; k = 0
while y < 44:
    for side in (-1, 1):
        src = houses[(k + (side > 0)) % 3]
        o = src.copy(); o.data = src.data; ST.objects.link(o); o.hide_render = False; o.hide_viewport = False
        mn, mx = bbox_world([src]); depth = (mx.y - mn.y); w = (mx.x - mn.x)
        if side < 0: o.location = (X0 - 9.6 - depth / 2, y, 0.15); o.rotation_euler = (0, 0, R_(90))
        else: o.location = (X0 + 9.6 + depth / 2, y, 0.15); o.rotation_euler = (0, 0, R_(-90))
        o.name = "House_%s_%d" % ("L" if side < 0 else "R", k)
    k += 1; y += 8.3
lamp = glb_asset("streetlamp", ST, target_size=4.2, axis=2); lamp.name = "StreetLamp"
lamp.location = (X0 - 7.4, -30, 0.15)
for i, yy in enumerate(range(-30, 40, 14)):
    for side in (-1, 1):
        o = lamp if (i == 0 and side < 0) else lamp.copy()
        if o is not lamp: o.data = lamp.data; ST.objects.link(o)
        o.location = (X0 + side * 7.4, yy + (7 if side > 0 else 0), 0.15)
        light("LampLight_%d_%d" % (i, side), 'POINT', (X0 + side * 7.4, yy + (7 if side > 0 else 0), 3.75), 140, (1.0, 0.7, 0.4), size=0.15, c=ST)
        bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=0.09)
        g = mesh_obj("LampFlame_%d_%d" % (i, side), bm, [M["lampglow"]], ST); g.location = (X0 + side * 7.4, yy + (7 if side > 0 else 0), 3.75)
# DA KRAS FILMS poster (S12) on the right-hand facades, and a crate stack with the white logo (S13)
POSTER = Vector((X0 + 9.55, 4.0, 2.3))
pp = decal("Poster", 2.0, 1.25, M["paper"], ST)
pp.location = POSTER; pp.rotation_euler = (0, 0, R_(-90))
pl = decal("PosterLogo", 1.7, 1.7 * 414 / 967, logo_mat("LogoDark", "dark"), ST)
pl.location = POSTER + Vector((-0.012, 0, 0.05)); pl.rotation_euler = (0, 0, R_(-90))
bd = decal("PosterBorder", 2.12, 1.37, M["velvet"], ST); bd.location = POSTER + Vector((0.01, 0, 0)); bd.rotation_euler = (0, 0, R_(-90))
crate = glb_asset("crate", ST, target_size=1.0, axis=0); crate.name = "Crate"
recolor(crate, (1.1, 0.95, 0.8))
CR = Vector((X0 - 8.2, -9.0, 0.15))
crate.location = CR; crate.rotation_euler = (0, 0, R_(90))
for j, (dx, dy, dz) in enumerate(((0, 1.05, 0), (0, 0.5, 0.46))):
    o = crate.copy(); o.data = crate.data; ST.objects.link(o); o.name = "Crate%d" % (j + 2)
    o.location = CR + Vector((dx, dy, dz)); o.rotation_euler = (0, 0, R_(90 + 4 * j))
cl = decal("CrateLogo", 0.9, 0.9 * 414 / 967, logo_mat("LogoWhite", "white"), ST)
cl.location = CR + Vector((0.36, 0.0, 0.24)); cl.rotation_euler = (0, 0, R_(90))
sc["POSTER"] = list(POSTER); sc["CRATE"] = list(CR)
moon = light("Moon", 'SUN', (X0, 0, 20), 2.6, (0.6, 0.72, 1.0), c=ST); moon.rotation_euler = (R_(50), 0, R_(-30))
moon.data.angle = R_(3)

# ================================================================== BARN (x = 200)
B = coll("Barn")
X1 = 200.0; BW, BL, EAVE, RIDGE = 4.5, 7.0, 3.6, 6.4
box("BarnFloor", (X1 - BW, -BL, -0.05), (X1 + BW, BL, 0), M["dirt"], B)
box("BarnOutside", (X1 - 30, -40, -0.1), (X1 + 30, -BL, 0), M["ground"], B)
box("BarnWallL", (X1 - BW - 0.15, -BL, 0), (X1 - BW, BL, EAVE), M["planks"], B)
box("BarnWallR", (X1 + BW, -BL, 0), (X1 + BW + 0.15, BL, EAVE), M["planks"], B)
box("BarnWallBack", (X1 - BW, BL, 0), (X1 + BW, BL + 0.15, EAVE), M["planks"], B)
DW = 1.8
box("BarnFrontL", (X1 - BW, -BL - 0.15, 0), (X1 - DW, -BL, EAVE), M["planks"], B)
box("BarnFrontR", (X1 + DW, -BL - 0.15, 0), (X1 + BW, -BL, EAVE), M["planks"], B)
box("BarnFrontTop", (X1 - DW, -BL - 0.15, 3.3), (X1 + DW, -BL, EAVE), M["planks"], B)
for yy, nm in ((BL, "Back"), (-BL - 0.15, "Front")):
    bm = bmesh.new()
    vs = [bm.verts.new(v) for v in ((X1 - BW, yy, EAVE), (X1 + BW, yy, EAVE), (X1, yy, RIDGE),
                                     (X1 - BW, yy + 0.15, EAVE), (X1 + BW, yy + 0.15, EAVE), (X1, yy + 0.15, RIDGE))]
    bm.faces.new(vs[:3]); bm.faces.new(vs[3:][::-1])
    for a, b in ((0, 1), (1, 2), (2, 0)): bm.faces.new((vs[a], vs[b], vs[b + 3], vs[a + 3]))
    mesh_obj("BarnGable" + nm, bm, [M["planks"]], B)
for side in (-1, 1):
    bm = bmesh.new()
    vs = [bm.verts.new(v) for v in ((X1 + side * (BW + 0.4), -BL - 0.4, EAVE - 0.25), (X1 + side * (BW + 0.4), BL + 0.4, EAVE - 0.25),
                                     (X1, BL + 0.4, RIDGE + 0.05), (X1, -BL - 0.4, RIDGE + 0.05))]
    bm.faces.new(vs if side > 0 else vs[::-1])
    o = mesh_obj("BarnRoof%d" % side, bm, [M["planks2"]], B); m = o.modifiers.new("Solid", 'SOLIDIFY'); m.thickness = 0.12
for i, yy in enumerate((-BL + 0.3, -3.5, 0.0, 3.5, BL - 0.3)):
    for side in (-1, 1):
        box("BarnPost%d_%d" % (i, side), (X1 + side * (BW - 0.25) - 0.12, yy - 0.12, 0), (X1 + side * (BW - 0.25) + 0.12, yy + 0.12, EAVE), M["planks2"], B)
    box("BarnTieBeam%d" % i, (X1 - BW, yy - 0.1, EAVE - 0.3), (X1 + BW, yy + 0.1, EAVE - 0.08), M["planks2"], B)
box("BarnRidgeBeam", (X1 - 0.12, -BL, RIDGE - 0.35), (X1 + 0.12, BL, RIDGE - 0.1), M["planks2"], B)
hay = glb_asset("haybale", B, target_size=1.1, axis=1); hay.name = "HayBale"
recolor(hay, (1.05, 0.95, 0.7))
HAY = [((X1 + 1.6, 0.2, 0), 0), ((X1 + 1.6, 1.35, 0), 4), ((X1 + 1.6, 0.8, 0.5), -3), ((X1 - 2.8, 3.2, 0), 88), ((X1 - 2.8, 4.4, 0), 92),
       ((X1 - 2.8, 3.8, 0.5), 90), ((X1 + 3.2, 4.8, 0), 0), ((X1 + 3.2, 5.95, 0), 2), ((X1 - 3.5, -4.5, 0), 0), ((X1 + 0.3, -1.6, 0), 30)]
for j, (p, yaw) in enumerate(HAY):
    o = hay if j == 0 else hay.copy()
    if o is not hay: o.data = hay.data; B.objects.link(o); o.name = "HayBale%d" % j
    o.location = p; o.rotation_euler = (0, 0, R_(yaw))
for i in range(0):
    bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5)
    o = mesh_obj("Straw%d" % i, bm, [M["straw"]], B); rnd = random.Random(i)
    o.location = (X1 + rnd.uniform(-4, 4), rnd.uniform(-6.5, 6.5), 0.005); o.rotation_euler = (0, 0, rnd.uniform(0, 6.3)); o.scale = (rnd.uniform(0.6, 1.6), rnd.uniform(0.4, 1.0), 1)

# stylised fire: emissive flame cards (noise W keyed later, no Scene Time)
fm = bpy.data.materials.new("FlameMat"); n, l = nodes_of(fm); n.clear()
out = n.new('ShaderNodeOutputMaterial'); em = n.new('ShaderNodeEmission'); tr = n.new('ShaderNodeBsdfTransparent'); mix = n.new('ShaderNodeMixShader')
tc = n.new('ShaderNodeTexCoord'); sep = n.new('ShaderNodeSeparateXYZ'); noise = n.new('ShaderNodeTexNoise'); noise.noise_dimensions = '4D'
noise.inputs['Scale'].default_value = 3.0; noise.inputs['Detail'].default_value = 3.0; noise.name = "FlameNoise"
ramp = n.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].position = 0.0; ramp.color_ramp.elements[0].color = (1.0, 0.75, 0.25, 1)
ramp.color_ramp.elements[1].position = 1.0; ramp.color_ramp.elements[1].color = (1.0, 0.25, 0.02, 1)
mp = n.new('ShaderNodeMapping'); mp.name = "FlameScroll"
l.new(tc.outputs['UV'], sep.inputs[0]); l.new(tc.outputs['UV'], mp.inputs[0]); l.new(mp.outputs[0], noise.inputs['Vector'])
sh = n.new('ShaderNodeMath'); sh.operation = 'SUBTRACT'
l.new(noise.outputs['Fac'], sh.inputs[0]); l.new(sep.outputs['Y'], sh.inputs[1])
gx = n.new('ShaderNodeMath'); gx.operation = 'PINGPONG'; gx.inputs[1].default_value = 0.5
l.new(sep.outputs['X'], gx.inputs[0])
wid = n.new('ShaderNodeMath'); wid.operation = 'MULTIPLY'; wid.inputs[1].default_value = 1.4
l.new(gx.outputs[0], wid.inputs[0])
sh2 = n.new('ShaderNodeMath'); sh2.operation = 'ADD'; l.new(sh.outputs[0], sh2.inputs[0]); l.new(wid.outputs[0], sh2.inputs[1])
mask = n.new('ShaderNodeMath'); mask.operation = 'GREATER_THAN'; mask.inputs[1].default_value = 0.62
l.new(sh2.outputs[0], mask.inputs[0])
l.new(sep.outputs['Y'], ramp.inputs[0]); l.new(ramp.outputs[0], em.inputs['Color']); em.inputs['Strength'].default_value = 3.5
l.new(mask.outputs[0], mix.inputs[0]); l.new(tr.outputs[0], mix.inputs[1]); l.new(em.outputs[0], mix.inputs[2]); l.new(mix.outputs[0], out.inputs[0])
try: fm.blend_method = 'HASHED'
except Exception: pass
FIRE = coll("BarnFire", B)
def flame(name, loc, w, h, yaw, mat=fm):
    bm = bmesh.new(); uv = bm.loops.layers.uv.new()
    vs = [bm.verts.new((x, 0, z)) for x, z in ((-w / 2, 0), (w / 2, 0), (w / 2, h), (-w / 2, h))]
    f = bm.faces.new(vs)
    for lp, co in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): lp[uv].uv = co
    o = mesh_obj(name, bm, [mat], FIRE); o.location = loc; o.rotation_euler = (0, 0, R_(yaw))
    o.visible_shadow = False
    return o
k = 0
for x in range(-4, 5):
    flame("FlameBack%d" % k, (X1 + x * 0.95, BL - 0.1, 0), 1.3, 2.6 + 0.6 * math.sin(x * 1.7), 0); k += 1
for yy in range(-2, 7):
    flame("FlameL%d" % k, (X1 - BW + 0.1, yy * 1.0, 0.2 + 1.2 * (yy > 2)), 1.2, 1.8 + 0.5 * math.cos(yy), 90); k += 1
    flame("FlameRoof%d" % k, (X1 - 2.2, yy * 1.0, EAVE + 0.4), 1.0, 1.1, 90); k += 1
for i, (p, e) in enumerate((((X1, BL - 1.0, 1.5), 700), ((X1 - BW + 1.0, 3.5, 1.6), 450), ((X1 - 1.5, 2.0, 4.6), 250))):
    light("FireLight%d" % i, 'POINT', p, e, (1.0, 0.45, 0.12), size=0.8, c=B)
light("BarnMoonDoor", 'AREA', (X1, -BL - 3.0, 3.0), 300, (0.55, 0.65, 1.0), size=3.0, rot=(R_(70), 0, 0), c=B)
light("BarnFill", 'AREA', (X1 + 2, -3, 3.2), 60, (1.0, 0.75, 0.5), size=3, c=B)

bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SETS_DONE")
