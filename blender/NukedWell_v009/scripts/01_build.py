"""NukedWell v009 stage A (from scratch): one desert diorama with a clean side cut-away, two crew, the device, the fire.
blender -b --python 01_build.py -- <polyhaven_dir> <models_dir> <out.blend>

World: +X right, ground surface z=0. The ground slab is cut at y=0 (the cut face looks at -Y, where the camera works),
so one view shows the surface, both shafts and the depth together. Nuke bore at x=-3 (vertical, device bottom z=-18.5),
gas well casing at x=+7 (down to the reservoir at z=-24..-30). The crew stand at the nuke collar under an A-frame
headframe whose sheave carries the device cable to a winch. Everything that animates is driven by keyed values
(no Scene Time, no particles, no simulations, no volumes)."""
import bpy, bmesh, sys, math, random, os
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "lib_build.py")).read())
a = sys.argv[sys.argv.index("--") + 1:]
PH, MD, OUT = a[0], a[1], a[2]
PKG = os.path.dirname(HERE)
random.seed(18)
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
sc = bpy.context.scene
sc.render.fps = 60
sc.frame_start, sc.frame_end = 1, 1541
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
NBX, GPX = -3.0, 7.0
DEV_BOT = -18.5

def col(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in sc.collection.children: sc.collection.children.link(c)
    return c
C_SET, C_FX, C_CH = col("SET"), col("FX"), col("CREW")
def to_col(o, c):
    for cc in list(o.users_collection): cc.objects.unlink(o)
    c.objects.link(o)
JOLT = bpy.data.objects.new("Jolt", None); C_SET.objects.link(JOLT)   # surface jolt at the detonation (keyed in stage B)

def tex(path, cs="sRGB"):
    im = bpy.data.images.load(path, check_existing=True)
    if cs != "sRGB": im.colorspace_settings.name = "Non-Color"
    return im
def phmap(asset, kind):
    d = os.path.join(PH, asset, "textures")
    for f in sorted(os.listdir(d)):
        if kind in f.lower(): return os.path.join(d, f)
    return None

# ================================================================== materials
def node(nt, t, **kw):
    n = nt.nodes.new(t)
    for k, v in kw.items(): setattr(n, k, v)
    return n

def rock_mat():
    """strata on the cut face: banded, saturated layers built on real scanned rock textures; the blast squeeze warps
    the coordinates radially (value node 'Squeeze', keyed in stage B) and darkens a crushed ring round the cavity."""
    m = bpy.data.materials.new("M_Strata"); m.use_nodes = True; nt = m.node_tree; L = nt.links
    p = nt.nodes["Principled BSDF"]; p.inputs["Roughness"].default_value = 0.85
    tc = node(nt, "ShaderNodeTexCoord")
    # radial squeeze about the cavity centre (in the XZ plane)
    sq = node(nt, "ShaderNodeValue", name="Squeeze", label="Squeeze"); sq.outputs[0].default_value = 0.0
    cen = node(nt, "ShaderNodeCombineXYZ"); cen.inputs[0].default_value = NBX; cen.inputs[1].default_value = 0.0; cen.inputs[2].default_value = -16.9
    dv = node(nt, "ShaderNodeVectorMath", operation='SUBTRACT'); L.new(tc.outputs["Object"], dv.inputs[0]); L.new(cen.outputs[0], dv.inputs[1])
    ln = node(nt, "ShaderNodeVectorMath", operation='LENGTH'); L.new(dv.outputs[0], ln.inputs[0])
    nr = node(nt, "ShaderNodeVectorMath", operation='NORMALIZE'); L.new(dv.outputs[0], nr.inputs[0])
    # push = Squeeze * 4.5 * exp(-(r-5)^2/40) for r>~2  -> strata pulled toward the cavity rim (compressed ring)
    m1 = node(nt, "ShaderNodeMath", operation='SUBTRACT'); L.new(ln.outputs["Value"], m1.inputs[0]); m1.inputs[1].default_value = 5.0
    m2 = node(nt, "ShaderNodeMath", operation='MULTIPLY'); L.new(m1.outputs[0], m2.inputs[0]); L.new(m1.outputs[0], m2.inputs[1])
    m3 = node(nt, "ShaderNodeMath", operation='DIVIDE'); L.new(m2.outputs[0], m3.inputs[0]); m3.inputs[1].default_value = -60.0
    m4 = node(nt, "ShaderNodeMath", operation='EXPONENT'); L.new(m3.outputs[0], m4.inputs[0])
    m5 = node(nt, "ShaderNodeMath", operation='MULTIPLY'); L.new(m4.outputs[0], m5.inputs[0]); L.new(sq.outputs[0], m5.inputs[1])
    m6 = node(nt, "ShaderNodeMath", operation='MULTIPLY'); L.new(m5.outputs[0], m6.inputs[0]); m6.inputs[1].default_value = 3.2
    sc_ = node(nt, "ShaderNodeVectorMath", operation='SCALE'); L.new(nr.outputs[0], sc_.inputs[0]); L.new(m6.outputs[0], sc_.inputs["Scale"])
    P = node(nt, "ShaderNodeVectorMath", operation='ADD'); L.new(tc.outputs["Object"], P.inputs[0]); L.new(sc_.outputs[0], P.inputs[1])
    sp = node(nt, "ShaderNodeSeparateXYZ"); L.new(P.outputs[0], sp.inputs[0])
    # wobbly layer height
    nz = node(nt, "ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.08; nz.inputs["Detail"].default_value = 3
    L.new(P.outputs[0], nz.inputs["Vector"])
    wz = node(nt, "ShaderNodeMath", operation='MULTIPLY_ADD'); L.new(nz.outputs["Fac"], wz.inputs[0]); wz.inputs[1].default_value = 2.2
    L.new(sp.outputs["Z"], wz.inputs[2])
    # layer colour ramp along depth (constant bands): top soil .. gas reservoir
    cr = node(nt, "ShaderNodeValToRGB"); cr.color_ramp.interpolation = 'CONSTANT'
    mr = node(nt, "ShaderNodeMapRange"); mr.inputs["From Min"].default_value = -31.0; mr.inputs["From Max"].default_value = 1.0
    L.new(wz.outputs[0], mr.inputs["Value"])
    bands = [(-31, (0.10, 0.08, 0.30)),   # gas reservoir sandstone: deep violet
             (-24, (0.85, 0.62, 0.62)),   # salt / anhydrite: pale rose
             (-21, (0.80, 0.42, 0.08)),   # ochre sandstone
             (-16, (0.06, 0.32, 0.34)),   # shale: deep teal
             (-12, (0.92, 0.76, 0.42)),   # limestone: warm cream
             (-8, (0.45, 0.16, 0.30)),    # clay: plum
             (-5, (0.75, 0.20, 0.07)),    # red sandstone
             (-1.6, (0.85, 0.42, 0.14))]  # top soil: terracotta
    els = cr.color_ramp.elements
    els.remove(els[1]); els[0].position = 0.0; els[0].color = (*bands[0][1], 1)
    for z, c in bands[1:]:
        e = els.new((z + 31) / 32.0); e.color = (*c, 1)
    L.new(mr.outputs["Result"], cr.inputs["Fac"])
    # rock detail: scanned textures, box-projected on object coords, multiplied in
    def img(asset, kind, cs="sRGB"):
        t = node(nt, "ShaderNodeTexImage"); t.image = tex(phmap(asset, kind), cs); t.projection = 'BOX'; t.projection_blend = 0.3
        mp = node(nt, "ShaderNodeMapping"); mp.inputs["Scale"].default_value = (0.22, 0.22, 0.22)
        L.new(P.outputs[0], mp.inputs["Vector"]); L.new(mp.outputs[0], t.inputs["Vector"]); return t
    d1 = img("cliff_side", "diff"); d2 = img("dark_rock", "diff")
    mxr = node(nt, "ShaderNodeMix", data_type='RGBA'); L.new(nz.outputs["Fac"], mxr.inputs["Factor"])
    L.new(d1.outputs["Color"], mxr.inputs["A"]); L.new(d2.outputs["Color"], mxr.inputs["B"])
    hsv = node(nt, "ShaderNodeHueSaturation"); hsv.inputs["Saturation"].default_value = 0.0; hsv.inputs["Value"].default_value = 1.9
    L.new(mxr.outputs["Result"], hsv.inputs["Color"])
    mul = node(nt, "ShaderNodeMix", data_type='RGBA', blend_type='MULTIPLY'); mul.inputs["Factor"].default_value = 0.85
    L.new(cr.outputs["Color"], mul.inputs["A"]); L.new(hsv.outputs["Color"], mul.inputs["B"])
    # thin darker seams at every layer boundary
    seam = node(nt, "ShaderNodeTexWave"); seam.wave_type = 'BANDS'; seam.bands_direction = 'Z'; seam.inputs["Scale"].default_value = 0.9
    seam.inputs["Distortion"].default_value = 4.0; L.new(P.outputs[0], seam.inputs["Vector"])
    sr = node(nt, "ShaderNodeMapRange"); sr.inputs["From Min"].default_value = 0.0; sr.inputs["From Max"].default_value = 0.12
    sr.inputs["To Min"].default_value = 0.78; sr.inputs["To Max"].default_value = 1.0; L.new(seam.outputs["Fac"], sr.inputs["Value"])
    # crushed zone ring (darker, glassy) round the cavity once squeezed: r in ~[4.5, 7.5]
    c1 = node(nt, "ShaderNodeMath", operation='SUBTRACT'); L.new(ln.outputs["Value"], c1.inputs[0]); c1.inputs[1].default_value = 6.0
    c2 = node(nt, "ShaderNodeMath", operation='ABSOLUTE'); L.new(c1.outputs[0], c2.inputs[0])
    c3 = node(nt, "ShaderNodeMapRange"); c3.inputs["From Min"].default_value = 0.6; c3.inputs["From Max"].default_value = 1.8
    c3.inputs["To Min"].default_value = 1.0; c3.inputs["To Max"].default_value = 0.0; L.new(c2.outputs[0], c3.inputs["Value"])
    c4 = node(nt, "ShaderNodeMath", operation='MULTIPLY'); L.new(c3.outputs["Result"], c4.inputs[0]); L.new(sq.outputs[0], c4.inputs[1])
    crushed = node(nt, "ShaderNodeMix", data_type='RGBA'); L.new(c4.outputs[0], crushed.inputs["Factor"])
    sh = node(nt, "ShaderNodeMix", data_type='RGBA', blend_type='MULTIPLY'); sh.inputs["Factor"].default_value = 1.0
    L.new(mul.outputs["Result"], sh.inputs["A"]); L.new(sr.outputs["Result"], sh.inputs["B"])
    L.new(sh.outputs["Result"], crushed.inputs["A"]); crushed.inputs["B"].default_value = (0.10, 0.06, 0.05, 1)
    L.new(crushed.outputs["Result"], p.inputs["Base Color"])
    nm = img("cliff_side", "nor_gl", "Non-Color"); nmap = node(nt, "ShaderNodeNormalMap"); nmap.inputs["Strength"].default_value = 0.7
    L.new(nm.outputs["Color"], nmap.inputs["Color"]); L.new(nmap.outputs["Normal"], p.inputs["Normal"])
    return m

def sand_mat(name="M_Sand", tintc=(1.25, 0.62, 0.30), scale=0.12):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; L = nt.links
    p = nt.nodes["Principled BSDF"]; p.inputs["Roughness"].default_value = 0.95
    tc = node(nt, "ShaderNodeTexCoord"); mp = node(nt, "ShaderNodeMapping"); mp.inputs["Scale"].default_value = (scale, scale, scale)
    L.new(tc.outputs["Object"], mp.inputs["Vector"])
    t = node(nt, "ShaderNodeTexImage"); t.image = tex(phmap("aerial_sand", "diff")); L.new(mp.outputs[0], t.inputs["Vector"])
    mx = node(nt, "ShaderNodeMix", data_type='RGBA', blend_type='MULTIPLY'); mx.inputs["Factor"].default_value = 1.0
    L.new(t.outputs["Color"], mx.inputs["A"]); mx.inputs["B"].default_value = (*tintc, 1)
    L.new(mx.outputs["Result"], p.inputs["Base Color"])
    n = node(nt, "ShaderNodeTexImage"); n.image = tex(phmap("aerial_sand", "nor_gl"), "Non-Color"); L.new(mp.outputs[0], n.inputs["Vector"])
    nm = node(nt, "ShaderNodeNormalMap"); nm.inputs["Strength"].default_value = 0.6
    L.new(n.outputs["Color"], nm.inputs["Color"]); L.new(nm.outputs["Normal"], p.inputs["Normal"])
    return m

def concrete_mat():
    m = bpy.data.materials.new("M_Concrete"); m.use_nodes = True; nt = m.node_tree; L = nt.links
    p = nt.nodes["Principled BSDF"]; p.inputs["Roughness"].default_value = 0.9
    tc = node(nt, "ShaderNodeNewGeometry"); t = node(nt, "ShaderNodeTexImage"); t.image = tex(phmap("concrete_floor_02", "diff"))
    t.projection = 'BOX'; mp = node(nt, "ShaderNodeMapping"); mp.inputs["Scale"].default_value = (0.6, 0.6, 0.6)
    L.new(tc.outputs["Position"], mp.inputs["Vector"]); L.new(mp.outputs[0], t.inputs["Vector"])
    mx = node(nt, "ShaderNodeMix", data_type='RGBA', blend_type='MULTIPLY'); mx.inputs["Factor"].default_value = 1.0
    L.new(t.outputs["Color"], mx.inputs["A"]); mx.inputs["B"].default_value = (0.95, 0.98, 1.1, 1)
    L.new(mx.outputs["Result"], p.inputs["Base Color"])
    return m

M_STRATA = rock_mat(); M_SAND = sand_mat(); M_CONC = concrete_mat()
M_STEEL = mat("M_Steel", (0.30, 0.32, 0.36), rough=0.35, metal=0.9)
M_DARKSTEEL = mat("M_DarkSteel", (0.08, 0.08, 0.09), rough=0.45, metal=0.8)
M_RED = mat("M_HeadframeRed", (0.85, 0.10, 0.04), rough=0.45, coat=0.3)
M_YEL = mat("M_WinchYellow", (0.95, 0.62, 0.02), rough=0.4, coat=0.2)
M_CABLE = mat("M_Cable", (0.05, 0.05, 0.055), rough=0.35, metal=0.6)
M_DEV = mat("M_Device", (0.05, 0.22, 0.10), rough=0.38, coat=0.5)
M_WOOD = mat("M_Crate", (0.55, 0.32, 0.14), rough=0.7)

# ================================================================== the ground slab with the cut face and the two shafts
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 30, -16))
SLAB = bpy.context.active_object; SLAB.name = "Ground_Slab"; SLAB.scale = (80, 60, 32)
bpy.ops.object.transform_apply(scale=True)
def cutter(name, x, z0, z1, r):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=z1 - z0, location=(x, 0, (z0 + z1) / 2), vertices=48)
    c = bpy.context.active_object; c.name = name; c.hide_render = True; c.display_type = 'WIRE'; return c
CUT_NB = cutter("Cut_NukeBore", NBX, DEV_BOT - 0.35, 0.6, 0.55)
CUT_GP = cutter("Cut_GasWell", GPX, -27.0, 0.6, 0.62)
for c in (CUT_NB, CUT_GP):
    b = SLAB.modifiers.new("bool_" + c.name, 'BOOLEAN'); b.object = c; b.operation = 'DIFFERENCE'; b.solver = 'EXACT'
bpy.context.view_layer.objects.active = SLAB
for mname in [m.name for m in SLAB.modifiers]: bpy.ops.object.modifier_apply(modifier=mname)
for c in (CUT_NB, CUT_GP): bpy.data.objects.remove(c, do_unlink=True)
# materials: faces with normal z>0.7 at z~0 are sand, the rest strata
SLAB.data.materials.clear(); SLAB.data.materials.append(M_STRATA); SLAB.data.materials.append(M_SAND)
for pl in SLAB.data.polygons:
    pl.material_index = 1 if (pl.normal.z > 0.7 and pl.center.z > -0.05) else 0
to_col(SLAB, C_SET); SLAB.parent = JOLT
# the reservoir: a thin glowing gas layer in the bottom stratum (cut face only)
bpy.ops.mesh.primitive_plane_add(size=1, location=(GPX, -0.01, -27.2), rotation=(math.pi / 2, 0, 0))
RES = bpy.context.active_object; RES.name = "Gas_Reservoir"; RES.scale = (16, 3.0, 1)
mres = bpy.data.materials.new("M_ResGas"); mres.use_nodes = True; nt = mres.node_tree; L = nt.links
pr = nt.nodes["Principled BSDF"]; pr.inputs["Base Color"].default_value = (0.2, 0.6, 1.0, 1)
pr.inputs["Emission Color"].default_value = (0.25, 0.75, 1.0, 1); pr.inputs["Emission Strength"].default_value = 1.2
vn = node(nt, "ShaderNodeTexVoronoi"); vn.inputs["Scale"].default_value = 3.0
tcr = node(nt, "ShaderNodeTexCoord"); L.new(tcr.outputs["Object"], vn.inputs["Vector"])
rr = node(nt, "ShaderNodeMapRange"); rr.inputs["From Min"].default_value = 0.05; rr.inputs["From Max"].default_value = 0.35
rr.inputs["To Min"].default_value = 1.0; rr.inputs["To Max"].default_value = 0.0; L.new(vn.outputs["Distance"], rr.inputs["Value"])
ge = node(nt, "ShaderNodeTexGradient"); ge.gradient_type = 'SPHERICAL'; L.new(tcr.outputs["Object"], ge.inputs["Vector"])
am = node(nt, "ShaderNodeMath", operation='MULTIPLY'); L.new(rr.outputs["Result"], am.inputs[0]); L.new(ge.outputs["Fac"], am.inputs[1])
am2 = node(nt, "ShaderNodeMath", operation='MULTIPLY'); L.new(am.outputs[0], am2.inputs[0]); am2.inputs[1].default_value = 1.4
L.new(am2.outputs[0], pr.inputs["Alpha"]); RES.data.materials.append(mres); to_col(RES, C_SET); RES.parent = JOLT
# far desert beyond the slab (gentle dunes)
bpy.ops.mesh.primitive_grid_add(x_subdivisions=120, y_subdivisions=120, size=1, location=(0, 260, -0.02))
FAR = bpy.context.active_object; FAR.name = "Desert_Far"; FAR.scale = (900, 460, 1); bpy.ops.object.transform_apply(scale=True)
for v in FAR.data.vertices:
    if v.co.y + 260 > 75:
        v.co.z += 3.5 * (0.5 + 0.5 * math.sin(v.co.x * 0.021 + v.co.y * 0.013)) * min(1.0, (v.co.y + 260 - 75) / 120)
FAR.data.materials.append(sand_mat("M_SandFar", (1.15, 0.55, 0.26), 0.05)); to_col(FAR, C_SET)
for p_ in FAR.data.polygons: p_.use_smooth = True
# left/right/back side walls of the slab are never framed (the slab is 80 m wide)

# ================================================================== gas well: half casing (cut), wellhead, gas inside
def half_tube(name, x, z0, z1, r_out, r_in, material, seg_z=120):
    """a casing cut by the plane y=0 (keeps y>=0): two half shells joined by the cut rims; real thickness"""
    bm = bmesh.new(); nseg = 24; rows = []
    for k in range(seg_z + 1):
        z = z0 + (z1 - z0) * k / seg_z; ring = []
        for rr_ in (r_out, r_in):
            ring.append([bm.verts.new((x + rr_ * math.cos(math.pi * i / nseg), rr_ * math.sin(math.pi * i / nseg), z)) for i in range(nseg + 1)])
        rows.append(ring)
    for k in range(seg_z):
        for s in (0, 1):
            for i in range(nseg):
                a_, b_ = rows[k][s][i], rows[k][s][i + 1]; c_, d_ = rows[k + 1][s][i + 1], rows[k + 1][s][i]
                bm.faces.new((a_, b_, c_, d_) if s == 0 else (a_, d_, c_, b_))
        for i in (0, nseg):   # cut rims (flat, at y=0)
            bm.faces.new((rows[k][0][i], rows[k][1][i], rows[k + 1][1][i], rows[k + 1][0][i]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); C_SET.objects.link(o); o.data.materials.append(material)
    for p_ in me.polygons: p_.use_smooth = True
    return o
CASING = half_tube("GasWell_Casing", GPX, -26.5, 0.0, 0.48, 0.40, M_STEEL)
CASING.parent = JOLT
# pinch shape key (stage B keys it): the casing squeezed shut round z=-16.9 (the blast level)
CASING.shape_key_add(name="Basis")
sk = CASING.shape_key_add(name="Pinch")
for v, kv in zip(CASING.data.vertices, sk.data):
    w = math.exp(-((v.co.z + 16.9) ** 2) / 2.2)
    dx = v.co.x - GPX
    kv.co = Vector((GPX + dx * (1 - 0.92 * w) + 0.10 * w, v.co.y * (1 - 0.55 * w), v.co.z))
# gas inside the casing: emissive flowing streaks; lower part (below the pinch) and upper part (to the surface)
def gas_strip(name, z0, z1):
    bm = bmesh.new(); n = 60; vs = []
    for k in range(n + 1):
        z = z0 + (z1 - z0) * k / n
        vs.append((bm.verts.new((GPX - 0.36, 0.06, z)), bm.verts.new((GPX + 0.36, 0.06, z))))
    for k in range(n): bm.faces.new((vs[k][0], vs[k][1], vs[k + 1][1], vs[k + 1][0]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); o = bpy.data.objects.new(name, me); C_FX.objects.link(o); o.parent = JOLT
    return o
GAS_FLOW = bpy.data.objects.new("GasFlow", None); C_FX.objects.link(GAS_FLOW)    # keyed z offset = flow speed
GAS_FRONT = bpy.data.objects.new("GasFront", None); C_FX.objects.link(GAS_FRONT)  # keyed z: gas exists below this height
def gas_mat(name, front=True):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; L = nt.links
    for n_ in list(nt.nodes):
        if n_.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n_)
    out = [n_ for n_ in nt.nodes if n_.type == 'OUTPUT_MATERIAL'][0]
    tc = node(nt, "ShaderNodeTexCoord"); tc.object = GAS_FLOW
    wv = node(nt, "ShaderNodeTexWave"); wv.wave_type = 'BANDS'; wv.bands_direction = 'Z'; wv.inputs["Scale"].default_value = 0.6
    wv.inputs["Distortion"].default_value = 6.0; wv.inputs["Detail"].default_value = 3; L.new(tc.outputs["Object"], wv.inputs["Vector"])
    cr = node(nt, "ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (0.05, 0.35, 1.0, 1); cr.color_ramp.elements[1].color = (0.85, 1.0, 1.0, 1)
    L.new(wv.outputs["Fac"], cr.inputs["Fac"])
    em = node(nt, "ShaderNodeEmission"); em.inputs["Strength"].default_value = 3.0; L.new(cr.outputs["Color"], em.inputs["Color"])
    tr = node(nt, "ShaderNodeBsdfTransparent")
    mx = node(nt, "ShaderNodeMixShader")
    st = node(nt, "ShaderNodeValue", name="GasOn", label="GasOn"); st.outputs[0].default_value = 1.0
    fac = st.outputs[0]
    if front:
        tf = node(nt, "ShaderNodeTexCoord"); tf.object = GAS_FRONT
        sp = node(nt, "ShaderNodeSeparateXYZ"); L.new(tf.outputs["Object"], sp.inputs[0])
        mr = node(nt, "ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.0; mr.inputs["From Max"].default_value = -1.2
        L.new(sp.outputs["Z"], mr.inputs["Value"])
        mm = node(nt, "ShaderNodeMath", operation='MULTIPLY'); L.new(mr.outputs["Result"], mm.inputs[0]); L.new(st.outputs[0], mm.inputs[1])
        fac = mm.outputs[0]
    L.new(fac, mx.inputs["Fac"]); L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], out.inputs["Surface"])
    return m
GAS_LO = gas_strip("Gas_Lower", -26.4, -16.9); GAS_LO.data.materials.append(gas_mat("M_GasLower"))
GAS_HI = gas_strip("Gas_Upper", -16.9, -0.05); GAS_HI.data.materials.append(gas_mat("M_GasUpper"))
for o in (GAS_LO, GAS_HI):
    o.shape_key_add(name="Basis"); k_ = o.shape_key_add(name="Pinch")
    for v, kv in zip(o.data.vertices, k_.data):
        w = math.exp(-((v.co.z + 16.9) ** 2) / 2.2); kv.co = Vector((GPX + (v.co.x - GPX) * (1 - 0.95 * w) + 0.1 * w, v.co.y, v.co.z))
# wellhead (surface, whole): flanged spool and a broken valve body, blackened by the fire
WH = cyl("Wellhead_Spool", 0.52, 0.7, (GPX, 0.0, 0.35), M_DARKSTEEL, verts=40, bevel=0.02); WH.parent = JOLT
WF = cyl("Wellhead_Flange", 0.75, 0.12, (GPX, 0.0, 0.72), M_DARKSTEEL, verts=40, bevel=0.02); WF.parent = JOLT
for i in range(12):
    an = 2 * math.pi * i / 12
    b_ = cyl("Wellhead_Bolt%02d" % i, 0.04, 0.2, (GPX + 0.66 * math.cos(an), 0.66 * math.sin(an), 0.78), M_STEEL, verts=8); b_.parent = JOLT
for o in [WH, WF] + [o for o in bpy.data.objects if o.name.startswith("Wellhead_Bolt")]: to_col(o, C_SET)

# ================================================================== nuke bore: steel collar, cable, device, concrete plug
COLLAR = cyl("NukeBore_Collar", 0.62, 0.4, (NBX, 0.0, 0.18), M_STEEL, verts=40, bevel=0.02)
bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=0.6, location=(NBX, 0.0, 0.18), vertices=40)
hole = bpy.context.active_object
bo = COLLAR.modifiers.new("hole", 'BOOLEAN'); bo.object = hole; bo.operation = 'DIFFERENCE'; bo.solver = 'EXACT'
bpy.context.view_layer.objects.active = COLLAR; bpy.ops.object.modifier_apply(modifier="hole"); bpy.data.objects.remove(hole, do_unlink=True)
# keep only the y>=0 half of the collar: it sits on the cut edge
bm = bmesh.new(); bm.from_mesh(COLLAR.data)
bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, 0), plane_no=(0, 1, 0), clear_outer=False, clear_inner=True)
bmesh.ops.contextual_create(bm, geom=[e for e in bm.edges if e.is_boundary])
bm.to_mesh(COLLAR.data); bm.free(); to_col(COLLAR, C_SET); COLLAR.parent = JOLT

def device():
    """a plain long dark-green cylinder with rounded ends, two steel bands and a lifting eye (no internals shown)"""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=40, v_segments=20, radius=0.32)
    for v in bm.verts:
        v.co.z = v.co.z * 0.9 + (1.28 if v.co.z > 0 else -1.28)
    me = bpy.data.meshes.new("Device"); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("Device", me); C_SET.objects.link(o); o.data.materials.append(M_DEV)
    for p_ in me.polygons: p_.use_smooth = True
    sd = o.modifiers.new("subd", 'SUBSURF'); sd.levels = 1; sd.render_levels = 2
    for z in (-0.9, 0.9):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.325, minor_radius=0.025, location=(0, 0, z))
        t = bpy.context.active_object; t.name = "Device_Band"; t.data.materials.append(M_STEEL); t.parent = o; to_col(t, C_SET)
        bpy.ops.object.shade_smooth()
    bpy.ops.mesh.primitive_torus_add(major_radius=0.09, minor_radius=0.025, location=(0, 0, 1.68), rotation=(math.pi / 2, 0, 0))
    t = bpy.context.active_object; t.name = "Device_Eye"; t.data.materials.append(M_STEEL); t.parent = o; to_col(t, C_SET)
    bpy.ops.object.shade_smooth()
    return o
DEV = device()          # origin at its centre; length 3.2 m (top of the eye at +1.77)
DEV.location = (NBX, 0.0, 2.6)
CABLE = cyl("Device_Cable", 0.022, 1.0, (0, 0, -0.5), M_CABLE, verts=10)
CABLE.data.transform(Matrix.Translation((0, 0, 0.5)))   # origin at the bottom end, +Z up, length 1 (scaled in stage B)
CABLE.location = (NBX, 0.0, 4.37)
to_col(CABLE, C_SET)
# concrete plug: a half cylinder (cut at y=0) that grows up from the device top; keyed scale z in stage B
bm = bmesh.new(); n = 24; ring0 = []; ring1 = []
for i in range(n + 1):
    an = math.pi * i / n; x_, y_ = 0.5 * math.cos(an), 0.5 * math.sin(an)
    ring0.append(bm.verts.new((x_, y_, 0))); ring1.append(bm.verts.new((x_, y_, 1)))
for i in range(n): bm.faces.new((ring0[i], ring0[i + 1], ring1[i + 1], ring1[i]))
bm.faces.new(ring0[::-1]); bm.faces.new(ring1)
bm.faces.new((ring0[0], ring1[0], ring1[n], ring0[n]))
me = bpy.data.meshes.new("Concrete_Plug"); bm.to_mesh(me); bm.free()
PLUG = bpy.data.objects.new("Concrete_Plug", me); C_SET.objects.link(PLUG); PLUG.data.materials.append(M_CONC)
PLUG.location = (NBX, 0.0, DEV_BOT + 3.55); PLUG.scale = (1, 1, 0.001); PLUG.parent = JOLT
# falling concrete inside the bore (a half stream), keyed in stage B
POUR = cyl("Concrete_Pour", 0.16, 1.0, (0, 0, 0), M_CONC, verts=16)
POUR.data.transform(Matrix.Translation((0, 0, -0.5)))       # origin at its TOP, hangs down
POUR.location = (NBX + 0.12, 0.0, 0.0); POUR.scale = (1, 1, 0.001); to_col(POUR, C_SET); POUR.parent = JOLT
dpo = POUR.modifiers.new("lumpy", 'DISPLACE'); dpo.texture = bpy.data.textures.new("pour_lumps", 'CLOUDS'); dpo.texture.noise_scale = 0.12; dpo.strength = 0.06

# ================================================================== A-frame headframe with the sheave, and the winch
def beam(name, p0, p1, w, material, c=C_SET):
    p0, p1 = Vector(p0), Vector(p1); d = p1 - p0
    bpy.ops.mesh.primitive_cube_add(size=1, location=(p0 + p1) / 2)
    o = bpy.context.active_object; o.name = name; o.scale = (w, w, d.length)
    o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d.normalized())
    bpy.ops.object.transform_apply(scale=True, rotation=True, location=False)
    b = o.modifiers.new("bev", 'BEVEL'); b.width = w * 0.12; b.segments = 2
    o.data.materials.append(material); to_col(o, c); o.parent = JOLT
    return o
APEX = Vector((NBX, -0.05, 10.6))
FL, FR = Vector((NBX - 2.6, 0.55, 0)), Vector((NBX + 2.6, 0.55, 0))
BL, BR = Vector((NBX - 1.3, 7.0, 0)), Vector((NBX + 1.3, 7.0, 0))
HF = []
for nm_, a_, b_ in (("HF_LegL", FL, APEX + Vector((-0.25, 0.05, 0))), ("HF_LegR", FR, APEX + Vector((0.25, 0.05, 0))),
                    ("HF_StayL", BL, APEX + Vector((-0.2, 0.35, -0.2))), ("HF_StayR", BR, APEX + Vector((0.2, 0.35, -0.2)))):
    HF.append(beam(nm_, a_, b_, 0.24, M_RED))
for t in (0.22, 0.48, 0.72):   # cross braces on the A
    pa = FL.lerp(APEX + Vector((-0.25, 0.05, 0)), t); pb = FR.lerp(APEX + Vector((0.25, 0.05, 0)), t)
    HF.append(beam("HF_Brace%d" % int(t * 100), pa, pb, 0.14, M_RED))
    qa = FL.lerp(APEX + Vector((-0.25, 0.05, 0)), t); qb = BL.lerp(APEX + Vector((-0.2, 0.35, -0.2)), t)
    HF.append(beam("HF_SideL%d" % int(t * 100), qa, qb, 0.10, M_RED))
    qa = FR.lerp(APEX + Vector((0.25, 0.05, 0)), t); qb = BR.lerp(APEX + Vector((0.2, 0.35, -0.2)), t)
    HF.append(beam("HF_SideR%d" % int(t * 100), qa, qb, 0.10, M_RED))
for p_ in (FL, FR, BL, BR):   # base plates on the sand
    pl = box("HF_Plate", (0.6, 0.6, 0.06), p_ + Vector((0, 0, 0.03)), M_DARKSTEEL, bevel=0.01); to_col(pl, C_SET); pl.parent = JOLT; HF.append(pl)
# sheave wheel at the apex: the cable runs over it from the winch (+Y) down to the device (x=NBX, y=0)
SHV_C = Vector((NBX, 0.38, 10.55)); SHV_R = 0.38
bpy.ops.mesh.primitive_torus_add(major_radius=SHV_R, minor_radius=0.06, location=SHV_C, rotation=(0, math.pi / 2, 0), major_segments=40)
SHV = bpy.context.active_object; SHV.name = "HF_Sheave"; SHV.data.materials.append(M_STEEL); to_col(SHV, C_SET); SHV.parent = JOLT
bpy.ops.object.shade_smooth()
for k in range(6):
    an = math.pi * k / 6
    beam("HF_Spoke%d" % k, SHV_C + Vector((0, SHV_R * math.cos(an), SHV_R * math.sin(an))), SHV_C - Vector((0, SHV_R * math.cos(an), SHV_R * math.sin(an))), 0.04, M_STEEL)
beam("HF_Axle", SHV_C + Vector((-0.4, 0, 0)), SHV_C + Vector((0.4, 0, 0)), 0.08, M_DARKSTEEL)
# winch skid behind (+Y): frame, drum, motor
WX = Vector((NBX, 9.0, 0))
box("Winch_Skid", (2.2, 1.6, 0.18), WX + Vector((0, 0, 0.09)), M_DARKSTEEL, bevel=0.02).parent = JOLT
DRUM = cyl("Winch_Drum", 0.38, 1.3, WX + Vector((0, 0, 0.75)), M_CABLE, rot=(0, math.pi / 2, 0), verts=32); DRUM.parent = JOLT
for sx in (-1, 1):
    cyl("Winch_Flange", 0.55, 0.06, WX + Vector((sx * 0.68, 0, 0.75)), M_YEL, rot=(0, math.pi / 2, 0), verts=32).parent = JOLT
    box("Winch_Side", (0.08, 1.2, 0.9), WX + Vector((sx * 0.78, 0, 0.6)), M_YEL, bevel=0.02).parent = JOLT
box("Winch_Motor", (0.9, 0.8, 0.75), WX + Vector((0, 0.75, 0.55)), M_YEL, bevel=0.05).parent = JOLT
for o in bpy.data.objects:
    if o.name.startswith(("Winch_",)): to_col(o, C_SET)
# cable sheave -> winch drum (static)
top = SHV_C + Vector((0, SHV_R * 0.7, SHV_R * 0.7)); dtop = WX + Vector((0, -0.1, 1.12))
beam("HF_CableBack", top, dtop, 0.04, M_CABLE)
CABLE.location = (NBX, 0.0, 4.37)
SHEAVE_DROP = Vector((NBX, SHV_C.y - SHV_R, SHV_C.z))    # where the hanging cable leaves the sheave

# crate with the DA KRAS FILMS logo (instrument crate beside the collar); logo on its front face (-Y)
CRATES = [(NBX + 1.3, 0.62), (GPX - 0.95, 2.9)]
M_SLAT = mat("M_CrateSlat", (0.36, 0.19, 0.07), rough=0.7)
for cx, cy in CRATES:
    box("Logo_Crate", (1.0, 0.6, 0.62), (cx, cy, 0.31), M_WOOD, bevel=0.02).parent = JOLT
    for dz in (-0.24, 0.24):
        box("Crate_Slat", (1.04, 0.64, 0.06), (cx, cy, 0.31 + dz), M_SLAT, bevel=0.01).parent = JOLT
LOGO_IMG = bpy.data.images.load(os.path.join(PKG, "..", "assets", "brand", "DaKrasFilms_logo_white.png"))
def logo_plane(name, loc, rot, width, img, bg=(0.04, 0.04, 0.05)):
    ar = img.size[1] / img.size[0]
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name; o.scale = (width, width * ar, 1)
    m = bpy.data.materials.new("M_" + name); m.use_nodes = True; nt = m.node_tree; L = nt.links; p = nt.nodes["Principled BSDF"]
    t = node(nt, "ShaderNodeTexImage"); t.image = img; t.extension = 'CLIP'
    mx = node(nt, "ShaderNodeMix", data_type='RGBA'); L.new(t.outputs["Alpha"], mx.inputs["Factor"])
    mx.inputs["A"].default_value = (*bg, 1); L.new(t.outputs["Color"], mx.inputs["B"])
    L.new(mx.outputs["Result"], p.inputs["Base Color"]); p.inputs["Roughness"].default_value = 0.6
    o.data.materials.append(m); to_col(o, C_SET); return o
for cx, cy in CRATES:
    logo_plane("Logo_CratePrint", (cx, cy - 0.322, 0.31), (math.pi / 2, 0, 0), 0.9, LOGO_IMG, bg=(0.05, 0.04, 0.03)).parent = JOLT
for o in bpy.data.objects:
    if o.name.startswith(("Crate_", "Logo_Crate", "HF_")): to_col(o, C_SET)

# ================================================================== the fire (no volumes): nested turbulent emission shells
FIRE_FLOW = bpy.data.objects.new("FireFlow", None); C_FX.objects.link(FIRE_FLOW)   # keyed upward drift = turbulence
def flame_shell_mesh(name, r0, r1, h, nseg=40, nz=48):
    bm = bmesh.new(); rows = []
    for k in range(nz + 1):
        t = k / nz; z = h * t
        r = r0 + (r1 - r0) * (t ** 0.8) + 0.25 * r0 * math.sin(t * math.pi)
        rows.append([bm.verts.new((r * math.cos(2 * math.pi * i / nseg), r * math.sin(2 * math.pi * i / nseg), z)) for i in range(nseg)])
    for k in range(nz):
        for i in range(nseg):
            j = (i + 1) % nseg; bm.faces.new((rows[k][i], rows[k][j], rows[k + 1][j], rows[k + 1][i]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p_ in me.polygons: p_.use_smooth = True
    return me
def flame_mat(name, h, smoke=False, strength=7.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; L = nt.links
    for n_ in list(nt.nodes):
        if n_.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n_)
    out = [n_ for n_ in nt.nodes if n_.type == 'OUTPUT_MATERIAL'][0]
    tc = node(nt, "ShaderNodeTexCoord"); tc.object = FIRE_FLOW
    tl = node(nt, "ShaderNodeTexCoord")
    sp = node(nt, "ShaderNodeSeparateXYZ"); L.new(tl.outputs["Generated"], sp.inputs[0])      # Z: 0 base .. 1 top
    mp = node(nt, "ShaderNodeMapping"); mp.inputs["Scale"].default_value = (0.55, 0.55, 0.22) if not smoke else (0.25, 0.25, 0.12)
    L.new(tc.outputs["Object"], mp.inputs["Vector"])
    n1 = node(nt, "ShaderNodeTexNoise"); n1.noise_dimensions = '4D'; n1.inputs["Scale"].default_value = 1.6; n1.inputs["Detail"].default_value = 6
    n1.inputs["Roughness"].default_value = 0.62; n1.inputs["Distortion"].default_value = 0.6; L.new(mp.outputs[0], n1.inputs["Vector"])
    wv = node(nt, "ShaderNodeValue", name="FireW", label="FireW"); L.new(wv.outputs[0], n1.inputs["W"])
    # density falls with height (flames thin and tear apart toward the top), soft silhouette from the facing ratio
    lw = node(nt, "ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.5
    fc = node(nt, "ShaderNodeMath", operation='SUBTRACT'); fc.inputs[0].default_value = 1.0; L.new(lw.outputs["Facing"], fc.inputs[1])
    fp = node(nt, "ShaderNodeMath", operation='POWER'); L.new(fc.outputs[0], fp.inputs[0]); fp.inputs[1].default_value = 1.6
    th = node(nt, "ShaderNodeMapRange"); th.inputs["From Min"].default_value = 0.0; th.inputs["From Max"].default_value = 1.0
    th.inputs["To Min"].default_value = 0.30 if not smoke else 0.40; th.inputs["To Max"].default_value = 0.62 if not smoke else 0.62
    L.new(sp.outputs["Z"], th.inputs["Value"])
    d1 = node(nt, "ShaderNodeMath", operation='SUBTRACT'); L.new(n1.outputs["Fac"], d1.inputs[0]); L.new(th.outputs["Result"], d1.inputs[1])
    d2 = node(nt, "ShaderNodeMath", operation='MULTIPLY'); L.new(d1.outputs[0], d2.inputs[0]); d2.inputs[1].default_value = 5.0
    d2.use_clamp = True
    base_fade = node(nt, "ShaderNodeMapRange"); base_fade.inputs["From Min"].default_value = 0.0; base_fade.inputs["From Max"].default_value = 0.05
    L.new(sp.outputs["Z"], base_fade.inputs["Value"])
    top_fade = node(nt, "ShaderNodeMapRange"); top_fade.inputs["From Min"].default_value = 1.0; top_fade.inputs["From Max"].default_value = 0.75
    L.new(sp.outputs["Z"], top_fade.inputs["Value"])
    a1 = node(nt, "ShaderNodeMath", operation='MULTIPLY'); L.new(d2.outputs[0], a1.inputs[0]); L.new(fp.outputs[0], a1.inputs[1])
    a2 = node(nt, "ShaderNodeMath", operation='MULTIPLY'); L.new(a1.outputs[0], a2.inputs[0]); L.new(top_fade.outputs["Result"], a2.inputs[1])
    a3 = node(nt, "ShaderNodeMath", operation='MULTIPLY'); L.new(a2.outputs[0], a3.inputs[0]); L.new(base_fade.outputs["Result"], a3.inputs[1])
    amt = node(nt, "ShaderNodeValue", name="FireAmt", label="FireAmt"); amt.outputs[0].default_value = 1.0
    a4 = node(nt, "ShaderNodeMath", operation='MULTIPLY'); L.new(a3.outputs[0], a4.inputs[0]); L.new(amt.outputs[0], a4.inputs[1])
    mx = node(nt, "ShaderNodeMixShader"); L.new(a4.outputs[0], mx.inputs["Fac"])
    tr = node(nt, "ShaderNodeBsdfTransparent"); L.new(tr.outputs[0], mx.inputs[1])
    if not smoke:
        hc = node(nt, "ShaderNodeMath", operation='MULTIPLY_ADD'); L.new(n1.outputs["Fac"], hc.inputs[0]); hc.inputs[1].default_value = -0.5
        L.new(sp.outputs["Z"], hc.inputs[2])
        cr = node(nt, "ShaderNodeValToRGB"); el = cr.color_ramp.elements
        el[0].position = 0.0; el[0].color = (1.0, 0.55, 0.10, 1)
        e2 = el.new(0.15); e2.color = (1.0, 0.32, 0.01, 1)
        e3 = el.new(0.40); e3.color = (0.85, 0.07, 0.005, 1)
        el[-1].position = 0.75; el[-1].color = (0.35, 0.04, 0.01, 1)
        L.new(hc.outputs[0], cr.inputs["Fac"])
        em = node(nt, "ShaderNodeEmission"); em.inputs["Strength"].default_value = strength; L.new(cr.outputs["Color"], em.inputs["Color"])
        L.new(em.outputs[0], mx.inputs[2])
    else:
        df = node(nt, "ShaderNodeBsdfDiffuse"); df.inputs["Color"].default_value = (0.05, 0.04, 0.04, 1)
        em = node(nt, "ShaderNodeEmission"); em.inputs["Color"].default_value = (1.0, 0.35, 0.08, 1)
        lo = node(nt, "ShaderNodeMapRange"); lo.inputs["From Min"].default_value = 0.0; lo.inputs["From Max"].default_value = 0.25
        lo.inputs["To Min"].default_value = 0.6; lo.inputs["To Max"].default_value = 0.0; L.new(sp.outputs["Z"], lo.inputs["Value"])
        L.new(lo.outputs["Result"], em.inputs["Strength"])
        ad = node(nt, "ShaderNodeAddShader"); L.new(df.outputs[0], ad.inputs[0]); L.new(em.outputs[0], ad.inputs[1])
        L.new(ad.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], out.inputs["Surface"])
    return m
def fire(name, loc, scale=1.0, n=5, height=24.0, smoke=True):
    root = bpy.data.objects.new(name, None); C_FX.objects.link(root); root.location = loc; root.scale = (scale,) * 3
    parts = []
    for i in range(n):
        t = i / max(1, n - 1)
        me = flame_shell_mesh(name + "_shell%d" % i, 0.32 + 0.38 * t, 2.4 + 2.2 * t, height * (1.0 - 0.18 * t))
        o = bpy.data.objects.new(name + "_shell%d" % i, me); C_FX.objects.link(o); o.parent = root
        o.rotation_euler.z = random.uniform(0, 6.28)
        d = o.modifiers.new("turb", 'DISPLACE'); tx = bpy.data.textures.new(name + "_turb%d" % i, 'CLOUDS'); tx.noise_scale = 1.4 + 0.3 * i
        d.texture = tx; d.texture_coords = 'OBJECT'; d.texture_coords_object = FIRE_FLOW; d.strength = 0.9 + 0.3 * t; d.direction = 'NORMAL'
        o.data.materials.append(flame_mat("M_" + name + "_%d" % i, height, strength=1.8 - 0.7 * t))
        o.visible_shadow = False; o.visible_diffuse = True
        parts.append(o)
    if smoke:
        me = flame_shell_mesh(name + "_smoke", 3.2, 9.0, 24.0)
        o = bpy.data.objects.new(name + "_smoke", me); C_FX.objects.link(o); o.parent = root; o.location.z = height * 0.62
        d = o.modifiers.new("turb", 'DISPLACE'); tx = bpy.data.textures.new(name + "_sturb", 'CLOUDS'); tx.noise_scale = 3.0
        d.texture = tx; d.texture_coords = 'OBJECT'; d.texture_coords_object = FIRE_FLOW; d.strength = 2.0
        o.data.materials.append(flame_mat("M_" + name + "_smoke", 24.0, smoke=True)); o.visible_shadow = False
        parts.append(o)
    return root, parts
FIRE, FIRE_PARTS = fire("Fire_Main", (GPX, 0.0, 0.78), 1.0)
FISSURES = []
for i, (x_, y_) in enumerate(((GPX - 3.4, 2.4), (GPX + 3.0, 1.6), (GPX + 1.0, 4.6))):
    r_, p_ = fire("Fire_Fissure%d" % i, (x_, y_, 0.0), 0.32, n=3, height=16.0, smoke=False)
    FISSURES.append((r_, p_))
    # the crack in the sand it bursts from: dark, hot-edged slit decals (scaled in stage B)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(x_, y_, 0.012), rotation=(0, 0, random.uniform(0, 3.1)))
    ck = bpy.context.active_object; ck.name = "Crack%d" % i; ck.scale = (2.6, 0.35, 1)
    mc = bpy.data.materials.new("M_Crack%d" % i); mc.use_nodes = True; nt = mc.node_tree; L = nt.links; pc = nt.nodes["Principled BSDF"]
    tcc = node(nt, "ShaderNodeTexCoord"); gr = node(nt, "ShaderNodeTexGradient"); gr.gradient_type = 'QUADRATIC_SPHERE'
    mpc = node(nt, "ShaderNodeMapping"); mpc.inputs["Location"].default_value = (0, 0, 0); mpc.inputs["Scale"].default_value = (1.0, 2.6, 1)
    L.new(tcc.outputs["Object"], mpc.inputs["Vector"]); L.new(mpc.outputs[0], gr.inputs["Vector"])
    nzc = node(nt, "ShaderNodeTexNoise"); nzc.inputs["Scale"].default_value = 9.0; L.new(tcc.outputs["Object"], nzc.inputs["Vector"])
    mm = node(nt, "ShaderNodeMath", operation='MULTIPLY'); L.new(gr.outputs["Fac"], mm.inputs[0]); L.new(nzc.outputs["Fac"], mm.inputs[1])
    rc = node(nt, "ShaderNodeMapRange"); rc.inputs["From Min"].default_value = 0.12; rc.inputs["From Max"].default_value = 0.22
    L.new(mm.outputs[0], rc.inputs["Value"]); L.new(rc.outputs["Result"], pc.inputs["Alpha"])
    pc.inputs["Base Color"].default_value = (0.03, 0.02, 0.02, 1); pc.inputs["Emission Color"].default_value = (1.0, 0.35, 0.05, 1)
    L.new(rc.outputs["Result"], pc.inputs["Emission Strength"])
    ck.data.materials.append(mc); to_col(ck, C_FX); ck.parent = JOLT
FIRE_LIGHT = bpy.data.objects.new("Fire_Light", bpy.data.lights.new("Fire_Light", 'POINT')); C_FX.objects.link(FIRE_LIGHT)
FIRE_LIGHT.data.color = (1.0, 0.45, 0.12); FIRE_LIGHT.data.energy = 60000; FIRE_LIGHT.data.shadow_soft_size = 2.0
FIRE_LIGHT.location = (GPX, -1.0, 6.0)

# ================================================================== the steel cap (lowered on a cable from above in stage B)
CAP = cyl("Cap_Body", 0.9, 1.1, (0, 0, 0.55), mat("M_CapSteel", (0.55, 0.58, 0.62), rough=0.3, metal=0.9), verts=48, bevel=0.03)
for z_, r_ in ((0.06, 1.05), (1.04, 0.95)):
    cyl("Cap_Ring", r_, 0.12, (0, 0, z_), M_DARKSTEEL, verts=48, bevel=0.02).parent = CAP
bpy.ops.mesh.primitive_torus_add(major_radius=0.18, minor_radius=0.05, location=(0, 0, 1.25), rotation=(math.pi / 2, 0, 0))
t = bpy.context.active_object; t.name = "Cap_Eye"; t.data.materials.append(M_STEEL); t.parent = CAP
CAP_CABLE = cyl("Cap_Cable", 0.03, 60.0, (0, 0, 31.3), M_CABLE, verts=10); CAP_CABLE.parent = CAP
for o in [CAP] + list(CAP.children): to_col(o, C_SET)
CAP.location = (GPX, 0.0, 40.0)

# ================================================================== water (truck monitors) and steam
def water_mat():
    m = bpy.data.materials.new("M_Water"); m.use_nodes = True; nt = m.node_tree; L = nt.links
    for n_ in list(nt.nodes):
        if n_.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n_)
    out = [n_ for n_ in nt.nodes if n_.type == 'OUTPUT_MATERIAL'][0]
    tc = node(nt, "ShaderNodeTexCoord"); tc.object = FIRE_FLOW
    nz = node(nt, "ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.0; nz.inputs["Detail"].default_value = 4
    mp = node(nt, "ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1.5, 1.5, 0.4); L.new(tc.outputs["Object"], mp.inputs["Vector"])
    L.new(mp.outputs[0], nz.inputs["Vector"])
    lw = node(nt, "ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.4
    fc = node(nt, "ShaderNodeMath", operation='SUBTRACT'); fc.inputs[0].default_value = 1.0; L.new(lw.outputs["Facing"], fc.inputs[1])
    rr = node(nt, "ShaderNodeMapRange"); rr.inputs["From Min"].default_value = 0.42; rr.inputs["From Max"].default_value = 0.62
    L.new(nz.outputs["Fac"], rr.inputs["Value"])
    a = node(nt, "ShaderNodeMath", operation='MULTIPLY'); L.new(rr.outputs["Result"], a.inputs[0]); L.new(fc.outputs[0], a.inputs[1])
    a2 = node(nt, "ShaderNodeMath", operation='MULTIPLY'); L.new(a.outputs[0], a2.inputs[0]); a2.inputs[1].default_value = 0.85
    pr = node(nt, "ShaderNodeBsdfPrincipled"); pr.inputs["Base Color"].default_value = (0.75, 0.9, 1.0, 1); pr.inputs["Roughness"].default_value = 0.15
    pr.inputs["Emission Color"].default_value = (0.6, 0.85, 1.0, 1); pr.inputs["Emission Strength"].default_value = 0.6
    tr = node(nt, "ShaderNodeBsdfTransparent"); mx = node(nt, "ShaderNodeMixShader")
    L.new(a2.outputs[0], mx.inputs["Fac"]); L.new(tr.outputs[0], mx.inputs[1]); L.new(pr.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs["Surface"])
    return m
M_WATER = water_mat()
def steam_mat():
    m = bpy.data.materials.new("M_Steam"); m.use_nodes = True; nt = m.node_tree; L = nt.links
    for n_ in list(nt.nodes):
        if n_.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n_)
    out = [n_ for n_ in nt.nodes if n_.type == 'OUTPUT_MATERIAL'][0]
    tc = node(nt, "ShaderNodeTexCoord"); tc.object = FIRE_FLOW
    nz = node(nt, "ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.9; nz.inputs["Detail"].default_value = 5; L.new(tc.outputs["Object"], nz.inputs["Vector"])
    lw = node(nt, "ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.5
    fc = node(nt, "ShaderNodeMath", operation='SUBTRACT'); fc.inputs[0].default_value = 1.0; L.new(lw.outputs["Facing"], fc.inputs[1])
    fp = node(nt, "ShaderNodeMath", operation='POWER'); L.new(fc.outputs[0], fp.inputs[0]); fp.inputs[1].default_value = 2.0
    rr = node(nt, "ShaderNodeMapRange"); rr.inputs["From Min"].default_value = 0.4; rr.inputs["From Max"].default_value = 0.7; L.new(nz.outputs["Fac"], rr.inputs["Value"])
    a = node(nt, "ShaderNodeMath", operation='MULTIPLY'); L.new(rr.outputs["Result"], a.inputs[0]); L.new(fp.outputs[0], a.inputs[1])
    amt = node(nt, "ShaderNodeValue", name="Amt", label="Amt"); amt.outputs[0].default_value = 1.0
    a2 = node(nt, "ShaderNodeMath", operation='MULTIPLY'); L.new(a.outputs[0], a2.inputs[0]); L.new(amt.outputs[0], a2.inputs[1])
    df = node(nt, "ShaderNodeBsdfDiffuse"); df.inputs["Color"].default_value = (0.95, 0.95, 0.97, 1)
    tr = node(nt, "ShaderNodeBsdfTransparent"); mx = node(nt, "ShaderNodeMixShader")
    L.new(a2.outputs[0], mx.inputs["Fac"]); L.new(tr.outputs[0], mx.inputs[1]); L.new(df.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs["Surface"])
    return m
M_STEAM = steam_mat()

# ================================================================== fire trucks (Soviet ZIL-131 AC-40, CC-BY): past only
def truck(name, loc, yaw):
    o = imp(os.path.join(MD, "firetruck.glb"), name); o.scale = (1, 1, 1)
    soften(o, rough_min=0.3); o.location = loc; o.rotation_euler.z = yaw; to_col(o, C_SET); o.parent = JOLT
    return o
T1 = truck("FireTruck_A", (GPX + 7.5, 5.2, 0.0), math.radians(200))
T2 = truck("FireTruck_B", (GPX - 7.8, 6.0, 0.0), math.radians(-20))
bpy.context.view_layer.update()
def nozzle(t):
    vs = [t.matrix_world @ v.co for v in t.data.vertices]
    top = [v for v in vs if v.z > max(w.z for w in vs) - 0.12]
    return sum(top, Vector()) / len(top)
NOZ = [nozzle(T1), nozzle(T2)]
print("NOZZLES", [tuple(round(c, 2) for c in n_) for n_ in NOZ])
# logo on truck A's door (a printed panel on the vehicle door, facing the camera side)
LOGO2_IMG = bpy.data.images.load(os.path.join(PKG, "..", "assets", "brand", "DaKrasFilms_logo_white.png"), check_existing=True)
WATER = []
for i, (t, n_) in enumerate(((T1, NOZ[0]), (T2, NOZ[1]))):
    tgt = Vector((GPX + (0.6 if i == 0 else -0.6), 0.3, 6.5))
    mid = (n_ + tgt) / 2 + Vector((0, 0, 4.0))
    cu = bpy.data.curves.new("WaterArc%d" % i, 'CURVE'); cu.dimensions = '3D'; sp = cu.splines.new('BEZIER'); sp.bezier_points.add(1)
    p0, p1 = sp.bezier_points
    p0.co = n_; p0.handle_left = n_ - (mid - n_) * 0.3; p0.handle_right = n_ + (mid - n_) * 0.75
    p1.co = tgt; p1.handle_left = tgt + (mid - tgt) * 0.75; p1.handle_right = tgt - (mid - tgt) * 0.3
    cu.bevel_depth = 0.16; cu.bevel_resolution = 4; cu.resolution_u = 32
    tp = bpy.data.curves.new("WaterTaper%d" % i, 'CURVE'); sp2 = tp.splines.new('POLY'); sp2.points.add(2)
    sp2.points[0].co = (0, 0.6, 0, 1); sp2.points[1].co = (0.5, 1.6, 0, 1); sp2.points[2].co = (1, 3.4, 0, 1)
    tpo = bpy.data.objects.new("WaterTaper%d" % i, tp); C_FX.objects.link(tpo); tpo.hide_render = True; tpo.hide_viewport = True
    cu.taper_object = tpo; cu.bevel_factor_end = 0.0
    o = bpy.data.objects.new("WaterArc%d" % i, cu); C_FX.objects.link(o); o.data.materials.append(M_WATER); o.parent = JOLT
    WATER.append(o)
STEAM = []
for i in range(4):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1.0, location=(GPX + random.uniform(-1.5, 1.5), random.uniform(-0.6, 1.2), random.uniform(5.0, 8.5)))
    s_ = bpy.context.active_object; s_.name = "Steam%d" % i; s_.data.materials.append(M_STEAM); bpy.ops.object.shade_smooth()
    d = s_.modifiers.new("lumps", 'DISPLACE'); tx = bpy.data.textures.new("steam%d" % i, 'CLOUDS'); tx.noise_scale = 0.6; d.texture = tx; d.strength = 0.5
    s_.scale = (0.001,) * 3; to_col(s_, C_FX); s_.visible_shadow = False; STEAM.append(s_)

# ================================================================== the blast: sphere, cavity, pressure ring, dust ring
def glow_sphere(name, col_core, col_rim, strength):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=1.0, location=(NBX, 0.0, -16.9))
    o = bpy.context.active_object; o.name = name; bpy.ops.object.shade_smooth()
    m = bpy.data.materials.new("M_" + name); m.use_nodes = True; nt = m.node_tree; L = nt.links
    for n_ in list(nt.nodes):
        if n_.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n_)
    out = [n_ for n_ in nt.nodes if n_.type == 'OUTPUT_MATERIAL'][0]
    lw = node(nt, "ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.35
    mx = node(nt, "ShaderNodeMix", data_type='RGBA'); L.new(lw.outputs["Facing"], mx.inputs["Factor"])
    mx.inputs["A"].default_value = (*col_core, 1); mx.inputs["B"].default_value = (*col_rim, 1)
    nz = node(nt, "ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 2.5; nz.inputs["Detail"].default_value = 6
    tcg = node(nt, "ShaderNodeTexCoord"); L.new(tcg.outputs["Object"], nz.inputs["Vector"])
    br = node(nt, "ShaderNodeMapRange"); br.inputs["To Min"].default_value = 0.6; br.inputs["To Max"].default_value = 1.3; L.new(nz.outputs["Fac"], br.inputs["Value"])
    st = node(nt, "ShaderNodeValue", name="Strength", label="Strength"); st.outputs[0].default_value = strength
    sm = node(nt, "ShaderNodeMath", operation='MULTIPLY'); L.new(br.outputs["Result"], sm.inputs[0]); L.new(st.outputs[0], sm.inputs[1])
    em = node(nt, "ShaderNodeEmission"); L.new(mx.outputs["Result"], em.inputs["Color"]); L.new(sm.outputs[0], em.inputs["Strength"])
    L.new(em.outputs[0], out.inputs["Surface"]); o.data.materials.append(m)
    o.visible_shadow = False; o.scale = (0.001,) * 3; to_col(o, C_FX)
    return o
BLAST = glow_sphere("Blast_Sphere", (1.0, 0.98, 0.9), (1.0, 0.55, 0.12), 30.0)
CAVITY = glow_sphere("Blast_Cavity", (0.9, 0.28, 0.04), (1.0, 0.65, 0.15), 6.0)
# keep only the y>=0 half of both spheres (they live inside the cut rock)
for o in (BLAST, CAVITY):
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, 0), plane_no=(0, 1, 0), clear_inner=True)
    bmesh.ops.contextual_create(bm, geom=[e for e in bm.edges if e.is_boundary])
    bm.to_mesh(o.data); bm.free()
    for p_ in o.data.polygons: p_.use_smooth = True
BLAST_LIGHT = bpy.data.objects.new("Blast_Light", bpy.data.lights.new("Blast_Light", 'POINT')); C_FX.objects.link(BLAST_LIGHT)
BLAST_LIGHT.data.color = (1.0, 0.85, 0.6); BLAST_LIGHT.data.energy = 0.0; BLAST_LIGHT.location = (NBX, -3.0, -16.9)
# pressure ring on the cut face (expands from the cavity: the squeeze wave)
bpy.ops.mesh.primitive_circle_add(vertices=96, radius=1.0, fill_type='NOTHING', location=(NBX, -0.03, -16.9), rotation=(math.pi / 2, 0, 0))
RING = bpy.context.active_object; RING.name = "Pressure_Ring"
RING.data.materials.append(mat("M_Ring", (1, 1, 1), emit=((1.0, 0.92, 0.75), 4.0)))
sol = RING.modifiers.new("w", 'SKIN') if False else None
bpy.ops.object.convert(target='CURVE'); RING = bpy.context.active_object; RING.data.bevel_depth = 0.012; RING.data.bevel_resolution = 2
RING.scale = (0.001,) * 3; to_col(RING, C_FX)
# dust ring at the surface over the blast (a torus of dust shooting outward)
bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.45, location=(NBX, 3.0, 0.35), major_segments=64, minor_segments=16)
DUST = bpy.context.active_object; DUST.name = "Dust_Ring"; bpy.ops.object.shade_smooth()
d = DUST.modifiers.new("lumps", 'DISPLACE'); tx = bpy.data.textures.new("dust", 'CLOUDS'); tx.noise_scale = 0.5; d.texture = tx; d.strength = 0.6
md = steam_mat(); md.name = "M_Dust"
for n_ in md.node_tree.nodes:
    if n_.type == 'BSDF_DIFFUSE': n_.inputs["Color"].default_value = (0.75, 0.45, 0.24, 1)
DUST.data.materials.append(md); DUST.scale = (0.001,) * 3; DUST.visible_shadow = False; to_col(DUST, C_FX)
SMOKE_WISP = fire("Smoke_Wisp", (GPX, 0.0, 0.8), 0.25, n=0, height=10, smoke=True)
for p_ in SMOKE_WISP[1]:
    p_.location.z = 0.0

# ================================================================== the crew: two men, real MakeHuman garments (one model each)
A, AB = human("CrewA", 1.0, 0.45, {"asian": 0.55, "caucasian": 0.40, "african": 0.05}, "short02/short02.mhclo",
              "middleage_asian_male/middleage_asian_male.mhmat", "eyebrow001/eyebrow001.mhclo", height=0.5, weight=0.55, muscle=0.6,
              clothes=["male_worksuit01/male_worksuit01.mhclo", "shoes02/shoes02.mhclo"])
B, BB = human("CrewB", 1.0, 0.6, {"asian": 0.25, "caucasian": 0.70, "african": 0.05}, "short04/short04.mhclo",
              "middleage_caucasian_male/middleage_caucasian_male.mhmat", "eyebrow006/eyebrow006.mhclo", height=0.55, weight=0.5, muscle=0.5,
              clothes=["male_casualsuit04/male_casualsuit04.mhclo", "shoes05/shoes05.mhclo"])
eye_group_fix()
for R_, BD in ((A, AB), (B, BB)):
    eye_fix(R_)
    for c in R_.children:
        if c.type == 'MESH' and any(k in c.name.lower() for k in ("worksuit", "casualsuit", "shoes")):
            so = c.modifiers.new("solid", 'SOLIDIFY'); so.thickness = 0.004; so.offset = 1.0; so.use_rim = True
            i = c.modifiers.find("solid")
            while i > c.modifiers.find("Armature") + 1:
                c.modifiers.move(i, i - 1); i -= 1
        if c.type == 'MESH' and "teeth" in c.name:
            for m in c.data.materials: tint(m, (1.4, 1.35, 1.3))
    for m in BD.data.materials: tint(m, (1.0, 0.82, 0.70))
    for c in R_.children: to_col(c, C_CH)
    to_col(R_, C_CH)
# wardrobe colours: worker in a deep blue work suit, engineer in a mustard shirt / olive trousers (via texture tint)
for c in A.children:
    if c.type == 'MESH' and "worksuit" in c.name:
        for m in c.data.materials: tint(m, (0.35, 0.55, 1.3))
for c in B.children:
    if c.type == 'MESH' and "casualsuit" in c.name:
        for m in c.data.materials: tint(m, (1.25, 0.85, 0.35))

# ================================================================== lights, look and render settings (fast, zero-error)
SUN = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN')); C_SET.objects.link(SUN)
SUN.data.energy = 4.0; SUN.data.color = (1.0, 0.93, 0.82); SUN.data.angle = math.radians(2.0)
SUN.rotation_euler = (math.radians(52), 0, math.radians(-32))
MOON = bpy.data.objects.new("Moon", bpy.data.lights.new("Moon", 'SUN')); C_SET.objects.link(MOON)
MOON.data.energy = 0.0; MOON.data.color = (0.45, 0.55, 1.0); MOON.rotation_euler = (math.radians(40), 0, math.radians(30))
FILL = bpy.data.objects.new("CutFill", bpy.data.lights.new("CutFill", 'AREA')); C_SET.objects.link(FILL)
FILL.data.energy = 700; FILL.data.size = 30; FILL.data.color = (0.95, 0.97, 1.0); FILL.location = (2, -22, -12); FILL.rotation_euler = (math.radians(90), 0, 0)

sc.render.engine = 'CYCLES'; cy = sc.cycles
cy.samples = 64; cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.05
cy.use_denoising = True; cy.denoiser = 'OPENIMAGEDENOISE'
cy.max_bounces = 6; cy.diffuse_bounces = 3; cy.glossy_bounces = 3; cy.transmission_bounces = 6; cy.transparent_max_bounces = 24
cy.caustics_reflective = False; cy.caustics_refractive = False
sc.render.use_persistent_data = True
sc.render.use_simplify = True; sc.render.simplify_subdivision_render = 2; cy.texture_limit_render = '2048'
sc.render.use_motion_blur = False
sc.view_settings.view_transform = 'Filmic'; sc.view_settings.look = 'High Contrast'; sc.view_settings.exposure = -0.3
sc.world = sc.world or bpy.data.worlds.new("World")
w = sc.world; w.use_nodes = True; nt = w.node_tree
for n_ in list(nt.nodes):
    if n_.type != 'OUTPUT_WORLD': nt.nodes.remove(n_)
tc = nt.nodes.new("ShaderNodeTexCoord"); sp = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Generated"], sp.inputs[0])
mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.5; mr.inputs["From Max"].default_value = 0.8; nt.links.new(sp.outputs["Z"], mr.inputs["Value"])
cr = nt.nodes.new("ShaderNodeValToRGB"); cr.name = "SkyRamp"
cr.color_ramp.elements[0].color = (0.55, 0.85, 1.0, 1); cr.color_ramp.elements[1].color = (0.02, 0.30, 0.95, 1)
nt.links.new(mr.outputs["Result"], cr.inputs["Fac"])
bg = nt.nodes.new("ShaderNodeBackground"); bg.name = "SkyBG"; bg.inputs["Strength"].default_value = 1.0; nt.links.new(cr.outputs["Color"], bg.inputs["Color"])
nt.links.new(bg.outputs[0], [n_ for n_ in nt.nodes if n_.type == 'OUTPUT_WORLD'][0].inputs["Surface"])
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("BUILD_DONE", OUT)
