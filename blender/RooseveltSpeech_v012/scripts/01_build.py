"""RooseveltSpeech v012 stage A (from scratch): characters, three sets, props.
blender -b --factory-startup --python 01_build.py -- <out.blend>

STREET (origin): 1912 night street outside a hotel. Roosevelt ("Hero") stands ON the road at (0,0) facing -Y, his open
touring car parked behind him (y=+1.7), the hotel facade behind that. The gunman stands at (-0.75,-3.1) facing him.
Four onlookers stand around. Everyone wears a real MakeHuman three-piece suit (male_elegantsuit01) and a fedora.
MACRO (x=+40): a real-scale cut block of his chest wall under the breast pocket, layers stacked down from z=0:
folded speech (z -4..-16 mm), steel glasses case (-18..-46), shirt, skin, fat, pectoral muscle, ribs, lung.
The cut face is the plane y=0 (seen from -Y). The bullet travels straight down the cut plane (x=0,y=0).
One geometry-nodes group (GN_Cut) carves the wound channel and drags the layer around the bullet nose, driven by
the keyed empty `TipCtl` (nothing reads the scene clock).
HALL (y=+60): the auditorium stage (z=1.0), flags, bunting, a clock, a lectern with the DA KRAS FILMS logo; the
audience stands on the floor in front of the stage."""
import bpy, bmesh, sys, math, random, os
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "lib_build.py")).read())
OUT = sys.argv[sys.argv.index("--") + 1]
SK = "/opt/assets/sk/"
BRAND = os.path.join(HERE, "../../assets/brand/")
random.seed(24)
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
sc = bpy.context.scene
sc.render.fps = 60
sc.frame_start, sc.frame_end = 1, 1307
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
MX = Vector((40.0, 0.0, 0.0))
HX = Vector((0.0, 60.0, 0.0))
STAGE_Z = 1.0
def col(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in sc.collection.children: sc.collection.children.link(c)
    return c
C_CHAR, C_STREET, C_MACRO, C_HALL = col("CHARS"), col("STREET"), col("MACRO"), col("HALL")
def to_col(o, c):
    for cc in list(o.users_collection): cc.objects.unlink(o)
    c.objects.link(o)

# ================================================================== characters
SUIT = "male_elegantsuit01/male_elegantsuit01.mhclo"
def dress(rig, suit_tint, hat_tint, hair_tint, skin_tint):
    for c in rig.children:
        if c.type != 'MESH': continue
        n = c.name.lower()
        if "elegantsuit" in n:
            for m in c.data.materials: tint(m, suit_tint)
        elif "fedora" in n:
            for m in c.data.materials: tint(m, hat_tint)
        elif any(k in n for k in ("short", "eyebrow")):
            for m in c.data.materials: tint(m, hair_tint)
        elif n.endswith(".body"):
            for m in c.data.materials: tint(m, skin_tint)
        if any(k in n for k in ("elegantsuit", "shoes", "fedora")):      # solid garments, no paper edges
            so = c.modifiers.new("solid", 'SOLIDIFY'); so.thickness = 0.003; so.offset = 1.0; so.use_rim = True
            i = c.modifiers.find("solid")
            while i > c.modifiers.find("Armature") + 1:
                c.modifiers.move(i, i - 1); i -= 1
    for c in list(rig.children): to_col(c, C_CHAR)
    to_col(rig, C_CHAR)

# Roosevelt: stout, 54, moustache, pince-nez, charcoal suit, dark grey fedora (no portrait likeness)
HERO, HB = human("Hero", 1.0, 0.62, {"asian": 0.0, "caucasian": 1.0, "african": 0.0}, "short02/short02.mhclo",
                 "middleage_caucasian_male/middleage_caucasian_male.mhmat", "eyebrow001/eyebrow001.mhclo",
                 height=0.48, weight=0.85, muscle=0.55,
                 clothes=[SUIT, "shoes02/shoes02.mhclo", "fedora01/fedora01.mhclo"])
dress(HERO, (0.22, 0.22, 0.26), (0.30, 0.27, 0.24), (0.32, 0.22, 0.14), (1.0, 0.88, 0.80))
GUN, GB = human("Gunman", 1.0, 0.40, {"asian": 0.0, "caucasian": 1.0, "african": 0.0}, "short04/short04.mhclo",
                "young_caucasian_male/young_caucasian_male.mhmat", "eyebrow007/eyebrow007.mhclo",
                height=0.45, weight=0.45, muscle=0.5,
                clothes=[SUIT, "shoes01/shoes01.mhclo", "fedora_cocked/fedora_cocked.mhclo"])
dress(GUN, (0.30, 0.20, 0.13), (0.12, 0.11, 0.10), (0.15, 0.10, 0.07), (1.0, 0.9, 0.82))
EXTRAS = []
for i, (g_age, race, hair, skin, brow, w_, suit_t, hat, hat_t, hair_t) in enumerate((
        (0.55, {"caucasian": 0.9, "african": 0.1, "asian": 0.0}, "short01/short01.mhclo", "middleage_caucasian_male/middleage_caucasian_male.mhmat", "eyebrow003/eyebrow003.mhclo", 0.6, (0.10, 0.16, 0.42), "fedora01", (0.25, 0.18, 0.10), (0.25, 0.18, 0.10)),
        (0.35, {"caucasian": 0.7, "african": 0.0, "asian": 0.3}, "short03/short03.mhclo", "young_caucasian_male2/young_caucasian_male2.mhmat", "eyebrow005/eyebrow005.mhclo", 0.4, (0.42, 0.24, 0.10), "fedora_cocked", (0.10, 0.10, 0.12), (0.12, 0.08, 0.05)),
        (0.75, {"caucasian": 1.0, "african": 0.0, "asian": 0.0}, "short02/short02.mhclo", "old_caucasian_male/old_caucasian_male.mhmat", "eyebrow001/eyebrow001.mhclo", 0.7, (0.12, 0.30, 0.18), "fedora01", (0.35, 0.33, 0.30), (0.75, 0.74, 0.72)),
        (0.45, {"caucasian": 0.3, "african": 0.7, "asian": 0.0}, "short04/short04.mhclo", "middleage_african_male/middleage_african_male.mhmat", "eyebrow009/eyebrow009.mhclo", 0.5, (0.45, 0.08, 0.10), "fedora_cocked", (0.20, 0.14, 0.08), (0.08, 0.06, 0.05)))):
    r_, b_ = human("Extra%d" % i, 1.0, g_age, race, hair, skin, brow, height=0.4 + 0.08 * i, weight=w_, muscle=0.5,
                   clothes=[SUIT, "shoes0%d/shoes0%d.mhclo" % (i + 3, i + 3), "%s/%s.mhclo" % (hat, hat)])
    dress(r_, suit_t, hat_t, hair_t, (1, 1, 1))
    EXTRAS.append(r_)
eye_group_fix()
for r_ in [HERO, GUN] + EXTRAS:
    eye_fix(r_)
    for c in r_.children:
        if c.type == 'MESH' and "teeth" in c.name:
            for m in c.data.materials: tint(m, (1.6, 1.55, 1.5))

# Roosevelt's moustache: particle hair on his upper lip (grows from the deforming body, so it moves with the face)
def moustache(rig, body):
    oris = [b.head_local for b in rig.data.bones if b.name.startswith("oris")]
    mc = sum(oris, Vector()) / len(oris)
    vs = body.data.vertices
    lip = min((v for v in vs if abs(v.co.x) < 0.006 and abs(v.co.z - mc.z) < 0.012), key=lambda v: v.co.y)
    mz = lip.co.z
    g = body.vertex_groups.new(name="moustache")
    sel = []
    for v in vs:
        if abs(v.co.x) < 0.040 - 0.25 * max(0.0, (v.co.z - mz - 0.004)) * 0 and mz + 0.003 - 0.25 * max(0.0, abs(v.co.x) - 0.02) < v.co.z < mz + 0.020 and v.co.y < lip.co.y + 0.02 and v.normal.y < -0.25:
            w = 1.0 - max(0.0, (abs(v.co.x) - 0.022) / 0.012)
            sel.append((v.index, max(0.2, w)))
    for i, w in sel: g.add([i], w, 'REPLACE')
    keep = {i for i, w in sel if w > 0.15}
    m_ = body.copy(); m_.data = body.data.copy(); m_.name = "Hero.moustache"; m_.data.name = "Hero.moustache"
    bpy.context.collection.objects.link(m_); m_.parent = rig
    if m_.data.shape_keys: m_.shape_key_clear()
    bm = bmesh.new(); bm.from_mesh(m_.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.index not in keep], context='VERTS')
    bm.to_mesh(m_.data); bm.free()
    for md in list(m_.modifiers):
        if md.type != 'ARMATURE': m_.modifiers.remove(md)
    for p in m_.data.polygons: p.use_smooth = True
    d = m_.modifiers.new("off", 'DISPLACE'); d.strength = 0.0025; d.mid_level = 0.0
    so = m_.modifiers.new("solid", 'SOLIDIFY'); so.thickness = 0.005; so.offset = 1.0; so.use_rim = True
    sd = m_.modifiers.new("subd", 'SUBSURF'); sd.levels = 1; sd.render_levels = 2
    mm = mat("M_Moustache", (0.12, 0.07, 0.035), rough=0.55, sheen=0.4)
    nt = mm.node_tree; p = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); wv = nt.nodes.new("ShaderNodeTexWave"); wv.bands_direction = 'X'
    wv.inputs["Scale"].default_value = 900.0; wv.inputs["Distortion"].default_value = 4.0; wv.inputs["Detail"].default_value = 4.0
    nt.links.new(tc.outputs["Object"], wv.inputs["Vector"])
    cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (0.05, 0.03, 0.015, 1); cr.color_ramp.elements[1].color = (0.26, 0.16, 0.08, 1)
    nt.links.new(wv.outputs["Fac"], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], p.inputs["Base Color"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.8; bp.inputs["Distance"].default_value = 0.001
    nt.links.new(wv.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], p.inputs["Normal"])
    m_.data.materials.clear(); m_.data.materials.append(mm)
    to_col(m_, C_CHAR)
    print("MOUSTACHE verts", len(keep), "mouth z", round(mz, 3))
moustache(HERO, HB)

# pince-nez: two round steel-rimmed lenses with a bridge, Child Of the head bone (never pops, never changes shape)
def pince_nez(rig, body):
    el = rig.data.bones["eye.L"].head_local; er = rig.data.bones["eye.R"].head_local
    front = min(v.co.y for v in body.data.vertices if abs(v.co.x - el.x) < 0.006 and abs(v.co.z - el.z) < 0.006)
    yy = front - 0.012
    M_RIM = mat("M_PinceRim", (0.75, 0.70, 0.62), rough=0.25, metal=1.0)
    M_LENS = bpy.data.materials.new("M_PinceLens"); M_LENS.use_nodes = True; nt = M_LENS.node_tree
    for n in list(nt.nodes):
        if n.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n)
    tr = nt.nodes.new("ShaderNodeBsdfTransparent"); gl = nt.nodes.new("ShaderNodeBsdfGlossy"); gl.inputs["Roughness"].default_value = 0.03
    fr = nt.nodes.new("ShaderNodeFresnel"); fr.inputs["IOR"].default_value = 1.5
    fm_ = nt.nodes.new("ShaderNodeMath"); fm_.operation = 'MULTIPLY'; fm_.inputs[1].default_value = 0.0; nt.links.new(fr.outputs[0], fm_.inputs[0])
    tr.inputs["Color"].default_value = (0.92, 0.95, 0.97, 1)
    mx = nt.nodes.new("ShaderNodeMixShader"); nt.links.new(fm_.outputs[0], mx.inputs[0]); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(gl.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    parts = []
    for e in (el, er):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.0165, minor_radius=0.0011, major_segments=48, minor_segments=8,
                                         location=(e.x, yy, e.z + 0.002), rotation=(math.pi / 2, 0, 0))
        t = bpy.context.active_object; t.data.materials.append(M_RIM); parts.append(t)
        bpy.ops.mesh.primitive_circle_add(vertices=48, radius=0.0162, fill_type='NGON', location=(e.x, yy, e.z + 0.002), rotation=(math.pi / 2, 0, 0))
        l_ = bpy.context.active_object; l_.data.materials.append(M_LENS); parts.append(l_)
    # bridge: a small arc over the nose
    cu = bpy.data.curves.new("bridge", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.0009; sp = cu.splines.new('BEZIER'); sp.bezier_points.add(2)
    pts = [Vector((el.x - 0.016, yy, el.z + 0.004)), Vector((0, yy - 0.004, el.z + 0.010)), Vector((er.x + 0.016, yy, er.z + 0.004))]
    for bp_, p_ in zip(sp.bezier_points, pts): bp_.co = p_; bp_.handle_left_type = bp_.handle_right_type = 'AUTO'
    bo = bpy.data.objects.new("bridge", cu); bpy.context.collection.objects.link(bo); bo.data.materials.append(M_RIM)
    bpy.context.view_layer.objects.active = bo; bo.select_set(True); bpy.ops.object.convert(target='MESH'); parts.append(bo)
    bpy.ops.object.select_all(action='DESELECT')
    for p_ in parts: p_.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]; bpy.ops.object.join()
    g = bpy.context.active_object; g.name = "PinceNez"
    for p in g.data.polygons: p.use_smooth = True
    c = g.constraints.new('CHILD_OF'); c.target = rig; c.subtarget = "head"
    c.inverse_matrix = (rig.matrix_world @ rig.data.bones["head"].matrix_local).inverted()
    to_col(g, C_CHAR)
    return g
pince_nez(HERO, HB)

# ================================================================== materials
def tint_all(o, mult):
    for m in o.data.materials:
        if not m or not m.use_nodes: continue
        nt = m.node_tree
        for nd in list(nt.nodes):
            if nd.type == 'TEX_IMAGE':
                for lk in list(nd.outputs['Color'].links):
                    if lk.to_node.type == 'BSDF_PRINCIPLED' and lk.to_socket.name == 'Base Color':
                        mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
                        mx.inputs['Factor'].default_value = 1.0; mx.inputs['B'].default_value = (*mult, 1)
                        nt.links.new(nd.outputs['Color'], mx.inputs['A']); nt.links.new(mx.outputs['Result'], lk.to_socket)
def noise_mat(name, c1, c2, scale=40.0, rough=0.8, bump=0.15, metal=0.0, coat=0.0, det=6.0, vor=False):
    m = mat(name, c1, rough=rough, metal=metal, coat=coat)
    nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    if vor:
        nz = nt.nodes.new("ShaderNodeTexVoronoi"); nz.feature = 'DISTANCE_TO_EDGE'; nz.inputs["Scale"].default_value = scale
        out = nz.outputs["Distance"]
    else:
        nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = scale; nz.inputs["Detail"].default_value = det
        out = nz.outputs["Fac"]
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (*c1, 1); cr.color_ramp.elements[1].color = (*c2, 1)
    if vor: cr.color_ramp.elements[0].position = 0.0; cr.color_ramp.elements[1].position = 0.08
    nt.links.new(out, cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], p.inputs["Base Color"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump; bp.inputs["Distance"].default_value = 0.002
    nt.links.new(out, bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], p.inputs["Normal"])
    return m

def img_mat(name, path, rough=0.5, emit=0.0, alpha=True):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = bpy.data.images.load(path); tx.extension = 'CLIP'
    nt.links.new(tx.outputs["Color"], p.inputs["Base Color"]); p.inputs["Roughness"].default_value = rough
    if alpha: nt.links.new(tx.outputs["Alpha"], p.inputs["Alpha"])
    if emit:
        nt.links.new(tx.outputs["Color"], p.inputs["Emission Color"]); p.inputs["Emission Strength"].default_value = emit
    return m

def logo_board(name, w, h, loc, rot, board_mat, logo_path, depth=0.02, emit=0.0):
    b = box(name, (w, depth, h), loc, board_mat, bevel=0.004, rot=rot)
    im = bpy.data.images.load(logo_path); ar = im.size[1] / im.size[0]
    lw = min(w * 0.86, h * 0.86 / ar)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
    pl = bpy.context.active_object; pl.name = name + "_logo"
    pl.data.transform(Matrix.Diagonal((lw, lw * ar, 1, 1)))
    pl.data.transform(Matrix.Rotation(math.pi / 2, 4, 'X'))
    pl.location = Vector(loc) + Vector((0, -depth / 2 - 0.0015, 0))
    tx_m = bpy.data.materials.new(name + "_M"); tx_m.use_nodes = True; nt = tx_m.node_tree; p = nt.nodes["Principled BSDF"]
    tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = im; tx.extension = 'CLIP'
    nt.links.new(tx.outputs["Color"], p.inputs["Base Color"]); nt.links.new(tx.outputs["Alpha"], p.inputs["Alpha"])
    if emit:
        nt.links.new(tx.outputs["Color"], p.inputs["Emission Color"]); p.inputs["Emission Strength"].default_value = emit
    pl.data.materials.append(tx_m)
    return b, pl

M_COBBLE = noise_mat("M_Cobble", (0.03, 0.03, 0.05), (0.14, 0.12, 0.14), scale=9.0, rough=0.55, bump=0.6, vor=True)
M_PAVE = noise_mat("M_Pave", (0.12, 0.11, 0.13), (0.2, 0.18, 0.2), scale=25.0, rough=0.7, bump=0.2)
M_KERB = noise_mat("M_Kerb", (0.35, 0.33, 0.32), (0.5, 0.48, 0.46), scale=30.0, rough=0.6)
M_BRASS = mat("M_Brass", (0.95, 0.62, 0.20), rough=0.25, metal=1.0)
M_STEEL = noise_mat("M_Steel", (0.78, 0.80, 0.84), (0.95, 0.96, 0.98), scale=300.0, rough=0.16, metal=1.0, bump=0.08)
M_GUNMETAL = mat("M_Gunmetal", (0.80, 0.80, 0.82), rough=0.18, metal=1.0)   # nickel-plated, reads against the dark coat
M_GRIPWOOD = noise_mat("M_GripWood", (0.20, 0.07, 0.02), (0.35, 0.13, 0.04), scale=60.0, rough=0.45)
M_BULLET = mat("M_Bullet", (0.95, 0.50, 0.22), rough=0.22, metal=1.0)
M_GLOW = mat("M_LampGlow", (1, 0.7, 0.35), emit=((1.0, 0.62, 0.25), 18.0))

# ================================================================== STREET set
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -4, 0)); road = bpy.context.active_object; road.name = "Road"
road.scale = (40, 28, 1); bpy.ops.object.transform_apply(scale=True); road.data.materials.append(M_COBBLE); to_col(road, C_STREET)
pave = box("Pavement", (40, 4.0, 0.16), (0, 5.2, 0.08), M_PAVE, bevel=0.0); to_col(pave, C_STREET)
kerb = box("Kerb", (40, 0.25, 0.17), (0, 3.15, 0.085), M_KERB, bevel=0.01); to_col(kerb, C_STREET)
# hotel facade (CC-BY scan), scaled to ~16 m wide behind the pavement, with warm lit windows behind it
fac = imp(SK + "facade.dl", "HotelFacade", target_dim=16.0, axis=0)
fac.location = (0, 7.3, -0.4); to_col(fac, C_STREET); soften(fac, rough_min=0.5)
tint_all(fac, (0.22, 0.20, 0.30))      # daylight scan -> night
for dx in (-15.6, 15.6):
    f2 = fac.copy(); f2.location = (dx, 7.3, -0.4); C_STREET.objects.link(f2)
glow_wall = box("HotelInterior", (16, 0.1, 9), (0, 8.6, 4.0), mat("M_HotelInside", (0.02, 0.01, 0.01), emit=((1.0, 0.45, 0.15), 0.6)), bevel=0)
to_col(glow_wall, C_STREET)
# hotel sign (DA KRAS FILMS) mounted over the scan's own lettering; a wall lantern and a planter cover its small plaques
hs, hl_ = logo_board("HotelSign", 2.1, 0.55, (2.45, 3.90, 3.07), (0, 0, 0), mat("M_HotelSign", (0.03, 0.10, 0.06), rough=0.4, coat=0.5),
                     BRAND + "DaKrasFilms_logo_white.png", depth=0.04, emit=1.2)
to_col(hs, C_STREET); to_col(hl_, C_STREET)
for nm, sz, loc, m_ in (("Planter", (0.9, 0.45, 0.75), (3.67, 3.72, 0.5), mat("M_Planter", (0.25, 0.08, 0.03), rough=0.6)),):
    o_ = box(nm, sz, loc, m_, bevel=0.02); to_col(o_, C_STREET)
# the open touring car (CC-BY Ford Model T scan), parked at the kerb behind him
car = imp(SK + "car.dl", "Car", target_dim=3.4, axis=1, keep=lambda o: "roof" not in o.name.lower())
car.rotation_euler = (0, 0, math.pi / 2); car.location = (0.3, 2.15, 0.0); to_col(car, C_STREET); soften(car, rough_min=0.3)
for m in car.data.materials:
    tint(m, (0.5, 0.5, 0.6))
    if m and m.use_nodes:
        p = [n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED']
        if p and not p[0].inputs["Base Color"].is_linked:
            c_ = p[0].inputs["Base Color"].default_value
            if sum(c_[:3]) < 0.6: p[0].inputs["Base Color"].default_value = (0.02, 0.05, 0.16, 1)   # deep royal-blue paint
bpy.context.view_layer.update()
# DA KRAS FILMS logo: a painted panel on the car's rear door, facing the street (white logo on the deep blue paint)
bb = [car.matrix_world @ Vector(c) for c in car.bound_box]
car_front_y = min(v.y for v in bb)
board, logo1 = logo_board("CarDoorPanel", 0.62, 0.30, (0.95, car_front_y - 0.012, 0.78), (0, 0, 0),
                          mat("M_CarPanel", (0.02, 0.05, 0.16), rough=0.3, coat=0.5), BRAND + "DaKrasFilms_logo_white.png", depth=0.01, emit=0.6)
to_col(board, C_STREET); to_col(logo1, C_STREET)
for side in (-1, 1):
    hl = cyl("HeadLamp%d" % side, 0.09, 0.05, (car.location.x + side * 0.0 - 1.55, car.location.y + side * 0.55, 0.95), M_GLOW, rot=(0, math.pi / 2, 0))
    to_col(hl, C_STREET)
# gas street lamps (CC-BY scan) along the kerb, with warm point lights
lamp = imp(SK + "lamp.dl", "StreetLamp", target_dim=3.6, axis=2)
lamp.location = (-3.2, 3.6, 0.0); to_col(lamp, C_STREET); soften(lamp); tint_all(lamp, (0.45, 0.42, 0.5))
for i, x in enumerate((-3.2, 4.4, -10.5, 11.5)):
    if i: l2 = lamp.copy(); l2.location = (x, 3.6, 0); C_STREET.objects.link(l2)
    L = bpy.data.lights.new("GasLamp%d" % i, 'POINT'); L.energy = 650; L.color = (1.0, 0.52, 0.20); L.shadow_soft_size = 0.15
    lo = bpy.data.objects.new("GasLamp%d" % i, L); lo.location = (x, 3.6, 3.3); C_STREET.objects.link(lo)
for nm, loc, en, colr, size in (("StreetKey", (2.4, -2.6, 3.2), 420, (1.0, 0.70, 0.42), 1.0),
                                ("StreetFill", (-3.5, -2.0, 2.4), 120, (0.30, 0.42, 1.0), 2.0),
                                ("StreetRim", (0.0, 4.5, 3.5), 420, (1.0, 0.55, 0.25), 1.0)):
    L = bpy.data.lights.new(nm, 'AREA'); L.energy = en; L.color = colr; L.size = size
    lo = bpy.data.objects.new(nm, L); lo.location = loc; C_STREET.objects.link(lo)
    tt = lo.constraints.new('TRACK_TO'); tt.target = HERO; tt.track_axis = 'TRACK_NEGATIVE_Z'; tt.up_axis = 'UP_Y'

# the gunman's revolver: a .38 six-shooter (barrel, fluted cylinder, frame, hammer, trigger guard, wood grip)
def revolver():
    parts = []
    parts.append(cyl("rv_barrel", 0.0062, 0.11, (0, 0.075, 0.0), M_GUNMETAL, rot=(math.pi / 2, 0, 0), verts=24))
    parts.append(box("rv_rib", (0.004, 0.11, 0.004), (0, 0.075, 0.0068), M_GUNMETAL, bevel=0.001))
    cy = cyl("rv_cyl", 0.017, 0.036, (0, 0.003, -0.004), M_GUNMETAL, rot=(math.pi / 2, 0, 0), verts=36, bevel=0.002)
    for k in range(6):
        a = k * math.pi / 3
        f = cyl("rv_flute", 0.0042, 0.03, (0.017 * math.cos(a), 0.003, -0.004 + 0.017 * math.sin(a)), M_GUNMETAL, rot=(math.pi / 2, 0, 0), verts=12)
        bo = cy.modifiers.new("fl%d" % k, 'BOOLEAN'); bo.object = f; bo.operation = 'DIFFERENCE'
        bpy.context.view_layer.objects.active = cy; bpy.ops.object.modifier_apply(modifier=bo.name)
        bpy.data.objects.remove(f, do_unlink=True)
    parts.append(cy)
    parts.append(box("rv_frame", (0.012, 0.055, 0.026), (0, 0.0, -0.006), M_GUNMETAL, bevel=0.003))
    parts.append(box("rv_hammer", (0.006, 0.012, 0.014), (0, -0.030, 0.006), M_GUNMETAL, bevel=0.002, rot=(-0.5, 0, 0)))
    bpy.ops.mesh.primitive_torus_add(major_radius=0.012, minor_radius=0.0018, location=(0, -0.006, -0.026), rotation=(0, math.pi / 2, 0))
    tg = bpy.context.active_object; tg.data.materials.append(M_GUNMETAL); parts.append(tg)
    parts.append(box("rv_trigger", (0.004, 0.004, 0.012), (0, -0.008, -0.022), M_GUNMETAL, bevel=0.001, rot=(0.3, 0, 0)))
    grip = box("rv_grip", (0.016, 0.026, 0.065), (0, -0.034, -0.045), M_GRIPWOOD, bevel=0.006, rot=(0.38, 0, 0))
    parts.append(grip)
    bpy.ops.object.select_all(action='DESELECT')
    for p in parts:
        for m_ in list(p.modifiers):
            bpy.context.view_layer.objects.active = p; bpy.ops.object.modifier_apply(modifier=m_.name)
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]; bpy.ops.object.join()
    g = bpy.context.active_object; g.name = "Revolver"
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return g
REV = revolver(); to_col(REV, C_STREET)
# the bullet (one object for the whole film): a .38 round-nose, origin at its base centre, nose along local +Z
def bullet():
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=0.0045, location=(0, 0, 0.0105))
    s = bpy.context.active_object
    bm = bmesh.new(); bm.from_mesh(s.data)
    for v in bm.verts:
        if v.co.z < 0.0105: v.co.z = 0.0105 - 0.0105 * min(1.0, (0.0105 - v.co.z) / 0.0001) if False else v.co.z
    bm.to_mesh(s.data); bm.free()
    bpy.ops.mesh.primitive_cylinder_add(radius=0.0045, depth=0.0105, location=(0, 0, 0.00525), vertices=32)
    c = bpy.context.active_object
    bpy.ops.object.select_all(action='DESELECT'); s.select_set(True); c.select_set(True); bpy.context.view_layer.objects.active = c
    bpy.ops.object.join(); b = bpy.context.active_object; b.name = "Bullet"
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bm = bmesh.new(); bm.from_mesh(b.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0002)
    kill = [v for v in bm.verts if v.co.z < 0.0104 and (v.co.xy.length < 0.0044 and v.co.z > 0.0001)]
    bmesh.ops.delete(bm, geom=kill, context='VERTS')
    bm.to_mesh(b.data); bm.free()
    for p in b.data.polygons: p.use_smooth = True
    b.data.materials.append(M_BULLET)
    w = b.modifiers.new("ws", 'WELD'); w.merge_threshold = 0.0003
    return b
BUL = bullet(); to_col(BUL, C_CHAR)
tr_m = mat("M_Trail", (1, 0.8, 0.5), emit=((1.0, 0.75, 0.4), 2.5))
TRAIL = cyl("BulletTrail", 0.0007, 1.0, (0, 0, -0.5), tr_m, verts=12); TRAIL.data.transform(Matrix.Translation((0, 0, 0)))
to_col(TRAIL, C_CHAR)
# muzzle flash: a star of emissive cones at the barrel tip (keyed scale, parented to the revolver)
bpy.ops.mesh.primitive_cone_add(vertices=10, radius1=0.09, radius2=0.0, depth=0.36, location=(0, 0.31, 0), rotation=(-math.pi / 2, 0, 0))
fl = bpy.context.active_object; fl.name = "MuzzleFlash"
fl.data.materials.append(mat("M_Flash", (1, 0.8, 0.4), emit=((1.0, 0.72, 0.30), 60.0)))
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.06, location=(0, 0.15, 0)); fb = bpy.context.active_object
fb.data.materials.append(fl.data.materials[0]); fb.select_set(True); fl.select_set(True); bpy.context.view_layer.objects.active = fl; bpy.ops.object.join()
fl.parent = REV; to_col(fl, C_STREET)
L = bpy.data.lights.new("FlashLight", 'POINT'); L.energy = 0.0; L.color = (1.0, 0.7, 0.35)
flo = bpy.data.objects.new("FlashLight", L); flo.parent = REV; flo.location = (0, 0.20, 0.02); C_STREET.objects.link(flo)
# the hole in his coat: a small dark scorched disc shrink-wrapped onto the jacket (placed in stage B)
bpy.ops.mesh.primitive_circle_add(vertices=24, radius=0.010, fill_type='TRIFAN', location=(0, 0, 0))
hole = bpy.context.active_object; hole.name = "CoatHole"
hm = mat("M_CoatHole", (0.01, 0.006, 0.004), rough=0.9)
hole.data.materials.append(hm); to_col(hole, C_CHAR)

# ================================================================== MACRO set (real scale cut block)
def gn_cut_group(name, tip, material, radius=0.0046, drag=0.004, reach=0.010):
    g = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    g.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    g.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    N = g.nodes; Lk = g.links
    gi = N.new("NodeGroupInput"); go = N.new("NodeGroupOutput")
    class _V:  # constant inputs as nodes
        pass
    def val(v):
        n = N.new("ShaderNodeValue"); n.outputs[0].default_value = v; return n.outputs[0]
    P = {"Radius": val(radius), "Drag": val(drag), "Reach": val(reach)}
    oi = N.new("GeometryNodeObjectInfo"); oi.transform_space = 'RELATIVE'; oi.inputs["Object"].default_value = tip
    sep_t = N.new("ShaderNodeSeparateXYZ"); Lk.new(oi.outputs["Location"], sep_t.inputs[0])
    pos = N.new("GeometryNodeInputPosition"); sep = N.new("ShaderNodeSeparateXYZ"); Lk.new(pos.outputs[0], sep.inputs[0])
    # radial distance from the bullet axis (x=tip.x, y=tip.y)
    dx = N.new("ShaderNodeMath"); dx.operation = 'SUBTRACT'; Lk.new(sep.outputs[0], dx.inputs[0]); Lk.new(sep_t.outputs[0], dx.inputs[1])
    dy = N.new("ShaderNodeMath"); dy.operation = 'SUBTRACT'; Lk.new(sep.outputs[1], dy.inputs[0]); Lk.new(sep_t.outputs[1], dy.inputs[1])
    cx = N.new("ShaderNodeCombineXYZ"); Lk.new(dx.outputs[0], cx.inputs[0]); Lk.new(dy.outputs[0], cx.inputs[1])
    rr = N.new("ShaderNodeVectorMath"); rr.operation = 'LENGTH'; Lk.new(cx.outputs[0], rr.inputs[0])
    # height above the nose
    dz = N.new("ShaderNodeMath"); dz.operation = 'SUBTRACT'; Lk.new(sep.outputs[2], dz.inputs[0]); Lk.new(sep_t.outputs[2], dz.inputs[1])
    # drag: points within Reach of the axis and in [-Drag*1.2, +inf) of the nose are pulled down (falloff), squeeze ahead of the nose
    fr = N.new("ShaderNodeMapRange"); Lk.new(rr.outputs[1], fr.inputs["Value"]); fr.inputs["From Min"].default_value = 0.0
    Lk.new(P["Reach"], fr.inputs["From Max"]); fr.inputs["To Min"].default_value = 1.0; fr.inputs["To Max"].default_value = 0.0
    fz = N.new("ShaderNodeMapRange"); Lk.new(dz.outputs[0], fz.inputs["Value"]); fz.inputs["From Min"].default_value = 0.0; fz.inputs["From Max"].default_value = 0.004
    fz.inputs["To Min"].default_value = 0.0; fz.inputs["To Max"].default_value = 1.0
    sm1 = N.new("ShaderNodeMath"); sm1.operation = 'MULTIPLY'; Lk.new(fr.outputs[0], sm1.inputs[0]); Lk.new(fz.outputs[0], sm1.inputs[1])
    sm2 = N.new("ShaderNodeMath"); sm2.operation = 'MULTIPLY'; Lk.new(sm1.outputs[0], sm2.inputs[0]); Lk.new(P["Drag"], sm2.inputs[1])
    neg = N.new("ShaderNodeMath"); neg.operation = 'MULTIPLY'; neg.inputs[1].default_value = -1.0; Lk.new(sm2.outputs[0], neg.inputs[0])
    off = N.new("ShaderNodeCombineXYZ"); Lk.new(neg.outputs[0], off.inputs[2])
    sp = N.new("GeometryNodeSetPosition"); Lk.new(gi.outputs["Geometry"], sp.inputs["Geometry"]); Lk.new(off.outputs[0], sp.inputs["Offset"])
    # the channel: a cylinder from the nose up, subtracted (mesh boolean)
    cyl_ = N.new("GeometryNodeMeshCylinder"); cyl_.inputs["Vertices"].default_value = 32; cyl_.inputs["Depth"].default_value = 0.30
    Lk.new(P["Radius"], cyl_.inputs["Radius"])
    zc = N.new("ShaderNodeMath"); zc.operation = 'ADD'; zc.inputs[1].default_value = 0.15 + 0.004; Lk.new(sep_t.outputs[2], zc.inputs[0])
    tl = N.new("ShaderNodeCombineXYZ"); Lk.new(sep_t.outputs[0], tl.inputs[0]); Lk.new(sep_t.outputs[1], tl.inputs[1]); Lk.new(zc.outputs[0], tl.inputs[2])
    tf = N.new("GeometryNodeTransform"); Lk.new(cyl_.outputs["Mesh"], tf.inputs["Geometry"]); Lk.new(tl.outputs[0], tf.inputs["Translation"])
    smc = N.new("GeometryNodeSetMaterial"); Lk.new(tf.outputs[0], smc.inputs["Geometry"]); smc.inputs["Material"].default_value = material
    bo = N.new("GeometryNodeMeshBoolean"); bo.operation = 'DIFFERENCE'
    try: bo.solver = 'EXACT'
    except Exception: pass
    Lk.new(sp.outputs[0], bo.inputs[0]); Lk.new(smc.outputs[0], bo.inputs[1])
    ssm = N.new("GeometryNodeSetShadeSmooth"); ssm.inputs["Shade Smooth"].default_value = False
    Lk.new(bo.outputs[0], go.inputs[0])
    return g
TIP = bpy.data.objects.new("TipCtl", None); TIP.empty_display_size = 0.01; TIP.location = MX + Vector((0, 0, 0.02)); C_MACRO.objects.link(TIP)

def slab(name, z0, z1, material, wall_mat=None, size=(0.15, 0.07), res=0.0016, rough_amp=0.0, round_x=0.0, cut=True, drag=0.004, reach=0.010):
    """a solid layer block x in +-size0/2, y in 0..size1, z0..z1, gridded fine enough for the drag, carved by GN_Cut"""
    nx = max(2, int(size[0] / res)); ny = max(2, int(size[1] / res)); nz = max(1, int((z1 - z0) / res))
    bpy.ops.mesh.primitive_cube_add(size=1)
    o = bpy.context.active_object; o.name = name
    o.scale = (size[0], size[1], z1 - z0); bpy.ops.object.transform_apply(scale=True)
    o.location = MX + Vector((0, size[1] / 2, (z0 + z1) / 2))
    bpy.ops.object.transform_apply(location=True)
    o.location = MX; o.data.transform(Matrix.Translation(-MX))
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bm = bmesh.from_edit_mesh(o.data)
    # grid cuts: bisect along x, y, z
    for i in range(1, nx):
        x = -size[0] / 2 + size[0] * i / nx
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(x, 0, 0), plane_no=(1, 0, 0))
    for i in range(1, ny):
        y = size[1] * i / ny
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, y, 0), plane_no=(0, 1, 0))
    for i in range(1, nz):
        z = z0 + (z1 - z0) * i / nz
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, z), plane_no=(0, 0, 1))
    if rough_amp or round_x:
        for v in bm.verts:
            if rough_amp and v.co.z > z1 - 1e-5:
                v.co.z += rough_amp * math.sin(v.co.x * 90 + 1.3) * math.sin(v.co.y * 70)
            if round_x:      # rounded ends (glasses case): pull the corners in near x = +-size/2
                ex = abs(v.co.x) - (size[0] / 2 - round_x)
                if ex > 0:
                    zc_ = (z0 + z1) / 2; hz = (z1 - z0) / 2
                    k = math.sqrt(max(0.0, 1 - (ex / round_x) ** 2))
                    v.co.z = zc_ + (v.co.z - zc_) * max(0.25, k)
    bmesh.update_edit_mesh(o.data); bpy.ops.object.mode_set(mode='OBJECT')
    o.data.materials.append(material)
    if cut:
        md = o.modifiers.new("GN_Cut", 'NODES'); md.node_group = gn_cut_group("GN_Cut_" + name, TIP, wall_mat or material, drag=drag, reach=reach)
    to_col(o, C_MACRO)
    return o

M_COAT = noise_mat("M_CoatWool", (0.035, 0.035, 0.05), (0.08, 0.075, 0.10), scale=900.0, rough=0.9, bump=0.4)
M_PAPER_EDGE = bpy.data.materials.new("M_PaperEdge"); M_PAPER_EDGE.use_nodes = True
pe = M_PAPER_EDGE.node_tree; pp = pe.nodes["Principled BSDF"]; pp.inputs["Roughness"].default_value = 0.8
tc = pe.nodes.new("ShaderNodeTexCoord"); wv = pe.nodes.new("ShaderNodeTexWave"); wv.wave_type = 'BANDS'; wv.bands_direction = 'Z'
wv.inputs["Scale"].default_value = 420.0; wv.inputs["Distortion"].default_value = 0.6; wv.inputs["Detail"].default_value = 2.0
cr = pe.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (0.45, 0.36, 0.22, 1); cr.color_ramp.elements[0].position = 0.25
cr.color_ramp.elements[1].color = (0.98, 0.93, 0.80, 1); cr.color_ramp.elements[1].position = 0.45
pe.links.new(tc.outputs["Object"], wv.inputs["Vector"]); pe.links.new(wv.outputs["Fac"], cr.inputs["Fac"]); pe.links.new(cr.outputs["Color"], pp.inputs["Base Color"])
# the top sheet: cream paper with lines of dark-blue ink handwriting strokes (illegible, no readable text)
def ink_paper(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    p.inputs["Roughness"].default_value = 0.75
    tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sep.inputs[0])
    # line rows along y (every 7 mm), strokes along x from a stretched noise
    mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1.0, 1.0, 1.0)
    nt.links.new(tc.outputs["Object"], mp.inputs[0])
    row = nt.nodes.new("ShaderNodeMath"); row.operation = 'MULTIPLY'; row.inputs[1].default_value = 1 / 0.007; nt.links.new(sep.outputs[1], row.inputs[0])
    fr_ = nt.nodes.new("ShaderNodeMath"); fr_.operation = 'FRACT'; nt.links.new(row.outputs[0], fr_.inputs[0])
    band = nt.nodes.new("ShaderNodeMapRange"); nt.links.new(fr_.outputs[0], band.inputs["Value"]); band.interpolation_type = 'SMOOTHERSTEP'
    band.inputs["From Min"].default_value = 0.35; band.inputs["From Max"].default_value = 0.55; band.inputs["To Min"].default_value = 0; band.inputs["To Max"].default_value = 1
    band2 = nt.nodes.new("ShaderNodeMapRange"); nt.links.new(fr_.outputs[0], band2.inputs["Value"])
    band2.inputs["From Min"].default_value = 0.55; band2.inputs["From Max"].default_value = 0.75; band2.inputs["To Min"].default_value = 1; band2.inputs["To Max"].default_value = 0
    bmin = nt.nodes.new("ShaderNodeMath"); bmin.operation = 'MINIMUM'; nt.links.new(band.outputs[0], bmin.inputs[0]); nt.links.new(band2.outputs[0], bmin.inputs[1])
    nz = nt.nodes.new("ShaderNodeTexWave"); nz.wave_type = 'BANDS'; nz.bands_direction = 'X'; nz.inputs["Scale"].default_value = 700.0
    nz.inputs["Distortion"].default_value = 9.0; nz.inputs["Detail"].default_value = 4.0; nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    wn = nt.nodes.new("ShaderNodeTexNoise"); wn.inputs["Scale"].default_value = 260.0; nt.links.new(tc.outputs["Object"], wn.inputs["Vector"])
    gap = nt.nodes.new("ShaderNodeMapRange"); nt.links.new(wn.outputs["Fac"], gap.inputs["Value"]); gap.inputs["From Min"].default_value = 0.36; gap.inputs["From Max"].default_value = 0.42
    st = nt.nodes.new("ShaderNodeMapRange"); nt.links.new(nz.outputs["Fac"], st.inputs["Value"]); st.inputs["From Min"].default_value = 0.45; st.inputs["From Max"].default_value = 0.60
    m1 = nt.nodes.new("ShaderNodeMath"); m1.operation = 'MULTIPLY'; nt.links.new(bmin.outputs[0], m1.inputs[0]); nt.links.new(st.outputs[0], m1.inputs[1])
    m2 = nt.nodes.new("ShaderNodeMath"); m2.operation = 'MULTIPLY'; nt.links.new(m1.outputs[0], m2.inputs[0]); nt.links.new(gap.outputs[0], m2.inputs[1])
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = 'RGBA'; nt.links.new(m2.outputs[0], mix.inputs["Factor"])
    mix.inputs["A"].default_value = (0.97, 0.92, 0.78, 1); mix.inputs["B"].default_value = (0.03, 0.05, 0.22, 1)
    nt.links.new(mix.outputs["Result"], p.inputs["Base Color"])
    return m
M_PAPER_TOP = ink_paper("M_PaperInk")
M_CASE_IN = noise_mat("M_CaseVelvet", (0.02, 0.03, 0.12), (0.05, 0.07, 0.22), scale=400.0, rough=0.95, bump=0.2)
M_SHIRT = noise_mat("M_ShirtCotton", (0.92, 0.93, 0.96), (1.0, 1.0, 1.0), scale=700.0, rough=0.85, bump=0.2)
M_SKIN = noise_mat("M_SkinX", (0.95, 0.42, 0.28), (1.0, 0.55, 0.38), scale=200.0, rough=0.5)
M_FAT = noise_mat("M_FatX", (1.0, 0.62, 0.0), (1.0, 0.80, 0.05), scale=260.0, rough=0.35, bump=0.5, vor=True)
M_MUSCLE = bpy.data.materials.new("M_MuscleX"); M_MUSCLE.use_nodes = True
mt = M_MUSCLE.node_tree; pm = mt.nodes["Principled BSDF"]; pm.inputs["Roughness"].default_value = 0.35; pm.inputs["Coat Weight"].default_value = 0.3
tc = mt.nodes.new("ShaderNodeTexCoord"); wv = mt.nodes.new("ShaderNodeTexWave"); wv.wave_type = 'BANDS'; wv.bands_direction = 'X'
wv.inputs["Scale"].default_value = 260.0; wv.inputs["Distortion"].default_value = 3.0; wv.inputs["Detail"].default_value = 3.0
cr = mt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (0.32, 0.0, 0.01, 1); cr.color_ramp.elements[1].color = (0.80, 0.02, 0.03, 1)
mt.links.new(tc.outputs["Object"], wv.inputs["Vector"]); mt.links.new(wv.outputs["Fac"], cr.inputs["Fac"]); mt.links.new(cr.outputs["Color"], pm.inputs["Base Color"])
bp = mt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.4; bp.inputs["Distance"].default_value = 0.001
mt.links.new(wv.outputs["Fac"], bp.inputs["Height"]); mt.links.new(bp.outputs["Normal"], pm.inputs["Normal"])
M_BONE = noise_mat("M_BoneX", (0.92, 0.86, 0.70), (1.0, 0.96, 0.86), scale=120.0, rough=0.4, coat=0.3)
M_LUNG = noise_mat("M_LungX", (0.85, 0.12, 0.35), (1.0, 0.38, 0.55), scale=180.0, rough=0.45, bump=0.6, vor=True, coat=0.2)
M_PLEURA = mat("M_PleuraX", (0.75, 0.70, 0.95), rough=0.15, coat=0.6)

LAYERS = {}
LAYERS["coat"] = slab("X_Coat", -0.004, 0.0, M_COAT, cut=False); LAYERS["coat"].location.y += 0.035   # cut back: the top page shows in front
LAYERS["paper"] = slab("X_Paper", -0.016, -0.0042, M_PAPER_EDGE, drag=0.006, reach=0.009)
LAYERS["papertop"] = slab("X_PaperTop", -0.0042, -0.0037, M_PAPER_TOP, drag=0.006, reach=0.009)
LAYERS["casetop"] = slab("X_CaseTop", -0.021, -0.018, M_STEEL, drag=0.005, reach=0.010)
LAYERS["caselin"] = slab("X_CaseLining", -0.0212, -0.0205, M_CASE_IN, drag=0.0045, reach=0.014)
LAYERS["casebot"] = slab("X_CaseBottom", -0.046, -0.043, M_STEEL, drag=0.005, reach=0.010)
LAYERS["caselin2"] = slab("X_CaseLining2", -0.043, -0.0423, M_CASE_IN, drag=0.004, reach=0.014)
for nm, xs in (("X_CaseEndL", -0.0735), ("X_CaseEndR", 0.0735)):
    e = box(nm, (0.005, 0.07, 0.028), MX + Vector((xs, 0.035, -0.032)), M_STEEL, bevel=0.002); to_col(e, C_MACRO)
e = box("X_CaseBack", (0.151, 0.003, 0.028), MX + Vector((0, 0.0715, -0.032)), M_STEEL, bevel=0.001); to_col(e, C_MACRO)
for k, x in enumerate((-0.034, 0.034)):
    bpy.ops.mesh.primitive_torus_add(major_radius=0.016, minor_radius=0.0012, location=MX + Vector((x, 0.03, -0.0405)))
    t = bpy.context.active_object; t.name = "X_Specs%d" % k; t.data.materials.append(M_BRASS); to_col(t, C_MACRO)
    bpy.ops.mesh.primitive_circle_add(vertices=32, radius=0.0155, fill_type='NGON', location=MX + Vector((x, 0.03, -0.0405)))
    l_ = bpy.context.active_object; l_.name = "X_SpecLens%d" % k; l_.data.materials.append(mat("M_SpecLens", (0.6, 0.8, 0.9), rough=0.05, coat=1.0)); to_col(l_, C_MACRO)
bpy.ops.mesh.primitive_torus_add(major_radius=0.006, minor_radius=0.001, location=MX + Vector((0, 0.03, -0.0402)))
br_ = bpy.context.active_object; br_.name = "X_SpecBridge"; br_.data.materials.append(M_BRASS); to_col(br_, C_MACRO)
LAYERS["shirt"] = slab("X_Shirt", -0.0478, -0.0465, M_SHIRT)
LAYERS["skin"] = slab("X_Skin", -0.0505, -0.0478, M_SKIN)
LAYERS["fat"] = slab("X_Fat", -0.058, -0.0505, M_FAT)
LAYERS["muscle"] = slab("X_Muscle", -0.080, -0.058, M_MUSCLE, drag=0.003)
# ribs run back into the cut (round sections on the cut face), intercostal muscle between, pleura, lung below
for i, x in enumerate((-0.045, 0.040)):
    r_ = cyl("X_Rib%d" % i, 0.0075, 0.07, MX + Vector((x, 0.035, -0.0885)), M_BONE, rot=(math.pi / 2, 0, 0), verts=40)
    r_.scale = (1.35, 1.0, 1.0); to_col(r_, C_MACRO)
ic = slab("X_Intercostal", -0.097, -0.080, mat("M_InterX", (0.62, 0.06, 0.08), rough=0.4), cut=False, res=0.004)
for i in range(2):
    bo = ic.modifiers.new("rib%d" % i, 'BOOLEAN'); bo.object = bpy.data.objects["X_Rib%d" % i]; bo.operation = 'DIFFERENCE'
slab("X_Pleura", -0.0985, -0.097, M_PLEURA, cut=False, res=0.004)
slab("X_Lung", -0.15, -0.0985, M_LUNG, cut=False, res=0.004)
# backdrop: a saturated cyan -> deep blue gradient dome around the block (the clean "inside the body" look)
bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=1.2, location=MX)
dome = bpy.context.active_object; dome.name = "X_Backdrop"
dm = bpy.data.materials.new("M_XBackdrop"); dm.use_nodes = True; nt = dm.node_tree
for n in list(nt.nodes):
    if n.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n)
tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sep.inputs[0])
mr = nt.nodes.new("ShaderNodeMapRange"); nt.links.new(sep.outputs[2], mr.inputs["Value"]); mr.inputs["From Min"].default_value = -0.9; mr.inputs["From Max"].default_value = 0.9
cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (0.00, 0.10, 0.55, 1); cr.color_ramp.elements[1].color = (0.25, 0.85, 1.0, 1)
nt.links.new(mr.outputs[0], cr.inputs["Fac"])
em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Strength"].default_value = 1.0; nt.links.new(cr.outputs[0], em.inputs[0])
nt.links.new(em.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
dome.data.materials.append(dm); dome.visible_shadow = False
for p in dome.data.polygons: p.use_smooth = True
to_col(dome, C_MACRO)
for nm, loc, en, size in (("XKey", (-0.25, -0.30, 0.30), 18.0, 0.25), ("XFill", (0.30, -0.25, 0.05), 7.0, 0.3), ("XTop", (0.0, 0.10, 0.35), 8.0, 0.3)):
    L = bpy.data.lights.new(nm, 'AREA'); L.energy = en; L.size = size; L.color = (1.0, 0.97, 0.92)
    lo = bpy.data.objects.new(nm, L); lo.location = MX + Vector(loc); C_MACRO.objects.link(lo)
    tt = lo.constraints.new('TRACK_TO'); tt.target = TIP; tt.track_axis = 'TRACK_NEGATIVE_Z'; tt.up_axis = 'UP_Y'

# ================================================================== HALL set (y=+60): stage, flags, bunting, clock, lectern
M_WOODSTAGE = wood = None
def woodm(name, c1, c2, scale=3.0, rough=0.4):
    m = mat(name, c1, rough=rough, coat=0.25)
    nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1, 10, 1)
    wv = nt.nodes.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = scale; wv.inputs["Distortion"].default_value = 6.0
    cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (*c1, 1); cr.color_ramp.elements[1].color = (*c2, 1)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"]); nt.links.new(mp.outputs["Vector"], wv.inputs["Vector"])
    nt.links.new(wv.outputs["Fac"], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], p.inputs["Base Color"])
    return m
M_STAGE = woodm("M_StageWood", (0.25, 0.08, 0.02), (0.42, 0.16, 0.05))
M_HALLFLOOR = woodm("M_HallFloor", (0.18, 0.06, 0.02), (0.30, 0.11, 0.04))
M_VELVET = noise_mat("M_Velvet", (0.35, 0.0, 0.03), (0.62, 0.02, 0.06), scale=30.0, rough=0.6, bump=0.3)
M_WALLH = noise_mat("M_HallWall", (0.04, 0.10, 0.22), (0.07, 0.16, 0.32), scale=6.0, rough=0.8)
M_GOLD = mat("M_Gold", (1.0, 0.70, 0.22), rough=0.3, metal=1.0)
st = box("Stage", (12, 5, STAGE_Z), HX + Vector((0, 1.5, STAGE_Z / 2)), M_STAGE, bevel=0.02); to_col(st, C_HALL)
apron = box("StageApron", (12.1, 0.06, STAGE_Z), HX + Vector((0, -1.0, STAGE_Z / 2)), M_VELVET, bevel=0.005); to_col(apron, C_HALL)
fl_ = box("HallFloor", (30, 30, 0.1), HX + Vector((0, -10, -0.05)), M_HALLFLOOR, bevel=0); to_col(fl_, C_HALL)
bw = box("HallBack", (16, 0.2, 9), HX + Vector((0, 4.2, 4.5)), M_WALLH, bevel=0); to_col(bw, C_HALL)
for side in (-1, 1):
    sw = box("HallSide%d" % side, (0.2, 30, 9), HX + Vector((side * 8.5, -8, 4.5)), M_WALLH, bevel=0); to_col(sw, C_HALL)
    # tall red velvet curtains with folds at the stage sides
    bpy.ops.mesh.primitive_plane_add(size=1, location=HX + Vector((side * 4.6, 3.6, 3.5)))
    cu = bpy.context.active_object; cu.name = "Curtain%d" % side; cu.scale = (2.4, 1, 5.0); bpy.ops.object.transform_apply(scale=True)
    cu.data.transform(Matrix.Rotation(math.pi / 2, 4, 'X'))
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.subdivide(number_cuts=60); bpy.ops.object.mode_set(mode='OBJECT')
    for v in cu.data.vertices: v.co.y += 0.12 * math.sin(v.co.x * 9.0)
    cu.data.materials.append(M_VELVET); so = cu.modifiers.new("s", 'SOLIDIFY'); so.thickness = 0.02
    for p in cu.data.polygons: p.use_smooth = True
    to_col(cu, C_HALL)
ceil = box("HallCeiling", (17, 31, 0.2), HX + Vector((0, -8, 9.0)), mat("M_HallCeil", (0.55, 0.42, 0.25), rough=0.8), bevel=0); to_col(ceil, C_HALL)
backw = box("HallBackWall", (17, 0.2, 9), HX + Vector((0, -23, 4.5)), M_WALLH, bevel=0); to_col(backw, C_HALL)
# US flags (13 stripes + blue canton with white stars as dots) on poles, and red-white-blue bunting swags
def flag_mat():
    m = bpy.data.materials.new("M_Flag"); m.use_nodes = True; nt = m.node_tree; p = nt.nodes["Principled BSDF"]; p.inputs["Roughness"].default_value = 0.7
    p.inputs["Sheen Weight"].default_value = 0.3
    uv = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(uv.outputs["UV"], sep.inputs[0])
    st_ = nt.nodes.new("ShaderNodeMath"); st_.operation = 'MULTIPLY'; st_.inputs[1].default_value = 6.5; nt.links.new(sep.outputs[1], st_.inputs[0])
    fr_ = nt.nodes.new("ShaderNodeMath"); fr_.operation = 'FRACT'; nt.links.new(st_.outputs[0], fr_.inputs[0])
    gt = nt.nodes.new("ShaderNodeMath"); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = 0.5; nt.links.new(fr_.outputs[0], gt.inputs[0])
    stripes = nt.nodes.new("ShaderNodeMix"); stripes.data_type = 'RGBA'; nt.links.new(gt.outputs[0], stripes.inputs["Factor"])
    stripes.inputs["A"].default_value = (0.70, 0.01, 0.03, 1); stripes.inputs["B"].default_value = (0.95, 0.93, 0.90, 1)
    # canton: u<0.4, v>0.46
    c1 = nt.nodes.new("ShaderNodeMath"); c1.operation = 'LESS_THAN'; c1.inputs[1].default_value = 0.4; nt.links.new(sep.outputs[0], c1.inputs[0])
    c2 = nt.nodes.new("ShaderNodeMath"); c2.operation = 'GREATER_THAN'; c2.inputs[1].default_value = 0.46; nt.links.new(sep.outputs[1], c2.inputs[0])
    cc = nt.nodes.new("ShaderNodeMath"); cc.operation = 'MULTIPLY'; nt.links.new(c1.outputs[0], cc.inputs[0]); nt.links.new(c2.outputs[0], cc.inputs[1])
    vor = nt.nodes.new("ShaderNodeTexVoronoi"); vor.inputs["Scale"].default_value = 14.0; vor.inputs["Randomness"].default_value = 0.0
    nt.links.new(uv.outputs["UV"], vor.inputs["Vector"])
    dot = nt.nodes.new("ShaderNodeMath"); dot.operation = 'LESS_THAN'; dot.inputs[1].default_value = 0.17; nt.links.new(vor.outputs["Distance"], dot.inputs[0])
    can = nt.nodes.new("ShaderNodeMix"); can.data_type = 'RGBA'; nt.links.new(dot.outputs[0], can.inputs["Factor"])
    can.inputs["A"].default_value = (0.01, 0.03, 0.30, 1); can.inputs["B"].default_value = (0.95, 0.93, 0.90, 1)
    fin = nt.nodes.new("ShaderNodeMix"); fin.data_type = 'RGBA'; nt.links.new(cc.outputs[0], fin.inputs["Factor"])
    nt.links.new(stripes.outputs["Result"], fin.inputs["A"]); nt.links.new(can.outputs["Result"], fin.inputs["B"])
    nt.links.new(fin.outputs["Result"], p.inputs["Base Color"])
    return m
M_FLAG = flag_mat()
FLAGS = []
for i, x in enumerate((-3.2, 3.2)):
    pole = cyl("FlagPole%d" % i, 0.025, 3.6, HX + Vector((x, 3.0, STAGE_Z + 1.8)), M_GOLD); to_col(pole, C_HALL)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
    f_ = bpy.context.active_object; f_.name = "Flag%d" % i
    f_.scale = (1.5, 1, 0.95); bpy.ops.object.transform_apply(scale=True)
    f_.data.transform(Matrix.Rotation(math.pi / 2, 4, 'X')); f_.data.transform(Matrix.Translation((0.75 if x < 0 else -0.75, 0, 0)))
    if x > 0:
        for lp in f_.data.uv_layers[0].data: lp.uv.x = 1 - lp.uv.x
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.subdivide(number_cuts=24); bpy.ops.object.mode_set(mode='OBJECT')
    f_.location = HX + Vector((x + (0.03 if x < 0 else -0.03), 3.0, STAGE_Z + 3.0)); f_.data.materials.append(M_FLAG)
    wv_ = f_.modifiers.new("wave", 'WAVE'); wv_.use_normal = False; wv_.use_y = False; wv_.height = 0.04; wv_.width = 0.6; wv_.speed = 0.02
    wv_.start_position_x = 0 if x < 0 else 0; wv_.narrowness = 1.0
    so = f_.modifiers.new("s", 'SOLIDIFY'); so.thickness = 0.004
    for p in f_.data.polygons: p.use_smooth = True
    to_col(f_, C_HALL); FLAGS.append(f_)
def swag(name, x0, x1, y, z, colors):
    """a draped half-fan bunting swag: three coloured bands, sagging between x0 and x1"""
    bm = bmesh.new(); nseg = 24; rows = len(colors) * 3
    verts = []
    for j in range(rows + 1):
        rowv = []
        for i in range(nseg + 1):
            u = i / nseg; x = x0 + (x1 - x0) * u
            sag = 0.55 * math.sin(math.pi * u) * (j / rows)
            rowv.append(bm.verts.new((x, y - 0.06 * math.sin(math.pi * u) * (j / rows) + 0.02 * math.sin(i * 1.7), z - 0.06 * j / rows * 0 - sag - 0.12 * j / rows)))
        verts.append(rowv)
    faces = []
    for j in range(rows):
        for i in range(nseg):
            faces.append((bm.faces.new((verts[j][i], verts[j][i + 1], verts[j + 1][i + 1], verts[j + 1][i])), j // 3))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); C_HALL.objects.link(o)
    for c_ in colors: o.data.materials.append(c_)
    for p, (fobj, k) in zip(o.data.polygons, faces): p.material_index = k; p.use_smooth = True
    so = o.modifiers.new("s", 'SOLIDIFY'); so.thickness = 0.004
    return o
M_RED = fabric("M_BuntRed", (0.75, 0.01, 0.03)); M_WHITE = fabric("M_BuntWhite", (0.95, 0.93, 0.90)); M_BLUE = fabric("M_BuntBlue", (0.01, 0.05, 0.45))
for i in range(-3, 3):
    swag("Swag%d" % i, HX.x + i * 2.0 + 0.02, HX.x + (i + 1) * 2.0 - 0.02, HX.y + 4.08, 7.2, [M_RED, M_WHITE, M_BLUE])
    swag("SwagApron%d" % i, HX.x + i * 2.0 + 0.02, HX.x + (i + 1) * 2.0 - 0.02, HX.y - 1.04, STAGE_Z - 0.02, [M_RED, M_WHITE, M_BLUE])
# the clock (CC-BY scan) on the back wall above the stage, with new hands that spin in stage B
clock = imp(SK + "clock.dl", "Clock", target_dim=1.1)
bpy.context.view_layer.update()
clock.location = HX + Vector((0, 4.05, 5.6)); to_col(clock, C_HALL); soften(clock)
bpy.context.view_layer.update()
cb = [clock.matrix_world @ Vector(c) for c in clock.bound_box]
cfront = min(v.y for v in cb); cz = (min(v.z for v in cb) + max(v.z for v in cb)) / 2
for nm, ln, w in (("ClockHour", 0.28, 0.035), ("ClockMinute", 0.42, 0.022)):
    h_ = box(nm, (w, 0.008, ln), (0, 0, ln / 2 - 0.04), mat("M_ClockHand", (0.02, 0.02, 0.02), rough=0.3, metal=0.6), bevel=0.003)
    bpy.ops.object.transform_apply(location=True)
    h_.location = (clock.location.x, cfront - 0.012 - (0.006 if "Min" in nm else 0), cz); to_col(h_, C_HALL)
# lectern: slim mahogany stand to his right with the DA KRAS FILMS logo panel on the front (white on deep red)
M_MAHOG = woodm("M_Mahogany", (0.18, 0.03, 0.01), (0.32, 0.07, 0.02))
LEC_X, LEC_Y = 0.78, 0.0
lec_post = box("LecternPost", (0.12, 0.12, 0.95), HX + Vector((LEC_X, LEC_Y, STAGE_Z + 0.475)), M_MAHOG, bevel=0.01); to_col(lec_post, C_HALL)
lec_base = box("LecternBase", (0.42, 0.36, 0.05), HX + Vector((LEC_X, LEC_Y, STAGE_Z + 0.025)), M_MAHOG, bevel=0.01); to_col(lec_base, C_HALL)
lec_top = box("LecternTop", (0.50, 0.38, 0.05), HX + Vector((LEC_X, LEC_Y, STAGE_Z + 1.06)), M_MAHOG, bevel=0.01, rot=(-0.30, 0, 0)); to_col(lec_top, C_HALL)
lp, ll = logo_board("LecternLogo", 0.46, 0.30, HX + Vector((LEC_X, LEC_Y - 0.075, STAGE_Z + 0.70)), (0, 0, 0),
                    mat("M_LecPanel", (0.45, 0.01, 0.03), rough=0.4, coat=0.4), BRAND + "DaKrasFilms_logo_white.png", depth=0.03, emit=0.4)
to_col(lp, C_HALL); to_col(ll, C_HALL)
# the bullet-holed speech he holds up in the hall (one object, a folded bundle of pages, inked, with the hole)
def manuscript():
    o = box("Speech", (0.11, 0.012, 0.17), (0, 0, 0), M_PAPER_EDGE, bevel=0.002)
    o.modifiers["bev"].segments = 2
    bpy.context.view_layer.objects.active = o; bpy.ops.object.modifier_apply(modifier="bev")
    o.data.materials.append(M_PAPER_TOP)
    for p in o.data.polygons:
        if abs(p.normal.y) > 0.9: p.material_index = 1
    h = cyl("speech_hole", 0.0055, 0.05, (0.018, 0, 0.03), M_PAPER_EDGE, rot=(math.pi / 2, 0, 0), verts=20)
    for v in h.data.vertices: v.co.x += 0.0012 * math.sin(v.co.z * 400 + v.index)
    bo = o.modifiers.new("hole", 'BOOLEAN'); bo.object = h; bo.operation = 'DIFFERENCE'
    bpy.context.view_layer.objects.active = o; bpy.ops.object.modifier_apply(modifier="hole")
    bpy.data.objects.remove(h, do_unlink=True)
    # scorched ring around the hole on both faces
    for sy in (-1, 1):
        bpy.ops.mesh.primitive_circle_add(vertices=32, radius=0.0115, fill_type='NGON', location=(0.018, sy * 0.0062, 0.03), rotation=(math.pi / 2, 0, 0))
        ring = bpy.context.active_object
        bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.inset(thickness=0.0055); bpy.ops.mesh.delete(type='FACE') if False else None
        bpy.ops.object.mode_set(mode='OBJECT')
        bm = bmesh.new(); bm.from_mesh(ring.data)
        cen = [f for f in bm.faces if all((v.co.xz - Vector((0, 0))).length < 0.0063 for v in f.verts)]
        bmesh.ops.delete(bm, geom=cen, context='FACES'); bm.to_mesh(ring.data); bm.free()
        ring.data.materials.append(mat("M_Scorch", (0.10, 0.05, 0.02), rough=0.9))
        ring.parent = o; ring.location = (0.018, sy * 0.0063, 0.03)
        ring.name = "SpeechScorch%d" % (sy + 1); to_col(ring, C_CHAR)
    for p in o.data.polygons: p.use_smooth = False
    to_col(o, C_CHAR)
    return o
SPEECH = manuscript()
# hall lights: warm key on the stage, cool fill, chandelier glow above the audience, footlights
for nm, loc, en, colr, size, tgt in (("HallKey", (2.6, -3.0, 3.6), 650, (1.0, 0.80, 0.55), 1.6, HERO), ("HallFill", (-3.5, -2.0, 2.6), 220, (0.55, 0.65, 1.0), 2.5, HERO),
                                     ("HallRim", (-1.0, 3.0, 4.2), 500, (1.0, 0.65, 0.35), 1.2, HERO), ("HallAud", (0.0, -6.0, 7.5), 2200, (1.0, 0.75, 0.45), 6.0, None),
                                     ("HallBackdrop", (0.0, 1.0, 7.5), 1800, (1.0, 0.85, 0.6), 5.0, None)):
    L = bpy.data.lights.new(nm, 'AREA'); L.energy = en; L.color = colr; L.size = size
    lo = bpy.data.objects.new(nm, L); lo.location = HX + Vector(loc); C_HALL.objects.link(lo)
    if tgt is not None:
        tt = lo.constraints.new('TRACK_TO'); tt.target = tgt; tt.track_axis = 'TRACK_NEGATIVE_Z'; tt.up_axis = 'UP_Y'
    elif nm == "HallBackdrop":
        lo.rotation_euler = (math.radians(-35), 0, 0)
# chandeliers: brass rings with glowing bulbs above the audience
for k, (x, y) in enumerate(((-3.5, -6), (3.5, -6), (0, -12))):
    bpy.ops.mesh.primitive_torus_add(major_radius=0.6, minor_radius=0.03, location=HX + Vector((x, y, 7.2)))
    ring = bpy.context.active_object; ring.name = "Chand%d" % k; ring.data.materials.append(M_BRASS); to_col(ring, C_HALL)
    for j in range(10):
        a = j * math.tau / 10
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.045, location=HX + Vector((x + 0.6 * math.cos(a), y + 0.6 * math.sin(a), 7.26)))
        b_ = bpy.context.active_object; b_.name = "ChandBulb%d_%d" % (k, j); b_.data.materials.append(M_GLOW); to_col(b_, C_HALL)
    ch = cyl("ChandRod%d" % k, 0.012, 1.7, HX + Vector((x, y, 8.1)), M_BRASS); to_col(ch, C_HALL)

# ================================================================== world, colour, render
w = bpy.data.worlds.new("Night"); sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes["Background"]; bg.inputs["Color"].default_value = (0.004, 0.008, 0.045, 1); bg.inputs["Strength"].default_value = 1.0
sc.render.engine = 'CYCLES'; sc.cycles.samples = 64; sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.05
sc.cycles.use_denoising = True; sc.cycles.denoiser = 'OPENIMAGEDENOISE'
sc.cycles.max_bounces = 6; sc.cycles.diffuse_bounces = 3; sc.cycles.glossy_bounces = 3; sc.cycles.transmission_bounces = 6
sc.cycles.transparent_max_bounces = 16; sc.cycles.caustics_reflective = False; sc.cycles.caustics_refractive = False
sc.render.use_persistent_data = True; sc.render.use_simplify = True; sc.render.simplify_subdivision_render = 2
sc.cycles.texture_limit_render = '2048'
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Punchy'; sc.view_settings.exposure = 0.3
cam_d = bpy.data.cameras.new("CAM_Film"); cam_d.lens = 40; cam_d.clip_start = 0.003; cam_d.clip_end = 120
cam = bpy.data.objects.new("CAM_Film", cam_d); sc.collection.objects.link(cam); sc.camera = cam
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("BUILD_DONE", OUT)
