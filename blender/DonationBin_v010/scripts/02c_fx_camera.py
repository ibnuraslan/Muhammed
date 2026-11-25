# DonationBin v010 stage B part 3 (exec'd by 02_animate.py after the bakes): flap (passer-by), latch, cut panel, cut glow,
# sparks, inside light (three days), helmets, saw, blinks, and the ONE continuous camera.
def key_const(obj, path, f, val, index=-1):
    setattr(obj, path, val) if index < 0 else getattr(obj, path).__setitem__(index, val)
    obj.keyframe_insert(path, frame=f, index=index)
def vis(obj, f, show):
    obj.hide_render = not show; obj.hide_viewport = not show
    obj.keyframe_insert("hide_render", frame=f); obj.keyframe_insert("hide_viewport", frame=f)
def set_constant(obj, contains):
    ad = obj.animation_data
    if ad and ad.action:
        for fc in iter_fcurves(ad.action):
            if contains in fc.data_path:
                for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
def iter_fcurves(action):
    try:
        for fc in action.fcurves: yield fc
    except AttributeError:
        for layer in action.layers:
            for strip in layer.strips:
                for cb in strip.channelbags:
                    for fc in cb.fcurves: yield fc

# ---------------------------------------------------------------- flap: the passer-by pushes it in (1792-1864), it falls shut (1872-1884)
for f in range(1786, 1890):
    a = pchip(P2_FLAP)(f) if f >= 1792 else 0.0
    FLAP.rotation_euler.x = R_(max(0.0, a)); FLAP.keyframe_insert("rotation_euler", index=0, frame=f)
FLAP.rotation_euler.x = 0.0; FLAP.keyframe_insert("rotation_euler", index=0, frame=1785)
# ---------------------------------------------------------------- latch pawl: drops into the catch at the slam (287) and clacks at 745
LP = O["A_LatchPivot"]; LP.rotation_mode = 'XYZ'
for f, a in ((1, 0), (282, 0), (285, 22), (289, 0), (292, 4), (295, 0), (728, 0), (736, 18), (745, 0), (749, 4), (752, 0),
             (1295, 0), (1299, 6), (1303, 0), (1317, 0), (1321, 6), (1325, 0), (1339, 0), (1343, 6), (1347, 0)):
    LP.rotation_euler.x = R_(-a); LP.keyframe_insert("rotation_euler", index=0, frame=f)
# ---------------------------------------------------------------- the cut panel (pivot on its bottom outer edge) falls outward
PAN = O["A_cutPanel"]
piv = bpy.data.objects.new("A_PanelHinge", None); sc.collection.objects.link(piv); piv.location = (0.0, BY0, CP[2])
upd(); mw = PAN.matrix_world.copy(); PAN.parent = piv; PAN.matrix_world = mw
for f, a in ((1, 0), (1950, 0), (1954, 3), (1960, 18), (1966, 52), (1971, 97), (1974, 92), (1977, 97)):
    piv.rotation_euler.x = R_(a); piv.keyframe_insert("rotation_euler", index=0, frame=f)
# ---------------------------------------------------------------- the glowing cut line travels round the panel; sparks follow the cut head
def set_origin(o, p_world):
    upd(); d = o.matrix_world.inverted() @ Vector(p_world)
    for v in o.data.vertices: v.co -= d
    o.location = o.matrix_world @ d if o.parent is None else o.location + d
x0, x1, z0, z1 = CP
SEG = [("L", (x0 + 0.006, z0), (x0 + 0.006, z1), 1878, 1896, 2), ("T", (x0, z1 - 0.006), (x1, z1 - 0.006), 1896, 1914, 0),
       ("R", (x1 - 0.006, z1), (x1 - 0.006, z0), 1914, 1932, 2), ("B", (x1, z0 + 0.006), (x0, z0 + 0.006), 1932, 1950, 0)]
gy = BY0 + T + 0.003
for nm, a_, b_, fa, fb, ax in SEG:
    o = O["CutGlow" + nm]; set_origin(o, (a_[0], gy, a_[1]))
    sgn = 1 if (b_[0] - a_[0]) + (b_[1] - a_[1]) > 0 else -1
    if sgn < 0:
        for v in o.data.vertices: v.co = -v.co
    s0 = [1, 1, 1]; s0[ax] = 0.001
    o.scale = s0; o.keyframe_insert("scale", frame=fa); o.scale = (1, 1, 1); o.keyframe_insert("scale", frame=fb)
    vis(o, 1, False); vis(o, fa, True); vis(o, 1952, False)
EM = O["SparkEmitter"]
for nm, a_, b_, fa, fb, ax in SEG:
    for f, u in ((fa, 0.0), (fb, 1.0)):
        EM.location = (a_[0] + (b_[0] - a_[0]) * u, gy + 0.004, a_[1] + (b_[1] - a_[1]) * u); EM.keyframe_insert("location", frame=f)
ps = EM.particle_systems[0].settings; ps.frame_start = 1878; ps.frame_end = 1950
log("cut line 1878-1950, panel falls 1950-1971")
# ---------------------------------------------------------------- inside light: day (warm) / night (blue) for the three days
IK, IF = O["InKey"], O["InFill"]
def light_key(f, e_key, c_key, e_fill, c_fill, vent):
    IK.data.energy = e_key; IK.data.color = c_key; IF.data.energy = e_fill; IF.data.color = c_fill
    for d_, p_ in ((IK.data, "energy"), (IK.data, "color"), (IF.data, "energy"), (IF.data, "color")): d_.keyframe_insert(p_, frame=f)
    m = bpy.data.materials["M_Vent"].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
    m.default_value = vent; m.keyframe_insert("default_value", frame=f)
DAY = ((1.0, 0.80, 0.58), (1.0, 0.82, 0.70)); NIGHT = ((0.45, 0.58, 1.0), (0.35, 0.45, 1.0))
light_key(1, 15, DAY[0], 15, DAY[1], 6.0); light_key(270, 15, DAY[0], 15, DAY[1], 6.0); light_key(290, 45, DAY[0], 18, DAY[1], 6.0)
for f0, kind in ((1505, "N"), (1560, "D"), (1610, "N"), (1665, "D")):
    a_ = DAY if kind == "D" else NIGHT
    light_key(f0, 45 if kind == "N" else 18, (DAY if kind == "N" else NIGHT)[0], 18 if kind == "N" else 16, (DAY if kind == "N" else NIGHT)[1], 6.0 if kind == "N" else 0.6)
    light_key(f0 + 18, 18 if kind == "N" else 45, a_[0], 16 if kind == "N" else 18, a_[1], 0.6 if kind == "N" else 6.0)
light_key(1953, 45, DAY[0], 18, DAY[1], 6.0); light_key(1972, 30, DAY[0], 20, DAY[1], 6.0)
# ---------------------------------------------------------------- helmets (Child Of the firefighters' head bones) and the saw on the ground
for hn, rn in (("Helmet1", "Fire1"), ("Helmet2", "Fire2")):
    h = O[hn]; rig = O[rn]; fs(1)
    hb = rig.pose.bones["head"]; Mh = rig.matrix_world @ hb.matrix
    top = rig.matrix_world @ hb.tail
    yb = (Mh.to_3x3().normalized() @ Vector((0, 1, 0))).normalized()
    h.matrix_world = Matrix.Translation(top - yb * 0.165) @ (Mh.to_3x3().normalized().to_4x4() @ Matrix.Rotation(R_(-90), 4, 'X'))
    upd()
    c = h.constraints.new('CHILD_OF'); c.target = rig; c.subtarget = "head"
    c.inverse_matrix = (rig.matrix_world @ hb.matrix).inverted()
    # seat it: lower until the inner shell rests on the hair (brim at the brow)
    h.location = h.location  # (fit offsets are applied below)
SAW = O["Saw"]
for f, loc, rot in ((1, (20, 2, 0), (0, 0, 0)), (1859, (-1.38, -1.52, 0.0), (0, 0, R_(25)))):
    SAW.location = loc; SAW.rotation_euler = rot; SAW.keyframe_insert("location", frame=f); SAW.keyframe_insert("rotation_euler", frame=f)
set_constant(SAW, "location"); set_constant(SAW, "rotation")
BAG = O["DonationBag"]; vis(BAG, 1, False)
for n, dx in (("Crate0", -1.9), ("CrateBoard", -1.9), ("Crate1", -1.2)):
    o = O[n]; o.keyframe_insert("location", frame=1); o.keyframe_insert("location", frame=1858)
    o.location.x += dx; o.location.y -= 0.6; o.keyframe_insert("location", frame=1859); set_constant(o, "location")
# ---------------------------------------------------------------- blinks
blinks(O["Woman"], [70, 330, 520, 760, 980, 1130, 1420, 1990, 2090, 2200, 2320])
blinks(O["Man"], [60, 205]); blinks(O["Passer"], [1770, 1880, 2150, 2330]); blinks(O["Fire1"], [2000, 2160, 2300]); blinks(O["Fire2"], [2050, 2250])
eyes_closed(O["Woman"], 1515, 1560); eyes_closed(O["Woman"], 1620, 1665); eyes_closed(O["Woman"], 1705, 1745)

# ---------------------------------------------------------------- the ONE continuous camera (smooth PCHIP path through empty space, level horizon)
CAMK = [
 (1, (-1.50, -3.00, 1.35), (0.0, -1.00, 1.50), 26), (55, (-0.75, -0.88, 1.60), (0.0, -1.02, 1.58), 26),
 (100, (-0.88, -1.02, 1.64), (0.0, -1.18, 1.55), 24), (140, (-1.25, -1.45, 1.70), (0.0, -1.20, 1.45), 24),
 (175, (-1.00, -1.80, 1.95), (0.0, -0.80, 1.50), 22), (215, (-0.35, -1.60, 1.60), (0.0, -0.70, 1.42), 22),
 (240, (-0.05, -1.10, 1.45), (0.0, -0.30, 1.35), 18), (256, (0.0, -0.75, 1.42), (0.0, -0.10, 1.15), 16),
 (266, (0.15, -0.45, 1.05), (-0.15, 0.10, 0.45), 14), (285, (0.55, -0.50, 0.95), (-0.20, 0.0, 0.70), 14),
 (330, (0.62, -0.55, 0.95), (-0.10, 0.12, 0.50), 15), (400, (0.60, -0.60, 1.00), (-0.05, 0.14, 0.62), 15),
 (451, (0.55, -0.60, 1.05), (0.0, 0.15, 0.75), 16), (500, (0.60, -0.62, 1.20), (0.0, -0.05, 1.05), 15),
 (555, (0.62, -0.62, 1.40), (0.0, -0.20, 1.35), 14), (600, (0.62, -0.60, 1.85), (0.0, -0.25, 1.50), 15),
 (650, (0.58, -0.60, 1.82), (0.0, -0.30, 1.48), 15),
 (690, (0.20, -0.47, 1.05), (0.0, -0.68, 1.17), 22), (745, (0.12, -0.48, 1.10), (0.0, -0.68, 1.18), 24),
 (790, (0.62, -0.60, 1.80), (0.0, -0.20, 1.45), 15), (847, (0.62, -0.60, 1.80), (0.0, -0.25, 1.48), 15),
 (905, (0.62, -0.60, 1.75), (-0.10, -0.35, 1.45), 14), (990, (0.55, -0.62, 1.70), (-0.40, -0.35, 1.45), 14),
 (1070, (0.42, -0.62, 1.65), (-0.55, -0.30, 1.45), 14), (1110, (0.42, -0.62, 1.62), (-0.50, -0.32, 1.42), 14),
 (1145, (0.55, -0.62, 1.00), (-0.02, -0.40, 1.85), 14), (1200, (0.50, -0.62, 0.95), (0.0, -0.55, 2.20), 14),
 (1250, (0.55, -0.60, 1.30), (0.0, -0.35, 1.50), 15), (1285, (0.58, -0.60, 1.78), (0.0, -0.30, 1.55), 17),
 (1330, (0.50, -0.62, 1.72), (0.0, -0.30, 1.55), 18), (1400, (0.62, -0.55, 1.70), (0.0, -0.25, 1.45), 15),
 (1465, (0.62, -0.40, 1.60), (-0.05, 0.05, 0.85), 14), (1550, (0.62, -0.50, 0.95), (-0.10, 0.10, 0.45), 14),
 (1650, (0.40, -0.60, 0.80), (-0.05, 0.12, 0.45), 14), (1753, (0.62, -0.45, 0.78), (0.0, 0.05, 0.60), 14),
 (1800, (0.62, -0.20, 0.72), (-0.10, -0.55, 1.30), 14), (1867, (0.62, -0.25, 0.80), (-0.05, -0.40, 1.00), 14),
 (1910, (0.62, -0.35, 1.25), (-0.15, -0.25, 0.65), 14), (1950, (0.60, -0.38, 1.20), (-0.15, -0.35, 0.62), 14),
 (1975, (0.40, -0.40, 0.95), (-0.05, -1.20, 0.55), 15), (1995, (0.10, -0.55, 0.68), (0.20, -1.50, 0.70), 18),
 (2012, (0.25, -1.20, 0.78), (0.90, -1.55, 1.30), 20), (2035, (0.55, -1.85, 0.85), (0.0, -0.60, 0.62), 20),
 (2080, (0.35, -1.95, 0.85), (0.0, -0.60, 0.70), 22), (2140, (0.20, -2.05, 0.95), (-0.15, -0.70, 0.75), 24),
 (2200, (0.40, -2.40, 1.25), (-0.05, -0.75, 0.80), 22), (2280, (1.20, -3.60, 2.10), (0.60, -0.60, 0.90), 20),
 (2388, (2.30, -5.40, 3.20), (1.60, -0.20, 1.00), 20)]
CAMK = [k for k in CAMK if k[0] <= END]
cam = bpy.data.objects.get("Cam") or bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
if cam.name not in sc.collection.objects: sc.collection.objects.link(cam)
sc.camera = cam; cam.data.clip_start = 0.01; cam.data.dof.use_dof = False; cam.data.sensor_fit = 'AUTO'
tgt = bpy.data.objects.get("CamTarget") or bpy.data.objects.new("CamTarget", None)
if tgt.name not in sc.collection.objects: sc.collection.objects.link(tgt)
fx = [pchip([(k[0], k[1][i]) for k in CAMK]) for i in range(3)]
ft = [pchip([(k[0], k[2][i]) for k in CAMK]) for i in range(3)]
fl = pchip([(k[0], k[3]) for k in CAMK])
for f in range(1, END + 1):
    cam.location = (fx[0](f), fx[1](f), fx[2](f)); cam.keyframe_insert("location", frame=f)
    tgt.location = (ft[0](f), ft[1](f), ft[2](f)); tgt.keyframe_insert("location", frame=f)
    cam.data.lens = fl(f); cam.data.keyframe_insert("lens", frame=f)
for c in list(cam.constraints): cam.constraints.remove(c)
tc = cam.constraints.new('TRACK_TO'); tc.target = tgt; tc.track_axis = 'TRACK_NEGATIVE_Z'; tc.up_axis = 'UP_Y'; tc.use_target_z = False
# small catchlight at the lens (no black-hole eyes), scaled down in close-ups
bpy.ops.object.light_add(type='POINT', location=(0, 0, 0)); cl = bpy.context.active_object; cl.name = "Catchlight"
cl.data.energy = 3.0; cl.data.shadow_soft_size = 0.05; cl.parent = cam; cl.location = (0.05, 0.08, 0.0); cl.visible_camera = False
log("camera keys", len(CAMK))
