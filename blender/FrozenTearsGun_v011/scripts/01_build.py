"""FrozenTearsGun v011 stage A (from scratch): two MPFB people in real MakeHuman garments, the lab set, the gun, the look.
blender -b --python 01_build.py -- <logo_dark.png> <out.blend> [people_only]

World layout (metres, Z up). One room, the camera never leaves it:
  BENCH  : she sits on a stool at (0, 0) facing +Y. Bench top z=0.76. The tear gun rests in a wooden cradle on the bench.
  RANGE  : the gun points +Y down a 3.4 m test range to a target board on the far wall (y=4.6).
  OFFICE : the mentor's desk corner at x=-2.6..-1.2, y=2.6..4.2 (memory beat), terracotta accent wall.
Characters face -Y in their rest pose; they are turned in 02_animate.py."""
import bpy, bmesh, sys, math, random, os
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "lib.py")).read())
a = sys.argv[sys.argv.index("--") + 1:]
LOGO, OUT = a[0], a[1]
PEOPLE_ONLY = len(a) > 2 and a[2] == "people_only"
random.seed(13)
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
sc.render.fps = 60
sc.frame_start, sc.frame_end = 1, 1655
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920

# ================================================================== PEOPLE (one model per character, whole film)
SWEATER = "toigo_fisherman_sweater/toigo_fisherman_sweater.mhclo"; PANTS = "toigo_wool_pants/toigo_wool_pants.mhclo"
SUIT = "toigo_male_suit_3/toigo_male_suit_3.mhclo"
INV, IB = human("Inventor", 0.0, 0.43, {"asian": 0.25, "caucasian": 0.65, "african": 0.10}, "ponytail01/ponytail01.mhclo",
                "young_caucasian_female/young_caucasian_female.mhmat", "eyebrow010/eyebrow010.mhclo", height=0.45, weight=0.45,
                shoes="shoes01/shoes01.mhclo", clothes=[SWEATER, PANTS], cup=0.25)
MEN, MB = human("Mentor", 1.0, 0.86, {"asian": 0.05, "caucasian": 0.85, "african": 0.10}, "short02/short02.mhclo",
                "old_caucasian_male/old_caucasian_male.mhmat", "eyebrow001/eyebrow001.mhclo", height=0.55, weight=0.55, muscle=0.3,
                shoes="shoes02/shoes02.mhclo", clothes=[SUIT])
for r, b in ((INV, IB), (MEN, MB)):
    bake_keys(b); eye_fix(r); drop_delete_masks(b)
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
for m in IB.data.materials: tint(m, (1.0, 0.78, 0.64))
for m in MB.data.materials: tint(m, (1.0, 0.80, 0.68))
for r, t, keys in ((INV, (0.42, 0.20, 0.10), ("ponytail01", "eyebrow")), (MEN, (0.85, 0.85, 0.88), ("short02", "eyebrow"))):
    for c in r.children:
        if c.type == 'MESH' and any(k in c.name for k in keys):
            for m in c.data.materials: tint(m, t)
def cl(rig, key, newname):
    o = part(rig, key); o.name = newname; return o
I_TOP = cl(INV, "fisherman_sweater", "Inv.sweater"); I_TRS = cl(INV, "wool_pants", "Inv.trousers")
M_SUIT = cl(MEN, "suit_3", "Men.suit")
colorize(I_TOP, (0.95, 0.50, 0.02), gain=1.0); colorize(I_TRS, (0.02, 0.08, 0.32), gain=1.0)   # the suit keeps its own pinstripe/shirt/tie texture
# trousers under the sweater: the waistband the sweater covers is masked off the TROUSERS (never the body)
zmin = min(v.co.z for v in I_TOP.data.vertices)
vg = I_TRS.vertex_groups.new(name="under_top"); vg.add([v.index for v in I_TRS.data.vertices if v.co.z > zmin + 0.02], 1.0, 'REPLACE')
mk = I_TRS.modifiers.new("under_top", 'MASK'); mk.vertex_group = "under_top"; mk.invert_vertex_group = True
solid_under(IB, I_TOP, (0.45, 0.28, 0.02), "Solid.sweater", rings=4)
solid_under(IB, I_TRS, (0.02, 0.05, 0.18), "Solid.trousers", rings=3)
solid_under(MB, M_SUIT, (0.80, 0.84, 0.90), "Solid.suit", rings=4)
sc["PEOPLE"] = [INV.name, MEN.name]
if PEOPLE_ONLY:
    MEN.location.x = 0.9
    bpy.ops.wm.save_as_mainfile(filepath=OUT); print("PEOPLE_OK"); raise SystemExit

# ================================================================== the collector glasses (built in the REST pose, bound to the head bone)
def to_head_bone(o, rig):
    """parent an object (modelled in rest/world coords with the rig at the origin) to the head bone, keeping it in place"""
    bpy.context.view_layer.update()
    Mw = o.matrix_world.copy(); o.parent = rig; o.parent_type = 'BONE'; o.parent_bone = "head"
    bpy.context.view_layer.update(); o.matrix_world = Mw
from mathutils.bvhtree import BVHTree
def body_bvh(body):
    return BVHTree.FromPolygons([v.co.copy() for v in body.data.vertices], [tuple(p.vertices) for p in body.data.polygons if all(True for _ in p.vertices)])
IBVH = body_bvh(IB)
def ray_front(x, z, y0=-0.5):
    hit = IBVH.ray_cast(Vector((x, y0, z)), Vector((0, 1, 0)))
    return hit[0]
EYE = {s: bl(INV, "eye." + s) for s in "LR"}
eyemesh = part(INV, "high-poly")
cornea_y = min(v.co.y for v in eyemesh.data.vertices)
brass = mat("M_Brass", (0.95, 0.62, 0.18), rough=0.22, metal=1.0)
brass_d = mat("M_BrassDark", (0.55, 0.33, 0.10), rough=0.3, metal=1.0)
glass = mat("M_Glass", (0.92, 0.97, 1.0), rough=0.02); gp = glass.node_tree.nodes["Principled BSDF"]
gp.inputs["Transmission Weight"].default_value = 1.0; gp.inputs["IOR"].default_value = 1.05
lensm = mat("M_Lens", (0.85, 0.95, 1.0), rough=0.02, alpha=0.12); lensm.node_tree.nodes["Principled BSDF"].inputs["Coat Weight"].default_value = 1.0
tube_m = mat("M_Tube", (0.75, 0.92, 1.0), rough=0.05); tp = tube_m.node_tree.nodes["Principled BSDF"]
tp.inputs["Transmission Weight"].default_value = 1.0; tp.inputs["IOR"].default_value = 1.33
water_m = mat("M_Water", (0.55, 0.85, 1.0), rough=0.02); wp = water_m.node_tree.nodes["Principled BSDF"]
wp.inputs["Transmission Weight"].default_value = 1.0; wp.inputs["IOR"].default_value = 1.33
wp.inputs["Emission Color"].default_value = (0.35, 0.75, 1.0, 1); wp.inputs["Emission Strength"].default_value = 0.6
GL = []
lens_y = cornea_y - 0.016
for s in "LR":
    E = EYE[s]; sx = 1 if E.x > 0 else -1
    c = Vector((E.x, lens_y, E.z + 0.002)); hw, hh = 0.021, 0.016
    ring = [c + Vector((hw * math.cos(t), 0.004 * math.cos(t) ** 2 * (1 if sx * math.cos(t) > 0 else 0), hh * math.sin(t))) for t in [2 * math.pi * k / 24 for k in range(24)]]
    # rim: closed tube
    cu = bpy.data.curves.new("GlassesRim." + s, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.0016; cu.bevel_resolution = 3
    sp = cu.splines.new('NURBS'); sp.points.add(len(ring) - 1); sp.use_cyclic_u = True; sp.order_u = 4
    for p_, q in zip(sp.points, ring): p_.co = (*q, 1)
    o = bpy.data.objects.new("GlassesRim." + s, cu); sc.collection.objects.link(o); cu.materials.append(brass); GL.append(o)
    me = bpy.data.meshes.new("Lens." + s); bm = bmesh.new()
    vs = [bm.verts.new(q) for q in ring]; bm.faces.new(vs); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("Lens." + s, me); sc.collection.objects.link(o); me.materials.append(lensm); GL.append(o)
    # temple arm: a straight arm from the outer rim back to the top of the ear (it disappears into the hair there)
    pts = [Vector((E.x + sx * 0.021, lens_y + 0.004, E.z + 0.004)), Vector((E.x + sx * 0.040, lens_y + 0.030, E.z + 0.003)),
           Vector((E.x + sx * 0.046, lens_y + 0.080, E.z - 0.002))]
    tm = curve_tube("GlassesTemple." + s, pts, 0.0015, brass); GL.append(tm)
# bridge over the nose
nb_y = ray_front(0.0, EYE["L"].z - 0.004)
bridge = curve_tube("GlassesBridge", [Vector((EYE["R"].x + 0.022 * (1 if EYE["R"].x < 0 else -1) * -1, lens_y, EYE["R"].z + 0.006)),
                                       Vector((0, min(lens_y + 0.006, nb_y.y - 0.004) if nb_y else lens_y, EYE["L"].z + 0.010)),
                                       Vector((EYE["L"].x - 0.022 * (1 if EYE["L"].x > 0 else -1), lens_y, EYE["L"].z + 0.006))], 0.0016, brass); GL.append(bridge)
# collector cup under her RIGHT eye: a small glass funnel whose back lip sits 2 mm off the cheek
ER = EYE["R"]
CX = ER.x * 1.45
cheek = ray_front(CX, ER.z - 0.030)
cup_c = Vector((CX, cheek.y - 0.007, ER.z - 0.030))
bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.0115, radius2=0.0032, depth=0.016, location=cup_c + Vector((0, 0, -0.008)), rotation=(math.pi, 0, 0), end_fill_type='NOTHING')
CUP = bpy.context.active_object; CUP.name = "CollectorCup"; CUP.data.materials.append(glass)
sl = CUP.modifiers.new("solid", 'SOLIDIFY'); sl.thickness = 0.0012; bpy.ops.object.shade_smooth(); GL.append(CUP)
CUPRIM = bpy.data.objects.new("CollectorRim", bpy.data.curves.new("CollectorRim", 'CURVE')); sc.collection.objects.link(CUPRIM)
CUPRIM.data.dimensions = '3D'; CUPRIM.data.bevel_depth = 0.0012; sp = CUPRIM.data.splines.new('NURBS'); sp.points.add(23); sp.use_cyclic_u = True
for k, p_ in enumerate(sp.points):
    t = 2 * math.pi * k / 24; p_.co = (cup_c.x + 0.0118 * math.cos(t), cup_c.y + 0.0118 * math.sin(t), cup_c.z, 1)
CUPRIM.data.materials.append(brass); GL.append(CUPRIM)
NOZ = cyl("CollectorNozzle", 0.0034, 0.008, cup_c + Vector((0, 0, -0.019)), brass); GL.append(NOZ)
BRK = curve_tube("CollectorBracket", [Vector((ER.x * 1.25, lens_y + 0.002, ER.z - 0.013)),
                                      cup_c + Vector((0.009 * (1 if ER.x > 0 else -1) * -1, -0.004, 0.0005))], 0.0011, brass); GL.append(BRK)
for o in GL: to_head_bone(o, INV)
# head-side tube anchor points (rest coords): nozzle -> along the jaw (2 cm off the skin) -> under the chin
sxR = 1 if ER.x > 0 else -1
jaw = bl(INV, "jaw"); chin_z = jaw.z - 0.06
TUBE_HEAD_PTS = [cup_c + Vector((0, 0, -0.024)), cup_c + Vector((sxR * 0.006, -0.010, -0.050)), Vector((CX * 1.1, cheek.y - 0.014, chin_z - 0.002)),
                 Vector((CX * 0.6, cheek.y - 0.010, chin_z - 0.045))]
for i, p in enumerate(TUBE_HEAD_PTS):
    loc, nrm, _, d = IBVH.find_nearest(p)
    if loc is not None and (p - loc).dot(nrm) < 0.018 and i > 0: TUBE_HEAD_PTS[i] = loc + nrm * 0.018
TH = empty("TubeHeadAnchor", (0, 0, 0)); to_head_bone(TH, INV)
sc["TUBE_HEAD_PTS"] = [list(p) for p in TUBE_HEAD_PTS]
sc["CUP_C"] = list(cup_c); sc["EYE_R"] = list(ER); sc["EYE_L"] = list(EYE["L"]); sc["CORNEA_Y"] = cornea_y
for o in GL + [TH]: o["glasses"] = True

# ================================================================== SET: one lab room
X0, X1, Y0, Y1, H = -3.4, 1.6, -1.5, 4.8, 2.9
teal = mat("M_WallTeal", (0.02, 0.36, 0.40), rough=0.75)
terra = mat("M_WallTerra", (0.62, 0.17, 0.06), rough=0.75)
purple = mat("M_WallPurple", (0.16, 0.06, 0.42), rough=0.75)
ceilm = mat("M_Ceil", (0.85, 0.86, 0.88), rough=0.9)
floorm = wood("M_Floor", (0.30, 0.12, 0.04), (0.55, 0.26, 0.09), scale=6.0)
box("Floor", (X1 - X0, Y1 - Y0, 0.02), ((X0 + X1) / 2, (Y0 + Y1) / 2, -0.01), floorm, bevel=0)
box("Ceiling", (X1 - X0, Y1 - Y0, 0.02), ((X0 + X1) / 2, (Y0 + Y1) / 2, H + 0.01), ceilm, bevel=0)
box("WallBack", (X1 - X0, 0.05, H), ((X0 + X1) / 2, Y0 - 0.025, H / 2), teal, bevel=0)
box("WallRight", (0.05, Y1 - Y0, H), (X1 + 0.025, (Y0 + Y1) / 2, H / 2), teal, bevel=0)
box("WallLeft", (0.05, Y1 - Y0, H), (X0 - 0.025, (Y0 + Y1) / 2, H / 2), terra, bevel=0)
box("WallFarRange", (X1 + 1.0, 0.05, H), ((X1 - 1.0) / 2, Y1 + 0.025, H / 2), purple, bevel=0)
box("WallFarOffice", (-1.0 - X0, 0.05, H), ((X0 - 1.0) / 2, Y1 + 0.025, H / 2), terra, bevel=0)
skirt = mat("M_Skirting", (0.95, 0.93, 0.88), rough=0.4)
for nm, sz, loc in (("SkBack", (X1 - X0, 0.02, 0.10), ((X0 + X1) / 2, Y0 + 0.01, 0.05)), ("SkRight", (0.02, Y1 - Y0, 0.10), (X1 - 0.01, (Y0 + Y1) / 2, 0.05)),
                    ("SkLeft", (0.02, Y1 - Y0, 0.10), (X0 + 0.01, (Y0 + Y1) / 2, 0.05)), ("SkFar", (X1 - X0, 0.02, 0.10), ((X0 + X1) / 2, Y1 - 0.01, 0.05))):
    box(nm, sz, loc, skirt, bevel=0.003)

# ---- the workbench (her bench): butcher-block top, steel frame, open front for her knees
BENCH_TOP = 0.72
benchwood = wood("M_BenchWood", (0.55, 0.30, 0.10), (0.78, 0.50, 0.22), scale=9.0)
steel = mat("M_SteelRed", (0.70, 0.04, 0.03), rough=0.35, metal=0.6, coat=0.3)
box("BenchTop", (1.50, 0.75, 0.05), (0.0, 0.425, BENCH_TOP - 0.025), benchwood, bevel=0.006)
for x in (-0.70, 0.70):
    for y in (0.10, 0.75):
        box("BenchLeg", (0.05, 0.05, BENCH_TOP - 0.05), (x, y, (BENCH_TOP - 0.05) / 2), steel, bevel=0.004)
    box("BenchRail", (0.04, 0.65, 0.04), (x, 0.425, 0.15), steel, bevel=0.004)
box("BenchBackRail", (1.40, 0.04, 0.06), (0.0, 0.75, BENCH_TOP - 0.08), steel, bevel=0.004)
# (no low shelf: her shins pass under the bench)

def import_asset(fname, name, loc, rot_z=0.0, scale=(1, 1, 1), skip=("wdg_",)):
    path = os.path.join(ASSETS, fname)
    with bpy.data.libraries.load(path) as (src, dst):
        dst.objects = [n for n in src.objects if not n.startswith(skip)]
    root = empty("A_" + name, loc, (0, 0, rot_z)); root.scale = scale
    for o in dst.objects:
        if o is None: continue
        if o.type in ('ARMATURE', 'LIGHT', 'CAMERA', 'EMPTY'):
            continue
        sc.collection.objects.link(o)
        for m in list(o.modifiers):
            if m.type == 'ARMATURE': o.modifiers.remove(m)
        if o.parent is None or o.parent.name not in sc.objects:
            Mw = o.matrix_world.copy(); o.parent = root; o.matrix_parent_inverse = Matrix()
            o.matrix_basis = Mw
    return root
ASSETS = sc.get("ASSETS", os.environ.get("FTG_ASSETS", ""))
STOOL = import_asset("metal_stool_01/metal_stool_01_1k.blend", "Stool", (0.0, -0.14, 0.0), scale=(1, 1, 0.52))
SEAT_Z = 0.883 * 0.52
# (removed after check 1: lens blocker / black material) # import_asset("bench_vice_01/bench_vice_01_1k.blend", "Vice", (0.55, 0.45, BENCH_TOP + 0.163), rot_z=math.pi / 2)
# (removed after check 1: lens blocker / black material) # import_asset("desk_lamp_arm_01/desk_lamp_arm_01_1k.blend", "BenchLamp", (-0.58, 0.68, BENCH_TOP + 0.327), rot_z=R_(200))
import_asset("adjustable_wrench/adjustable_wrench_1k.blend", "Wrench", (0.36, 0.62, BENCH_TOP + 0.016), rot_z=R_(70))
import_asset("chemistry_set/chemistry_set_1k.blend", "Chem", (-0.45, 0.58, BENCH_TOP + 0.009), rot_z=R_(10))
import_asset("metal_tool_chest/metal_tool_chest_1k.blend", "ToolChest", (1.20, 1.25, 0.47), rot_z=R_(-90))
import_asset("drill_press_01/drill_press_01_1k.blend", "Drill", (1.25, -0.55, 0.536 + 0.75), rot_z=R_(-90))
box("DrillCabinet", (0.55, 0.60, 0.75), (1.28, -0.55, 0.375), steel, bevel=0.01)
# (removed after check 1: lens blocker / black material) # import_asset("painted_wooden_shelves/painted_wooden_shelves_1k.blend", "ShelfR", (X1, 0.45, 0.0), rot_z=R_(90), scale=(1.2, 1.2, 1.4))
import_asset("hanging_industrial_lamp/hanging_industrial_lamp_1k.blend", "LampHang1", (1.05, 0.30, H - 0.01))
import_asset("hanging_industrial_lamp/hanging_industrial_lamp_1k.blend", "LampHang2", (-2.90, 2.60, H - 0.01))
# ---- office corner: the mentor's desk, her chair, shelves, plant
DESK = import_asset("metal_office_desk/metal_office_desk_1k.blend", "Desk", (-2.10, 3.68, 0.0), rot_z=math.pi, scale=(0.72, 0.75, 0.97))
DESK_TOP = 0.788 * 0.97
for o in DESK.children:
    if o.type == 'MESH': colorize(o, (0.03, 0.42, 0.24), gain=1.0, lo=0.55)   # deep green enamel desk, not grey
CHAIR = import_asset("SchoolChair_01/SchoolChair_01_1k.blend", "OfficeChair", (-2.10, 2.78, 0.0), rot_z=math.pi)
import_asset("pachira_aquatica_01/pachira_aquatica_01_1k.blend", "Plant", (-3.05, 4.45, 0.0), scale=(0.8, 0.8, 0.8))
# (removed after check 1: lens blocker / black material) # import_asset("painted_wooden_shelves/painted_wooden_shelves_1k.blend", "ShelfL", (X0, 3.10, 0.0), rot_z=R_(-90), scale=(1.2, 1.2, 1.5))
# (removed: printed covers could read as text) import_asset
# (removed: printed covers could read as text) import_asset
# (removed: printed covers could read as text) import_asset

# ---- the target board at the end of the range (rings: yellow / red / blue / white)
TGT_C = Vector((0.0, Y1 - 0.06, 1.45))
tgt_m = mat("M_Target", (1, 1, 1), rough=0.6); nt = tgt_m.node_tree; P = nt.nodes["Principled BSDF"]
tc = nt.nodes.new("ShaderNodeTexCoord"); gr = nt.nodes.new("ShaderNodeTexGradient"); gr.gradient_type = 'SPHERICAL'
mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (3.2, 3.2, 3.2)
cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.interpolation = 'CONSTANT'
cols = [(0.0, (0.95, 0.95, 0.92)), (0.30, (0.02, 0.18, 0.75)), (0.55, (0.85, 0.03, 0.03)), (0.80, (1.0, 0.80, 0.0))]
cr.color_ramp.elements[0].position = cols[0][0]; cr.color_ramp.elements[0].color = (*cols[0][1], 1)
cr.color_ramp.elements[1].position = cols[1][0]; cr.color_ramp.elements[1].color = (*cols[1][1], 1)
for pos, col in cols[2:]:
    e = cr.color_ramp.elements.new(pos); e.color = (*col, 1)
nt.links.new(tc.outputs["Object"], mp.inputs["Vector"]); nt.links.new(mp.outputs["Vector"], gr.inputs["Vector"])
nt.links.new(gr.outputs["Fac"], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], P.inputs["Base Color"])
TGT = cyl("TargetBoard", 0.30, 0.06, TGT_C, tgt_m, rot=(math.pi / 2, 0, 0), verts=64, bevel=0.01)
cyl("TargetRim", 0.315, 0.05, TGT_C + Vector((0, 0.012, 0)), mat("M_TargetRim", (0.25, 0.10, 0.03), rough=0.5), rot=(math.pi / 2, 0, 0), verts=64, bevel=0.005)
sc["TGT_C"] = list(TGT_C)

# ---- DA KRAS FILMS posters (real framed prints on the walls; logo_dark on a light card)
logo_img = bpy.data.images.load(os.path.abspath(LOGO)); logo_img.pack()
def poster(name, loc, rot_z, w):
    ar = logo_img.size[1] / logo_img.size[0]; h = w * ar
    lm = bpy.data.materials.new("M_" + name); lm.use_nodes = True; lnt = lm.node_tree; lp = lnt.nodes["Principled BSDF"]
    tx = lnt.nodes.new("ShaderNodeTexImage"); tx.image = logo_img; tx.extension = 'CLIP'
    mixc = lnt.nodes.new("ShaderNodeMix"); mixc.data_type = 'RGBA'; mixc.inputs["A"].default_value = (0.97, 0.95, 0.90, 1)
    lnt.links.new(tx.outputs["Alpha"], mixc.inputs["Factor"]); lnt.links.new(tx.outputs["Color"], mixc.inputs["B"])
    lnt.links.new(mixc.outputs["Result"], lp.inputs["Base Color"]); lp.inputs["Roughness"].default_value = 0.5
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=(math.pi / 2, 0, rot_z))
    o = bpy.context.active_object; o.name = name; o.scale = (w, h, 1); bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(lm)
    nrm = Vector((0, -1, 0)); nrm.rotate(Matrix.Rotation(rot_z, 3, 'Z'))
    box(name + "_frame", (w + 0.08, 0.025, h + 0.08), Vector(loc) - nrm * 0.014, mat("M_Frame", (0.08, 0.05, 0.03), rough=0.4), bevel=0.008, rot=(0, 0, rot_z))
    return o
POSTER1 = poster("LogoPoster_Lab", (-0.78, Y0 + 0.02, 1.52), math.pi, 0.80)
POSTER2 = poster("LogoPoster_Office", (-2.10, Y1 - 0.02, 1.95), 0.0, 0.70)
print("LOGO size", logo_img.size[:])

# ================================================================== THE TEAR GUN (ours): glass chamber, red valve wheel, CO2 canister, spring breech, brass barrel
GUN = empty("GUN", (0, 0, 0))
def hollow_glass(name, r, h, loc, rot=(0, 0, 0)):
    """a thin-walled open glass tube (not a solid refractive rod: the drops inside must read clearly)"""
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=loc, rotation=rot, vertices=48, end_fill_type='NOTHING')
    o = bpy.context.active_object; o.name = name; o.data.materials.append(glass)
    so = o.modifiers.new("wall", 'SOLIDIFY'); so.thickness = 0.0012; so.offset = -1.0
    bpy.ops.object.shade_smooth(); return o
def gpart(o):
    Mw = o.matrix_world.copy(); o.parent = GUN; o.matrix_parent_inverse = Matrix(); o.matrix_basis = Mw; return o
RY = (math.pi / 2, 0, 0)      # cylinder axis along +Y
woodgrip = wood("M_GripWood", (0.30, 0.10, 0.03), (0.52, 0.22, 0.07), scale=14.0)
red = mat("M_ValveRed", (0.85, 0.02, 0.02), rough=0.25, coat=0.6)
can_m = mat("M_Canister", (0.05, 0.25, 0.95), rough=0.2, metal=0.7, coat=0.8)
dark = mat("M_Bore", (0.01, 0.01, 0.01), rough=0.6)
steel_s = mat("M_Spring", (0.85, 0.87, 0.9), rough=0.15, metal=1.0)
# rear (spring) tube: clear glass with brass end cap and collars
gpart(hollow_glass("G_RearTube", 0.017, 0.118, (0, -0.071, 0), rot=RY))
gpart(cyl("G_RearCap", 0.020, 0.018, (0, -0.139, 0), brass, rot=RY, bevel=0.003))
gpart(cyl("G_RearKnob", 0.010, 0.016, (0, -0.155, 0), brass_d, rot=RY, bevel=0.002))
gpart(cyl("G_Collar1", 0.020, 0.008, (0, -0.012, 0), brass, rot=RY, bevel=0.002))
# breech block under the chamber, chamber, top cap, inlet nipple
gpart(box("G_Breech", (0.046, 0.050, 0.030), (0, 0.012, -0.002), brass, bevel=0.006))
gpart(cyl("G_ChamberBase", 0.029, 0.010, (0, 0.012, 0.016), brass, bevel=0.002))
CH = gpart(hollow_glass("G_Chamber", 0.026, 0.074, (0, 0.012, 0.058)))
gpart(cyl("G_ChamberTop", 0.029, 0.010, (0, 0.012, 0.099), brass, bevel=0.002))
gpart(cyl("G_Inlet", 0.0055, 0.022, (0, 0.012, 0.114), brass_d))
for k in range(4):
    a_ = math.pi / 4 + k * math.pi / 2
    gpart(cyl("G_ChamberPost%d" % k, 0.0022, 0.076, (0.028 * math.cos(a_), 0.012 + 0.028 * math.sin(a_), 0.058), brass))
# barrel with decorative rings, muzzle crown and a dark bore disc
gpart(cyl("G_Barrel", 0.012, 0.236, (0, 0.155, 0), brass, rot=RY))
for yy in (0.06, 0.12, 0.20):
    gpart(cyl("G_Ring", 0.0145, 0.006, (0, yy, 0), brass_d, rot=RY, bevel=0.0015))
gpart(cyl("G_Muzzle", 0.0155, 0.014, (0, 0.270, 0), brass, rot=RY, bevel=0.003))
gpart(cyl("G_BoreDisc", 0.0065, 0.001, (0, 0.2773, 0), dark, rot=RY))
# CO2 canister under the barrel + regulator + brass gas line up to the valve on her left (-X) side of the breech
gpart(cyl("G_Canister", 0.0135, 0.120, (0, 0.120, -0.036), can_m, rot=RY, bevel=0.006))
gpart(sphere("G_CanisterNose", 0.0135, (0, 0.180, -0.036), can_m))
gpart(cyl("G_Regulator", 0.010, 0.022, (0, 0.050, -0.036), brass, rot=RY, bevel=0.002))
gpart(box("G_CanClamp", (0.032, 0.010, 0.040), (0, 0.140, -0.020), brass_d, bevel=0.003))
gpart(curve_tube("G_GasLine", [Vector((0, 0.040, -0.036)), Vector((-0.020, 0.030, -0.030)), Vector((-0.030, 0.014, -0.012)), Vector((-0.030, 0.012, -0.004))], 0.0028, brass))
gpart(curve_tube("G_GasIn", [Vector((-0.032, 0.012, 0.004)), Vector((-0.032, 0.012, 0.022)), Vector((-0.026, 0.012, 0.030))], 0.0022, brass))
VX, VY, VZ, VRR = -0.074, 0.012, -0.004, 0.022      # valve wheel on a side stalk, clear of the chamber (her pinch reaches it from the left)
VALVE = empty("G_Valve", (VX, VY, VZ)); VALVE.rotation_euler = (0, math.pi / 2, 0); gpart(VALVE)
vw = cyl("G_ValveHub", 0.006, 0.010, (VX, VY, VZ), red, rot=(0, math.pi / 2, 0))
vr = bpy.data.objects.new("G_ValveRim", bpy.data.curves.new("G_ValveRim", 'CURVE')); sc.collection.objects.link(vr)
vr.data.dimensions = '3D'; vr.data.bevel_depth = 0.0032; vr.data.bevel_resolution = 3
sp = vr.data.splines.new('NURBS'); sp.points.add(23); sp.use_cyclic_u = True; sp.order_u = 4
for k, p_ in enumerate(sp.points):
    t = 2 * math.pi * k / 24; p_.co = (VX - 0.004, VY + VRR * math.cos(t), VZ + VRR * math.sin(t), 1)
vr.data.materials.append(red)
spokes = [curve_tube("G_ValveSpoke%d" % k, [Vector((VX - 0.002, VY, VZ)), Vector((VX - 0.004, VY + VRR * math.cos(k * math.pi / 2 + 0.4), VZ + VRR * math.sin(k * math.pi / 2 + 0.4)))], 0.0022, red) for k in range(4)]
VW = [vw, vr] + spokes
for o in [vr] + spokes:
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
    bpy.ops.object.convert(target='MESH')
for o in VW:
    Mw = o.matrix_world.copy(); o.parent = VALVE; o.matrix_parent_inverse = VALVE.matrix_world.inverted(); o.matrix_world = Mw
gpart(cyl("G_ValveStalk", 0.0042, 0.050, ((VX - 0.022) / 2 + 0.0, VY, VZ), brass, rot=(0, math.pi / 2, 0)))
gpart(cyl("G_ValveBonnet", 0.008, 0.014, (VX + 0.012, VY, VZ), brass_d, rot=(0, math.pi / 2, 0), bevel=0.002))
# grip (wood, raked back 14 deg) with brass butt, trigger guard and the trigger (pivot empty)
gr_ = gpart(box("G_Grip", (0.026, 0.040, 0.105), (0, -0.082, -0.068), woodgrip, bevel=0.010, rot=(R_(-14), 0, 0)))
gpart(box("G_GripButt", (0.029, 0.043, 0.008), (0, -0.095, -0.120), brass, bevel=0.003, rot=(R_(-14), 0, 0)))
gpart(box("G_Frame", (0.030, 0.090, 0.016), (0, -0.068, -0.020), brass, bevel=0.005))
gpart(curve_tube("G_Guard", [Vector((0, -0.064, -0.070)), Vector((0, -0.040, -0.074)), Vector((0, -0.016, -0.060)), Vector((0, -0.010, -0.034)), Vector((0, -0.016, -0.026))], 0.0028, brass))
TRIG = empty("G_TriggerPivot", (0, -0.034, -0.028)); gpart(TRIG)
tr_ = curve_tube("G_Trigger", [Vector((0, -0.034, -0.028)), Vector((0, -0.036, -0.042)), Vector((0, -0.042, -0.054))], 0.0026, brass_d)
Mw = tr_.matrix_world.copy(); tr_.parent = TRIG; tr_.matrix_parent_inverse = TRIG.matrix_world.inverted(); tr_.matrix_world = Mw
# spring + plunger inside the clear rear tube (scale.y animates: 1 = released, 0.36 = cocked)
me = bpy.data.meshes.new("G_Spring"); bm = bmesh.new()
L0, R0, TURNS, W0 = 0.096, 0.0105, 11, 0.0016
path = [Vector((R0 * math.cos(2 * math.pi * TURNS * t), L0 * t, R0 * math.sin(2 * math.pi * TURNS * t))) for t in [i / 440 for i in range(441)]]
cu = bpy.data.curves.new("G_SpringC", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = W0; cu.bevel_resolution = 2
sp = cu.splines.new('POLY'); sp.points.add(len(path) - 1)
for p_, q in zip(sp.points, path): p_.co = (*q, 1)
SPRING = bpy.data.objects.new("G_Spring", cu); sc.collection.objects.link(SPRING); cu.materials.append(steel_s)
SPRING.location = (0, -0.128, 0); gpart(SPRING)
PLUNGER = gpart(cyl("G_Plunger", 0.0135, 0.007, (0, -0.128 + L0 + 0.0035, 0), brass, rot=RY, bevel=0.0015))
sc["SPRING_L0"] = L0
# the cradle on the bench: base board, two posts with V-saddles (the gun RESTS on them)
GUN_POS = Vector((0.0, 0.30, 0.88)); GUN_PITCH = 7.5
GUN.location = GUN_POS; GUN.rotation_euler = (R_(GUN_PITCH), 0, 0)
bpy.context.view_layer.update()
cradle_w = wood("M_Cradle", (0.20, 0.07, 0.02), (0.36, 0.15, 0.05), scale=10.0)
def gw(v): return GUN.matrix_world @ Vector(v)
rear_sad = gw((0, -0.139, -0.020)); front_sad = gw((0, 0.230, -0.012))
box("Cradle_Base", (0.12, 0.50, 0.022), (0, 0.33, BENCH_TOP + 0.011), cradle_w, bevel=0.004)
for nm, p in (("Cradle_PostR", rear_sad), ("Cradle_PostF", front_sad)):
    h = p.z - BENCH_TOP - 0.022
    box(nm, (0.034, 0.030, h), (0, p.y, BENCH_TOP + 0.022 + h / 2), cradle_w, bevel=0.004)
    box(nm + "_Saddle", (0.05, 0.034, 0.016), (0, p.y, p.z - 0.004), brass_d, bevel=0.004)
sc["GUN_POS"] = list(GUN_POS); sc["GUN_PITCH"] = GUN_PITCH; sc["BENCH_TOP"] = BENCH_TOP; sc["SEAT_Z"] = SEAT_Z; sc["DESK_TOP"] = DESK_TOP

# ================================================================== look: AgX Punchy, deep saturated, fast render settings
sc.view_settings.view_transform = 'AgX'
try: sc.view_settings.look = 'AgX - Punchy'
except Exception: pass
sc.view_settings.exposure = -0.6
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
w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.35
def area(name, loc, target, power, size, col):
    ld = bpy.data.lights.new(name, 'AREA'); ld.energy = power; ld.size = size; ld.color = col; ld.shape = 'DISK'
    o = bpy.data.objects.new(name, ld); sc.collection.objects.link(o); o.location = loc
    d = Vector(target) - Vector(loc); o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return o
area("L_BenchKey", (-0.9, 1.3, 2.2), (0.0, 0.0, 1.15), 260, 1.4, (1.0, 0.93, 0.84))
area("L_BenchFill", (1.0, 1.1, 1.5), (0.0, 0.0, 1.15), 110, 1.6, (0.85, 0.93, 1.0))
area("L_BenchRim", (0.6, -1.2, 2.2), (0.0, 0.0, 1.3), 160, 1.0, (1.0, 0.95, 0.90))
area("L_BenchTop", (0.0, 0.35, 2.4), (0.0, 0.35, 0.8), 120, 1.2, (1.0, 0.97, 0.92))
area("L_Range", (0.8, 2.6, 2.5), (0.0, 4.4, 1.2), 260, 1.6, (1.0, 0.95, 0.88))
area("L_RangeFill", (-0.9, 2.2, 1.8), (0.0, 4.4, 1.3), 120, 1.6, (0.88, 0.92, 1.0))
area("L_OfficeKey", (-1.1, 2.4, 2.4), (-2.1, 3.6, 1.2), 280, 1.6, (1.0, 0.90, 0.78))
area("L_OfficeFill", (-3.0, 2.2, 1.8), (-2.1, 3.4, 1.2), 140, 1.6, (0.85, 0.92, 1.0))
area("L_OfficeRim", (-1.6, 4.6, 2.4), (-2.1, 3.2, 1.3), 140, 1.0, (1.0, 0.95, 0.9))
area("L_Ceil", (-0.9, 1.6, 2.85), (-0.9, 1.6, 0.0), 260, 3.0, (1.0, 0.97, 0.93))
sc["INV"] = INV.name; sc["MEN"] = MEN.name
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("BUILD_OK", OUT)
for r in (INV, MEN):
    print("BONES", r.name, {n: tuple(round(x, 3) for x in r.data.bones[n].head_local) for n in ("head", "neck01", "spine03", "upperarm01.R", "wrist.R", "pelvis.L", "upperleg01.L", "lowerleg01.L", "foot.L", "eye.R")})
