# Part of 03_animate.py (exec'd): x-ray explainer, time-lapse light, sparks/cutter, ambient life, the one continuous camera.
import random
random.seed(91)
W = sc.world; WN = W.node_tree.nodes
def kv(sock, f, v):
    sock.default_value = v; sock.keyframe_insert("default_value", frame=f)
# ---------------------------------------------------------------- x-ray (505-540 in, 905-955 out)
XR = [(1, 0), (492, 0), (520, 1), (905, 1), (952, 0)]
for mn in ("BinSteel", "BinSteelInner", "MechSteel"):
    m = bpy.data.materials[mn]; v = m.node_tree.nodes["XRAY"].outputs[0]
    for f, x in XR: kv(v, f, x)
for f, x in XR: kv(WN["STUDIO_MIX"].inputs['Fac'], f, x)
SUN = bpy.data.objects["Sun"].data; FILL = bpy.data.objects["BinFill"].data; SLOT = bpy.data.objects["SlotBeam"].data; STK = bpy.data.objects["StudioKey"].data
def kl(L, f, e, col=None):
    L.energy = e; L.keyframe_insert("energy", frame=f)
    if col: L.color = col; L.keyframe_insert("color", frame=f)
def kw(f, s): kv(WN["BG_HDRI"].inputs['Strength'], f, s)
def kex(f, e): sc.view_settings.exposure = e; sc.view_settings.keyframe_insert("exposure", frame=f)
DAY = (1.0, 0.95, 0.88)
for f, sun, fill, slot, stk, w_, ex, col, scol in (
        (1, 3.2, 3, 120, 0, 1.0, 0.0, DAY, (1, .93, .8)), (290, 3.2, 3, 120, 0, 1.0, 0.0, DAY, (1, .93, .8)),
        (330, 3.2, 14, 22, 0, 1.0, 0.55, DAY, (1, .93, .8)),                    # flap shut: only the slit leaks light; eyes adjust
        (505, 3.2, 14, 22, 0, 1.0, 0.55, DAY, (1, .93, .8)), (538, 1.0, 0, 0, 350, 0.3, 0.0, DAY, (1, .93, .8)),
        (905, 1.0, 0, 0, 350, 0.3, 0.0, DAY, (1, .93, .8)), (952, 3.2, 14, 22, 0, 1.0, 0.55, DAY, (1, .93, .8)),
        (1395, 3.2, 14, 22, 0, 1.0, 0.55, DAY, (1, .93, .8)), (1410, 3.2, 3, 22, 0, 1.0, 0.0, DAY, (1, .93, .8)),
        (1495, 3.2, 3, 22, 0, 1.0, 0.0, DAY, (1, .93, .8)), (1530, 3.2, 14, 22, 0, 1.0, 0.55, DAY, (1, .93, .8)),
        # time-lapse: day -> dusk -> night -> dawn -> day -> night -> day
        (1580, 2.0, 6, 30, 0, 0.6, 0.3, (1.0, 0.55, 0.3), (1, .55, .3)), (1620, 0.05, 2.5, 10, 0, 0.06, 0.6, (0.4, 0.5, 1.0), (0.45, 0.55, 1)),
        (1670, 0.05, 2.5, 10, 0, 0.06, 0.6, (0.4, 0.5, 1.0), (0.45, 0.55, 1)), (1705, 1.8, 6, 30, 0, 0.5, 0.3, (1.0, 0.7, 0.5), (1, .7, .5)),
        (1740, 3.2, 14, 22, 0, 1.0, 0.55, DAY, (1, .93, .8)), (1770, 0.05, 2.5, 10, 0, 0.06, 0.6, (0.4, 0.5, 1.0), (0.45, 0.55, 1)),
        (1810, 3.2, 14, 22, 0, 1.0, 0.55, DAY, (1, .93, .8)), (1860, 3.2, 3, 22, 0, 1.0, 0.0, DAY, (1, .93, .8)),
        (2070, 3.2, 3, 22, 0, 1.0, 0.0, DAY, (1, .93, .8)), (2095, 3.2, 3, 22, 0, 1.0, 0.0, DAY, (1, .93, .8))):
    kl(SUN, f, sun, col); kl(FILL, f, fill); kl(SLOT, f, slot, scol); kl(STK, f, stk); kw(f, w_); kex(f, ex)
for c_ in (SUN, FILL, SLOT, STK):
    if c_.animation_data and c_.animation_data.action:
        pass
# the sun's shadows sweep during the time-lapse
so = bpy.data.objects["Sun"]
for f, rz in ((1530, -160), (1620, -100), (1700, -210), (1770, -130), (1820, -165)):
    so.rotation_euler.z = R_(rz); so.keyframe_insert("rotation_euler", index=2, frame=f)

# ---------------------------------------------------------------- rotary cutter, cut line glow, sparks (1985-2060)
def emis(name, rgb, s):
    m = bpy.data.materials.new(name); m.use_nodes = True; p = m.node_tree.nodes["Principled BSDF"]
    p.inputs['Base Color'].default_value = rgb + (1,); p.inputs['Emission Color'].default_value = rgb + (1,); p.inputs['Emission Strength'].default_value = s
    return m
M_SPARK = emis("Spark", (1.0, 0.6, 0.18), 40.0); M_CUT = emis("CutGlow", (1.0, 0.45, 0.1), 25.0)
col_fx = bpy.data.collections.new("FX"); sc.collection.children.link(col_fx)
bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.115, depth=0.006, location=(0, 0, 0))
disc = bpy.context.object; disc.name = "CutterDisc"
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.2, 0.02)); body = bpy.context.object; body.name = "CutterBody"; body.scale = (0.09, 0.32, 0.11)
for o in (disc, body):
    for c_ in o.users_collection: c_.objects.unlink(o)
    col_fx.objects.link(o)
disc.data.materials.append(bpy.data.materials["MechSteel"].copy()); disc.active_material.name = "CutterDiscMat"
body.data.materials.append(bpy.data.materials.new("CutterOrange")); body.active_material.use_nodes = True
body.active_material.node_tree.nodes["Principled BSDF"].inputs['Base Color'].default_value = (0.8, 0.25, 0.03, 1)
body.parent = disc; disc.rotation_euler = (0, R_(90), 0)
body.location = (0, -0.2, 0.0); body.rotation_euler = (0, R_(-90), 0)
for f in [1960] + list(range(1976, 2071, 3)) + [2100]:
    c = cutter_pos(f); disc.location = c + Vector((0, -0.01, 0)); disc.keyframe_insert("location", frame=f)
for o in (disc, body):
    for f_, h_ in ((1, True), (1975, False), (2062, True)):
        o.hide_render = h_; o.keyframe_insert("hide_render", frame=f_)
cutl = bpy.data.objects.new("CutLine", bpy.data.meshes.new("CutLine")); col_fx.objects.link(cutl)
import bmesh as _bm
p0, p1 = cutter_pos(1985), cutter_pos(1985 + 49)
cbm = _bm.new(); _bm.ops.create_cube(cbm, size=1.0); cbm.to_mesh(cutl.data); cbm.free()
cutl.data.transform(Matrix.Translation(Vector((0.5, 0, 0)))); cutl.data.transform(Matrix.Diagonal((1.0, 0.006, 0.008, 1.0)))
cutl.data.materials.append(M_CUT); cutl.location = p0 + Vector((0, 0.05, 0))
for f, sx in ((1984, 0.001), (2034, (p1 - p0).length), (2100, (p1 - p0).length)):
    cutl.scale = (sx, 1, 1); cutl.keyframe_insert("scale", frame=f)
for f_, h_ in ((1, True), (1985, False), (2090, True)):
    cutl.hide_render = h_; cutl.keyframe_insert("hide_render", frame=f_)
sp_me = bpy.data.meshes.new("SparkMesh"); bm = _bm.new(); _bm.ops.create_cube(bm, size=1.0); bm.to_mesh(sp_me); bm.free()
sp_me.transform(Matrix.Diagonal((0.004, 0.004, 0.06, 1.0)).to_4x4() if False else Matrix.Diagonal((0.004, 0.004, 0.06, 1.0)))
sp_me.materials.append(M_SPARK)
for i in range(70):
    s = bpy.data.objects.new("Spark%02d" % i, sp_me); col_fx.objects.link(s); s.rotation_mode = 'QUATERNION'
    s.scale = (0, 0, 0); s.keyframe_insert("scale", frame=1)
    f = 1985 + random.randint(0, 9)
    while f < 2056:
        life = random.randint(8, 14); o = cutter_pos(f) + Vector((0, -0.02, 0))
        v = Vector((random.uniform(-0.6, 1.2), random.uniform(-3.0, -1.2), random.uniform(0.2, 1.8)))
        for k in range(0, life + 1, max(1, life // 3)):
            t = k / 60.0; p = o + v * t + Vector((0, 0, -4.9 * t * t))
            if p.z < 0.01: p.z = 0.01 + abs(p.z) * 0.3
            vel = v + Vector((0, 0, -9.8 * t))
            s.location = p; s.keyframe_insert("location", frame=f + k)
            s.rotation_quaternion = vel.to_track_quat('Z', 'Y'); s.keyframe_insert("rotation_quaternion", frame=f + k)
            sc_ = 1.0 - 0.5 * k / life
            s.scale = (sc_, sc_, sc_ * (1 + vel.length * 0.3)); s.keyframe_insert("scale", frame=f + k)
        s.scale = (0, 0, 0); s.keyframe_insert("scale", frame=f + life + 1)
        f += life + random.randint(1, 4)
        s.keyframe_insert("scale", frame=f - 1)
spl_d = bpy.data.lights.new("SparkLight", 'POINT'); spl_d.color = (1, 0.6, 0.25); spl_d.shadow_soft_size = 0.05
spl = bpy.data.objects.new("SparkLight", spl_d); col_fx.objects.link(spl)
for f in range(1976, 2070, 3):
    spl.location = cutter_pos(f) + Vector((0, -0.15, 0.05)); spl.keyframe_insert("location", frame=f)
    spl_d.energy = (0 if f < 1985 or f > 2056 else 60 + 40 * random.random()); spl_d.keyframe_insert("energy", frame=f)
# daylight floods in once the panel opens
for f, e in ((2070, 3), (2095, 25), (2200, 8)):
    kl(FILL, f, e)

# ---------------------------------------------------------------- ambient life
rat = bpy.data.objects["street_rat"]
for f, loc, rz in ((1, (-3.6, 0.85, 0.12), -90), (30, (-3.6, 0.85, 0.12), -90), (110, (-0.9, 0.85, 0.12), -90), (130, (-0.9, 0.85, 0.12), -90), (131, (-6, 0.85, 0.12), -90),
                   (1400, (-6.0, 0.85, 0.12), -90), (1480, (-2.0, 0.85, 0.12), -90), (1500, (-1.6, 0.85, 0.12), -70), (1501, (-8, 0.9, 0.12), -90), (2300, (-8.0, 0.9, 0.12), -90), (2490, (-4.0, 0.9, 0.12), -90)):
    rat.location = loc; rat.keyframe_insert("location", frame=f); rat.rotation_euler.z = R_(rz); rat.keyframe_insert("rotation_euler", index=2, frame=f)
for i, nm in enumerate(sc["leaves"].split(",")[:14]):
    lf = bpy.data.objects[nm]; p = lf.location.copy()
    for f in range(1, 2491, 60):
        gust = 0.6 * (0.5 + 0.5 * math.sin(f / 90.0 + i))
        p = p + Vector((-0.4 * gust - 0.1, 0.15 * math.sin(f / 37.0 + i), 0))
        if p.x < -6: p.x += 10
        lf.location = (p.x, p.y, 0.004 + 0.06 * gust * abs(math.sin(f / 20.0 + i))); lf.keyframe_insert("location", frame=f)
        lf.rotation_euler = (0.5 * gust * math.sin(f + i), 0.4 * gust, lf.rotation_euler.z + gust * 2.0); lf.keyframe_insert("rotation_euler", frame=f)
pb = bpy.data.objects["PaperBag"]
for f, loc, rot in ((1, (1.5, -2.6, 0.02), (0, 0, 0)), (150, (0.2, -2.8, 0.05), (0.4, 0.2, 2.0)), (300, (-1.4, -2.4, 0.02), (0, 0.3, 3.5)),
                    (1400, (2.5, -3.5, 0.02), (0, 0, 1)), (1450, (1.0, -3.2, 0.25), (1.2, 0.6, 3)), (1500, (-0.6, -3.4, 0.05), (0.3, 1.5, 5)), (1900, (-2.5, -3.0, 0.02), (0, 0, 6))):
    pb.location = loc; pb.keyframe_insert("location", frame=f); pb.rotation_euler = rot; pb.keyframe_insert("rotation_euler", frame=f)
# a car passes far away during the scream (nobody stops)
car = bpy.data.objects["covered_car"]
pc = car.copy(); pc.name = "PassingCar"; bpy.data.collections["SET"].objects.link(pc)
for ch in car.children:
    d = ch.copy(); bpy.data.collections["SET"].objects.link(d); d.parent = pc
for f, x in ((1, 30), (1420, 18), (1500, -10), (1501, 40)):
    pc.location = (x, -13.5, car.location.z); pc.rotation_euler.z = R_(-90); pc.keyframe_insert("location", frame=f)
for fc in (pc.animation_data.action.layers[0].strips[0].channelbags[0].fcurves if hasattr(pc.animation_data.action, "layers") else []):
    for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
# dust motes inside the bin (drift in the beam)
mm = emis("Mote", (1.0, 0.95, 0.85), 3.0)
mote_me = bpy.data.meshes.new("Mote"); bm = _bm.new(); _bm.ops.create_icosphere(bm, subdivisions=1, radius=0.0025); bm.to_mesh(mote_me); bm.free(); mote_me.materials.append(mm)
for i in range(60):
    mo = bpy.data.objects.new("Mote%02d" % i, mote_me); col_fx.objects.link(mo)
    base = Vector((random.uniform(-0.6, 0.6), random.uniform(-0.5, 0.5), random.uniform(0.6, 1.9)))
    for f in range(280, 1850, 90):
        mo.location = base + Vector((0.08 * math.sin(f / 70.0 + i), 0.08 * math.cos(f / 53.0 + i * 2), 0.05 * math.sin(f / 41.0 + i))); mo.keyframe_insert("location", frame=f)
    for f_, h_ in ((1, True), (280, False), (1850, True)):
        mo.hide_render = h_; mo.keyframe_insert("hide_render", frame=f_)
# blanket around her (beat 11): a copy of her torso + arms skin, masked by bone weights and inflated, in grey wool
WB = bpy.data.objects["Woman.body"]
bl = WB.copy(); bl.data = WB.data.copy(); bl.name = "Blanket"; col_fx.objects.link(bl)
keep = [g.index for g in bl.vertex_groups if g.name.split(".")[0] in ("spine01", "spine02", "spine03", "spine04", "clavicle", "shoulder01",
                                                                  "upperarm01", "upperarm02", "lowerarm01", "lowerarm02", "breast", "neck01")]
vg = bl.vertex_groups.new(name="BlanketMask")
for v in bl.data.vertices:
    w = sum(g.weight for g in v.groups if g.group in keep)
    if w > 0.5: vg.add([v.index], 1.0, 'REPLACE')
for m in list(bl.modifiers):
    if m.type not in ('ARMATURE',): bl.modifiers.remove(m)
mk = bl.modifiers.new("mask", 'MASK'); mk.vertex_group = "BlanketMask"
dp = bl.modifiers.new("puff", 'DISPLACE'); dp.strength = 0.035; dp.mid_level = 0.0
tx = bpy.data.textures.new("folds", 'CLOUDS'); tx.noise_scale = 0.12; dp.texture = tx; dp.texture_coords = 'OBJECT'
dp2 = bl.modifiers.new("inflate", 'DISPLACE'); dp2.strength = 0.03; dp2.mid_level = 0.0
smo = bl.modifiers.new("smooth", 'SMOOTH'); smo.factor = 1.0; smo.iterations = 8
sol = bl.modifiers.new("thick", 'SOLIDIFY'); sol.thickness = 0.008
sub = bl.modifiers.new("sub", 'SUBSURF'); sub.levels = 0; sub.render_levels = 1
bl.data.materials.clear()
bm_ = bpy.data.materials["terry_cloth"].copy(); bm_.name = "BlanketMat"; bl.data.materials.append(bm_)
for poly in bl.data.polygons: poly.material_index = 0
for nd in bm_.node_tree.nodes:
    if nd.type == 'BSDF_PRINCIPLED':
        for lk in list(nd.inputs['Base Color'].links): bm_.node_tree.links.remove(lk)
        nd.inputs['Base Color'].default_value = (0.34, 0.33, 0.31, 1)
for f_, h_ in ((1, True), (2150, False)):
    bl.hide_render = h_; bl.keyframe_insert("hide_render", frame=f_)
    bl.hide_viewport = h_; bl.keyframe_insert("hide_viewport", frame=f_)

# ---------------------------------------------------------------- the one continuous camera
cam_d = bpy.data.cameras.new("CAM_Film"); cam_d.sensor_fit = 'AUTO'; cam_d.clip_start = 0.02; cam_d.clip_end = 200
cam = bpy.data.objects.new("CAM_Film", cam_d); sc.collection.objects.link(cam); sc.camera = cam
cam_d.dof.use_dof = True; cam_d.dof.aperture_fstop = 5.6
CAMK = [  # frame, location, target, lens
    (1, (-3.2, -5.6, 0.35), (0.0, -0.8, 1.0), 18), (60, (-1.7, -3.5, 0.75), (0.0, -0.85, 1.1), 22), (110, (-0.95, -2.1, 1.45), (0.05, -0.65, 1.25), 26),
    (150, (-0.55, -1.85, 1.9), (0.0, -0.8, 1.15), 28),
    (168, (0.9, -2.0, 1.85), (-0.05, -1.15, 1.1), 24), (200, (0.45, -1.25, 1.8), (0.0, -0.55, 1.3), 22), (240, (0.06, -1.0, 1.5), (0.0, -0.3, 1.2), 20),
    (268, (0.0, -0.74, 1.40), (0.0, 0.0, 0.85), 18), (288, (0.02, -0.42, 1.36), (0.05, 0.1, 0.4), 18),
    (302, (0.15, -0.1, 1.2), (0.05, 0.1, 0.35), 18), (330, (0.35, 0.10, 1.05), (0.0, -0.58, 1.35), 20), (380, (-0.4, -0.35, 1.25), (0.1, 0.1, 0.45), 20),
    (440, (-0.5, 0.2, 0.95), (0.1, 0.05, 0.5), 22), (470, (-0.05, 0.48, 1.6), (0.05, -0.1, 0.75), 22), (495, (0.62, -0.15, 0.95), (0.0, -0.2, 0.85), 22),
    (540, (1.25, -0.2, 1.05), (0.0, -0.3, 1.1), 24), (600, (2.1, -0.9, 1.5), (0.0, -0.5, 1.3), 30), (680, (2.3, 0.3, 1.75), (0.0, -0.45, 1.3), 30),
    (760, (1.6, -1.6, 1.6), (0.0, -0.55, 1.28), 35),
    (805, (0.9, -1.05, 1.28), (0.0, -0.62, 1.16), 45), (835, (0.35, -0.92, 1.02), (0.0, -0.63, 1.14), 55), (870, (-0.35, -1.0, 1.25), (0.1, -0.62, 1.15), 55), (905, (0.75, -1.25, 1.4), (0.0, -0.6, 1.25), 45),
    (952, (0.95, -0.35, 1.3), (0.0, -0.1, 1.0), 26), (962, (0.62, -0.25, 1.35), (-0.4, -0.1, 1.2), 22),
    (990, (0.45, -0.05, 1.45), (-0.74, -0.05, 1.3), 20), (1030, (0.05, 0.45, 1.2), (-0.72, -0.05, 1.35), 20), (1070, (-0.25, 0.45, 1.05), (-0.72, -0.1, 1.4), 20), (1125, (0.45, 0.35, 1.25), (0.0, -0.58, 1.3), 20),
    (1180, (0.4, -0.35, 0.75), (0.0, 0.55, 1.4), 18), (1230, (0.35, -0.4, 1.1), (0.0, 0.5, 1.85), 16), (1275, (0.25, -0.35, 1.75), (0.0, 0.45, 1.6), 16),
    (1305, (0.35, -0.25, 1.95), (0.0, 0.15, 0.45), 16),
    (1340, (0.12, -0.40, 1.75), (0.0, 0.0, 1.68), 28), (1380, (0.08, -0.5, 1.62), (0.0, 0.05, 1.68), 32), (1404, (0.0, -0.72, 1.45), (0.0, 0.0, 1.4), 26),
    (1440, (0.5, -2.9, 1.6), (0.0, -0.5, 1.1), 20), (1490, (-1.5, -5.6, 2.3), (0.0, -1.0, 0.9), 18),
    (1540, (0.0, -1.5, 2.6), (0.0, -0.4, 1.3), 24), (1572, (0.0, -0.78, 1.40), (0.0, 0.0, 0.6), 20), (1600, (0.0, -0.3, 1.38), (0.05, 0.1, 0.3), 18),
    (1680, (0.3, 0.1, 1.95), (0.05, 0.05, 0.3), 22), (1760, (-0.3, 0.25, 1.95), (0.05, 0.05, 0.3), 26), (1830, (-0.2, -0.3, 1.9), (0.05, 0.05, 0.35), 30),
    (1862, (0.0, -0.3, 1.45), (0.05, 0.1, 0.4), 20), (1880, (0.0, -0.72, 1.45), (1.3, -1.7, 1.5), 22), (1905, (0.1, -0.98, 1.5), (1.1, -1.5, 1.5), 24), (1932, (0.0, -1.0, 1.65), (0.7, -1.18, 1.5), 26),
    (1965, (0.0, -2.2, 1.5), (0.6, -1.0, 1.2), 24),
    (1995, (-1.6, -1.95, 0.8), (-0.2, -0.65, 0.9), 26), (2030, (-0.4, -2.05, 0.6), (0.2, -0.65, 0.85), 24), (2060, (-0.2, -2.0, 0.95), (0.1, -0.6, 0.7), 24),
    (2086, (-0.15, -1.7, 1.25), (0.0, 0.0, 0.6), 20),
    (2110, (-0.35, -1.45, 0.95), (0.0, -0.5, 0.8), 20), (2160, (0.3, -2.6, 1.35), (-0.2, -1.2, 1.1), 24), (2210, (0.2, -3.5, 1.6), (-0.5, -1.8, 1.1), 24),
    (2265, (1.6, -4.6, 2.4), (0.3, -1.4, 1.0), 22), (2345, (3.0, -6.6, 3.6), (2.4, 0.0, 1.0), 20), (2420, (3.9, -7.6, 4.2), (3.0, 0.3, 1.0), 21),
    (2490, (5.0, -8.4, 4.6), (3.6, 0.3, 0.9), 23)]
sc["cam_keys"] = json.dumps(CAMK)
cl = catmull([(k[0], Vector(k[1])) for k in CAMK]); ct = catmull([(k[0], Vector(k[2])) for k in CAMK]); cln = pchip([(k[0], float(k[3])) for k in CAMK])
qprev = None
for f in range(1, 2491):
    p, t = cl(f), ct(f)
    cam.location = p; cam.keyframe_insert("location", frame=f)
    q = (t - p).to_track_quat('-Z', 'Y'); cam.rotation_mode = 'QUATERNION'
    if qprev is not None and q.dot(qprev) < 0: q = -q
    qprev = q.copy(); cam.rotation_quaternion = q; cam.keyframe_insert("rotation_quaternion", frame=f)
    cam_d.lens = cln(f); cam_d.keyframe_insert("lens", frame=f)
    cam_d.dof.focus_distance = (t - p).length; cam_d.dof.keyframe_insert("focus_distance", frame=f)
# flip-safe quaternions
fcs = [fc for fc in cam.animation_data.action.layers[0].strips[0].channelbags[0].fcurves if fc.data_path == "rotation_quaternion"]
print("FX_CAMERA_DONE", len(CAMK))

# ---------------------------------------------------------------- firefighter turnout gear + helmets
for nm in ("FireA", "FireB"):
    rig = bpy.data.objects[nm]
    for ch in rig.children:
        if "worksuit" in ch.name:
            for m in ch.data.materials:
                nt = m.node_tree; pr = next(x for x in nt.nodes if x.type == 'BSDF_PRINCIPLED')
                for lk in list(pr.inputs['Base Color'].links): nt.links.remove(lk)
                tcn = nt.nodes.new('ShaderNodeTexCoord'); sepn = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tcn.outputs['Object'], sepn.inputs['Vector'])
                band = nt.nodes.new('ShaderNodeMath'); band.operation = 'PINGPONG'; band.inputs[1].default_value = 0.5
                mz = nt.nodes.new('ShaderNodeMath'); mz.operation = 'MULTIPLY'; mz.inputs[1].default_value = 1.0
                nt.links.new(sepn.outputs['Z'], band.inputs[0])
                rmp = nt.nodes.new('ShaderNodeValToRGB'); cr = rmp.color_ramp; cr.interpolation = 'CONSTANT'
                cr.elements[0].position = 0.0; cr.elements[0].color = (0.42, 0.33, 0.16, 1)
                e = cr.elements[1]; e.position = 0.06; e.color = (0.42, 0.33, 0.16, 1)
                e2 = cr.elements.new(0.035); e2.color = (0.85, 0.9, 0.6, 1)
                e3 = cr.elements.new(0.012); e3.color = (0.42, 0.33, 0.16, 1)
                # bands at hips, chest and the lower legs: distance from band heights
                for hgt in (0.38,):
                    pass
                d1 = nt.nodes.new('ShaderNodeMath'); d1.operation = 'PINGPONG'; d1.inputs[1].default_value = 0.55
                sub = nt.nodes.new('ShaderNodeMath'); sub.operation = 'SUBTRACT'; sub.inputs[1].default_value = 0.0
                nt.links.new(sepn.outputs['Z'], d1.inputs[0]); nt.links.new(d1.outputs[0], rmp.inputs['Fac'])
                nt.links.new(rmp.outputs['Color'], pr.inputs['Base Color'])
                pr.inputs['Roughness'].default_value = 0.75
        if ch.name.split(".")[-1].startswith("short"):
            ch.hide_render = True; ch.keyframe_insert("hide_render", frame=1975)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=1.0)
    hm = bpy.context.object; hm.name = nm + "_Helmet"
    for c_ in hm.users_collection: c_.objects.unlink(hm)
    col_fx.objects.link(hm)
    bmh = _bm.new(); bmh.from_mesh(hm.data)
    _bm.ops.delete(bmh, geom=[v for v in bmh.verts if v.co.z < -0.25], context='VERTS')
    for v in bmh.verts:
        if v.co.z < 0.0: v.co.x *= 1.25; v.co.y *= 1.35 if v.co.y > 0 else 1.15
    bmh.to_mesh(hm.data); bmh.free()
    hm.data.transform(Matrix.Diagonal((0.125, 0.14, 0.12, 1)))
    hm.modifiers.new("t", 'SOLIDIFY').thickness = 0.01
    hmat = bpy.data.materials.new(nm + "_HelmetMat"); hmat.use_nodes = True
    hp = hmat.node_tree.nodes["Principled BSDF"]; hp.inputs['Base Color'].default_value = ((0.02, 0.02, 0.02, 1) if nm == "FireA" else (0.75, 0.6, 0.05, 1)); hp.inputs['Roughness'].default_value = 0.3
    hm.data.materials.append(hmat)
    hm.parent = rig; hm.parent_type = 'BONE'; hm.parent_bone = "head"; hm.matrix_parent_inverse = Matrix.Identity(4)
    hm.location = (0, -0.11 if nm == 'FireB' else -0.14, 0.0); hm.rotation_euler = (R_(-90), 0, 0)
    for f_, h_ in ((1, True), (1975, False)):
        hm.hide_render = h_; hm.keyframe_insert("hide_render", frame=f_)
