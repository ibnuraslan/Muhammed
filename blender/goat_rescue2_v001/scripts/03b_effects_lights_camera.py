# Part 2 of 03_animate.py: x-ray hip, bottle + milk, light/grade keys, continuous camera.

# ------------------------------------------------------------------ x-ray: bones placed on the right hip, porthole in body+clothes
femur, pelvis = bpy.data.objects["XRay_Femur"], bpy.data.objects["XRay_Pelvis"]
def fit_long_axis(o, length):
    me = o.data
    pts = [v.co for v in me.vertices]
    mn = Vector([min(p[i] for p in pts) for i in range(3)]); mx = Vector([max(p[i] for p in pts) for i in range(3)])
    d = mx - mn; ax = max(range(3), key=lambda i: d[i])
    me.transform(Matrix.Translation(-(mn + mx) / 2))
    me.transform(Matrix.Scale(length / d[ax], 4))
    if ax != 1:   # long axis -> local Y (bone axis)
        me.transform(Matrix.Rotation(R_(90), 4, 'X' if ax == 2 else 'Z'))
fit_long_axis(femur, 0.44); fit_long_axis(pelvis, 0.27)
ev(240)
def attach(o, bone, M):
    o.matrix_world = M
    c = o.constraints.new('CHILD_OF'); c.target = F; c.subtarget = bone
    c.inverse_matrix = (F.matrix_world @ FR.PB[bone].matrix).inverted()
th = FR.PB["upperleg02.L"]; mid = (th.head + th.tail) / 2 + (th.head - th.tail).normalized() * 0.03
attach(femur, "upperleg02.L", Matrix.Translation(mid) @ (th.matrix.to_3x3().to_4x4()))
rt = FR.PB["root"]
attach(pelvis, "root", Matrix.Translation(rt.head + (rt.matrix.to_3x3() @ Vector((0, 0.0, 0.02)))) @ rt.matrix.to_3x3().to_4x4())
for o in (femur, pelvis):
    for f, h in ((1, True), (206, False), (282, True)):
        o.hide_render = h; o.keyframe_insert("hide_render", frame=f)
xc = bpy.data.objects.new("XRay_Center", None); sc.collection.objects.link(xc)
xc.location = th.head + (th.head - rt.head) * 0.15
cc = xc.constraints.new('CHILD_OF'); cc.target = F; cc.subtarget = "root"
cc.inverse_matrix = (F.matrix_world @ rt.matrix).inverted()
XRAY_KEYS = ((1, 0.0), (205, 0.0), (222, 1.0), (268, 1.0), (283, 0.0))
done = set()
for ob in [o for o in bpy.data.objects if o.parent == F and o.type == 'MESH']:
    for m in ob.data.materials:
        if not m or m.name in done or not m.node_tree: continue
        done.add(m.name)
        nt = m.node_tree; n, l = nt.nodes, nt.links
        out = next((x for x in n if x.type == 'OUTPUT_MATERIAL' and x.is_active_output), None)
        if not out or not out.inputs['Surface'].links: continue
        src = out.inputs['Surface'].links[0].from_socket
        # --- muck: wet dark-brown patches, heaviest on the back (rest-pose +Y), keyed in at the landing
        if ob.name.split(".")[-1] not in ("high-poly", "eyelashes01", "eyebrow001", "teeth_base", "tongue01"):
            mtc = n.new('ShaderNodeTexCoord')
            mnz = n.new('ShaderNodeTexNoise'); mnz.inputs['Scale'].default_value = 9.0; mnz.inputs['Detail'].default_value = 8; mnz.inputs['Roughness'].default_value = 0.65
            msep = n.new('ShaderNodeSeparateXYZ')
            mback = n.new('ShaderNodeMapRange'); mback.inputs['From Min'].default_value = 0.0; mback.inputs['From Max'].default_value = 0.12; mback.inputs['To Max'].default_value = 0.35
            madd = n.new('ShaderNodeMath'); madd.operation = 'ADD'
            mmap = n.new('ShaderNodeMapRange'); mmap.inputs['From Min'].default_value = 0.66; mmap.inputs['From Max'].default_value = 0.74
            mamt = n.new('ShaderNodeValue'); mamt.name = "MuckAmount"
            mmul = n.new('ShaderNodeMath'); mmul.operation = 'MULTIPLY'
            mbs = n.new('ShaderNodeBsdfPrincipled'); mbs.inputs['Roughness'].default_value = 0.55
            mud_img = bpy.data.images.get("brown_mud_02_diff_2k.jpg")
            mud_tex = n.new('ShaderNodeTexImage'); mud_tex.image = mud_img
            mud_map = n.new('ShaderNodeMapping'); mud_map.inputs['Scale'].default_value = (3.0, 3.0, 3.0)
            mud_hsv = n.new('ShaderNodeHueSaturation'); mud_hsv.inputs['Value'].default_value = 0.55; mud_hsv.inputs['Saturation'].default_value = 1.2
            mud_bump = n.new('ShaderNodeBump'); mud_bump.inputs['Strength'].default_value = 0.35
            l.new(mtc.outputs['Object'], mud_map.inputs['Vector']); l.new(mud_map.outputs['Vector'], mud_tex.inputs['Vector'])
            l.new(mud_tex.outputs['Color'], mud_hsv.inputs['Color']); l.new(mud_hsv.outputs['Color'], mbs.inputs['Base Color'])
            l.new(mnz.outputs['Fac'], mud_bump.inputs['Height']); l.new(mud_bump.outputs['Normal'], mbs.inputs['Normal'])
            mmix = n.new('ShaderNodeMixShader')
            for a2, b2 in ((mtc.outputs['Object'], mnz.inputs['Vector']), (mtc.outputs['Object'], msep.inputs['Vector']),
                           (msep.outputs['Y'], mback.inputs['Value']), (mnz.outputs['Fac'], madd.inputs[0]), (mback.outputs['Result'], madd.inputs[1]),
                           (madd.outputs[0], mmap.inputs['Value']), (mmap.outputs['Result'], mmul.inputs[0]), (mamt.outputs[0], mmul.inputs[1]),
                           (mmul.outputs[0], mmix.inputs['Fac']), (src, mmix.inputs[1]), (mbs.outputs['BSDF'], mmix.inputs[2])):
                l.new(a2, b2)
            for f_, v_ in ((1, 0.0), (91, 0.0), (96, 0.75), (600, 0.85), (2149, 0.85), (2150, 0.0)):
                mamt.outputs[0].default_value = v_; mamt.outputs[0].keyframe_insert("default_value", frame=f_)
            src = mmix.outputs['Shader']
        tc = n.new('ShaderNodeTexCoord'); tc.object = xc
        ln = n.new('ShaderNodeVectorMath'); ln.operation = 'LENGTH'
        mr = n.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.12; mr.inputs['From Max'].default_value = 0.20
        mr.inputs['To Min'].default_value = 1.0; mr.inputs['To Max'].default_value = 0.0
        val = n.new('ShaderNodeValue'); val.name = "XRayFade"; val.outputs[0].default_value = 0.0
        mul = n.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
        tr = n.new('ShaderNodeBsdfTransparent'); tr.inputs['Color'].default_value = (0.75, 0.9, 1.0, 1)
        mx = n.new('ShaderNodeMixShader')
        l.new(tc.outputs['Object'], ln.inputs[0]); l.new(ln.outputs['Value'], mr.inputs['Value'])
        l.new(mr.outputs['Result'], mul.inputs[0]); l.new(val.outputs[0], mul.inputs[1])
        l.new(mul.outputs[0], mx.inputs['Fac']); l.new(src, mx.inputs[1]); l.new(tr.outputs['BSDF'], mx.inputs[2])
        l.new(mx.outputs['Shader'], out.inputs['Surface'])
        for f, v in XRAY_KEYS:
            val.outputs[0].default_value = v; val.outputs[0].keyframe_insert("default_value", frame=f)
for m in bpy.data.objects["Farmer.male_worksuit01"].data.materials:
    for nd in list(m.node_tree.nodes):
        if nd.type == 'TEX_IMAGE' and nd.image and "diffuse" in nd.image.name.lower():
            for lk in list(nd.outputs['Color'].links):
                hs = m.node_tree.nodes.new('ShaderNodeHueSaturation'); hs.inputs['Saturation'].default_value = 0.72; hs.inputs['Value'].default_value = 0.62
                m.node_tree.links.new(nd.outputs['Color'], hs.inputs['Color']); m.node_tree.links.new(hs.outputs['Color'], lk.to_socket)
            print("OVERALLS desaturated via", nd.image.name)
for m in bpy.data.objects["Farmer.male_casualsuit06"].data.materials:
    for nd in list(m.node_tree.nodes):
        if nd.type == 'TEX_IMAGE' and nd.image and "diffuse" in nd.image.name.lower():
            for lk in list(nd.outputs['Color'].links):
                mx_ = m.node_tree.nodes.new('ShaderNodeMix'); mx_.data_type = 'RGBA'; mx_.blend_type = 'MULTIPLY'
                mx_.inputs['Factor'].default_value = 1.0; mx_.inputs['B'].default_value = (0.62, 0.78, 0.9, 1)
                m.node_tree.links.new(nd.outputs['Color'], mx_.inputs['A']); m.node_tree.links.new(mx_.outputs['Result'], lk.to_socket)
# crack flash at the femoral neck on "snapping"
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.016, location=(0, 0, 0))
crack = bpy.context.active_object; crack.name = "XRay_Crack"
cm = bpy.data.materials.new("M_Crack_Glow"); cm.use_nodes = True
cn = cm.node_tree.nodes; cn.clear(); co_ = cn.new('ShaderNodeOutputMaterial'); ce = cn.new('ShaderNodeEmission')
ce.inputs['Color'].default_value = (1.0, 0.08, 0.04, 1); cm.node_tree.links.new(ce.outputs[0], co_.inputs['Surface'])
crack.data.materials.append(cm)
ev(240); attach(crack, "upperleg02.L", Matrix.Translation(th.head + (th.tail - th.head).normalized() * 0.05))
for f, v in ((1, 0.0), (238, 0.0), (244, 8.0), (252, 3.0), (258, 6.0), (276, 0.0)):
    ce.inputs['Strength'].default_value = v; ce.inputs['Strength'].keyframe_insert("default_value", frame=f)
for f, h in ((1, True), (238, False), (278, True)):
    crack.hide_render = h; crack.keyframe_insert("hide_render", frame=f)

# ------------------------------------------------------------------ old milk bottle + milk
prof = [(0.0, 0.0), (3.0, 0.0), (3.4, 0.4), (3.5, 1.5), (3.5, 12.5), (3.0, 15.5), (1.9, 18.0), (1.7, 21.0), (1.95, 21.6), (1.9, 22.3), (1.6, 22.4)]
me = bpy.data.meshes.new("MilkBottle"); me.from_pydata([(r / 100, 0, z / 100) for r, z in prof], [(i, i + 1) for i in range(len(prof) - 1)], [])
bottle = bpy.data.objects.new("MilkBottle", me); sc.collection.objects.link(bottle)
for mtype, kw in (('SCREW', dict(axis='Z', steps=40, render_steps=40, use_merge_vertices=True, use_normal_calculate=True)), ('SOLIDIFY', dict(thickness=0.003, offset=-1))):
    md = bottle.modifiers.new(mtype, mtype)
    for k_, v_ in kw.items(): setattr(md, k_, v_)
gm = bpy.data.materials.new("M_OldGlass"); gm.use_nodes = True
gp_ = gm.node_tree.nodes["Principled BSDF"]
gp_.inputs['Base Color'].default_value = (0.82, 0.88, 0.85, 1); gp_.inputs['Transmission Weight'].default_value = 1.0
gp_.inputs['Roughness'].default_value = 0.18; gp_.inputs['IOR'].default_value = 1.5
bottle.data.materials.append(gm)
bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.031, depth=1.0, location=(0, 0, 0))
milk = bpy.context.active_object; milk.name = "Milk_Fill"
milk.data.transform(Matrix.Translation((0, 0, 0.5)))
mmat = bpy.data.materials.new("M_Milk"); mmat.use_nodes = True
mp = mmat.node_tree.nodes["Principled BSDF"]; mp.inputs['Base Color'].default_value = (0.92, 0.9, 0.84, 1)
mp.inputs['Subsurface Weight'].default_value = 0.4; mp.inputs['Roughness'].default_value = 0.25
milk.data.materials.append(mmat); milk.parent = bottle; milk.location = (0, 0, 0.006)
for f, h in ((1, 0.001), (1680, 0.001), (1825, 0.10), (1880, 0.10), (1945, 0.04)):
    milk.scale = (1, 1, h); milk.keyframe_insert("scale", frame=f)
# bottle lies in the muck on his right (goat) side; it is animated directly and his right hand follows it
ev(300)                                  # crater + rim in place before resting the bottle on the surface
B_REST = LIE_POS.to_2d() + RSIDE * 0.42 - HEAD_DIR * 0.05
_bd = Vector((math.cos(R_(25 + 90)), math.sin(R_(25 + 90))))
_g1, _g2 = ground_z(*(B_REST + _bd * 0.11)), ground_z(*(B_REST - _bd * 0.11))
bottle.location = (B_REST.x, B_REST.y, min(_g1, _g2) + 0.022); bottle.rotation_euler = (R_(90) + math.atan2(_g1 - _g2, 0.22), 0, R_(25))
bottle.keyframe_insert("location", frame=1); bottle.keyframe_insert("rotation_euler", frame=1)
bottle.keyframe_insert("location", frame=1650); bottle.keyframe_insert("rotation_euler", frame=1650)
BOTTLE_MOUTH = bpy.data.objects.new("Bottle_Mouth", None); sc.collection.objects.link(BOTTLE_MOUTH)
BOTTLE_MOUTH.parent = bottle; BOTTLE_MOUTH.location = (0, 0, 0.215)
for f, h in ((1, False), (2011, True)):
    bottle.hide_render = h; bottle.keyframe_insert("hide_render", frame=f)
# milk stream pulses from the teat into the bottle mouth
bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.004, depth=1.0)
stream = bpy.context.active_object; stream.name = "Milk_Stream"; stream.data.materials.append(mmat)
# Stretch To works along local +Y: lay the 1 m cylinder along +Y starting at the origin
stream.data.transform(Matrix.Rotation(R_(-90), 4, 'X')); stream.data.transform(Matrix.Translation((0, 0.5, 0)))
UD = bpy.data.objects.new("Udder_Point", None); sc.collection.objects.link(UD)
st_c = stream.constraints.new('COPY_LOCATION'); st_c.target = UD
st_t = stream.constraints.new('STRETCH_TO'); st_t.target = BOTTLE_MOUTH; st_t.rest_length = 1.0
for i, f in enumerate(range(1680, 1825, 15)):
    for ff, h in ((f, False), (f + 7, True)):
        stream.hide_render = h; stream.keyframe_insert("hide_render", frame=ff)
stream.hide_render = True; stream.keyframe_insert("hide_render", frame=1)

# ------------------------------------------------------------------ light + grade keys per beat
sun = bpy.data.objects["Key_Sun"]; moon = bpy.data.objects["Moon_Fill"]
tint = sc.world.node_tree.nodes["SkyTint"]; sky = sc.world.node_tree.nodes["SkyStrength"]
def sun_dir(az, el):
    d = Vector((math.cos(R_(el)) * math.sin(R_(az)), -math.cos(R_(el)) * math.cos(R_(az)), math.sin(R_(el))))
    return d.to_track_quat('Z', 'Y').to_euler()
LK = []   # frame, sun_energy, sun_rgb, az, el, sky_strength, tint_rgb, moon, exposure
DAY = (4.2, (1.0, 0.96, 0.9), -33, 48, 1.0, (1, 1, 1), 0.0, 0.0)
NIGHT = (0.0, (0.6, 0.7, 1.0), -33, 30, 0.10, (0.30, 0.42, 0.85), 2.2, -0.15)
HEAT = (5.5, (1.0, 0.8, 0.55), -20, 66, 1.1, (1.0, 0.86, 0.66), 0.0, 0.3)
DAWN = (2.6, (1.0, 0.72, 0.45), 30, 9, 0.6, (1.0, 0.82, 0.7), 0.0, 0.0)
def L(f, s): LK.append((f,) + s)
L(1, DAY); L(496, DAY)
# five days: fast sun sweep with night dips
for i in range(3):
    f0 = 497 + i * 60
    L(f0 + 12, (3.0, (1.0, 0.9, 0.8), -150 + 120 * i, 35, 0.8, (1, 1, 1), 0.0, 0.0))
    L(f0 + 38, NIGHT[:2] + (-90 + 120 * i, 20) + NIGHT[4:])
    L(f0 + 56, (2.4, (1.0, 0.8, 0.6), -60 + 120 * i, 12, 0.6, (1, 0.9, 0.8), 0.0, 0.0))
L(690, HEAT); L(745, HEAT); L(770, NIGHT); L(860, NIGHT)
L(890, DAWN); L(960, DAWN); L(1010, DAY); L(1170, DAY); L(1200, NIGHT); L(1380, NIGHT)
for i in range(2):
    f0 = 1395 + i * 70
    L(f0 + 15, (3.0, (1.0, 0.9, 0.8), -150 + 140 * i, 35, 0.8, (1, 1, 1), 0.0, 0.0))
    L(f0 + 45, NIGHT[:2] + (-90 + 140 * i, 20) + NIGHT[4:])
L(1560, DAY); L(2149, DAY); L(2150, DAY); L(2340, DAY)
LK.sort()
for f, se, sc_, az, el, ss, tn, mo, ex in LK:
    sun.data.energy = se; sun.data.color = sc_; sun.rotation_euler = sun_dir(az, el)
    sun.data.keyframe_insert("energy", frame=f); sun.data.keyframe_insert("color", frame=f); sun.keyframe_insert("rotation_euler", frame=f)
    sky.inputs['Strength'].default_value = ss; sky.inputs['Strength'].keyframe_insert("default_value", frame=f)
    tint.inputs['B'].default_value = (*tn, 1); tint.inputs['B'].keyframe_insert("default_value", frame=f)
    moon.data.energy = mo; moon.data.keyframe_insert("energy", frame=f)
    sc.view_settings.exposure = ex; sc.view_settings.keyframe_insert("exposure", frame=f)

# ------------------------------------------------------------------ continuous camera (two segments; the jump is hidden in a sky tilt)
cam_d = bpy.data.cameras.new("CAM_Film"); cam_d.lens = 28; cam_d.sensor_fit = 'AUTO'; cam_d.clip_start = 0.03
cam_d.dof.use_dof = True; cam_d.dof.aperture_fstop = 4.0
cam = bpy.data.objects.new("CAM_Film", cam_d); sc.collection.objects.link(cam); sc.camera = cam
aim = bpy.data.objects.new("CAM_Film_Aim", None); sc.collection.objects.link(aim)
tt = cam.constraints.new('TRACK_TO'); tt.target = aim; tt.track_axis = 'TRACK_NEGATIVE_Z'; tt.up_axis = 'UP_Y'
cam_d.dof.focus_object = aim
LP = LIE_POS
V = lambda *a: Vector(a)
HIP = LP + Vector((0, 0, 0)) - Vector((RSIDE.x, RSIDE.y, 0)) * 0.11
SEG1 = [  # frame, camera, aim, lens
    (1, V(-3.6, -4.7, 1.2), V(-3.2, -0.5, 1.0), 28), (36, V(-3.7, -3.9, 1.1), V(-2.7, -0.5, 1.1), 30),
    (62, V(-2.9, -3.6, 1.5), V(-1.2, -0.3, 1.5), 28), (92, V(-1.8, -3.0, 1.7), V(LP.x - 0.2, LP.y, 0.75), 28),
    (150, V(-1.1, -2.4, 1.85), V(LP.x, LP.y, 0.65), 30), (205, V(HIP.x - 0.4, HIP.y - 1.3, 1.3), V(HIP.x, HIP.y, HIP.z), 35),
    (262, V(HIP.x - 0.15, HIP.y - 0.62, 1.0), V(HIP.x, HIP.y, HIP.z), 40), (320, V(-0.2, -1.2, 2.0), V(LP.x + 0.2, LP.y, 0.62), 32),
    (410, V(0.6, -0.55, 2.8), V(LP.x + 0.3, LP.y + 0.05, 0.6), 30), (496, V(0.7, 0.6, 3.25), V(LP.x + 0.3, LP.y + 0.05, 0.6), 30),
    (590, V(3.0, -3.0, 4.2), V(LP.x + 0.3, LP.y, 0.5), 28), (676, V(2.2, -3.8, 2.6), V(LP.x + 0.2, LP.y, 0.6), 30),
    (725, V(-1.4, -2.0, 1.0), V(LP.x + 0.4, LP.y, 0.75), 32), (800, V(-0.7, -1.35, 1.3), V(LP.x + 0.45, LP.y, 0.68), 35),
    (868, V(0.1, -1.15, 1.05), V(LP.x + 0.8, LP.y + 0.4, 0.85), 30), (930, V(0.9, -1.3, 0.95), V(G_RIDGE.x, G_RIDGE.y, 1.0), 30),
    (1010, V(0.9, -1.5, 1.15), V(1.35, 1.0, 0.85), 30), (1100, V(0.75, -0.9, 1.0), V(G_HEAD.x - 0.15, G_HEAD.y - 0.2, 0.78), 35),
    (1175, V(0.2, -1.35, 1.45), V(LP.x + 0.5, LP.y + 0.3, 0.62), 32), (1260, V(-0.7, -1.75, 1.6), V(LP.x + 0.3, LP.y + 0.3, 0.55), 30),
    (1388, V(LP.x + 0.35, LP.y - 0.05, 3.3), V(LP.x + 0.3, LP.y + 0.18, 0.5), 30), (1500, V(LP.x + 0.9, LP.y - 0.6, 2.5), V(LP.x + 0.4, LP.y + 0.1, 0.55), 30),
    (1604, V(LP.x + 1.25, LP.y - 0.55, 0.98), V(HEAD_W_POS.x, HEAD_W_POS.y, 0.75), 40), (1700, V(LP.x - 0.75, LP.y + 0.45, 1.25), V(G_MILK.x + 0.05, G_MILK.y - 0.08, 0.66), 35),
    (1830, V(LP.x - 0.55, LP.y + 0.2, 1.3), V(LP.x + 0.55, LP.y + 0.15, 0.72), 35), (1910, V(LP.x + 1.1, LP.y - 0.8, 1.0), V(HEAD_W_POS.x - 0.1, HEAD_W_POS.y, 0.82), 40),
    (1973, V(-0.6, -3.7, 1.8), V(LP.x - 0.4, LP.y - 0.3, 0.8), 28), (2060, V(-1.4, -6.4, 1.6), V(-2.4, -2.6, 0.9), 28),
    (2120, V(-2.0, -7.0, 1.5), V(-3.6, -4.0, 2.2), 28), (2149, V(-2.1, -7.1, 1.45), V(-3.4, -4.6, 6.5), 26)]
# hospital: comes down out of the sky outside, sees the goat at the window, pushes in through it to him in bed
SEG2 = [(2150, V(HX.x + 9.0, -5.5, 1.5), V(HX.x + 7.0, -3.5, 9.0), 26),
        (2190, V(HX.x + 7.6, -3.6, 1.35), V(HX.x + 3.4, 0.0, 1.05), 28),
        (2235, V(HX.x + 4.6, -0.55, 1.25), V(HX.x + 3.2, 0.0, 1.0), 30),
        (2275, V(HX.x + 2.8, -0.6, 1.35), V(HX.x + 1.2, 1.0, 0.85), 30),
        (2300, V(HX.x + 1.6, -1.45, 1.45), V(HX.x + 1.6, 0.9, 0.9), 28),
        (2340, V(HX.x + 0.25, -1.75, 1.55), V(HX.x + 2.1, 0.55, 1.0), 26)]
for seg in (SEG1, SEG2):
    fc = catmull([(f, c) for f, c, a, l in seg]); fa = catmull([(f, a) for f, c, a, l in seg]); fl = catmull([(f, float(l)) for f, c, a, l in seg])
    f0, f1 = seg[0][0], seg[-1][0]
    for f in list(range(f0, f1 + 1, 3)) + [f1]:
        cam.location = fc(f); cam.keyframe_insert("location", frame=f)
        aim.location = fa(f); aim.keyframe_insert("location", frame=f)
        cam_d.lens = fl(f); cam_d.keyframe_insert("lens", frame=f)
stepped(cam, {2149}); stepped(aim, {2149})
cd_ad = cam_d.animation_data
for layer in getattr(cd_ad.action, "layers", []):
    for strip in layer.strips:
        for cb in strip.channelbags:
            for fcv in cb.fcurves:
                for kp in fcv.keyframe_points:
                    if int(round(kp.co.x)) == 2149: kp.interpolation = 'CONSTANT'

def clear_keys(obj, bone, f0, f1):
    ad = obj.animation_data
    for layer in ad.action.layers:
        for strip in layer.strips:
            for cb in strip.channelbags:
                for fcv in cb.fcurves:
                    if ('"%s"' % bone) in fcv.data_path:
                        for kp in [k for k in fcv.keyframe_points if f0 <= k.co.x <= f1][::-1]:
                            fcv.keyframe_points.remove(kp)
for s_ in "LR":
    clear_keys(F, "IK_hand." + s_, 1645, 1972)
GB = bpy.data.objects["goat_body"]
_hy = G.data.bones["upper.HL"].head_local.y
_cands = [v for v in GB.data.vertices if abs(v.co.x) < 0.035 and _hy - 0.16 < v.co.y < _hy + 0.02]
UDDER_V = min(_cands, key=lambda v: v.co.z).index
def udder(f):
    ev(f)
    dg = bpy.context.evaluated_depsgraph_get()
    me = GB.evaluated_get(dg).to_mesh()
    p = GB.matrix_world @ me.vertices[UDDER_V].co
    GB.evaluated_get(dg).to_mesh_clear()
    return p
def key_pt(s_, f, name):
    ev(f); M = FR.delta("spine01"); R3 = M.to_3x3(); sx = 1 if s_ == "L" else -1
    W, d, n = HAND_PT[name](sx)
    FR.key_world("IK_hand." + s_, f, hand_matrix(s_, M @ W, R3 @ d, R3 @ n))
def bkey(f, loc, R):
    bottle.location = loc; bottle.rotation_euler = R.to_euler()
    bottle.keyframe_insert("location", frame=f); bottle.keyframe_insert("rotation_euler", frame=f)
def grip_key(f, toward):
    """right hand wraps the bottle at mid height, on his side of it"""
    ev(f)
    M = bottle.matrix_world; ax = (M.to_3x3() @ Vector((0, 0, 1))).normalized()
    side = (toward - ax * toward.dot(ax)).normalized()
    centre = M @ Vector((0, 0, 0.085))
    W = centre + side * 0.05
    d = ax.cross(side).normalized()
    FR.key_world("IK_hand.R", f, hand_matrix("R", W, d, -side))
u0 = udder(1670)
TOWARD = (LIE_POS - u0).to_2d().normalized().to_3d()
STAND_XY = u0.to_2d() + TOWARD.to_2d() * 0.02
STAND_LOC = Vector((STAND_XY.x, STAND_XY.y, gz(STAND_XY.to_3d()) - 0.03))
REST_LOC, REST_R = bottle.location.copy(), bottle.rotation_euler.to_matrix()
I3 = Matrix.Identity(3)
# reach (1640->1650), lift and stand it under the udder (1650->1668)
grip_key(1650, TOWARD)
bkey(1659, REST_LOC.lerp(STAND_LOC, 0.5) + Vector((0, 0, 0.12)), (Quaternion().slerp(REST_R.to_quaternion(), 0.5)).to_matrix())
grip_key(1659, TOWARD)
bkey(1668, STAND_LOC, I3); grip_key(1668, TOWARD)
bkey(1840, STAND_LOC, I3)
# milking: right hand squeezes the teat (rhythmic), left hand rests on his chest
for i, f in enumerate(range(1678, 1831, 10)):
    u = udder(f)
    UD.location = u + Vector((0, 0, -0.03)); UD.keyframe_insert("location", frame=f)
    sq = (i % 2)
    W = u + TOWARD * 0.045 + Vector((0, 0, -0.045 - 0.025 * sq))
    FR.key_world("IK_hand.R", f, hand_matrix("R", W, Vector((0, 0, 1)), -TOWARD))
for f in (1650, 1760, 1972):
    key_pt("L", f, "chest")
# pick it up again (1840->1852) and drink, bottle bottom up so the milk flows (1880-1945)
grip_key(1852, TOWARD)
def lips(f):
    ev(f)
    hb = FR.PB["head"]
    return F.matrix_world @ (hb.matrix @ (hb.bone.matrix_local.inverted() @ Vector((0.0, -0.165, 1.60))))
D_B = Vector((-HEAD_DIR.x * 0.8, -HEAD_DIR.y * 0.8, 0.62)).normalized()
for f, gap in ((1866, 0.16), (1882, 0.006), (1905, 0.004), (1928, 0.004), (1945, 0.006), (1960, 0.12)):
    lp = lips(f)
    up_b = -D_B
    R = Vector((0, 0, 1)).rotation_difference(up_b).to_matrix()
    bkey(f, lp + D_B * (0.2165 + gap), R)
    grip_key(f, TOWARD)
ev(1972); chest = F.matrix_world @ FR.PB["spine02"].head + Vector((0, 0, 0.13))
bkey(1972, chest + Vector((0, 0, 0.0)), Vector((0, 0, 1)).rotation_difference(Vector((HEAD_DIR.x, HEAD_DIR.y, 0.35)).normalized()).to_matrix())
grip_key(1972, TOWARD)
# right hand reaches to her neck when she arrives, rests on her back at night
for s_ in ("R",):
    clear_keys(F, "IK_hand." + s_, 1105, 1180)
    clear_keys(F, "IK_hand." + s_, 1270, 1390)
for f in (1120, 1145, 1175):
    ev(f); nk = G.matrix_world @ G.pose.bones["neck1"].head
    tgt = nk + Vector((0, 0, -0.06)) - (nk - LIE_POS).normalized() * 0.07
    FR.key_world("IK_hand.R", f, hand_matrix("R", tgt, (nk - F.matrix_world @ FR.PB["upperarm01.R"].head).normalized(), Vector((0, 0, -1))))
for f in (1290, 1340, 1388):
    ev(f); bk = G.matrix_world @ G.pose.bones["spine1"].head
    tgt = bk + Vector((0, 0, 0.07)) - (bk - LIE_POS).normalized() * 0.05
    FR.key_world("IK_hand.R", f, hand_matrix("R", tgt, (bk - LIE_POS).normalized(), Vector((0, 0, -1))))
print("FX_LIGHT_CAMERA_DONE")
