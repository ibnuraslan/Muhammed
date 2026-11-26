"""DrunkTrain v008 stage A (from scratch): one drunk man, one rail worker, one cargo train, one rail line, the muscle explainer.
blender -b --python 01_build.py -- <polyhaven_dir> <glb_dir> <out.blend>

TRACK: the line runs along +Y. Rails at x=+-RX (rail top z=RT), sleepers every 0.62 m, flat ballast |x|<3.0 (z=0),
a dirt path on the -X side, grass beyond, colourful houses and trees in the distance.
TRAIN: an imported diesel locomotive (CC-BY) + two container flat wagons (deck, side sills, imported bogie wheels, bright
containers; one carries the DA KRAS FILMS logo). The wagons are open underneath between the bogies, so the man can be seen
lying between the rails under them. Everything of the train is parented to the empty `Train` (keyed in 02).
EXPLAINER (x=+400): a sky-blue gradient dome with a glossy muscle bundle (fibres + tendons) on a lattice that sways."""
import bpy, bmesh, sys, math, random, os
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "lib_build.py")).read())
a = sys.argv[sys.argv.index("--") + 1:]
PH, GLB, OUT = a[0], a[1], a[2]
PKG = os.path.dirname(HERE)
random.seed(16)
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
sc = bpy.context.scene
sc.render.fps = 60
sc.frame_start, sc.frame_end = 1, 1735
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
RX, RT = 0.80, 0.22            # rail centre x, rail top z
EX = Vector((400.0, 0.0, 0.0))  # explainer set origin
def col(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in sc.collection.children: sc.collection.children.link(c)
    return c
C_SET, C_TRAIN, C_PEOPLE, C_EXP = col("SET"), col("TRAIN"), col("PEOPLE"), col("EXPLAINER")
def to_col(o, c):
    for cc in list(o.users_collection): cc.objects.unlink(o)
    c.objects.link(o)

# ================================================================== people (ONE model each for the whole film)
MAN, MB = human("Man", 1.0, 0.5, {"asian": 0.05, "caucasian": 0.85, "african": 0.10}, "short02/short02.mhclo",
                "young_caucasian_male/young_caucasian_male.mhmat", "eyebrow001/eyebrow001.mhclo",
                height=0.55, weight=0.45, muscle=0.5,
                clothes=["male_casualsuit04/male_casualsuit04.mhclo", "shoes02/shoes02.mhclo"])
eye_fix(MAN); eye_group_fix()
WK, WKB = human("Worker", 1.0, 0.75, {"asian": 0.05, "caucasian": 0.25, "african": 0.70}, "short01/short01.mhclo",
                "middleage_african_male/middleage_african_male.mhmat", "eyebrow003/eyebrow003.mhclo",
                height=0.5, weight=0.6, muscle=0.55,
                clothes=["male_worksuit01/male_worksuit01.mhclo", "shoes06/shoes06.mhclo"])
eye_fix(WK)
EG = bpy.data.node_groups.get("EnhancedEye")
for n in (EG.nodes if EG else []):
    if n.type == 'MATH' and abs(n.inputs[1].default_value - 0.92) < 1e-4: n.inputs[1].default_value = 0.96
for R in (MAN, WK):
    for m in [m for c in R.children if c.type == 'MESH' and "high-poly" in c.name for m in c.data.materials]:
        for n in m.node_tree.nodes:
            if n.type == 'GROUP' and "IrisMajorColor" in n.inputs:
                n.inputs["IrisMajorColor"].default_value = (0.13, 0.06, 0.02, 1); n.inputs["IrisMinorColor"].default_value = (0.05, 0.025, 0.01, 1)
    for c in R.children:
        if c.type == 'MESH' and "teeth" in c.name:
            for m in c.data.materials: tint(m, (1.5, 1.45, 1.4))
for c in MAN.children:
    if c.type == 'MESH' and any(k in c.name.lower() for k in ("short02", "eyebrow")):
        for m in c.data.materials: tint(m, (0.55, 0.32, 0.16))        # warm brown hair
for m in MB.data.materials: tint(m, (1.0, 0.80, 0.66))                 # warm, slightly flushed skin
TEE = [c for c in MAN.children if c.type == 'MESH' and "casualsuit" in c.name][0]
TEE.name = "Man.clothes"
tee = bpy.data.images.load(os.path.join(PKG, "assets/tex/man_tee_diffuse.png")); tee.name = "man_tee_diffuse"
for m in TEE.data.materials:
    for nd in m.node_tree.nodes:
        if nd.type == 'TEX_IMAGE' and nd.image and "diffuse" in nd.image.name.lower(): nd.image = tee
        if nd.type == 'NORMAL_MAP': nd.inputs["Strength"].default_value = 0.4
SUIT = [c for c in WK.children if c.type == 'MESH' and "worksuit" in c.name][0]
SUIT.name = "Worker.clothes"
def recolour(m, col_):
    # luminance of the original diffuse x a saturated colour (keeps folds and seams, drops the denim blue)
    for nd in list(m.node_tree.nodes):
        if nd.type == 'TEX_IMAGE' and nd.image and "diffuse" in nd.image.name.lower():
            for lk in list(nd.outputs['Color'].links):
                bw = m.node_tree.nodes.new('ShaderNodeRGBToBW'); mx_ = m.node_tree.nodes.new('ShaderNodeMix'); mx_.data_type = 'RGBA'
                mx_.blend_type = 'MULTIPLY'; mx_.inputs['Factor'].default_value = 1.0; mx_.inputs['B'].default_value = (*col_, 1)
                m.node_tree.links.new(nd.outputs['Color'], bw.inputs[0]); m.node_tree.links.new(bw.outputs[0], mx_.inputs['A'])
                m.node_tree.links.new(mx_.outputs['Result'], lk.to_socket)
for m in SUIT.data.materials: recolour(m, (2.6, 0.62, 0.03))            # hi-vis orange overalls
# the T-shirt under the overalls (unsaturated in the original texture) becomes navy, never skin-coloured
for m in SUIT.data.materials:
    nt_ = m.node_tree
    for mx_ in [n for n in nt_.nodes if n.type == 'MIX' and n.blend_type == 'MULTIPLY' and n.inputs['A'].is_linked
                and n.inputs['A'].links[0].from_node.type == 'RGBTOBW']:
        tex = mx_.inputs['A'].links[0].from_node.inputs[0].links[0].from_node
        hsv = nt_.nodes.new('ShaderNodeSeparateColor'); hsv.mode = 'HSV'; nt_.links.new(tex.outputs['Color'], hsv.inputs[0])
        mr_ = nt_.nodes.new('ShaderNodeMapRange'); mr_.inputs['From Min'].default_value = 0.12; mr_.inputs['From Max'].default_value = 0.25
        nt_.links.new(hsv.outputs[1], mr_.inputs['Value'])
        out_links = list(mx_.outputs['Result'].links)
        mm = nt_.nodes.new('ShaderNodeMix'); mm.data_type = 'RGBA'; mm.inputs['A'].default_value = (0.02, 0.05, 0.22, 1)
        nt_.links.new(mr_.outputs['Result'], mm.inputs['Factor']); nt_.links.new(mx_.outputs['Result'], mm.inputs['B'])
        for lk in out_links: nt_.links.new(mm.outputs['Result'], lk.to_socket)
# the man's few small cuts on his right palm: a colour attribute painted on a handful of palm vertices
idx2 = {vg.index: vg.name for vg in MB.vertex_groups}
palm = []
for v in MB.data.vertices:
    best = max(((g.weight, idx2.get(g.group)) for g in v.groups), default=(0, None))
    if best[1] and best[1].startswith("metacarpal") and best[1].endswith(".R"): palm.append(v)
ca = MB.data.color_attributes.new("cuts", 'FLOAT_COLOR', 'POINT')
for i in range(len(MB.data.vertices)): ca.data[i].color = (0, 0, 0, 1)
if palm:
    # the palm side: vertices whose normal points most along the palm normal (rest pose, palms face the thigh -> inward x)
    pn = Vector((1, 0, 0)) if True else None
    cand = sorted(palm, key=lambda v: -(v.normal.dot(Vector((1, 0.0, -0.2)).normalized())))[:max(6, len(palm) // 6)]
    rnd = random.Random(5)
    for v in rnd.sample(cand, min(5, len(cand))):
        ca.data[v.index].color = (1, 1, 1, 1)
for m in MB.data.materials:
    if not m or not m.use_nodes: continue
    nt = m.node_tree; P = [n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED']
    if not P: continue
    P = P[0]; src = P.inputs["Base Color"].links[0].from_socket if P.inputs["Base Color"].is_linked else None
    at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_name = "cuts"
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.55; mr.inputs["From Max"].default_value = 0.8
    nt.links.new(at.outputs["Fac"], mr.inputs["Value"])
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'
    mx.inputs['B'].default_value = (0.45, 0.02, 0.03, 1)
    if src: nt.links.new(src, mx.inputs['A'])
    else: mx.inputs['A'].default_value = P.inputs["Base Color"].default_value
    nt.links.new(mr.outputs["Result"], mx.inputs["Factor"]); nt.links.new(mx.outputs["Result"], P.inputs["Base Color"])
print("PALM_CUT_VERTS", len(palm))
for R in (MAN, WK):
    for c in R.children:
        if c.type == 'MESH' and ("clothes" in c.name or "shoes" in c.name):
            so = c.modifiers.new("solid", 'SOLIDIFY'); so.thickness = 0.003; so.offset = 1.0; so.use_rim = True
            i = c.modifiers.find("solid")
            while i > c.modifiers.find("Armature") + 1:
                c.modifiers.move(i, i - 1); i -= 1
    for c in R.children: to_col(c, C_PEOPLE)
    to_col(R, C_PEOPLE)

# ================================================================== materials
def pbr(name, tex_id, scale=1.0, tint_=(1, 1, 1), bump=0.6, rough_mul=1.0, coords="Object"):
    """Poly Haven 1k texture set, box-projected in object (or generated) coordinates, `scale` repeats per metre"""
    d = os.path.join(PH, tex_id, "textures") if os.path.isdir(os.path.join(PH, tex_id, "textures")) else os.path.join(PH, tex_id)
    files = os.listdir(d)
    def f(key):
        k = [x for x in files if key in x]; return os.path.join(d, k[0]) if k else None
    m = mat(name, (0.5, 0.5, 0.5), rough=0.8); nt = m.node_tree; P = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (scale,) * 3
    nt.links.new(tc.outputs[coords], mp.inputs["Vector"])
    def img(path, non_color=False):
        t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(path, check_existing=True)
        t.projection = 'BOX'; t.projection_blend = 0.25
        if non_color: t.image.colorspace_settings.name = 'Non-Color'
        nt.links.new(mp.outputs["Vector"], t.inputs["Vector"]); return t
    dt = img(f("_diff_"))
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
    mx.inputs['B'].default_value = (*tint_, 1)
    hs = nt.nodes.new("ShaderNodeHueSaturation"); hs.inputs["Saturation"].default_value = 1.25
    nt.links.new(dt.outputs["Color"], mx.inputs['A']); nt.links.new(mx.outputs['Result'], hs.inputs["Color"])
    nt.links.new(hs.outputs["Color"], P.inputs["Base Color"])
    if f("_rough_") and f("_rough_").endswith((".jpg", ".png")):
        rt = img(f("_rough_"), True); mm = nt.nodes.new("ShaderNodeMath"); mm.operation = 'MULTIPLY'; mm.inputs[1].default_value = rough_mul
        nt.links.new(rt.outputs["Color"], mm.inputs[0]); nt.links.new(mm.outputs[0], P.inputs["Roughness"])
    if f("_disp_") and f("_disp_").endswith(".png") and bump > 0:
        ht = img(f("_disp_"), True); bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump
        bp.inputs["Distance"].default_value = 0.02
        nt.links.new(ht.outputs["Color"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], P.inputs["Normal"])
    return m

def corrugated(name, col_, scale=22.0):
    m = mat(name, col_, rough=0.38, coat=0.35); nt = m.node_tree; P = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); wv = nt.nodes.new("ShaderNodeTexWave"); wv.wave_type = 'BANDS'
    wv.bands_direction = 'Y'; wv.wave_profile = 'SIN'; wv.inputs["Scale"].default_value = scale
    nt.links.new(tc.outputs["Object"], wv.inputs["Vector"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.55; bp.inputs["Distance"].default_value = 0.02
    nt.links.new(wv.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], P.inputs["Normal"])
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.0
    cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (*[c * 0.8 for c in col_], 1); cr.color_ramp.elements[1].color = (*col_, 1)
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"]); nt.links.new(nz.outputs["Fac"], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], P.inputs["Base Color"])
    return m

M_BALLAST = pbr("M_Ballast", "gravel_stones", scale=0.9, tint_=(0.95, 0.85, 0.75), bump=0.8)
M_GRASS = pbr("M_Grass", "leafy_grass", scale=0.5, tint_=(0.75, 1.15, 0.45), bump=0.4)
M_DIRT = pbr("M_Dirt", "dirt", scale=0.6, tint_=(1.15, 0.72, 0.42), bump=0.4)
M_SLEEPER = pbr("M_Sleeper", "old_planks_02", scale=1.2, tint_=(0.85, 0.62, 0.42), bump=0.5)
M_RAIL = mat("M_Rail", (0.30, 0.22, 0.16), rough=0.55, metal=0.6)     # rusty brown web
M_RAILTOP = mat("M_RailTop", (0.85, 0.85, 0.88), rough=0.18, metal=1.0)  # polished running surface
M_PLATE = mat("M_Plate", (0.12, 0.10, 0.09), rough=0.6, metal=0.5)
M_STONE = pbr("M_Stone", "gravel_stones", scale=3.0, tint_=(1.0, 0.92, 0.85), bump=0.3)

# ================================================================== the rail line
Y0, Y1 = -200.0, 120.0
def sleeper_row():
    o = box("TR_Sleepers", (2.6, 0.24, 0.16), (0, Y0, -0.02), M_SLEEPER, bevel=0.012)
    ar = o.modifiers.new("arr", 'ARRAY'); ar.fit_type = 'FIT_LENGTH'; ar.fit_length = Y1 - Y0; ar.use_relative_offset = False
    ar.use_constant_offset = True; ar.constant_offset_displace = (0, 0.62, 0); ar.relative_offset_displace = (0, 0, 0)
    to_col(o, C_SET); return o
sleeper_row()
def rail(x):
    # an I profile: foot 0.13 wide x 0.012, web 0.016 x 0.11, head 0.07 x 0.045, along Y; polished top strip
    parts = []
    parts.append(box("TR_RailFoot", (0.13, Y1 - Y0, 0.014), (x, (Y0 + Y1) / 2, 0.067), M_RAIL, bevel=0.003))
    parts.append(box("TR_RailWeb", (0.018, Y1 - Y0, 0.105), (x, (Y0 + Y1) / 2, 0.126), M_RAIL, bevel=0.003))
    parts.append(box("TR_RailHead", (0.072, Y1 - Y0, 0.043), (x, (Y0 + Y1) / 2, RT - 0.0215), M_RAIL, bevel=0.008))
    top = box("TR_RailTop", (0.05, Y1 - Y0, 0.004), (x, (Y0 + Y1) / 2, RT - 0.0015), M_RAILTOP, bevel=0.0)
    parts.append(top)
    for p in parts: to_col(p, C_SET)
    # tie plates under the rail on every sleeper
    tp = box("TR_TiePlates", (0.22, 0.17, 0.008), (x, Y0, 0.064), M_PLATE, bevel=0.002)
    ar = tp.modifiers.new("arr", 'ARRAY'); ar.fit_type = 'FIT_LENGTH'; ar.fit_length = Y1 - Y0; ar.use_relative_offset = False
    ar.use_constant_offset = True; ar.constant_offset_displace = (0, 0.62, 0)
    to_col(tp, C_SET)
    return parts
RAIL_L, RAIL_R = rail(-RX), rail(RX)
def plane(name, x0, x1, y0, y1, z, material, subdiv=0):
    bm = bmesh.new()
    vs = [bm.verts.new((x0, y0, z)), bm.verts.new((x1, y0, z)), bm.verts.new((x1, y1, z)), bm.verts.new((x0, y1, z))]
    bm.faces.new(vs)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); C_SET.objects.link(o); me.materials.append(material)
    if subdiv:
        s = o.modifiers.new("sub", 'SUBSURF'); s.subdivision_type = 'SIMPLE'; s.levels = subdiv; s.render_levels = subdiv
    return o
BALLAST = plane("TR_Ballast", -3.0, 3.0, Y0, Y1, 0.0, M_BALLAST)
PATH = plane("TR_Path", -4.6, -3.0, Y0, Y1, -0.005, M_DIRT)
GRASS_L = plane("TR_GrassL", -90, -4.6, Y0, Y1, -0.01, M_GRASS)
GRASS_R = plane("TR_GrassR", 3.0, 90, Y0, Y1, -0.01, M_GRASS)
# a low ballast edge (shoulder stones) so the bed reads as a raised bed: a bevelled strip each side
for sx in (-1, 1):
    e = box("TR_BallastEdge", (0.5, Y1 - Y0, 0.08), (sx * 3.0, (Y0 + Y1) / 2, -0.02), M_BALLAST, bevel=0.035); to_col(e, C_SET)

# ---- real 3D ballast stones on the bed near the action (instanced by geometry nodes, sitting ON the bed)
def stone_mesh(name, r, seed):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=r, location=(0, 0, -50))
    o = bpy.context.active_object; o.name = name
    rnd = random.Random(seed)
    for v in o.data.vertices:
        v.co = Vector((v.co.x * rnd.uniform(0.75, 1.25), v.co.y * rnd.uniform(0.75, 1.25), v.co.z * rnd.uniform(0.45, 0.8)))
    o.data.materials.append(M_STONE); bpy.ops.object.shade_flat(); to_col(o, C_SET); o.hide_render = True; o.hide_viewport = True
    return o
STONES = [stone_mesh("TR_Stone%d" % i, 0.028 + 0.006 * i, i) for i in range(4)]
sc_col = bpy.data.collections.new("StoneSet"); C_SET.children.link(sc_col)
for s in STONES:
    sc_col.objects.link(s)
def stone_bed(name, x0, x1, y0, y1, density, seed):
    o = plane(name, x0, x1, y0, y1, 0.0, M_BALLAST)
    ng = bpy.data.node_groups.new(name + "_GN", 'GeometryNodeTree')
    ng.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    N = ng.nodes; L = ng.links
    gi = N.new("NodeGroupInput"); go = N.new("NodeGroupOutput")
    dp = N.new("GeometryNodeDistributePointsOnFaces"); dp.inputs["Density"].default_value = density; dp.inputs["Seed"].default_value = seed
    ci = N.new("GeometryNodeCollectionInfo"); ci.inputs["Collection"].default_value = sc_col
    ci.inputs["Separate Children"].default_value = True; ci.inputs["Reset Children"].default_value = True
    ip = N.new("GeometryNodeInstanceOnPoints"); ip.inputs["Pick Instance"].default_value = True
    rr = N.new("FunctionNodeRandomValue"); rr.data_type = 'FLOAT_VECTOR'
    rr.inputs[0].default_value = (0, 0, 0); rr.inputs[1].default_value = (6.3, 6.3, 6.3)
    rs = N.new("FunctionNodeRandomValue"); rs.data_type = 'FLOAT'; rs.inputs[0].default_value = 0.7; rs.inputs[1].default_value = 1.3
    # keep stones off the sleeper tops and away from the rails (they sit between the sleepers and outside the rails)
    pos = N.new("GeometryNodeInputPosition"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(pos.outputs[0], sep.inputs[0])
    modn = N.new("ShaderNodeMath"); modn.operation = 'FLOORED_MODULO'; modn.inputs[1].default_value = 0.62
    addy = N.new("ShaderNodeMath"); addy.operation = 'SUBTRACT'; addy.inputs[1].default_value = Y0 - 0.16
    L.new(sep.outputs["Y"], addy.inputs[0]); L.new(addy.outputs[0], modn.inputs[0])
    gt = N.new("ShaderNodeMath"); gt.operation = 'LESS_THAN'; gt.inputs[1].default_value = 0.32
    L.new(modn.outputs[0], gt.inputs[0])
    ax = N.new("ShaderNodeMath"); ax.operation = 'ABSOLUTE'; L.new(sep.outputs["X"], ax.inputs[0])
    inside = N.new("ShaderNodeMath"); inside.operation = 'LESS_THAN'; inside.inputs[1].default_value = 1.32; L.new(ax.outputs[0], inside.inputs[0])
    on_sl = N.new("ShaderNodeMath"); on_sl.operation = 'MULTIPLY'; L.new(gt.outputs[0], on_sl.inputs[0]); L.new(inside.outputs[0], on_sl.inputs[1])
    nr = N.new("ShaderNodeMath"); nr.operation = 'ABSOLUTE'; d1 = N.new("ShaderNodeMath"); d1.operation = 'SUBTRACT'; d1.inputs[1].default_value = RX
    L.new(ax.outputs[0], d1.inputs[0]); L.new(d1.outputs[0], nr.inputs[0])
    nearr = N.new("ShaderNodeMath"); nearr.operation = 'LESS_THAN'; nearr.inputs[1].default_value = 0.14; L.new(nr.outputs[0], nearr.inputs[0])
    kill = N.new("ShaderNodeMath"); kill.operation = 'MAXIMUM'; L.new(on_sl.outputs[0], kill.inputs[0]); L.new(nearr.outputs[0], kill.inputs[1])
    dl = N.new("GeometryNodeDeleteGeometry"); dl.domain = 'POINT'
    L.new(gi.outputs[0], dp.inputs["Mesh"]); L.new(dp.outputs["Points"], dl.inputs["Geometry"]); L.new(kill.outputs[0], dl.inputs["Selection"])
    L.new(dl.outputs[0], ip.inputs["Points"]); L.new(ci.outputs[0], ip.inputs["Instance"])
    L.new(rr.outputs[0], ip.inputs["Rotation"]); L.new(rs.outputs[0], ip.inputs["Scale"])
    rz = N.new("GeometryNodeRotateInstances")
    L.new(ip.outputs[0], go.inputs[0])
    md = o.modifiers.new("stones", 'NODES'); md.node_group = ng
    return o
STONEBED = stone_bed("TR_StoneBed", -3.0, 3.0, -16.0, 50.0, 70.0, 3)
# keep stone rotations mostly flat-lying: the random rotation is only about Z (x,y kept small)
for n in STONEBED.modifiers["stones"].node_group.nodes:
    if n.bl_idname == "FunctionNodeRandomValue" and n.data_type == 'FLOAT_VECTOR':
        n.inputs[0].default_value = (-0.25, -0.25, 0); n.inputs[1].default_value = (0.25, 0.25, 6.3)

# a few loose stones by his head that bounce when the rail vibrates (keyed in 02)
for i in range(7):
    s = stone_mesh("TR_Hop%d" % i, 0.022 + 0.004 * (i % 3), 40 + i)
    s.hide_render = False; s.hide_viewport = False
    s.location = (RX + 0.18 + 0.05 * (i % 3), -0.35 - 0.16 * i, 0.012)

# ================================================================== distance: houses, trees, shrubs, poles
M_PL_BLUE = pbr("M_PlBlue", "blue_plaster_wall", scale=0.5, tint_=(0.6, 0.9, 1.4), bump=0.3)
M_PL_WARM = pbr("M_PlWarm", "beige_wall_002", scale=0.5, tint_=(1.45, 0.75, 0.35), bump=0.3)
M_PL_PINK = pbr("M_PlPink", "beige_wall_002", scale=0.5, tint_=(1.4, 0.55, 0.65), bump=0.3)
M_PL_YEL = pbr("M_PlYel", "beige_wall_002", scale=0.5, tint_=(1.45, 1.15, 0.30), bump=0.3)
M_ROOF = pbr("M_Roof", "clay_roof_tiles", scale=0.6, tint_=(1.25, 0.55, 0.35), bump=0.5)
M_WIN = mat("M_Window", (0.05, 0.10, 0.16), rough=0.08, metal=0.0, coat=0.8)
M_FRAME = mat("M_Frame", (0.92, 0.92, 0.90), rough=0.4)
def house(name, x, y, w, d, h, wall, rot=0.0):
    root = bpy.data.objects.new(name, None); C_SET.objects.link(root)
    b = box(name + "_Body", (w, d, h), (0, 0, h / 2), wall, bevel=0.03); b.parent = root; to_col(b, C_SET)
    # gable roof: a prism with overhang
    bm = bmesh.new(); ov = 0.35; rh = h * 0.45
    pts = [(-w / 2 - ov, -d / 2 - ov, h - 0.05), (w / 2 + ov, -d / 2 - ov, h - 0.05), (w / 2 + ov, 0, h + rh), (-w / 2 - ov, 0, h + rh),
           (-w / 2 - ov, d / 2 + ov, h - 0.05), (w / 2 + ov, d / 2 + ov, h - 0.05)]
    V = [bm.verts.new(p) for p in pts]
    bm.faces.new((V[0], V[1], V[2], V[3])); bm.faces.new((V[3], V[2], V[5], V[4])); bm.faces.new((V[0], V[3], V[4])); bm.faces.new((V[1], V[5], V[2]))
    bm.faces.new((V[0], V[4], V[5], V[1]))
    me = bpy.data.meshes.new(name + "_Roof"); bm.to_mesh(me); bm.free()
    r = bpy.data.objects.new(name + "_Roof", me); C_SET.objects.link(r); me.materials.append(M_ROOF); r.parent = root
    so = r.modifiers.new("so", 'SOLIDIFY'); so.thickness = 0.08
    # gable wall triangles
    bm = bmesh.new()
    for sy in (-1, 1):
        V = [bm.verts.new((-w / 2, sy * d / 2 * 0 + 0, 0))]
    bm.free()
    for sy in (-1, 1):
        bm = bmesh.new(); yy = 0
        V = [bm.verts.new((sy * w / 2, -d / 2, h - 0.05)), bm.verts.new((sy * w / 2, d / 2, h - 0.05)), bm.verts.new((sy * w / 2, 0, h + rh - 0.05))]
        bm.faces.new(V); me = bpy.data.meshes.new(name + "_Gable"); bm.to_mesh(me); bm.free()
        g = bpy.data.objects.new(name + "_Gable", me); C_SET.objects.link(g); me.materials.append(wall); g.parent = root
        so = g.modifiers.new("so", 'SOLIDIFY'); so.thickness = 0.1
    # windows on the two long walls facing +-X, and a door
    for sx in (-1, 1):
        for i in range(max(1, int(d / 2.2))):
            for fl in range(max(1, int(h / 2.8))):
                yy = -d / 2 + (i + 0.5) * d / max(1, int(d / 2.2)); zz = 1.4 + fl * 2.8
                fr = box(name + "_WF", (0.06, 1.0, 1.3), (sx * (w / 2 + 0.01), yy, zz), M_FRAME, bevel=0.01); fr.parent = root
                gl = box(name + "_WG", (0.07, 0.86, 1.16), (sx * (w / 2 + 0.015), yy, zz), M_WIN, bevel=0.0); gl.parent = root
                to_col(fr, C_SET); to_col(gl, C_SET)
    root.location = (x, y, 0); root.rotation_euler.z = rot
    return root
HOUSES = [("H1", 19, -30, 7, 9, 5.6, M_PL_BLUE), ("H2", 21, -14, 6, 8, 3.0, M_PL_WARM), ("H3", 18, 4, 7, 10, 5.6, M_PL_YEL),
          ("H4", 20, 22, 6, 8, 3.0, M_PL_PINK), ("H5", 22, 40, 7, 9, 5.6, M_PL_BLUE), ("H6", -20, -24, 7, 9, 5.6, M_PL_PINK),
          ("H7", -22, -6, 6, 8, 3.0, M_PL_BLUE), ("H8", -19, 12, 7, 10, 5.6, M_PL_WARM), ("H9", -21, 30, 6, 8, 3.0, M_PL_YEL),
          ("H10", -20, 48, 7, 9, 5.6, M_PL_BLUE), ("H11", 20, 58, 7, 9, 5.6, M_PL_WARM), ("H12", -21, -44, 7, 9, 5.6, M_PL_YEL),
          ("H13", 20, -48, 6, 8, 3.0, M_PL_PINK)]
for n, x, y, w, d, h, m in HOUSES: house("BG_" + n, x, y, w, d, h, m)

def append_ph(asset, name, loc, rot_z=0.0, scale=1.0, collection=C_SET):
    d = os.path.join(PH, asset); blend = [f for f in os.listdir(d) if f.endswith(".blend")][0]
    with bpy.data.libraries.load(os.path.join(d, blend), link=False) as (src, dst):
        dst.objects = list(src.objects)
    objs = [o for o in dst.objects if o is not None and o.type == 'MESH']
    root = bpy.data.objects.new(name, None); collection.objects.link(root)
    for o in objs:
        collection.objects.link(o)
        if o.parent is None or o.parent not in objs: o.parent = root
    root.location = loc; root.rotation_euler.z = rot_z; root.scale = (scale,) * 3
    return root, objs
TREE0, TREE_P = append_ph("tree_small_02", "BG_Tree0", (-12, -10, 0), scale=1.4)
SHR0, SHR_P = append_ph("shrub_01", "BG_Shrub0", (7.5, -4, 0), scale=1.3)
SHR1, SHR1_P = append_ph("shrub_02", "BG_Shrub1", (-7.5, 6, 0), scale=1.3)
def inst(root, name, loc, rot_z, scale):
    e = bpy.data.objects.new(name, None); C_SET.objects.link(e); e.instance_type = 'COLLECTION'
    cn = root.name + "_C"
    c = bpy.data.collections.get(cn)
    if c is None:
        c = bpy.data.collections.new(cn)
        for o in [root] + [o for o in bpy.data.objects if o.parent == root]:
            c.objects.link(o)
        root.location = (0, 0, 0); root.rotation_euler.z = 0; root.scale = (1, 1, 1)
        for o in [root] + [o for o in bpy.data.objects if o.parent == root]:
            for cc in list(o.users_collection):
                if cc != c: cc.objects.unlink(o)
    e.instance_collection = c; e.location = loc; e.rotation_euler.z = rot_z; e.scale = (scale,) * 3
    return e
rnd = random.Random(7)
for i in range(22):
    sx = -1 if i % 2 else 1
    inst(TREE0, "BG_TreeI%d" % i, (sx * rnd.uniform(11, 16), -60 + i * 6.5 + rnd.uniform(-2, 2), 0), rnd.uniform(0, 6.3), rnd.uniform(1.2, 1.7))
for i in range(30):
    sx = -1 if i % 2 else 1
    r_ = SHR0 if i % 3 else SHR1
    inst(r_, "BG_ShrubI%d" % i, (sx * rnd.uniform(6.5, 9.5), -50 + i * 3.6 + rnd.uniform(-1, 1), 0), rnd.uniform(0, 6.3), rnd.uniform(1.0, 1.6))
for C in [c for c in bpy.data.collections if c.name.endswith("_C")]:
    if C.name not in [cc.name for cc in sc.collection.children_recursive]:
        pass  # instance-only collections stay unlinked from the scene (rendered through the instancers)

# overhead-line-free poles: simple wooden fence posts along the path (readable scale cue, nothing at the lens)
M_POST = pbr("M_Post", "old_planks_02", scale=2.0, tint_=(0.8, 0.6, 0.45), bump=0.3)
post = cyl("BG_FencePost", 0.06, 1.1, (-5.0, Y0, 0.55), M_POST, verts=10)
ar = post.modifiers.new("arr", 'ARRAY'); ar.fit_type = 'FIT_LENGTH'; ar.fit_length = Y1 - Y0; ar.use_relative_offset = False
ar.use_constant_offset = True; ar.constant_offset_displace = (0, 2.5, 0); to_col(post, C_SET)
rail_f = box("BG_FenceRail", (0.05, Y1 - Y0, 0.08), (-5.0, (Y0 + Y1) / 2, 0.95), M_POST, bevel=0.01); to_col(rail_f, C_SET)
rail_f2 = box("BG_FenceRail2", (0.05, Y1 - Y0, 0.08), (-5.0, (Y0 + Y1) / 2, 0.55), M_POST, bevel=0.01); to_col(rail_f2, C_SET)

# ================================================================== the train (ONE train; parented to the keyed empty `Train`)
TRAIN = bpy.data.objects.new("Train", None); C_TRAIN.objects.link(TRAIN)
def imp_glb(path, drop=()):
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
    keep = []
    for o in new:
        if o.type != 'MESH' or any(k in o.name for k in drop): bpy.data.objects.remove(o, do_unlink=True)
        else: keep.append(o)
    for o in keep:
        bpy.context.view_layer.objects.active = o; o.select_set(True)
    bpy.ops.object.select_all(action='DESELECT')
    for o in keep: o.select_set(True)
    bpy.context.view_layer.objects.active = keep[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return keep
# ---- locomotive: model long axis X -> track +Y (front = +Y). Drop the loose display wheel set.
LOCO_P = imp_glb(os.path.join(GLB, "loco.glb"), drop=("rama_Wheel frame", "wheels.006", "wheels.007"))
S_L = 1.75
def bb(objs):
    import numpy as np
    arrs = []
    for o in objs:
        n = len(o.data.vertices); co = np.empty(n * 3, dtype=np.float64); o.data.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3); M = np.array(o.matrix_world); arrs.append(co @ M[:3, :3].T + M[:3, 3])
    A = np.concatenate(arrs); return Vector(A.min(0)), Vector(A.max(0))
def bb_old(objs):
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    return Vector([min(v[i] for v in pts) for i in range(3)]), Vector([max(v[i] for v in pts) for i in range(3)])
mn, mx = bb(LOCO_P)
# which end is the cab front with the headlights: the model's +X end has the lamps (thumbnail); front -> +Y
wheels = [o for o in LOCO_P if "wheel pair" in o.name]
wmn, wmx = bb(wheels)
cx = (mn.x + mx.x) / 2; cy = (wmn.y + wmx.y) / 2
M_loco = Matrix.Rotation(math.radians(90), 4, 'Z') @ Matrix.Scale(S_L, 4) @ Matrix.Translation((-cx, -cy, -wmn.z))
for o in LOCO_P:
    o.data.transform(M_loco); o.matrix_world = Matrix.Identity(4)
mn, mx = bb(LOCO_P)
LOCO_LEN = mx.y - mn.y
for o in LOCO_P:
    o.data.transform(Matrix.Translation((0, -mx.y, RT))); o.parent = TRAIN; to_col(o, C_TRAIN)   # front face at y=0 (Train origin)
mn, mx = bb(LOCO_P)
print("LOCO", "len", round(LOCO_LEN, 2), "min", mn, "max", mx)
# brighten / saturate the dark model materials (deep green body with a red band reads well; lift it)
def lift_mats(objs, mult, rough_min=0.35):
    done = set()
    for o in objs:
        for m in o.data.materials:
            if not m or m.name in done or not m.use_nodes: continue
            done.add(m.name)
            for nd in list(m.node_tree.nodes):
                if nd.type == 'TEX_IMAGE' and nd.image:
                    is_col = nd.image.colorspace_settings.name == 'sRGB'
                    for lk in list(nd.outputs['Color'].links):
                        if is_col and lk.to_socket.name == "Base Color":
                            mx_ = m.node_tree.nodes.new('ShaderNodeMix'); mx_.data_type = 'RGBA'; mx_.blend_type = 'MULTIPLY'
                            mx_.inputs['Factor'].default_value = 1.0; mx_.inputs['B'].default_value = (*mult, 1)
                            m.node_tree.links.new(nd.outputs['Color'], mx_.inputs['A']); m.node_tree.links.new(mx_.outputs['Result'], lk.to_socket)
                if nd.type == 'BSDF_PRINCIPLED':
                    if not nd.inputs["Base Color"].is_linked:
                        c = nd.inputs["Base Color"].default_value; nd.inputs["Base Color"].default_value = (min(1, c[0] * mult[0]), min(1, c[1] * mult[1]), min(1, c[2] * mult[2]), 1)
                    if not nd.inputs["Roughness"].is_linked: nd.inputs["Roughness"].default_value = max(rough_min, nd.inputs["Roughness"].default_value)
lift_mats([o for o in LOCO_P if "Korpus" in o.name], (2.6, 2.6, 2.2))
lift_mats([o for o in LOCO_P if "Korpus" not in o.name], (1.6, 1.6, 1.6))
# headlight: emissive disc + a spot (front centre, upper) and two lower marker lamps
fl = mx.y
HL = cyl("TN_Headlight", 0.16, 0.05, (0, fl + 0.02, RT + 3.25), mat("M_HeadLamp", (1, 1, 1), emit=((1.0, 0.95, 0.80), 60.0)), rot=(math.radians(90), 0, 0))
HL.parent = TRAIN; to_col(HL, C_TRAIN)
spot = bpy.data.lights.new("TN_HeadSpot", 'SPOT'); spot.energy = 3500; spot.spot_size = math.radians(40); spot.color = (1.0, 0.95, 0.82)
SP = bpy.data.objects.new("TN_HeadSpot", spot); C_TRAIN.objects.link(SP); SP.location = (0, fl + 0.3, RT + 3.2)
SP.rotation_euler = (math.radians(-80), 0, 0); SP.parent = TRAIN
SP.rotation_euler = Vector((0, 1, -0.25)).to_track_quat('-Z', 'Z').to_euler()

# ---- container flat wagons (procedural deck + the imported wagon's real wheel sets as bogies)
WAG_P = imp_glb(os.path.join(GLB, "wagon.glb"))
WHEELS = [o for o in WAG_P if "weels" in o.name]
for o in WAG_P:
    if o not in WHEELS: bpy.data.objects.remove(o, do_unlink=True)
# one wheel set (2 axles in the model are separate objects; take one bogie pair = two objects nearest each other)
WHEELS.sort(key=lambda o: bb([o])[0].y)
bogie_src = WHEELS[:2]
bmn, bmx = bb(bogie_src); bcy = (bmn.y + bmx.y) / 2
for o in bogie_src: o.data.transform(Matrix.Translation((0, -bcy, -bmn.z)))
for o in WHEELS[2:]: bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.object.select_all(action='DESELECT')
for o in bogie_src: o.select_set(True)
bpy.context.view_layer.objects.active = bogie_src[0]; bpy.ops.object.join()
BOGIE = bpy.context.active_object; BOGIE.name = "TN_BogieSrc"
lift_mats([BOGIE], (1.5, 1.5, 1.5))
bmn, bmx = bb([BOGIE]); print("BOGIE", bmn, bmx)
M_DECK = mat("M_Deck", (0.10, 0.10, 0.11), rough=0.55, metal=0.4)
M_SILL = mat("M_Sill", (0.06, 0.07, 0.09), rough=0.5, metal=0.5, coat=0.1)        # dark steel underframe (no colour block)
CONT_COLS = [(0.02, 0.18, 0.75), (0.85, 0.55, 0.02), (0.75, 0.05, 0.05), (0.02, 0.45, 0.22)]
LOGO_IMG = bpy.data.images.load("/home/user/Muhammed/blender/assets/brand/DaKrasFilms_logo_white.png"); LOGO_IMG.name = "logo_white"
WAG_LEN, WAG_GAP = 15.0, 1.2
DECK_Z = RT + 1.15
def wagon(i, y_front):
    yc = y_front - WAG_LEN / 2
    parts = []
    parts.append(box("TN_W%d_Deck" % i, (2.7, WAG_LEN, 0.10), (0, yc, DECK_Z), M_DECK, bevel=0.01))
    for sx in (-1, 1):
        parts.append(box("TN_W%d_Sill" % i, (0.10, WAG_LEN, 0.36), (sx * 1.33, yc, DECK_Z - 0.20), M_SILL, bevel=0.012))
    parts.append(box("TN_W%d_Centre" % i, (0.35, WAG_LEN - 0.4, 0.32), (0, yc, DECK_Z - 0.22), M_SILL, bevel=0.012))
    for e in (-1, 1):
        parts.append(box("TN_W%d_End" % i, (2.7, 0.18, 0.40), (0, yc + e * (WAG_LEN / 2 - 0.09), DECK_Z - 0.18), M_SILL, bevel=0.012))
        parts.append(cyl("TN_W%d_Buffer" % i, 0.13, 0.5, (0.0, yc + e * (WAG_LEN / 2 + 0.2), DECK_Z - 0.2), M_DECK, rot=(math.radians(90), 0, 0), verts=16))
        b = BOGIE.copy(); b.data = BOGIE.data; b.name = "TN_W%d_Bogie" % i; C_TRAIN.objects.link(b)
        b.location = (0, yc + e * (WAG_LEN / 2 - 2.4), RT - 0.0); parts.append(b)
        # bolster under the deck above the bogie
        parts.append(box("TN_W%d_Bolster" % i, (2.2, 0.5, 0.30), (0, yc + e * (WAG_LEN / 2 - 2.4), DECK_Z - 0.35), M_DECK, bevel=0.01))
    # two 6 m containers on the deck
    for k in range(2):
        cy_ = yc + (k - 0.5) * 6.4
        cm = corrugated("M_Cont%d_%d" % (i, k), CONT_COLS[(2 * i + k) % 4])
        c = box("TN_W%d_Cont%d" % (i, k), (2.44, 6.06, 2.59), (0, cy_, DECK_Z + 0.05 + 1.295), cm, bevel=0.02)
        parts.append(c)
        # corner castings + top rails (dark)
        for sx in (-1, 1):
            parts.append(box("TN_W%d_CRail" % i, (0.06, 6.06, 0.12), (sx * 1.20, cy_, DECK_Z + 0.05 + 2.55), M_DECK, bevel=0.01))
            parts.append(box("TN_W%d_CRailB" % i, (0.06, 6.06, 0.12), (sx * 1.20, cy_, DECK_Z + 0.11), M_DECK, bevel=0.01))
    for p in parts:
        p.parent = TRAIN; to_col(p, C_TRAIN)
    return parts
W1_FRONT = -(LOCO_LEN + WAG_GAP)
W2_FRONT = W1_FRONT - WAG_LEN - WAG_GAP
WAG1 = wagon(1, W1_FRONT); WAG2 = wagon(2, W2_FRONT)
BOGIE.location = (0, 0, -60); BOGIE.hide_render = True; BOGIE.hide_viewport = True; BOGIE.parent = None
# the logo on the -X side of wagon 1's front container (blue): a decal plane just off the corrugated wall
def logo_decal(name, cont, side=-1):
    cmn, cmx = bb([cont]); cy_ = (cmn.y + cmx.y) / 2; cz = (cmn.z + cmx.z) / 2
    bpy.ops.mesh.primitive_plane_add(size=1, location=(side * (cmx.x + 0.012), cy_, cz + 0.2))
    d = bpy.context.active_object; d.name = name
    asp = LOGO_IMG.size[0] / LOGO_IMG.size[1]
    d.scale = (3.6, 3.6 / asp, 1); d.rotation_euler = (math.radians(90), 0, math.radians(-90 if side < 0 else 90))
    bpy.ops.object.transform_apply(scale=True, rotation=False, location=False)
    m = bpy.data.materials.new("M_LogoDecal"); m.use_nodes = True; nt = m.node_tree
    P = nt.nodes["Principled BSDF"]; t = nt.nodes.new("ShaderNodeTexImage"); t.image = LOGO_IMG; t.extension = 'CLIP'
    nt.links.new(t.outputs["Color"], P.inputs["Base Color"]); nt.links.new(t.outputs["Alpha"], P.inputs["Alpha"])
    P.inputs["Roughness"].default_value = 0.4
    try: m.blend_method = 'HASHED'
    except Exception: pass
    d.data.materials.append(m); d.parent = TRAIN; to_col(d, C_TRAIN)
    return d
LOGO_DECAL = logo_decal("TN_LogoDecal", [p for p in WAG1 if p.name.startswith("TN_W1_Cont0")][0], side=-1)
# wheel sparks: emissive streak cards at every wheel tread on the rails (scaled up when braking, keyed in 02)
M_SPARK = mat("M_Spark", (1.0, 0.6, 0.1), emit=((1.0, 0.55, 0.12), 40.0))
SPARKS = []
for o in [p for p in WAG1 + WAG2 if "Bogie" in p.name]:
    for ax in (-0.9, 0.9):
        for sx in (-1, 1):
            g = bpy.data.objects.new("TN_SparkSet", None); C_TRAIN.objects.link(g); g.parent = TRAIN
            g.location = (sx * RX, o.location.y + ax, RT + 0.01)
            rr = random.Random(len(SPARKS))
            for k in range(9):
                c = cyl("TN_Spark", 0.004, 0.16 + 0.12 * rr.random(), (0, 0, 0), M_SPARK, verts=5)
                c.rotation_euler = (math.radians(90 - 25 * rr.random()), 0, math.radians(rr.uniform(-25, 25)))
                c.location = (rr.uniform(-0.05, 0.05), -0.12 - 0.25 * rr.random(), 0.03 + 0.12 * rr.random())
                c.parent = g; to_col(c, C_TRAIN)
            to_col(g, C_TRAIN); SPARKS.append(g)
print("SPARK_SETS", len(SPARKS))

# ================================================================== the bottle (ONE object; held by the man, then dropped)
before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=os.path.join(GLB, "bottle.glb"))
BOT = [o for o in bpy.data.objects if o not in before and o.type == 'MESH'][0]
for o in [o for o in bpy.data.objects if o not in before and o != BOT]: bpy.data.objects.remove(o, do_unlink=True)
mw = BOT.matrix_world.copy(); BOT.parent = None; BOT.matrix_world = mw
bpy.context.view_layer.objects.active = BOT; BOT.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bmn, bmx = bb([BOT]); s_ = 0.30 / (bmx.z - bmn.z)
BOT.data.transform(Matrix.Scale(s_, 4) @ Matrix.Translation((-(bmn.x + bmx.x) / 2, -(bmn.y + bmx.y) / 2, -bmn.z)))
BOT.name = "Bottle"; to_col(BOT, C_PEOPLE)
M_BOT = bpy.data.materials.new("M_BottleGlass"); M_BOT.use_nodes = True; P = M_BOT.node_tree.nodes["Principled BSDF"]
P.inputs["Base Color"].default_value = (0.05, 0.55, 0.12, 1); P.inputs["Roughness"].default_value = 0.08
P.inputs["Transmission Weight"].default_value = 0.55; P.inputs["IOR"].default_value = 1.45; P.inputs["Coat Weight"].default_value = 0.5
BOT.data.materials.clear(); BOT.data.materials.append(M_BOT)
for p in BOT.data.polygons: p.use_smooth = True
BOT.location = (0, 0, -40)

# ================================================================== EXPLAINER: muscle fibres on a sky gradient
M_SKY = bpy.data.materials.new("M_ExpSky"); M_SKY.use_nodes = True; nt = M_SKY.node_tree
for n in list(nt.nodes):
    if n.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n)
tc = nt.nodes.new("ShaderNodeTexCoord"); sp_ = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sp_.inputs[0])
mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = -8; mr.inputs["From Max"].default_value = 10
nt.links.new(sp_.outputs["Z"], mr.inputs["Value"])
cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (0.55, 0.92, 1.0, 1); cr.color_ramp.elements[1].color = (0.0, 0.30, 1.0, 1)
nt.links.new(mr.outputs["Result"], cr.inputs["Fac"])
em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Strength"].default_value = 1.4; nt.links.new(cr.outputs["Color"], em.inputs["Color"])
nt.links.new(em.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
bpy.ops.mesh.primitive_uv_sphere_add(radius=14, location=EX, segments=48, ring_count=24)
DOME = bpy.context.active_object; DOME.name = "EX_Dome"; DOME.data.materials.append(M_SKY); to_col(DOME, C_EXP)
bpy.ops.object.shade_smooth()
DOME.visible_shadow = False
# muscle fibre material: glossy red with fine striations along the fibre (wave bands across the length)
def muscle_mat(name, c1, c2):
    m = mat(name, c1, rough=0.28, sss=0.15, coat=0.5); nt = m.node_tree; P = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); wv = nt.nodes.new("ShaderNodeTexWave"); wv.wave_type = 'BANDS'; wv.bands_direction = 'X'
    wv.inputs["Scale"].default_value = 60.0; wv.inputs["Distortion"].default_value = 1.5
    nt.links.new(tc.outputs["Object"], wv.inputs["Vector"])
    cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (*c1, 1); cr.color_ramp.elements[1].color = (*c2, 1)
    nt.links.new(wv.outputs["Fac"], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], P.inputs["Base Color"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.25; bp.inputs["Distance"].default_value = 0.002
    nt.links.new(wv.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], P.inputs["Normal"])
    return m
M_MUS = muscle_mat("M_Muscle", (0.50, 0.005, 0.02), (0.90, 0.05, 0.06))
M_TEN = mat("M_Tendon", (0.95, 0.92, 0.85), rough=0.25, coat=0.6, sheen=0.2)
M_FASC = bpy.data.materials.new("M_Fascia"); M_FASC.use_nodes = True; P = M_FASC.node_tree.nodes["Principled BSDF"]
P.inputs["Base Color"].default_value = (1.0, 0.75, 0.75, 1); P.inputs["Roughness"].default_value = 0.15; P.inputs["Alpha"].default_value = 0.22
P.inputs["Coat Weight"].default_value = 0.8
# one muscle bundle along X (length 1.6 m in explainer units), made of 19 spindle fibres + 2 tendons; deformed by a lattice
MUS_LEN = 1.6
def spindle(name, r, length, off, segs=48, ring=10, m=M_MUS):
    bm = bmesh.new(); rings = []
    for i in range(segs + 1):
        u = i / segs; x = -length / 2 + u * length
        rr = r * (math.sin(math.pi * u) ** 0.6) + 0.004
        ring_ = [bm.verts.new((x, off[0] + rr * math.cos(2 * math.pi * k / ring), off[1] + rr * math.sin(2 * math.pi * k / ring))) for k in range(ring)]
        rings.append(ring_)
    for i in range(segs):
        for k in range(ring):
            bm.faces.new((rings[i][k], rings[i][(k + 1) % ring], rings[i + 1][(k + 1) % ring], rings[i + 1][k]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); C_EXP.objects.link(o); me.materials.append(m)
    for p in me.polygons: p.use_smooth = True
    return o
fibres = []
rr = random.Random(11)
for k in range(19):
    ang = 2 * math.pi * k / 7 if k < 7 else (2 * math.pi * k / 12 if k < 19 else 0)
    rad = 0.0 if k == 0 else (0.075 if k < 7 else 0.15)
    off = (rad * math.cos(ang) + rr.uniform(-0.01, 0.01), rad * math.sin(ang) + rr.uniform(-0.01, 0.01))
    fibres.append(spindle("EX_Fibre%d" % k, 0.07 + rr.uniform(-0.01, 0.01), MUS_LEN * rr.uniform(0.92, 1.0), off))
for e in (-1, 1):
    t = spindle("EX_Tendon", 0.05, 0.45, (0, 0), segs=12, ring=12, m=M_TEN)
    for v in t.data.vertices: v.co.x += e * (MUS_LEN / 2 + 0.12)
    fibres.append(t)
bpy.ops.object.select_all(action='DESELECT')
for o in fibres: o.select_set(True)
bpy.context.view_layer.objects.active = fibres[0]; bpy.ops.object.join()
MUS = bpy.context.active_object; MUS.name = "EX_Muscle"; MUS.location = EX + Vector((0, 0, 0)); MUS.rotation_euler = (0, math.radians(90), 0)
# anchors: two white bone knobs the tendons attach to (the muscle hangs between them like a rope)
M_BONE = mat("M_Bone", (0.96, 0.93, 0.84), rough=0.35, coat=0.4)
for e in (-1, 1):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.16, location=EX + Vector((0, 0, e * (MUS_LEN / 2 + 0.40))))
    kb = bpy.context.active_object; kb.name = "EX_Knob"; kb.data.materials.append(M_BONE); bpy.ops.object.shade_smooth(); to_col(kb, C_EXP)
    kb.scale = (1.3, 1.0, 0.85)
# the lattice (8 points along X) with shape keys: sag (loose hang), swayA/swayB (side sway), flow (bent along the arrow)
lat = bpy.data.lattices.new("EX_LatticeD"); lat.points_u = 8; lat.points_v = 2; lat.points_w = 2
lat.interpolation_type_u = 'KEY_BSPLINE'
LAT = bpy.data.objects.new("EX_Lattice", lat); C_EXP.objects.link(LAT)
LAT.location = EX; LAT.scale = ((MUS_LEN + 0.9) / 7.0, 0.5, 0.5); LAT.rotation_euler = (0, math.radians(90), 0)
lm = MUS.modifiers.new("lat", 'LATTICE'); lm.object = LAT
LAT.shape_key_add(name="Basis")
def lkey(name, fn):
    k = LAT.shape_key_add(name=name, from_mix=False)
    for i, p in enumerate(lat.points):
        u = (p.co_deform.x + 3.5) / 7.0              # 0..1 along the muscle (lattice coords run -3.5..3.5 for 8 points)
        d = fn(u); k.data[i].co = p.co_deform + Vector(d)
    return k
# lattice local z = world +X after the 90 deg turn (screen horizontal): the vertical bundle bows sideways like a rope
sag = lkey("sag", lambda u: (0, 0.06 * math.sin(math.pi * u), 0.18 * math.sin(2 * math.pi * u)))
swA = lkey("swayA", lambda u: (0, 0.0, 0.85 * math.sin(math.pi * u) + 0.15 * math.sin(2 * math.pi * u)))
swB = lkey("swayB", lambda u: (0, 0.0, -0.85 * math.sin(math.pi * u) + 0.12 * math.sin(2 * math.pi * u)))
flo = lkey("flow", lambda u: (0, 0.0, -1.6 * math.sin(math.pi * u)))
# the force arrow (glossy orange-yellow), pointing down at the muscle; keyed in 02
M_ARROW = mat("M_Arrow", (1.0, 0.30, 0.0), rough=0.3, coat=0.4, emit=((1.0, 0.25, 0.0), 0.4))
shaft = cyl("EX_ArrowShaft", 0.07, 0.9, (0, 0, 0.45), M_ARROW, verts=32, bevel=0.01)
bpy.ops.mesh.primitive_cone_add(radius1=0.17, radius2=0.0, depth=0.34, vertices=32, location=(0, 0, -0.17), rotation=(math.pi, 0, 0))
head = bpy.context.active_object; head.data.materials.append(M_ARROW); bpy.ops.object.shade_smooth()
bpy.ops.object.select_all(action='DESELECT'); shaft.select_set(True); head.select_set(True); bpy.context.view_layer.objects.active = shaft
bpy.ops.object.join(); ARROW = bpy.context.active_object; ARROW.name = "EX_Arrow"; to_col(ARROW, C_EXP)
ARROW.location = EX + Vector((3.2, 0, 0)); ARROW.rotation_euler = (0, math.radians(90), 0)
for o in (MUS, LAT): to_col(o, C_EXP)
# explainer lights: soft key from front-left-top, fill right, warm rim behind
def light(name, kind, energy, loc, rot=(0, 0, 0), size=1.0, color=(1, 1, 1), c=C_SET):
    L = bpy.data.lights.new(name, kind); L.energy = energy; L.color = color
    if kind == 'AREA': L.size = size; L.shape = 'DISK'
    if kind == 'SUN': L.angle = math.radians(2.5)
    o = bpy.data.objects.new(name, L); c.objects.link(o); o.location = loc; o.rotation_euler = rot
    return o
def aim(o, tgt):
    o.rotation_euler = (Vector(tgt) - o.location).to_track_quat('-Z', 'Y').to_euler()
k1 = light("EX_Key", 'AREA', 260, EX + Vector((-1.5, -2.6, 2.0)), size=1.5, color=(1.0, 0.97, 0.93), c=C_EXP); aim(k1, EX)
k2 = light("EX_Fill", 'AREA', 140, EX + Vector((2.2, -2.0, 0.5)), size=2.0, color=(0.9, 0.95, 1.0), c=C_EXP); aim(k2, EX)
k3 = light("EX_Rim", 'AREA', 200, EX + Vector((0.0, 2.0, 2.2)), size=1.5, color=(1.0, 0.88, 0.75), c=C_EXP); aim(k3, EX)
for L_ in (k1, k2, k3):
    L_.data.use_shadow = True

# ================================================================== daylight
SUN = light("SN_Sun", 'SUN', 5.0, (0, 0, 20), rot=(math.radians(48), 0, math.radians(-142)), color=(1.0, 0.92, 0.80))
sc.render.engine = 'CYCLES'; cy = sc.cycles
cy.samples = 64; cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.05
cy.use_denoising = True; cy.denoiser = 'OPENIMAGEDENOISE'
cy.max_bounces = 6; cy.diffuse_bounces = 3; cy.glossy_bounces = 3; cy.transmission_bounces = 6; cy.transparent_max_bounces = 16
cy.caustics_reflective = False; cy.caustics_refractive = False
sc.render.use_persistent_data = True
sc.render.use_simplify = True; sc.render.simplify_subdivision_render = 2; cy.texture_limit_render = '2048'
sc.render.use_motion_blur = False
sc.view_settings.view_transform = 'AgX'
try: sc.view_settings.look = 'AgX - Punchy'
except Exception: sc.view_settings.look = 'Punchy'
sc.view_settings.exposure = 0.0
sc.world = sc.world or bpy.data.worlds.new("World")
w = sc.world; w.use_nodes = True; nt = w.node_tree
for n in list(nt.nodes):
    if n.type != 'OUTPUT_WORLD': nt.nodes.remove(n)
hd = [f for f in os.listdir(os.path.join(PH, "hdri")) if f.endswith(".hdr")][0]
env = nt.nodes.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(os.path.join(PH, "hdri", hd))
mp = nt.nodes.new("ShaderNodeMapping"); tc = nt.nodes.new("ShaderNodeTexCoord"); mp.inputs["Rotation"].default_value = (0, 0, math.radians(110))
nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"]); nt.links.new(mp.outputs["Vector"], env.inputs["Vector"])
hs = nt.nodes.new("ShaderNodeHueSaturation"); hs.inputs["Saturation"].default_value = 1.35; nt.links.new(env.outputs["Color"], hs.inputs["Color"])
bg = nt.nodes.new("ShaderNodeBackground"); bg.inputs["Strength"].default_value = 1.1; nt.links.new(hs.outputs["Color"], bg.inputs["Color"])
nt.links.new(bg.outputs[0], [n for n in nt.nodes if n.type == 'OUTPUT_WORLD'][0].inputs["Surface"])
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("BUILD_DONE", OUT)
