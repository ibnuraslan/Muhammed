# LegoInNose v013 stage B part 3 (exec'd): set visibility per island, the void bubble, light changes, water, the ONE camera, VO, save.

# ================================================================== which island is live (objects of the other islands hidden: they never block rays)
def island(o):
    n = o.name
    if n.startswith(("LR_", "Sofa", "Scatter", "ToyTub", "Book", "Tweezers", "BrickYellow", "ClickFlash")): return "LR"
    if n.startswith(("BR_", "Bed", "Nightstand", "TissueBox", "Inhaler", "WinSkyBR", "WinFrameBR")): return "BR"
    if n.startswith(("BA_", "Water")): return "BA"
    if n.startswith(("WinSkyLR", "WinFrameLR")): return "LR"
    return None
V1_HIDE, V1_SHOW = 1199, 1256       # inside void 1: LR off, BR on (behind the opaque bubble)
V2_HIDE = TV                        # inside void 2: BR off, BA on
SETS = {"LR": [], "BR": [], "BA": []}
for o in list(O):
    if o.type not in ('MESH', 'CURVE'): continue
    k = island(o)
    if k: SETS[k].append(o)
for o in SETS["LR"]: vis(o, 1, True); vis(o, V1_HIDE, False)
for o in SETS["BR"]: vis(o, 1, False); vis(o, V1_SHOW, True); vis(o, 1558, False)
for o in SETS["BA"]: vis(o, 1, False); vis(o, V2_HIDE, True)
for rig, on, off in ((BOY, 1, V1_HIDE), (MOM, 1, V1_HIDE), (MAN, V1_SHOW - 20, END + 1)):
    for c in rig.children:
        if c.type != 'MESH': continue
        vis(c, 1, on == 1)
        if on != 1: vis(c, on, True)
        if off <= END: vis(c, off, False)
# pajamas in bed, nothing under the shower (framed over the tiled wall): garments + their skin mask switch at TV
for n in ("Man.top", "Man.trousers"): vis(O[n], TV, False)
mk = NB.modifiers.get("hide_under")
if mk:
    mk.show_render = mk.show_viewport = True; mk.keyframe_insert("show_render", frame=1); mk.keyframe_insert("show_viewport", frame=1)
    mk.show_render = mk.show_viewport = False; mk.keyframe_insert("show_render", frame=TV); mk.keyframe_insert("show_viewport", frame=TV)

# ================================================================== the void bubble (camera-parented sphere, sky-blue gradient, camera rays only)
cam_d = bpy.data.cameras.new("CAM_Film"); CAM = bpy.data.objects.new("CAM_Film", cam_d); sc.collection.objects.link(CAM); sc.camera = CAM
AIM = bpy.data.objects.new("CAM_Film_Aim", None); sc.collection.objects.link(AIM)
cam_d.sensor_fit = 'AUTO'; cam_d.sensor_width = 36; cam_d.dof.use_dof = True; cam_d.dof.focus_object = AIM; cam_d.dof.aperture_fstop = 22.0
cam_d.clip_start = 0.004
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=48, ring_count=24); VOID = bpy.context.active_object; VOID.name = "VoidBubble"
VOID.data.flip_normals() if hasattr(VOID.data, "flip_normals") else None
for p in VOID.data.polygons: p.use_smooth = True
vm = bpy.data.materials.new("M_Void"); vm.use_nodes = True; nt = vm.node_tree
for n in list(nt.nodes):
    if n.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n)
out = nt.nodes["Material Output"]
tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sep.inputs[0])
mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = -0.7; mr.inputs["From Max"].default_value = 0.7
nt.links.new(sep.outputs["Y"], mr.inputs["Value"])
cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (0.10, 0.03, 0.30, 1); cr.color_ramp.elements[1].color = (0.0, 0.30, 0.55, 1)   # deep purple -> blue, no grey
nt.links.new(mr.outputs["Result"], cr.inputs["Fac"])
em = nt.nodes.new("ShaderNodeEmission"); nt.links.new(cr.outputs["Color"], em.inputs["Color"]); em.inputs["Strength"].default_value = 1.0
tr = nt.nodes.new("ShaderNodeBsdfTransparent")
lp = nt.nodes.new("ShaderNodeLightPath")
av = nt.nodes.new("ShaderNodeValue"); av.name = "VoidAlpha"; av.outputs[0].default_value = 0.0
mul = nt.nodes.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'; nt.links.new(lp.outputs["Is Camera Ray"], mul.inputs[0]); nt.links.new(av.outputs[0], mul.inputs[1])
mx = nt.nodes.new("ShaderNodeMixShader"); nt.links.new(mul.outputs[0], mx.inputs["Fac"]); nt.links.new(tr.outputs["BSDF"], mx.inputs[1]); nt.links.new(em.outputs["Emission"], mx.inputs[2])
nt.links.new(mx.outputs["Shader"], out.inputs["Surface"])
VOID.data.materials.append(vm)
VOID.visible_shadow = False; VOID.visible_diffuse = False; VOID.visible_glossy = False; VOID.visible_transmission = False
VOID.parent = CAM; VOID.matrix_parent_inverse = Matrix.Identity(4); VOID.location = (0, 0, 0)
VA = av.outputs[0]
def key_void(f, a, r):
    VA.default_value = a; VA.keyframe_insert("default_value", frame=f)
    VOID.scale = (r, r, r); VOID.keyframe_insert("scale", frame=f)
for f, a, r in ((1, 0.0, 2.0), (1132, 0.0, 2.0), (1178, 1.0, 0.30), (1200, 1.0, 0.7), (1250, 1.0, 0.7), (1256, 1.0, 0.30), (1300, 0.0, 2.0),
                (1538, 0.0, 2.0), (1564, 1.0, 0.30), (1598, 1.0, 0.30), (1632, 0.0, 2.0), (END, 0.0, 2.0)):
    key_void(f, a, r)
vis(VOID, 1, False); vis(VOID, 1130, True); vis(VOID, 1302, False); vis(VOID, 1536, True); vis(VOID, 1634, False)

# ================================================================== light changes: bedroom evening -> night (sleep apnea)
def key_light(name, f, energy, col=None):
    L = O[name].data; L.energy = energy; L.keyframe_insert("energy", frame=f)
    if col: L.color = col; L.keyframe_insert("color", frame=f)
for f, e, c in ((1, 150, (1.0, 0.85, 0.65)), (1425, 150, (1.0, 0.85, 0.65)), (1460, 45, (0.55, 0.65, 1.0))): key_light("BR_Key", f, e, c)
for f, e in ((1, 25), (1426, 25), (1432, 0)): key_light("BR_LampBulb", f, e)
for f, e, c in ((1, 70, (0.80, 0.88, 1.0)), (1425, 70, (0.80, 0.88, 1.0)), (1460, 60, (0.45, 0.58, 1.0))): key_light("BR_Fill", f, e, c)
shade = [m for m in bpy.data.materials if "lamp3fabtic" in m.name.lower() or "fabtic" in m.name.lower()]

# the hero brick glows a little while it is inside a head (x-ray reads), plain LEGO red once it is out in the bath light
_rb = [n_ for n_ in bpy.data.materials["M_BrickRed"].node_tree.nodes if n_.type == "BSDF_PRINCIPLED"][0].inputs["Emission Strength"]
for f, v in ((1, 0.45), (1806, 0.45), (1836, 0.06), (END, 0.06)):
    _rb.default_value = v; _rb.keyframe_insert("default_value", frame=f)
for f, e in ((1, -0.45), (1571, -0.45), (1572, -0.55), (END, -0.55)):
    sc.view_settings.exposure = e; sc.view_settings.keyframe_insert("exposure", frame=f)
for fc in iter_fcurves(sc.animation_data.action):
    if 'exposure' in fc.data_path:
        for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
# ================================================================== shower water: thin streams with travelling droplets (keyed phase, no Scene Time)
wm = bpy.data.materials.new("M_Water"); wm.use_nodes = True; nt = wm.node_tree
for n in list(nt.nodes):
    if n.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n)
tc = nt.nodes.new("ShaderNodeTexCoord"); mpn = nt.nodes.new("ShaderNodeMapping"); nt.links.new(tc.outputs["Object"], mpn.inputs["Vector"])
wv = nt.nodes.new("ShaderNodeTexWave"); wv.wave_type = 'BANDS'; wv.bands_direction = 'Z'; wv.inputs["Scale"].default_value = 6.0; wv.inputs["Distortion"].default_value = 3.0
nt.links.new(mpn.outputs["Vector"], wv.inputs["Vector"])
crw = nt.nodes.new("ShaderNodeValToRGB"); crw.color_ramp.elements[0].position = 0.45; crw.color_ramp.elements[1].position = 0.75
nt.links.new(wv.outputs["Fac"], crw.inputs["Fac"])
emw = nt.nodes.new("ShaderNodeEmission"); emw.inputs["Color"].default_value = (0.80, 0.93, 1.0, 1); emw.inputs["Strength"].default_value = 1.2
trw = nt.nodes.new("ShaderNodeBsdfTransparent"); mxw = nt.nodes.new("ShaderNodeMixShader")
mw_ = nt.nodes.new("ShaderNodeMath"); mw_.operation = 'MULTIPLY'; mw_.inputs[1].default_value = 0.7; nt.links.new(crw.outputs["Color"], mw_.inputs[0])
nt.links.new(mw_.outputs[0], mxw.inputs["Fac"]); nt.links.new(trw.outputs["BSDF"], mxw.inputs[1]); nt.links.new(emw.outputs["Emission"], mxw.inputs[2])
nt.links.new(mxw.outputs["Shader"], nt.nodes["Material Output"].inputs["Surface"])
for f in (1, END):
    mpn.inputs["Location"].default_value = (0, 0, (f / 60.0) * 2.2); mpn.inputs["Location"].keyframe_insert("default_value", frame=f)
for fc in iter_fcurves(wm.node_tree.animation_data.action):
    for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
SH = O["BA_ShowerHead"]; shc = SH.matrix_world.translation.copy()
rw = random.Random(9)
for i in range(22):
    a_ = rw.uniform(0, 2 * math.pi); r_ = rw.uniform(0.0, 0.06)
    top = shc + Vector((math.cos(a_) * r_, math.sin(a_) * r_ * 0.6 - 0.02, -0.02))
    bot = Vector((top.x + math.cos(a_) * 0.10, top.y - 0.12 + math.sin(a_) * 0.05, TUB_FLOOR + 0.01))
    if (Vector((bot.x, bot.y)) - Vector((BATH_X - 0.02, SH_Y))).length < 0.24: bot.y = max(bot.y, SH_Y + 0.22)
    cu = bpy.data.curves.new("Water%02d" % i, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.0018; cu.bevel_resolution = 1
    sp = cu.splines.new('POLY'); sp.points.add(1); sp.points[0].co = (*top, 1); sp.points[1].co = (*bot, 1)
    ob = bpy.data.objects.new("Water%02d" % i, cu); sc.collection.objects.link(ob); cu.materials.append(wm)
    ob.visible_shadow = False
    vis(ob, 1, False); vis(ob, V2_HIDE, True)

# ================================================================== the ONE camera: world keys + nostril-frame keys inside the voids
def Gm(rig, N, f):
    """nostril frame (unscaled): head deform @ translate(nostril)"""
    return head_M(rig, f) @ Matrix.Translation(N)
def headc(rig, f):
    fs(f); M = head_M(rig, f); e = (rig.data.bones["eye.L"].head_local + rig.data.bones["eye.R"].head_local) / 2
    return M @ (e + Vector((0, 0.03, -0.03)))
def nose(rig, N, f): return Gm(rig, N, f).translation.copy()
def loc_in(rig, N, f, v): return Gm(rig, N, f) @ Vector(v)
def P(*v): return Vector(v)
fs(1)
def bh(f): return headc(BOY, f)
def mh(f): return headc(MOM, f)
def nb(f): return nose(BOY, N_B, f)
def red_w(f): fs(f); return RED.matrix_world @ Vector((0, 0, 0.005))
def yel_w(f): fs(f); return YEL.matrix_world @ Vector((0, 0, 0.005))
def mn(f): return nose(MAN, N_M, f)
def mhd(f): return headc(MAN, f)
def mloc(f, v): return loc_in(MAN, N_M, f, v)
def bloc(f, v): return loc_in(BOY, N_B, f, v)
CAMK = [  # frame, camera position, aim point, lens  (world)
    (1,    lambda: bh(1) + P(0.36, -0.72, 0.22), lambda: bh(1).lerp(red_w(1), 0.42), 28),
    (24,   lambda: bh(24) + P(0.30, -0.60, 0.18), lambda: bh(24).lerp(red_w(24), 0.45), 30),
    (60,   lambda: bh(60) + P(-0.12, -0.40, 0.08), lambda: red_w(60).lerp(bh(60), 0.5), 36),
    (98,   lambda: nb(98) + P(-0.20, -0.15, 0.04), lambda: red_w(98).lerp(nb(98), 0.5), 44),
    (135,  lambda: red_w(135) + P(-0.02, -0.085, 0.01), lambda: red_w(135), 50),
    (175,  lambda: bh(175) + P(0.16, -0.38, 0.05), lambda: bh(175), 36),
    (215,  lambda: bh(215) + P(0.34, -0.66, 0.16), lambda: bh(215).lerp(yel_w(215), 0.45), 30),
    (242,  lambda: bh(242) + P(0.34, -0.60, 0.10), lambda: bh(242).lerp(yel_w(242), 0.45), 32),
    (282,  lambda: bh(282) + P(0.03, -0.40, 0.05), lambda: bh(282).lerp(yel_w(282), 0.4), 36),
    (318,  lambda: bh(318) + P(-0.22, -0.26, 0.06), lambda: nb(318), 42),
    (360,  lambda: yel_w(360) + P(-0.03, -0.10, 0.02), lambda: yel_w(360).lerp(red_w(360), 0.5), 50),
    (420,  lambda: yel_w(420) + P(0.03, -0.09, 0.02), lambda: yel_w(420).lerp(red_w(420), 0.5), 50),
    (465,  lambda: yel_w(465) + P(-0.02, -0.08, 0.02), lambda: yel_w(465).lerp(red_w(465), 0.5), 52),
    (515,  lambda: bh(515) + P(0.12, -0.34, 0.04), lambda: bh(515), 38),
    (580,  lambda: bh(580) + P(0.02, -0.28, -0.05), lambda: nb(580), 42),
    (645,  lambda: yel_w(645) + P(-0.03, -0.10, 0.02), lambda: yel_w(645).lerp(red_w(645), 0.5), 50),
    (705,  lambda: yel_w(705) + P(0.04, -0.10, 0.03), lambda: yel_w(705).lerp(red_w(705), 0.5), 50),
    (765,  lambda: bh(765).lerp(mh(765), 0.4) + P(0.45, -0.95, 0.05), lambda: bh(765).lerp(mh(765), 0.45), 30),
    (790,  lambda: nb(790) + P(0.03, -0.30, 0.03), lambda: nb(790), 40),
    (808,  lambda: nb(808) + P(0.06, -0.31, 0.02), lambda: nb(808), 40),
    (830,  lambda: bh(830).lerp(mh(830), 0.45) + P(-0.36, -0.82, 0.06), lambda: bh(830).lerp(mh(830), 0.42), 27),
    (858,  lambda: nb(858).lerp(mh(858), 0.45) + P(-0.30, -0.62, 0.04), lambda: nb(858).lerp(mh(858), 0.45), 30),
    (892,  lambda: yel_w(892).lerp(mh(892), 0.35) + P(-0.24, -0.50, 0.03), lambda: yel_w(892).lerp(mh(892), 0.3), 34),
    (925,  lambda: yel_w(925) + P(-0.07, -0.29, 0.02), lambda: yel_w(925), 42),
    (962,  lambda: yel_w(962).lerp(mh(962), 0.3) + P(-0.28, -0.62, 0.06), lambda: yel_w(962).lerp(mh(962), 0.45), 30),
    (1005, lambda: bh(1005) + P(-0.10, -0.34, 0.03), lambda: nb(1005), 40),
    (1060, lambda: bloc(1060, (0.03, -0.15, 0.05)), lambda: red_w(1060), 48),
    (1110, lambda: bloc(1110, (0.05, -0.15, 0.03)), lambda: red_w(1110), 46),
    (1150, lambda: bloc(1150, (-0.02, -0.12, 0.03)), lambda: red_w(1150), 48),
    # void 1: nostril-frame (rides the boy, then the man after the swap)
    (1185, lambda: bloc(1185, (0.05, -0.08, 0.02)), lambda: red_w(1185), 46),
    (1210, lambda: bloc(1210, (0.12, -0.20, 0.06)), lambda: bloc(1210, (0, 0.04, 0.03)), 40),
    (1224, lambda: bloc(1224, (0.16, -0.22, 0.07)), lambda: bloc(1224, (0, 0.05, 0.04)), 40),
    (1225, lambda: mloc(1225, (0.16, -0.22, 0.07)), lambda: mloc(1225, (0, 0.05, 0.04)), 40),
    (1245, lambda: mloc(1245, (0.04, -0.09, 0.03)), lambda: red_w(1245), 44),
    (1270, lambda: mloc(1270, (0.0, -0.10, -0.07)), lambda: mn(1270), 42),
    # bedroom
    (1305, lambda: mhd(1305) + P(0.05, -0.30, 0.20), lambda: mhd(1305), 36),
    (1345, lambda: mhd(1345) + P(0.12, -0.50, 0.50), lambda: mhd(1345) + P(0, -0.10, 0), 32),
    (1385, lambda: mhd(1385) + P(0.12, -0.44, 0.34), lambda: mn(1385), 34),
    (1405, lambda: mhd(1405) + P(0.10, -0.36, 0.30), lambda: mn(1405), 38),
    (1445, lambda: mhd(1445) + P(-0.02, -0.52, 0.40), lambda: mhd(1445), 34),
    (1490, lambda: mhd(1490) + P(0.04, -0.32, 0.32), lambda: mhd(1490), 40),
    (1520, lambda: mhd(1520) + P(0.06, -0.18, 0.22), lambda: mn(1520), 45),
    (1548, lambda: mloc(1548, (0.02, -0.09, -0.06)), lambda: red_w(1548), 48),
    # void 2: rides the man's nostril frame through the move bed -> shower
    (1571, lambda: mloc(1571, (0.12, -0.20, 0.06)), lambda: mloc(1571, (0, 0.05, 0.04)), 40),
    (1572, lambda: mloc(1572, (0.12, -0.20, 0.06)), lambda: mloc(1572, (0, 0.05, 0.04)), 40),
    (1600, lambda: mloc(1600, (-0.03, -0.11, 0.02)), lambda: mn(1600), 44),
    # shower
    (1635, lambda: mhd(1635) + P(0.10, -0.46, -0.02), lambda: mhd(1635), 35),
    (1662, lambda: mhd(1662) + P(0.06, -0.40, -0.03), lambda: mn(1662), 38),
    (1695, lambda: mhd(1695) + P(-0.07, -0.38, -0.03), lambda: mn(1695), 40),
    (1745, lambda: mn(1745) + P(0.04, -0.17, 0.02), lambda: red_w(1745), 46),
    (1800, lambda: mn(1800) + P(-0.03, -0.16, 0.01), lambda: red_w(1800), 46),
    (1833, lambda: mhd(1833) + P(0.07, -0.30, -0.02), lambda: mn(1833).lerp(red_w(1846), 0.5), 40),
    (1850, lambda: mhd(1850) + P(0.05, -0.36, -0.02), lambda: red_w(1850).lerp(mhd(1850), 0.5), 40),
    (1895, lambda: red_w(1895) + P(0.02, -0.055, 0.035), lambda: red_w(1895).lerp(mhd(1895), 0.08), 40),
    (1940, lambda: red_w(1940) + P(-0.03, -0.08, 0.04), lambda: red_w(1940).lerp(mhd(1940), 0.3), 34),
    (1980, lambda: red_w(1980) + P(0.05, -0.13, 0.04), lambda: red_w(1980).lerp(mhd(1980), 0.5), 26),
    (2036, lambda: red_w(2036) + P(0.08, -0.16, 0.04), lambda: red_w(2036).lerp(mhd(2036), 0.5), 24),
]
KEYS = []
for f, pf, af, lens in CAMK:
    KEYS.append((f, pf(), af(), lens))
    log("camkey", f, tuple(round(x, 3) for x in KEYS[-1][1]))
# camera interpolation: world PCHIP between keys, except the void spans (1185-1270, 1571-1600), where the camera is
# expressed in the nostril frame of the active head and interpolated there (seamless across the boy->man swap / the move)
def seg_frame(f):
    if 1185 <= f <= 1224: return ("B", BOY, N_B)
    if 1225 <= f <= 1270 or 1548 <= f <= 1600: return ("M", MAN, N_M)
    return None
fx = [pchip([(k[0], k[1][i]) for k in KEYS]) for i in range(3)]
ax = [pchip([(k[0], k[2][i]) for k in KEYS]) for i in range(3)]
fl = pchip([(k[0], k[3]) for k in KEYS])
# local (nostril-frame) splines for the void spans
LOCAL = {}
for tag, f0, f1, rig, N in (("v1b", 1150, 1224, BOY, N_B), ("v1m", 1225, 1305, MAN, N_M), ("v2", 1520, 1635, MAN, N_M)):
    ks = [k for k in KEYS if f0 <= k[0] <= f1]
    loc = []
    for f, p, a, l in ks:
        Gi = Gm(rig, N, f).inverted(); loc.append((f, Gi @ p, Gi @ a))
    LOCAL[tag] = (f0, f1, rig, N, [pchip([(k[0], k[1][i]) for k in loc]) for i in range(3)], [pchip([(k[0], k[2][i]) for k in loc]) for i in range(3)])
def which_local(f):
    if 1185 <= f <= 1224: return LOCAL["v1b"]
    if 1225 <= f <= 1270: return LOCAL["v1m"]
    if 1548 <= f <= 1600: return LOCAL["v2"]
    return None
def up_hint(f):
    Z = Vector((0, 0, 1))
    def gz(rig, N): return (Gm(rig, N, f).to_3x3() @ Vector((0, 0, 1))).normalized()
    def bl(a, b, u): return a.lerp(b, smoothstep(u)).normalized()
    if 1185 <= f <= 1224: return bl(Z, gz(BOY, N_B), (f - 1185) / 25.0)
    if 1225 <= f <= 1256: return bl(gz(MAN, N_M), Z, (f - 1228) / 27.0)
    if 1560 <= f <= 1571: return bl(Z, gz(MAN, N_M), (f - 1561) / 10.0)
    if 1572 <= f <= 1598: return bl(gz(MAN, N_M), Z, (f - 1576) / 22.0)
    return Z
CAM.rotation_mode = 'QUATERNION'
prevq = None
for f in range(1, END + 1):
    L = which_local(f)
    if L:
        f0, f1, rig, N, lp_, la_ = L; G = Gm(rig, N, f)
        p = G @ Vector([lp_[i](f) for i in range(3)]); a = G @ Vector([la_[i](f) for i in range(3)])
    else:
        p = Vector([fx[i](f) for i in range(3)]); a = Vector([ax[i](f) for i in range(3)])
    fs(f); up = up_hint(f)
    zc = (p - a).normalized(); yc = (up - zc * up.dot(zc)).normalized(); xc = yc.cross(zc)
    q = Matrix((xc, yc, zc)).transposed().to_quaternion()
    if prevq is not None and prevq.dot(q) < 0: q = -q
    prevq = q
    CAM.location = p; CAM.rotation_quaternion = q; AIM.location = a; cam_d.lens = fl(f)
    CAM.keyframe_insert("location", frame=f); CAM.keyframe_insert("rotation_quaternion", frame=f)
    AIM.keyframe_insert("location", frame=f); cam_d.keyframe_insert("lens", frame=f)
set_interp(CAM, 'LINEAR'); set_interp(AIM, 'LINEAR'); set_interp(cam_d, 'LINEAR')
# within the void spans the camera may roll with the head (keep the image continuous): up axis from the nostril frame
cl = bpy.data.lights.new("Catch", 'AREA'); cl.energy = 10.0; cl.size = 0.25; cl.color = (1, 0.97, 0.94)
clo = bpy.data.objects.new("Catchlight", cl); sc.collection.objects.link(clo); clo.parent = CAM; clo.location = (0.0, 0.10, 0.0)
# its strength follows the camera-subject distance (inverse square): a soft eye glint, never a blown-out macro
for f in list(range(1, END + 1, 6)) + [END]:
    fs(f); d_ = (CAM.matrix_world.translation - AIM.matrix_world.translation).length
    cl.energy = max(0.15, min(8.0, 8.0 * (d_ / 0.8) ** 2)); cl.keyframe_insert("energy", frame=f)

# ================================================================== audio, range, save
sc.frame_start, sc.frame_end = 1, END
if not sc.sequence_editor: sc.sequence_editor_create()
vo = "/home/user/Muhammed/blender/LegoInNose_v013/LegoInNose_v013_VO.mp3"
try:
    se = sc.sequence_editor; strips = se.strips if hasattr(se, "strips") else se.sequences
    strips.new_sound("VO", vo, 1, 1)
except Exception as e:
    log("vo strip failed", e)
for o in O:
    for m in getattr(o, "modifiers", []):
        if m.type == 'SUBSURF': m.show_viewport = True
log("quat flips fixed", quat_continuity(BOY), quat_continuity(MOM), quat_continuity(MAN))
sc.frame_set(1)
sc.render.filepath = "//render/LegoInNose_v013_####.png"; sc.render.image_settings.file_format = 'PNG'
# no linked libraries in the farm file (auto-smooth node group from the brick build -> local)
for ng in list(bpy.data.node_groups):
    if ng.library: ng.make_local()
for o_ in O:
    for m_ in getattr(o_, "modifiers", []):
        if m_.type == 'NODES' and m_.node_group and m_.node_group.library: m_.node_group = m_.node_group.make_local()
for lib in list(bpy.data.libraries):
    try: bpy.data.libraries.remove(lib)
    except Exception as e: log("lib remove", e)
