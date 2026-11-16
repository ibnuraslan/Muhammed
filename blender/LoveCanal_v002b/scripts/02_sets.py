"""All Love Canal sets in one scene, each at its own origin. blender -b work/chars.blend -P 02_sets.py -- work/sets.blend"""
import sys, os
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib.py")).read())
out = sys.argv[sys.argv.index("--") + 1]
random.seed(5)
LIB = coll("LIB"); LIB.hide_render = True; LIB.hide_viewport = True

# ------------------------------------------------------------------ world, look
w = bpy.data.worlds.new("Sky"); sc.world = w; w.use_nodes = True; nt = w.node_tree
env = nt.nodes.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(os.path.join(PH, "hdri", "kloofendal_48d_partly_cloudy_puresky_2k.hdr"))
mpw = nt.nodes.new("ShaderNodeMapping"); tcw = nt.nodes.new("ShaderNodeTexCoord"); nt.links.new(tcw.outputs["Generated"], mpw.inputs[0]); nt.links.new(mpw.outputs[0], env.inputs[0])
mpw.inputs["Rotation"].default_value = (0, 0, R_(140))
bg = nt.nodes["Background"]; nt.links.new(env.outputs[0], bg.inputs[0]); bg.inputs[1].default_value = 1.0
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 3.2; sun.data.angle = R_(3); sun.rotation_euler = (R_(42), 0, R_(35)); sun.data.color = (1.0, 0.97, 0.92)
sc.render.engine = 'CYCLES'; sc.render.resolution_x, sc.render.resolution_y = 1080, 1920; sc.render.fps = 60
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Punchy'

# ------------------------------------------------------------------ shared materials
M_asph = pbr("Asphalt", "asphalt_02", 0.25, tint=(0.75, 0.75, 0.78), coords="Object")
M_walk = pbr("Sidewalk", "concrete_tiles", 0.4, tint=(1.05, 1.05, 1.05), coords="Object")
M_lawn = pbr("Lawn", "leafy_grass", 0.3, tint=(0.55, 0.95, 0.4), coords="Object")
M_farg = mat("FarGrass", (0.18, 0.42, 0.1), 0.9)
M_mud = pbr("Dirt", "brown_mud", 0.2, tint=(1.0, 0.85, 0.7), coords="Object")
M_soil = pbr("SoilWall", "excavated_soil_wall", 0.25, tint=(0.85, 0.65, 0.5), coords="Object")
M_block = pbr("CinderBlock", "concrete_block_wall", 0.5, tint=(1.6, 1.55, 1.4), coords="Object")
M_floorwood = pbr("FloorWood", "laminate_floor_02", 0.5, coords="Object")
M_white = mat("PaintWhite", (0.9, 0.9, 0.88), 0.6)
M_dash = mat("RoadDash", (0.95, 0.95, 0.9), 0.5)
M_curb = mat("Curb", (0.7, 0.7, 0.68), 0.7)
M_tox = mat("Toxic", (0.12, 0.95, 0.02), 0.15, emit=(0.25, 1.0, 0.0), emit_s=4.0, spec=0.5)
M_toxd = mat("ToxicDim", (0.2, 0.9, 0.08), 0.2, emit=(0.25, 0.9, 0.05), emit_s=0.9, spec=0.4)

# ------------------------------------------------------------------ library models
def lib_model(name, size, axis=2, drop=(), rz=0.0):
    ms = import_glb(name)
    bad = [o for o in ms if any(k in (o.name + " ".join(m.name for m in o.data.materials if m)) for k in drop)]
    for o in bad: bpy.data.objects.remove(o, do_unlink=True)
    ms = [o for o in ms if o not in bad]
    if rz:
        for o in ms: o.data.transform(Matrix.Rotation(R_(rz), 4, 'Z'))
    normalize(ms, size, axis)
    o = join(ms, "LIB_" + name); link(o, LIB)
    return o
L_house0 = lib_model("house0", 12.5, axis=0)
L_house5 = lib_model("house5", 6.5, drop=("Grass", "Brick_Rough", "Snow"))
L_fence = lib_model("fence", 1.0, rz=90)                  # runs along Y
L_lamp = lib_model("lamp", 6.0)
L_tree = lib_model("tree", 7.0, drop=("Groundcover", "grass"))
L_drum = lib_model("drum", 0.88)
# windows: the scans' see-through glass showed black voids (hollow houses). Opaque glass: sky reflection (clear coat) over cream curtain folds
def window_mat():
    m = bpy.data.materials.new("WindowCurtain"); m.use_nodes = True; nt = m.node_tree; P = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); wv = nt.nodes.new("ShaderNodeTexWave"); wv.wave_type = 'BANDS'; wv.bands_direction = 'X'
    wv.inputs["Scale"].default_value = 3.0; wv.inputs["Distortion"].default_value = 1.5; nt.links.new(tc.outputs["Object"], wv.inputs["Vector"])
    rp = nt.nodes.new("ShaderNodeValToRGB"); nt.links.new(wv.outputs["Fac"], rp.inputs[0])
    rp.color_ramp.elements[0].color = (0.72, 0.62, 0.5, 1); rp.color_ramp.elements[1].color = (0.95, 0.9, 0.8, 1)
    nt.links.new(rp.outputs[0], P.inputs["Base Color"]); P.inputs["Roughness"].default_value = 0.6
    nt.links.new(rp.outputs[0], P.inputs["Emission Color"]); P.inputs["Emission Strength"].default_value = 0.55   # panes sit in shadowed recesses: never a black void
    P.inputs["Coat Weight"].default_value = 1.0; P.inputs["Coat Roughness"].default_value = 0.03; P.inputs["Coat IOR"].default_value = 1.6
    return m
M_win = window_mat()
def siding_mat(name, rgb):
    """painted lap siding without UVs (the scan's siding texture rendered black on its gable and porch faces)"""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; P = nt.nodes["Principled BSDF"]
    P.inputs["Base Color"].default_value = (*rgb, 1); P.inputs["Roughness"].default_value = 0.7
    P.inputs["Emission Color"].default_value = (*rgb, 1); P.inputs["Emission Strength"].default_value = 0.25
    tc = nt.nodes.new("ShaderNodeTexCoord"); wv = nt.nodes.new("ShaderNodeTexWave"); wv.wave_type = 'BANDS'; wv.bands_direction = 'Z'
    wv.wave_profile = 'SAW'; wv.inputs["Scale"].default_value = 1.6; nt.links.new(tc.outputs["Object"], wv.inputs["Vector"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.25; nt.links.new(wv.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], P.inputs["Normal"])
    return m
def fill_hull(L_, rgb):
    bm = bmesh.new(); bm.from_mesh(L_.data)
    ch = bmesh.ops.convex_hull(bm, input=bm.verts[:])
    keep = set(ch["geom"]); [bm.faces.remove(f) for f in [f for f in bm.faces if f not in keep]]
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    c = sum((v.co for v in bm.verts), Vector()) / len(bm.verts)
    for v in bm.verts: v.co = c + (v.co - c) * Vector((0.78, 0.78, 0.92))
    me = bpy.data.meshes.new(L_.name + "_fill"); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(L_.name + "_fill", me); o.data.materials.append(mat("HouseInside", rgb, 0.8)); return o
for L_ in (L_house0, L_house5):
    for i, m in enumerate(L_.data.materials):
        if m and any(k in m.name.lower() for k in ("glass", "window")): L_.data.materials[i] = M_win
for i, m in enumerate(L_house5.data.materials):
    if m and "Cladding_Siding_White" in m.name: L_house5.data.materials[i] = siding_mat("SidingTan", (0.72, 0.56, 0.38))
    elif m and "Cladding_Siding_Tan" in m.name: L_house5.data.materials[i] = siding_mat("SidingTan2", (0.66, 0.5, 0.34))
    elif m and m.name == "material": L_house5.data.materials[i] = siding_mat("SidingTan3", (0.7, 0.54, 0.37))
for L_ in (L_house0, L_house5):          # inverted faces render black under bump/normal maps: make every normal face outward
    _bm = bmesh.new(); _bm.from_mesh(L_.data)
    bmesh.ops.remove_doubles(_bm, verts=_bm.verts[:], dist=0.002)
    seen_ = {}; dup_ = []
    for f_ in _bm.faces:                     # coincident duplicate faces shadow each other black: keep one
        k_ = tuple(sorted(v.index for v in f_.verts))
        if k_ in seen_: dup_.append(f_)
        else: seen_[k_] = f_
    bmesh.ops.delete(_bm, geom=dup_, context='FACES_ONLY')
    bmesh.ops.recalc_face_normals(_bm, faces=_bm.faces[:]); _bm.to_mesh(L_.data); _bm.free()
    print("HOUSE dedupe", L_.name, len(dup_))


# ------------------------------------------------------------------ STREET (origin 0,0,0): road along +Y
STREET = coll("SET_street")
road = plane("Road", (7.0, 170), (0, 15, 0.0), M_asph, STREET)
for y in range(-60, 100, 6): plane("Dash.%d" % y, (0.12, 2.6), (0, y, 0.004), M_dash, STREET)
for sx in (-1, 1):
    box("Curb.%d" % sx, (0.18, 170, 0.15), (sx * 3.59, 15, 0.075), M_curb, STREET)
    box("Walk.%d" % sx, (2.4, 170, 0.12), (sx * 4.88, 15, 0.06), M_walk, STREET)
    plane("Lawn.%d" % sx, (60, 170), (sx * 36.1, 15, 0.1), M_lawn, STREET)
plane("Ground_far", (500, 600), (-20, 100, 0.0), M_farg, STREET).location.z = -0.03
HOUSE_Y = [-24, -6, 12, 30, 48, 66, 84]
for sx in (-1, 1):
    for i, y in enumerate(HOUSE_Y):
        src = L_house0 if (i + (sx > 0)) % 2 == 0 else L_house5
        copy_obj(src, "House.%s%d" % ("L" if sx < 0 else "R", i), (sx * 17.5, y, 0.1), rz=(-90 if sx < 0 else 90), c=STREET)
        for k in range(6):                                                   # fence along the lawn front with a gate gap
            yy = y - 8.0 + k * 2.27 + (2.4 if k >= 3 else 0)
            if yy > y + 9: continue
            copy_obj(L_fence, "Fence.%s%d_%d" % ("L" if sx < 0 else "R", i, k), (sx * 6.25, yy + 1.13, 0.1), c=STREET)
        copy_obj(L_tree, "Tree.%s%d" % ("L" if sx < 0 else "R", i), (sx * (10 + random.random() * 3), y + 6 + random.random() * 2, 0.1), rz=random.random() * 360, c=STREET).scale = [0.8 + random.random() * 0.4] * 3
for k, y in enumerate(range(-40, 100, 28)):
    for sx in (-1, 1): copy_obj(L_lamp, "Lamp.%d%d" % (k, sx), (sx * 5.7, y + (14 if sx > 0 else 0), 0.12), rz=(0 if sx < 0 else 180), c=STREET)

exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "02b_sets.py")).read())
bpy.ops.wm.save_as_mainfile(filepath=out)
