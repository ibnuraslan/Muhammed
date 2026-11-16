"""YardTrench sets. blender -b work/chars.blend -P 02_sets.py -- work/sets.blend
Yard (origin): house at +Y facing the yard, wooden fences, one worn path along -Y from the porch to the back fence.
The ground is ONE mesh whose groove is driven by shape keys (Rut -> Groove -> Trench) keyed in 03_anim; its material and the
grass-blade scatter read the same keyed values (bare / dry / wet / crush), so the time-lapse is one clean continuous change.
Section block (x=100): explainer cut-away of the lawn and soil clods (S06)."""
import sys, os
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib.py")).read())
out = sys.argv[sys.argv.index("--") + 1]
random.seed(37)
LIB = coll("LIB"); LIB.hide_render = True; LIB.hide_viewport = True
YARD = coll("Yard"); SECT = coll("Section"); FX = coll("FX")

# ------------------------------------------------------------------ world, look
w = bpy.data.worlds.new("Sky"); sc.world = w; w.use_nodes = True; nt = w.node_tree
env = nt.nodes.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(os.path.join(PH, "hdri", "kloofendal_48d_partly_cloudy_puresky_2k.hdr"))
mpw = nt.nodes.new("ShaderNodeMapping"); tcw = nt.nodes.new("ShaderNodeTexCoord"); nt.links.new(tcw.outputs["Generated"], mpw.inputs[0]); nt.links.new(mpw.outputs[0], env.inputs[0])
mpw.inputs["Rotation"].default_value = (0, 0, R_(200))
bg = nt.nodes["Background"]; nt.links.new(env.outputs[0], bg.inputs[0]); bg.inputs[1].default_value = 1.0; bg.name = "SkyBG"
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 3.4; sun.data.angle = R_(3); sun.rotation_euler = (R_(42), 0, R_(-28)); sun.data.color = (1.0, 0.97, 0.92)
sc.render.engine = 'CYCLES'; sc.render.resolution_x, sc.render.resolution_y = 1080, 1920; sc.render.fps = 60
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Punchy'

# ------------------------------------------------------------------ the path (shared with 03_anim)
def path_x(y): return 0.55 * math.sin(y * 0.22) + 0.25 * math.sin(y * 0.07 + 1.0)
Y_PORCH, Y_BACK = 9.0, -12.5          # worn line runs from the porch steps to the back fence

def taper(y, a=Y_BACK + 0.6, b=Y_PORCH - 0.6, r=1.6):
    return smooth((y - a) / r) * smooth((b - y) / r)

def hsh(i, j):                          # deterministic 0..1 noise
    return (math.sin(i * 12.9898 + j * 78.233) * 43758.5453) % 1.0

def vnoise(x, y, s):
    """smooth value noise"""
    xi, yi = math.floor(x / s), math.floor(y / s); fx, fy = x / s - xi, y / s - yi
    fx, fy = smooth(fx), smooth(fy)
    a, b, c, d = hsh(xi, yi), hsh(xi + 1, yi), hsh(xi, yi + 1), hsh(xi + 1, yi + 1)
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy

def prof(t, edge):                      # 1 in the middle, 0 outside; edge = width of the wall transition (fraction)
    return 1.0 - smooth((t - (1 - edge)) / edge) if t < 1 else 0.0

# groove stages: (half width, depth, wall fraction)
STAGES = {"Rut": (0.42, 0.035, 0.6), "Groove": (0.5, 0.30, 0.45), "Trench": (0.72, 1.95, 0.16)}

# ------------------------------------------------------------------ yard ground: non-uniform grid, fine across the path band
XL, XR, YF, YB = -13.0, 13.0, 12.5, -14.5
def xs_cols():
    xs = []; x = XL
    while x < XR:
        xs.append(x); band = abs(x) < 2.4
        x += 0.045 if band else (0.25 if abs(x) < 6 else 0.6)
    xs.append(XR); return xs
XS = xs_cols(); YS = []
y = YB
while y < YF:
    YS.append(y); y += 0.07 if (Y_BACK - 1.5 < y < Y_PORCH + 1.5) else 0.4
YS.append(YF)
verts = [(x, y, 0.0) for y in YS for x in XS]; nx = len(XS)
faces = [(j * nx + i, j * nx + i + 1, (j + 1) * nx + i + 1, (j + 1) * nx + i) for j in range(len(YS) - 1) for i in range(nx - 1)]
me = bpy.data.meshes.new("Ground"); me.from_pydata(verts, [], faces); me.update()
G = bpy.data.objects.new("Ground", me); YARD.objects.link(G)
for p in me.polygons: p.use_smooth = True
# per-vertex attributes: pd = distance across the path (m), pu = position along the path, tp = taper
pd = me.attributes.new("pd", 'FLOAT', 'POINT'); tp = me.attributes.new("tp", 'FLOAT', 'POINT')
for i, (x, y, _) in enumerate(verts):
    pd.data[i].value = abs(x - path_x(y)); tp.data[i].value = taper(y)
G.shape_key_add(name="Basis")
for nm, (hw, dep, ed) in STAGES.items():
    k = G.shape_key_add(name=nm, from_mix=False)
    for i, (x, y, _) in enumerate(verts):
        v = x - path_x(y); t = abs(v) / hw
        z = -dep * prof(t, ed) * taper(y)
        if nm == "Rut":
            z += 0.02 * (vnoise(x, y, 0.3) - 0.5) * prof(t, 0.9) * taper(y)        # little hollows -> puddles
        else:
            z += 0.03 * (vnoise(x, y, 0.5) - 0.5) * prof(t * 0.9, 0.5) * taper(y)    # uneven floor / walls
        if nm == "Trench":                                                            # wall bulges
            z_rim = 1 - prof(t, ed)
            k.data[i].co = (x + 0.03 * (vnoise(x * 3, y, 0.6) - 0.5) * (1 - z_rim) , y, z)
        else:
            k.data[i].co = (x, y, z)
    k.value = 0.0

# ------------------------------------------------------------------ ground material: grass -> compacted strip -> cracked -> wet
def tex_node(nt, path, coords_out, scale, nc=False, box=True):
    N = nt.nodes; mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (scale, scale, scale)
    nt.links.new(coords_out, mp.inputs[0])
    t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(path, check_existing=True)
    if box: t.projection = 'BOX'; t.projection_blend = 0.25
    if nc: t.image.colorspace_settings.name = "Non-Color"
    nt.links.new(mp.outputs[0], t.inputs[0]); return t

def phf(folder, key):
    d = os.path.join(PH, folder, "textures"); return os.path.join(d, [f for f in os.listdir(d) if key in f][0])

def tint(nt, sock, rgb, k=1.0):
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs[0].default_value = k
    nt.links.new(sock, mx.inputs[6]); mx.inputs[7].default_value = (*rgb, 1); return mx.outputs[2]

def mixc(nt, fac, a, b):
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'
    nt.links.new(fac, mx.inputs[0]) if not isinstance(fac, float) else None
    if isinstance(fac, float): mx.inputs[0].default_value = fac
    for s_, v in ((6, a), (7, b)):
        if isinstance(v, tuple): mx.inputs[s_].default_value = (*v, 1)
        else: nt.links.new(v, mx.inputs[s_])
    return mx.outputs[2]

def mrange(nt, src, a, b, c=0.0, d=1.0, smoothst=True):
    m = nt.nodes.new("ShaderNodeMapRange"); m.interpolation_type = 'SMOOTHSTEP' if smoothst else 'LINEAR'
    nt.links.new(src, m.inputs[0]); m.inputs[1].default_value = a; m.inputs[2].default_value = b; m.inputs[3].default_value = c; m.inputs[4].default_value = d
    return m

def value_node(nt, name, v):
    n = nt.nodes.new("ShaderNodeValue"); n.name = name; n.label = name; n.outputs[0].default_value = v; return n

M_G = bpy.data.materials.new("GroundMat"); M_G.use_nodes = True; nt = M_G.node_tree; N = nt.nodes; L = nt.links
P = N["Principled BSDF"]; tc = N.new("ShaderNodeTexCoord")
grass = tex_node(nt, phf("leafy_grass", "diff"), tc.outputs["Object"], 0.45)
grass_c = tint(nt, grass.outputs[0], (0.62, 1.05, 0.42))
mud = tex_node(nt, phf("brown_mud_dry", "diff"), tc.outputs["Object"], 0.5)
mud_c = tint(nt, mud.outputs[0], (1.15, 0.95, 0.75))
crk = tex_node(nt, phf("mud_cracked_dry_03", "diff"), tc.outputs["Object"], 0.55)
crk_c = tint(nt, crk.outputs[0], (1.25, 1.02, 0.78))
wall = tex_node(nt, phf("excavated_soil_wall", "diff"), tc.outputs["Object"], 0.6)
wall_c = tint(nt, wall.outputs[0], (1.1, 0.9, 0.72))
attr = N.new("ShaderNodeAttribute"); attr.attribute_name = "pd"
atp = N.new("ShaderNodeAttribute"); atp.attribute_name = "tp"
V_bare = value_node(nt, "bare", 0.0)      # 0 = all lawn, 1 = full-width bare strip
V_dry = value_node(nt, "dry", 0.0)        # 0 = fresh compacted mud, 1 = cracked hard crust
V_wet = value_node(nt, "wet", 0.0)        # darkening in the rain
V_hw = value_node(nt, "halfw", 0.42)      # half width of the bare strip (follows the groove stage)
# bare mask = bare * tp * (pd < halfw * bare-ish)
mul_w = N.new("ShaderNodeMath"); mul_w.operation = 'MULTIPLY'; L.new(V_hw.outputs[0], mul_w.inputs[0]); L.new(V_bare.outputs[0], mul_w.inputs[1])
noise = N.new("ShaderNodeTexNoise"); noise.inputs["Scale"].default_value = 1.6; L.new(tc.outputs["Object"], noise.inputs["Vector"])
nz = N.new("ShaderNodeMath"); nz.operation = 'MULTIPLY_ADD'; L.new(noise.outputs[0], nz.inputs[0]); nz.inputs[1].default_value = 0.22; nz.inputs[2].default_value = -0.11
pdn = N.new("ShaderNodeMath"); pdn.operation = 'ADD'; L.new(attr.outputs["Fac"], pdn.inputs[0]); L.new(nz.outputs[0], pdn.inputs[1])
diff = N.new("ShaderNodeMath"); diff.operation = 'SUBTRACT'; L.new(pdn.outputs[0], diff.inputs[0]); L.new(mul_w.outputs[0], diff.inputs[1])
bm = mrange(nt, diff.outputs[0], -0.06, 0.06, 1.0, 0.0)
bm2 = N.new("ShaderNodeMath"); bm2.operation = 'MULTIPLY'; L.new(bm.outputs[0], bm2.inputs[0]); L.new(atp.outputs["Fac"], bm2.inputs[1])
bm3 = N.new("ShaderNodeMath"); bm3.operation = 'MULTIPLY'; bm3.use_clamp = True; L.new(bm2.outputs[0], bm3.inputs[0]); bm3.inputs[1].default_value = 1.6
bare_mask = bm3.outputs[0]
dirt = mixc(nt, V_dry.outputs[0], mud_c, crk_c)
# deep trench walls: soil wall texture where the surface is steep (geometry normal z small)
geo = N.new("ShaderNodeNewGeometry"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs["Normal"], sep.inputs[0])
steep = mrange(nt, sep.outputs["Z"], 0.55, 0.85, 1.0, 0.0)
dirt2 = mixc(nt, steep.outputs[0], dirt, wall_c)
col = mixc(nt, bare_mask, grass_c, dirt2)
wetd = N.new("ShaderNodeMath"); wetd.operation = 'MULTIPLY_ADD'; L.new(V_wet.outputs[0], wetd.inputs[0]); wetd.inputs[1].default_value = -0.35; wetd.inputs[2].default_value = 1.0
colw = N.new("ShaderNodeMix"); colw.data_type = 'RGBA'; colw.blend_type = 'MULTIPLY'; colw.inputs[0].default_value = 1
L.new(col, colw.inputs[6]); cw = N.new("ShaderNodeCombineColor")
for i in range(3): L.new(wetd.outputs[0], cw.inputs[i])
L.new(cw.outputs[0], colw.inputs[7]); L.new(colw.outputs[2], P.inputs["Base Color"])
rgh = N.new("ShaderNodeMath"); rgh.operation = 'MULTIPLY_ADD'; L.new(V_wet.outputs[0], rgh.inputs[0]); rgh.inputs[1].default_value = -0.3; rgh.inputs[2].default_value = 0.85
L.new(rgh.outputs[0], P.inputs["Roughness"]); P.inputs["Specular IOR Level"].default_value = 0.25
# light bump from the crack texture on the strip
bw = N.new("ShaderNodeRGBToBW"); L.new(crk.outputs[0], bw.inputs[0])
bmp = N.new("ShaderNodeBump"); bmp.inputs["Strength"].default_value = 0.35; bmp.inputs["Distance"].default_value = 0.01
bmh = N.new("ShaderNodeMath"); bmh.operation = 'MULTIPLY'; L.new(bw.outputs[0], bmh.inputs[0]); L.new(bare_mask, bmh.inputs[1])
bmd = N.new("ShaderNodeMath"); bmd.operation = 'MULTIPLY'; L.new(bmh.outputs[0], bmd.inputs[0]); L.new(V_dry.outputs[0], bmd.inputs[1])
L.new(bmd.outputs[0], bmp.inputs["Height"]); L.new(bmp.outputs[0], P.inputs["Normal"])
G.data.materials.append(M_G)

# ------------------------------------------------------------------ grass blades (GN scatter on the evaluated ground)
def blade_mesh():
    vs, fs = [], []
    segs = 4
    for i in range(segs + 1):
        t = i / segs; wdt = 0.0032 * (1 - t) + 0.0004; bend = 0.018 * t * t
        vs += [(-wdt, bend, 0.075 * t), (wdt, bend, 0.075 * t)]
    for i in range(segs): fs.append((2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2))
    m = bpy.data.meshes.new("Blade"); m.from_pydata(vs, [], fs); m.update()
    for p in m.polygons: p.use_smooth = True
    o = bpy.data.objects.new("Blade", m); LIB.objects.link(o)
    bm_ = bpy.data.materials.new("BladeMat"); bm_.use_nodes = True; nb = bm_.node_tree; Pb = nb.nodes["Principled BSDF"]
    gz = nb.nodes.new("ShaderNodeTexCoord"); sz = nb.nodes.new("ShaderNodeSeparateXYZ"); nb.links.new(gz.outputs["Generated"], sz.inputs[0])
    rp = nb.nodes.new("ShaderNodeValToRGB"); nb.links.new(sz.outputs["Z"], rp.inputs[0])
    rp.color_ramp.elements[0].color = (0.05, 0.22, 0.03, 1); rp.color_ramp.elements[1].color = (0.32, 0.62, 0.12, 1)
    rnd = nb.nodes.new("ShaderNodeObjectInfo"); hm = nb.nodes.new("ShaderNodeMix"); hm.data_type = 'RGBA'; hm.blend_type = 'MULTIPLY'
    nb.links.new(rnd.outputs["Random"], hm.inputs[0]); nb.links.new(rp.outputs[0], hm.inputs[6]); hm.inputs[7].default_value = (0.75, 0.9, 0.6, 1)
    nb.links.new(hm.outputs[2], Pb.inputs["Base Color"]); Pb.inputs["Roughness"].default_value = 0.6
    Pb.inputs["Subsurface Weight"].default_value = 0.0
    o.data.materials.append(bm_)
    return o
BLADE = blade_mesh()

def grass_gn(name, target, density_far, density_near, near_box, foot_objs=()):
    """scatter blades on target's evaluated surface; reads target attributes pd/tp; inputs bare/halfw/crush keyed in 03_anim"""
    g = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    g.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    for nm, dv in (("bare", 0.0), ("halfw", 0.42), ("crush", 0.0)):
        s_ = g.interface.new_socket(nm, in_out='INPUT', socket_type='NodeSocketFloat'); s_.default_value = dv
    N = g.nodes; L = g.links
    gi = N.new("NodeGroupInput"); go = N.new("NodeGroupOutput")
    oi = N.new("GeometryNodeObjectInfo"); oi.inputs[0].default_value = target; oi.transform_space = 'RELATIVE'
    # density: near box gets dense blades
    pos = N.new("GeometryNodeInputPosition"); sp = N.new("ShaderNodeSeparateXYZ"); L.new(pos.outputs[0], sp.inputs[0])
    (x0, x1, y0, y1) = near_box
    def inrange(sock, a, b):
        c1 = N.new("FunctionNodeCompare"); c1.data_type = 'FLOAT'; c1.operation = 'GREATER_THAN'; L.new(sock, c1.inputs[0]); c1.inputs[1].default_value = a
        c2 = N.new("FunctionNodeCompare"); c2.data_type = 'FLOAT'; c2.operation = 'LESS_THAN'; L.new(sock, c2.inputs[0]); c2.inputs[1].default_value = b
        an = N.new("FunctionNodeBooleanMath"); an.operation = 'AND'; L.new(c1.outputs[0], an.inputs[0]); L.new(c2.outputs[0], an.inputs[1]); return an.outputs[0]
    nb = N.new("FunctionNodeBooleanMath"); nb.operation = 'AND'; L.new(inrange(sp.outputs["X"], x0, x1), nb.inputs[0]); L.new(inrange(sp.outputs["Y"], y0, y1), nb.inputs[1])
    sw = N.new("GeometryNodeSwitch"); sw.input_type = 'FLOAT'; L.new(nb.outputs[0], sw.inputs[0]); sw.inputs[1].default_value = density_far; sw.inputs[2].default_value = density_near
    dp = N.new("GeometryNodeDistributePointsOnFaces"); dp.distribute_method = 'RANDOM'
    L.new(oi.outputs["Geometry"], dp.inputs["Mesh"]); L.new(sw.outputs[0], dp.inputs["Density"]); dp.inputs["Seed"].default_value = 3
    # attributes at the points
    a_pd = N.new("GeometryNodeInputNamedAttribute"); a_pd.data_type = 'FLOAT'; a_pd.inputs[0].default_value = "pd"
    a_tp = N.new("GeometryNodeInputNamedAttribute"); a_tp.data_type = 'FLOAT'; a_tp.inputs[0].default_value = "tp"
    # captured on the mesh before distribution: Distribute interpolates point-domain attributes automatically
    # strip factor s = 1 inside the worn strip (pd < halfw) * tp
    m1 = N.new("ShaderNodeMath"); m1.operation = 'SUBTRACT'; L.new(a_pd.outputs[0], m1.inputs[0]); L.new(gi.outputs["halfw"], m1.inputs[1])
    s_in = N.new("ShaderNodeMapRange"); s_in.interpolation_type = 'SMOOTHSTEP'; L.new(m1.outputs[0], s_in.inputs[0])
    s_in.inputs[1].default_value = 0.08; s_in.inputs[2].default_value = -0.04; s_in.inputs[3].default_value = 0.0; s_in.inputs[4].default_value = 1.0
    sm = N.new("ShaderNodeMath"); sm.operation = 'MULTIPLY'; L.new(s_in.outputs[0], sm.inputs[0]); L.new(a_tp.outputs[0], sm.inputs[1])
    # scale = (1 - bare*s) * random(0.6..1.25)
    sb = N.new("ShaderNodeMath"); sb.operation = 'MULTIPLY'; L.new(sm.outputs[0], sb.inputs[0]); L.new(gi.outputs["bare"], sb.inputs[1])
    one = N.new("ShaderNodeMath"); one.operation = 'SUBTRACT'; one.inputs[0].default_value = 1.0; L.new(sb.outputs[0], one.inputs[1]); one.use_clamp = True
    rv = N.new("FunctionNodeRandomValue"); rv.data_type = 'FLOAT'; rv.inputs["Min"].default_value = 0.6; rv.inputs["Max"].default_value = 1.25
    scl = N.new("ShaderNodeMath"); scl.operation = 'MULTIPLY'; L.new(one.outputs[0], scl.inputs[0]); L.new(rv.outputs[0], scl.inputs[1])
    # tilt = max(crush*s, foot proximity) * 80 deg (+ small random lean)
    tl = N.new("ShaderNodeMath"); tl.operation = 'MULTIPLY'; L.new(sm.outputs[0], tl.inputs[0]); L.new(gi.outputs["crush"], tl.inputs[1])
    tilt = tl.outputs[0]
    for fo in foot_objs:
        fi = N.new("GeometryNodeObjectInfo"); fi.inputs[0].default_value = fo; fi.transform_space = 'RELATIVE'
        sub = N.new("ShaderNodeVectorMath"); sub.operation = 'SUBTRACT'; L.new(pos.outputs[0], sub.inputs[0]); L.new(fi.outputs["Location"], sub.inputs[1])
        sx = N.new("ShaderNodeSeparateXYZ"); L.new(sub.outputs[0], sx.inputs[0])
        # ellipse under the shoe sole: local foot frame ~ along Y (approximation: radius 0.13 m), and the sole is low (z diff < 0.12)
        cxy = N.new("ShaderNodeCombineXYZ"); L.new(sx.outputs["X"], cxy.inputs[0]); L.new(sx.outputs["Y"], cxy.inputs[1])
        ln = N.new("ShaderNodeVectorMath"); ln.operation = 'LENGTH'; L.new(cxy.outputs[0], ln.inputs[0])
        pr = N.new("ShaderNodeMapRange"); pr.interpolation_type = 'SMOOTHSTEP'; L.new(ln.outputs[1], pr.inputs[0])
        pr.inputs[1].default_value = 0.2; pr.inputs[2].default_value = 0.1; pr.inputs[3].default_value = 0.0; pr.inputs[4].default_value = 1.0
        hz = N.new("ShaderNodeMapRange"); L.new(sx.outputs["Z"], hz.inputs[0]); hz.interpolation_type = 'SMOOTHSTEP'
        hz.inputs[1].default_value = -0.2; hz.inputs[2].default_value = -0.08; hz.inputs[3].default_value = 0.0; hz.inputs[4].default_value = 1.0
        hm_ = N.new("ShaderNodeMath"); hm_.operation = 'MULTIPLY'; L.new(pr.outputs[0], hm_.inputs[0]); L.new(hz.outputs[0], hm_.inputs[1])
        mx_ = N.new("ShaderNodeMath"); mx_.operation = 'MAXIMUM'; L.new(tilt, mx_.inputs[0]); L.new(hm_.outputs[0], mx_.inputs[1]); tilt = mx_.outputs[0]
    tdeg = N.new("ShaderNodeMath"); tdeg.operation = 'MULTIPLY'; L.new(tilt, tdeg.inputs[0]); tdeg.inputs[1].default_value = R_(78)
    rl = N.new("FunctionNodeRandomValue"); rl.data_type = 'FLOAT'; rl.inputs["Min"].default_value = -0.25; rl.inputs["Max"].default_value = 0.25; rl.inputs["Seed"].default_value = 7
    tadd = N.new("ShaderNodeMath"); tadd.operation = 'ADD'; L.new(tdeg.outputs[0], tadd.inputs[0]); L.new(rl.outputs[0], tadd.inputs[1])
    rz = N.new("FunctionNodeRandomValue"); rz.data_type = 'FLOAT'; rz.inputs["Min"].default_value = 0; rz.inputs["Max"].default_value = 6.283; rz.inputs["Seed"].default_value = 11
    ce = N.new("ShaderNodeCombineXYZ"); L.new(tadd.outputs[0], ce.inputs[0]); L.new(rz.outputs[0], ce.inputs[2])
    bo = N.new("GeometryNodeObjectInfo"); bo.inputs[0].default_value = BLADE
    ip = N.new("GeometryNodeInstanceOnPoints"); L.new(dp.outputs["Points"], ip.inputs["Points"]); L.new(bo.outputs["Geometry"], ip.inputs["Instance"])
    L.new(ce.outputs[0], ip.inputs["Rotation"]); L.new(scl.outputs[0], ip.inputs["Scale"])
    # drop blades that are almost gone
    cmp_ = N.new("FunctionNodeCompare"); cmp_.data_type = 'FLOAT'; cmp_.operation = 'LESS_THAN'; L.new(scl.outputs[0], cmp_.inputs[0]); cmp_.inputs[1].default_value = 0.12
    dl = N.new("GeometryNodeDeleteGeometry"); dl.domain = 'INSTANCE'; L.new(ip.outputs[0], dl.inputs[0]); L.new(cmp_.outputs[0], dl.inputs["Selection"])
    L.new(dl.outputs[0], go.inputs[0])
    return g

FOOTL = bpy.data.objects.new("FootProbe.L", None); FOOTR = bpy.data.objects.new("FootProbe.R", None)
for e in (FOOTL, FOOTR): FX.objects.link(e); e.empty_display_size = 0.05
GB = bpy.data.objects.new("GrassBlades", bpy.data.meshes.new("GrassBladesHost")); YARD.objects.link(GB)
mod = GB.modifiers.new("Grass", 'NODES'); mod.node_group = grass_gn("GrassGN", G, 70.0, 1400.0, (-3.2, 3.2, -9.0, 8.5), (FOOTL, FOOTR))

# ------------------------------------------------------------------ library models
def lib_model(name, size, axis=2, drop=(), rz=0.0):
    ms = import_glb(name)
    bad = [o for o in ms if any(k in (o.name + " ".join(m.name for m in o.data.materials if m)) for k in drop)]
    for o in bad: bpy.data.objects.remove(o, do_unlink=True)
    ms = [o for o in ms if o not in bad]
    if rz:
        for o in ms: o.data.transform(Matrix.Rotation(R_(rz), 4, 'Z'))
    normalize(ms, size, axis)
    o = join(ms, "LIB_" + name); link(o, LIB)
    return o
L_house = lib_model("house", 9.5, axis=0)
L_fence = lib_model("fence", 1.85)
L_bag = lib_model("sandbag", 0.62, axis='max')
L_bag.data.materials.clear(); L_bag.data.materials.append(mat("Burlap", (0.62, 0.52, 0.34), 0.9))
L_helmet = lib_model("helmet", 0.29, axis=0)
print("BBOX house", bbox([L_house])); print("BBOX fence", bbox([L_fence])); print("BBOX bag", bbox([L_bag])); print("BBOX helmet", bbox([L_helmet]))

# the scan's SketchUp textures render as black stripes (tiny UV tiling + hashed alpha): clean painted materials instead
def siding(name, rgb):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; P = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); wv = nt.nodes.new("ShaderNodeTexWave"); wv.wave_type = 'BANDS'; wv.bands_direction = 'Z'
    wv.wave_profile = 'SAW'; wv.inputs["Scale"].default_value = 2.2; nt.links.new(tc.outputs["Object"], wv.inputs["Vector"])
    rp = nt.nodes.new("ShaderNodeValToRGB"); nt.links.new(wv.outputs["Fac"], rp.inputs[0])
    rp.color_ramp.elements[0].color = (rgb[0] * 0.82, rgb[1] * 0.82, rgb[2] * 0.82, 1); rp.color_ramp.elements[1].color = (*rgb, 1)
    nt.links.new(rp.outputs[0], P.inputs["Base Color"]); P.inputs["Roughness"].default_value = 0.6
    return m
REMAT = {"Cladding_Siding_White": siding("HouseSiding", (0.80, 0.85, 0.93)),
         "Roofing": mat("HouseRoof", (0.16, 0.18, 0.24), 0.7), "Brick": mat("HouseFoundation", (0.62, 0.6, 0.58), 0.8),
         "Glass": mat("HouseWindow", (0.55, 0.62, 0.7), 0.15, emit=(0.75, 0.78, 0.8), emit_s=0.35),
         "Snow": mat("HouseTrim", (0.95, 0.95, 0.93), 0.5), "material_0": mat("HouseTrim2", (0.9, 0.91, 0.92), 0.5),
         "Blacktop": mat("HouseConcrete", (0.7, 0.69, 0.66), 0.85), "Asphalt": mat("HouseConcrete", (0.7, 0.69, 0.66), 0.85)}
for j, m in enumerate(L_house.data.materials):
    nm = REMAT.get(next((k for k in REMAT if m and k in m.name), ""), None) if m else None
    L_house.data.materials[j] = nm or REMAT["Snow"]
import bmesh as _bm
bmh = _bm.new(); bmh.from_mesh(L_house.data)
_bm.ops.remove_doubles(bmh, verts=bmh.verts, dist=0.002)
seen = {}; dup = []
for f in bmh.faces:
    k = tuple(sorted(v.index for v in f.verts))
    if k in seen: dup.append(f)
    else: seen[k] = f
_bm.ops.delete(bmh, geom=dup, context='FACES')
_bm.ops.recalc_face_normals(bmh, faces=bmh.faces); bmh.to_mesh(L_house.data); bmh.free()
print("house dup faces removed", len(dup))
house = copy_obj(L_house, "House", (0.0, YF - 1.2, 0.0), 0, YARD)
house["front_rz"] = 0.0
# fences: back (y = YB+0.6) and both sides
mn, mx = bbox([L_fence]); FL = (mx - mn).x if (mx - mn).x > (mx - mn).y else (mx - mn).y
FRZ = 0 if (mx - mn).x >= (mx - mn).y else 90
def fence_run(p0, p1, tag):
    p0, p1 = Vector(p0), Vector(p1); n = max(1, round((p1 - p0).length / FL)); d = (p1 - p0) / n
    ang = math.degrees(math.atan2(d.y, d.x))
    for i in range(n):
        c = p0 + d * (i + 0.5)
        copy_obj(L_fence, "Fence_%s_%02d" % (tag, i), (c.x, c.y, 0), ang - FRZ, YARD)
fence_run((XL + 0.6, YB + 0.6, 0), (XR - 0.6, YB + 0.6, 0), "B")
fence_run((XL + 0.6, YB + 0.6, 0), (XL + 0.6, YF - 4.0, 0), "L")
fence_run((XR - 0.6, YB + 0.6, 0), (XR - 0.6, YF - 4.0, 0), "R")
# outer ground so wides never show the void
M_lawn = bpy.data.materials.new("LawnMat"); M_lawn.use_nodes = True; ntl = M_lawn.node_tree
tl_ = tex_node(ntl, phf("leafy_grass", "diff"), ntl.nodes.new("ShaderNodeTexCoord").outputs["Object"], 0.45)
ntl.links.new(tint(ntl, tl_.outputs[0], (0.62, 1.05, 0.42)), ntl.nodes["Principled BSDF"].inputs["Base Color"])
for nm_, (cx, cy, sx, sy) in {"N": (0, YF + 100, 400, 200), "S": (0, YB - 100, 400, 200), "W": (XL - 100, (YF + YB) / 2, 200, YF - YB), "E": (XR + 100, (YF + YB) / 2, 200, YF - YB)}.items():
    plane("OuterGround_" + nm_, (sx + 0.02, sy + 0.02), (cx, cy, -0.005), M_lawn, YARD)
# a few shrubs / trees beyond the fence (simple but organic: displaced icospheres in leaf green) for depth
def shrub(name, loc, r, c):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=r, location=loc); o = bpy.context.active_object; o.name = name
    tx = bpy.data.textures.new(name + "_n", 'CLOUDS'); tx.noise_scale = r * 0.35
    d = o.modifiers.new("d", 'DISPLACE'); d.texture = tx; d.strength = r * 0.35
    bpy.ops.object.shade_smooth(); o.data.materials.append(c); link(o, YARD); o.scale = (1, 1, 0.8); return o
# ------------------------------------------------------------------ water in the groove (flat sheet clipped by the ground; level keyed)
wv, wf = [], []
ys_w = [Y_BACK + 0.3 + i * 0.1 for i in range(int((Y_PORCH - Y_BACK - 0.6) / 0.1))]
for j, yy in enumerate(ys_w):
    for k_, vv in enumerate((-0.9, -0.45, 0.0, 0.45, 0.9)):
        wv.append((path_x(yy) + vv, yy, 0.0))
for j in range(len(ys_w) - 1):
    for k_ in range(4): wf.append((j * 5 + k_, j * 5 + k_ + 1, (j + 1) * 5 + k_ + 1, (j + 1) * 5 + k_))
wm = bpy.data.meshes.new("Water"); wm.from_pydata(wv, [], wf); wm.update()
WATER = bpy.data.objects.new("Water", wm); FX.objects.link(WATER)
for p in wm.polygons: p.use_smooth = True
MW = bpy.data.materials.new("WaterMat"); MW.use_nodes = True; nt = MW.node_tree; Pw = nt.nodes["Principled BSDF"]
Pw.inputs["Base Color"].default_value = (0.18, 0.42, 0.62, 1); Pw.inputs["Roughness"].default_value = 0.3
Pw.inputs["Specular IOR Level"].default_value = 0.03; Pw.inputs["Alpha"].default_value = 0.85
tcw2 = nt.nodes.new("ShaderNodeTexCoord"); mpf = nt.nodes.new("ShaderNodeMapping"); mpf.name = "Flow"
nt.links.new(tcw2.outputs["Object"], mpf.inputs[0]); mpf.inputs["Scale"].default_value = (3.0, 1.0, 3.0)
nzw = nt.nodes.new("ShaderNodeTexNoise"); nzw.inputs["Scale"].default_value = 3.0; nzw.inputs["Detail"].default_value = 4
nt.links.new(mpf.outputs[0], nzw.inputs["Vector"])
bpw = nt.nodes.new("ShaderNodeBump"); bpw.inputs["Strength"].default_value = 0.35; nt.links.new(nzw.outputs[0], bpw.inputs["Height"]); nt.links.new(bpw.outputs[0], Pw.inputs["Normal"])
rmp = nt.nodes.new("ShaderNodeValToRGB"); nt.links.new(nzw.outputs[0], rmp.inputs[0])
rmp.color_ramp.elements[0].position = 0.55; rmp.color_ramp.elements[0].color = (0.16, 0.38, 0.58, 1)
rmp.color_ramp.elements[1].position = 0.75; rmp.color_ramp.elements[1].color = (0.42, 0.62, 0.78, 1)
nt.links.new(rmp.outputs[0], Pw.inputs["Base Color"])
WATER.data.materials.append(MW)

# ------------------------------------------------------------------ rain: streaks in a box, fall driven by a keyed input "t"
def rain_gn():
    g = bpy.data.node_groups.new("RainGN", 'GeometryNodeTree')
    g.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    st = g.interface.new_socket("t", in_out='INPUT', socket_type='NodeSocketFloat'); st.default_value = 0.0
    N = g.nodes; L = g.links; gi = N.new("NodeGroupInput"); go = N.new("NodeGroupOutput")
    cube = N.new("GeometryNodeMeshCube"); cube.inputs["Size"].default_value = (9, 9, 7)
    dp = N.new("GeometryNodeDistributePointsInVolume") if False else None
    pts = N.new("GeometryNodePoints"); pts.inputs["Count"].default_value = 9000
    rx = N.new("FunctionNodeRandomValue"); rx.data_type = 'FLOAT_VECTOR'; rx.inputs[0].default_value = (-4.5, -4.5, 0); rx.inputs[1].default_value = (4.5, 4.5, 7)
    L.new(rx.outputs[0], pts.inputs["Position"])
    # z = mod(z0 - t*9, 7)
    sp = N.new("ShaderNodeSeparateXYZ"); L.new(rx.outputs[0], sp.inputs[0])
    mt = N.new("ShaderNodeMath"); mt.operation = 'MULTIPLY'; L.new(gi.outputs["t"], mt.inputs[0]); mt.inputs[1].default_value = -9.0
    ad = N.new("ShaderNodeMath"); ad.operation = 'ADD'; L.new(sp.outputs["Z"], ad.inputs[0]); L.new(mt.outputs[0], ad.inputs[1])
    md = N.new("ShaderNodeMath"); md.operation = 'FLOORED_MODULO'; L.new(ad.outputs[0], md.inputs[0]); md.inputs[1].default_value = 7.0
    cc = N.new("ShaderNodeCombineXYZ"); L.new(sp.outputs["X"], cc.inputs[0]); L.new(sp.outputs["Y"], cc.inputs[1]); L.new(md.outputs[0], cc.inputs[2])
    setp = N.new("GeometryNodeSetPosition"); L.new(pts.outputs[0], setp.inputs["Geometry"]); L.new(cc.outputs[0], setp.inputs["Position"])
    ci = N.new("GeometryNodeObjectInfo"); ci.name = "CamInfo"; ci.transform_space = 'RELATIVE'
    dv = N.new("ShaderNodeVectorMath"); dv.operation = 'DISTANCE'; L.new(cc.outputs[0], dv.inputs[0]); L.new(ci.outputs["Location"], dv.inputs[1])
    near = N.new("FunctionNodeCompare"); near.data_type = 'FLOAT'; near.operation = 'LESS_THAN'; L.new(dv.outputs["Value"], near.inputs[0]); near.inputs[1].default_value = 2.2
    dl = N.new("GeometryNodeDeleteGeometry"); dl.domain = 'POINT'; L.new(setp.outputs[0], dl.inputs[0]); L.new(near.outputs[0], dl.inputs["Selection"]); setp = dl
    cy = N.new("GeometryNodeMeshCylinder"); cy.inputs["Vertices"].default_value = 4; cy.inputs["Radius"].default_value = 0.0016; cy.inputs["Depth"].default_value = 0.32
    ip = N.new("GeometryNodeInstanceOnPoints"); L.new(setp.outputs[0], ip.inputs["Points"]); L.new(cy.outputs["Mesh"], ip.inputs["Instance"])
    rot = N.new("ShaderNodeCombineXYZ"); rot.inputs[0].default_value = R_(8); L.new(rot.outputs[0], ip.inputs["Rotation"])
    sm = N.new("GeometryNodeSetMaterial"); L.new(ip.outputs[0], sm.inputs[0])
    mr = bpy.data.materials.new("RainMat"); mr.use_nodes = True; Pr = mr.node_tree.nodes["Principled BSDF"]
    Pr.inputs["Base Color"].default_value = (0.85, 0.92, 1.0, 1); Pr.inputs["Alpha"].default_value = 0.3; Pr.inputs["Roughness"].default_value = 0.3
    Pr.inputs["Emission Color"].default_value = (0.8, 0.88, 1.0, 1); Pr.inputs["Emission Strength"].default_value = 0.15
    sm.inputs["Material"].default_value = mr
    L.new(sm.outputs[0], go.inputs[0])
    return g
RAIN = bpy.data.objects.new("Rain", bpy.data.meshes.new("RainHost")); FX.objects.link(RAIN)
RAIN.modifiers.new("Rain", 'NODES').node_group = rain_gn()
RAIN.visible_shadow = False

# ------------------------------------------------------------------ soil cross-section block (x=100): lawn on top, clods below
SX = 100.0
M_clod = [mat("Clod%d" % i, c, 0.85) for i, c in enumerate([(0.42, 0.26, 0.14), (0.50, 0.32, 0.18), (0.36, 0.22, 0.12), (0.55, 0.37, 0.22)])]
M_back = mat("SoilBack", (0.20, 0.12, 0.07), 0.9)
SEC_W, SEC_D, SEC_H = 3.0, 0.9, 0.62
box("SectBack", (SEC_W, 0.05, SEC_H), (SX, 0.42, SEC_H / 2), M_back, SECT)
box("SectFloor", (SEC_W, SEC_D, 0.04), (SX, 0.0, 0.02), M_back, SECT)
for side in (-1, 1):
    box("SectEnd%d" % side, (0.05, SEC_D, SEC_H), (SX + side * SEC_W / 2, 0.0, SEC_H / 2), M_back, SECT)
# top lawn layer: thin turf box with the grass material, blades scattered on its top (dense)
turf = box("SectTurf", (SEC_W, SEC_D, 0.06), (SX, 0.0, SEC_H - 0.03), None, SECT)
M_turf = bpy.data.materials.new("TurfMat"); M_turf.use_nodes = True; ntt = M_turf.node_tree
tg = tex_node(ntt, phf("leafy_grass", "diff"), ntt.nodes.new("ShaderNodeTexCoord").outputs["Object"], 0.8)
ntt.links.new(tint(ntt, tg.outputs[0], (0.6, 1.0, 0.4)), ntt.nodes["Principled BSDF"].inputs["Base Color"])
turf.data.materials.append(M_turf)
# a subdivided top plane carries the blades (pd = |x - SX| so the middle strip can be crushed)
top = plane("SectTop", (SEC_W - 0.06, SEC_D - 0.06), (SX, 0.0, SEC_H + 0.001), M_turf, SECT, subdiv=30)
pa = top.data.attributes.new("pd", 'FLOAT', 'POINT'); pt_ = top.data.attributes.new("tp", 'FLOAT', 'POINT')
for i, v in enumerate(top.data.vertices):
    pa.data[i].value = abs(v.co.y + 0.0); pt_.data[i].value = 1.0         # strip runs along X under the walking line (y=0)
SB = bpy.data.objects.new("SectBlades", bpy.data.meshes.new("SectBladesHost")); SECT.objects.link(SB)
SB.modifiers.new("Grass", 'NODES').node_group = grass_gn("SectGrassGN", top, 2200.0, 2200.0, (-1, 1, -1, 1), (FOOTL, FOOTR))
# clods: packed displaced icospheres in a grid (front rows visible), each keyed to squash in 03_anim
CLODS = []
for ix in range(13):
    for iz in range(3):
        for iy in range(2):
            r = 0.105 + 0.02 * random.random()
            x = SX - SEC_W / 2 + 0.13 + ix * 0.228 + (0.06 if iz % 2 else 0) + random.uniform(-0.02, 0.02)
            if x > SX + SEC_W / 2 - 0.1: continue
            z = 0.12 + iz * 0.17 + random.uniform(-0.01, 0.01); yy = -0.3 + iy * 0.32
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=r, location=(x, yy, z)); o = bpy.context.active_object
            o.name = "Clod_%02d_%d_%d" % (ix, iz, iy)
            tx = bpy.data.textures.get("ClodN") or bpy.data.textures.new("ClodN", 'CLOUDS')
            tx.noise_scale = 0.06
            d = o.modifiers.new("d", 'DISPLACE'); d.texture = tx; d.strength = 0.04; d.texture_coords = 'GLOBAL'
            o.scale = (1.0, 1.0, 0.82); bpy.ops.object.shade_smooth()
            o.data.materials.append(M_clod[random.randrange(4)]); link(o, SECT); CLODS.append(o)
            o["rest_z"] = z
print("clods", len(CLODS))

# ------------------------------------------------------------------ war-trench dressing (S22-S23): sandbags on both rims, hidden until then
BAGS = []
def bag_row(y0, y1, side, tag):
    yy = y0; i = 0
    while yy < y1:
        for lvl in range(2):
            px = path_x(yy) + side * (STAGES["Trench"][0] + 0.32)
            o = copy_obj(L_bag, "Bag_%s_%02d_%d" % (tag, i, lvl), (px, yy + (0.28 if lvl else 0), 0.0 + lvl * 0.17), random.uniform(-6, 6), YARD)
            BAGS.append(o)
        yy += 0.56; i += 1
bag_row(-6.4, -2.6, -1, "L"); bag_row(-6.4, -2.6, 1, "R")
HELMET = copy_obj(L_helmet, "Helmet", (0, 0, -50), 0, YARD)

# DA KRAS FILMS logo image (used on the man's shirt in 03_anim)
LOGO = bpy.data.images.load(os.path.join(FILM, "..", "assets", "brand", "DaKrasFilms_logo_dark.png"))
LOGO.name = "DaKrasFilms_logo_dark"
G["groove_stages"] = str(STAGES)
bpy.ops.wm.save_as_mainfile(filepath=out)
