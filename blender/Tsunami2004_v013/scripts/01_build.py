"""Tsunami2004 v013 stage A (from scratch): the coast, the ocean, the town, the earthquake cut-away and the family.
blender -b --factory-startup --python 01_build.py -- <models_dir> <out.blend>

World (metres, Z up): the sea lies to -Y, the land to +Y. Shore at y=-10 (sea level 0). Beach with palms, boats and
umbrellas; a three-storey beach hotel (DA KRAS FILMS sign on its roof) at x=+28; the town (houses, cars, the mosque) at
y=50..240; high ground (the hill) at (-70, 280). ONE water surface (geometry nodes) carries the drawdown, the wave, the
flood and the earthquake bulge, all driven by two keyed empties (WaveCtl, QuakeCtl); nothing reads the scene clock.
The earthquake cut-away sits under the sea at y=-1330..-1070: its cut face is the plane x=0 (seen from -X)."""
import bpy, bmesh, sys, math, random, os
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "lib_build.py")).read())
exec(open(os.path.join(HERE, "lib_tsu.py")).read())
a = sys.argv[sys.argv.index("--") + 1:]
MD, OUT = a[0], a[1]
PKG = os.path.dirname(HERE)
random.seed(25)
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
sc = bpy.context.scene
sc.render.fps = 60
sc.frame_start, sc.frame_end = 1, 2066
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
def col(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in sc.collection.children: sc.collection.children.link(c)
    return c
C_PEOPLE, C_SET, C_TOWN, C_SEC = col("PEOPLE"), col("SET"), col("TOWN"), col("SECTION")
def to_col(o, c):
    for cc in list(o.users_collection): cc.objects.unlink(o)
    c.objects.link(o)

# ================================================================== materials
def noise_mat(name, c1, c2, scale=2.0, rough=0.8, bump=0.2, detail=6.0, coat=0.0):
    m = mat(name, c1, rough=rough, coat=coat); nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = scale; nz.inputs["Detail"].default_value = detail
    cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (*c1, 1); cr.color_ramp.elements[1].color = (*c2, 1)
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"]); nt.links.new(nz.outputs["Fac"], cr.inputs["Fac"])
    nt.links.new(cr.outputs["Color"], p.inputs["Base Color"])
    if name.startswith(("M_Sediment", "M_OceanCrust", "M_Cont")):     # cut-away: clean, bright explainer layers with strata
        wv = nt.nodes.new("ShaderNodeTexWave"); wv.bands_direction = 'Z'; wv.inputs["Scale"].default_value = 0.06
        wv.inputs["Distortion"].default_value = 3.0; nt.links.new(tc.outputs["Object"], wv.inputs["Vector"])
        mx_ = nt.nodes.new("ShaderNodeMix"); mx_.data_type = 'RGBA'; mx_.blend_type = 'MULTIPLY'; mx_.inputs["Factor"].default_value = 0.35
        nt.links.new(cr.outputs["Color"], mx_.inputs["A"]); nt.links.new(wv.outputs["Color"], mx_.inputs["B"])
        nt.links.new(mx_.outputs["Result"], p.inputs["Base Color"])
        nt.links.new(cr.outputs["Color"], p.inputs["Emission Color"]); p.inputs["Emission Strength"].default_value = 0.45
    if bump:
        bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump; bp.inputs["Distance"].default_value = 0.02
        nt.links.new(nz.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], p.inputs["Normal"])
    return m

def ground_mat():
    """one material for the whole ground: wet sand / dry sand / seabed by height, earth+grass inland (world position)"""
    m = bpy.data.materials.new("M_Ground"); m.use_nodes = True; nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    L = nt.links.new
    geo = nt.nodes.new("ShaderNodeNewGeometry"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); L(geo.outputs["Position"], sep.inputs[0])
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.35; nz.inputs["Detail"].default_value = 8
    L(geo.outputs["Position"], nz.inputs["Vector"])
    nz2 = nt.nodes.new("ShaderNodeTexNoise"); nz2.inputs["Scale"].default_value = 0.04; nz2.inputs["Detail"].default_value = 3
    L(geo.outputs["Position"], nz2.inputs["Vector"])
    # sand colour by height: deep seabed -> wet -> dry
    rz = nt.nodes.new("ShaderNodeValToRGB"); e = rz.color_ramp.elements
    e[0].position = 0.0; e[0].color = (0.30, 0.20, 0.09, 1)        # z=-8: dark wet seabed
    e[1].position = 0.80; e[1].color = (0.55, 0.36, 0.15, 1)       # z=-1.6..0.3: wet sand
    e3 = rz.color_ramp.elements.new(0.93); e3.color = (0.95, 0.70, 0.36, 1)   # dry golden sand
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs[1].default_value = -8.0; mr.inputs[2].default_value = 1.0
    L(sep.outputs["Z"], mr.inputs[0]); L(mr.outputs[0], rz.inputs["Fac"])
    # inland: terracotta earth with green grass patches (y > 32)
    ry = nt.nodes.new("ShaderNodeValToRGB"); f = ry.color_ramp.elements
    f[0].position = 0.45; f[0].color = (0.62, 0.26, 0.08, 1); f[1].position = 0.56; f[1].color = (0.16, 0.42, 0.05, 1)
    L(nz2.outputs["Fac"], ry.inputs["Fac"])
    my = nt.nodes.new("ShaderNodeMapRange"); my.inputs[1].default_value = 30.0; my.inputs[2].default_value = 40.0
    L(sep.outputs["Y"], my.inputs[0])
    # real CC0 textures (Poly Haven): sand, grass; tinted by the height ramps above (wet/dry sand, earth/grass)
    def T(fname, size):
        ti = nt.nodes.new("ShaderNodeTexImage"); ti.image = bpy.data.images.load(os.path.join(PKG, "assets", "tex", fname)); ti.image.name = fname[:-4]
        mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1.0 / size, 1.0 / size, 1.0 / size)
        L(geo.outputs["Position"], mp.inputs["Vector"]); L(mp.outputs["Vector"], ti.inputs["Vector"]); return ti.outputs["Color"]
    def MUL(a_, b_, k=1.0):
        m_ = nt.nodes.new("ShaderNodeMix"); m_.data_type = 'RGBA'; m_.blend_type = 'MULTIPLY'; m_.inputs["Factor"].default_value = 1.0
        L(a_, m_.inputs["A"])
        if isinstance(b_, tuple): m_.inputs["B"].default_value = (*b_, 1)
        else: L(b_, m_.inputs["B"])
        vm = nt.nodes.new("ShaderNodeVectorMath"); vm.operation = 'SCALE'; vm.inputs["Scale"].default_value = k
        L(m_.outputs["Result"], vm.inputs[0]); return vm.outputs[0]
    sandt = T("coast_sand_01_diff_1k.jpg", 2.5); grasst = T("aerial_grass_rock_diff_1k.jpg", 5.0)
    sandc = MUL(rz.outputs["Color"], sandt, 2.4)
    earth = MUL(sandt, (0.62, 0.26, 0.08), 2.0); grass = MUL(grasst, (0.75, 1.0, 0.55), 1.5)
    gm = nt.nodes.new("ShaderNodeMapRange"); gm.inputs[1].default_value = 0.47; gm.inputs[2].default_value = 0.53; L(nz2.outputs["Fac"], gm.inputs[0])
    inl = nt.nodes.new("ShaderNodeMix"); inl.data_type = 'RGBA'; L(gm.outputs[0], inl.inputs["Factor"]); L(earth, inl.inputs["A"]); L(grass, inl.inputs["B"])
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; L(my.outputs[0], mx.inputs["Factor"])
    L(sandc, mx.inputs["A"]); L(inl.outputs["Result"], mx.inputs["B"])
    # fine grain variation
    mul = nt.nodes.new("ShaderNodeMix"); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs["Factor"].default_value = 0.35
    L(mx.outputs["Result"], mul.inputs["A"]); L(nz.outputs["Color"], mul.inputs["B"])
    L(mul.outputs["Result"], p.inputs["Base Color"])
    # wet sand is glossier
    rr = nt.nodes.new("ShaderNodeMapRange"); rr.inputs[1].default_value = -1.0; rr.inputs[2].default_value = 0.5
    rr.inputs[3].default_value = 0.6; rr.inputs[4].default_value = 0.92; L(sep.outputs["Z"], rr.inputs[0]); L(rr.outputs[0], p.inputs["Roughness"])
    # sand ripples
    wv = nt.nodes.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = 0.9; wv.inputs["Distortion"].default_value = 4
    wv.inputs["Detail"].default_value = 2; wv.bands_direction = 'Y'; L(geo.outputs["Position"], wv.inputs["Vector"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Distance"].default_value = 0.03
    inv = nt.nodes.new("ShaderNodeMath"); inv.operation = 'MULTIPLY_ADD'; inv.inputs[1].default_value = -0.25; inv.inputs[2].default_value = 0.25
    L(my.outputs[0], inv.inputs[0]); L(inv.outputs[0], bp.inputs["Strength"])          # sand ripples on the sand only, not the grass
    L(wv.outputs["Fac"], bp.inputs["Height"]); L(bp.outputs["Normal"], p.inputs["Normal"])
    return m

def water_mat():
    m = bpy.data.materials.new("M_Water"); m.use_nodes = True; nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    L = nt.links.new
    geo = nt.nodes.new("ShaderNodeNewGeometry"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); L(geo.outputs["Position"], sep.inputs[0])
    # sea colour: deep blue offshore -> saturated turquoise near the shore; muddy brown over land (attribute "mud")
    my = nt.nodes.new("ShaderNodeMapRange"); my.inputs[1].default_value = -600.0; my.inputs[2].default_value = -60.0; L(sep.outputs["Y"], my.inputs[0])
    c1 = nt.nodes.new("ShaderNodeMix"); c1.data_type = 'RGBA'; L(my.outputs[0], c1.inputs["Factor"])
    c1.inputs["A"].default_value = (0.0, 0.10, 0.36, 1); c1.inputs["B"].default_value = (0.0, 0.42, 0.50, 1)
    mud = nt.nodes.new("ShaderNodeAttribute"); mud.attribute_name = "mud"
    c2 = nt.nodes.new("ShaderNodeMix"); c2.data_type = 'RGBA'; L(mud.outputs["Fac"], c2.inputs["Factor"])
    L(c1.outputs["Result"], c2.inputs["A"]); c2.inputs["B"].default_value = (0.36, 0.22, 0.08, 1)
    fa = nt.nodes.new("ShaderNodeAttribute"); fa.attribute_name = "face"
    sk = nt.nodes.new("ShaderNodeTexNoise"); sk.inputs["Scale"].default_value = 0.15; sk.inputs["Detail"].default_value = 3
    mpp = nt.nodes.new("ShaderNodeMapping"); mpp.inputs["Scale"].default_value = (1.0, 0.25, 0.04)
    L(geo.outputs["Position"], mpp.inputs["Vector"]); L(mpp.outputs["Vector"], sk.inputs["Vector"])
    skr = nt.nodes.new("ShaderNodeValToRGB"); skr.color_ramp.elements[0].color = (0.0, 0.20, 0.24, 1); skr.color_ramp.elements[1].color = (0.02, 0.36, 0.38, 1)
    L(sk.outputs["Fac"], skr.inputs["Fac"])
    c15 = nt.nodes.new("ShaderNodeMix"); c15.data_type = 'RGBA'; L(fa.outputs["Fac"], c15.inputs["Factor"])
    L(c2.outputs["Result"], c15.inputs["A"]); L(skr.outputs["Color"], c15.inputs["B"])
    foam = nt.nodes.new("ShaderNodeAttribute"); foam.attribute_name = "foam"
    fn = nt.nodes.new("ShaderNodeTexNoise"); fn.inputs["Scale"].default_value = 0.25; fn.inputs["Detail"].default_value = 8
    fmp = nt.nodes.new("ShaderNodeMapping"); fmp.inputs["Scale"].default_value = (1.0, 0.5, 0.18)     # foam in streaks running down the face
    L(geo.outputs["Position"], fmp.inputs["Vector"]); L(fmp.outputs["Vector"], fn.inputs["Vector"])
    fm = nt.nodes.new("ShaderNodeMath"); fm.operation = 'MULTIPLY'; L(foam.outputs["Fac"], fm.inputs[0]); L(fn.outputs["Fac"], fm.inputs[1])
    fr = nt.nodes.new("ShaderNodeMapRange"); fr.inputs[1].default_value = 0.18; fr.inputs[2].default_value = 0.42; L(fm.outputs[0], fr.inputs[0])
    c3 = nt.nodes.new("ShaderNodeMix"); c3.data_type = 'RGBA'; L(fr.outputs[0], c3.inputs["Factor"])
    L(c15.outputs["Result"], c3.inputs["A"]); c3.inputs["B"].default_value = (0.92, 0.96, 0.97, 1)
    L(c3.outputs["Result"], p.inputs["Base Color"])
    rr = nt.nodes.new("ShaderNodeMapRange"); rr.inputs[3].default_value = 0.08; rr.inputs[4].default_value = 0.6
    L(fr.outputs[0], rr.inputs[0]); L(rr.outputs[0], p.inputs["Roughness"])
    p.inputs["IOR"].default_value = 1.33; p.inputs["Specular IOR Level"].default_value = 0.35
    # small chop on the normal
    wn = nt.nodes.new("ShaderNodeTexNoise"); wn.inputs["Scale"].default_value = 0.6; wn.inputs["Detail"].default_value = 4
    L(geo.outputs["Position"], wn.inputs["Vector"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.12; bp.inputs["Distance"].default_value = 0.1
    L(wn.outputs["Fac"], bp.inputs["Height"]); L(bp.outputs["Normal"], p.inputs["Normal"])
    # seen from below (the dive into the cut-away): a bright cyan ceiling
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (0.25, 0.80, 0.95, 1); em.inputs["Strength"].default_value = 1.2
    ms = nt.nodes.new("ShaderNodeMixShader"); L(geo.outputs["Backfacing"], ms.inputs["Fac"])
    L(p.outputs["BSDF"], ms.inputs[1]); L(em.outputs["Emission"], ms.inputs[2])
    L(ms.outputs["Shader"], nt.nodes["Material Output"].inputs["Surface"])
    return m

M_GROUND = ground_mat(); M_WATER = water_mat()

# ================================================================== variable-spacing grids
def axis(lo, hi, bands):
    """coordinates lo..hi; bands = [(a, b, step)] fine regions, else the last default step"""
    xs = [lo]; x = lo
    while x < hi:
        st = bands[-1][2]
        for a_, b_, s_ in bands[:-1]:
            if a_ <= x < b_: st = s_; break
        x = min(hi, x + st); xs.append(x)
    return xs

def grid_mesh(name, xs, ys, zfun, keep=None):
    me = bpy.data.meshes.new(name); bm = bmesh.new(); V = {}
    for j, y in enumerate(ys):
        for i, x in enumerate(xs):
            V[i, j] = bm.verts.new((x, y, zfun(x, y)))
    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            cx, cy = (xs[i] + xs[i + 1]) / 2, (ys[j] + ys[j + 1]) / 2
            if keep and not keep(cx, cy): continue
            bm.faces.new((V[i, j], V[i + 1, j], V[i + 1, j + 1], V[i, j + 1]))
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context='VERTS')
    bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o); return o

# ---- terrain (the hole for the cut-away: x<0 within SECTION_Y)
def keep_ground(x, y): return not (x < 0 and SECTION_Y[0] < y < SECTION_Y[1])
def zg(x, y):
    z = G(x, y)
    if not (-40 < x < 40 and -60 < y < 50):        # gentle dunes away from where people walk (feet use G exactly)
        z += 0.12 * math.sin(x * 0.11 + y * 0.05) * math.sin(y * 0.07)
    return z
gx = axis(-900, 900, [(-160, 160, 1.5), (-400, 400, 5.0), (0, 0, 14.0)])
gy = axis(-2100, 420, [(-70, 70, 1.0), (-300, 330, 2.0), (-1400, -300, 6.0), (0, 0, 14.0)])
GROUND = grid_mesh("Ground", gx, gy, zg, keep_ground); GROUND.data.materials.append(M_GROUND); to_col(GROUND, C_SET)
print("ground verts", len(GROUND.data.vertices))

# ---- the ocean: one surface for drawdown, wave, flood and quake bulge
wx = axis(-900, 900, [(-140, 140, 1.0), (-400, 400, 4.0), (0, 0, 12.0)])
wy = axis(-2100, 400, [(-280, 380, 0.8), (-1400, -280, 3.0), (0, 0, 8.0)])
SEA = grid_mesh("Ocean", wx, wy, lambda x, y: 0.0); SEA.data.materials.append(M_WATER); to_col(SEA, C_SET)
print("ocean verts", len(SEA.data.vertices))
WCTL = bpy.data.objects.new("WaveCtl", None); C_SET.objects.link(WCTL)        # loc = (L level, Yf front, A height); scale = (p plateau, curl, phase)
WCTL.location = (0.0, -2600.0, 0.0); WCTL.scale = (0.5, 0.0, 0.0)
QCTL = bpy.data.objects.new("QuakeCtl", None); C_SET.objects.link(QCTL)       # loc = (x, y, height) of the bulge
QCTL.location = (60.0, -1200.0, 0.0)

def build_ocean_gn():
    ng = bpy.data.node_groups.new("OceanGN", 'GeometryNodeTree')
    ng.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    N = ng.nodes; Lk = ng.links.new
    gi = N.new("NodeGroupInput"); go = N.new("NodeGroupOutput")
    def node(t, **kw):
        n = N.new(t)
        for k, v in kw.items(): setattr(n, k, v)
        return n
    def sock(v):
        return v
    def M(op, a_, b_=None, c_=None):
        n = node("ShaderNodeMath", operation=op)
        for i, v in enumerate((a_, b_, c_)):
            if v is None: continue
            if isinstance(v, (int, float)): n.inputs[i].default_value = v
            else: Lk(v, n.inputs[i])
        return n.outputs[0]
    def SS(e0, e1, x):
        n = node("ShaderNodeMapRange", interpolation_type='SMOOTHSTEP')
        for i, v in ((1, e0), (2, e1)):
            if isinstance(v, (int, float)): n.inputs[i].default_value = v
            else: Lk(v, n.inputs[i])
        Lk(x, n.inputs[0]); return n.outputs[0]
    pos = node("GeometryNodeInputPosition"); sp = node("ShaderNodeSeparateXYZ"); Lk(pos.outputs[0], sp.inputs[0])
    X, Y = sp.outputs[0], sp.outputs[1]
    oi = node("GeometryNodeObjectInfo"); oi.inputs[0].default_value = WCTL; oi.transform_space = 'ORIGINAL'
    so = node("ShaderNodeSeparateXYZ"); Lk(oi.outputs["Location"], so.inputs[0])
    ss = node("ShaderNodeSeparateXYZ"); Lk(oi.outputs["Scale"], ss.inputs[0])
    Lv, Yf, A = so.outputs[0], so.outputs[1], so.outputs[2]
    P, CURL, PH = ss.outputs[0], ss.outputs[1], ss.outputs[2]
    qi = node("GeometryNodeObjectInfo"); qi.inputs[0].default_value = QCTL; qi.transform_space = 'ORIGINAL'
    sq = node("ShaderNodeSeparateXYZ"); Lk(qi.outputs["Location"], sq.inputs[0])
    lr = M('MULTIPLY', Lv, SS(-1200.0, -400.0, Y))
    wf = M('MAXIMUM', 3.0, M('MULTIPLY', A, 0.8))
    wb = M('ADD', M('MULTIPLY', A, 4.0), 20.0)
    u = M('SUBTRACT', Yf, Y)
    rise = SS(M('MULTIPLY', wf, -0.15), wf, u)
    behind = M('DIVIDE', M('MAXIMUM', 0.0, M('SUBTRACT', u, wf)), wb)
    decay = M('ADD', P, M('MULTIPLY', M('SUBTRACT', 1.0, P), M('EXPONENT', M('MULTIPLY', behind, -1.0))))
    taper = M('SUBTRACT', 1.0, SS(450.0, 800.0, M('ABSOLUTE', X)))
    # variation along the front (the wave is not a ruler line)
    nz = node("ShaderNodeTexNoise"); nz.noise_dimensions = '2D'; nz.inputs["Scale"].default_value = 0.012
    cxy = node("ShaderNodeCombineXYZ"); Lk(X, cxy.inputs[0]); cxy.inputs[1].default_value = 0.0; Lk(cxy.outputs[0], nz.inputs["Vector"])
    var = M('ADD', 0.82, M('MULTIPLY', nz.outputs["Fac"], 0.36))
    hw = M('MULTIPLY', M('MULTIPLY', M('MULTIPLY', A, rise), decay), M('MULTIPLY', taper, var))
    dx = M('SUBTRACT', X, sq.outputs[0]); dy = M('SUBTRACT', Y, sq.outputs[1])
    gq = M('EXPONENT', M('ADD', M('DIVIDE', M('MULTIPLY', dx, dx), -9800.0), M('DIVIDE', M('MULTIPLY', dy, dy), -3200.0)))
    hq = M('MULTIPLY', sq.outputs[2], gq)
    # ripples: 4D noise, phase keyed on WaveCtl.scale.z (no scene clock)
    rn = node("ShaderNodeTexNoise"); rn.noise_dimensions = '4D'; rn.inputs["Scale"].default_value = 0.18; rn.inputs["Detail"].default_value = 3
    Lk(pos.outputs[0], rn.inputs["Vector"]); Lk(PH, rn.inputs["W"])
    rip = M('MULTIPLY', M('SUBTRACT', rn.outputs["Fac"], 0.5), 0.35)
    z = M('ADD', M('ADD', lr, hw), M('ADD', hq, rip))
    # the crest leans forward (+Y) a little: a lip
    tq = M('DIVIDE', M('SUBTRACT', u, M('MULTIPLY', wf, 0.85)), M('MULTIPLY', wf, 0.3))
    cr = M('EXPONENT', M('MULTIPLY', M('MULTIPLY', tq, tq), -1.0))
    dyo = M('MULTIPLY', M('MULTIPLY', M('MULTIPLY', CURL, A), cr), taper)
    off = node("ShaderNodeCombineXYZ"); off.inputs[0].default_value = 0.0; Lk(dyo, off.inputs[1]); Lk(z, off.inputs[2])
    setp = node("GeometryNodeSetPosition"); Lk(gi.outputs[0], setp.inputs["Geometry"]); Lk(off.outputs[0], setp.inputs["Offset"])
    # foam: on the face and crest, and a fading wake behind
    fcrest = M('MULTIPLY', SS(M('MULTIPLY', wf, 0.3), M('MULTIPLY', wf, 0.7), u), M('SUBTRACT', 1.0, SS(M('MULTIPLY', wf, 1.2), M('MULTIPLY', wf, 3.0), u)))
    ftoe = M('MULTIPLY', SS(M('MULTIPLY', wf, -0.18), M('MULTIPLY', wf, -0.02), u), M('SUBTRACT', 1.0, SS(M('MULTIPLY', wf, 0.02), M('MULTIPLY', wf, 0.15), u)))
    fface = M('MAXIMUM', fcrest, ftoe)
    fwake = M('MULTIPLY', M('MULTIPLY', 0.55, SS(0.0, 4.0, u)), M('SUBTRACT', 1.0, SS(0.0, M('MULTIPLY', wb, 2.5), u)))
    foam = M('MULTIPLY', M('MAXIMUM', fface, fwake), M('MINIMUM', 1.0, M('MULTIPLY', A, 0.4)))
    foam = M('MULTIPLY', foam, taper)
    st = node("GeometryNodeStoreNamedAttribute"); st.data_type = 'FLOAT'; st.domain = 'POINT'; st.inputs["Name"].default_value = "foam"
    Lk(setp.outputs[0], st.inputs["Geometry"]); Lk(foam, st.inputs["Value"])
    face = M('MULTIPLY', M('MULTIPLY', SS(M('MULTIPLY', wf, -0.1), M('MULTIPLY', wf, 0.3), u), M('SUBTRACT', 1.0, SS(M('MULTIPLY', wf, 0.7), M('MULTIPLY', wf, 1.6), u))),
              M('MINIMUM', 1.0, M('MULTIPLY', A, 0.12)))
    st3 = node("GeometryNodeStoreNamedAttribute"); st3.data_type = 'FLOAT'; st3.domain = 'POINT'; st3.inputs["Name"].default_value = "face"
    Lk(st.outputs[0], st3.inputs["Geometry"]); Lk(M('MULTIPLY', face, taper), st3.inputs["Value"])
    mud = SS(-14.0, 6.0, Y)
    st2 = node("GeometryNodeStoreNamedAttribute"); st2.data_type = 'FLOAT'; st2.domain = 'POINT'; st2.inputs["Name"].default_value = "mud"
    Lk(st3.outputs[0], st2.inputs["Geometry"]); Lk(mud, st2.inputs["Value"])
    # spray: clumps of white droplets thrown off the crest (deterministic per frame, no simulation)
    crest_sel = M('GREATER_THAN', M('MULTIPLY', cr, M('MINIMUM', 1.0, M('MULTIPLY', M('SUBTRACT', A, 6.0), 0.2))), 0.35)
    dist = node("GeometryNodeDistributePointsOnFaces"); dist.distribute_method = 'RANDOM'
    Lk(st2.outputs[0], dist.inputs["Mesh"]); Lk(crest_sel, dist.inputs["Selection"]); dist.inputs["Density"].default_value = 0.08
    def rsock(n, io, name, typ):
        return [x for x in (n.inputs if io == 'in' else n.outputs) if x.name == name and x.type == typ][0]
    rv = node("FunctionNodeRandomValue"); rv.data_type = 'FLOAT'
    rsock(rv, 'in', "Min", 'VALUE').default_value = 0.0; rsock(rv, 'in', "Max", 'VALUE').default_value = 1.0
    RV = rsock(rv, 'out', "Value", 'VALUE')
    up = node("ShaderNodeCombineXYZ"); up.inputs[0].default_value = 0.0
    Lk(M('MULTIPLY', M('MULTIPLY', RV, A), -0.25), up.inputs[1]); Lk(M('MULTIPLY', M('MULTIPLY', RV, A), 0.30), up.inputs[2])
    sp2 = node("GeometryNodeSetPosition"); Lk(dist.outputs["Points"], sp2.inputs["Geometry"]); Lk(up.outputs[0], sp2.inputs["Offset"])
    ico = node("GeometryNodeMeshIcoSphere"); ico.inputs["Radius"].default_value = 0.45; ico.inputs["Subdivisions"].default_value = 2
    inst = node("GeometryNodeInstanceOnPoints"); Lk(sp2.outputs[0], inst.inputs["Points"]); Lk(ico.outputs["Mesh"], inst.inputs["Instance"])
    rs = node("FunctionNodeRandomValue"); rs.data_type = 'FLOAT_VECTOR'
    rsock(rs, 'in', "Min", 'VECTOR').default_value = (0.4, 0.4, 0.3); rsock(rs, 'in', "Max", 'VECTOR').default_value = (2.2, 2.2, 1.6)
    Lk(rsock(rs, 'out', "Value", 'VECTOR'), inst.inputs["Scale"])
    smat = node("GeometryNodeSetMaterial"); Lk(inst.outputs[0], smat.inputs["Geometry"]); smat.inputs["Material"].default_value = M_SPRAY
    join = node("GeometryNodeJoinGeometry"); Lk(smat.outputs[0], join.inputs[0]); Lk(st2.outputs[0], join.inputs[0])
    Lk(join.outputs[0], go.inputs[0])
    return ng
M_SPRAY = mat("M_Spray", (0.95, 0.97, 1.0), rough=0.5); M_SPRAY.node_tree.nodes["Principled BSDF"].inputs["Subsurface Weight"].default_value = 0.4
md = SEA.modifiers.new("Ocean", 'NODES'); md.node_group = build_ocean_gn()

# ---- far ocean outside the simulated area (static, sea level 0), a ring around it
FAR = bpy.data.meshes.new("FarSea"); bm = bmesh.new()
outer = [(-30000, -30000), (30000, -30000), (30000, 30000), (-30000, 30000)]
inner = [(-899, -2099), (899, -2099), (899, 399), (-899, 399)]
vo = [bm.verts.new((x, y, -0.02)) for x, y in outer]; vi = [bm.verts.new((x, y, -0.02)) for x, y in inner]
for i in range(4):
    bm.faces.new((vo[i], vo[(i + 1) % 4], vi[(i + 1) % 4], vi[i]))
bm.to_mesh(FAR); bm.free()
FARO = bpy.data.objects.new("FarSea", FAR); C_SET.objects.link(FARO)
M_FAR = mat("M_FarSea", (0.0, 0.10, 0.36), rough=0.12); M_FAR.node_tree.nodes["Principled BSDF"].inputs["Specular IOR Level"].default_value = 0.35
FAR.materials.append(M_FAR)
# land beyond the simulated area inland (y>400): green hills band so the horizon behind the town is not water
LAND = grid_mesh("FarLand", axis(-6000, 6000, [(0, 0, 200.0)]), axis(395, 6000, [(0, 0, 150.0)]),
                 lambda x, y: 1.4 + (0 if y < 450 else 6.0 * (1 - math.exp(-(y - 450) / 600.0)) * (0.7 + 0.3 * math.sin(x * 0.004))))
LAND.data.materials.append(noise_mat("M_FarLand", (0.10, 0.34, 0.04), (0.22, 0.45, 0.08), scale=0.01, bump=0.0)); to_col(LAND, C_SET)

# ================================================================== sky (gradient + clouds; the golden-hour mix is keyed in 02)
W = bpy.data.worlds.new("Sky"); sc.world = W; W.use_nodes = True; nt = W.node_tree; Lk = nt.links.new
bg = nt.nodes["Background"]
tc = nt.nodes.new("ShaderNodeTexCoord"); sep0 = nt.nodes.new("ShaderNodeSeparateXYZ"); Lk(tc.outputs["Generated"], sep0.inputs[0])
zmap = nt.nodes.new("ShaderNodeMapRange"); zmap.inputs[1].default_value = -1.0; zmap.inputs[2].default_value = 1.0; Lk(sep0.outputs["Z"], zmap.inputs[0])
class _S: pass
sep = _S(); sep.outputs = {"Z": zmap.outputs[0]}
def sky_ramp(cols):
    r = nt.nodes.new("ShaderNodeValToRGB"); el = r.color_ramp.elements
    el[0].position, el[0].color = cols[0][0], (*cols[0][1], 1); el[1].position, el[1].color = cols[1][0], (*cols[1][1], 1)
    for p_, c_ in cols[2:]:
        e = el.new(p_); e.color = (*c_, 1)
    Lk(sep.outputs["Z"], r.inputs["Fac"]); return r
# Generated z of the world: 0.5 = horizon; below = under the horizon (seen underwater: deep blue)
DAY = sky_ramp([(0.30, (0.0, 0.05, 0.22)), (0.49, (0.10, 0.55, 0.80)), (0.505, (0.62, 0.88, 1.0)), (0.62, (0.18, 0.55, 0.98)), (0.95, (0.03, 0.22, 0.80))])
DUSK = sky_ramp([(0.30, (0.0, 0.04, 0.18)), (0.49, (0.30, 0.25, 0.35)), (0.505, (1.0, 0.55, 0.18)), (0.58, (0.95, 0.35, 0.25)), (0.95, (0.16, 0.12, 0.50))])
SKYMIX = nt.nodes.new("ShaderNodeMix"); SKYMIX.data_type = 'RGBA'; SKYMIX.name = "SkyMix"; SKYMIX.inputs["Factor"].default_value = 0.0
Lk(DAY.outputs["Color"], SKYMIX.inputs["A"]); Lk(DUSK.outputs["Color"], SKYMIX.inputs["B"])
cl = nt.nodes.new("ShaderNodeTexNoise"); cl.inputs["Scale"].default_value = 3.5; cl.inputs["Detail"].default_value = 6; cl.inputs["Roughness"].default_value = 0.6
Lk(tc.outputs["Generated"], cl.inputs["Vector"])
cm = nt.nodes.new("ShaderNodeMapRange"); cm.inputs[1].default_value = 0.56; cm.inputs[2].default_value = 0.72; Lk(cl.outputs["Fac"], cm.inputs[0])
hz = nt.nodes.new("ShaderNodeMapRange"); hz.inputs[1].default_value = 0.505; hz.inputs[2].default_value = 0.56; Lk(sep.outputs["Z"], hz.inputs[0])
cmm = nt.nodes.new("ShaderNodeMath"); cmm.operation = 'MULTIPLY'; Lk(cm.outputs[0], cmm.inputs[0]); Lk(hz.outputs[0], cmm.inputs[1])
CLOUDCOL = nt.nodes.new("ShaderNodeMix"); CLOUDCOL.data_type = 'RGBA'; CLOUDCOL.name = "CloudCol"
CLOUDCOL.inputs["A"].default_value = (1.0, 1.0, 1.0, 1); CLOUDCOL.inputs["B"].default_value = (1.0, 0.62, 0.38, 1); CLOUDCOL.inputs["Factor"].default_value = 0.0
cmix = nt.nodes.new("ShaderNodeMix"); cmix.data_type = 'RGBA'; Lk(cmm.outputs[0], cmix.inputs["Factor"])
Lk(SKYMIX.outputs["Result"], cmix.inputs["A"]); Lk(CLOUDCOL.outputs["Result"], cmix.inputs["B"])
Lk(cmix.outputs["Result"], bg.inputs["Color"]); bg.inputs["Strength"].default_value = 1.0

# ================================================================== props from the CC-BY models (credits in CREDITS.md)
MODELS = {}
def model(key, dim, axis_=None, keep=None):
    if key not in MODELS:
        o = imp(os.path.join(MD, key + ".glb"), "SRC_" + key, target_dim=dim, axis=axis_, keep=keep)
        soften(o, rough_min=0.35); MODELS[key] = o
        to_col(o, C_SET); o.hide_render = o.hide_viewport = True
    return MODELS[key]
def place(key, name, loc, rz=0.0, s=1.0, coll=C_SET, rx=0.0, ry=0.0, ground=True, sink=0.0):
    src = MODELS[key]; o = bpy.data.objects.new(name, src.data); coll.objects.link(o)
    z = G(loc[0], loc[1]) - sink if ground else loc[2]
    o.location = (loc[0], loc[1], z); o.rotation_euler = (rx, ry, rz); o.scale = (s, s, s)
    return o
model("palm_a", 9.0, 2); model("banana", 4.5, 2); model("longtail", 9.0, 1); model("rowboat", 3.6, 1)
model("umbrella", 2.4, 2); model("coral", 1.1, 2); model("car", 4.3, 1)
model("house", 13.0, 0); model("house2", 9.0, 0); model("b_slum1", 7.5, 2)
model("rubble_roof", 6.5, 0); model("rubble_brick", 3.0, 0); model("rubble_wood", 4.0, 0)
model("mosque", 34.0, 0)
for k in ("house", "house2", "b_slum1", "mosque"):           # buildings: deeper, warmer colours
    for m_ in MODELS[k].data.materials: tint(m_, (1.15, 1.0, 0.85))

# fish: three separate fish from the one glb
before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=os.path.join(MD, "fish.glb"))
FISH_SRC = [o for o in bpy.data.objects if o not in before and o.type == 'MESH']
for o in [o for o in bpy.data.objects if o not in before and o.type != 'MESH']: bpy.data.objects.remove(o)
fishes = []
for i, o in enumerate(FISH_SRC):
    mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    vs = [v.co for v in o.data.vertices]; mn = Vector([min(v[k] for v in vs) for k in range(3)]); mx = Vector([max(v[k] for v in vs) for k in range(3)])
    o.data.transform(Matrix.Translation(-(mn + mx) / 2)); d = mx - mn
    long_ax = max(range(3), key=lambda k: d[k]); s = 0.42 / d[long_ax]
    o.data.transform(Matrix.Scale(s, 4))
    if long_ax == 2: o.data.transform(Matrix.Rotation(math.radians(90), 4, 'X'))
    if long_ax == 0: o.data.transform(Matrix.Rotation(math.radians(90), 4, 'Z'))
    o.name = "SRC_fish%d" % i; soften(o, rough_min=0.3); fishes.append(o); to_col(o, C_SET); o.hide_render = o.hide_viewport = True
for o in fishes:
    for m_ in o.data.materials: tint(m_, (0.75, 1.1, 1.25))      # silver-blue, a little saturated

# ---- beach dressing
PALMS = []
for i, (x, y) in enumerate([(-34, 12), (-24, 16), (-15, 13), (-8, 19), (9, 13), (14, 18), (44, 13), (52, 17), (62, 12), (-44, 18),
                            (-55, 14), (72, 16), (-66, 19), (84, 13), (-10, 30), (60, 34), (-40, 40), (90, 30)]):
    o = place("palm_a", "Palm%02d" % i, (x, y), rz=random.uniform(0, 6.28), s=random.uniform(0.9, 1.2))
    o.rotation_euler.x = math.radians(random.uniform(-5, 5)); PALMS.append(o)
for i, (x, y) in enumerate([(-30, 4), (-18, 6), (10, 5), (40, 6), (54, 4)]):
    place("umbrella", "Umbrella%d" % i, (x, y), rz=random.uniform(0, 6.28), sink=0.15)
BOATS = []
for i, (x, y, rz) in enumerate([(-28, -3, 1.4), (18, -4, 1.7), (34, -1, 1.5)]):
    BOATS.append(place("longtail", "Longtail%d" % i, (x, y), rz=rz, sink=0.25))
BOATS.append(place("rowboat", "Rowboat0", (-36, 1), rz=0.9, sink=0.08))
# the stranded boat on the exposed seabed, on its side (rests on the sand: hull bilge on the ground)
TIPPED = place("longtail", "LongtailTipped", (14.0, -34.0), rz=math.radians(25), ry=math.radians(62), sink=-0.35)
for i, (x, y, s) in enumerate([(-9, -46, 1.0), (-5, -52, 0.8), (7, -55, 1.2), (12, -44, 0.7), (-14, -60, 1.1), (2, -66, 0.9), (16, -63, 1.0)]):
    place("coral", "Coral%d" % i, (x, y), rz=random.uniform(0, 6.28), s=s, sink=0.05)
FISH = []
for i, (x, y) in enumerate([(-1.0, -16.2), (1.1, -17.4), (-3.6, -18.0), (2.9, -19.6), (-1.8, -20.4), (4.6, -16.8), (-5.6, -16.6), (0.6, -22.4)]):
    src = fishes[i % len(fishes)]
    o = bpy.data.objects.new("Fish%d" % i, src.data); C_SET.objects.link(o)
    o.rotation_mode = 'XYZ'; o.rotation_euler = (0, math.radians(90), random.uniform(0, 6.28))   # lying on its side (roll about its length)
    o.location = (x, y, G(x, y) + 0.045); FISH.append(o)

# ================================================================== the beach hotel (DA KRAS FILMS sign on the roof)
M_PLASTER = noise_mat("M_HotelPlaster", (0.96, 0.90, 0.78), (0.99, 0.95, 0.86), scale=4.0, bump=0.05)
M_TEAL = mat("M_HotelTeal", (0.0, 0.48, 0.52), rough=0.4, coat=0.2)
M_WIN = mat("M_Window", (0.02, 0.06, 0.10), rough=0.05, metal=0.3)
M_RAIL = mat("M_Rail", (0.95, 0.95, 0.95), rough=0.3)
M_ROOF = mat("M_RoofTiles", (0.70, 0.18, 0.06), rough=0.6)
M_ROOFTOP = noise_mat("M_RoofTop", (0.62, 0.20, 0.07), (0.72, 0.28, 0.10), scale=1.5, bump=0.1)
M_SIGN = mat("M_SignBoard", (0.98, 0.97, 0.94), rough=0.5)
HX, HY0, HY1, HW, FL = 28.0, 24.0, 36.0, 20.0, 3.4
hotel = []
base = G(HX, HY0) - 0.6
hotel.append(box("Hotel_Plinth", (HW + 1.0, HY1 - HY0 + 1.0, 1.2), (HX, (HY0 + HY1) / 2, base + 0.6), M_PLASTER, bevel=0.02))
z0 = base + 1.2
for k in range(3):
    zb = z0 + k * FL
    hotel.append(box("Hotel_Slab%d" % k, (HW + 0.6, HY1 - HY0 + 0.6, 0.25), (HX, (HY0 + HY1) / 2, zb + 0.125), M_PLASTER, bevel=0.02))
    # walls: back and sides solid, front with window openings (piers between)
    hotel.append(box("Hotel_Back%d" % k, (HW, 0.3, FL - 0.25), (HX, HY1 - 0.15, zb + 0.25 + (FL - 0.25) / 2), M_PLASTER, bevel=0.0))
    for sx in (-1, 1):
        hotel.append(box("Hotel_Side%d%d" % (k, sx), (0.3, HY1 - HY0, FL - 0.25), (HX + sx * (HW / 2 - 0.15), (HY0 + HY1) / 2, zb + 0.25 + (FL - 0.25) / 2), M_PLASTER, bevel=0.0))
    nbay = 6; bw = HW / nbay
    for i in range(nbay + 1):
        xp = HX - HW / 2 + i * bw
        hotel.append(box("Hotel_Pier%d%d" % (k, i), (0.5, 0.35, FL - 0.25), (xp, HY0 + 1.2, zb + 0.25 + (FL - 0.25) / 2), M_PLASTER, bevel=0.01))
    for i in range(nbay):
        xc = HX - HW / 2 + (i + 0.5) * bw
        hotel.append(box("Hotel_Glass%d%d" % (k, i), (bw - 0.5, 0.06, FL - 0.25), (xc, HY0 + 1.3, zb + 0.25 + (FL - 0.25) / 2), M_WIN, bevel=0.0))
        hotel.append(box("Hotel_Frame%d%d" % (k, i), (0.06, 0.1, FL - 0.25), (xc, HY0 + 1.25, zb + 0.25 + (FL - 0.25) / 2), M_RAIL, bevel=0.0))
        if k > 0:      # balconies with teal fronts and white rails
            hotel.append(box("Hotel_Balc%d%d" % (k, i), (bw - 0.6, 1.2, 0.18), (xc, HY0 + 0.4, zb + 0.09), M_PLASTER, bevel=0.02))
            hotel.append(box("Hotel_BalcFront%d%d" % (k, i), (bw - 0.6, 0.08, 0.5), (xc, HY0 - 0.16, zb + 0.43), M_TEAL, bevel=0.01))
            hotel.append(box("Hotel_Rail%d%d" % (k, i), (bw - 0.6, 0.06, 0.06), (xc, HY0 - 0.16, zb + 1.05), M_RAIL, bevel=0.0))
            for j in range(6):
                hotel.append(box("Hotel_Bar%d%d%d" % (k, i, j), (0.04, 0.04, 0.4), (xc - (bw - 0.8) / 2 + j * (bw - 0.8) / 5, HY0 - 0.16, zb + 0.84), M_RAIL, bevel=0.0))
ztop = z0 + 3 * FL
hotel.append(box("Hotel_Roof", (HW + 0.8, HY1 - HY0 + 0.8, 0.3), (HX, (HY0 + HY1) / 2, ztop + 0.15), M_ROOFTOP, bevel=0.03))
hotel.append(box("Hotel_Parapet", (HW + 0.8, 0.25, 0.9), (HX, HY0 - 0.25, ztop + 0.75), M_TEAL, bevel=0.03))
# a pitched tile roof over the stair tower at the side
hotel.append(box("Hotel_Tower", (4.0, 4.0, 3.0), (HX + HW / 2 - 2.5, HY1 - 3.0, ztop + 1.8), M_PLASTER, bevel=0.03))
bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=3.4, depth=1.8, location=(HX + HW / 2 - 2.5, HY1 - 3.0, ztop + 4.2), rotation=(0, 0, math.radians(45)))
tr = bpy.context.active_object; tr.name = "Hotel_TowerRoof"; tr.data.materials.append(M_ROOF); hotel.append(tr)
# the sign: a white board on two posts on the roof, the logo on its front (faces the sea, -Y)
SIGN_W, SIGN_H = 8.0, 3.4
SZ = ztop + 1.4 + SIGN_H / 2
hotel.append(box("Hotel_SignBoard", (SIGN_W + 0.3, 0.2, SIGN_H + 0.3), (HX - 3.0, HY0 + 0.6, SZ), M_TEAL, bevel=0.03))
for sx in (-1, 1):
    hotel.append(box("Hotel_SignPost%d" % sx, (0.2, 0.2, 1.6), (HX - 3.0 + sx * SIGN_W * 0.35, HY0 + 0.8, ztop + 0.9), M_RAIL, bevel=0.0))
bpy.ops.mesh.primitive_plane_add(size=1, location=(HX - 3.0, HY0 + 0.49, SZ), rotation=(math.radians(90), 0, 0))
LOGO1 = bpy.context.active_object; LOGO1.name = "Hotel_Logo"; LOGO1.scale = (SIGN_W, SIGN_H, 1); bpy.ops.object.transform_apply(scale=True)
limg = bpy.data.images.load("/home/user/Muhammed/blender/assets/brand/DaKrasFilms_logo_dark.png"); limg.name = "DaKrasFilms_logo_dark"
ml = mat("M_Logo", (1, 1, 1), rough=0.5); nt_ = ml.node_tree; ti = nt_.nodes.new("ShaderNodeTexImage"); ti.image = limg
mxl = nt_.nodes.new("ShaderNodeMix"); mxl.data_type = 'RGBA'; mxl.inputs["A"].default_value = (0.98, 0.97, 0.94, 1)
nt_.links.new(ti.outputs["Alpha"], mxl.inputs["Factor"]); nt_.links.new(ti.outputs["Color"], mxl.inputs["B"])
nt_.links.new(mxl.outputs["Result"], nt_.nodes["Principled BSDF"].inputs["Base Color"])
LOGO1.data.materials.append(ml); hotel.append(LOGO1)
# UV of the plane: the logo fills the board with a margin, keeping its aspect (967x414)
uv = LOGO1.data.uv_layers.active.data
asp_img = 967 / 414; asp_b = SIGN_W / SIGN_H
for lp in LOGO1.data.loops:
    u_, v_ = uv[lp.index].uv
    su = asp_b / asp_img * 1.12; sv = 1.12
    uv[lp.index].uv = ((u_ - 0.5) * su + 0.5, (v_ - 0.5) * sv + 0.5)
ti.extension = 'CLIP'
# an outside staircase on the right side (how the family could get up; also scale reference)
for i in range(16):
    hotel.append(box("Hotel_Step%d" % i, (1.4, 0.32, 0.2), (HX + HW / 2 + 0.9, HY0 + 1.0 + i * 0.32, base + 1.3 + i * 0.21), M_PLASTER, bevel=0.0))
for o in hotel: to_col(o, C_SET)

# ================================================================== the town (each house its own object: they get swept away)
HOUSES = []
spots = []
for j, y in enumerate((62, 88, 114, 142, 170, 200, 228)):
    for i, x in enumerate((-110, -84, -58, -36, -18, 18, 38, 62, 88, 114)):
        if (x, y) in ((38, 170), (62, 170), (38, 200), (62, 200), (18, 170), (18, 200)): continue          # the mosque square
        if math.hypot(x - HILL[0], y - HILL[1]) < 60: continue                          # the hill stays open
        spots.append((x + random.uniform(-3, 3), y + random.uniform(-3, 3)))
kinds = ["house", "house2", "b_slum1"]
for n, (x, y) in enumerate(spots):
    k = kinds[n % 3]
    o = place(k, "House%02d" % n, (x, y), rz=random.choice((0, 1.5708, 3.1416, -1.5708)) + random.uniform(-0.1, 0.1),
              s=random.uniform(0.9, 1.1), coll=C_TOWN, sink=0.1)
    HOUSES.append(o)
MOSQUE = place("mosque", "Mosque", (49.0, 185.0), rz=math.radians(180), coll=C_TOWN, sink=0.2)
CARS = [place("car", "Car%d" % i, (x, y), rz=r_, coll=C_TOWN) for i, (x, y, r_) in enumerate([(-30, 48, 0.1), (8, 75, 3.0), (-4, 130, 0.0), (6, 160, 3.1)])]
for i, (x, y) in enumerate([(-20, 50), (24, 52), (-45, 75), (100, 78), (-95, 150), (78, 130), (-20, 240), (120, 240), (-120, 100), (10, 260)]):
    place("banana", "Banana%d" % i, (x, y), rz=random.uniform(0, 6.28), s=random.uniform(0.8, 1.1), coll=C_TOWN)
# road: a strip of darker packed earth up the middle of the town
M_ROAD = mat("M_Road", (0.3, 0.3, 0.3), rough=0.8)          # CC0 Poly Haven asphalt
_nt = M_ROAD.node_tree; _ti = _nt.nodes.new("ShaderNodeTexImage"); _ti.image = bpy.data.images.load(os.path.join(PKG, "assets", "tex", "asphalt_02_diff_1k.jpg"))
_tc = _nt.nodes.new("ShaderNodeTexCoord"); _mp = _nt.nodes.new("ShaderNodeMapping"); _mp.inputs["Scale"].default_value = (0.3, 0.3, 0.3)
_nt.links.new(_tc.outputs["Object"], _mp.inputs["Vector"]); _nt.links.new(_mp.outputs["Vector"], _ti.inputs["Vector"])
_nt.links.new(_ti.outputs["Color"], _nt.nodes["Principled BSDF"].inputs["Base Color"])
road = grid_mesh("Road", axis(-5, 5, [(0, 0, 1.0)]), axis(40, 400, [(0, 0, 2.0)]), lambda x, y: G(x, y) + 0.03)
road.data.materials.append(M_ROAD); to_col(road, C_TOWN)
# rubble fields: under the ground until the flood hides their rise (keyed in 02); random piles where the houses stood
RUBBLE = []
rk = ["rubble_roof", "rubble_brick", "rubble_wood"]
for n, (x, y) in enumerate(spots):
    for m_ in range(4):
        k = rk[(n + m_) % 3]
        o = place(k, "Rubble%02d_%d" % (n, m_), (x + random.uniform(-7, 7), y + random.uniform(-7, 7)),
                  rz=random.uniform(0, 6.28), s=random.uniform(1.3, 2.0), coll=C_TOWN)
        o["z_final"] = o.location.z - 0.05; RUBBLE.append(o)
for n in range(18):     # more debris along the beach front and the road
    x, y = random.uniform(-90, 110), random.uniform(28, 58)
    o = place(rk[n % 3], "RubbleB%02d" % n, (x, y), rz=random.uniform(0, 6.28), s=random.uniform(0.8, 1.3), coll=C_TOWN)
    o["z_final"] = o.location.z - 0.05; RUBBLE.append(o)

# ================================================================== the earthquake cut-away (under the sea at y=-1330..-1070)
M_SED = noise_mat("M_Sediment", (0.92, 0.62, 0.22), (0.98, 0.74, 0.32), scale=0.08, bump=0.1)
M_OCRUST = noise_mat("M_OceanCrust", (0.42, 0.06, 0.05), (0.55, 0.10, 0.06), scale=0.05, bump=0.1)
M_CONT1 = noise_mat("M_ContA", (0.20, 0.42, 0.08), (0.30, 0.52, 0.10), scale=0.05, bump=0.1)
M_CONT2 = noise_mat("M_ContB", (0.62, 0.36, 0.08), (0.72, 0.44, 0.10), scale=0.05, bump=0.1)
M_MANTLE = mat("M_Mantle", (0.95, 0.30, 0.03), rough=0.6, emit=((1.0, 0.35, 0.05), 0.6))
YT = -250.0                    # the trench
def prism(name, poly_yz, x0, x1, material):
    """extrude a (y,z) polygon along x from x0 to x1 (the cut face is at x0)"""
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    a_ = [bm.verts.new((x0, y, z)) for y, z in poly_yz]; b_ = [bm.verts.new((x1, y, z)) for y, z in poly_yz]
    bm.faces.new(a_[::-1]); bm.faces.new(b_)
    n = len(poly_yz)
    for i in range(n):
        bm.faces.new((a_[i], a_[(i + 1) % n], b_[(i + 1) % n], b_[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:]); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); C_SEC.objects.link(o); me.materials.append(material); return o
def sfl(y): return G(0, y)
Y0, Y1 = SECTION_Y[0] - 40, SECTION_Y[1] + 40
dip = math.tan(math.radians(22))
def slab_top(y): return sfl(y) if y <= YT else sfl(YT) - 4.0 - (y - YT) * dip
ys_ = [Y0 + i * (Y1 - Y0) / 40 for i in range(41)]
# oceanic plate: 26 m thick, diving under the continent past the trench
top = [(y, slab_top(y)) for y in ys_]
bot = [(y, slab_top(y) - 26.0) for y in ys_[::-1]]
OPLATE = prism("SEC_OceanPlate", top + bot, 0.0, 160.0, M_OCRUST)
SED = prism("SEC_Sediment", [(y, slab_top(y) + 1.6) for y in ys_ if y <= YT] + [(y, slab_top(y)) for y in ys_ if y <= YT][::-1], 0.0, 160.0, M_SED)
# continent: everything above the slab, landward of the trench; two coloured layers; its seaward tip is a separate wedge
yc = [y for y in ys_ if y >= YT + 6.5]
CONT_LO = prism("SEC_ContLow", [(y, slab_top(y) + 0.3) for y in yc] + [(y, sfl(y) - 14.0) for y in yc[::-1]], 0.0, 160.0, M_CONT2)
CONT_HI = prism("SEC_ContHigh", [(y, sfl(y) - 14.0) for y in yc] + [(y, sfl(y)) for y in yc[::-1]], 0.0, 160.0, M_CONT1)
wy0, wy1 = YT + 1.0, YT + 26.0
WEDGE = prism("SEC_Wedge", [(wy0, sfl(wy0) - 1.0), (wy1, slab_top(wy1) + 0.3), (wy1, sfl(wy1) + 0.0), (wy0 + 2, sfl(wy0) + 0.3)], 0.0, 160.0, M_CONT1)
# the wedge pivots at its landward bottom corner (the snap-up in 02)
piv = Vector((0.0, wy1, slab_top(wy1)))
WEDGE.data.transform(Matrix.Translation(-piv)); WEDGE.location = piv
MANTLE = prism("SEC_Mantle", [(Y0, -170.0), (Y1, -170.0)] + [(y, slab_top(y) - 26.5) for y in ys_[::-1]], 0.0, 160.0, M_MANTLE)
# the focus: a glowing point where the plates lock, and the shock ring (both keyed in 02)
FOCUS_P = Vector((-0.3, YT + 18.0, slab_top(YT + 18.0) + 0.5))
bpy.ops.mesh.primitive_ico_sphere_add(radius=1.0, subdivisions=3, location=FOCUS_P)
FOCUS = bpy.context.active_object; FOCUS.name = "SEC_Focus"; FOCUS.data.materials.append(mat("M_Focus", (1.0, 0.9, 0.2), emit=((1.0, 0.85, 0.15), 30.0)))
bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.06, location=FOCUS_P, rotation=(0, math.radians(90), 0))
RING = bpy.context.active_object; RING.name = "SEC_Ring"; RING.data.materials.append(mat("M_Ring", (1.0, 0.95, 0.5), emit=((1.0, 0.9, 0.4), 8.0)))
for o in (FOCUS, RING): to_col(o, C_SEC)
FOCUS.scale = (0.01,) * 3; RING.scale = (0.01,) * 3
# a cyan 'water column' glow wall behind the cut so the dive reads as water (not sky): a gradient plane far behind
bpy.ops.mesh.primitive_plane_add(size=1, location=(400.0, -250.0, -85.0), rotation=(0, math.radians(90), 0))
BACK = bpy.context.active_object; BACK.name = "SEC_WaterBack"; BACK.scale = (150, 700, 1)
mb = bpy.data.materials.new("M_WaterBack"); mb.use_nodes = True; ntb = mb.node_tree
for n_ in list(ntb.nodes):
    if n_.type != 'OUTPUT_MATERIAL': ntb.nodes.remove(n_)
gb = ntb.nodes.new("ShaderNodeTexCoord"); sb = ntb.nodes.new("ShaderNodeSeparateXYZ"); ntb.links.new(gb.outputs["Generated"], sb.inputs[0])
rb = ntb.nodes.new("ShaderNodeValToRGB"); rb.color_ramp.elements[0].color = (0.15, 0.70, 0.90, 1); rb.color_ramp.elements[1].color = (0.0, 0.08, 0.30, 1)
ntb.links.new(sb.outputs["X"], rb.inputs["Fac"])
eb_ = ntb.nodes.new("ShaderNodeEmission"); eb_.inputs["Strength"].default_value = 1.0; ntb.links.new(rb.outputs["Color"], eb_.inputs["Color"])
ntb.links.new(eb_.outputs[0], ntb.nodes["Material Output"].inputs["Surface"])
BACK.data.materials.append(mb); to_col(BACK, C_SEC)
BACK.visible_shadow = False; BACK.visible_diffuse = False; BACK.visible_glossy = False
# lights for the cut-away only (light linking would be nicer; an area light right in front of the cut face is enough)
la = bpy.data.lights.new("SEC_Light", 'AREA'); la.energy = 250000; la.shape = 'RECTANGLE'; la.size = 40; la.size_y = 160; la.color = (1.0, 0.96, 0.9)
LA = bpy.data.objects.new("SEC_Light", la); C_SEC.objects.link(LA); LA.location = (-90.0, -250.0, -14.0)
LA.rotation_euler = (0, math.radians(-90), 0); LA.location.z = -28.0
LA.visible_camera = False; LA.visible_glossy = False; LA.visible_diffuse = True

# ================================================================== the family: ONE model each, real CC0 MakeHuman clothes and hair
TEX = os.path.join(PKG, "assets", "tex")
def dress_texture(rig, key, png):
    cl = [c for c in rig.children if c.type == 'MESH' and key in c.name][0]
    img = bpy.data.images.load(os.path.join(TEX, png)); img.name = png[:-4]
    for m_ in cl.data.materials:
        for nd in m_.node_tree.nodes:
            if nd.type == 'TEX_IMAGE' and nd.image and "diffuse" in nd.image.name.lower(): nd.image = img
            if nd.type == 'NORMAL_MAP': nd.inputs["Strength"].default_value = 0.5
    return cl
def finish(rig, body, hair_tint, skin_tint):
    eye_fix(rig)
    for c in rig.children:
        if c.type != 'MESH': continue
        n = c.name.lower()
        if any(k in n for k in ("short", "long", "braid", "bob", "pony", "eyebrow")):
            for m_ in c.data.materials: tint(m_, hair_tint)
        if "teeth" in n:
            for m_ in c.data.materials: tint(m_, (1.4, 1.35, 1.3))
        if any(k in n for k in ("suit", "shoes")):           # solid garments: real thickness, no open paper edges
            so = c.modifiers.new("solid", 'SOLIDIFY'); so.thickness = 0.003; so.offset = 1.0; so.use_rim = True
            i = c.modifiers.find("solid")
            while i > c.modifiers.find("Armature") + 1:
                c.modifiers.move(i, i - 1); i -= 1
    for m_ in body.data.materials: tint(m_, skin_tint)
    for c in rig.children: to_col(c, C_PEOPLE)
    to_col(rig, C_PEOPLE)
EAS = {"asian": 0.80, "caucasian": 0.05, "african": 0.15}
DAD, DADB = human("Dad", 1.0, 0.52, EAS, "short02/short02.mhclo", "young_asian_male/young_asian_male.mhmat", "eyebrow001/eyebrow001.mhclo",
                  height=0.62, weight=0.55, muscle=0.6, clothes=["male_casualsuit03/male_casualsuit03.mhclo", "shoes02/shoes02.mhclo"])
MOM, MOMB = human("Mom", 0.0, 0.48, EAS, "long01/long01.mhclo", "young_asian_female/young_asian_female.mhmat", "eyebrow010/eyebrow010.mhclo",
                  height=0.45, weight=0.5, muscle=0.4, clothes=["female_casualsuit01/female_casualsuit01.mhclo", "shoes01/shoes01.mhclo"])
BOY, BOYB = human("Boy", 1.0, 0.17, EAS, "short04/short04.mhclo", "young_asian_male/young_asian_male.mhmat", "eyebrow001/eyebrow001.mhclo",
                  height=0.5, weight=0.45, muscle=0.5, clothes=["male_casualsuit04/male_casualsuit04.mhclo", "shoes02/shoes02.mhclo"])
GIRL, GIRLB = human("Girl", 0.0, 0.14, EAS, "braid01/braid01.mhclo", "young_asian_female/young_asian_female.mhmat", "eyebrow010/eyebrow010.mhclo",
                    height=0.5, weight=0.45, muscle=0.45, clothes=["female_casualsuit02/female_casualsuit02.mhclo", "shoes01/shoes01.mhclo"])
eye_group_fix()
dress_texture(MOM, "casualsuit01", "mom_tee_diffuse.png"); dress_texture(GIRL, "casualsuit02", "girl_tee_diffuse.png")
dress_texture(BOY, "casualsuit04", "boy_tee_diffuse.png")
for r_, b_, sk in ((DAD, DADB, (0.95, 0.72, 0.52)), (MOM, MOMB, (1.0, 0.78, 0.58)), (BOY, BOYB, (0.98, 0.74, 0.54)), (GIRL, GIRLB, (1.0, 0.78, 0.58))):
    finish(r_, b_, (0.16, 0.11, 0.08), sk)
for m_ in [m for c in DAD.children if c.type == 'MESH' and "casualsuit03" in c.name for m in c.data.materials]:
    tint(m_, (1.2, 0.9, 0.9))         # the striped shirt a deeper red
# the eyes: clear cornea, dark brown irises (no milky dead eyes)
EG = bpy.data.node_groups.get("EnhancedEye")
for n in (EG.nodes if EG else []):
    if n.type == 'MATH' and abs(n.inputs[1].default_value - 0.92) < 1e-4: n.inputs[1].default_value = 0.96
for rig in (DAD, MOM, BOY, GIRL):
    for m_ in [m for c in rig.children if c.type == 'MESH' and "high-poly" in c.name for m in c.data.materials]:
        for n in m_.node_tree.nodes:
            if n.type == 'GROUP' and "IrisMajorColor" in n.inputs:
                n.inputs["IrisMajorColor"].default_value = (0.10, 0.05, 0.02, 1); n.inputs["IrisMinorColor"].default_value = (0.04, 0.02, 0.01, 1)

# ================================================================== sun + render settings
sd = bpy.data.lights.new("Sun", 'SUN'); sd.energy = 4.5; sd.angle = math.radians(1.5); sd.color = (1.0, 0.95, 0.86)
SUN = bpy.data.objects.new("Sun", sd); C_SET.objects.link(SUN); SUN.rotation_euler = (math.radians(42), 0, math.radians(200))
r = sc.render; r.engine = 'CYCLES'; cy = sc.cycles
cy.samples = 64; cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.04
cy.use_denoising = True; cy.denoiser = 'OPENIMAGEDENOISE'
cy.max_bounces = 6; cy.diffuse_bounces = 3; cy.glossy_bounces = 3; cy.transmission_bounces = 6; cy.transparent_max_bounces = 12
cy.caustics_reflective = cy.caustics_refractive = False
r.use_persistent_data = True; r.use_simplify = True; r.simplify_subdivision_render = 2
cy.texture_limit_render = '2048'
r.use_motion_blur = False
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Punchy'
sc.view_settings.exposure = 0.0
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SAVED", OUT)
