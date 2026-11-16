"""PhoneCrazy sets: dig site (origin) + cross-section block (x=300). blender -b work/chars.blend -P 02_sets.py -- work/sets.blend"""
import sys, os
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib.py")).read())
out = sys.argv[sys.argv.index("--") + 1]
random.seed(7)
SITE = coll("SITE"); XS = coll("XSECTION"); EXC = coll("EXCAVATOR")
PIT = Vector((0.0, 7.0, 0.0)); PR, PD = 3.6, 2.0          # pit centre, radius, depth
HOLE_R, HOLE_D = 0.75, 1.6                                # drain hole at the pit bottom

# ------------------------------------------------------------------ world, look
w = bpy.data.worlds.new("Sky"); sc.world = w; w.use_nodes = True; nt = w.node_tree
env = nt.nodes.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(os.path.join(PH, "hdri", "kloofendal_48d_partly_cloudy_puresky_2k.hdr"))
mpw = nt.nodes.new("ShaderNodeMapping"); tcw = nt.nodes.new("ShaderNodeTexCoord"); nt.links.new(tcw.outputs["Generated"], mpw.inputs[0]); nt.links.new(mpw.outputs[0], env.inputs[0])
mpw.inputs["Rotation"].default_value = (0, 0, R_(200))
bg = nt.nodes["Background"]; nt.links.new(env.outputs[0], bg.inputs[0]); bg.inputs[1].default_value = 1.0
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 3.4; sun.data.angle = R_(3); sun.rotation_euler = (R_(40), 0, R_(-30)); sun.data.color = (1.0, 0.97, 0.92)
sc.render.engine = 'CYCLES'; sc.render.resolution_x, sc.render.resolution_y = 1080, 1920; sc.render.fps = 60
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Punchy'

# ------------------------------------------------------------------ ground materials: dirt site fading to grass, soil walls on steep slopes
def ground_mat():
    m = bpy.data.materials.new("SiteGround"); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; L = nt.links; P = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    def tex(folder, key, scale, nc=False):
        d = os.path.join(PH, folder, "textures"); f = [x for x in os.listdir(d) if key in x.lower()][0]
        mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (scale,) * 3; L.new(tc.outputs["Object"], mp.inputs[0])
        t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(os.path.join(d, f), check_existing=True); t.projection = 'BOX'; t.projection_blend = 0.35
        if nc: t.image.colorspace_settings.name = "Non-Color"
        L.new(mp.outputs[0], t.inputs[0]); return t
    dirt = tex("brown_mud", "diff", 0.25); wall = tex("excavated_soil_wall", "diff", 0.35); grass = tex("leafy_grass", "diff", 0.3)
    def tint(sock, rgb):
        mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs[0].default_value = 1
        L.new(sock, mx.inputs[6]); mx.inputs[7].default_value = (*rgb, 1); return mx.outputs[2]
    dirt_c = tint(dirt.outputs[0], (1.05, 0.85, 0.68)); wall_c = tint(wall.outputs[0], (0.78, 0.64, 0.52)); grass_c = tint(grass.outputs[0], (0.55, 1.0, 0.35))
    # steepness -> soil wall
    geo = N.new("ShaderNodeNewGeometry"); sz = N.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs["Normal"], sz.inputs[0])
    st = N.new("ShaderNodeMapRange"); L.new(sz.outputs["Z"], st.inputs[0]); st.inputs[1].default_value = 0.85; st.inputs[2].default_value = 0.7
    m1 = N.new("ShaderNodeMix"); m1.data_type = 'RGBA'; L.new(st.outputs[0], m1.inputs[0]); L.new(dirt_c, m1.inputs[6]); L.new(wall_c, m1.inputs[7])
    # distance from the site centre -> grass (noisy edge)
    so = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], so.inputs[0])
    cx = N.new("ShaderNodeVectorMath"); cx.operation = 'SUBTRACT'; L.new(tc.outputs["Object"], cx.inputs[0]); cx.inputs[1].default_value = (-1.0, 4.0, 0.0)
    ln = N.new("ShaderNodeVectorMath"); ln.operation = 'LENGTH'; L.new(cx.outputs[0], ln.inputs[0])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.35; L.new(tc.outputs["Object"], nz.inputs["Vector"])
    ad = N.new("ShaderNodeMath"); ad.operation = 'MULTIPLY_ADD'; L.new(nz.outputs["Fac"], ad.inputs[0]); ad.inputs[1].default_value = 6.0; L.new(ln.outputs["Value"], ad.inputs[2])
    gr = N.new("ShaderNodeMapRange"); L.new(ad.outputs[0], gr.inputs[0]); gr.inputs[1].default_value = 17.0; gr.inputs[2].default_value = 18.5
    m2 = N.new("ShaderNodeMix"); m2.data_type = 'RGBA'; L.new(gr.outputs[0], m2.inputs[0]); L.new(m1.outputs[2], m2.inputs[6]); L.new(grass_c, m2.inputs[7])
    dz = N.new("ShaderNodeMapRange"); L.new(so.outputs["Z"], dz.inputs[0]); dz.inputs[1].default_value = -0.1; dz.inputs[2].default_value = -2.2
    dz.inputs[3].default_value = 0.0; dz.inputs[4].default_value = 1.0
    m3 = N.new("ShaderNodeMix"); m3.data_type = 'RGBA'; m3.blend_type = 'MULTIPLY'; L.new(dz.outputs[0], m3.inputs[0]); L.new(m2.outputs[2], m3.inputs[6]); m3.inputs[7].default_value = (0.62, 0.52, 0.45, 1)
    L.new(m3.outputs[2], P.inputs["Base Color"]); P.inputs["Roughness"].default_value = 0.85; P.inputs["Specular IOR Level"].default_value = 0.2
    bump = N.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.25; L.new(dirt.outputs[0], bump.inputs["Height"]); L.new(bump.outputs[0], P.inputs["Normal"])
    return m
M_ground = ground_mat()

def pit_h(x, y, hole=True):
    r = math.hypot(x - PIT.x, y - PIT.y)
    z = 0.0
    if r < PR + 0.6:
        u = min(r / PR, 1.0)
        z -= PD * (1 - u * u) ** 1.3 if r < PR else 0.0
        if r >= PR: z += 0.12 * math.sin(math.pi * (r - PR) / 0.6)       # trodden lip
    if hole and r < HOLE_R * 1.6:
        u = min(r / HOLE_R, 1.0); z -= HOLE_D * (1 - u * u) ** 1.5 if r < HOLE_R else 0.0
    return z
def mound(x, y, cx, cy, rad, h):
    r = math.hypot(x - cx, y - cy); return h * (0.5 + 0.5 * math.cos(math.pi * r / rad)) if r < rad else 0.0
def ground_h(x, y):
    z = pit_h(x, y)
    z += mound(x, y, -2.5, 12.5, 3.2, 1.1) + mound(x, y, 1.2, 13.5, 2.4, 0.7)         # spoil heaps behind the pit
    z += 0.05 * math.sin(x * 0.9) * math.cos(y * 0.7) + 0.03 * math.sin(x * 2.3 + y * 1.7)
    if math.hypot(x + 4.0, y - 0.6) < 2.6: z *= 0.3                                     # flat where the crew stands
    return z

def grid_mesh(name, x0, x1, y0, y1, step, hfun, m, c):
    nx = int((x1 - x0) / step) + 1; ny = int((y1 - y0) / step) + 1
    bm = bmesh.new(); vs = []
    for j in range(ny):
        for i in range(nx):
            x = x0 + i * step; y = y0 + j * step; vs.append(bm.verts.new((x, y, hfun(x, y))))
    for j in range(ny - 1):
        for i in range(nx - 1):
            a = j * nx + i; bm.faces.new((vs[a], vs[a + 1], vs[a + nx + 1], vs[a + nx]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); c.objects.link(o); me.materials.append(m)
    for p in me.polygons: p.use_smooth = True
    return o
GROUND = grid_mesh("Ground", -22, 22, -16, 30, 0.2, ground_h, M_ground, SITE)
FAR = grid_mesh("FarGround", -260, 260, -240, 300, 10.0,
                lambda x, y: (-6.0 if abs(x) < 21 and -15 < y < 29 else 0.0) + (0.0 if math.hypot(x, y) < 40 else 3.0 * (0.5 + 0.5 * math.sin(x * 0.02 + 1) * math.cos(y * 0.025))),
                M_ground, SITE)

# ------------------------------------------------------------------ water in the pit (level keyed in 03_anim; radius follows the bowl)
def water_mat():
    m = bpy.data.materials.new("PitWater"); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; L = nt.links; P = N["Principled BSDF"]
    P.inputs["Base Color"].default_value = (0.12, 0.32, 0.38, 1); P.inputs["Roughness"].default_value = 0.12
    P.inputs["Specular IOR Level"].default_value = 0.05; P.inputs["Coat Weight"].default_value = 0.0
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.name = "Swirl"; L.new(tc.outputs["Object"], mp.inputs[0])
    # polar swirl: noise on (angle + k/r, r) so rotating the mapping reads as a whirlpool
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 2.2; nz.inputs["Detail"].default_value = 4; L.new(mp.outputs[0], nz.inputs["Vector"])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.25; L.new(nz.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs[0], P.inputs["Normal"])
    cr = N.new("ShaderNodeValToRGB"); L.new(nz.outputs["Fac"], cr.inputs[0]); cr.color_ramp.elements[0].color = (0.07, 0.22, 0.28, 1); cr.color_ramp.elements[1].color = (0.25, 0.5, 0.55, 1)
    L.new(cr.outputs[0], P.inputs["Base Color"])
    return m
M_water = water_mat()
bpy.ops.mesh.primitive_circle_add(vertices=96, radius=1.0, fill_type='TRIFAN', location=(PIT.x, PIT.y, 0)); WATER = bpy.context.active_object; WATER.name = "PitWater"
WATER.data.materials.append(M_water); link(WATER, SITE)
# swirl dimple: a shallow cone in the middle of the water (scale keyed in 03_anim)
bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=1.0, radius2=0.02, depth=1.0, location=(PIT.x, PIT.y, 0), rotation=(math.pi, 0, 0)); VORT = bpy.context.active_object
VORT.name = "Vortex"; VORT.data.transform(Matrix.Translation((0, 0, 0.5))); bpy.ops.object.shade_smooth(); link(VORT, SITE)
def vortex_mat():
    """concave funnel: spiral streaks (angle + k*r), darker toward the throat; 03_anim keys the 'Spin' value"""
    m = bpy.data.materials.new("Whirlpool"); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; L = nt.links; P = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); sx = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sx.inputs[0])
    at = N.new("ShaderNodeMath"); at.operation = 'ARCTAN2'; L.new(sx.outputs["Y"], at.inputs[0]); L.new(sx.outputs["X"], at.inputs[1])
    ln = N.new("ShaderNodeVectorMath"); ln.operation = 'LENGTH'; L.new(tc.outputs["Object"], ln.inputs[0])
    k = N.new("ShaderNodeMath"); k.operation = 'MULTIPLY_ADD'; L.new(ln.outputs["Value"], k.inputs[0]); k.inputs[1].default_value = 9.0; L.new(at.outputs[0], k.inputs[2])
    a3 = N.new("ShaderNodeMath"); a3.operation = 'MULTIPLY'; L.new(at.outputs[0], a3.inputs[0]); a3.inputs[1].default_value = 3.0
    sm = N.new("ShaderNodeMath"); sm.operation = 'ADD'; L.new(a3.outputs[0], sm.inputs[0]); L.new(k.outputs[0], sm.inputs[1])
    sp = N.new("ShaderNodeValue"); sp.name = "Spin"
    s2 = N.new("ShaderNodeMath"); s2.operation = 'ADD'; L.new(sm.outputs[0], s2.inputs[0]); L.new(sp.outputs[0], s2.inputs[1])
    sn = N.new("ShaderNodeMath"); sn.operation = 'SINE'; L.new(s2.outputs[0], sn.inputs[0])
    cr = N.new("ShaderNodeValToRGB"); L.new(sn.outputs[0], cr.inputs[0]); cr.color_ramp.elements[0].position = 0.0; cr.color_ramp.elements[1].position = 1.0   # soft, water-coloured streaks
    cr.color_ramp.elements[0].color = (0.012, 0.05, 0.07, 1); cr.color_ramp.elements[1].color = (0.05, 0.15, 0.18, 1)
    dk = N.new("ShaderNodeMapRange"); L.new(ln.outputs["Value"], dk.inputs[0]); dk.inputs[1].default_value = 0.0; dk.inputs[2].default_value = 0.9
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; L.new(dk.outputs[0], mx.inputs[0]); mx.inputs[0].default_value = 1
    L.new(cr.outputs[0], mx.inputs[6]); L.new(dk.outputs[0], mx.inputs[7])
    L.new(mx.outputs[2], P.inputs["Base Color"]); P.inputs["Roughness"].default_value = 0.3; P.inputs["Specular IOR Level"].default_value = 0.1
    return m
VORT.data.materials.append(vortex_mat())

# ------------------------------------------------------------------ excavator (CC-BY, articulated): clean animated-look materials
def excavator(root_name, c):
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=os.path.join(ASSETS, "excavator_anim.glb"))
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        link(o, c)
        if o.animation_data: o.animation_data_clear()
    for o in new:
        if o.rotation_mode == 'QUATERNION': o.rotation_quaternion = (1, 0, 0, 0)
    top = [o for o in new if o.parent is None][0]
    root = bpy.data.objects.new(root_name, None); c.objects.link(root); top.parent = root
    cols = {"Body_MAT": ((0.95, 0.66, 0.05), 0.4, 0.0), "Arm_MAT": ((0.95, 0.66, 0.05), 0.4, 0.0), "Scoop_MAT": ((0.22, 0.22, 0.24), 0.45, 0.6),
            "Tire_MAT": ((0.07, 0.07, 0.08), 0.7, 0.0), "Gear_MAT": ((0.18, 0.18, 0.2), 0.5, 0.5), "Rod_MAT": ((0.75, 0.76, 0.78), 0.3, 0.9),
            "Pipe_MAT": ((0.06, 0.06, 0.07), 0.6, 0.0), "Bolts_MAT": ((0.3, 0.3, 0.32), 0.4, 0.8), "Chair_MAT": ((0.08, 0.08, 0.09), 0.7, 0.0),
            "Control_MAT": ((0.08, 0.08, 0.09), 0.6, 0.0), "Pedal_MAT": ((0.1, 0.1, 0.11), 0.6, 0.0), "phong3": ((0.1, 0.2, 0.28), 0.05, 0.0)}
    for o in new:
        if o.type != 'MESH': continue
        for i, m_ in enumerate(o.data.materials):
            key = next((k for k in cols if m_ and m_.name.startswith(k)), None)
            if key:
                rgb, ro, me = cols[key]; o.data.materials[i] = mat("EXC_" + key, rgb, ro, me, spec=0.4)
    return root, {o.name.split(".")[0]: o for o in new}
EXR, EXP = excavator("EXC_root", EXC)
bpy.context.view_layer.update()
pts = [o.matrix_world @ Vector(cc) for o in EXP.values() if o.type == 'MESH' for cc in o.bound_box]
mn = Vector([min(p[i] for p in pts) for i in range(3)]); mx = Vector([max(p[i] for p in pts) for i in range(3)])
k = 3.6 / (mx.z - mn.z); EXR.scale = (k, k, k); EXR["base_off"] = (-(mn.z) * k)
print("EXC bbox", mn, mx, "scale", k)

# ------------------------------------------------------------------ site case (the phone lies on it) with the DA KRAS FILMS logo on its front
CASE_P = Vector((-4.0, 0.55, 0.0)); CW, CD, CH_ = 0.62, 0.42, 0.62
M_case = mat("CaseOrange", (0.95, 0.38, 0.05), 0.45, spec=0.35); M_caseD = mat("CaseDark", (0.08, 0.08, 0.09), 0.5); M_latch = mat("Latch", (0.75, 0.75, 0.78), 0.3, 0.9)
body = box("Case", (CW, CD, CH_ - 0.08), (0, 0, (CH_ - 0.08) / 2), M_case, SITE, bevel=0.025)
lid = box("Case.lid", (CW + 0.02, CD + 0.02, 0.08), (0, 0, CH_ - 0.04), M_case, SITE, bevel=0.02)
rim = box("Case.rim", (CW + 0.025, CD + 0.025, 0.018), (0, 0, CH_ - 0.085), M_caseD, SITE, bevel=0.004)
parts = [body, lid, rim]
for sx in (-1, 1):
    parts.append(box("Case.latch", (0.06, 0.02, 0.07), (sx * 0.2, -CD / 2 - 0.012, CH_ - 0.085), M_latch, SITE, bevel=0.006))
    parts.append(box("Case.foot", (0.08, CD - 0.04, 0.03), (sx * 0.22, 0, 0.015), M_caseD, SITE, bevel=0.008))
for sx in (-1, 1):   # side handles
    parts.append(box("Case.handle", (0.02, 0.18, 0.04), (sx * (CW / 2 + 0.03), 0, CH_ - 0.2), M_caseD, SITE, bevel=0.008))
for p_ in parts:
    for md in p_.modifiers:
        with bpy.context.temp_override(object=p_): bpy.ops.object.modifier_apply(modifier=md.name)
CASE = join(parts, "Case"); CASE.location = CASE_P; CASE.rotation_euler = (0, 0, R_(-8)); link(CASE, SITE)
# logo decal (white version on the orange case), flat on the front face
lm = bpy.data.materials.new("Logo_white"); lm.use_nodes = True; lnt = lm.node_tree; LP = lnt.nodes["Principled BSDF"]
li = lnt.nodes.new("ShaderNodeTexImage"); li.image = bpy.data.images.load(os.path.join(FILM, "..", "assets", "brand", "DaKrasFilms_logo_white.png")); li.extension = 'CLIP'
lnt.links.new(li.outputs["Color"], LP.inputs["Base Color"]); lnt.links.new(li.outputs["Alpha"], LP.inputs["Alpha"]); LP.inputs["Roughness"].default_value = 0.5
lw = 0.46; lh = lw * 414 / 967
LOGO = plane("Case.logo", (lw, lh), (0, 0, 0), lm, SITE)
LOGO.data.transform(Matrix.Rotation(R_(90), 4, 'X')); LOGO.location = (0, -CD / 2 - 0.0035, (CH_ - 0.1) * 0.5); LOGO.parent = CASE

# ------------------------------------------------------------------ phone (CC-BY) lying face-up on the case lid, + screen plane with the atlas
before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=os.path.join(ASSETS, "phone.glb"))
new = [o for o in bpy.data.objects if o not in before]; bpy.context.view_layer.update()
pm = [o for o in new if o.type == 'MESH'][0]; mw = pm.matrix_world.copy(); pm.parent = None; pm.data = pm.data.copy(); pm.data.transform(mw); pm.matrix_world.identity()
for o in new:
    if o is not pm: bpy.data.objects.remove(o, do_unlink=True)
PHONE = pm; PHONE.name = "Phone"; link(PHONE, SITE)
def vbb(o):
    o.data.update(); co = [v.co for v in o.data.vertices]
    return Vector([min(p[i] for p in co) for i in range(3)]), Vector([max(p[i] for p in co) for i in range(3)])
mn, mx = vbb(PHONE); print("PHONE raw", mn, mx)
PHONE.data.transform(Matrix.Translation(-(mn + mx) / 2))
PHONE.data.transform(Matrix.Rotation(R_(-90), 4, 'Y'))
mn, mx = vbb(PHONE); ext = mx - mn
if ext.x > ext.y: PHONE.data.transform(Matrix.Rotation(R_(90), 4, 'Z'))
mn, mx = vbb(PHONE); k = 0.16 / (mx.y - mn.y); PHONE.data.transform(Matrix.Scale(k, 4))
mn, mx = vbb(PHONE); print("PHONE flat", mn, mx)
PHONE.data.transform(Matrix.Translation((0, 0, -mn.z)))
for mm in PHONE.data.materials:
    if mm and mm.node_tree:
        P_ = next(n for n in mm.node_tree.nodes if n.type == "BSDF_PRINCIPLED"); P_.inputs["Roughness"].default_value = max(P_.inputs["Roughness"].default_value, 0.3)
sm = bpy.data.materials.new("PhoneScreen"); sm.use_nodes = True; snt = sm.node_tree; SN = snt.nodes; SL = snt.links
for n in list(SN): SN.remove(n)
o_ = SN.new("ShaderNodeOutputMaterial"); em = SN.new("ShaderNodeEmission"); em.inputs["Strength"].default_value = 1.6
gl = SN.new("ShaderNodeBsdfGlossy"); gl.inputs["Roughness"].default_value = 0.05; gl.inputs["Color"].default_value = (0.25, 0.25, 0.27, 1)
fr = SN.new("ShaderNodeFresnel"); fr.inputs["IOR"].default_value = 1.5; ad_ = SN.new("ShaderNodeAddShader")
mxs = SN.new("ShaderNodeMixShader"); SL.new(fr.outputs[0], mxs.inputs[0]); SL.new(em.outputs[0], mxs.inputs[1]); SL.new(gl.outputs[0], mxs.inputs[2])
SL.new(mxs.outputs[0], o_.inputs[0])
uv = SN.new("ShaderNodeUVMap"); mp = SN.new("ShaderNodeMapping"); mp.name = "Tile"; mp.vector_type = 'POINT'
mp.inputs["Scale"].default_value = (1 / 8, 1 / 3, 1); SL.new(uv.outputs[0], mp.inputs[0])
im = SN.new("ShaderNodeTexImage"); im.image = bpy.data.images.load(os.path.join(ASSETS, "screens.png")); im.interpolation = 'Linear'; im.extension = 'CLIP'
SL.new(mp.outputs[0], im.inputs[0]); SL.new(im.outputs[0], em.inputs["Color"])
# glitch jitter: keyed X offset added through the mapping location (03_anim keys location = tile offset + jitter)
sw, sh = (mx.x - mn.x) * 0.9, (mx.y - mn.y) * 0.93
SCR = plane("Phone.screen", (sw, sh), (0, 0, 0), sm, SITE)
SCR.location = (0, 0, (mx.z - mn.z) + 0.0004); SCR.parent = PHONE
PHONE.location = CASE_P + Vector((0.03, 0.02, CH_)); PHONE.rotation_euler = (0, 0, R_(-14))
PHONE["thick"] = mx.z - mn.z

# ------------------------------------------------------------------ cross-section block (x = 300): pit on top, cut face showing a cavern and an underground stream
XO = Vector((300.0, 0.0, 0.0))
def soil_mat():
    m = bpy.data.materials.new("SoilSection"); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; L = nt.links; P = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); sz = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sz.inputs[0])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.6; L.new(tc.outputs["Object"], nz.inputs["Vector"])
    ad = N.new("ShaderNodeMath"); ad.operation = 'MULTIPLY_ADD'; L.new(nz.outputs["Fac"], ad.inputs[0]); ad.inputs[1].default_value = 0.9; L.new(sz.outputs["Z"], ad.inputs[2])
    cr = N.new("ShaderNodeValToRGB"); L.new(ad.outputs[0], cr.inputs[0]); cr.color_ramp.interpolation = 'CONSTANT'
    E = cr.color_ramp.elements
    E[0].position = 0.0; E[0].color = (0.16, 0.10, 0.07, 1); E[1].position = 0.995; E[1].color = (0.36, 0.55, 0.15, 1)
    for pos, c_ in ((0.45, (0.30, 0.21, 0.14, 1)), (0.62, (0.42, 0.30, 0.19, 1)), (0.76, (0.55, 0.42, 0.28, 1)), (0.88, (0.44, 0.30, 0.19, 1)), (0.96, (0.36, 0.24, 0.15, 1))):
        e = E.new(pos); e.color = c_
    mr = N.new("ShaderNodeMapRange"); L.new(ad.outputs[0], mr.inputs[0]); mr.inputs[1].default_value = -13.0; mr.inputs[2].default_value = 13.3
    L.new(mr.outputs[0], cr.inputs[0])
    dt = N.new("ShaderNodeTexImage"); d = os.path.join(PH, "excavated_soil_wall", "textures"); dt.image = bpy.data.images.load(os.path.join(d, [x for x in os.listdir(d) if "diff" in x][0]), check_existing=True)
    dt.projection = 'BOX'; mpp = N.new("ShaderNodeMapping"); mpp.inputs["Scale"].default_value = (0.3,) * 3; L.new(tc.outputs["Object"], mpp.inputs[0]); L.new(mpp.outputs[0], dt.inputs[0])
    mx_ = N.new("ShaderNodeMix"); mx_.data_type = 'RGBA'; mx_.blend_type = 'OVERLAY'; mx_.inputs[0].default_value = 0.45; L.new(cr.outputs[0], mx_.inputs[6]); L.new(dt.outputs[0], mx_.inputs[7])
    L.new(mx_.outputs[2], P.inputs["Base Color"]); P.inputs["Roughness"].default_value = 0.85
    return m
M_soil = soil_mat()
BW, BDp, BH = 16.0, 12.0, 26.0
blk = grid_mesh("XS_top", -BW / 2, BW / 2, -BDp / 2, BDp / 2, 0.2, lambda x, y: pit_h(x, y + 7.0 - 0.0 - (7.0 - PIT.y) - (-0.0)) if False else 0.0, M_ground, XS)
bpy.data.objects.remove(blk, do_unlink=True)
bpy.ops.mesh.primitive_cube_add(size=1); B_ = bpy.context.active_object; B_.name = "XS_block"
B_.scale = (BW, BDp, BH); bpy.ops.object.transform_apply(scale=True); B_.location = XO + Vector((0, 0, -BH / 2))
M_top = pbr('XSTop', 'brown_mud', 0.25, tint=(1.05, 0.85, 0.68), coords='Object'); B_.data.materials.append(M_soil); B_.data.materials.append(M_top); link(B_, XS)
for p_ in B_.data.polygons:
    if p_.normal.z > 0.9: p_.material_index = 1
def cutter(name, verts_fn):
    o = verts_fn(); o.name = name; o.data.materials.append(M_soil); o.display_type = 'WIRE'; o.hide_render = True; link(o, XS)
    md = B_.modifiers.new(name, 'BOOLEAN'); md.object = o; md.operation = 'DIFFERENCE'; md.solver = 'EXACT'; return o
FRONT = -BDp / 2
def c_pit():
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=1.0, location=XO + Vector((0, FRONT + 2.2, 0))); o = bpy.context.active_object
    o.scale = (PR, PR, PD * 1.15); bpy.ops.object.transform_apply(scale=True); return o
def c_shaft():
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.55, depth=6.0, location=XO + Vector((0.3, FRONT + 0.6, -4.0)), rotation=(R_(18), 0, 0)); return bpy.context.active_object
def c_cave():
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=1.0, location=XO + Vector((0.8, FRONT + 0.4, -7.6))); o = bpy.context.active_object
    o.scale = (3.6, 2.2, 1.6); bpy.ops.object.transform_apply(scale=True)
    for v in o.data.vertices: v.co += v.co.normalized() * 0.25 * math.sin(v.co.x * 2.1 + v.co.z * 3.3)
    return o
cutter("XS_cut_pit", c_pit); cutter("XS_cut_shaft", c_shaft); cutter("XS_cut_cave", c_cave)
# stream: water ribbon falling down the shaft into a pool in the cavern (flow keyed through its texture mapping)
M_stream = mat("Stream", (0.15, 0.55, 0.95), 0.1, emit=(0.2, 0.6, 1.0), emit_s=1.2, spec=0.5)
sn = M_stream.node_tree; P_ = sn.nodes["Principled BSDF"]; tc_ = sn.nodes.new("ShaderNodeTexCoord"); mps = sn.nodes.new("ShaderNodeMapping"); mps.name = "Flow"
wv = sn.nodes.new("ShaderNodeTexWave"); wv.wave_type = 'BANDS'; wv.bands_direction = 'Z'; wv.inputs["Scale"].default_value = 1.4; wv.inputs["Distortion"].default_value = 4
sn.links.new(tc_.outputs["Object"], mps.inputs[0]); sn.links.new(mps.outputs[0], wv.inputs["Vector"])
crs = sn.nodes.new("ShaderNodeValToRGB"); sn.links.new(wv.outputs["Fac"], crs.inputs[0]); crs.color_ramp.elements[0].color = (0.08, 0.35, 0.85, 1); crs.color_ramp.elements[1].color = (0.6, 0.85, 1.0, 1)
sn.links.new(crs.outputs[0], P_.inputs["Base Color"]); sn.links.new(crs.outputs[0], P_.inputs["Emission Color"])
cu = bpy.data.curves.new("StreamC", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.22; cu.bevel_resolution = 3; cu.resolution_u = 16
spl = cu.splines.new('BEZIER'); pts_ = [(0.0, FRONT + 2.2, -1.9), (0.15, FRONT + 1.3, -3.2), (0.4, FRONT + 0.8, -5.0), (0.7, FRONT + 0.6, -6.6), (1.4, FRONT + 0.7, -8.4)]
spl.bezier_points.add(len(pts_) - 1)
for bp_, p_ in zip(spl.bezier_points, pts_): bp_.co = XO + Vector(p_); bp_.handle_left_type = bp_.handle_right_type = 'AUTO'
ST = bpy.data.objects.new("XS_stream", cu); XS.objects.link(ST); cu.materials.append(M_stream)
bpy.ops.mesh.primitive_circle_add(vertices=48, radius=1.0, fill_type='NGON', location=XO + Vector((0.9, FRONT + 0.9, -8.75))); POOL = bpy.context.active_object
POOL.name = "XS_pool"; POOL.scale = (3.0, 1.4, 1); POOL.data.materials.append(M_stream); link(POOL, XS)
# green surface around the block + an instance of the excavator at the pit rim
XG = grid_mesh("XS_grass", -BW / 2 - 40, BW / 2 + 40, -BDp / 2 + 0.001, 80, 2.0, lambda x, y: 0.0, M_ground, XS); XG.location = XO
XG.hide_render = True    # placeholder off: the block reads cleaner on the sky
inst = bpy.data.objects.new("XS_excavator", None); inst.instance_type = 'COLLECTION'; inst.instance_collection = EXC; XS.objects.link(inst)
inst["note"] = "instance of the site excavator; placed in 03_anim relative to EXC_root"
bpy.ops.wm.save_as_mainfile(filepath=out)
print("SETS OK")
