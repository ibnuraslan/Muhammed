# Part 2 of 03_animate.py: bricks + props baked to hands/noses, cross-section bricks, FX, lights, tunnels, the one camera.
PR = bpy.data.collections["Props"]
XS = 6.0
XSM = bpy.data.objects["XS_Head"].matrix_world.copy()
def flat(name, col, rough=0.5, metal=0.0, sss=0.0, transm=0.0, emit=None, es=0.0, coat=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b_ = m.node_tree.nodes["Principled BSDF"]
    b_.inputs["Base Color"].default_value = (*col, 1); b_.inputs["Roughness"].default_value = rough; b_.inputs["Metallic"].default_value = metal
    if sss: b_.inputs["Subsurface Weight"].default_value = sss
    if transm: b_.inputs["Transmission Weight"].default_value = transm
    if emit: b_.inputs["Emission Color"].default_value = (*emit, 1); b_.inputs["Emission Strength"].default_value = es
    if coat: b_.inputs["Coat Weight"].default_value = coat
    return m
def link(o, c):
    for cc in o.users_collection: cc.objects.unlink(o)
    c.objects.link(o); return o
def box(name, c, size, loc, mat=None, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = bpy.context.active_object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel: bm_ = o.modifiers.new("bev", "BEVEL"); bm_.width = bevel; bm_.segments = 2
    if mat: o.data.materials.append(mat)
    return link(o, c)
def key_obj(o, f, M_, scale=None):
    loc, rot, sca = M_.decompose()
    o.rotation_mode = "QUATERNION"
    o.location = loc; o.keyframe_insert("location", frame=f)
    if o.rotation_quaternion.dot(rot) < 0: rot = -rot
    o.rotation_quaternion = rot; o.keyframe_insert("rotation_quaternion", frame=f)
    if scale is not None:
        o.scale = (scale,) * 3; o.keyframe_insert("scale", frame=f)
def hand_M(c, s):
    """orientation frame of a hand: x = across palm, y = finger direction, z = palm normal (world)"""
    wr = c.bone_world("wrist." + s); f3 = c.bone_world("finger3-1." + s); f2 = c.bone_world("finger2-1." + s); f5 = c.bone_world("finger5-1." + s)
    d = (f3 - wr).normalized(); a = (f2 - f5).normalized(); n = d.cross(a).normalized(); a = n.cross(d).normalized()
    return Matrix((a, d, n)).transposed()
BIG, SMALL = bpy.data.objects["Brick_Big"], bpy.data.objects["Brick_Small"]
NOSE_IN = {"Boy": V(0.0085, 0.006, -0.010), "Man": V(0.0105, 0.008, -0.013)}  # nostril inner point, head space offset from nose tip
def nostril_M(c, depth=0.0, tilt=0.0):
    hm = c.head_M(); base = Vector(NOSE_REST_C[c.name]) + NOSE_IN[c.name] + V(0, depth * 0.6, depth)
    R = hm.to_3x3().normalized() @ Matrix.Rotation(R_(-60 + tilt), 3, "X")
    return Matrix.Translation(hm @ base) @ R.to_4x4()
def pinch_M(c, s, off=V(0, 0, 0)):
    p = c.pinch(s); R = hand_M(c, s)
    return Matrix.Translation(p + R @ off) @ R.to_4x4()
def bake(o, f0, f1, fn, step=2):
    for f in list(range(f0, f1 + 1, step)) + [f1]:
        ev(f); key_obj(o, f, fn(f))
# --- red (big) brick: in hand -> into the left nostril -> stuck (2/3 inside) -> tweezers -> held up
TUB_TOP = Matrix.Translation(TUBW + V(0.02, -0.02, 0.105))
bake(BIG, 1, 130, lambda f: pinch_M(B, "R", V(0, 0.004, -0.004)))
def into(f, f0, f1, depth0, depth1):
    t = smooth((f - f0) / (f1 - f0)); A_ = pinch_M(B, "R", V(0, 0.004, -0.004)); B_ = nostril_M(B, depth0 + (depth1 - depth0) * t)
    return A_.lerp(B_, t) if hasattr(A_, "lerp") else B_
def lerpM(A_, B_, t):
    la, ra, _ = A_.decompose(); lb, rb, _ = B_.decompose()
    return Matrix.Translation(la.lerp(lb, t)) @ ra.slerp(rb, t).to_matrix().to_4x4()
bake(BIG, 132, 150, lambda f: lerpM(pinch_M(B, "R", V(0, 0.004, -0.004)), nostril_M(B, 0.004 * smooth((f - 132) / 18)), smooth((f - 132) / 10)))
def stuck(f):
    wig = 6 * math.sin((f - 150) * 0.5) * (1 - smooth((f - 150) / 90)) if f < 240 else 0
    d = 0.004 + (0.002 if f > 740 else 0.0)
    return nostril_M(B, d, tilt=wig)
bake(BIG, 152, 1040, stuck, step=4)
TWZ = bpy.data.objects.new("Prop_Tweezers", None); PR.objects.link(TWZ)
mt = flat("M_Tweezers", (0.85, 0.85, 0.88), 0.2, metal=1.0)
for i, sx in enumerate((-1, 1)):
    bpy.ops.mesh.primitive_cube_add(size=1); arm_ = bpy.context.active_object; arm_.name = "Prop_TweezerArm%d" % i; link(arm_, PR)
    arm_.scale = (0.0016, 0.085, 0.0008); bpy.ops.object.transform_apply(scale=True)
    arm_.data.materials.append(mt); arm_.parent = TWZ; arm_.location = (sx * 0.0035, 0.042, 0); arm_.rotation_euler = (0, 0, R_(-sx * 2.2))
def twz_M(f):
    ev(f); p = W.pinch("R"); nz = B.nose(1.0); d = (nz - p).normalized()
    up = V(0, 0, 1); a = d.cross(up).normalized(); n = a.cross(d)
    return Matrix.Translation(p) @ Matrix((a, d, n)).transposed().to_4x4()
bake(TWZ, 960, 1145, twz_M, step=3)
def twz_tip(f):
    M_ = twz_M(f); return Matrix.Translation(M_ @ V(0, 0.088, 0)) @ M_.to_3x3().to_4x4()
bake(BIG, 1042, 1058, lambda f: lerpM(nostril_M(B, 0.004), twz_tip(f), smooth((f - 1042) / 14)))
bake(BIG, 1060, 1145, twz_tip, step=3)
key_vis(["Brick_Big"], [(1, 1146)])
key_vis(["Prop_Tweezers"], [(960, 1146)])
# --- beat 1 cutaway porthole: a round window opens in the side of his nose, showing the brick in the passage (clean cyan look)
XC = bpy.data.objects.new("XRay_Center", None); PR.objects.link(XC)
bake(XC, 140, 250, lambda f: nostril_M(B, 0.004), step=2)
PORT = ((1, 0.0), (150, 0.0), (162, 0.016), (232, 0.016), (244, 0.0))
skin = bpy.data.objects["Boy_Body"].material_slots[0].material; nt = skin.node_tree
outn = [n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"][0]; lk = [l for l in nt.links if l.to_node == outn and l.to_socket.name == "Surface"][0]
src = lk.from_socket
tc = nt.nodes.new("ShaderNodeTexCoord"); tc.object = XC
ln = nt.nodes.new("ShaderNodeVectorMath"); ln.operation = "LENGTH"; nt.links.new(tc.outputs["Object"], ln.inputs[0])
rad = nt.nodes.new("ShaderNodeValue"); rad.name = "PortRadius"
for f, r in PORT: rad.outputs[0].default_value = r; rad.outputs[0].keyframe_insert("default_value", frame=f)
lt_ = nt.nodes.new("ShaderNodeMath"); lt_.operation = "LESS_THAN"; nt.links.new(ln.outputs["Value"], lt_.inputs[0]); nt.links.new(rad.outputs[0], lt_.inputs[1])
rimr = nt.nodes.new("ShaderNodeMath"); rimr.operation = "MULTIPLY"; rimr.inputs[1].default_value = 1.15; nt.links.new(rad.outputs[0], rimr.inputs[0])
rim = nt.nodes.new("ShaderNodeMath"); rim.operation = "LESS_THAN"; nt.links.new(ln.outputs["Value"], rim.inputs[0]); nt.links.new(rimr.outputs[0], rim.inputs[1])
trn = nt.nodes.new("ShaderNodeBsdfTransparent")
em = nt.nodes.new("ShaderNodeEmission"); em.inputs[0].default_value = (0.4, 0.9, 1.0, 1); em.inputs[1].default_value = 1.5
m1 = nt.nodes.new("ShaderNodeMixShader"); nt.links.new(rim.outputs[0], m1.inputs[0]); nt.links.new(src, m1.inputs[1]); nt.links.new(em.outputs[0], m1.inputs[2])
m2 = nt.nodes.new("ShaderNodeMixShader"); nt.links.new(lt_.outputs[0], m2.inputs[0]); nt.links.new(m1.outputs[0], m2.inputs[1]); nt.links.new(trn.outputs[0], m2.inputs[2])
nt.links.new(m2.outputs[0], outn.inputs["Surface"])
# inside the porthole: mucosa passage + cyan backdrop, following the head
port_root = bpy.data.objects.new("XRay_Inside", None); PR.objects.link(port_root)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.014, segments=24, ring_count=12); bk_ = bpy.context.active_object; bk_.name = "XRay_Backdrop"; link(bk_, PR)
bk_.data.materials.append(flat("M_XRayBack", (0.6, 0.9, 1.0), 0.5, emit=(0.55, 0.88, 1.0), es=1.2)); bk_.parent = port_root
bpy.ops.mesh.primitive_cylinder_add(radius=0.0075, depth=0.03, vertices=24); pas = bpy.context.active_object; pas.name = "XRay_Passage"; link(pas, PR)
pas.data.materials.append(flat("M_XRayMucosa", (0.75, 0.25, 0.28), 0.3, sss=0.2, coat=0.5)); pas.parent = port_root; pas.location = (0, 0, 0.008)
def inside_only(m_):
    t_ = m_.node_tree; o_ = t_.nodes["Material Output"]; src_ = o_.inputs["Surface"].links[0].from_socket
    g_ = t_.nodes.new("ShaderNodeNewGeometry"); tr_ = t_.nodes.new("ShaderNodeBsdfTransparent"); mx_ = t_.nodes.new("ShaderNodeMixShader")
    t_.links.new(g_.outputs["Backfacing"], mx_.inputs[0]); t_.links.new(tr_.outputs[0], mx_.inputs[1]); t_.links.new(src_, mx_.inputs[2])
    t_.links.new(mx_.outputs[0], o_.inputs["Surface"])
for o_ in (bk_, pas):
    for p_ in o_.data.polygons: p_.use_smooth = True
    inside_only(o_.data.materials[0])
bk_.data.materials[0].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 0.35
pl_ = bpy.data.objects.new("XRay_Light", bpy.data.lights.new("XRay_Light", "POINT")); PR.objects.link(pl_); pl_.parent = port_root
pl_.location = (0, -0.006, 0.0); pl_.data.energy = 0.03; pl_.data.shadow_soft_size = 0.002; pl_.data.color = (0.9, 0.97, 1.0)
bake(port_root, 140, 250, lambda f: nostril_M(B, 0.004), step=2)
key_vis(["XRay_Inside"], [(150, 246)])
# --- yellow (small) brick: in the tub -> hand -> dream -> nostril (disappears) ... shower: shoots out into the palm
key_obj(SMALL, 1, TUB_TOP @ Matrix.Rotation(R_(20), 4, "Z")); key_obj(SMALL, 332, TUB_TOP @ Matrix.Rotation(R_(20), 4, "Z"))
bake(SMALL, 336, 712, lambda f: pinch_M(B, "R", V(0, 0.003, -0.003)))
bake(SMALL, 714, 736, lambda f: lerpM(pinch_M(B, "R", V(0, 0.003, -0.003)), nostril_M(B, 0.0), smooth((f - 714) / 18)))
bake(SMALL, 738, 744, lambda f: nostril_M(B, 0.006 + 0.002 * (f - 738)))
def shoot(f):
    ev(f); t = (f - 2088) / 62.0
    a = nostril_M(M, 0.0).translation; b_ = M_PALM_W(f)
    p = a.lerp(b_, smooth(t)) + V(0, 0, 0.05 * math.sin(math.pi * min(1, t)))
    return Matrix.Translation(p) @ Euler((t * 7.0, t * 4.0, t * 2.0)).to_matrix().to_4x4()
def M_PALM_W(f):
    ev(f); R = hand_M(M, "L"); return M.bone_world("finger3-1.L") + R @ V(0, -0.01, 0.022)
bake(SMALL, 2086, 2088, lambda f: nostril_M(M, 0.004))
bake(SMALL, 2090, 2150, shoot)
bake(SMALL, 2152, 2310, lambda f: Matrix.Translation(M_PALM_W(f)) @ (hand_M(M, "L").to_4x4()) @ Matrix.Rotation(R_(90), 4, "X"), step=3)
key_vis(["Brick_Small"], [(1, 745), (2086, 2400)])
# --- dream bricks (beat 3): floating macro, the yellow one snaps onto the red one with a click flash
DR, DY = BIG.copy(), SMALL.copy(); DR.data = BIG.data; DY.data = SMALL.data; DR.name = "Dream_Red"; DY.name = "Dream_Yellow"
for o in (DR, DY): PR.objects.link(o); o.animation_data_clear()
ev(500); DREAM = B.nose(0.0) + (B.head_M().to_3x3() @ V(0, -1, 0)).normalized() * 0.15 + V(-0.02, 0, -0.01)
SNAP = 517
for f in range(457, 632, 2):
    t = f - 457; spin = R_(t * 1.4)
    base = Matrix.Translation(DREAM + V(0, 0, 0.006 * math.sin(t * 0.08))) @ Matrix.Rotation(spin, 4, "Z") @ Matrix.Rotation(R_(25), 4, "X")
    key_obj(DR, f, base, scale=2.2)
    if f < SNAP:
        u = smooth((f - 457) / (SNAP - 457))
        off = V(0.05 * (1 - u), 0, 0.012 + 0.04 * (1 - u) ** 1.5)
    else:
        off = V(0, 0, 0.0096 * 2.2 - 0.0012 * max(0, 1 - (f - SNAP) / 6.0))
    if f > 570:   # both pulled out together, drifting away to the left
        dd = smooth((f - 570) / 60.0); base = Matrix.Translation(V(-0.12 * dd, -0.05 * dd, 0.05 * dd)) @ base
        key_obj(DR, f, base, scale=2.2)
    key_obj(DY, f, base @ Matrix.Translation(off / 2.2), scale=2.2)
key_vis(["Dream_Red", "Dream_Yellow"], [(457, 632)])
flash = bpy.data.objects.new("FX_ClickFlash", bpy.data.lights.new("FX_ClickFlash", "POINT")); PR.objects.link(flash)
flash.location = DREAM + V(0, -0.02, 0.03); flash.data.shadow_soft_size = 0.01; flash.data.color = (1.0, 0.95, 0.8)
for f, e in ((1, 0), (SNAP - 1, 0), (SNAP + 1, 5), (SNAP + 5, 1.5), (SNAP + 14, 0)):
    flash.data.energy = e; flash.data.keyframe_insert("energy", frame=f)
spk_m = flat("M_Sparkle", (1, 1, 1), 0.3, emit=(1.0, 0.9, 0.6), es=30)
for i in range(16):
    bpy.ops.mesh.primitive_ico_sphere_add(radius=0.0018, subdivisions=1); s_ = bpy.context.active_object; s_.name = "FX_Sparkle%02d" % i; link(s_, PR)
    s_.data.materials.append(spk_m); d = Vector((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-0.3, 1))).normalized()
    for f in (SNAP, SNAP + 4, SNAP + 12, SNAP + 24):
        u = (f - SNAP) / 24.0; s_.location = flash.location + d * (0.07 * (1 - (1 - u) ** 2)); s_.keyframe_insert("location", frame=f)
        s_.scale = (max(0.01, 1 - u),) * 3; s_.keyframe_insert("scale", frame=f)
    key_vis([s_.name], [(SNAP, SNAP + 25)])
# --- cross-section bricks: wedge deeper (beat 5), then the hidden glowing yellow one (beat 7)
XSB, XSS = bpy.data.objects["XS_Brick_Big"], bpy.data.objects["XS_Brick_Small"]
ny_, zc_, L__, Hh_, XC_ = sc["XS_P"]
def Prest(u, v, dx=0.002): return V(XC_ + dx, ny_ + u * L__, zc_ + v * Hh_)
def xsM(u, v, ang, dx=-0.004):
    return XSM @ Matrix.Translation(Prest(u, v, dx)) @ Matrix.Rotation(R_(ang), 4, "X") @ Matrix.Rotation(R_(90), 4, "Y")
for o, keys in ((XSB, ((740, 0.06, 0.34, -40), (800, 0.07, 0.355, -45), (840, 0.10, 0.38, -50), (860, 0.11, 0.385, -52))),
                (XSS, ((740, 0.02, 0.32, -35), (770, 0.05, 0.34, -40), (800, 0.12, 0.39, -50), (840, 0.17, 0.43, -58), (870, 0.18, 0.44, -60),
                       (1130, 0.19, 0.455, -62), (1320, 0.19, 0.455, -62)))):
    for f, u, v, a in keys:
        key_obj(o, f, xsM(u, v, a), scale=XS)
key_obj(XSB, 1130, xsM(0.4, 0.2, 0, dx=-1.0), scale=0.01)    # gone (pulled out) when we return
const_at(XSB, {860})
# both cross-section bricks glow a little for readability (own object-level materials)
for o_, col_ in ((XSB, (0.85, 0.06, 0.04)), (XSS, (1.0, 0.75, 0.1))):
    mg = flat("M_XSGlow_" + o_.name, col_, 0.15, emit=col_, es=0.6, coat=0.8)
    o_.material_slots[0].link = "OBJECT"; o_.material_slots[0].material = mg
gnode = bpy.data.materials["M_XSGlow_XS_Brick_Small"].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
for f, e in ((1, 0.6), (1150, 0.6), (1185, 3.0), (1250, 4.5), (1320, 3.0)):
    gnode.default_value = e; gnode.keyframe_insert("default_value", frame=f)
MB_YEL = bpy.data.materials["M_Brick_Yellow"]   # glow keyed on the shared material: only visible in the studio (room brick hidden then)
eo = MB_YEL.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
for f, e in ((1, 0), (1150, 0), (1185, 2.5), (1250, 4.0), (1320, 3.0), (1345, 0)):
    eo.default_value = e; eo.keyframe_insert("default_value", frame=f)
glow = bpy.data.objects.new("FX_BrickGlow", bpy.data.lights.new("FX_BrickGlow", "POINT")); PR.objects.link(glow)
glow.location = xsM(0.19, 0.455, -62, dx=-0.004).translation; glow.data.color = (1.0, 0.8, 0.3); glow.data.shadow_soft_size = 0.05
for f, e in ((1, 0), (1150, 0), (1185, 12), (1320, 12), (1345, 0)):
    glow.data.energy = e; glow.data.keyframe_insert("energy", frame=f)
# mucosa 'breathing' in the studio: the airway lining pulses
lin = bpy.data.objects["XS_AirwayLining"]
for f in range(740, 1340, 30):
    lin.data.bevel_depth = 0.0015 * (1.0 + 0.25 * math.sin(f * 0.21)); lin.data.keyframe_insert("bevel_depth", frame=f)

# --- time-lapse props: gamepad in the teen's hands, laptop on the man's thighs; the toys are gone after childhood
gp = bpy.data.objects["Prop_Gamepad"]
lp = box("Prop_Phone", PR, (0.072, 0.148, 0.008), (50, 50, 0), flat("M_Phone", (0.02, 0.02, 0.025), 0.2, metal=0.3, coat=0.8), bevel=0.006)
scr = box("Prop_PhoneScreen", PR, (0.064, 0.136, 0.001), (0, 0, 0.0042), flat("M_PhoneScreen", (0.1, 0.15, 0.2), 0.1, emit=(0.55, 0.7, 0.95), es=3.0))
scr.parent = lp
for f, p in TEEN_PAD.items():
    key_obj(gp, f, Matrix.Translation(p + V(0, 0, 0.02)) @ Matrix.Rotation(R_(-35), 4, "X"))
for f, p in MAN_LAP.items():
    ev(f); key_obj(lp, f, Matrix.Translation((M.pinch("L") + M.pinch("R")) / 2 + V(0, 0, 0.01)) @ Matrix.Rotation(R_(40), 4, "X"))
key_vis(["Prop_Gamepad"], [(1395, 1439)]); key_vis(["Prop_Phone"], [(1440, 1469)])
for o in bpy.data.objects:
    if o.name.startswith(("TubBrick", "RugBrick", "HouseBrick", "Prop_Tub")):
        for f, v in ((1, False), (1395, True)):
            o.hide_render = v; o.keyframe_insert("hide_render", frame=f)
# --- tissues + inhaler (beat 9)
for i in range(14):
    key_vis(["LR_TissueBall%02d" % i], [(1470, 1746)])
bpy.ops.mesh.primitive_ico_sphere_add(radius=0.04, subdivisions=3); tis = bpy.context.active_object; tis.name = "Prop_Tissue"; link(tis, PR)
tis.data.materials.append(bpy.data.materials["M_Tissue"]); sub = tis.modifiers.new("s", "SUBSURF"); sub.levels = 2
dsp = tis.modifiers.new("d", "DISPLACE"); dsp.texture = bpy.data.textures["TissueNoise"]; dsp.strength = 0.025; tis.scale = (1.0, 1.3, 0.8)
bake(tis, 1515, 1582, lambda f: pinch_M(M, "R", V(0, 0.005, 0.0)))
key_vis(["Prop_Tissue"], [(1515, 1583)])
inh = bpy.data.objects.new("Prop_Inhaler", None); PR.objects.link(inh)
for nm, sz, lc, col in (("Can", (0.026, 0.026, 0.07), (0, 0, 0.03), (0.75, 0.75, 0.78)), ("Body", (0.03, 0.034, 0.09), (0, 0, 0.0), (0.25, 0.45, 0.75)),
                        ("Mouth", (0.028, 0.04, 0.022), (0, -0.03, -0.045), (0.25, 0.45, 0.75))):
    o = box("Prop_Inhaler" + nm, PR, sz, (0, 0, 0), flat("M_Inh" + nm, col, 0.35, metal=0.8 if nm == "Can" else 0.0), bevel=0.003)
    o.parent = inh; o.location = lc
bake(inh, 1606, 1720, lambda f: pinch_M(M, "R", V(0, 0.0, 0.0)) @ Matrix.Rotation(R_(-70), 4, "X"))
key_vis(["Prop_Inhaler"], [(1606, 1721)])
# --- duvet over the man in bed (follows the hips)
bpy.ops.mesh.primitive_plane_add(size=1); duv = bpy.context.active_object; duv.name = "BR_Duvet"; link(duv, bpy.data.collections["Set_Bedroom"])
duv.scale = (0.95, 1.25, 1); bpy.ops.object.transform_apply(scale=True)
for p_ in duv.data.polygons: p_.use_smooth = True
duv.data.materials.append(bpy.data.materials.get("M_Duvet") or flat("M_Duvet", (0.25, 0.33, 0.5), 0.9, sss=0.05)); so_ = duv.modifiers.new("sol", "SOLIDIFY"); so_.thickness = 0.04
ss_ = duv.modifiers.new("sub", "SUBSURF"); ss_.levels = 2; ss_.render_levels = 2
dtx = bpy.data.textures.new("DuvetNoise", "CLOUDS"); dtx.noise_scale = 0.35
dd_ = duv.modifiers.new("dsp", "DISPLACE"); dd_.texture = dtx; dd_.strength = 0.07
ss_.levels = ss_.render_levels = 3
for f in list(range(1724, 1869, 6)):
    ev(f); hp = M.bone_world("root"); kn = (M.bone_world("lowerleg01.L") + M.bone_world("lowerleg01.R")) / 2
    sit = 0.0
    duv.location = V(5.1, hp.y - 0.5, 0.74 + 0.1 * max(0.0, min(1.0, (kn.z - 0.7) / 0.3))); duv.keyframe_insert("location", frame=f)
    duv.rotation_euler = (R_(-6 + 10 * math.sin(f * 0.2)), R_(4 * math.sin(f * 0.13)), 0); duv.keyframe_insert("rotation_euler", frame=f)

key_vis(["BR_Duvet"], [(1722, 1870)])
# --- shower water streaks + steam
WM = flat("M_Water", (0.9, 0.95, 1.0), 0.02, transm=1.0)
for i in range(46):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.0016, depth=0.14, vertices=6); o = bpy.context.active_object; o.name = "FX_Water%02d" % i; link(o, bpy.data.collections["Set_Bathroom"])
    o.data.materials.append(WM)
    a = random.random() * 2 * math.pi; r = 0.09 * math.sqrt(random.random())
    x, y = 8.6 + r * math.cos(a) - 0.12 * random.random(), 1.95 + r * math.sin(a) - 0.1 * random.random()
    ph = random.random()
    o.location = (x, y, 2.0); o.keyframe_insert("location", frame=1, index=2)
    o.location = (x, y, 0.1); o.keyframe_insert("location", frame=31, index=2)
    fc = [c for c in all_fcurves(o.animation_data.action) if c.data_path == "location" and c.array_index == 2][0]
    for kp in fc.keyframe_points: kp.interpolation = "LINEAR"
    cm = fc.modifiers.new("CYCLES"); fc.modifiers[0].mode_before = fc.modifiers[0].mode_after = "REPEAT"
    o.location.x, o.location.y = x, y
    fcx = None
    # phase offset per streak
    for kp in fc.keyframe_points: kp.co.x += ph * 30; kp.handle_left.x += ph * 30; kp.handle_right.x += ph * 30
    key_vis([o.name], [(1860, 2400)])
bpy.ops.mesh.primitive_cube_add(size=1, location=(7.7, 1.3, 1.3)); stm = bpy.context.active_object; stm.name = "FX_Steam"; link(stm, bpy.data.collections["Set_Bathroom"])
stm.scale = (2.4, 2.4, 2.4)
vm = bpy.data.materials.new("M_Steam"); vm.use_nodes = True; N = vm.node_tree.nodes; Lk = vm.node_tree.links
N.remove(N["Principled BSDF"]); pv = N.new("ShaderNodeVolumePrincipled"); nz_ = N.new("ShaderNodeTexNoise"); nz_.inputs["Scale"].default_value = 1.5
mr = N.new("ShaderNodeMapRange"); mr.inputs[1].default_value = 0.45; mr.inputs[2].default_value = 0.75; mr.inputs[3].default_value = 0.0; mr.inputs[4].default_value = 0.12
Lk.new(nz_.outputs[0], mr.inputs[0]); Lk.new(mr.outputs[0], pv.inputs["Density"]); Lk.new(pv.outputs[0], N["Material Output"].inputs["Volume"])
stm.data.materials.append(vm)
key_vis(["FX_Steam"], [(1880, 2400)])
# --- dust motes in the living-room sunbeam
dm = flat("M_Dust", (1, 1, 1), 0.5, emit=(1.0, 0.95, 0.85), es=2.0)
for i in range(40):
    bpy.ops.mesh.primitive_ico_sphere_add(radius=0.0012, subdivisions=1); o = bpy.context.active_object; o.name = "FX_Dust%02d" % i; link(o, PR); o.data.materials.append(dm)
    p0 = V(random.uniform(-1.5, 0.8), random.uniform(-0.6, 1.8), random.uniform(0.3, 1.8))
    for f in (1, 700, 1400):
        o.location = p0 + V(0.15 * math.sin(f * 0.003 + i), 0.1 * math.cos(f * 0.002 + i), 0.12 * math.sin(f * 0.0025 + i * 2)); o.keyframe_insert("location", frame=f)
    key_vis([o.name], [(1, 1470)])
# --- the cat breathes (and startles at the panic)
catr = bpy.data.objects.get("LR_Cat")
if catr:
    s0 = catr.scale.x; z0 = catr.location.z
    for f in range(1, 2311, 40):
        catr.scale = (s0, s0, s0 * (1.0 + 0.025 * (1 if (f // 40) % 2 else -1))); catr.keyframe_insert("scale", frame=f)
    for f, dz in ((895, 0.0), (902, 0.05), (910, 0.0)):
        catr.location.z = z0 + dz; catr.keyframe_insert("location", frame=f)
# --- TV flicker (cartoon glow, no image) and curtains swaying
tv = bpy.data.objects.new("FX_TVGlow", bpy.data.lights.new("FX_TVGlow", "AREA")); PR.objects.link(tv)
tv.data.size = 0.5; tv.location = (-1.75, -0.4, 0.75); tv.rotation_euler = (0, R_(90), 0)
for f in range(1, 1471, 9):
    tv.data.energy = random.uniform(8, 30); tv.data.color = random.choice(((0.6, 0.8, 1.0), (1.0, 0.8, 0.5), (0.7, 1.0, 0.7)))
    tv.data.keyframe_insert("energy", frame=f); tv.data.keyframe_insert("color", frame=f)
for s_i in (-1, 1):
    cu = bpy.data.objects["LR_Curtain%d" % s_i]
    for f in range(1, 1750, 50):
        cu.rotation_euler = (R_(3 * math.sin(f * 0.02 + s_i)), 0, R_(2 * math.sin(f * 0.013))); cu.keyframe_insert("rotation_euler", frame=f)
# --- wall clock spins during the time-lapse
for nm, turns in (("wall_clock_minute_hand", 14), ("wall_clock_hours_hand", 1.2)):
    o = bpy.data.objects.get(nm)
    if o:
        ax = 1
        o.keyframe_insert("rotation_euler", frame=1351); r0 = o.rotation_euler.copy()
        o.rotation_euler[ax] = r0[ax] - turns * 2 * math.pi; o.keyframe_insert("rotation_euler", frame=1470)

# ------------------------------------------------------------------ lights / time of day / seasons / exposure
sun = bpy.data.objects["Sun"]; wn = sc.world.node_tree.nodes
def Lk_(f, sun_e, sun_col, sun_rot, world, ex, s1=0.0, s2=0.0, moon=0.0, lroom=1.0, bath=1.0):
    sun.data.energy = sun_e; sun.data.keyframe_insert("energy", frame=f)
    sun.data.color = sun_col; sun.data.keyframe_insert("color", frame=f)
    sun.rotation_euler = sun_rot; sun.keyframe_insert("rotation_euler", frame=f)
    for i in range(3):
        bg = wn["BG%d" % i].inputs[1]; bg.default_value = world; bg.keyframe_insert("default_value", frame=f)
    for nm, v in (("SeasonMix1", s1), ("SeasonMix2", s2)):
        mx = wn[nm].inputs[0]; mx.default_value = v; mx.keyframe_insert("default_value", frame=f)
    sc.view_settings.exposure = ex; sc.view_settings.keyframe_insert("exposure", frame=f)
    bpy.data.objects["BR_Moon"].data.energy = moon; bpy.data.objects["BR_Moon"].data.keyframe_insert("energy", frame=f)
    for nm, base in (("LR_WindowFill", 260), ("LR_CeilBounce", 220), ("LR_FrontFill", 120)):
        o = bpy.data.objects[nm]; o.data.energy = base * lroom; o.data.keyframe_insert("energy", frame=f)
    for nm, base in (("BR_Ceil", 150),):
        o = bpy.data.objects[nm]; o.data.energy = base * (1 - min(1, moon / 40.0)) * 0.0; o.data.keyframe_insert("energy", frame=f)
DAY = ((1.0, 0.93, 0.82), Euler((R_(55), 0, R_(200))))
Lk_(1, 4.0, DAY[0], DAY[1], 1.0, 0.6)
Lk_(1350, 4.0, DAY[0], DAY[1], 1.0, 0.6)
# time-lapse: summer -> autumn dusk -> winter -> summer, sun sweeping
Lk_(1375, 2.5, (1.0, 0.7, 0.45), Euler((R_(78), 0, R_(250))), 0.8, 0.6, s1=1.0)
Lk_(1395, 0.3, (0.5, 0.6, 1.0), Euler((R_(95), 0, R_(290))), 0.2, 0.9, s1=1.0)
Lk_(1415, 3.0, (0.95, 0.95, 1.0), Euler((R_(65), 0, R_(170))), 1.2, 0.5, s1=1.0, s2=1.0)
Lk_(1440, 1.5, (0.8, 0.85, 1.0), Euler((R_(80), 0, R_(240))), 0.7, 0.7, s1=1.0, s2=1.0)
Lk_(1465, 4.0, DAY[0], DAY[1], 1.0, 0.6, s1=0.0, s2=0.0)
Lk_(1720, 3.5, (1.0, 0.8, 0.6), Euler((R_(70), 0, R_(240))), 0.9, 0.6)
# bedroom at night
Lk_(1756, 0.0, (0.5, 0.6, 1.0), Euler((R_(70), 0, R_(240))), 0.03, 1.4, moon=140, lroom=0.0)
Lk_(1864, 0.0, (0.5, 0.6, 1.0), Euler((R_(70), 0, R_(240))), 0.03, 1.4, moon=140, lroom=0.0)
# morning bathroom
Lk_(1882, 3.0, (1.0, 0.95, 0.88), Euler((R_(40), 0, R_(150))), 1.0, 0.5, lroom=0.0)
# time-lapse flashes hide the character swaps (boy -> teen -> man) and the move to the bench
for fc_ in (1395, 1440, 1470):
    for f, d in ((fc_ - 5, 0.0), (fc_, 2.6), (fc_ + 5, 0.0)):
        base = sc.view_settings.exposure
    pass
ex_fc = [c for c in all_fcurves(sc.animation_data.action) if c.data_path == "view_settings.exposure"][0]
for fc_ in (1395, 1440, 1470):
    v = ex_fc.evaluate(fc_)
    for f, d in ((fc_ - 6, 0.0), (fc_, 3.2), (fc_ + 6, 0.0)):
        ex_fc.keyframe_points.insert(f, ex_fc.evaluate(f) + d if d else ex_fc.evaluate(f))
# exposure steps hidden inside the tunnels (studio is brighter than the room), and the bright bathroom
def ex_step(f_mid, before, after):
    ex_fc.keyframe_points.insert(f_mid - 1, before); ex_fc.keyframe_points.insert(f_mid, after)
    for kp in ex_fc.keyframe_points:
        if int(round(kp.co.x)) == f_mid - 1: kp.interpolation = "CONSTANT"
ex_step(735, 0.6, -0.6); ex_step(861, -0.6, 0.6); ex_step(1115, 0.6, -0.6); ex_step(1322, -0.6, 0.6)
for kp in ex_fc.keyframe_points:
    if kp.co.x >= 1882: kp.co.y = 0.0
    elif 1470 <= kp.co.x <= 1720: kp.co.y = 0.15
ex_fc.update()
# studio light is self-contained (sphere emission + 3 area keys); dim them a little so whites do not clip
for i, e in enumerate((420, 90, 260)): bpy.data.objects["Studio_Key%d" % i].data.energy = e
sph_em = bpy.data.materials["M_StudioGradient"].node_tree.nodes["Emission"].inputs[1]; sph_em.default_value = 1.0

# ------------------------------------------------------------------ the one camera (Catmull-Rom through framing keys)
def fw_of(c): return (c.head_M().to_3x3() @ V(0, -1, 0)).normalized()
def up_of(c): return (c.head_M().to_3x3() @ V(0, 0, 1)).normalized()
def face_of(c, f):
    ev(f); return c.nose(0.0) + (c.head_M().to_3x3() @ V(0, 0.06, 0.02)) * c.s
def nose_of(c, f, side=1.0):
    ev(f); return c.nose(side)
def pinch_of(c, s, f): ev(f); return c.pinch(s)
SCW = Vector((0.0, 0.0, -7.0))
XS_C = XSM @ Prest(0.3, 0.5, 0)
XS_AIR = XSM @ Prest(0.12, 0.39, 0)
XS_HI = XSM @ Prest(0.19, 0.455, 0)
K = []   # (frame, cam, aim, lens)
def k(f, cam, aim, lens): K.append((f, Vector(cam), Vector(aim), float(lens)))
# beat 1
k(1, V(0.95, -1.35, 0.22), V(-0.05, 0.0, 0.35), 24)
k(60, V(0.6, -0.95, 0.42), pinch_of(B, "R", 60), 32)
k(115, V(0.3, -0.5, 0.6), nose_of(B, 115), 45)
k(170, V(0.14, -0.27, 0.63), nose_of(B, 170), 60)
k(225, V(0.42, -0.24, 0.67), nose_of(B, 225), 55)
# beat 2: whip down-left to the tub, macro on the dig, rise with the hand
k(272, V(0.05, -0.72, 0.52), TUBW + V(0, 0, 0.12), 34)
k(325, V(-0.18, -0.36, 0.3), TUBW + V(0.01, -0.02, 0.1), 50)
k(378, V(-0.05, -0.48, 0.48), pinch_of(B, "R", 378), 45)
k(430, V(0.08, -0.4, 0.66), (pinch_of(B, "R", 430) + face_of(B, 430)) / 2, 50)
# beat 3: floating macro on the dream bricks
k(480, DREAM + V(0.13, -0.15, 0.03), DREAM, 70)
k(517, DREAM + V(0.0, -0.13, 0.035), DREAM + V(0, 0, 0.01), 85)
k(565, DREAM + V(-0.13, -0.15, 0.0), DREAM + V(-0.02, 0, 0.01), 70)
k(612, V(0.35, -0.6, 0.6), face_of(B, 612), 42)
# beat 4: low hero angle, push to the nostril, dive
k(660, V(0.1, -0.5, 0.4), face_of(B, 660), 34)
k(700, nose_of(B, 700) + V(0.03, -0.13, -0.05), nose_of(B, 700), 50)
N0 = nose_of(B, 724); fwB = fw_of(B); upB = up_of(B)
k(718, N0 + fwB * 0.03 - upB * 0.018, N0, 40)
DIVE1 = [(724, N0 + fwB * 0.002), (728, N0 + upB * 0.03 - fwB * 0.01), (733, V(0.15, 0.3, -1.0)), (739, V(0.0, -1.4, -3.6)), (747, V(0.05, -2.75, -6.2))]
for i, (f, p) in enumerate(DIVE1):
    nxt = DIVE1[i + 1][1] if i + 1 < len(DIVE1) else XS_C
    k(f, p, nxt, 32)
# beat 5: studio, wedge
k(790, V(0.7, -1.9, -6.45), XS_AIR, 32)
k(828, XS_AIR + V(0.1, -0.75, 0.05), XS_AIR + V(0, 0, 0.02), 40)
RET1 = [(852, V(0.25, -1.6, -5.6)), (858, V(0.1, -1.2, -3.6)), (864, V(0.15, 0.3, -1.0))]
N1 = nose_of(B, 870); fw1 = fw_of(B)
RET1 += [(870, N1 + fw1 * 0.002), (879, N1 + fw1 * 0.09)]
for i, (f, p) in enumerate(RET1):
    prv = RET1[i - 1][1] if i > 0 else XS_AIR
    k(f, p, prv if f < 870 else N1, 32 if f < 870 else 38)
k(905, V(0.3, -1.05, 0.62), face_of(B, 905), 30)
# beat 6: mom
k(950, V(0.05, -1.4, 0.95), (face_of(B, 950) + V(0.8, 0.0, 0.3)), 26)
ev(1010); dirm = (MOMK - BOYP).normalized()
k(1005, BOYP + V(-0.3, -0.62, 0.78), (nose_of(B, 1005) + pinch_of(W, "R", 1005)) / 2, 38)
k(1045, nose_of(B, 1045) + V(-0.1, -0.12, 0.02), nose_of(B, 1045), 55)
k(1075, BOYP + V(-0.2, -0.75, 0.95), twz_tip(1075).translation, 36)
# beat 7: dive two
N2 = nose_of(B, 1104); fw2 = fw_of(B); up2 = up_of(B)
k(1094, N2 + fw2 * 0.08 + V(0.03, 0, 0.0), N2, 48)
DIVE2 = [(1104, N2 + fw2 * 0.002), (1108, N2 + up2 * 0.03 - fw2 * 0.01), (1113, V(0.15, 0.3, -1.0)), (1119, V(-0.3, -1.4, -3.6)), (1128, V(-1.0, -2.7, -6.0))]
for i, (f, p) in enumerate(DIVE2):
    nxt = DIVE2[i + 1][1] if i + 1 < len(DIVE2) else XS_C
    k(f, p, nxt, 30)
k(1185, V(-0.55, -1.7, -6.25), XS_HI, 34)
k(1240, XS_HI + V(0.35, -0.75, -0.05), XS_HI, 48)
k(1285, XS_HI + V(0.75, -0.95, 0.2), XS_HI, 42)
RET2 = [(1312, V(0.4, -1.6, -5.5)), (1318, V(0.1, -1.2, -3.6)), (1324, V(0.15, 0.3, -1.0))]
N3 = nose_of(B, 1330); fw3 = fw_of(B)
RET2 += [(1330, N3 + fw3 * 0.002), (1342, N3 + fw3 * 0.12)]
for i, (f, p) in enumerate(RET2):
    prv = RET2[i - 1][1] if i > 0 else XS_HI
    k(f, p, prv if f < 1330 else N3, 30 if f < 1330 else 36)
# beat 8: time-lapse orbit
SITC = BOYP + V(0, 0, 0.55)
k(1365, V(0.45, -0.75, 0.75), SITC, 26)
k(1395, V(1.25, -1.35, 1.05), SITC, 24)
k(1425, V(1.3, -0.75, 0.95), SITC + V(0, 0, -0.05), 30)
k(1455, V(-0.15, -0.95, 0.85), BOYP + V(0, 0, 0.45), 30)
# beat 9: bench, inhaler, through the door to the bedroom at night
k(1485, V(-0.35, 0.55, 1.05), face_of(M, 1485), 30)
k(1530, V(-0.85, 1.15, 1.05), face_of(M, 1530), 45)
k(1590, V(-1.55, 1.3, 0.95), face_of(M, 1590), 40)
k(1640, V(-1.65, 1.38, 0.72), pinch_of(M, "R", 1640), 45)
k(1688, V(-0.8, 1.15, 1.2), face_of(M, 1688), 40)
k(1704, V(-0.45, 1.15, 1.25), face_of(M, 1704), 36)
k(1722, V(0.9, 1.35, 1.35), V(2.8, 1.65, 1.1), 28)
k(1745, V(3.25, 1.45, 1.45), V(5.1, 1.4, 0.6), 24)
k(1790, V(4.75, 1.0, 2.15), face_of(M, 1790), 28)
k(1830, V(4.5, 1.95, 1.0), face_of(M, 1830), 34)
k(1862, V(5.75, 0.6, 1.25), face_of(M, 1862), 30)
# beat 10: through the wall into the bathroom
k(1878, V(6.2, 1.15, 1.5), V(7.5, 1.55, 1.5), 26)
k(1888, V(6.62, 1.22, 1.55), V(8.0, 1.6, 1.55), 27)
k(1897, V(6.85, 1.25, 1.6), face_of(M, 1897), 28)
k(1935, V(7.2, 1.0, 1.65), face_of(M, 1935), 34)
k(1990, V(7.5, 1.3, 1.45), face_of(M, 1990), 45)
k(2040, V(7.6, 1.38, 1.5), nose_of(M, 2040, 0), 62)
# beat 11: macro on the nostril, track the brick (slow-mo), land in the palm, pull back on the laugh
k(2077, V(7.665, 1.42, 1.62), nose_of(M, 2077, 0), 85)
k(2115, V(7.665, 1.41, 1.55), shoot(2115).translation, 85)
k(2150, V(7.665, 1.4, 1.47), M_PALM_W(2150), 85)
k(2200, V(7.6, 1.32, 1.55), (M_PALM_W(2200) + face_of(M, 2200)) / 2, 50)
k(2260, V(7.2, 1.08, 1.6), face_of(M, 2260), 34)
k(2310, V(6.9, 0.88, 1.62), (M_PALM_W(2310) + face_of(M, 2310)) / 2, 30)
K.sort(key=lambda x: x[0])
cam_d = bpy.data.cameras.new("CAM_Film"); cam_d.sensor_fit = "AUTO"; cam_d.clip_start = 0.001; cam_d.clip_end = 200
cam_d.dof.use_dof = True; cam_d.dof.aperture_fstop = 2.8
cam = bpy.data.objects.new("CAM_Film", cam_d); sc.collection.objects.link(cam); sc.camera = cam
aim = bpy.data.objects.new("CAM_Film_Aim", None); sc.collection.objects.link(aim)
tt = cam.constraints.new("TRACK_TO"); tt.target = aim; tt.track_axis = "TRACK_NEGATIVE_Z"; tt.up_axis = "UP_Y"
cam_d.dof.focus_object = aim
fc_ = catmull([(f, c) for f, c, a, l in K]); fa_ = catmull([(f, a) for f, c, a, l in K]); fl_ = pchip([(f, l) for f, c, a, l in K])
CAMPATH = fc_
for f in list(range(1, 2311, 2)) + [2310]:
    cam.location = fc_(f); cam.keyframe_insert("location", frame=f)
    aim.location = fa_(f); aim.keyframe_insert("location", frame=f)
    cam_d.lens = fl_(f); cam_d.keyframe_insert("lens", frame=f)
# f-stop: deep in the studio/tunnel, shallow in macros
for f, fs in ((1, 4.0), (460, 5.6), (630, 4.0), (720, 8.0), (2070, 8.0), (2200, 5.6), (2310, 4.0)):
    cam_d.dof.aperture_fstop = fs; cam_d.dof.keyframe_insert("aperture_fstop", frame=f)

# ------------------------------------------------------------------ tunnels: organic tubes built along the camera path
TM = bpy.data.materials.new("M_Tunnel"); TM.use_nodes = True; N = TM.node_tree.nodes; Lk = TM.node_tree.links
bs = N["Principled BSDF"]; bs.inputs["Base Color"].default_value = (0.72, 0.22, 0.24, 1); bs.inputs["Roughness"].default_value = 0.25
bs.inputs["Subsurface Weight"].default_value = 0.3; bs.inputs["Coat Weight"].default_value = 0.6
bs.inputs["Emission Color"].default_value = (0.6, 0.15, 0.15, 1); bs.inputs["Emission Strength"].default_value = 0.4
nzt = N.new("ShaderNodeTexNoise"); nzt.inputs["Scale"].default_value = 18; bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.5
wvt = N.new("ShaderNodeTexWave"); wvt.inputs["Scale"].default_value = 3.0; wvt.inputs["Distortion"].default_value = 6
adh = N.new("ShaderNodeMath"); adh.operation = "ADD"
Lk.new(nzt.outputs[0], adh.inputs[0]); Lk.new(wvt.outputs[1], adh.inputs[1])
Lk.new(adh.outputs[0], bp.inputs["Height"]); Lk.new(bp.outputs[0], bs.inputs["Normal"])
cr = N.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (0.25, 0.02, 0.04, 1); cr.color_ramp.elements[1].color = (0.82, 0.3, 0.3, 1)
vn = N.new("ShaderNodeTexVoronoi"); vn.feature = "DISTANCE_TO_EDGE"; vn.inputs["Scale"].default_value = 9
vr = N.new("ShaderNodeMapRange"); vr.inputs[1].default_value = 0.0; vr.inputs[2].default_value = 0.04; Lk.new(vn.outputs["Distance"], vr.inputs[0])
bs.inputs["Coat Weight"].default_value = 1.0; bs.inputs["Coat Roughness"].default_value = 0.03; bs.inputs["Roughness"].default_value = 0.15
Lk.new(wvt.outputs[1], cr.inputs[0])
veinmix = N.new("ShaderNodeMix"); veinmix.data_type = "RGBA"; veinmix.inputs[7].default_value = (0.3, 0.02, 0.05, 1)
Lk.new(vr.outputs[0], veinmix.inputs[0]); Lk.new(cr.outputs[0], veinmix.inputs[7]); veinmix.inputs[6].default_value = (0.32, 0.03, 0.08, 1)
Lk.new(veinmix.outputs[2], bs.inputs["Base Color"])
def tunnel(name, f0, f1, nostril_end):
    """tube around the camera path between frames f0..f1; small at the nostril end, flared at the studio end"""
    pts = [fc_(f0 + (f1 - f0) * i / 120.0) for i in range(121)]
    bm_ = bmesh.new(); rings = []; ringpos = []
    seg = 20
    a_prev = None
    for i, p in enumerate(pts):
        t = i / 120.0; tn = t if nostril_end == "start" else 1 - t       # 0 at the nostril
        r = 0.005 + 0.6 * smooth(tn / 0.5) + 0.5 * smooth((tn - 0.85) / 0.15)
        r *= 1.0 + 0.12 * math.sin(i * 0.9)
        d = (pts[min(120, i + 1)] - pts[max(0, i - 1)]).normalized()
        if a_prev is None:
            a = d.cross(V(0, 0, 1)); a = a.normalized() if a.length > 1e-3 else V(1, 0, 0)
        else:
            a = (a_prev - d * a_prev.dot(d)); a = a.normalized() if a.length > 1e-6 else d.orthogonal().normalized()
        a_prev = a; b_ = d.cross(a).normalized()
        ring = [bm_.verts.new(p + (a * math.cos(2 * math.pi * j / seg) + b_ * math.sin(2 * math.pi * j / seg)) * r * (1 + 0.15 * math.sin(j * 1.7 + i * 0.5))) for j in range(seg)]
        rings.append(ring); ringpos.append([v.co.copy() for v in ring])
    for r0, r1 in zip(rings, rings[1:]):
        for j in range(seg):
            bm_.faces.new((r0[j], r0[(j + 1) % seg], r1[(j + 1) % seg], r1[j]))
    me_ = bpy.data.meshes.new(name); bm_.to_mesh(me_); bm_.free()
    o = bpy.data.objects.new(name, me_); bpy.data.collections["Set_Studio"].objects.link(o); me_.materials.append(TM)
    for p in me_.polygons: p.use_smooth = True
    o.modifiers.new("sub", "SUBSURF").levels = 1
    # nostril hairs: dark curved strands from the wall near the nostril end, pointing inward/along the tube
    hm = bpy.data.materials.get("M_NoseHair") or flat("M_NoseHair", (0.08, 0.05, 0.035), 0.35, coat=0.5)
    cu = bpy.data.curves.new(name + "_Hairs", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 1.0; cu.bevel_resolution = 1
    ho = bpy.data.objects.new(name + "_Hairs", cu); bpy.data.collections["Set_Studio"].objects.link(ho); cu.materials.append(hm)
    for hcount in range(70):
        tn = random.uniform(0.02, 0.22); i = int((tn if nostril_end == "start" else 1 - tn) * 120)
        ring_ = ringpos[i]; j = random.randrange(seg); root = ring_[j].copy(); ctr = pts[i]
        d = (pts[min(120, i + 1)] - pts[max(0, i - 1)]).normalized() * (1 if nostril_end == "start" else -1)
        inward = (ctr - root); rr = inward.length; inward.normalize()
        L_ = rr * random.uniform(0.5, 0.95)
        sp = cu.splines.new("BEZIER"); sp.bezier_points.add(2)
        cps = [root, root + inward * L_ * 0.45 + d * L_ * 0.35, root + inward * L_ * 0.8 + d * L_ * 0.9]
        for bp, c_ in zip(sp.bezier_points, cps):
            bp.co = c_; bp.handle_left_type = bp.handle_right_type = "AUTO"; bp.radius = rr * 0.012
        sp.bezier_points[-1].radius = rr * 0.003
    key_vis([ho.name], [(f0 - 1, f1 + 2)])
    key_vis([name], [(f0 - 1, f1 + 2)])
    lt = bpy.data.objects.new(name + "_Light", bpy.data.lights.new(name + "_Light", "POINT")); bpy.data.collections["Set_Studio"].objects.link(lt)
    lt.data.energy = 0.4; lt.data.color = (1.0, 0.75, 0.7); lt.data.shadow_soft_size = 0.02
    for f in range(f0, f1 + 1, 2):
        lt.location = fc_(f + 1); lt.keyframe_insert("location", frame=f)
    key_vis([lt.name], [(f0 - 1, f1 + 2)])
tunnel("Tunnel_Dive1", 720, 744, "start")
tunnel("Tunnel_Return1", 850, 872, "end")
tunnel("Tunnel_Dive2", 1100, 1125, "start")
tunnel("Tunnel_Return2", 1310, 1332, "end")
# while the camera is inside a tunnel, the room, props and people are invisible to the camera only (shadows/light unchanged):
# otherwise the floor slab and the boy's own skin cut across the tube as membranes.
INSIDE = [(726, 748), (849, 869), (1106, 1130), (1309, 1329)]
hide_cols = [bpy.data.collections[n] for n in ("Set_LivingRoom", "Props")]
obs = set(o for c_ in hide_cols for o in c_.all_objects)
for nm in ("Boy", "Teen", "Man", "Mom"):
    a_ = bpy.data.objects[nm]; obs.add(a_); obs.update(a_.children_recursive)
obs = [o for o in obs if o.type in ("MESH", "CURVE", "EMPTY") and not o.name.startswith("BrickLib")]
for o in obs:
    o.visible_camera = True; o.keyframe_insert("visible_camera", frame=1)
    for a, b_ in INSIDE:
        o.visible_camera = False; o.keyframe_insert("visible_camera", frame=a)
        o.visible_camera = True; o.keyframe_insert("visible_camera", frame=b_)
# fly through the bedroom/bathroom wall: the wall opens for the camera only while it passes
for o in bpy.data.objects:
    if o.name.startswith(("BR_WallE", "BA_WallW", "BR_SkirtE", "BA_SkirtW")):
        for f, v in ((1, True), (1871, False), (1892, True)):
            o.visible_camera = v; o.keyframe_insert("visible_camera", frame=f)
# eyes: the cornea casts no shadow, so lights reach the iris through it (refractive caustics are off)
for o in bpy.data.objects:
    if o.name.endswith("high-poly"): o.visible_shadow = False
# dawn: the bedroom light comes on as we head for the bathroom wall
brc = bpy.data.objects["BR_Ceil"].data
for f, e in ((1, 0), (1862, 0), (1872, 160), (1900, 160)):
    brc.energy = e; brc.keyframe_insert("energy", frame=f)
sc.frame_set(1)
print("CAMERA_DONE keys", len(K))
