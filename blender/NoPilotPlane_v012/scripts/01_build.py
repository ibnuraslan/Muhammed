"""NoPilotPlane v012 stage A (from scratch): the characters, the airliner interior (cabin + cockpit), the wing outside
the windows and the sky/ground world that moves around the plane.
blender -b --python 01_build.py -- <seat.glb> <pilot_seat.glb> <out.blend>

Axes: the plane's nose is +Y, the floor is z=0, x+ is the right-hand side (first officer's side).
CABIN  y -5.2 .. 2.0  (6 rows, 2+2 seats, a wide aisle); front bulkhead at y=2.0 with the cockpit doorway x -0.5..0.5
COCKPIT y 2.0 .. 5.5  (captain seat left x=-0.52, FO seat right x=+0.52, seats at y=3.85, yokes at y~4.5)
WORLD  the ground, clouds, town and field hang under the empties WORLD_ROT (attitude) > WORLD_POS (distance, altitude);
       the plane itself never moves, so every person and contact stays exact."""
import bpy, bmesh, sys, math, random, os
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
exec(open(os.path.join(HERE, "lib_build.py")).read())
a = sys.argv[sys.argv.index("--") + 1:]
SEAT_GLB, PSEAT_GLB, OUT = a[0], a[1], a[2]
random.seed(12)
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
sc = bpy.context.scene
sc.render.fps = 60
sc.frame_start, sc.frame_end = 1, 3481
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920

def col(name, parent=None):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    p = parent or sc.collection
    if c.name not in p.children: p.children.link(c)
    return c
C_CHAR, C_CABIN, C_COCK, C_WORLD = col("CHARACTERS"), col("CABIN"), col("COCKPIT"), col("WORLD")
def to_col(o, c):
    for cc in list(o.users_collection): cc.objects.unlink(o)
    c.objects.link(o)
def mesh_obj(name, verts, faces, material, c):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    o = bpy.data.objects.new(name, me); c.objects.link(o)
    if material: me.materials.append(material)
    return o

# ================================================================== the characters (ONE model each, real MPFB garments)
def finish_char(rig, body, top_col, bot_col, tex_override=None, skin_mult=(1.0, 0.82, 0.70), hair_mult=None, sleeve_col=None):
    eye_fix(rig)
    for c in rig.children:
        if c.type != 'MESH': continue
        if hair_mult and any(k in c.name.lower() for k in ("short", "pony", "bob", "long", "braid", "afro", "eyebrow")):
            for m in c.data.materials: tint(m, hair_mult)
        if "teeth" in c.name:
            for m in c.data.materials: tint(m, (1.4, 1.35, 1.3))
    for m in body.data.materials: tint(m, skin_mult)
    suit = [c for c in rig.children if c.type == 'MESH' and "suit" in c.name][0]
    # split the garment into a TOP and a BOTTOM material by the dominant bone of each face, then recolour each
    # (the diffuse's luminance keeps every fold; the colours are deep and saturated)
    m0 = suit.data.materials[0]
    if tex_override:
        for nd in m0.node_tree.nodes:
            if nd.type == 'TEX_IMAGE' and nd.image and "diffuse" in nd.image.name.lower(): nd.image = tex_override
    def recol(m, colr):
        nt = m.node_tree
        for nd in list(nt.nodes):
            if nd.type == 'TEX_IMAGE' and nd.image and "diffuse" in nd.image.name.lower():
                for lk in list(nd.outputs['Color'].links):
                    bw = nt.nodes.new('ShaderNodeRGBToBW'); mth = nt.nodes.new('ShaderNodeMath'); mth.operation = 'POWER'
                    mth.inputs[1].default_value = 0.8
                    sc2 = nt.nodes.new('ShaderNodeMath'); sc2.operation = 'MULTIPLY'; sc2.inputs[1].default_value = 2.6
                    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
                    mx.inputs['B'].default_value = (*colr, 1)
                    nt.links.new(nd.outputs['Color'], bw.inputs[0]); nt.links.new(bw.outputs[0], mth.inputs[0])
                    nt.links.new(mth.outputs[0], sc2.inputs[0]); nt.links.new(sc2.outputs[0], mx.inputs['A'])
                    nt.links.new(mx.outputs['Result'], lk.to_socket)
            if nd.type == 'NORMAL_MAP': nd.inputs["Strength"].default_value = 0.6
    if top_col or bot_col or sleeve_col:
        mt = m0.copy(); mt.name = rig.name + "_top"; mb = m0.copy(); mb.name = rig.name + "_bottom"
        if top_col: recol(mt, top_col)
        if bot_col: recol(mb, bot_col)
        suit.data.materials.clear(); suit.data.materials.append(mt); suit.data.materials.append(mb)
        bn = {b.name for b in rig.data.bones}; i2n = {g.index: g.name for g in suit.vertex_groups if g.name in bn}
        LEG = ("upperleg", "lowerleg", "foot", "toe", "pelvis", "root")
        vdom = {}
        for v in suit.data.vertices:
            best = (0, None)
            for g in v.groups:
                n = i2n.get(g.group)
                if n and g.weight > best[0]: best = (g.weight, n)
            vdom[v.index] = best[1]
        zs = [v.co.z for v in suit.data.vertices]
        for p in suit.data.polygons:
            legs = sum(1 for vi in p.vertices if vdom[vi] and vdom[vi].startswith(LEG))
            zc = sum(suit.data.vertices[vi].co.z for vi in p.vertices) / len(p.vertices)
            # the hem of the top hangs over the belt: faces above the waist line stay TOP
            p.material_index = 1 if (legs * 2 > len(p.vertices) and zc < WAIST_Z[rig.name]) else 0
    if sleeve_col:
        ms = m0.copy(); ms.name = rig.name + "_sleeves"; recol(ms, sleeve_col)
        idx = len(suit.data.materials); suit.data.materials.append(ms)
        bn = {b.name for b in rig.data.bones}; i2n = {g.index: g.name for g in suit.vertex_groups if g.name in bn}
        ARMB = ("upperarm", "lowerarm", "wrist")
        for p in suit.data.polygons:
            if p.material_index != 0: continue
            arm = 0
            for vi in p.vertices:
                best = (0, None)
                for g in suit.data.vertices[vi].groups:
                    n = i2n.get(g.group)
                    if n and g.weight > best[0]: best = (g.weight, n)
                if best[1] and best[1].startswith(ARMB): arm += 1
            if arm * 2 > len(p.vertices): p.material_index = idx
    # solid garments: real thickness, rim-filled edges (no hollow sleeves, no open crotch)
    for c in rig.children:
        if c.type == 'MESH' and ("suit" in c.name or "shoes" in c.name):
            so = c.modifiers.new("solid", 'SOLIDIFY'); so.thickness = 0.004; so.offset = 1.0; so.use_rim = True; so.use_rim_only = False
            i = c.modifiers.find("solid")
            while i > c.modifiers.find("Armature") + 1:
                c.modifiers.move(i, i - 1); i -= 1
    for c in rig.children: to_col(c, C_CHAR)
    to_col(rig, C_CHAR)
    return suit

WAIST_Z = {}
CAST = [
    # name, gender, age, race, hair, skin, brows, height, weight, muscle, suit, top colour, bottom colour, hair tint
    ("HERO", 1.0, 0.45, {"caucasian": 0.55, "african": 0.15, "asian": 0.30}, "short02/short02.mhclo",
     "young_caucasian_male/young_caucasian_male.mhmat", "eyebrow001/eyebrow001.mhclo", 0.55, 0.45, 0.5,
     "male_casualsuit02", None, None, (0.45, 0.30, 0.20)),
    ("CAPT", 1.0, 0.75, {"african": 0.8, "caucasian": 0.2, "asian": 0.0}, "short04/short04.mhclo",
     "middleage_african_male/middleage_african_male.mhmat", "eyebrow003/eyebrow003.mhclo", 0.6, 0.55, 0.55,
     "male_casualsuit01", (0.95, 0.95, 0.97), (0.02, 0.03, 0.12), (0.35, 0.33, 0.33)),
    ("FO", 1.0, 0.5, {"asian": 0.8, "caucasian": 0.2, "african": 0.0}, "short01/short01.mhclo",
     "young_asian_male/young_asian_male.mhmat", "eyebrow002/eyebrow002.mhclo", 0.5, 0.45, 0.5,
     "male_casualsuit01", (0.95, 0.95, 0.97), (0.02, 0.03, 0.12), None),
    ("PAX1", 1.0, 0.55, {"caucasian": 0.9, "african": 0.0, "asian": 0.1}, "short03/short03.mhclo",
     "middleage_caucasian_male/middleage_caucasian_male.mhmat", "eyebrow004/eyebrow004.mhclo", 0.55, 0.6, 0.5,
     "male_casualsuit03", None, (0.10, 0.08, 0.06), (0.55, 0.42, 0.25)),
    ("PAX2", 0.0, 0.45, {"african": 0.85, "caucasian": 0.15, "asian": 0.0}, "afro01/afro01.mhclo",
     "young_african_female/young_african_female.mhmat", "eyebrow010/eyebrow010.mhclo", 0.45, 0.5, 0.4,
     "female_casualsuit02", (0.0, 0.55, 0.50), (0.05, 0.05, 0.30), None),
    ("PAX3", 1.0, 0.5, {"african": 0.6, "caucasian": 0.2, "asian": 0.2}, "short02/short02.mhclo",
     "young_african_male/young_african_male.mhmat", "eyebrow005/eyebrow005.mhclo", 0.55, 0.55, 0.6,
     "male_casualsuit05", (0.05, 0.30, 0.08), (0.30, 0.18, 0.06), None),
    ("PAX4", 0.0, 0.5, {"caucasian": 0.8, "asian": 0.2, "african": 0.0}, "ponytail01/ponytail01.mhclo",
     "young_caucasian_female/young_caucasian_female.mhmat", "eyebrow009/eyebrow009.mhclo", 0.45, 0.45, 0.4,
     "female_elegantsuit01", (0.75, 0.04, 0.30), (0.03, 0.03, 0.05), (0.75, 0.45, 0.18)),
    ("PAX5", 1.0, 0.85, {"caucasian": 0.7, "asian": 0.3, "african": 0.0}, "short04/short04.mhclo",
     "old_caucasian_male/old_caucasian_male.mhmat", "eyebrow006/eyebrow006.mhclo", 0.5, 0.65, 0.4,
     "male_casualsuit06", (1.0, 0.70, 0.02), (0.15, 0.10, 0.30), (1.3, 1.3, 1.3)),
    ("PAX6", 0.0, 0.55, {"asian": 0.85, "caucasian": 0.15, "african": 0.0}, "braid01/braid01.mhclo",
     "young_asian_female/young_asian_female.mhmat", "eyebrow011/eyebrow011.mhclo", 0.45, 0.5, 0.4,
     "female_casualsuit01", (0.30, 0.05, 0.60), (0.02, 0.10, 0.25), None),
    ("PAX7", 1.0, 0.4, {"caucasian": 0.5, "asian": 0.2, "african": 0.3}, "short01/short01.mhclo",
     "young_caucasian_male2/young_caucasian_male2.mhmat", "eyebrow007/eyebrow007.mhclo", 0.5, 0.45, 0.5,
     "male_casualsuit04", (0.0, 0.45, 0.70), (0.25, 0.20, 0.15), (0.25, 0.18, 0.12)),
    ("PAX8", 0.0, 0.6, {"african": 0.5, "caucasian": 0.3, "asian": 0.2}, "ponytail01/ponytail01.mhclo",
     "middleage_african_female/middleage_african_female.mhmat", "eyebrow012/eyebrow012.mhclo", 0.45, 0.55, 0.4,
     "female_casualsuit02", (0.95, 0.65, 0.0), (0.05, 0.05, 0.25), (0.25, 0.2, 0.2)),
    ("PAX9", 1.0, 0.6, {"asian": 0.6, "caucasian": 0.4, "african": 0.0}, "short03/short03.mhclo",
     "middleage_asian_male/middleage_asian_male.mhmat", "eyebrow008/eyebrow008.mhclo", 0.55, 0.5, 0.5,
     "male_elegantsuit01", (0.02, 0.05, 0.30), (0.02, 0.05, 0.30), None),
    ("PAX10", 0.0, 0.7, {"caucasian": 0.9, "asian": 0.1, "african": 0.0}, "braid01/braid01.mhclo",
     "middleage_caucasian_female/middleage_caucasian_female.mhmat", "eyebrow010/eyebrow010.mhclo", 0.45, 0.6, 0.4,
     "female_elegantsuit01", (0.0, 0.50, 0.45), (0.10, 0.05, 0.20), (0.9, 0.7, 0.4)),
]
CH = {}
hero_tee = bpy.data.images.load(os.path.join(PKG, "assets/hero_tee_diffuse.png")); hero_tee.name = "hero_tee_diffuse"
for (nm, g, age, race, hair, skin, brow, hgt, wgt, mus, suit, tc, bc, hm) in CAST:
    rig, body = human(nm, g, age, race, hair, skin, brow, height=hgt, weight=wgt, muscle=mus,
                      clothes=[suit + "/" + suit + ".mhclo", "shoes01/shoes01.mhclo" if g > 0.5 else "shoes02/shoes02.mhclo"])
    WAIST_Z[nm] = rig.data.bones["spine04"].head_local.z + 0.02
    s = finish_char(rig, body, tc, bc, tex_override=hero_tee if nm == "HERO" else None, hair_mult=hm,
                    sleeve_col=(0.80, 0.10, 0.03) if nm == "HERO" else None,
                    skin_mult=(1.0, 0.85, 0.74) if race.get("african", 0) < 0.5 else (1.05, 0.9, 0.8))
    s.name = nm + ".clothes"
    CH[nm] = (rig, body)
eye_group_fix()
EG = bpy.data.node_groups.get("EnhancedEye")
for n in (EG.nodes if EG else []):
    if n.type == 'MATH' and abs(n.inputs[1].default_value - 0.92) < 1e-4: n.inputs[1].default_value = 0.96
# park everybody far away; 02_animate places them
for i, (nm, (rig, body)) in enumerate(CH.items()):
    rig.location = (30 + i * 1.5, 0, 0)

# ================================================================== materials
def noise_mat(name, c1, c2, scale=30.0, rough=0.6, coat=0.0, bump=0.1, metal=0.0):
    m = mat(name, c1, rough=rough, coat=coat, metal=metal)
    nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = scale
    nz.inputs["Detail"].default_value = 5.0
    cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (*c1, 1); cr.color_ramp.elements[1].color = (*c2, 1)
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"]); nt.links.new(nz.outputs["Fac"], cr.inputs["Fac"])
    nt.links.new(cr.outputs["Color"], p.inputs["Base Color"])
    if bump:
        bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump; bp.inputs["Distance"].default_value = 0.002
        nt.links.new(nz.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], p.inputs["Normal"])
    return m

def emit_mat(name, colr, strength):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n)
    e = nt.nodes.new("ShaderNodeEmission"); e.inputs["Color"].default_value = (*colr, 1); e.inputs["Strength"].default_value = strength
    nt.links.new(e.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    return m

def glass_mat(name, tint=(0.9, 0.97, 1.0), refl=0.05):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n)
    tr = nt.nodes.new("ShaderNodeBsdfTransparent"); tr.inputs["Color"].default_value = (*tint, 1)
    gl = nt.nodes.new("ShaderNodeBsdfGlossy"); gl.inputs["Roughness"].default_value = 0.03
    fr = nt.nodes.new("ShaderNodeFresnel"); fr.inputs["IOR"].default_value = 1.45
    mm = nt.nodes.new("ShaderNodeMath"); mm.operation = 'MULTIPLY'; mm.inputs[1].default_value = refl / 0.035
    nt.links.new(fr.outputs[0], mm.inputs[0])
    mx = nt.nodes.new("ShaderNodeMixShader"); nt.links.new(mm.outputs[0], mx.inputs["Fac"])
    nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(gl.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    return m

M_WALL = noise_mat("M_CabinWall", (0.62, 0.78, 0.86), (0.68, 0.84, 0.90), scale=60, rough=0.45, coat=0.2, bump=0.03)
M_PANEL_TEAL = noise_mat("M_PanelTeal", (0.00, 0.28, 0.36), (0.01, 0.36, 0.44), scale=40, rough=0.4, coat=0.3, bump=0.03)
M_BULK = noise_mat("M_Bulkhead", (0.16, 0.02, 0.30), (0.22, 0.04, 0.40), scale=30, rough=0.45, coat=0.3, bump=0.03)   # deep purple
M_CARPET = noise_mat("M_Carpet", (0.16, 0.005, 0.05), (0.24, 0.01, 0.08), scale=400, rough=0.95, bump=0.4)              # wine red
M_CEIL = mat("M_Ceiling", (0.92, 0.93, 0.95), rough=0.5)
M_BIN = mat("M_Bins", (0.90, 0.91, 0.94), rough=0.35, coat=0.3)
M_MOOD = emit_mat("M_MoodLight", (0.65, 0.10, 1.0), 6.0)          # violet mood-light strips
M_MOOD2 = emit_mat("M_MoodLight2", (0.10, 0.55, 1.0), 5.0)        # cyan strips
M_WIN_FRAME = mat("M_WinFrame", (0.95, 0.95, 0.97), rough=0.3, coat=0.4)
M_SHADE = mat("M_WinShade", (0.85, 0.86, 0.88), rough=0.5)
M_GLASS = glass_mat("M_Glass")
M_CHROME = mat("M_Chrome", (0.85, 0.86, 0.9), rough=0.15, metal=1.0)
M_PANEL = noise_mat("M_CockpitPanel", (0.03, 0.05, 0.12), (0.05, 0.08, 0.17), scale=80, rough=0.55, bump=0.05)    # deep navy
M_PANEL2 = noise_mat("M_CockpitPanel2", (0.06, 0.09, 0.20), (0.08, 0.12, 0.25), scale=80, rough=0.5, bump=0.05)
M_COCK_WALL = noise_mat("M_CockpitWall", (0.04, 0.08, 0.22), (0.06, 0.11, 0.28), scale=50, rough=0.5, bump=0.03)
M_COCK_FLOOR = noise_mat("M_CockpitFloor", (0.015, 0.02, 0.05), (0.03, 0.035, 0.07), scale=300, rough=0.9, bump=0.3)
M_YOKE = mat("M_Yoke", (0.02, 0.02, 0.025), rough=0.35, coat=0.3)
M_YOKE_GRIP = noise_mat("M_YokeGrip", (0.10, 0.05, 0.03), (0.16, 0.08, 0.04), scale=900, rough=0.6, bump=0.3)
M_RED = mat("M_RedKnob", (0.85, 0.02, 0.02), rough=0.3, coat=0.4)
M_YELLOW = mat("M_Yellow", (1.0, 0.75, 0.0), rough=0.35, coat=0.3)
M_WHITE = mat("M_White", (0.92, 0.92, 0.94), rough=0.35)
M_BLACK = mat("M_Black", (0.02, 0.02, 0.025), rough=0.4)
M_SCREEN_BEZEL = mat("M_Bezel", (0.015, 0.015, 0.02), rough=0.3, coat=0.5)
M_DOOR = noise_mat("M_Door", (0.20, 0.03, 0.36), (0.26, 0.05, 0.44), scale=30, rough=0.4, coat=0.3, bump=0.02)

# ================================================================== CABIN shell (curved section, extruded along Y)
Y0, Y1 = -5.4, 2.0
PROF = [(1.70, 0.0), (1.78, 0.45), (1.80, 0.85), (1.76, 1.25), (1.66, 1.55), (1.50, 1.80), (1.20, 2.02), (0.70, 2.15), (0.0, 2.18)]
WIN_Y = [-4.55 + 0.95 * i + 0.05 for i in range(7)]       # one window per row, level with the passengers' heads
WIN_Z = (0.95, 1.32); WIN_W = 0.30
def cabin_side(sx):
    """one side wall as a grid (y steps x profile) with rounded-rect window holes"""
    bm = bmesh.new()
    ys = []
    y = Y0
    while y < Y1 - 1e-6:
        ys.append(y); y += 0.05
    ys.append(Y1)
    prof = []
    for (x0, z0), (x1, z1) in zip(PROF[:-1], PROF[1:]):
        n = max(2, int(math.hypot(x1 - x0, z1 - z0) / 0.05))
        for k in range(n): prof.append((x0 + (x1 - x0) * k / n, z0 + (z1 - z0) * k / n))
    prof.append(PROF[-1])
    V = [[bm.verts.new((sx * px, yy, pz)) for (px, pz) in prof] for yy in ys]
    for i in range(len(ys) - 1):
        for j in range(len(prof) - 1):
            yc = (ys[i] + ys[i + 1]) / 2; zc = (prof[j][1] + prof[j + 1][1]) / 2
            hole = any(abs(yc - wy) < WIN_W / 2 and WIN_Z[0] < zc < WIN_Z[1] for wy in WIN_Y)
            if not hole:
                f = bm.faces.new((V[i][j], V[i + 1][j], V[i + 1][j + 1], V[i][j + 1]) if sx > 0 else (V[i][j], V[i][j + 1], V[i + 1][j + 1], V[i + 1][j]))
    me = bpy.data.meshes.new("CAB_Side"); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("CAB_Side" + ("R" if sx > 0 else "L"), me); C_CABIN.objects.link(o)
    me.materials.append(M_WALL)
    so = o.modifiers.new("solid", 'SOLIDIFY'); so.thickness = 0.06; so.offset = 1.0
    for p in me.polygons: p.use_smooth = True
    return o
for sx in (1, -1): cabin_side(sx)
# floor (carpet), skirt panels
box("CAB_Floor", (3.6, Y1 - Y0, 0.05), (0, (Y0 + Y1) / 2, -0.025), M_CARPET, bevel=0.0)
to_col(bpy.context.active_object, C_CABIN)
for sx in (1, -1):
    for wy in WIN_Y:     # window bezels (rounded frames) + an open shade above + outer glass
        bpy.ops.mesh.primitive_torus_add(major_radius=0.18, minor_radius=0.025, location=(sx * 1.79, wy, 1.135),
                                         rotation=(0, math.radians(90), 0), major_segments=32, minor_segments=8)
        t = bpy.context.active_object; t.name = "CAB_Bezel"; t.scale = (1.0, 0.95, 1.20)
        t.data.materials.append(M_WIN_FRAME); to_col(t, C_CABIN)
# overhead bins (each side) and the mood-light strips under them
for sx in (1, -1):
    b = box("CAB_Bins" + ("R" if sx > 0 else "L"), (0.55, Y1 - Y0 - 0.6, 0.42), (sx * 1.28, (Y0 + Y1) / 2 - 0.3, 1.78), M_BIN, bevel=0.03)
    to_col(b, C_CABIN)
    s_ = box("CAB_Mood" + ("R" if sx > 0 else "L"), (0.02, Y1 - Y0 - 0.6, 0.02), (sx * 1.00, (Y0 + Y1) / 2 - 0.3, 1.56), M_MOOD, bevel=0.0)
    to_col(s_, C_CABIN)
    s2 = box("CAB_MoodC" + ("R" if sx > 0 else "L"), (0.02, Y1 - Y0 - 0.6, 0.02), (sx * 0.62, (Y0 + Y1) / 2 - 0.3, 2.10), M_MOOD2, bevel=0.0)
    to_col(s2, C_CABIN)
# front bulkhead (deep purple), with the doorway; the logo panel above the door on the cabin side
def wall_with_hole(name, y0, y1, xr, zr, hole_x, hole_z, material, c):
    pieces = []
    for nm, x0, x1, z0, z1 in (("L", xr[0], hole_x[0], zr[0], zr[1]), ("R", hole_x[1], xr[1], zr[0], zr[1]),
                               ("T", hole_x[0], hole_x[1], hole_z[1], zr[1])):
        if x1 - x0 < 1e-4 or z1 - z0 < 1e-4: continue
        pieces.append(box(name + nm, (x1 - x0, y1 - y0, z1 - z0), ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), material, bevel=0.0))
    bpy.ops.object.select_all(action='DESELECT')
    for p in pieces: p.select_set(True)
    bpy.context.view_layer.objects.active = pieces[0]; bpy.ops.object.join()
    o = bpy.context.active_object; o.name = name; to_col(o, c)
    return o
DOOR_X = (-0.50, 0.50); DOOR_Z = 1.98
wall_with_hole("CAB_Bulkhead", 1.95, 2.05, (-1.8, 1.8), (0.0, 2.2), DOOR_X, (0.0, DOOR_Z), M_BULK, C_CABIN)
# door frame (white trim) and the door leaf, swung open INTO the cockpit against the right wall of the entry
for nm, sz, lc in (("CAB_DoorTrimL", (0.06, 0.14, DOOR_Z), (DOOR_X[0] - 0.03, 2.0, DOOR_Z / 2)),
                   ("CAB_DoorTrimR", (0.06, 0.14, DOOR_Z), (DOOR_X[1] + 0.03, 2.0, DOOR_Z / 2)),
                   ("CAB_DoorTrimT", (1.12, 0.14, 0.06), (0, 2.0, DOOR_Z + 0.03))):
    to_col(box(nm, sz, lc, M_WIN_FRAME, bevel=0.008), C_CABIN)
DOOR = box("CK_Door", (0.98, 0.05, 1.94), (0.49, 0.0, 0.97), M_DOOR, bevel=0.01)
DOOR.data.transform(Matrix.Translation((0, 0, 0)))
bpy.ops.object.origin_set(type='ORIGIN_CURSOR')    # cursor at world origin -> origin at the door's hinge corner
DOOR.location = (DOOR_X[1] - 0.02, 2.10, 0.01); DOOR.rotation_euler = (0, 0, math.radians(-95))
to_col(DOOR, C_COCK)
# logo panel above the doorway (cabin side): DA KRAS FILMS, white on the purple bulkhead
logo_w = bpy.data.images.load("/home/user/Muhammed/blender/assets/brand/DaKrasFilms_logo_white.png"); logo_w.name = "logo_white"
logo_d = bpy.data.images.load("/home/user/Muhammed/blender/assets/brand/DaKrasFilms_logo_dark.png"); logo_d.name = "logo_dark"
def logo_mat(name, img, base, emit=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*base, 1); p.inputs["Roughness"].default_value = 0.4
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = img; t.extension = 'CLIP'
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'
    nt.links.new(t.outputs["Alpha"], mx.inputs["Factor"]); mx.inputs["A"].default_value = (*base, 1)
    nt.links.new(t.outputs["Color"], mx.inputs["B"]); nt.links.new(mx.outputs["Result"], p.inputs["Base Color"])
    if emit:
        nt.links.new(mx.outputs["Result"], p.inputs["Emission Color"]); p.inputs["Emission Strength"].default_value = emit
    return m
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 1.944, 2.10), rotation=(math.radians(90), 0, math.radians(180)))
LP = bpy.context.active_object; LP.name = "CAB_LogoPanel"; LP.scale = (0.56, 0.24, 1)
LP.data.materials.append(logo_mat("M_LogoPanel", logo_w, (0.16, 0.02, 0.30), emit=0.6)); to_col(LP, C_CABIN)
# ceiling above the aisle (between the bins) and the ceiling lights
to_col(box("CAB_Ceil", (1.5, Y1 - Y0, 0.04), (0, (Y0 + Y1) / 2, 2.16), M_CEIL, bevel=0.0), C_CABIN)
# rear wall (closes the tube behind the last row)
to_col(box("CAB_Rear", (3.6, 0.1, 2.3), (0, Y0 - 0.05, 1.1), M_BULK, bevel=0.0), C_CABIN)
# galley side cabinets ahead of row 1, left and right of the walkway (stainless + teal doors)
for sx in (1, -1):
    to_col(box("CAB_Galley" + ("R" if sx > 0 else "L"), (0.85, 0.75, 1.05), (sx * 1.25, 1.50, 0.525), M_PANEL_TEAL, bevel=0.02), C_CABIN)
    to_col(box("CAB_GalleyTop" + ("R" if sx > 0 else "L"), (0.88, 0.78, 0.03), (sx * 1.25, 1.50, 1.065), M_CHROME, bevel=0.005), C_CABIN)

# ---- passenger seats (Sketchfab "Seat" by maximmus / shah_max, CC BY 4.0), recoloured
def import_glb(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == 'MESH']
    for o in meshes:
        mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
    for o in new:
        if o not in meshes: bpy.data.objects.remove(o, do_unlink=True)
    return meshes
sm = import_glb(SEAT_GLB)
SEAT_PARTS = {}
for o in sm:
    nm = o.name.split("_")[0].strip()
    SEAT_PARTS[nm] = o
bpy.ops.object.select_all(action='DESELECT')
for o in sm: o.select_set(True)
bpy.context.view_layer.objects.active = sm[0]
cushion = SEAT_PARTS.get("Ziri")
cz = max((cushion.matrix_world @ Vector(c)).z for c in cushion.bound_box)
bpy.ops.object.join()
SEAT = bpy.context.active_object; SEAT.name = "SEAT_proto"
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
pts = [v.co for v in SEAT.data.vertices]
mn = Vector([min(p[i] for p in pts) for i in range(3)]); mx = Vector([max(p[i] for p in pts) for i in range(3)])
# mm -> m; cushion top at 0.46 m, width 0.47 m; flip so the seat faces +Y
s_z = 0.46 / (cz - mn.z); s_x = 0.47 / (mx.x - mn.x); s_y = 0.80 * s_z
SEAT.data.transform(Matrix.Translation(-Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))))
SEAT.data.transform(Matrix.Diagonal((s_x, s_y, s_z, 1)))
SEAT.data.transform(Matrix.Rotation(math.radians(180), 4, 'Z'))
for p in SEAT.data.polygons: p.use_smooth = True
pts = [v.co for v in SEAT.data.vertices]
print("SEAT dims", [round(max(p[i] for p in pts) - min(p[i] for p in pts), 3) for i in range(3)],
      "y", round(min(p.y for p in pts), 3), round(max(p.y for p in pts), 3))
def recolor_img(m, colr, gain=2.4):
    nt = m.node_tree
    for nd in list(nt.nodes):
        if nd.type == 'TEX_IMAGE' and nd.image:
            for lk in list(nd.outputs['Color'].links):
                if lk.to_node.type != 'BSDF_PRINCIPLED' or lk.to_socket.name != 'Base Color': continue
                bw = nt.nodes.new('ShaderNodeRGBToBW'); g_ = nt.nodes.new('ShaderNodeMath'); g_.operation = 'MULTIPLY'; g_.inputs[1].default_value = gain
                mx_ = nt.nodes.new('ShaderNodeMix'); mx_.data_type = 'RGBA'; mx_.blend_type = 'MULTIPLY'; mx_.inputs['Factor'].default_value = 1.0
                mx_.inputs['B'].default_value = (*colr, 1)
                nt.links.new(nd.outputs['Color'], bw.inputs[0]); nt.links.new(bw.outputs[0], g_.inputs[0]); nt.links.new(g_.outputs[0], mx_.inputs['A'])
                nt.links.new(mx_.outputs['Result'], lk.to_socket)
for m in SEAT.data.materials:
    recolor_img(m, (0.06, 0.10, 0.75))                # rich royal-blue upholstery
    for n in m.node_tree.nodes:
        if n.type == 'BSDF_PRINCIPLED' and not n.inputs["Roughness"].is_linked: n.inputs["Roughness"].default_value = 0.6
SEAT_X = (-1.12, -0.62, 0.62, 1.12)
ROWS_Y = [-4.55 + 0.95 * i for i in range(6)]          # -4.55 .. 0.20
SEATS = {}
for ri, ry in enumerate(ROWS_Y):
    for si, sx in enumerate(SEAT_X):
        o = SEAT.copy(); o.data = SEAT.data; o.name = "SEAT_r%d_%d" % (ri + 1, si); o.location = (sx, ry, 0.0)
        C_CABIN.objects.link(o); SEATS[(ri + 1, si)] = o
bpy.data.objects.remove(SEAT, do_unlink=True)
for o in list(bpy.data.objects):
    if o.name in ("Ziri",): pass

# ================================================================== COCKPIT
CK_Y0, CK_Y1 = 2.05, 5.6
# cockpit shell: narrower tube that tapers toward the nose
def cock_shell():
    bm = bmesh.new()
    sections = []
    ys = [CK_Y0 + i * 0.1 for i in range(int((CK_Y1 - CK_Y0) / 0.1) + 1)]
    for yy in ys:
        t = (yy - CK_Y0) / (CK_Y1 - CK_Y0)
        w = 1.55 - 0.35 * max(0.0, (t - 0.55) / 0.45) ** 1.5        # half width
        top = 2.12 - 0.25 * max(0.0, (t - 0.6) / 0.4)
        prof = [(-w, 0.0), (-w - 0.05, 0.6), (-w + 0.02, 1.2), (-w + 0.25, 1.75), (-w * 0.45, top - 0.02), (0.0, top),
                (w * 0.45, top - 0.02), (w - 0.25, 1.75), (w - 0.02, 1.2), (w + 0.05, 0.6), (w, 0.0)]
        sections.append([bm.verts.new((px, yy, pz)) for px, pz in prof])
    for i in range(len(sections) - 1):
        for j in range(len(sections[0]) - 1):
            bm.faces.new((sections[i][j], sections[i][j + 1], sections[i + 1][j + 1], sections[i + 1][j]))
    me = bpy.data.meshes.new("CK_Shell"); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("CK_Shell", me); C_COCK.objects.link(o); me.materials.append(M_COCK_WALL)
    so = o.modifiers.new("solid", 'SOLIDIFY'); so.thickness = 0.05; so.offset = -1.0
    for p in me.polygons: p.use_smooth = True
    return o
SHELL = cock_shell()
# window openings: remove shell faces that fall inside the windscreen and side-window zones
def cut_windows(o):
    me = o.data; bm = bmesh.new(); bm.from_mesh(me)
    kill = []
    for f in bm.faces:
        c = f.calc_center_median()
        side = abs(c.x) > 0.9 and 3.35 < c.y < 4.95 and 1.10 < c.z < 1.72
        front = c.y > 4.95 and c.z > 1.22 and abs(c.x) < 1.3
        if side or front: kill.append(f)
    bmesh.ops.delete(bm, geom=kill, context='FACES')
    bm.to_mesh(me); bm.free()
cut_windows(SHELL)
to_col(box("CK_Floor", (3.2, CK_Y1 - CK_Y0, 0.05), (0, (CK_Y0 + CK_Y1) / 2, -0.025), M_COCK_FLOOR, bevel=0.0), C_COCK)
# nose cap (closes the shell ahead of the panel below the windscreen) and the windscreen frame + glass
to_col(box("CK_NoseLower", (2.6, 0.30, 1.22), (0, 5.45, 0.61), M_PANEL, bevel=0.0), C_COCK)
WS_BOT = (5.30, 1.24); WS_TOP = (4.90, 1.98)
def quad(name, p0, p1, p2, p3, material, c):
    return mesh_obj(name, [p0, p1, p2, p3], [(0, 1, 2, 3)], material, c)
# windscreen: 4 panes across (2 front, 2 angled corner panes) with posts
xs = [-1.20, -0.55, 0.0, 0.55, 1.20]
for i in range(4):
    x0, x1 = xs[i] + 0.035, xs[i + 1] - 0.035
    yb0 = WS_BOT[0] - 0.25 * (abs(x0) / 1.2) ** 2; yb1 = WS_BOT[0] - 0.25 * (abs(x1) / 1.2) ** 2
    yt0 = WS_TOP[0] - 0.2 * (abs(x0) / 1.2) ** 2; yt1 = WS_TOP[0] - 0.2 * (abs(x1) / 1.2) ** 2
    quad("CK_WSGlass%d" % i, (x0, yb0, WS_BOT[1]), (x1, yb1, WS_BOT[1]), (x1, yt1, WS_TOP[1]), (x0, yt0, WS_TOP[1]), M_GLASS, C_COCK)
for x in xs:
    yb = WS_BOT[0] - 0.25 * (abs(x) / 1.2) ** 2; yt = WS_TOP[0] - 0.2 * (abs(x) / 1.2) ** 2
    v0 = Vector((x, yb, WS_BOT[1])); v1 = Vector((x, yt, WS_TOP[1])); mid = (v0 + v1) / 2; d = v1 - v0
    bpy.ops.mesh.primitive_cube_add(size=1, location=mid)
    p = bpy.context.active_object; p.name = "CK_WSPost"; p.scale = (0.07, 0.05, d.length + 0.04)
    p.rotation_euler = (-math.atan2(d.y, d.z), 0, 0); p.data.materials.append(M_PANEL2); to_col(p, C_COCK)
to_col(box("CK_WSHeader", (2.5, 0.25, 0.10), (0, WS_TOP[0] - 0.05, WS_TOP[1] + 0.03), M_PANEL2, bevel=0.01), C_COCK)
# side windows (glass in the openings)
for sx in (1, -1):
    bpy.ops.mesh.primitive_plane_add(size=1, location=(sx * 1.53, 4.15, 1.41), rotation=(0, math.radians(90), 0))
    g = bpy.context.active_object; g.name = "CK_SideGlass" + ("R" if sx > 0 else "L"); g.scale = (0.62, 1.60, 1)
    g.data.materials.append(M_GLASS); to_col(g, C_COCK)
# main instrument panel: a slab facing the pilots, with a glareshield on top
PANEL_Y = 5.02
to_col(box("CK_Panel", (2.4, 0.18, 0.62), (0, PANEL_Y + 0.09, 0.86), M_PANEL, bevel=0.01), C_COCK)
to_col(box("CK_Glareshield", (2.45, 0.42, 0.10), (0, PANEL_Y - 0.03, 1.20), M_PANEL2, bevel=0.03), C_COCK)
to_col(box("CK_GSLip", (2.45, 0.06, 0.06), (0, PANEL_Y - 0.25, 1.17), M_BLACK, bevel=0.02), C_COCK)
# displays with SYMBOLS only (no text): per pilot an attitude display (PFD), a map (ND); the centre engine display
ATT = bpy.data.objects.new("ATT_CTL", None); C_COCK.objects.link(ATT); ATT.location = (0, 0, 0)
def screen(name, loc, size, kind):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=(math.radians(90), 0, math.radians(180)))
    o = bpy.context.active_object; o.name = name; o.scale = (size[0], size[1], 1); bpy.ops.object.transform_apply(scale=True)
    m = bpy.data.materials.new("M_" + name); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n)
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Strength"].default_value = 2.2
    tc = nt.nodes.new("ShaderNodeTexCoord")
    if kind == "pfd":
        tc.object = ATT
        # attitude: the horizon split rotates with ATT_CTL (roll = its Y rotation, pitch = its Z location)
        sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sep.inputs[0])
        gt = nt.nodes.new("ShaderNodeMath"); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = 0.0
        nt.links.new(sep.outputs["Z"], gt.inputs[0])
        mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; nt.links.new(gt.outputs[0], mx.inputs["Factor"])
        mx.inputs["A"].default_value = (0.55, 0.22, 0.04, 1); mx.inputs["B"].default_value = (0.05, 0.35, 1.0, 1)
        # the yellow aircraft symbol (fixed, in the screen's own coords)
        tc2 = nt.nodes.new("ShaderNodeTexCoord"); sp = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc2.outputs["Generated"], sp.inputs[0])
        ab = nt.nodes.new("ShaderNodeMath"); ab.operation = 'SUBTRACT'; ab.inputs[1].default_value = 0.5; nt.links.new(sp.outputs["Y"], ab.inputs[0])
        ab2 = nt.nodes.new("ShaderNodeMath"); ab2.operation = 'ABSOLUTE'; nt.links.new(ab.outputs[0], ab2.inputs[0])
        lt = nt.nodes.new("ShaderNodeMath"); lt.operation = 'LESS_THAN'; lt.inputs[1].default_value = 0.025; nt.links.new(ab2.outputs[0], lt.inputs[0])
        bx = nt.nodes.new("ShaderNodeMath"); bx.operation = 'SUBTRACT'; bx.inputs[1].default_value = 0.5; nt.links.new(sp.outputs["X"], bx.inputs[0])
        bx2 = nt.nodes.new("ShaderNodeMath"); bx2.operation = 'ABSOLUTE'; nt.links.new(bx.outputs[0], bx2.inputs[0])
        lt2 = nt.nodes.new("ShaderNodeMath"); lt2.operation = 'LESS_THAN'; lt2.inputs[1].default_value = 0.22; nt.links.new(bx2.outputs[0], lt2.inputs[0])
        gt2 = nt.nodes.new("ShaderNodeMath"); gt2.operation = 'GREATER_THAN'; gt2.inputs[1].default_value = 0.06; nt.links.new(bx2.outputs[0], gt2.inputs[0])
        a1 = nt.nodes.new("ShaderNodeMath"); a1.operation = 'MULTIPLY'; nt.links.new(lt.outputs[0], a1.inputs[0]); nt.links.new(lt2.outputs[0], a1.inputs[1])
        a2 = nt.nodes.new("ShaderNodeMath"); a2.operation = 'MULTIPLY'; nt.links.new(a1.outputs[0], a2.inputs[0]); nt.links.new(gt2.outputs[0], a2.inputs[1])
        mx2 = nt.nodes.new("ShaderNodeMix"); mx2.data_type = 'RGBA'; nt.links.new(a2.outputs[0], mx2.inputs["Factor"])
        nt.links.new(mx.outputs["Result"], mx2.inputs["A"]); mx2.inputs["B"].default_value = (1.0, 0.85, 0.0, 1)
        nt.links.new(mx2.outputs["Result"], em.inputs["Color"])
    elif kind == "nd":
        # map: dark blue field, green range rings, a magenta route line
        sp = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Generated"], sp.inputs[0])
        cmb = nt.nodes.new("ShaderNodeCombineXYZ"); nt.links.new(sp.outputs["X"], cmb.inputs["X"])
        sub = nt.nodes.new("ShaderNodeMath"); sub.operation = 'MULTIPLY'; sub.inputs[1].default_value = 1.0; nt.links.new(sp.outputs["Y"], sub.inputs[0])
        nt.links.new(sub.outputs[0], cmb.inputs["Y"])
        vm = nt.nodes.new("ShaderNodeVectorMath"); vm.operation = 'DISTANCE'; vm.inputs[1].default_value = (0.5, 0.12, 0)
        nt.links.new(cmb.outputs[0], vm.inputs[0])
        ring = nt.nodes.new("ShaderNodeMath"); ring.operation = 'PINGPONG'; ring.inputs[1].default_value = 0.11; nt.links.new(vm.outputs["Value"], ring.inputs[0])
        rl = nt.nodes.new("ShaderNodeMath"); rl.operation = 'LESS_THAN'; rl.inputs[1].default_value = 0.008; nt.links.new(ring.outputs[0], rl.inputs[0])
        rx = nt.nodes.new("ShaderNodeMath"); rx.operation = 'SUBTRACT'; rx.inputs[1].default_value = 0.5; nt.links.new(sp.outputs["X"], rx.inputs[0])
        rx2 = nt.nodes.new("ShaderNodeMath"); rx2.operation = 'ABSOLUTE'; nt.links.new(rx.outputs[0], rx2.inputs[0])
        rlt = nt.nodes.new("ShaderNodeMath"); rlt.operation = 'LESS_THAN'; rlt.inputs[1].default_value = 0.012; nt.links.new(rx2.outputs[0], rlt.inputs[0])
        mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; nt.links.new(rl.outputs[0], mx.inputs["Factor"])
        mx.inputs["A"].default_value = (0.0, 0.02, 0.10, 1); mx.inputs["B"].default_value = (0.1, 1.0, 0.25, 1)
        mx2 = nt.nodes.new("ShaderNodeMix"); mx2.data_type = 'RGBA'; nt.links.new(rlt.outputs[0], mx2.inputs["Factor"])
        nt.links.new(mx.outputs["Result"], mx2.inputs["A"]); mx2.inputs["B"].default_value = (1.0, 0.1, 0.9, 1)
        nt.links.new(mx2.outputs["Result"], em.inputs["Color"])
    else:
        # engine display: two rows of coloured arc dials and bars
        sp = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Generated"], sp.inputs[0])
        wv = nt.nodes.new("ShaderNodeTexWave"); wv.wave_type = 'RINGS'; wv.inputs["Scale"].default_value = 6
        nt.links.new(tc.outputs["Generated"], wv.inputs["Vector"])
        cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.interpolation = 'CONSTANT'
        cr.color_ramp.elements[0].color = (0.0, 0.02, 0.08, 1); cr.color_ramp.elements[1].position = 0.85
        cr.color_ramp.elements[1].color = (0.1, 0.9, 1.0, 1)
        nt.links.new(wv.outputs["Fac"], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], em.inputs["Color"])
    nt.links.new(em.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    o.data.materials.append(m); to_col(o, C_COCK)
    to_col(box(name + "_bezel", (size[0] + 0.03, 0.02, size[1] + 0.03), (loc[0], loc[1] + 0.012, loc[2]), M_SCREEN_BEZEL, bevel=0.004), C_COCK)
    return o
SY = PANEL_Y - 0.004
for sx, tag in ((-1, "L"), (1, "R")):
    screen("DISP_PFD_" + tag, (sx * 0.78, SY, 0.88), (0.19, 0.19), "pfd")
    screen("DISP_ND_" + tag, (sx * 0.53, SY, 0.88), (0.19, 0.19), "nd")
screen("DISP_EICAS", (0.0, SY, 0.93), (0.20, 0.24), "eng")
# round gauges with needles (no numbers): altimeter (hero side, large), speed, vertical speed
GAUGES = {}
def gauge(name, loc, r, face_col=(0.01, 0.01, 0.015)):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=0.01, location=loc, rotation=(math.radians(90), 0, 0), vertices=48)
    f = bpy.context.active_object; f.name = name + "_face"; f.data.materials.append(mat("M_GaugeFace", face_col, rough=0.3)); to_col(f, C_COCK)
    bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=r * 0.08, location=(loc[0], loc[1] - 0.006, loc[2]), rotation=(math.radians(90), 0, 0))
    t = bpy.context.active_object; t.name = name + "_rim"; t.data.materials.append(M_CHROME); to_col(t, C_COCK)
    # tick marks (white) and a coloured arc
    for k in range(12):
        ang = 2 * math.pi * k / 12
        tk = box(name + "_tick", (0.004, 0.003, r * 0.18), (loc[0] + math.sin(ang) * r * 0.82, loc[1] - 0.007, loc[2] + math.cos(ang) * r * 0.82),
                 M_WHITE, bevel=0.0, rot=(0, -ang, 0))
        to_col(tk, C_COCK)
    piv = bpy.data.objects.new(name + "_needle", None); piv.location = (loc[0], loc[1] - 0.012, loc[2]); C_COCK.objects.link(piv)
    nd = box(name + "_needleMesh", (0.008, 0.004, r * 0.85), (0, 0, r * 0.38), M_YELLOW, bevel=0.0)
    nd.parent = piv; nd.location = (0, 0, r * 0.38); to_col(nd, C_COCK)
    piv.rotation_mode = 'XYZ'
    GAUGES[name] = piv
    return piv
gauge("ALT", (-0.26, PANEL_Y - 0.004, 0.75), 0.055)
gauge("SPD", (-0.26, PANEL_Y - 0.004, 0.99), 0.045)
gauge("VSI", (0.26, PANEL_Y - 0.004, 0.75), 0.045)
gauge("ALT2", (0.26, PANEL_Y - 0.004, 0.99), 0.045)
# master warning lamps on the glareshield (one in front of each pilot) and the panel caution lamps
WARN = []
for sx in (1, -1):
    w = box("WARN_" + ("R" if sx > 0 else "L"), (0.07, 0.03, 0.035), (sx * 0.38, PANEL_Y - 0.24, 1.21), emit_mat("M_WarnOff", (0.25, 0.0, 0.0), 0.5), bevel=0.005)
    to_col(w, C_COCK); WARN.append(w)
M_WARN = emit_mat("M_Warn", (1.0, 0.02, 0.0), 0.0)            # strength keyed in 02_animate (the flashes)
for w in WARN: w.data.materials[0] = M_WARN
# red warning beacon strips on the cockpit ceiling and the rear bulkhead (flash with the alarms, read behind his face)
to_col(box("WARN_beacon", (0.9, 0.06, 0.03), (0, 3.05, 2.06), M_WARN, bevel=0.01), C_COCK)
to_col(box("WARN_beaconB", (0.06, 0.03, 0.5), (-0.95, 2.09, 1.55), M_WARN, bevel=0.01), C_COCK)
to_col(box("WARN_beaconC", (0.06, 0.03, 0.5), (0.95, 2.09, 1.55), M_WARN, bevel=0.01), C_COCK)
# button rows on the glareshield (autopilot panel) and on the panel: small coloured caps
for i in range(14):
    x = -0.30 + i * 0.046
    to_col(box("CK_APbtn", (0.03, 0.02, 0.018), (x, PANEL_Y - 0.22, 1.255), [M_WHITE, M_YELLOW, M_PANEL2][i % 3], bevel=0.003), C_COCK)
for sx in (1, -1):
    for i in range(6):
        to_col(box("CK_PanelKnob", (0.025, 0.02, 0.025), (sx * (0.95 + 0.0), PANEL_Y - 0.01, 0.62 + i * 0.075), [M_RED, M_YELLOW, M_WHITE][i % 3], bevel=0.004), C_COCK)
# overhead panel (sloped, rows of coloured switches) and side consoles
to_col(box("CK_Overhead", (1.0, 1.1, 0.06), (0, 4.15, 2.02), M_PANEL, bevel=0.01), C_COCK)
for i in range(8):
    for j in range(5):
        to_col(box("CK_OHbtn", (0.035, 0.035, 0.02), (-0.4 + i * 0.115, 3.75 + j * 0.18, 1.985), [M_WHITE, M_YELLOW, M_RED, M_PANEL2, M_WHITE][(i + j) % 5], bevel=0.004), C_COCK)
for sx in (1, -1):
    to_col(box("CK_SideConsole" + ("R" if sx > 0 else "L"), (0.30, 1.10, 0.72), (sx * 1.20, 4.15, 0.36), M_PANEL2, bevel=0.02), C_COCK)
# pedestal between the seats: throttles, flap lever, radio panel with blinking lights
PED_Y = (4.30, 4.95)
to_col(box("CK_Pedestal", (0.26, PED_Y[1] - PED_Y[0], 0.70), (0, (PED_Y[0] + PED_Y[1]) / 2, 0.35), M_PANEL, bevel=0.015), C_COCK)
to_col(box("CK_PedestalFace", (0.22, 0.20, 0.02), (0, 4.42, 0.705), M_PANEL2, bevel=0.004), C_COCK)
THR = []
for k, x in enumerate((-0.05, 0.05)):
    piv = bpy.data.objects.new("THR_piv%d" % k, None); piv.location = (x, 4.56, 0.70); C_COCK.objects.link(piv)
    arm = box("THR_arm%d" % k, (0.018, 0.018, 0.16), (0, 0, 0.08), M_CHROME, bevel=0.003); arm.parent = piv; arm.location = (0, 0, 0.08)
    to_col(arm, C_COCK)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.022, depth=0.09, location=(0, 0, 0.17), rotation=(0, math.radians(90), 0), vertices=20)
    kn = bpy.context.active_object; kn.name = "THR_knob%d" % k; kn.data.materials.append(M_BLACK); kn.parent = piv; kn.location = (0, 0, 0.17)
    to_col(kn, C_COCK)
    piv.rotation_euler = (math.radians(-12), 0, 0)
    THR.append(piv)
to_col(box("CK_FlapLever", (0.02, 0.02, 0.10), (0.12, 4.75, 0.75), M_WHITE, bevel=0.003), C_COCK)
RADIO_LEDS = []
for i in range(6):
    led = box("RADIO_LED%d" % i, (0.016, 0.016, 0.006), (-0.08 + i * 0.032, 4.40, 0.712), emit_mat("M_RadioLED%d" % i, (0.1, 1.0, 0.3) if i % 2 else (1.0, 0.55, 0.0), 4.0), bevel=0.002)
    to_col(led, C_COCK); RADIO_LEDS.append(led)
# the hand microphone and its hook on the LEFT side console (captain's outer side, away from the FO)
MIC_HOOK = Vector((-1.00, 4.10, 1.00))
to_col(box("CK_MicHook", (0.03, 0.06, 0.05), (MIC_HOOK.x - 0.03, MIC_HOOK.y, MIC_HOOK.z + 0.03), M_CHROME, bevel=0.005), C_COCK)
to_col(box("CK_MicPost", (0.04, 0.05, 0.30), (MIC_HOOK.x - 0.06, MIC_HOOK.y, 0.86), M_PANEL2, bevel=0.005), C_COCK)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
MIC = bpy.context.active_object; MIC.name = "MIC"; MIC.scale = (0.035, 0.028, 0.095)
bpy.ops.object.transform_apply(scale=True)
bv = MIC.modifiers.new("bev", 'BEVEL'); bv.width = 0.011; bv.segments = 4
MIC.data.materials.append(M_BLACK); to_col(MIC, C_COCK)
bpy.ops.object.shade_smooth()
grill = box("MIC_grill", (0.028, 0.004, 0.035), (0, -0.0145, 0.025), mat("M_Grill", (0.25, 0.25, 0.27), rough=0.4, metal=0.6), bevel=0.002)
grill.parent = MIC; grill.location = (0, -0.0145, 0.025); to_col(grill, C_COCK)
ptt = box("MIC_ptt", (0.008, 0.018, 0.03), (-0.019, 0, 0.0), M_RED, bevel=0.002); ptt.parent = MIC; ptt.location = (-0.019, 0.0, 0.0); to_col(ptt, C_COCK)
MIC.rotation_mode = 'XYZ'; MIC.location = MIC_HOOK + Vector((0.005, 0.0, -0.01)); MIC.rotation_euler = (0, 0, 0)

# ---- pilot seats (Sketchfab "Plane Seat" by icenvain, CC BY 4.0): dark sheepskin-blue leather
ps = import_glb(PSEAT_GLB)
bpy.ops.object.select_all(action='DESELECT')
for o in ps: o.select_set(True)
bpy.context.view_layer.objects.active = ps[0]
if len(ps) > 1: bpy.ops.object.join()
PS = bpy.context.active_object; PS.name = "PSEAT_proto"
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
pts = [v.co for v in PS.data.vertices]
mn = Vector([min(p[i] for p in pts) for i in range(3)]); mx = Vector([max(p[i] for p in pts) for i in range(3)])
print("PSEAT raw", mn, mx)
s_ = 1.15 / (mx.z - mn.z)
PS.data.transform(Matrix.Translation(-Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))))
PS.data.transform(Matrix.Diagonal((0.62 / (mx.x - mn.x), s_, s_, 1)))
PS.data.transform(Matrix.Rotation(math.radians(180), 4, 'Z'))   # the model faces -Y; ours face the nose (+Y)
M_PSEAT = noise_mat("M_PilotSeat", (0.12, 0.03, 0.02), (0.18, 0.05, 0.03), scale=300, rough=0.55, coat=0.15, bump=0.15)   # oxblood leather
PS.data.materials.clear(); PS.data.materials.append(M_PSEAT)
for p in PS.data.polygons: p.use_smooth = True
PSEATS = {}
for tag, sx in (("L", -0.56), ("R", 0.56)):
    o = PS.copy(); o.data = PS.data; o.name = "PSEAT_" + tag; C_COCK.objects.link(o)
    o.location = (sx, 4.0, 0.17); o.rotation_euler = (0, 0, 0)
    PSEATS[tag] = o
bpy.data.objects.remove(PS, do_unlink=True)
# captain seat: drop the loose parts on its inner (+x) side above the cushion = the inner armrest
cs = PSEATS["L"]; cs.data = cs.data.copy()
bm = bmesh.new(); bm.from_mesh(cs.data); bm.verts.ensure_lookup_table()
seen = set(); kill = []
for v in bm.verts:
    if v in seen: continue
    st = [v]; comp = []; seen.add(v)
    while st:
        x_ = st.pop(); comp.append(x_)
        for e in x_.link_edges:
            y_ = e.other_vert(x_)
            if y_ not in seen: seen.add(y_); st.append(y_)
    cxm = sum(q.co.x for q in comp) / len(comp); czm = sum(q.co.z for q in comp) / len(comp)
    if cxm > 0.17 and 0.30 < czm < 0.50: kill += comp
print("PSEAT inner armrest verts removed", len(kill))
bmesh.ops.delete(bm, geom=kill, context='VERTS'); bm.to_mesh(cs.data); bm.free()
# a base (rails) under each seat
for tag, sx in (("L", -0.56), ("R", 0.56)):
    to_col(box("PSEAT_riser" + tag, (0.36, 0.46, 0.18), (sx, 4.0, 0.09), M_PANEL, bevel=0.01), C_COCK)
    to_col(box("PSEAT_rail" + tag, (0.44, 0.80, 0.03), (sx, 4.0, 0.015), M_CHROME, bevel=0.005), C_COCK)

# ---- yokes: column pivots at the floor; the wheel (ram's horn) on top, pitch = column rotation, roll = wheel rotation
YOKES = {}
for tag, sx in (("L", -0.56), ("R", 0.56)):
    piv = bpy.data.objects.new("YOKE_piv" + tag, None); piv.location = (sx, 4.62, 0.06); C_COCK.objects.link(piv); piv.rotation_mode = 'XYZ'
    colm = cyl("YOKE_col" + tag, 0.028, 0.72, (0, 0, 0.36), M_YOKE); colm.parent = piv; colm.location = (0, 0, 0.36); to_col(colm, C_COCK)
    arm = cyl("YOKE_arm" + tag, 0.022, 0.20, (0, -0.10, 0.74), M_YOKE, rot=(math.radians(90), 0, 0)); arm.parent = piv; arm.location = (0, -0.10, 0.74)
    to_col(arm, C_COCK)
    wheel = bpy.data.objects.new("YOKE_wheel" + tag, None); wheel.parent = piv; wheel.location = (0, -0.21, 0.74); C_COCK.objects.link(wheel)
    wheel.rotation_mode = 'XYZ'
    # the horns: a bent bar each side, built from a curve with a bevel (grip sections thicker)
    for hs in (1, -1):
        cu = bpy.data.curves.new("YOKE_horn", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.017; cu.bevel_resolution = 4
        sp = cu.splines.new('BEZIER'); sp.bezier_points.add(2)
        P = [(0.0, 0.0, 0.0), (hs * 0.12, -0.01, 0.0), (hs * 0.16, -0.015, 0.09)]
        for bp_, p_ in zip(sp.bezier_points, P):
            bp_.co = p_; bp_.handle_left_type = bp_.handle_right_type = 'AUTO'
        ho = bpy.data.objects.new("YOKE_horn" + tag + ("R" if hs > 0 else "L"), cu); ho.parent = wheel; C_COCK.objects.link(ho)
        cu.materials.append(M_YOKE)
        g = cyl("YOKE_grip" + tag + ("R" if hs > 0 else "L"), 0.021, 0.10, (hs * 0.16, -0.015, 0.075), M_YOKE_GRIP)
        g.parent = wheel; g.location = (hs * 0.16, -0.015, 0.075); to_col(g, C_COCK)
    hub = box("YOKE_hub" + tag, (0.10, 0.05, 0.07), (0, 0, 0.0), M_YOKE, bevel=0.012); hub.parent = wheel; hub.location = (0, 0.0, 0.0); to_col(hub, C_COCK)
    YOKES[tag] = (piv, wheel)
# rudder pedals (feet rest on them)
for tag, sx in (("L", -0.56), ("R", 0.56)):
    for hs in (1, -1):
        to_col(box("PEDAL_" + tag, (0.08, 0.03, 0.18), (sx + hs * 0.13, 4.84, 0.12), M_CHROME, bevel=0.006, rot=(math.radians(-25), 0, 0)), C_COCK)

# ================================================================== the wing and engine outside the cabin windows (static, part of the plane)
def wing(sx):
    """swept, tapered wing with thickness; root chord 5.5 m at x=1.9, tip chord 1.5 m at x=17; low wing (z -0.5)"""
    bm = bmesh.new()
    sec = []
    for i, t in enumerate([0.0, 0.25, 0.5, 0.75, 1.0]):
        x = sx * (1.85 + t * 15.0); chord = 5.6 - 4.1 * t; yle = 1.0 - t * 7.5; z = -0.55 + t * 1.0
        th = 0.55 - 0.42 * t
        ring = []
        for u, dz in ((0.0, 0.0), (0.08, 0.5), (0.3, 0.6), (0.6, 0.4), (1.0, 0.0), (0.6, -0.2), (0.3, -0.25), (0.08, -0.2)):
            ring.append(bm.verts.new((x, yle - u * chord, z + dz * th)))
        sec.append(ring)
    for i in range(len(sec) - 1):
        for j in range(8):
            a_, b_ = sec[i][j], sec[i][(j + 1) % 8]; c_, d_ = sec[i + 1][(j + 1) % 8], sec[i + 1][j]
            bm.faces.new((a_, b_, c_, d_) if sx > 0 else (d_, c_, b_, a_))
    bm.faces.new(sec[-1] if sx < 0 else list(reversed(sec[-1])))
    me = bpy.data.meshes.new("WING"); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("WING_" + ("R" if sx > 0 else "L"), me); C_CABIN.objects.link(o)
    sd = o.modifiers.new("sd", 'SUBSURF'); sd.levels = 2; sd.render_levels = 2
    for p in me.polygons: p.use_smooth = True
    return o
M_WING = mat("M_Wing", (0.85, 0.87, 0.92), rough=0.3, coat=0.3)
M_LIVERY = mat("M_Livery", (0.02, 0.15, 0.75), rough=0.3, coat=0.5)       # deep blue
M_LIVERY2 = mat("M_Livery2", (1.0, 0.30, 0.0), rough=0.3, coat=0.5)       # orange
for sx in (1, -1):
    w = wing(sx); w.data.materials.append(M_WING)
    # winglet (orange) and an engine nacelle (blue with an orange lip)
    bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=3.6, location=(sx * 5.8, 1.6, -1.4), rotation=(math.radians(90), 0, 0), vertices=40)
    nac = bpy.context.active_object; nac.name = "ENGINE_" + ("R" if sx > 0 else "L"); nac.data.materials.append(M_LIVERY)
    bpy.ops.object.shade_smooth(); to_col(nac, C_CABIN)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.95, minor_radius=0.10, location=(sx * 5.8, 3.4, -1.4), rotation=(math.radians(90), 0, 0))
    lip = bpy.context.active_object; lip.name = "ENGINE_lip"; lip.data.materials.append(M_CHROME); to_col(lip, C_CABIN)
    to_col(box("PYLON_" + ("R" if sx > 0 else "L"), (0.25, 3.0, 0.8), (sx * 5.8, 0.6, -0.65), M_WING, bevel=0.05), C_CABIN)
# the fuselage OUTSIDE skin (seen only at the window edges): white with the blue belly stripe
for sx in (1, -1):
    sk = box("FUSE_skin" + ("R" if sx > 0 else "L"), (0.05, 40.0, 3.0), (sx * 1.92, -2.0, 0.6), M_WING, bevel=0.0)
    to_col(sk, C_CABIN)
    st = box("FUSE_stripe" + ("R" if sx > 0 else "L"), (0.06, 40.0, 0.18), (sx * 1.93, -2.0, 0.70), M_LIVERY, bevel=0.0); to_col(st, C_CABIN)
# make the outside skin have holes at the windows: cut with boolean-free trick -> skin sits below the windows only
for o in [o for o in bpy.data.objects if o.name.startswith("FUSE_skin")]:
    o.scale = (1, 1, 1); o.dimensions = (0.05, 40.0, 0.80); o.location.z = 0.45

# ================================================================== the WORLD: sky, ground, town, field, clouds
W_ROT = bpy.data.objects.new("WORLD_ROT", None); C_WORLD.objects.link(W_ROT); W_ROT.location = (0, 4.0, 1.4); W_ROT.rotation_mode = 'XYZ'
W_POS = bpy.data.objects.new("WORLD_POS", None); C_WORLD.objects.link(W_POS); W_POS.parent = W_ROT; W_POS.location = (0, 0, -1300.0)
# sky: deep saturated blue zenith -> bright cyan horizon, a warm sun glow
wd = bpy.data.worlds.new("SKY"); sc.world = wd; wd.use_nodes = True; nt = wd.node_tree
for n in list(nt.nodes):
    if n.type != 'OUTPUT_WORLD': nt.nodes.remove(n)
tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ")
vr = nt.nodes.new("ShaderNodeVectorRotate"); vr.name = "SKY_ATT"; vr.rotation_type = 'EULER_XYZ'; vr.invert = True
nt.links.new(tc.outputs["Generated"], vr.inputs["Vector"])
nt.links.new(vr.outputs[0], sep.inputs[0])
cr = nt.nodes.new("ShaderNodeValToRGB")
cr.color_ramp.elements[0].position = 0.0; cr.color_ramp.elements[0].color = (0.25, 0.62, 1.0, 1)
cr.color_ramp.elements[1].position = 0.45; cr.color_ramp.elements[1].color = (0.0, 0.07, 0.60, 1)
e2 = cr.color_ramp.elements.new(0.10); e2.color = (0.03, 0.35, 1.0, 1)
mp = nt.nodes.new("ShaderNodeMapRange"); mp.inputs["From Min"].default_value = -0.05; mp.inputs["From Max"].default_value = 1.0
nt.links.new(sep.outputs["Z"], mp.inputs["Value"]); nt.links.new(mp.outputs["Result"], cr.inputs["Fac"])
bg = nt.nodes.new("ShaderNodeBackground"); bg.inputs["Strength"].default_value = 1.4
nt.links.new(cr.outputs["Color"], bg.inputs["Color"]); nt.links.new(bg.outputs[0], nt.nodes["World Output"].inputs["Surface"])
# a dimmer world for lighting so interiors don't go milky: light path is_camera_ray -> full sky, else 0.6
lp = nt.nodes.new("ShaderNodeLightPath"); mixs = nt.nodes.new("ShaderNodeMath"); mixs.operation = 'MULTIPLY_ADD'
mixs.inputs[1].default_value = 0.8; mixs.inputs[2].default_value = 0.6
nt.links.new(lp.outputs["Is Camera Ray"], mixs.inputs[0]); nt.links.new(mixs.outputs[0], bg.inputs["Strength"])
SUN = bpy.data.lights.new("SUN", 'SUN'); SUN.energy = 4.0; SUN.color = (1.0, 0.93, 0.80); SUN.angle = math.radians(1.5)
so = bpy.data.objects.new("SUN", SUN); C_WORLD.objects.link(so); so.parent = W_ROT
so.rotation_euler = (math.radians(55), 0, math.radians(200))
# ground: a 600 km plane, patchwork farmland (Voronoi fields in greens/golds), roads, distance haze to the horizon colour
bpy.ops.mesh.primitive_plane_add(size=600000, location=(0, 0, 0))
GR = bpy.context.active_object; GR.name = "GROUND"; GR.parent = W_POS; to_col(GR, C_WORLD)
m = bpy.data.materials.new("M_Ground"); m.use_nodes = True; nt = m.node_tree; p = nt.nodes["Principled BSDF"]
p.inputs["Roughness"].default_value = 0.9
tcg = nt.nodes.new("ShaderNodeTexCoord")
vor = nt.nodes.new("ShaderNodeTexVoronoi"); vor.inputs["Scale"].default_value = 0.004; vor.voronoi_dimensions = '2D'
nt.links.new(tcg.outputs["Object"], vor.inputs["Vector"])
crf = nt.nodes.new("ShaderNodeValToRGB"); crf.color_ramp.interpolation = 'CONSTANT'
pal = [(0.05, 0.40, 0.04), (0.35, 0.55, 0.02), (0.75, 0.55, 0.05), (0.10, 0.30, 0.03), (0.55, 0.30, 0.06), (0.02, 0.50, 0.10), (0.85, 0.75, 0.15), (0.20, 0.45, 0.02)]
crf.color_ramp.elements[0].color = (*pal[0], 1)
for i, c_ in enumerate(pal[1:]):
    e = crf.color_ramp.elements.new((i + 1) / len(pal)); e.color = (*c_, 1)
nt.links.new(vor.outputs["Color"], crf.inputs["Fac"]) if False else None
sepc = nt.nodes.new("ShaderNodeSeparateColor"); nt.links.new(vor.outputs["Color"], sepc.inputs[0]); nt.links.new(sepc.outputs[0], crf.inputs["Fac"])
# field edges (hedges/roads): the voronoi F1 distance-to-edge
ve = nt.nodes.new("ShaderNodeTexVoronoi"); ve.feature = 'DISTANCE_TO_EDGE'; ve.inputs["Scale"].default_value = 0.004; ve.voronoi_dimensions = '2D'
nt.links.new(tcg.outputs["Object"], ve.inputs["Vector"])
edge = nt.nodes.new("ShaderNodeMath"); edge.operation = 'LESS_THAN'; edge.inputs[1].default_value = 0.012
nt.links.new(ve.outputs["Distance"], edge.inputs[0])
mxe = nt.nodes.new("ShaderNodeMix"); mxe.data_type = 'RGBA'; nt.links.new(edge.outputs[0], mxe.inputs["Factor"])
nt.links.new(crf.outputs["Color"], mxe.inputs["A"]); mxe.inputs["B"].default_value = (0.02, 0.12, 0.02, 1)
# crop rows: fine stripes modulate the brightness
wvr = nt.nodes.new("ShaderNodeTexWave"); wvr.inputs["Scale"].default_value = 0.6; nt.links.new(tcg.outputs["Object"], wvr.inputs["Vector"])
wvr.inputs["Distortion"].default_value = 0.0
br = nt.nodes.new("ShaderNodeMapRange"); br.inputs["To Min"].default_value = 0.85; br.inputs["To Max"].default_value = 1.1
nt.links.new(wvr.outputs["Fac"], br.inputs["Value"])
mxr = nt.nodes.new("ShaderNodeMix"); mxr.data_type = 'RGBA'; mxr.blend_type = 'MULTIPLY'; mxr.inputs["Factor"].default_value = 1.0
nt.links.new(mxe.outputs["Result"], mxr.inputs["A"]); nt.links.new(br.outputs["Result"], mxr.inputs["B"])
# haze with distance from the camera
cd = nt.nodes.new("ShaderNodeCameraData")
hz = nt.nodes.new("ShaderNodeMapRange"); hz.inputs["From Min"].default_value = 4000.0; hz.inputs["From Max"].default_value = 90000.0
nt.links.new(cd.outputs["View Distance"], hz.inputs["Value"])
hz2 = nt.nodes.new("ShaderNodeMath"); hz2.operation = 'POWER'; hz2.inputs[1].default_value = 0.7; nt.links.new(hz.outputs["Result"], hz2.inputs[0])
mxh = nt.nodes.new("ShaderNodeMix"); mxh.data_type = 'RGBA'; nt.links.new(hz2.outputs[0], mxh.inputs["Factor"])
nt.links.new(mxr.outputs["Result"], mxh.inputs["A"]); mxh.inputs["B"].default_value = (0.25, 0.62, 1.0, 1)
nt.links.new(mxh.outputs["Result"], p.inputs["Base Color"])
emh = nt.nodes.new("ShaderNodeMath"); emh.operation = 'MULTIPLY'; emh.inputs[1].default_value = 0.9
nt.links.new(hz2.outputs[0], emh.inputs[0])
nt.links.new(mxh.outputs["Result"], p.inputs["Emission Color"]); nt.links.new(emh.outputs[0], p.inputs["Emission Strength"])
GR.data.materials.append(m)
# the landing FIELD: a long bright mown-grass strip (2.6 km x 140 m) and a TOWN of colourful roofs before it
FIELD_Y = 9000.0
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, FIELD_Y, 0.4))
FL = bpy.context.active_object; FL.name = "FIELD"; FL.scale = (240, 3200, 1); FL.parent = W_POS; to_col(FL, C_WORLD)
mf = bpy.data.materials.new("M_Field"); mf.use_nodes = True; ntf = mf.node_tree; pf = ntf.nodes["Principled BSDF"]
tcf = ntf.nodes.new("ShaderNodeTexCoord"); wvf = ntf.nodes.new("ShaderNodeTexWave"); wvf.bands_direction = 'Y'
wvf.inputs["Scale"].default_value = 0.012; wvf.inputs["Distortion"].default_value = 0.0; ntf.links.new(tcf.outputs["Object"], wvf.inputs["Vector"])
crm = ntf.nodes.new("ShaderNodeValToRGB"); crm.color_ramp.elements[0].color = (0.20, 0.85, 0.02, 1); crm.color_ramp.elements[1].color = (0.45, 1.0, 0.10, 1)
ntf.links.new(wvf.outputs["Fac"], crm.inputs["Fac"]); ntf.links.new(crm.outputs["Color"], pf.inputs["Base Color"])
pf.inputs["Roughness"].default_value = 0.8
pf.inputs["Emission Color"].default_value = (0.3, 0.9, 0.1, 1); pf.inputs["Emission Strength"].default_value = 0.25
FL.data.materials.append(mf)
M_ROOFS = [mat("M_Roof%d" % i, c_, rough=0.6) for i, c_ in enumerate(((0.75, 0.12, 0.04), (0.9, 0.45, 0.05), (0.05, 0.25, 0.65), (0.85, 0.85, 0.8), (0.6, 0.05, 0.10)))]
rng = random.Random(4)
town = []
for i in range(220):
    x = rng.uniform(-900, 900) + (450 if rng.random() < 0.5 else -450); y = FIELD_Y - 2200 - rng.uniform(0, 1600)
    if abs(x) < 120: x += 300
    sx_, sy_ = rng.uniform(10, 24), rng.uniform(10, 24); h = rng.uniform(6, 14)
    o = box("TOWN_%03d" % i, (sx_, sy_, h), (x, y, h / 2), M_ROOFS[i % len(M_ROOFS)], bevel=0.0, rot=(0, 0, rng.uniform(0, 0.3)))
    o.parent = W_POS; to_col(o, C_WORLD); town.append(o)
bpy.ops.object.select_all(action='DESELECT')
for o in town: o.select_set(True)
bpy.context.view_layer.objects.active = town[0]; bpy.ops.object.join(); town[0].name = "TOWN"
# a winding river (deep blue) through the farmland
cu = bpy.data.curves.new("RIVER", 'CURVE'); cu.dimensions = '2D'; cu.extrude = 0.0
sp = cu.splines.new('BEZIER'); sp.bezier_points.add(7)
for k, bp_ in enumerate(sp.bezier_points):
    bp_.co = (rng.uniform(-2500, 2500), -4000 + k * 3000, 0.3); bp_.handle_left_type = bp_.handle_right_type = 'AUTO'
cu.bevel_depth = 0.0; cu.extrude = 0.0; cu.offset = 0.0
rv = bpy.data.objects.new("RIVER", cu); C_WORLD.objects.link(rv); rv.parent = W_POS
cu.fill_mode = 'NONE'; cu.extrude = 0.0; cu.bevel_depth = 35.0; cu.bevel_resolution = 0
cu.materials.append(mat("M_River", (0.0, 0.12, 0.45), rough=0.15, coat=0.6))
# clouds: puffy cumulus clusters (white, slightly glowing, soft blue shadows), around the flight path
M_CLOUD = mat("M_Cloud", (0.95, 0.97, 1.0), rough=1.0, sss=0.0, emit=((0.75, 0.85, 1.0), 0.35))
rng = random.Random(7)
cl = []
for i in range(70):
    cx = rng.uniform(-7000, 7000); cy = rng.uniform(-8000, 16000); cz = rng.uniform(850, 1150)
    if abs(cx) < 1600: cx += 1700 * (1 if cx >= 0 else -1)
    base = rng.uniform(150, 420)
    for k in range(rng.randint(4, 7)):
        r_ = base * rng.uniform(0.5, 1.0)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=r_, location=(cx + rng.uniform(-1.2, 1.2) * base, cy + rng.uniform(-1.2, 1.2) * base, cz + rng.uniform(0, 0.6) * base))
        o = bpy.context.active_object; o.scale.z = 0.7; cl.append(o)
bpy.ops.object.select_all(action='DESELECT')
for o in cl: o.select_set(True)
bpy.context.view_layer.objects.active = cl[0]; bpy.ops.object.join()
CLOUDS = bpy.context.active_object; CLOUDS.name = "CLOUDS"; CLOUDS.parent = W_POS; to_col(CLOUDS, C_WORLD)
tx = bpy.data.textures.new("cloudnoise", 'CLOUDS'); tx.noise_scale = 120.0
dm = CLOUDS.modifiers.new("puff", 'DISPLACE'); dm.texture = tx; dm.strength = 60.0
CLOUDS.data.materials.append(M_CLOUD); bpy.ops.object.shade_smooth()

# ================================================================== interior lights
def area(name, loc, rot, size, energy, colr, c, shape='RECTANGLE', size_y=None):
    L = bpy.data.lights.new(name, 'AREA'); L.energy = energy; L.color = colr; L.shape = shape; L.size = size
    if size_y: L.size_y = size_y
    o = bpy.data.objects.new(name, L); c.objects.link(o); o.location = loc; o.rotation_euler = rot
    o.visible_camera = False; o.visible_glossy = False
    return o
area("L_CabinCeil", (0, -1.6, 2.05), (0, 0, 0), 0.6, 220, (1.0, 0.96, 0.92), C_CABIN, size_y=7.0)
area("L_CabinWinR", (1.55, -1.6, 1.2), (0, math.radians(-90), 0), 0.5, 120, (0.85, 0.92, 1.0), C_CABIN, size_y=7.0)
area("L_CabinWinL", (-1.55, -1.6, 1.2), (0, math.radians(90), 0), 0.5, 120, (0.85, 0.92, 1.0), C_CABIN, size_y=7.0)
area("L_CabinMood", (0, -1.6, 1.6), (0, 0, 0), 2.6, 80, (0.75, 0.35, 1.0), C_CABIN, size_y=7.0)
area("L_Galley", (0, 1.4, 2.0), (0, 0, 0), 1.2, 120, (1.0, 0.92, 0.85), C_CABIN, size_y=0.8)
area("L_CockCeil", (0, 3.6, 1.95), (0, 0, 0), 1.0, 90, (1.0, 0.95, 0.9), C_COCK, size_y=1.2)
area("L_CockFront", (0, 4.75, 1.55), (math.radians(-110), 0, 0), 1.6, 110, (0.92, 0.96, 1.0), C_COCK, size_y=0.3)
area("L_PanelGlow", (0, 4.85, 1.0), (math.radians(-90), 0, 0), 1.6, 25, (0.4, 0.7, 1.0), C_COCK, size_y=0.3)
ALARM = area("L_Alarm", (0, 4.80, 1.05), (math.radians(-95), 0, 0), 1.4, 0.0, (1.0, 0.03, 0.0), C_COCK, size_y=0.25)
CATCH = bpy.data.lights.new("L_Catch", 'POINT'); CATCH.energy = 2.0; CATCH.shadow_soft_size = 0.02
cto = bpy.data.objects.new("L_Catch", CATCH); C_COCK.objects.link(cto); cto.visible_camera = False

# ================================================================== camera (keyed in 02_animate)
cam = bpy.data.cameras.new("CAM_Film"); cam.lens = 32; cam.clip_start = 0.02; cam.clip_end = 400000.0
cam.dof.use_dof = False; cam.sensor_width = 36.0
CAM = bpy.data.objects.new("CAM_Film", cam); sc.collection.objects.link(CAM); sc.camera = CAM
CT = bpy.data.objects.new("CAM_Target", None); sc.collection.objects.link(CT)
tt = CAM.constraints.new('TRACK_TO'); tt.target = CT; tt.track_axis = 'TRACK_NEGATIVE_Z'; tt.up_axis = 'UP_Y'
cto.parent = CAM; cto.location = (0.0, 0.12, 0.0)

# ================================================================== render settings (fast + rich)
sc.render.engine = 'CYCLES'
cy = sc.cycles
cy.samples = 64; cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.04
cy.use_denoising = True; cy.denoiser = 'OPENIMAGEDENOISE'
cy.max_bounces = 6; cy.diffuse_bounces = 3; cy.glossy_bounces = 3; cy.transmission_bounces = 6; cy.transparent_max_bounces = 16
cy.caustics_reflective = False; cy.caustics_refractive = False
sc.render.use_persistent_data = True
sc.render.use_simplify = True; sc.render.simplify_subdivision_render = 2
try: cy.texture_limit_render = '2048'
except Exception: pass
sc.render.use_motion_blur = False
sc.view_settings.view_transform = 'AgX'
try: sc.view_settings.look = 'AgX - Punchy'
except Exception: sc.view_settings.look = 'Punchy'
sc.view_settings.exposure = -0.45
sc.render.image_settings.file_format = 'PNG'
sc.render.filepath = "//render/NoPilotPlane_v012_####.png"
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("BUILD_DONE", OUT)
