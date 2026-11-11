"""Build the static Tsunami2004 set.  blender -b --factory-startup --python 02_scene.py -- <out.blend>"""
import sys
exec(open("/home/user/Muhammed/blender/Tsunami2004_v001/scripts/lib.py").read())
out = sys.argv[sys.argv.index("--") + 1]
random.seed(25)
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob, do_unlink=True)
sc = bpy.context.scene
r = sc.render
r.resolution_x, r.resolution_y, r.resolution_percentage = 1080, 1920, 100
r.fps, r.fps_base = 60, 1.0
sc.frame_start, sc.frame_end = 1, 2400
r.engine = 'CYCLES'; cy = sc.cycles
cy.device = 'CPU'; cy.samples = 48; cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.05
cy.use_denoising = True; cy.denoiser = 'OPENIMAGEDENOISE'
cy.max_bounces, cy.diffuse_bounces, cy.glossy_bounces, cy.transmission_bounces, cy.transparent_max_bounces = 8, 3, 3, 8, 8
cy.volume_bounces = 0; cy.caustics_reflective = cy.caustics_refractive = False
r.use_persistent_data = True
r.use_motion_blur = True; r.motion_blur_shutter = 0.5
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
r.image_settings.file_format = 'PNG'

LIB = coll("LIB"); C_T = coll("Terrain"); C_W = coll("Water"); C_B = coll("Beach"); C_H = coll("Hotel")
C_TOWN = coll("Town"); C_SEA = coll("Seabed"); C_D = coll("Diorama"); C_FX = coll("FX")
bpy.context.view_layer.layer_collection.children["LIB"].exclude = True

# ================================================================== world + sun
w = bpy.data.worlds.new("World"); sc.world = w; w.use_nodes = True
N, Lk = w.node_tree.nodes, w.node_tree.links
bg = N["Background"]
e1 = N.new("ShaderNodeTexEnvironment"); e1.image = load_img(ASSETS + "/hdri/qwantani_mid_morning_puresky_2k.hdr")
e2 = N.new("ShaderNodeTexEnvironment"); e2.image = load_img(ASSETS + "/hdri/qwantani_sunset_puresky_2k.hdr")
mpw = N.new("ShaderNodeMapping"); tcw = N.new("ShaderNodeTexCoord"); Lk.new(tcw.outputs["Generated"], mpw.inputs["Vector"])
mpw.inputs["Rotation"].default_value[2] = math.radians(90)
Lk.new(mpw.outputs["Vector"], e1.inputs["Vector"]); Lk.new(mpw.outputs["Vector"], e2.inputs["Vector"])
mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.name = "HDRI_MIX"
Lk.new(e1.outputs["Color"], mx.inputs["A"]); Lk.new(e2.outputs["Color"], mx.inputs["B"]); Lk.new(mx.outputs["Result"], bg.inputs["Color"])
mx.inputs["Factor"].default_value = 0.0; bg.inputs["Strength"].default_value = 0.9
sun_d = bpy.data.lights.new("Sun", 'SUN'); sun_d.energy = 4.0; sun_d.angle = math.radians(1.5); sun_d.color = (1.0, 0.95, 0.88)
sun = bpy.data.objects.new("Sun", sun_d); sc.collection.objects.link(sun)
sun.rotation_euler = (math.radians(55), 0, math.radians(200))   # from the land side (east), morning

# ================================================================== terrain
def grid(nx, ny, x0, x1, y0, y1, fy=None):
    xs = np.linspace(x0, x1, nx); ys = np.linspace(0, 1, ny)
    ys = y0 + (y1 - y0) * (fy(ys) if fy else ys)
    verts = [(x, y, terrain_h(x, y)) for y in ys for x in xs]
    faces = [(j * nx + i, j * nx + i + 1, (j + 1) * nx + i + 1, (j + 1) * nx + i) for j in range(ny - 1) for i in range(nx - 1)]
    return verts, faces
v, f = grid(420, 520, -420, 420, -380, 440)
terr = mesh_obj("Terrain", v, f, C_T)
for p in terr.data.polygons: p.use_smooth = True
v, f = grid(40, 40, -3000, 3000, 440, 7000)
deep = mesh_obj("DeepFloor", v, f, C_T)

m, nt = node_mat("M_Terrain")
NN, LL = nt.nodes, nt.links
bsdf = NN["Principled BSDF"]
tc = NN.new("ShaderNodeTexCoord"); sx = NN.new("ShaderNodeSeparateXYZ"); LL.new(tc.outputs["Object"], sx.inputs["Vector"])
zones = [("red_laterite_soil_stones", 3.0, (0.85, 0.75, 0.65)), ("coast_sand_01", 2.5, (1.0, 0.95, 0.85)),
         ("damp_beach_sand", 2.5, (0.85, 0.8, 0.72)), ("coral_mud_01", 4.0, (0.55, 0.55, 0.48))]
socks = [pbr_nodes(nt, tid, s, tint, coord=tc.outputs["Object"], x=-1400, y=900 - 700 * i) for i, (tid, s, tint) in enumerate(zones)]
edges = [(-50, -40), (-2, 6), (24, 40)]
def ramp_fac(a, b):
    mr = NN.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = a; mr.inputs["From Max"].default_value = b
    LL.new(sx.outputs["Y"], mr.inputs["Value"]); return mr.outputs["Result"]
col, nor, rou = socks[0]
for i, (a, b) in enumerate(edges):
    fac = ramp_fac(a, b)
    c2, n2, r2 = socks[i + 1]
    mc = NN.new("ShaderNodeMix"); mc.data_type = 'RGBA'; LL.new(fac, mc.inputs["Factor"]); LL.new(col, mc.inputs["A"]); LL.new(c2, mc.inputs["B"]); col = mc.outputs["Result"]
    mn = NN.new("ShaderNodeMix"); mn.data_type = 'VECTOR'; LL.new(fac, mn.inputs["Factor"]); LL.new(nor, mn.inputs["A"]); LL.new(n2, mn.inputs["B"]); nor = mn.outputs["Result"]
    if r2 is not None:
        mr_ = NN.new("ShaderNodeMix"); mr_.data_type = 'FLOAT'; LL.new(fac, mr_.inputs["Factor"]); LL.new(rou, mr_.inputs["A"]); LL.new(r2, mr_.inputs["B"]); rou = mr_.outputs["Result"]
# wetness: everything below z 0.25 is wet (darker, glossier)
wet = NN.new("ShaderNodeMapRange"); wet.inputs["From Min"].default_value = 0.35; wet.inputs["From Max"].default_value = 0.0
LL.new(sx.outputs["Z"], wet.inputs["Value"])
# aftermath mud over the land: MUD value is keyframed 0 -> 1
mud_v = NN.new("ShaderNodeValue"); mud_v.name = "MUD"; mud_v.outputs[0].default_value = 0.0
mud_c, mud_n, mud_r = pbr_nodes(nt, "brown_mud", 3.0, (0.7, 0.62, 0.5), coord=tc.outputs["Object"], x=-1400, y=-2000)
mud_mask = NN.new("ShaderNodeMath"); mud_mask.operation = 'MULTIPLY'; LL.new(mud_v.outputs[0], mud_mask.inputs[0])
lm = NN.new("ShaderNodeMapRange"); lm.inputs["From Min"].default_value = 15; lm.inputs["From Max"].default_value = 0; LL.new(sx.outputs["Y"], lm.inputs["Value"])
LL.new(lm.outputs["Result"], mud_mask.inputs[1])
mc = NN.new("ShaderNodeMix"); mc.data_type = 'RGBA'; LL.new(mud_mask.outputs[0], mc.inputs["Factor"]); LL.new(col, mc.inputs["A"]); LL.new(mud_c, mc.inputs["B"]); col = mc.outputs["Result"]
wetall = NN.new("ShaderNodeMath"); wetall.operation = 'MAXIMUM'; LL.new(wet.outputs["Result"], wetall.inputs[0]); LL.new(mud_mask.outputs[0], wetall.inputs[1])
dk = NN.new("ShaderNodeMix"); dk.data_type = 'RGBA'; dk.blend_type = 'MULTIPLY'; LL.new(wetall.outputs[0], dk.inputs["Factor"])
dk.inputs["B"].default_value = (0.55, 0.55, 0.55, 1); LL.new(col, dk.inputs["A"])
LL.new(dk.outputs["Result"], bsdf.inputs["Base Color"]); LL.new(nor, bsdf.inputs["Normal"])
rw = NN.new("ShaderNodeMix"); rw.data_type = 'FLOAT'; LL.new(wetall.outputs[0], rw.inputs["Factor"]); LL.new(rou, rw.inputs["A"]); rw.inputs["B"].default_value = 0.18
LL.new(rw.outputs["Result"], bsdf.inputs["Roughness"])
terr.data.materials.append(m); deep.data.materials.append(simple_mat("M_Deep", (0.05, 0.06, 0.05), 0.9))

# roads (asphalt strips)
asph = pbr_mat("M_Asphalt", "worn_asphalt", 4.0, (0.8, 0.8, 0.8))
for i, x in enumerate(ROADS_X):
    box("RoadNS_%d" % i, C_T, (7, 330, 0.12), (x, -215, 0.58), asph)
for i, y in enumerate(ROADS_Y):
    box("RoadEW_%d" % i, C_T, (420, 7, 0.12), (0, y, 0.585), asph)

# ================================================================== water materials
def water_mat(name, foam_steep=True):
    m, nt = node_mat(name)
    if nt is None: return m
    NN, LL = nt.nodes, nt.links; b = NN["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.012, 0.045, 0.05, 1); b.inputs["Roughness"].default_value = 0.07
    b.inputs["IOR"].default_value = 1.33; b.inputs["Specular IOR Level"].default_value = 0.6
    tc = NN.new("ShaderNodeTexCoord")
    nz = NN.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.35; nz.inputs["Detail"].default_value = 8; nz.noise_dimensions = '4D'
    nz.name = "NZ"; LL.new(tc.outputs["Object"], nz.inputs["Vector"])
    bp = NN.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.35; bp.inputs["Distance"].default_value = 0.3
    LL.new(nz.outputs["Fac"], bp.inputs["Height"]); LL.new(bp.outputs["Normal"], b.inputs["Normal"])
    geo = NN.new("ShaderNodeNewGeometry"); sz = NN.new("ShaderNodeSeparateXYZ"); LL.new(geo.outputs["Normal"], sz.inputs["Vector"])
    # steep faces glow a lighter green-teal (light through the thin wall)
    stp = NN.new("ShaderNodeMapRange"); stp.inputs["From Min"].default_value = 0.8; stp.inputs["From Max"].default_value = 0.2; LL.new(sz.outputs["Z"], stp.inputs["Value"])
    emi = NN.new("ShaderNodeMath"); emi.operation = 'MULTIPLY'; emi.inputs[1].default_value = 0.35 if foam_steep else 0.0
    LL.new(stp.outputs["Result"], emi.inputs[0]); LL.new(emi.outputs[0], b.inputs["Emission Strength"])
    b.inputs["Emission Color"].default_value = (0.05, 0.22, 0.2, 1)
    # foam: lip/overhang (normal pointing down/sideways) + soft streak noise + base patches (flood)
    lipm = NN.new("ShaderNodeMapRange"); lipm.inputs["From Min"].default_value = 0.15; lipm.inputs["From Max"].default_value = -0.25; LL.new(sz.outputs["Z"], lipm.inputs["Value"])
    fn = NN.new("ShaderNodeTexNoise"); fn.inputs["Scale"].default_value = 0.22; fn.inputs["Detail"].default_value = 12; fn.inputs["Roughness"].default_value = 0.7
    fn.noise_dimensions = '4D'; fn.name = "FN"
    mp = NN.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1.0, 1.0, 0.5); LL.new(tc.outputs["Object"], mp.inputs["Vector"]); LL.new(mp.outputs["Vector"], fn.inputs["Vector"])
    fr = NN.new("ShaderNodeMapRange"); fr.inputs["From Min"].default_value = 0.42; fr.inputs["From Max"].default_value = 0.72; LL.new(fn.outputs["Fac"], fr.inputs["Value"])
    fv = NN.new("ShaderNodeValue"); fv.name = "FOAM_BASE"; fv.outputs[0].default_value = 0.0
    a1 = NN.new("ShaderNodeMath"); a1.operation = 'MULTIPLY'; a1.inputs[1].default_value = 0.55 if foam_steep else 0.0
    LL.new(stp.outputs["Result"], a1.inputs[0])
    a2 = NN.new("ShaderNodeMath"); a2.operation = 'ADD'; LL.new(a1.outputs[0], a2.inputs[0]); LL.new(fv.outputs[0], a2.inputs[1])
    a3 = NN.new("ShaderNodeMath"); a3.operation = 'MULTIPLY'; LL.new(a2.outputs[0], a3.inputs[0]); LL.new(fr.outputs["Result"], a3.inputs[1])
    a4 = NN.new("ShaderNodeMath"); a4.operation = 'ADD'; a4.use_clamp = True; LL.new(a3.outputs[0], a4.inputs[0])
    lw = NN.new("ShaderNodeMath"); lw.operation = 'MULTIPLY'; lw.inputs[1].default_value = 1.0 if foam_steep else 0.0
    LL.new(lipm.outputs["Result"], lw.inputs[0]); LL.new(lw.outputs[0], a4.inputs[1])
    foam = NN.new("ShaderNodeBsdfPrincipled"); foam.inputs["Base Color"].default_value = (0.82, 0.86, 0.86, 1); foam.inputs["Roughness"].default_value = 0.75
    foam.inputs["Subsurface Weight"].default_value = 0.3; foam.inputs["Subsurface Radius"].default_value = (0.5, 0.5, 0.5)
    ms = NN.new("ShaderNodeMixShader"); LL.new(a4.outputs[0], ms.inputs["Fac"]); LL.new(b.outputs[0], ms.inputs[1]); LL.new(foam.outputs[0], ms.inputs[2])
    LL.new(ms.outputs[0], NN["Material Output"].inputs["Surface"])
    return m
M_SEA = water_mat("M_Sea", foam_steep=False)
M_WAVE = water_mat("M_Wave")

sea = mesh_obj("SeaPlane", [(-3000, -10, 0), (3000, -10, 0), (3000, 7000, 0), (-3000, 7000, 0)], [(0, 1, 2, 3)], C_W, [M_SEA])
ssd = sea.modifiers.new("sub", 'SUBSURF'); ssd.subdivision_type = 'SIMPLE'; ssd.levels = ssd.render_levels = 6

# ================================================================== the wave sheet (shape-keyed stages)
NXW, NUW = 900, 170
xs = np.linspace(-1500, 1500, NXW)
s = np.linspace(0, 1, NUW); us = -12 + 3012 * s ** 2.1
amp = 1 + 0.12 * np.sin(xs / 97) + 0.07 * np.sin(xs / 41 + 1)
yoff = 14 * np.sin(xs / 230) + 5 * np.sin(xs / 77 + 2)
TOE = -7.0
STAGES = {  # crest z, front width, power, lip, back decay, back level
    "S0": (-2.6, 160, 1.5, 0.0, 160, -4.3),
    "S1": (7.0, 75, 2.3, 2.5, 110, -2.6),
    "S2": (32.0, 42, 3.0, 11.0, 90, -0.6),
    "S2b": (17.0, 34, 2.2, 18.0, 70, 2.0),
    "S3": (5.0, 16, 1.4, 2.0, 30, 2.5),
}
def profile(st):
    Zc, c, p, lip, wb, Lb = st
    X = np.zeros((NUW, NXW)); Y = np.zeros((NUW, NXW)); Z = np.zeros((NUW, NXW))
    for j, u in enumerate(us):
        zc = TOE + (Zc - TOE) * amp
        if u < 0:
            z = np.full(NXW, TOE - 1.0); dy = np.zeros(NXW)
        elif u < c:
            x = u / c; z = TOE + (zc - TOE) * x ** p; dy = -lip * amp * x ** 6
        else:
            e = np.exp(-((u - c) / wb) ** 1.5); z = Lb + (zc - Lb) * e
            dy = -lip * amp * np.exp(-((u - c) / (0.35 * c + 1)) ** 2)
            z = z - 0.35 * lip * (1 - np.exp(-((u - c) / (0.3 * c + 1)) ** 2)) * np.exp(-((u - c) / (0.8 * c + 1)) ** 2)
        X[j] = xs; Y[j] = u + dy + yoff; Z[j] = z
    return np.stack([X, Y, Z], -1).reshape(-1, 3)
P0 = profile(STAGES["S0"])
faces = [(j * NXW + i, j * NXW + i + 1, (j + 1) * NXW + i + 1, (j + 1) * NXW + i) for j in range(NUW - 1) for i in range(NXW - 1)]
wave = mesh_obj("Wave", [tuple(p) for p in P0], faces, C_W, [M_WAVE])
for p in wave.data.polygons: p.use_smooth = True
wave.shape_key_add(name="S0")
for k in ("S1", "S2", "S2b", "S3"):
    sk = wave.shape_key_add(name=k, from_mix=False); sk.data.foreach_set("co", profile(STAGES[k]).ravel())
wave.location = (0, 1800, 0)
for k in wave.data.shape_keys.key_blocks[1:]: k.value = 0.0
tx = bpy.data.textures.new("WaveNoiseTex", 'CLOUDS'); tx.noise_scale = 6.0; tx.noise_depth = 2
wn = bpy.data.objects.new("WaveNoiseEmpty", None); C_W.objects.link(wn)
dm = wave.modifiers.new("chop", 'DISPLACE'); dm.texture = tx; dm.texture_coords = 'OBJECT'; dm.texture_coords_object = wn
dm.strength = 1.2; dm.mid_level = 0.5

NSR = 8
def spray_profile(st, k):
    Zc, c, p, lip, wb, Lb = st
    rows = []
    for j in range(NSR):
        v = j / (NSR - 1); u = c * (0.82 + 0.9 * v)
        zc = TOE + (Zc - TOE) * amp
        e = np.exp(-((u - c) / wb) ** 1.5) if u >= c else (u / c) ** p
        z = (Lb + (zc - Lb) * e) if u >= c else TOE + (zc - TOE) * e
        dy = -lip * amp * (np.exp(-((u - c) / (0.35 * c + 1)) ** 2) if u >= c else (u / c) ** 6)
        rows.append(np.stack([xs, u + dy + yoff - 2.0, z + 0.8 + k * (1.0 - v) * 2.5], -1))
    return np.concatenate(rows)
SPR = {"S0": 0.0, "S1": 0.4, "S2": 1.0, "S2b": 1.6, "S3": 0.5}
Q0 = spray_profile(STAGES["S0"], SPR["S0"])
sfaces = [(j * NXW + i, j * NXW + i + 1, (j + 1) * NXW + i + 1, (j + 1) * NXW + i) for j in range(NSR - 1) for i in range(NXW - 1)]
spray_m2, ntq = node_mat("M_CrestSpray")
NNq, LLq = ntq.nodes, ntq.links; NNq.remove(NNq["Principled BSDF"])
vq = NNq.new("ShaderNodeVolumePrincipled"); vq.inputs["Color"].default_value = (0.92, 0.95, 0.97, 1)
nq = NNq.new("ShaderNodeTexNoise"); nq.inputs["Scale"].default_value = 0.4; nq.inputs["Detail"].default_value = 8; nq.noise_dimensions = '4D'; nq.name = "NQ"
rq = NNq.new("ShaderNodeMapRange"); rq.inputs["From Min"].default_value = 0.45; rq.inputs["From Max"].default_value = 0.7; rq.inputs["To Max"].default_value = 0.6
rq.name = "SPRAY_DENS"
LLq.new(nq.outputs["Fac"], rq.inputs["Value"]); LLq.new(rq.outputs["Result"], vq.inputs["Density"]); LLq.new(vq.outputs[0], NNq["Material Output"].inputs["Volume"])
spray = mesh_obj("WaveSpray", [tuple(p) for p in Q0], sfaces, C_W, [spray_m2])
spray.shape_key_add(name="S0")
for k in ("S1", "S2", "S2b", "S3"):
    sk = spray.shape_key_add(name=k, from_mix=False); sk.data.foreach_set("co", spray_profile(STAGES[k], SPR[k]).ravel()); sk.value = 0.0
sso = spray.modifiers.new("shell", 'SOLIDIFY'); sso.thickness = 4.5; sso.offset = 0.0
spray.parent = wave


# ================================================================== beach set
C_LIB = LIB
palmA = import_glb("palm_a", 11.0, "z", C_LIB); palmB = import_glb("palm_b", 12.5, "z", C_LIB)
longt = import_glb("longtail", 10.0, "y", C_LIB); rowb = import_glb("rowboat", 4.2, "y", C_LIB)
umb = import_glb("umbrella", 2.5, "z", C_LIB); umb2 = import_glb("umbrella2", 2.4, "z", C_LIB)
car = import_glb("car", 4.3, "y", C_LIB); car2 = import_glb("car2", 4.5, "y", C_LIB)
coral = import_glb("coral", 1.3, "z", C_LIB)
for ms_ in coral.data.materials:
    ntc = ms_.node_tree; bc = ntc.nodes.get("Principled BSDF")
    if bc and bc.inputs["Base Color"].links:
        src_ = bc.inputs["Base Color"].links[0].from_socket
        hs = ntc.nodes.new("ShaderNodeHueSaturation"); hs.inputs["Hue"].default_value = 0.8; hs.inputs["Saturation"].default_value = 0.55; hs.inputs["Value"].default_value = 0.8
        ntc.links.new(src_, hs.inputs["Color"]); ntc.links.new(hs.outputs["Color"], bc.inputs["Base Color"])
house = import_glb("house", 10.0, "x", C_LIB); house2 = import_glb("house2", 8.5, "x", C_LIB)
rub_roof = import_glb("rubble_roof", 7.0, "max", C_LIB); rub_brick = import_glb("rubble_brick", 3.5, "max", C_LIB)
rub_wood = import_glb("rubble_wood", 4.5, "max", C_LIB); mosque = import_glb("mosque", 26.0, "max", C_LIB)
mosque = link(mosque, C_TOWN); mosque.name = "Mosque"; mosque.location = (-44, -162, terrain_h(-44, -162) - 0.32)
mosque.rotation_euler = (0, 0, math.radians(90))

def ground(x, y): return terrain_h(x, y)
PALMS = []
for i in range(46):
    x = -210 + i * 9.5 + random.uniform(-3, 3); y = random.uniform(-12, 4)
    if -20 < x < 20 and y < -5: continue
    lib = palmA if i % 2 else palmB
    p = inst(lib, "Palm_%02d" % i, C_B, (x, y, ground(x, y) - 0.2), (math.radians(random.uniform(-6, 6)), math.radians(random.uniform(-6, 6)), random.uniform(0, 6.28)), random.uniform(0.85, 1.15))
    PALMS.append(p)
for i in range(30):   # palms in town
    x = random.uniform(-200, 200); y = random.uniform(-330, -60)
    if any(abs(x - rx) < 6 for rx in ROADS_X) or any(abs(y - ry) < 6 for ry in ROADS_Y): continue
    p = inst(palmA if i % 2 else palmB, "TPalm_%02d" % i, C_TOWN, (x, y, ground(x, y) - 0.2), (0, 0, random.uniform(0, 6.28)), random.uniform(0.8, 1.1))
UMB = []
for i in range(14):
    x = -70 + i * 10 + random.uniform(-2, 2); y = random.uniform(-15, -4)
    u = inst(umb if i % 3 else umb2, "Umbrella_%02d" % i, C_B, (x, y, ground(x, y) - 0.25), (math.radians(random.uniform(-4, 4)), 0, random.uniform(0, 6.28)))
    UMB.append(u)
lounger_m = simple_mat("M_Lounger", (0.75, 0.68, 0.55), 0.6)
for i in range(12):
    x = -66 + i * 11 + random.uniform(-1, 1); y = random.uniform(-14, -6)
    box("Lounger_%02d" % i, C_B, (0.7, 1.9, 0.08), (x + 1.2, y, ground(x, y) + 0.35), lounger_m, rot=(math.radians(8), 0, math.radians(random.uniform(-10, 10))), bevel=0.02)
# longtail boats: drawn up on the beach, and moored in the shallows (they settle on the sand as the sea drains)
BOATS = []
for i, (x, y, yaw) in enumerate([(36, 3, 80), (48, 1, 95), (62, 4, 70), (-48, 2, 100), (-60, 5, 85),
                                 (14, 34, 10), (-8, 46, -20), (30, 58, 35), (-26, 70, 5), (6, 88, -40)]):
    b = inst(longt, "Longtail_%02d" % i, C_B, (x, y, ground(x, y) + 0.05), (0, 0, math.radians(yaw)))
    b["moored"] = 1 if y > 20 else 0; BOATS.append(b)
ROWB = []
for i, (x, y, yaw) in enumerate([(10, 104, 30), (-14, 122, 120), (22, 140, -60), (-4, 165, 80)]):
    b = inst(rowb, "Rowboat_%02d" % i, C_SEA, (x, y, ground(x, y)), (0, math.radians(28), math.radians(yaw))); ROWB.append(b)
# coral heads and rocks on the shelf
rock_m = pbr_mat("M_Rock", "rubble", 1.5, (0.5, 0.48, 0.42))
for i in range(70):
    x = random.uniform(-60, 60); y = random.uniform(60, 420)
    inst(coral, "Coral_%02d" % i, C_SEA, (x, y, ground(x, y) - 0.15), (0, 0, random.uniform(0, 6.28)), random.uniform(0.6, 1.6))
for i in range(60):
    x = random.uniform(-80, 80); y = random.uniform(40, 420)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1, location=(x, y, ground(x, y)))
    o = bpy.context.active_object; o.name = "Rock_%02d" % i; link(o, C_SEA)
    sc_ = random.uniform(0.3, 1.2); o.scale = (sc_ * random.uniform(0.8, 1.5), sc_, sc_ * 0.45); o.rotation_euler.z = random.uniform(0, 6)
    o.data.materials.append(rock_m)
# stranded fish (procedural, silver)
fish_m, nt = node_mat("M_Fish")
b_ = nt.nodes["Principled BSDF"]; b_.inputs["Metallic"].default_value = 0.6; b_.inputs["Roughness"].default_value = 0.25
grad = nt.nodes.new("ShaderNodeTexGradient"); tcf = nt.nodes.new("ShaderNodeTexCoord"); sp = nt.nodes.new("ShaderNodeSeparateXYZ")
nt.links.new(tcf.outputs["Object"], sp.inputs["Vector"])
cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (0.75, 0.78, 0.8, 1); cr.color_ramp.elements[1].color = (0.12, 0.18, 0.25, 1)
mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = -0.02; mr.inputs["From Max"].default_value = 0.05
nt.links.new(sp.outputs["Z"], mr.inputs["Value"]); nt.links.new(mr.outputs["Result"], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], b_.inputs["Base Color"])
def make_fish_mesh():
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=1.0)
    for v_ in bm.verts:
        x, y, z = v_.co
        taper = 1 - 0.55 * max(0, y)   # thinner tail end at +y
        v_.co = Vector((x * 0.035 * taper, y * 0.17, z * 0.06 * taper))
    tail = [bm.verts.new(c) for c in ((0, 0.16, 0), (0.002, 0.27, 0.07), (0.002, 0.27, -0.07))]
    bm.faces.new(tail)
    me = bpy.data.meshes.new("FishMesh"); bm.to_mesh(me); bm.free(); me.materials.append(fish_m)
    for p in me.polygons: p.use_smooth = True
    return me
fme = make_fish_mesh()
FISH = []
fish_spots = [(2, 86), (-1.5, 90), (4, 93), (-3, 84), (-0.5, 90.9), (-2.4, 89.1), (-1.0, 91.8)] + [(random.uniform(-30, 30), random.uniform(45, 200)) for _ in range(40)]
for i, (x, y) in enumerate(fish_spots):
    o = bpy.data.objects.new("Fish_%02d" % i, fme); C_SEA.objects.link(o)
    sc_ = random.uniform(1.0, 1.7) if i > 6 else 1.9
    o.scale = (sc_,) * 3
    o.location = (x, y, ground(x, y) + 0.09 * sc_); o.rotation_euler = (0, math.radians(90), random.uniform(0, 6.28))
    FISH.append(o)

# ================================================================== hotel (3 storeys, seafront at y -28)
HX0, HX1, HY0, HY1, FH = -16, 16, -44, -28, 3.6
plaster = pbr_mat("M_HotelPlaster", "white_plaster_rough_01", 3.0, (0.95, 0.93, 0.88))
glass = simple_mat("M_Glass", (0.2, 0.28, 0.3), 0.05, metal=0.0, trans=0.0)
glass.node_tree.nodes["Principled BSDF"].inputs["Specular IOR Level"].default_value = 1.0
dark = simple_mat("M_Interior", (0.06, 0.05, 0.045), 0.8)
rail_m = simple_mat("M_Rail", (0.85, 0.85, 0.82), 0.4, metal=0.5)
z0 = 0.6
box("Hotel_Slab0", C_H, (33, 17, 0.4), (0, -36, z0 + 0.0), plaster)
for k in range(1, 4):
    box("Hotel_Slab%d" % k, C_H, (33, 17, 0.35), (0, -36, z0 + k * FH), plaster)
    box("Hotel_Balc%d" % k, C_H, (33, 1.6, 0.25), (0, HY1 + 0.8, z0 + k * FH - 0.1), plaster)
    box("Hotel_RailTop%d" % k, C_H, (33, 0.06, 0.06), (0, HY1 + 1.55, z0 + k * FH + 1.0), rail_m)
    for i in range(34):
        box("Hotel_Bar%d_%02d" % (k, i), C_H, (0.04, 0.04, 1.0), (-16.4 + i, HY1 + 1.55, z0 + k * FH + 0.5), rail_m)
box("Hotel_Parapet", C_H, (33, 17, 0.9), (0, -36, z0 + 3 * FH + 0.6), plaster)
box("Hotel_Back", C_H, (32, 0.3, 3 * FH), (0, HY0, z0 + 1.5 * FH), plaster)
for sx in (-1, 1):
    box("Hotel_Side%d" % sx, C_H, (0.3, 16, 3 * FH), (sx * 16, -36, z0 + 1.5 * FH), plaster)
for i in range(9):
    x = -16 + i * 4
    for k in range(3):
        box("Hotel_Col%d_%d" % (i, k), C_H, (0.5, 0.5, FH), (x, HY1 - 0.2, z0 + (k + 0.5) * FH), plaster)
for k in (1, 2):   # upper floors: glass sliding doors
    box("Hotel_Glass%d" % k, C_H, (32, 0.08, FH - 0.5), (0, HY1 - 0.6, z0 + (k + 0.5) * FH - 0.1), glass)
box("Hotel_Inside", C_H, (31.5, 14, 3 * FH - 0.2), (0, -36.6, z0 + 1.5 * FH), dark)
# ground floor lobby: separate glass panes (blown in at impact), furniture
HPANES = []
for i in range(8):
    x = -14 + i * 4
    HPANES.append(box("Hotel_Pane_%d" % i, C_H, (3.4, 0.06, 2.9), (x, HY1 - 0.6, z0 + 1.65), glass))
bpy.data.objects["Hotel_Inside"].scale.z = 1.0
furn_m = simple_mat("M_Furniture", (0.35, 0.22, 0.14), 0.5)
HFURN = [box("Hotel_Sofa_%d" % i, C_H, (2.0, 0.9, 0.8), (-10 + i * 5, -31.5, z0 + 0.6), furn_m, bevel=0.08) for i in range(5)]
sign_m = simple_mat("M_Awning", (0.75, 0.25, 0.18), 0.7)
box("Hotel_Awning", C_H, (12, 2.6, 0.12), (0, HY1 + 1.2, z0 + 3.2), sign_m, rot=(math.radians(-12), 0, 0))

# ================================================================== town
wall_tints = [(0.95, 0.92, 0.82), (0.98, 0.88, 0.62), (0.78, 0.86, 0.92), (0.96, 0.8, 0.72), (0.9, 0.9, 0.9), (0.82, 0.9, 0.78)]
WALLM = [pbr_mat("M_Wall_%d" % i, "yellow_plaster" if i % 2 else "white_plaster_rough_01", 2.5, t) for i, t in enumerate(wall_tints)]
ROOFM = [pbr_mat("M_RoofTile", "clay_roof_tiles", 2.0, (0.9, 0.75, 0.7)), pbr_mat("M_RoofIron", "corrugated_iron", 2.0, (0.75, 0.8, 0.82)),
         pbr_mat("M_RoofIronRust", "corrugated_iron", 2.0, (0.8, 0.55, 0.4))]
win_m = simple_mat("M_Window", (0.03, 0.035, 0.04), 0.15)
door_m = simple_mat("M_Door", (0.3, 0.17, 0.08), 0.6)
def proc_house(name, cx, cy, w, d, h, yaw, wm, rm, c):
    """walls+openings object and a roof object (parented), origin at ground centre"""
    gz = ground(cx, cy) - 0.3
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v_ in bm.verts: v_.co = Vector((v_.co.x * w, v_.co.y * d, (v_.co.z + 0.5) * (h + 0.3)))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    me.materials.append(wm); me.materials.append(win_m); me.materials.append(door_m)
    walls = bpy.data.objects.new(name, me); c.objects.link(walls)
    walls.location = (cx, cy, gz); walls.rotation_euler.z = yaw
    nwin = max(1, int(w / 2.6))
    for side in (1, -1):
        for i in range(nwin):
            x = -w / 2 + (i + 0.5) * w / nwin
            if side == 1 and i == nwin // 2:
                o = box(name + "_door", c, (0.95, 0.08, 2.1), (x, side * d / 2, 1.35), door_m)
            else:
                o = box(name + "_win%d%d" % (side, i), c, (1.0, 0.08, 1.2), (x, side * d / 2, min(h - 0.6, 2.0)), win_m)
            o.parent = walls
    # roof
    oh = 0.5; rh = 0.25 * min(w, d) + 0.4
    vs = [(-w / 2 - oh, -d / 2 - oh, 0), (w / 2 + oh, -d / 2 - oh, 0), (w / 2 + oh, d / 2 + oh, 0), (-w / 2 - oh, d / 2 + oh, 0),
          (-w / 2 - oh, 0, rh), (w / 2 + oh, 0, rh)]
    fs = [(0, 1, 5, 4), (3, 4, 5, 2), (0, 4, 3), (1, 2, 5), (0, 3, 2, 1)]
    roof = mesh_obj(name + "_roof", vs, fs, c, [rm]); roof.parent = walls; roof.location = (0, 0, h + 0.3)
    sol = roof.modifiers.new("sol", 'SOLIDIFY'); sol.thickness = 0.12
    return walls, roof
HOUSES = []
occupied = []
def free(x, y, rad):
    if -25 < x < 25 and y > -52: return False
    if abs(x + 44) < 22 and abs(y + 162) < 22: return False
    if any(abs(x - rx) < 3.5 + rad for rx in ROADS_X) or any(abs(y - ry) < 3.5 + rad for ry in ROADS_Y): return False
    return all((x - ox) ** 2 + (y - oy) ** 2 > (rad + orad + 1.5) ** 2 for ox, oy, orad in occupied)
attempts = 0
while len(HOUSES) < 150 and attempts < 6000:
    attempts += 1
    x = random.uniform(-230, 230); y = random.uniform(-340, -50)
    kind = random.random()
    rad = 5.5 if kind < 0.12 else (4.8 if kind < 0.2 else random.uniform(3.6, 5.0))
    if not free(x, y, rad): continue
    occupied.append((x, y, rad))
    near_road = min(ROADS_X, key=lambda rx: abs(rx - x))
    yaw = math.radians(90 if x > near_road else -90) if random.random() < 0.5 else math.radians(random.choice([0, 180]))
    yaw += math.radians(random.uniform(-4, 4))
    n = "House_%03d" % len(HOUSES)
    if kind < 0.12:
        o = inst(house, n, C_TOWN, (x, y, ground(x, y) - 0.15), (0, 0, yaw), 0.9); roof = None
    elif kind < 0.2:
        o = inst(house2, n, C_TOWN, (x, y, ground(x, y) - 0.15), (0, 0, yaw), 0.95); roof = None
    else:
        w_ = rad * 1.4; d_ = rad * random.uniform(1.1, 1.4); h_ = random.choice([3.0, 3.2, 3.4, 6.2])
        o, roof = proc_house(n, x, y, w_, d_, h_, yaw, random.choice(WALLM), random.choice(ROOFM), C_TOWN)
    o["hx"], o["hy"], o["rad"] = x, y, rad
    HOUSES.append(o)
# parked cars along the beach road and town streets
CARS = []
for i, (x, y, yaw) in enumerate([(26, -22.5, 90), (-30, -25.5, -90), (52, -22.6, 92), (-52, -22.4, 88), (34, -60, 0), (80, -100, 180),
                                 (-24, -110, 2), (34, -150, 178), (-62, -90, 0), (80, -160, 1), (6, -72, 90), (-90, -72.5, -90)]):
    lib = car if i % 2 == 0 else car2
    o = inst(lib, "Car_%02d" % i, C_TOWN, (x + (2.5 if i % 3 == 0 else 0), y, ground(x, y) + 0.08 + 0.1), (0, 0, math.radians(yaw)))
    CARS.append(o)
# rubble piles: hidden below ground, rise after the flood (keyed in 03)
RUB = []
for i, hs in enumerate(HOUSES):
    lib = (rub_roof, rub_brick, rub_wood)[i % 3]
    o = inst(lib, "Rubble_%03d" % i, C_TOWN, (hs["hx"] + random.uniform(-2, 2), hs["hy"] + random.uniform(-3, 1), ground(hs["hx"], hs["hy"]) - 3.0),
             (0, 0, random.uniform(0, 6.28)), random.uniform(0.9, 1.5))
    RUB.append(o)
for i in range(220):  # extra scattered debris (planks / iron sheets) for the aftermath
    x = random.uniform(-200, 200); y = random.uniform(-330, -20)
    lib = (rub_wood, rub_brick)[i % 2]
    inst(lib, "Debris_%02d" % i, C_TOWN, (x, y, ground(x, y) - 2.5), (0, 0, random.uniform(0, 6.28)), random.uniform(0.6, 1.2))
iron = bpy.data.materials["M_RoofIronRust"]
for i in range(120):
    x = random.uniform(-200, 200); y = random.uniform(-330, -20)
    box("Sheet_%02d" % i, C_TOWN, (2.4, 1.0, 0.03), (x, y, ground(x, y) - 2.0), iron, rot=(random.uniform(-0.4, 0.4), random.uniform(-0.4, 0.4), random.uniform(0, 6.28)))

# ================================================================== diorama under the sea (explainer bowl)
DC = Vector((0, 470, -36))
bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=25, location=DC)
bowl = bpy.context.active_object; bowl.name = "StudioBowl"; link(bowl, C_D)
for p in bowl.data.polygons: p.use_smooth = True
m, nt = node_mat("M_StudioBowl")
NN, LL = nt.nodes, nt.links
NN.remove(NN["Principled BSDF"])
geo = NN.new("ShaderNodeNewGeometry"); tc = NN.new("ShaderNodeTexCoord"); sp = NN.new("ShaderNodeSeparateXYZ"); LL.new(tc.outputs["Object"], sp.inputs["Vector"])
mr = NN.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = -18; mr.inputs["From Max"].default_value = 20; LL.new(sp.outputs["Z"], mr.inputs["Value"])
cr = NN.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (0.18, 0.62, 0.78, 1); cr.color_ramp.elements[1].color = (0.92, 0.97, 1.0, 1)
LL.new(mr.outputs["Result"], cr.inputs["Fac"])
em = NN.new("ShaderNodeEmission"); LL.new(cr.outputs["Color"], em.inputs["Color"]); em.inputs["Strength"].default_value = 1.0
tr = NN.new("ShaderNodeBsdfTransparent")
ms = NN.new("ShaderNodeMixShader"); LL.new(geo.outputs["Backfacing"], ms.inputs["Fac"]); LL.new(tr.outputs[0], ms.inputs[1]); LL.new(em.outputs[0], ms.inputs[2])
LL.new(ms.outputs[0], NN["Material Output"].inputs["Surface"])
bowl.data.materials.append(m)
bowl.visible_shadow = False
# the cross-section block: camera looks +X at the section face (x = -3); screen right = shore (-Y)
oce = pbr_mat("M_OceanCrust", "mud_cracked_dry_03", 1.2, (0.28, 0.3, 0.34))
con = pbr_mat("M_ContCrust", "red_laterite_soil_stones", 1.2, (0.95, 0.75, 0.55))
mant = simple_mat("M_Mantle", (0.6, 0.18, 0.05), 0.7, emit=((1.0, 0.32, 0.06), 1.2))
fault_m = simple_mat("M_FaultGlow", (1, 0.5, 0.1), 0.5, emit=((1.0, 0.55, 0.1), 0.0))
arrow_m = simple_mat("M_Arrow", (1.0, 0.75, 0.2), 0.4, emit=((1.0, 0.7, 0.15), 2.0))
wcol, nt = node_mat("M_WaterColumn")
b_ = nt.nodes["Principled BSDF"]; b_.inputs["Base Color"].default_value = (0.2, 0.55, 0.8, 1); b_.inputs["Alpha"].default_value = 0.5
b_.inputs["Roughness"].default_value = 0.15; b_.inputs["Emission Color"].default_value = (0.15, 0.45, 0.7, 1); b_.inputs["Emission Strength"].default_value = 0.25
D = DC
def prism(name, poly, mat, x0=-3.0, x1=3.0, c=C_D, ny=1):
    n = len(poly)
    vs = [(x0, D.y + dy, D.z + z) for dy, z in poly] + [(x1, D.y + dy, D.z + z) for dy, z in poly]
    fs = [tuple(range(n))[::-1], tuple(range(n, 2 * n))] + [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    o = mesh_obj(name, vs, fs, c, [mat]); return o
def plate_top(dy):   # top of the oceanic plate
    return -2.6 - 0.32 * max(0, 2 - dy) - 0.05 * max(0, dy - 2) if dy < 10 else -2.2
mantle = prism("D_Mantle", [(-10, -11), (10, -11), (10, -7.0), (-10, -7.0)], mant)
op = [(dy, plate_top(dy)) for dy in np.linspace(10, -10, 21)]
ocean_plate = prism("D_OceanPlate", op + [(dy, z - 1.8) for dy, z in op[::-1]], oce)
cont = prism("D_ContPlate", [(-10, -0.8), (-3, -0.8), (-3, plate_top(-3)), (-10, plate_top(-10))], con)
tip_poly = [(-3, -0.8 - 0.0), (-3, plate_top(-3))] + [(dy, plate_top(dy)) for dy in np.linspace(-2.5, 2.0, 6)] + [(2.0, plate_top(2.0) + 0.3), (0.0, -1.3), (-1.5, -1.0)]
tip = prism("D_Tip", [(dy + 3.0, z + 0.8) for dy, z in tip_poly], con)    # local coords relative to the hinge at dy -3, z -0.8
tip.location = (0, -3.0, -0.8)
for v_ in tip.data.vertices: v_.co.y -= D.y; v_.co.z -= D.z
tip.location = (0, D.y - 3.0, D.z - 0.8); tip.data.update()
fault = prism("D_Fault", [(dy, plate_top(dy) + 0.06) for dy in np.linspace(-6, 2.5, 8)] + [(dy, plate_top(dy) - 0.06) for dy in np.linspace(2.5, -6, 8)], fault_m, x0=-3.06, x1=3.06)
seab = [(dy, (plate_top(dy) if dy > 2.0 else (-0.8 if dy < -3 else -1.2))) for dy in np.linspace(10, -10, 41)]
NY = 160
bpy.ops.mesh.primitive_grid_add(x_subdivisions=6, y_subdivisions=NY, size=1, location=(D.x, D.y, D.z + 2.6))
wtop = bpy.context.active_object; wtop.name = "D_WaterTop"; link(wtop, C_D); wtop.scale = (6, 20, 1)
bpy.ops.object.transform_apply(scale=True)
wtop.data.materials.append(wcol)
wbody = prism("D_WaterBody", [(10, 2.58), (-10, 2.58)] + [(dy, z + 0.02) for dy, z in seab[::-1]][::-1][::-1], wcol)
wtop.shape_key_add(name="Basis")
for nm, cen in (("Bulge", [0.0]), ("SplitA", [-6.0]), ("SplitB", [6.0])):
    k = wtop.shape_key_add(name=nm, from_mix=False)
    co = np.zeros(len(wtop.data.vertices) * 3); k.data.foreach_get("co", co); co = co.reshape(-1, 3)
    for c0 in cen:
        co[:, 2] += 1.6 * np.exp(-((co[:, 1] - c0) / 2.2) ** 2) * (1.0 if nm == "Bulge" else 0.75)
    k.data.foreach_set("co", co.ravel())
for p in wtop.data.polygons: p.use_smooth = True
# arrows on the section face: oceanic plate pushing under the continent
def arrow(name, a, b_, w=0.35):
    a = Vector(a); b_ = Vector(b_); d = (b_ - a); L_ = d.length; d.normalize(); nrm = Vector((-d.y, d.x))
    pts = [a + nrm * w * 0.5, a + d * (L_ - 1.0) + nrm * w * 0.5, a + d * (L_ - 1.0) + nrm * w * 1.4, b_, a + d * (L_ - 1.0) - nrm * w * 1.4,
           a + d * (L_ - 1.0) - nrm * w * 0.5, a - nrm * w * 0.5]
    vs = [(-3.08, D.y + p_.x, D.z + p_.y) for p_ in pts]
    return mesh_obj(name, vs, [tuple(range(len(vs)))], C_D, [arrow_m])
arrow("D_ArrowOcean", (8.5, -3.8), (3.5, -4.9)); arrow("D_ArrowCont", (-8.5, -2.2), (-5.0, -2.2), 0.3)

# little seabed props on the cross-section (rocks) and studio lights
for i in range(10):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.25, location=(D.x + random.uniform(-2.5, 2.5), D.y + random.uniform(-8, 8), D.z - 2.0 + random.uniform(-0.1, 0.4)))
    o = bpy.context.active_object; o.name = "D_Chunk_%d" % i; link(o, C_D); o.data.materials.append(oce)
for nm, loc, en, sz in (("D_Key", (-14, 460, -24), 9000, 8), ("D_Fill", (-10, 486, -32), 3000, 8), ("D_Top", (0, 470, -16), 4000, 10)):
    ld = bpy.data.lights.new(nm, 'AREA'); ld.energy = en; ld.size = sz; ld.color = (1, 0.98, 0.95)
    lo = bpy.data.objects.new(nm, ld); C_D.objects.link(lo); lo.location = loc
    dirv = (DC - Vector(loc)); lo.rotation_euler = dirv.to_track_quat('-Z', 'Y').to_euler()

# ================================================================== FX placeholders: spray puffs + dust volume
spray_m, nt = node_mat("M_Spray")
NN, LL = nt.nodes, nt.links; NN.remove(NN["Principled BSDF"])
vol = NN.new("ShaderNodeVolumePrincipled"); vol.inputs["Color"].default_value = (0.95, 0.97, 1.0, 1)
nz = NN.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.6; nz.inputs["Detail"].default_value = 4
rmp = NN.new("ShaderNodeMapRange"); rmp.inputs["From Min"].default_value = 0.45; rmp.inputs["From Max"].default_value = 0.7; rmp.inputs["To Max"].default_value = 1.5
LL.new(nz.outputs["Fac"], rmp.inputs["Value"]); LL.new(rmp.outputs["Result"], vol.inputs["Density"])
LL.new(vol.outputs[0], NN["Material Output"].inputs["Volume"])
dust_m, nt = node_mat("M_Dust")
NN, LL = nt.nodes, nt.links; NN.remove(NN["Principled BSDF"])
vol = NN.new("ShaderNodeVolumePrincipled"); vol.inputs["Color"].default_value = (1.0, 0.85, 0.65, 1); vol.inputs["Density"].default_value = 0.0
vol.name = "DUSTVOL"; vol.inputs["Anisotropy"].default_value = 0.6
LL.new(vol.outputs[0], NN["Material Output"].inputs["Volume"])
dust = box("DustVolume", C_FX, (500, 420, 40), (0, -160, 20), dust_m)

bpy.ops.wm.save_as_mainfile(filepath=out)
print("SCENE_DONE", len(HOUSES), "houses", len(PALMS), "palms")
