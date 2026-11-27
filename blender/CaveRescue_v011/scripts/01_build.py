"""CaveRescue v011 stage A (from scratch): sets, characters, diver gear, props, look.
blender -b --python 01_build.py -- <polyhaven_dir> <out.blend>

ONE world at real scale. The route runs along +X in the plane y=0: the cave mouth in a limestone cliff at x=0, a dry
passage, sump 1 (x 98-150), a dry gallery, sump 2 (x 232-292) and the ledge chamber (x 289-315).
The whole mountain is ONE carved solid (mountain - tunnel - chamber + mud ledge), split at y=0 into ROCK_Back and
ROCK_Front. Everything in front (y<0) is parented to the empty FRONT_CTL; dropping it 160 m opens the cross-section
(strata on the cut face). Water bodies are split the same way (volume-only material, so the coincident halves are
invisible when the front is closed)."""
import bpy, bmesh, sys, math, random, os
from mathutils import Vector, Matrix, noise
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "lib_build.py")).read())
a = sys.argv[sys.argv.index("--") + 1:]
PH, OUT = a[0], a[1]
PKG = os.path.dirname(HERE)
random.seed(23)
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
sc = bpy.context.scene
sc.render.fps = 60
sc.frame_start, sc.frame_end = 1, 2436
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
def col(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in sc.collection.children: sc.collection.children.link(c)
    return c
C_SET, C_CHR, C_PROP, C_FX = col("SET"), col("CHARACTERS"), col("PROPS"), col("FX")
def to_col(o, c):
    for cc in list(o.users_collection): cc.objects.unlink(o)
    c.objects.link(o)
def sm(a_, b_, x):
    t = max(0.0, min(1.0, (x - a_) / (b_ - a_))); return t * t * (3 - 2 * t)
def interp(tab, x):
    if x <= tab[0][0]: return tab[0][1:]
    for (x0, *v0), (x1, *v1) in zip(tab, tab[1:]):
        if x <= x1:
            t = (x - x0) / (x1 - x0); t = t * t * (3 - 2 * t)
            return tuple(p + (q - p) * t for p, q in zip(v0, v1))
    return tab[-1][1:]

# ================================================================== materials
def ph_tex_mat(name, asset, scale=1.0, tint_=(1, 1, 1), bump=0.6, rough_add=0.0, triplanar=True):
    """a Poly Haven texture set as a box-projected (object coords) material: no UVs needed on carved geometry"""
    d = os.path.join(PH, asset, "textures")
    files = os.listdir(d)
    def find(k): return [f for f in files if k in f.lower()]
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (scale,) * 3
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    def img(fn, noncolor=False):
        t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(os.path.join(d, fn), check_existing=True)
        if noncolor: t.image.colorspace_settings.name = "Non-Color"
        t.projection = 'BOX'; t.projection_blend = 0.3
        nt.links.new(mp.outputs["Vector"], t.inputs["Vector"]); return t
    dif = img(find("diff")[0])
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs["Factor"].default_value = 1.0
    mx.inputs["B"].default_value = (*tint_, 1); nt.links.new(dif.outputs["Color"], mx.inputs["A"]); nt.links.new(mx.outputs["Result"], p.inputs["Base Color"])
    rg = find("rough")
    if rg:
        r = img(rg[0], True); mr = nt.nodes.new("ShaderNodeMath"); mr.operation = 'ADD'; mr.inputs[1].default_value = rough_add; mr.use_clamp = True
        nt.links.new(r.outputs["Color"], mr.inputs[0]); nt.links.new(mr.outputs[0], p.inputs["Roughness"])
    dp = find("disp")
    if dp:
        h = img(dp[0], True); bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump; bp.inputs["Distance"].default_value = 0.03 / scale
        nt.links.new(h.outputs["Color"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], p.inputs["Normal"])
    return m

M_ROCK = ph_tex_mat("M_Rock", "cliff_side", scale=0.3, tint_=(1.35, 1.0, 0.62), bump=1.0)        # warm limestone
M_MUD = ph_tex_mat("M_Mud", "brown_mud_leaves_01", scale=0.6, tint_=(1.05, 0.70, 0.42), bump=0.5)
M_JUNGLE = ph_tex_mat("M_JungleFloor", "forest_leaves_03", scale=0.5, tint_=(0.85, 1.15, 0.35), bump=0.5)
# mountain skin: rock on the cliff, jungle green on gentle slopes and the floor (mix by the surface normal)
def mountain_mat():
    m = bpy.data.materials.new("M_Mountain"); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n)
    out = [n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'][0]
    g1 = nt.nodes.new("ShaderNodeGroup"); g2 = nt.nodes.new("ShaderNodeGroup")
    def grp(src):
        g = bpy.data.node_groups.new(src.name + "_G", 'ShaderNodeTree')
        g.interface.new_socket("BSDF", in_out='OUTPUT', socket_type='NodeSocketShader')
        go = g.nodes.new("NodeGroupOutput")
        for n in src.node_tree.nodes:
            pass
        return g
    # simpler: two principled stacks copied by re-creating the texture materials inside one tree
    return None
def mix_mat(name, m1, m2, fac_fn):
    """copy both materials' node trees into one: a Mix Shader with a factor from fac_fn(nt)"""
    m = m1.copy(); m.name = name; nt = m.node_tree
    out = [n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'][0]
    p1 = out.inputs["Surface"].links[0].from_node
    # rebuild m2's nodes in this tree
    mapping = {}
    for n in m2.node_tree.nodes:
        if n.type == 'OUTPUT_MATERIAL': continue
        nn = nt.nodes.new(n.bl_idname); mapping[n.name] = nn
        if n.type == 'TEX_IMAGE': nn.image = n.image; nn.projection = n.projection; nn.projection_blend = n.projection_blend
        if n.type == 'MIX': nn.data_type = n.data_type; nn.blend_type = n.blend_type
        if n.type == 'MATH': nn.operation = n.operation; nn.use_clamp = n.use_clamp
        for i, s in enumerate(n.inputs):
            if hasattr(s, "default_value") and not s.is_linked:
                try: nn.inputs[i].default_value = s.default_value
                except Exception: pass
    for l in m2.node_tree.links:
        if l.to_node.type == 'OUTPUT_MATERIAL': p2 = mapping[l.from_node.name]; continue
        fo = mapping[l.from_node.name].outputs[[s.identifier for s in l.from_node.outputs].index(l.from_socket.identifier)]
        ti = mapping[l.to_node.name].inputs[[s.identifier for s in l.to_node.inputs].index(l.to_socket.identifier)]
        nt.links.new(fo, ti)
    ms = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(p1.outputs[0], ms.inputs[1]); nt.links.new(p2.outputs[0], ms.inputs[2])
    nt.links.new(fac_fn(nt), ms.inputs["Fac"]); nt.links.new(ms.outputs[0], out.inputs["Surface"])
    return m
def slope_fac(nt):
    g = nt.nodes.new("ShaderNodeNewGeometry"); sp = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(g.outputs["Normal"], sp.inputs[0])
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.35
    ad = nt.nodes.new("ShaderNodeMath"); ad.operation = 'ADD'; nt.links.new(sp.outputs["Z"], ad.inputs[0])
    mm = nt.nodes.new("ShaderNodeMath"); mm.operation = 'MULTIPLY'; mm.inputs[1].default_value = 0.3; nt.links.new(nz.outputs["Fac"], mm.inputs[0])
    nt.links.new(mm.outputs[0], ad.inputs[1])
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.78; mr.inputs["From Max"].default_value = 0.92
    nt.links.new(ad.outputs[0], mr.inputs["Value"]); return mr.outputs["Result"]
M_MOUNT = mix_mat("M_Mountain", M_ROCK, M_JUNGLE, slope_fac)
# the cut face of the cross-section: saturated limestone strata (bands in z with noise wobble)
def strata_mat():
    m = mat("M_Strata", (0.8, 0.5, 0.2), rough=0.8); nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); wv = nt.nodes.new("ShaderNodeTexWave"); wv.wave_type = 'BANDS'; wv.bands_direction = 'Z'
    wv.inputs["Scale"].default_value = 0.035; wv.inputs["Distortion"].default_value = 6.0; wv.inputs["Detail"].default_value = 4.0
    nt.links.new(tc.outputs["Object"], wv.inputs["Vector"])
    cr = nt.nodes.new("ShaderNodeValToRGB"); E = cr.color_ramp.elements
    E[0].position = 0.0; E[0].color = (0.55, 0.22, 0.06, 1); E[1].position = 1.0; E[1].color = (0.95, 0.70, 0.32, 1)
    e = E.new(0.35); e.color = (0.85, 0.42, 0.10, 1); e = E.new(0.62); e.color = (0.98, 0.82, 0.45, 1)
    nt.links.new(wv.outputs["Fac"], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], p.inputs["Base Color"])
    return m
M_STRATA = strata_mat()
def water_vol(name, emit=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n)
    out = [n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'][0]
    pv = nt.nodes.new("ShaderNodeVolumePrincipled")
    pv.inputs["Color"].default_value = (0.30, 0.60, 0.50, 1); pv.inputs["Density"].default_value = 0.07
    pv.inputs["Absorption Color"].default_value = (0.35, 0.62, 0.55, 1)
    pv.inputs["Emission Color"].default_value = (0.05, 0.35, 0.75, 1); pv.inputs["Emission Strength"].default_value = emit
    nt.links.new(pv.outputs[0], out.inputs["Volume"])
    return m
M_WATER = water_vol("M_WaterVol")
def water_surface():
    m = bpy.data.materials.new("M_WaterSurf"); m.use_nodes = True; nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (0.25, 0.55, 0.50, 1); p.inputs["Roughness"].default_value = 0.08
    p.inputs["Transmission Weight"].default_value = 1.0; p.inputs["IOR"].default_value = 1.33
    p.inputs["Specular IOR Level"].default_value = 0.25
    tc = nt.nodes.new("ShaderNodeTexCoord"); nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 1.8
    nz.inputs["Detail"].default_value = 3.0
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.25; bp.inputs["Distance"].default_value = 0.02
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"]); nt.links.new(nz.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], p.inputs["Normal"])
    return m
M_WSURF = water_surface()

# ================================================================== the route (floor centre line, y=0) and the passage profile
ROUTE = [(-12, 0.0), (0, 0.0), (20, -0.3), (45, 0.2), (75, 1.0), (98, -0.6), (112, -8.0), (135, -8.0), (150, 0.4),
         (185, 3.0), (215, 3.5), (232, -2.5), (245, -6.0), (270, -6.0), (284, -3.2), (293, -1.6), (300, -1.2)]
PROF = [(-12, 6.5, 5.5), (0, 5.2, 4.6), (30, 4.5, 4.0), (90, 3.6, 3.1), (108, 1.9, 1.6), (140, 1.9, 1.6), (156, 3.6, 3.0),
        (222, 3.0, 2.6), (238, 1.9, 1.6), (256, 1.8, 1.5), (268, 1.9, 1.6), (276, 1.55, 1.3), (280, 1.5, 1.25), (283.5, 1.9, 1.6),
        (289, 3.0, 2.8), (295, 4.5, 4.0), (300, 4.5, 4.0)]
def floor_z(x): return interp(ROUTE, x)[0]
def prof(x): return interp(PROF, x)
POOL_Z = 1.2
CH_C, CH_R = Vector((302.0, 0.0, 2.6)), Vector((13.5, 9.0, 5.6))
def ledge_top(x, y): return 0.15 + 1.65 * sm(295.5, 303.5, x) + 0.06 * noise.noise(Vector((x * 0.7, y * 0.7, 3.1)))

# ---- mountain solid (heightfield + skirt + bottom)
def mount_h(x, y):
    g = -0.15 + 0.25 * noise.noise(Vector((x * 0.08, y * 0.08, 0.5)))
    ridge = math.exp(-(y / 75.0) ** 2)
    cliff = 17.0 * sm(-2.8, 1.6, x) * sm(-60, -25, -abs(y)) ** 0.0
    cliff *= (0.35 + 0.65 * math.exp(-(y / 45.0) ** 2))
    dome = 105.0 * math.exp(-((x - 150.0) / 115.0) ** 2) * ridge * sm(-1.0, 25.0, x)
    tail = 1.0 - sm(330.0, 365.0, x)
    n = 3.2 * noise.fractal(Vector((x / 28.0, y / 28.0, 1.7)), 0.5, 2.0, 4) + 0.5 * noise.noise(Vector((x / 4.0, y / 4.0, 7.0)))
    h = g + (cliff + dome + max(0.0, n) * sm(-1.0, 6.0, x)) * tail
    if x < -2.8: h = g + 0.6 * max(0.0, noise.noise(Vector((x / 9.0, y / 9.0, 2.0))))
    return h
def axis_steps(segs):
    v = []
    for a_, b_, st in segs:
        n = int(round((b_ - a_) / st))
        v += [a_ + (b_ - a_) * i / n for i in range(n)]
    v.append(segs[-1][1]); return v
XS = axis_steps([(-60, -14, 1.5), (-14, 12, 0.3), (12, 368, 2.0)])
YS = axis_steps([(-110, -14, 1.5), (-14, 14, 0.3), (14, 110, 1.5)])
bm = bmesh.new()
grid = [[bm.verts.new((x, y, mount_h(x, y))) for x in XS] for y in YS]
bot = [[None] * len(XS) for _ in YS]
for j in range(len(YS) - 1):
    for i in range(len(XS) - 1):
        bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
ZB = -45.0
ring = [grid[0][i] for i in range(len(XS))] + [grid[j][-1] for j in range(1, len(YS))] + \
       [grid[-1][i] for i in range(len(XS) - 2, -1, -1)] + [grid[j][0] for j in range(len(YS) - 2, 0, -1)]
low = [bm.verts.new((v.co.x, v.co.y, ZB)) for v in ring]
for k in range(len(ring)):
    a1, a2, b1, b2 = ring[k], ring[(k + 1) % len(ring)], low[k], low[(k + 1) % len(ring)]
    bm.faces.new((a2, a1, b1, b2))
bm.faces.new(low)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
me = bpy.data.meshes.new("Mountain"); bm.to_mesh(me); bm.free()
MOUNT = bpy.data.objects.new("Mountain", me); C_SET.objects.link(MOUNT); me.materials.append(M_MOUNT)

# ---- the passage cutter: rings along the route, arch profile with a flat floor, 3D-noise walls (never a pipe)
def ring_pts(w, h, n=30):
    pts = []
    for k in range(n):
        t = k / n
        if t < 0.18:            # floor, left to right
            u = -w / 2 + w * (t / 0.18); v = 0.0
        else:                   # wall + arch, right to left (a squashed superellipse)
            ang = (t - 0.18) / 0.82 * math.pi
            c, s_ = math.cos(ang), math.sin(ang)
            u = w / 2 * math.copysign(abs(c) ** 0.6, c); v = h * (abs(s_) ** 0.45)
        pts.append((u, v))
    return pts
def cutter_mesh(name, x0, x1, step=0.3, extra=0.0, seed=1.0):
    bm = bmesh.new(); rings = []
    xs = [x0 + i * step for i in range(int((x1 - x0) / step) + 1)]
    for x in xs:
        z = floor_z(x); dz = (floor_z(x + 0.5) - floor_z(x - 0.5))
        T = Vector((1.0, 0.0, dz)).normalized(); L = Vector((0, 1, 0)); U = T.cross(L)
        w, h = prof(x); w += extra; h += extra
        rr = []
        for (u, v) in ring_pts(w, h):
            p = Vector((x, 0, z)) + L * u + U * v
            nrm = Vector((u, v - h * 0.45)); nrm = nrm.normalized() if nrm.length > 1e-6 else Vector((0, 1))
            wall = 0.12 if v < 0.01 else 1.0
            amp = (0.10 + 0.13 * min(w, 5.0)) * wall
            d = amp * (noise.fractal(p * 0.55 + Vector((seed, 0, 0)), 0.6, 2.0, 4) + 0.35 * noise.noise(p * 2.2))
            if v < 0.01: d = 0.04 * noise.noise(p * 1.3) - 0.02
            p = p + (L * nrm.x + U * nrm.y) * d
            rr.append(bm.verts.new(p))
        rings.append(rr)
    n = len(rings[0])
    for r1, r2 in zip(rings, rings[1:]):
        for k in range(n):
            bm.faces.new((r1[k], r1[(k + 1) % n], r2[(k + 1) % n], r2[k]))
    bm.faces.new(rings[0][::-1]); bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); C_SET.objects.link(o); return o
TUN = cutter_mesh("CUT_Tunnel", -12.0, 301.0)
# the chamber: a noisy ellipsoid
def chamber_mesh(name, c, r, extra=0.0):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=5, radius=1.0)
    for v in bm.verts:
        d = v.co.normalized(); p = c + Vector((d.x * (r.x + extra), d.y * (r.y + extra), d.z * (r.z + extra)))
        p += d * (0.9 * noise.fractal(p * 0.18, 0.6, 2.0, 4) + 0.25 * noise.noise(p * 0.9))
        v.co = p
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); C_SET.objects.link(o); return o
CHM = chamber_mesh("CUT_Chamber", CH_C, CH_R)
# the mud ledge (union back in): a slab whose top slopes up out of the pool to a flat shelf
def ledge_mesh(name):
    bm = bmesh.new(); xs = [290 + 0.25 * i for i in range(105)]; ys = [-9.5 + 0.25 * j for j in range(77)]
    top = [[bm.verts.new((x, y, ledge_top(x, y))) for x in xs] for y in ys]
    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            bm.faces.new((top[j][i], top[j][i + 1], top[j + 1][i + 1], top[j + 1][i]))
    ring = [top[0][i] for i in range(len(xs))] + [top[j][-1] for j in range(1, len(ys))] + \
           [top[-1][i] for i in range(len(xs) - 2, -1, -1)] + [top[j][0] for j in range(len(ys) - 2, 0, -1)]
    low = [bm.verts.new((v.co.x, v.co.y, -5.0)) for v in ring]
    for k in range(len(ring)):
        bm.faces.new((ring[(k + 1) % len(ring)], ring[k], low[k], low[(k + 1) % len(ring)]))
    bm.faces.new(low); bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); C_SET.objects.link(o); me.materials.append(M_MUD); return o
LEDGE = ledge_mesh("CUT_Ledge")

def boolean(target, cutter, op, solver='EXACT'):
    md = target.modifiers.new("b", 'BOOLEAN'); md.operation = op; md.object = cutter; md.solver = solver
    bpy.context.view_layer.objects.active = target; bpy.ops.object.select_all(action='DESELECT'); target.select_set(True)
    bpy.ops.object.modifier_apply(modifier="b")
for c_ in (TUN, CHM): c_.data.materials.append(M_ROCK)
boolean(MOUNT, TUN, 'DIFFERENCE'); print("BOOL tunnel", len(MOUNT.data.vertices))
boolean(MOUNT, CHM, 'DIFFERENCE'); print("BOOL chamber", len(MOUNT.data.vertices))
boolean(MOUNT, LEDGE, 'UNION'); print("BOOL ledge", len(MOUNT.data.vertices))

# ---- water bodies: (passage | chamber) inside a box below the water line, minus the ledge
def box_obj(name, x0, x1, y0, y1, z0, z1, m_=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    o = bpy.context.active_object; o.name = name; o.scale = (x1 - x0, y1 - y0, z1 - z0); bpy.ops.object.transform_apply(scale=True)
    if m_: o.data.materials.append(m_)
    return o
def copy_obj(o, name):
    c = o.copy(); c.data = o.data.copy(); c.name = name; C_SET.objects.link(c); return c
W2 = box_obj("Water2", 226.0, 317.0, -11.0, 11.0, -12.0, POOL_Z, M_WATER)
W3 = box_obj("Water3", 226.0, 317.0, -11.0, 11.0, -12.0, POOL_Z, M_WATER)
tun_w = cutter_mesh("CUT_TunW", 222.0, 292.0, seed=1.0)          # identical noise to CUT_Tunnel over this range
un = copy_obj(CHM, "CUT_Union")
boolean(W2, tun_w, 'INTERSECT'); print('W2', len(W2.data.vertices))
boolean(W3, un, 'INTERSECT'); boolean(W3, LEDGE, 'DIFFERENCE'); print('W3', len(W3.data.vertices))
W1 = box_obj("Water1", 96.0, 152.0, -6.0, 6.0, -12.0, -2.2, M_WATER)
tun_1 = cutter_mesh("CUT_Tun1", 94.0, 154.0, seed=1.0)
boolean(W1, tun_1, 'INTERSECT'); print('W1', len(W1.data.vertices))
for o in (W1, W2, W3):
    o.data.materials.clear(); o.data.materials.append(M_WATER)
    for p in o.data.polygons: p.material_index = 0
for o in (tun_w, un, tun_1, TUN, CHM, LEDGE): bpy.data.objects.remove(o, do_unlink=True)

# ---- split everything along y=0: back (y>=0, cap = strata) and front (y<=0); the front hangs on FRONT_CTL
FRONT = bpy.data.objects.new("FRONT_CTL", None); C_SET.objects.link(FRONT)
def split(o, cap_mat):
    big = 600
    halves = []
    for nm, y0, y1 in (("_Back", 0.0, big), ("_Front", -big, 0.0)):
        h = copy_obj(o, o.name + nm)
        bx = box_obj("tmpbox", -200, 600, y0, y1, -200, 400, cap_mat)
        md = h.modifiers.new("b", 'BOOLEAN'); md.operation = 'INTERSECT'; md.object = bx; md.solver = 'EXACT'
        md.material_mode = 'TRANSFER'
        bpy.context.view_layer.objects.active = h; bpy.ops.object.select_all(action='DESELECT'); h.select_set(True)
        bpy.ops.object.modifier_apply(modifier="b"); bpy.data.objects.remove(bx, do_unlink=True)
        halves.append(h)
    bpy.data.objects.remove(o, do_unlink=True)
    print('SPLITN', [len(h.data.vertices) for h in halves])
    halves[1].parent = FRONT
    for h in halves:
        for p in h.data.polygons: p.use_smooth = False
    return halves
MOUNT.name = "ROCK"
ROCK_B, ROCK_F = split(MOUNT, M_STRATA)
W1_B, W1_F = split(W1, M_WATER)
W2_B, W2_F = split(W2, M_WATER)
W3_B, W3_F = split(W3, M_WATER)
for o in (W1_B, W1_F, W2_B, W2_F, W3_B, W3_F):
    o.data.materials.clear(); o.data.materials.append(M_WATER)
# water bodies scale from their own floor (the flood fill in the cross-section)
for o in (W1_B, W1_F, W2_B, W2_F, W3_B, W3_F):
    zmin = min(v.co.z for v in o.data.vertices)
    o.data.transform(Matrix.Translation((0, 0, -zmin))); o.location.z += zmin
for o in (ROCK_B, ROCK_F):
    print("SPLIT", o.name, len(o.data.vertices), len(o.data.polygons))
# smooth shading on the rock but keep the crease at the strata cap (auto smooth by angle)
for o in (ROCK_B, ROCK_F):
    for p in o.data.polygons: p.use_smooth = True
    md = o.modifiers.new("autosmooth", 'NODES')
    try:
        bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
        bpy.ops.object.shade_auto_smooth(angle=math.radians(50))
        o.modifiers.remove(md)
    except Exception as e:
        print("autosmooth", e); o.modifiers.remove(md)

# ---- the pool surface (back/front halves), gently waving (texture driven by the keyed empty WaveCtl)
def plane(name, x0, x1, y0, y1, z, m_, res=0.25):
    bm = bmesh.new(); nx = int((x1 - x0) / res); ny = int((y1 - y0) / res)
    vv = [[bm.verts.new((x0 + (x1 - x0) * i / nx, y0 + (y1 - y0) * j / ny, z)) for i in range(nx + 1)] for j in range(ny + 1)]
    for j in range(ny):
        for i in range(nx): bm.faces.new((vv[j][i], vv[j][i + 1], vv[j + 1][i + 1], vv[j + 1][i]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); C_SET.objects.link(o); me.materials.append(m_)
    for p in me.polygons: p.use_smooth = True
    return o
WAVE = bpy.data.objects.new("WaveCtl", None); C_FX.objects.link(WAVE)
def waves(o, amp=0.025):
    tx = bpy.data.textures.get("T_Waves") or bpy.data.textures.new("T_Waves", 'CLOUDS'); tx.noise_scale = 0.9
    d = o.modifiers.new("waves", 'DISPLACE'); d.texture = tx; d.texture_coords = 'OBJECT'; d.texture_coords_object = WAVE
    d.strength = amp; d.mid_level = 0.5
POOL_B = plane("PoolSurf_Back", 286.0, 304.0, 0.0, 9.5, POOL_Z + 0.004, M_WSURF); waves(POOL_B)
POOL_F = plane("PoolSurf_Front", 286.0, 304.0, -9.5, 0.0, POOL_Z + 0.004, M_WSURF); waves(POOL_F); POOL_F.parent = FRONT
# trim the pool planes to the water body footprint (delete faces outside the chamber / over the ledge)
for o in (POOL_B, POOL_F):
    bm = bmesh.new(); bm.from_mesh(o.data)
    kill = []
    for f_ in bm.faces:
        c = f_.calc_center_median()
        dd = ((c.x - CH_C.x) / CH_R.x) ** 2 + ((c.y - CH_C.y) / CH_R.y) ** 2 + ((POOL_Z - CH_C.z) / CH_R.z) ** 2
        if ledge_top(c.x, c.y) > POOL_Z - 0.02 or dd > 0.98: kill.append(f_)
    bmesh.ops.delete(bm, geom=kill, context='FACES'); bm.to_mesh(o.data); bm.free()

# ---- mud bank strip where the flood surges in near the mouth (B2): a thin water sheet that slides in along +X
M_SURGE = mat("M_Surge", (0.32, 0.26, 0.15), rough=0.12)
M_SURGE.node_tree.nodes["Principled BSDF"].inputs["Specular IOR Level"].default_value = 0.3
SURGE = plane("FX_Surge", -14.0, 40.0, -2.4, 2.4, 0.0, M_SURGE, res=0.2)
bm = bmesh.new(); bm.from_mesh(SURGE.data)
for v in bm.verts:
    x = v.co.x; v.co.z = floor_z(x) + 0.07 + 0.03 * noise.noise(Vector((x * 1.2, v.co.y * 1.2, 0.3)))
    if x > 39.5: v.co.z -= 0.3
bm.to_mesh(SURGE.data); bm.free(); to_col(SURGE, C_FX); waves(SURGE, 0.05)

# ================================================================== jungle outside the mouth (x < 0)
def append_ph(asset, name, loc, rot_z=0.0, scale=1.0, collection=C_SET, parent=None):
    d = os.path.join(PH, asset); blend = [f for f in os.listdir(d) if f.endswith(".blend")][0]
    with bpy.data.libraries.load(os.path.join(d, blend), link=False) as (src, dst):
        dst.objects = list(src.objects)
    objs = [o for o in dst.objects if o is not None and o.type == 'MESH']
    root = bpy.data.objects.new(name, None); collection.objects.link(root)
    for o in objs:
        collection.objects.link(o)
        if o.parent is None or o.parent not in objs: o.parent = root
    root.location = loc; root.rotation_euler.z = rot_z; root.scale = (scale,) * 3
    if parent is not None: root.parent = parent
    for o in objs:
        for m in o.data.materials:
            if not m or not m.use_nodes: continue
            for n in m.node_tree.nodes:
                if n.type == 'BSDF_PRINCIPLED' and not n.inputs["Roughness"].is_linked:
                    n.inputs["Roughness"].default_value = max(0.35, n.inputs["Roughness"].default_value)
                if n.type == 'NORMAL_MAP': n.inputs["Strength"].default_value = 0.5
    return root, objs
def lib_once(asset):
    """load a Poly Haven model once (lowest useful LOD); later placements are linked-data copies (small file)"""
    r, objs = append_ph(asset, "LIB_" + asset, (0, 0, 0))
    keep = {"island_tree_01": lambda n: n == "island_tree_01_LOD1", "island_tree_02": lambda n: n == "island_tree_02_LOD1",
            "boulder_01": lambda n: n == "boulder_01_LOD2"}.get(asset, lambda n: True)
    upd_ = bpy.context.view_layer.update; upd_()
    out = []
    for o in list(objs):
        if keep(o.name): out.append((o.data, [m for m in o.data.materials], o.matrix_world.copy()))
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.objects.remove(r, do_unlink=True)
    return out
LIBS = {k: lib_once(k) for k in ("island_tree_01", "island_tree_02", "fern_02", "pachira_aquatica_01", "boulder_01")}
def place(asset, name, loc, rot_z=0.0, scale=1.0):
    root = bpy.data.objects.new(name, None); C_SET.objects.link(root)
    gz = mount_h(loc[0], loc[1])
    root.location = (loc[0], loc[1], gz + loc[2]); root.rotation_euler.z = rot_z; root.scale = (scale,) * 3
    for i, (me_, mats, rel) in enumerate(LIBS[asset]):
        c = bpy.data.objects.new(name + "_m%d" % i, me_); C_SET.objects.link(c); c.parent = root
        c.matrix_parent_inverse = Matrix.Identity(4); c.matrix_basis = rel
    if loc[1] < 0: root.parent = FRONT
    return root
rnd = random.Random(5)
spots = []
for i in range(70):
    x = rnd.uniform(-55, -4); y = rnd.uniform(-40, 40)
    if abs(y) < 5.0 and x > -24: continue          # the walking lane to the mouth stays clear
    spots.append((x, y))
for i, (x, y) in enumerate(spots):
    k = rnd.random()
    if k < 0.30: place("island_tree_01" if i % 2 else "island_tree_02", "JG_Tree%02d" % i, (x, y, -0.05), rnd.uniform(0, 6.28), rnd.uniform(2.2, 3.0))
    elif k < 0.55: place("pachira_aquatica_01", "JG_Plant%02d" % i, (x, y, -0.02), rnd.uniform(0, 6.28), rnd.uniform(1.6, 2.4))
    else: place("fern_02", "JG_Fern%02d" % i, (x, y, -0.02), rnd.uniform(0, 6.28), rnd.uniform(1.2, 2.0))
for i, (x, y, s) in enumerate(((-3.2, -4.6, 1.3), (-2.6, 5.2, 1.6), (-6.5, -7.5, 1.0), (-1.5, 8.5, 2.0), (-8.0, 6.0, 0.8))):
    place("boulder_01", "JG_Boulder%d" % i, (x, y, -0.3), rnd.uniform(0, 6.28), s)
# a few trees on top of the cliff
for i in range(16):
    x = rnd.uniform(3, 40); y = rnd.uniform(-30, 30)
    place("island_tree_01" if i % 2 else "island_tree_02", "JG_TopTree%02d" % i, (x, y, -0.2), rnd.uniform(0, 6.28), rnd.uniform(2.2, 2.8))
# ferns hanging around the mouth lip
for i, (x, y) in enumerate(((-1.6, -3.4), (-1.4, 3.6), (-2.2, -2.9), (-2.0, 3.0))):
    place("fern_02", "JG_MouthFern%d" % i, (x, y, 0.0), rnd.uniform(0, 6.28), 1.6)

# ================================================================== the route line, the boys' marker, the flood fill
def route_curve(name, x0, x1, step=1.0, y=-0.02, lift=0.9):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; sp = cu.splines.new('POLY')
    xs = [x0 + i * step for i in range(int((x1 - x0) / step) + 1)]
    sp.points.add(len(xs) - 1)
    for i, x in enumerate(xs): sp.points[i].co = (x, y, floor_z(x) + lift, 1)
    cu.bevel_depth = 1.6; cu.bevel_resolution = 3; cu.use_fill_caps = True
    o = bpy.data.objects.new(name, cu); C_FX.objects.link(o); return o
ROUTE_O = route_curve("FX_Route", -4.0, 303.0)
ROUTE_O["flood"] = 0.0
def route_mat():
    m = bpy.data.materials.new("M_Route"); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n)
    out = [n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'][0]
    at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_type = 'OBJECT'; at.attribute_name = '["flood"]'
    g = nt.nodes.new("ShaderNodeNewGeometry"); sp = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(g.outputs["Position"], sp.inputs[0])
    def m_(op, a_, b_):
        n = nt.nodes.new("ShaderNodeMath"); n.operation = op
        for i, v in enumerate((a_, b_)):
            if isinstance(v, (int, float)): n.inputs[i].default_value = v
            else: nt.links.new(v, n.inputs[i])
        return n.outputs[0]
    # underwater where (98<x<152 and z<-2.2+0.9) or (226<x<300 and z<1.2+0.9)
    s1 = m_('MULTIPLY', m_('MULTIPLY', m_('GREATER_THAN', sp.outputs["X"], 97.0), m_('LESS_THAN', sp.outputs["X"], 152.0)), m_('LESS_THAN', sp.outputs["Z"], -1.0))
    s2 = m_('MULTIPLY', m_('MULTIPLY', m_('GREATER_THAN', sp.outputs["X"], 227.0), m_('LESS_THAN', sp.outputs["X"], 296.0)), m_('LESS_THAN', sp.outputs["Z"], 2.2))
    fac = m_('MULTIPLY', m_('MAXIMUM', s1, s2), at.outputs["Fac"])
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.inputs["A"].default_value = (1.0, 0.55, 0.02, 1); mx.inputs["B"].default_value = (0.05, 0.55, 1.0, 1)
    nt.links.new(fac, mx.inputs["Factor"])
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Strength"].default_value = 6.0; nt.links.new(mx.outputs["Result"], em.inputs["Color"])
    nt.links.new(em.outputs[0], out.inputs["Surface"]); return m
ROUTE_O.data.materials.append(route_mat())
ROUTE_O.data.bevel_factor_mapping_end = 'SPLINE'
# the boys' marker in the chamber: a pulsing red beacon (sphere + ring) on the ledge, cross-section only
M_BEACON = mat("M_Beacon", (1.0, 0.05, 0.03), emit=((1.0, 0.08, 0.03), 8.0))
bpy.ops.mesh.primitive_uv_sphere_add(radius=4.0, location=(306.0, -2.0, 3.4)); BEACON = bpy.context.active_object; BEACON.name = "FX_Beacon"
BEACON.data.materials.append(M_BEACON); to_col(BEACON, C_FX)
bpy.ops.mesh.primitive_torus_add(major_radius=7.0, minor_radius=0.9, location=(306.0, -2.0, 3.4), rotation=(math.radians(90), 0, 0))
BRING = bpy.context.active_object; BRING.name = "FX_BeaconRing"; BRING.data.materials.append(M_BEACON); to_col(BRING, C_FX)
# the rescue lights moving along the route one by one (B12): small bright white-blue orbs
M_ORB = mat("M_Orb", (0.8, 0.95, 1.0), emit=((0.75, 0.92, 1.0), 14.0))
ORBS = []
for i in range(5):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.1, location=(300, -0.6, 2)); o = bpy.context.active_object; o.name = "FX_Orb%d" % i
    o.data.materials.append(M_ORB); to_col(o, C_FX); ORBS.append(o)

# ================================================================== characters
def suit_split(cloth, rig, top_mat, keep_bottom=True, bottom_mat=None):
    """per-face recolour of an MPFB suit: faces on the torso/arms get top_mat; the rest keep (or get) the bottom"""
    names = {b.name for b in rig.data.bones}; i2n = {g.index: g.name for g in cloth.vertex_groups if g.name in names}
    top = ("spine", "clavicle", "upperarm", "lowerarm", "neck", "breast", "pectoral", "shoulder", "wrist")
    vtop = []
    for v in cloth.data.vertices:
        best = (0, None)
        for g in v.groups:
            n = i2n.get(g.group)
            if n and g.weight > best[0]: best = (g.weight, n)
        vtop.append(best[1] is not None and best[1].startswith(top))
    me = cloth.data
    if bottom_mat is not None:
        me.materials.clear(); me.materials.append(bottom_mat)
    me.materials.append(top_mat); ti = len(me.materials) - 1
    for p in me.polygons:
        if sum(vtop[i] for i in p.vertices) >= len(p.vertices) / 2: p.material_index = ti
def solid_clothes(rig):
    for c in rig.children:
        if c.type == 'MESH' and any(k in c.name for k in ("suit", "shoes", "clothes")):
            so = c.modifiers.new("solid", 'SOLIDIFY'); so.thickness = 0.003; so.offset = 1.0; so.use_rim = True
            i = c.modifiers.find("solid")
            while i > c.modifiers.find("Armature") + 1:
                c.modifiers.move(i, i - 1); i -= 1
def hair_tint(rig, mult):
    for c in rig.children:
        if c.type == 'MESH' and any(k in c.name.lower() for k in ("short", "eyebrow", "afro", "bob")):
            for m in c.data.materials: tint(m, mult)
def finish_char(rig, skin_mult=(0.95, 0.72, 0.55)):
    eye_fix(rig)
    body = [c for c in rig.children if c.type == 'MESH' and c.name.endswith(".body")][0]
    for m in body.data.materials: tint(m, skin_mult)
    for c in rig.children:
        if c.type == 'MESH' and "teeth" in c.name:
            for m in c.data.materials: tint(m, (1.4, 1.35, 1.3))
    solid_clothes(rig)
    for c in rig.children: to_col(c, C_CHR)
    to_col(rig, C_CHR)
    return body
def jersey(name, c1, c2):
    """a football jersey: saturated body colour with two contrasting sleeve/side stripes"""
    m = fabric(name, c1, scale=800, bump=0.2)
    nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); sp = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sp.inputs[0])
    ab = nt.nodes.new("ShaderNodeMath"); ab.operation = 'ABSOLUTE'; nt.links.new(sp.outputs["X"], ab.inputs[0])
    cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.interpolation = 'CONSTANT'
    E = cr.color_ramp.elements; E[0].color = (*c1, 1); E[1].position = 0.155; E[1].color = (*c2, 1)
    e = E.new(0.185); e.color = (*c1, 1)
    nt.links.new(ab.outputs[0], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], p.inputs["Base Color"])
    return m
ASIAN = {"asian": 0.92, "caucasian": 0.04, "african": 0.04}
CHARS = {}
BOYS = [("Boy1", "short02", (0.85, 0.03, 0.03), (1.0, 0.85, 0.1), 0.24, 0.40),       # hero: red jersey, yellow stripes
        ("Boy2", "short03", (1.0, 0.62, 0.0), (0.02, 0.10, 0.6), 0.22, 0.32),        # orange
        ("Boy3", "short01", (0.02, 0.22, 0.85), (1, 1, 1), 0.27, 0.50),                # royal blue
        ("Boy4", "short04", (0.05, 0.55, 0.12), (1, 0.9, 0.1), 0.25, 0.44)]          # green
for nm, hair, c1, c2, age, hgt in BOYS:
    r, b = human(nm, 1.0, age, ASIAN, hair + "/" + hair + ".mhclo", "young_asian_male/young_asian_male.mhmat", "eyebrow001/eyebrow001.mhclo",
                 height=hgt, weight=0.42, muscle=0.5, clothes=["male_casualsuit06/male_casualsuit06.mhclo", "shoes02/shoes02.mhclo"])
    cl = [c for c in r.children if c.type == 'MESH' and "casualsuit" in c.name][0]
    suit_split(cl, r, jersey("M_Jersey_" + nm, c1, c2))
    hair_tint(r, (0.18, 0.15, 0.13))
    CHARS[nm] = (r, finish_char(r))
r, b = human("Coach", 1.0, 0.42, ASIAN, "short02/short02.mhclo", "young_asian_male/young_asian_male.mhmat", "eyebrow002/eyebrow002.mhclo",
             height=0.55, weight=0.45, muscle=0.6, clothes=["male_casualsuit01/male_casualsuit01.mhclo", "shoes01/shoes01.mhclo"])
cl = [c for c in r.children if c.type == 'MESH' and "casualsuit" in c.name][0]
suit_split(cl, r, fabric("M_CoachShirt", (0.0, 0.42, 0.40), scale=700))      # deep teal shirt over dark jeans
hair_tint(r, (0.18, 0.15, 0.13)); CHARS["Coach"] = (r, finish_char(r))
PANEL = {"Diver1": (0.0, 0.25, 0.95), "Diver2": (0.95, 0.30, 0.0), "Diver3": (0.0, 0.25, 0.95)}
for nm, race, hair, h_ in (("Diver1", {"asian": 0.5, "caucasian": 0.45, "african": 0.05}, "short04", 0.6),
                           ("Diver2", {"asian": 0.15, "caucasian": 0.80, "african": 0.05}, "short04", 0.62),
                           ("Diver3", {"asian": 0.3, "caucasian": 0.65, "african": 0.05}, "short04", 0.6)):
    r, b = human(nm, 1.0, 0.55, race, hair + "/" + hair + ".mhclo", "young_caucasian_male/young_caucasian_male.mhmat", "eyebrow003/eyebrow003.mhclo",
                 height=h_, weight=0.5, muscle=0.7, clothes=["male_casualsuit02/male_casualsuit02.mhclo", "shoes06/shoes06.mhclo"])
    cl = [c for c in r.children if c.type == 'MESH' and "casualsuit" in c.name][0]
    suit_split(cl, r, mat("M_NeoPanel_" + nm, PANEL[nm], rough=0.4), bottom_mat=mat("M_Neoprene", (0.025, 0.028, 0.035), rough=0.45, sheen=0.3))
    # the wetsuit: re-skin the whole top as neoprene too, keep the coloured panel only on the upper chest/shoulders
    for p in cl.data.polygons:
        c_ = p.center
        if p.material_index == 1 and not (c_.z > 1.25 and abs(c_.x) < 0.30): p.material_index = 0
    hair_tint(r, (0.35, 0.28, 0.22))
    sh = [c for c in r.children if c.type == 'MESH' and "shoes" in c.name][0]
    sh.data.materials.clear(); sh.data.materials.append(mat("M_Booty", (0.02, 0.02, 0.02), rough=0.6))
    CHARS[nm] = (r, finish_char(r, (0.95, 0.75, 0.60)))
r, b = human("Medic", 0.0, 0.40, {"asian": 0.85, "caucasian": 0.1, "african": 0.05}, "ponytail01/ponytail01.mhclo",
             "young_asian_female/young_asian_female.mhmat", "eyebrow010/eyebrow010.mhclo", height=0.45, weight=0.5,
             clothes=["female_casualsuit01/female_casualsuit01.mhclo", "shoes01/shoes01.mhclo"])
cl = [c for c in r.children if c.type == 'MESH' and "casualsuit" in c.name][0]
suit_split(cl, r, fabric("M_MedicTop", (0.9, 0.04, 0.03), scale=700))
for c in r.children:
    if c.type == 'MESH' and any(k in c.name.lower() for k in ("pony", "eyebrow")):
        for m in c.data.materials: tint(m, (0.2, 0.15, 0.12))
CHARS["Medic"] = (r, finish_char(r))
eye_group_fix()
for nm, (r, b) in CHARS.items():
    r["home"] = 1

# ================================================================== diver gear (separate pieces, bone-parented, fitted with clearance)
def parent_bone(o, rig, bone):
    mw = o.matrix_world.copy(); o.parent = rig; o.parent_type = 'BONE'; o.parent_bone = bone
    bpy.context.view_layer.update(); o.matrix_world = mw
def verts_world(objs, filt=None):
    out = []
    for o in objs:
        dg = bpy.context.evaluated_depsgraph_get(); e = o.evaluated_get(dg); me_ = e.to_mesh()
        out += [o.matrix_world @ v.co for v in me_.vertices if filt is None or filt(o.matrix_world @ v.co)]
        e.to_mesh_clear()
    return out
def bbox(pts):
    return Vector([min(p[i] for p in pts) for i in range(3)]), Vector([max(p[i] for p in pts) for i in range(3)])
M_HELMET = {"Diver1": mat("M_Helmet1", (1.0, 0.75, 0.0), rough=0.3, coat=0.5), "Diver2": mat("M_Helmet2", (0.95, 0.1, 0.05), rough=0.3, coat=0.5),
            "Diver3": mat("M_Helmet3", (1.0, 0.75, 0.0), rough=0.3, coat=0.5)}
M_BLACK = mat("M_BlackRubber", (0.015, 0.015, 0.018), rough=0.55)
M_METAL = mat("M_Metal", (0.8, 0.8, 0.82), rough=0.25, metal=1.0)
M_TANK = mat("M_Tank", (0.95, 0.95, 0.92), rough=0.3, coat=0.6)
M_VEST = mat("M_Vest", (0.06, 0.07, 0.08), rough=0.6, sheen=0.2)
M_GLASS = bpy.data.materials.new("M_MaskGlass"); M_GLASS.use_nodes = True
_nt = M_GLASS.node_tree; _p = _nt.nodes["Principled BSDF"]; _p.inputs["Transmission Weight"].default_value = 1.0
_p.inputs["Roughness"].default_value = 0.02; _p.inputs["IOR"].default_value = 1.05; _p.inputs["Base Color"].default_value = (0.9, 0.97, 1.0, 1)
M_FIN = mat("M_Fin", (1.0, 0.82, 0.0), rough=0.4)
M_LENS = mat("M_TorchLens", (1, 1, 0.95), emit=((1.0, 0.95, 0.85), 30.0))
def ellipsoid_shell(name, c, r, m_, zcut=None, ycut=None, thick=0.006, seg=40):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, radius=1.0, location=(0, 0, 0))
    o = bpy.context.active_object; o.name = name
    bm = bmesh.new(); bm.from_mesh(o.data)
    kill = [v for v in bm.verts if (zcut is not None and v.co.z < zcut) or (ycut is not None and v.co.y > ycut)]
    bmesh.ops.delete(bm, geom=kill, context='VERTS')
    for v in bm.verts: v.co = Vector((v.co.x * r.x, v.co.y * r.y, v.co.z * r.z))
    bm.to_mesh(o.data); bm.free(); o.location = c
    so = o.modifiers.new("solid", 'SOLIDIFY'); so.thickness = thick; so.offset = 1.0
    o.data.materials.append(m_); bpy.ops.object.shade_smooth(); to_col(o, C_PROP)
    return o
def head_region(rig):
    hb = ("head", "jaw", "eye", "orbic", "oris", "levator", "risor", "temporal", "neck03")
    objs = [c for c in rig.children if c.type == 'MESH' and (c.name.endswith(".body") or "short" in c.name or "pony" in c.name)]
    eye_z = rig.data.bones["eye.L"].head_local.z
    pts = verts_world(objs, lambda p: p.z > eye_z - 0.16 and abs(p.x) < 0.14 and abs(p.y - rig.data.bones["head"].head_local.y) < 0.16)
    return bbox(pts), eye_z
GEAR = {}
for nm in ("Diver1", "Diver2", "Diver3"):
    rig, body = CHARS[nm]; B = rig.data.bones; parts = []
    (mn, mx), eye_z = head_region(rig)
    hc = (mn + mx) / 2
    # helmet: shell over the skull above the brow, 1.5 cm clear of the hair; torch on the brow
    hr = Vector(((mx.x - mn.x) / 2 + 0.02, (mx.y - mn.y) / 2 + 0.02, (mx.z - eye_z) + 0.0))
    helm = ellipsoid_shell(nm + "_Helmet", Vector((hc.x, hc.y + 0.005, eye_z + 0.035)), Vector((hr.x, hr.y, hr.z - 0.01)), M_HELMET[nm], zcut=0.0, thick=0.008)
    parts.append((helm, "head"))
    front_y = mn.y                       # the face front (most -Y point near the eyes)
    face_pts = verts_world([body], lambda p: abs(p.z - eye_z) < 0.03 and abs(p.x) < 0.05)
    fy = min(p.y for p in face_pts)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.022, depth=0.05, location=(0, hc.y - hr.y + 0.005, eye_z + 0.075), rotation=(math.radians(90), 0, 0))
    torch = bpy.context.active_object; torch.name = nm + "_HeadTorch"; torch.data.materials.append(M_BLACK); to_col(torch, C_PROP)
    bpy.ops.mesh.primitive_circle_add(vertices=24, radius=0.019, fill_type='NGON', location=(0, hc.y - hr.y - 0.0205, eye_z + 0.075), rotation=(math.radians(90), 0, 0))
    lens = bpy.context.active_object; lens.name = nm + "_TorchLens"; lens.data.materials.append(M_LENS); to_col(lens, C_PROP)
    parts += [(torch, "head"), (lens, "head")]
    L = bpy.data.lights.new(nm + "_Beam", 'SPOT'); L.energy = 60.0; L.spot_size = math.radians(42); L.spot_blend = 0.6; L.color = (1.0, 0.95, 0.85)
    L.shadow_soft_size = 0.02
    lo = bpy.data.objects.new(nm + "_Beam", L); C_PROP.objects.link(lo)
    lo.location = (0, hc.y - hr.y - 0.03, eye_z + 0.075); lo.rotation_euler = (math.radians(95), 0, 0)
    parts.append((lo, "head"))
    # mask: a black rubber frame + clear glass in front of the eyes, skirt 5 mm off the face
    mw_ = 0.15; mh_ = 0.075
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, fy - 0.022, eye_z + 0.006))
    fr = bpy.context.active_object; fr.name = nm + "_MaskFrame"; fr.scale = (mw_, 0.032, mh_); bpy.ops.object.transform_apply(scale=True)
    bv = fr.modifiers.new("bev", 'BEVEL'); bv.width = 0.02; bv.segments = 4
    bm = bmesh.new(); bm.from_mesh(fr.data)      # hollow it: remove the front and back faces (a frame ring), solidify
    kill = [f_ for f_ in bm.faces if abs(f_.normal.y) > 0.9]
    bmesh.ops.delete(bm, geom=kill, context='FACES'); bm.to_mesh(fr.data); bm.free()
    so = fr.modifiers.new("solid", 'SOLIDIFY'); so.thickness = 0.006
    fr.data.materials.append(M_BLACK); to_col(fr, C_PROP)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, fy - 0.036, eye_z + 0.006), rotation=(math.radians(90), 0, 0))
    gl = bpy.context.active_object; gl.name = nm + "_MaskGlass"; gl.scale = (mw_ - 0.012, mh_ - 0.012, 1); bpy.ops.object.transform_apply(scale=True)
    gl.data.materials.append(M_GLASS); to_col(gl, C_PROP)
    parts += [(fr, "head"), (gl, "head")]
    # mask strap: a flat band around the back of the head, 1.2 cm off the hair, at eye height (under the helmet rim)
    bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.012, major_segments=48, minor_segments=6, location=(hc.x, hc.y + 0.01, eye_z + 0.01))
    st = bpy.context.active_object; st.name = nm + "_MaskStrap"
    st.scale = ((mx.x - mn.x) / 2 + 0.014, (mx.y - mn.y) / 2 + 0.012, 0.6); bpy.ops.object.transform_apply(scale=True)
    bm = bmesh.new(); bm.from_mesh(st.data); bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.y < -0.045 + 0], context='VERTS'); bm.to_mesh(st.data); bm.free()
    st.data.materials.append(M_BLACK); to_col(st, C_PROP); parts.append((st, "head"))
    # regulator: second stage in front of the mouth + mouthpiece; hose to the chest
    mz = B["jaw"].tail_local.z if "jaw" in B else eye_z - 0.08
    mouth_pts = verts_world([body], lambda p: abs(p.z - (eye_z - 0.075)) < 0.012 and abs(p.x) < 0.02)
    my = min(p.y for p in mouth_pts)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.03, depth=0.035, location=(0, my - 0.032, eye_z - 0.078), rotation=(math.radians(90), 0, 0))
    reg = bpy.context.active_object; reg.name = nm + "_Regulator"; reg.data.materials.append(M_BLACK); to_col(reg, C_PROP)
    bv = reg.modifiers.new("bev", 'BEVEL'); bv.width = 0.008; bv.segments = 3
    parts.append((reg, "head"))
    # tank on the back: find the back surface over the shoulder blades
    back_pts = verts_world([c for c in rig.children if c.type == 'MESH' and "suit" in c.name], lambda p: 1.05 < p.z < 1.40 and abs(p.x) < 0.12)
    by = max(p.y for p in back_pts)
    sz = B["spine05"].head_local.z
    bpy.ops.mesh.primitive_cylinder_add(radius=0.088, depth=0.56, location=(0, by + 0.035 + 0.088, sz - 0.08))
    tk = bpy.context.active_object; tk.name = nm + "_Tank"; tk.data.materials.append(M_TANK); to_col(tk, C_PROP)
    bv = tk.modifiers.new("bev", 'BEVEL'); bv.width = 0.05; bv.segments = 6; bv.limit_method = 'ANGLE'; bpy.ops.object.shade_smooth()
    bpy.ops.mesh.primitive_cylinder_add(radius=0.02, depth=0.07, location=(0, by + 0.123, sz - 0.08 + 0.31))
    vl = bpy.context.active_object; vl.name = nm + "_TankValve"; vl.data.materials.append(M_METAL); to_col(vl, C_PROP)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.012, depth=0.12, location=(0, by + 0.123, sz - 0.08 + 0.345), rotation=(0, math.radians(90), 0))
    vk = bpy.context.active_object; vk.name = nm + "_TankKnob"; vk.data.materials.append(M_BLACK); to_col(vk, C_PROP)
    parts += [(tk, "spine04"), (vl, "spine04"), (vk, "spine04")]
    # BCD vest: a separate garment 2.2 cm over the wetsuit on the torso only (body hidden under the suit already)
    vest, _cov = garment(rig, body, nm + "_Vest", lambda co, bn: bn is not None and bn.startswith(("spine", "clavicle", "breast", "pectoral"))
                         and 0.98 < co.z < 1.42, [], 0.028, M_VEST, thick=0.012)
    to_col(vest, C_PROP)
    # tank cam bands: two black rings around the tank (bands tie it to the vest)
    for k_, dz in enumerate((0.10, -0.12)):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.093, minor_radius=0.008, location=(0, by + 0.123, sz - 0.08 + dz))
        bd = bpy.context.active_object; bd.name = nm + "_TankBand%d" % k_; bd.data.materials.append(M_BLACK); to_col(bd, C_PROP)
        parts.append((bd, "spine04"))
    # fins on the boots: a foot pocket box clear of the shoe + a long blade beyond the toes
    for s in "LR":
        shoe = [c for c in rig.children if c.type == 'MESH' and "shoes" in c.name][0]
        sx = 1 if s == "L" else -1
        fp = verts_world([shoe], lambda p: p.x * sx > 0)
        smn, smx = bbox(fp)
        cx = (smn.x + smx.x) / 2
        bpy.ops.mesh.primitive_cube_add(size=1, location=(cx, (smn.y + smx.y) / 2 - 0.01, smn.z + 0.045))
        pk = bpy.context.active_object; pk.name = nm + "_FinPocket." + s
        pk.scale = (smx.x - smn.x + 0.03, smx.y - smn.y - 0.06, 0.07); bpy.ops.object.transform_apply(scale=True)
        bv = pk.modifiers.new("bev", 'BEVEL'); bv.width = 0.015; bv.segments = 3; pk.data.materials.append(M_BLACK); to_col(pk, C_PROP)
        bm = bmesh.new()
        tip_y = smn.y - 0.42; w0 = smx.x - smn.x + 0.02
        vs = [bm.verts.new(p) for p in ((cx - w0 / 2, smn.y + 0.05, smn.z + 0.02), (cx + w0 / 2, smn.y + 0.05, smn.z + 0.02),
                                        (cx + 0.12, tip_y, smn.z + 0.0), (cx + 0.02, tip_y + 0.04, smn.z + 0.0), (cx - 0.02, tip_y + 0.04, smn.z + 0.0), (cx - 0.12, tip_y, smn.z))]
        bm.faces.new(vs); me_ = bpy.data.meshes.new(nm + "_Fin." + s); bm.to_mesh(me_); bm.free()
        fn = bpy.data.objects.new(nm + "_Fin." + s, me_); C_PROP.objects.link(fn); me_.materials.append(M_FIN)
        so = fn.modifiers.new("solid", 'SOLIDIFY'); so.thickness = 0.008; so.offset = 0
        parts += [(pk, "foot." + s), (fn, "foot." + s)]
    for o, bn in parts: parent_bone(o, rig, bn)
    GEAR[nm] = [o.name for o, _ in parts] + [vest.name]
    rig["gear"] = ",".join(GEAR[nm])

# ================================================================== props
def imp_ph_model(asset, name):
    r, objs = append_ph(asset, name + "_root", (0, 0, 0), collection=C_PROP)
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw; o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    if len(objs) > 1: bpy.ops.object.join()
    o = bpy.context.active_object; o.name = name
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.data.objects.remove(r, do_unlink=True)
    return o
# flashlights for the coach and two boys (the same CC0 model, recoloured red/yellow/blue bodies)
TORCH_SRC = imp_ph_model("pastic_torch_6v", "Torch_src")
dims = TORCH_SRC.dimensions; print("TORCH dims", tuple(dims))
TORCHES = []
for i, (nm, c) in enumerate((("Torch_Coach", (1, 0.8, 0)), ("Torch_Boy1", (1, 0.1, 0.05)), ("Torch_Boy3", (0.1, 0.4, 1)))):
    t = TORCH_SRC.copy(); t.data = TORCH_SRC.data.copy(); t.name = nm; C_PROP.objects.link(t)
    for m in t.data.materials: tint(m, c)
    L = bpy.data.lights.new(nm + "_Beam", 'SPOT'); L.energy = 45.0; L.spot_size = math.radians(38); L.spot_blend = 0.5; L.color = (1.0, 0.93, 0.8)
    lo = bpy.data.objects.new(nm + "_Beam", L); C_PROP.objects.link(lo); lo.parent = t
    TORCHES.append(t)
bpy.data.objects.remove(TORCH_SRC, do_unlink=True)
# the gear bag with the DA KRAS FILMS logo (white logo on a dark navy dry bag), on the ledge
def logo_mat(name, base, logo_file, rect):
    m = mat(name, base, rough=0.55); nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    img = bpy.data.images.load(os.path.join(PKG, "..", "assets", "brand", logo_file), check_existing=True)
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping")
    (u0, v0, u1, v1) = rect
    mp.inputs["Location"].default_value = (-u0 / (u1 - u0), -v0 / (v1 - v0), 0); mp.inputs["Scale"].default_value = (1 / (u1 - u0), 1 / (v1 - v0), 1)
    tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = img; tx.extension = 'CLIP'
    nt.links.new(tc.outputs["UV"], mp.inputs["Vector"]); nt.links.new(mp.outputs["Vector"], tx.inputs["Vector"])
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.inputs["A"].default_value = (*base, 1)
    nt.links.new(tx.outputs["Color"], mx.inputs["B"]); nt.links.new(tx.outputs["Alpha"], mx.inputs["Factor"])
    nt.links.new(mx.outputs["Result"], p.inputs["Base Color"])
    return m
bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=0.7, vertices=40, location=(0, 0, 0), rotation=(0, math.radians(90), 0))
BAG = bpy.context.active_object; BAG.name = "GearBag"; bpy.ops.object.transform_apply(rotation=True)
BAG.data.materials.append(mat("M_BagEnd", (0.9, 0.55, 0.0), rough=0.5))
BAG.data.materials.append(logo_mat("M_BagLogo", (0.01, 0.04, 0.22), "DaKrasFilms_logo_white.png", (0.03, 0.25, 0.47, 0.75)))
for p in BAG.data.polygons: p.material_index = 1 if abs(p.normal.x) < 0.5 else 0
bv = BAG.modifiers.new("bev", 'BEVEL'); bv.width = 0.05; bv.segments = 4; bv.limit_method = 'ANGLE'; bpy.ops.object.shade_smooth()
to_col(BAG, C_PROP)
# spare tank and a coil of rope beside the bag
bpy.ops.mesh.primitive_cylinder_add(radius=0.088, depth=0.56, location=(0, 0, 0), rotation=(0, math.radians(90), 0))
SPARE = bpy.context.active_object; SPARE.name = "SpareTank"; bpy.ops.object.transform_apply(rotation=True)
SPARE.data.materials.append(mat("M_SpareTank", (1.0, 0.8, 0.0), rough=0.3, coat=0.5))
bv = SPARE.modifiers.new("bev", 'BEVEL'); bv.width = 0.05; bv.segments = 6; bv.limit_method = 'ANGLE'; bpy.ops.object.shade_smooth(); to_col(SPARE, C_PROP)
# the syringe: barrel (clear), plunger (white), flange, needle (steel), orange cap removed; 13 cm long
def syringe():
    parts = []
    bpy.ops.mesh.primitive_cylinder_add(radius=0.0065, depth=0.075, location=(0, 0, 0), rotation=(0, math.radians(90), 0))
    b_ = bpy.context.active_object; b_.data.materials.append(M_GLASS); parts.append(b_)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.0052, depth=0.05, location=(-0.012, 0, 0), rotation=(0, math.radians(90), 0))
    lq = bpy.context.active_object; lq.data.materials.append(mat("M_Drug", (0.2, 0.75, 1.0), rough=0.1, emit=((0.1, 0.5, 1.0), 0.6))); parts.append(lq)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.0045, depth=0.06, location=(-0.06, 0, 0), rotation=(0, math.radians(90), 0))
    pl = bpy.context.active_object; pl.data.materials.append(mat("M_Plunger", (0.95, 0.95, 0.95), rough=0.4)); parts.append(pl)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.011, depth=0.003, location=(-0.091, 0, 0), rotation=(0, math.radians(90), 0))
    th = bpy.context.active_object; th.data.materials.append(pl.data.materials[0]); parts.append(th)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(-0.0375, 0, 0)); fl = bpy.context.active_object; fl.scale = (0.003, 0.03, 0.012)
    bpy.ops.object.transform_apply(scale=True); fl.data.materials.append(pl.data.materials[0]); parts.append(fl)
    bpy.ops.mesh.primitive_cone_add(radius1=0.0045, radius2=0.0015, depth=0.008, location=(0.0415, 0, 0), rotation=(0, math.radians(90), 0))
    hb = bpy.context.active_object; hb.data.materials.append(mat("M_Hub", (0.95, 0.45, 0.0), rough=0.4)); parts.append(hb)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.0004, depth=0.025, location=(0.058, 0, 0), rotation=(0, math.radians(90), 0))
    nd = bpy.context.active_object; nd.data.materials.append(M_METAL); parts.append(nd)
    bpy.ops.object.select_all(action='DESELECT')
    for o in parts: o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]; bpy.ops.object.join()
    o = bpy.context.active_object; o.name = "Syringe"; to_col(o, C_PROP); return o
SYR = syringe()
# the boy's full-face mask: a black silicone skirt, a big clear visor, a small regulator block, spider straps
def full_mask():
    rig, body = CHARS["Boy1"]; (mn, mx), eye_z = head_region(rig)
    hc = (mn + mx) / 2
    face_pts = verts_world([body], lambda p: eye_z - 0.13 < p.z < eye_z + 0.05 and abs(p.x) < 0.075 and p.y < hc.y)
    fy = min(p.y for p in face_pts)                     # nose tip
    cz = eye_z - 0.045
    # visor: front half of an ellipsoid, 2.2 cm off the nose tip
    vis = ellipsoid_shell("FFM_Visor", Vector((0, fy + 0.055, cz)), Vector((0.085, 0.085, 0.105)), M_GLASS, ycut=0.0, thick=0.003)
    sk = ellipsoid_shell("FFM_Skirt", Vector((0, fy + 0.058, cz)), Vector((0.093, 0.075, 0.113)), M_BLACK, ycut=-0.35, thick=0.008)
    bm = bmesh.new(); bm.from_mesh(sk.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.y < -0.62], context='VERTS'); bm.to_mesh(sk.data); bm.free()
    bpy.ops.mesh.primitive_cylinder_add(radius=0.024, depth=0.03, location=(0, fy - 0.040, cz - 0.05), rotation=(math.radians(90), 0, 0))
    rg = bpy.context.active_object; rg.name = "FFM_Reg"; rg.data.materials.append(mat("M_FFMReg", (1.0, 0.75, 0.0), rough=0.35)); to_col(rg, C_PROP)
    straps = []
    for k_, (dz, sy) in enumerate(((0.03, 1.0), (-0.035, 0.95))):
        bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.008, major_segments=48, minor_segments=6, location=(hc.x, hc.y + 0.005, cz + dz))
        st = bpy.context.active_object; st.name = "FFM_Strap%d" % k_
        st.scale = ((mx.x - mn.x) / 2 + 0.016, ((mx.y - mn.y) / 2 + 0.016) * sy, 0.7); bpy.ops.object.transform_apply(scale=True)
        bm = bmesh.new(); bm.from_mesh(st.data); bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.y < -0.02], context='VERTS')
        bm.to_mesh(st.data); bm.free(); st.data.materials.append(M_BLACK); to_col(st, C_PROP); straps.append(st)
    # one object (rigid): join visor-less parts; the visor stays separate (glass) but parented to the skirt
    bpy.ops.object.select_all(action='DESELECT')
    for o in [sk, rg]: o.select_set(True)
    bpy.context.view_layer.objects.active = sk; bpy.ops.object.join(); sk.name = "FullMask"
    bpy.ops.object.select_all(action='DESELECT')
    for o in straps: o.select_set(True)
    bpy.context.view_layer.objects.active = straps[0]; bpy.ops.object.join(); straps[0].name = "FullMaskStraps"
    parent_bone(straps[0], rig, "head")
    for o in (sk, vis):
        pass
    so = sk.modifiers.new("solid", 'SOLIDIFY'); so.thickness = 0.006
    vis.parent = sk; vis.matrix_parent_inverse = sk.matrix_world.inverted()
    sk["fit_head"] = 1
    return sk
FFM = full_mask()
# the orange SKED-style rescue wrap/stretcher: a long shallow tray (open top), rails and four grab loops
def sked():
    bm = bmesh.new(); L_, W_, H_ = 1.75, 0.62, 0.20
    nU, nV = 36, 14; vv = []
    for i in range(nU + 1):
        x = -L_ / 2 + L_ * i / nU
        taper = 1.0 - 0.18 * (abs(x) / (L_ / 2)) ** 4
        row = []
        for j in range(nV + 1):
            t = -1 + 2 * j / nV
            y = W_ / 2 * t * taper; z = H_ * (abs(t) ** 2.4)
            if abs(x) > L_ / 2 - 0.12: z += 0.10 * ((abs(x) - (L_ / 2 - 0.12)) / 0.12) ** 2
            row.append(bm.verts.new((x, y, z)))
        vv.append(row)
    for i in range(nU):
        for j in range(nV): bm.faces.new((vv[i][j], vv[i + 1][j], vv[i + 1][j + 1], vv[i][j + 1]))
    me_ = bpy.data.meshes.new("Sked"); bm.to_mesh(me_); bm.free()
    o = bpy.data.objects.new("Sked", me_); C_PROP.objects.link(o)
    o.data.materials.append(mat("M_Sked", (1.0, 0.22, 0.0), rough=0.4, coat=0.4))
    so = o.modifiers.new("solid", 'SOLIDIFY'); so.thickness = 0.008; so.offset = -1
    for p in me_.polygons: p.use_smooth = True
    # grab loops (black webbing) on the long sides
    for k_, (x, s) in enumerate(((-0.74, 1), (0.74, 1), (-0.74, -1), (0.74, -1))):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.06, minor_radius=0.011, location=(x, s * 0.295, H_ + 0.02), rotation=(math.radians(90), 0, 0))
        lp = bpy.context.active_object; lp.name = "Sked_Loop%d" % k_; lp.data.materials.append(mat("M_Webbing", (0.02, 0.02, 0.02), rough=0.7))
        to_col(lp, C_PROP); lp.parent = o
    o["L"] = L_; o["W"] = W_; o["H"] = H_
    return o
SKED = sked()
# the yellow guide line along the floor of sump 2, the restriction, into the chamber pool
cu = bpy.data.curves.new("GuideLine", 'CURVE'); cu.dimensions = '3D'; sp_ = cu.splines.new('POLY')
gx = [228 + 0.5 * i for i in range(130)]; sp_.points.add(len(gx) - 1)
for i, x in enumerate(gx):
    w, h = prof(x); sp_.points[i].co = (x, 0.25 * w * math.sin(x * 0.13), floor_z(x) + 0.25 + 0.05 * math.sin(x * 0.7), 1)
cu.bevel_depth = 0.006; cu.bevel_resolution = 2
GUIDE = bpy.data.objects.new("GuideLine", cu); C_PROP.objects.link(GUIDE); cu.materials.append(mat("M_Guide", (1.0, 0.85, 0.0), rough=0.4, emit=((1.0, 0.8, 0.0), 0.4)))
# silt clouds stirred up at the restriction (soft brown volume, grown in by scale)
M_SILT = bpy.data.materials.new("M_Silt"); M_SILT.use_nodes = True; nt = M_SILT.node_tree
for n in list(nt.nodes):
    if n.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n)
pv = nt.nodes.new("ShaderNodeVolumePrincipled"); pv.inputs["Color"].default_value = (0.75, 0.55, 0.32, 1); pv.inputs["Density"].default_value = 0.5
nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 2.5; tcx = nt.nodes.new("ShaderNodeTexCoord")
nt.links.new(tcx.outputs["Object"], nz.inputs["Vector"])
mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.45; mr.inputs["From Max"].default_value = 0.7
mr.inputs["To Max"].default_value = 0.5; nt.links.new(nz.outputs["Fac"], mr.inputs["Value"]); nt.links.new(mr.outputs["Result"], pv.inputs["Density"])
nt.links.new(pv.outputs[0], [n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'][0].inputs["Volume"])
SILT = []
for i, x in enumerate((278.0, 281.0, 275.0)):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1.0, location=(x, 0.1 * i, floor_z(x) + 0.35))
    o = bpy.context.active_object; o.name = "FX_Silt%d" % i; o.scale = (0.9, 0.6, 0.4); o.data.materials.append(M_SILT); to_col(o, C_FX); SILT.append(o)
# rain: thin, translucent slanted streaks instanced on a box of points; the whole sheet moves down (keyed empty, looped)
RAINCTL = bpy.data.objects.new("RainCtl", None); C_FX.objects.link(RAINCTL)
bm = bmesh.new(); rr = random.Random(3)
for i in range(4500):
    x = rr.uniform(-40, -0.8); y = rr.uniform(-16, 16); z = rr.uniform(0, 24)
    v0 = bm.verts.new((x, y, z)); v1 = bm.verts.new((x + 0.05, y + 0.02, z + 0.55)); v2 = bm.verts.new((x + 0.055, y + 0.024, z + 0.55))
    v3 = bm.verts.new((x + 0.005, y + 0.004, z)); bm.faces.new((v0, v3, v2, v1))
me_ = bpy.data.meshes.new("FX_Rain"); bm.to_mesh(me_); bm.free()
RAIN = bpy.data.objects.new("FX_Rain", me_); C_FX.objects.link(RAIN)
mr_ = bpy.data.materials.new("M_Rain"); mr_.use_nodes = True; nt = mr_.node_tree
for n in list(nt.nodes):
    if n.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n)
tr = nt.nodes.new("ShaderNodeBsdfTransparent"); em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (0.8, 0.88, 1.0, 1)
em.inputs["Strength"].default_value = 1.2; ms = nt.nodes.new("ShaderNodeMixShader"); ms.inputs["Fac"].default_value = 0.35
nt.links.new(tr.outputs[0], ms.inputs[1]); nt.links.new(em.outputs[0], ms.inputs[2])
nt.links.new(ms.outputs[0], [n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'][0].inputs["Surface"])
me_.materials.append(mr_)
RAIN2 = RAIN.copy(); RAIN2.name = "FX_Rain2"; C_FX.objects.link(RAIN2); RAIN2.location.z = 24.0
RAIN.parent = RAINCTL; RAIN2.parent = RAINCTL
for o in (RAIN, RAIN2): o.visible_shadow = False

# ---- the ambulance outside (white box van, red stripe and light bar, logo on the side door), on the jungle track
def ambulance():
    parts = []
    W_white = mat("M_AmbWhite", (0.92, 0.93, 0.95), rough=0.3, coat=0.6)
    def bx(nm, s, l, m_, bev=0.04):
        o = box(nm, s, l, m_, bevel=bev); to_col(o, C_SET); parts.append(o); return o
    bx("Amb_Body", (2.0, 3.4, 2.1), (0, 0.6, 1.45), W_white, 0.06)
    bx("Amb_Cab", (2.0, 1.7, 1.55), (0, -1.95, 1.2), W_white, 0.08)
    bx("Amb_Windscreen", (1.85, 0.05, 0.7), (0, -2.79, 1.6), mat("M_AmbGlass", (0.02, 0.03, 0.05), rough=0.05, coat=1.0), 0.02)
    bx("Amb_Stripe", (2.02, 5.06, 0.22), (0, -0.25, 1.05), mat("M_AmbRed", (0.85, 0.02, 0.02), rough=0.35, coat=0.5), 0.01)
    bx("Amb_LightBar", (1.4, 0.3, 0.12), (0, -1.6, 2.05), mat("M_AmbLight", (0.1, 0.3, 1.0), emit=((0.1, 0.35, 1.0), 25.0)), 0.02)
    # logo on the side door (the near side faces -X)
    lg = box("Amb_LogoPanel", (0.01, 1.4, 0.7), (-1.006, 0.9, 1.55), logo_mat("M_AmbLogo", (0.92, 0.93, 0.95), "DaKrasFilms_logo_dark.png", (0.0, 0.0, 1.0, 1.0)), bevel=0)
    bpy.context.view_layer.objects.active = lg
    lg.data.uv_layers.new(name="UVMap")
    for poly in lg.data.polygons:
        for li in poly.loop_indices:
            v = lg.data.vertices[lg.data.loops[li].vertex_index].co
            lg.data.uv_layers[0].data[li].uv = ((-(v.y - 0.9) / 1.4) + 0.5, (v.z - 1.55) / 0.7 + 0.5)
    to_col(lg, C_SET); parts.append(lg)
    for k_, (x, y) in enumerate(((-0.85, -1.9), (0.85, -1.9), (-0.85, 1.4), (0.85, 1.4))):
        o = cyl("Amb_Wheel%d" % k_, 0.38, 0.28, (x, y, 0.38), M_BLACK, rot=(0, math.radians(90), 0)); to_col(o, C_SET); parts.append(o)
    root = bpy.data.objects.new("Ambulance", None); C_SET.objects.link(root)
    for o in parts: o.parent = root
    root.location = (-6.5, -7.5, mount_h(-6.5, -7.5)); root.rotation_euler.z = math.radians(-156)
    root.parent = FRONT
    return root
AMB = ambulance()

# ================================================================== lights (cave fills are hidden emitters; daylight sun + HDRI)
def light(name, kind, energy, loc, rot=(0, 0, 0), size=1.0, color=(1, 1, 1)):
    L = bpy.data.lights.new(name, kind); L.energy = energy; L.color = color
    if kind == 'AREA': L.size = size; L.shape = 'DISK'
    if kind == 'SUN': L.angle = math.radians(3)
    o = bpy.data.objects.new(name, L); C_SET.objects.link(o); o.location = loc; o.rotation_euler = rot
    return o
SUN = light("Sun", 'SUN', 3.0, (0, 0, 50), rot=(math.radians(40), 0, math.radians(-60)), color=(1.0, 0.92, 0.78))
# the chamber: warm torch-bounce fills (the boys' torches + the divers' lamps carry the key)
light("CH_Fill1", 'AREA', 420, (300.0, -3.5, 6.0), rot=(math.radians(30), 0, math.radians(-20)), size=3.0, color=(1.0, 0.72, 0.45))
light("CH_Fill2", 'AREA', 260, (308.0, -2.0, 5.5), rot=(math.radians(35), 0, math.radians(30)), size=3.0, color=(0.55, 0.75, 1.0))
light("CH_Rim", 'AREA', 200, (306.0, 6.5, 5.0), rot=(math.radians(-50), 0, 0), size=2.0, color=(1.0, 0.6, 0.3))
# the passage near the mouth: daylight spill + a warm fill deeper in
light("TN_Fill0", 'AREA', 500, (3.5, 0.0, 3.6), rot=(0, 0, 0), size=3.0, color=(1.0, 0.8, 0.6))
light("TN_Fill1", 'AREA', 400, (12.0, -1.0, 3.3), rot=(0, 0, 0), size=2.5, color=(1.0, 0.75, 0.5))
light("TN_Fill2", 'AREA', 220, (24.0, 0.8, 3.0), rot=(0, 0, 0), size=2.5, color=(1.0, 0.65, 0.4))
# sump: a dim green-blue glow so the divers read as silhouettes against their lamps (keyed later)
light("SU_Glow", 'POINT', 60, (281.0, 0.0, -2.2), rot=(0, 0, 0), size=3.0, color=(0.3, 0.8, 0.7))

# ================================================================== look and render settings (fast, zero-error)
sc.render.engine = 'CYCLES'; cy = sc.cycles
cy.samples = 64; cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.05
cy.use_denoising = True; cy.denoiser = 'OPENIMAGEDENOISE'
cy.max_bounces = 6; cy.diffuse_bounces = 3; cy.glossy_bounces = 3; cy.transmission_bounces = 6; cy.transparent_max_bounces = 16
cy.volume_bounces = 0; cy.volume_step_rate = 4.0
cy.caustics_reflective = False; cy.caustics_refractive = False
sc.render.use_persistent_data = True
sc.render.use_simplify = True; sc.render.simplify_subdivision_render = 2; cy.texture_limit_render = '2048'
sc.render.use_motion_blur = False
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Punchy'; sc.view_settings.exposure = 0.0
sc.world = sc.world or bpy.data.worlds.new("World")
w = sc.world; w.use_nodes = True; nt = w.node_tree
for n in list(nt.nodes):
    if n.type != 'OUTPUT_WORLD': nt.nodes.remove(n)
outw = [n for n in nt.nodes if n.type == 'OUTPUT_WORLD'][0]
env = nt.nodes.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(os.path.join(PH, "hdri", "mossy_forest_1k.hdr"))
# camera rays see a saturated sky gradient; lighting comes from the HDRI (light path mix)
tc = nt.nodes.new("ShaderNodeNewGeometry"); sp = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Incoming"], sp.inputs[0])
mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.0; mr.inputs["From Max"].default_value = -0.7; nt.links.new(sp.outputs["Z"], mr.inputs["Value"])
cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (0.22, 0.55, 1.0, 1); cr.color_ramp.elements[1].color = (0.01, 0.12, 0.75, 1)
nt.links.new(mr.outputs["Result"], cr.inputs["Fac"])
b1 = nt.nodes.new("ShaderNodeBackground"); b1.name = "SkyBG"; b1.inputs["Strength"].default_value = 1.0; nt.links.new(cr.outputs["Color"], b1.inputs["Color"])
b2 = nt.nodes.new("ShaderNodeBackground"); b2.name = "HdriBG"; b2.inputs["Strength"].default_value = 1.2; nt.links.new(env.outputs["Color"], b2.inputs["Color"])
lp = nt.nodes.new("ShaderNodeLightPath"); ms = nt.nodes.new("ShaderNodeMixShader")
nt.links.new(lp.outputs["Is Camera Ray"], ms.inputs["Fac"]); nt.links.new(b2.outputs[0], ms.inputs[1]); nt.links.new(b1.outputs[0], ms.inputs[2])
nt.links.new(ms.outputs[0], outw.inputs["Surface"])
# keep the library sources out of the render, then save
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("BUILD_DONE", OUT)
