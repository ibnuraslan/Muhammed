# PrisonKeyCake v011 stage B part 3 (exec'd): the ONE camera, the two glow voids, sky/light changes, VO, render settings.
# Scene changes happen inside the move: (1) push into the candle flame -> warm glow -> pull out of the gate torch (341);
# (2) a matched macro on the cake side: the workshop cake and the cell cake share the same cake-relative camera (800);
# (3) a press-camera flash as he walks free -> years later on the government steps (1622).

def hd(rig, f):
    fs(f); return (Wh(rig, "eye.L") + Wh(rig, "eye.R")) / 2
def ow(obj, f, off=(0, 0, 0)):
    fs(f); return obj.matrix_world.translation + Vector(off)
def P(*v): return Vector(v)
FLAME = O["CandleFlame"]
def flame(f): fs(f); return FLAME.matrix_world.translation + Vector((0, 0, 0.012))
TIN2_C = TIN2.matrix_world.translation + Vector((0, 0, 0.02))
TIN1_C = TIN1.matrix_world.translation + Vector((0, 0, 0.02))
LOCK = P(1.475, 0.34, 1.05); GLOCK = P(2.53, 0.02, 1.05)
TORCH = O["TorchBFire"].matrix_world.translation.copy()
MOULD_C = P(11.40, 0.05, 0.985)
CAKE_REL_P, CAKE_REL_A = Vector((0.0, 0.17, 0.065)), Vector((0.0, 0.0, 0.045))
def cake_ws_cam(off): return CAKE_WS.matrix_world @ off
def cake_c_cam(off): return CAKE_C.matrix_world @ off
SIGN = P(8.65, 1.75, 2.50)

SEGS = [
  [  # A: cell, night
    (1,   lambda: hd(PRIS, 1) + P(0.50, -1.05, 0.02), lambda: hd(PRIS, 1).lerp(ow(MKEY, 1), 0.45), 32),
    (60,  lambda: hd(PRIS, 60) + P(0.36, -0.92, -0.04), lambda: hd(PRIS, 60).lerp(TIN1_C, 0.45), 33),
    (110, lambda: hd(PRIS, 110) + P(0.26, -0.72, -0.12), lambda: hd(PRIS, 110).lerp(TIN1_C, 0.60), 34),
    (150, lambda: TIN1_C + P(0.14, -0.50, 0.08), lambda: TIN1_C.lerp(hd(PRIS, 150), 0.48), 30),
    (195, lambda: TIN1_C + P(0.06, -0.46, 0.07), lambda: TIN1_C.lerp(hd(PRIS, 195), 0.45), 31),
    (225, lambda: TIN1_C + P(0.08, -0.25, 0.12), lambda: TIN1_C, 44),
    (262, lambda: TIN1_C + P(0.05, -0.24, 0.14), lambda: TIN1_C, 46),
    (292, lambda: hd(PRIS, 292) + P(0.45, -0.85, 0.02), lambda: hd(PRIS, 292).lerp(flame(292), 0.45), 30),
    (315, lambda: flame(315) + P(0.30, -0.06, 0.02), lambda: flame(315), 40),
    (328, lambda: flame(328) + P(0.10, -0.02, 0.005), lambda: flame(328), 48),
    (341, lambda: flame(341) + P(0.03, -0.006, 0.0), lambda: flame(341), 50),
  ],
  [  # B: lane at dusk, the workshop
    (341, lambda: TORCH + P(0.03, -0.06, -0.01), lambda: TORCH, 50),
    (356, lambda: P(7.15, 1.50, 1.95), lambda: hd(VIS, 356).lerp(TORCH, 0.2), 34),
    (385, lambda: P(7.95, -1.00, 1.75), lambda: hd(VIS, 385), 30),
    (410, lambda: P(8.35, -0.85, 1.85), lambda: hd(VIS, 410).lerp(SIGN, 0.5), 30),
    (470, lambda: P(8.70, -0.80, 1.90), lambda: hd(VIS, 470).lerp(SIGN, 0.5), 30),
    (500, lambda: P(10.25, -1.00, 1.75), lambda: hd(VIS, 500).lerp(hd(SMITH, 500), 0.5), 28),
    (530, lambda: P(11.15, -0.90, 1.62), lambda: hd(SMITH, 530).lerp(MOULD_C, 0.4), 30),
    (556, lambda: P(11.45, -0.70, 1.50), lambda: hd(SMITH, 556).lerp(MOULD_C, 0.55), 30),
    (578, lambda: MOULD_C + P(-0.24, -0.42, 0.30), lambda: MOULD_C + P(0.05, 0, 0.08), 36),
    (612, lambda: MOULD_C + P(-0.10, -0.22, 0.16), lambda: MOULD_C, 45),
    (640, lambda: MOULD_C + P(0.10, -0.26, 0.18), lambda: MOULD_C, 44),
    (672, lambda: MOULD_C + P(0.50, -0.75, 0.42), lambda: MOULD_C.lerp(hd(SMITH, 672), 0.45), 30),
    (686, lambda: P(11.65, -0.55, 1.25), lambda: cake_ws_cam(P(0, 0, 0.05)), 34),
    (700, lambda: cake_ws_cam(P(0.10, -0.40, 0.16)), lambda: cake_ws_cam(P(-0.08, -0.03, 0.04)), 40),
    (716, lambda: cake_ws_cam(P(-0.02, -0.27, 0.11)), lambda: cake_ws_cam(P(-0.09, -0.04, 0.03)), 50),
    (744, lambda: cake_ws_cam(P(-0.01, -0.26, 0.115)), lambda: cake_ws_cam(P(-0.08, -0.04, 0.03)), 50),
    (760, lambda: P(12.05, 0.60, 1.65), lambda: hd(VIS, 760).lerp(hd(SMITH, 760), 0.5), 24),
    (780, lambda: cake_ws_cam(P(0.05, 0.36, 0.14)), lambda: cake_ws_cam(P(0, 0, 0.05)), 38),
    (800, lambda: cake_ws_cam(CAKE_REL_P), lambda: cake_ws_cam(CAKE_REL_A), 40),
  ],
  [  # C: cell (the cake arrives) ... the escape
    (800, lambda: cake_c_cam(CAKE_REL_P), lambda: cake_c_cam(CAKE_REL_A), 40),
    (832, lambda: cake_c_cam(P(-0.05, 0.55, 0.38)), lambda: cake_c_cam(P(0, 0, 0.05)).lerp(hd(PRIS, 832), 0.5), 30),
    (868, lambda: P(1.15, -0.95, 1.40), lambda: cake_c_cam(P(-0.08, -0.05, 0.05)).lerp(hd(PRIS, 868), 0.35), 32),
    (905, lambda: P(1.38, -0.65, 1.55), lambda: hd(PRIS, 905).lerp(ow(KEY1, 905), 0.4), 30),
    (922, lambda: P(1.38, 0.70, 1.50), lambda: hd(PRIS, 922).lerp(ow(KEY1, 922), 0.4), 30),
    (945, lambda: P(1.30, 0.66, 1.40), lambda: hd(PRIS, 945).lerp(LOCK, 0.5), 32),
    (966, lambda: LOCK + P(-0.14, 0.40, 0.08), lambda: LOCK + P(-0.05, 0, 0.0), 38),
    (990, lambda: LOCK + P(-0.16, 0.42, 0.10), lambda: LOCK + P(-0.05, 0, 0.0), 40),
    (1012, lambda: LOCK + P(-0.16, 0.42, 0.10), lambda: LOCK + P(-0.05, 0, 0.02), 38),
    (1036, lambda: P(1.30, 0.70, 1.45), lambda: hd(PRIS, 1036), 32),
    (1046, lambda: P(1.30, 0.72, 1.55), lambda: P(-0.6, 1.62, 1.97), 60),
    (1052, lambda: P(1.25, 0.72, 1.56), lambda: P(-0.6, 1.62, 1.97), 100),
    (1064, lambda: P(1.15, 0.70, 1.56), lambda: P(-0.6, 1.62, 1.97), 100),
    (1084, lambda: P(-0.05, -0.35, 1.20), lambda: TIN2_C.lerp(hd(PRIS, 1084), 0.45), 32),
    (1104, lambda: TIN2_C + P(0.24, 0.02, 0.11), lambda: TIN2_C, 42),
    (1130, lambda: TIN2_C + P(0.10, -0.48, 0.08), lambda: TIN2_C.lerp(hd(PRIS, 1130), 0.45), 30),
    (1165, lambda: hd(PRIS, 1165) + P(0.62, -0.95, 0.05), lambda: hd(PRIS, 1165).lerp(flame(1165), 0.35), 30),
    (1210, lambda: hd(PRIS, 1210) + P(0.75, -0.85, 0.12), lambda: hd(PRIS, 1210).lerp(flame(1210), 0.3), 32),
    (1230, lambda: P(0.98, -0.45, 1.20), lambda: ow(CAKE_C2, 1230, (-0.04, -0.03, 0.05)), 42),
    (1246, lambda: P(1.00, -0.40, 1.18), lambda: ow(CAKE_C2, 1246, (-0.06, -0.04, 0.05)), 45),
    (1258, lambda: P(1.42, 0.00, 1.75), lambda: LOCK.lerp(hd(PRIS, 1258), 0.4), 30),
    (1272, lambda: P(1.40, 0.60, 1.55), lambda: hd(PRIS, 1272).lerp(LOCK, 0.5), 32),
    (1290, lambda: LOCK + P(-0.14, 0.40, 0.08), lambda: LOCK + P(-0.05, 0, 0.0), 38),
    (1318, lambda: LOCK + P(-0.16, 0.42, 0.10), lambda: LOCK + P(-0.05, 0, 0.0), 40),
    (1338, lambda: P(1.30, 0.70, 1.45), lambda: hd(PRIS, 1338), 32),
    (1356, lambda: P(1.48, 0.66, 1.50), lambda: hd(PRIS, 1356).lerp(P(2.3, 0.7, 1.4), 0.5), 30),
    (1372, lambda: P(1.95, 0.78, 1.68), lambda: hd(PRIS, 1372), 30),
    (1396, lambda: P(2.30, 0.80, 1.62), lambda: hd(PRIS, 1396), 30),
    (1422, lambda: P(2.22, 0.84, 1.50), lambda: hd(PRIS, 1422).lerp(GLOCK, 0.45), 30),
    (1448, lambda: P(2.36, 0.85, 1.42), lambda: hd(PRIS, 1448).lerp(GLOCK, 0.45), 30),
    (1480, lambda: P(2.40, 0.90, 1.55), lambda: hd(PRIS, 1480), 28),
    (1508, lambda: P(3.55, 0.20, 1.90), lambda: hd(PRIS, 1508), 28),
    (1532, lambda: P(4.30, 0.10, 1.95), lambda: hd(PRIS, 1532), 28),
    (1548, lambda: P(4.78, 0.10, 1.80), lambda: hd(PRIS, 1548).lerp(P(5.3, 0.7, 1.3), 0.3), 28),
    (1562, lambda: P(5.30, 0.55, 1.70), lambda: hd(PRIS, 1562), 30),
    (1576, lambda: P(6.05, 0.35, 1.65), lambda: hd(PRIS, 1576), 30),
    (1600, lambda: P(6.75, 0.25, 1.65), lambda: hd(PRIS, 1600), 32),
    (1622, lambda: P(7.00, 0.15, 1.70), lambda: hd(PRIS, 1622), 34),
  ],
  [  # D: years later, the steps, day
    (1622, lambda: P(40.35, -1.60, 1.30), lambda: P(40.0, 2.9, 2.0), 28),
    (1700, lambda: P(39.75, -0.80, 1.75), lambda: hd(PRIS, 1700) + P(0, 0, -0.35), 28),
    (1770, lambda: P(40.30, -0.30, 1.95), lambda: P(40.0, 2.8, 1.9), 26),
    (END, lambda: P(40.05, -0.55, 1.90), lambda: P(40.0, 2.8, 2.1), 24),
  ],
]
cam_d = bpy.data.cameras.new("CAM_Film"); CAM = bpy.data.objects.new("CAM_Film", cam_d); sc.collection.objects.link(CAM); sc.camera = CAM
AIM = bpy.data.objects.new("CAM_Film_Aim", None); sc.collection.objects.link(AIM)
cam_d.sensor_fit = 'AUTO'; cam_d.sensor_width = 36; cam_d.dof.use_dof = True; cam_d.dof.focus_object = AIM; cam_d.dof.aperture_fstop = 11.0
cam_d.clip_start = 0.006
CAM.rotation_mode = 'QUATERNION'
prevq = None
for si, seg in enumerate(SEGS):
    ks = [(f, pf(), af(), l) for f, pf, af, l in seg]
    fx = [pchip([(k[0], k[1][i]) for k in ks]) for i in range(3)]
    ax = [pchip([(k[0], k[2][i]) for k in ks]) for i in range(3)]
    fl = pchip([(k[0], k[3]) for k in ks])
    f0, f1 = ks[0][0], ks[-1][0]
    rng = range(f0 if si == 0 else f0 + (0 if si == 0 else 0), f1 + (1 if si == len(SEGS) - 1 else 0))
    if si > 0: rng = range(f0, f1 + (1 if si == len(SEGS) - 1 else 0))
    for f in rng:
        if si < len(SEGS) - 1 and f == f1: continue
        p = Vector([fx[i](f) for i in range(3)]); a = Vector([ax[i](f) for i in range(3)])
        zc = (p - a).normalized(); up = Vector((0, 0, 1)); yc = (up - zc * up.dot(zc)).normalized(); xc = yc.cross(zc)
        q = Matrix((xc, yc, zc)).transposed().to_quaternion()
        if prevq is not None and prevq.dot(q) < 0: q = -q
        prevq = q
        CAM.location = p; CAM.rotation_quaternion = q; AIM.location = a; cam_d.lens = fl(f)
        CAM.keyframe_insert("location", frame=f); CAM.keyframe_insert("rotation_quaternion", frame=f)
        AIM.keyframe_insert("location", frame=f); cam_d.keyframe_insert("lens", frame=f)
set_interp(CAM, 'LINEAR'); set_interp(AIM, 'LINEAR'); set_interp(cam_d, 'LINEAR')
# small catchlight riding with the camera (no black-hole eyes), scaled with distance
cl = bpy.data.lights.new("Catch", 'AREA'); cl.energy = 6.0; cl.size = 0.25; cl.color = (1, 0.96, 0.92)
clo = bpy.data.objects.new("Catchlight", cl); sc.collection.objects.link(clo); clo.parent = CAM; clo.location = (0.0, 0.10, 0.0)
for f in list(range(1, END + 1, 6)) + [END]:
    fs(f); d_ = (CAM.matrix_world.translation - AIM.matrix_world.translation).length
    cl.energy = max(0.15, min(6.0, 6.0 * (d_ / 0.9) ** 2)); cl.keyframe_insert("energy", frame=f)

# ================================================================== the glow void (camera-parented, camera rays only)
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=48, ring_count=24); VOID = bpy.context.active_object; VOID.name = "GlowVoid"
for p_ in VOID.data.polygons: p_.use_smooth = True
vm = bpy.data.materials.new("M_GlowVoid"); vm.use_nodes = True; nt = vm.node_tree
for n in list(nt.nodes):
    if n.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n)
tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sep.inputs[0])
mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = -0.8; mr.inputs["From Max"].default_value = 0.8
nt.links.new(sep.outputs["Y"], mr.inputs["Value"])
cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (1.0, 0.38, 0.04, 1); cr.color_ramp.elements[1].color = (1.0, 0.82, 0.35, 1)
nt.links.new(mr.outputs["Result"], cr.inputs["Fac"])
em = nt.nodes.new("ShaderNodeEmission"); nt.links.new(cr.outputs["Color"], em.inputs["Color"])
es = nt.nodes.new("ShaderNodeValue"); es.name = "GlowStrength"; es.outputs[0].default_value = 1.2; nt.links.new(es.outputs[0], em.inputs["Strength"])
tr = nt.nodes.new("ShaderNodeBsdfTransparent"); lp = nt.nodes.new("ShaderNodeLightPath")
av = nt.nodes.new("ShaderNodeValue"); av.name = "VoidAlpha"; av.outputs[0].default_value = 0.0
mul = nt.nodes.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'; nt.links.new(lp.outputs["Is Camera Ray"], mul.inputs[0]); nt.links.new(av.outputs[0], mul.inputs[1])
mx = nt.nodes.new("ShaderNodeMixShader"); nt.links.new(mul.outputs[0], mx.inputs["Fac"]); nt.links.new(tr.outputs["BSDF"], mx.inputs[1]); nt.links.new(em.outputs["Emission"], mx.inputs[2])
nt.links.new(mx.outputs["Shader"], nt.nodes["Material Output"].inputs["Surface"])
VOID.data.materials.append(vm)
VOID.visible_shadow = False; VOID.visible_diffuse = False; VOID.visible_glossy = False; VOID.visible_transmission = False
VOID.parent = CAM; VOID.matrix_parent_inverse = Matrix.Identity(4); VOID.location = (0, 0, 0); VOID.scale = (0.05, 0.05, 0.05)
VA, VS = av.outputs[0], es.outputs[0]
for f, a, st in ((1, 0.0, 0.15), (330, 0.0, 0.15), (337, 1.0, 0.18), (346, 1.0, 0.18), (354, 0.0, 0.15),
                 (1610, 0.0, 0.9), (1617, 1.0, 1.1), (1626, 1.0, 1.1), (1636, 0.0, 0.9), (END, 0.0, 0.9)):
    VA.default_value = a; VA.keyframe_insert("default_value", frame=f); VS.default_value = st; VS.keyframe_insert("default_value", frame=f)
vis(VOID, 1, False); vis(VOID, 329, True); vis(VOID, 356, False); vis(VOID, 1609, True); vis(VOID, 1638, False)

# ================================================================== sky and sun per time of day (world seen by camera rays only)
w = sc.world; nt = w.node_tree
for n in list(nt.nodes):
    if n.type != 'OUTPUT_WORLD': nt.nodes.remove(n)
out = [n for n in nt.nodes if n.type == 'OUTPUT_WORLD'][0]
tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Generated"], sep.inputs[0])
mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.48; mr.inputs["From Max"].default_value = 0.62; nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
hz = nt.nodes.new("ShaderNodeRGB"); hz.name = "Horizon"; ze = nt.nodes.new("ShaderNodeRGB"); ze.name = "Zenith"
mxc = nt.nodes.new("ShaderNodeMix"); mxc.data_type = 'RGBA'; nt.links.new(mr.outputs["Result"], mxc.inputs["Factor"])
nt.links.new(hz.outputs[0], mxc.inputs['A']); nt.links.new(ze.outputs[0], mxc.inputs['B'])
bgc = nt.nodes.new("ShaderNodeBackground"); nt.links.new(mxc.outputs['Result'], bgc.inputs["Color"]); bgc.inputs["Strength"].default_value = 1.0
bgl = nt.nodes.new("ShaderNodeBackground"); nt.links.new(mxc.outputs['Result'], bgl.inputs["Color"])
lpw = nt.nodes.new("ShaderNodeLightPath"); mxs = nt.nodes.new("ShaderNodeMixShader")
nt.links.new(lpw.outputs["Is Camera Ray"], mxs.inputs["Fac"]); nt.links.new(bgl.outputs[0], mxs.inputs[1]); nt.links.new(bgc.outputs[0], mxs.inputs[2])
nt.links.new(mxs.outputs[0], out.inputs["Surface"])
for f, h_, z_, ls in ((1, (0.10, 0.08, 0.35), (0.02, 0.02, 0.12), 0.10), (340, (0.10, 0.08, 0.35), (0.02, 0.02, 0.12), 0.10),
                      (341, (1.0, 0.42, 0.18), (0.22, 0.10, 0.50), 0.25), (799, (1.0, 0.42, 0.18), (0.22, 0.10, 0.50), 0.25),
                      (800, (0.16, 0.10, 0.45), (0.03, 0.03, 0.18), 0.10), (1621, (0.25, 0.14, 0.55), (0.04, 0.05, 0.25), 0.12),
                      (1622, (0.75, 0.92, 1.0), (0.20, 0.55, 1.0), 0.8), (END, (0.75, 0.92, 1.0), (0.20, 0.55, 1.0), 0.8)):
    hz.outputs[0].default_value = (*h_, 1); hz.outputs[0].keyframe_insert("default_value", frame=f)
    ze.outputs[0].default_value = (*z_, 1); ze.outputs[0].keyframe_insert("default_value", frame=f)
    bgl.inputs["Strength"].default_value = ls; bgl.inputs["Strength"].keyframe_insert("default_value", frame=f)
for fc in iter_fcurves(w.node_tree.animation_data.action):
    for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
def key_light(name, frames):
    L = O[name].data
    for f, e, c in frames:
        L.energy = e; L.keyframe_insert("energy", frame=f)
        if c: L.color = c; L.keyframe_insert("color", frame=f)
    for fc in iter_fcurves(L.animation_data.action):
        for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
key_light("SunDusk", [(1, 2.2, (1.0, 0.55, 0.30)), (800, 0.9, (0.45, 0.55, 1.0)), (1622, 0.0, None)])
key_light("SunDay", [(1, 0.0, None), (1622, 4.0, None)])
key_light("EXT_Fill", [(1, 260, (0.55, 0.60, 1.0)), (800, 200, (0.45, 0.50, 1.0)), (1622, 0, None)])
# cell window: night -> dawn while he waits; the moon light warms
WS_ = bpy.data.materials["M_CellSky"].node_tree
ramp = [n for n in WS_.nodes if n.type == 'VALTORGB'][0]
for f, c0, c1 in ((1, (0.05, 0.10, 0.45), (0.01, 0.02, 0.15)), (1120, (0.05, 0.10, 0.45), (0.01, 0.02, 0.15)), (1230, (1.0, 0.55, 0.25), (0.35, 0.30, 0.75)), (END, (1.0, 0.55, 0.25), (0.35, 0.30, 0.75))):
    ramp.color_ramp.elements[0].color = (*c0, 1); ramp.color_ramp.elements[1].color = (*c1, 1)
    ramp.color_ramp.elements[0].keyframe_insert("color", frame=f); ramp.color_ramp.elements[1].keyframe_insert("color", frame=f)
L = O["CELL_Moon"].data
for f, e, c in ((1, 80, (0.45, 0.60, 1.0)), (1120, 80, (0.45, 0.60, 1.0)), (1230, 120, (1.0, 0.70, 0.45)), (END, 120, (1.0, 0.70, 0.45))):
    L.energy = e; L.color = c; L.keyframe_insert("energy", frame=f); L.keyframe_insert("color", frame=f)
# STEPS island hidden until the flash (nothing there can block rays earlier)
for o_ in O:
    if o_.get("island") == "SET_STEPS" or o_.name.startswith("ST_"):
        vis(o_, 1, False); vis(o_, 1620, True)

# ================================================================== VO, output, cleanup
sc.frame_start, sc.frame_end = 1, END
if not sc.sequence_editor: sc.sequence_editor_create()
vo = "/home/user/Muhammed/blender/PrisonKeyCake_v011/PrisonKeyCake_v011_VO.mp3"
try:
    se = sc.sequence_editor; strips = se.strips if hasattr(se, "strips") else se.sequences
    strips.new_sound("VO", vo, 1, 1)
except Exception as e:
    log("vo strip failed", e)
for r in (PRIS, VIS, SMITH): log("quat flips fixed", r.name, quat_continuity(r))
sc.frame_set(1)
sc.render.filepath = "//render/PrisonKeyCake_v011_####.png"; sc.render.image_settings.file_format = 'PNG'
log("camera done")
