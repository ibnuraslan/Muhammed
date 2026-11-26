"""ToddlerWell v010 stage A (from scratch): three people, one cut-away well, one excavator.
blender -b --python 01_build.py -- <asset_dir> <polyhaven_dir> <out.blend>

The set is a diorama cut-away: a farm field (ground top z=0) whose earth block lies at y>0; its front face (the cut
plane y=0) shows the soil strata. The well shaft (radius 0.40) is centred on the cut plane at x=0, so its back half is
an open groove in the cut face, 9 m deep (bottom z=-9). A steel casing ring sticks 0.14 m out of the ground. A second,
shallow pit (the dig) sits beside it at x=+1.7, its depth driven by the keyed empty PitCtl (boolean cutter scale).
The camera always stays at y<0, looking at +Y. Everyone stands on y>0 ground; the toddler and the teen go down the shaft.
"""
import bpy, bmesh, sys, math, random, os
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "lib_build.py")).read())
a = sys.argv[sys.argv.index("--") + 1:]
AS, PH, OUT = a[0], a[1], a[2]
PKG = os.path.dirname(HERE)
random.seed(17)
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
sc = bpy.context.scene
sc.render.fps = 60
sc.frame_start, sc.frame_end = 1, 1728
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
R_SH, Z_BOT = 0.40, -9.0

def col(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in sc.collection.children: sc.collection.children.link(c)
    return c
C_PPL, C_SET = col("PEOPLE"), col("SET")
def to_col(o, c):
    for cc in list(o.users_collection): cc.objects.unlink(o)
    c.objects.link(o)

# ================================================================== people (ONE model each for the whole film)
def solid_clothes(rig):
    for c in rig.children:
        if c.type == 'MESH' and any(k in c.name.lower() for k in ("suit", "shoes")):
            so = c.modifiers.new("solid", 'SOLIDIFY'); so.thickness = 0.003; so.offset = 1.0; so.use_rim = True
            i = c.modifiers.find("solid")
            while i > c.modifiers.find("Armature") + 1:
                c.modifiers.move(i, i - 1); i -= 1

def recolor_clothes(rig, key, mult):
    for c in rig.children:
        if c.type == 'MESH' and key in c.name.lower():
            for m in c.data.materials: tint(m, mult)

def person(name, gender, age, race, hair, skin, brow, clothes, skin_tint, hair_tint, **kw):
    rig, body = human(name, gender, age, race, hair, skin, brow, clothes=clothes, **kw)
    eye_fix(rig)
    for m in body.data.materials: tint(m, skin_tint)
    for c in rig.children:
        if c.type == 'MESH' and any(k in c.name.lower() for k in (hair.split("/")[0], "eyebrow")):
            for m in c.data.materials: tint(m, hair_tint)
        if c.type == 'MESH' and "teeth" in c.name:
            for m in c.data.materials: tint(m, (1.5, 1.45, 1.4))
    solid_clothes(rig)
    for c in rig.children: to_col(c, C_PPL)
    to_col(rig, C_PPL)
    return rig, body

# the toddler: about 3 years old, blue shirt and jeans
TOD, TODB = person("Toddler", 1.0, 0.035, {"asian": 0.1, "caucasian": 0.8, "african": 0.1}, "short02/short02.mhclo",
                   "young_caucasian_male/young_caucasian_male.mhmat", "eyebrow001/eyebrow001.mhclo",
                   ["male_casualsuit01/male_casualsuit01.mhclo", "shoes02/shoes02.mhclo"], (0.98, 0.74, 0.60), (0.55, 0.36, 0.18),
                   height=0.5, weight=0.65, muscle=0.4, prop=0.5)
# the teen: about 16, red shirt
TEEN, TEENB = person("Teen", 1.0, 0.30, {"asian": 0.1, "caucasian": 0.45, "african": 0.45}, "short04/short04.mhclo",
                     "young_african_male/young_african_male.mhmat", "eyebrow001/eyebrow001.mhclo",
                     ["male_casualsuit02/male_casualsuit02.mhclo", "shoes01/shoes01.mhclo"], (0.85, 0.62, 0.48), (0.12, 0.08, 0.05),
                     height=0.55, weight=0.35, muscle=0.5)
# the rescuer: orange work suit and a yellow hard hat
RES, RESB = person("Rescuer", 1.0, 0.62, {"asian": 0.2, "caucasian": 0.7, "african": 0.1}, "short02/short02.mhclo",
                   "middleage_caucasian_male/middleage_caucasian_male.mhmat", "eyebrow001/eyebrow001.mhclo",
                   ["male_worksuit01/male_worksuit01.mhclo", "shoes03/shoes03.mhclo"], (0.95, 0.70, 0.56), (0.25, 0.17, 0.10),
                   height=0.55, weight=0.6, muscle=0.6)
eye_group_fix()
recolor_clothes(RES, "worksuit", (1.55, 1.45, 0.10))      # hi-vis yellow shirt, olive overalls (never skin-toned)
tee = bpy.data.images.load(os.path.join(PKG, "assets/tex/teen_tee_diffuse.png")); tee.name = "teen_tee_diffuse"
for c in TEEN.children:
    if c.type == 'MESH' and "casualsuit" in c.name:
        c.name = "Teen.clothes"
        for m in c.data.materials:
            for nd in m.node_tree.nodes:
                if nd.type == 'TEX_IMAGE' and nd.image and "diffuse" in nd.image.name.lower(): nd.image = tee
                if nd.type == 'NORMAL_MAP': nd.inputs["Strength"].default_value = 0.4
for rig, x in ((TOD, 3.0), (TEEN, -6.0), (RES, -1.0)):
    rig.location = (x, 1.0, 0.0)

# hard hat on the rescuer (CC-BY asset), parented to the head bone
HAT = imp(os.path.join(AS, "helmet.glb"), "RES_HardHat", target_dim=0.33, axis=1)
to_col(HAT, C_PPL)
for m in HAT.data.materials:
    p = m.node_tree.nodes.get("Principled BSDF")
    if p:
        for l in list(p.inputs["Base Color"].links): m.node_tree.links.remove(l)
        p.inputs["Base Color"].default_value = (0.95, 0.62, 0.02, 1); p.inputs["Roughness"].default_value = 0.35
        p.inputs["Metallic"].default_value = 0.0

# ================================================================== materials
def imgmat(name, folder, ident, scale=1.0, tint_=(1, 1, 1), rough=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (scale, scale, scale)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    tex = os.path.join(PH, folder, "textures")
    di = nt.nodes.new("ShaderNodeTexImage"); di.image = bpy.data.images.load(os.path.join(tex, ident + "_diff_1k.jpg"))
    nt.links.new(mp.outputs["Vector"], di.inputs["Vector"])
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
    mx.inputs['B'].default_value = (*tint_, 1)
    nt.links.new(di.outputs["Color"], mx.inputs["A"]); nt.links.new(mx.outputs["Result"], p.inputs["Base Color"])
    p.inputs["Roughness"].default_value = rough if rough is not None else 0.85
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.35; bp.inputs["Distance"].default_value = 0.01
    nt.links.new(di.outputs["Color"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], p.inputs["Normal"])
    return m

M_GRASS = imgmat("M_Field", "aerial_grass_rock", "aerial_grass_rock", scale=0.25, tint_=(0.95, 1.05, 0.55))
M_MUD = imgmat("M_Mud", "brown_mud_leaves_01", "brown_mud_leaves_01", scale=0.5, tint_=(1.1, 0.85, 0.6))

def strata(name):
    """cut-face soil: dark topsoil, red clay, ochre sand, grey-brown gravel, all with noise wobble and pebble bump"""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    p.inputs["Roughness"].default_value = 0.92
    tc = nt.nodes.new("ShaderNodeTexCoord"); sp = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sp.inputs[0])
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.6; nz.inputs["Detail"].default_value = 4
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    ad = nt.nodes.new("ShaderNodeMath"); ad.operation = 'MULTIPLY_ADD'; ad.inputs[1].default_value = 0.5
    nt.links.new(nz.outputs["Fac"], ad.inputs[0]); nt.links.new(sp.outputs["Z"], ad.inputs[2])
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = -9.5; mr.inputs["From Max"].default_value = 0.4
    nt.links.new(ad.outputs[0], mr.inputs["Value"])
    cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.interpolation = 'CONSTANT'
    stops = [(0.00, (0.16, 0.10, 0.07)), (0.16, (0.30, 0.17, 0.09)), (0.29, (0.50, 0.22, 0.06)), (0.43, (0.62, 0.36, 0.08)),
             (0.56, (0.40, 0.11, 0.04)), (0.70, (0.58, 0.20, 0.05)), (0.84, (0.30, 0.14, 0.05)), (0.95, (0.10, 0.05, 0.02))]
    cr.color_ramp.elements[0].position, cr.color_ramp.elements[0].color = stops[0][0], (*stops[0][1], 1)
    cr.color_ramp.elements[1].position, cr.color_ramp.elements[1].color = stops[-1][0], (*stops[-1][1], 1)
    for pos, c in stops[1:-1]:
        e = cr.color_ramp.elements.new(pos); e.color = (*c, 1)
    nt.links.new(mr.outputs["Result"], cr.inputs["Fac"])
    vo = nt.nodes.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 5.0
    nt.links.new(tc.outputs["Object"], vo.inputs["Vector"])
    pb = nt.nodes.new("ShaderNodeMath"); pb.operation = 'LESS_THAN'; pb.inputs[1].default_value = 0.07
    nt.links.new(vo.outputs["Distance"], pb.inputs[0])
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MIX'
    mx.inputs['B'].default_value = (0.22, 0.19, 0.16, 1)
    nt.links.new(pb.outputs[0], mx.inputs["Factor"]); nt.links.new(cr.outputs["Color"], mx.inputs["A"])
    nt.links.new(mx.outputs["Result"], p.inputs["Base Color"])
    n2 = nt.nodes.new("ShaderNodeTexNoise"); n2.inputs["Scale"].default_value = 14.0; n2.inputs["Detail"].default_value = 8
    nt.links.new(tc.outputs["Object"], n2.inputs["Vector"])
    hs = nt.nodes.new("ShaderNodeMath"); hs.operation = 'ADD'
    nt.links.new(n2.outputs["Fac"], hs.inputs[0]); nt.links.new(pb.outputs[0], hs.inputs[1])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.6; bp.inputs["Distance"].default_value = 0.02
    nt.links.new(hs.outputs[0], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], p.inputs["Normal"])
    return m
M_STRATA = strata("M_Strata")
M_SHAFT = imgmat("M_ShaftWall", "brown_mud_leaves_01", "brown_mud_leaves_01", scale=1.2, tint_=(0.75, 0.48, 0.30))
M_STEEL = mat("M_CasingSteel", (0.30, 0.31, 0.33), rough=0.45, metal=0.9)
M_RUST = mat("M_TripodRed", (0.62, 0.04, 0.02), rough=0.4, metal=0.3, coat=0.3)
M_ROPE = fabric("M_Rope", (0.85, 0.62, 0.12), scale=300, bump=0.5)
M_DIRT = imgmat("M_DirtPile", "brown_mud_leaves_01", "brown_mud_leaves_01", scale=0.8, tint_=(0.9, 0.55, 0.32))

# ================================================================== the earth block with the well and the dig pit
bpy.ops.mesh.primitive_cube_add(size=1)
G = bpy.context.active_object; G.name = "SET_Ground"
G.scale = (70.0, 50.0, 16.0); bpy.ops.object.transform_apply(scale=True)
G.location = (0, 25.0, -8.0); bpy.ops.object.transform_apply(location=True)
G.data.materials.append(M_GRASS); G.data.materials.append(M_STRATA); G.data.materials.append(M_SHAFT)
for p in G.data.polygons:
    p.material_index = 0 if p.normal.z > 0.5 else 1
# subdivide the top so the field can take a gentle displacement far from the well (kept flat within 6 m)
bm = bmesh.new(); bm.from_mesh(G.data)
top = [f for f in bm.faces if f.normal.z > 0.5]
bmesh.ops.subdivide_edges(bm, edges=list({e for f in top for e in f.edges}), cuts=60, use_grid_fill=True)
for v in bm.verts:
    if v.co.z > -0.01:
        r = math.hypot(v.co.x, v.co.y - 4.0)
        k = max(0.0, min(1.0, (r - 8.0) / 10.0))
        v.co.z = k * (0.6 * math.sin(v.co.x * 0.21) + 0.5 * math.cos(v.co.y * 0.17) + 0.4)
bm.to_mesh(G.data); bm.free()
G.data.update()
to_col(G, C_SET)
def cutter(name, r, z0, z1, loc_xy, verts=48):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=z1 - z0, location=(loc_xy[0], loc_xy[1], (z0 + z1) / 2), vertices=verts)
    o = bpy.context.active_object; o.name = name; o.data.materials.append(M_SHAFT)
    o.hide_render = True; o.display_type = 'WIRE'; to_col(o, C_SET)
    return o
WELLC = cutter("CUT_Well", R_SH, Z_BOT, 1.5, (0, 0))
WELLC.data.materials[0] = M_STRATA
# the dig pit: a cutter whose top stays above ground; PitCtl (an empty) scales it down from the top
PITC = cutter("CUT_Pit", 0.55, -1.0, 0.0, (2.3, 0.0))
PITC.data.materials[0] = M_STRATA
PITC.data.transform(Matrix.Translation((0, 0, -0.5)))       # object-space z: -1 (bottom) .. 0 (top)
PITC.location = (2.3, 0.0, 0.6)                              # top 0.6 above ground: depth below ground = scale.z - 0.6
PITC.scale.z = 0.9                                           # 0.3 m deep at the start
for nm, c in (("well", WELLC), ("pit", PITC)):
    b = G.modifiers.new("bool_" + nm, 'BOOLEAN'); b.operation = 'DIFFERENCE'; b.object = c; b.solver = 'EXACT'
    b.use_hole_tolerant = True; b.material_mode = 'TRANSFER'
# smooth the bottom of the well into a slight bowl: a mud disc the toddler stands on
bpy.ops.mesh.primitive_cylinder_add(radius=R_SH - 0.005, depth=0.02, location=(0, 0.0, Z_BOT + 0.005), vertices=48)
FLOORW = bpy.context.active_object; FLOORW.name = "SET_WellFloor"; FLOORW.data.materials.append(M_STRATA)
bm = bmesh.new(); bm.from_mesh(FLOORW.data)
bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, -0.0, 0), plane_no=(0, 1, 0), clear_inner=True)
bmesh.ops.contextual_create(bm, geom=[e for e in bm.edges if e.is_boundary])
bm.to_mesh(FLOORW.data); bm.free(); to_col(FLOORW, C_SET)

# the well casing: a steel pipe ring (back half only, y>0) from -0.5 to +0.14
def half_tube(name, r_in, r_out, z0, z1, material, loc=(0, 0, 0)):
    bm = bmesh.new(); n = 48
    rings = []
    for r in (r_in, r_out):
        for z in (z0, z1):
            rings.append([bm.verts.new((r * math.cos(math.pi * i / n), r * math.sin(math.pi * i / n), z)) for i in range(n + 1)])
    ib, it, ob, ot = rings
    for i in range(n):
        for A, B in ((ib, it), (ot, ob), (it, ot), (ob, ib)):
            bm.faces.new((A[i], A[i + 1], B[i + 1], B[i]))
    for A in ((ib[0], it[0], ot[0], ob[0]), (ib[n], ob[n], ot[n], it[n])):
        bm.faces.new(A)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); C_SET.objects.link(o); o.location = loc
    o.data.materials.append(material)
    for p in o.data.polygons: p.use_smooth = True
    o.data.shade_smooth()
    return o
CASING = half_tube("SET_Casing", R_SH + 0.002, R_SH + 0.05, -0.5, 0.04, M_STEEL)
bv = CASING.modifiers.new("bev", 'BEVEL'); bv.width = 0.008; bv.segments = 2; bv.limit_method = 'ANGLE'

# ================================================================== tripod with a pulley over the well (rescue gear)
APEX = Vector((0.0, -0.10, 2.55))
TRI_FEET = [Vector((-1.25, 0.10, 0.0)), Vector((1.25, 0.10, 0.0)), Vector((0.0, 1.85, 0.0))]
tri_parts = []
for i, ft in enumerate(TRI_FEET):
    d = APEX - ft; L = d.length
    bpy.ops.mesh.primitive_cylinder_add(radius=0.03, depth=L, location=(ft + APEX) / 2, vertices=16)
    o = bpy.context.active_object; o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d)
    o.data.materials.append(M_RUST); tri_parts.append(o)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.06, depth=0.04, location=ft + Vector((0, 0, 0.02)), vertices=16)
    o = bpy.context.active_object; o.data.materials.append(M_STEEL); tri_parts.append(o)
bpy.ops.mesh.primitive_cylinder_add(radius=0.09, depth=0.12, location=APEX + Vector((0, 0, 0.05)), vertices=24)
o = bpy.context.active_object; o.data.materials.append(M_STEEL); tri_parts.append(o)
bpy.ops.object.select_all(action='DESELECT')
for o in tri_parts: o.select_set(True)
bpy.context.view_layer.objects.active = tri_parts[0]; bpy.ops.object.join()
TRIPOD = bpy.context.active_object; TRIPOD.name = "SET_Tripod"; bpy.ops.object.shade_smooth(); to_col(TRIPOD, C_SET)
# pulley wheel hangs under the apex; the rope leaves it at x=0,y=0.25-> straight down the shaft centre line
bpy.ops.mesh.primitive_torus_add(major_radius=0.08, minor_radius=0.022, location=APEX + Vector((0.0, 0.0, -0.12)), rotation=(0, math.radians(90), 0))
PUL = bpy.context.active_object; PUL.name = "SET_Pulley"; PUL.data.materials.append(M_STEEL); to_col(PUL, C_SET)
ROPE_TOP = APEX + Vector((0.0, 0.0, -0.20))

# ================================================================== ropes: curves whose two ends are hooked to empties
def empty(name, loc, size=0.05):
    e = bpy.data.objects.new(name, None); e.empty_display_size = size; e.location = loc; C_SET.objects.link(e); return e
def rope_obj(name, n, r=0.013):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = r; cu.bevel_resolution = 3
    cu.use_fill_caps = True
    sp = cu.splines.new('POLY'); sp.points.add(n - 1)
    o = bpy.data.objects.new(name, cu); C_SET.objects.link(o); o.data.materials.append(M_ROPE)
    emps = []
    for i, p in enumerate(sp.points):
        e = empty("%s_P%02d" % (name, i), ROPE_TOP - Vector((0, 0, i * 0.3)), 0.02); emps.append(e)
        p.co = (0.0, 0.0, 0.0, 1)      # hooks without an inverse matrix: the point = the empty's location
        hk = o.modifiers.new("h%02d" % i, 'HOOK'); hk.object = e; hk.vertex_indices_set([i])
    return o, emps
ROPE1, R1P = rope_obj("ROPE_Loop", 16)          # B2: the looped rope lowered to the toddler
bpy.ops.mesh.primitive_torus_add(major_radius=0.16, minor_radius=0.013, major_segments=40, minor_segments=8)
LOOP = bpy.context.active_object; LOOP.name = "ROPE_LoopRing"; LOOP.data.materials.append(M_ROPE); to_col(LOOP, C_SET)
ROPE2, R2P = rope_obj("ROPE_Teen", 16)          # B6-B10: the rope from the pulley to the teen's waist knot
bpy.ops.mesh.primitive_torus_add(major_radius=0.20, minor_radius=0.014, major_segments=48, minor_segments=8)
WAIST = bpy.context.active_object; WAIST.name = "ROPE_WaistRing"; WAIST.data.materials.append(M_ROPE); to_col(WAIST, C_SET)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.035, segments=16, ring_count=8)
KNOT = bpy.context.active_object; KNOT.name = "ROPE_Knot"; KNOT.data.materials.append(M_ROPE); KNOT.scale = (1.0, 0.8, 0.8); to_col(KNOT, C_SET)
# ================================================================== the head torch (procedural): strap band + lamp, fitted in stage B
bpy.ops.mesh.primitive_torus_add(major_radius=0.095, minor_radius=0.006, major_segments=48, minor_segments=6)
STRAP = bpy.context.active_object; STRAP.name = "TEEN_TorchStrap"; STRAP.scale = (1.0, 1.2, 0.9)
STRAP.data.materials.append(mat("M_Strap", (0.03, 0.03, 0.035), rough=0.6)); to_col(STRAP, C_PPL)
LAMP = box("TEEN_TorchLamp", (0.05, 0.03, 0.035), (0, 0, 0), mat("M_LampBody", (0.05, 0.05, 0.06), rough=0.3, coat=0.5), bevel=0.006)
bpy.ops.mesh.primitive_cylinder_add(radius=0.013, depth=0.004, location=(0, -0.016, 0), rotation=(math.radians(90), 0, 0))
LENS = bpy.context.active_object; LENS.name = "TEEN_TorchLens"
LENS.data.materials.append(mat("M_LampLens", (1.0, 0.95, 0.8), emit=((1.0, 0.93, 0.75), 40.0)))
LENS.parent = LAMP; to_col(LAMP, C_PPL); to_col(LENS, C_PPL)
# the beam: a cone with an emissive, alpha-faded shader (cheap, no volumes)
bpy.ops.mesh.primitive_cone_add(radius1=0.004, radius2=0.26, depth=1.2, vertices=48, end_fill_type='NOTHING', location=(0, -0.6, 0), rotation=(math.radians(90), 0, 0))
BEAM = bpy.context.active_object; BEAM.name = "TEEN_TorchBeam"
bpy.ops.object.transform_apply(location=True, rotation=True)
mb = bpy.data.materials.new("M_Beam"); mb.use_nodes = True; nt = mb.node_tree
for n_ in list(nt.nodes):
    if n_.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n_)
tc = nt.nodes.new("ShaderNodeTexCoord"); sp = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sp.inputs[0])
mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.0; mr.inputs["From Max"].default_value = -1.2
mr.inputs["To Min"].default_value = 0.09; mr.inputs["To Max"].default_value = 0.0
nt.links.new(sp.outputs["Y"], mr.inputs["Value"])
em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (1.0, 0.92, 0.7, 1); em.inputs["Strength"].default_value = 1.0
tr = nt.nodes.new("ShaderNodeBsdfTransparent")
ad = nt.nodes.new("ShaderNodeAddShader"); mx = nt.nodes.new("ShaderNodeMixShader")
nt.links.new(mr.outputs["Result"], mx.inputs["Fac"]); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], ad.inputs[0])
nt.links.new(tr.outputs[0], ad.inputs[1]); nt.links.new(ad.outputs[0], mx.inputs[2])
nt.links.new(mx.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
BEAM.data.materials.append(mb); BEAM.visible_shadow = False; BEAM.parent = LAMP; to_col(BEAM, C_PPL)
SPOT = bpy.data.lights.new("TorchSpot", 'SPOT'); SPOT.energy = 60; SPOT.spot_size = math.radians(40); SPOT.spot_blend = 0.6
SPOT.color = (1.0, 0.92, 0.75); SPOT.shadow_soft_size = 0.01
SPO = bpy.data.objects.new("TEEN_TorchSpot", SPOT); C_PPL.objects.link(SPO); SPO.parent = LAMP
SPO.rotation_euler = (math.radians(90), 0, 0); SPO.location = (0, -0.03, 0)

# ================================================================== the excavator (CC-BY, hierarchical arm we key in stage B)
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=os.path.join(AS, "excav6.glb"))
EXN = [o for o in bpy.data.objects if o not in before]
for o in EXN: to_col(o, C_SET)
for ad_ in [o.animation_data for o in EXN if o.animation_data]:
    ad_.action = None
for ac in list(bpy.data.actions): bpy.data.actions.remove(ac)
EXROOT = [o for o in EXN if o.parent is None][0]; EXROOT.name = "EXC_Root"
for o in EXN:
    if o.type == 'MESH':
        soften(o, rough_min=0.35)
print('EXC root rot', tuple(EXROOT.rotation_euler), tuple(EXROOT.scale))
EXROOT.matrix_world = Matrix.Rotation(math.radians(144), 4, 'Z') @ EXROOT.matrix_world; EXROOT.scale *= 2.5
EXROOT.location = (4.35, 2.75, 0.0); bpy.context.view_layer.update()
zmin = min((o.matrix_world @ Vector(c)).z for o in EXN if o.type == 'MESH' for c in o.bound_box)
EXROOT.location.z -= zmin; bpy.context.view_layer.update()
for o in EXN:
    if o.type == 'EMPTY' and o.name in ("claw_GEO", "Arm_2_GEO", "arm_01_GEO1", "Body_GEO"):
        print("EXC part", o.name, tuple(round(x, 2) for x in o.matrix_world.translation))
print("EXC root", EXROOT.name, [o.name for o in EXN if o.type == 'EMPTY'])

# ================================================================== spoil heap beside the pit, and the backdrop
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=32, ring_count=16, location=(7.3, 1.4, -0.35))
HEAP = bpy.context.active_object; HEAP.name = "SET_SpoilHeap"; HEAP.scale = (1.0, 0.9, 0.55)
HEAP.data.materials.append(M_DIRT); bpy.ops.object.shade_smooth()
tx = bpy.data.textures.new("heapnoise", 'CLOUDS'); tx.noise_scale = 0.4
dm = HEAP.modifiers.new("lumps", 'DISPLACE'); dm.texture = tx; dm.strength = 0.18; to_col(HEAP, C_SET)
# trees and shrubs (Poly Haven CC0), appended from their blends
def append_ph(folder, fname, name, locs, scale=1.0):
    path = os.path.join(PH, folder, fname)
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.objects = [n for n in src.objects]
    base = [o for o in dst.objects if o and o.type == 'MESH']
    out = []
    for i, (x, y, rz) in enumerate(locs):
        for b in base:
            o = b.copy() if i else b
            if i: o.data = b.data
            C_SET.objects.link(o) if o.name not in C_SET.objects else None
            o.location = (x, y, 0.0); o.rotation_euler = (0, 0, rz); o.scale = (scale, scale, scale)
            out.append(o)
    return out
TREES = append_ph("island_tree_01", "island_tree_01_1k.blend", "Tree", [(-9.0, 16.0, 0.3), (8.5, 19.0, 2.0), (-2.0, 26.0, 4.0), (15.0, 13.0, 1.0)], 1.0)
SHRUBS = append_ph("shrub_01", "shrub_01_1k.blend", "Shrub", [(-4.5, 5.0, 0.4), (5.8, 6.5, 1.2), (-6.5, 9.0, 2.2), (2.5, 9.5, 3.0)], 1.3)

# ================================================================== world + sun + render look
wd = bpy.data.worlds.new("World"); sc.world = wd; wd.use_nodes = True; nt = wd.node_tree
bg = nt.nodes["Background"]; env = nt.nodes.new("ShaderNodeTexEnvironment")
env.image = bpy.data.images.load(os.path.join(PH, "hdri", "kloofendal_48d_partly_cloudy_puresky_1k.hdr"))
nt.links.new(env.outputs["Color"], bg.inputs["Color"]); bg.inputs["Strength"].default_value = 1.0
SUN = bpy.data.lights.new("Sun", 'SUN'); SUN.energy = 4.0; SUN.angle = math.radians(2.0); SUN.color = (1.0, 0.95, 0.86)
SUNO = bpy.data.objects.new("Sun", SUN); sc.collection.objects.link(SUNO)
SUNO.rotation_euler = (math.radians(50), 0, math.radians(-35))
# shaft fill: a soft warm area light low in the cut-away so the toddler reads at the bottom (no white faces: low power)
for nm, z in (("ShaftFill_Low", Z_BOT + 1.6), ("ShaftFill_Mid", -4.5)):
    L = bpy.data.lights.new(nm, 'AREA'); L.energy = 130; L.size = 1.5; L.color = (1.0, 0.88, 0.72)
    o = bpy.data.objects.new(nm, L); sc.collection.objects.link(o); o.location = (0.0, -2.2, z); o.rotation_euler = (math.radians(90), 0, 0)
sc.render.engine = 'CYCLES'; sc.cycles.samples = 64; sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True; sc.cycles.device = 'CPU'
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Punchy'
sc.render.use_motion_blur = False
cam_d = bpy.data.cameras.new("CAM_Film"); cam_d.lens = 32; cam_d.sensor_width = 36; cam_d.sensor_fit = 'AUTO'
CAM = bpy.data.objects.new("CAM_Film", cam_d); sc.collection.objects.link(CAM); sc.camera = CAM
cam_d.clip_start = 0.05
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SAVED", OUT)
