"""DwarfGiant v009 stage A (from scratch): one recruiting office, two men, one continuous camera.
blender -b --python 01_build.py -- <brain_src.blend> <out.blend>

World layout (metres, floor z=0): the HERO stands at the origin facing -Y (his rig is never moved: he grows by the rig
object's scale, so his feet stay planted on the floor). The OFFICER stands at (0.95, -0.30) turned toward him.
Back wall inner face y=0.42: the measuring rod right behind the hero, the DA KRAS FILMS plaque and (later) the framed
photo at x=-0.78, the door at x=-2.0..-1.1, the flag at x=0.45..1.15 high up, the window at x=1.3..2.2.
The hero carries an x-ray look (a keyed mix in each of his materials, value node 'XR'), a brain with the pituitary
gland (tumour) parented to his head bone, and a chain of vertebrae parented to his spine bones."""
import bpy, bmesh, sys, math, random, os
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "lib_build.py")).read())
a = sys.argv[sys.argv.index("--") + 1:]
BRAIN_SRC, OUT = a[0], a[1]
PKG = os.path.dirname(HERE)
random.seed(26)
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
sc = bpy.context.scene
sc.render.fps = 60
sc.frame_start, sc.frame_end = 1, 2083
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
WALL_Y = 0.42

def solidify_clothes(rig):
    for c in rig.children:
        if c.type == 'MESH' and any(k in c.name for k in ("suit", "shoes")):
            so = c.modifiers.new("solid", 'SOLIDIFY'); so.thickness = 0.003; so.offset = 1.0; so.use_rim = True
            i = c.modifiers.find("solid")
            while i > c.modifiers.find("Armature") + 1:
                c.modifiers.move(i, i - 1); i -= 1

def retex(rig, key, path, nstr=0.4):
    im = bpy.data.images.load(path); im.name = os.path.basename(path)
    for c in rig.children:
        if c.type == 'MESH' and key in c.name:
            for m in c.data.materials:
                for nd in m.node_tree.nodes:
                    if nd.type == 'TEX_IMAGE' and nd.image and "diffuse" in nd.image.name.lower(): nd.image = im
                    if nd.type == 'NORMAL_MAP': nd.inputs["Strength"].default_value = nstr

def dark_eyes():
    for o in bpy.data.objects:
        if o.type == 'MESH' and "high-poly" in o.name:
            for m in o.data.materials:
                for n in m.node_tree.nodes:
                    if n.type == 'GROUP' and "IrisMajorColor" in n.inputs:
                        n.inputs["IrisMajorColor"].default_value = (0.16, 0.08, 0.03, 1); n.inputs["IrisMinorColor"].default_value = (0.06, 0.03, 0.01, 1)

# ================================================================== the two men (ONE model each, all film)
HERO, HB = human("Hero", 1.0, 0.5, {"asian": 0.0, "caucasian": 0.95, "african": 0.05}, "short02/short02.mhclo",
                 "young_caucasian_male/young_caucasian_male.mhmat", "eyebrow001/eyebrow001.mhclo",
                 height=0.2, weight=0.45, muscle=0.5, prop=0.5,
                 clothes=["male_worksuit01/male_worksuit01.mhclo", "shoes02/shoes02.mhclo"])
OFF, OB = human("Officer", 1.0, 0.62, {"asian": 0.0, "caucasian": 0.9, "african": 0.1}, "short01/short01.mhclo",
                "middleage_caucasian_male/middleage_caucasian_male.mhmat", "eyebrow007/eyebrow007.mhclo",
                height=0.62, weight=0.6, muscle=0.55, prop=0.6,
                clothes=["male_elegantsuit01/male_elegantsuit01.mhclo", "shoes03/shoes03.mhclo"])
eye_fix(HERO); eye_fix(OFF); eye_group_fix()
EG = bpy.data.node_groups.get("EnhancedEye")
for n in (EG.nodes if EG else []):
    if n.type == 'MATH' and abs(n.inputs[1].default_value - 0.92) < 1e-4: n.inputs[1].default_value = 0.96
dark_eyes()
for rig, hair_t in ((HERO, (0.30, 0.18, 0.09)), (OFF, (0.22, 0.17, 0.14))):
    for c in rig.children:
        if c.type == 'MESH' and any(k in c.name.lower() for k in ("short0", "eyebrow")):
            for m in c.data.materials: tint(m, hair_t)
        if c.type == 'MESH' and "teeth" in c.name:
            for m in c.data.materials: tint(m, (1.5, 1.45, 1.4))
for m in HB.data.materials: tint(m, (1.0, 0.86, 0.78))
for m in OB.data.materials: tint(m, (0.95, 0.80, 0.70))
retex(HERO, "worksuit", os.path.join(PKG, "assets/tex/hero_overalls_diffuse.png"))
retex(OFF, "elegantsuit", os.path.join(PKG, "assets/tex/officer_uniform_diffuse.png"))
solidify_clothes(HERO); solidify_clothes(OFF)
# rest heights (the hero is scaled to 1.37 m in stage B, the officer to 1.80 m)
def top_z(body):
    dg = bpy.context.evaluated_depsgraph_get(); e = body.evaluated_get(dg); me = e.to_mesh()
    z = max((body.matrix_world @ v.co).z for v in me.vertices); e.to_mesh_clear(); return z
bpy.context.view_layer.update()
HERO["rest_height"] = top_z(HB); OFF["rest_height"] = top_z(OB)
print("HEIGHTS", HERO["rest_height"], OFF["rest_height"])

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
def wood(name, c1, c2, scale=3.0, rough=0.4, stretch=(1, 10, 1)):
    m = mat(name, c1, rough=rough, coat=0.25)
    nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = stretch
    wv = nt.nodes.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = scale; wv.inputs["Distortion"].default_value = 6.0
    wv.inputs["Detail"].default_value = 3.0
    cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (*c1, 1); cr.color_ramp.elements[1].color = (*c2, 1)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"]); nt.links.new(mp.outputs["Vector"], wv.inputs["Vector"])
    nt.links.new(wv.outputs["Fac"], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], p.inputs["Base Color"])
    return m
def parquet(name):
    """herringbone-ish parquet: brick texture of narrow planks with per-plank tone + grain"""
    m = mat(name, (0.35, 0.14, 0.05), rough=0.35, coat=0.35)
    nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); br = nt.nodes.new("ShaderNodeTexBrick"); br.offset = 0.5
    br.inputs["Scale"].default_value = 1.0; br.inputs["Brick Width"].default_value = 0.60; br.inputs["Row Height"].default_value = 0.10
    br.inputs["Mortar Size"].default_value = 0.002
    br.inputs["Color1"].default_value = (0.36, 0.13, 0.04, 1); br.inputs["Color2"].default_value = (0.48, 0.20, 0.07, 1)
    br.inputs["Mortar"].default_value = (0.08, 0.03, 0.01, 1)
    nt.links.new(tc.outputs["Object"], br.inputs["Vector"])
    wv = nt.nodes.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = 30.0; wv.inputs["Distortion"].default_value = 8.0
    nt.links.new(tc.outputs["Object"], wv.inputs["Vector"])
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs["Factor"].default_value = 0.35
    nt.links.new(br.outputs["Color"], mx.inputs["A"]); nt.links.new(wv.outputs["Color"], mx.inputs["B"])
    nt.links.new(mx.outputs["Result"], p.inputs["Base Color"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.25; bp.inputs["Distance"].default_value = 0.001
    nt.links.new(br.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], p.inputs["Normal"])
    return m
def img_mat(name, path, rough=0.35, coat=0.3):
    m = mat(name, (1, 1, 1), rough=rough, coat=coat); nt = m.node_tree
    tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = bpy.data.images.load(path); tx.extension = 'CLIP'
    nt.links.new(tx.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
    return m, tx

M_WALL = plaster("M_Wall", (0.020, 0.22, 0.20), (0.030, 0.30, 0.27), scale=8.0)          # deep green-teal plaster
M_WAINS = wood("M_Wainscot", (0.26, 0.025, 0.02), (0.34, 0.04, 0.03), scale=2.0, rough=0.35)   # oxblood panels
M_TRIM = mat("M_Trim", (0.90, 0.86, 0.74), rough=0.35, coat=0.3)                           # cream trim
M_FLOOR = parquet("M_Floor")
M_CEIL = mat("M_Ceiling", (0.85, 0.80, 0.70), rough=0.9)
M_DOOR = wood("M_Door", (0.03, 0.16, 0.08), (0.05, 0.22, 0.11), scale=1.5, rough=0.35)       # bottle-green door
M_BRASS = mat("M_Brass", (0.95, 0.62, 0.20), rough=0.25, metal=1.0)
M_DESK = wood("M_Desk", (0.18, 0.06, 0.02), (0.30, 0.11, 0.04), scale=3.0)
M_ROD = mat("M_RodBase", (0.93, 0.86, 0.62), rough=0.4, coat=0.3)
M_RED = fabric("M_FlagRed", (0.70, 0.02, 0.03), scale=600)
M_WHITE = fabric("M_FlagWhite", (0.92, 0.90, 0.86), scale=600)
M_GLASS = mat("M_Glass", (0.9, 0.95, 1.0), rough=0.02); M_GLASS.node_tree.nodes["Principled BSDF"].inputs["Transmission Weight"].default_value = 1.0
M_LAMPSHADE = mat("M_LampShade", (0.02, 0.35, 0.10), rough=0.2, coat=0.6, emit=((0.4, 1.0, 0.5), 0.4))
M_PAPER = mat("M_Paper", (0.95, 0.92, 0.82), rough=0.8)

# ================================================================== the room
def wall_with_holes(name, y0, y1, xr, zr, holes, material):
    """a wall slab y0..y1 with rectangular holes [(x0,x1,z0,z1)] cut by booleans"""
    o = box(name, (xr[1] - xr[0], y1 - y0, zr[1] - zr[0]), ((xr[0] + xr[1]) / 2, (y0 + y1) / 2, (zr[0] + zr[1]) / 2), material, bevel=0.0)
    for i, (x0, x1, z0, z1) in enumerate(holes):
        c = box(name + "_cut%d" % i, (x1 - x0, (y1 - y0) + 0.2, z1 - z0), ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), material, bevel=0.0)
        md = o.modifiers.new("cut%d" % i, 'BOOLEAN'); md.object = c; md.operation = 'DIFFERENCE'; md.solver = 'EXACT'
        bpy.context.view_layer.objects.active = o; bpy.ops.object.modifier_apply(modifier=md.name)
        bpy.data.objects.remove(c, do_unlink=True)
    return o
DOOR = (-2.0, -1.1, 0.0, 2.10)
WIN = (1.30, 2.20, 0.95, 2.35)
CEIL_Z = 3.30
BACK = wall_with_holes("RM_BackWall", WALL_Y, WALL_Y + 0.15, (-3.2, 3.2), (0.0, CEIL_Z), [DOOR, WIN], M_WALL)
# oxblood wainscot (lower 1.0 m) as a 1 cm skin in front of the wall, with the same door gap
WAIN = wall_with_holes("RM_Wainscot", WALL_Y - 0.012, WALL_Y, (-3.2, 3.2), (0.0, 1.0), [(DOOR[0] - 0.08, DOOR[1] + 0.08, 0.0, 1.2), (WIN[0], WIN[1], WIN[2], 1.2)], M_WAINS)
box("RM_ChairRail", (6.4, 0.03, 0.05), (0, WALL_Y - 0.02, 1.0), M_TRIM, bevel=0.006)
box("RM_Skirting", (6.4, 0.025, 0.12), (0, WALL_Y - 0.0245, 0.06), M_TRIM, bevel=0.004)
box("RM_Cornice", (6.4, 0.08, 0.10), (0, WALL_Y - 0.04, CEIL_Z - 0.05), M_TRIM, bevel=0.01)
box("RM_Floor", (6.4, 8.0, 0.05), (0, -3.5, -0.025), M_FLOOR, bevel=0.0)
box("RM_Ceiling", (6.4, 8.0, 0.05), (0, -3.5, CEIL_Z + 0.025), M_CEIL, bevel=0.0)
box("RM_SideL", (0.12, 8.0, CEIL_Z), (-3.2, -3.5, CEIL_Z / 2), M_WALL, bevel=0.0)
box("RM_SideR", (0.12, 8.0, CEIL_Z), (3.2, -3.5, CEIL_Z / 2), M_WALL, bevel=0.0)
# panel moulding rectangles on the wainscot (cream), skipping the door and window gaps
for x in [-2.9, -2.5, -0.85, -0.45, -0.05, 0.35, 0.75, 2.45, 2.85]:
    for nm, sz, lc in (("t", (0.32, 0.012, 0.018), (x, WALL_Y - 0.018, 0.86)), ("b", (0.32, 0.012, 0.018), (x, WALL_Y - 0.018, 0.22)),
                       ("l", (0.018, 0.012, 0.64), (x - 0.15, WALL_Y - 0.018, 0.54)), ("r", (0.018, 0.012, 0.64), (x + 0.15, WALL_Y - 0.018, 0.54))):
        box("RM_Mould%s_%.2f" % (nm, x), sz, lc, M_TRIM, bevel=0.003)
# ---- the door: casing, a recessed panelled leaf, brass knob
dx0, dx1, dz1 = DOOR[0], DOOR[1], DOOR[3]
for nm, sz, lc in (("L", (0.10, 0.04, dz1 + 0.08), (dx0 - 0.05, WALL_Y - 0.02, (dz1 + 0.08) / 2)),
                   ("R", (0.10, 0.04, dz1 + 0.08), (dx1 + 0.05, WALL_Y - 0.02, (dz1 + 0.08) / 2)),
                   ("T", (dx1 - dx0 + 0.20, 0.05, 0.12), ((dx0 + dx1) / 2, WALL_Y - 0.025, dz1 + 0.06))):
    box("RM_DoorCase" + nm, sz, lc, M_TRIM, bevel=0.008)
LEAF = box("RM_DoorLeaf", (dx1 - dx0 - 0.01, 0.045, dz1 - 0.01), ((dx0 + dx1) / 2, WALL_Y + 0.06, (dz1 - 0.01) / 2 + 0.005), M_DOOR, bevel=0.006)
for k, (z0, z1) in enumerate(((0.15, 0.95), (1.10, 1.95))):
    for j, (x0, x1) in enumerate(((dx0 + 0.10, (dx0 + dx1) / 2 - 0.04), ((dx0 + dx1) / 2 + 0.04, dx1 - 0.10))):
        box("RM_DoorPanel%d%d" % (k, j), (x1 - x0, 0.012, z1 - z0), ((x0 + x1) / 2, WALL_Y + 0.034, (z0 + z1) / 2), M_DOOR, bevel=0.01)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.03, location=(dx1 - 0.10, WALL_Y + 0.01, 1.0)); kn = bpy.context.active_object
kn.name = "RM_DoorKnob"; kn.data.materials.append(M_BRASS); bpy.ops.object.shade_smooth()
# ---- the window: casing, sill, muntins, glass; outside a tree (seasons keyed in stage B) and a far hedge
wx0, wx1, wz0, wz1 = WIN
for nm, sz, lc in (("L", (0.08, 0.04, wz1 - wz0 + 0.1), (wx0 - 0.04, WALL_Y - 0.02, (wz0 + wz1) / 2)),
                   ("R", (0.08, 0.04, wz1 - wz0 + 0.1), (wx1 + 0.04, WALL_Y - 0.02, (wz0 + wz1) / 2)),
                   ("T", (wx1 - wx0 + 0.16, 0.05, 0.10), ((wx0 + wx1) / 2, WALL_Y - 0.025, wz1 + 0.05)),
                   ("S", (wx1 - wx0 + 0.20, 0.14, 0.04), ((wx0 + wx1) / 2, WALL_Y - 0.05, wz0 - 0.02)),
                   ("MV", (0.03, 0.03, wz1 - wz0), ((wx0 + wx1) / 2, WALL_Y + 0.08, (wz0 + wz1) / 2)),
                   ("MH", (wx1 - wx0, 0.03, 0.03), ((wx0 + wx1) / 2, WALL_Y + 0.08, (wz0 + wz1) / 2 + 0.15))):
    box("RM_Win" + nm, sz, lc, M_TRIM, bevel=0.006)
bpy.ops.mesh.primitive_plane_add(size=1, location=((wx0 + wx1) / 2, WALL_Y + 0.09, (wz0 + wz1) / 2), rotation=(math.radians(90), 0, 0))
GL = bpy.context.active_object; GL.name = "RM_WinGlass"; GL.scale = (wx1 - wx0, wz1 - wz0, 1); GL.data.materials.append(M_GLASS)
GL.visible_shadow = False
M_TRUNK = mat("M_Trunk", (0.12, 0.07, 0.04), rough=0.8)
M_LEAF = mat("M_Leaves", (0.10, 0.45, 0.06), rough=0.7, sheen=0.2)     # colour keyed in stage B (seasons)
cyl("EX_TreeTrunk", 0.12, 3.2, (1.95, 3.2, 1.6), M_TRUNK)
rng = random.Random(4)
for i in range(16):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=rng.uniform(0.55, 0.9),
                                          location=(1.95 + rng.uniform(-1.1, 1.1), 3.2 + rng.uniform(-0.6, 0.6), 2.9 + rng.uniform(-0.5, 0.9)))
    lf = bpy.context.active_object; lf.name = "EX_Leaves%d" % i; lf.data.materials.append(M_LEAF)
    tx = bpy.data.textures.new("leafnoise%d" % i, 'CLOUDS'); tx.noise_scale = 0.25
    dm = lf.modifiers.new("d", 'DISPLACE'); dm.texture = tx; dm.strength = 0.25
    bpy.ops.object.shade_smooth()
box("EX_Ground", (20, 12, 0.05), (0, 7.0, -0.03), mat("M_Lawn", (0.08, 0.32, 0.04), rough=0.9), bevel=0.0)
box("EX_Hedge", (14, 0.8, 1.4), (0, 8.5, 0.7), mat("M_Hedge", (0.04, 0.22, 0.04), rough=0.8), bevel=0.05)
box("EX_HouseFar", (6, 1.0, 5.0), (4.0, 11.0, 2.5), plaster("M_FarHouse", (0.85, 0.55, 0.20), (0.90, 0.62, 0.25), scale=5.0), bevel=0.0)
# ---- the measuring rod (stadiometer): a cream board with black ticks every 2 cm, long ticks every 10 cm, red every 50 cm;
#      a brass head slide on top. No numbers on screen.
ROD = box("RM_Rod", (0.22, 0.025, 2.20), (0.0, WALL_Y - 0.0125, 1.10), M_ROD, bevel=0.004)
m = M_ROD; nt = m.node_tree; p = nt.nodes["Principled BSDF"]
tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sep.inputs[0])
def mnode(op, a_, b_=None):
    n_ = nt.nodes.new("ShaderNodeMath"); n_.operation = op
    for i_, v_ in enumerate((a_, b_)):
        if v_ is None: continue
        if isinstance(v_, (int, float)): n_.inputs[i_].default_value = v_
        else: nt.links.new(v_, n_.inputs[i_])
    return n_.outputs[0]
zz = mnode('ADD', sep.outputs["Z"], 1.10); xx = mnode('ABSOLUTE', sep.outputs["X"])
t2 = mnode('LESS_THAN', mnode('FRACT', mnode('MULTIPLY', zz, 50.0)), 0.10)
t10 = mnode('LESS_THAN', mnode('FRACT', mnode('MULTIPLY', zz, 10.0)), 0.025)
t50 = mnode('LESS_THAN', mnode('FRACT', mnode('MULTIPLY', zz, 2.0)), 0.008)
edge = mnode('GREATER_THAN', xx, 0.07); edge10 = mnode('GREATER_THAN', xx, 0.02)
blk = mnode('MAXIMUM', mnode('MULTIPLY', t2, edge), mnode('MULTIPLY', t10, edge10))
mixb = nt.nodes.new("ShaderNodeMix"); mixb.data_type = 'RGBA'; mixb.inputs["A"].default_value = (0.93, 0.86, 0.62, 1); mixb.inputs["B"].default_value = (0.02, 0.02, 0.02, 1)
nt.links.new(blk, mixb.inputs["Factor"])
mixr = nt.nodes.new("ShaderNodeMix"); mixr.data_type = 'RGBA'; mixr.inputs["B"].default_value = (0.75, 0.03, 0.03, 1)
nt.links.new(mixb.outputs["Result"], mixr.inputs["A"]); nt.links.new(t50, mixr.inputs["Factor"])
nt.links.new(mixr.outputs["Result"], p.inputs["Base Color"])
box("RM_RodSlide", (0.24, 0.10, 0.03), (0.0, WALL_Y - 0.05, 2.21), M_BRASS, bevel=0.005)
# ---- DA KRAS FILMS plaque (enamel, brass frame) at x=-0.78, z=2.02
PM, _ = img_mat("M_Plaque", os.path.join(PKG, "assets/tex/plaque_logo.png"), rough=0.25, coat=0.6)
box("RM_PlaqueFrame", (0.74, 0.02, 0.32), (-0.82, WALL_Y - 0.010, 2.12), M_BRASS, bevel=0.004)
bpy.ops.mesh.primitive_plane_add(size=1, location=(-0.82, WALL_Y - 0.0215, 2.12), rotation=(math.radians(90), 0, 0))
PL = bpy.context.active_object; PL.name = "RM_PlaqueLogo"; PL.scale = (0.70, 0.29, 1); bpy.ops.object.transform_apply(scale=True)
PL.data.materials.append(PM)
# ---- framed photo (texture rendered from this film in stage B2) at x=-0.78, z=1.40, 0.36 x 0.48
FRM = box("RM_PhotoFrame", (0.52, 0.025, 0.68), (-0.84, WALL_Y - 0.0125, 1.48), M_DESK, bevel=0.006)
PHM = mat("M_Photo", (0.5, 0.42, 0.32), rough=0.3, coat=0.5)
bpy.ops.mesh.primitive_plane_add(size=1, location=(-0.84, WALL_Y - 0.0255, 1.48), rotation=(math.radians(90), 0, 0))
PH = bpy.context.active_object; PH.name = "RM_Photo"; PH.scale = (0.46, 0.62, 1); bpy.ops.object.transform_apply(scale=True)
PH.data.materials.append(PHM)
# ---- red-white-red flag hanging high on the back wall (x 0.45..1.15)
for k, (mm, z0) in enumerate(((M_RED, 2.62), (M_WHITE, 2.42), (M_RED, 2.22))):
    o = box("RM_Flag%d" % k, (0.80, 0.008, 0.20), (0.82, WALL_Y - 0.03, z0 + 0.10), mm, bevel=0.0)
    sd = o.modifiers.new("sd", 'SUBSURF'); sd.levels = 2; sd.render_levels = 2
cyl("RM_FlagPole", 0.012, 0.95, (0.82, WALL_Y - 0.04, 2.85), M_BRASS, rot=(0, math.radians(90), 0))
# ---- desk at the right (well clear of the officer): top, legs, papers, a green banker's lamp
box("RM_DeskTop", (0.95, 0.60, 0.04), (2.05, -0.70, 0.76), M_DESK, bevel=0.008)
for x in (1.62, 2.48):
    for y in (-0.95, -0.45):
        box("RM_DeskLeg%.1f%.1f" % (x, y), (0.05, 0.05, 0.74), (x, y, 0.37), M_DESK, bevel=0.004)
box("RM_DeskDrawers", (0.40, 0.55, 0.50), (2.28, -0.70, 0.49), M_DESK, bevel=0.006)
box("RM_Papers", (0.30, 0.22, 0.012), (1.88, -0.78, 0.786), M_PAPER, bevel=0.001, rot=(0, 0, 0.2))
cyl("RM_LampBase", 0.07, 0.02, (2.30, -0.62, 0.79), M_BRASS); cyl("RM_LampStem", 0.012, 0.30, (2.30, -0.62, 0.94), M_BRASS)
bpy.ops.mesh.primitive_cylinder_add(radius=0.10, depth=0.30, location=(2.24, -0.66, 1.10), rotation=(0, math.radians(90), math.radians(20)))
ls_ = bpy.context.active_object; ls_.name = "RM_LampShade"; ls_.data.materials.append(M_LAMPSHADE)
for i in range(len(ls_.data.vertices)): pass
# ================================================================== the brain (CC-BY model, re-materialled), tumour and vertebrae
with bpy.data.libraries.load(BRAIN_SRC, link=False) as (src, dst):
    dst.objects = list(src.objects)
BR = [o for o in dst.objects if o is not None and o.type == 'MESH'][0]
sc.collection.objects.link(BR)
mw_ = BR.matrix_world.copy(); BR.parent = None
BR.animation_data_clear(); BR.data.transform(mw_); BR.matrix_world = Matrix.Identity(4)      # bake the source transform into the mesh
BR.name = "Brain"
vs = [v.co.copy() for v in BR.data.vertices]
mn = Vector([min(v[i] for v in vs) for i in range(3)]); mxv = Vector([max(v[i] for v in vs) for i in range(3)])
ctr = (mn + mxv) / 2; dims = mxv - mn
print("BRAIN dims", dims)
# long axis -> Y (front = -Y). The brainstem/cerebellum end (posterior) has the lowest vertices.
ax = max(range(3), key=lambda i: dims[i]) if dims[0] != dims[1] else 0
lowz = mn.z + 0.15 * dims.z
low = [v for v in vs if v.z < lowz]
lm = sum((v for v in low), Vector()) / len(low)
post_sign = 1 if (lm[ax] - ctr[ax]) > 0 else -1          # posterior end on +ax if the low mass sits there
BR.data.transform(Matrix.Translation(-ctr))
if ax == 0:
    R = Matrix.Rotation(math.radians(90 if post_sign > 0 else -90), 4, 'Z')    # +X -> +Y when posterior is +X
    BR.data.transform(R)
elif ax == 1 and post_sign < 0:
    BR.data.transform(Matrix.Rotation(math.radians(180), 4, 'Z'))
BR.data.materials.clear()
M_BRAIN = mat("M_Brain", (0.95, 0.42, 0.50), rough=0.35, sss=0.2, coat=0.4, emit=((1.0, 0.45, 0.55), 0.6))
BR.data.materials.append(M_BRAIN)
for p_ in BR.data.polygons: p_.use_smooth = True
# fit inside the hero's head: bbox of head-dominant body vertices at rest
bpy.context.view_layer.update()
idx2 = {vg.index: vg.name for vg in HB.vertex_groups}
def rest_coords(body):
    """rest-pose vertex coords WITH the phenotype shape keys (modifiers off so indices match the mesh)"""
    sv = [(m, m.show_viewport) for m in body.modifiers]
    for m, _ in sv: m.show_viewport = False
    bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get(); e = body.evaluated_get(dg); me = e.to_mesh()
    co = [v.co.copy() for v in me.vertices]; e.to_mesh_clear()
    for m, v_ in sv: m.show_viewport = v_
    bpy.context.view_layer.update(); return co
RC = rest_coords(HB)
hv = []
for v in HB.data.vertices:
    best = (0, None)
    for g in v.groups:
        n_ = idx2.get(g.group)
        if n_ in ("head",) and g.weight > best[0]: best = (g.weight, n_)
    if best[1] == "head" and best[0] > 0.9: hv.append(HB.matrix_world @ RC[v.index])
hmn = Vector([min(v[i] for v in hv) for i in range(3)]); hmx = Vector([max(v[i] for v in hv) for i in range(3)])
hd = hmx - hmn
eyeL = HERO.matrix_world @ HERO.data.bones["eye.L"].head_local; eyeR = HERO.matrix_world @ HERO.data.bones["eye.R"].head_local
eye_c = (eyeL + eyeR) / 2
bvs = [v.co for v in BR.data.vertices]; bd = Vector([max(v[i] for v in bvs) - min(v[i] for v in bvs) for i in range(3)])
s_ = min(0.70 * hd.y / bd.y, 0.70 * hd.x / bd.x)
BR.data.transform(Matrix.Scale(s_, 4))
bvs = [v.co for v in BR.data.vertices]; bmn = Vector([min(v[i] for v in bvs) for i in range(3)]); bmx = Vector([max(v[i] for v in bvs) for i in range(3)])
# brain: centred left-right, its front 2 cm behind the eyes' front, its top 1.8 cm under the scalp
loc = Vector(((hmn.x + hmx.x) / 2, eye_c.y + 0.035 - bmn.y, hmx.z - 0.022 - bmx.z))
BR.location = loc
print("HEAD dims", hd, "brain scale", s_, "loc", loc)
# pituitary gland / tumour: a small sphere at the base of the brain, 40 % back from the front, just under the cerebrum
TUM_LOC = loc + Vector((0.0, bmn.y + 0.40 * (bmx.y - bmn.y), bmn.z + 0.30 * (bmx.z - bmn.z)))
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=32, ring_count=16, location=TUM_LOC)
TUM = bpy.context.active_object; TUM.name = "Tumour"; TUM.scale = (0.006,) * 3; bpy.ops.object.shade_smooth()
tx = bpy.data.textures.new("tumnoise", 'CLOUDS'); tx.noise_scale = 0.4
dmt = TUM.modifiers.new("lumps", 'DISPLACE'); dmt.texture = tx; dmt.strength = 0.25
M_TUM = mat("M_Tumour", (1.0, 0.35, 0.05), rough=0.3, emit=((1.0, 0.30, 0.03), 3.0))     # emission keyed in stage B
TUM.data.materials.append(M_TUM)
# brain + tumour ride on the head bone
for o in (BR, TUM):
    mw = o.matrix_world.copy(); o.parent = HERO; o.parent_type = 'BONE'; o.parent_bone = "head"
    bpy.context.view_layer.update(); o.matrix_world = mw
# vertebrae along the spine and neck bones (white bone, slightly emissive so they read in the x-ray)
M_BONE = mat("M_Vertebra", (0.95, 0.93, 0.85), rough=0.4, emit=((0.85, 0.95, 1.0), 1.2))
VERT = []
chain = [("spine05", 4), ("spine04", 3), ("spine03", 3), ("spine02", 3), ("spine01", 3), ("neck01", 2), ("neck02", 2), ("neck03", 1)]
for bn, n_ in chain:
    b = HERO.data.bones[bn]; h_ = HERO.matrix_world @ b.head_local; t_ = HERO.matrix_world @ b.tail_local
    for k in range(n_):
        u = (k + 0.5) / n_; p_ = h_.lerp(t_, u)
        r_ = 0.016 if bn.startswith("spine") else 0.011
        bpy.ops.mesh.primitive_cylinder_add(radius=r_, depth=r_ * 0.95, vertices=20, location=p_ + Vector((0, 0.012, 0)))
        v_ = bpy.context.active_object; v_.name = "Vert_%s_%d" % (bn, k)
        bv = v_.modifiers.new("bev", 'BEVEL'); bv.width = r_ * 0.3; bv.segments = 3
        bpy.ops.mesh.primitive_cube_add(size=1, location=p_ + Vector((0, 0.012 + r_ * 1.3, -r_ * 0.2)))
        sp_ = bpy.context.active_object; sp_.scale = (r_ * 0.5, r_ * 1.4, r_ * 0.6)
        bpy.ops.object.transform_apply(scale=True)
        bpy.ops.object.select_all(action='DESELECT'); sp_.select_set(True); v_.select_set(True); bpy.context.view_layer.objects.active = v_
        bpy.ops.object.join(); v_ = bpy.context.active_object
        v_.data.materials.append(M_BONE); bpy.ops.object.shade_smooth()
        mw = v_.matrix_world.copy(); v_.parent = HERO; v_.parent_type = 'BONE'; v_.parent_bone = bn
        bpy.context.view_layer.update(); v_.matrix_world = mw
        VERT.append(v_)

# ================================================================== x-ray mix in every hero material ('XR' value node, keyed in B)
def xray_inject(m, kind):
    nt = m.node_tree
    outn = [n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output] or [n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL']
    outn = outn[0]
    if not outn.inputs["Surface"].is_linked: return
    src = outn.inputs["Surface"].links[0].from_socket
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    if kind == "skin":
        lw = nt.nodes.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.45
        pw = nt.nodes.new("ShaderNodeMath"); pw.operation = 'POWER'; pw.inputs[1].default_value = 1.6; nt.links.new(lw.outputs["Facing"], pw.inputs[0])
        em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (0.25, 0.75, 1.0, 1); em.inputs["Strength"].default_value = 2.2
        mxe = nt.nodes.new("ShaderNodeMixShader"); nt.links.new(pw.outputs[0], mxe.inputs["Fac"]); nt.links.new(tr.outputs[0], mxe.inputs[1]); nt.links.new(em.outputs[0], mxe.inputs[2])
        xr_sh = mxe.outputs[0]
    elif kind == "cloth":
        lw = nt.nodes.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.3
        pw = nt.nodes.new("ShaderNodeMath"); pw.operation = 'MULTIPLY'; pw.inputs[1].default_value = 0.35; nt.links.new(lw.outputs["Facing"], pw.inputs[0])
        em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (0.35, 0.55, 1.0, 1); em.inputs["Strength"].default_value = 1.2
        mxe = nt.nodes.new("ShaderNodeMixShader"); nt.links.new(pw.outputs[0], mxe.inputs["Fac"]); nt.links.new(tr.outputs[0], mxe.inputs[1]); nt.links.new(em.outputs[0], mxe.inputs[2])
        xr_sh = mxe.outputs[0]
    else:
        xr_sh = tr.outputs[0]
    v = nt.nodes.new("ShaderNodeValue"); v.name = "XR"; v.label = "XR"; v.outputs[0].default_value = 0.0
    mx = nt.nodes.new("ShaderNodeMixShader"); nt.links.new(v.outputs[0], mx.inputs["Fac"])
    nt.links.new(src, mx.inputs[1]); nt.links.new(xr_sh, mx.inputs[2])
    nt.links.new(mx.outputs[0], outn.inputs["Surface"])
XR_MATS = []
for c in HERO.children:
    if c.type != 'MESH' or c.name.startswith(("Brain", "Tumour", "Vert_")): continue
    kind = "skin" if c.name.endswith(".body") else ("cloth" if any(k in c.name for k in ("suit", "shoes")) else "none")
    for m in c.data.materials:
        if m and m.use_nodes and m.name not in [x.name for x in XR_MATS]:
            xray_inject(m, kind); XR_MATS.append(m)
print("XR materials", [m.name for m in XR_MATS])
HERO["xr_mats"] = [m.name for m in XR_MATS]

# ================================================================== lights + world + look (fast, zero-error)
def light(name, kind, energy, loc, rot=(0, 0, 0), size=1.0, color=(1, 1, 1)):
    ld = bpy.data.lights.new(name, kind); ld.energy = energy; ld.color = color
    if kind == 'AREA': ld.size = size
    o = bpy.data.objects.new(name, ld); sc.collection.objects.link(o); o.location = loc; o.rotation_euler = rot
    return o
light("L_Key", 'AREA', 260, (-1.6, -2.4, 2.9), rot=(math.radians(55), 0, math.radians(-35)), size=1.6, color=(1.0, 0.90, 0.78))
light("L_Fill", 'AREA', 90, (2.2, -2.6, 1.8), rot=(math.radians(70), 0, math.radians(40)), size=2.0, color=(0.80, 0.88, 1.0))
light("L_Rim", 'AREA', 120, (0.6, 0.0, 3.1), rot=(math.radians(-25), 0, 0), size=1.2, color=(1.0, 0.85, 0.65))
light("L_Window", 'AREA', 140, ((wx0 + wx1) / 2, WALL_Y + 0.25, (wz0 + wz1) / 2), rot=(math.radians(-90), 0, 0), size=0.9, color=(1.0, 0.92, 0.80))
light("L_Sun", 'SUN', 3.0, (2, 6, 6), rot=(math.radians(-50), math.radians(10), math.radians(160)), color=(1.0, 0.88, 0.70))
sc.render.engine = 'CYCLES'; cy = sc.cycles
cy.samples = 64; cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.05
cy.use_denoising = True; cy.denoiser = 'OPENIMAGEDENOISE'
cy.max_bounces = 6; cy.diffuse_bounces = 3; cy.glossy_bounces = 3; cy.transmission_bounces = 6; cy.transparent_max_bounces = 24
cy.caustics_reflective = False; cy.caustics_refractive = False
sc.render.use_persistent_data = True
sc.render.use_simplify = True; sc.render.simplify_subdivision_render = 2; cy.texture_limit_render = '2048'
sc.render.use_motion_blur = False
sc.view_settings.view_transform = 'Filmic'; sc.view_settings.look = 'High Contrast'; sc.view_settings.exposure = -0.3
sc.world = sc.world or bpy.data.worlds.new("World")
w = sc.world; w.use_nodes = True; nt = w.node_tree
for n in list(nt.nodes):
    if n.type != 'OUTPUT_WORLD': nt.nodes.remove(n)
tc = nt.nodes.new("ShaderNodeTexCoord"); sp = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Generated"], sp.inputs[0])
mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.5; mr.inputs["From Max"].default_value = 0.75; nt.links.new(sp.outputs["Z"], mr.inputs["Value"])
cr = nt.nodes.new("ShaderNodeValToRGB"); cr.name = "SkyRamp"
cr.color_ramp.elements[0].color = (0.65, 0.85, 1.0, 1); cr.color_ramp.elements[1].color = (0.10, 0.40, 0.95, 1)
nt.links.new(mr.outputs["Result"], cr.inputs["Fac"])
bg = nt.nodes.new("ShaderNodeBackground"); bg.name = "SkyBG"; bg.inputs["Strength"].default_value = 0.6; nt.links.new(cr.outputs["Color"], bg.inputs["Color"])
nt.links.new(bg.outputs[0], [n for n in nt.nodes if n.type == 'OUTPUT_WORLD'][0].inputs["Surface"])
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("BUILD_DONE", OUT)
