"""PrisonKeyCake v011 stage A: sets, three characters (one model each), props, look. Built from scratch.
blender -b --python 01_build.py -- <out.blend>
Layout (metres, Z up). The PRISON island is one connected set:
  CELL       x -1.5..1.5, y -1.9..1.6. Door in the right wall (x=1.5), opening y 0.2..1.1, hinge at y=1.1, opens to +X.
  CORRIDOR   x 1.5..9.3, y -0.1..1.5, ceiling 3.1, two barred gates (x=4.0, x=6.6) hinged at y=1.5, swinging to +X.
  GATEHOUSE  outer wall x 9.3..9.8 with the big gate and a wicket door (y 0.3..1.1) hinged at y=1.1, opening to +X.
  LANE       x 9.8..13.5 (cobbles), torches on the prison wall.
  WORKSHOP   x 13.5..18.0, y -2.0..3.5, door in the west wall (y 0.3..1.4); bench, forge, crucible, logo board.
The STEPS island (years later) sits at x=40: steps rising to +Y, columns, doors, two tricolour flags."""
import bpy, bmesh, sys, math, random, json
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
exec(open("/home/user/Muhammed/blender/PrisonKeyCake_v011/scripts/lib_build.py").read())
OUT = sys.argv[sys.argv.index("--") + 1:][0]
random.seed(6)
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
sc = bpy.context.scene
sc.render.fps = 60
sc.frame_start, sc.frame_end = 1, 1836
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
LOGO_DARK = "/home/user/Muhammed/blender/assets/brand/DaKrasFilms_logo_dark.png"

# ================================================================== characters
RACE = {"asian": 0.03, "caucasian": 0.92, "african": 0.05}
PRIS, PB = human("Pris", 1.0, 0.45, RACE, "short02/short02.mhclo", "young_caucasian_male/young_caucasian_male.mhmat",
                 "eyebrow001/eyebrow001.mhclo", height=0.55, weight=0.45, muscle=0.5,
                 clothes=["male_casualsuit03/male_casualsuit03.mhclo", "male_elegantsuit01/male_elegantsuit01.mhclo", "shoes03/shoes03.mhclo"])
VIS, VB = human("Vis", 0.0, 0.45, {"asian": 0.05, "caucasian": 0.9, "african": 0.05}, "ponytail01/ponytail01.mhclo",
                "young_caucasian_female/young_caucasian_female.mhmat", "eyebrow010/eyebrow010.mhclo", height=0.45, weight=0.45,
                clothes=["female_elegantsuit01/female_elegantsuit01.mhclo", "shoes01/shoes01.mhclo"])
SMITH, SB = human("Smith", 1.0, 0.62, RACE, "short01/short01.mhclo", "middleage_caucasian_male/middleage_caucasian_male.mhmat",
                  "eyebrow002/eyebrow002.mhclo", height=0.5, weight=0.6, muscle=0.6,
                  clothes=["male_worksuit01/male_worksuit01.mhclo", "shoes03/shoes03.mhclo"])
for r, b in ((PRIS, PB), (VIS, VB), (SMITH, SB)):
    bake_keys(b); eye_fix(r)
eye_group_fix()

def flatten_chest(rig, body, keep=0.0):
    """male chest: push breast-weighted vertices back to the sternum plane BEFORE dressing (05 lesson)"""
    me = body.data
    gi = {body.vertex_groups[n].index for n in ("breast.L", "breast.R") if n in body.vertex_groups}
    mids = [v for v in me.vertices if abs(v.co.x) < 0.012 and 1.12 < v.co.z < 1.42 and v.co.y < 0.0 and v.normal.y < -0.5]
    def ster(z):
        near = sorted(mids, key=lambda v: abs(v.co.z - z))[:4]
        return sum(v.co.y for v in near) / max(1, len(near))
    n = 0
    for v in me.vertices:
        w = max([g.weight for g in v.groups if g.group in gi] or [0.0])
        if w <= 0.02 or v.co.y > 0.02: continue
        lim = ster(v.co.z) + 0.10 * v.co.x * v.co.x / 0.04 * 0.25     # gentle curvature toward the sides
        if v.co.y < lim:
            u = min(1.0, w * 2.5)
            target = lim + (v.co.y - lim) * keep
            v.co.y = v.co.y + (target - v.co.y) * u; n += 1
    me.update(); print("CHEST flattened", rig.name, n)
flatten_chest(PRIS, PB); flatten_chest(SMITH, SB)

HAIR = {PRIS: (0.20, 0.11, 0.06), SMITH: (0.30, 0.26, 0.22), VIS: (0.55, 0.13, 0.03)}
for rig, col in HAIR.items():
    for c in rig.children:
        if c.type == 'MESH' and any(k in c.name.lower() for k in ("short", "pony", "eyebrow")):
            for m in c.data.materials: tint(m, col)
for b in (PB, VB, SB):
    for m in b.data.materials: tint(m, (1.0, 0.82, 0.68))
for rig in (PRIS, VIS, SMITH):
    for c in rig.children:
        if c.type == 'MESH' and "teeth" in c.name:
            for m in c.data.materials: tint(m, (1.5, 1.45, 1.4))

def wardrobe(rig, body, top_m, bot_m, hem_drop, top_off, bot_off, top_folds, bot_folds, prefix, collar=0.03, hide=True, thick=0.003):
    hip = bl(rig, "pelvis.L").z; neck = bl(rig, "neck01")
    cuts_top = [((0, 0, hip - hem_drop), (0, 0, -1)), ((0, neck.y, neck.z - collar), (0, -0.35, 1))]
    arm_cut = {}
    for s in "LR":
        el = bl(rig, "lowerarm01." + s); wr = bl(rig, "wrist." + s)
        dvec = (wr - el).normalized(); p0 = wr - dvec * 0.015
        arm_cut[s] = (p0, dvec); cuts_top.append((p0, dvec))
    def top_region(co, bn):
        if bn is None or in_region(bn, HEADB + ("lowerleg", "foot", "toe") + HANDS): return False
        if plane_side(co, *cuts_top[0]) > 1e-5 or plane_side(co, *cuts_top[1]) > 1e-5: return False
        if in_region(bn, ARM) or in_region(bn, ("shoulder", "clavicle")):
            s = "L" if co.x > 0 else "R"
            if plane_side(co, *arm_cut[s]) > 1e-5: return False
        return True
    top, cov_t = garment(rig, body, prefix + ".top", top_region, cuts_top, top_off, top_m, folds=top_folds, thick=thick)
    ank = {s: bl(rig, "foot." + s).z + 0.06 for s in "LR"}
    cuts_bot = [((0, 0, hip + 0.07), (0, 0, 1)), ((0, 0, ank["L"]), (0, 0, -1))]
    def bot_region(co, bn):
        if bn is None: return ank["L"] < co.z < hip + 0.07 and abs(co.x) < 0.12
        if in_region(bn, HEADB + ARM + ("clavicle", "shoulder", "breast", "foot", "toe")): return False
        if in_region(bn, ("spine03", "spine04", "spine05")) and co.z > hip - 0.01: return False
        if plane_side(co, *cuts_bot[0]) > 1e-5 or plane_side(co, *cuts_bot[1]) > 1e-5: return False
        return True
    bot, cov_b = garment(rig, body, prefix + ".trousers", bot_region, cuts_bot, bot_off, bot_m, folds=bot_folds)
    mk = hide_under(body, cov_t | cov_b, name="hide_" + prefix) if hide else None
    return top, bot, mk, cov_t | cov_b

def shoes(rig, body, col, prefix):
    m = mat("M_Shoe" + prefix, col, rough=0.35, coat=0.3)
    ank = bl(rig, "foot.L").z + 0.075
    def reg(co, bn, ank=ank): return in_region(bn, ("foot", "toe", "lowerleg")) and co.z <= ank
    sh, cov = garment(rig, body, rig.name + ".shoes", reg, [((0, 0, ank), (0, 0, 1))], 0.006, m, thick=0.004)
    hide_under(body, cov, name="hide_shoes", rings=2)
    return sh

# Clothes are REAL MakeHuman/MPFB garment assets (separate pieces with folds and volume; MPFB hides the body under them
# with their delete groups): prisoner = striped shirt + jeans + boots, later the elegant suit (switched inside the flash);
# visitor = striped blouse + skirt + shoes; locksmith = work overalls + boots.

# ================================================================== materials for sets
def brickmat(name, c1, c2, mortar, scale=3.0, bw=0.5, rh=0.25, msize=0.02, rough=0.8, bump=0.25, vertical=True):
    m = mat(name, c1, rough=rough)
    nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    br = nt.nodes.new("ShaderNodeTexBrick"); br.inputs["Scale"].default_value = scale; br.offset = 0.5
    br.inputs["Color1"].default_value = (*c1, 1); br.inputs["Color2"].default_value = (*c2, 1)
    br.inputs["Mortar"].default_value = (*mortar, 1); br.inputs["Mortar Size"].default_value = msize
    br.inputs["Brick Width"].default_value = bw; br.inputs["Row Height"].default_value = rh
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 18.0
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'OVERLAY'; mx.inputs['Factor'].default_value = 0.25
    if vertical:   # walls: bricks run along the wall (x+y) and stack in z
        se = nt.nodes.new("ShaderNodeSeparateXYZ"); ad = nt.nodes.new("ShaderNodeMath"); ad.operation = 'ADD'
        co = nt.nodes.new("ShaderNodeCombineXYZ")
        nt.links.new(tc.outputs["Object"], se.inputs[0]); nt.links.new(se.outputs["X"], ad.inputs[0]); nt.links.new(se.outputs["Y"], ad.inputs[1])
        nt.links.new(ad.outputs[0], co.inputs["X"]); nt.links.new(se.outputs["Z"], co.inputs["Y"])
        nt.links.new(co.outputs[0], br.inputs["Vector"])
    else:
        nt.links.new(tc.outputs["Object"], br.inputs["Vector"])
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    nt.links.new(br.outputs["Color"], mx.inputs['A']); nt.links.new(nz.outputs["Color"], mx.inputs['B'])
    nt.links.new(mx.outputs['Result'], p.inputs["Base Color"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump; bp.inputs["Distance"].default_value = 0.01
    nt.links.new(br.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], p.inputs["Normal"])
    return m

def woodmat(name, c1, c2, scale=6.0, rough=0.45):
    m = mat(name, c1, rough=rough, coat=0.15)
    nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1, 8, 1)
    wv = nt.nodes.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = scale; wv.inputs["Distortion"].default_value = 6.0
    wv.inputs["Detail"].default_value = 3.0
    cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (*c1, 1); cr.color_ramp.elements[1].color = (*c2, 1)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"]); nt.links.new(mp.outputs["Vector"], wv.inputs["Vector"])
    nt.links.new(wv.outputs["Fac"], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], p.inputs["Base Color"])
    return m

stone_cell = brickmat("M_CellStone", (0.05, 0.20, 0.30), (0.04, 0.15, 0.25), (0.02, 0.07, 0.11), scale=2.2, bw=0.55, rh=0.28, msize=0.015)
stone_cor = brickmat("M_CorStone", (0.10, 0.12, 0.34), (0.07, 0.09, 0.28), (0.03, 0.03, 0.10), scale=2.2, bw=0.55, rh=0.28, msize=0.015)
stone_out = brickmat("M_OutStone", (0.42, 0.20, 0.10), (0.36, 0.16, 0.08), (0.16, 0.07, 0.04), scale=1.6, bw=0.6, rh=0.3, msize=0.012)
flag_m = brickmat("M_Flags", (0.36, 0.13, 0.05), (0.30, 0.10, 0.04), (0.12, 0.05, 0.02), scale=1.2, bw=0.5, rh=0.5, msize=0.02, vertical=False)
cobble = brickmat("M_Cobble", (0.24, 0.20, 0.30), (0.20, 0.16, 0.26), (0.06, 0.05, 0.08), scale=7.0, bw=0.5, rh=0.4, msize=0.05, bump=0.4, vertical=False)
redbrick = brickmat("M_RedBrick", (0.55, 0.10, 0.04), (0.45, 0.08, 0.03), (0.30, 0.22, 0.16), scale=9.0, bw=0.5, rh=0.25, msize=0.03)
plaster = mat("M_ShopPlaster", (0.80, 0.42, 0.10), rough=0.8)
wood = woodmat("M_Wood", (0.42, 0.20, 0.07), (0.30, 0.13, 0.04))
wood_dark = woodmat("M_WoodDark", (0.20, 0.08, 0.03), (0.13, 0.05, 0.02))
iron_red = mat("M_IronDoor", (0.38, 0.05, 0.02), rough=0.45, metal=0.6)
iron = mat("M_Iron", (0.06, 0.06, 0.07), rough=0.35, metal=1.0)
brass = mat("M_Brass", (0.85, 0.55, 0.12), rough=0.25, metal=1.0)
steel = mat("M_Steel", (0.80, 0.82, 0.86), rough=0.22, metal=1.0)
blanket = fabric("M_Blanket", (0.60, 0.04, 0.05), scale=300, bump=0.4)
sand_m = mat("M_Sand", (0.62, 0.34, 0.12), rough=0.9)
nt = sand_m.node_tree; p = nt.nodes["Principled BSDF"]; nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 300
bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.3; nt.links.new(nz.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], p.inputs["Normal"])

def sky_mat(name, bottom, top, strength=1.5):
    m = mat(name, top, emit=(top, strength))
    nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); ramp = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0]); nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
    ramp.color_ramp.elements[0].color = (*bottom, 1); ramp.color_ramp.elements[1].color = (*top, 1)
    nt.links.new(ramp.outputs["Color"], p.inputs["Emission Color"]); nt.links.new(ramp.outputs["Color"], p.inputs["Base Color"])
    return m

# ================================================================== helpers
def wall(name, x0, x1, y0, y1, z0, z1, m, holes=()):
    """axis-aligned slab with rectangular holes, as a few boxes (holes: (a0, a1, z0, z1) along its long axis)"""
    along_x = (x1 - x0) >= (y1 - y0)
    a0, a1 = (x0, x1) if along_x else (y0, y1)
    pieces = []
    cuts = sorted(holes)
    cur = a0
    def add(p0, p1, zz0, zz1):
        if p1 - p0 < 1e-3 or zz1 - zz0 < 1e-3: return
        if along_x: o = box(name, (p1 - p0, y1 - y0, zz1 - zz0), ((p0 + p1) / 2, (y0 + y1) / 2, (zz0 + zz1) / 2), m, bevel=0)
        else: o = box(name, (x1 - x0, p1 - p0, zz1 - zz0), ((x0 + x1) / 2, (p0 + p1) / 2, (zz0 + zz1) / 2), m, bevel=0)
        pieces.append(o)
    for (h0, h1, hz0, hz1) in cuts:
        add(cur, h0, z0, z1); add(h0, h1, z0, hz0); add(h0, h1, hz1, z1); cur = h1
    add(cur, a1, z0, z1)
    return pieces

def join(objs, name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
        for md in list(o.modifiers):
            bpy.context.view_layer.objects.active = o
            try: bpy.ops.object.modifier_apply(modifier=md.name)
            except Exception: pass
    bpy.context.view_layer.objects.active = objs[0]
    for o in objs: o.select_set(True)
    if len(objs) > 1: bpy.ops.object.join()
    o = bpy.context.active_object; o.name = name; return o

def origin_to(o, p):
    p = Vector(p); o.data.transform(Matrix.Translation(-(p - o.location)) if False else Matrix.Translation(o.matrix_world.inverted() @ p * -1))
    o.location = p

def set_origin(o, world_p):
    """move the object's origin to world_p without moving its geometry"""
    w = Vector(world_p); local = o.matrix_world.inverted() @ w
    o.data.transform(Matrix.Translation(-local)); o.location = w if o.parent is None else o.location + (o.matrix_world.to_3x3() @ local)

# ================================================================== CELL
CELL = []
def C(o):
    for x in (o if isinstance(o, list) else [o]): CELL.append(x)
    return o
C(box("CELL_Floor", (3.2, 3.6, 0.1), (0, -0.15, -0.05), flag_m, bevel=0))
C(wall("CELL_WallBack", -1.6, 1.6, 1.6, 1.8, 0, 2.9, stone_cell, holes=[(-0.85, -0.35, 1.75, 2.2)]))
C(wall("CELL_WallLeft", -1.7, -1.5, -1.9, 1.8, 0, 2.9, stone_cell))
C(wall("CELL_WallRight", 1.5, 1.7, -1.9, 1.8, 0, 2.9, stone_cell, holes=[(0.2, 1.1, 0.0, 2.05)]))
C(wall("CELL_WallFront", -1.7, 1.7, -2.1, -1.9, 0, 2.9, stone_cell))
C(box("CELL_Ceiling", (3.4, 3.8, 0.12), (0, -0.05, 2.96), stone_cell, bevel=0))
# window: bars + night/dawn sky behind
WIN_SKY = C(box("CELL_WinSky", (0.9, 0.02, 0.8), (-0.6, 1.95, 1.97), sky_mat("M_CellSky", (0.05, 0.10, 0.45), (0.01, 0.02, 0.15), 1.2), bevel=0))
for i in range(4):
    C(cyl("CELL_WinBar", 0.011, 0.47, (-0.79 + i * 0.125, 1.70, 1.975), iron))
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05, location=(-0.48, 1.88, 2.06), segments=24, ring_count=12)
MOON = bpy.context.active_object; MOON.name = "CELL_MoonDisc"; MOON.data.materials.append(mat("M_Moon", (1, 1, 0.9), emit=((1.0, 0.95, 0.80), 3.0)))
MOON.visible_shadow = False; C(MOON)
# iron door, hinged at (1.5, 1.1); the panel spans y 0.21..1.09 at rest; origin on the hinge axis
dparts = [box("DoorPanel", (0.06, 0.88, 2.02), (1.56, 0.65, 1.02), iron_red, bevel=0.008)]
for z in (0.35, 1.0, 1.7):
    dparts.append(box("DoorStrap", (0.075, 0.86, 0.07), (1.56, 0.65, z), iron, bevel=0.006))
for y in (0.28, 1.02):
    for z in [0.1 + k * 0.16 for k in range(12)]:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.011, location=(1.525, y, z), segments=12, ring_count=6); r_ = bpy.context.active_object
        r_.data.materials.append(iron); dparts.append(r_)
# lock box on the inner face near the free edge (y=0.21): keyhole axis = +X at (1.47, 0.34, 1.05)
dparts.append(box("LockBox", (0.05, 0.16, 0.22), (1.505, 0.34, 1.05), iron, bevel=0.01))
DOOR = join(dparts, "CellDoor"); set_origin(DOOR, (1.56, 1.09, 0.0)); C(DOOR)
KH = box("Keyhole", (0.004, 0.012, 0.026), (1.4795, 0.34, 1.045), mat("M_KeyholeDark", (0.0, 0.0, 0.0), rough=1.0), bevel=0)
bpy.ops.mesh.primitive_cylinder_add(radius=0.008, depth=0.004, location=(1.4795, 0.34, 1.058), rotation=(0, R_(90), 0))
k2 = bpy.context.active_object; k2.data.materials.append(KH.data.materials[0])
KH = join([KH, k2], "Keyhole"); KH.parent = DOOR; KH.matrix_parent_inverse = DOOR.matrix_world.inverted(); C(KH)
BOLT = box("DoorBolt", (0.03, 0.10, 0.03), (1.47, 0.20, 1.12), steel, bevel=0.004); BOLT.parent = DOOR; BOLT.matrix_parent_inverse = DOOR.matrix_world.inverted(); C(BOLT)
C(box("DoorFrameTop", (0.24, 1.04, 0.12), (1.6, 0.65, 2.11), stone_cell, bevel=0.01))
# table, stool, cot, shelf
tparts = [box("TableTop", (0.95, 0.62, 0.05), (-0.45, 0.30, 0.735), wood, bevel=0.008)]
for dx in (-0.4, 0.4):
    for dy in (-0.25, 0.25):
        tparts.append(box("TableLeg", (0.05, 0.05, 0.71), (-0.45 + dx, 0.30 + dy, 0.355), wood, bevel=0.005))
TABLE = C(join(tparts, "CellTable"))
sparts = [cyl("StoolTop", 0.17, 0.04, (-0.45, 0.88, 0.45), wood, bevel=0.006)]
for a in range(3):
    t = a * 2 * math.pi / 3
    sparts.append(cyl("StoolLeg", 0.018, 0.44, (-0.45 + 0.11 * math.cos(t), 0.88 + 0.11 * math.sin(t), 0.215), wood))
STOOL = C(join(sparts, "CellStool"))
cparts = [box("CotFrame", (0.75, 1.9, 0.06), (-1.08, -0.85, 0.40), iron, bevel=0.01)]
for dy in (-1.75, 0.05):
    for dx in (-0.35, 0.35):
        cparts.append(cyl("CotLeg", 0.02, 0.40, (-1.08 + dx, dy, 0.20), iron))
cparts.append(box("CotBlanket", (0.73, 1.86, 0.09), (-1.08, -0.85, 0.475), blanket, bevel=0.03))
cparts.append(box("CotPillow", (0.55, 0.32, 0.10), (-1.08, -1.6, 0.55), fabric("M_Pillow", (0.95, 0.88, 0.70), scale=300), bevel=0.04))
COT = C(join(cparts, "CellCot"))
SHELF = C(box("CellShelf", (0.30, 0.55, 0.04), (1.35, -0.32, 0.93), wood, bevel=0.006))
C(box("ShelfBracket", (0.03, 0.03, 0.20), (1.46, -0.52, 0.82), iron, bevel=0)); C(box("ShelfBracket", (0.03, 0.03, 0.20), (1.46, -0.12, 0.82), iron, bevel=0))
C(cyl("CellJug", 0.06, 0.18, (-1.25, 1.35, 0.09), mat("M_Jug", (0.10, 0.35, 0.65), rough=0.3, coat=0.4), bevel=0.01))

# ---------------------------------------------------------------- the candle (one burn-down via scale z; the flame rides a wick empty)
CANDLE_XY = (-0.12, 0.47)
holder = cyl("CandleHolder", 0.05, 0.012, (CANDLE_XY[0], CANDLE_XY[1], 0.766), brass, bevel=0.004)
cup = cyl("CandleCup", 0.022, 0.02, (CANDLE_XY[0], CANDLE_XY[1], 0.782), brass, bevel=0.003)
C(join([holder, cup], "CandleHolder"))
wax_m = mat("M_CandleWax", (0.95, 0.86, 0.62), rough=0.4, sss=0.3)
CAND = cyl("Candle", 0.018, 0.14, (CANDLE_XY[0], CANDLE_XY[1], 0.79 + 0.07), wax_m, verts=24)
set_origin(CAND, (CANDLE_XY[0], CANDLE_XY[1], 0.79)); C(CAND)
WICK = bpy.data.objects.new("CandleWick", None); sc.collection.objects.link(WICK); WICK.location = (CANDLE_XY[0], CANDLE_XY[1], 0.79 + 0.14)
fl_m = mat("M_Flame", (0.0, 0.0, 0.0), emit=((1.0, 0.16, 0.0), 3.0))
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.009, location=(0, 0, 0), segments=32, ring_count=16)
FLAME = bpy.context.active_object; FLAME.name = "CandleFlame"
for v in FLAME.data.vertices:
    z = v.co.z / 0.009; v.co.z = (z + 1) * 0.016; v.co.x *= (1.0 - 0.55 * max(0, z)); v.co.y *= (1.0 - 0.55 * max(0, z))
FLAME.data.materials.append(fl_m); bpy.ops.object.shade_smooth()
FLAME.parent = WICK; FLAME.location = (0, 0, 0.003); C(FLAME)
FLAME.visible_shadow = False
cl = bpy.data.lights.new("CandleLight", 'POINT'); cl.energy = 9.0; cl.color = (1.0, 0.62, 0.28); cl.shadow_soft_size = 0.02
CLO = bpy.data.objects.new("CandleLight", cl); sc.collection.objects.link(CLO); CLO.parent = WICK; CLO.location = (0, 0, 0.03)

# ================================================================== KEYS: local +X = shaft toward the bit, +Z = bow normal, bit teeth toward -Y. Origin = bow centre.
def make_key(name, material, ornate=True, L=0.072):
    parts = []
    bpy.ops.mesh.primitive_torus_add(major_radius=0.0135, minor_radius=0.0038, major_segments=32, minor_segments=10, location=(0, 0, 0))
    t = bpy.context.active_object; parts.append(t)
    if ornate:
        for a in (60, 180, 300):
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.004, location=(-0.0135 * math.cos(R_(a)) * 1.0, 0.0135 * math.sin(R_(a)), 0), segments=12, ring_count=6)
            parts.append(bpy.context.active_object)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.0055, depth=0.008, location=(0.0165, 0, 0), rotation=(0, R_(90), 0), vertices=16)
    parts.append(bpy.context.active_object)    # collar
    bpy.ops.mesh.primitive_cylinder_add(radius=0.0034, depth=L, location=(0.0135 + L / 2, 0, 0), rotation=(0, R_(90), 0), vertices=16)
    parts.append(bpy.context.active_object)    # shaft
    bx = 0.0135 + L - 0.017
    for (dx, w, h) in ((0.0, 0.016, 0.017),):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(bx + 0.008, -0.0034 - h / 2 + (0 if dx == 0 else 0), 0))
        c = bpy.context.active_object
        if dx == 0: c.scale = (w, h, 0.0042)
        else: c.location = (bx + dx + 0.002, -0.0034 - 0.017 - 0.0005 + h / 2 - 0.004, 0); c.scale = (w, h, 0.0046)
        bpy.ops.object.transform_apply(scale=True); parts.append(c)
    k = join(parts, name)
    # cut the ward notches out of the bit (teeth) with booleans applied
    for (nx, ny) in ((bx + 0.004, -0.0034 - 0.013), (bx + 0.011, -0.0034 - 0.009)):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(nx, ny, 0)); ct = bpy.context.active_object; ct.scale = (0.003, 0.008, 0.02)
        md = k.modifiers.new("cut", 'BOOLEAN'); md.object = ct; md.operation = 'DIFFERENCE'
        bpy.context.view_layer.objects.active = k; bpy.ops.object.modifier_apply(modifier=md.name)
        bpy.data.objects.remove(ct, do_unlink=True)
    k.location = (0, 0, 0)
    k.data.materials.clear(); k.data.materials.append(material)
    for p_ in k.data.polygons: p_.use_smooth = True
    try:
        bpy.context.view_layer.objects.active = k; bpy.ops.object.shade_auto_smooth(angle=R_(40))
    except Exception: pass
    return k
MKEY = make_key("MasterKey", brass, ornate=True)
copy_hot = mat("M_KeyCopy1", (0.78, 0.80, 0.84), rough=0.3, metal=1.0, emit=((1.0, 0.14, 0.0), 0.0))
KEY1 = make_key("KeyCopy1", copy_hot, ornate=False)
KEY2 = make_key("KeyCopy2", mat("M_KeyCopy2", (0.80, 0.82, 0.86), rough=0.25, metal=1.0), ornate=False)
print("KEY dims", tuple(round(d, 4) for d in MKEY.dimensions))

# ================================================================== the wax tin (imprint = one shape key, R5)
def make_tin(name, loc, imprint_key=None, rot_z=R_(18)):
    tin = cyl(name + "_Tin", 0.050, 0.020, (0, 0, 0.010), brass, bevel=0.003, verts=48)
    bm = bmesh.new(); bm.from_mesh(tin.data)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.z > 0.9], context='FACES_ONLY'); bm.to_mesh(tin.data); bm.free()
    so = tin.modifiers.new("solid", 'SOLIDIFY'); so.thickness = 0.0025; so.offset = -1
    # the wax: a fine grid disc, top at z=0.016
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=120, y_segments=120, size=0.048)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.xy.length > 0.0470], context='VERTS')
    for v in bm.verts: v.co.z = 0.016
    me = bpy.data.meshes.new(name + "_Wax"); bm.to_mesh(me); bm.free()
    wax = bpy.data.objects.new(name + "_Wax", me); sc.collection.objects.link(wax)
    wm = mat("M_Wax_" + name, (0.62, 0.015, 0.03), rough=0.3, sss=0.15, coat=0.4)
    me.materials.append(wm)
    for p_ in me.polygons: p_.use_smooth = True
    wax.parent = tin
    tin.location = loc; tin.rotation_euler = (0, 0, rot_z)
    if imprint_key is not None:
        # key lying flat, centred on the tin (key-local centre ~ x=0.045), sunk so its lower half presses 3.5 mm into the wax
        wax.shape_key_add(name="Basis")
        sk = wax.shape_key_add(name="imprint")
        kme = imprint_key.data
        verts = [Vector(v.co) for v in kme.vertices]
        Mk = Matrix.Translation((-0.045, 0.0, 0.016 + 0.0042 - 0.0035))
        bvh = BVHTree.FromPolygons([Mk @ v for v in verts], [p_.vertices[:] for p_ in kme.polygons])
        n = 0
        for i, v in enumerate(me.vertices):
            hit = bvh.ray_cast(Vector((v.co.x, v.co.y, -0.05)), Vector((0, 0, 1)), 0.1)
            if hit[0] is not None and hit[0].z < 0.016:
                sk.data[i].co.z = hit[0].z - 0.0003; n += 1
        # a soft raised rim around the impression
        print("IMPRINT verts", name, n)
        sk.value = 0.0
    return tin, wax
TIN1, WAX1 = make_tin("Mold1", (-0.50, 0.42, 0.76), imprint_key=MKEY, rot_z=R_(-45))
TIN2, WAX2 = make_tin("Mold2", (-0.50, 0.42, 0.76), imprint_key=MKEY, rot_z=R_(-45))
C(TIN2)

# ================================================================== cakes + baskets
def make_cake(name, loc, cut=False, hollow=None):
    sponge = mat("M_Sponge", (0.80, 0.45, 0.13), rough=0.8)
    nt = sponge.node_tree; p = nt.nodes["Principled BSDF"]
    if not any(n.type == 'TEX_VORONOI' for n in nt.nodes):
        vo = nt.nodes.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 90
        cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].position = 0.04; cr.color_ramp.elements[0].color = (0.30, 0.04, 0.02, 1)
        cr.color_ramp.elements[1].position = 0.08; cr.color_ramp.elements[1].color = (0.80, 0.45, 0.13, 1)
        nt.links.new(vo.outputs["Distance"], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], p.inputs["Base Color"])
    icing = mat("M_Icing", (0.97, 0.93, 0.85), rough=0.3, sss=0.1, coat=0.3)
    cherry = mat("M_Cherry", (0.75, 0.0, 0.02), rough=0.15, coat=0.6)
    body = cyl(name, 0.11, 0.075, (0, 0, 0.0375), sponge, verts=64, bevel=0.004)
    top = cyl(name + "_Icing", 0.113, 0.016, (0, 0, 0.078), icing, verts=64, bevel=0.007)
    parts = [body, top]
    for i in range(8):
        a = i * math.pi / 4
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.011, location=(0.075 * math.cos(a), 0.075 * math.sin(a), 0.092), segments=24, ring_count=12)
        c = bpy.context.active_object; c.data.materials.append(cherry); parts.append(c)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.013, location=(0, 0, 0.093), segments=16, ring_count=8)
    c = bpy.context.active_object; c.data.materials.append(cherry); parts.append(c)
    if cut:
        def in_wedge(p):   # wedge facing local -X, apex at x=+0.012, half-angle ~37 deg
            return p.x < 0.012 and abs(p.y) < (0.012 - p.x) * 0.76
        parts = [p for p in parts if p in (body, top) or not in_wedge(p.location)]
        for p in [p for p in bpy.data.objects if p.name.startswith(name) and p not in parts and p.type == 'MESH' and p.name != name and not p.name.startswith(name + "_Icing")]:
            pass
    cake = join(parts, name) if not cut else None
    if cut:
        for part in (body, top):
            bm = bmesh.new()
            pts = [Vector((0.012, 0, -0.01)), Vector((-0.20, 0.16, -0.01)), Vector((-0.20, -0.16, -0.01))]
            v_ = [bm.verts.new(q) for q in pts] + [bm.verts.new(q + Vector((0, 0, 0.14))) for q in pts]
            bm.faces.new((v_[0], v_[1], v_[2])); bm.faces.new((v_[3], v_[5], v_[4]))
            for a_, b_ in ((0, 1), (1, 2), (2, 0)): bm.faces.new((v_[a_], v_[b_], v_[b_ + 3], v_[a_ + 3]))
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            wm_ = bpy.data.meshes.new("wedge"); bm.to_mesh(wm_); bm.free(); wo = bpy.data.objects.new("wedge", wm_); sc.collection.objects.link(wo)
            for md_ in list(part.modifiers):
                bpy.context.view_layer.objects.active = part; bpy.ops.object.modifier_apply(modifier=md_.name)
            md = part.modifiers.new("cut", 'BOOLEAN'); md.object = wo; md.operation = 'DIFFERENCE'; md.solver = 'EXACT'
            bpy.context.view_layer.objects.active = part; bpy.ops.object.modifier_apply(modifier="cut")
            bpy.data.objects.remove(wo, do_unlink=True)
            print("CAKECUT", part.name, len(part.data.polygons))
        if hollow is not None:   # the key-shaped hollow left in the sponge where the key was pulled out
            kobj, Mloc = hollow
            bpy.ops.mesh.primitive_cube_add(size=1); dup = bpy.context.active_object       # a slot where the key lay (shaft + bow)
            dup.matrix_world = Mloc @ Matrix.Translation((0.034, -0.004, 0)); dup.scale = (0.106, 0.036, 0.012)
            md = body.modifiers.new("hollow", 'BOOLEAN'); md.object = dup; md.operation = 'DIFFERENCE'; md.solver = 'EXACT'
            bpy.context.view_layer.objects.active = body; bpy.ops.object.modifier_apply(modifier="hollow")
            bpy.data.objects.remove(dup, do_unlink=True); print("HOLLOW", len(body.data.polygons))
        for p in parts:
            for p_ in p.data.polygons: p_.use_smooth = True
        cake = join(parts, name)
    if False:   # a wedge removed facing local -Y (the side the camera sees in the cell after the turn)
        bm = bmesh.new()
        pts = [Vector((0.012, 0, -0.01)), Vector((-0.20, 0.16, -0.01)), Vector((-0.20, -0.16, -0.01))]
        v_ = [bm.verts.new(q) for q in pts] + [bm.verts.new(q + Vector((0, 0, 0.14))) for q in pts]
        bm.faces.new((v_[0], v_[1], v_[2])); bm.faces.new((v_[3], v_[5], v_[4]))
        for a_, b_ in ((0, 1), (1, 2), (2, 0)): bm.faces.new((v_[a_], v_[b_], v_[b_ + 3], v_[a_ + 3]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        wm_ = bpy.data.meshes.new("wedge"); bm.to_mesh(wm_); bm.free(); wo = bpy.data.objects.new("wedge", wm_); sc.collection.objects.link(wo)
        md = cake.modifiers.new("cut", 'BOOLEAN'); md.object = wo; md.operation = 'DIFFERENCE'; md.solver = 'EXACT'
        bpy.context.view_layer.objects.active = cake; bpy.ops.object.modifier_apply(modifier="cut")
        bpy.data.objects.remove(wo, do_unlink=True)
        for p_ in cake.data.polygons:
            if p_.material_index == 0 and abs(p_.normal.z) < 0.5: pass
    cake.location = loc
    return cake

def make_basket(name, loc, rot_z=0.0):
    wick_m = mat("M_Wicker", (0.62, 0.32, 0.08), rough=0.7)
    nt = wick_m.node_tree; p = nt.nodes["Principled BSDF"]
    if not any(n.type == 'TEX_WAVE' for n in nt.nodes):
        tc = nt.nodes.new("ShaderNodeTexCoord"); wv = nt.nodes.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = 60; wv.bands_direction = 'Z'
        bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.5
        nt.links.new(tc.outputs["Object"], wv.inputs["Vector"]); nt.links.new(wv.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], p.inputs["Normal"])
    b = cyl(name, 0.16, 0.10, (0, 0, 0.05), wick_m, verts=48)
    bm = bmesh.new(); bm.from_mesh(b.data)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.z > 0.9], context='FACES_ONLY'); bm.to_mesh(b.data); bm.free()
    so = b.modifiers.new("solid", 'SOLIDIFY'); so.thickness = 0.008; so.offset = -1
    bpy.ops.mesh.primitive_torus_add(major_radius=0.15, minor_radius=0.008, location=(0, 0, 0.10), rotation=(R_(90), 0, 0), major_segments=48, minor_segments=8)
    h = bpy.context.active_object; h.data.materials.append(wick_m)
    bm = bmesh.new(); bm.from_mesh(h.data); bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.y < -0.002], context='VERTS'); bm.to_mesh(h.data); bm.free()
    cloth = cyl(name + "_Cloth", 0.145, 0.006, (0, 0, 0.012), stripes("M_Cloth", (0.85, 0.05, 0.05), (0.96, 0.94, 0.88), scale=25), verts=48)
    bk = join([b, h, cloth], name)
    bk.location = loc; bk.rotation_euler = (0, 0, rot_z)
    return bk

# ================================================================== CORRIDOR (x 1.5..9.3)
COR = []
def K(o):
    for x in (o if isinstance(o, list) else [o]): COR.append(x)
    return o
K(box("COR_Floor", (3.6, 1.8, 0.1), (3.25, 0.7, -0.05), flag_m, bevel=0))
K(wall("COR_WallS", 1.7, 5.0, -0.3, -0.1, 0, 3.2, stone_cor))
K(wall("COR_WallN", 1.7, 5.0, 1.5, 1.7, 0, 3.2, stone_cor))
K(box("COR_Ceiling", (3.6, 2.0, 0.12), (3.3, 0.7, 3.16), stone_cor, bevel=0))
def gate(name, x):
    parts = []
    for k in range(9):
        y = -0.06 + k * 0.19
        parts.append(cyl(name + "Bar", 0.014, 2.16, (x, y, 1.1), iron))
    for z in (0.12, 1.1, 2.12):
        parts.append(box(name + "Rail", (0.04, 1.58, 0.05), (x, 0.70, z), iron, bevel=0.005))
    parts.append(box(name + "Lock", (0.07, 0.12, 0.16), (x - 0.03, 0.02, 1.05), brass, bevel=0.01))
    g = join(parts, name); set_origin(g, (x, 1.48, 0.0)); return g
GATE1 = K(gate("Gate1", 2.6))
lant_m = mat("M_LanternGlow", (1.0, 0.7, 0.3), emit=((1.0, 0.55, 0.15), 18.0))
def lantern(name, loc, energy=30.0, bucket=None):
    parts = [box(name + "Cage", (0.12, 0.12, 0.18), loc, iron, bevel=0.01)]
    g_ = box(name + "Glow", (0.09, 0.09, 0.14), loc, lant_m, bevel=0.01); g_.visible_shadow = False
    L = bpy.data.lights.new(name, 'POINT'); L.energy = energy; L.color = (1.0, 0.62, 0.30); L.shadow_soft_size = 0.05
    lo = bpy.data.objects.new(name + "Light", L); sc.collection.objects.link(lo); lo.location = Vector(loc) + Vector((0, 0, -0.12))
    if bucket is not None: bucket += [parts[0], g_]
    return lo
for x_ in (2.0, 4.0):
    lantern("CorLantern", (x_, -0.03, 2.25), 25.0, COR)

# ================================================================== GATEHOUSE + LANE (x 9.3..13.5)
EXT = []
def E(o):
    for x in (o if isinstance(o, list) else [o]): EXT.append(x)
    return o
E(wall("GATE_Wall", 9.3, 9.8, -6.0, 6.0, 0, 5.2, stone_out, holes=[(-0.25, 1.85, 0.0, 3.2)]))
E(box("GATE_Arch", (0.6, 2.2, 0.35), (9.55, 0.80, 3.3), stone_out, bevel=0.02))
# the big gate (two leaves, closed) with a wicket door in the left leaf; the wicket swings to +X about its hinge at y=1.1
gl = [box("GateLeaf", (0.12, 2.06, 3.18), (9.62, 0.80, 1.59), wood_dark, bevel=0.01)]
for z in (0.4, 1.6, 2.8): gl.append(box("GateStrap", (0.14, 2.0, 0.08), (9.62, 0.80, z), iron, bevel=0.006))
GLEAF = join(gl, "GateLeaves")
md = GLEAF.modifiers.new("wicket", 'BOOLEAN'); ct = box("cutter", (0.6, 0.80, 1.86), (9.62, 0.70, 0.93), iron, bevel=0)
md.object = ct; md.operation = 'DIFFERENCE'; bpy.context.view_layer.objects.active = GLEAF; bpy.ops.object.modifier_apply(modifier="wicket")
bpy.data.objects.remove(ct, do_unlink=True); E(GLEAF)
wk = [box("WicketPanel", (0.10, 0.78, 1.84), (9.62, 0.70, 0.93), wood_dark, bevel=0.01), box("WicketStrap", (0.12, 0.74, 0.06), (9.62, 0.70, 0.5), iron, bevel=0.004),
      box("WicketStrap", (0.12, 0.74, 0.06), (9.62, 0.70, 1.4), iron, bevel=0.004)]
for y_ in (0.40, 0.70, 1.00):
    for z_ in (0.25, 0.75, 1.15, 1.65):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.016, location=(9.565, y_, z_), segments=12, ring_count=6); st_ = bpy.context.active_object
        st_.data.materials.append(iron); wk.append(st_)
WICKET = join(wk, "Wicket"); set_origin(WICKET, (9.62, 1.09, 0.0)); E(WICKET)
E(box("LANE_Ground", (5.0, 14.0, 0.1), (11.6, 0.8, -0.05), cobble, bevel=0))
E(box("LANE_Ground2", (6.0, 14.0, 0.1), (15.8, 0.8, -0.06), cobble, bevel=0))
def torch(name, loc, energy=60.0):
    st = cyl(name + "Bracket", 0.02, 0.35, Vector(loc) + Vector((0.12, 0, -0.18)), iron, rot=(0, R_(35), 0))
    bowl = cyl(name + "Bowl", 0.06, 0.07, Vector(loc) + Vector((0.22, 0, 0.0)), iron, bevel=0.005)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05, location=Vector(loc) + Vector((0.22, 0, 0.08)), segments=16, ring_count=8)
    f_ = bpy.context.active_object; f_.name = name + "Fire"; f_.scale = (1, 1, 1.8); f_.data.materials.append(fl_m); f_.visible_shadow = False
    L = bpy.data.lights.new(name, 'POINT'); L.energy = energy; L.color = (1.0, 0.55, 0.22); L.shadow_soft_size = 0.08
    lo = bpy.data.objects.new(name + "Light", L); sc.collection.objects.link(lo); lo.location = Vector(loc) + Vector((0.28, 0, 0.10))
    return [st, bowl, f_], lo
TORCH_A, TLA = torch("TorchA", (9.8, -0.75, 2.4)); TORCH_B, TLB = torch("TorchB", (9.8, 2.35, 2.4)); E(TORCH_A); E(TORCH_B)
house_cols = [(0.55, 0.12, 0.10), (0.10, 0.32, 0.45), (0.60, 0.42, 0.10), (0.25, 0.12, 0.40)]
for i, x0 in enumerate((9.9, 10.9, 11.9, 12.9)):
    hc = mat("M_House%d" % i, house_cols[i], rough=0.7)
    E(box("LANE_House", (0.98, 1.2, 4.2 + 0.3 * (i % 2)), (x0 + 0.5, 5.2, 2.1 + 0.15 * (i % 2)), hc, bevel=0.01))
    E(box("LANE_Roof", (1.04, 1.3, 0.25), (x0 + 0.5, 5.2, 4.3 + 0.3 * (i % 2)), mat("M_Roof", (0.25, 0.08, 0.05), rough=0.6), bevel=0.01))
    for z in (1.4, 2.9):
        E(box("LANE_HouseWin", (0.40, 0.06, 0.6), (x0 + 0.5, 4.58, z), mat("M_HouseWin", (1.0, 0.70, 0.30), emit=((1.0, 0.6, 0.25), 1.2)), bevel=0.01))
    E(box("LANE_HouseDoor", (0.36, 0.06, 1.0), (x0 + 0.2, 4.58, 0.5), wood_dark, bevel=0.01))
# ================================================================== WORKSHOP (x 13.5..18)
E(wall("WS_WallW", 13.5, 13.7, -2.0, 3.5, 0, 3.4, plaster, holes=[(-2.0, 1.45, 0.0, 2.55)]))
E(box("WS_Beam", (0.30, 3.3, 0.18), (13.6, -0.10, 2.64), wood_dark, bevel=0.01))

E(wall("WS_WallE", 17.9, 18.1, -2.0, 3.5, 0, 3.4, redbrick))
E(wall("WS_WallN", 13.5, 18.1, 3.5, 3.7, 0, 3.4, redbrick))
E(wall("WS_WallS", 13.5, 18.1, -2.2, -2.0, 0, 3.4, redbrick))
E(box("WS_Floor", (4.4, 5.6, 0.1), (15.8, 0.75, -0.04), woodmat("M_WSFloor", (0.30, 0.14, 0.05), (0.22, 0.10, 0.04)), bevel=0))
E(box("WS_Roof", (4.8, 6.0, 0.15), (15.8, 0.75, 3.45), wood_dark, bevel=0))
E(box("WS_Facade", (0.05, 5.5, 1.2), (13.48, 0.75, 3.0), mat("M_Facade", (0.05, 0.30, 0.28), rough=0.6), bevel=0))
# blade sign over the lane (logo both faces) and the logo board inside above the bench
def logo_plane(name, w, loc, rot, logo=LOGO_DARK, bg=(0.97, 0.88, 0.62)):
    m = bpy.data.materials.new("M_" + name); m.use_nodes = True; nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    p.inputs["Roughness"].default_value = 0.5
    tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = bpy.data.images.load(logo); tx.extension = 'CLIP'
    mp = nt.nodes.new("ShaderNodeMapping"); tc = nt.nodes.new("ShaderNodeTexCoord")
    mp.inputs["Scale"].default_value = (1.12, 1.12 * (w / (w * 414 / 967)) * (414 / 967) / 0.62 if False else 1.12, 1); mp.inputs["Location"].default_value = (-0.06, -0.06, 0)
    nt.links.new(tc.outputs["UV"], mp.inputs["Vector"]); nt.links.new(mp.outputs["Vector"], tx.inputs["Vector"])
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.inputs['A'].default_value = (*bg, 1)
    nt.links.new(tx.outputs["Alpha"], mx.inputs['Factor']); nt.links.new(tx.outputs["Color"], mx.inputs['B'])
    nt.links.new(mx.outputs['Result'], p.inputs["Base Color"])
    h = w * 414 / 967 * 1.12 / 1.12
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name; o.scale = (w, h, 1); bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(m)
    return o
E(box("SignBracket", (1.0, 0.03, 0.03), (13.0, 1.75, 2.80), iron, bevel=0))
E(box("SignBoard", (0.98, 0.05, 0.50), (12.95, 1.75, 2.50), wood_dark, bevel=0.01))
E(logo_plane("LogoSignA", 0.90, (12.95, 1.722, 2.50), (R_(90), 0, R_(0))))
E(logo_plane("LogoSignB", 0.90, (12.95, 1.778, 2.50), (R_(90), 0, R_(180))))
E(box("WS_LogoBoard", (0.04, 0.95, 0.47), (13.73, 2.30, 1.80), wood_dark, bevel=0.012))
E(logo_plane("LogoBoard", 0.86, (13.755, 2.30, 1.80), (R_(90), 0, R_(90))))
# bench along y at x 15.3..16.2
bparts = [box("BenchTop", (0.90, 1.6, 0.06), (15.75, 0.15, 0.88), wood, bevel=0.01)]
for dx in (-0.38, 0.38):
    for dy in (-0.72, 0.72): bparts.append(box("BenchLeg", (0.07, 0.07, 0.85), (15.75 + dx, 0.15 + dy, 0.425), wood, bevel=0.006))
bparts.append(box("BenchShelf", (0.85, 1.5, 0.03), (15.75, 0.15, 0.25), wood, bevel=0.004))
BENCH = E(join(bparts, "Bench"))
# sand mould (two-part flask) on the bench with the key cavity (KeyCopy1 cools in it)
MOULD = box("SandMould", (0.18, 0.24, 0.07), (15.70, 0.05, 0.945), sand_m, bevel=0.004)
fl_ = box("MouldFlask", (0.20, 0.26, 0.07), (15.70, 0.05, 0.945), wood_dark, bevel=0.004)
bm = bmesh.new(); bm.from_mesh(fl_.data); bmesh.ops.delete(bm, geom=[f for f in bm.faces if abs(f.normal.z) > 0.9], context='FACES_ONLY'); bm.to_mesh(fl_.data); bm.free()
so = fl_.modifiers.new("s", 'SOLIDIFY'); so.thickness = 0.012; so.offset = 1
KEY1_MOULD = Matrix.Translation((15.70, 0.05 - 0.035, 0.98 - 0.0042 + 0.001)) @ Matrix.Rotation(R_(90), 4, 'Z')
KEY1.matrix_world = KEY1_MOULD
md = MOULD.modifiers.new("cav", 'BOOLEAN'); md.object = KEY1; md.operation = 'DIFFERENCE'; md.solver = 'EXACT'
bpy.context.view_layer.objects.active = MOULD; bpy.ops.object.modifier_apply(modifier="cav")
E(MOULD); E(fl_)
# forge with glowing coals, chimney hood
fparts = [box("ForgeBase", (1.0, 0.8, 0.85), (17.3, 2.9, 0.425), redbrick, bevel=0.01)]
coal_m = mat("M_Coals", (0.2, 0.05, 0.02), rough=0.8, emit=((1.0, 0.28, 0.02), 6.0))
nt = coal_m.node_tree; p = nt.nodes["Principled BSDF"]; vo = nt.nodes.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 25
cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (1.0, 0.45, 0.05, 1); cr.color_ramp.elements[1].color = (0.25, 0.02, 0.0, 1)
nt.links.new(vo.outputs["Distance"], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], p.inputs["Emission Color"])
coals = box("ForgeCoals", (0.8, 0.6, 0.05), (17.3, 2.9, 0.86), coal_m, bevel=0.01); coals.modifiers.clear()
FORGE = E(join(fparts, "Forge")); E(coals)
E(box("ForgeHood", (1.1, 0.9, 0.5), (17.3, 2.9, 2.3), redbrick, bevel=0.02))
E(box("ForgeChimney", (0.4, 0.4, 1.2), (17.3, 3.1, 2.9), redbrick, bevel=0.01))
FL = bpy.data.lights.new("ForgeGlow", 'AREA'); FL.energy = 260; FL.size = 0.8; FL.color = (1.0, 0.42, 0.12)
FLO = bpy.data.objects.new("ForgeGlow", FL); sc.collection.objects.link(FLO); FLO.location = (17.3, 2.9, 1.05); FLO.rotation_euler = (0, 0, 0)
FLO.rotation_euler = (R_(180), 0, 0)
FL2 = bpy.data.lights.new("ForgeGlowUp", 'POINT'); FL2.energy = 120; FL2.color = (1.0, 0.45, 0.12)
FL2O = bpy.data.objects.new("ForgeGlowUp", FL2); sc.collection.objects.link(FL2O); FL2O.location = (17.1, 2.55, 1.15)
# tilting crucible on a bench stand: pivot axis Y at (15.85, 0.05, 1.22); the lip on the -X side over the mould; lever to -X.
crm = mat("M_Crucible", (0.08, 0.06, 0.06), rough=0.6)
melt = mat("M_Melt", (0.0, 0.0, 0.0), emit=((1.0, 0.14, 0.0), 3.0))
PIV = Vector((15.85, 0.05, 1.22))
pot = cyl("CruciblePot", 0.075, 0.16, (PIV.x, PIV.y, PIV.z - 0.10), crm, bevel=0.01)
bm = bmesh.new(); bm.from_mesh(pot.data); bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.z > 0.9], context='FACES_ONLY'); bm.to_mesh(pot.data); bm.free()
so = pot.modifiers.new("s", 'SOLIDIFY'); so.thickness = 0.012; so.offset = -1
mlt = cyl("CrucibleMelt", 0.064, 0.01, (PIV.x, PIV.y, PIV.z - 0.04), melt)
lip = box("CrucibleLip", (0.04, 0.03, 0.012), (PIV.x - 0.085, PIV.y, PIV.z - 0.025), crm, bevel=0.004)
yoke = box("CrucibleYoke", (0.025, 0.22, 0.025), (PIV.x, PIV.y, PIV.z), iron, bevel=0.003)
lever = cyl("CrucibleLever", 0.012, 0.40, (PIV.x - 0.20, PIV.y + 0.12, PIV.z), iron, rot=(0, R_(90), 0))
arm_ = box("CrucibleArm", (0.02, 0.02, 0.02), (PIV.x, PIV.y + 0.12, PIV.z), iron, bevel=0)
grip = cyl("CrucibleGrip", 0.018, 0.12, (PIV.x - 0.40 + 0.04, PIV.y + 0.12, PIV.z), wood_dark, rot=(0, R_(90), 0))
CRUC = join([pot, mlt, lip, yoke, lever, arm_, grip], "Crucible"); set_origin(CRUC, PIV); E(CRUC)
CRUC.rotation_mode = 'XYZ'
stand = [box("StandPost", (0.03, 0.03, PIV.z - 0.91), (PIV.x, PIV.y + 0.13, (PIV.z + 0.91) / 2), iron, bevel=0),
         box("StandPost", (0.03, 0.03, PIV.z - 0.91), (PIV.x, PIV.y - 0.13, (PIV.z + 0.91) / 2), iron, bevel=0),
         box("StandFoot", (0.10, 0.32, 0.02), (PIV.x, PIV.y, 0.92), iron, bevel=0)]
E(join(stand, "CrucibleStand"))
# the pour stream: a thin tube keyed per frame in stage B from the lip to the mould sprue
bpy.ops.mesh.primitive_cylinder_add(radius=0.005, depth=1.0, location=(0, 0, 0), vertices=12)
STREAM = bpy.context.active_object; STREAM.name = "PourStream"; STREAM.data.transform(Matrix.Translation((0, 0, -0.5)))
STREAM.data.materials.append(melt); STREAM.visible_shadow = False; E(STREAM)
# tools on the wall, anvil
E(box("WS_ToolRack", (0.04, 1.2, 0.06), (17.86, 1.6, 1.6), wood_dark, bevel=0.005))
for i in range(5):
    E(cyl("WS_Tool", 0.008, 0.40, (17.82, 1.15 + i * 0.22, 1.40), iron))
anv = [box("AnvilTop", (0.42, 0.14, 0.10), (14.6, 2.6, 0.82), iron, bevel=0.01), box("AnvilWaist", (0.16, 0.10, 0.25), (14.6, 2.6, 0.64), iron, bevel=0.01),
       cyl("AnvilStump", 0.20, 0.52, (14.6, 2.6, 0.26), wood, bevel=0.01)]
E(join(anv, "Anvil"))
E(box("WS_Window", (0.04, 1.0, 0.8), (17.88, -1.2, 1.8), sky_mat("M_WSWinSky", (0.95, 0.55, 0.25), (0.40, 0.20, 0.55), 2.0), bevel=0))

# cake + basket (workshop: on the bench, whole), the cell copy (cut) and the second cake (cut, a key-shaped hollow)
plate_m = mat("M_Plate", (0.95, 0.95, 0.97), rough=0.2, coat=0.5); rim_m = mat("M_PlateRim", (0.02, 0.18, 0.75), rough=0.25, coat=0.5)
def make_plate(name, loc):
    a = cyl(name, 0.15, 0.012, (0, 0, 0.006), plate_m, verts=64, bevel=0.004)
    b = cyl(name + "Rim", 0.152, 0.004, (0, 0, 0.011), rim_m, verts=64)
    bm = bmesh.new(); bm.from_mesh(b.data); bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.xy.length < 0.13], context='VERTS'); bm.to_mesh(b.data); bm.free()
    p_ = join([a, b], name); p_.location = loc; return p_
BASKET_WS = make_basket("Basket", (0, 0, 0)); BASKET_WS["island"] = "PROP"
BENCH_TOP = 0.91
PLATE_WS = make_plate("PlateWS", (15.55, 0.62, BENCH_TOP)); E(PLATE_WS)
CAKE_WS = make_cake("CakeWS", (15.55, 0.62, BENCH_TOP + 0.012)); E(CAKE_WS)
SHELF_TOP = 0.95
PLATE_C = make_plate("PlateCell", (1.33, -0.32, SHELF_TOP)); C(PLATE_C)
CAKE_C = make_cake("CakeCell", (1.33, -0.32, SHELF_TOP + 0.012), cut=True); C(CAKE_C)
# the key inside a cake (cake-local): shaft along +X from the -X side, bow normal +Y, centred at cake mid-height, bow just inside the cut face
KEY_IN_CAKE = Matrix.Translation((-0.085, -0.055, 0.040)) @ Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, -1, 0, 0), (0, 0, 0, 1)))
CAKE_C2 = make_cake("CakeCell2", (1.33, -0.32, SHELF_TOP + 0.012), cut=True, hollow=(KEY2, KEY_IN_CAKE)); C(CAKE_C2)
sc["KEY_IN_CAKE"] = [list(r) for r in KEY_IN_CAKE]

# ================================================================== STEPS island (x = 40): years later
STEPS = []
def T(o):
    for x in (o if isinstance(o, list) else [o]): STEPS.append(x)
    return o
SX = 40.0
sand2 = brickmat("M_Sandstone", (0.82, 0.55, 0.30), (0.76, 0.50, 0.26), (0.55, 0.36, 0.20), scale=1.0, bw=0.8, rh=0.4, msize=0.006, rough=0.6, bump=0.1)
T(box("ST_Ground", (24, 20, 0.1), (SX, -4.0, -0.05), cobble, bevel=0))
for i in range(5):
    T(box("ST_Step", (6.0, 3.0 - i * 0.45, 0.17), (SX, 0.0 + i * 0.45 + (3.0 - i * 0.45) / 2 - 0.0, 0.085 + i * 0.17), sand2, bevel=0.01))
T(box("ST_Platform", (6.0, 2.2, 0.85), (SX, 3.0 + 1.1 - 0.75, 0.425), sand2, bevel=0.01))
T(box("ST_Facade", (12.0, 0.6, 7.0), (SX, 4.3, 3.5), sand2, bevel=0))
for dx in (-2.2, -0.9, 0.9, 2.2):
    T(cyl("ST_Column", 0.22, 4.6, (SX + dx, 3.55, 0.85 + 2.3), mat("M_Column", (0.93, 0.86, 0.72), rough=0.4), verts=32, bevel=0.01))
T(box("ST_Pediment", (6.4, 0.9, 0.5), (SX, 3.6, 5.7), mat("M_Column", (0.93, 0.86, 0.72)), bevel=0.02))
T(box("ST_Door", (1.6, 0.1, 2.8), (SX, 3.98, 0.85 + 1.4), woodmat("M_GovDoor", (0.30, 0.09, 0.03), (0.20, 0.05, 0.02)), bevel=0.02))
T(box("ST_DoorFrame", (1.9, 0.12, 0.18), (SX, 3.95, 0.85 + 2.85), mat("M_Column", (0.93, 0.86, 0.72)), bevel=0.02))
for dx in (-0.4, 0.4):
    T(box("ST_DoorPanel", (0.55, 0.04, 1.0), (SX + dx, 3.92, 0.85 + 1.9), woodmat("M_GovDoorP", (0.22, 0.06, 0.02), (0.14, 0.04, 0.01)), bevel=0.01))
    T(box("ST_DoorPanel", (0.55, 0.04, 0.9), (SX + dx, 3.92, 0.85 + 0.65), woodmat("M_GovDoorP", (0.22, 0.06, 0.02), (0.14, 0.04, 0.01)), bevel=0.01))
glass = mat("M_GovGlass", (0.05, 0.25, 0.55), rough=0.1, coat=0.6)
for dx in (-4.3, -3.0, 3.0, 4.3):
    for z in (1.6, 4.2):
        T(box("ST_Window", (0.8, 0.08, 1.4), (SX + dx, 3.98, z), glass, bevel=0.01))
        T(box("ST_WinFrame", (0.95, 0.10, 0.10), (SX + dx, 3.97, z - 0.75), mat("M_Column", (0.93, 0.86, 0.72)), bevel=0.01))
tri = bpy.data.materials.new("M_Tricolour"); tri.use_nodes = True; nt = tri.node_tree; p = nt.nodes["Principled BSDF"]
tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); cr = nt.nodes.new("ShaderNodeValToRGB")
cr.color_ramp.interpolation = 'CONSTANT'
cr.color_ramp.elements[0].position = 0.0; cr.color_ramp.elements[0].color = (0.0, 0.42, 0.14, 1)
cr.color_ramp.elements[1].position = 0.3333; cr.color_ramp.elements[1].color = (0.95, 0.95, 0.93, 1)
e3 = cr.color_ramp.elements.new(0.6667); e3.color = (1.0, 0.36, 0.02, 1)
nt.links.new(tc.outputs["UV"], sep.inputs[0]); nt.links.new(sep.outputs["X"], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], p.inputs["Base Color"])
p.inputs["Roughness"].default_value = 0.6; p.inputs["Sheen Weight"].default_value = 0.3
FLAGS = []
for i, dx in enumerate((-1.45, 1.45)):
    T(cyl("ST_FlagPole", 0.035, 4.6, (SX + dx, 2.7, 0.85 + 2.3), mat("M_Pole", (0.85, 0.70, 0.25), rough=0.2, metal=1.0)))
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=30, y_subdivisions=18, size=1, location=(0, 0, 0))
    fg = bpy.context.active_object; fg.name = "ST_Flag%d" % i
    for v in fg.data.vertices: v.co = Vector(((v.co.x + 0.5) * 1.5, 0.0, (v.co.y + 0.5) * 0.9))
    fg.data.uv_layers.active.data.foreach_set("uv", [c for l in fg.data.loops for c in (fg.data.vertices[l.vertex_index].co.x / 1.5, fg.data.vertices[l.vertex_index].co.z / 0.9)])
    fg.location = (SX + dx + (0.04 if dx > 0 else -0.04), 2.7, 3.3); fg.rotation_euler = (0, 0, 0 if dx > 0 else R_(180))
    wv = fg.modifiers.new("wave", 'WAVE'); wv.use_x = True; wv.use_y = False; wv.height = 0.07; wv.width = 0.45; wv.speed = 0.012
    wv.start_position_x = 0.0; wv.falloff_radius = 0.0; wv.use_normal = False
    vg = fg.vertex_groups.new(name="free"); vg.add([v.index for v in fg.data.vertices], 1.0, 'REPLACE')
    for v in fg.data.vertices: vg.add([v.index], min(1.0, v.co.x / 0.5), 'REPLACE')
    wv.vertex_group = "free"; wv.use_normal = True
    so = fg.modifiers.new("s", 'SOLIDIFY'); so.thickness = 0.004
    fg.data.materials.append(tri); bpy.ops.object.shade_smooth(); FLAGS.append(fg); T(fg)
# bunting / planters for colour
for dx in (-2.6, 2.6):
    T(cyl("ST_Planter", 0.30, 0.45, (SX + dx, -0.6, 0.225), mat("M_Planter", (0.70, 0.30, 0.08), rough=0.5), bevel=0.02))
    for k in range(6):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.16, location=(SX + dx + random.uniform(-0.15, 0.15), -0.6 + random.uniform(-0.15, 0.15), 0.55 + random.uniform(0, 0.2)))
        o_ = bpy.context.active_object; o_.data.materials.append(mat("M_Shrub", (0.05, 0.42, 0.10), rough=0.6)); bpy.ops.object.shade_smooth(); T(o_)

# ================================================================== look: AgX Punchy, deep saturated, fast-render settings
sc.view_settings.view_transform = 'Filmic'      # as the approved LegoInNose v013: keeps the molten metal and flame a true orange
try: sc.view_settings.look = 'High Contrast'
except Exception: pass
sc.view_settings.exposure = 0.0
import colorsys
for m_ in bpy.data.materials:
    if not m_.use_nodes or not m_.name.startswith("M_") or m_.name.startswith(("M_Icing", "M_Steel", "M_KeyCopy", "M_KeyholeDark", "M_Column")): continue
    for n_ in m_.node_tree.nodes:
        if n_.type == 'BSDF_PRINCIPLED' and not n_.inputs["Base Color"].is_linked:
            r_, g_, b_, a_ = n_.inputs["Base Color"].default_value
            h_, l_, s_ = colorsys.rgb_to_hls(r_, g_, b_)
            if s_ > 0.05: n_.inputs["Base Color"].default_value = (*colorsys.hls_to_rgb(h_, l_, min(1.0, s_ * 1.2)), a_)
sc.render.engine = 'CYCLES'
sc.cycles.samples = 64; sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.04; sc.cycles.use_denoising = True
try: sc.cycles.denoiser = 'OPENIMAGEDENOISE'
except Exception: pass
sc.cycles.max_bounces = 6; sc.cycles.diffuse_bounces = 3; sc.cycles.glossy_bounces = 3; sc.cycles.transmission_bounces = 6
sc.cycles.transparent_max_bounces = 16; sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
sc.render.use_persistent_data = True; sc.render.use_motion_blur = False
sc.render.use_simplify = True; sc.render.simplify_subdivision_render = 2; sc.cycles.texture_limit_render = '2048'
w = bpy.data.worlds.new("World"); sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes["Background"]; bg.inputs["Color"].default_value = (0.08, 0.10, 0.30, 1); bg.inputs["Strength"].default_value = 0.15

def area(name, loc, power, size, col, target, shape='DISK'):
    ld = bpy.data.lights.new(name, 'AREA'); ld.energy = power; ld.size = size; ld.color = col; ld.shape = shape
    o = bpy.data.objects.new(name, ld); sc.collection.objects.link(o); o.location = loc
    d = Vector(target) - o.location; o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return o
# cell: candle (point) + warm fill + cool moon through the window
area("CELL_Fill", (0.6, -1.4, 2.2), 70, 1.6, (1.0, 0.78, 0.55), (-0.3, 0.5, 1.0))
area("CELL_Moon", (-0.6, 1.5, 2.4), 80, 0.8, (0.45, 0.60, 1.0), (-0.1, 0.0, 0.8))
area("CELL_DoorFill", (0.6, -0.8, 1.8), 45, 1.2, (0.95, 0.85, 0.75), (1.3, 0.4, 1.1))
area("COR_Fill", (5.5, 0.7, 3.0), 120, 3.0, (0.55, 0.65, 1.0), (5.5, 0.7, 0.0), shape='RECTANGLE')
# exterior dusk: low warm sun + cool sky fill
sun = bpy.data.lights.new("SunDusk", 'SUN'); sun.energy = 2.2; sun.color = (1.0, 0.55, 0.30); sun.angle = R_(3)
so_ = bpy.data.objects.new("SunDusk", sun); sc.collection.objects.link(so_); so_.rotation_euler = (R_(70), 0, R_(-60))
area("EXT_Fill", (11.6, -3.0, 4.0), 260, 4.0, (0.55, 0.60, 1.0), (11.6, 0.8, 1.0))
area("WS_Key", (14.2, -1.2, 2.8), 160, 1.6, (1.0, 0.80, 0.60), (15.8, 0.4, 1.0))
area("WS_Fill", (14.0, 2.6, 2.6), 70, 1.6, (0.70, 0.75, 1.0), (15.8, 0.4, 1.0))
# steps: bright day
sun2 = bpy.data.lights.new("SunDay", 'SUN'); sun2.energy = 4.0; sun2.color = (1.0, 0.93, 0.82); sun2.angle = R_(2)
so2 = bpy.data.objects.new("SunDay", sun2); sc.collection.objects.link(so2); so2.rotation_euler = (R_(50), 0, R_(25))
area("ST_Fill", (SX, -6.0, 3.0), 600, 6.0, (0.85, 0.92, 1.0), (SX, 2.0, 1.5))

GX = -4.3
ext_lights = [TLA, TLB, FLO, FL2O, O_["EXT_Fill"], O_["WS_Key"], O_["WS_Fill"]] if False else []
for o in EXT + [TLA, TLB, FLO, FL2O] + [bpy.data.objects[n] for n in ("EXT_Fill", "WS_Key", "WS_Fill")]:
    if o.parent is None: o.location.x += GX
KEY1.location.x += GX
sc["GX"] = GX
# collections by island (for the visibility switching in stage B)
for name, objs in (("SET_CELL", CELL), ("SET_COR", COR), ("SET_EXT", EXT), ("SET_STEPS", STEPS)):
    for o in objs: o["island"] = name
for o in (TIN1, WAX1, MKEY, KEY1, KEY2, WICK, CLO):
    o["island"] = "PROP"
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("BUILD_OK", OUT)
for r in (PRIS, VIS, SMITH):
    print("BONES", r.name, {n: tuple(round(x, 3) for x in r.data.bones[n].head_local) for n in ("root", "head", "eye.L", "foot.L", "wrist.L", "pelvis.L")})
