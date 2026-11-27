"""BelugaRescue v009 stage A (from scratch): one diver, one beluga, two spectators, one arctic whale tank.
blender -b --python 01_build.py -- <beluga.gltf> <out.blend>

World: the water surface is z=0, the tank floor z=-5. Tank interior x -7..7, y -6..6, ice-rock walls.
The back wall (y=+6) has a viewing window (x -3..3, z -4.6..-1.2) onto a lit gallery where two spectators stand.
Above the water (z>0): a deck at z=0.5 round the tank and an arctic hall with an aurora mural (the ending).
Underwater depth haze is a compositor mist mix (no volumes); its depth is keyed by stage B (off above water)."""
import bpy, bmesh, sys, math, random, os
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "lib_build.py")).read())
a = sys.argv[sys.argv.index("--") + 1:]
GLTF, OUT = a[0], a[1]
PKG = os.path.dirname(HERE)
random.seed(22)
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
sc = bpy.context.scene
sc.render.fps = 60
sc.frame_start, sc.frame_end = 1, 1736
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
def col(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in sc.collection.children: sc.collection.children.link(c)
    return c
C_CHAR, C_SET, C_WHALE = col("CHARACTERS"), col("SET"), col("WHALE")
def to_col(o, c):
    for cc in list(o.users_collection): cc.objects.unlink(o)
    c.objects.link(o)
D = "/root/.config/blender/5.2/extensions/.user/user_default/mpfb/data/clothes/"

def loose_parts(me):
    bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
    seen = set(); comps = []
    for v in bm.verts:
        if v.index in seen: continue
        st = [v]; comp = []; seen.add(v.index)
        while st:
            x = st.pop(); comp.append(x.index)
            for e in x.link_edges:
                y = e.other_vert(x)
                if y.index not in seen: seen.add(y.index); st.append(y)
        comps.append(comp)
    bm.free(); return comps

def drop_parts(o, kill_fn):
    """delete the loose parts of a garment for which kill_fn(minz, maxz) is True (rest pose)"""
    me = o.data; comps = loose_parts(me)
    kill = []
    for c in comps:
        zs = [me.vertices[i].co.z for i in c]
        k = kill_fn(min(zs), max(zs))
        print("PART", o.name, len(c), round(min(zs), 3), round(max(zs), 3), "KILL" if k else "keep")
        if k: kill += c
    bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.verts[i] for i in kill], context='VERTS'); bm.to_mesh(me); bm.free()

def solid_clothes(rig):
    for c in rig.children:
        if c.type == 'MESH' and any(k in c.name for k in ("suit", "clothes", "shoes")):
            so = c.modifiers.new("solid", 'SOLIDIFY'); so.thickness = 0.003; so.offset = 1.0; so.use_rim = True
            i = c.modifiers.find("solid")
            while i > c.modifiers.find("Armature") + 1:
                c.modifiers.move(i, i - 1); i -= 1

def iris(rig, major, minor):
    for m in [m for c in rig.children if c.type == 'MESH' and "high-poly" in c.name for m in c.data.materials]:
        for n in m.node_tree.nodes:
            if n.type == 'GROUP' and "IrisMajorColor" in n.inputs:
                n.inputs["IrisMajorColor"].default_value = (*major, 1); n.inputs["IrisMinorColor"].default_value = (*minor, 1)

# ================================================================== the diver (ONE model for the whole film)
W, WB = human("Diver", 0.0, 0.5, {"asian": 0.75, "caucasian": 0.20, "african": 0.05}, "braid01/braid01.mhclo",
              "young_asian_female/young_asian_female.mhmat", "eyebrow006/eyebrow006.mhclo",
              height=0.45, weight=0.45, muscle=0.55, prop=0.6,
              clothes=["female_casualsuit01/female_casualsuit01.mhclo", "female_sportsuit01/female_sportsuit01.mhclo"])
eye_fix(W); eye_group_fix()
EG = bpy.data.node_groups.get("EnhancedEye")
for n in (EG.nodes if EG else []):
    if n.type == 'MATH' and abs(n.inputs[1].default_value - 0.92) < 1e-4: n.inputs[1].default_value = 0.96
iris(W, (0.12, 0.06, 0.02), (0.05, 0.025, 0.01))
for c in W.children:
    if c.type == 'MESH' and any(k in c.name.lower() for k in ("braid", "eyebrow")):
        for m in c.data.materials: tint(m, (0.16, 0.09, 0.06))
for m in WB.data.materials: tint(m, (1.0, 0.80, 0.66))
for c in W.children:
    if c.type == 'MESH' and "teeth" in c.name:
        for m in c.data.materials: tint(m, (1.5, 1.45, 1.4))
TEE = [c for c in W.children if c.type == 'MESH' and "casualsuit" in c.name][0]
LEG = [c for c in W.children if c.type == 'MESH' and "sportsuit" in c.name][0]
knee_z = W.data.bones["lowerleg01.L"].head_local.z
hip_z = W.data.bones["upperleg01.L"].head_local.z
drop_parts(TEE, lambda mn, mx: mn < knee_z)              # the jeans go: the swim tee stays
drop_parts(LEG, lambda mn, mx: mn > hip_z - 0.05)        # the crop top goes: the leggings stay
TEE.name = "Diver.tee"; LEG.name = "Diver.leggings"
tee = bpy.data.images.load(os.path.join(PKG, "assets/tex/diver_tee_diffuse.png")); tee.name = "diver_tee_diffuse"
for m in TEE.data.materials:
    for nd in m.node_tree.nodes:
        if nd.type == 'TEX_IMAGE' and nd.image and "diffuse" in nd.image.name.lower(): nd.image = tee
        if nd.type == 'NORMAL_MAP': nd.inputs["Strength"].default_value = 0.4
for m in LEG.data.materials:
    tint(m, (2.6, 0.45, 3.2))                            # deep violet leggings
    for nd in m.node_tree.nodes:
        if nd.type == 'NORMAL_MAP': nd.inputs["Strength"].default_value = 0.5
solid_clothes(W)
# trim the braid's side fringe off her eyes (face readable in every close-up)
eyeL, eyeR = W.data.bones["eye.L"].head_local, W.data.bones["eye.R"].head_local
for c in W.children:
    if c.type == 'MESH' and "braid" in c.name:
        bm = bmesh.new(); bm.from_mesh(c.data)
        kill = [v for v in bm.verts if v.co.z < eyeL.z + 0.012 and v.co.y < eyeL.y + 0.03 and abs(v.co.x) < 0.07]
        print("FRINGE trimmed", len(kill)); bmesh.ops.delete(bm, geom=kill, context='VERTS'); bm.to_mesh(c.data); bm.free()
for c in W.children: to_col(c, C_CHAR)
to_col(W, C_CHAR)

# ================================================================== two spectators in the viewing gallery (real clothes, hair, faces)
SPECS = []
for nm, g, age, race, hair, skin, brow, clo, h, pos in (
        ("SpecMan", 1.0, 0.55, {"asian": 0.1, "caucasian": 0.7, "african": 0.2}, "short02/short02.mhclo",
         "young_caucasian_male/young_caucasian_male.mhmat", "eyebrow001/eyebrow001.mhclo",
         ["male_casualsuit05/male_casualsuit05.mhclo", "shoes02/shoes02.mhclo"], 0.6, (-0.85, 7.05)),
        ("SpecWoman", 0.0, 0.45, {"asian": 0.05, "caucasian": 0.25, "african": 0.70}, "bob02/bob02.mhclo",
         "young_african_female/young_african_female.mhmat", "eyebrow010/eyebrow010.mhclo",
         ["female_elegantsuit01/female_elegantsuit01.mhclo", "shoes01/shoes01.mhclo"], 0.45, (0.80, 7.15))):
    R_, B_ = human(nm, g, age, race, hair, skin, brow, height=h, clothes=clo)
    eye_fix(R_); iris(R_, (0.10, 0.05, 0.02), (0.04, 0.02, 0.01))
    for c in R_.children:
        if c.type == 'MESH' and any(k in c.name.lower() for k in ("short", "bob", "eyebrow")):
            for m in c.data.materials: tint(m, (0.25, 0.15, 0.09) if nm == "SpecMan" else (0.10, 0.06, 0.05))
        if c.type == 'MESH' and "casualsuit05" in c.name:
            for m in c.data.materials: tint(m, (2.2, 0.35, 0.25))          # the man's puffer jacket: deep red
        if c.type == 'MESH' and "teeth" in c.name:
            for m in c.data.materials: tint(m, (1.5, 1.45, 1.4))
    solid_clothes(R_)
    for c in R_.children: to_col(c, C_CHAR)
    to_col(R_, C_CHAR)
    SPECS.append((R_, pos))
GAL_Z = -4.75
for R_, pos in SPECS:
    R_["home"] = (pos[0], pos[1], GAL_Z)

# ================================================================== the beluga (ONE CC-BY sculpt, rigged here)
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=GLTF)
new = [o for o in bpy.data.objects if o not in before]
meshes = [o for o in new if o.type == 'MESH']
for o in meshes:
    mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
for o in new:
    if o not in meshes: bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.object.select_all(action='DESELECT')
for o in meshes: o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
bpy.ops.object.join()
WH = bpy.context.active_object; WH.name = "Beluga.body"; WH.data.name = "Beluga.body"
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
dm = WH.modifiers.new("dec", 'DECIMATE'); dm.ratio = 0.25
bpy.ops.object.modifier_apply(modifier="dec")
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.remove_doubles(threshold=0.0004)
bpy.ops.object.mode_set(mode='OBJECT')
WS = 4.0 / 1.81                                   # 4.0 m beluga (model is 1.81 units long, head at -Y, back up +Z)
WH.data.transform(Matrix.Scale(WS, 4))
for p in WH.data.polygons: p.use_smooth = True
print("BELUGA faces", len(WH.data.polygons))
def S(y, z, x=0.0): return Vector((x * WS, y * WS, z * WS))
# ---- the mouth: split the lip crease so the jaw can open (corner y=-0.675, tip y=-0.885, model units)
def zline(y): return 0.028 + (0.041 - 0.028) * (-0.675 - y) / (0.885 - 0.675)
bm = bmesh.new(); bm.from_mesh(WH.data); bm.faces.ensure_lookup_table()
def is_jaw(co):
    y, z = co.y / WS, co.z / WS
    return y < -0.66 and z < zline(y)
jawf = set(f.index for f in bm.faces if is_jaw(f.calc_center_median()))
cut = []
for e in bm.edges:
    if len(e.link_faces) != 2: continue
    a_, b_ = e.link_faces
    if (a_.index in jawf) == (b_.index in jawf): continue
    mid = (e.verts[0].co + e.verts[1].co) / 2
    y, z = mid.y / WS, mid.z / WS
    if y < -0.69 and abs(z - zline(y)) < 0.03: cut.append(e)
bmesh.ops.split_edges(bm, edges=cut)
print("MOUTH split edges", len(cut))
bm.to_mesh(WH.data); bm.free()
# ---- armature: a spine chain along the centreline (head .. fluke), two flippers, the jaw
cz = {-0.905: 0.075, -0.55: 0.06, -0.25: 0.0, 0.05: -0.008, 0.30: -0.035, 0.50: -0.03, 0.65: 0.04, 0.92: 0.15}
cy = sorted(cz)
def cen(y):
    for i in range(len(cy) - 1):
        if cy[i] <= y <= cy[i + 1]:
            u = (y - cy[i]) / (cy[i + 1] - cy[i]); return cz[cy[i]] * (1 - u) + cz[cy[i + 1]] * u
    return cz[cy[0]] if y < cy[0] else cz[cy[-1]]
arm = bpy.data.armatures.new("Beluga"); BR = bpy.data.objects.new("Beluga", arm); C_WHALE.objects.link(BR)
bpy.context.view_layer.objects.active = BR; bpy.ops.object.mode_set(mode='EDIT')
eb = arm.edit_bones
CH = [("chest", -0.25, 0.05, None), ("neck", -0.25, -0.55, "chest"), ("head", -0.55, -0.905, "neck"),
      ("belly", 0.05, 0.30, "chest"), ("tail1", 0.30, 0.50, "belly"), ("tail2", 0.50, 0.65, "tail1"), ("fluke", 0.65, 0.92, "tail2")]
for nm, y0, y1, par in CH:
    b = eb.new(nm); b.head = S(y0, cen(y0)); b.tail = S(y1, cen(y1)); b.roll = 0.0
    if par: b.parent = eb[par]; b.use_connect = False
for s, sx in (("L", 1), ("R", -1)):
    b = eb.new("flipper." + s); b.head = S(-0.30, -0.16, sx * 0.20); b.tail = S(-0.17, -0.22, sx * 0.36); b.parent = eb["chest"]
j = eb.new("jaw"); j.head = S(-0.675, 0.028); j.tail = S(-0.885, 0.035); j.parent = eb["head"]
bpy.ops.object.mode_set(mode='OBJECT')
WH.parent = BR
for nm in [c[0] for c in CH] + ["flipper.L", "flipper.R", "jaw"]: WH.vertex_groups.new(name=nm)
cent = {"head": -0.80, "neck": -0.45, "chest": -0.10, "belly": 0.17, "tail1": 0.40, "tail2": 0.575, "fluke": 0.75}
order = sorted(cent, key=lambda k: cent[k])
VG = {g.name: g for g in WH.vertex_groups}
jaw_verts = set()
me = WH.data
fl_set = set()
for v in me.vertices:
    y, z, x = v.co.y / WS, v.co.z / WS, v.co.x / WS
    w = {}
    if y <= cent[order[0]]: w[order[0]] = 1.0
    elif y >= cent[order[-1]]: w[order[-1]] = 1.0
    else:
        for i in range(len(order) - 1):
            a0, a1 = cent[order[i]], cent[order[i + 1]]
            if a0 <= y <= a1:
                u = (y - a0) / (a1 - a0); u = u * u * (3 - 2 * u); w[order[i]] = 1 - u; w[order[i + 1]] = u; break
    if -0.46 < y < -0.04 and abs(x) > 0.205 and z < 0.0:
        k = min(1.0, (abs(x) - 0.205) / 0.04)
        w = {kk: vv * (1 - k) for kk, vv in w.items()}; w["flipper." + ("L" if x > 0 else "R")] = k
    if y < -0.60 and z < zline(y) + 0.0005:
        k = 1.0 if y < -0.72 else (-0.60 - y) / 0.12
        k = k * k * (3 - 2 * k)
        w = {kk: vv * (1 - k) for kk, vv in w.items()}; w["jaw"] = w.get("jaw", 0) + k
    for kk, vv in w.items():
        if vv > 1e-4: VG[kk].add([v.index], vv, 'REPLACE')
am = WH.modifiers.new("Armature", 'ARMATURE'); am.object = BR
sd = WH.modifiers.new("subd", 'SUBSURF'); sd.levels = 0; sd.render_levels = 1
to_col(WH, C_WHALE)
# ---- material: the sculpt's albedo (white), wet coat, a soft SSS; inside faces (the mouth) a deep pink
wm = WH.data.materials[0]; wm.name = "M_Beluga"; nt = wm.node_tree
p = [n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'][0]
p.inputs["Coat Weight"].default_value = 0.35; p.inputs["Coat Roughness"].default_value = 0.15
p.inputs["Subsurface Weight"].default_value = 0.08; p.inputs["Subsurface Radius"].default_value = (0.8, 0.5, 0.4)
p.inputs["Subsurface Scale"].default_value = 0.02
if not p.inputs["Roughness"].is_linked: p.inputs["Roughness"].default_value = 0.35
bc = p.inputs["Base Color"]
if bc.is_linked:
    src = bc.links[0].from_socket
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs["Factor"].default_value = 1.0
    mx.inputs["B"].default_value = (0.92, 0.97, 1.0, 1); nt.links.new(src, mx.inputs["A"]); nt.links.new(mx.outputs["Result"], bc)
else:
    bc.default_value = (0.88, 0.92, 0.95, 1)
outn = [n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'][0]
srf = outn.inputs["Surface"].links[0].from_socket
geo = nt.nodes.new("ShaderNodeNewGeometry")
pk = nt.nodes.new("ShaderNodeBsdfPrincipled"); pk.inputs["Base Color"].default_value = (0.55, 0.08, 0.12, 1); pk.inputs["Roughness"].default_value = 0.3
mxs = nt.nodes.new("ShaderNodeMixShader"); nt.links.new(geo.outputs["Backfacing"], mxs.inputs["Fac"])
nt.links.new(srf, mxs.inputs[1]); nt.links.new(pk.outputs["BSDF"], mxs.inputs[2]); nt.links.new(mxs.outputs["Shader"], outn.inputs["Surface"])
for n in nt.nodes:
    if n.type == 'NORMAL_MAP': n.inputs["Strength"].default_value = 0.6
WH.data.materials.clear(); WH.data.materials.append(wm)

# ================================================================== materials for the set
def noise_mat(name, c1, c2, scale=3.0, rough=0.5, bump=0.2, bdist=0.02, coat=0.0, sss=0.0, detail=6.0):
    m = mat(name, c1, rough=rough, coat=coat, sss=sss)
    nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = scale
    nz.inputs["Detail"].default_value = detail
    cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (*c1, 1); cr.color_ramp.elements[1].color = (*c2, 1)
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"]); nt.links.new(nz.outputs["Fac"], cr.inputs["Fac"])
    nt.links.new(cr.outputs["Color"], p.inputs["Base Color"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump; bp.inputs["Distance"].default_value = bdist
    nt.links.new(nz.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], p.inputs["Normal"])
    return m
M_ICE = noise_mat("M_IceRock", (0.04, 0.28, 0.62), (0.45, 0.75, 0.95), scale=1.6, rough=0.32, bump=0.35, bdist=0.05, coat=0.4, sss=0.1)
M_ICE_DRY = noise_mat("M_IceRockDry", (0.35, 0.65, 0.92), (0.90, 0.96, 1.0), scale=2.2, rough=0.45, bump=0.6, bdist=0.05, coat=0.2)
M_STEEL = mat("M_FrameSteel", (0.02, 0.10, 0.32), rough=0.35, metal=0.6, coat=0.4)
M_GAL_WALL = noise_mat("M_GalleryWall", (0.05, 0.05, 0.30), (0.10, 0.06, 0.40), scale=6.0, rough=0.8, bump=0.05)
M_GAL_FLOOR = mat("M_GalleryFloor", (0.12, 0.04, 0.05), rough=0.5, coat=0.3)
M_PLATE = mat("M_LogoPlate", (0.95, 0.95, 0.93), rough=0.3, coat=0.5)
M_DECK = noise_mat("M_Deck", (0.80, 0.86, 0.92), (0.92, 0.95, 0.98), scale=8.0, rough=0.35, bump=0.05, coat=0.3)
M_COPING = mat("M_Coping", (0.96, 0.97, 0.98), rough=0.3, coat=0.4)
# tank floor tiles: deep blue + white mosaic, with animated caustics (the W of a 4D voronoi is keyed by stage B)
M_FLOOR = mat("M_TankFloor", (0.1, 0.3, 0.6), rough=0.35, coat=0.3)
nt = M_FLOOR.node_tree; p = nt.nodes["Principled BSDF"]
tc = nt.nodes.new("ShaderNodeTexCoord"); br = nt.nodes.new("ShaderNodeTexBrick"); br.offset = 0.0
br.inputs["Scale"].default_value = 2.0; br.inputs["Color1"].default_value = (0.01, 0.10, 0.45, 1); br.inputs["Color2"].default_value = (0.02, 0.20, 0.62, 1)
br.inputs["Mortar"].default_value = (0.55, 0.75, 0.90, 1); br.inputs["Mortar Size"].default_value = 0.02
br.inputs["Brick Width"].default_value = 0.5; br.inputs["Row Height"].default_value = 0.5
nt.links.new(tc.outputs["Object"], br.inputs["Vector"])
vo = nt.nodes.new("ShaderNodeTexVoronoi"); vo.voronoi_dimensions = '4D'
vo.feature = 'DISTANCE_TO_EDGE'; vo.inputs["Scale"].default_value = 1.6; vo.name = "Caustics"
nt.links.new(tc.outputs["Object"], vo.inputs["Vector"])
cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].position = 0.0; cr.color_ramp.elements[0].color = (1.6, 1.9, 2.0, 1)
cr.color_ramp.elements[1].position = 0.10; cr.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1)
nt.links.new(vo.outputs["Distance"], cr.inputs["Fac"])
mm = nt.nodes.new("ShaderNodeMix"); mm.data_type = 'RGBA'; mm.blend_type = 'MULTIPLY'; mm.inputs["Factor"].default_value = 1.0
nt.links.new(br.outputs["Color"], mm.inputs["A"]); nt.links.new(cr.outputs["Color"], mm.inputs["B"]); nt.links.new(mm.outputs["Result"], p.inputs["Base Color"])
bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.3; bp.inputs["Distance"].default_value = 0.005
nt.links.new(br.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], p.inputs["Normal"])

# ================================================================== the tank
def rock_panel(name, w, h, loc, rot, material, cuts=(70, 30), strength=0.35, seed=0, scale=0.9):
    """an ice-rock wall: a subdivided plane displaced along its normal (real geometry, never a flat slab)"""
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=cuts[0], y_subdivisions=cuts[1], size=1, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name; o.scale = (w, h, 1); bpy.ops.object.transform_apply(scale=True)
    tx = bpy.data.textures.new(name + "_tx", 'CLOUDS'); tx.noise_scale = scale; tx.noise_depth = 3; tx.noise_basis = 'VORONOI_F2'
    dmo = o.modifiers.new("rock", 'DISPLACE'); dmo.texture = tx; dmo.strength = strength; dmo.mid_level = 0.0; dmo.texture_coords = 'GLOBAL'
    tx2 = bpy.data.textures.new(name + "_tx2", 'CLOUDS'); tx2.noise_scale = 0.25; tx2.noise_depth = 2
    d2 = o.modifiers.new("detail", 'DISPLACE'); d2.texture = tx2; d2.strength = 0.06; d2.mid_level = 0.5; d2.texture_coords = 'GLOBAL'
    s_ = o.modifiers.new("subd", 'SUBSURF'); s_.levels = 0; s_.render_levels = 1
    o.data.materials.append(material)
    for pp in o.data.polygons: pp.use_smooth = True
    to_col(o, C_SET); return o
R90 = math.radians(90)
# walls (normals facing into the tank; displacement pushes inward = toward the water)
rock_panel("TK_WallL", 12.4, 5.8, (-7.0, 0.0, -2.3), (R90, 0, R90), M_ICE, seed=1)
rock_panel("TK_WallR", 12.4, 5.8, (7.0, 0.0, -2.3), (R90, 0, -R90), M_ICE, seed=2)
rock_panel("TK_WallF", 14.4, 5.8, (0.0, -6.0, -2.3), (R90, 0, 0), M_ICE, seed=3)
# back wall around the window (x -3..3, z -4.6..-1.2): four rock panels + a deep-blue steel frame over the seams
WX, WZ0, WZ1 = 3.0, -4.6, -1.2
for nm, w, h, cx, cz_ in (("TK_WallB_L", 4.2, 5.8, -5.0, -2.3), ("TK_WallB_R", 4.2, 5.8, 5.0, -2.3),
                          ("TK_WallB_T", 6.4, 1.85, 0.0, -0.33), ("TK_WallB_B", 6.4, 0.55, 0.0, -4.93)):
    rock_panel(nm, w, h, (cx, 6.0, cz_), (R90, 0, math.radians(180)), M_ICE, cuts=(max(8, int(w * 6)), max(4, int(h * 6))))
for nm, sz, lc in (("TK_FrameL", (0.30, 0.40, 3.8), (-WX - 0.1, 5.95, (WZ0 + WZ1) / 2)), ("TK_FrameR", (0.30, 0.40, 3.8), (WX + 0.1, 5.95, (WZ0 + WZ1) / 2)),
                   ("TK_FrameT", (6.5, 0.40, 0.30), (0, 5.95, WZ1 + 0.1)), ("TK_FrameB", (6.5, 0.40, 0.30), (0, 5.95, WZ0 - 0.1))):
    to_col(box(nm, sz, lc, M_STEEL, bevel=0.04), C_SET)
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 6.0, (WZ0 + WZ1) / 2), rotation=(R90, 0, 0))
GL = bpy.context.active_object; GL.name = "TK_WindowGlass"; GL.scale = (2 * WX, WZ1 - WZ0, 1); bpy.ops.object.transform_apply(scale=True)
gm = bpy.data.materials.new("M_Acrylic"); gm.use_nodes = True; nt = gm.node_tree
for n in list(nt.nodes):
    if n.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n)
tr = nt.nodes.new("ShaderNodeBsdfTransparent"); tr.inputs["Color"].default_value = (0.80, 0.95, 1.0, 1)
gl = nt.nodes.new("ShaderNodeBsdfGlossy"); gl.inputs["Roughness"].default_value = 0.03
fr = nt.nodes.new("ShaderNodeFresnel"); fr.inputs["IOR"].default_value = 1.33
mx = nt.nodes.new("ShaderNodeMixShader"); nt.links.new(fr.outputs[0], mx.inputs["Fac"])
nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(gl.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
GL.data.materials.append(gm); to_col(GL, C_SET)
# the floor (tiles + caustics) and two ice-rock outcrops on it at the side walls
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, -5.0)); FLR = bpy.context.active_object; FLR.name = "TK_Floor"
FLR.scale = (14.2, 12.2, 1); bpy.ops.object.transform_apply(scale=True); FLR.data.materials.append(M_FLOOR); to_col(FLR, C_SET)
for nm, loc, sz in (("TK_RockA", (-6.0, 2.5, -5.0), (2.2, 3.0, 1.6)), ("TK_RockB", (6.1, -1.5, -5.0), (2.0, 2.6, 2.2)),
                    ("TK_RockC", (-5.6, -4.6, -5.0), (2.6, 2.0, 1.2))):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=5, radius=1.0, location=loc); o = bpy.context.active_object; o.name = nm
    o.scale = sz; bpy.ops.object.transform_apply(scale=True)
    tx = bpy.data.textures.new(nm + "_tx", 'CLOUDS'); tx.noise_scale = 0.7; tx.noise_basis = 'VORONOI_F2'
    dmo = o.modifiers.new("rock", 'DISPLACE'); dmo.texture = tx; dmo.strength = 0.45; dmo.mid_level = 0.3; dmo.texture_coords = 'GLOBAL'
    o.data.materials.append(M_ICE)
    for pp in o.data.polygons: pp.use_smooth = True
    to_col(o, C_SET)
# the DA KRAS FILMS exhibit plate on the back wall, above the window (dark logo on a white enamel plate)
to_col(box("TK_LogoPlate", (2.3, 0.06, 0.95), (0, 5.88, -0.62), M_PLATE, bevel=0.03), C_SET)
LOGO_D = "/home/user/Muhammed/blender/assets/brand/DaKrasFilms_logo_dark.png"
LOGO_W = "/home/user/Muhammed/blender/assets/brand/DaKrasFilms_logo_white.png"
def logo_decal(name, path, w, loc, rot, emit=0.0):
    img = bpy.data.images.load(path); lw, lh = img.size
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot); o = bpy.context.active_object; o.name = name
    o.scale = (w, w * lh / lw, 1); bpy.ops.object.transform_apply(scale=True)
    m = bpy.data.materials.new("M_" + name); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n)
    ti = nt.nodes.new("ShaderNodeTexImage"); ti.image = img; ti.interpolation = 'Cubic'
    pr = nt.nodes.new("ShaderNodeBsdfPrincipled"); pr.inputs["Roughness"].default_value = 0.4
    nt.links.new(ti.outputs["Color"], pr.inputs["Base Color"])
    if emit:
        nt.links.new(ti.outputs["Color"], pr.inputs["Emission Color"]); pr.inputs["Emission Strength"].default_value = emit
    trn = nt.nodes.new("ShaderNodeBsdfTransparent"); mxn = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(ti.outputs["Alpha"], mxn.inputs["Fac"]); nt.links.new(trn.outputs[0], mxn.inputs[1]); nt.links.new(pr.outputs[0], mxn.inputs[2])
    nt.links.new(mxn.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    o.data.materials.append(m); o.visible_shadow = False; to_col(o, C_SET); return o
logo_decal("TK_Logo", LOGO_D, 2.0, (0, 5.845, -0.62), (R90, 0, 0))

# ---- the viewing gallery behind the window (lit, two spectators)
to_col(box("GA_Floor", (8.0, 3.4, 0.1), (0, 7.75, GAL_Z - 0.05), M_GAL_FLOOR, bevel=0.0), C_SET)
to_col(box("GA_Back", (8.0, 0.1, 3.6), (0, 9.45, GAL_Z + 1.8), M_GAL_WALL, bevel=0.0), C_SET)
to_col(box("GA_Ceil", (8.0, 3.4, 0.1), (0, 7.75, GAL_Z + 3.5), M_GAL_WALL, bevel=0.0), C_SET)
for sx_ in (-1, 1):
    to_col(box("GA_Side%d" % sx_, (0.1, 3.4, 3.6), (sx_ * 4.0, 7.75, GAL_Z + 1.8), M_GAL_WALL, bevel=0.0), C_SET)
to_col(box("GA_Wall", (8.0, 0.25, 0.2), (0, 6.2, GAL_Z + 0.1), M_STEEL, bevel=0.02), C_SET)
# soft glowing arctic murals on the gallery back wall (aurora bands, no text)
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 9.39, GAL_Z + 1.9), rotation=(R90, 0, 0))
MU = bpy.context.active_object; MU.name = "GA_Mural"; MU.scale = (7.6, 3.0, 1); bpy.ops.object.transform_apply(scale=True)
mu = bpy.data.materials.new("M_Aurora"); mu.use_nodes = True; nt = mu.node_tree
for n in list(nt.nodes):
    if n.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n)
tc = nt.nodes.new("ShaderNodeTexCoord"); wv = nt.nodes.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = 1.2
wv.inputs["Distortion"].default_value = 6.0; wv.inputs["Detail"].default_value = 3.0; nt.links.new(tc.outputs["Generated"], wv.inputs["Vector"])
cr = nt.nodes.new("ShaderNodeValToRGB"); el = cr.color_ramp.elements
el[0].color = (0.04, 0.02, 0.25, 1); el[1].position = 1.0; el[1].color = (0.45, 0.05, 0.55, 1)
e2 = el.new(0.45); e2.color = (0.02, 0.75, 0.45, 1); e3 = el.new(0.7); e3.color = (0.05, 0.45, 0.85, 1)
nt.links.new(wv.outputs["Fac"], cr.inputs["Fac"])
em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Strength"].default_value = 1.2; nt.links.new(cr.outputs["Color"], em.inputs["Color"])
nt.links.new(em.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
MU.data.materials.append(mu); to_col(MU, C_SET)

# ---- the water surface: a displaced sheet (waves ride the keyed empty WaveCtl, never the scene clock)
WC = bpy.data.objects.new("WaveCtl", None); C_SET.objects.link(WC)
bpy.ops.mesh.primitive_grid_add(x_subdivisions=180, y_subdivisions=150, size=1, location=(0, 0, 0))
WT = bpy.context.active_object; WT.name = "TK_Water"; WT.scale = (14.0, 12.0, 1); bpy.ops.object.transform_apply(scale=True)
tx = bpy.data.textures.new("Waves", 'CLOUDS'); tx.noise_scale = 0.55; tx.noise_depth = 2
dmo = WT.modifiers.new("waves", 'DISPLACE'); dmo.texture = tx; dmo.strength = 0.07; dmo.mid_level = 0.5; dmo.texture_coords = 'OBJECT'; dmo.texture_coords_object = WC
for pp in WT.data.polygons: pp.use_smooth = True
wmat = bpy.data.materials.new("M_Water"); wmat.use_nodes = True; nt = wmat.node_tree
for n in list(nt.nodes):
    if n.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n)
geo = nt.nodes.new("ShaderNodeNewGeometry")
# from below: a luminous rippling ceiling (cyan to white)
tcw = nt.nodes.new("ShaderNodeTexCoord"); vw = nt.nodes.new("ShaderNodeTexVoronoi"); vw.voronoi_dimensions = '4D'; vw.feature = 'DISTANCE_TO_EDGE'
vw.inputs["Scale"].default_value = 0.9; vw.inputs["Randomness"].default_value = 1.0; vw.name = "Ripple"; nt.links.new(tcw.outputs["Object"], vw.inputs["Vector"])
crw = nt.nodes.new("ShaderNodeValToRGB"); crw.color_ramp.elements[0].color = (0.85, 0.97, 1.0, 1); crw.color_ramp.elements[1].position = 0.30
crw.color_ramp.elements[1].color = (0.20, 0.70, 0.90, 1); nt.links.new(vw.outputs["Distance"], crw.inputs["Fac"])
emw = nt.nodes.new("ShaderNodeEmission"); emw.inputs["Strength"].default_value = 0.6; nt.links.new(crw.outputs["Color"], emw.inputs["Color"])
glb = nt.nodes.new("ShaderNodeBsdfGlossy"); glb.inputs["Roughness"].default_value = 0.08; glb.inputs["Color"].default_value = (0.3, 0.8, 0.95, 1)
mb = nt.nodes.new("ShaderNodeMixShader"); mb.inputs["Fac"].default_value = 0.08; nt.links.new(emw.outputs[0], mb.inputs[1]); nt.links.new(glb.outputs[0], mb.inputs[2])
# from above: clear teal water (transparent, tinted) with a glossy sheen
tra = nt.nodes.new("ShaderNodeBsdfTransparent"); tra.inputs["Color"].default_value = (0.03, 0.20, 0.24, 1)
gla = nt.nodes.new("ShaderNodeBsdfGlossy"); gla.inputs["Roughness"].default_value = 0.04; gla.inputs["Color"].default_value = (0.9, 0.97, 1.0, 1)
fra = nt.nodes.new("ShaderNodeFresnel"); fra.inputs["IOR"].default_value = 1.33
deep = nt.nodes.new("ShaderNodeBsdfPrincipled"); deep.inputs["Base Color"].default_value = (0.0, 0.10, 0.14, 1); deep.inputs["Roughness"].default_value = 0.6
murk = nt.nodes.new("ShaderNodeMixShader"); murk.inputs["Fac"].default_value = 0.72; nt.links.new(tra.outputs[0], murk.inputs[1]); nt.links.new(deep.outputs[0], murk.inputs[2])
ma = nt.nodes.new("ShaderNodeMixShader"); nt.links.new(fra.outputs[0], ma.inputs["Fac"]); nt.links.new(murk.outputs[0], ma.inputs[1]); nt.links.new(gla.outputs[0], ma.inputs[2])
mfin = nt.nodes.new("ShaderNodeMixShader"); nt.links.new(geo.outputs["Backfacing"], mfin.inputs["Fac"])
nt.links.new(ma.outputs[0], mfin.inputs[1]); nt.links.new(mb.outputs[0], mfin.inputs[2])
nt.links.new(mfin.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
WT.data.materials.append(wmat); WT.visible_shadow = False; to_col(WT, C_SET)
# floating ice floes (they bob with the waves in stage B)
for i, (x, y, r_) in enumerate(((-4.6, 3.8, 0.9), (4.8, 4.2, 0.7), (5.4, -3.6, 1.0), (-5.2, -2.8, 0.6), (2.6, 4.9, 0.5))):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=1.0, location=(x, y, 0.0)); o = bpy.context.active_object
    o.name = "TK_Floe%d" % i; o.scale = (r_, r_ * 0.8, 0.22); bpy.ops.object.transform_apply(scale=True)
    tx = bpy.data.textures.new(o.name + "_tx", 'CLOUDS'); tx.noise_scale = 0.4
    dmo = o.modifiers.new("rock", 'DISPLACE'); dmo.texture = tx; dmo.strength = 0.12; dmo.texture_coords = 'GLOBAL'
    o.data.materials.append(M_ICE_DRY)
    for pp in o.data.polygons: pp.use_smooth = True
    to_col(o, C_SET)

# ---- above the water: the coping, the deck and the arctic hall (the ending)
for nm, sz, lc in (("UP_CopeL", (0.5, 12.9, 0.55), (-7.2, 0, 0.22)), ("UP_CopeR", (0.5, 12.9, 0.55), (7.2, 0, 0.22)),
                   ("UP_CopeF", (14.9, 0.5, 0.55), (0, -6.2, 0.22)), ("UP_CopeB", (14.9, 0.5, 0.55), (0, 6.2, 0.22))):
    to_col(box(nm, sz, lc, M_COPING, bevel=0.06), C_SET)
to_col(box("UP_Deck", (40, 36, 0.2), (0, 0, 0.40), M_DECK, bevel=0.0), C_SET)        # a hole is cut below
bpy.ops.object.select_all(action='DESELECT')
DK = bpy.data.objects["UP_Deck"]
hole = box("UP_DeckHole", (14.6, 12.6, 1.0), (0, 0, 0.4), M_DECK, bevel=0.0)
bo = DK.modifiers.new("hole", 'BOOLEAN'); bo.object = hole; bo.operation = 'DIFFERENCE'
bpy.context.view_layer.objects.active = DK; bpy.ops.object.modifier_apply(modifier="hole"); bpy.data.objects.remove(hole, do_unlink=True)
# snowy ice-rock formations on the deck behind the far rim, an aurora mural wall far behind, a dark ceiling
for i, (x, y, s_) in enumerate(((-5.5, 8.5, 2.2), (-2.0, 9.6, 1.6), (3.0, 9.0, 2.5), (6.5, 8.0, 1.8), (-9.0, 4.0, 2.0), (9.5, 3.0, 2.4))):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=5, radius=1.0, location=(x, y, 0.5)); o = bpy.context.active_object
    o.name = "UP_Rock%d" % i; o.scale = (s_ * 1.1, s_ * 0.7, s_ * 0.9); bpy.ops.object.transform_apply(scale=True)
    tx = bpy.data.textures.new(o.name + "_tx", 'CLOUDS'); tx.noise_scale = 0.8; tx.noise_basis = 'VORONOI_F2'
    dmo = o.modifiers.new("rock", 'DISPLACE'); dmo.texture = tx; dmo.strength = 0.5; dmo.mid_level = 0.3; dmo.texture_coords = 'GLOBAL'
    o.data.materials.append(M_ICE_DRY)
    for pp in o.data.polygons: pp.use_smooth = True
    to_col(o, C_SET)
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 14.0, 5.0), rotation=(R90, 0, 0))
HM = bpy.context.active_object; HM.name = "UP_HallMural"; HM.scale = (40, 10, 1); bpy.ops.object.transform_apply(scale=True)
HM.data.materials.append(mu); to_col(HM, C_SET)
for nm, sz, lc in (("UP_HallL", (0.2, 36, 10), (-18, 0, 5.0)), ("UP_HallR", (0.2, 36, 10), (18, 0, 5.0)), ("UP_HallF", (40, 0.2, 10), (0, -16, 5.0)),
                   ("UP_HallCeil", (40, 36, 0.2), (0, 0, 9.0))):
    to_col(box(nm, sz, lc, M_GAL_WALL, bevel=0.0), C_SET)
# a DA KRAS FILMS banner on the far rim (white logo on a deep-purple banner), read in the ending
to_col(box("UP_Banner", (2.6, 0.05, 1.05), (0.9, 6.75, 1.35), mat("M_Banner", (0.20, 0.02, 0.38), rough=0.6, sheen=0.3), bevel=0.01), C_SET)
for sx_ in (-1, 1):
    to_col(cyl("UP_BannerPole%d" % sx_, 0.03, 1.9, (0.9 + sx_ * 1.35, 6.75, 1.45), M_STEEL), C_SET)
logo_decal("UP_Logo", LOGO_W, 2.3, (0.9, 6.72, 1.35), (R90, 0, 0), emit=0.6)

# ================================================================== light
def light(name, kind, energy, loc, rot=(0, 0, 0), size=1.0, color=(1, 1, 1), size_y=None):
    ld = bpy.data.lights.new(name, kind); ld.energy = energy; ld.color = color
    if kind == 'AREA':
        ld.size = size
        if size_y: ld.shape = 'RECTANGLE'; ld.size_y = size_y
    if kind == 'SUN': ld.angle = math.radians(6)
    o = bpy.data.objects.new(name, ld); C_SET.objects.link(o); o.location = loc; o.rotation_euler = rot
    return o
light("L_Sun", 'SUN', 2.4, (0, 0, 10), rot=(math.radians(12), math.radians(-8), 0), color=(0.85, 0.96, 1.0))
light("L_SkyUnder", 'AREA', 300, (0, 0, -0.25), size=13.0, size_y=11.0, color=(0.55, 0.88, 1.0))
light("L_Gallery1", 'AREA', 260, (-1.2, 7.6, GAL_Z + 3.2), size=2.0, color=(1.0, 0.82, 0.62))
light("L_Gallery2", 'AREA', 260, (1.4, 7.6, GAL_Z + 3.2), size=2.0, color=(1.0, 0.82, 0.62))
light("L_GalleryFace", 'AREA', 120, (0.0, 6.4, GAL_Z + 1.4), rot=(math.radians(-90), 0, 0), size=2.5, color=(1.0, 0.9, 0.8))
light("L_HallKey", 'AREA', 1500, (-3.0, -4.0, 6.5), rot=(math.radians(35), 0, math.radians(-30)), size=6.0, color=(1.0, 0.93, 0.85))
light("L_HallRim", 'AREA', 900, (2.0, 9.0, 5.0), rot=(math.radians(-50), 0, math.radians(180)), size=5.0, color=(0.55, 0.75, 1.0))

# ================================================================== look and render settings (fast, zero-error)
sc.render.engine = 'CYCLES'; cy = sc.cycles
cy.samples = 64; cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.05
cy.use_denoising = True; cy.denoiser = 'OPENIMAGEDENOISE'
cy.max_bounces = 6; cy.diffuse_bounces = 3; cy.glossy_bounces = 3; cy.transmission_bounces = 6; cy.transparent_max_bounces = 16
cy.caustics_reflective = False; cy.caustics_refractive = False
sc.render.use_persistent_data = True
sc.render.use_simplify = True; sc.render.simplify_subdivision_render = 2; cy.texture_limit_render = '2048'
sc.render.use_motion_blur = False
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Punchy'; sc.view_settings.exposure = -0.2
sc.world = sc.world or bpy.data.worlds.new("World")
w = sc.world; w.use_nodes = True; nt = w.node_tree
bgn = [n for n in nt.nodes if n.type == 'BACKGROUND'][0]
bgn.inputs["Color"].default_value = (0.01, 0.16, 0.24, 1); bgn.inputs["Strength"].default_value = 0.6
w.mist_settings.start = 0.8; w.mist_settings.depth = 11.0; w.mist_settings.falloff = 'LINEAR'
# compositor: underwater haze = mix(image, deep teal, mist * HazeAmount); HazeAmount is keyed by stage B
bpy.context.view_layer.use_pass_mist = True
ng = bpy.data.node_groups.new("Comp", "CompositorNodeTree"); sc.compositing_node_group = ng
ng.interface.new_socket("Image", in_out='OUTPUT', socket_type='NodeSocketColor')
rl = ng.nodes.new("CompositorNodeRLayers"); go = ng.nodes.new("NodeGroupOutput")
hv = ng.nodes.new("ShaderNodeValue"); hv.name = "HazeAmount"; hv.outputs[0].default_value = 0.80
mlt = ng.nodes.new("ShaderNodeMath"); mlt.operation = 'MULTIPLY'; ng.links.new(rl.outputs["Mist"], mlt.inputs[0]); ng.links.new(hv.outputs[0], mlt.inputs[1])
mix = ng.nodes.new("ShaderNodeMix"); mix.data_type = 'RGBA'; mix.blend_type = 'MIX'; mix.inputs["B"].default_value = (0.0, 0.13, 0.24, 1)
ng.links.new(mlt.outputs[0], mix.inputs["Factor"]); ng.links.new(rl.outputs["Image"], mix.inputs["A"]); ng.links.new(mix.outputs["Result"], go.inputs[0])
sc.render.use_compositing = True; sc.render.compositor_device = 'CPU'
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("BUILD_DONE", OUT)
