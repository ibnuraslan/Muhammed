"""Sets, props, hero gun, lights, render settings.
blender -b work/humans.blend --python scripts/02_build_scene.py -- work/scene.blend
World layout (m): workshop around the origin (she stands at y=+0.55 facing -Y behind the bench),
office at x=+7.5 (window wall at x=+5.2 faces the workshop window at x=+2.4)."""
import sys, os, glob, math
import bpy, bmesh
from mathutils import Vector, Matrix
R_ = math.radians
OUT = sys.argv[sys.argv.index("--") + 1]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PH = os.path.join(ROOT, "assets", "ph")
sc = bpy.context.scene

def coll(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in sc.collection.children: sc.collection.children.link(c)
    return c
C_WS, C_OF, C_GUN, C_FX = coll("Workshop"), coll("Office"), coll("Gun"), coll("FX")

def link(o, c):
    for u in list(o.users_collection): u.objects.unlink(o)
    c.objects.link(o)

# ------------------------------------------------------------------ materials
def mat(name, color, rough=0.5, metal=0.0, trans=0.0, ior=1.45, emit=None, estr=0.0, alpha=1.0, coat=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*color, 1); p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal; p.inputs["Transmission Weight"].default_value = trans
    p.inputs["IOR"].default_value = ior; p.inputs["Alpha"].default_value = alpha
    p.inputs["Coat Weight"].default_value = coat
    if emit: p.inputs["Emission Color"].default_value = (*emit, 1); p.inputs["Emission Strength"].default_value = estr
    return m

def ph_mat(n):
    f = glob.glob(os.path.join(PH, n, "*.blend"))[0]
    with bpy.data.libraries.load(f) as (s, t): t.materials = [n]
    return t.materials[0]

M_BRASS = mat("M_Brass", (0.78, 0.56, 0.26), 0.28, 1.0)
M_BRASS_DK = mat("M_BrassAged", (0.55, 0.38, 0.17), 0.42, 1.0)
M_GLASS = mat("M_Glass", (0.95, 0.98, 1.0), 0.02, 0.0, 1.0, 1.5)
M_TUBE = mat("M_SiliconeTube", (0.92, 0.97, 1.0), 0.08, 0.0, 1.0, 1.41)
M_STEEL = mat("M_Steel", (0.62, 0.63, 0.65), 0.3, 1.0)
M_CANISTER = mat("M_Canister", (0.42, 0.44, 0.47), 0.36, 0.85)
def wear(m, scale=900.0, strength=0.25, rough=(0.25, 0.55)):
    nt_ = m.node_tree; n_ = nt_.nodes; p_ = n_["Principled BSDF"]
    tc_ = n_.new('ShaderNodeTexCoord'); nz_ = n_.new('ShaderNodeTexNoise'); nz_.inputs["Scale"].default_value = scale; nz_.inputs["Detail"].default_value = 10
    mp_ = n_.new('ShaderNodeMapping'); mp_.inputs["Scale"].default_value = (1, 1, 40)     # brushed streaks along one axis
    nz2 = n_.new('ShaderNodeTexNoise'); nz2.inputs["Scale"].default_value = scale * 0.08; nz2.inputs["Detail"].default_value = 6
    bp2 = n_.new('ShaderNodeBump'); bp2.inputs["Strength"].default_value = strength; bp2.inputs["Distance"].default_value = 0.0002
    mr_ = n_.new('ShaderNodeMapRange'); mr_.inputs["To Min"].default_value = rough[0]; mr_.inputs["To Max"].default_value = rough[1]
    L_ = nt_.links
    L_.new(tc_.outputs["Object"], mp_.inputs["Vector"]); L_.new(mp_.outputs["Vector"], nz_.inputs["Vector"]); L_.new(nz_.outputs["Fac"], bp2.inputs["Height"])
    L_.new(bp2.outputs["Normal"], p_.inputs["Normal"]); L_.new(tc_.outputs["Object"], nz2.inputs["Vector"]); L_.new(nz2.outputs["Fac"], mr_.inputs["Value"])
    L_.new(mr_.outputs["Result"], p_.inputs["Roughness"])
wear(M_CANISTER)
M_WOOD = mat("M_GripWood", (0.25, 0.12, 0.05), 0.45, 0.0, coat=0.4)
M_WATER = mat("M_TearWater", (0.9, 0.96, 1.0), 0.02, 0.0, 1.0, 1.33)
M_ICE = mat("M_Ice", (0.92, 0.97, 1.0), 0.12, 0.0, 0.5, 1.31, emit=(0.7, 0.85, 1.0), estr=0.12, coat=1.0)
M_ICE.node_tree.nodes["Principled BSDF"].inputs["Subsurface Weight"].default_value = 0.4
M_ICE.node_tree.nodes["Principled BSDF"].inputs["Subsurface Radius"].default_value = (0.4, 0.6, 1.0)
M_ICE.node_tree.nodes["Principled BSDF"].inputs["Subsurface Scale"].default_value = 0.003
M_SPRING = mat("M_SpringSteel", (0.7, 0.72, 0.75), 0.22, 1.0)
M_RUBBER = mat("M_Rubber", (0.05, 0.05, 0.05), 0.7)
M_PAPER = mat("M_Paper", (0.86, 0.84, 0.78), 0.8)
M_GRAPHITE = mat("M_Graphite", (0.08, 0.08, 0.09), 0.5)
M_DARK = mat("M_NightOutside", (0.02, 0.03, 0.06), 1.0, emit=(0.05, 0.09, 0.2), estr=0.6)
M_DAY = mat("M_DayOutside", (0.8, 0.85, 0.9), 1.0, emit=(0.85, 0.92, 1.0), estr=3.0)
M_PEG = mat("M_Pegboard", (0.42, 0.3, 0.19), 0.7)
def peg_holes(m, pitch=0.025, hole=0.0045):
    nt_ = m.node_tree; n_ = nt_.nodes; p_ = n_["Principled BSDF"]; L_ = nt_.links
    tc_ = n_.new('ShaderNodeTexCoord'); sc_ = n_.new('ShaderNodeVectorMath'); sc_.operation = 'SCALE'; sc_.inputs["Scale"].default_value = 1 / pitch
    fr_ = n_.new('ShaderNodeVectorMath'); fr_.operation = 'FRACTION'
    sb_ = n_.new('ShaderNodeVectorMath'); sb_.operation = 'SUBTRACT'; sb_.inputs[1].default_value = (0.5, 0.5, 0.5)
    mk = n_.new('ShaderNodeVectorMath'); mk.operation = 'MULTIPLY'; mk.inputs[1].default_value = (1, 0, 1)     # board is in the XZ plane
    ln_ = n_.new('ShaderNodeVectorMath'); ln_.operation = 'LENGTH'
    st_ = n_.new('ShaderNodeMath'); st_.operation = 'LESS_THAN'; st_.inputs[1].default_value = hole / pitch
    mx_ = n_.new('ShaderNodeMix'); mx_.data_type = 'RGBA'; mx_.inputs["A"].default_value = (0.42, 0.3, 0.19, 1); mx_.inputs["B"].default_value = (0.03, 0.025, 0.02, 1)
    nzw = n_.new('ShaderNodeTexNoise'); nzw.inputs["Scale"].default_value = 30
    bp_ = n_.new('ShaderNodeBump'); bp_.inputs["Strength"].default_value = 0.6; bp_.invert = True
    for a_, b_ in ((tc_.outputs["Object"], sc_.inputs[0]), (sc_.outputs[0], fr_.inputs[0]), (fr_.outputs[0], sb_.inputs[0]), (sb_.outputs[0], mk.inputs[0]),
                   (mk.outputs[0], ln_.inputs[0]), (ln_.outputs["Value"], st_.inputs[0]), (st_.outputs[0], mx_.inputs["Factor"]), (mx_.outputs["Result"], p_.inputs["Base Color"]),
                   (st_.outputs[0], bp_.inputs["Height"]), (bp_.outputs["Normal"], p_.inputs["Normal"])):
        L_.new(a_, b_)
peg_holes(M_PEG)
M_BLIND = mat("M_Blinds", (0.85, 0.84, 0.8), 0.5)
M_FRAME = mat("M_WindowFrame", (0.75, 0.74, 0.7), 0.5)
M_CONCRETE, M_PLASTER, M_WOODFLOOR, M_BRICK, M_LAMINATE = (ph_mat(n) for n in
    ("concrete_floor_02", "plastered_wall_04", "wood_table_001", "red_brick_03", "laminate_floor_02"))

def blueprint(i):
    m = mat("M_Blueprint_%d" % i, (0.12, 0.25, 0.5), 0.8)
    nt_ = m.node_tree; n_ = nt_.nodes; p_ = n_["Principled BSDF"]; L_ = nt_.links
    tc_ = n_.new('ShaderNodeTexCoord'); br = n_.new('ShaderNodeTexBrick'); br.inputs["Scale"].default_value = 18 + 6 * i
    br.inputs["Color1"].default_value = (0.1, 0.22, 0.45, 1); br.inputs["Color2"].default_value = (0.12, 0.25, 0.5, 1); br.inputs["Mortar"].default_value = (0.75, 0.85, 0.95, 1)
    br.inputs["Mortar Size"].default_value = 0.006; br.offset = 0.0
    wv = n_.new('ShaderNodeTexWave'); wv.wave_type = 'RINGS'; wv.inputs["Scale"].default_value = 2.5 + i; wv.inputs["Distortion"].default_value = 0
    rp = n_.new('ShaderNodeValToRGB'); rp.color_ramp.elements[0].position = 0.97; rp.color_ramp.elements[0].color = (0, 0, 0, 1); rp.color_ramp.elements[1].color = (1, 1, 1, 1)
    mx_ = n_.new('ShaderNodeMix'); mx_.data_type = 'RGBA'; mx_.blend_type = 'SCREEN'
    for a_, b_ in ((tc_.outputs["Object"], br.inputs["Vector"]), (tc_.outputs["Object"], wv.inputs["Vector"]), (wv.outputs["Fac"], rp.inputs[0]),
                   (br.outputs["Color"], mx_.inputs["A"]), (rp.outputs[0], mx_.inputs["B"]), (mx_.outputs["Result"], p_.inputs["Base Color"])):
        L_.new(a_, b_)
    mx_.inputs["Factor"].default_value = 0.6
    return m

def obj_from_bm(name, bm_, material, c, smooth=True):
    me = bpy.data.meshes.new(name); bm_.to_mesh(me); bm_.free()
    o = bpy.data.objects.new(name, me); c.objects.link(o)
    if material: me.materials.append(material)
    if smooth:
        for p in me.polygons: p.use_smooth = True
    return o

def box(name, size, loc, material, c, rot=(0, 0, 0), uvscale=None):
    bm_ = bmesh.new(); bmesh.ops.create_cube(bm_, size=1.0)
    bmesh.ops.scale(bm_, vec=Vector(size), verts=bm_.verts)
    o = obj_from_bm(name, bm_, material, c, smooth=False)
    o.location = loc; o.rotation_euler = [R_(a) for a in rot]
    if uvscale:
        uv = o.data.uv_layers.new()
        for poly in o.data.polygons:
            n = poly.normal
            for li in poly.loop_indices:
                v = o.data.vertices[o.data.loops[li].vertex_index].co
                a, b = (v.y, v.z) if abs(n.x) > 0.5 else ((v.x, v.z) if abs(n.y) > 0.5 else (v.x, v.y))
                uv.data[li].uv = (a / uvscale, b / uvscale)
    return o

def cyl(name, r, depth, loc, material, c, axis="Z", segs=32, r2=None):
    bm_ = bmesh.new()
    bmesh.ops.create_cone(bm_, cap_ends=True, segments=segs, radius1=r, radius2=r if r2 is None else r2, depth=depth)
    o = obj_from_bm(name, bm_, material, c)
    o.location = loc
    if axis == "Y": o.rotation_euler = (R_(90), 0, 0)
    if axis == "X": o.rotation_euler = (0, R_(90), 0)
    bpy.context.view_layer.update()
    return o

def sphere(name, r, loc, material, c, segs=16):
    bm_ = bmesh.new(); bmesh.ops.create_uvsphere(bm_, u_segments=segs, v_segments=max(8, segs // 2), radius=r)
    o = obj_from_bm(name, bm_, material, c); o.location = loc
    return o

def torus(name, R, r, loc, material, c, axis="Z", segs=32):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, major_segments=segs, minor_segments=10, location=loc)
    o = bpy.context.active_object; o.name = name; link(o, c); o.data.materials.append(material)
    if axis == "X": o.rotation_euler = (0, R_(90), 0)
    if axis == "Y": o.rotation_euler = (R_(90), 0, 0)
    for p in o.data.polygons: p.use_smooth = True
    return o

def ph_model(n, loc, rz=0.0, c=None, scale=1.0, name=None):
    f = glob.glob(os.path.join(PH, n, "*.blend"))[0]
    with bpy.data.libraries.load(f) as (s, t): t.objects = s.objects
    root = bpy.data.objects.new(name or ("PH_" + n), None); (c or C_WS).objects.link(root)
    objs = [o for o in t.objects if o and "stash" not in o.name.lower()]
    for o in objs:
        (c or C_WS).objects.link(o)
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(b) for o in objs if o.type == 'MESH' for b in o.bound_box]
    mn = Vector([min(p[i] for p in pts) for i in range(3)]); mx = Vector([max(p[i] for p in pts) for i in range(3)])
    base = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))
    for o in objs:
        if o.parent is None:
            o.parent = root; o.matrix_parent_inverse = Matrix.Translation(-base)
    root.location = loc; root.rotation_euler = (0, 0, R_(rz)); root.scale = (scale,) * 3
    root["size"] = list(mx - mn)
    return root

def plane_uv(name, w, h, loc, rot, material, c, uvscale=2.0):
    bm_ = bmesh.new(); bmesh.ops.create_grid(bm_, x_segments=1, y_segments=1, size=0.5)
    bmesh.ops.scale(bm_, vec=Vector((w, h, 1)), verts=bm_.verts)
    o = obj_from_bm(name, bm_, material, c, smooth=False)
    uv = o.data.uv_layers.new()
    for poly in o.data.polygons:
        for li in poly.loop_indices:
            v = o.data.vertices[o.data.loops[li].vertex_index].co
            uv.data[li].uv = (v.x / uvscale, v.y / uvscale)
    o.location = loc; o.rotation_euler = [R_(a) for a in rot]
    return o

# ------------------------------------------------------------------ WORKSHOP (night)
plane_uv("WS_Floor", 5.0, 6.0, (0, -0.8, 0), (0, 0, 0), M_CONCRETE, C_WS, 2.5)
plane_uv("WS_BackWall", 5.0, 3.0, (0, 1.6, 1.5), (90, 0, 180), M_BRICK, C_WS, 1.5)
plane_uv("WS_LeftWall", 6.0, 3.0, (-2.4, -0.8, 1.5), (90, 0, -90), M_PLASTER, C_WS, 2.0)
# right wall with a window opening (x=+2.4), window centre y=-0.4, z=1.45, 1.1 x 1.0
for nm, w, h, y, z in (("WS_RightWall_a", 2.65, 3.0, 0.775 - 0.0, 1.5), ("WS_RightWall_b", 2.25, 3.0, -2.675, 1.5)):
    plane_uv(nm, w, h, (2.4, y - 0.1, z), (90, 0, 90), M_PLASTER, C_WS, 2.0)
plane_uv("WS_RightWall_low", 1.1, 0.95, (2.4, -0.4, 0.475), (90, 0, 90), M_PLASTER, C_WS, 2.0)
plane_uv("WS_RightWall_high", 1.1, 1.05, (2.4, -0.4, 2.475), (90, 0, 90), M_PLASTER, C_WS, 2.0)
plane_uv("WS_Ceiling", 5.0, 6.0, (0, -0.8, 3.0), (180, 0, 0), M_PLASTER, C_WS, 2.0)
for nm, s, l in (("WS_WinFrameTop", (0.08, 1.2, 0.06), (2.4, -0.4, 1.98)), ("WS_WinFrameBot", (0.12, 1.2, 0.05), (2.4, -0.4, 0.93)),
                 ("WS_WinFrameL", (0.08, 0.05, 1.05), (2.4, 0.15, 1.45)), ("WS_WinFrameR", (0.08, 0.05, 1.05), (2.4, -0.95, 1.45)),
                 ("WS_WinMullion", (0.05, 0.03, 1.0), (2.4, -0.4, 1.45))):
    box(nm, s, l, M_FRAME, C_WS)
# workbench (Poly Haven WoodenTable_03) between her and the camera
bench = ph_model("WoodenTable_03", (0, 0, 0), 0, C_WS, name="WS_Bench")
bench_top = bench["size"][2]
sc["bench_top"] = bench_top
ph_model("bench_vice_01", (-0.5, 0.05, bench_top), 90, C_WS, name="WS_Vice")
ph_model("desk_lamp_arm_01", (0.52, 0.15, bench_top), -140, C_WS, name="WS_Lamp", scale=0.8)
ph_model("hand_plane_no4", (-0.15, -0.22, bench_top), 20, C_WS)
ph_model("small_oil_can_01", (0.62, -0.15, bench_top), -30, C_WS)
ph_model("magnifying_glass_01", (-0.3, -0.2, bench_top), 0, C_WS)
ph_model("old_drill_press", (-1.7, 0.9, 0), 160, C_WS)
ph_model("metal_tool_chest", (1.6, 1.1, 0), 180, C_WS)
ph_model("wooden_bookshelf_worn", (-2.05, -0.9, 0), 90, C_WS)
ph_model("cardboard_box_01", (1.65, -1.8, 0), 25, C_WS)
# lying tools for the bench (screwdriver, pliers, wrench, hammer) laid flat
for n, l, r in (("screwdrivers_02", (0.12, -0.27, bench_top + 0.012), 75), ("pliers", (-0.35, 0.18, bench_top + 0.012), 40),
                ("adjustable_wrench", (0.42, 0.25, bench_top + 0.012), -20), ("cross_pein_hammer", (-0.62, -0.2, bench_top + 0.022), 100)):
    o = ph_model(n, l, r, C_WS)
    if n != "screwdrivers_02":
        o.rotation_euler = (R_(90), 0, R_(r)); o.location.z = bench_top + 0.012
# pegboard on the back wall with hung tools
box("WS_Pegboard", (1.8, 0.02, 0.9), (0, 1.58, 1.55), M_PEG, C_WS)
for i, (n, x) in enumerate((("adjustable_wrench", -0.6), ("cross_pein_hammer", -0.25), ("pliers", 0.15), ("screwdrivers_02", 0.5))):
    o = ph_model(n, (x, 1.55, 1.35), 0, C_WS, name="WS_Peg_%d" % i)
    o.rotation_euler = (R_(90 if n != "screwdrivers_02" else 0), 0, 0) if n == "screwdrivers_02" else (0, 0, 0)
    if n == "screwdrivers_02": o.rotation_euler = (R_(90), 0, 0)
# brass stock shelf on the left wall: jars and rods
for i in range(7):
    cyl("WS_Rod_%d" % i, 0.008 + 0.003 * (i % 3), 0.45, (-2.2, -0.3 + i * 0.06, 1.5), M_BRASS_DK if i % 2 else M_BRASS, C_WS, axis="X")
box("WS_ShelfBoard", (0.28, 1.0, 0.03), (-2.25, -0.1, 1.48), M_WOOD, C_WS)
for i in range(5):
    cyl("WS_Jar_%d" % i, 0.045, 0.12, (-2.25, -0.5 + i * 0.2, 1.56), M_GLASS, C_WS)
# pinned sketches on the back wall (blank lines, no text)
for i, (x, z, r) in enumerate(((0.95, 1.75, 4), (1.25, 1.55, -6), (-1.05, 1.8, -3))):
    p = box("WS_Sketch_%d" % i, (0.21, 0.004, 0.297), (x, 1.575, z), M_PAPER, C_WS, rot=(0, r, 0))
# coffee mug with steam spot on bench
mug = cyl("WS_Mug", 0.04, 0.095, (0.33, 0.12, bench_top + 0.0475), mat("M_Mug", (0.55, 0.18, 0.12), 0.35, coat=0.6), C_WS)
plane_uv("WS_NightOutside", 3.0, 2.5, (3.6, -0.4, 1.4), (90, 0, 90), M_DARK, C_WS, 2.0)

# ------------------------------------------------------------------ OFFICE (memory, daylight), x from 5.2 to 10.2
OX = 7.7
plane_uv("OF_Floor", 5.0, 5.0, (OX, 0, 0), (0, 0, 0), M_LAMINATE, C_OF, 1.7)
plane_uv("OF_BackWall", 5.0, 3.0, (OX, 2.5, 1.5), (90, 0, 180), M_PLASTER, C_OF, 2.0)
plane_uv("OF_FrontWall", 5.0, 3.0, (OX, -2.5, 1.5), (90, 0, 0), M_PLASTER, C_OF, 2.0)
plane_uv("OF_FarWall", 5.0, 3.0, (OX + 2.5, 0, 1.5), (90, 0, -90), M_PLASTER, C_OF, 2.0)
plane_uv("OF_Ceiling", 5.0, 5.0, (OX, 0, 3.0), (180, 0, 0), M_PLASTER, C_OF, 2.0)
# window wall at x=5.2 with a big opening y in [-1.2, 0.6], z in [0.9, 2.2]
for nm, w, h, y, z in (("OF_WinWall_a", 1.9, 3.0, 1.55, 1.5), ("OF_WinWall_b", 1.3, 3.0, -1.85, 1.5),
                       ("OF_WinWall_lo", 1.8, 0.9, -0.3, 0.45), ("OF_WinWall_hi", 1.8, 0.8, -0.3, 2.6)):
    plane_uv(nm, w, h, (OX - 2.5, y, z), (90, 0, 90), M_PLASTER, C_OF, 2.0)
_city = plane_uv("OF_DayOutside", 4.0, 2.9, (OX - 3.6, -0.3, 1.6), (90, 0, 90), None, C_OF, 2.0)
M_CITY = bpy.data.materials.new("M_CityView"); M_CITY.use_nodes = True
cn_ = M_CITY.node_tree.nodes; cn_.remove(cn_["Principled BSDF"])
ci = cn_.new('ShaderNodeTexImage'); ci.image = bpy.data.images.load(os.path.join(ROOT, "assets", "tex", "office_city_view.jpg"))
ctc = cn_.new('ShaderNodeTexCoord'); cem = cn_.new('ShaderNodeEmission'); cem.inputs["Strength"].default_value = 2.2
M_CITY.node_tree.links.new(ctc.outputs["Generated"], ci.inputs["Vector"]); M_CITY.node_tree.links.new(ci.outputs["Color"], cem.inputs["Color"])
M_CITY.node_tree.links.new(cem.outputs[0], cn_["Material Output"].inputs["Surface"])
_city.data.materials.append(M_CITY)
for i in range(11):   # blinds, half-open slats
    box("OF_Blind_%d" % i, (0.01, 1.8, 0.05), (OX - 2.45, -0.3, 2.15 - i * 0.12), M_BLIND, C_OF, rot=(50, 0, 0))
desk = ph_model("metal_office_desk", (OX + 0.3, 0.6, 0), 180, C_OF, name="OF_Desk")
sc["desk_top"] = desk["size"][2]
ph_model("modern_arm_chair_01", (OX + 0.3, 1.75, 0), 0, C_OF, name="OF_ChairMentor")
ph_model("modern_arm_chair_01", (OX + 0.3, -0.45, 0), 180, C_OF, name="OF_ChairHer")
ph_model("wooden_bookshelf_worn", (OX + 1.6, 2.2, 0), 180, C_OF, name="OF_Shelf")
ph_model("book_encyclopedia_set_01", (OX + 1.6, 2.15, 1.02), 180, C_OF, scale=1.0)
ph_model("potted_plant_01", (OX + 2.1, 1.4, 0), 0, C_OF)
ph_model("wooden_bookshelf_worn", (OX + 0.2, 2.2, 0), 180, C_OF, name="OF_Shelf2")
ph_model("book_encyclopedia_set_01", (OX + 0.2, 2.15, 1.42), 180, C_OF, name="OF_Books2")
for k_, z_ in enumerate((0.03, 0.43, 0.83, 1.22, 1.62)):
    ph_model("book_encyclopedia_set_01", (OX + 0.2 + 0.25 * ((k_ % 2) - 0.5), 2.15, z_), 180 + 4 * k_, C_OF, name="OF_BooksS_%d" % k_)
    ph_model("book_encyclopedia_set_01", (OX + 1.6 - 0.25 * ((k_ % 2) - 0.5), 2.15, z_), 176 - 4 * k_, C_OF, name="OF_BooksT_%d" % k_)
ph_model("book_encyclopedia_set_01", (OX + 1.6, 2.15, 0.62), 180, C_OF, name="OF_Books3")
ph_model("cardboard_box_01", (OX + 2.0, -1.8, 0), 30, C_OF, name="OF_Box", scale=0.9)
ph_model("hanging_picture_frame_01", (OX - 0.9, 2.47, 1.55), 0, C_OF)
dt = desk["size"][2]
ph_model("office_notepads", (OX + 0.05, 0.45, dt), 15, C_OF)
ph_model("desk_lamp_arm_01", (OX - 0.9, 0.75, dt), 30, C_OF, name="OF_DeskLamp", scale=0.8)
for i in range(6):   # loose papers on the desk (blank)
    box("OF_Paper_%d" % i, (0.21, 0.297, 0.001), (OX + 0.1 + 0.11 * math.sin(i * 2.1), 0.5 + 0.08 * math.cos(i * 1.7), dt + 0.001 + 0.0012 * i),
        M_PAPER, C_OF, rot=(0, 0, 13 * i))
# blank monitor (no logo)
box("OF_MonitorBase", (0.2, 0.15, 0.015), (OX - 0.55, 0.85, dt + 0.0075), M_RUBBER, C_OF)
box("OF_MonitorNeck", (0.04, 0.03, 0.3), (OX - 0.55, 0.88, dt + 0.16), M_RUBBER, C_OF)
box("OF_Monitor", (0.55, 0.03, 0.33), (OX - 0.55, 0.86, dt + 0.42), M_RUBBER, C_OF, rot=(0, 0, -8))
box("OF_MonitorScreen", (0.52, 0.002, 0.30), (OX - 0.55 + 0.002, 0.844, dt + 0.42), mat("M_Screen", (0.05, 0.08, 0.12), 0.15, emit=(0.25, 0.4, 0.55), estr=0.8), C_OF, rot=(0, 0, -8))

# workshop front wall (y=-3.8) with a framed picture the pellets fly into
plane_uv("WS_FrontWall", 5.0, 3.0, (0, -3.8, 1.5), (90, 0, 0), M_PLASTER, C_WS, 2.0)
ph_model("wooden_bookshelf_worn", (-1.45, -3.5, 0), 180, C_WS, name="WS_FrontShelf")
ph_model("cardboard_box_01", (-1.45, -3.5, 1.42), 170, C_WS, name="WS_FrontBox", scale=0.7)
ph_model("metal_tool_chest", (1.5, -3.35, 0), 0, C_WS, name="WS_FrontChest")
ph_model("small_oil_can_01", (1.4, -3.3, 0.8), 40, C_WS, name="WS_FrontCan")
box("WS_Door", (0.9, 0.04, 2.05), (1.0, -3.78, 1.025), M_WOODFLOOR, C_WS, uvscale=1.5)
for k_, (pz, ph_) in enumerate(((1.55, 0.75), (0.6, 0.85))):
    box("WS_DoorPanel_%d" % k_, (0.62, 0.012, ph_), (1.0, -3.757, pz), M_WOODFLOOR, C_WS, uvscale=1.5)
box("WS_DoorFrame", (1.02, 0.06, 0.06), (1.0, -3.77, 2.08), M_FRAME, C_WS)
cyl("WS_DoorKnob", 0.028, 0.05, (0.62, -3.735, 1.02), M_BRASS_DK, C_WS, axis="Y")
sphere("WS_DoorKnobBall", 0.03, (0.62, -3.705, 1.02), M_BRASS_DK, C_WS)
for i in range(3):
    box("WS_Poster_%d" % i, (0.3, 0.004, 0.4), (-0.75 + 0.42 * i, -3.775, 1.75 + 0.05 * (i % 2)), blueprint(i), C_WS, rot=(0, 3 - 3 * i, 0))
pf = ph_model("hanging_picture_frame_01", (0.05, -3.78, 0.85), 180, C_WS, name="WS_PhotoFrame")

# ------------------------------------------------------------------ THE TEAR GUN (local: barrel along -Y, up +Z, origin at the grip top)
gun = bpy.data.objects.new("Gun", None); C_GUN.objects.link(gun); gun.empty_display_size = 0.05
def gpart(o):
    o.parent = gun; return o
g = {}
grip = box("Gun_Grip", (0.026, 0.04, 0.095), (0, 0.022, -0.045), M_WOOD, C_GUN, rot=(-14, 0, 0)); gpart(grip)
bev = grip.modifiers.new("bev", 'BEVEL'); bev.width = 0.006; bev.segments = 3
gpart(cyl("Gun_Receiver", 0.022, 0.08, (0, -0.01, 0.034), M_BRASS, C_GUN, axis="Y"))
gpart(cyl("Gun_RearCap", 0.018, 0.012, (0, 0.034, 0.034), M_BRASS_DK, C_GUN, axis="Y"))
gpart(cyl("Gun_SpringWindow", 0.022, 0.09, (0, -0.095, 0.034), M_GLASS, C_GUN, axis="Y"))
for nm, y in (("Gun_RingA", -0.05), ("Gun_RingB", -0.14)):
    gpart(cyl(nm, 0.026, 0.009, (0, y, 0.034), M_BRASS_DK, C_GUN, axis="Y"))
gpart(cyl("Gun_Barrel", 0.0095, 0.11, (0, -0.195, 0.034), M_BRASS, C_GUN, axis="Y"))
gpart(cyl("Gun_Muzzle", 0.013, 0.012, (0, -0.248, 0.034), M_BRASS_DK, C_GUN, axis="Y"))
# glass reservoir chamber on top
gpart(cyl("Gun_ChamberGlass", 0.026, 0.055, (0, -0.095, 0.0935), M_GLASS, C_GUN, segs=40))
gpart(cyl("Gun_ChamberCollar", 0.029, 0.008, (0, -0.095, 0.062), M_BRASS_DK, C_GUN))
gpart(cyl("Gun_ChamberCap", 0.029, 0.01, (0, -0.095, 0.126), M_BRASS, C_GUN))
gpart(cyl("Gun_Inlet", 0.0045, 0.018, (0, -0.095, 0.14), M_BRASS, C_GUN))
gpart(cyl("Gun_FeedNeck", 0.008, 0.012, (0, -0.095, 0.054), M_BRASS, C_GUN))
# CO2 canister under the barrel (plain, unbranded) + valve on the +X side of the chamber
prof_c = [(0.0, 0.0), (0.006, 0.0008), (0.0105, 0.003), (0.0128, 0.0065), (0.0135, 0.011), (0.0135, 0.066), (0.0131, 0.071),
          (0.0115, 0.0765), (0.0085, 0.0805), (0.0062, 0.0825), (0.0058, 0.084)]
for k in range(7):
    prof_c += [(0.0062, 0.0845 + k * 0.0012), (0.0056, 0.0851 + k * 0.0012)]
prof_c += [(0.0045, 0.0935), (0.0, 0.0935)]
mc = bpy.data.meshes.new("Gun_Canister"); mc.from_pydata([(r_, 0, z_) for r_, z_ in prof_c], [(i, i + 1) for i in range(len(prof_c) - 1)], [])
can = bpy.data.objects.new("Gun_Canister", mc); C_GUN.objects.link(can); mc.materials.append(M_CANISTER)
scw = can.modifiers.new("lathe", 'SCREW'); scw.axis = 'Z'; scw.steps = 48; scw.render_steps = 48; scw.use_merge_vertices = True; scw.use_normal_calculate = True
can.modifiers.new("sm", 'WEIGHTED_NORMAL') if False else None
for pl in mc.polygons: pl.use_smooth = True
can.location = (0, -0.06, -0.004); can.rotation_euler = (R_(90), 0, 0); gpart(can)
gpart(cyl("Gun_CanisterNozzle", 0.006, 0.012, (0, -0.155, -0.004), M_BRASS_DK, C_GUN, axis="Y"))
gpart(cyl("Gun_CanisterBand", 0.0145, 0.006, (0, -0.075, -0.004), M_BRASS_DK, C_GUN, axis="Y"))
pipe_c = bpy.data.curves.new("Gun_GasPipe", 'CURVE'); pipe_c.dimensions = '3D'; pipe_c.bevel_depth = 0.0022; pipe_c.bevel_resolution = 3
sp = pipe_c.splines.new('BEZIER'); pts = [(0, -0.16, -0.004), (0.03, -0.16, 0.02), (0.034, -0.12, 0.06), (0.034, -0.095, 0.085)]
sp.bezier_points.add(len(pts) - 1)
for bp, p in zip(sp.bezier_points, pts): bp.co = p; bp.handle_left_type = bp.handle_right_type = 'AUTO'
pipe = bpy.data.objects.new("Gun_GasPipe", pipe_c); C_GUN.objects.link(pipe); pipe_c.materials.append(M_BRASS_DK); gpart(pipe)
gpart(cyl("Gun_ValveBody", 0.007, 0.022, (0.036, -0.095, 0.085), M_BRASS, C_GUN, axis="X"))
wheel = bpy.data.objects.new("Gun_ValveWheel", None); C_GUN.objects.link(wheel); wheel.parent = gun
wheel.location = (0.05, -0.095, 0.085); wheel.empty_display_size = 0.01
w_r = torus("Gun_ValveRim", 0.0125, 0.0022, (0, 0, 0), M_BRASS, C_GUN, axis="X"); w_r.parent = wheel; w_r.location = (0, 0, 0)
for i in range(3):
    s_ = box("Gun_ValveSpoke_%d" % i, (0.003, 0.024, 0.003), (0, 0, 0), M_BRASS, C_GUN, rot=(60 * i, 0, 0)); s_.parent = wheel
gpart(cyl("Gun_ValveHub", 0.004, 0.006, (0.05, -0.095, 0.085), M_BRASS_DK, C_GUN, axis="X"))
# trigger + guard
trig = bpy.data.objects.new("Gun_TriggerPivot", None); C_GUN.objects.link(trig); trig.parent = gun; trig.location = (0, -0.01, 0.012)
t_ = box("Gun_Trigger", (0.005, 0.007, 0.026), (0, -0.004, -0.013), M_STEEL, C_GUN, rot=(12, 0, 0)); t_.parent = trig
guard = torus("Gun_TriggerGuard", 0.02, 0.0022, (0, -0.016, 0.0), M_BRASS_DK, C_GUN, axis="X"); gpart(guard)
# spring + plunger inside the window: spring fixed at the rear (y=-0.052), plunger at its front end
sm = bmesh.new()
turns, seg, rr, wire = 9, 14, 0.0135, 0.0018
prof = [(math.cos(2 * math.pi * k / 8) * wire, math.sin(2 * math.pi * k / 8) * wire) for k in range(8)]
N = turns * seg
rings = []
for i in range(N + 1):
    t = i / N; a = 2 * math.pi * turns * t
    c_ = Vector((rr * math.cos(a), -t, rr * math.sin(a)))
    tang = Vector((-rr * math.sin(a) * 2 * math.pi * turns, -1, rr * math.cos(a) * 2 * math.pi * turns)).normalized()
    nrm = Vector((math.cos(a), 0, math.sin(a))); bin_ = tang.cross(nrm).normalized(); nrm = bin_.cross(tang)
    rings.append([sm.verts.new(c_ + nrm * px * Vector((1, 1 / 1, 1)) + bin_ * py) for px, py in prof])
for i in range(N):
    for k in range(8):
        sm.faces.new((rings[i][k], rings[i][(k + 1) % 8], rings[i + 1][(k + 1) % 8], rings[i + 1][k]))
spring = obj_from_bm("Gun_Spring", sm, M_SPRING, C_GUN); spring.parent = gun
spring.location = (0, -0.052, 0.034); spring.scale = (1, 0.075, 1)
plunger = cyl("Gun_Plunger", 0.0125, 0.006, (0, -0.128, 0.034), M_BRASS_DK, C_GUN, axis="Y"); plunger.parent = gun
gun.location = (0.05, 0.2, 1.1)

# ------------------------------------------------------------------ monocle funnel + tube, built at the rest pose on the Inventor's head
W = bpy.data.objects["Inventor"]; body = bpy.data.objects["Inventor.body"]
bpy.context.view_layer.update()
eyeL = W.matrix_world @ W.data.bones["eye.L"].head_local
dg = bpy.context.evaluated_depsgraph_get()
be = body.evaluated_get(dg)
inv = be.matrix_world.inverted()
def skin_point(p):
    """first body hit shooting from the front (-Y) toward +Y through x,z of p"""
    o = inv @ Vector((p.x, p.y - 0.3, p.z)); d = (inv.to_3x3() @ Vector((0, 1, 0))).normalized()
    hit, loc, nrm, idx = be.ray_cast(o, d)
    return (be.matrix_world @ loc, (be.matrix_world.to_3x3() @ nrm).normalized()) if hit else (p, Vector((0, -1, 0)))
sc["eyeL"] = list(eyeL)
lid, lidn = skin_point(eyeL + Vector((0.0, 0, -0.016)))
cheek, cheekn = skin_point(eyeL + Vector((0.004, 0, -0.034)))
sc["lidL"] = list(lid); sc["cheekL"] = list(cheek)
eyeR = W.matrix_world @ W.data.bones["eye.R"].head_local
lidR, _ = skin_point(eyeR + Vector((0, 0, -0.016)))
sc["lidR"] = list(lidR)
for k, dz, dx in (("cheekR1", -0.035, -0.004), ("cheekR2", -0.055, -0.01), ("cheekR3", -0.075, -0.012), ("chinR", -0.095, -0.015)):
    p_, _ = skin_point(eyeR + Vector((dx, 0, dz))); sc[k] = list(p_)
M_WET = mat("M_WetStreak", (0.9, 0.95, 1.0), 0.03, 0.0, 1.0, 1.33)
for nm, pts_ in (("TearStreakR", [lidR] + [Vector(sc[k]) for k in ("cheekR1", "cheekR2", "cheekR3", "chinR")]),):
    cu = bpy.data.curves.new(nm, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.0011; cu.bevel_resolution = 2
    spl = cu.splines.new('BEZIER'); spl.bezier_points.add(len(pts_) - 1)
    for bp, p_ in zip(spl.bezier_points, pts_):
        bp.co = p_ + Vector((0, -0.0016, 0)); bp.handle_left_type = bp.handle_right_type = 'AUTO'
    so = bpy.data.objects.new(nm, cu); C_GUN.objects.link(so); cu.materials.append(M_WET)
    mw = so.matrix_world.copy(); so.parent = W; so.parent_type = 'BONE'; so.parent_bone = "head"; bpy.context.view_layer.update(); so.matrix_world = mw
funnel_mouth = cheek + cheekn * 0.0165 + Vector((0, 0, 0.004))
fun = cyl("Funnel", 0.0035, 0.02, (0, 0, 0), M_BRASS, C_GUN, r2=0.013, segs=32)
fun.data.transform(Matrix.Translation((0, 0, -0.01)))      # origin at the wide mouth
sol = fun.modifiers.new("sol", 'SOLIDIFY'); sol.thickness = 0.0008
# remove the caps so it is an open cone
bmf = bmesh.new(); bmf.from_mesh(fun.data)
caps = [f for f in bmf.faces if abs(f.normal.z) > 0.99]; bmesh.ops.delete(bmf, geom=caps, context='FACES'); bmf.to_mesh(fun.data); bmf.free()
fun.location = funnel_mouth
fun.rotation_euler = (R_(-12), R_(-8), 0)
rim = torus("Funnel_Rim", 0.013, 0.0012, (0, 0, 0), M_BRASS_DK, C_GUN); rim.parent = fun
# arm from the funnel to above the ear
arm_c = bpy.data.curves.new("Funnel_Arm", 'CURVE'); arm_c.dimensions = '3D'; arm_c.bevel_depth = 0.0012
ear = W.matrix_world @ W.data.bones["temporalis02.L"].head_local
sp = arm_c.splines.new('BEZIER'); pts = [funnel_mouth + Vector((0.012, 0.0, 0.0)), cheek + Vector((0.035, 0.03, 0.01)), ear + Vector((0.01, 0.02, 0.0))]
sp.bezier_points.add(len(pts) - 1)
for bp, p in zip(sp.bezier_points, pts): bp.co = p; bp.handle_left_type = bp.handle_right_type = 'AUTO'
arm = bpy.data.objects.new("Funnel_Arm", arm_c); C_GUN.objects.link(arm); arm_c.materials.append(M_BRASS_DK)
for o in (fun, arm):
    mw = o.matrix_world.copy(); o.parent = W; o.parent_type = 'BONE'; o.parent_bone = "head"
    bpy.context.view_layer.update(); o.matrix_world = mw
sc["funnel_tip"] = list(fun.matrix_world @ Vector((0, 0, -0.02)))
# tube: hooked bezier from the funnel tip down the neck to the gun inlet
tube_c = bpy.data.curves.new("TearTube", 'CURVE'); tube_c.dimensions = '3D'; tube_c.bevel_depth = 0.003; tube_c.bevel_resolution = 3
tube_c.resolution_u = 16; tube_c.use_path = True
sp = tube_c.splines.new('BEZIER'); sp.bezier_points.add(4)
tube = bpy.data.objects.new("TearTube", tube_c); C_GUN.objects.link(tube); tube_c.materials.append(M_TUBE)
tip = Vector(sc["funnel_tip"])
neck = W.matrix_world @ W.data.bones["neck01"].head_local
anchors = [("TubeH0", tip, "head"), ("TubeH1", tip + Vector((0.012, -0.012, -0.05)), "head"),
           ("TubeH2", neck + Vector((0.06, -0.09, -0.04)), "spine01"), ("TubeH3", None, "gun_up"), ("TubeH4", None, "gun")]
for bp in sp.bezier_points: bp.handle_left_type = bp.handle_right_type = 'AUTO'
for i, (nm, p, par) in enumerate(anchors):
    e = bpy.data.objects.new(nm, None); C_GUN.objects.link(e); e.empty_display_size = 0.01
    if par in ("gun", "gun_up"):
        e.parent = gun; e.location = (0, -0.095, 0.149 if par == "gun" else 0.2)
    else:
        e.location = p
        bpy.context.view_layer.update(); mw = e.matrix_world.copy()
        e.parent = W; e.parent_type = 'BONE'; e.parent_bone = par; bpy.context.view_layer.update(); e.matrix_world = mw
bpy.context.view_layer.update()
for i, (nm, _, _) in enumerate(anchors):
    sp.bezier_points[i].co = bpy.data.objects[nm].matrix_world.translation
    sp.bezier_points[i].handle_left = sp.bezier_points[i].co; sp.bezier_points[i].handle_right = sp.bezier_points[i].co
for bp in sp.bezier_points: bp.handle_left_type = bp.handle_right_type = 'AUTO'
for i, (nm, _, _) in enumerate(anchors):
    h = tube.modifiers.new(nm, 'HOOK'); h.object = bpy.data.objects[nm]
    # hook vertex indices: each bezier point = 3 verts (left handle, co, right handle)
    h.vertex_indices_set([i * 3, i * 3 + 1, i * 3 + 2])
    h.center = bpy.data.objects[nm].matrix_world.translation
    h.matrix_inverse = bpy.data.objects[nm].matrix_world.inverted()

# ------------------------------------------------------------------ tears (water drops that turn to ice)
def drop_mat(i):
    m = bpy.data.materials.new("M_Tear_%02d" % i); m.use_nodes = True
    nt = m.node_tree; n = nt.nodes; n.remove(n["Principled BSDF"])
    out = n["Material Output"]
    w = n.new('ShaderNodeBsdfPrincipled'); w.inputs["Base Color"].default_value = (0.9, 0.96, 1.0, 1); w.inputs["Roughness"].default_value = 0.02
    w.inputs["Transmission Weight"].default_value = 1.0; w.inputs["IOR"].default_value = 1.33
    ic = n.new('ShaderNodeBsdfPrincipled'); ic.inputs["Base Color"].default_value = (0.93, 0.97, 1.0, 1); ic.inputs["Roughness"].default_value = 0.3
    ic.inputs["Transmission Weight"].default_value = 0.15; ic.inputs["IOR"].default_value = 1.31
    ic.inputs["Emission Color"].default_value = (0.7, 0.85, 1.0, 1); ic.inputs["Emission Strength"].default_value = 0.25
    ic.inputs["Subsurface Weight"].default_value = 0.5; ic.inputs["Subsurface Scale"].default_value = 0.002
    ic.inputs["Coat Weight"].default_value = 0.6; ic.inputs["Coat Roughness"].default_value = 0.05
    nz = n.new('ShaderNodeTexNoise'); nz.inputs["Scale"].default_value = 900; nz.inputs["Detail"].default_value = 6
    bp_ = n.new('ShaderNodeBump'); bp_.inputs["Strength"].default_value = 0.6
    nt.links.new(nz.outputs["Fac"], bp_.inputs["Height"]); nt.links.new(bp_.outputs["Normal"], ic.inputs["Normal"])
    mx = n.new('ShaderNodeMixShader'); v = n.new('ShaderNodeValue'); v.name = "Freeze"; v.outputs[0].default_value = 0.0
    nt.links.new(v.outputs[0], mx.inputs[0]); nt.links.new(w.outputs[0], mx.inputs[1]); nt.links.new(ic.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    return m
for i in range(14):
    d = sphere("Tear_%02d" % i, 0.0028, (0, 0, -50), drop_mat(i), C_FX, segs=16)
for i in range(6):
    sphere("TearR_%02d" % i, 0.0024, (0, 0, -50), M_WATER, C_FX, segs=12)
# frost crystals: spiky instances on the inside of the chamber glass, scale keyed
fr_bm = bmesh.new()
import random
random.seed(3)
for i in range(90):
    a = random.uniform(0, 2 * math.pi); z = random.uniform(-0.024, 0.022); r_ = 0.0245
    base = Vector((r_ * math.cos(a), r_ * math.sin(a), z))
    inward = Vector((-math.cos(a), -math.sin(a), random.uniform(-0.4, 0.4))).normalized()
    ln = random.uniform(0.002, 0.006)
    side = inward.cross(Vector((0, 0, 1))).normalized() * 0.0007
    v0 = fr_bm.verts.new(base + side); v1 = fr_bm.verts.new(base - side); v2 = fr_bm.verts.new(base + inward * ln)
    v3 = fr_bm.verts.new(base + Vector((0, 0, 0.0007)))
    fr_bm.faces.new((v0, v1, v2)); fr_bm.faces.new((v0, v3, v2)); fr_bm.faces.new((v1, v3, v2))
frost = obj_from_bm("Frost", fr_bm, mat("M_Frost", (0.92, 0.97, 1.0), 0.25, 0.0, 0.3, 1.31, emit=(0.6, 0.8, 1.0), estr=0.15), C_GUN, smooth=False)
frost.parent = gun; frost.location = (0, -0.095, 0.0935)
# gas puffs (volume) from the valve nozzle into the chamber
gm = bpy.data.materials.new("M_Gas"); gm.use_nodes = True
gn = gm.node_tree.nodes; gn.remove(gn["Principled BSDF"])
pv = gn.new('ShaderNodeVolumePrincipled'); pv.inputs["Color"].default_value = (0.95, 0.97, 1.0, 1)
gnz = gn.new('ShaderNodeTexNoise'); gnz.inputs["Scale"].default_value = 160; gnz.inputs["Detail"].default_value = 4
gmr = gn.new('ShaderNodeMapRange'); gmr.inputs["From Min"].default_value = 0.45; gmr.inputs["From Max"].default_value = 0.75
gmr.inputs["To Max"].default_value = 70.0
gvl = gn.new('ShaderNodeValue'); gvl.name = "GasDensity"; gvl.outputs[0].default_value = 0.0
gmul = gn.new('ShaderNodeMath'); gmul.operation = 'MULTIPLY'
gm.node_tree.links.new(gnz.outputs["Fac"], gmr.inputs["Value"]); gm.node_tree.links.new(gmr.outputs["Result"], gmul.inputs[0])
gtc = gn.new('ShaderNodeTexCoord'); glen = gn.new('ShaderNodeVectorMath'); glen.operation = 'LENGTH'
gfo = gn.new('ShaderNodeMapRange'); gfo.inputs["From Min"].default_value = 0.012; gfo.inputs["From Max"].default_value = 0.0; gfo.inputs["To Max"].default_value = 1.0
gm2 = gn.new('ShaderNodeMath'); gm2.operation = 'MULTIPLY'
gm.node_tree.links.new(gtc.outputs["Object"], glen.inputs[0]); gm.node_tree.links.new(glen.outputs["Value"], gfo.inputs["Value"])
gm.node_tree.links.new(gtc.outputs["Object"], gnz.inputs["Vector"])
gm.node_tree.links.new(gvl.outputs[0], gm2.inputs[0]); gm.node_tree.links.new(gfo.outputs["Result"], gm2.inputs[1])
gm.node_tree.links.new(gm2.outputs[0], gmul.inputs[1]); gm.node_tree.links.new(gmul.outputs[0], pv.inputs["Density"])
gm.node_tree.links.new(pv.outputs[0], gn["Material Output"].inputs["Volume"])
for i in range(6):
    p = sphere("Gas_%d" % i, 0.012, (0, 0, -50), gm, C_FX, segs=12)
# pellets (fired ice) + glints
M_GLINT = mat("M_Glint", (1, 1, 1), 0.5, emit=(0.8, 0.92, 1.0), estr=40.0)
for i in range(12):
    sphere("Pellet_%02d" % i, 0.0042, (0, 0, -50), M_ICE, C_FX, segs=14)
    gl = bpy.data.objects.new("Glint_%02d" % i, None)
for i in range(24):
    o = sphere("Spark_%02d" % i, 0.0012, (0, 0, -50), M_GLINT, C_FX, segs=6)
# frost puff on impact (beat 13) + muzzle frost
M_PUFF = bpy.data.materials.new("M_FrostPuff"); M_PUFF.use_nodes = True
pn = M_PUFF.node_tree.nodes; pn.remove(pn["Principled BSDF"])
pv2 = pn.new('ShaderNodeVolumePrincipled'); pv2.inputs["Color"].default_value = (0.92, 0.96, 1.0, 1)
pnz = pn.new('ShaderNodeTexNoise'); pnz.inputs["Scale"].default_value = 18; pnz.inputs["Detail"].default_value = 4
pmr = pn.new('ShaderNodeMapRange'); pmr.inputs["From Min"].default_value = 0.5; pmr.inputs["From Max"].default_value = 0.8; pmr.inputs["To Max"].default_value = 60.0
pvl = pn.new('ShaderNodeValue'); pvl.name = "PuffDensity"; pvl.outputs[0].default_value = 0.0
pml = pn.new('ShaderNodeMath'); pml.operation = 'MULTIPLY'
lk = M_PUFF.node_tree.links
ptc = pn.new('ShaderNodeTexCoord'); plen = pn.new('ShaderNodeVectorMath'); plen.operation = 'LENGTH'
pfo = pn.new('ShaderNodeMapRange'); pfo.name = "PuffFalloff"; pfo.inputs["From Min"].default_value = 0.12; pfo.inputs["From Max"].default_value = 0.03
pm2 = pn.new('ShaderNodeMath'); pm2.operation = 'MULTIPLY'
lk.new(ptc.outputs["Object"], plen.inputs[0]); lk.new(plen.outputs["Value"], pfo.inputs["Value"]); lk.new(ptc.outputs["Object"], pnz.inputs["Vector"])
lk.new(pnz.outputs["Fac"], pmr.inputs["Value"]); lk.new(pmr.outputs["Result"], pml.inputs[0]); lk.new(pvl.outputs[0], pm2.inputs[0]); lk.new(pfo.outputs["Result"], pm2.inputs[1]); lk.new(pm2.outputs[0], pml.inputs[1])
lk.new(pml.outputs[0], pv2.inputs["Density"]); lk.new(pv2.outputs[0], pn["Material Output"].inputs["Volume"])
sphere("ImpactPuff", 0.12, (0, 0, -50), M_PUFF, C_FX, segs=16)
_mp = sphere("MuzzlePuff", 0.03, (0, 0, -50), M_PUFF.copy(), C_FX, segs=16); _mp.data.materials[0].name = "M_MuzzlePuff"
_ff = _mp.data.materials[0].node_tree.nodes["PuffFalloff"]; _ff.inputs["From Min"].default_value = 0.03; _ff.inputs["From Max"].default_value = 0.008
_mp.data.materials[0].node_tree.nodes["Noise Texture"].inputs["Scale"].default_value = 70
# grinder sparks for the time-lapse (emissive streaks)
M_SPARK = mat("M_GrindSpark", (1, 0.6, 0.2), 0.5, emit=(1.0, 0.55, 0.15), estr=60.0)
for i in range(20):
    box("GSpark_%02d" % i, (0.0015, 0.03, 0.0015), (0, 0, -50), M_SPARK, C_FX)
# thought bubble (beat 11): thin iridescent shell
bub = sphere("ThoughtBubble", 1.0, (0, 0, -50), None, C_FX, segs=48)
bm_m = bpy.data.materials.new("M_Bubble"); bm_m.use_nodes = True
bn = bm_m.node_tree.nodes; bn.remove(bn["Principled BSDF"])
lw = bn.new('ShaderNodeLayerWeight'); lw.inputs["Blend"].default_value = 0.25
cr = bn.new('ShaderNodeValToRGB'); cr.color_ramp.elements[0].color = (0.6, 0.85, 1.0, 1); cr.color_ramp.elements[1].color = (1.0, 0.75, 0.95, 1)
em = bn.new('ShaderNodeEmission'); em.inputs["Strength"].default_value = 1.5
tr = bn.new('ShaderNodeBsdfTransparent')
mx = bn.new('ShaderNodeMixShader'); bv = bn.new('ShaderNodeValue'); bv.name = "BubbleOn"; bv.outputs[0].default_value = 0.0
mul = bn.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
L = bm_m.node_tree.links
L.new(lw.outputs["Facing"], cr.inputs[0]); L.new(cr.outputs[0], em.inputs["Color"])
L.new(lw.outputs["Facing"], mul.inputs[0]); L.new(bv.outputs[0], mul.inputs[1])
L.new(mul.outputs[0], mx.inputs[0]); L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2])
L.new(mx.outputs[0], bn["Material Output"].inputs["Surface"])
bub.data.materials.append(bm_m)
for i in range(3):   # small trailing bubbles
    sphere("ThoughtBubbleSmall_%d" % i, 1.0, (0, 0, -50), bm_m, C_FX, segs=24)
# sketch paper + pencil + brass blanks for the time-lapse
box("TL_Sketch", (0.297, 0.21, 0.001), (0.15, -0.05, -50), M_PAPER, C_WS)
cyl("TL_Pencil", 0.0035, 0.17, (0, 0, -50), mat("M_Pencil", (0.85, 0.65, 0.1), 0.5), C_WS, axis="Y", segs=6)
cyl("TL_File", 0.006, 0.2, (0, 0, -50), M_STEEL, C_WS, axis="Y", segs=6)
for i in range(5):
    cyl("TL_Blank_%d" % i, 0.012 + 0.004 * (i % 2), 0.05 + 0.02 * i, (0, 0, -50), M_BRASS, C_WS, axis="Y")

# ------------------------------------------------------------------ explainer backdrop card (camera-parented later), studio lights
card = plane_uv("ExplainerCard", 1.0, 1.0, (0, 0, -50), (0, 0, 0), None, C_FX, 1.0)
cm = bpy.data.materials.new("M_ExplainerGradient"); cm.use_nodes = True
cn = cm.node_tree.nodes; cn.remove(cn["Principled BSDF"])
tc = cn.new('ShaderNodeTexCoord'); sep = cn.new('ShaderNodeSeparateXYZ')
rmp = cn.new('ShaderNodeValToRGB')
rmp.color_ramp.elements[0].position = 0.15; rmp.color_ramp.elements[0].color = (0.05, 0.42, 0.62, 1)
rmp.color_ramp.elements[1].position = 0.95; rmp.color_ramp.elements[1].color = (0.82, 0.95, 1.0, 1)
em2 = cn.new('ShaderNodeEmission'); em2.inputs["Strength"].default_value = 1.0
tr2 = cn.new('ShaderNodeBsdfTransparent'); mx2 = cn.new('ShaderNodeMixShader'); cv = cn.new('ShaderNodeValue'); cv.name = "CardOn"
L = cm.node_tree.links
L.new(tc.outputs["UV"], sep.inputs[0]); L.new(sep.outputs["Y"], rmp.inputs[0]); L.new(rmp.outputs[0], em2.inputs["Color"])
L.new(cv.outputs[0], mx2.inputs[0]); L.new(tr2.outputs[0], mx2.inputs[1]); L.new(em2.outputs[0], mx2.inputs[2])
L.new(mx2.outputs[0], cn["Material Output"].inputs["Surface"])
uvl = card.data.uv_layers[0]
for li, lp in enumerate(card.data.loops):
    v = card.data.vertices[lp.vertex_index].co; uvl.data[li].uv = (v.x + 0.5, v.y + 0.5)
card.data.materials.append(cm)
card.visible_shadow = False; card.visible_diffuse = False; card.visible_glossy = True

def light(name, kind, loc, rot, energy, color, size=0.5, c=None, spot=None):
    L_ = bpy.data.lights.new(name, kind); L_.energy = energy; L_.color = color
    if kind == 'AREA': L_.size = size
    if kind in ('POINT', 'SPOT'): L_.shadow_soft_size = size
    if spot: L_.spot_size = R_(spot); L_.spot_blend = 0.6
    o = bpy.data.objects.new(name, L_); (c or C_WS).objects.link(o); o.location = loc; o.rotation_euler = [R_(a) for a in rot]
    return o
light("L_DeskLamp", 'SPOT', (0.3, -0.05, 1.45), (35, 0, -150), 60, (1.0, 0.78, 0.5), 0.05, spot=80)
light("L_Bulb", 'POINT', (0.0, -0.4, 2.55), (0, 0, 0), 220, (1.0, 0.72, 0.45), 0.12)
light("L_WindowMoon", 'AREA', (2.3, -0.4, 1.45), (0, -90, 0), 25, (0.55, 0.7, 1.0), 1.0)
light("L_RimBack", 'AREA', (-0.6, 1.4, 2.2), (-135, 0, 180), 40, (0.7, 0.8, 1.0), 0.8)
light("L_FaceFill", 'AREA', (-0.4, -1.0, 1.6), (70, 0, -20), 12, (1.0, 0.9, 0.8), 0.8)
light("L_StudioKey", 'AREA', (-0.4, -0.5, 1.6), (60, 0, -40), 0.0, (1.0, 1.0, 1.0), 0.6, c=C_FX)
light("L_StudioRim", 'AREA', (0.5, 0.6, 1.5), (-60, 0, 140), 0.0, (0.7, 0.9, 1.0), 0.5, c=C_FX)
light("L_OfficeSun", 'AREA', (OX - 2.3, -0.3, 1.6), (0, -90, 0), 900, (1.0, 0.97, 0.92), 1.6, c=C_OF)
light("L_OfficeCeil", 'AREA', (OX + 0.3, 0.3, 2.95), (0, 0, 0), 250, (0.95, 0.97, 1.0), 1.5, c=C_OF)
light("L_OfficeLampWarm", 'POINT', (OX - 0.8, 0.6, dt + 0.45), (0, 0, 0), 25, (1.0, 0.75, 0.45), 0.05, c=C_OF)
light("L_OfficeBounce", 'AREA', (OX + 1.5, -1.5, 1.6), (70, 0, 45), 60, (1.0, 0.95, 0.9), 1.0, c=C_OF)
light("L_FrontWash", 'AREA', (0.0, -2.6, 2.8), (40, 0, 0), 90, (1.0, 0.8, 0.6), 1.5)
light("L_ImpactWarm", 'AREA', (0.0, -1.0, 2.2), (30, 0, 0), 0.0, (1.0, 0.85, 0.7), 1.0)

# office root: local (OX, 0) -> world (0, -6.5), turned 180 deg so its -Y side (her chair) faces the workshop
of_root = bpy.data.objects.new("OfficeRoot", None); C_OF.objects.link(of_root)
of_root.location = (0, -6.5, 0); of_root.rotation_euler = (0, 0, R_(180))
for o in list(C_OF.objects):
    if o is not of_root and o.parent is None:
        o.parent = of_root; o.matrix_parent_inverse = Matrix.Translation((-OX, 0, 0))
# world: dim studio HDRI fill
wd = bpy.data.worlds.new("W_Film"); sc.world = wd; wd.use_nodes = True
wn = wd.node_tree.nodes; env = wn.new('ShaderNodeTexEnvironment')
env.image = bpy.data.images.load(glob.glob(os.path.join(PH, "hdri", "*.hdr"))[0])
wd.node_tree.links.new(env.outputs[0], wn["Background"].inputs[0]); wn["Background"].inputs[1].default_value = 0.08

# ------------------------------------------------------------------ render settings (farm baseline)
r = sc.render; r.engine = 'CYCLES'; r.resolution_x, r.resolution_y, r.resolution_percentage = 1080, 1920, 100
r.fps, r.fps_base = 60, 1.0; sc.frame_start, sc.frame_end = 1, 2100
cy = sc.cycles; cy.device = 'CPU'; cy.samples = 48; cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.05
cy.use_denoising = True; cy.denoiser = 'OPENIMAGEDENOISE'
cy.max_bounces = 8; cy.diffuse_bounces = 3; cy.glossy_bounces = 3; cy.transmission_bounces = 8; cy.transparent_max_bounces = 8
cy.caustics_reflective = cy.caustics_refractive = False
r.use_motion_blur = True; r.motion_blur_shutter = 0.5; r.use_persistent_data = True
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
r.image_settings.file_format = 'PNG'; r.image_settings.color_depth = '8'; r.image_settings.compression = 15
# clothes clipping: push garments 3 mm out along their normals after the armature deform
for nm in ("Inventor.female_casualsuit01", "Mentor.male_elegantsuit01"):
    o = bpy.data.objects[nm]
    d_ = o.modifiers.new("ClipPush", 'DISPLACE'); d_.strength = 0.003; d_.mid_level = 0.0; d_.direction = 'NORMAL'
# clean texture for her top (logo painted out)
for m in bpy.data.objects["Inventor.female_casualsuit01"].data.materials:
    for nd in m.node_tree.nodes:
        if nd.type == 'TEX_IMAGE' and nd.image and "diffuse" in nd.image.name.lower():
            nd.image = bpy.data.images.load(os.path.join(ROOT, "assets", "tex", "inventor_top_clean.jpg"))
art = bpy.data.images.load(os.path.join(ROOT, "assets", "tex", "frame_artwork.jpg"))
for m in bpy.data.materials:
    if m.name.startswith("hanging_picture_frame_01_artwork"):
        for nd in m.node_tree.nodes:
            if nd.type == 'TEX_IMAGE' and nd.image and "artwork_diff" in nd.image.name: nd.image = art
    if m.name.startswith("hanging_picture_frame_01_glass"):
        for nd in m.node_tree.nodes:   # the glass normal map carries the placeholder print; drop it
            if nd.type == 'TEX_IMAGE' and nd.image and "artwork_nor" in nd.image.name:
                for lk in list(nd.outputs[0].links): m.node_tree.links.remove(lk)
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name.startswith(("WS_Door", "WS_Pegboard", "WS_Poster", "WS_ShelfBoard", "OF_Monitor", "WS_WinFrame", "OF_Blind", "WS_DoorPanel")):
        if not any(m_.type == 'BEVEL' for m_ in o.modifiers):
            b_ = o.modifiers.new("bev", 'BEVEL'); b_.width = 0.004 if not o.name.startswith("OF_Blind") else 0.002; b_.segments = 2; b_.limit_method = 'ANGLE'
            for pl in o.data.polygons: pl.use_smooth = True
            o.data.shade_auto_smooth(angle=R_(35)) if hasattr(o.data, "shade_auto_smooth") else None
bpy.ops.file.make_paths_absolute()
# de-duplicate images loaded more than once (props appended twice)
seen = {}
for im in list(bpy.data.images):
    if im.source != 'FILE' or not im.filepath: continue
    k = bpy.path.abspath(im.filepath)
    if k in seen and seen[k] is not im:
        im.user_remap(seen[k]); bpy.data.images.remove(im)
    else:
        seen[k] = im
print("IMAGES", len(bpy.data.images))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SCENE SAVED", OUT, "bench_top", bench_top, "desk_top", sc["desk_top"])
