"""BellyFat v018 stage A (from scratch): one woman, one bullet, two sets.
blender -b --python 01_build.py -- <polyhaven_dir> <out.blend>

HOME (origin): a bright living room. The woman stands ON the floor at the origin facing -Y, looking out of a French
window in the wall in front of her (inner face y=-0.95). Outside (y<-1.10): a sunny terrace, plants, the house facade.
The left door leaf (x<0) is closed (its glass takes the bullet); the right leaf is open inward (the camera's way in).
MACRO (x=+20): a real-scale cross-section of her belly wall (shirt, skin, fat with fascia sheets, muscle, peritoneum,
bowel loops). The cut face is the plane y=0 (seen from -Y); tissue lies at y>0; the shirt top is z=0; the bullet
travels straight down the cut plane (x=0). One geometry-nodes modifier carves the wound track and squeezes the fat
around the bullet nose, driven by the keyed empty `TipCtl` (nothing reads the scene clock)."""
import bpy, bmesh, sys, math, random, os
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "lib_build.py")).read())
a = sys.argv[sys.argv.index("--") + 1:]
PH, OUT = a[0], a[1]
PKG = os.path.dirname(HERE)
random.seed(10)
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
sc = bpy.context.scene
sc.render.fps = 60
sc.frame_start, sc.frame_end = 1, 1273
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
MX = Vector((20.0, 0.0, 0.0))      # the macro set origin
def col(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in sc.collection.children: sc.collection.children.link(c)
    return c
C_HOME, C_MACRO = col("HOME"), col("MACRO")
def to_col(o, c):
    for cc in list(o.users_collection): cc.objects.unlink(o)
    c.objects.link(o)

# ================================================================== the woman (ONE model for the whole film)
W, WB = human("Woman", 0.0, 0.5, {"asian": 0.05, "caucasian": 0.60, "african": 0.35}, "ponytail01/ponytail01.mhclo",
              "young_caucasian_female/young_caucasian_female.mhmat", "eyebrow010/eyebrow010.mhclo",
              height=0.45, weight=1.0, muscle=0.4,
              clothes=["female_casualsuit01/female_casualsuit01.mhclo", "shoes01/shoes01.mhclo"])
eye_fix(W); eye_group_fix()
EG = bpy.data.node_groups.get("EnhancedEye")
for n in (EG.nodes if EG else []):          # cornea a touch clearer so the brown iris and dark pupil read (no milky "dead" eyes)
    if n.type == 'MATH' and abs(n.inputs[1].default_value - 0.92) < 1e-4: n.inputs[1].default_value = 0.96
for m in [m for c in W.children if c.type == 'MESH' and "high-poly" in c.name for m in c.data.materials]:
    for n in m.node_tree.nodes:                 # deeper brown irises
        if n.type == 'GROUP' and "IrisMajorColor" in n.inputs:
            n.inputs["IrisMajorColor"].default_value = (0.13, 0.06, 0.02, 1); n.inputs["IrisMinorColor"].default_value = (0.05, 0.025, 0.01, 1)
for c in W.children:
    if c.type == 'MESH' and any(k in c.name.lower() for k in ("pony", "eyebrow")):
        for m in c.data.materials: tint(m, (0.30, 0.17, 0.10))
for m in WB.data.materials: tint(m, (0.98, 0.74, 0.58))
for c in W.children:
    if c.type == 'MESH' and "teeth" in c.name:
        for m in c.data.materials: tint(m, (1.5, 1.45, 1.4))
SUIT = [c for c in W.children if c.type == 'MESH' and "casualsuit" in c.name][0]
SUIT.name = "Woman.clothes"
tee = bpy.data.images.load(os.path.join(PKG, "assets/tex/woman_tee_diffuse.png")); tee.name = "woman_tee_diffuse"
for m in SUIT.data.materials:
    for nd in m.node_tree.nodes:
        if nd.type == 'TEX_IMAGE' and nd.image and "diffuse" in nd.image.name.lower():
            nd.image = tee
        if nd.type == 'NORMAL_MAP': nd.inputs["Strength"].default_value = 0.4
# solid garments: real thickness, no open paper edges (brief: bodies SOLID, no hollow clothes)
for c in W.children:
    if c.type == 'MESH' and ("clothes" in c.name or "shoes" in c.name):
        so = c.modifiers.new("solid", 'SOLIDIFY'); so.thickness = 0.003; so.offset = 1.0; so.use_rim = True
        i = c.modifiers.find("solid")
        while i > c.modifiers.find("Armature") + 1:
            c.modifiers.move(i, i - 1); i -= 1
for c in W.children:
    to_col(c, C_HOME)
to_col(W, C_HOME)

# ================================================================== materials
def plaster(name, c1, c2, scale=40.0, rough=0.85):
    m = mat(name, c1, rough=rough)
    nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = scale
    nz.inputs["Detail"].default_value = 6.0
    cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (*c1, 1); cr.color_ramp.elements[1].color = (*c2, 1)
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"]); nt.links.new(nz.outputs["Fac"], cr.inputs["Fac"])
    nt.links.new(cr.outputs["Color"], p.inputs["Base Color"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.12; bp.inputs["Distance"].default_value = 0.002
    nt.links.new(nz.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], p.inputs["Normal"])
    return m

def tiles(name, c1, c2, mortar, scale=4.0):
    m = mat(name, c1, rough=0.45, coat=0.2)
    nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); br = nt.nodes.new("ShaderNodeTexBrick")
    br.inputs["Scale"].default_value = scale; br.offset = 0.0
    br.inputs["Color1"].default_value = (*c1, 1); br.inputs["Color2"].default_value = (*c2, 1); br.inputs["Mortar"].default_value = (*mortar, 1)
    br.inputs["Mortar Size"].default_value = 0.012; br.inputs["Brick Width"].default_value = 0.5; br.inputs["Row Height"].default_value = 0.5
    nt.links.new(tc.outputs["Object"], br.inputs["Vector"]); nt.links.new(br.outputs["Color"], p.inputs["Base Color"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.3; bp.inputs["Distance"].default_value = 0.003
    nt.links.new(br.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], p.inputs["Normal"])
    return m

def wood(name, c1, c2, scale=3.0, rough=0.4):
    m = mat(name, c1, rough=rough, coat=0.25)
    nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1, 10, 1)
    wv = nt.nodes.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = scale; wv.inputs["Distortion"].default_value = 6.0
    wv.inputs["Detail"].default_value = 3.0
    cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (*c1, 1); cr.color_ramp.elements[1].color = (*c2, 1)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"]); nt.links.new(mp.outputs["Vector"], wv.inputs["Vector"])
    nt.links.new(wv.outputs["Fac"], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], p.inputs["Base Color"])
    return m

def thin_glass(name, tint=(0.85, 0.95, 1.0), refl=0.06):
    """thin window glass: mostly Transparent (the room reads through it) + a faint fresnel sheen; no refraction blur"""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n)
    tr = nt.nodes.new("ShaderNodeBsdfTransparent"); tr.inputs["Color"].default_value = (*tint, 1)
    gl = nt.nodes.new("ShaderNodeBsdfGlossy"); gl.inputs["Roughness"].default_value = 0.02
    fr = nt.nodes.new("ShaderNodeFresnel"); fr.inputs["IOR"].default_value = 1.5
    mm = nt.nodes.new("ShaderNodeMath"); mm.operation = 'MULTIPLY'; mm.inputs[1].default_value = refl / 0.04
    nt.links.new(fr.outputs[0], mm.inputs[0])
    mx = nt.nodes.new("ShaderNodeMixShader"); nt.links.new(mm.outputs[0], mx.inputs["Fac"])
    nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(gl.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    return m

M_WALL_IN = plaster("M_WallIn", (0.010, 0.30, 0.33), (0.016, 0.38, 0.40), scale=8.0)          # deep saturated teal room
M_FACADE = plaster("M_Facade", (0.85, 0.30, 0.06), (0.95, 0.40, 0.10), scale=6.0)            # warm terracotta-orange plaster
M_TRIM = mat("M_Trim", (0.92, 0.92, 0.90), rough=0.35, coat=0.3)                               # white window frame
M_SHUTTER = mat("M_Shutter", (0.02, 0.18, 0.55), rough=0.45, coat=0.2)                         # royal-blue shutters
M_FLOOR = wood("M_Floor", (0.30, 0.10, 0.03), (0.45, 0.18, 0.06), scale=2.0)
M_TERR = tiles("M_Terrace", (0.62, 0.20, 0.07), (0.70, 0.25, 0.09), (0.85, 0.80, 0.72), scale=3.0)
M_CEIL = mat("M_Ceiling", (0.90, 0.88, 0.84), rough=0.9)
M_GLASS = thin_glass("M_Glass")
M_RUG = fabric("M_Rug", (0.75, 0.42, 0.02), scale=500, bump=0.35)                               # saturated mustard rug
M_BRASS = mat("M_Brass", (0.95, 0.62, 0.20), rough=0.25, metal=1.0)

# ================================================================== HOME set: room shell
WY_IN, WY_OUT = -0.95, -1.10
OPEN_X = (-0.75, 0.75); OPEN_Z = (0.02, 2.18)
def wall_with_hole(name, y0, y1, xr, zr, hole_x, hole_z, material):
    """a wall slab from y0..y1 with a rectangular hole (door/window opening)"""
    pieces = []
    for nm, x0, x1, z0, z1 in (("L", xr[0], hole_x[0], zr[0], zr[1]), ("R", hole_x[1], xr[1], zr[0], zr[1]),
                               ("T", hole_x[0], hole_x[1], hole_z[1], zr[1]), ("B", hole_x[0], hole_x[1], zr[0], hole_z[0])):
        if x1 - x0 < 1e-4 or z1 - z0 < 1e-4: continue
        o = box(name + nm, (x1 - x0, y1 - y0, z1 - z0), ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), material, bevel=0.0)
        pieces.append(o)
    bpy.ops.object.select_all(action='DESELECT')
    for p in pieces: p.select_set(True)
    bpy.context.view_layer.objects.active = pieces[0]; bpy.ops.object.join()
    o = bpy.context.active_object; o.name = name
    return o
WALL_F = wall_with_hole("HM_FrontWall", WY_OUT, WY_IN, (-4.0, 4.0), (0.0, 3.6), OPEN_X, OPEN_Z, M_WALL_IN)
# the outside face of the same wall is plaster: a thin skin 1 mm outside
FAC = wall_with_hole("HM_Facade", WY_OUT - 0.001, WY_OUT, (-6.0, 6.0), (-0.1, 5.5), OPEN_X, OPEN_Z, M_FACADE)
FLOOR = box("HM_Floor", (8.0, 6.0, 0.05), (0, 1.9, -0.025), M_FLOOR, bevel=0.0)
CEIL = box("HM_Ceiling", (8.0, 6.0, 0.05), (0, 1.9, 2.75), M_CEIL, bevel=0.0)
BACK = box("HM_BackWall", (8.0, 0.1, 2.8), (0, 3.2, 1.4), M_WALL_IN, bevel=0.0)
SIDEL = box("HM_SideL", (0.1, 4.4, 2.8), (3.0, 1.0, 1.4), M_WALL_IN, bevel=0.0)
SIDER = box("HM_SideR", (0.1, 4.4, 2.8), (-3.0, 1.0, 1.4), M_WALL_IN, bevel=0.0)
RUG = box("HM_Rug", (2.2, 1.6, 0.008), (0.0, 0.55, 0.004), M_RUG, bevel=0.003)
TERR = box("HM_Terrace", (12.0, 6.0, 0.05), (0, -4.1, -0.03), M_TERR, bevel=0.0)
# skirting boards, a white ceiling cornice
for nm, size, loc in (("HM_SkirtB", (6.0, 0.02, 0.10), (0, 3.14, 0.05)), ("HM_SkirtFL", (2.2, 0.02, 0.10), (1.9, WY_IN + 0.01, 0.05)),
                      ("HM_SkirtFR", (2.2, 0.02, 0.10), (-1.9, WY_IN + 0.01, 0.05))):
    box(nm, size, loc, M_TRIM, bevel=0.003)

# ---- the French window: frame, two leaves with 3x2 panes each; left leaf closed, right leaf open inward
def leaf(name, w, h, rails=(2, 3)):
    """a door leaf at the origin: x 0..w (hinge side at x=0), z 0..h, thickness 0.05; returns (frame obj, glass obj, pane list)"""
    st = 0.07; parts = []
    for nm, sz, lc in (("_stL", (st, 0.05, h), (st / 2, 0, h / 2)), ("_stR", (st, 0.05, h), (w - st / 2, 0, h / 2)),
                       ("_top", (w - 0.004, 0.046, st), (w / 2, 0, h - st / 2)), ("_bot", (w - 0.004, 0.046, 0.22), (w / 2, 0, 0.11))):
        parts.append(box(name + nm, sz, lc, M_TRIM, bevel=0.0))
    cols, rows = rails; gw = (w - 2 * st); gh = (h - st - 0.22)
    for i in range(1, cols):
        x = st + gw * i / cols; parts.append(box(name + "_mv%d" % i, (0.03, 0.038, gh - 0.004), (x, 0, 0.22 + gh / 2), M_TRIM, bevel=0.0))
    for j in range(1, rows):
        z = 0.22 + gh * j / rows; parts.append(box(name + "_mh%d" % j, (gw, 0.04, 0.03), (w / 2, 0, z), M_TRIM, bevel=0.0))
    bpy.ops.object.select_all(action='DESELECT')
    for p in parts: p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]; bpy.ops.object.join()
    fr = bpy.context.active_object; fr.name = name + "_Frame"
    bpy.ops.mesh.primitive_plane_add(size=1, location=(w / 2, 0, 0.22 + gh / 2), rotation=(math.radians(90), 0, 0))
    gl = bpy.context.active_object; gl.name = name + "_Glass"; gl.scale = (gw, gh, 1); bpy.ops.object.transform_apply(scale=True)
    gl.data.materials.append(M_GLASS)
    gl.parent = fr
    return fr, gl
LW = (OPEN_X[1] - OPEN_X[0]) / 2; LH = OPEN_Z[1] - OPEN_Z[0]
LEAF_A, GLASS_A = leaf("HM_LeafA", LW, LH)         # closed, x from -0.75 to 0 (hinge at -0.75)
LEAF_A.location = (OPEN_X[0], WY_OUT + 0.075, OPEN_Z[0])
LEAF_B, GLASS_B = leaf("HM_LeafB", LW, LH)         # open inward, hinge at +0.75
LEAF_B.rotation_euler = (0, 0, math.radians(180)); LEAF_B.location = (OPEN_X[1], WY_OUT + 0.075, OPEN_Z[0])
LEAF_B.rotation_euler.z = math.radians(180 - 100)   # swung ~100 deg into the room, flat against the wall side
# outer casing around the opening (white architrave on the facade) and a sill
for nm, sz, lc in (("HM_CaseL", (0.10, 0.03, LH + 0.12), (OPEN_X[0] - 0.05, WY_OUT - 0.015, OPEN_Z[0] + LH / 2 + 0.04)),
                   ("HM_CaseR", (0.10, 0.03, LH + 0.12), (OPEN_X[1] + 0.05, WY_OUT - 0.015, OPEN_Z[0] + LH / 2 + 0.04)),
                   ("HM_CaseT", (1.70, 0.04, 0.12), (0, WY_OUT - 0.02, OPEN_Z[1] + 0.06)),
                   ("HM_Sill", (1.70, 0.20, 0.04), (0, WY_OUT - 0.05, 0.0))):
    box(nm, sz, lc, M_TRIM, bevel=0.008)
# louvred shutters, open against the facade either side
def shutter(name, x0, flip):
    parts = [box(name + "_f", (0.62, 0.03, LH), (x0 + 0.31 * flip, WY_OUT - 0.03, OPEN_Z[0] + LH / 2), M_SHUTTER, bevel=0.006)]
    for k in range(22):
        z = OPEN_Z[0] + 0.15 + k * (LH - 0.3) / 21
        parts.append(box(name + "_l%d" % k, (0.52, 0.012, 0.06), (x0 + 0.31 * flip, WY_OUT - 0.048, z), M_SHUTTER, bevel=0.003,
                         rot=(math.radians(35), 0, 0)))
    bpy.ops.object.select_all(action='DESELECT')
    for p in parts: p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]; bpy.ops.object.join(); bpy.context.active_object.name = name
shutter("HM_ShutterL", OPEN_X[0] - 0.12, -1); shutter("HM_ShutterR", OPEN_X[1] + 0.12, 1)

# ---- the crack in the closed leaf's glass: radial + ring cracks, revealed by a keyed radius (the bullet hole at its centre)
GLASS_HIT = Vector((-0.26, WY_OUT + 0.075, 1.22))      # where the bullet passes the glass (set again in 02 from the path)
def crack_mat():
    m = bpy.data.materials.new("M_Crack"); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n)
    tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sep.inputs[0])
    # polar coords in the plane (object x, y)
    at = nt.nodes.new("ShaderNodeMath"); at.operation = 'ARCTAN2'; nt.links.new(sep.outputs["Y"], at.inputs[0]); nt.links.new(sep.outputs["X"], at.inputs[1])
    ln = nt.nodes.new("ShaderNodeVectorMath"); ln.operation = 'LENGTH'; nt.links.new(tc.outputs["Object"], ln.inputs[0])
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 30.0; nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    # radial lines: |sin(angle*9 + noise*2)| small
    m1 = nt.nodes.new("ShaderNodeMath"); m1.operation = 'MULTIPLY'; m1.inputs[1].default_value = 9.0; nt.links.new(at.outputs[0], m1.inputs[0])
    m2 = nt.nodes.new("ShaderNodeMath"); m2.operation = 'MULTIPLY_ADD'; m2.inputs[1].default_value = 2.2; nt.links.new(nz.outputs["Fac"], m2.inputs[0]); nt.links.new(m1.outputs[0], m2.inputs[2])
    sn = nt.nodes.new("ShaderNodeMath"); sn.operation = 'SINE'; nt.links.new(m2.outputs[0], sn.inputs[0])
    ab = nt.nodes.new("ShaderNodeMath"); ab.operation = 'ABSOLUTE'; nt.links.new(sn.outputs[0], ab.inputs[0])
    rad = nt.nodes.new("ShaderNodeMath"); rad.operation = 'LESS_THAN'; rad.inputs[1].default_value = 0.06; nt.links.new(ab.outputs[0], rad.inputs[0])
    # ring cracks: fract(r*28 + noise) near 0
    r1 = nt.nodes.new("ShaderNodeMath"); r1.operation = 'MULTIPLY_ADD'; r1.inputs[1].default_value = 28.0; nt.links.new(ln.outputs["Value"], r1.inputs[0])
    nt.links.new(nz.outputs["Fac"], r1.inputs[2])
    fr = nt.nodes.new("ShaderNodeMath"); fr.operation = 'FRACT'; nt.links.new(r1.outputs[0], fr.inputs[0])
    rg = nt.nodes.new("ShaderNodeMath"); rg.operation = 'LESS_THAN'; rg.inputs[1].default_value = 0.05; nt.links.new(fr.outputs[0], rg.inputs[0])
    rgm = nt.nodes.new("ShaderNodeMath"); rgm.operation = 'MULTIPLY'; nt.links.new(rg.outputs[0], rgm.inputs[0])
    mk = nt.nodes.new("ShaderNodeMath"); mk.operation = 'LESS_THAN'; mk.inputs[1].default_value = 0.07; nt.links.new(ln.outputs["Value"], mk.inputs[0])
    nt.links.new(mk.outputs[0], rgm.inputs[1])
    mxm = nt.nodes.new("ShaderNodeMath"); mxm.operation = 'MAXIMUM'; nt.links.new(rad.outputs[0], mxm.inputs[0]); nt.links.new(rgm.outputs[0], mxm.inputs[1])
    # fade with radius; the reveal radius is the object's scale (keyed), so the crack spreads out from the hole
    fd = nt.nodes.new("ShaderNodeMapRange"); fd.inputs["From Min"].default_value = 0.12; fd.inputs["From Max"].default_value = 0.30
    fd.inputs["To Min"].default_value = 1.0; fd.inputs["To Max"].default_value = 0.0; nt.links.new(ln.outputs["Value"], fd.inputs["Value"])
    a1 = nt.nodes.new("ShaderNodeMath"); a1.operation = 'MULTIPLY'; nt.links.new(mxm.outputs[0], a1.inputs[0]); nt.links.new(fd.outputs[0], a1.inputs[1])
    hole = nt.nodes.new("ShaderNodeMath"); hole.operation = 'LESS_THAN'; hole.inputs[1].default_value = 0.012; nt.links.new(ln.outputs["Value"], hole.inputs[0])
    halo = nt.nodes.new("ShaderNodeMath"); halo.operation = 'LESS_THAN'; halo.inputs[1].default_value = 0.03; nt.links.new(ln.outputs["Value"], halo.inputs[0])
    a2 = nt.nodes.new("ShaderNodeMath"); a2.operation = 'MAXIMUM'; nt.links.new(a1.outputs[0], a2.inputs[0]); nt.links.new(halo.outputs[0], a2.inputs[1])
    wh = nt.nodes.new("ShaderNodeBsdfPrincipled"); wh.inputs["Base Color"].default_value = (0.95, 0.97, 1.0, 1); wh.inputs["Roughness"].default_value = 0.25
    wh.inputs["Emission Color"].default_value = (1, 1, 1, 1); wh.inputs["Emission Strength"].default_value = 0.4
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mx = nt.nodes.new("ShaderNodeMixShader"); nt.links.new(a2.outputs[0], mx.inputs["Fac"]); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(wh.outputs[0], mx.inputs[2])
    # the hole itself: transparent
    mx2 = nt.nodes.new("ShaderNodeMixShader"); nt.links.new(hole.outputs[0], mx2.inputs["Fac"]); nt.links.new(mx.outputs[0], mx2.inputs[1])
    tr2 = nt.nodes.new("ShaderNodeBsdfTransparent"); nt.links.new(tr2.outputs[0], mx2.inputs[2])
    nt.links.new(mx2.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    return m
bpy.ops.mesh.primitive_circle_add(vertices=64, radius=0.30, fill_type='NGON', location=(0, 0, 0), rotation=(math.radians(90), 0, 0))
CRACK = bpy.context.active_object; CRACK.name = "HM_GlassCrack"; CRACK.data.materials.append(crack_mat())
bpy.ops.object.transform_apply(rotation=True)
CRACK.location = GLASS_HIT + Vector((0, -0.002, 0)); CRACK.scale = (0.001, 0.001, 0.001)

# ---- Poly Haven furniture and plants (CC0)
def append_ph(asset, name, loc, rot_z=0.0, scale=1.0, collection=C_HOME):
    d = os.path.join(PH, asset); blend = [f for f in os.listdir(d) if f.endswith(".blend")][0]
    with bpy.data.libraries.load(os.path.join(d, blend), link=False) as (src, dst):
        dst.objects = list(src.objects)
    objs = [o for o in dst.objects if o is not None and o.type == 'MESH']
    root = bpy.data.objects.new(name, None); collection.objects.link(root)
    for o in objs:
        collection.objects.link(o)
        if o.parent is None or o.parent not in objs: o.parent = root
    root.location = loc; root.rotation_euler.z = rot_z; root.scale = (scale,) * 3
    for o in objs:
        for m in o.data.materials:
            if not m or not m.use_nodes: continue
            for n in m.node_tree.nodes:
                if n.type == 'BSDF_PRINCIPLED' and not n.inputs["Roughness"].is_linked:
                    n.inputs["Roughness"].default_value = max(0.35, n.inputs["Roughness"].default_value)
                if n.type == 'NORMAL_MAP': n.inputs["Strength"].default_value = 0.4
    return root, objs
SOFA, SOFA_P = append_ph("sofa_02", "HM_Sofa", (0.25, 2.55, 0.0), rot_z=0.0)
CAB, CAB_P = append_ph("painted_wooden_cabinet", "HM_Cabinet", (-1.75, 2.95, 0.0), rot_z=0.0)
PL1, _ = append_ph("potted_plant_01", "HM_PlantIn1", (1.65, 2.75, 0.0), scale=1.25)
PL2, _ = append_ph("potted_plant_02", "HM_PlantOut1", (-1.35, -1.75, 0.0), scale=1.1)
PL3, _ = append_ph("potted_plant_01", "HM_PlantOut2", (1.35, -1.70, 0.0), scale=1.0)
SH1, _ = append_ph("shrub_01", "HM_Shrub1", (-2.6, -2.6, 0.0), scale=1.1)
SH2, _ = append_ph("shrub_01", "HM_Shrub2", (2.7, -2.4, 0.0), rot_z=1.7, scale=1.0)
# sofa recolour: deep purple velvet (saturated, separates from the teal wall and the magenta top)
def tint_any(objs, mult):
    done = set()
    for o in objs:
        for m in o.data.materials:
            if not m or not m.use_nodes or m.name in done: continue
            done.add(m.name)
            for nd in list(m.node_tree.nodes):
                if nd.type == 'TEX_IMAGE' and nd.image and "diff" in nd.image.name.lower():
                    for lk in list(nd.outputs['Color'].links):
                        mx = m.node_tree.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
                        mx.inputs['Factor'].default_value = 1.0; mx.inputs['B'].default_value = (*mult, 1)
                        m.node_tree.links.new(nd.outputs['Color'], mx.inputs['A']); m.node_tree.links.new(mx.outputs['Result'], lk.to_socket)
tint_any(SOFA_P, (0.75, 0.25, 1.6))      # deep purple sofa
tint_any(CAB_P, (1.15, 0.72, 0.12))      # mustard-yellow cabinet
# wall art: three abstract colour-block canvases (no text) above the sofa
def canvas(name, loc, size, c1, c2):
    o = box(name, (size[0], 0.03, size[1]), loc, mat(name + "_frame", (0.05, 0.05, 0.06), rough=0.4), bevel=0.004)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(loc[0], loc[1] - 0.017, loc[2]), rotation=(math.radians(90), 0, 0))
    p = bpy.context.active_object; p.name = name + "_art"; p.scale = (size[0] - 0.05, size[1] - 0.05, 1)
    m = mat(name + "_artm", c1, rough=0.6); nt = m.node_tree; pr = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); gr = nt.nodes.new("ShaderNodeTexGradient"); gr.gradient_type = 'SPHERICAL'
    cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.interpolation = 'CONSTANT'
    cr.color_ramp.elements[0].color = (*c1, 1); cr.color_ramp.elements[1].position = 0.35; cr.color_ramp.elements[1].color = (*c2, 1)
    nt.links.new(tc.outputs["Object"], gr.inputs["Vector"]); nt.links.new(gr.outputs["Fac"], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], pr.inputs["Base Color"])
    p.data.materials.append(m)
    return o
canvas("HM_ArtA", (-0.35, 3.13, 1.65), (0.55, 0.75), (0.95, 0.70, 0.03), (0.85, 0.10, 0.05))
canvas("HM_ArtB", (0.40, 3.13, 1.70), (0.70, 0.55), (0.02, 0.35, 0.80), (0.98, 0.45, 0.05))
canvas("HM_ArtC", (1.10, 3.13, 1.62), (0.40, 0.55), (0.65, 0.05, 0.35), (0.98, 0.85, 0.25))
# a ceiling pendant (brass) and a floor lamp glow are faked with emissive shades
bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=0.24, radius2=0.06, depth=0.22, location=(0.0, 1.2, 2.35))
PEND = bpy.context.active_object; PEND.name = "HM_Pendant"; PEND.data.materials.append(M_BRASS)
sd = PEND.modifiers.new("so", 'SOLIDIFY'); sd.thickness = 0.004; bpy.ops.object.shade_smooth()
cyl("HM_PendantCord", 0.004, 0.40, (0.0, 1.2, 2.55), M_TRIM)

# ---- exterior: a sky dome is the world; a garden hedge strip and a low wall at the terrace edge read as "outside"
M_HEDGE = mat("M_Hedge", (0.05, 0.35, 0.05), rough=0.7)
M_WALLLOW = plaster("M_LowWall", (0.92, 0.88, 0.78), (0.98, 0.95, 0.86), scale=10.0)
box("HM_TerrWall", (10.0, 0.25, 0.75), (0, -6.8, 0.375), M_WALLLOW, bevel=0.02)

HOME_OBJS = [o for o in sc.collection.objects if o.type in ('MESH', 'EMPTY')]
for o in HOME_OBJS:
    to_col(o, C_HOME)
for o in list(bpy.data.objects):
    if o.parent and o.parent.name.startswith("HM_") and o.users_collection and o.users_collection[0] == sc.collection:
        to_col(o, C_HOME)

# ---- HOME lights: the sun through the window, warm interior area lights
def light(name, kind, energy, loc, rot=(0, 0, 0), size=1.0, color=(1, 1, 1), c=C_HOME):
    L = bpy.data.lights.new(name, kind); L.energy = energy; L.color = color
    if kind == 'AREA': L.size = size; L.shape = 'DISK'
    if kind == 'SUN': L.angle = math.radians(3)
    o = bpy.data.objects.new(name, L); c.objects.link(o); o.location = loc; o.rotation_euler = rot
    return o
light("HM_Sun", 'SUN', 4.5, (0, -5, 6), rot=(math.radians(52), 0, math.radians(-28)), color=(1.0, 0.93, 0.80))
light("HM_RoomKey", 'AREA', 170, (0.6, -0.55, 2.4), rot=(math.radians(28), 0, math.radians(-15)), size=1.4, color=(1.0, 0.92, 0.84))
light("HM_RoomFill", 'AREA', 90, (-1.6, 0.8, 2.3), rot=(math.radians(35), math.radians(-35), 0), size=1.6, color=(0.95, 0.90, 1.0))
light("HM_BackRim", 'AREA', 120, (0.9, 1.6, 2.2), rot=(math.radians(-40), 0, math.radians(160)), size=0.8, color=(1.0, 0.80, 0.60))
light("HM_ExtFill", 'AREA', 400, (0, -4.5, 2.5), rot=(math.radians(80), 0, 0), size=4.0, color=(0.80, 0.90, 1.0))

# ================================================================== the bullet (ONE object for the whole film)
def bullet():
    """9 mm round-nose slug, real size (9.0 mm x 15.5 mm), copper jacket; origin at the BASE centre, nose along +Z."""
    prof = []
    R = 0.0045; Lc = 0.0075; Ln = 0.0080
    prof.append((0.0, 0.0)); prof.append((R * 0.92, 0.0)); prof.append((R, 0.0006))
    for i in range(1, 6): prof.append((R, Lc * i / 5))
    for i in range(1, 17):
        t = i / 16; ang = t * math.pi / 2
        prof.append((R * math.cos(ang) ** 0.9, Lc + Ln * math.sin(ang) ** 1.05))
    bm = bmesh.new(); vs = [bm.verts.new((r, 0, z)) for r, z in prof]
    for a_, b_ in zip(vs, vs[1:]): bm.edges.new((a_, b_))
    bmesh.ops.spin(bm, geom=bm.verts[:] + bm.edges[:], angle=math.radians(360), steps=48, axis=(0, 0, 1), cent=(0, 0, 0), use_duplicate=False)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    me = bpy.data.meshes.new("Bullet"); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("Bullet", me); sc.collection.objects.link(o)
    for p in me.polygons: p.use_smooth = True
    m = mat("M_Bullet", (0.90, 0.33, 0.12), rough=0.24, metal=1.0, coat=0.3)
    nt = m.node_tree; p = nt.nodes["Principled BSDF"]          # fine lathe rings on the jacket
    tc = nt.nodes.new("ShaderNodeTexCoord"); wv = nt.nodes.new("ShaderNodeTexWave"); wv.wave_type = 'RINGS'
    wv.inputs["Scale"].default_value = 900.0; wv.inputs["Distortion"].default_value = 0.5
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.08; bp.inputs["Distance"].default_value = 0.0001
    nt.links.new(tc.outputs["Object"], wv.inputs["Vector"]); nt.links.new(wv.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], p.inputs["Normal"])
    me.materials.append(m)
    wn = o.modifiers.new("ws", 'WEIGHTED_NORMAL')
    return o
BUL = bullet()
TIP = bpy.data.objects.new("TipCtl", None); sc.collection.objects.link(TIP); TIP.parent = BUL; TIP.location = (0, 0, 0.0155)
TIP.empty_display_size = 0.003
# a thin air trail behind the bullet (attached to it; its length is keyed in 02 with the speed)
bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=0.0040, radius2=0.0002, depth=1.0, location=(0, 0, -0.5), rotation=(math.radians(180), 0, 0))
TRAIL = bpy.context.active_object; TRAIL.name = "BulletTrail"
bpy.ops.object.transform_apply(location=True, rotation=True)
TRAIL.parent = BUL
tm = bpy.data.materials.new("M_Trail"); tm.use_nodes = True; nt = tm.node_tree
for n in list(nt.nodes):
    if n.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n)
tcn = nt.nodes.new("ShaderNodeTexCoord"); sp = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tcn.outputs["Generated"], sp.inputs[0])
mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.0; mr.inputs["From Max"].default_value = 1.0
mr.inputs["To Min"].default_value = 0.0; mr.inputs["To Max"].default_value = 0.55; nt.links.new(sp.outputs["Z"], mr.inputs["Value"])
tr = nt.nodes.new("ShaderNodeBsdfTransparent"); em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (1.0, 0.95, 0.85, 1); em.inputs["Strength"].default_value = 1.2
mx = nt.nodes.new("ShaderNodeMixShader"); nt.links.new(mr.outputs[0], mx.inputs["Fac"]); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2])
nt.links.new(mx.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
TRAIL.data.materials.append(tm)
TRAIL.visible_shadow = False; TRAIL.visible_diffuse = False; TRAIL.visible_glossy = False

# ================================================================== MACRO set: the belly wall in cross-section (real scale)
# layer depths below the shirt top (m): shirt 1.2 mm, skin 3 mm, fat 44 mm (3 fascia sheets), muscle 14 mm, peritoneum
Z_SHIRT, Z_SKIN, Z_FAT, Z_MUS, Z_PER = -0.0012, -0.0042, -0.0480, -0.0620, -0.0636
FASCIA = (-0.0160, -0.0275, -0.0385)
XW, ZB = 0.10, -0.066                   # cut face half width, bottom of the wall (below it: the abdominal cavity)
def grid(name, x0, x1, z0, z1, dx):
    nx = int(round((x1 - x0) / dx)); nz = int(round((z1 - z0) / dx))
    bm = bmesh.new()
    vs = [[bm.verts.new((x0 + (x1 - x0) * i / nx, 0.0, z0 + (z1 - z0) * j / nz)) for i in range(nx + 1)] for j in range(nz + 1)]
    for j in range(nz):
        for i in range(nx):
            bm.faces.new((vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); C_MACRO.objects.link(o)
    for p in me.polygons: p.use_smooth = True
    return o
CUT = grid("MC_CutFace", -XW, XW, ZB, 0.0, 0.0005)
CUT.location = MX
# the shirt's top surface (seen from above at the start) and the cut block's back/sides (never on camera, but keep it solid)
def top_grid():
    o = grid("MC_TopFabric", -XW, XW, 0.0, 0.09, 0.0006)
    o.data.transform(Matrix.Rotation(math.radians(90), 4, 'X'))     # (x, 0, z) -> (x, -z?, ...) : rotate so it lies in z=0 with y from 0 to 0.09
    for v in o.data.vertices: v.co.y = abs(v.co.y)
    o.location = MX
    return o
TOP = top_grid()
# underlying slab (keeps it SOLID from oblique angles: back, sides, bottom)
SLAB = box("MC_Slab", (2 * XW, 0.078, -ZB), (MX.x, 0.051, ZB / 2), mat("M_SlabSide", (0.85, 0.55, 0.12), rough=0.6), bevel=0.0)
to_col(SLAB, C_MACRO)

# ---- tissue shader: bands by ORIGINAL position (attribute 'opos' stored before the GN deformation), so layers move with the tissue
def tissue_mat():
    m = bpy.data.materials.new("M_Tissue"); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n)
    out = nt.nodes["Material Output"]
    at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_name = "opos"
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(at.outputs["Vector"], sep.inputs[0])
    trk = nt.nodes.new("ShaderNodeAttribute"); trk.attribute_name = "track"       # 0..1: inside the wound track surface
    sq = nt.nodes.new("ShaderNodeAttribute"); sq.attribute_name = "squeeze"       # 0..1: compressed tissue ahead of the nose
    Z = sep.outputs["Z"]
    def band(lo, hi):
        """1 where lo <= z < hi (z negative downward)"""
        g1 = nt.nodes.new("ShaderNodeMath"); g1.operation = 'GREATER_THAN'; g1.inputs[1].default_value = lo; nt.links.new(Z, g1.inputs[0])
        g2 = nt.nodes.new("ShaderNodeMath"); g2.operation = 'LESS_THAN'; g2.inputs[1].default_value = hi; nt.links.new(Z, g2.inputs[0])
        mm = nt.nodes.new("ShaderNodeMath"); mm.operation = 'MULTIPLY'; nt.links.new(g1.outputs[0], mm.inputs[0]); nt.links.new(g2.outputs[0], mm.inputs[1])
        return mm.outputs[0]
    def mix(fac, a_, b_):
        mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; nt.links.new(fac, mx.inputs["Factor"])
        for sock, v in ((mx.inputs['A'], a_), (mx.inputs['B'], b_)):
            if isinstance(v, tuple): sock.default_value = (*v, 1)
            else: nt.links.new(v, sock)
        return mx.outputs["Result"]
    def mixf(fac, a_, b_):
        mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'FLOAT'; nt.links.new(fac, mx.inputs["Factor"])
        for sock, v in ((mx.inputs[2], a_), (mx.inputs[3], b_)):
            if isinstance(v, float): sock.default_value = v
            else: nt.links.new(v, sock)
        return mx.outputs[0]
    # fat: voronoi lobules (yellow, per-cell brightness) with thin orange-pink septa
    vo = nt.nodes.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 330.0; vo.inputs["Randomness"].default_value = 0.85
    nt.links.new(at.outputs["Vector"], vo.inputs["Vector"])
    ve = nt.nodes.new("ShaderNodeTexVoronoi"); ve.feature = 'DISTANCE_TO_EDGE'; ve.inputs["Scale"].default_value = 330.0; ve.inputs["Randomness"].default_value = 0.85
    nt.links.new(at.outputs["Vector"], ve.inputs["Vector"])
    sept = nt.nodes.new("ShaderNodeMapRange"); sept.inputs["From Min"].default_value = 0.015; sept.inputs["From Max"].default_value = 0.045
    sept.inputs["To Min"].default_value = 1.0; sept.inputs["To Max"].default_value = 0.0; nt.links.new(ve.outputs["Distance"], sept.inputs["Value"])
    cellc = nt.nodes.new("ShaderNodeValToRGB"); cellc.color_ramp.elements[0].color = (1.0, 0.55, 0.02, 1); cellc.color_ramp.elements[1].color = (1.0, 0.80, 0.08, 1)
    nt.links.new(vo.outputs["Color"], cellc.inputs["Fac"])
    rim_ = nt.nodes.new("ShaderNodeMapRange"); rim_.inputs["From Min"].default_value = 0.03; rim_.inputs["From Max"].default_value = 0.22
    rim_.inputs["To Min"].default_value = 0.75; rim_.inputs["To Max"].default_value = 0.0; nt.links.new(ve.outputs["Distance"], rim_.inputs["Value"])
    cell_dark = mix(rim_.outputs["Result"], cellc.outputs["Color"], (0.85, 0.30, 0.02))     # lobule edges shade to deep orange (rounded read)
    fat_c = mix(sept.outputs["Result"], cell_dark, (0.80, 0.12, 0.10))
    # fascia sheets inside the fat: pearly white-pink thin lines
    fas = band(FASCIA[0] - 0.00045, FASCIA[0] + 0.00045)
    for fz in FASCIA[1:]:
        mm_ = nt.nodes.new("ShaderNodeMath"); mm_.operation = 'MAXIMUM'
        nt.links.new(fas, mm_.inputs[0]); nt.links.new(band(fz - 0.00045, fz + 0.00045), mm_.inputs[1]); fas = mm_.outputs[0]
    fat_c = mix(fas, fat_c, (0.98, 0.88, 0.86))
    # muscle: red with horizontal fibres
    wv = nt.nodes.new("ShaderNodeTexWave"); wv.bands_direction = 'Z'; wv.inputs["Scale"].default_value = 900.0
    wv.inputs["Distortion"].default_value = 1.5; wv.inputs["Detail"].default_value = 2.0
    nt.links.new(at.outputs["Vector"], wv.inputs["Vector"])
    mus_r = nt.nodes.new("ShaderNodeValToRGB"); mus_r.color_ramp.elements[0].color = (0.45, 0.02, 0.05, 1); mus_r.color_ramp.elements[1].color = (0.80, 0.10, 0.12, 1)
    nt.links.new(wv.outputs["Fac"], mus_r.inputs["Fac"])
    # skin: epidermis (warm tan line) over dermis (peach-pink)
    skin_c = mix(band(Z_SHIRT - 0.0005, Z_SHIRT + 0.0001), (0.95, 0.45, 0.30), (0.62, 0.22, 0.12))
    # shirt: magenta knit
    shirt_w = nt.nodes.new("ShaderNodeTexWave"); shirt_w.inputs["Scale"].default_value = 2500.0; nt.links.new(at.outputs["Vector"], shirt_w.inputs["Vector"])
    shirt_c = mix(shirt_w.outputs["Fac"], (0.40, 0.01, 0.16), (0.55, 0.02, 0.24))
    # stack: start at the bottom (peritoneum), overwrite upward
    c = mix(band(-1.0, Z_PER), (0.90, 0.55, 0.55), (0.90, 0.55, 0.55))
    c = mix(band(Z_PER, Z_MUS), c, (0.97, 0.80, 0.78))
    c = mix(band(Z_MUS, Z_FAT), c, mus_r.outputs["Color"])
    c = mix(band(Z_MUS, Z_MUS + 0.0006), c, (0.97, 0.88, 0.86))     # fascia on both sides of the muscle
    c = mix(band(Z_FAT - 0.0006, Z_FAT), c, (0.97, 0.88, 0.86))
    c = mix(band(Z_FAT, Z_SKIN), c, fat_c)
    c = mix(band(Z_SKIN, Z_SHIRT), c, skin_c)
    c = mix(band(Z_SHIRT, 1.0), c, shirt_c)
    # the wound track surface: deep red-pink, glossy; squeezed fat a touch more orange
    c = mix(sq.outputs["Fac"], c, (1.0, 0.55, 0.10))
    trk_m = nt.nodes.new("ShaderNodeMath"); trk_m.operation = 'MULTIPLY'; trk_m.inputs[1].default_value = 1.0; nt.links.new(trk.outputs["Fac"], trk_m.inputs[0])
    c = mix(trk_m.outputs[0], c, (0.62, 0.02, 0.04))
    p = nt.nodes.new("ShaderNodeBsdfPrincipled"); nt.links.new(c, p.inputs["Base Color"])
    rough = mixf(band(Z_FAT, Z_SKIN), 0.40, 0.28)
    p.inputs["Coat Weight"].default_value = 0.35; p.inputs["Coat Roughness"].default_value = 0.15
    nt.links.new(rough, p.inputs["Roughness"])
    p.inputs["Subsurface Weight"].default_value = 0.15; p.inputs["Subsurface Radius"].default_value = (1.0, 0.5, 0.25)
    p.inputs["Subsurface Scale"].default_value = 0.0008
    # lobule relief (bump) in the fat only
    dome = nt.nodes.new("ShaderNodeMath"); dome.operation = 'SQRT'; nt.links.new(ve.outputs["Distance"], dome.inputs[0])
    bpf = nt.nodes.new("ShaderNodeMath"); bpf.operation = 'MULTIPLY'; nt.links.new(dome.outputs[0], bpf.inputs[0]); nt.links.new(band(Z_FAT, Z_SKIN), bpf.inputs[1])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.6; bp.inputs["Distance"].default_value = 0.0004
    nt.links.new(bpf.outputs[0], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], p.inputs["Normal"])
    nt.links.new(p.outputs[0], out.inputs["Surface"])
    return m
M_TISSUE = tissue_mat()
CUT.data.materials.append(M_TISSUE)
M_TOPFAB = mat("M_TopFabric", (0.58, 0.03, 0.26), rough=0.8, sheen=0.3)
ntt = M_TOPFAB.node_tree; pt = ntt.nodes["Principled BSDF"]
tct = ntt.nodes.new("ShaderNodeTexCoord"); wvt = ntt.nodes.new("ShaderNodeTexWave"); wvt.inputs["Scale"].default_value = 2500.0; wvt.inputs["Distortion"].default_value = 3.0
bpt = ntt.nodes.new("ShaderNodeBump"); bpt.inputs["Strength"].default_value = 0.35; bpt.inputs["Distance"].default_value = 0.0002
ntt.links.new(tct.outputs["Object"], wvt.inputs["Vector"]); ntt.links.new(wvt.outputs["Fac"], bpt.inputs["Height"]); ntt.links.new(bpt.outputs["Normal"], pt.inputs["Normal"])
TOP.data.materials.append(M_TOPFAB)

# ---- geometry nodes: wound track + squeeze ahead of the nose + a soft ripple ("energy" keyed on TipCtl's custom props)
# WoundCtl: keyed location carries the wound state (no drivers, no scene clock): x = energy 0..1 (push left in the nose),
# y = ripple phase (linear), z = entry 0..1 (the shirt has been pierced; opens the hole in the top fabric)
WCTL = bpy.data.objects.new("WoundCtl", None); C_MACRO.objects.link(WCTL); WCTL.empty_display_size = 0.01
def wound_gn(name, is_top):
    ng = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    ng.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    N = ng.nodes; L = ng.links
    gi = N.new("NodeGroupInput"); go = N.new("NodeGroupOutput")
    pos = N.new("GeometryNodeInputPosition")
    # store the original position for the shader
    st = N.new("GeometryNodeStoreNamedAttribute"); st.data_type = 'FLOAT_VECTOR'; st.domain = 'POINT'; st.inputs["Name"].default_value = "opos"
    L.new(gi.outputs[0], st.inputs["Geometry"]); L.new(pos.outputs[0], st.inputs["Value"])
    oi = N.new("GeometryNodeObjectInfo"); oi.inputs["Object"].default_value = TIP; oi.transform_space = 'ORIGINAL'
    # the tip position in this object's local space = world - MX (the macro objects are not rotated)
    tip_l = N.new("ShaderNodeVectorMath"); tip_l.operation = 'SUBTRACT'; L.new(oi.outputs["Location"], tip_l.inputs[0]); tip_l.inputs[1].default_value = tuple(MX)
    tsep = N.new("ShaderNodeSeparateXYZ"); L.new(tip_l.outputs[0], tsep.inputs[0])
    psep = N.new("ShaderNodeSeparateXYZ"); L.new(pos.outputs[0], psep.inputs[0])
    def math(op, a_, b_=None, v=None):
        m_ = N.new("ShaderNodeMath"); m_.operation = op
        for i_, x in enumerate((a_, b_)):
            if x is None: continue
            if isinstance(x, (int, float)): m_.inputs[i_].default_value = float(x)
            else: L.new(x, m_.inputs[i_])
        return m_.outputs[0]
    wc = N.new("GeometryNodeObjectInfo"); wc.inputs["Object"].default_value = WCTL; wc.transform_space = 'ORIGINAL'
    wsep = N.new("ShaderNodeSeparateXYZ"); L.new(wc.outputs["Location"], wsep.inputs[0])
    def prop(pn):
        return wsep.outputs[{"energy": "X", "ripple": "Y", "entry": "Z"}[pn]]
    R0 = 0.0045
    zn = tsep.outputs["Z"]            # nose z (local)
    x = psep.outputs["X"]; y = psep.outputs["Y"]; z = psep.outputs["Z"]
    if not is_top:
        ax = math('ABSOLUTE', x)
        # --- track: above the nose (z > zn) and below the top (z < 0): a half-cylinder groove pushed +y (into the tissue)
        above = math('GREATER_THAN', z, zn)
        inside_r = math('LESS_THAN', ax, R0 * 1.05)
        xr = math('DIVIDE', ax, R0); xr2 = math('MULTIPLY', xr, xr); one_m = math('SUBTRACT', 1.0, xr2); one_m = math('MAXIMUM', one_m, 0.0)
        prof = math('SQRT', one_m)
        # behind the bullet the track relaxes to 60 % (the tissue partly closes); at the bullet body it fits the bullet
        dz = math('SUBTRACT', z, zn)                    # >= 0 above the nose
        mr = N.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.016; mr.inputs["From Max"].default_value = 0.030
        mr.inputs["To Min"].default_value = 1.0; mr.inputs["To Max"].default_value = 0.6; L.new(dz, mr.inputs["Value"])
        # nose profile: in the nose zone (0..8 mm above the tip) the radius narrows like the ogive
        nz_r = N.new("ShaderNodeMapRange"); nz_r.inputs["From Min"].default_value = 0.0; nz_r.inputs["From Max"].default_value = 0.008
        nz_r.inputs["To Min"].default_value = 0.25; nz_r.inputs["To Max"].default_value = 1.0; L.new(dz, nz_r.inputs["Value"])
        depth = math('MULTIPLY', prof, mr.outputs["Result"]); depth = math('MULTIPLY', depth, nz_r.outputs["Result"])
        neg_top = math('LESS_THAN', z, 0.0)
        gate = math('MULTIPLY', above, inside_r); gate = math('MULTIPLY', gate, neg_top)
        gy = math('MULTIPLY', depth, gate); gy = math('MULTIPLY', gy, R0)
        # --- squeeze ahead of the nose: down + sideways, bulging slightly toward the camera (-y)
        dx2 = math('MULTIPLY', x, x); dzn = math('SUBTRACT', z, zn); dz2 = math('MULTIPLY', dzn, dzn)
        dist = math('SQRT', math('ADD', dx2, dz2))
        fall = math('EXPONENT', math('MULTIPLY', dist, -1.0 / 0.0045))
        below = math('LESS_THAN', z, math('ADD', zn, 0.002))
        en = prop("energy")
        sq = math('MULTIPLY', math('MULTIPLY', fall, below), en)
        push = math('MULTIPLY', sq, 0.0022)                       # up to 2.2 mm squash
        dirx = math('DIVIDE', x, math('ADD', dist, 1e-5)); dirz = math('DIVIDE', dzn, math('ADD', dist, 1e-5))
        offx = math('MULTIPLY', dirx, push); offz = math('MULTIPLY', dirz, push)
        offy = math('MULTIPLY', sq, -0.0012)
        # --- ripple: a soft radial wave from the nose, amplitude with the energy (the fat "cushions")
        rp = prop("ripple")
        ph = math('SUBTRACT', math('MULTIPLY', dist, 900.0), rp)
        wave = math('SINE', ph)
        damp = math('EXPONENT', math('MULTIPLY', dist, -1.0 / 0.010))
        rip = math('MULTIPLY', math('MULTIPLY', wave, damp), math('MULTIPLY', en, -0.00035))
        offy = math('ADD', offy, rip)
        oy = math('ADD', gy, offy)
        off = N.new("ShaderNodeCombineXYZ"); L.new(offx, off.inputs[0]); L.new(oy, off.inputs[1]); L.new(offz, off.inputs[2])
        sp = N.new("GeometryNodeSetPosition"); L.new(st.outputs[0], sp.inputs["Geometry"]); L.new(off.outputs[0], sp.inputs["Offset"])
        s1 = N.new("GeometryNodeStoreNamedAttribute"); s1.data_type = 'FLOAT'; s1.inputs["Name"].default_value = "track"
        L.new(sp.outputs[0], s1.inputs["Geometry"]); L.new(math('MULTIPLY', gate, math('GREATER_THAN', prof, 0.02)), s1.inputs["Value"])
        s2 = N.new("GeometryNodeStoreNamedAttribute"); s2.data_type = 'FLOAT'; s2.inputs["Name"].default_value = "squeeze"
        L.new(s1.outputs[0], s2.inputs["Geometry"]); L.new(math('MINIMUM', math('MULTIPLY', sq, 1.4), 1.0), s2.inputs["Value"])
        L.new(s2.outputs[0], go.inputs[0])
    else:
        # top fabric: a dimple while the nose presses it, then a hole (half disc at the cut edge) once pierced
        r2 = math('ADD', math('MULTIPLY', x, x), math('MULTIPLY', y, y)); r = math('SQRT', r2)
        dimple = math('MINIMUM', zn, 0.0)                             # nose below the top -> negative
        fall = math('EXPONENT', math('MULTIPLY', r, -1.0 / 0.006))
        ent = prop("entry")
        dz_ = math('MULTIPLY', math('MULTIPLY', dimple, fall), math('SUBTRACT', 1.0, ent))
        dz_ = math('MAXIMUM', dz_, -0.004)
        # a raised torn rim once pierced (0.6 mm), so the hole edge reads
        rim = math('MULTIPLY', math('EXPONENT', math('MULTIPLY', math('ABSOLUTE', math('SUBTRACT', r, R0 * 1.1)), -1.0 / 0.0012)), math('MULTIPLY', ent, -0.0006))
        off = N.new("ShaderNodeCombineXYZ"); L.new(math('ADD', dz_, rim), off.inputs[2])
        sp = N.new("GeometryNodeSetPosition"); L.new(st.outputs[0], sp.inputs["Geometry"]); L.new(off.outputs[0], sp.inputs["Offset"])
        hole = math('MULTIPLY', math('LESS_THAN', r, R0 * 0.95), ent)
        dl = N.new("GeometryNodeDeleteGeometry"); dl.domain = 'POINT'; L.new(sp.outputs[0], dl.inputs["Geometry"]); L.new(math('GREATER_THAN', hole, 0.5), dl.inputs["Selection"])
        L.new(dl.outputs[0], go.inputs[0])
    return ng
for o, top in ((CUT, False), (TOP, True)):
    md = o.modifiers.new("Wound", 'NODES'); md.node_group = wound_gn("GN_Wound_" + ("top" if top else "cut"), top)

# ---- the bowel loops below the peritoneum (procedural): glossy pink tubes, 2.2 cm across, coiled in rows behind the cut plane
gm = mat("M_Bowel", (0.92, 0.32, 0.38), rough=0.25, sss=0.15, coat=0.6)
ntb = gm.node_tree; pb_ = ntb.nodes["Principled BSDF"]
tcb_ = ntb.nodes.new("ShaderNodeTexCoord"); wvb = ntb.nodes.new("ShaderNodeTexWave"); wvb.inputs["Scale"].default_value = 160.0
wvb.inputs["Distortion"].default_value = 1.5; ntb.links.new(tcb_.outputs["Object"], wvb.inputs["Vector"])
crb_ = ntb.nodes.new("ShaderNodeValToRGB"); crb_.color_ramp.elements[0].color = (0.92, 0.33, 0.40, 1); crb_.color_ramp.elements[1].color = (0.98, 0.40, 0.46, 1)
ntb.links.new(wvb.outputs["Fac"], crb_.inputs["Fac"]); ntb.links.new(crb_.outputs["Color"], pb_.inputs["Base Color"])
bpb = ntb.nodes.new("ShaderNodeBump"); bpb.inputs["Strength"].default_value = 0.12; bpb.inputs["Distance"].default_value = 0.0006
ntb.links.new(wvb.outputs["Fac"], bpb.inputs["Height"]); ntb.links.new(bpb.outputs["Normal"], pb_.inputs["Normal"])
rng_ = random.Random(7)
def meander(seed, z0, z1, n=26):
    """a coiled bowel path in the cavity (x-z, just behind the cut plane): a random walk that turns back on itself"""
    r_ = random.Random(seed); x, z = r_.uniform(-0.09, 0.09), r_.uniform(z1, z0); ang = r_.uniform(0, 6.28); pts = []
    for i in range(n):
        pts.append((x, 0.0105 + r_.uniform(-0.002, 0.004), z))
        ang += r_.uniform(-1.3, 1.3); step = 0.017
        nx, nz = x + math.cos(ang) * step, z + math.sin(ang) * step
        if not (-0.12 < nx < 0.12) or not (z1 < nz < z0): ang += math.pi; nx, nz = x + math.cos(ang) * step, z + math.sin(ang) * step
        x, z = nx, nz
    return pts
for k in range(5):
    cu = bpy.data.curves.new("MC_BowelC%d" % k, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.0085; cu.bevel_resolution = 6
    cu.resolution_u = 16; sp_ = cu.splines.new('BEZIER'); pts_ = meander(11 + k, ZB - 0.010, ZB - 0.080)
    sp_.bezier_points.add(len(pts_) - 1)
    for i, pt in enumerate(pts_):
        bp_ = sp_.bezier_points[i]; bp_.co = pt; bp_.handle_left_type = bp_.handle_right_type = 'AUTO'
    o = bpy.data.objects.new("MC_Bowel%d" % k, cu); C_MACRO.objects.link(o); o.location = MX
    cu.materials.append(gm)
# cavity wall behind the loops (deep wine-red, glossy), a pearly peritoneum sheet just under the muscle
cav = box("MC_Cavity", (2 * XW + 0.1, 0.01, 0.14), (MX.x, 0.075, ZB - 0.07), mat("M_Cavity", (0.35, 0.03, 0.08), rough=0.35, coat=0.4), bevel=0.0)
to_col(cav, C_MACRO)
# the backdrop above the tissue: a deep blue-to-cyan gradient (the explainer sky), far behind
bpy.ops.mesh.primitive_plane_add(size=1, location=MX + Vector((0, 0.35, 0.05)), rotation=(math.radians(90), 0, 0))
BD = bpy.context.active_object; BD.name = "MC_Backdrop"; BD.scale = (1.2, 0.8, 1)
bdm = bpy.data.materials.new("M_Backdrop"); bdm.use_nodes = True; nt = bdm.node_tree
for n in list(nt.nodes):
    if n.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n)
tcb = nt.nodes.new("ShaderNodeTexCoord"); spb = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tcb.outputs["Generated"], spb.inputs[0])
crb = nt.nodes.new("ShaderNodeValToRGB"); crb.color_ramp.elements[0].color = (0.02, 0.10, 0.45, 1); crb.color_ramp.elements[1].color = (0.20, 0.72, 0.98, 1)
nt.links.new(spb.outputs["Y"], crb.inputs["Fac"])
emb = nt.nodes.new("ShaderNodeEmission"); emb.inputs["Strength"].default_value = 1.0; nt.links.new(crb.outputs["Color"], emb.inputs["Color"])
nt.links.new(emb.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
BD.data.materials.append(bdm); to_col(BD, C_MACRO)
# macro lights: soft high-key key from front-top-left, a fill from the right, a warm rim from above-behind
light("MC_Key", 'AREA', 1.6, MX + Vector((-0.10, -0.18, 0.10)), rot=(math.radians(62), 0, math.radians(-28)), size=0.12, color=(1.0, 0.96, 0.92), c=C_MACRO)
light("MC_Fill", 'AREA', 0.8, MX + Vector((0.14, -0.16, -0.02)), rot=(math.radians(85), 0, math.radians(40)), size=0.15, color=(0.90, 0.95, 1.0), c=C_MACRO)
light("MC_Top", 'AREA', 0.7, MX + Vector((0.0, 0.03, 0.12)), rot=(0, 0, 0), size=0.10, color=(1.0, 0.90, 0.80), c=C_MACRO)


# ================================================================== look and render settings (fast, zero-error)
sc.render.engine = 'CYCLES'; cy = sc.cycles
cy.samples = 64; cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.05
cy.use_denoising = True; cy.denoiser = 'OPENIMAGEDENOISE'
cy.max_bounces = 6; cy.diffuse_bounces = 3; cy.glossy_bounces = 3; cy.transmission_bounces = 6; cy.transparent_max_bounces = 16
cy.caustics_reflective = False; cy.caustics_refractive = False
sc.render.use_persistent_data = True
sc.render.use_simplify = True; sc.render.simplify_subdivision_render = 2; cy.texture_limit_render = '2048'
sc.render.use_motion_blur = False
sc.view_settings.view_transform = 'Filmic'; sc.view_settings.look = 'High Contrast'; sc.view_settings.exposure = -0.6
sc.world = sc.world or bpy.data.worlds.new("World")
w = sc.world; w.use_nodes = True; nt = w.node_tree
for n in list(nt.nodes):
    if n.type != 'OUTPUT_WORLD': nt.nodes.remove(n)
tc = nt.nodes.new("ShaderNodeTexCoord"); sp = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Generated"], sp.inputs[0])
mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.5; mr.inputs["From Max"].default_value = 0.75; nt.links.new(sp.outputs["Z"], mr.inputs["Value"])
cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (0.55, 0.82, 1.0, 1); cr.color_ramp.elements[1].color = (0.05, 0.38, 0.95, 1)
nt.links.new(mr.outputs["Result"], cr.inputs["Fac"])
bg = nt.nodes.new("ShaderNodeBackground"); bg.inputs["Strength"].default_value = 1.0; nt.links.new(cr.outputs["Color"], bg.inputs["Color"])
nt.links.new(bg.outputs[0], nt.nodes["Output"].inputs["Surface"] if "Output" in nt.nodes else [n for n in nt.nodes if n.type == 'OUTPUT_WORLD'][0].inputs["Surface"])
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("BUILD_DONE", OUT)
