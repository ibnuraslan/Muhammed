# Part 2 of 03_animate.py: light/world keys, bubble, explainer dome, x-ray, pulses, lip contours, time-lapse, camera.
def keyv(sock, f, v):
    sock.default_value = v; sock.keyframe_insert("default_value", frame=f)
def keyseq(sock, seq):
    for f, v in seq: keyv(sock, f, v)
def keyattr(obj, attr, seq):
    for f, v in seq:
        setattr(obj, attr, v); obj.keyframe_insert(attr, frame=f)
LIGHTS = {n: bpy.data.objects[n].data for n in ("L_Sun", "L_Window", "L_Lamp", "L_Fill", "L_Ceil", "L_StudioKey", "L_StudioRim")}
for o_ in bpy.data.objects:
    if o_.type == 'LIGHT':
        o_.visible_camera = False
        if o_.name in ('L_Fill', 'L_Ceil', 'L_StudioKey', 'L_StudioRim'): o_.visible_glossy = False
BASE = {n: L.energy for n, L in LIGHTS.items()}
BASE["L_StudioKey"], BASE["L_StudioRim"] = 160.0, 120.0
bg = sc.world.node_tree.nodes["Background"].inputs["Strength"]
# room level: 1 = normal, ~0.12 = the dark of beat 2, ~0.25 under the explainer dome
ROOM = [(1, 1.0), (175, 1.0), (250, 0.14), (395, 0.14), (450, 1.0), (700, 1.0), (735, 0.3), (1060, 0.3), (1100, 1.0), (END, 1.0)]
STUDIO = [(1, 0.0), (700, 0.0), (735, 1.0), (1060, 1.0), (1100, 0.0), (END, 0.0)]
room = pchip(ROOM); stud = pchip(STUDIO)
TL0, TL1 = 1723, 1843   # time-lapse window
def season(f):
    """returns (sun colour, sun mult, leaf colour mult, snow) through summer -> autumn -> winter -> spring"""
    u = (f - TL0) / (TL1 - TL0)
    if u <= 0 or u >= 1: return (1.0, 0.92, 0.8), 1.0, (1.0, 1.0, 1.0), 0
    k = [(0.0, (1.0, 0.92, 0.8), 1.0, (1.0, 1.0, 1.0)), (0.3, (1.0, 0.7, 0.45), 0.8, (1.6, 0.7, 0.2)),
         (0.55, (0.75, 0.85, 1.0), 0.6, (0.6, 0.6, 0.6)), (0.8, (0.95, 1.0, 0.9), 1.0, (0.8, 1.2, 0.6)), (1.0, (1.0, 0.92, 0.8), 1.0, (1.0, 1.0, 1.0))]
    for (a, c0, s0, l0), (b, c1, s1, l1) in zip(k, k[1:]):
        if a <= u <= b:
            t = (u - a) / (b - a); return tuple(x + (y - x) * t for x, y in zip(c0, c1)), s0 + (s1 - s0) * t, tuple(x + (y - x) * t for x, y in zip(l0, l1)), 1 if 0.45 < u < 0.68 else 0
# leaf tint node
leaf_mix = []
for mn in sc.get("leaf_mats", []):
    m = bpy.data.materials.get(mn)
    if not m or not m.node_tree: continue
    nt = m.node_tree; bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if not bsdf or not bsdf.inputs['Base Color'].links: continue
    src = bsdf.inputs['Base Color'].links[0].from_socket
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
    nt.links.new(src, mx.inputs['A']); nt.links.new(mx.outputs['Result'], bsdf.inputs['Base Color']); leaf_mix.append(mx.inputs['B'])
snow_objs = [bpy.data.objects["SnowGround"], bpy.data.objects["SnowWallCap"]]
def daylight(f):
    if not (TL0 < f < TL1): return 1.0
    ph = ((f - TL0) / 30.0) % 1.0
    return 0.06 + 0.94 * math.sin(math.pi * ph) ** 2
lamp_on = lambda f: (1.0 if not (TL0 < f < TL1) else 0.3 + 2.2 * (1 - daylight(f)))
for f in keys_every(1, END, 3) if False else sorted(set(list(range(1, END, 6)) + list(range(TL0, TL1 + 1, 2)) + [END])):
    rv, sv = room(f), stud(f)
    col, smul, leaf, snow = season(f)
    for n, L in LIGHTS.items():
        if n.startswith("L_Studio"):
            L.energy = BASE[n] * sv
        elif n == "L_Lamp":
            L.energy = BASE[n] * max(rv, 0.25) * lamp_on(f)
        elif n in ("L_Sun", "L_Window"):
            L.energy = BASE[n] * rv * smul * daylight(f) * (1.4 if TL0 < f < TL1 else 1.0)
            if n == "L_Sun": L.color = col
        else:
            L.energy = BASE[n] * rv * (0.35 + 0.65 * daylight(f))
        L.keyframe_insert("energy", frame=f)
        if n == "L_Sun": L.keyframe_insert("color", frame=f)
    keyv(bg, f, 1.0 * rv * smul * daylight(f))
    for s_ in leaf_mix: keyv(s_, f, (*leaf, 1))
for o in snow_objs:
    keyattr(o, "hide_render", [(1, True), (TL0 + 50, True), (TL0 + 54, False), (TL0 + 82, False), (TL0 + 86, True)])
# sun direction sweeps during the time-lapse (shadows sweep)
sun = bpy.data.objects["L_Sun"]
for f, z in ((1, 170), (TL0, 170), (TL0 + 30, 230), (TL0 + 31, 120), (TL0 + 60, 230), (TL0 + 61, 120), (TL0 + 90, 230), (TL0 + 91, 120), (TL1, 170), (END, 170)):
    sun.rotation_euler = (R_(-55), 0, R_(z)); sun.keyframe_insert("rotation_euler", frame=f)
# lamp flame emission follows the lamp
fl = bpy.data.objects.get("vintage_oil_lamp_flame")
if fl and fl.data.materials:
    fm = fl.data.materials[0]
    bs = next((n for n in fm.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if bs:
        bs.inputs["Emission Color"].default_value = (1.0, 0.55, 0.2, 1)
        for f in sorted(set(list(range(1, END, 30)) + list(range(TL0, TL1 + 1, 3)))):
            keyv(bs.inputs["Emission Strength"], f, 8.0 * lamp_on(f))
# ---------------------------------------------- dark bubble (beat 2) and the explainer dome (beats 5-6)
bub_mix = bpy.data.materials["M_Bubble"].node_tree.nodes["BubbleMix"].inputs[0]
keyseq(bub_mix, [(1, 0.0), (180, 0.0), (255, 0.78), (400, 0.78), (418, 0.5), (450, 0.0), (END, 0.0)])
bn = bpy.data.materials["M_Bubble"].node_tree.nodes
bn["Layer Weight"].inputs['Blend'].default_value = 0.6      # soft vignette edge, clear centre
ev(300); gface_p = G.bone_world("head") + V(0, -0.12, 0.03)
fl_ = bpy.data.lights.new("L_BubbleFace", 'SPOT'); fl_.spot_size = R_(40); fl_.spot_blend = 0.8; fl_.shadow_soft_size = 0.15; fl_.color = (1.0, 0.86, 0.72)
flo = bpy.data.objects.new("L_BubbleFace", fl_); sc.collection.objects.link(flo); flo.visible_camera = False
flo.location = gface_p + V(0.35, -0.55, 0.35); flo.rotation_euler = (gface_p - flo.location).to_track_quat('-Z', 'Y').to_euler()
for f, e_ in ((1, 0.0), (175, 0.0), (240, 45.0), (400, 45.0), (450, 0.0), (END, 0.0)):
    fl_.energy = e_; fl_.keyframe_insert("energy", frame=f)
bub = bpy.data.objects["DarkBubble"]
keyattr(bub, "scale", [(170, Vector((1.6, 1.6, 1.6))), (255, Vector((1.0, 1.0, 1.0))), (400, Vector((1.0, 1.0, 1.0))), (450, Vector((1.25, 1.25, 1.25)))])
keyattr(bub, "hide_render", [(1, True)])   # no visible sphere: the "trapped" beat is a lighting vignette (room fades, her face keeps a soft key)
dome_mix = bpy.data.materials["M_ExplainerDome"].node_tree.nodes["DomeMix"].inputs[0]
_cr = next(n for n in bpy.data.materials["M_ExplainerDome"].node_tree.nodes if n.type == 'VALTORGB').color_ramp
_cr.elements[0].position = 0.2; _cr.elements[0].color = (0.02, 0.16, 0.24, 1); _cr.elements[1].position = 0.9; _cr.elements[1].color = (0.55, 0.85, 0.95, 1)
keyseq(dome_mix, [(1, 0.0), (700, 0.0), (740, 1.0), (1058, 1.0), (1100, 0.0), (END, 0.0)])
dome = bpy.data.objects["ExplainerDome"]
keyattr(dome, "hide_render", [(1, True), (698, False), (1102, True)])
ev(800); mid = (G.bone_world("head") + T.bone_world("head")) / 2
dome.location = V(mid.x, mid.y, 0.9); dome.scale = (0.56, 0.56, 0.56)   # 1.7 m: every wall stays outside, no visible edge
# ---------------------------------------------- x-ray portholes: teacher's throat, girl's hand and forearm
def attach(o, P, bone, f=600):
    ev(f); c_ = o.constraints.new('CHILD_OF'); c_.target = P.o; c_.subtarget = bone
    c_.inverse_matrix = (P.o.matrix_world @ P.o.pose.bones[bone].matrix).inverted()
def empty(name, P, bone, f, loc, scale, rot=None):
    e = bpy.data.objects.new(name, None); bpy.data.collections["FX"].objects.link(e)
    ev(f); M = P.o.matrix_world @ P.o.pose.bones[bone].matrix
    e.matrix_world = Matrix.Translation(loc) @ M.to_3x3().normalized().to_4x4() @ Matrix.Diagonal((*scale, 1))
    attach(e, P, bone, f); return e
ev(760)
xr_t = empty("XR_Throat", T, "neck01", 760, T.bone_world("neck01").lerp(T.bone_world("neck02"), 0.5) + fdir(T_YAW) * 0.02, (0.075, 0.07, 0.075))
el, wr = G.bone_world("lowerarm01.R"), G.bone_world("wrist.R")
xr_a = empty("XR_Arm", G, "lowerarm02.R", 760, el.lerp(wr, 0.5), (0.05, 0.16, 0.05))
xr_h = empty("XR_Hand", G, "wrist.R", 760, G.bone_world("finger3-1.R"), (0.07, 0.09, 0.06))
XR_VAL = []
def xray_material(m, empties):
    nt = m.node_tree; out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
    if not out.inputs['Surface'].links: return
    src = out.inputs['Surface'].links[0].from_socket
    masks = []
    for e in empties:
        tc = nt.nodes.new('ShaderNodeTexCoord'); tc.object = e
        ln = nt.nodes.new('ShaderNodeVectorMath'); ln.operation = 'LENGTH'; nt.links.new(tc.outputs['Object'], ln.inputs[0])
        mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 1.0; mr.inputs['From Max'].default_value = 0.85
        nt.links.new(ln.outputs['Value'], mr.inputs['Value']); masks.append(mr.outputs['Result'])
    acc = masks[0]
    for mk_ in masks[1:]:
        mx = nt.nodes.new('ShaderNodeMath'); mx.operation = 'MAXIMUM'; nt.links.new(acc, mx.inputs[0]); nt.links.new(mk_, mx.inputs[1]); acc = mx.outputs[0]
    val = nt.nodes.new('ShaderNodeValue'); val.name = "XRAY"; val.outputs[0].default_value = 0.0; XR_VAL.append(val.outputs[0])
    mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; nt.links.new(acc, mul.inputs[0]); nt.links.new(val.outputs[0], mul.inputs[1])
    tr_ = nt.nodes.new('ShaderNodeBsdfTransparent'); em_ = nt.nodes.new('ShaderNodeEmission'); em_.inputs['Color'].default_value = (0.6, 0.9, 1.0, 1); em_.inputs['Strength'].default_value = 1.2
    lw_ = nt.nodes.new('ShaderNodeLayerWeight'); lw_.inputs['Blend'].default_value = 0.12
    gm = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(lw_.outputs['Facing'], gm.inputs[0]); nt.links.new(tr_.outputs[0], gm.inputs[1]); nt.links.new(em_.outputs[0], gm.inputs[2])
    mixs = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(mul.outputs[0], mixs.inputs[0]); nt.links.new(src, mixs.inputs[1]); nt.links.new(gm.outputs[0], mixs.inputs[2])
    nt.links.new(mixs.outputs[0], out.inputs['Surface'])
done_m = set()
for P_, emps in ((T, [xr_t]), (G, [xr_a, xr_h])):
    for ch in P_.o.children:
        if ch.type != 'MESH': continue
        if not any(k in ch.name for k in (".body", "elegantsuit")): continue
        for m in ch.data.materials:
            if m and m.name not in done_m:
                done_m.add(m.name); xray_material(m, emps)
for s_ in XR_VAL:
    keyseq(s_, [(1, 0.0), (705, 0.0), (745, 1.0), (1050, 1.0), (1085, 0.0), (END, 0.0)])
# larynx (clean, procedural): thyroid shield + cricoid ring + two vocal folds that buzz
m_cart = bpy.data.materials.new("M_Cartilage"); m_cart.use_nodes = True
pc = m_cart.node_tree.nodes["Principled BSDF"]; pc.inputs["Base Color"].default_value = (0.92, 0.88, 0.82, 1); pc.inputs["Roughness"].default_value = 0.35
pc.inputs["Subsurface Weight"].default_value = 0.3; pc.inputs["Emission Color"].default_value = (0.6, 0.9, 1.0, 1); pc.inputs["Emission Strength"].default_value = 0.4
m_fold = bpy.data.materials.new("M_VocalFold"); m_fold.use_nodes = True
pf = m_fold.node_tree.nodes["Principled BSDF"]; pf.inputs["Base Color"].default_value = (0.85, 0.55, 0.5, 1); pf.inputs["Roughness"].default_value = 0.3
pf.inputs["Emission Color"].default_value = (1.0, 0.8, 0.6, 1); pf.inputs["Emission Strength"].default_value = 0.3
ev(760); TF = fdir(T_YAW); TR = rdir(T_YAW); lc = T.bone_world("neck01").lerp(T.bone_world("neck02"), 0.5) + TF * 0.012
LARYNX = []
# real larynx anatomy (CC-BY model): thyroid prominence just under the throat skin, trachea down the neck
lxm = bpy.data.objects["Model_Larynx"]; lxm.hide_render = False
n1_, n2_ = T.bone_world("neck01"), T.bone_world("neck02")
Zw = (n2_ - n1_).normalized(); Yw = -(TF - Zw * TF.dot(Zw)).normalized(); Xw = Yw.cross(Zw)
skin = t_throat(760)
lxm.matrix_world = Matrix.Translation(skin - TF * 0.022 + Zw * 0.004) @ Matrix((Xw, Yw, Zw)).transposed().to_4x4()
attach(lxm, T, "neck01", 760); LARYNX.append(lxm)
for o in LARYNX:
    keyattr(o, "hide_render", [(1, True), (715, False), (1080, True)])
# the larynx buzzes with the voice: tiny, fast scale tremor (bigger when loud)
for f in range(697, 1063, 3):
    loud = 895 <= f < 985; soft = f >= 985
    a = 0.02 if loud else (0.004 if soft else 0.01)
    k = 1 + a * (1 if (f // 3) % 2 else -1)
    lxm.scale = (k, k, 1.0); lxm.keyframe_insert("scale", frame=f)
# real hand skeleton (CC-BY model) fitted to the girl's right hand: wrist, middle fingertip and thumb
hsm = bpy.data.objects["Model_HandSkeleton"]; hsm.hide_render = False
ev(760)
wr_ = G.bone_world("wrist.R"); tp_ = G.bone_world("finger3-3.R", tail=True); th_ = G.bone_world("finger1-3.R", tail=True)
Yg = (tp_ - wr_).normalized(); Lg = (tp_ - wr_).length * 0.97
lat_ = (th_ - wr_) - Yg * (th_ - wr_).dot(Yg); Xg = lat_.normalized(); Zg = Xg.cross(Yg)
hsm.matrix_world = Matrix.Translation(wr_) @ Matrix((Xg, Yg, Zg)).transposed().to_4x4() @ Matrix.Scale(Lg, 4)
attach(hsm, G, "wrist.R", 760)
HAND_BONES = [hsm]
for o in HAND_BONES:
    keyattr(o, "hide_render", [(1, True), (712, False), (1080, True)])
# pulse dots: larynx -> fingertip -> knuckles -> wrist -> forearm -> elbow -> shoulder
m_dot = bpy.data.materials.new("M_PulseDot"); m_dot.use_nodes = True
nd = m_dot.node_tree.nodes; nd.remove(nd["Principled BSDF"])
oi = nd.new('ShaderNodeObjectInfo'); emd = nd.new('ShaderNodeEmission'); m_dot.node_tree.links.new(oi.outputs['Color'], emd.inputs['Color'])
sep_ = nd.new('ShaderNodeSeparateColor'); m_dot.node_tree.links.new(oi.outputs['Color'], sep_.inputs[0])
mul_ = nd.new('ShaderNodeMath'); mul_.operation = 'MULTIPLY'; mul_.inputs[1].default_value = 30.0; m_dot.node_tree.links.new(oi.outputs['Alpha'], mul_.inputs[0])
m_dot.node_tree.links.new(mul_.outputs[0], emd.inputs['Strength']); m_dot.node_tree.links.new(emd.outputs[0], nd["Material Output"].inputs['Surface'])
NDOT = 16
dots = [mk("PulseDot_%02d" % i, lambda bm: bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=0.004), m_dot) for i in range(NDOT)]
for d_ in dots: d_.visible_shadow = False; d_.visible_diffuse = False
def polyline_pt(pts, u):
    L = [0.0]
    for a, b in zip(pts, pts[1:]): L.append(L[-1] + (b - a).length)
    t = u * L[-1]
    for i in range(len(pts) - 1):
        if L[i + 1] >= t: return pts[i].lerp(pts[i + 1], (t - L[i]) / max(1e-6, L[i + 1] - L[i]))
    return pts[-1]
FINGER_OF = {}
def path_teacher(f, k=3):
    ev(f); tip = G.bone_world("finger%d-3.R" % k, tail=True)
    return [lc_world(f), tip, G.bone_world("finger%d-3.R" % k), G.bone_world("finger%d-2.R" % k), G.bone_world("finger%d-1.R" % k), G.bone_world("wrist.R"), G.bone_world("lowerarm01.R").lerp(G.bone_world("wrist.R"), 0.5),
            G.bone_world("lowerarm01.R"), G.bone_world("upperarm01.R").lerp(G.bone_world("lowerarm01.R"), 0.5), G.bone_world("upperarm01.R"), G.bone_world("neck03"), G.bone_world("head") + V(0, 0, 0.06)]
def lc_world(f):
    ev(f); return T.bone_world("neck01").lerp(T.bone_world("neck02"), 0.5) + fdir(T_YAW) * 0.012
def path_girl(f):
    ev(f)
    ff = fdir(0); lg = G.bone_world("neck01").lerp(G.bone_world("neck02"), 0.5) + V(0, -0.02, 0)
    return [lg, G.bone_world("finger3-3.L", tail=True), G.bone_world("wrist.L"), G.bone_world("lowerarm01.L"), G.bone_world("upperarm01.L"), G.bone_world("head") + V(0, 0, 0.06)]
def dot_keys(f0, f1, pathfn, style):
    for f in range(f0, f1 + 1, 2):
        sz, br, sp = style(f)
        paths = {k: pathfn(f, k) for k in (2, 3, 4)} if pathfn is path_teacher else None
        pts = None if paths else pathfn(f)
        for i, d_ in enumerate(dots):
            if paths: pts = paths[2 + i % 3]
            u = ((f - f0) * sp + i / NDOT) % 1.0
            d_.location = polyline_pt(pts, u); fade = min(1.0, u * 8, (1 - u) * 6)
            s_ = sz * (0.6 + 0.4 * fade); d_.scale = (s_, s_, s_)
            d_.color = (1.0, 0.62, 0.28, br * fade)
            d_.keyframe_insert("location", frame=f); d_.keyframe_insert("scale", frame=f); d_.keyframe_insert("color", frame=f)
def style_teacher(f):
    if f < 895: return 1.0, 0.6 * smooth((f - 705) / 30.0), 0.006
    if f < 985: return 2.2, 1.6, 0.010         # loud: big, bright, fast
    return 0.6, 0.25, 0.0035                   # soft: small, dim, slow
for d_ in dots:
    keyattr(d_, "hide_render", [(1, True), (705, False), (1075, True), (1850, False), (END + 1, False)])
dot_keys(705, 1075, path_teacher, style_teacher)
dot_keys(1850, END, path_girl, lambda f: (1.3, 1.1 * smooth((f - 1850) / 20.0), 0.008))
# lip contour rings (beat 8 on the teacher, beat 9 faint on the girl)
m_ct = bpy.data.materials.new("M_Contour"); m_ct.use_nodes = True
nc_ = m_ct.node_tree.nodes; nc_.remove(nc_["Principled BSDF"])
emc = nc_.new('ShaderNodeEmission'); emc.inputs['Color'].default_value = (0.5, 0.9, 1.0, 1); emc.name = "E"
m_ct.node_tree.links.new(emc.outputs[0], nc_["Material Output"].inputs['Surface'])
def contour_ring(name, P):
    ev(1300)
    hb = P.o.pose.bones["head"]
    mp_ = P.o.matrix_world @ (hb.matrix @ (P.r.BN["head"].matrix_local.inverted() @ P.r.BN["oris06"].head_local))
    ff_ = (hb.matrix.to_3x3() @ (P.r.BN["head"].matrix_local.to_3x3().inverted() @ V(0, -1, 0))).normalized()
    rings = []
    for k, r_ in enumerate((0.022, 0.03, 0.038)):
        o = mk("%s_%d" % (name, k), lambda bm: bmesh.ops.create_circle(bm, cap_ends=False, radius=r_, segments=48), m_ct)
        o.modifiers.new("Sk", 'SOLIDIFY').thickness = 0.0015
        sk_ = o.modifiers.new("Skin", 'WIREFRAME'); sk_.thickness = 0.0012
        o.matrix_world = Matrix.Translation(mp_ + ff_ * (0.012 + 0.004 * k)) @ Vector((0, 0, 1)).rotation_difference(ff_).to_matrix().to_4x4()
        attach(o, P, "head", 1300); o.visible_shadow = False; rings.append(o)
    return rings
t_rings = contour_ring("LipContour_T", T)
SHAPE_SCALE = {"O": (0.8, 1.0), "E": (1.4, 0.45), "M": (1.3, 0.15)}
for o in t_rings:
    keyattr(o, "hide_render", [(1, True), (1255, False), (1460, True)])
for f, shp in OEM:
    sx_, sz_ = SHAPE_SCALE[shp]
    for k, o in enumerate(t_rings):
        o.scale = (sx_, sz_, 1); o.keyframe_insert("scale", frame=f)
    keyv(emc.inputs['Strength'], f, 0.0); keyv(emc.inputs['Strength'], f + 6, 6.0); keyv(emc.inputs['Strength'], f + 28, 1.0)
g_rings = contour_ring("LipContour_G", G)
for o in g_rings:
    keyattr(o, "hide_render", [(1, True), (1470, False), (1720, True)])
def press_dent(surface, P, bone, name):
    e = bpy.data.objects.new(name, None); bpy.data.collections["FX"].objects.link(e)
    c_ = e.constraints.new('COPY_LOCATION'); c_.target = P.o; c_.subtarget = bone; c_.head_tail = 1.0
    ob = bpy.data.objects[surface]
    vg = ob.vertex_groups.get("press_" + name) or ob.vertex_groups.new(name="press_" + name)
    vg.add(list(range(len(ob.data.vertices))), 0.0, 'REPLACE')
    vp = ob.modifiers.new("PressW_" + name, 'VERTEX_WEIGHT_PROXIMITY'); vp.vertex_group = vg.name; vp.target = e
    vp.proximity_mode = 'OBJECT'; vp.min_dist = 0.016; vp.max_dist = 0.0; vp.falloff_type = 'SMOOTH'
    ds = ob.modifiers.new("PressD_" + name, 'DISPLACE'); ds.vertex_group = vg.name; ds.strength = -0.0025; ds.mid_level = 0.0
    ds.direction = 'NORMAL'
    # keep these right after the armature so they act on the posed skin
    for m_ in (vp, ds):
        idx = list(ob.modifiers).index(m_); arm_i = next(i for i, mm in enumerate(ob.modifiers) if mm.type == 'ARMATURE')
        ob.modifiers.move(idx, arm_i + 1 + (1 if m_ is ds else 0))
press_dent("Teacher.body", G, "finger3-3.R", "GirlTipR")
press_dent("Girl.body", G, "finger3-3.L", "GirlTipL")
print("FX_DONE")
# ---------------------------------------------- one continuous camera (Catmull-Rom through ~1 s framings)
cam_d = bpy.data.cameras.new("CAM_Film"); cam_d.sensor_fit = 'AUTO'; cam_d.clip_start = 0.02
cam_d.dof.use_dof = True; cam_d.dof.aperture_fstop = 5.6
cam = bpy.data.objects.new("CAM_Film", cam_d); sc.collection.objects.link(cam); sc.camera = cam
aim = bpy.data.objects.new("CAM_Film_Aim", None); sc.collection.objects.link(aim)
tt = cam.constraints.new('TRACK_TO'); tt.target = aim; tt.track_axis = 'TRACK_NEGATIVE_Z'; tt.up_axis = 'UP_Y'
cam_d.dof.focus_object = aim
def gface(f): ev(f); return G.bone_world("head") + V(0, -0.07, 0.05)
def geye(f): ev(f); return G.bone_world("eye.R", tail=True)
def tmouth(f): return t_mouth(f)[0]
def tthroat(f): return t_throat(f)
def gtip(f): ev(f); return G.bone_world("finger3-3.R", tail=True)
def gelbow(f): ev(f); return G.bone_world("lowerarm01.R")
def gmouth(f): return g_own_mouth(f)[0]
def gface_cam(f, d, side=0.0, up=0.0):
    p, ff = g_own_mouth(f); ff = (ff - UP * ff.dot(UP)).normalized(); sd = ff.cross(UP).normalized()
    return p + ff * d + sd * side + UP * up
def pair(f): ev(f); return (G.bone_world("head") + T.bone_world("head")) / 2 - V(0, 0, 0.12)
def dogh(f): ev(f); return dog.matrix_world @ dog.pose.bones["head"].head
TFw, TRw = fdir(T_YAW), rdir(T_YAW)
SHOTS = [  # frame, camera position fn/vec, aim fn/vec, lens
    (1, V(-2.65, -2.3, 2.55), V(0.2, 0.7, 0.75), 16), (60, V(-1.9, -2.25, 1.7), V(0.2, 0.5, 0.75), 18),
    (120, V(1.55, -1.55, 0.32), lambda f: dogh(f).lerp(gface(f), 0.4), 20),
    (163, V(0.95, -1.25, 0.95), gface, 24), (225, lambda f: gface(f) + V(0.32, -0.62, 0.02), gface, 35),
    (290, lambda f: geye(f) + V(0.1, -0.3, 0.01), geye, 50), (350, V(0.95, -1.6, 1.3), V(0.2, 0.4, 0.9), 24),
    (397, V(0.65, -2.1, 1.45), V(-0.35, 0.1, 0.85), 22), (460, lambda f: pair(f) + V(0.05, -1.15, 0.0), pair, 26),
    (530, lambda f: tthroat(f) + V(0.32, -0.38, -0.05), tthroat, 40),
    (595, lambda f: tthroat(f) + TRw * 0.32 - TFw * 0.05 + V(0, 0, -0.2), tmouth, 30),
    (655, lambda f: tmouth(f) + TRw * 0.48 - TFw * 0.06 + V(0, 0, -0.02), tmouth, 40),
    (697, lambda f: tthroat(f) + TRw * 0.4 - TFw * 0.05 + V(0, 0, -0.03), tthroat, 45),
    (760, lambda f: gtip(f) + TRw * 0.38 - TFw * 0.08 + V(0, 0, 0.02), gtip, 50),
    (830, lambda f: gelbow(f).lerp(gtip(f), 0.5) + TRw * 0.42 - TFw * 0.12 + V(0, 0, -0.04), lambda f: gelbow(f).lerp(gtip(f), 0.45), 38),
    (895, lambda f: pair(f) + V(0.25, -0.95, 0.15), lambda f: tthroat(f).lerp(gtip(f), 0.5), 28),
    (960, lambda f: gface(f) + V(0.42, -0.5, 0.02), gface, 35), (1020, lambda f: tthroat(f) + TRw * 0.5 - TFw * 0.15 + V(0.0, 0, 0.0), lambda f: tthroat(f).lerp(gtip(f), 0.5), 40),
    (1063, lambda f: tmouth(f) + TRw * 0.42 + V(0, 0, 0.07), tmouth, 35),
    (1125, lambda f: tmouth(f) + TRw * 0.36 - TFw * 0.04 + V(0, 0, 0.04), tmouth, 55),
    (1190, lambda f: tmouth(f) + TRw * 0.32 + TFw * 0.06 + V(0, 0, 0.1), tmouth, 55),
    (1261, lambda f: tmouth(f) + TRw * 0.3 - TFw * 0.02 + V(0, 0, 0.02), tmouth, 60),
    (1320, lambda f: tmouth(f) + TRw * 0.28 - TFw * 0.12 + V(0, 0, 0.0), tmouth, 60),
    (1385, lambda f: tmouth(f) + TRw * 0.3 + TFw * 0.02 + V(0, 0, -0.1), tmouth, 55),
    (1453, lambda f: pair(f) + V(0.0, -1.35, 0.05), pair, 26), (1520, lambda f: gface(f) + V(0.5, -0.55, 0.02), gface, 32),
    (1590, lambda f: gmouth(f) + V(0.22, -0.36, 0.03), gmouth, 45), (1660, lambda f: pair(f) + V(0.7, -1.1, 0.55), pair, 24)]
# beat 10: orbit 120 deg in front of the pair, the window sweeping behind them
for k, f in enumerate((1723, 1763, 1803)):
    a = R_(65 - 55 * k)
    SHOTS.append((f, (lambda a_: (lambda f_: pair(f_) + V(1.55 * math.sin(a_), -1.55 * math.cos(a_), 0.15)))(a), pair, 24))
SHOTS += [(1843, lambda f: gmouth(f) + V(0.25, -0.5, 0.05), gface, 40), (1900, lambda f: pair(f) + V(0.55, -1.3, 0.4), pair, 28),
          (END, lambda f: pair(f) + V(0.35, -1.9, 1.1), pair, 22)]
res = []
for f, cp, ap, ln in SHOTS:
    c_ = cp(f) if callable(cp) else cp; a_ = ap(f) if callable(ap) else ap
    res.append((f, c_, a_, float(ln)))
fc = catmull([(f, c_) for f, c_, a_, l_ in res]); fa = catmull([(f, a_) for f, c_, a_, l_ in res]); fl_ = catmull([(f, l_) for f, c_, a_, l_ in res])
# clearance: keep the lens >= 15 cm from the two characters' skin, clothes and hair (smoothed so the move stays fluid)
from mathutils.bvhtree import BVHTree
CLR = ["Teacher.body", "Teacher.female_elegantsuit01", "Teacher.ponytail01", "Girl.body", "Girl.female_elegantsuit01", "Girl.braid01"]
CAMF = keys_every(1, END, 3); push = {}
for f in CAMF:
    p = fc(f); ev(f); dg = bpy.context.evaluated_depsgraph_get(); off = Vector()
    if (p - G.bone_world("head")).length < 1.0:
        for it in range(3):
            best = None
            for nm in CLR:
                o_ = bpy.data.objects.get(nm)
                if not o_: continue
                eo = o_.evaluated_get(dg); me_ = eo.to_mesh()
                t_ = BVHTree.FromPolygons([eo.matrix_world @ v.co for v in me_.vertices], [tuple(q.vertices) for q in me_.polygons]); eo.to_mesh_clear()
                loc, nrm, idx, dist = t_.find_nearest(p + off)
                if loc is not None:
                    inside = ((p + off) - loc).dot(nrm) < 0
                    sd = -dist if inside else dist
                    if best is None or sd < best[0]: best = (sd, loc, nrm)
            if best is None or best[0] >= 0.18: break
            off += best[2].normalized() * (0.18 - best[0] + 0.01)
    push[f] = off
sm = {}
for i, f in enumerate(CAMF):
    w = [push[CAMF[j]] for j in range(max(0, i - 4), min(len(CAMF), i + 5))]
    m_ = max(w, key=lambda v: v.length)
    sm[f] = m_
nfix = sum(1 for v in push.values() if v.length > 0)
print("CAM_CLEARANCE keys pushed", nfix)
for f in CAMF:
    cam.location = fc(f) + sm[f]; cam.keyframe_insert("location", frame=f)
    aim.location = fa(f); aim.keyframe_insert("location", frame=f)
    cam_d.lens = fl_(f); cam_d.keyframe_insert("lens", frame=f)
import json
json.dump([dict(frame=f, cam=tuple(round(x, 3) for x in c_), aim=tuple(round(x, 3) for x in a_), lens=l_) for f, c_, a_, l_ in res],
          open(os.path.join(os.path.dirname(HERE), "camera_path.json"), "w"), indent=1)
print("CAMERA_DONE", len(res))
