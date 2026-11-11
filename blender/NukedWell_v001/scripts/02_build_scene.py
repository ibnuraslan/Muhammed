"""NukedWell set: desert drill site with a y=0 cutaway strata face, gas well, device shaft, derrick, crane, trucks, props, sky.
blender -b crew.blend --python 02_build_scene.py -- <assets_dir> <out.blend>
assets_dir: Poly Haven downloads (fetch_polyhaven.py) + glb/ (find_models.py)."""
import sys, os, math, random, glob
import bpy, bmesh
from mathutils import Vector, Matrix, noise

A, OUT = sys.argv[sys.argv.index("--") + 1:][:2]
sc = bpy.context.scene
FPS, END = 60, 2160
R_ = math.radians
random.seed(18)

# ------------------------------------------------------------------ timeline / render (farm baseline)
sc.render.fps, sc.render.fps_base = FPS, 1.0
sc.frame_start, sc.frame_end = 1, END
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, 100
sc.render.engine = 'CYCLES'
c = sc.cycles
c.device = 'CPU'; c.samples = 48; c.use_adaptive_sampling = True; c.adaptive_threshold = 0.05
c.use_denoising = True; c.denoiser = 'OPENIMAGEDENOISE'
c.max_bounces = 8; c.diffuse_bounces = 3; c.glossy_bounces = 3; c.transmission_bounces = 8; c.transparent_max_bounces = 16
c.volume_step_rate = 2.0; c.volume_max_steps = 256
c.caustics_reflective = c.caustics_refractive = False
sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = 0.5
sc.render.use_persistent_data = True
vs = sc.view_settings; vs.view_transform = 'AgX'; vs.look = 'AgX - Medium High Contrast'; vs.exposure = 0.0
im = sc.render.image_settings; im.file_format = 'PNG'; im.color_mode = 'RGB'; im.color_depth = '8'; im.compression = 15
sc.render.filepath = "//render/NukedWell_v001_"

def coll(name):
    c_ = bpy.data.collections.new(name); sc.collection.children.link(c_); return c_
C_SET, C_PROP, C_FX = coll("Set"), coll("Props"), coll("FX")
def link(o, c_=None):
    for u in list(o.users_collection): u.objects.unlink(o)
    (c_ or C_SET).objects.link(o); return o

# ------------------------------------------------------------------ materials
def img(path, nc=False):
    i = bpy.data.images.load(path, check_existing=True)
    if nc: i.colorspace_settings.name = 'Non-Color'
    return i
def tex_files(aid):
    fs = glob.glob(os.path.join(A, aid, "textures", "*")) + glob.glob(os.path.join(A, aid, "*.jpg"))
    pick = lambda k: next((f for f in fs if k in os.path.basename(f)), None)
    return pick("_diff_"), pick("_rough_"), pick("_nor_gl_")
def pbr(name, aid, scale, tint=None, val=1.0, bump=1.0, rough=None, coord='Object', metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links; p = n["Principled BSDF"]
    p.inputs['Metallic'].default_value = metal
    d_, r_, nm_ = tex_files(aid)
    tc = n.new('ShaderNodeTexCoord'); mp = n.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1 / scale,) * 3
    l.new(tc.outputs[coord], mp.inputs['Vector'])
    d = n.new('ShaderNodeTexImage'); d.image = img(d_); l.new(mp.outputs['Vector'], d.inputs['Vector'])
    col = d.outputs['Color']
    if tint or val != 1.0:
        mx = n.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
        t = tint or (1, 1, 1); mx.inputs['B'].default_value = (t[0] * val, t[1] * val, t[2] * val, 1)
        l.new(col, mx.inputs['A']); col = mx.outputs['Result']
    l.new(col, p.inputs['Base Color'])
    if rough is None and r_:
        r = n.new('ShaderNodeTexImage'); r.image = img(r_, True); l.new(mp.outputs['Vector'], r.inputs['Vector']); l.new(r.outputs['Color'], p.inputs['Roughness'])
    else:
        p.inputs['Roughness'].default_value = rough if rough is not None else 0.8
    if nm_:
        t = n.new('ShaderNodeTexImage'); t.image = img(nm_, True); l.new(mp.outputs['Vector'], t.inputs['Vector'])
        nmap = n.new('ShaderNodeNormalMap'); nmap.inputs['Strength'].default_value = bump
        l.new(t.outputs['Color'], nmap.inputs['Color']); l.new(nmap.outputs['Normal'], p.inputs['Normal'])
    return m
def flat(name, rgb, rough=0.6, metal=0.0, emit=None, es=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; p = m.node_tree.nodes["Principled BSDF"]
    p.inputs['Base Color'].default_value = (*rgb, 1); p.inputs['Roughness'].default_value = rough; p.inputs['Metallic'].default_value = metal
    if emit:
        p.inputs['Emission Color'].default_value = (*emit, 1); p.inputs['Emission Strength'].default_value = es
    return m

def backface_hide(m):
    """underside of the ground is invisible: the camera dives through the 'skin' into the cross-section"""
    n, l = m.node_tree.nodes, m.node_tree.links
    out = n["Material Output"]; src = out.inputs['Surface'].links[0].from_socket
    g = n.new('ShaderNodeNewGeometry'); tr = n.new('ShaderNodeBsdfTransparent'); mx = n.new('ShaderNodeMixShader')
    l.new(g.outputs['Backfacing'], mx.inputs['Fac']); l.new(src, mx.inputs[1]); l.new(tr.outputs['BSDF'], mx.inputs[2])
    l.new(mx.outputs['Shader'], out.inputs['Surface'])

# ------------------------------------------------------------------ ground: flat at the site, dunes far out
def build_ground():
    bm = bmesh.new()
    N = 120; S = 3000.0
    # non-uniform grid: dense near the site
    def g(i): t = i / N * 2 - 1; return math.copysign(abs(t) ** 2.2, t) * S / 2
    verts = {}
    for i in range(N + 1):
        for j in range(N + 1):
            x, y = g(i), g(j) + 400
            r = math.hypot(x, y - 40)
            amp = 0.0 if r < 140 else min(1.0, (r - 140) / 500) ** 1.5
            z = amp * (18 * noise.noise(Vector((x / 260, y / 260, 0.3))) + 6 * noise.noise(Vector((x / 70, y / 70, 1.7))))
            if y < -60: z = min(z, 0.0) + 0.0 * z
            verts[i, j] = bm.verts.new((x, y, z))
    for i in range(N):
        for j in range(N):
            bm.faces.new((verts[i, j], verts[i + 1, j], verts[i + 1, j + 1], verts[i, j + 1]))
    me = bpy.data.meshes.new("Ground"); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new("Ground", me); link(o)
    m = pbr("M_Ground", "aerial_sand", 14.0, tint=(0.78, 0.62, 0.46), bump=0.6)
    # blend in cracked dry ground near the site
    n, l = m.node_tree.nodes, m.node_tree.links; p = n["Principled BSDF"]
    base = p.inputs['Base Color'].links[0].from_socket
    d2, _, _ = tex_files("cracked_red_ground")
    tc = n.new('ShaderNodeTexCoord'); mp = n.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1 / 5.0,) * 3
    t2 = n.new('ShaderNodeTexImage'); t2.image = img(d2); l.new(tc.outputs['Object'], mp.inputs['Vector']); l.new(mp.outputs['Vector'], t2.inputs['Vector'])
    nz = n.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 0.02; l.new(tc.outputs['Object'], nz.inputs['Vector'])
    mr = n.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.45; mr.inputs['From Max'].default_value = 0.6
    l.new(nz.outputs['Fac'], mr.inputs['Value'])
    mx = n.new('ShaderNodeMix'); mx.data_type = 'RGBA'; l.new(mr.outputs['Result'], mx.inputs['Factor'])
    l.new(base, mx.inputs['A']); tint2 = n.new('ShaderNodeMix'); tint2.data_type = 'RGBA'; tint2.blend_type = 'MULTIPLY'
    tint2.inputs['Factor'].default_value = 1; tint2.inputs['B'].default_value = (0.8, 0.66, 0.54, 1)
    l.new(t2.outputs['Color'], tint2.inputs['A']); l.new(tint2.outputs['Result'], mx.inputs['B'])
    l.new(mx.outputs['Result'], p.inputs['Base Color'])
    backface_hide(m)
    me.materials.append(m)
    return o
GROUND = build_ground()

# ------------------------------------------------------------------ strata face at y = 0 (normal -Y), UV v = depth
FX0, FX1, FZ0 = -200.0, 200.0, -160.0
SHAFT_X, CASING_X, BLAST_Z, RES_Z = -14.0, 0.0, -60.0, -92.0
PIPE_Y, SHAFT_Y = -1.6, -2.7   # pipes sit just in front of the face: the cut shows their back halves
def build_face():
    nx, nz = 200, 110
    bm = bmesh.new(); uv = bm.loops.layers.uv.new("UVMap"); V = {}
    def xs(i):  # denser around the wells
        t = i / nx * 2 - 1; return math.copysign(abs(t) ** 1.6, t) * (FX1 - FX0) / 2 - 7
    def zs(j): t = j / nz; return FZ0 * (t ** 1.25)
    for i in range(nx + 1):
        for j in range(nz + 1):
            V[i, j] = bm.verts.new((xs(i), 0.0, zs(j)))
    for i in range(nx):
        for j in range(nz):
            f = bm.faces.new((V[i, j], V[i, j + 1], V[i + 1, j + 1], V[i + 1, j]))
            for lp in f.loops:
                lp[uv].uv = ((lp.vert.co.x - FX0) / (FX1 - FX0), (lp.vert.co.z - FZ0) / -FZ0)
    bm.normal_update()
    me = bpy.data.meshes.new("StrataFace"); bm.to_mesh(me); bm.free()
    if me.polygons[0].normal.y > 0:
        for p_ in me.polygons: p_.flip()
    o = bpy.data.objects.new("StrataFace", me); link(o)
    # material: layered bands from UV.v (bends with shape keys), rock texture detail, shaft strip, blast glow
    m = bpy.data.materials.new("M_Strata"); m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links; p = n["Principled BSDF"]; p.inputs['Roughness'].default_value = 0.9
    tc = n.new('ShaderNodeTexCoord'); sep = n.new('ShaderNodeSeparateXYZ'); l.new(tc.outputs['UV'], sep.inputs['Vector'])
    dep = n.new('ShaderNodeMath'); dep.operation = 'MULTIPLY_ADD'; dep.inputs[1].default_value = -FZ0; dep.inputs[2].default_value = FZ0
    l.new(sep.outputs['Y'], dep.inputs[0])  # depth z (m, negative) at rest
    wob = n.new('ShaderNodeTexNoise'); wob.inputs['Scale'].default_value = 6.0; wob.inputs['Detail'].default_value = 3
    l.new(tc.outputs['UV'], wob.inputs['Vector'])
    wm = n.new('ShaderNodeMath'); wm.operation = 'MULTIPLY_ADD'; wm.inputs[1].default_value = 5.0; wm.inputs[2].default_value = -2.5
    l.new(wob.outputs['Fac'], wm.inputs[0])
    dz = n.new('ShaderNodeMath'); dz.operation = 'ADD'; l.new(dep.outputs[0], dz.inputs[0]); l.new(wm.outputs[0], dz.inputs[1])
    nd = n.new('ShaderNodeMath'); nd.operation = 'MULTIPLY'; nd.inputs[1].default_value = 1 / FZ0; l.new(dz.outputs[0], nd.inputs[0])
    ramp = n.new('ShaderNodeValToRGB'); ramp.color_ramp.interpolation = 'CONSTANT'
    bands = [(0.0, (0.62, 0.48, 0.32)), (6, (0.50, 0.30, 0.18)), (11, (0.66, 0.52, 0.36)), (18, (0.36, 0.35, 0.36)),
             (30, (0.58, 0.56, 0.50)), (38, (0.44, 0.28, 0.20)), (47, (0.60, 0.50, 0.36)), (76, (0.17, 0.16, 0.16)),
             (86, (0.46, 0.40, 0.30)), (104, (0.24, 0.22, 0.24)), (125, (0.30, 0.27, 0.26))]
    el = ramp.color_ramp.elements
    el[0].position = 0.0; el[0].color = (*bands[0][1], 1); el[1].position = bands[1][0] / -FZ0; el[1].color = (*bands[1][1], 1)
    for d_, col in bands[2:]:
        e = el.new(d_ / -FZ0); e.color = (*col, 1)
    l.new(nd.outputs[0], ramp.inputs['Fac'])
    dr, rr, nr = tex_files("rock_face")
    mp = n.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (40, 16, 1); l.new(tc.outputs['UV'], mp.inputs['Vector'])
    td = n.new('ShaderNodeTexImage'); td.image = img(dr); l.new(mp.outputs['Vector'], td.inputs['Vector'])
    bw = n.new('ShaderNodeRGBToBW'); l.new(td.outputs['Color'], bw.inputs['Color'])
    det = n.new('ShaderNodeMath'); det.operation = 'MULTIPLY_ADD'; det.inputs[1].default_value = 1.3; det.inputs[2].default_value = 0.45
    l.new(bw.outputs['Val'], det.inputs[0])
    mul = n.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs['Factor'].default_value = 1
    l.new(ramp.outputs['Color'], mul.inputs['A']); l.new(det.outputs[0], mul.inputs['B'])
    tn = n.new('ShaderNodeTexImage'); tn.image = img(nr, True); l.new(mp.outputs['Vector'], tn.inputs['Vector'])
    nmap = n.new('ShaderNodeNormalMap'); nmap.inputs['Strength'].default_value = 1.2; l.new(tn.outputs['Color'], nmap.inputs['Color'])
    l.new(nmap.outputs['Normal'], p.inputs['Normal'])
    # shaft strip (concrete-lined bore, dark interior) at SHAFT_X, top 0 to -66
    ux = n.new('ShaderNodeMath'); ux.operation = 'MULTIPLY_ADD'; ux.inputs[1].default_value = FX1 - FX0; ux.inputs[2].default_value = FX0
    l.new(sep.outputs['X'], ux.inputs[0])
    ax = n.new('ShaderNodeMath'); ax.operation = 'SUBTRACT'; ax.inputs[1].default_value = SHAFT_X; l.new(ux.outputs[0], ax.inputs[0])
    aab = n.new('ShaderNodeMath'); aab.operation = 'ABSOLUTE'; l.new(ax.outputs[0], aab.inputs[0])
    inner = n.new('ShaderNodeMath'); inner.operation = 'LESS_THAN'; inner.inputs[1].default_value = 2.3; l.new(aab.outputs[0], inner.inputs[0])
    lining = n.new('ShaderNodeMath'); lining.operation = 'LESS_THAN'; lining.inputs[1].default_value = 2.9; l.new(aab.outputs[0], lining.inputs[0])
    top = n.new('ShaderNodeMath'); top.operation = 'GREATER_THAN'; top.inputs[1].default_value = 999.0; l.new(dep.outputs[0], top.inputs[0])
    li = n.new('ShaderNodeMath'); li.operation = 'MULTIPLY'; l.new(lining.outputs[0], li.inputs[0]); l.new(top.outputs[0], li.inputs[1])
    ii = n.new('ShaderNodeMath'); ii.operation = 'MULTIPLY'; l.new(inner.outputs[0], ii.inputs[0]); l.new(top.outputs[0], ii.inputs[1])
    c1 = n.new('ShaderNodeMix'); c1.data_type = 'RGBA'; l.new(li.outputs[0], c1.inputs['Factor']); l.new(mul.outputs['Result'], c1.inputs['A'])
    c1.inputs['B'].default_value = (0.55, 0.54, 0.50, 1)
    c2 = n.new('ShaderNodeMix'); c2.data_type = 'RGBA'; l.new(ii.outputs[0], c2.inputs['Factor']); l.new(c1.outputs['Result'], c2.inputs['A'])
    c2.inputs['B'].default_value = (0.07, 0.07, 0.075, 1)
    l.new(c2.outputs['Result'], p.inputs['Base Color'])
    # blast glow: orange emission around the blast point, keyed by the GlowAmt value; also gas glow in the reservoir band
    gv = n.new('ShaderNodeValue'); gv.name = "GlowAmt"; gv.outputs[0].default_value = 0.0
    gr = n.new('ShaderNodeValue'); gr.name = "GlowRad"; gr.outputs[0].default_value = 10.0
    pos = n.new('ShaderNodeVectorMath'); pos.operation = 'DISTANCE'; pos.inputs[1].default_value = (SHAFT_X, 0, BLAST_Z)
    l.new(tc.outputs['Object'], pos.inputs[0])
    dv = n.new('ShaderNodeMath'); dv.operation = 'DIVIDE'; l.new(pos.outputs['Value'], dv.inputs[0]); l.new(gr.outputs[0], dv.inputs[1])
    fall = n.new('ShaderNodeMapRange'); fall.inputs['From Min'].default_value = 0.0; fall.inputs['From Max'].default_value = 1.0
    fall.inputs['To Min'].default_value = 1.0; fall.inputs['To Max'].default_value = 0.0; fall.interpolation_type = 'SMOOTHSTEP'
    l.new(dv.outputs[0], fall.inputs['Value'])
    es = n.new('ShaderNodeMath'); es.operation = 'MULTIPLY'; l.new(fall.outputs['Result'], es.inputs[0]); l.new(gv.outputs[0], es.inputs[1])
    bb = n.new('ShaderNodeBlackbody'); bb.inputs['Temperature'].default_value = 2400
    l.new(bb.outputs['Color'], p.inputs['Emission Color']); l.new(es.outputs[0], p.inputs['Emission Strength'])
    me.materials.append(m)
    return o
FACE = build_face()

def cyl(name, r, z0, z1, x=0.0, y=0.0, verts=32, mat=None, c_=None, half=False, ry=None):
    bm = bmesh.new()
    if half:
        rr = [r, r * 0.86]
        ring = lambda rad, z: [bm.verts.new((x + rad * math.cos(math.pi * k / verts), y + rad * math.sin(math.pi * k / verts), z)) for k in range(verts + 1)]
        oT, oB, iT, iB = ring(rr[0], z1), ring(rr[0], z0), ring(rr[1], z1), ring(rr[1], z0)
        for k in range(verts):
            bm.faces.new((oB[k], oB[k + 1], oT[k + 1], oT[k])); bm.faces.new((iB[k + 1], iB[k], iT[k], iT[k + 1]))
            bm.faces.new((oT[k], oT[k + 1], iT[k + 1], iT[k]))
    else:
        bmesh.ops.create_cone(bm, cap_ends=True, segments=verts, radius1=r, radius2=r, depth=z1 - z0,
                              matrix=Matrix.Translation((x, y, (z0 + z1) / 2)))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p_ in me.polygons: p_.use_smooth = True
    o = bpy.data.objects.new(name, me); link(o, c_)
    if mat: me.materials.append(mat)
    return o
def box(name, size, loc, mat=None, c_=None, rot=(0, 0, 0)):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts: v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); o.location = loc; o.rotation_euler = rot; link(o, c_)
    if mat: me.materials.append(mat)
    return o

M_STEEL = pbr("M_Steel", "rusty_metal_02", 2.0, tint=(0.55, 0.55, 0.58), metal=0.8, bump=0.5)
M_CONC = pbr("M_Concrete", "brushed_concrete", 3.0, tint=(0.85, 0.84, 0.8))
M_DEVICE = pbr("M_Device", "green_metal_rust", 1.5, tint=(0.35, 0.5, 0.3), val=0.7, metal=0.5, bump=0.4)
M_DARK = flat("M_DarkSteel", (0.05, 0.05, 0.05), 0.4, 0.9)
M_RED = flat("M_RedPaint", (0.45, 0.06, 0.04), 0.45, 0.2)

# ------------------------------------------------------------------ gas well: half casing (back half, cut open), gas flow, wellhead, reservoir
CASING = cyl("Casing", 1.5, RES_Z - 4, 0.0, x=CASING_X, y=PIPE_Y, verts=24, mat=M_STEEL, half=True)
# subdivide the casing along z for the pinch shape key
bm = bmesh.new(); bm.from_mesh(CASING.data)
edges = [e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) > 1]
bmesh.ops.subdivide_edges(bm, edges=edges, cuts=60, use_grid_fill=True)
bm.to_mesh(CASING.data); bm.free()
GAS = cyl("GasFlow", 1.2, RES_Z - 4, 0.0, x=CASING_X, y=PIPE_Y, verts=24, c_=C_FX)
bm = bmesh.new(); bm.from_mesh(GAS.data)
edges = [e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) > 1]
bmesh.ops.subdivide_edges(bm, edges=edges, cuts=60, use_grid_fill=True); bm.to_mesh(GAS.data); bm.free()
mg = bpy.data.materials.new("M_GasFlow"); mg.use_nodes = True
n, l = mg.node_tree.nodes, mg.node_tree.links; out = n["Material Output"]; n.remove(n["Principled BSDF"])
tc = n.new('ShaderNodeTexCoord'); mpg = n.new('ShaderNodeMapping'); mpg.name = "GasMap"
mpg.inputs['Scale'].default_value = (1, 1, 0.12); l.new(tc.outputs['Object'], mpg.inputs['Vector'])
wv = n.new('ShaderNodeTexWave'); wv.wave_type = 'BANDS'; wv.bands_direction = 'Z'; wv.inputs['Scale'].default_value = 1.0
wv.inputs['Distortion'].default_value = 4.0; wv.inputs['Detail'].default_value = 3; l.new(mpg.outputs['Vector'], wv.inputs['Vector'])
mr = n.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.35; mr.inputs['From Max'].default_value = 0.95
l.new(wv.outputs['Fac'], mr.inputs['Value'])
ga = n.new('ShaderNodeValue'); ga.name = "GasAmt"; ga.outputs[0].default_value = 0.0
# z mask: gas only below GasTop (pinch cuts it off)
gt = n.new('ShaderNodeValue'); gt.name = "GasTop"; gt.outputs[0].default_value = 5.0
sz = n.new('ShaderNodeSeparateXYZ'); l.new(tc.outputs['Object'], sz.inputs['Vector'])
lt = n.new('ShaderNodeMath'); lt.operation = 'LESS_THAN'; l.new(sz.outputs['Z'], lt.inputs[0]); l.new(gt.outputs[0], lt.inputs[1])
m1 = n.new('ShaderNodeMath'); m1.operation = 'MULTIPLY'; l.new(mr.outputs['Result'], m1.inputs[0]); l.new(ga.outputs[0], m1.inputs[1])
m2 = n.new('ShaderNodeMath'); m2.operation = 'MULTIPLY'; l.new(m1.outputs[0], m2.inputs[0]); l.new(lt.outputs[0], m2.inputs[1])
em = n.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (0.55, 0.85, 1.0, 1); em.inputs['Strength'].default_value = 6.0
trn = n.new('ShaderNodeBsdfTransparent'); mix = n.new('ShaderNodeMixShader')
l.new(m2.outputs[0], mix.inputs['Fac']); l.new(trn.outputs['BSDF'], mix.inputs[1]); l.new(em.outputs['Emission'], mix.inputs[2])
l.new(mix.outputs['Shader'], out.inputs['Surface'])
GAS.data.materials.append(mg)
GAS.visible_shadow = False
# reservoir gas glow: pockets in the reservoir band
RESV = box("ReservoirGlow", (150, 0.2, 10), (0, -0.15, RES_Z + 2), c_=C_FX)
mrv = bpy.data.materials.new("M_ResGlow"); mrv.use_nodes = True
n, l = mrv.node_tree.nodes, mrv.node_tree.links; out = n["Material Output"]; n.remove(n["Principled BSDF"])
tc = n.new('ShaderNodeTexCoord'); vn = n.new('ShaderNodeTexVoronoi'); vn.inputs['Scale'].default_value = 0.6; l.new(tc.outputs['Object'], vn.inputs['Vector'])
mr = n.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.15; mr.inputs['From Max'].default_value = 0.0; l.new(vn.outputs['Distance'], mr.inputs['Value'])
gv2 = n.new('ShaderNodeValue'); gv2.name = "ResAmt"; gv2.outputs[0].default_value = 0.0
mm = n.new('ShaderNodeMath'); mm.operation = 'MULTIPLY'; l.new(mr.outputs['Result'], mm.inputs[0]); l.new(gv2.outputs[0], mm.inputs[1])
em = n.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (0.45, 0.8, 1.0, 1); em.inputs['Strength'].default_value = 3.0
trn = n.new('ShaderNodeBsdfTransparent'); mix = n.new('ShaderNodeMixShader')
l.new(mm.outputs[0], mix.inputs['Fac']); l.new(trn.outputs['BSDF'], mix.inputs[1]); l.new(em.outputs['Emission'], mix.inputs[2])
l.new(mix.outputs['Shader'], out.inputs['Surface']); RESV.data.materials.append(mrv); RESV.visible_shadow = False

# wellhead ("christmas tree") at the surface, full round, sits on the cut line
WH = bpy.data.objects.new("Wellhead", None); link(WH)
parts = [cyl("WH_base", 2.2, 0.0, 0.6, mat=M_CONC), cyl("WH_spool", 1.0, 0.6, 2.8, mat=M_STEEL), cyl("WH_flange1", 1.4, 1.2, 1.5, mat=M_STEEL),
         cyl("WH_flange2", 1.4, 2.3, 2.6, mat=M_STEEL), cyl("WH_top", 0.7, 2.8, 3.6, mat=M_STEEL)]
for side in (-1, 1):
    a = cyl("WH_wing%d" % side, 0.35, -1.2, 1.2, mat=M_STEEL); a.rotation_euler = (0, R_(90), 0); a.location = (side * 1.6, 0, 1.9); parts.append(a)
    w = cyl("WH_wheel%d" % side, 0.6, -0.08, 0.08, mat=M_RED); w.rotation_euler = (0, R_(90), 0); w.location = (side * 2.85, 0, 1.9); parts.append(w)
for p_ in parts: p_.parent = WH

# ------------------------------------------------------------------ device shaft: lining collar at the surface, concrete plug, device, cable
COLLAR = cyl("ShaftCollar", 3.4, -0.3, 0.5, x=SHAFT_X, y=SHAFT_Y, mat=M_CONC)
bm = bmesh.new(); bm.from_mesh(COLLAR.data)
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.z > 0.9], context='FACES'); bm.to_mesh(COLLAR.data); bm.free()
LINING = cyl("ShaftLining", 2.7, -67.0, 0.0, x=SHAFT_X, y=SHAFT_Y, verts=24, mat=pbr("M_LiningDark", "brushed_concrete", 2.0, tint=(0.32, 0.31, 0.3)), half=True)
HOLE = cyl("ShaftHole", 2.4, -0.25, 0.52, x=SHAFT_X, y=SHAFT_Y, mat=flat("M_Hole", (0.01, 0.01, 0.01), 0.9))
DEV_L, DEV_R = 9.0, 1.7
def build_device():
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=40, radius1=DEV_R, radius2=DEV_R, depth=DEV_L, matrix=Matrix.Translation((0, 0, -DEV_L / 2)))
    for v in bm.verts:   # rounded ends
        if v.co.z > -0.2: v.co.x *= 0.85; v.co.y *= 0.85
        if v.co.z < -DEV_L + 0.2: v.co.x *= 0.8; v.co.y *= 0.8
    me = bpy.data.meshes.new("Device"); bm.to_mesh(me); bm.free()
    mod_o = bpy.data.objects.new("Device", me); link(mod_o, C_PROP); me.materials.append(M_DEVICE)
    for p_ in me.polygons: p_.use_smooth = True
    bv = mod_o.modifiers.new("bevel", 'BEVEL'); bv.width = 0.25; bv.segments = 3; bv.limit_method = 'ANGLE'
    for z_ in (-1.5, -DEV_L + 1.5):
        b = cyl("Device_band", DEV_R + 0.04, z_ - 0.15, z_ + 0.15, mat=M_DARK, c_=C_PROP); b.parent = mod_o
    eye = cyl("Device_eye", 0.35, 0.0, 0.7, mat=M_DARK, c_=C_PROP); eye.parent = mod_o
    ring = bpy.data.objects.new("Device_ring", bpy.data.meshes.new("ring")); link(ring, C_PROP)
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=False, segments=16, radius1=0.12, radius2=0.12, depth=0.1)
    bm.free()
    return mod_o
DEVICE = build_device()
CABLE = cyl("Cable", 0.06, 0.0, 1.0, mat=M_DARK, verts=8, c_=C_PROP)   # unit length, scaled in z by animation
PLUG = box("ConcretePlug", (4.6, 2.6, 1.0), (SHAFT_X, SHAFT_Y + 1.3, 0), mat=M_CONC, c_=C_PROP)   # origin at bottom via mesh shift
for v in PLUG.data.vertices: v.co.z += 0.5
POUR = cyl("PourStream", 0.45, 0.0, 1.0, x=0, mat=pbr("M_WetConcrete", "brushed_concrete", 1.0, tint=(0.6, 0.6, 0.58), rough=0.25), c_=C_FX, verts=12)
CHUTE_STREAM = None

# ------------------------------------------------------------------ derrick (lattice tower) at (26, 22)
def lattice_tower(name, base, top, h, levels, loc, mat):
    bm = bmesh.new()
    def corner(k, t):
        s = base + (top - base) * t; sx = (1, -1, -1, 1)[k]; sy = (1, 1, -1, -1)[k]
        return Vector((sx * s / 2, sy * s / 2, h * t))
    def strut(a, b, r):
        d = b - a; L = d.length
        M = Matrix.Translation((a + b) / 2) @ d.to_track_quat('Z', 'Y').to_matrix().to_4x4()
        bmesh.ops.create_cone(bm, cap_ends=False, segments=6, radius1=r, radius2=r, depth=L, matrix=M)
    for k in range(4):
        strut(corner(k, 0), corner(k, 1), 0.18)
    for i in range(levels):
        t0, t1 = i / levels, (i + 1) / levels
        for k in range(4):
            k2 = (k + 1) % 4
            strut(corner(k, t1), corner(k2, t1), 0.08)
            strut(corner(k, t0), corner(k2, t1), 0.06)
            strut(corner(k2, t0), corner(k, t1), 0.06)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); o.location = loc; link(o); me.materials.append(mat); return o
M_DERRICK = pbr("M_Derrick", "rusty_metal_02", 1.5, tint=(0.75, 0.68, 0.6), metal=0.7)
DERRICK = lattice_tower("Derrick", 9.0, 2.2, 38.0, 12, (28, 24, 0), M_DERRICK)
box("Derrick_floor", (11, 11, 0.6), (28, 24, 3.2), mat=pbr("M_Planks", "rusty_metal_02", 2.0, tint=(0.5, 0.42, 0.35)))
box("Derrick_crown", (3.5, 3.5, 1.2), (28, 24, 38.4), mat=M_DERRICK)
for k in range(4):
    sx, sy = (1, -1, -1, 1)[k], (1, 1, -1, -1)[k]
    box("Derrick_foot%d" % k, (1.6, 1.6, 0.8), (28 + sx * 4.5, 24 + sy * 4.5, 0.4), mat=M_CONC)

# ------------------------------------------------------------------ crane: lattice mast + slewing boom; base (-7, 22); hook reaches shaft (-14,0) and well (0,0)
CRANE_BASE = Vector((-7.0, 22.0, 0.0))
CR = bpy.data.objects.new("Crane_Slew", None); CR.location = CRANE_BASE; link(CR)
M_CRANE = pbr("M_CraneYellow", "green_metal_rust", 1.5, tint=(1.0, 0.75, 0.25), val=1.0, metal=0.4)
mast = lattice_tower("Crane_Mast", 2.6, 2.0, 34.0, 11, (0, 0, 0), M_CRANE); mast.parent = CR
cab = box("Crane_Cab", (4.5, 3.2, 3.0), (0, 2.6, 2.0), mat=M_CRANE); cab.parent = CR
cw = box("Crane_Counterweight", (3.5, 4, 2.5), (0, 9.0, 33.5), mat=M_CONC); cw.parent = CR
BOOM_LEN = math.hypot(*(Vector((SHAFT_X, 0)) - CRANE_BASE.to_2d())) + 0.0
boom = lattice_tower("Crane_Jib", 1.8, 1.4, BOOM_LEN + 9, 14, (0, 0, 0), M_CRANE)
boom.rotation_euler = (R_(90), 0, 0); boom.location = (0, 9.0, 34.0); boom.parent = CR   # jib points -Y (local)
box("Crane_Footing", (7, 7, 1.0), CRANE_BASE + Vector((0, 0, 0.5)), mat=M_CONC)
TROLLEY = box("Crane_Trolley", (1.6, 1.6, 0.8), (0, -BOOM_LEN, 32.9), mat=M_DARK); TROLLEY.parent = CR
HOOK = bpy.data.objects.new("Hook", None); link(HOOK, C_PROP)
hk = cyl("Hook_block", 0.6, -0.6, 0.6, mat=M_RED, c_=C_PROP); hk.parent = HOOK
CRANE_TOP_Z = 32.5

# ------------------------------------------------------------------ steel cap for beat 7
CAP = bpy.data.objects.new("Cap", None); link(CAP, C_PROP)
for p_ in (cyl("Cap_body", 2.4, -2.0, 0.0, mat=M_STEEL, c_=C_PROP), cyl("Cap_flange", 3.0, -2.0, -1.6, mat=M_STEEL, c_=C_PROP),
           cyl("Cap_lug", 0.4, 0.0, 0.8, mat=M_DARK, c_=C_PROP)):
    p_.parent = CAP

# ------------------------------------------------------------------ vehicles (CC-BY GLBs), normalised: long axis X, wheels on z=0
def import_glb(name, path, length, loc, yaw, tint=None):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    root = bpy.data.objects.new(name, None); link(root, C_PROP)
    for o in new:
        link(o, C_PROP)
        if o.parent is None: o.parent = root
    bpy.context.view_layer.update()
    ms = [o for o in new if o.type == 'MESH']
    pts = [o.matrix_world @ Vector(cn) for o in ms for cn in o.bound_box]
    mn = Vector([min(p[i] for p in pts) for i in range(3)]); mx = Vector([max(p[i] for p in pts) for i in range(3)])
    d = mx - mn; s = length / max(d.x, d.y)
    for o in new:
        if o.parent == root:
            o.matrix_world = Matrix.Scale(s, 4) @ Matrix.Translation(-Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))) @ o.matrix_world
    if d.y > d.x:
        for o in new:
            if o.parent == root: o.matrix_world = Matrix.Rotation(R_(90), 4, 'Z') @ o.matrix_world
    root.location = loc; root.rotation_euler = (0, 0, R_(yaw))
    for o in ms:
        for m in o.data.materials:
            if m and tint and m.node_tree:
                pass
    return root
G = os.path.join(A, "glb")
FT1 = import_glb("FireTruck1", os.path.join(G, "firetruck.glb"), 7.4, (22, 40, 0), 120)
FT2 = import_glb("FireTruck2", os.path.join(G, "firetruck.glb"), 7.4, (-26, 44, 0), 60)
MIXER = import_glb("MixerTruck", os.path.join(G, "maz500.glb"), 7.6, (-23.5, 2.2, 0), 0)
TRUCK = import_glb("CargoTruck", os.path.join(G, "zil130.glb"), 7.0, (-40, 30, 0), 35)
# mixer drum (procedural) on the MAZ bed: rear of the truck faces the shaft (+X)
DRUM = bpy.data.objects.new("MixerDrum", None); link(DRUM, C_PROP)
DRUM.parent = MIXER; DRUM.location = (-1.6, 0, 2.6); DRUM.rotation_euler = (0, R_(-76), 0)
bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=32, radius1=0.9, radius2=1.25, depth=2.2, matrix=Matrix.Translation((0, 0, -1.1)))
bmesh.ops.create_cone(bm, cap_ends=True, segments=32, radius1=1.25, radius2=0.7, depth=2.0, matrix=Matrix.Translation((0, 0, 1.0)))
me = bpy.data.meshes.new("Drum"); bm.to_mesh(me); bm.free(); dr = bpy.data.objects.new("MixerDrumMesh", me); link(dr, C_PROP); dr.parent = DRUM
me.materials.append(pbr("M_Drum", "green_metal_rust", 1.0, tint=(0.95, 0.9, 0.8), metal=0.5)); [setattr(p_, "use_smooth", True) for p_ in me.polygons]
for k in range(6):   # spiral fins outside so rotation reads
    f_ = box("DrumRib%d" % k, (0.12, 0.3, 4.0), (math.cos(k * math.pi / 3) * 1.05, math.sin(k * math.pi / 3) * 1.05, 0), mat=M_DARK, c_=C_PROP); f_.parent = DRUM
    f_.rotation_euler = (0, 0, k * math.pi / 3)
CHUTE = box("MixerChute", (3.4, 0.7, 0.25), (3.6, 0, 1.6), mat=M_STEEL, c_=C_PROP); CHUTE.parent = MIXER; CHUTE.rotation_euler = (0, R_(22), 0)

# ------------------------------------------------------------------ Poly Haven props scattered around the site (only y > 2)
def ph_model(aid, name, loc, yaw=0.0, scale=1.0):
    fs = glob.glob(os.path.join(A, aid, "*.blend"))
    if not fs: return None
    with bpy.data.libraries.load(fs[0], link=False) as (src, dst):
        dst.objects = list(src.objects)
    root = bpy.data.objects.new(name, None); link(root, C_PROP); root.location = loc; root.rotation_euler = (0, 0, R_(yaw)); root.scale = (scale,) * 3
    for o in dst.objects:
        if o is None: continue
        link(o, C_PROP)
        if o.parent is None: o.parent = root
    return root
for aid, pts in (("old_military_crate", [(-20, 12, 0, 20), (-21.2, 13.4, 0, 70), (14, 9, 0, -15)]),
                 ("wooden_military_crate", [(-19, 14.5, 0, 5), (16, 11, 0, 40), (-34, 22, 0, 10)]),
                 ("barrel_03", [(10, 8, 0, 0), (10.9, 8.6, 0, 0), (10.3, 9.6, 0, 0), (-30, 16, 0, 0), (-31, 16.4, 0, 0)]),
                 ("metal_jerrycan_green", [(13.2, 8.4, 0, 30), (-18.2, 11.4, 0, -20)]),
                 ("portable_generator", [(-16, 18, 0, 80)]), ("portable_searchlight", [(-10, 9, 0, -140), (8, 12, 0, 150)]),
                 ("old_military_compressor", [(18, 14, 0, 100)]), ("cement_bag", [(-22.5, 10, 0, 10), (-23, 11, 0, 40), (-22.4, 11.2, 0.25, 70)]),
                 ("vintage_radio_transceiver", [(15.6, 11.1, 0.5, 200)]),
                 ("namaqualand_boulder_02", [(60, 70, 0, 10), (-75, 55, 0, 100), (110, 160, 0, 40), (-130, 140, 0, 200)]),
                 ("namaqualand_boulder_04", [(45, 110, 0, 50), (-55, 95, 0, 0), (90, 40, 0, 150), (-110, 60, 0, 80)]),
                 ("shrub_01", [(35, 60, 0, 0), (-48, 70, 0, 90), (70, 95, 0, 40), (-90, 100, 0, 10), (25, 85, 0, 70), (-28, 105, 0, 20),
                               (55, 30, 0, 0), (-60, 35, 0, 10), (40, -40, 0, 0), (-45, -50, 0, 0), (80, -30, 0, 0), (-85, -25, 0, 0)]),
                 ("dead_tree_trunk", [(-65, 80, 0, 30), (75, 120, 0, 120)])):
    for i, (x, y, z, yw) in enumerate(pts):
        ph_model(aid, "%s_%d" % (aid, i), (x, y, z), yw, 1.0 if "boulder" not in aid else 2.5)
# crate on top of the crate for stacking
# tents and a sandbag bunker far back (the crew watches the test from here)
M_CANVAS = pbr("M_Canvas", "aerial_sand", 1.0, tint=(0.55, 0.52, 0.35), val=0.9, rough=0.9)
for i, (x, y, yw) in enumerate(((-55, 40, 20), (-62, 52, 35), (48, 55, -25))):
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=4, radius1=4.0, radius2=0.2, depth=3.4, matrix=Matrix.Translation((0, 0, 1.7)) @ Matrix.Rotation(R_(45), 4, 'Z'))
    me = bpy.data.meshes.new("Tent%d" % i); bm.to_mesh(me); bm.free(); t = bpy.data.objects.new("Tent%d" % i, me); link(t, C_PROP)
    t.location = (x, y, 0); t.rotation_euler = (0, 0, R_(yw)); t.scale = (1.4, 1.0, 1.0); me.materials.append(M_CANVAS)
BUNKER = Vector((-25, 60, 0))
M_SAND = pbr("M_Sandbag", "aerial_sand", 0.6, tint=(0.75, 0.68, 0.5), rough=0.95)
for i in range(16):
    x = BUNKER.x - 7 + i * 0.95
    for row in range(3):
        b = box("Sandbag_%d_%d" % (i, row), (0.9, 0.5, 0.32), (x + (row % 2) * 0.45, BUNKER.y - 2.2, 0.16 + row * 0.3), mat=M_SAND, c_=C_PROP)
        mb = b.modifiers.new("bv", 'BEVEL'); mb.width = 0.12; mb.segments = 2
# telegraph poles along a track
for i in range(8):
    p_ = cyl("Pole%d" % i, 0.15, 0, 8, x=-90 + i * 34, y=200 + i * 6, mat=pbr("M_Wood", "dead_tree_trunk", 1.0), c_=C_PROP, verts=8)

# ------------------------------------------------------------------ fire column, smoke, fissure fires (volumes)
def fire_material(name, dens=6.0, smoke=False):
    m = bpy.data.materials.new(name); m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links; out = n["Material Output"]; n.remove(n["Principled BSDF"])
    tc = n.new('ShaderNodeTexCoord')
    mp = n.new('ShaderNodeMapping'); mp.name = "FlowMap"; mp.inputs['Scale'].default_value = (1.0, 1.0, 1.6); l.new(tc.outputs['Generated'], mp.inputs['Vector'])
    nz = n.new('ShaderNodeTexNoise'); nz.noise_dimensions = '4D'; nz.name = "FireNoise"
    nz.inputs['Scale'].default_value = 4.5; nz.inputs['Detail'].default_value = 8; nz.inputs['Roughness'].default_value = 0.62; nz.inputs['Distortion'].default_value = 1.2
    l.new(mp.outputs['Vector'], nz.inputs['Vector'])
    # radial falloff in generated space (0..1 box)
    sep = n.new('ShaderNodeSeparateXYZ'); l.new(tc.outputs['Generated'], sep.inputs['Vector'])
    cx = n.new('ShaderNodeVectorMath'); cx.operation = 'SUBTRACT'; cx.inputs[1].default_value = (0.5, 0.5, 0); l.new(tc.outputs['Generated'], cx.inputs[0])
    cxy = n.new('ShaderNodeVectorMath'); cxy.operation = 'MULTIPLY'; cxy.inputs[1].default_value = (2, 2, 0); l.new(cx.outputs[0], cxy.inputs[0])
    rl = n.new('ShaderNodeVectorMath'); rl.operation = 'LENGTH'; l.new(cxy.outputs[0], rl.inputs[0])
    rad = n.new('ShaderNodeMapRange'); rad.inputs['From Min'].default_value = 1.0; rad.inputs['From Max'].default_value = 0.25; l.new(rl.outputs['Value'], rad.inputs['Value'])
    rad.interpolation_type = 'SMOOTHSTEP'
    top = n.new('ShaderNodeMapRange'); top.inputs['From Min'].default_value = 1.0; top.inputs['From Max'].default_value = 0.55; l.new(sep.outputs['Z'], top.inputs['Value'])
    sh = n.new('ShaderNodeMath'); sh.operation = 'MULTIPLY'; l.new(rad.outputs['Result'], sh.inputs[0]); l.new(top.outputs['Result'], sh.inputs[1])
    d = n.new('ShaderNodeMath'); d.operation = 'MULTIPLY'; l.new(nz.outputs['Fac'], d.inputs[0]); l.new(sh.outputs[0], d.inputs[1])
    th = n.new('ShaderNodeMapRange'); th.inputs['From Min'].default_value = 0.36; th.inputs['From Max'].default_value = 0.6; l.new(d.outputs[0], th.inputs['Value'])
    amt = n.new('ShaderNodeValue'); amt.name = "FireAmt"; amt.outputs[0].default_value = 1.0
    da = n.new('ShaderNodeMath'); da.operation = 'MULTIPLY'; l.new(th.outputs['Result'], da.inputs[0]); l.new(amt.outputs[0], da.inputs[1])
    vol = n.new('ShaderNodeVolumePrincipled')
    dm = n.new('ShaderNodeMath'); dm.operation = 'MULTIPLY'; dm.inputs[1].default_value = dens; l.new(da.outputs[0], dm.inputs[0])
    l.new(dm.outputs[0], vol.inputs['Density'])
    if smoke:
        vol.inputs['Color'].default_value = (0.05, 0.045, 0.04, 1)
    else:
        vol.inputs['Color'].default_value = (0.2, 0.08, 0.02, 1)
        tmp = n.new('ShaderNodeMapRange'); tmp.inputs['To Min'].default_value = 900; tmp.inputs['To Max'].default_value = 2300
        hz = n.new('ShaderNodeMath'); hz.operation = 'MULTIPLY'; l.new(da.outputs[0], hz.inputs[0]); l.new(top.outputs['Result'], hz.inputs[1])
        l.new(hz.outputs[0], tmp.inputs['Value']); l.new(tmp.outputs['Result'], vol.inputs['Blackbody Tint'] if False else vol.inputs['Temperature'])
        bi = n.new('ShaderNodeMath'); bi.operation = 'MULTIPLY'; bi.inputs[1].default_value = 14.0; l.new(da.outputs[0], bi.inputs[0])
        l.new(bi.outputs[0], vol.inputs['Blackbody Intensity'])
    l.new(vol.outputs['Volume'], out.inputs['Volume'])
    return m
def fire_obj(name, base, r0, r1, h, mat):
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=r0, radius2=r1, depth=h, matrix=Matrix.Translation((0, 0, h / 2)))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); o.location = base; link(o, C_FX); me.materials.append(mat)
    o.visible_shadow = True
    return o
FIRE = fire_obj("FireColumn", (0, 0, 2.6), 9.0, 30.0, 125.0, fire_material("M_Fire", 5.0))
SMOKE = fire_obj("SmokePlume", (4, 8, 100), 22.0, 75.0, 160.0, fire_material("M_Smoke", 0.22, smoke=True))
FISSURES = []
FIS_PTS = [(13, 6), (-6, 14), (17, 26), (-24, 4), (6, 34), (-12, 30)]
M_FIS = fire_material("M_FissureFire", 6.0)
for i, (x, y) in enumerate(FIS_PTS):
    FISSURES.append(fire_obj("FissureFire%d" % i, (x, y, 0.2), 2.2, 5.0, 22.0, M_FIS))
# ground cracks: dark glowing strips radiating from the well
M_CRACK = flat("M_Crack", (0.02, 0.015, 0.01), 0.9, emit=(1.0, 0.35, 0.05), es=0.0)
CRACKS = []
for i, (x, y) in enumerate(FIS_PTS):
    d = Vector((x, y)); L = d.length
    bm = bmesh.new(); pts_ = []
    for k in range(13):
        t = k / 12; jitter = (noise.noise(Vector((i * 3.1, t * 6, 0))) * 1.6) if 0 < k < 12 else 0
        pp = d * t + Vector((-d.y, d.x)).normalized() * jitter; pts_.append(pp)
    for k in range(12):
        a, b = pts_[k], pts_[k + 1]; nrm = Vector((-(b - a).y, (b - a).x)).normalized() * (0.35 + 0.4 * math.sin(math.pi * k / 12))
        v = [bm.verts.new((a.x + nrm.x, a.y + nrm.y, 0.03)), bm.verts.new((b.x + nrm.x, b.y + nrm.y, 0.03)),
             bm.verts.new((b.x - nrm.x, b.y - nrm.y, 0.03)), bm.verts.new((a.x - nrm.x, a.y - nrm.y, 0.03))]
        bm.faces.new(v)
    me = bpy.data.meshes.new("Crack%d" % i); bm.to_mesh(me); bm.free(); o = bpy.data.objects.new("Crack%d" % i, me); link(o, C_FX)
    me.materials.append(M_CRACK); CRACKS.append(o)

# ------------------------------------------------------------------ water jets, steam, dust ring, blast sphere
M_WATER = bpy.data.materials.new("M_Water"); M_WATER.use_nodes = True
pw = M_WATER.node_tree.nodes["Principled BSDF"]; pw.inputs['Base Color'].default_value = (0.8, 0.9, 1.0, 1)
pw.inputs['Roughness'].default_value = 0.15; pw.inputs['Transmission Weight'].default_value = 0.6; pw.inputs['IOR'].default_value = 1.33
M_STEAM = bpy.data.materials.new("M_Steam"); M_STEAM.use_nodes = True
n, l = M_STEAM.node_tree.nodes, M_STEAM.node_tree.links; n.remove(n["Principled BSDF"])
tc = n.new('ShaderNodeTexCoord'); nz = n.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 2.5; nz.inputs['Detail'].default_value = 5; nz.name = "SteamNoise"
nz.noise_dimensions = '4D'; l.new(tc.outputs['Generated'], nz.inputs['Vector'])
sv = n.new('ShaderNodeValue'); sv.name = "SteamAmt"; sv.outputs[0].default_value = 0.0
rl = n.new('ShaderNodeVectorMath'); rl.operation = 'DISTANCE'; rl.inputs[1].default_value = (0.5, 0.5, 0.5); l.new(tc.outputs['Generated'], rl.inputs[0])
fo = n.new('ShaderNodeMapRange'); fo.inputs['From Min'].default_value = 0.5; fo.inputs['From Max'].default_value = 0.15; l.new(rl.outputs['Value'], fo.inputs['Value'])
mm = n.new('ShaderNodeMath'); mm.operation = 'MULTIPLY'; l.new(nz.outputs['Fac'], mm.inputs[0]); l.new(fo.outputs['Result'], mm.inputs[1])
mm2 = n.new('ShaderNodeMath'); mm2.operation = 'MULTIPLY'; l.new(mm.outputs[0], mm2.inputs[0]); l.new(sv.outputs[0], mm2.inputs[1])
vol = n.new('ShaderNodeVolumePrincipled'); vol.inputs['Color'].default_value = (0.95, 0.95, 0.95, 1)
l.new(mm2.outputs[0], vol.inputs['Density']); l.new(vol.outputs['Volume'], n["Material Output"].inputs['Volume'])
def steam_ball(name, loc, r):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=r)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); o = bpy.data.objects.new(name, me); o.location = loc; link(o, C_FX)
    me.materials.append(M_STEAM); return o
STEAM = [steam_ball("Steam%d" % i, (x, y, z), r) for i, (x, y, z, r) in enumerate(((3, 4, 4, 7), (-4, 6, 6, 6), (1, 8, 10, 8)))]
M_DUST = M_STEAM.copy(); M_DUST.name = "M_Dust"
M_DUST.node_tree.nodes["Principled Volume"].inputs['Color'].default_value = (0.75, 0.6, 0.42, 1)
M_DUST.node_tree.nodes["SteamAmt"].name = "DustAmt"
bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=48, radius1=1.0, radius2=0.8, depth=0.35, matrix=Matrix.Translation((0, 0, 0.17)))
me = bpy.data.meshes.new("DustRing"); bm.to_mesh(me); bm.free()
DUST = bpy.data.objects.new("DustRing", me); DUST.location = (SHAFT_X, 4, 0); link(DUST, C_FX); me.materials.append(M_DUST)
# blast: emission sphere + light
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=1.0)
me = bpy.data.meshes.new("BlastSphere"); bm.to_mesh(me); bm.free()
BLAST = bpy.data.objects.new("BlastSphere", me); BLAST.location = (SHAFT_X, 0.0, BLAST_Z); link(BLAST, C_FX)
for p_ in me.polygons: p_.use_smooth = True
mb_ = bpy.data.materials.new("M_Blast"); mb_.use_nodes = True; n = mb_.node_tree.nodes; n.remove(n["Principled BSDF"])
e = n.new('ShaderNodeEmission'); e.name = "BlastEmit"; e.inputs['Color'].default_value = (1.0, 0.95, 0.85, 1); e.inputs['Strength'].default_value = 0.0
mb_.node_tree.links.new(e.outputs['Emission'], n["Material Output"].inputs['Surface']); me.materials.append(mb_)
BLAST.visible_shadow = False
L_BLAST = bpy.data.lights.new("L_Blast", 'POINT'); L_BLAST.energy = 0; L_BLAST.color = (1.0, 0.85, 0.6); L_BLAST.shadow_soft_size = 4
lb = bpy.data.objects.new("L_Blast", L_BLAST); lb.location = (SHAFT_X, -6, BLAST_Z); link(lb, C_FX)

# ------------------------------------------------------------------ lights + world
sun = bpy.data.lights.new("Sun", 'SUN'); sun.energy = 3.0; sun.angle = R_(1.2); sun.color = (1.0, 0.95, 0.88)
SUN = bpy.data.objects.new("Sun", sun); SUN.rotation_euler = (R_(40), 0, R_(200)); link(SUN)
for i, (x, y, z) in enumerate(((0, -2, 15), (0, -2, 50), (0, 6, 90))):
    lf = bpy.data.lights.new("L_Fire%d" % i, 'POINT'); lf.energy = 0; lf.color = (1.0, 0.55, 0.2); lf.shadow_soft_size = 8
    o = bpy.data.objects.new("L_Fire%d" % i, lf); o.location = (x, y, z); link(o, C_FX)
# underground fill for the section (camera-invisible area lights in front of the face)
for i, (x, z, en) in enumerate(((-30, -25, 14000), (25, -70, 12000))):
    la = bpy.data.lights.new("L_Section%d" % i, 'AREA'); la.energy = en; la.size = 90; la.color = (0.95, 0.97, 1.0)
    o = bpy.data.objects.new("L_Section%d" % i, la); o.location = (x, -70, z); o.rotation_euler = (R_(90), 0, 0); link(o)
    o.visible_camera = False
# shaft lamp rings (small warm point lights down the bore)
for i, z in enumerate((-12, -28, -44)):
    ll = bpy.data.lights.new("L_ShaftLamp%d" % i, 'POINT'); ll.energy = 800; ll.color = (1.0, 0.8, 0.5); ll.shadow_soft_size = 0.5
    o = bpy.data.objects.new("L_ShaftLamp%d" % i, ll); o.location = (SHAFT_X, -2.4, z); link(o)

wd = bpy.data.worlds.new("World"); sc.world = wd; wd.use_nodes = True
n, l = wd.node_tree.nodes, wd.node_tree.links; bg = n["Background"]
tc = n.new('ShaderNodeTexCoord'); mpw = n.new('ShaderNodeMapping'); mpw.name = "SkyRot"; l.new(tc.outputs['Generated'], mpw.inputs['Vector'])
envs = []
for k in ("qwantani_noon_puresky", "qwantani_dusk_2_puresky", "qwantani_night_puresky"):
    t = n.new('ShaderNodeTexEnvironment'); t.image = img(os.path.join(A, "hdri", k + "_2k.hdr")); l.new(mpw.outputs['Vector'], t.inputs['Vector']); envs.append(t)
m1 = n.new('ShaderNodeMix'); m1.data_type = 'RGBA'; m1.name = "SkyDusk"; m1.inputs['Factor'].default_value = 0.0
m2 = n.new('ShaderNodeMix'); m2.data_type = 'RGBA'; m2.name = "SkyNight"; m2.inputs['Factor'].default_value = 0.0
l.new(envs[0].outputs['Color'], m1.inputs['A']); l.new(envs[1].outputs['Color'], m1.inputs['B'])
l.new(m1.outputs['Result'], m2.inputs['A']); l.new(envs[2].outputs['Color'], m2.inputs['B'])
l.new(m2.outputs['Result'], bg.inputs['Color']); bg.inputs['Strength'].default_value = 0.7; bg.name = "SkyBG"

# ------------------------------------------------------------------ camera
cam = bpy.data.cameras.new("CAM_Film"); cam.lens = 30; cam.sensor_fit = 'AUTO'; cam.clip_start = 0.1; cam.clip_end = 5000
cam.dof.use_dof = False
CAM = bpy.data.objects.new("CAM_Film", cam); link(CAM); sc.camera = CAM
TGT = bpy.data.objects.new("CAM_Target", None); link(TGT)
tt = CAM.constraints.new('TRACK_TO'); tt.target = TGT; tt.track_axis = 'TRACK_NEGATIVE_Z'; tt.up_axis = 'UP_Y'

# crew: park them at the site (animation places them per beat)
for i, nm in enumerate(("SolA", "SolB", "SolC", "SolD", "EngA", "EngB")):
    o = bpy.data.objects.get(nm)
    if o: o.location = (i * 2.0 - 5, 12, 0)
for m in bpy.data.materials:
    if m.name.startswith("M_"): m.use_fake_user = True
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SCENE SAVED", OUT, len(bpy.data.objects), "objects")
