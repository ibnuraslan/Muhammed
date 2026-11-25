"""SurgeonBrandsLivers v015 stage A (from scratch): four MPFB people with real cloth, the four-room carousel set, props, look.
blender -b --python 01_build.py -- <src_assets.blend> <logo_dark.png> <out.blend>

World layout: ONE continuous camera that whips between four open rooms built as 90-degree sectors around a hub at the origin.
  OR1     sector theta=0    (looks +Y)  first surgery: the surgeon brands the liver, closes, smirks
  HOME    sector theta=-90  (looks +X)  a week later: she doubles over at home
  OR2     sector theta=180  (looks -Y)  second surgery: a different doctor finds the initials
  HEARING sector theta=+90  (looks -X)  the hearing: he admits it, the gavel comes down
Each sector is modelled in local coords (x right, y outward from the hub) under an empty rotated by theta.
The radial walls between sectors act as the whip-pan wipe. Characters face -Y in their rest pose."""
import bpy, bmesh, sys, math, random, os
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "lib.py")).read())

a = sys.argv[sys.argv.index("--") + 1:]
SRC, LOGO, OUT = a[0], a[1], a[2]
random.seed(5)
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
sc.render.fps = 60
sc.frame_start, sc.frame_end = 1, 1644
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920

# ================================================================== PEOPLE
TSHIRT_M = "elvs_crude_t-shirt_male/elvs_crude_t-shirt_male.mhclo"; TSHIRT_F = "joepal_crude_t-shirt_female/joepal_crude_t-shirt_female.mhclo"
SWEATER = "toigo_fisherman_sweater/toigo_fisherman_sweater.mhclo"; PANTS = "toigo_wool_pants/toigo_wool_pants.mhclo"
CARGO = "cortu_cargo_pants/cortu_cargo_pants.mhclo"; SUIT = "toigo_male_suit_tie_and_jacket/toigo_male_suit_tie_and_jacket.mhclo"
SUIT3 = "toigo_male_suit_3/toigo_male_suit_3.mhclo"
PAT, PB = human("Patient", 0.0, 0.42, {"asian": 0.15, "caucasian": 0.75, "african": 0.10}, "ponytail01/ponytail01.mhclo",
                "young_caucasian_female/young_caucasian_female.mhmat", "eyebrow010/eyebrow010.mhclo", height=0.68, weight=0.45, shoes="shoes01/shoes01.mhclo",
                clothes=[SWEATER, PANTS, TSHIRT_F], cup=0.3)
DOC, DB = human("Surgeon", 1.0, 0.55, {"asian": 0.05, "caucasian": 0.90, "african": 0.05}, "short02/short02.mhclo",
                "middleage_caucasian_male/middleage_caucasian_male.mhmat", "eyebrow004/eyebrow004.mhclo", height=0.55, muscle=0.25, weight=0.45, shoes="shoes02/shoes02.mhclo",
                clothes=[TSHIRT_M, PANTS, SUIT])
DOC2, DB2 = human("Surgeon2", 0.0, 0.5, {"asian": 0.05, "caucasian": 0.10, "african": 0.85}, "short04/short04.mhclo",
                  "young_african_female/young_african_female.mhmat", "eyebrow007/eyebrow007.mhclo", height=0.5, shoes="shoes01/shoes01.mhclo",
                  clothes=[TSHIRT_F, CARGO], cup=0.3)
JUD, JB = human("Judge", 1.0, 0.85, {"asian": 0.05, "caucasian": 0.15, "african": 0.80}, "short01/short01.mhclo",
                "old_african_male/old_african_male.mhmat", "eyebrow001/eyebrow001.mhclo", height=0.5, weight=0.6, muscle=0.3, shoes="shoes02/shoes02.mhclo",
                clothes=[SUIT3])
PEOPLE = ((PAT, PB), (DOC, DB), (DOC2, DB2), (JUD, JB))
for r, b in PEOPLE:
    bake_keys(b); eye_fix(r)
# EnhancedEye cornea: refractive transmission -> transparent mix (LESSONS 3, Connect03 a44130b), every eye group
for g in [g for g in bpy.data.node_groups if g.name.startswith("EnhancedEye")]:
    P = next((n for n in g.nodes if n.type == "BSDF_PRINCIPLED"), None); OUTN = next((n for n in g.nodes if n.type == "GROUP_OUTPUT"), None)
    if P is None or OUTN is None or "CorneaTransparentMix" in g.nodes: continue
    tl = [l for l in g.links if l.to_node == P and l.to_socket.name == "Transmission Weight"]
    src = tl[0].from_socket if tl else None
    for l in tl: g.links.remove(l)
    P.inputs["Transmission Weight"].default_value = 0.0
    ols = [l for l in g.links if l.from_node == P and l.to_node == OUTN]
    if not ols: continue
    out_sock = ols[0].to_socket; g.links.remove(ols[0])
    tr = g.nodes.new("ShaderNodeBsdfTransparent"); mx = g.nodes.new("ShaderNodeMixShader"); mx.name = "CorneaTransparentMix"
    if src: g.links.new(src, mx.inputs[0])
    else: mx.inputs[0].default_value = 0.0
    g.links.new(P.outputs[0], mx.inputs[1]); g.links.new(tr.outputs[0], mx.inputs[2]); g.links.new(mx.outputs[0], out_sock)
    print("EYEFIX", g.name)
# warm, saturated skin (STYLE colour grade) and hair tints
for m in PB.data.materials: tint(m, (1.0, 0.92, 0.86))
for m in DB.data.materials: tint(m, (1.0, 0.92, 0.85))
hair_tints = {PAT: (0.55, 0.25, 0.12), DOC: (0.30, 0.20, 0.13), DOC2: (0.25, 0.18, 0.14)}
for r, t in hair_tints.items():
    for c in r.children:
        if c.type == 'MESH' and any(k in c.name for k in ("ponytail01", "short02", "short04", "eyebrow")):
            for m in c.data.materials: tint(m, t)

# ---- wardrobe: REAL garments (MakeHuman community CC0 clothes), recoloured; body hidden under each with its own mask
def cl(rig, key, newname):
    o = part(rig, key); o.name = newname; return o
P_TOP = cl(PAT, "fisherman_sweater", "PatHome.top"); P_JEANS = cl(PAT, "wool_pants", "PatHome.trousers"); P_GOWN = cl(PAT, "crude_t-shirt_female", "PatGown.top")
colorize(P_TOP, (0.80, 0.05, 0.40)); colorize(P_JEANS, (0.04, 0.08, 0.32)); colorize(P_GOWN, (0.55, 0.78, 0.95))
S1_TOP = cl(DOC, "crude_t-shirt_male", "S1Scrub.top"); S1_TRS = cl(DOC, "wool_pants", "S1Scrub.trousers"); S1_SUIT = cl(DOC, "suit_tie_and_jacket", "S1Suit.top")
colorize(S1_TOP, (0.02, 0.50, 0.55)); colorize(S1_TRS, (0.02, 0.40, 0.46))
S2_TOP = cl(DOC2, "crude_t-shirt_female", "S2Scrub.top"); S2_TRS = cl(DOC2, "cargo_pants", "S2Scrub.trousers")
colorize(S2_TOP, (0.42, 0.08, 0.46)); colorize(S2_TRS, (0.34, 0.06, 0.38))
# trousers under a top: the waistband part the top covers is masked (no waistband poking through the knit)
def under_top(trs, top):
    zmin = min(v.co.z for v in top.data.vertices)
    vg = trs.vertex_groups.new(name="under_top"); vg.add([v.index for v in trs.data.vertices if v.co.z > zmin + 0.06], 1.0, 'REPLACE')
    mk = trs.modifiers.new("under_top", 'MASK'); mk.vertex_group = "under_top"; mk.invert_vertex_group = True
under_top(P_JEANS, P_TOP); under_top(S1_TRS, S1_TOP); under_top(S2_TRS, S2_TOP)
for body, gar in ((PB, P_TOP), (PB, P_JEANS), (PB, P_GOWN), (DB, S1_TOP), (DB, S1_TRS), (DB, S1_SUIT), (DB2, S2_TOP), (DB2, S2_TRS), (JB, part(JUD, "suit_3"))):
    hide_by_proximity(body, gar, "Hide." + gar.name)
cap1_m = fabric("M_Cap1", (0.03, 0.52, 0.58), scale=400, bump=0.5); mask_m = fabric("M_Mask", (0.45, 0.72, 0.92), scale=45, bump=0.2)
S1_CAP, S1_MASK, S1_CAPPL, S1_NOSE = cap_and_mask(DOC, DB, "S1", cap1_m, mask_m)
glove_m = mat("M_Glove", (0.18, 0.30, 0.85), rough=0.38, coat=0.25)
def glove_shell(rig, body, name):
    def reg(co, bn):
        if not in_region(bn, HANDS + ("lowerarm02",)): return False
        s = "L" if co.x > 0 else "R"; el = bl(rig, "lowerarm01." + s); wr = bl(rig, "wrist." + s)
        return (Vector(co) - wr).dot((wr - el).normalized()) > -0.06
    g, _ = garment(rig, body, name, reg, [], 0.0015, glove_m, thick=0.0008, folds=0.0)
    g.modifiers.remove(g.modifiers["subd"])
    return g
S1_GLOVES = glove_shell(DOC, DB, "S1.gloves")
# hair: a trimmed copy under the cap (hairline and sideburns show), the full hair for the hearing
S1_HAIR = part(DOC, "short02")
S1_HAIR_CAP = S1_HAIR.copy(); S1_HAIR_CAP.data = S1_HAIR.data.copy(); S1_HAIR_CAP.name = "Surgeon.hair_under_cap"; sc.collection.objects.link(S1_HAIR_CAP)
trim_hair(S1_HAIR_CAP, None, *S1_CAPPL)

cap2_m = fabric("M_Cap2", (0.62, 0.42, 0.85), scale=400, bump=0.5)
S2_CAP, S2_MASK, S2_CAPPL, _ = cap_and_mask(DOC2, DB2, "S2", cap2_m, mask_m)
S2_GLOVES = glove_shell(DOC2, DB2, "S2.gloves")
h2 = part(DOC2, "short04"); trim_hair(h2, None, *S2_CAPPL)

# ================================================================== SET: four sectors around the hub
D = 5.6        # back wall distance
H = 3.0        # ceiling
R0 = 0.16      # radial walls start here (camera whips at the hub)
SECT = {"OR1": 0.0, "HOME": -90.0, "OR2": 180.0, "HEAR": 90.0}
ROOT = {k: empty("SECT_" + k, rot=(0, 0, R_(v))) for k, v in SECT.items()}
bpy.context.view_layer.update()

def wedge_floor(name, parent, material, z=0.0, flip=False):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    vs = [bm.verts.new((0, 0, z)), bm.verts.new((D + 0.2, D + 0.2, z)), bm.verts.new((-D - 0.2, D + 0.2, z))]
    f = bm.faces.new(vs if not flip else vs[::-1])
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=8, use_grid_fill=True)
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o); o.parent = parent; me.materials.append(material)
    return o

def radial_wall(name, parent, side, material, dado_m=None, rail_m=None):
    """the wall along local direction (side*1, 1) from R0 out to the back wall; its inner face belongs to this sector"""
    L = (D * math.sqrt(2)) - R0
    ang = math.atan2(1, side)
    mid = Vector((side, 1, 0)).normalized() * (R0 + L / 2)
    inward = Vector((-side, 1, 0)).normalized() * -1 * 0.03 if False else None
    th = 0.05
    nrm = Vector((-1, 1, 0)).normalized() if side > 0 else Vector((1, 1, 0)).normalized()   # pointing into this sector... (unused)
    o = box(name, (L, th, H), (mid.x, mid.y, H / 2), material, bevel=0, rot=(0, 0, ang))
    # push it half a thickness into this sector's side so the two sectors' wall halves don't overlap
    inn = Vector((-side, 0, 0)) * 0 + (Vector((-1, 1, 0)).normalized() if side > 0 else Vector((1, 1, 0)).normalized())
    off = Vector((math.cos(ang + math.pi / 2), math.sin(ang + math.pi / 2), 0)) * (th / 2)
    if off.dot(Vector((-side, 0.0, 0))) < 0: off = -off
    o.location += off
    o.parent = parent
    if dado_m:
        d = box(name + "_dado", (L, 0.012, 1.0), (mid.x, mid.y, 0.5), dado_m, bevel=0, rot=(0, 0, ang)); d.location += off * 2.3; d.parent = parent
    if rail_m:
        r = box(name + "_rail", (L, 0.04, 0.05), (mid.x, mid.y, 1.0), rail_m, bevel=0.006, rot=(0, 0, ang)); r.location += off * 2.6; r.parent = parent
    # rounded end cap at the hub (reads as a wall corner during the whip)
    return o

def room(key, wall_m, floor_m, ceil_m, dado_m=None, rail_m=None):
    P = ROOT[key]
    wedge_floor(key + "_Floor", P, floor_m)
    wedge_floor(key + "_Ceil", P, ceil_m, z=H, flip=True)
    box(key + "_WallBack", (2 * D + 0.4, 0.08, H), (0, D + 0.04, H / 2), wall_m, bevel=0, parent=P)
    if dado_m: box(key + "_DadoBack", (2 * D + 0.4, 0.012, 1.0), (0, D - 0.006, 0.5), dado_m, bevel=0, parent=P)
    if rail_m: box(key + "_RailBack", (2 * D + 0.4, 0.04, 0.05), (0, D - 0.02, 1.0), rail_m, bevel=0.006, parent=P)
    for s in (1, -1):
        radial_wall(key + "_WallR%+d" % s, P, s, wall_m, dado_m, rail_m)
    return P

# ---------------------------------------------------------------- materials (deep, saturated: STYLE colour)
steel = mat("M_Steel", (0.80, 0.82, 0.85), rough=0.22, metal=1.0)
white = mat("M_White", (0.93, 0.94, 0.95), rough=0.35)
rubber = mat("M_Rubber", (0.06, 0.06, 0.07), rough=0.6)
lampglow = mat("M_LampGlow", (1, 1, 1), emit=((1.0, 0.97, 0.92), 8.0))
screen_dark = mat("M_ScreenDark", (0.01, 0.02, 0.03), rough=0.15)

# ---------------------------------------------------------------- operating rooms (OR1 teal, OR2 deep blue-violet)
def operating_room(key, tileA, tileB, floor_cols, accent):
    wall = tiles("M_%s_Wall" % key, tileA, tileB, (0.80, 0.86, 0.86), scale=4.0, w=0.25, h=0.25)
    flo = tiles("M_%s_Floor" % key, *floor_cols, (0.2, 0.2, 0.22), scale=1.6, w=0.5, h=0.5, rough=0.3, coat=0.35)
    ceil = mat("M_%s_Ceil" % key, (0.85, 0.88, 0.90), rough=0.6)
    P = room(key, wall, flo, ceil)
    # overhead surgical light (dome + arm), high and out of the working frames
    cyl(key + "_LampArm", 0.03, 0.9, (0.3, 2.9, 2.6), white, rot=(R_(90), 0, R_(20)), parent=P)
    dome = cyl(key + "_LampDome", 0.34, 0.12, (0.25, 2.55, 2.55), white, bevel=0.03, parent=P)
    cyl(key + "_LampGlow", 0.30, 0.01, (0.25, 2.55, 2.485), lampglow, parent=P)
    cyl(key + "_LampPost", 0.035, 0.45, (0.25, 2.55, 2.8), white, parent=P)
    # monitors on a boom at the back wall with live traces (emissive), an IV pole, an anaesthesia cart, cabinets
    for i, (x, col) in enumerate(((-1.55, (0.1, 1.0, 0.35)), (1.7, (1.0, 0.85, 0.1)))):
        box(key + "_MonBody%d" % i, (0.62, 0.06, 0.42), (x, D - 0.25, 1.75), mat("M_MonCase", (0.12, 0.13, 0.15), rough=0.4), bevel=0.012, parent=P)
        scr = box(key + "_MonScreen%d" % i, (0.56, 0.01, 0.36), (x, D - 0.285, 1.75), screen_dark, bevel=0, parent=P)
        for j in range(3):
            pts = [(x - 0.25 + 0.5 * k / 40.0, D - 0.292, 1.86 - j * 0.1 + 0.025 * (math.sin(k * 1.7 + j) if k % 9 else 2.2)) for k in range(41)]
            tr = curve_tube(key + "_Trace%d%d" % (i, j), pts, 0.0035, mat("M_Trace%d%d" % (i, j), col, emit=(col, 6.0)), parent=P)
            tr.data.bevel_factor_mapping_end = 'SPLINE'
        cyl(key + "_MonArm%d" % i, 0.025, 0.5, (x, D - 0.12, 2.05), white, rot=(R_(90), 0, 0), parent=P)
    cyl(key + "_IVPole", 0.012, 1.9, (-1.35, 3.6, 0.95), steel, parent=P)
    cyl(key + "_IVBase", 0.22, 0.03, (-1.35, 3.6, 0.02), steel, parent=P)
    bag = box(key + "_IVBag", (0.12, 0.03, 0.2), (-1.30, 3.6, 1.75), mat("M_IVBag", (0.75, 0.88, 0.95), rough=0.15, alpha=0.8), bevel=0.02, parent=P)
    box(key + "_Cart", (0.6, 0.45, 0.95), (2.15, 4.4, 0.475), mat("M_%s_Cart" % key, accent, rough=0.35, coat=0.3), bevel=0.02, parent=P)
    for k in range(3):
        box(key + "_CartDrawer%d" % k, (0.5, 0.01, 0.22), (2.15, 4.17, 0.2 + k * 0.28), white, bevel=0.005, parent=P)
    box(key + "_Cabinet", (1.4, 0.45, 2.0), (-2.6, D - 0.25, 1.0), white, bevel=0.01, parent=P)
    for k in range(2):
        box(key + "_CabGlass%d" % k, (0.62, 0.01, 1.0), (-2.95 + k * 0.7, D - 0.48, 1.35), mat("M_CabGlass", (0.55, 0.75, 0.85), rough=0.1, alpha=0.6), bevel=0, parent=P)
    # wall-mounted doors (swing doors with portholes) at the right of the back wall
    box(key + "_Door", (1.2, 0.05, 2.2), (0.9, D - 0.03, 1.1), mat("M_%s_Door" % key, accent, rough=0.3, coat=0.4), bevel=0.01, parent=P)
    for dx in (-0.3, 0.3):
        cyl(key + "_Port", 0.11, 0.02, (0.9 + dx, D - 0.06, 1.55), mat("M_Port", (0.6, 0.8, 0.95), rough=0.05, emit=((0.6, 0.85, 1.0), 1.5)), rot=(R_(90), 0, 0), parent=P)
    return P

OR1 = operating_room("OR1", (0.02, 0.42, 0.45), (0.03, 0.47, 0.50), ((0.30, 0.36, 0.40), (0.26, 0.32, 0.36)), (0.95, 0.55, 0.05))
OR2 = operating_room("OR2", (0.10, 0.14, 0.52), (0.12, 0.17, 0.58), ((0.36, 0.34, 0.42), (0.31, 0.29, 0.37)), (0.05, 0.70, 0.55))

# ---------------------------------------------------------------- the patient stage (table, mattress, pillow): moves OR1 -> OR2 with her
STAGE = empty("PATIENT_STAGE")
TABLE_TOP = 0.86
TABLE_C = Vector((-0.30, 2.60))
TABLE_L, TABLE_W = 2.0, 0.52
tbl_m = mat("M_TableBase", (0.20, 0.22, 0.26), rough=0.35, metal=0.6)
mat_m = mat("M_Mattress", (0.05, 0.12, 0.22), rough=0.5, coat=0.2)
box("Table_Column", (0.30, 0.22, 0.62), (TABLE_C.x, TABLE_C.y, 0.31 + 0.05), tbl_m, bevel=0.02, parent=STAGE)
box("Table_Base", (0.80, 0.42, 0.08), (TABLE_C.x, TABLE_C.y, 0.04), tbl_m, bevel=0.02, parent=STAGE)
box("Table_Frame", (TABLE_L, TABLE_W, 0.12), (TABLE_C.x, TABLE_C.y, TABLE_TOP - 0.06 - 0.06), steel, bevel=0.01, parent=STAGE)
box("Table_Mattress", (TABLE_L, TABLE_W, 0.06), (TABLE_C.x, TABLE_C.y, TABLE_TOP - 0.03), mat_m, bevel=0.025, segs=4, parent=STAGE)

# ---------------------------------------------------------------- HOME: deep teal walls, warm floor, mustard sofa, window
home_wall = mat("M_HomeWall", (0.02, 0.38, 0.40), rough=0.65)
home_floor = wood("M_HomeFloor", (0.55, 0.30, 0.13), (0.42, 0.20, 0.08), scale=2.5)
home_ceil = mat("M_HomeCeil", (0.92, 0.88, 0.82), rough=0.7)
HOME = room("HOME", home_wall, home_floor, home_ceil, dado_m=mat("M_HomeDado", (0.95, 0.92, 0.86), rough=0.5), rail_m=white)
sky = gradient_emit("M_Sky", (0.25, 0.62, 1.0), (0.85, 0.95, 1.0), strength=2.2)
box("HOME_Window", (1.4, 0.02, 1.3), (1.75, D - 0.02, 1.75), sky, bevel=0, parent=HOME)
for (sx, sz, lx, lz) in ((0.06, 1.42, 1.04, 1.75), (0.06, 1.42, 2.46, 1.75), (1.48, 0.06, 1.75, 2.43), (1.48, 0.08, 1.75, 1.07), (0.04, 1.3, 1.75, 1.75)):
    box("HOME_WinFrame", (sx, 0.06, sz), (lx, D - 0.05, lz), white, bevel=0.006, parent=HOME)
rug = fabric("M_Rug", (0.85, 0.30, 0.08), scale=200, bump=0.6)
box("HOME_Rug", (2.4, 1.6, 0.012), (0.2, 3.9, 0.006), rug, bevel=0.004, parent=HOME)
# side table + lamp + plant (no hand contact, set dressing)
side_m = wood("M_SideTable", (0.75, 0.48, 0.25), (0.55, 0.32, 0.15))
box("HOME_SideTable", (0.45, 0.45, 0.04), (-1.15, 4.9, 0.6), side_m, bevel=0.005, parent=HOME)
for dx in (-0.19, 0.19):
    for dy in (-0.19, 0.19):
        cyl("HOME_STLeg", 0.015, 0.58, (-1.15 + dx, 4.9 + dy, 0.29), side_m, parent=HOME)
cyl("HOME_LampBase", 0.07, 0.3, (-1.15, 4.9, 0.77), mat("M_LampBase", (0.95, 0.75, 0.1), rough=0.3), parent=HOME)
cyl("HOME_LampShade", 0.16, 0.22, (-1.15, 4.9, 1.03), mat("M_Shade", (1.0, 0.92, 0.75), rough=0.8, emit=((1.0, 0.8, 0.5), 1.5)), verts=32, parent=HOME)
pot_m = mat("M_Pot", (0.85, 0.85, 0.82), rough=0.4); leaf_m = mat("M_Leaf", (0.08, 0.45, 0.12), rough=0.5, sss=0.1)
cyl("HOME_Pot", 0.16, 0.36, (2.65, 4.95, 0.18), pot_m, parent=HOME)
for k in range(14):
    rr = random.Random(k)
    a_ = rr.uniform(0, 6.28); h_ = rr.uniform(0.45, 1.0)
    lf = sphere("HOME_Leaf", 0.09, (2.65 + 0.18 * math.cos(a_), 4.95 + 0.18 * math.sin(a_), 0.36 + h_), leaf_m, parent=HOME, segs=12)
    lf.scale = (1.0, 0.35, 0.18); lf.rotation_euler = (rr.uniform(-0.6, 0.6), rr.uniform(-0.8, 0.8), a_)
    cyl("HOME_Stem", 0.006, h_, (2.65 + 0.09 * math.cos(a_), 4.95 + 0.09 * math.sin(a_), 0.36 + h_ / 2), leaf_m, parent=HOME, verts=6)

# wall calendar: a month grid, the last 7 days crossed off in red (a week) - no text
cal_paper = mat("M_CalPaper", (0.97, 0.96, 0.93), rough=0.7)
cal_head = mat("M_CalHead", (0.85, 0.12, 0.10), rough=0.5)
cal_line = mat("M_CalLine", (0.35, 0.35, 0.38), rough=0.7)
cal_x = mat("M_CalX", (0.90, 0.05, 0.05), rough=0.5)
CAL_C = Vector((-0.42, D - 0.05, 1.62))
box("HOME_CalBoard", (0.44, 0.012, 0.56), (CAL_C.x, CAL_C.y, CAL_C.z), cal_paper, bevel=0.002, parent=HOME)
box("HOME_CalHead", (0.44, 0.014, 0.12), (CAL_C.x, CAL_C.y - 0.001, CAL_C.z + 0.22), cal_head, bevel=0.002, parent=HOME)
box("HOME_CalPhoto", (0.30, 0.015, 0.07), (CAL_C.x, CAL_C.y - 0.002, CAL_C.z + 0.22), mat("M_CalPhoto", (0.98, 0.85, 0.30), rough=0.5), bevel=0, parent=HOME)
gx0, gz0, cw, ch = CAL_C.x - 0.20, CAL_C.z + 0.14, 0.40 / 7, 0.36 / 5
for i in range(8):
    box("HOME_CalV", (0.003, 0.016, 0.36), (gx0 + i * cw, CAL_C.y - 0.001, gz0 - 0.18), cal_line, bevel=0, parent=HOME)
for j in range(6):
    box("HOME_CalH", (0.40, 0.016, 0.003), (CAL_C.x, CAL_C.y - 0.001, gz0 - j * ch), cal_line, bevel=0, parent=HOME)
k = 0
for j in range(5):
    for i in range(7):
        k += 1
        cx_, cz_ = gx0 + (i + 0.5) * cw, gz0 - (j + 0.5) * ch
        if 10 <= k <= 16 or k == 3:  # the surgery day ringed (3) and a week crossed off (10..16)
            for sgn in (1, -1):
                box("HOME_CalX", (cw * 0.85, 0.018, 0.006), (cx_, CAL_C.y - 0.002, cz_), cal_x, bevel=0, rot=(0, R_(35 * sgn), 0), parent=HOME)
# framed poster with the DA KRAS FILMS logo (dark logo on a light print) - a natural placement, readable
logo_m = image_mat("M_LogoPoster", LOGO, emit=0.0, rough=0.6, alpha=True)
logo_bg = mat("M_PosterBG", (0.98, 0.86, 0.25), rough=0.6)
POST_C = Vector((0.58, D - 0.04, 1.62))
box("HOME_PosterFrame", (0.66, 0.03, 0.46), (POST_C.x, POST_C.y, POST_C.z), mat("M_PosterFrame", (0.08, 0.08, 0.09), rough=0.4), bevel=0.006, parent=HOME)
box("HOME_PosterBG", (0.60, 0.01, 0.40), (POST_C.x, POST_C.y - 0.016, POST_C.z), logo_bg, bevel=0, parent=HOME)
bpy.ops.mesh.primitive_plane_add(size=1, location=(POST_C.x, POST_C.y - 0.023, POST_C.z), rotation=(R_(90), 0, 0))
lp = bpy.context.active_object; lp.name = "HOME_Logo"; lp.scale = (0.54, 0.54 * 414 / 967, 1); bpy.ops.object.transform_apply(scale=True)
lp.data.materials.append(logo_m); lp.parent = HOME
# sofa (CC-BY asset from v011's set): mustard re-material
with bpy.data.libraries.load(SRC, link=False) as (src, dst):
    dst.objects = [n for n in src.objects]
SRCO = {o.name: o for o in dst.objects if o is not None}
for o in SRCO.values():
    if o.name not in sc.collection.objects: sc.collection.objects.link(o)
for o in list(bpy.data.objects):
    if o.type == 'EMPTY' and o.name.startswith("Gavel"):
        for ch in list(o.children):
            mw = ch.matrix_world.copy(); ch.parent = None; ch.matrix_world = mw
        bpy.data.objects.remove(o, do_unlink=True)
sofa = SRCO["Sofa"]; sofa.parent = None; sofa.matrix_world = Matrix.Identity(4)
sofa.data.materials.clear(); sofa.data.materials.append(fabric("M_Sofa", (0.95, 0.55, 0.05), scale=300, bump=0.5))
bb = [Vector(c) for c in sofa.bound_box]; mn = Vector([min(v[i] for v in bb) for i in range(3)]); mx_ = Vector([max(v[i] for v in bb) for i in range(3)])
sofa.data.transform(Matrix.Translation(Vector((-(mn.x + mx_.x) / 2, -(mn.y + mx_.y) / 2, -mn.z))))
sofa.location = (-2.05, 3.6, 0); sofa.rotation_euler = (0, 0, R_(0)); sofa.parent = HOME
print("SOFA dims", tuple(round(d, 2) for d in sofa.dimensions))

# ---------------------------------------------------------------- HEARING ROOM: deep green walls, wood panelling, bench, evidence screen
hear_wall = mat("M_HearWall", (0.04, 0.30, 0.16), rough=0.6)
hear_floor = wood("M_HearFloor", (0.30, 0.13, 0.05), (0.20, 0.08, 0.03), scale=2.0)
panel_w = wood("M_Panel", (0.45, 0.20, 0.07), (0.32, 0.13, 0.04), scale=4.0)
HEAR = room("HEAR", hear_wall, hear_floor, mat("M_HearCeil", (0.88, 0.85, 0.78), rough=0.7), dado_m=panel_w, rail_m=wood("M_Rail", (0.30, 0.12, 0.04), (0.22, 0.08, 0.03)))
# the bench (judge's desk) - local: judge sits at (-1.25, 3.7) facing +x
BENCH = Vector((-0.80, 3.70))
box("HEAR_BenchTop", (0.62, 1.8, 0.05), (BENCH.x, BENCH.y, 0.80), panel_w, bevel=0.01, parent=HEAR)
box("HEAR_BenchFront", (0.05, 1.8, 0.78), (BENCH.x + 0.29, BENCH.y, 0.39), panel_w, bevel=0.005, parent=HEAR)
for dy in (-0.88, 0.88):
    box("HEAR_BenchSide", (0.6, 0.04, 0.78), (BENCH.x, BENCH.y + dy, 0.39), panel_w, bevel=0.005, parent=HEAR)
chair_m = mat("M_Leather", (0.45, 0.04, 0.05), rough=0.4, coat=0.3)
CHAIR = Vector((-1.38, 3.70))
box("HEAR_ChairSeat", (0.5, 0.5, 0.09), (CHAIR.x, CHAIR.y, 0.47), chair_m, bevel=0.03, parent=HEAR)
box("HEAR_ChairBack", (0.10, 0.52, 0.85), (CHAIR.x - 0.27, CHAIR.y, 0.93), chair_m, bevel=0.035, parent=HEAR)
cyl("HEAR_ChairCol", 0.04, 0.42, (CHAIR.x, CHAIR.y, 0.21), steel, parent=HEAR)
cyl("HEAR_ChairFoot", 0.26, 0.03, (CHAIR.x, CHAIR.y, 0.02), steel, parent=HEAR)
# papers + a closed folder on the bench, a water glass
box("HEAR_Folder", (0.24, 0.32, 0.012), (BENCH.x - 0.05, BENCH.y + 0.42, 0.831), mat("M_Folder", (0.85, 0.55, 0.10), rough=0.6), bevel=0.002, parent=HEAR)
box("HEAR_Papers", (0.21, 0.30, 0.006), (BENCH.x - 0.02, BENCH.y - 0.45, 0.828), cal_paper, bevel=0.001, rot=(0, 0, R_(8)), parent=HEAR)
cyl("HEAR_Glass", 0.032, 0.11, (BENCH.x - 0.12, BENCH.y + 0.70, 0.88), mat("M_Glass", (0.8, 0.9, 0.95), rough=0.05, alpha=0.35), parent=HEAR)
# the gavel and its sound block (ours): block rests on the bench; the gavel is gripped in stage B
gav_w = wood("M_Gavel", (0.42, 0.16, 0.05), (0.28, 0.09, 0.03), scale=6.0, rough=0.3)
BLK = cyl("GavelBlock", 0.075, 0.035, (BENCH.x + 0.02, BENCH.y - 0.22, 0.825 + 0.0175), gav_w, bevel=0.006, verts=48, parent=HEAR)
gparts = [cyl("Gv_handle", 0.0115, 0.24, (0, -0.12 - 0.02, 0), gav_w, rot=(R_(90), 0, 0), verts=20),
          cyl("Gv_head", 0.030, 0.13, (0, 0, 0), gav_w, verts=32, bevel=0.004),
          cyl("Gv_band1", 0.0315, 0.012, (0, 0, 0.042), mat("M_GavelBand", (0.85, 0.65, 0.15), rough=0.25, metal=0.8), verts=32),
          cyl("Gv_band2", 0.0315, 0.012, (0, 0, -0.042), bpy.data.materials["M_GavelBand"], verts=32),
          cyl("Gv_knob", 0.014, 0.02, (0, -0.265, 0), gav_w, rot=(R_(90), 0, 0), verts=20, bevel=0.004)]
bpy.ops.object.select_all(action='DESELECT')
for o in gparts: o.select_set(True)
bpy.context.view_layer.objects.active = gparts[1]; bpy.ops.object.join(); GAV = bpy.context.active_object; GAV.name = "Gavel"
# the evidence screen on the back wall: three branded livers (texture made in stage B from the liver model)
box("HEAR_ScreenCase", (1.5, 0.06, 0.9), (3.2, D - 0.05, 1.75), mat("M_ScrCase", (0.05, 0.05, 0.06), rough=0.3), bevel=0.01, parent=HEAR)
box("HEAR_Screen", (1.42, 0.01, 0.82), (3.2, D - 0.085, 1.75), screen_dark, bevel=0, parent=HEAR)
# bookshelves and a window
shelf_m = wood("M_Shelf", (0.40, 0.18, 0.06), (0.28, 0.11, 0.04))
for sx in (-2.6,):
    box("HEAR_Shelf", (1.4, 0.35, 2.1), (sx, D - 0.2, 1.05), shelf_m, bevel=0.01, parent=HEAR)
    for row in range(4):
        x = sx - 0.62
        while x < sx + 0.6:
            w_ = random.uniform(0.03, 0.06); h_ = random.uniform(0.22, 0.32)
            col = random.choice(((0.6, 0.05, 0.05), (0.05, 0.2, 0.55), (0.1, 0.4, 0.15), (0.85, 0.6, 0.1), (0.3, 0.1, 0.35)))
            box("HEAR_Book", (w_, 0.22, h_), (x + w_ / 2, D - 0.25, 0.25 + row * 0.5 + h_ / 2), mat("M_Book%d" % (hash(col) % 1000), col, rough=0.6), bevel=0.003, parent=HEAR)
            x += w_ + 0.004
box("HEAR_Window", (0.02, 1.2, 1.3), (0, 0, 0), sky, bevel=0, parent=HEAR)  # placed below on the left radial wall
win = bpy.data.objects["HEAR_Window"]
win.rotation_euler = (0, 0, R_(45)); win.location = Vector((-1, 1, 0)).normalized() * 3.6 + Vector((0, 0, 1.75)) + Vector((1, 1, 0)).normalized() * 0.02
# DA KRAS FILMS plaque on the panelled wall behind the judge (white logo on the dark wood)
logo_w = image_mat("M_LogoPlaque", LOGO.replace("_dark", "_white"), emit=0.6, rough=0.5)
bpy.ops.mesh.primitive_plane_add(size=1)
pl = bpy.context.active_object; pl.name = "HEAR_Logo"; pl.scale = (0.72, 0.72 * 414 / 967, 1); bpy.ops.object.transform_apply(scale=True)
pl.data.materials.append(logo_w); pl.parent = HEAR
# radial wall on the judge's side is the (-1,1) diagonal; the plaque hangs on it above and behind the judge
wpos = Vector((-1, 1, 0)).normalized() * 4.95
pl.location = (wpos.x + 0.035, wpos.y + 0.035, 1.95); pl.rotation_euler = (R_(90), 0, R_(135))
box("HEAR_PlaqueBoard", (0.84, 0.02, 0.42), (wpos.x + 0.025, wpos.y + 0.025, 1.95), mat("M_PlaqueBoard", (0.10, 0.05, 0.03), rough=0.35, coat=0.4), bevel=0.008, rot=(0, 0, R_(-45)), parent=HEAR)
# ---------------------------------------------------------------- the liver (CC-BY asset) + the open abdomen pieces are fitted in stage B
LIV = SRCO["Liver"]; LIV.parent = None
bb = [Vector(c) for c in LIV.bound_box]; mn = Vector([min(v[i] for v in bb) for i in range(3)]); mx_ = Vector([max(v[i] for v in bb) for i in range(3)])
LIV.data.transform(Matrix.Translation(-(mn + mx_) / 2)); LIV.location = (0, 0, 0); LIV.rotation_euler = (0, 0, 0); LIV.scale = (1, 1, 1)
print("LIVER dims", tuple(round(d, 3) for d in LIV.dimensions))
for n in ("Gavel_src_1", "Gavel_src_2", "Gavel_src_3", "Gavel_src_4"):
    if n in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[n], do_unlink=True)

# ================================================================== look: AgX Punchy, deep saturated, fast render settings
sc.view_settings.view_transform = 'AgX'
try: sc.view_settings.look = 'AgX - Punchy'
except Exception: pass
sc.view_settings.exposure = -0.55
sc.render.engine = 'CYCLES'
sc.cycles.samples = 64; sc.cycles.adaptive_threshold = 0.04; sc.cycles.use_adaptive_sampling = True; sc.cycles.use_denoising = True
sc.cycles.denoiser = 'OPENIMAGEDENOISE'
sc.cycles.max_bounces = 6; sc.cycles.diffuse_bounces = 3; sc.cycles.glossy_bounces = 3; sc.cycles.transmission_bounces = 6
sc.cycles.transparent_max_bounces = 16; sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
sc.render.use_persistent_data = True
sc.render.use_simplify = True; sc.render.simplify_subdivision_render = 2; sc.cycles.texture_limit_render = '2048'
sc.render.use_motion_blur = False
w = bpy.data.worlds.new("World"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.6, 0.75, 0.9, 1)
w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.25

def area(name, loc, target, power, size, col, parent):
    ld = bpy.data.lights.new(name, 'AREA'); ld.energy = power; ld.size = size; ld.color = col; ld.shape = 'DISK'
    o = bpy.data.objects.new(name, ld); sc.collection.objects.link(o); o.parent = parent; o.location = loc
    d = Vector(target) - Vector(loc); o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return o
for key, P in (("OR1", OR1), ("OR2", OR2)):
    area(key + "_Key", (-1.2, 1.2, 2.6), (0.0, 2.8, 1.1), 320, 1.6, (1.0, 0.95, 0.88), P)
    area(key + "_Fill", (1.6, 1.4, 1.8), (0.0, 2.8, 1.2), 110, 2.0, (0.85, 0.93, 1.0), P)
    area(key + "_Rim", (0.4, 4.6, 2.5), (0.1, 3.0, 1.4), 220, 1.4, (1.0, 0.96, 0.92), P)
    area(key + "_Top", (0.25, 2.55, 2.45), (0.25, 2.55, 0.0), 90, 0.6, (1.0, 0.98, 0.95), P)
area("HOME_Key", (-1.0, 2.2, 2.4), (0.3, 4.5, 1.2), 300, 1.6, (1.0, 0.90, 0.78), HOME)
area("HOME_Fill", (1.8, 2.6, 1.8), (0.2, 4.5, 1.2), 120, 2.0, (0.80, 0.90, 1.0), HOME)
area("HOME_Win", (1.75, D - 0.4, 1.9), (0.3, 4.2, 1.0), 160, 1.2, (0.75, 0.88, 1.0), HOME)
area("HEAR_Key", (0.2, 1.6, 2.6), (0.4, 3.8, 1.3), 320, 1.6, (1.0, 0.90, 0.75), HEAR)
area("HEAR_Fill", (-0.4, 2.4, 2.2), (-1.2, 3.7, 1.2), 160, 1.6, (1.0, 0.92, 0.82), HEAR)
area("HEAR_Rim", (1.8, 5.0, 2.5), (1.0, 3.6, 1.5), 180, 1.2, (0.85, 0.92, 1.0), HEAR)
area("HEAR_CornerR", (2.6, 4.4, 2.7), (3.0, 5.4, 1.2), 260, 1.6, (1.0, 0.88, 0.70), HEAR)
area("HEAR_CornerL", (-2.2, 4.2, 2.7), (-3.0, 4.6, 1.2), 260, 1.6, (1.0, 0.88, 0.70), HEAR)
area("HEAR_Ceil", (0.0, 3.6, 2.9), (0.0, 3.6, 0.0), 220, 2.5, (1.0, 0.95, 0.88), HEAR)

sc["D"] = D; sc["TABLE_TOP"] = TABLE_TOP; sc["TABLE_C"] = list(TABLE_C)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("BUILD_OK", OUT)
for r in (PAT, DOC, DOC2, JUD):
    print("BONES", r.name, {n: tuple(round(x, 3) for x in r.data.bones[n].head_local) for n in ("head", "neck01", "spine03", "upperarm01.R", "wrist.R", "pelvis.L", "foot.L")},
          "zmax", round(max(v.co.z for v in [b for b in r.children if b.name.endswith('.body')][0].data.vertices), 3))
