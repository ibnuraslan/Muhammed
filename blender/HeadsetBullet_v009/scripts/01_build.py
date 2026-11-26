"""HeadsetBullet v009 stage A (from scratch): one boy, one headset, one bullet, two sets.
blender -b --python 01_build.py -- <polyhaven_dir> <out.blend>

HOME (origin): a teen's gaming room. The boy sits at the origin facing -Y at his desk (monitor at y=-0.88).
The window is in the wall on his LEFT (+X, inner face x=+1.40); outside it (x>1.55) a sunny lawn, a tree and the house
facade with a tiled roof. The window has two casement leaves: the front leaf (y<0) is closed (its glass takes the
bullet), the back leaf is open inward (the camera's way in). The back wall (y=+1.80) takes the ricochet.
MACRO (x=+20): a real-scale cross-section of the left ear cup (shell, padding foam, metal frame, cushion). The cut face
is the plane y=0 (seen from -Y); material lies at y>0; the outer shell face is z=0; the bullet comes straight down
(x=0). One geometry-nodes modifier carves the bullet track and squeezes the foam, driven by keyed empties (no scene clock)."""
import bpy, bmesh, sys, math, random, os
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "lib_build.py")).read())
a = sys.argv[sys.argv.index("--") + 1:]
PH, OUT = a[0], a[1]
PKG = os.path.dirname(HERE)
random.seed(20)
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
sc = bpy.context.scene
sc.render.fps = 60
sc.frame_start, sc.frame_end = 1, 1203
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
MX = Vector((20.0, 0.0, 0.0))
def col(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in sc.collection.children: sc.collection.children.link(c)
    return c
C_HOME, C_MACRO = col("HOME"), col("MACRO")
def to_col(o, c):
    for cc in list(o.users_collection): cc.objects.unlink(o)
    c.objects.link(o)

# ================================================================== the boy (ONE model for the whole film)
B, BB = human("Boy", 1.0, 0.32, {"asian": 0.10, "caucasian": 0.55, "african": 0.35}, "short02/short02.mhclo",
              "young_caucasian_male/young_caucasian_male.mhmat", "eyebrow001/eyebrow001.mhclo",
              height=0.5, weight=0.45, muscle=0.5,
              clothes=["male_casualsuit04/male_casualsuit04.mhclo", "shoes02/shoes02.mhclo"])
eye_fix(B); eye_group_fix()
EG = bpy.data.node_groups.get("EnhancedEye")
for n in (EG.nodes if EG else []):
    if n.type == 'MATH' and abs(n.inputs[1].default_value - 0.92) < 1e-4: n.inputs[1].default_value = 0.96
for m in [m for c in B.children if c.type == 'MESH' and "high-poly" in c.name for m in c.data.materials]:
    for n in m.node_tree.nodes:
        if n.type == 'GROUP' and "IrisMajorColor" in n.inputs:
            n.inputs["IrisMajorColor"].default_value = (0.16, 0.08, 0.03, 1); n.inputs["IrisMinorColor"].default_value = (0.06, 0.03, 0.01, 1)
for c in B.children:
    if c.type == 'MESH' and any(k in c.name.lower() for k in ("short02", "eyebrow")):
        for m in c.data.materials: tint(m, (0.35, 0.22, 0.14))
for m in BB.data.materials: tint(m, (0.95, 0.74, 0.60))
for c in B.children:
    if c.type == 'MESH' and "teeth" in c.name:
        for m in c.data.materials: tint(m, (1.5, 1.45, 1.4))
SUIT = [c for c in B.children if c.type == 'MESH' and "casualsuit" in c.name][0]
SUIT.name = "Boy.clothes"
tee = bpy.data.images.load(os.path.join(PKG, "assets/tex/boy_tee_diffuse.png")); tee.name = "boy_tee_diffuse"
for m in SUIT.data.materials:
    for nd in m.node_tree.nodes:
        if nd.type == 'TEX_IMAGE' and nd.image and "diffuse" in nd.image.name.lower():
            nd.image = tee
        if nd.type == 'NORMAL_MAP': nd.inputs["Strength"].default_value = 0.5
# solid garments: real thickness, no open paper edges
for c in B.children:
    if c.type == 'MESH' and ("clothes" in c.name or "shoes" in c.name):
        so = c.modifiers.new("solid", 'SOLIDIFY'); so.thickness = 0.003; so.offset = 1.0; so.use_rim = True
        i = c.modifiers.find("solid")
        while i > c.modifiers.find("Armature") + 1:
            c.modifiers.move(i, i - 1); i -= 1
# flatten the chest under the T-shirt (no clinging contour): smooth + 4 mm lift on the breast weights, before thickness
vg_ = SUIT.vertex_groups.new(name="chest_flat")
gi_ = [SUIT.vertex_groups[n].index for n in ("breast.L", "breast.R")]
for v in SUIT.data.vertices:
    w_ = max((g.weight for g in v.groups if g.group in gi_), default=0.0)
    if w_ > 0.01: vg_.add([v.index], min(1.0, w_ * 1.5), 'REPLACE')
smm = SUIT.modifiers.new("chest_smooth", 'SMOOTH'); smm.factor = 1.0; smm.iterations = 14; smm.vertex_group = "chest_flat"
dsm = SUIT.modifiers.new("chest_lift", 'DISPLACE'); dsm.strength = 0.004; dsm.mid_level = 0.0; dsm.direction = 'NORMAL'; dsm.vertex_group = "chest_flat"
for nm_ in ("chest_lift", "chest_smooth"):
    i = SUIT.modifiers.find(nm_)
    while i > SUIT.modifiers.find("Armature") + 1:
        SUIT.modifiers.move(i, i - 1); i -= 1
for c in B.children:
    to_col(c, C_HOME)
to_col(B, C_HOME)
print("BODY MODS", [(m.name, m.type) for m in BB.modifiers])

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

def tiles(name, c1, c2, mortar, scale=4.0, rw=0.5, rh=0.5, rough=0.45):
    m = mat(name, c1, rough=rough, coat=0.2)
    nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); br = nt.nodes.new("ShaderNodeTexBrick")
    br.inputs["Scale"].default_value = scale; br.offset = 0.5
    br.inputs["Color1"].default_value = (*c1, 1); br.inputs["Color2"].default_value = (*c2, 1); br.inputs["Mortar"].default_value = (*mortar, 1)
    br.inputs["Mortar Size"].default_value = 0.015; br.inputs["Brick Width"].default_value = rw; br.inputs["Row Height"].default_value = rh
    nt.links.new(tc.outputs["Object"], br.inputs["Vector"]); nt.links.new(br.outputs["Color"], p.inputs["Base Color"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.4; bp.inputs["Distance"].default_value = 0.004
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

def image_mat(name, path, emit=0.0, rough=0.5):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    img = bpy.data.images.load(path); img.name = os.path.basename(path)
    tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = img; tx.extension = 'EXTEND'
    nt.links.new(tx.outputs["Color"], p.inputs["Base Color"]); p.inputs["Roughness"].default_value = rough
    if emit:
        nt.links.new(tx.outputs["Color"], p.inputs["Emission Color"]); p.inputs["Emission Strength"].default_value = emit
    return m, tx

M_WALL_IN = plaster("M_WallIn", (0.020, 0.040, 0.30), (0.030, 0.055, 0.36), scale=8.0)        # deep royal-blue room
M_WALL_ACC = plaster("M_WallAccent", (0.30, 0.03, 0.22), (0.36, 0.05, 0.27), scale=8.0)       # plum accent (window wall)
M_FACADE = mat("M_Facade", (0.92, 0.80, 0.52), rough=0.7)                                     # warm cream siding
M_TRIM = mat("M_Trim", (0.93, 0.93, 0.91), rough=0.35, coat=0.3)
M_ROOF = tiles("M_RoofTiles", (0.55, 0.10, 0.04), (0.65, 0.14, 0.05), (0.25, 0.05, 0.02), scale=7.0, rw=0.6, rh=0.35)
M_FLOOR = wood("M_Floor", (0.32, 0.12, 0.04), (0.46, 0.20, 0.07), scale=2.0)
M_CEIL = mat("M_Ceiling", (0.85, 0.84, 0.88), rough=0.9)
M_GLASS = thin_glass("M_Glass")
M_LAWN = mat("M_Lawn", (0.10, 0.42, 0.04), rough=0.9)
ntl = M_LAWN.node_tree; pl = ntl.nodes["Principled BSDF"]
tcl = ntl.nodes.new("ShaderNodeTexCoord"); nzl = ntl.nodes.new("ShaderNodeTexNoise"); nzl.inputs["Scale"].default_value = 3.0
crl = ntl.nodes.new("ShaderNodeValToRGB"); crl.color_ramp.elements[0].color = (0.06, 0.32, 0.03, 1); crl.color_ramp.elements[1].color = (0.20, 0.55, 0.06, 1)
ntl.links.new(tcl.outputs["Object"], nzl.inputs["Vector"]); ntl.links.new(nzl.outputs["Fac"], crl.inputs["Fac"]); ntl.links.new(crl.outputs["Color"], pl.inputs["Base Color"])
M_DESK = mat("M_Desk", (0.02, 0.02, 0.025), rough=0.35, coat=0.4)                                # black gloss desk
M_BLACK = mat("M_BlackPlastic", (0.015, 0.015, 0.018), rough=0.35)
M_ALU = mat("M_Alu", (0.75, 0.76, 0.80), rough=0.25, metal=1.0)
M_CHAIR_R = mat("M_ChairRed", (0.55, 0.01, 0.02), rough=0.45, coat=0.3, sheen=0.2)
M_CHAIR_K = mat("M_ChairBlack", (0.02, 0.02, 0.025), rough=0.55, sheen=0.2)
M_LED_M = mat("M_LedMagenta", (1.0, 0.1, 0.7), emit=((1.0, 0.05, 0.65), 12.0))
M_LED_C = mat("M_LedCyan", (0.1, 0.9, 1.0), emit=((0.05, 0.85, 1.0), 10.0))
M_SCREEN, TX_SCREEN = image_mat("M_Screen", os.path.join(PKG, "assets/tex/game_screen.png"), emit=2.2, rough=0.2)
M_MAT, TX_MAT = image_mat("M_DeskMat", os.path.join(PKG, "assets/tex/deskmat.png"), rough=0.75)
M_KEYS = mat("M_Keys", (0.03, 0.03, 0.035), rough=0.5)

# ================================================================== HOME set: room shell
WX_IN, WX_OUT = 1.40, 1.55
OPEN_Y = (-0.60, 0.60); OPEN_Z = (0.95, 2.15)
YF, YB = -1.15, 1.80                     # front wall (behind the monitor), back wall (ricochet)
def wall_x_with_hole(name, x0, x1, yr, zr, hole_y, hole_z, material):
    pieces = []
    for nm, y0, y1, z0, z1 in (("L", yr[0], hole_y[0], zr[0], zr[1]), ("R", hole_y[1], yr[1], zr[0], zr[1]),
                               ("T", hole_y[0], hole_y[1], hole_z[1], zr[1]), ("B", hole_y[0], hole_y[1], zr[0], hole_z[0])):
        if y1 - y0 < 1e-4 or z1 - z0 < 1e-4: continue
        pieces.append(box(name + nm, (x1 - x0, y1 - y0, z1 - z0), ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), material, bevel=0.0))
    bpy.ops.object.select_all(action='DESELECT')
    for p in pieces: p.select_set(True)
    bpy.context.view_layer.objects.active = pieces[0]; bpy.ops.object.join()
    o = bpy.context.active_object; o.name = name
    return o
wall_x_with_hole("HM_WindowWall", WX_IN, WX_OUT, (YF - 0.1, YB + 0.1), (0.0, 2.7), OPEN_Y, OPEN_Z, M_WALL_ACC)
wall_x_with_hole("HM_Facade", WX_OUT, WX_OUT + 0.002, (-5.0, 5.0), (-0.05, 2.95), OPEN_Y, OPEN_Z, M_FACADE)
box("HM_Floor", (3.6, YB - YF + 0.2, 0.05), (-0.35, (YF + YB) / 2, -0.025), M_FLOOR, bevel=0.0)
box("HM_Ceiling", (3.6, YB - YF + 0.2, 0.05), (-0.35, (YF + YB) / 2, 2.70), M_CEIL, bevel=0.0)
box("HM_FrontWall", (3.6, 0.1, 2.8), (-0.35, YF - 0.05, 1.35), M_WALL_IN, bevel=0.0)
box("HM_BackWall", (3.6, 0.1, 2.8), (-0.35, YB + 0.05, 1.35), M_WALL_IN, bevel=0.0)
box("HM_SideWallR", (0.1, YB - YF + 0.2, 2.8), (-2.10, (YF + YB) / 2, 1.35), M_WALL_IN, bevel=0.0)
for nm, size, loc in (("HM_SkirtB", (3.4, 0.02, 0.10), (-0.35, YB - 0.01, 0.05)), ("HM_SkirtF", (3.4, 0.02, 0.10), (-0.35, YF + 0.01, 0.05)),
                      ("HM_SkirtW", (0.02, YB - YF, 0.10), (WX_IN - 0.01, (YF + YB) / 2, 0.05))):
    box(nm, size, loc, M_TRIM, bevel=0.003)
# a deep-purple rug under the chair
box("HM_Rug", (1.6, 1.4, 0.008), (0.0, 0.15, 0.004), fabric("M_Rug", (0.18, 0.02, 0.30), scale=500, bump=0.35), bevel=0.003)

# ---- the window: casing, sill, two casement leaves (front closed, back open inward)
def leaf(name, w, h):
    """a casement leaf in its own space: y 0..w (hinge at y=0), z 0..h, thickness 0.05 (x); returns frame, glass"""
    st = 0.06; parts = []
    for nm, sz, lc in (("_s0", (0.05, st, h), (0, st / 2, h / 2)), ("_s1", (0.05, st, h), (0, w - st / 2, h / 2)),
                       ("_top", (0.046, w - 0.004, st), (0, w / 2, h - st / 2)), ("_bot", (0.046, w - 0.004, st), (0, w / 2, st / 2)),
                       ("_mid", (0.04, w - 0.004, 0.03), (0, w / 2, h * 0.52))):
        parts.append(box(name + nm, sz, lc, M_TRIM, bevel=0.0))
    bpy.ops.object.select_all(action='DESELECT')
    for p in parts: p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]; bpy.ops.object.join()
    fr = bpy.context.active_object; fr.name = name + "_Frame"
    gw, gh = w - 2 * st, h - 2 * st
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, w / 2, h / 2), rotation=(0, math.radians(90), 0))
    gl = bpy.context.active_object; gl.name = name + "_Glass"; gl.scale = (gh, gw, 1); bpy.ops.object.transform_apply(scale=True)
    gl.data.materials.append(M_GLASS); gl.parent = fr
    return fr, gl
LW = (OPEN_Y[1] - OPEN_Y[0]) / 2; LH = OPEN_Z[1] - OPEN_Z[0]
XL = (WX_IN + WX_OUT) / 2
LEAF_A, GLASS_A = leaf("HM_LeafA", LW, LH)          # closed: hinge at y=-0.60, spans to y=0
LEAF_A.location = (XL, OPEN_Y[0], OPEN_Z[0])
LEAF_B, GLASS_B = leaf("HM_LeafB", LW, LH)          # open inward: hinge at y=+0.60
LEAF_B.location = (XL, OPEN_Y[1], OPEN_Z[0]); LEAF_B.rotation_euler = (0, 0, math.radians(180 - 95))       # swung 95 deg into the room
for nm, sz, lc in (("HM_CaseL", (0.03, 0.10, LH + 0.12), (WX_OUT + 0.015, OPEN_Y[0] - 0.05, OPEN_Z[0] + LH / 2)),
                   ("HM_CaseR", (0.03, 0.10, LH + 0.12), (WX_OUT + 0.015, OPEN_Y[1] + 0.05, OPEN_Z[0] + LH / 2)),
                   ("HM_CaseT", (0.04, 1.40, 0.12), (WX_OUT + 0.02, 0, OPEN_Z[1] + 0.06)),
                   ("HM_SillOut", (0.20, 1.40, 0.04), (WX_OUT + 0.06, 0, OPEN_Z[0] - 0.02)),
                   ("HM_SillIn", (0.18, 1.36, 0.03), (WX_IN - 0.06, 0, OPEN_Z[0] - 0.015))):
    box(nm, sz, lc, M_TRIM, bevel=0.006)
# the crack in the closed leaf's glass (radial + ring cracks, revealed by a keyed scale; transparent hole in the middle)
def crack_mat(name="M_Crack", hole_r=0.012, ring=28.0, white=(0.95, 0.97, 1.0), emit=0.4, metal_core=False):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n)
    tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sep.inputs[0])
    at = nt.nodes.new("ShaderNodeMath"); at.operation = 'ARCTAN2'; nt.links.new(sep.outputs["Y"], at.inputs[0]); nt.links.new(sep.outputs["X"], at.inputs[1])
    ln0 = nt.nodes.new("ShaderNodeVectorMath"); ln0.operation = 'LENGTH'; nt.links.new(tc.outputs["Object"], ln0.inputs[0])
    gv = nt.nodes.new("ShaderNodeValue"); gv.name = "Grow"; gv.outputs[0].default_value = 1.0
    gmax = nt.nodes.new("ShaderNodeMath"); gmax.operation = 'MAXIMUM'; gmax.inputs[1].default_value = 0.002; nt.links.new(gv.outputs[0], gmax.inputs[0])
    ln = nt.nodes.new("ShaderNodeMath"); ln.operation = 'DIVIDE'; nt.links.new(ln0.outputs["Value"], ln.inputs[0]); nt.links.new(gmax.outputs[0], ln.inputs[1])
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 30.0; nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    def M(op, a_, b_=None):
        m_ = nt.nodes.new("ShaderNodeMath"); m_.operation = op
        for i_, x in enumerate((a_, b_)):
            if x is None: continue
            if isinstance(x, (int, float)): m_.inputs[i_].default_value = float(x)
            else: nt.links.new(x, m_.inputs[i_])
        return m_.outputs[0]
    rad = M('LESS_THAN', M('ABSOLUTE', M('SINE', M('ADD', M('MULTIPLY', at.outputs[0], 9.0), M('MULTIPLY', nz.outputs["Fac"], 2.2)))), 0.06)
    rg = M('LESS_THAN', M('FRACT', M('ADD', M('MULTIPLY', ln.outputs[0], ring), nz.outputs["Fac"])), 0.05)
    rgm = M('MULTIPLY', rg, M('LESS_THAN', ln.outputs[0], 0.07 * 28.0 / ring))
    mxm = M('MAXIMUM', rad, rgm)
    fd = nt.nodes.new("ShaderNodeMapRange"); fd.inputs["From Min"].default_value = 0.12 * 28.0 / ring; fd.inputs["From Max"].default_value = 0.30 * 28.0 / ring
    fd.inputs["To Min"].default_value = 1.0; fd.inputs["To Max"].default_value = 0.0; nt.links.new(ln.outputs[0], fd.inputs["Value"])
    a1 = M('MULTIPLY', mxm, fd.outputs[0])
    hole = M('LESS_THAN', ln.outputs[0], hole_r)
    halo = M('LESS_THAN', ln.outputs[0], hole_r * 1.6)
    a2 = M('MAXIMUM', a1, halo)
    wh = nt.nodes.new("ShaderNodeBsdfPrincipled"); wh.inputs["Base Color"].default_value = (*white, 1); wh.inputs["Roughness"].default_value = 0.3
    wh.inputs["Emission Color"].default_value = (*white, 1); wh.inputs["Emission Strength"].default_value = emit
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mx = nt.nodes.new("ShaderNodeMixShader"); nt.links.new(a2, mx.inputs["Fac"]); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(wh.outputs[0], mx.inputs[2])
    mx2 = nt.nodes.new("ShaderNodeMixShader"); nt.links.new(hole, mx2.inputs["Fac"]); nt.links.new(mx.outputs[0], mx2.inputs[1])
    if metal_core:      # a gouge: dark rim, bright bare metal at the centre
        core = nt.nodes.new("ShaderNodeBsdfPrincipled"); core.inputs["Base Color"].default_value = (0.8, 0.8, 0.82, 1)
        core.inputs["Metallic"].default_value = 1.0; core.inputs["Roughness"].default_value = 0.3
        dark = nt.nodes.new("ShaderNodeBsdfPrincipled"); dark.inputs["Base Color"].default_value = (0.02, 0.01, 0.01, 1)
        mc = nt.nodes.new("ShaderNodeMixShader"); nt.links.new(M('LESS_THAN', ln.outputs[0], hole_r * 0.6), mc.inputs["Fac"])
        nt.links.new(dark.outputs[0], mc.inputs[1]); nt.links.new(core.outputs[0], mc.inputs[2]); nt.links.new(mc.outputs[0], mx2.inputs[2])
    else:
        tr2 = nt.nodes.new("ShaderNodeBsdfTransparent"); nt.links.new(tr2.outputs[0], mx2.inputs[2])
    nt.links.new(mx2.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    return m
GLASS_HIT = Vector((XL - 0.002, -0.22, 1.27))
bpy.ops.mesh.primitive_circle_add(vertices=64, radius=0.30, fill_type='NGON', location=(0, 0, 0), rotation=(0, math.radians(90), 0))
CRACK = bpy.context.active_object; CRACK.name = "HM_GlassCrack"; CRACK.data.materials.append(crack_mat())
CRACK.location = GLASS_HIT + Vector((-0.004, 0, 0)); CRACK.scale = (0.001,) * 3
# 36 glass shards (thin slivers), placed on the pane around the hole; animated in 02
M_SHARD = mat("M_Shard", (0.80, 0.92, 1.0), rough=0.05, coat=1.0)
M_SHARD.node_tree.nodes["Principled BSDF"].inputs["Transmission Weight"].default_value = 0.85
SHARDS = []
rs = random.Random(5)
for k in range(36):
    bm = bmesh.new(); n = rs.choice((3, 4)); r_ = rs.uniform(0.008, 0.022)
    vs = [bm.verts.new((0.0, r_ * math.cos(2 * math.pi * i / n + rs.uniform(-0.4, 0.4)) * rs.uniform(0.6, 1.2),
                        r_ * math.sin(2 * math.pi * i / n + rs.uniform(-0.4, 0.4)) * rs.uniform(0.6, 1.2))) for i in range(n)]
    bm.faces.new(vs)
    me = bpy.data.meshes.new("Shard%02d" % k); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("HM_Shard%02d" % k, me); C_HOME.objects.link(o)
    so = o.modifiers.new("so", 'SOLIDIFY'); so.thickness = 0.003
    me.materials.append(M_SHARD); SHARDS.append(o)
    ang = rs.uniform(0, 2 * math.pi); d_ = rs.uniform(0.01, 0.10)
    o.location = GLASS_HIT + Vector((0, math.cos(ang) * d_, math.sin(ang) * d_))
    o["home"] = tuple(o.location)

# ---- the desk, monitor, keyboard, mouse, desk mat, chair
DESK_Z = 0.73; DY0, DY1 = -0.30, -1.08            # desk top height, front edge (toward him) and back edge
box("HM_DeskTop", (1.50, DY0 - DY1, 0.03), (0.0, (DY0 + DY1) / 2, DESK_Z - 0.015), M_DESK, bevel=0.004)
for sx in (-1, 1):
    box("HM_DeskLeg%d" % sx, (0.05, DY0 - DY1 - 0.10, 0.05), (sx * 0.70, (DY0 + DY1) / 2, 0.025), M_BLACK, bevel=0.004)
    box("HM_DeskPost%d" % sx, (0.05, 0.05, DESK_Z - 0.08), (sx * 0.70, (DY0 + DY1) / 2, (DESK_Z - 0.03) / 2 + 0.025), M_BLACK, bevel=0.004)
box("HM_DeskBeam", (1.40, 0.04, 0.06), (0.0, DY1 + 0.10, DESK_Z - 0.06), M_BLACK, bevel=0.003)
# LED strip along the back edge of the desk (magenta) and along the window wall top (cyan)
box("HM_LedDesk", (1.46, 0.012, 0.010), (0.0, DY1 + 0.005, DESK_Z - 0.035), M_LED_M, bevel=0.0)
box("HM_LedWall", (0.012, YB - YF - 0.1, 0.012), (WX_IN - 0.01, (YF + YB) / 2, 2.62), M_LED_C, bevel=0.0)
box("HM_LedBack", (3.2, 0.012, 0.012), (-0.35, YB - 0.01, 2.62), M_LED_M, bevel=0.0)
# desk mat (0.90 x 0.42) with the logo; UV so the image's +x runs to his right (-X) and the image top is the far edge
MAT_C = Vector((-0.06, -0.55, DESK_Z + 0.002))
bpy.ops.mesh.primitive_plane_add(size=1, location=MAT_C)
DM = bpy.context.active_object; DM.name = "HM_DeskMat"; DM.scale = (0.90, 0.42, 1); bpy.ops.object.transform_apply(scale=True)
for lp in DM.data.uv_layers.active.data: pass
uvl = DM.data.uv_layers.active
for poly in DM.data.polygons:
    for li in poly.loop_indices:
        v = DM.data.vertices[DM.data.loops[li].vertex_index].co
        uvl.data[li].uv = (0.5 - v.x / 0.90, 0.5 - v.y / 0.42)
sol = DM.modifiers.new("so", 'SOLIDIFY'); sol.thickness = 0.003; sol.offset = -1.0
DM.data.materials.append(M_MAT)
# keyboard (tenkeyless, black frame, key grid) and mouse
KB_C = Vector((0.10, -0.46, DESK_Z + 0.004))
box("HM_Keyboard", (0.36, 0.13, 0.022), KB_C + Vector((0, 0, 0.011)), M_BLACK, bevel=0.004)
for r_ in range(5):
    for c_ in range(15):
        box("HM_Key%d_%d" % (r_, c_), (0.019, 0.019, 0.008), KB_C + Vector((0.16 - c_ * 0.0228, -0.048 + r_ * 0.0235, 0.025)), M_KEYS, bevel=0.002, segs=1)
bpy.ops.object.select_all(action='DESELECT')
for o in bpy.data.objects:
    if o.name.startswith("HM_Key") and o.name != "HM_Keyboard": o.select_set(True)
bpy.context.view_layer.objects.active = [o for o in bpy.context.selected_objects][0]; bpy.ops.object.join()
bpy.context.active_object.name = "HM_Keys"
# keyboard backlight: a thin emissive plate under the keys
box("HM_KeyGlow", (0.345, 0.118, 0.002), KB_C + Vector((0, 0, 0.0225)), M_LED_C, bevel=0.0)
MOUSE_C = Vector((-0.25, -0.44, DESK_Z + 0.005))
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=32, ring_count=16, location=MOUSE_C)
MS = bpy.context.active_object; MS.name = "HM_Mouse"; MS.scale = (0.032, 0.060, 0.020)
bpy.ops.object.transform_apply(scale=True)
bm = bmesh.new(); bm.from_mesh(MS.data)
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < 0.0], context='VERTS')
bm.to_mesh(MS.data); bm.free()
MS.data.materials.append(M_BLACK); bpy.ops.object.shade_smooth()
sm_ = MS.modifiers.new("so", 'SOLIDIFY'); sm_.thickness = 0.003
box("HM_MouseLed", (0.004, 0.02, 0.003), MOUSE_C + Vector((0, -0.035, 0.012)), M_LED_M, bevel=0.0).parent = MS
bpy.data.objects["HM_MouseLed"].matrix_parent_inverse = MS.matrix_world.inverted()
# monitor: 27" class, thin bezel, on a stand
MON_C = Vector((0.05, -0.86, DESK_Z + 0.36)); MW_, MH_ = 0.64, 0.37
box("HM_MonBezel", (MW_ + 0.02, 0.03, MH_ + 0.02), MON_C + Vector((0, -0.015, 0)), M_BLACK, bevel=0.004)
bpy.ops.mesh.primitive_plane_add(size=1, location=MON_C + Vector((0, 0.0012, 0)), rotation=(math.radians(90), 0, math.radians(180)))
SCR = bpy.context.active_object; SCR.name = "HM_Screen"; SCR.scale = (MW_, MH_, 1); bpy.ops.object.transform_apply(scale=True)
SCR.data.materials.append(M_SCREEN)
box("HM_MonNeck", (0.05, 0.03, 0.26), MON_C + Vector((0, -0.05, -0.20)), M_ALU, bevel=0.004)
box("HM_MonFoot", (0.26, 0.18, 0.012), Vector((MON_C.x, MON_C.y - 0.06, DESK_Z + 0.006)), M_ALU, bevel=0.004)
# a tower PC on the floor to his left-front (glass side panel lit), speakers on the desk
box("HM_Tower", (0.22, 0.45, 0.48), (0.48, -0.78, 0.24), M_BLACK, bevel=0.008)
box("HM_TowerGlow", (0.002, 0.40, 0.40), (0.59, -0.78, 0.25), M_LED_C, bevel=0.0)
for sx, nm in ((1, "L"), (-1, "R")):
    box("HM_Speaker" + nm, (0.10, 0.12, 0.18), (MON_C.x + sx * 0.46, -0.90, DESK_Z + 0.09), M_BLACK, bevel=0.008)
    cyl("HM_SpeakerCone" + nm, 0.035, 0.004, (MON_C.x + sx * 0.46, -0.838, DESK_Z + 0.10), M_ALU, rot=(math.radians(90), 0, 0))
# a soda can and a pen pot (true primary colours)
cyl("HM_Can", 0.033, 0.122, (0.52, -0.62, DESK_Z + 0.061), mat("M_CanRed", (0.75, 0.02, 0.03), rough=0.3, metal=0.6), bevel=0.003)
cyl("HM_PenPot", 0.04, 0.10, (-0.52, -0.85, DESK_Z + 0.05), mat("M_PotYellow", (0.95, 0.65, 0.02), rough=0.4))
# ---- gaming chair (seat height and back position set in 02 from the seated body; built here at a default)
def chair():
    parts = []
    parts.append(box("CH_Seat", (0.50, 0.50, 0.09), (0, 0, 0), M_CHAIR_K, bevel=0.03, segs=4))
    parts.append(box("CH_SeatSideL", (0.06, 0.50, 0.11), (0.25, 0, 0.02), M_CHAIR_R, bevel=0.025, segs=4))
    parts.append(box("CH_SeatSideR", (0.06, 0.50, 0.11), (-0.25, 0, 0.02), M_CHAIR_R, bevel=0.025, segs=4))
    parts.append(box("CH_Back", (0.50, 0.10, 0.78), (0, 0.30, 0.45), M_CHAIR_K, bevel=0.035, segs=4, rot=(math.radians(-8), 0, 0)))
    parts.append(box("CH_BackWingL", (0.07, 0.11, 0.74), (0.24, 0.29, 0.44), M_CHAIR_R, bevel=0.03, segs=4, rot=(math.radians(-8), 0, 0)))
    parts.append(box("CH_BackWingR", (0.07, 0.11, 0.74), (-0.24, 0.29, 0.44), M_CHAIR_R, bevel=0.03, segs=4, rot=(math.radians(-8), 0, 0)))
    parts.append(box("CH_Pillow", (0.30, 0.07, 0.13), (0, 0.26, 0.74), M_CHAIR_R, bevel=0.03, segs=4, rot=(math.radians(-8), 0, 0)))
    root = bpy.data.objects.new("HM_Chair", None); C_HOME.objects.link(root)
    for p in parts: p.parent = root
    # base: gas lift + 5 legs + casters (in a separate root that stays on the floor)
    base = bpy.data.objects.new("HM_ChairBase", None); C_HOME.objects.link(base)
    g = cyl("CH_Gas", 0.025, 0.30, (0, 0, 0.21), M_ALU); g.parent = base
    for k in range(5):
        a_ = 2 * math.pi * k / 5
        l_ = box("CH_Leg%d" % k, (0.30, 0.045, 0.035), (math.cos(a_) * 0.15, math.sin(a_) * 0.15, 0.075), M_BLACK, bevel=0.01, rot=(0, 0, a_))
        l_.parent = base
        c_ = cyl("CH_Caster%d" % k, 0.025, 0.03, (math.cos(a_) * 0.30, math.sin(a_) * 0.30, 0.025), M_BLACK, rot=(math.radians(90), 0, a_)); c_.parent = base
    return root, base
CHAIR, CHAIR_BASE = chair()
CHAIR.location = (0, 0.06, 0.45); CHAIR_BASE.location = (0, 0.12, 0.0)
# ---- back wall: shelf with books and a plant, two abstract canvases (no text), a framed colour poster
def canvas(name, loc, size, c1, c2, axis='Y'):
    o = box(name, (size[0], 0.03, size[1]), loc, mat(name + "_frame", (0.05, 0.05, 0.06), rough=0.4), bevel=0.004)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(loc[0], loc[1] - 0.017, loc[2]), rotation=(math.radians(90), 0, 0))
    p = bpy.context.active_object; p.name = name + "_art"; p.scale = (size[0] - 0.05, size[1] - 0.05, 1)
    m = mat(name + "_artm", c1, rough=0.6); nt = m.node_tree; pr = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); gr = nt.nodes.new("ShaderNodeTexGradient"); gr.gradient_type = 'SPHERICAL'
    cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.interpolation = 'CONSTANT'
    cr.color_ramp.elements[0].color = (*c1, 1); cr.color_ramp.elements[1].position = 0.35; cr.color_ramp.elements[1].color = (*c2, 1)
    nt.links.new(tc.outputs["Object"], gr.inputs["Vector"]); nt.links.new(gr.outputs["Fac"], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], pr.inputs["Base Color"])
    p.data.materials.append(m)
    if axis == 'Y_NEG':        # on the front wall, facing +Y
        o.rotation_euler.z = math.radians(180); p.rotation_euler.z = math.radians(180); p.location.y = loc[1] + 0.017
    return o
canvas("HM_ArtB", (-1.45, YB - 0.016, 1.55), (0.55, 0.70), (0.02, 0.75, 0.80), (0.98, 0.25, 0.55))
# the studio logo poster on the back wall (behind him, to his right): it reads in every front view
M_POSTER, _ = image_mat("M_LogoPoster", os.path.join(PKG, "assets/tex/logo_poster.png"), emit=0.25, rough=0.5)
box("HM_PosterFrame", (0.78, 0.025, 0.54), (-0.55, YB - 0.0125, 1.70), M_BLACK, bevel=0.004)
bpy.ops.mesh.primitive_plane_add(size=1, location=(-0.55, YB - 0.026, 1.70), rotation=(math.radians(90), 0, 0))
PST = bpy.context.active_object; PST.name = "HM_LogoPoster"; PST.scale = (0.72, 0.48, 1); bpy.ops.object.transform_apply(scale=True)
PST.data.materials.append(M_POSTER)
SHELF_Z = 1.10
box("HM_Shelf", (0.90, 0.24, 0.025), (0.85, YB - 0.12, SHELF_Z), mat("M_ShelfWhite", (0.92, 0.92, 0.90), rough=0.4), bevel=0.004)
for k, sx in enumerate((0.48, 1.22)):
    box("HM_ShelfBr%d" % k, (0.02, 0.20, 0.10), (sx, YB - 0.11, SHELF_Z - 0.06), M_BLACK, bevel=0.002)
# the poster where the ricochet lands is a plain plum wall area (no art damaged) at about (0.75, YB, 1.62)

# ---- Poly Haven assets (CC0)
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
BOOKS, _ = append_ph("decorative_book_set_01", "HM_Books", (1.00, YB - 0.12, SHELF_Z + 0.0125), rot_z=math.radians(180), scale=1.0)
PLANT_IN, _ = append_ph("potted_plant_02", "HM_PlantIn", (-1.75, 1.45, 0.0), scale=1.0)
TREE, _ = append_ph("island_tree_02", "EX_Tree", (6.5, 4.2, 0.0), scale=1.0)
SH1, _ = append_ph("shrub_01", "EX_Shrub1", (2.05, -1.6, 0.0), scale=0.9)
SH2, _ = append_ph("shrub_01", "EX_Shrub2", (2.05, 1.7, 0.0), rot_z=1.7, scale=0.85)
SH3, _ = append_ph("shrub_01", "EX_Shrub3", (2.1, -3.3, 0.0), rot_z=0.6, scale=1.0)

# ---- exterior: lawn, path, a white picket fence far back, the roof (tiles), gutters
box("EX_Lawn", (40.0, 40.0, 0.04), (WX_OUT + 20.0, 0.0, -0.02), M_LAWN, bevel=0.0)
box("EX_Path", (6.0, 1.0, 0.02), (WX_OUT + 3.0, -2.2, 0.005), mat("M_Path", (0.75, 0.72, 0.66), rough=0.8), bevel=0.0)
box("EX_Foundation", (0.06, 10.0, 0.30), (WX_OUT + 0.03, 0.0, 0.15), mat("M_Found", (0.55, 0.52, 0.50), rough=0.8), bevel=0.0)
for k in range(30):
    box("EX_Picket%02d" % k, (0.05, 0.09, 0.95), (13.0, -7.0 + k * 0.5, 0.47), M_TRIM, bevel=0.01)
box("EX_Rail1", (0.04, 15.0, 0.06), (12.97, 0.25, 0.30), M_TRIM, bevel=0.005)
box("EX_Rail2", (0.04, 15.0, 0.06), (12.97, 0.25, 0.75), M_TRIM, bevel=0.005)
# roof: a slope from the eave (x=WX_OUT+0.45, z=2.95) up to the ridge (x=-1.8, z=4.7), tiles, a fascia board and a gutter
def roof():
    x0, z0, x1, z1 = WX_OUT + 0.55, 2.92, -1.8, 4.7
    L = math.hypot(x0 - x1, z1 - z0); ang = math.atan2(z1 - z0, x0 - x1)
    o = box("EX_Roof", (L, 11.0, 0.06), ((x0 + x1) / 2, 0.0, (z0 + z1) / 2), M_ROOF, bevel=0.0, rot=(0, ang, 0))
    box("EX_Fascia", (0.03, 11.0, 0.18), (x0 + 0.01, 0.0, z0 - 0.06), M_TRIM, bevel=0.004)
    cyl("EX_Gutter", 0.06, 11.0, (x0 + 0.07, 0.0, z0 - 0.08), M_TRIM, rot=(math.radians(90), 0, 0))
    box("EX_Soffit", (0.60, 11.0, 0.02), (WX_OUT + 0.28, 0.0, 2.90), M_TRIM, bevel=0.0)
    return o
roof()
# a second window on the facade (further right) so the house reads as a house
for nm, yc in (("EX_Win2", 3.0), ("EX_Win3", -3.2)):
    box(nm + "_glass", (0.01, 1.0, 1.1), (WX_OUT + 0.004, yc, 1.55), mat(nm + "_m", (0.08, 0.14, 0.22), rough=0.08, coat=1.0), bevel=0.0)
    box(nm + "_frT", (0.03, 1.12, 0.06), (WX_OUT + 0.015, yc, 2.13), M_TRIM, bevel=0.004)
    box(nm + "_frB", (0.08, 1.16, 0.05), (WX_OUT + 0.03, yc, 0.98), M_TRIM, bevel=0.004)
    box(nm + "_frL", (0.03, 0.06, 1.12), (WX_OUT + 0.015, yc - 0.53, 1.55), M_TRIM, bevel=0.004)
    box(nm + "_frR", (0.03, 0.06, 1.12), (WX_OUT + 0.015, yc + 0.53, 1.55), M_TRIM, bevel=0.004)
    box(nm + "_shL", (0.03, 0.40, 1.15), (WX_OUT + 0.02, yc - 0.78, 1.55), mat(nm + "_sh", (0.02, 0.20, 0.55), rough=0.4), bevel=0.006)
    box(nm + "_shR", (0.03, 0.40, 1.15), (WX_OUT + 0.02, yc + 0.78, 1.55), bpy.data.materials[nm + "_sh"], bevel=0.006)
# blue shutters beside the hero window too
M_SHUT = mat("M_Shutter", (0.02, 0.20, 0.55), rough=0.4)
box("EX_ShutL", (0.03, 0.42, LH), (WX_OUT + 0.02, OPEN_Y[0] - 0.33, OPEN_Z[0] + LH / 2), M_SHUT, bevel=0.006)
box("EX_ShutR", (0.03, 0.42, LH), (WX_OUT + 0.02, OPEN_Y[1] + 0.33, OPEN_Z[0] + LH / 2), M_SHUT, bevel=0.006)
# flower bed under the window: red and yellow blooms (small spheres on stems)
box("EX_Bed", (0.45, 2.6, 0.12), (WX_OUT + 0.25, 0.0, 0.06), mat("M_Soil", (0.12, 0.06, 0.03), rough=0.95), bevel=0.01)
M_FL1 = mat("M_FlowerRed", (0.85, 0.02, 0.04), rough=0.5); M_FL2 = mat("M_FlowerYel", (0.98, 0.75, 0.02), rough=0.5)
M_STEM = mat("M_Stem", (0.05, 0.30, 0.03), rough=0.6)
rf = random.Random(9)
for k in range(46):
    p_ = Vector((WX_OUT + 0.08 + rf.uniform(0, 0.34), rf.uniform(-1.25, 1.25), 0.12))
    h_ = rf.uniform(0.18, 0.38)
    cyl("EX_Stem%02d" % k, 0.004, h_, p_ + Vector((0, 0, h_ / 2)), M_STEM, verts=6)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=rf.uniform(0.025, 0.04), segments=10, ring_count=6, location=p_ + Vector((0, 0, h_)))
    o = bpy.context.active_object; o.name = "EX_Bloom%02d" % k; o.data.materials.append(M_FL1 if k % 2 else M_FL2)
bpy.ops.object.select_all(action='DESELECT')
for o in bpy.data.objects:
    if o.name.startswith(("EX_Stem", "EX_Bloom")): o.select_set(True)
bpy.context.view_layer.objects.active = bpy.data.objects["EX_Stem00"]; bpy.ops.object.join(); bpy.context.active_object.name = "EX_Flowers"

HOME_OBJS = [o for o in sc.collection.objects if o.type in ('MESH', 'EMPTY', 'CURVE')]
for o in HOME_OBJS:
    to_col(o, C_HOME)

# ---- HOME lights
def light(name, kind, energy, loc, rot=(0, 0, 0), size=1.0, color=(1, 1, 1), c=C_HOME):
    L = bpy.data.lights.new(name, kind); L.energy = energy; L.color = color
    if kind == 'AREA': L.size = size; L.shape = 'DISK'
    if kind == 'SUN': L.angle = math.radians(3)
    o = bpy.data.objects.new(name, L); c.objects.link(o); o.location = loc; o.rotation_euler = rot
    return o
# the sun comes from outside, high, toward -X (through the window onto his left side)
light("HM_Sun", 'SUN', 4.0, (5, 0, 6), rot=(math.radians(50), 0, math.radians(75)), color=(1.0, 0.92, 0.78))
light("HM_MonitorGlow", 'AREA', 18, MON_C + Vector((0, 0.06, 0)), rot=(math.radians(-90), 0, 0), size=0.6, color=(0.75, 0.55, 1.0))
light("HM_RoomKey", 'AREA', 70, (0.9, -0.7, 2.3), rot=(math.radians(35), math.radians(25), 0), size=1.0, color=(1.0, 0.90, 0.80))
light("HM_RoomFill", 'AREA', 40, (-1.4, 0.2, 2.2), rot=(math.radians(40), math.radians(-40), 0), size=1.4, color=(0.70, 0.60, 1.0))
light("HM_BackRim", 'AREA', 60, (-0.5, 1.2, 2.1), rot=(math.radians(-45), 0, math.radians(200)), size=0.8, color=(1.0, 0.35, 0.80))
light("HM_WindowFill", 'AREA', 120, (WX_IN - 0.05, 0.0, 1.6), rot=(0, math.radians(-90), 0), size=1.0, color=(1.0, 0.95, 0.85))
light("EX_Fill", 'AREA', 600, (6.0, 0.0, 3.0), rot=(0, math.radians(-75), 0), size=4.0, color=(0.85, 0.92, 1.0))

# ================================================================== the headset (fitted to HIS head at rest; parented to the head in 02)
def eval_mesh_world(o, raw=False):
    saved = []
    if raw:
        for m in o.modifiers:
            if m.type in ('MASK', 'SUBSURF'): saved.append((m, m.show_viewport)); m.show_viewport = False
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get(); e = o.evaluated_get(dg); me = e.to_mesh(); Mw = o.matrix_world
    vs = [Mw @ v.co for v in me.vertices]; fs_ = [p.vertices[:] for p in me.polygons]; e.to_mesh_clear()
    for m, sv in saved: m.show_viewport = sv
    return vs, fs_
bpy.context.view_layer.update()
HAIR = [c for c in B.children if c.type == 'MESH' and "short02" in c.name][0]
bvs, bfs = eval_mesh_world(BB, raw=True); hvs, hfs = eval_mesh_world(HAIR)
_names = {b_.name for b_ in B.data.bones}; _i2n = {g.index: g.name for g in BB.vertex_groups if g.name in _names}
_headset = set()
for v in BB.data.vertices:
    bn_ = dom_bone(((g.group, g.weight) for g in v.groups), _i2n)
    if bn_ and not bn_.startswith(("neck", "spine", "clavicle", "shoulder", "upperarm", "breast", "pectoral")): _headset.add(v.index)
_hf = [f for f in bfs if all(i in _headset for i in f) and min(bvs[i].z for i in f) > 1.0]
BVH_B = BVHTree.FromPolygons(bvs, _hf); BVH_H = BVHTree.FromPolygons(hvs, hfs)
def ray_in(o, d):
    best = None
    for bv in (BVH_B, BVH_H):
        h = bv.ray_cast(Vector(o), Vector(d).normalized(), 2.0)
        if h[0] is not None and (best is None or h[3] < best[3]): best = h
    return best
# head-dominant vertices -> ear extremes
names = {b.name for b in B.data.bones}; i2n = {g.index: g.name for g in BB.vertex_groups if g.name in names}
headv = []
_hg = BB.vertex_groups["HelperGeometry"].index; _jc = BB.vertex_groups["JointCubes"].index
for v in BB.data.vertices:
    gs = {g.group: g.weight for g in v.groups}
    if gs.get(_hg, 0) > 0.5 or gs.get(_jc, 0) > 0.5: continue
    bn = dom_bone(((g.group, g.weight) for g in v.groups), i2n)
    if bn == "head" and bvs[v.index].x > 0: headv.append(bvs[v.index])
xs = [p.x for p in headv]; xmax = max(xs)
earL = [p for p in headv if p.x > xmax - 0.010]
EAR = Vector((0, sum(p.y for p in earL) / len(earL), sum(p.z for p in earL) / len(earL)))
EAR_OUT = xmax
HEAD_TOP = ray_in((0, EAR.y + 0.01, 3.0), (0, 0, -1))[0].z
# cushion contact plane: max x of skin/hair hit on a ring around the ear (radius 3.5-5 cm)
cx_ = 0.0
for rr in (0.036, 0.044, 0.050):
    for k in range(24):
        an = 2 * math.pi * k / 24
        o_ = Vector((0.4, EAR.y + rr * math.cos(an), EAR.z + 1.2 * rr * math.sin(an)))
        h = BVH_B.ray_cast(o_, Vector((-1, 0, 0)), 2.0)
        if h[0] is not None: cx_ = max(cx_, h[0].x)
X_C = cx_ + 0.002                       # cushion face 2 mm off the widest skin point on the ring (the hair there is pressed under it)                       # cushion face 3 mm off the widest skin/hair point on the ring
print("HEADFIT ear", tuple(round(x, 3) for x in EAR), "ear_out", round(EAR_OUT, 3), "cushion_x", round(X_C, 3), "top", round(HEAD_TOP, 3))
M_HS_SHELL = mat("M_HeadsetShell", (0.62, 0.02, 0.02), rough=0.22, coat=0.8)          # glossy red
M_HS_PAD = mat("M_HeadsetPad", (0.025, 0.022, 0.025), rough=0.6, sheen=0.3)           # black leatherette
M_HS_MET = mat("M_HeadsetMetal", (0.78, 0.79, 0.82), rough=0.25, metal=1.0)
def lathe(name, prof, material, segs=48, axis_x=True):
    """profile [(r, x)] revolved around the X axis (cup axis), centred at the origin"""
    bm = bmesh.new(); vs = [bm.verts.new((x, r, 0)) for r, x in prof]
    for a_, b_ in zip(vs, vs[1:]): bm.edges.new((a_, b_))
    bmesh.ops.spin(bm, geom=bm.verts[:] + bm.edges[:], angle=math.radians(360), steps=segs, axis=(1, 0, 0), cent=(0, 0, 0))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); C_HOME.objects.link(o); me.materials.append(material)
    for p in me.polygons: p.use_smooth = True
    return o
CUP_RO, CUP_RI, CUSH_T, SHELL_T = 0.043, 0.026, 0.020, 0.026       # outer radius, ear hole, cushion thickness, shell depth
X_BAFFLE = max(X_C + CUSH_T, EAR_OUT + 0.006)
CUSH_T = X_BAFFLE - X_C
def cup(side):
    sx = 1 if side == "L" else -1
    piv = bpy.data.objects.new("HS_CupPivot" + side, None); C_HOME.objects.link(piv)
    # cushion: a soft ring (torus-like profile) from the contact plane to the baffle
    prof = []
    for k in range(17):
        t = k / 16 * 2 * math.pi
        rm = (CUP_RO + CUP_RI) / 2; rr = (CUP_RO - CUP_RI) / 2
        prof.append((rm + rr * math.cos(t), CUSH_T / 2 + CUSH_T / 2 * 0.95 * math.sin(t)))
    cu = lathe("HS_Cushion" + side, prof, M_HS_PAD)
    cu.scale = (1, 1, 1.18)
    # shell: baffle plate + dome, depth SHELL_T, outer face slightly domed
    sp = [(0.0, CUSH_T - 0.001), (CUP_RO * 0.98, CUSH_T - 0.001), (CUP_RO * 1.02, CUSH_T + 0.004)]
    for k in range(1, 13):
        t = k / 12
        sp.append((CUP_RO * 1.02 * math.cos(t * math.pi / 2) ** 0.35, CUSH_T + 0.004 + (SHELL_T - 0.004) * math.sin(t * math.pi / 2)))
    sp.append((0.0, CUSH_T + SHELL_T))
    sh = lathe("HS_Shell" + side, sp, M_HS_SHELL)
    sh.scale = (1, 1, 1.18)
    ring = lathe("HS_Ring" + side, [(CUP_RO * 1.03, CUSH_T + 0.002), (CUP_RO * 1.045, CUSH_T + 0.006), (CUP_RO * 1.03, CUSH_T + 0.010)], M_HS_MET)
    ring.scale = (1, 1, 1.18)
    for o in (cu, sh, ring):
        if sx < 0: o.scale.x = -1
        o.location = (sx * X_C, EAR.y, EAR.z); o.parent = piv
        bpy.context.view_layer.update()
    return piv, cu, sh
# band: follows the hair/head contour (rays from the ear-line centre), 10 mm off the hair, from cup top to cup top
CEN = Vector((0, EAR.y, EAR.z))
pts = []
for k in range(41):
    th = math.radians(18 + 144 * k / 40)                        # 18..162 deg from +X through +Z
    d = Vector((math.cos(th), 0, math.sin(th)))
    h = ray_in(CEN + d * 0.5, -d)
    r_ = (h[0] - CEN).length if h else 0.11
    pts.append((th, r_ + 0.010))
# smooth the radius and make sure it clears the cups' top
for _ in range(3):
    pts = [(pts[i][0], max(pts[i][1], (pts[max(0, i - 1)][1] + pts[i][1] + pts[min(len(pts) - 1, i + 1)][1]) / 3)) for i in range(len(pts))]
BAND_W, BAND_T = 0.034, 0.012
def band(name, width, dn0, dn1, material, top_only=False):
    bm = bmesh.new(); rows = []
    # extend the ends down to the yoke (straight down to just above the cup top, outside the cushion plane)
    path = []
    xl = X_C + CUSH_T + 0.010; zt = EAR.z + CUP_RO * 1.18 + 0.010; zmax = HEAD_TOP + 0.010
    for k in range(49):                        # a superellipse from yoke top to yoke top, pushed out to 10 mm off the hair
        ph = math.pi * k / 48; c_, s_ = math.cos(ph), math.sin(ph)
        p = Vector((math.copysign(abs(c_) ** (2 / 2.6), c_) * xl, 0, zt + (zmax - zt) * abs(s_) ** (2 / 2.6)))
        d = Vector((p.x, 0, p.z - CEN.z)); dl = d.length; d.normalize()
        h = ray_in(CEN + d * 0.5 + Vector((0, EAR.y, 0)), -d)
        if h:
            rc = (Vector((h[0].x, 0, h[0].z - CEN.z))).length + 0.010
            if dl < rc: p = Vector((d.x * rc, 0, CEN.z + d.z * rc))
            pc = Vector((d.x * rc, 0, CEN.z + d.z * rc))
            w_ = max(0.0, min(1.0, (p.z - zt) / 0.05)); w_ = w_ * w_ * (3 - 2 * w_)
            p = p.lerp(pc, w_) if dl > rc else p
        path.append(p)
    for _ in range(2):
        path = [path[0]] + [(path[i - 1] + path[i] * 2 + path[i + 1]) / 4 for i in range(1, len(path) - 1)] + [path[-1]]
    for i, p in enumerate(path):
        tdir = (path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)]).normalized()
        nrm = Vector((0, 1, 0)).cross(tdir).normalized()          # points outward (away from the head)
        if nrm.dot(Vector((p.x, 0, p.z - CEN.z))) < 0: nrm = -nrm
        if top_only and p.z < EAR.z + 0.55 * (HEAD_TOP - EAR.z): continue
        row = []
        for dy, dn in ((-width / 2, dn0), (width / 2, dn0), (width / 2, dn1), (-width / 2, dn1)):
            row.append(bm.verts.new(p + Vector((0, EAR.y + dy, 0)) + nrm * dn))
        rows.append(row)
    for r0, r1 in zip(rows, rows[1:]):
        for j in range(4):
            bm.faces.new((r0[j], r0[(j + 1) % 4], r1[(j + 1) % 4], r1[j]))
    bm.faces.new(rows[0][::-1]); bm.faces.new(rows[-1])
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); C_HOME.objects.link(o); me.materials.append(material)
    bv = o.modifiers.new("bev", 'BEVEL'); bv.width = 0.003; bv.segments = 2
    sd = o.modifiers.new("sd", 'SUBSURF'); sd.levels = 1; sd.render_levels = 2
    for p in me.polygons: p.use_smooth = True
    return o, path
BAND, BPATH = band("HS_Band", BAND_W, 0.004, BAND_T, M_HS_MET)
# the padded underside (black leatherette), wider, under the top of the band, resting on the hair
PAD, _ = band("HS_BandPad", BAND_W + 0.010, -0.009, 0.0045, M_HS_PAD, top_only=True)
# yokes: a silver fork from each band end down around the cup sides
def yoke(side):
    sx = 1 if side == "L" else -1
    xm = sx * (X_C + CUSH_T + 0.010)
    cu = bpy.data.curves.new("HS_Yoke" + side, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.004; cu.bevel_resolution = 3
    spl = cu.splines.new('POLY'); n_ = 17; spl.points.add(n_ - 1)
    for k in range(n_):
        a_ = math.pi * k / (n_ - 1)
        spl.points[k].co = (xm, EAR.y + (CUP_RO + 0.008) * math.cos(a_), EAR.z + (CUP_RO * 1.18 + 0.008) * math.sin(a_), 1)
    o = bpy.data.objects.new("HS_Yoke" + side, cu); C_HOME.objects.link(o); cu.materials.append(M_HS_MET)
    return o
HS = bpy.data.objects.new("HS_Root", None); C_HOME.objects.link(HS); HS.location = CEN; HS.empty_display_size = 0.1
HS["rest_loc"] = tuple(CEN)
for o in (BAND, PAD):
    o.parent = HS; o.matrix_parent_inverse = Matrix.Translation(-CEN)
for side in "LR":
    piv, cu_, sh_ = cup(side)
    sx = 1 if side == "L" else -1
    # the pivot sits at the band end so the cup can swing outward a little when he pulls the headset off
    pv = Vector((sx * (X_C + CUSH_T + 0.010), EAR.y, EAR.z + CUP_RO * 1.18 + 0.010))
    bpy.context.view_layer.update()
    for ch in list(piv.children):
        mw = ch.matrix_world.copy(); ch.parent = None; ch.matrix_world = mw
    bpy.context.view_layer.update()
    piv.location = pv
    for ch in [o for o in bpy.data.objects if o.name.endswith(side) and o.name.startswith(("HS_Cushion", "HS_Shell", "HS_Ring"))]:
        ch.parent = piv; ch.matrix_parent_inverse = Matrix.Translation(-pv)
    y_ = yoke(side); y_.parent = piv; y_.matrix_parent_inverse = Matrix.Translation(-pv)
    piv.parent = HS; piv.matrix_parent_inverse = Matrix.Translation(-CEN)
bpy.context.view_layer.update()
# the impact point: centre of the left shell's outer face; crack decal + crater (shape key) + fragment chips
SHL = bpy.data.objects["HS_ShellL"]
CUP_HIT = Vector((X_C + CUSH_T + SHELL_T, EAR.y - 0.006, EAR.z + 0.010))
hb = BVHTree.FromPolygons(*eval_mesh_world(SHL)).ray_cast(CUP_HIT + Vector((0.05, 0, 0)), Vector((-1, 0, 0)), 0.2)
CUP_HIT = hb[0].copy(); CUP_N = hb[1].copy()
print("CUP_HIT", tuple(round(x, 4) for x in CUP_HIT))
# the crack decal: a cap cut from the shell's own outer surface around the hit (so it fits exactly), 0.7 mm proud
CK = SHL.copy(); CK.data = SHL.data.copy(); CK.name = "HS_CupCrack"; C_HOME.objects.link(CK); CK.data.name = "HS_CupCrack"
bm = bmesh.new(); bm.from_mesh(CK.data); Mw = SHL.matrix_world
bmesh.ops.delete(bm, geom=[v for v in bm.verts if ((Mw @ v.co) - CUP_HIT).length > 0.034], context='VERTS')
bmesh.ops.delete(bm, geom=[f for f in bm.faces if (Mw @ f.calc_center_median()).x < CUP_HIT.x - 0.010], context='FACES')
bmesh.ops.reverse_faces(bm, faces=[f for f in bm.faces if (Mw.to_3x3() @ f.normal).x < 0])
Rk = Vector((1, 0, 0)).rotation_difference(Vector((0, 0, 1))).to_matrix().to_4x4()       # world X -> local Z
Tk = Rk @ Matrix.Translation(-CUP_HIT) @ Mw
bmesh.ops.transform(bm, matrix=Tk, verts=bm.verts)
bm.to_mesh(CK.data); bm.free()
CK.parent = None; CK.matrix_world = Matrix.Translation(CUP_HIT) @ Rk.inverted()
CK.data.materials.clear(); CK.data.materials.append(crack_mat("M_CupCrack", hole_r=0.0045, ring=70.0, white=(0.95, 0.80, 0.80), emit=0.15, metal_core=True))
dsp = CK.modifiers.new("proud", 'DISPLACE'); dsp.strength = 0.0007; dsp.mid_level = 0.0; dsp.direction = 'NORMAL'
bpy.context.view_layer.update()
CK.parent = SHL; CK.matrix_parent_inverse = SHL.matrix_world.inverted()
# crater: a shape key on the shell pushing the faces around the hit inward 4 mm (radius 12 mm)
SHL.shape_key_add(name="Basis"); kc = SHL.shape_key_add(name="crater"); kc.value = 0.0
Minv = SHL.matrix_world.inverted()
for v in SHL.data.vertices:
    pw = SHL.matrix_world @ v.co; d_ = (pw - CUP_HIT).length
    if d_ < 0.013 and pw.x > CUP_HIT.x - 0.006:
        w_ = 0.5 * (1 + math.cos(math.pi * d_ / 0.013))
        kc.data[v.index].co = Minv @ (pw - CUP_N * 0.004 * w_)
CK.shape_key_add(name="Basis"); kk = CK.shape_key_add(name="crater"); kk.value = 0.0
Rk3 = Rk.to_3x3()
for v in CK.data.vertices:
    pw = CK.matrix_world @ v.co; d_ = (pw - CUP_HIT).length
    if d_ < 0.013:
        w_ = 0.5 * (1 + math.cos(math.pi * d_ / 0.013))
        kk.data[v.index].co = v.co + Rk3 @ (-CUP_N * 0.004 * w_)
# shell fragments (14 red chips), placed at the hit; animated in 02
CHIPS = []
for k in range(14):
    bm = bmesh.new(); n = rs.choice((3, 4, 5)); r_ = rs.uniform(0.002, 0.005)
    vs = [bm.verts.new((0.0, r_ * math.cos(2 * math.pi * i / n) * rs.uniform(0.6, 1.3), r_ * math.sin(2 * math.pi * i / n) * rs.uniform(0.6, 1.3))) for i in range(n)]
    bm.faces.new(vs); me = bpy.data.meshes.new("Chip%02d" % k); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("HS_Chip%02d" % k, me); C_HOME.objects.link(o)
    so = o.modifiers.new("so", 'SOLIDIFY'); so.thickness = 0.0015; me.materials.append(M_HS_SHELL); CHIPS.append(o)
    o.location = CUP_HIT

# ================================================================== the bullet (ONE object for the whole film)
def bullet():
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
    m = mat("M_Bullet", (0.92, 0.40, 0.14), rough=0.36, metal=0.85, coat=0.15)
    nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); wv = nt.nodes.new("ShaderNodeTexWave"); wv.wave_type = 'RINGS'
    wv.inputs["Scale"].default_value = 900.0; wv.inputs["Distortion"].default_value = 0.5
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.08; bp.inputs["Distance"].default_value = 0.0001
    nt.links.new(tc.outputs["Object"], wv.inputs["Vector"]); nt.links.new(wv.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], p.inputs["Normal"])
    me.materials.append(m)
    o.modifiers.new("ws", 'WEIGHTED_NORMAL')
    return o
BUL = bullet()
TIP = bpy.data.objects.new("TipCtl", None); sc.collection.objects.link(TIP); TIP.parent = BUL; TIP.location = (0, 0, 0.0155)
TIP.empty_display_size = 0.003
bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=0.0040, radius2=0.0002, depth=1.0, location=(0, 0, -0.5), rotation=(math.radians(180), 0, 0))
TRAIL = bpy.context.active_object; TRAIL.name = "BulletTrail"
bpy.ops.object.transform_apply(location=True, rotation=True)
TRAIL.parent = BUL
tm = bpy.data.materials.new("M_Trail"); tm.use_nodes = True; nt = tm.node_tree
for n in list(nt.nodes):
    if n.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n)
tcn = nt.nodes.new("ShaderNodeTexCoord"); sp = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tcn.outputs["Generated"], sp.inputs[0])
mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["To Max"].default_value = 0.55; nt.links.new(sp.outputs["Z"], mr.inputs["Value"])
tr = nt.nodes.new("ShaderNodeBsdfTransparent"); em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (1.0, 0.95, 0.85, 1); em.inputs["Strength"].default_value = 1.2
mx = nt.nodes.new("ShaderNodeMixShader"); nt.links.new(mr.outputs[0], mx.inputs["Fac"]); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2])
nt.links.new(mx.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
TRAIL.data.materials.append(tm)
TRAIL.visible_shadow = False; TRAIL.visible_diffuse = False; TRAIL.visible_glossy = False
# sparks (24 short glowing streaks) used at the cup hit, the metal hit (macro) and the wall hit; animated in 02
M_SPARK = mat("M_Spark", (1.0, 0.7, 0.2), emit=((1.0, 0.62, 0.15), 25.0))
for k in range(24):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.0006, depth=0.012, vertices=6, location=(0, 0, 0))
    o = bpy.context.active_object; o.name = "FX_Spark%02d" % k; o.data.materials.append(M_SPARK)
    o.visible_shadow = False
    to_col(o, sc.collection)
# the wall hit: a hole decal on the back wall (dark hole, cracked plaster ring) + plaster chips
WALL_HIT = Vector((0.85, YB - 0.001, 1.40))
bpy.ops.mesh.primitive_circle_add(vertices=48, radius=0.06, fill_type='NGON', location=(0, 0, 0), rotation=(math.radians(90), 0, 0))
WH = bpy.context.active_object; WH.name = "HM_WallHole"
WH.data.materials.append(crack_mat("M_WallHole", hole_r=0.006, ring=60.0, white=(0.75, 0.72, 0.85), emit=0.0, metal_core=True))
WH.location = WALL_HIT; WH.scale = (0.001,) * 3; to_col(WH, C_HOME)
M_PLASTER = mat("M_PlasterChip", (0.85, 0.83, 0.88), rough=0.9)
for k in range(10):
    bpy.ops.mesh.primitive_ico_sphere_add(radius=0.004, subdivisions=1, location=WALL_HIT)
    o = bpy.context.active_object; o.name = "HM_PlasterChip%02d" % k; o.data.materials.append(M_PLASTER); to_col(o, C_HOME)

# ================================================================== MACRO set: the left ear cup in cross-section (real scale)
# depths below the shell's outer face (m): shell 3 mm, padding foam 14 mm, metal frame 2.5 mm, cushion 12 mm
Z_SHELL, Z_FOAM, Z_MET, Z_CUSH = -0.0030, -0.0170, -0.0195, -0.0320
XW, ZB = 0.075, -0.034
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
CUT = grid("MC_CutFace", -XW, XW, ZB, 0.0, 0.0005); CUT.location = MX
TOPG = grid("MC_TopShell", -XW, XW, 0.0, 0.06, 0.0006)
TOPG.data.transform(Matrix.Rotation(math.radians(90), 4, 'X'))
for v in TOPG.data.vertices: v.co.y = abs(v.co.y)
TOPG.location = MX
SLAB = box("MC_Slab", (2 * XW, 0.058, -ZB), (MX.x, 0.0295, ZB / 2), mat("M_SlabSide", (0.30, 0.01, 0.01), rough=0.4), bevel=0.0)
to_col(SLAB, C_MACRO)
def layers_mat():
    m = bpy.data.materials.new("M_CupLayers"); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n)
    out = nt.nodes["Material Output"]
    at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_name = "opos"
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(at.outputs["Vector"], sep.inputs[0])
    trk = nt.nodes.new("ShaderNodeAttribute"); trk.attribute_name = "track"
    sq = nt.nodes.new("ShaderNodeAttribute"); sq.attribute_name = "squeeze"
    Z = sep.outputs["Z"]
    def band_(lo, hi):
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
    # foam: open-cell look (voronoi cells, deep teal-blue with dark pores)
    vo = nt.nodes.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 900.0; vo.inputs["Randomness"].default_value = 1.0
    nt.links.new(at.outputs["Vector"], vo.inputs["Vector"])
    pore = nt.nodes.new("ShaderNodeMapRange"); pore.inputs["From Min"].default_value = 0.10; pore.inputs["From Max"].default_value = 0.35
    nt.links.new(vo.outputs["Distance"], pore.inputs["Value"])
    foam_c = mix(pore.outputs["Result"], (0.01, 0.05, 0.12), (0.02, 0.35, 0.80))
    # cushion: soft grey memory foam (finer cells) under a black leatherette skin at the bottom
    vo2 = nt.nodes.new("ShaderNodeTexVoronoi"); vo2.inputs["Scale"].default_value = 1500.0
    nt.links.new(at.outputs["Vector"], vo2.inputs["Vector"])
    cush_c = mix(vo2.outputs["Distance"], (0.25, 0.22, 0.30), (0.55, 0.52, 0.60))
    # shell: glossy red plastic; metal: brushed steel (fine stripes)
    wv = nt.nodes.new("ShaderNodeTexWave"); wv.bands_direction = 'X'; wv.inputs["Scale"].default_value = 4000.0
    nt.links.new(at.outputs["Vector"], wv.inputs["Vector"])
    met_c = mix(wv.outputs["Fac"], (0.62, 0.63, 0.66), (0.85, 0.86, 0.90))
    c = mix(band_(-1.0, Z_CUSH + 0.0012), (0.02, 0.02, 0.02), (0.02, 0.02, 0.02))
    c = mix(band_(Z_CUSH + 0.0012, Z_MET), c, cush_c)
    c = mix(band_(Z_MET, Z_FOAM), c, met_c)
    c = mix(band_(Z_FOAM, Z_SHELL), c, foam_c)
    c = mix(band_(Z_SHELL, 1.0), c, (0.62, 0.02, 0.02))
    c = mix(sq.outputs["Fac"], c, (0.01, 0.12, 0.40))           # compressed foam is darker and denser
    c = mix(trk.outputs["Fac"], c, (0.03, 0.03, 0.05))
    p = nt.nodes.new("ShaderNodeBsdfPrincipled"); nt.links.new(c, p.inputs["Base Color"])
    ismet = band_(Z_MET, Z_FOAM)
    nt.links.new(mixf(ismet, 0.0, 1.0), p.inputs["Metallic"])
    nt.links.new(mixf(band_(Z_SHELL, 1.0), mixf(ismet, 0.65, 0.28), 0.18), p.inputs["Roughness"])
    p.inputs["Coat Weight"].default_value = 0.2
    nt.links.new(p.outputs[0], out.inputs["Surface"])
    return m
M_LAYERS = layers_mat()
CUT.data.materials.append(M_LAYERS)
M_TOPSH = mat("M_TopShell", (0.62, 0.02, 0.02), rough=0.2, coat=0.8)
TOPG.data.materials.append(M_TOPSH)
# WoundCtl: keyed location carries the state (no drivers, no clock): x = squeeze energy 0..1, y = track bottom z (local),
# z = entry 0..1 (shell broken: opens the hole in the top shell)
WCTL = bpy.data.objects.new("WoundCtl", None); C_MACRO.objects.link(WCTL); WCTL.empty_display_size = 0.01
def wound_gn(name, is_top):
    ng = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    ng.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    N = ng.nodes; L = ng.links
    gi = N.new("NodeGroupInput"); go = N.new("NodeGroupOutput")
    pos = N.new("GeometryNodeInputPosition")
    st = N.new("GeometryNodeStoreNamedAttribute"); st.data_type = 'FLOAT_VECTOR'; st.domain = 'POINT'; st.inputs["Name"].default_value = "opos"
    L.new(gi.outputs[0], st.inputs["Geometry"]); L.new(pos.outputs[0], st.inputs["Value"])
    oi = N.new("GeometryNodeObjectInfo"); oi.inputs["Object"].default_value = TIP; oi.transform_space = 'ORIGINAL'
    tip_l = N.new("ShaderNodeVectorMath"); tip_l.operation = 'SUBTRACT'; L.new(oi.outputs["Location"], tip_l.inputs[0]); tip_l.inputs[1].default_value = tuple(MX)
    tsep = N.new("ShaderNodeSeparateXYZ"); L.new(tip_l.outputs[0], tsep.inputs[0])
    psep = N.new("ShaderNodeSeparateXYZ"); L.new(pos.outputs[0], psep.inputs[0])
    def math_(op, a_, b_=None):
        m_ = N.new("ShaderNodeMath"); m_.operation = op
        for i_, x in enumerate((a_, b_)):
            if x is None: continue
            if isinstance(x, (int, float)): m_.inputs[i_].default_value = float(x)
            else: L.new(x, m_.inputs[i_])
        return m_.outputs[0]
    wc = N.new("GeometryNodeObjectInfo"); wc.inputs["Object"].default_value = WCTL; wc.transform_space = 'ORIGINAL'
    wsep = N.new("ShaderNodeSeparateXYZ"); L.new(wc.outputs["Location"], wsep.inputs[0])
    en, tb, ent = wsep.outputs["X"], wsep.outputs["Y"], wsep.outputs["Z"]
    R0 = 0.0045
    tx, zn = tsep.outputs["X"], tsep.outputs["Z"]
    x = psep.outputs["X"]; y = psep.outputs["Y"]; z = psep.outputs["Z"]
    if not is_top:
        ax = math_('ABSOLUTE', x)
        # track: from the keyed bottom (tb) up to the top, a half-cylinder groove pushed +y; nose ogive at the bottom
        above = math_('GREATER_THAN', z, tb)
        inside_r = math_('LESS_THAN', ax, R0 * 1.05)
        xr = math_('DIVIDE', ax, R0); one_m = math_('MAXIMUM', math_('SUBTRACT', 1.0, math_('MULTIPLY', xr, xr)), 0.0)
        prof = math_('SQRT', one_m)
        dz = math_('SUBTRACT', z, tb)
        nz_r = N.new("ShaderNodeMapRange"); nz_r.inputs["From Min"].default_value = 0.0; nz_r.inputs["From Max"].default_value = 0.006
        nz_r.inputs["To Min"].default_value = 0.25; nz_r.inputs["To Max"].default_value = 1.0; L.new(dz, nz_r.inputs["Value"])
        depth = math_('MULTIPLY', prof, nz_r.outputs["Result"])
        gate = math_('MULTIPLY', math_('MULTIPLY', above, inside_r), math_('LESS_THAN', z, 0.0))
        gy = math_('MULTIPLY', math_('MULTIPLY', depth, gate), R0)
        # squeeze ahead of the nose (only in the foam band: strong; metal: 15 %), down + sideways, bulging to -y
        dx_ = math_('SUBTRACT', x, tx); dzn = math_('SUBTRACT', z, zn)
        dist = math_('SQRT', math_('ADD', math_('MULTIPLY', dx_, dx_), math_('MULTIPLY', dzn, dzn)))
        fall = math_('EXPONENT', math_('MULTIPLY', dist, -1.0 / 0.0050))
        below = math_('LESS_THAN', z, math_('ADD', zn, 0.002))
        infoam = math_('MULTIPLY', math_('GREATER_THAN', z, Z_FOAM), math_('LESS_THAN', z, Z_SHELL))
        inmet = math_('MULTIPLY', math_('GREATER_THAN', z, Z_MET - 0.0005), math_('LESS_THAN', z, Z_FOAM + 0.0002))
        lay = math_('ADD', infoam, math_('MULTIPLY', inmet, 0.15))
        sq = math_('MULTIPLY', math_('MULTIPLY', math_('MULTIPLY', fall, below), en), lay)
        push = math_('MULTIPLY', sq, 0.0035)
        dirx = math_('DIVIDE', dx_, math_('ADD', dist, 1e-5)); dirz = math_('DIVIDE', dzn, math_('ADD', dist, 1e-5))
        offx = math_('MULTIPLY', dirx, push); offz = math_('MULTIPLY', dirz, push)
        offy = math_('MULTIPLY', sq, -0.0010)
        oy = math_('ADD', gy, offy)
        off = N.new("ShaderNodeCombineXYZ"); L.new(offx, off.inputs[0]); L.new(oy, off.inputs[1]); L.new(offz, off.inputs[2])
        sp = N.new("GeometryNodeSetPosition"); L.new(st.outputs[0], sp.inputs["Geometry"]); L.new(off.outputs[0], sp.inputs["Offset"])
        s1 = N.new("GeometryNodeStoreNamedAttribute"); s1.data_type = 'FLOAT'; s1.inputs["Name"].default_value = "track"
        L.new(sp.outputs[0], s1.inputs["Geometry"]); L.new(math_('MULTIPLY', gate, math_('GREATER_THAN', prof, 0.02)), s1.inputs["Value"])
        s2 = N.new("GeometryNodeStoreNamedAttribute"); s2.data_type = 'FLOAT'; s2.inputs["Name"].default_value = "squeeze"
        L.new(s1.outputs[0], s2.inputs["Geometry"]); L.new(math_('MINIMUM', math_('MULTIPLY', sq, 1.6), 1.0), s2.inputs["Value"])
        L.new(s2.outputs[0], go.inputs[0])
    else:
        r = math_('SQRT', math_('ADD', math_('MULTIPLY', x, x), math_('MULTIPLY', y, y)))
        dimple = math_('MINIMUM', zn, 0.0)
        fall = math_('EXPONENT', math_('MULTIPLY', r, -1.0 / 0.006))
        dz_ = math_('MAXIMUM', math_('MULTIPLY', math_('MULTIPLY', dimple, fall), math_('SUBTRACT', 1.0, ent)), -0.003)
        off = N.new("ShaderNodeCombineXYZ"); L.new(dz_, off.inputs[2])
        sp = N.new("GeometryNodeSetPosition"); L.new(st.outputs[0], sp.inputs["Geometry"]); L.new(off.outputs[0], sp.inputs["Offset"])
        hole = math_('MULTIPLY', math_('LESS_THAN', r, R0 * 1.15), ent)
        dl = N.new("GeometryNodeDeleteGeometry"); dl.domain = 'POINT'; L.new(sp.outputs[0], dl.inputs["Geometry"]); L.new(math_('GREATER_THAN', hole, 0.5), dl.inputs["Selection"])
        L.new(dl.outputs[0], go.inputs[0])
    return ng
for o, top in ((CUT, False), (TOPG, True)):
    md = o.modifiers.new("Wound", 'NODES'); md.node_group = wound_gn("GN_Wound_" + ("top" if top else "cut"), top)
# a crack star on the top shell around the entry (scaled up when the shell breaks)
bpy.ops.mesh.primitive_circle_add(vertices=64, radius=0.03, fill_type='NGON', location=MX + Vector((0, 0.0, 0.0002)))
MCK = bpy.context.active_object; MCK.name = "MC_ShellCrack"
bm = bmesh.new(); bm.from_mesh(MCK.data); bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, 0), plane_no=(0, 1, 0), clear_inner=True)
bm.to_mesh(MCK.data); bm.free(); MCK.data.materials.append(crack_mat("M_MacroCrack", hole_r=0.0001, ring=70.0, white=(1.0, 0.85, 0.85), emit=0.1))
MCK.scale = (0.001,) * 3; to_col(MCK, C_MACRO)
# backdrop: the explainer sky (deep blue to cyan), far behind
bpy.ops.mesh.primitive_plane_add(size=1, location=MX + Vector((0, 0.25, 0.0)), rotation=(math.radians(90), 0, 0))
BD = bpy.context.active_object; BD.name = "MC_Backdrop"; BD.scale = (1.0, 0.7, 1)
bdm = bpy.data.materials.new("M_Backdrop"); bdm.use_nodes = True; nt = bdm.node_tree
for n in list(nt.nodes):
    if n.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n)
tcb = nt.nodes.new("ShaderNodeTexCoord"); spb = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tcb.outputs["Generated"], spb.inputs[0])
crb = nt.nodes.new("ShaderNodeValToRGB"); crb.color_ramp.elements[0].color = (0.02, 0.10, 0.45, 1); crb.color_ramp.elements[1].color = (0.20, 0.72, 0.98, 1)
nt.links.new(spb.outputs["Y"], crb.inputs["Fac"])
emb = nt.nodes.new("ShaderNodeEmission"); nt.links.new(crb.outputs["Color"], emb.inputs["Color"])
nt.links.new(emb.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
BD.data.materials.append(bdm); to_col(BD, C_MACRO)
light("MC_Key", 'AREA', 0.9, MX + Vector((-0.08, -0.15, 0.09)), rot=(math.radians(62), 0, math.radians(-28)), size=0.10, color=(1.0, 0.96, 0.92), c=C_MACRO)
light("MC_Fill", 'AREA', 0.6, MX + Vector((0.12, -0.14, -0.02)), rot=(math.radians(85), 0, math.radians(40)), size=0.12, color=(0.90, 0.95, 1.0), c=C_MACRO)
light("MC_Top", 'AREA', 0.5, MX + Vector((0.0, 0.03, 0.10)), rot=(0, 0, 0), size=0.08, color=(1.0, 0.90, 0.80), c=C_MACRO)

# ================================================================== look and render settings
sc.render.engine = 'CYCLES'; cy = sc.cycles
cy.samples = 64; cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.05
cy.use_denoising = True; cy.denoiser = 'OPENIMAGEDENOISE'
cy.max_bounces = 6; cy.diffuse_bounces = 3; cy.glossy_bounces = 3; cy.transmission_bounces = 6; cy.transparent_max_bounces = 16
cy.caustics_reflective = False; cy.caustics_refractive = False
sc.render.use_persistent_data = True
sc.render.use_simplify = True; sc.render.simplify_subdivision_render = 2; cy.texture_limit_render = '2048'
sc.render.use_motion_blur = False
sc.view_settings.view_transform = 'Filmic'; sc.view_settings.look = 'High Contrast'; sc.view_settings.exposure = -0.4
sc.world = sc.world or bpy.data.worlds.new("World")
w = sc.world; w.use_nodes = True; nt = w.node_tree
for n in list(nt.nodes):
    if n.type != 'OUTPUT_WORLD': nt.nodes.remove(n)
tc = nt.nodes.new("ShaderNodeTexCoord"); sp = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Generated"], sp.inputs[0])
mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.5; mr.inputs["From Max"].default_value = 0.75; nt.links.new(sp.outputs["Z"], mr.inputs["Value"])
cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (0.55, 0.82, 1.0, 1); cr.color_ramp.elements[1].color = (0.05, 0.38, 0.95, 1)
nt.links.new(mr.outputs["Result"], cr.inputs["Fac"])
bg = nt.nodes.new("ShaderNodeBackground"); bg.inputs["Strength"].default_value = 1.0; nt.links.new(cr.outputs["Color"], bg.inputs["Color"])
nt.links.new(bg.outputs[0], [n for n in nt.nodes if n.type == 'OUTPUT_WORLD'][0].inputs["Surface"])
for o in list(sc.collection.objects):
    if o.name.startswith(("HS_", "HM_", "EX_")): to_col(o, C_HOME)
for o in bpy.data.objects:
    if o.parent and o.parent.name.startswith(("HM_", "EX_")) and o.users_collection and o.users_collection[0] == sc.collection:
        to_col(o, C_HOME)
# every object still in the startup 'Collection' goes to its set (HOME / MACRO); the bullet, its trail and sparks stay global
dc = bpy.data.collections.get("Collection")
if dc:
    for o in list(dc.objects):
        if o.name in ("Bullet", "TipCtl", "BulletTrail") or o.name.startswith("FX_"): to_col(o, sc.collection)
        elif o.name.startswith("MC_"): to_col(o, C_MACRO)
        else: to_col(o, C_HOME)
    bpy.data.collections.remove(dc)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("BUILD_DONE", OUT)
