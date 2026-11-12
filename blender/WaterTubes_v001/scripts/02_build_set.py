"""WaterTubes set: street, houses, vegetation, tube ring (GN fill front), flood surface (GN), cutaway shell, materials, world.
blender -b --factory-startup --python 02_build_set.py -- <scratch_dir> <out.blend>"""
import bpy, sys, os, math, glob, random
import bmesh
from mathutils import Vector, Matrix, noise
a = sys.argv[sys.argv.index("--") + 1:]
S, OUT = a[0], a[1]
PH = S + "/ph"
random.seed(33)
R_ = math.radians
def rin(node, nm, typ):
    return next(x for x in node.inputs if x.name == nm and x.type == typ)
def rout(node, typ):
    return next(x for x in node.outputs if x.type == typ)
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob)
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, 100
sc.render.fps, sc.render.fps_base = 60, 1.0
sc.frame_start, sc.frame_end = 1, 2010
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = 48; sc.cycles.adaptive_threshold = 0.05; sc.cycles.use_denoising = True; sc.cycles.denoiser = "OPENIMAGEDENOISE"
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"
sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = 0.5
sc.cycles.max_bounces = 6; sc.cycles.transparent_max_bounces = 16

def coll(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in sc.collection.children: sc.collection.children.link(c)
    return c
C_SET, C_HOUSE, C_TUBE, C_WATER, C_FX, C_VEG = (coll(n) for n in ("Set", "Houses", "Tubes", "Water", "FX", "Vegetation"))
def link(ob, c):
    for u in list(ob.users_collection): u.objects.unlink(ob)
    c.objects.link(ob); return ob

# ------------------------------------------------------------------ material helpers
def img(path, non_color=False):
    im = bpy.data.images.load(path, check_existing=True)
    if non_color: im.colorspace_settings.name = "Non-Color"
    return im
def pbr(name, tex_id, scale=1.0, disp=0.0, tint=None, rough_mul=1.0):
    """Poly Haven texture set -> principled material with box-free planar mapping by object coords (uses UV if mesh has one)."""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; L = nt.links
    bs = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (scale, scale, scale)
    L.new(tc.outputs["UV"], mp.inputs["Vector"])
    d = glob.glob(f"{PH}/{tex_id}/textures/*diff*")[0]
    td = N.new("ShaderNodeTexImage"); td.image = img(d); L.new(mp.outputs[0], td.inputs[0])
    col = td.outputs["Color"]
    if tint:
        mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs["Factor"].default_value = 1
        L.new(col, mx.inputs["A"]); mx.inputs["B"].default_value = (*tint, 1); col = mx.outputs["Result"]
    L.new(col, bs.inputs["Base Color"])
    r = glob.glob(f"{PH}/{tex_id}/textures/*rough*")
    if r:
        tr = N.new("ShaderNodeTexImage"); tr.image = img(r[0], True); L.new(mp.outputs[0], tr.inputs[0])
        mm = N.new("ShaderNodeMath"); mm.operation = "MULTIPLY"; mm.inputs[1].default_value = rough_mul
        L.new(tr.outputs["Color"], mm.inputs[0]); L.new(mm.outputs[0], bs.inputs["Roughness"])
    n = glob.glob(f"{PH}/{tex_id}/textures/*nor_gl*")
    if n:
        tn = N.new("ShaderNodeTexImage"); tn.image = img(n[0], True); L.new(mp.outputs[0], tn.inputs[0])
        nm = N.new("ShaderNodeNormalMap"); L.new(tn.outputs["Color"], nm.inputs["Color"]); L.new(nm.outputs[0], bs.inputs["Normal"])
    if disp:
        dp = glob.glob(f"{PH}/{tex_id}/textures/*disp*")[0]
        tdp = N.new("ShaderNodeTexImage"); tdp.image = img(dp, True); L.new(mp.outputs[0], tdp.inputs[0])
        dn = N.new("ShaderNodeDisplacement"); dn.inputs["Scale"].default_value = disp; dn.inputs["Midlevel"].default_value = 0.5
        L.new(tdp.outputs["Color"], dn.inputs["Height"]); L.new(dn.outputs[0], N["Material Output"].inputs["Displacement"])
        m.displacement_method = "BOTH"
    return m

def value_node(nt, name, v):
    n = nt.nodes.new("ShaderNodeValue"); n.name = n.label = name; n.outputs[0].default_value = v; return n

# ------------------------------------------------------------------ world: overcast HDRI, rotated over time (clouds drift)
w = bpy.data.worlds.new("Storm"); sc.world = w; w.use_nodes = True
N, L = w.node_tree.nodes, w.node_tree.links
env = N.new("ShaderNodeTexEnvironment"); env.image = img(glob.glob(PH + "/hdri/*.hdr")[0])
tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.name = "HDRIMap"
L.new(tc.outputs["Generated"], mp.inputs[0]); L.new(mp.outputs[0], env.inputs[0])
# storm grade: desaturate + darken, then clearing at the end (keyed on the mix factor)
hsv = N.new("ShaderNodeHueSaturation"); hsv.name = "StormGrade"; hsv.inputs["Saturation"].default_value = 0.55; hsv.inputs["Value"].default_value = 0.55
L.new(env.outputs["Color"], hsv.inputs["Color"])
bg = N["Background"]; L.new(hsv.outputs["Color"], bg.inputs["Color"]); bg.inputs["Strength"].default_value = 0.8
for f, rz, sat, val, st in ((1, 0, 0.6, 0.55, 0.85), (1470, 22, 0.45, 0.42, 0.7), (1700, 30, 0.8, 0.9, 1.0), (2010, 34, 0.95, 1.0, 1.15)):
    mp.inputs["Rotation"].default_value = (0, 0, R_(rz)); mp.inputs["Rotation"].keyframe_insert("default_value", frame=f)
    hsv.inputs["Saturation"].default_value = sat; hsv.inputs["Saturation"].keyframe_insert("default_value", frame=f)
    hsv.inputs["Value"].default_value = val; hsv.inputs["Value"].keyframe_insert("default_value", frame=f)
    bg.inputs["Strength"].default_value = st; bg.inputs["Strength"].keyframe_insert("default_value", frame=f)

# sun: soft storm key, warming at the end
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN")); link(sun, C_SET)
sun.rotation_euler = (R_(52), R_(8), R_(-35)); sun.data.angle = R_(6)
for f, e, c in ((1, 1.2, (0.85, 0.9, 1.0)), (1400, 0.8, (0.8, 0.88, 1.0)), (1690, 3.2, (1.0, 0.92, 0.8)), (2010, 4.0, (1.0, 0.9, 0.75))):
    sun.data.energy = e; sun.data.keyframe_insert("energy", frame=f); sun.data.color = c; sun.data.keyframe_insert("color", frame=f)

# ------------------------------------------------------------------ ring geometry (rounded rectangle around the hero house)
RC = Vector((0.0, 0.8)); HX, HY, CR = 10.5, 9.8, 3.2       # ring centre, half extents, corner radius -> front at y = -9
def ring_points(step=0.1):
    """closed rounded-rect polyline, CCW, starting at the front-left of the front edge (the hose end)"""
    pts = []
    def arc(cx, cy, a0, a1):
        n = max(2, int(abs(a1 - a0) * CR / step))
        return [Vector((cx + CR * math.cos(a0 + (a1 - a0) * i / n), cy + CR * math.sin(a0 + (a1 - a0) * i / n))) for i in range(n)]
    def line(p, q):
        n = max(1, int((q - p).length / step)); return [p.lerp(q, i / n) for i in range(n)]
    x0, x1, y0, y1 = RC.x - HX, RC.x + HX, RC.y - HY, RC.y + HY
    start = Vector((x0 + CR + 1.2, y0))
    pts += line(start, Vector((x1 - CR, y0)))
    pts += arc(x1 - CR, y0 + CR, -math.pi / 2, 0)
    pts += line(Vector((x1, y0 + CR)), Vector((x1, y1 - CR)))
    pts += arc(x1 - CR, y1 - CR, 0, math.pi / 2)
    pts += line(Vector((x1 - CR, y1)), Vector((x0 + CR, y1)))
    pts += arc(x0 + CR, y1 - CR, math.pi / 2, math.pi)
    pts += line(Vector((x0, y1 - CR)), Vector((x0, y0 + CR)))
    pts += arc(x0 + CR, y0 + CR, math.pi, 1.5 * math.pi)
    pts += line(Vector((x0 + CR, y0)), start)
    return pts
RING = ring_points()
def inside_ring(x, y, inset=0.0):
    dx = max(abs(x - RC.x) - (HX - CR), 0); dy = max(abs(y - RC.y) - (HY - CR), 0)
    if abs(x - RC.x) > HX - inset or abs(y - RC.y) > HY - inset: return False
    return math.hypot(dx, dy) <= CR - inset

# ------------------------------------------------------------------ ground (grass lawn -> mud after the flood), street, kerbs, sidewalks
def grid(name, x0, x1, y0, y1, step):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    nx, ny = int((x1 - x0) / step), int((y1 - y0) / step)
    V = [[bm.verts.new((x0 + i * step, y0 + j * step, 0)) for j in range(ny + 1)] for i in range(nx + 1)]
    uvl = bm.loops.layers.uv.new()
    for i in range(nx):
        for j in range(ny):
            f = bm.faces.new((V[i][j], V[i + 1][j], V[i + 1][j + 1], V[i][j + 1]))
            for l in f.loops: l[uvl].uv = (l.vert.co.x / 4, l.vert.co.y / 4)
    bm.to_mesh(me); bm.free(); ob = bpy.data.objects.new(name, me); return ob

ground = link(grid("Ground", -90, 90, -70, 70, 1.0), C_SET)
for p in ground.data.polygons: p.use_smooth = True
# gentle undulation, kerb dip for the street
for v in ground.data.vertices:
    x, y = v.co.x, v.co.y
    v.co.z = 0.05 * noise.noise(Vector((x * 0.15, y * 0.15, 0.3))) + 0.02 * noise.noise(Vector((x * 0.6, y * 0.6, 1.0)))
    if -20.2 < y < -11.8: v.co.z = -0.14
mg = pbr("Lawn", "grass_ground", 1.0, tint=(0.62, 0.95, 0.42))
mm = pbr("MudGround", "brown_mud_02", 1.0, tint=(0.75, 0.62, 0.5), rough_mul=0.5)
# combine: Lawn, then mud blended by MudAmount * (outside-ring mask stored as vertex colour)
mground = bpy.data.materials.new("GroundMix"); mground.use_nodes = True; nt = mground.node_tree; Nn = nt.nodes; Ll = nt.links
Nn.remove(Nn["Principled BSDF"])
g1 = Nn.new("ShaderNodeGroup"); g2 = Nn.new("ShaderNodeGroup")
def mat_to_group(m):
    """wrap a material's surface into a shader node group"""
    gtree = bpy.data.node_groups.new(m.name + "_G", "ShaderNodeTree")
    gtree.interface.new_socket("Shader", in_out="OUTPUT", socket_type="NodeSocketShader")
    mapping = {}
    for n in m.node_tree.nodes:
        if n.type == "OUTPUT_MATERIAL": continue
        nn = gtree.nodes.new(n.bl_idname); mapping[n.name] = nn
        for attr in ("image", "operation", "data_type", "blend_type"):
            if hasattr(n, attr) and getattr(n, attr) is not None:
                try: setattr(nn, attr, getattr(n, attr))
                except Exception: pass
        for i, s in enumerate(n.inputs):
            if hasattr(s, "default_value"):
                try: nn.inputs[i].default_value = s.default_value
                except Exception: pass
    for l in m.node_tree.links:
        if l.to_node.type == "OUTPUT_MATERIAL": continue
        fo = next(x for x in mapping[l.from_node.name].outputs if x.identifier == l.from_socket.identifier)
        ti = next(x for x in mapping[l.to_node.name].inputs if x.identifier == l.to_socket.identifier)
        gtree.links.new(fo, ti)
    out = gtree.nodes.new("NodeGroupOutput")
    gtree.links.new(mapping["Principled BSDF"].outputs[0], out.inputs[0])
    return gtree
g1.node_tree = mat_to_group(mg); g2.node_tree = mat_to_group(mm)
mix = Nn.new("ShaderNodeMixShader")
attr = Nn.new("ShaderNodeAttribute"); attr.attribute_name = "outside"
amt = value_node(nt, "MudAmount", 0.0)
# patchy mud edge
nz = Nn.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.6; nz.inputs["Detail"].default_value = 6
m1 = Nn.new("ShaderNodeMath"); m1.operation = "MULTIPLY"; Ll.new(attr.outputs["Fac"], m1.inputs[0]); Ll.new(amt.outputs[0], m1.inputs[1])
m2 = Nn.new("ShaderNodeMath"); m2.operation = "MULTIPLY"; m2.use_clamp = True; Ll.new(m1.outputs[0], m2.inputs[0])
m3 = Nn.new("ShaderNodeMapRange"); m3.inputs["From Min"].default_value = 0.3; m3.inputs["From Max"].default_value = 0.6
m3.inputs["To Min"].default_value = 0.8; m3.inputs["To Max"].default_value = 1.6; Ll.new(nz.outputs["Fac"], m3.inputs["Value"]); Ll.new(m3.outputs[0], m2.inputs[1])
Ll.new(m2.outputs[0], mix.inputs["Fac"]); Ll.new(g1.outputs[0], mix.inputs[1]); Ll.new(g2.outputs[0], mix.inputs[2])
Ll.new(mix.outputs[0], Nn["Material Output"].inputs["Surface"])
ground.data.materials.append(mground)
ca = ground.data.color_attributes.new("outside", "FLOAT_COLOR", "POINT")
for v in ground.data.vertices:
    o = 0.0 if inside_ring(v.co.x, v.co.y, -0.3) else 1.0
    ca.data[v.index].color = (o, o, o, 1)

street = link(grid("Street", -90, 90, -19.8, -12.2, 0.5), C_SET)
for v in street.data.vertices: v.co.z = -0.12 + 0.01 * noise.noise(Vector((v.co.x, v.co.y, 0)))
street.data.materials.append(pbr("Asphalt", "asphalt_02", 1.0, tint=(0.8, 0.8, 0.8)))
# kerbs + sidewalks (concrete from rocky_trail desaturated) with joints
def box(name, cx, cy, cz, sx, sy, sz, mat, c):
    me = bpy.data.meshes.new(name); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts); bmesh.ops.translate(bm, vec=(cx, cy, cz), verts=bm.verts)
    bmesh.ops.bevel(bm, geom=bm.edges[:], offset=0.015, segments=2, affect="EDGES")
    uv = bm.loops.layers.uv.new()
    for f in bm.faces:
        nrm = f.normal
        for l in f.loops:
            co = l.vert.co
            l[uv].uv = (co.x / 3, co.y / 3) if abs(nrm.z) > 0.5 else ((co.x + co.y) / 3, co.z / 3)
    bm.to_mesh(me); bm.free(); ob = bpy.data.objects.new(name, me); me.materials.append(mat); link(ob, c); return ob
mconc = pbr("Concrete", "rocky_trail", 0.6, tint=(0.75, 0.73, 0.7))
for sgn, yk, ys in ((1, -12.1, -11.0), (-1, -19.9, -21.0)):
    for i in range(-45, 45):
        box(f"Sidewalk_{sgn}_{i}", i * 2.0 + 1.0, ys, -0.02, 1.97, 1.9, 0.08, mconc, C_SET)
    box(f"Kerb_{sgn}", 0, yk, -0.07, 180, 0.25, 0.18, mconc, C_SET)
# driveways (concrete) for each lot
LOTS_N = [(-22, 0, "house_e", 0), (22, 0, "house_c", 0), (44, 0, "house_d", 0), (-44, 0, "house_b", 0)]
LOTS_S = [(-22, -36, "hero_house", 180), (0, -36, "house_e", 180), (22, -36, "house_d", 180), (44, -36, "house_c", 180), (-44, -36, "house_b", 180)]
for (x, y, n, r) in LOTS_N + [(0, 0, "house_a", 0)]:
    for k in range(5):
        box(f"Drive_{x}_{k}", x + 7.5 if x != 0 else 6.5, -9.5 + k * 0 + 0, -0.03, 3.2, 3.0, 0.06, mconc, C_SET) if k == 0 else None
for (x, y, n, r) in LOTS_S:
    box(f"DriveS_{x}", x + 7.5, -24.5, -0.03, 3.2, 6.0, 0.06, mconc, C_SET)

# ------------------------------------------------------------------ houses (CC-BY), siding fixed + grime + flood mud line
with bpy.data.libraries.load(S + "/assets.blend") as (src, dst): dst.objects = src.objects
ASSET = {o.name: o for o in dst.objects}
C_LIB = coll("AssetLib")
for o in dst.objects: C_LIB.objects.link(o); o.hide_render = True; o.hide_viewport = True; o.location.z = -50
def siding_fix(m, color):
    """replace the tiny SketchUp siding texture with procedural lap siding (wave bands + wood grain noise)"""
    nt = m.node_tree; N = nt.nodes; L = nt.links
    bs = next(n for n in N if n.type == "BSDF_PRINCIPLED")
    for l in list(bs.inputs["Base Color"].links): L.remove(l)
    tc = N.new("ShaderNodeTexCoord"); wv = N.new("ShaderNodeTexWave"); wv.wave_type = "BANDS"; wv.bands_direction = "Z"
    wv.wave_profile = "SAW"; wv.inputs["Scale"].default_value = 3.6; wv.inputs["Distortion"].default_value = 0.2
    L.new(tc.outputs["Object"], wv.inputs["Vector"])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 40; nz.inputs["Detail"].default_value = 8
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    cr = N.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (color[0] * 0.55, color[1] * 0.55, color[2] * 0.55, 1)
    cr.color_ramp.elements[1].color = (*color, 1); cr.color_ramp.elements[0].position = 0.0; cr.color_ramp.elements[1].position = 0.12
    L.new(wv.outputs["Fac"], cr.inputs[0])
    mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs["Factor"].default_value = 0.25
    L.new(cr.outputs[0], mx.inputs["A"]); L.new(nz.outputs["Color"], mx.inputs["B"]); L.new(mx.outputs["Result"], bs.inputs["Base Color"])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.6; L.new(wv.outputs["Fac"], bp.inputs["Height"])
    L.new(bp.outputs[0], bs.inputs["Normal"])
    bs.inputs["Roughness"].default_value = 0.7

MUDLINE = {}   # material -> value node controlling the mud-line height (flooded neighbours only)
def grime(m, flooded):
    """darken near the ground, streaks; flooded houses also get a brown mud line driven by a value node (keyed later)"""
    nt = m.node_tree; N = nt.nodes; L = nt.links
    bs = next((n for n in N if n.type == "BSDF_PRINCIPLED"), None)
    if bs is None: return
    src = bs.inputs["Base Color"].links[0].from_socket if bs.inputs["Base Color"].links else None
    base = N.new("ShaderNodeRGB"); base.outputs[0].default_value = bs.inputs["Base Color"].default_value
    col = src or base.outputs[0]
    gp = N.new("ShaderNodeNewGeometry"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(gp.outputs["Position"], sep.inputs[0])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.0; nz.inputs["Detail"].default_value = 10
    L.new(gp.outputs["Position"], nz.inputs["Vector"])
    # ground grime: 0 at z>0.8
    gr = N.new("ShaderNodeMapRange"); gr.inputs["From Min"].default_value = 0.0; gr.inputs["From Max"].default_value = 0.9
    gr.inputs["To Min"].default_value = 0.55; gr.inputs["To Max"].default_value = 0.0; L.new(sep.outputs["Z"], gr.inputs["Value"])
    mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; L.new(gr.outputs[0], mx.inputs["Factor"])
    L.new(col, mx.inputs["A"]); mx.inputs["B"].default_value = (0.35, 0.3, 0.25, 1); col = mx.outputs["Result"]
    # streaky weathering everywhere
    mw = N.new("ShaderNodeMix"); mw.data_type = "RGBA"; mw.blend_type = "MULTIPLY"; mw.inputs["Factor"].default_value = 0.3
    L.new(col, mw.inputs["A"]); L.new(nz.outputs["Color"], mw.inputs["B"]); col = mw.outputs["Result"]
    if flooded:
        v = value_node(nt, "MudLine", -0.5)
        sub = N.new("ShaderNodeMath"); sub.operation = "SUBTRACT"; L.new(v.outputs[0], sub.inputs[0]); L.new(sep.outputs["Z"], sub.inputs[1])
        jit = N.new("ShaderNodeMath"); jit.operation = "MULTIPLY_ADD"; L.new(nz.outputs["Fac"], jit.inputs[0]); jit.inputs[1].default_value = 0.08
        L.new(sub.outputs[0], jit.inputs[2])
        st = N.new("ShaderNodeMath"); st.operation = "MULTIPLY"; st.use_clamp = True; st.inputs[1].default_value = 25; L.new(jit.outputs[0], st.inputs[0])
        mm_ = N.new("ShaderNodeMix"); mm_.data_type = "RGBA"; L.new(st.outputs[0], mm_.inputs["Factor"]); L.new(col, mm_.inputs["A"])
        mm_.inputs["B"].default_value = (0.09, 0.06, 0.035, 1); col = mm_.outputs["Result"]
        MUDLINE[m.name] = v
    L.new(col, bs.inputs["Base Color"])
SIDING = {"hero_house": (0.85, 0.83, 0.78), "house_b": (0.72, 0.62, 0.48), "house_c": (0.88, 0.86, 0.82), "house_e": (0.62, 0.66, 0.68),
          "house_d": (0.8, 0.78, 0.72)}
fixed = set()
for name, colr in SIDING.items():
    for m in ASSET[name].data.materials:
        if m and "Siding" in m.name and m.name not in fixed: siding_fix(m, colr); fixed.add(m.name)
def place(name, x, y, rz, c, flooded, copy_mats=False):
    src = ASSET[name]; ob = bpy.data.objects.new(f"{name}_{x}_{y}", src.data); link(ob, c)
    ob.location = (x, y, 0); ob.rotation_euler.z = R_(rz)
    if copy_mats:
        ob.data = src.data.copy()
        for i, m in enumerate(ob.data.materials):
            if m: ob.data.materials[i] = m.copy()
    if flooded:
        for m in ob.data.materials:
            if m and m.name not in MUDLINE: grime(m, True)
    return ob
hero = place("house_a", 0, 0.5, -90, C_HOUSE, False); hero.name = "HeroHouse"
for m in hero.data.materials: grime(m, False)
for (x, y, n, r) in LOTS_N + LOTS_S:
    place(n, x, y + (0 if y == 0 else 0), r, C_HOUSE, True, copy_mats=True)

for (x, y, n, r) in [(-66, 0, "house_d", 0), (66, 0, "house_e", 0), (-66, -36, "house_c", 180), (66, -36, "house_b", 180)] + \
        [(x, 30, n, 180) for x, n in zip(range(-66, 67, 22), ["house_b", "house_c", "house_d", "house_e", "hero_house", "house_c", "house_d"])] + \
        [(x, -66, n, 0) for x, n in zip(range(-66, 67, 22), ["house_e", "house_d", "house_c", "hero_house", "house_b", "house_e", "house_c"])]:
    place(n, x, y, r, C_HOUSE, False)
# ------------------------------------------------------------------ vegetation (Poly Haven CC0)
def ph_objs(asset, names):
    p = glob.glob(f"{PH}/{asset}/*.blend")[0]
    with bpy.data.libraries.load(p) as (s_, d_): d_.objects = [n for n in s_.objects if n in names]
    return {o.name: o for o in d_.objects}
TREE = ph_objs("tree_small_02", ["tree_small_02_LOD1"])["tree_small_02_LOD1"]
dec = TREE.modifiers.new("dec", "DECIMATE"); dec.ratio = 0.35
bpy.context.collection.objects.link(TREE); bpy.context.view_layer.objects.active = TREE
dg = bpy.context.evaluated_depsgraph_get(); me = bpy.data.meshes.new_from_object(TREE.evaluated_get(dg)); TREE.modifiers.clear(); TREE.data = me
bpy.context.collection.objects.unlink(TREE)
SHR = ph_objs("shrub_02", ["shrub_02_a_LOD1", "shrub_02_b_LOD1", "shrub_02_c_LOD1"])
LAMP = ph_objs("street_lamp_01", ["street_lamp_01"])["street_lamp_01"]
TREES = []
for i, (x, y) in enumerate([(-12.8, -6.5), (13.5, -10.0), (-30, -10.5), (31, -10.5), (-14, -26), (8, -26.5), (30, -26), (-36, -26.5), (52, -10.3), (-52, -26)] + [(random.uniform(-85, 85), random.choice((18, 22, -50, -55))) for _ in range(30)] + [(random.choice((-84, 84)), random.uniform(-60, 60)) for _ in range(12)]):
    t = bpy.data.objects.new(f"Tree_{i}", TREE.data); link(t, C_VEG); t.location = (x, y, 0); t.rotation_euler.z = random.uniform(0, 6.28)
    t.scale = [random.uniform(1.25, 1.6)] * 3; TREES.append(t)
for i in range(40):
    side = random.choice((1, -1)); x = random.uniform(-55, 55); y = random.choice((-5.6, 6.8)) if side > 0 else random.choice((-29.5, -42))
    if abs(x) < 7.5 and y > -8: continue
    s_ = bpy.data.objects.new(f"Shrub_{i}", random.choice(list(SHR.values())).data); link(s_, C_VEG)
    s_.location = (x, y, 0); s_.rotation_euler.z = random.uniform(0, 6.28); s_.scale = [random.uniform(0.8, 1.3)] * 3
for i, x in enumerate(range(-80, 81, 26)):
    for y, rz in ((-11.3, 0), (-20.7, 180)):
        l_ = bpy.data.objects.new(f"Lamp_{i}_{y}", LAMP.data); link(l_, C_SET); l_.location = (x + (13 if y < -15 else 0), y, 0); l_.rotation_euler.z = R_(rz + 90)
# hero shrubs along the house front (inside the ring)
for i, x in enumerate((-4.8, -3.2, 4.0, 5.2)):
    s_ = bpy.data.objects.new(f"HeroShrub_{i}", list(SHR.values())[i % 3].data); link(s_, C_VEG); s_.location = (x, -5.9, 0); s_.scale = (0.7, 0.7, 0.7)

# lawn grass clumps inside the ring (and the hero front yard): GN scatter on a lawn patch
GR = ph_objs("grass_medium_01", ["grass_medium_01_large_a_LOD1", "grass_medium_01_large_b_LOD1", "grass_medium_01_mid_a_LOD1",
                                 "grass_medium_01_mid_b_LOD1", "grass_medium_01_tall_a_LOD1", "grass_medium_01_small_a_LOD1"])
gc = bpy.data.collections.new("GrassClumps")
for o in GR.values():
    for m in o.data.materials:
        if m and m.node_tree and not m.get("bright"):
            m["bright"] = 1
            b = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
            if b and b.inputs["Base Color"].links:
                src_ = b.inputs["Base Color"].links[0].from_socket
                bc = m.node_tree.nodes.new("ShaderNodeBrightContrast"); bc.inputs["Bright"].default_value = 0.08; bc.inputs["Contrast"].default_value = -0.1
                hs = m.node_tree.nodes.new("ShaderNodeHueSaturation"); hs.inputs["Value"].default_value = 1.7; hs.inputs["Saturation"].default_value = 1.1
                m.node_tree.links.new(src_, hs.inputs["Color"]); m.node_tree.links.new(hs.outputs[0], bc.inputs["Color"]); m.node_tree.links.new(bc.outputs[0], b.inputs["Base Color"])
for o in GR.values(): gc.objects.link(o)
patch = grid("LawnPatch", RC.x - HX, RC.x + HX, RC.y - HY, RC.y + HY, 0.5); link(patch, C_VEG)
bm = bmesh.new(); bm.from_mesh(patch.data)
bmesh.ops.delete(bm, geom=[f for f in bm.faces if not inside_ring(f.calc_center_median().x, f.calc_center_median().y, 0.55)
                           or (abs(f.calc_center_median().x) < 5.9 and -5.3 < f.calc_center_median().y < 6.8)], context="FACES")
bm.to_mesh(patch.data); bm.free()
for v in patch.data.vertices:
    v.co.z = 0.05 * noise.noise(Vector((v.co.x * 0.15, v.co.y * 0.15, 0.3))) + 0.02 * noise.noise(Vector((v.co.x * 0.6, v.co.y * 0.6, 1.0)))
gn = bpy.data.node_groups.new("GrassScatter", "GeometryNodeTree")
gn.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
gn.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
Ng, Lg = gn.nodes, gn.links
gi = Ng.new("NodeGroupInput"); go = Ng.new("NodeGroupOutput")
dp = Ng.new("GeometryNodeDistributePointsOnFaces"); dp.distribute_method = "POISSON"
dp.inputs["Distance Min"].default_value = 0.12; dp.inputs["Density Max"].default_value = 28
ci = Ng.new("GeometryNodeCollectionInfo"); ci.inputs["Collection"].default_value = gc; ci.inputs["Separate Children"].default_value = True
ci.inputs["Reset Children"].default_value = True
ip = Ng.new("GeometryNodeInstanceOnPoints"); ip.inputs["Pick Instance"].default_value = True
rv = Ng.new("FunctionNodeRandomValue"); rv.data_type = "FLOAT_VECTOR"; rin(rv, "Min", "VECTOR").default_value = (0, 0, 0); rin(rv, "Max", "VECTOR").default_value = (0.15, 0.15, 6.28)
rs = Ng.new("FunctionNodeRandomValue"); rs.data_type = "FLOAT"; rin(rs, "Min", "VALUE").default_value = 0.9; rin(rs, "Max", "VALUE").default_value = 1.6
ri = Ng.new("FunctionNodeRandomValue"); ri.data_type = "INT"; rin(ri, "Min", "INT").default_value = 0; rin(ri, "Max", "INT").default_value = 5
Lg.new(gi.outputs[0], dp.inputs["Mesh"]); Lg.new(dp.outputs["Points"], ip.inputs["Points"]); Lg.new(ci.outputs[0], ip.inputs["Instance"])
Lg.new(rout(rv, "VECTOR"), ip.inputs["Rotation"]); Lg.new(rout(rs, "VALUE"), ip.inputs["Scale"]); Lg.new(rout(ri, "INT"), ip.inputs["Instance Index"])
jg = Ng.new("GeometryNodeJoinGeometry"); Lg.new(ip.outputs[0], jg.inputs[0]); Lg.new(gi.outputs[0], jg.inputs[0]); Lg.new(jg.outputs[0], go.inputs[0])
patch.modifiers.new("Grass", "NODES").node_group = gn
patch.data.materials.append(mg)

# ------------------------------------------------------------------ the water tubes
def tube_material():
    m = bpy.data.materials.new("TubeVinyl"); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; L = nt.links
    bs = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); gp = N.new("ShaderNodeNewGeometry")
    # dark olive-black PVC, mottled, with mud splash near the ground and lighter scuffs
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 9; nz.inputs["Detail"].default_value = 12; L.new(tc.outputs["Object"], nz.inputs["Vector"])
    cr = N.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (0.018, 0.024, 0.02, 1); cr.color_ramp.elements[1].color = (0.05, 0.06, 0.045, 1)
    L.new(nz.outputs["Fac"], cr.inputs[0])
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(gp.outputs["Position"], sep.inputs[0])
    mz = N.new("ShaderNodeMapRange"); mz.inputs["From Min"].default_value = 0.0; mz.inputs["From Max"].default_value = 0.22
    mz.inputs["To Min"].default_value = 0.85; mz.inputs["To Max"].default_value = 0.0; L.new(sep.outputs["Z"], mz.inputs["Value"])
    nz2 = N.new("ShaderNodeTexNoise"); nz2.inputs["Scale"].default_value = 22; nz2.inputs["Detail"].default_value = 6; L.new(tc.outputs["Object"], nz2.inputs["Vector"])
    mm = N.new("ShaderNodeMath"); mm.operation = "MULTIPLY"; mm.use_clamp = True; L.new(mz.outputs[0], mm.inputs[0]); L.new(nz2.outputs["Fac"], mm.inputs[1])
    mm2 = N.new("ShaderNodeMath"); mm2.operation = "MULTIPLY"; mm2.use_clamp = True; mm2.inputs[1].default_value = 1.8; L.new(mm.outputs[0], mm2.inputs[0])
    mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; L.new(mm2.outputs[0], mx.inputs["Factor"]); L.new(cr.outputs[0], mx.inputs["A"])
    mx.inputs["B"].default_value = (0.2, 0.15, 0.09, 1); L.new(mx.outputs["Result"], bs.inputs["Base Color"])
    rr = N.new("ShaderNodeMapRange"); rr.inputs["To Min"].default_value = 0.22; rr.inputs["To Max"].default_value = 0.75; L.new(mm2.outputs[0], rr.inputs["Value"])
    L.new(rr.outputs[0], bs.inputs["Roughness"])
    bs.inputs["Coat Weight"].default_value = 0.4; bs.inputs["Coat Roughness"].default_value = 0.15
    # weld seams (along v = 0.25 / 0.75) and fabric weave bump
    uvn = N.new("ShaderNodeUVMap"); su = N.new("ShaderNodeSeparateXYZ"); L.new(uvn.outputs[0], su.inputs[0])
    sm = N.new("ShaderNodeMath"); sm.operation = "PINGPONG"; sm.inputs[1].default_value = 0.25; L.new(su.outputs["Y"], sm.inputs[0])
    sm2 = N.new("ShaderNodeMapRange"); sm2.inputs["From Min"].default_value = 0.0; sm2.inputs["From Max"].default_value = 0.006
    sm2.inputs["To Min"].default_value = 1.0; sm2.inputs["To Max"].default_value = 0.0; L.new(sm.outputs[0], sm2.inputs["Value"])
    wv = N.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = 900; wv.bands_direction = "DIAGONAL"; L.new(tc.outputs["UV"], wv.inputs["Vector"])
    ad = N.new("ShaderNodeMath"); ad.operation = "MULTIPLY_ADD"; L.new(wv.outputs["Fac"], ad.inputs[0]); ad.inputs[1].default_value = 0.05
    L.new(sm2.outputs[0], ad.inputs[2])
    nz3 = N.new("ShaderNodeTexNoise"); nz3.inputs["Scale"].default_value = 60; nz3.inputs["Detail"].default_value = 4; L.new(tc.outputs["Object"], nz3.inputs["Vector"])
    ad2 = N.new("ShaderNodeMath"); ad2.operation = "MULTIPLY_ADD"; L.new(nz3.outputs["Fac"], ad2.inputs[0]); ad2.inputs[1].default_value = 0.15; L.new(ad.outputs[0], ad2.inputs[2])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.35; bp.inputs["Distance"].default_value = 0.004
    L.new(ad2.outputs[0], bp.inputs["Height"]); L.new(bp.outputs[0], bs.inputs["Normal"]); L.new(bp.outputs[0], bs.inputs["Coat Normal"])
    return m
MT = tube_material()

def tube_gn():
    g = bpy.data.node_groups.new("TubeFill", "GeometryNodeTree")
    g.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    g.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N, L = g.nodes, g.links
    gi = N.new("NodeGroupInput"); go = N.new("NodeGroupOutput")
    vf = N.new("ShaderNodeValue"); vf.name = "Front"; vf.outputs[0].default_value = -1.0
    vs = N.new("ShaderNodeValue"); vs.name = "Soft"; vs.outputs[0].default_value = 1.2
    fu = N.new("GeometryNodeInputNamedAttribute"); fu.data_type = "FLOAT"; fu.inputs["Name"].default_value = "u"
    ff = N.new("GeometryNodeInputNamedAttribute"); ff.data_type = "FLOAT_VECTOR"; ff.inputs["Name"].default_value = "full"
    sub = N.new("ShaderNodeMath"); sub.operation = "SUBTRACT"; L.new(vf.outputs[0], sub.inputs[0]); L.new(fu.outputs["Attribute"], sub.inputs[1])
    dv = N.new("ShaderNodeMath"); dv.operation = "DIVIDE"; dv.use_clamp = True; L.new(sub.outputs[0], dv.inputs[0]); L.new(vs.outputs[0], dv.inputs[1])
    sm = N.new("ShaderNodeMapRange"); sm.interpolation_type = "SMOOTHSTEP"; L.new(dv.outputs[0], sm.inputs["Value"])
    pos = N.new("GeometryNodeInputPosition")
    mx = N.new("ShaderNodeMix"); mx.data_type = "VECTOR"; L.new(sm.outputs[0], mx.inputs["Factor"]); L.new(pos.outputs[0], mx.inputs[4]); L.new(ff.outputs["Attribute"], mx.inputs[5])
    sp = N.new("GeometryNodeSetPosition"); L.new(gi.outputs[0], sp.inputs["Geometry"]); L.new(mx.outputs[1], sp.inputs["Position"])
    ss = N.new("GeometryNodeSetShadeSmooth"); L.new(sp.outputs[0], ss.inputs[0]); L.new(ss.outputs[0], go.inputs[0])
    return g
GN_TUBE = tube_gn()

def profile(t, full, u, length, seed):
    """cross-section point for angle t. Full: water-filled, flattened bottom, bulging sides. Flat: crumpled empty ribbon."""
    st = math.sin(t); ct = math.cos(t)
    if full:
        a, h = 0.6, 0.82
        if st >= 0: x, z = a * ct, h * 0.5 + h * 0.5 * st
        else:
            x = a * math.copysign(abs(ct) ** 0.55, ct) * 1.04; z = h * 0.5 * (1 - abs(st) ** 0.33)
        # baffle creases every 3 m, slight lengthwise sag, wrinkles
        bf = 1 - 0.045 * math.exp(-((u % 3.0) - 1.5) ** 2 / 0.01) * 0 - 0.05 * math.exp(-(((u + 1.5) % 3.0) - 1.5) ** 2 / 0.02)
        x *= bf; z = z * bf if z > 0.1 else z
        w = 0.008 * noise.noise(Vector((u * 3, t * 2, seed))) + 0.004 * noise.noise(Vector((u * 11, t * 6, seed + 3)))
        r = Vector((x, z)); nrm = Vector((ct, max(st, -0.2))).normalized()
        x, z = x + nrm.x * w, max(0.0, z + nrm.y * w)
    else:
        x = 0.92 * ct; z = 0.012 + 0.012 * st
        z += max(0, 0.03 * noise.noise(Vector((u * 1.5, x * 2, seed)))) + 0.01 * noise.noise(Vector((u * 6, x * 6, seed + 1)))
        z = max(0.004, z)
    # rounded welded ends
    e = min(u, length - u)
    if e < 0.45:
        k = math.sqrt(max(0.0, 1 - ((0.45 - e) / 0.45) ** 2)); k = 0.12 + 0.88 * k
        x *= k
        zc = 0.34 if full else 0.0
        z = max(0.0, zc + (z - zc) * k) if full else z
    return x, z

def build_tube(name, pts, seed, nv=28):
    """pts: polyline (Vector2). Returns tube object with attributes u and full; base positions = empty."""
    # arc length
    us = [0.0]
    for p, q in zip(pts, pts[1:]): us.append(us[-1] + (q - p).length)
    Lg_ = us[-1]
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    au = bm.verts.layers.float.new("u"); af = bm.verts.layers.float_vector.new("full")
    rows = []
    for i, (p, u) in enumerate(zip(pts, us)):
        tng = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        side = Vector((tng.y, -tng.x))   # outward for CCW ring
        row = []
        for j in range(nv):
            t = 2 * math.pi * j / nv - math.pi / 2
            x0, z0 = profile(t, False, u, Lg_, seed); x1, z1 = profile(t, True, u, Lg_, seed)
            v = bm.verts.new((p.x + side.x * x0, p.y + side.y * x0, z0))
            v[au] = u; v[af] = (p.x + side.x * x1, p.y + side.y * x1, z1)
            row.append(v)
        rows.append(row)
    uvl = bm.loops.layers.uv.new()
    for i in range(len(rows) - 1):
        for j in range(nv):
            f = bm.faces.new((rows[i][j], rows[i][(j + 1) % nv], rows[i + 1][(j + 1) % nv], rows[i + 1][j]))
            for l, (ii, jj) in zip(f.loops, ((i, j), (i, j + 1), (i + 1, j + 1), (i + 1, j))):
                l[uvl].uv = (us[ii] / 4.0, jj / nv)
    for row, uu in ((rows[0], 0.0), (rows[-1], Lg_)):
        c = bm.verts.new(sum((v.co for v in row), Vector()) / nv); c[au] = uu
        c[af] = sum((Vector(v[af]) for v in row), Vector()) / nv
        for j in range(nv): bm.faces.new((row[j], row[(j + 1) % nv], c) if uu == 0 else (row[(j + 1) % nv], row[j], c))
    bm.normal_update(); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); link(ob, C_TUBE); me.materials.append(MT)
    md = ob.modifiers.new("Fill", "NODES"); md.node_group = GN_TUBE.copy(); md.node_group.name = "TubeFill_" + name
    ob["length"] = Lg_
    return ob, md, Lg_

# split the ring into 6 segments (small gaps get closed by the bulging rounded ends)
tot = sum((q - p).length for p, q in zip(RING, RING[1:] + RING[:1]))
SEG = []; acc = 0.0; cur = [RING[0]]; seglen = tot / 6
for p, q in zip(RING, RING[1:] + RING[:1]):
    acc += (q - p).length; cur.append(q)
    if acc >= seglen * (len(SEG) + 1) - 1e-6 and len(SEG) < 5:
        SEG.append(cur); cur = [q]
SEG.append(cur)
TUBES = []
# fill schedule: segment 0 = beat 1 (frames 20-215), then 1..5 during beat 2 (223-499)
FILL = [(20, 215), (232, 330), (280, 380), (330, 430), (370, 470), (410, 495)]
for k, seg in enumerate(SEG):
    seg = seg[3:-3] if k else seg[:-3]
    ob, md, ln = build_tube(f"Tube_{k}", seg, 10 + k)
    f0, f1 = FILL[k]
    fo = md.node_group.nodes["Front"].outputs[0]
    fo.default_value = -1.5; fo.keyframe_insert("default_value", frame=f0)
    fo.default_value = ln + 1.5; fo.keyframe_insert("default_value", frame=f1)
    TUBES.append(ob)
    # valve + cap at the start of each tube (fill end), on top of the tube near u=0.8
    p, q = seg[8], seg[9]; tng = (q - p).normalized()
    me = bpy.data.meshes.new(f"Valve_{k}"); bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=20, radius1=0.055, radius2=0.05, depth=0.12)
    bmesh.ops.translate(bm, vec=(0, 0, 0.06), verts=bm.verts)
    r2 = bmesh.ops.create_cone(bm, cap_ends=True, segments=20, radius1=0.075, radius2=0.075, depth=0.03)
    bmesh.ops.translate(bm, vec=(0, 0, 0.015), verts=r2["verts"])
    for rr in range(5):
        rg = bmesh.ops.create_cone(bm, cap_ends=True, segments=20, radius1=0.058, radius2=0.058, depth=0.008)
        bmesh.ops.translate(bm, vec=(0, 0, 0.05 + rr * 0.014), verts=rg["verts"])
    lug = bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.scale(bm, vec=(0.13, 0.018, 0.03), verts=lug["verts"]); bmesh.ops.translate(bm, vec=(0, 0, 0.135), verts=lug["verts"])
    bmesh.ops.bevel(bm, geom=bm.edges[:], offset=0.002, segments=2, affect="EDGES")
    bm.to_mesh(me); bm.free()
    vo = bpy.data.objects.new(f"Valve_{k}", me); link(vo, C_TUBE)
    mv = bpy.data.materials.get("ValvePlastic") or bpy.data.materials.new("ValvePlastic")
    mv.use_nodes = True; mv.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.03, 0.032, 0.03, 1)
    mv.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.45
    me.materials.append(mv)
    # ride on the tube's top surface: shrinkwrap to the evaluated tube along -Z via Shrinkwrap constraint
    vo.location = (p.x, p.y, 1.5)
    cn = vo.constraints.new("SHRINKWRAP"); cn.target = ob; cn.shrinkwrap_type = "PROJECT"; cn.project_axis = "NEG_Z"
    cn.project_limit = 3.0
    TUBES.append(vo)

# ------------------------------------------------------------------ flood surface: grid with the ring interior cut out, GN-driven level / front / waves
wpl = grid("Flood", -90, 90, -70, 70, 0.6)
bm = bmesh.new(); bm.from_mesh(wpl.data)
bmesh.ops.delete(bm, geom=[f for f in bm.faces if inside_ring(f.calc_center_median().x, f.calc_center_median().y, -0.05)], context="FACES")
bm.to_mesh(wpl.data); bm.free(); link(wpl, C_WATER)
for p in wpl.data.polygons: p.use_smooth = True
g = bpy.data.node_groups.new("FloodSurface", "GeometryNodeTree")
g.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
g.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
N, L = g.nodes, g.links
gi0 = N.new("NodeGroupInput"); go = N.new("NodeGroupOutput")
class _GI: pass
gi = _GI(); gi.outputs = {}
for nm, dv in (("FrontX", 120.0), ("SpreadY", 0.0), ("Level", 0.55), ("Lip", 0.35), ("Chop", 0.06)):
    vn = N.new("ShaderNodeValue"); vn.name = nm; vn.outputs[0].default_value = dv; gi.outputs[nm] = vn.outputs[0]
tn = N.new("GeometryNodeInputSceneTime"); gi.outputs["Time"] = tn.outputs["Seconds"]
gi.outputs[0] = gi0.outputs[0]
def M(op, x, y=None, clamp=False):
    n = N.new("ShaderNodeMath"); n.operation = op; n.use_clamp = clamp
    for i, v in enumerate((x, y)):
        if v is None: continue
        if isinstance(v, (int, float)): n.inputs[i].default_value = v
        else: L.new(v, n.inputs[i])
    return n.outputs[0]
pos = N.new("GeometryNodeInputPosition"); sp = N.new("ShaderNodeSeparateXYZ"); L.new(pos.outputs[0], sp.inputs[0])
X, Y = sp.outputs["X"], sp.outputs["Y"]
# along-street front: water where x > FrontX (comes from +X), soft over 6 m
fa = M("DIVIDE", M("SUBTRACT", X, gi.outputs["FrontX"]), 6.0)
fa_c = M("MINIMUM", M("MAXIMUM", fa, 0.0), 1.0)
# spread away from street centre line y=-16
dy = M("ABSOLUTE", M("ADD", Y, 16.0))
sa = M("DIVIDE", M("SUBTRACT", M("ADD", gi.outputs["SpreadY"], 0.0), dy), 2.5)
sa_c = M("MINIMUM", M("MAXIMUM", sa, 0.0), 1.0)
cover = M("MULTIPLY", fa_c, sa_c)
# lips at both fronts (gaussian bumps)
lipx = M("EXPONENT", M("MULTIPLY", M("POWER", M("SUBTRACT", fa, 0.35), 2.0), -10.0))
lipy = M("EXPONENT", M("MULTIPLY", M("POWER", M("SUBTRACT", sa, 0.5), 2.0), -6.0))
lip = M("MULTIPLY", M("ADD", M("MULTIPLY", lipx, sa_c), M("MULTIPLY", lipy, fa_c)), gi.outputs["Lip"])
# chop: two noise octaves advected along -X (flow direction) with time
cmb = N.new("ShaderNodeCombineXYZ")
L.new(M("ADD", X, M("MULTIPLY", gi.outputs["Time"], 2.2)), cmb.inputs["X"]); L.new(Y, cmb.inputs["Y"])
nz = N.new("ShaderNodeTexNoise"); nz.noise_dimensions = "4D"; nz.inputs["Scale"].default_value = 0.35; nz.inputs["Detail"].default_value = 5
L.new(cmb.outputs[0], nz.inputs["Vector"]); L.new(M("MULTIPLY", gi.outputs["Time"], 0.4), nz.inputs["W"])
chop = M("MULTIPLY", M("SUBTRACT", nz.outputs["Fac"], 0.5), gi.outputs["Chop"])
chop = M("MULTIPLY", chop, 4.0)
z = M("ADD", M("ADD", M("SUBTRACT", M("MULTIPLY", cover, M("ADD", gi.outputs["Level"], 0.6)), 0.6), lip), M("MULTIPLY", chop, cover))
off = N.new("ShaderNodeCombineXYZ"); L.new(z, off.inputs["Z"])
st = N.new("GeometryNodeSetPosition"); L.new(gi.outputs[0], st.inputs["Geometry"]); L.new(off.outputs[0], st.inputs["Offset"])
# store foam factor (lips + chop crests) for the shader
sa_ = N.new("GeometryNodeStoreNamedAttribute"); sa_.data_type = "FLOAT"; sa_.inputs["Name"].default_value = "foam"
L.new(st.outputs[0], sa_.inputs["Geometry"]); L.new(M("ADD", M("DIVIDE", lip, M("ADD", gi.outputs["Lip"], 0.001)), M("MULTIPLY", chop, 3.0)), sa_.inputs["Value"])
ss = N.new("GeometryNodeSetShadeSmooth"); L.new(sa_.outputs[0], ss.inputs[0]); L.new(ss.outputs[0], go.inputs[0])
fmd = wpl.modifiers.new("Flood", "NODES"); fmd.node_group = g
sub = wpl.modifiers.new("Sub", "SUBSURF"); sub.levels = 1; sub.render_levels = 1
# flood material: muddy brown water, specular, foam streaks
mw = bpy.data.materials.new("FloodWater"); mw.use_nodes = True; nt = mw.node_tree; N2, L2 = nt.nodes, nt.links
bs = N2["Principled BSDF"]; bs.inputs["Base Color"].default_value = (0.13, 0.085, 0.045, 1); bs.inputs["Roughness"].default_value = 0.06
bs.inputs["IOR"].default_value = 1.33; bs.inputs["Specular IOR Level"].default_value = 0.6
fa_attr = N2.new("ShaderNodeAttribute"); fa_attr.attribute_name = "foam"
tc = N2.new("ShaderNodeTexCoord"); nzf = N2.new("ShaderNodeTexNoise"); nzf.inputs["Scale"].default_value = 1.6; nzf.inputs["Detail"].default_value = 14
nzf.inputs["Distortion"].default_value = 0.6
mpf = N2.new("ShaderNodeMapping"); mpf.inputs["Scale"].default_value = (0.25, 1.4, 1.0); L2.new(tc.outputs["Object"], mpf.inputs["Vector"]); L2.new(mpf.outputs[0], nzf.inputs["Vector"])
mr = N2.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.6; mr.inputs["From Max"].default_value = 0.78; L2.new(nzf.outputs["Fac"], mr.inputs["Value"])
fm = N2.new("ShaderNodeMath"); fm.operation = "MULTIPLY_ADD"; fm.use_clamp = True; L2.new(fa_attr.outputs["Fac"], fm.inputs[0]); fm.inputs[1].default_value = 0.8
L2.new(mr.outputs[0], fm.inputs[2])
fm2 = N2.new("ShaderNodeMath"); fm2.operation = "MULTIPLY"; fm2.use_clamp = True; L2.new(fm.outputs[0], fm2.inputs[0]); L2.new(mr.outputs[0], fm2.inputs[1])
fm3 = N2.new("ShaderNodeMath"); fm3.operation = "MAXIMUM"; L2.new(fm2.outputs[0], fm3.inputs[0]); L2.new(fa_attr.outputs["Fac"], fm3.inputs[1])
fm4 = N2.new("ShaderNodeMath"); fm4.operation = "MULTIPLY"; fm4.use_clamp = True; fm4.inputs[1].default_value = 0.45; L2.new(fm3.outputs[0], fm4.inputs[0])
cm = N2.new("ShaderNodeMix"); cm.data_type = "RGBA"; L2.new(fm4.outputs[0], cm.inputs["Factor"])
cm.inputs["A"].default_value = (0.13, 0.085, 0.045, 1); cm.inputs["B"].default_value = (0.4, 0.33, 0.24, 1); L2.new(cm.outputs["Result"], bs.inputs["Base Color"])
rm = N2.new("ShaderNodeMapRange"); rm.inputs["To Min"].default_value = 0.05; rm.inputs["To Max"].default_value = 0.6; L2.new(fm4.outputs[0], rm.inputs["Value"])
L2.new(rm.outputs[0], bs.inputs["Roughness"])
nzb = N2.new("ShaderNodeTexNoise"); nzb.inputs["Scale"].default_value = 14; nzb.inputs["Detail"].default_value = 6; L2.new(tc.outputs["Object"], nzb.inputs["Vector"])
bpm = N2.new("ShaderNodeBump"); bpm.inputs["Strength"].default_value = 0.25; L2.new(nzb.outputs["Fac"], bpm.inputs["Height"]); L2.new(bpm.outputs[0], bs.inputs["Normal"])
wpl.data.materials.append(mw)

# ------------------------------------------------------------------ cutaway shell: deep teal->navy gradient sphere around the front tube section
CUT_C = Vector((2.0, -9.6, 0.3))
me = bpy.data.meshes.new("CutShell"); bm = bmesh.new()
bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=24, radius=3.6)
bmesh.ops.reverse_faces(bm, faces=bm.faces[:]); bm.to_mesh(me); bm.free()
shell = bpy.data.objects.new("CutShell", me); link(shell, C_FX); shell.location = CUT_C
for p in me.polygons: p.use_smooth = True
msh = bpy.data.materials.new("CutBackdrop"); msh.use_nodes = True; nt = msh.node_tree; N3, L3 = nt.nodes, nt.links
N3.remove(N3["Principled BSDF"])
tc = N3.new("ShaderNodeTexCoord"); sp3 = N3.new("ShaderNodeSeparateXYZ"); L3.new(tc.outputs["Object"], sp3.inputs[0])
mr3 = N3.new("ShaderNodeMapRange"); mr3.inputs["From Min"].default_value = -4; mr3.inputs["From Max"].default_value = 5; L3.new(sp3.outputs["Z"], mr3.inputs["Value"])
cr3 = N3.new("ShaderNodeValToRGB"); cr3.color_ramp.elements[0].color = (0.004, 0.06, 0.075, 1); cr3.color_ramp.elements[1].color = (0.004, 0.012, 0.05, 1)
cr3.color_ramp.elements.new(0.45).color = (0.01, 0.11, 0.14, 1)
L3.new(mr3.outputs[0], cr3.inputs[0])
em = N3.new("ShaderNodeEmission"); em.inputs["Strength"].default_value = 1.0; L3.new(cr3.outputs[0], em.inputs["Color"])
tr = N3.new("ShaderNodeBsdfTransparent"); mxs = N3.new("ShaderNodeMixShader"); mxs.name = "ShellFade"
L3.new(tr.outputs[0], mxs.inputs[1]); L3.new(em.outputs[0], mxs.inputs[2]); L3.new(mxs.outputs[0], N3["Material Output"].inputs["Surface"])
lp = N3.new("ShaderNodeLightPath"); mxs2 = N3.new("ShaderNodeMixShader")
# only the camera sees the backdrop; it doesn't light or shadow the subject
L3.new(lp.outputs["Is Camera Ray"], mxs2.inputs[0]); L3.new(tr.outputs[0], mxs2.inputs[1]); L3.new(mxs.outputs[0], mxs2.inputs[2])
L3.new(mxs2.outputs[0], N3["Material Output"].inputs["Surface"])
me.materials.append(msh)
shell.visible_shadow = False; shell.visible_diffuse = False; shell.visible_glossy = False


# ------------------------------------------------------------------ cutaway section of Tube_0 (same profile, cut open at x = CUT_X), water core, bubbles
CUT_X = 2.05
seg0 = SEG[0][:-3]
x_start = seg0[0].x
def straight_tube(name, x0, x1, y, seed, shrink=0.0, nv=40, cap_cut=False, taper=True):
    me = bpy.data.meshes.new(name); bm = bmesh.new(); uvl = bm.loops.layers.uv.new()
    n = int((x1 - x0) / 0.05) + 1; rows = []
    for i in range(n):
        x = x0 + (x1 - x0) * i / (n - 1); u = x - x_start
        row = []
        for j in range(nv):
            t = 2 * math.pi * j / nv - math.pi / 2
            px, pz = profile(t, True, u, 1e3 if not taper else 1e3, seed)
            if shrink:
                c = Vector((0, 0.41)); q = Vector((px, pz)); q = c + (q - c) * (1 - shrink / max(0.05, (q - c).length)); px, pz = q.x, max(shrink, q.y)
            row.append(bm.verts.new((x, y - px, pz)))
        rows.append(row)
    for i in range(n - 1):
        for j in range(nv):
            f = bm.faces.new((rows[i][j], rows[i + 1][j], rows[i + 1][(j + 1) % nv], rows[i][(j + 1) % nv]))
            for l, (ii, jj) in zip(f.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))): l[uvl].uv = ((x0 + (x1 - x0) * ii / (n - 1)) / 4, jj / nv)
    if cap_cut: bm.faces.new(list(reversed(rows[-1])))
    bm.faces.new(rows[0])
    bm.normal_update(); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    return bpy.data.objects.new(name, me)
cut_shell = link(straight_tube("CutTube", x_start + 0.6, CUT_X, -9.0, 10), C_FX)
# open the cut end: remove the cap at x = CUT_X (none built), give the vinyl a visible wall thickness
so = cut_shell.modifiers.new("Wall", "SOLIDIFY"); so.thickness = 0.014; so.offset = -1; so.use_rim = True
cut_shell.data.materials.append(MT)
mcut = bpy.data.materials.new("VinylCutEdge"); mcut.use_nodes = True
mcut.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.07, 0.075, 0.06, 1)
mcut.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.6
cut_shell.data.materials.append(mcut); so.material_offset_rim = 1
cut_shell.visible_shadow = False
al = bpy.data.objects.new("CutKey", bpy.data.lights.new("CutKey", "AREA")); link(al, C_FX); al.data.energy = 120; al.data.size = 1.5
al.location = (CUT_X + 1.6, -10.4, 1.6); al.rotation_euler = (Vector((CUT_X, -9.0, 0.4)) - al.location).to_track_quat("-Z", "Y").to_euler(); al.data.color = (0.85, 0.95, 1.0)
al2 = bpy.data.objects.new("CutRim", bpy.data.lights.new("CutRim", "AREA")); link(al2, C_FX); al2.data.energy = 80; al2.data.size = 1.0
al2.location = (CUT_X - 1.5, -7.6, 1.4); al2.rotation_euler = (Vector((CUT_X, -9.0, 0.4)) - al2.location).to_track_quat("-Z", "Y").to_euler()
core = link(straight_tube("CutWater", x_start + 0.6, CUT_X - 0.002, -9.0, 10, shrink=0.016, cap_cut=True), C_FX)
mwt = bpy.data.materials.new("TubeWater"); mwt.use_nodes = True; nt = mwt.node_tree
b = nt.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = (0.03, 0.2, 0.3, 1); b.inputs["Transmission Weight"].default_value = 0.0
b.inputs["Subsurface Weight"].default_value = 0.45; b.inputs["Subsurface Radius"].default_value = (0.15, 0.5, 0.8); b.inputs["Subsurface Scale"].default_value = 0.12
b.inputs["Emission Color"].default_value = (0.03, 0.22, 0.3, 1); b.inputs["Emission Strength"].default_value = 0.04
b.inputs["Specular IOR Level"].default_value = 0.8
b.inputs["Roughness"].default_value = 0.03; b.inputs["IOR"].default_value = 1.33
va = nt.nodes.new("ShaderNodeVolumeAbsorption"); va.inputs["Color"].default_value = (0.35, 0.72, 0.78, 1); va.inputs["Density"].default_value = 0.5
nt.links.new(va.outputs[0], nt.nodes["Material Output"].inputs["Volume"])
# fine suspended particles / light shafts read better with a touch of scatter
vs_ = nt.nodes.new("ShaderNodeVolumeScatter"); vs_.inputs["Density"].default_value = 0.25; vs_.inputs["Color"].default_value = (0.6, 0.85, 0.9, 1)
ad = nt.nodes.new("ShaderNodeAddShader"); nt.links.new(va.outputs[0], ad.inputs[0]); nt.links.new(vs_.outputs[0], ad.inputs[1])
# caustic ripple pattern on the cut face
tcw = nt.nodes.new("ShaderNodeTexCoord"); vor = nt.nodes.new("ShaderNodeTexVoronoi"); vor.feature = "SMOOTH_F1"; vor.inputs["Scale"].default_value = 9
nt.links.new(tcw.outputs["Object"], vor.inputs["Vector"]); bpw = nt.nodes.new("ShaderNodeBump"); bpw.inputs["Strength"].default_value = 0.35
nt.links.new(vor.outputs["Distance"], bpw.inputs["Height"]); nt.links.new(bpw.outputs[0], b.inputs["Normal"])
core.data.materials.append(mwt)
mb = bpy.data.materials.new("Bubble"); mb.use_nodes = True; bb = mb.node_tree.nodes["Principled BSDF"]
bb.inputs["Transmission Weight"].default_value = 1; bb.inputs["IOR"].default_value = 0.75; bb.inputs["Roughness"].default_value = 0.0
bme = bpy.data.meshes.new("Bubble"); bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0); bm.to_mesh(bme); bm.free()
for p in bme.polygons: p.use_smooth = True
bme.materials.append(mb)
BUB = []
for i in range(70):
    t = random.uniform(-0.8, 1.0) * math.pi / 2 + random.choice((0, math.pi)) * 0
    yy = random.uniform(-0.45, 0.45); zz = random.uniform(0.08, 0.72) if random.random() < 0.5 else random.uniform(0.55, 0.76)
    if abs(yy) > 0.5 * math.sqrt(max(0, 1 - ((zz - 0.41) / 0.42) ** 2)): continue
    o = bpy.data.objects.new(f"Bubble_{i}", bme); link(o, C_FX); o.location = (CUT_X - random.uniform(-0.004, 0.006), -9.0 + yy, zz)
    o.scale = [random.uniform(0.003, 0.012)] * 3; BUB.append(o)
    o.parent = core

# explainer arrows (glossy 3D, no text): flood force (amber) and weight (cyan)
def arrow(name, length, r, mat):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    sh = bmesh.ops.create_cone(bm, cap_ends=True, segments=32, radius1=r, radius2=r, depth=length - 3 * r)
    bmesh.ops.translate(bm, vec=(0, 0, (length - 3 * r) / 2), verts=sh["verts"])
    hd = bmesh.ops.create_cone(bm, cap_ends=True, segments=32, radius1=r * 2.3, radius2=0.0, depth=3 * r)
    bmesh.ops.translate(bm, vec=(0, 0, length - 1.5 * r), verts=hd["verts"])
    bmesh.ops.bevel(bm, geom=[e for e in bm.edges if e.calc_face_angle(0) > 0.5], offset=r * 0.12, segments=3, affect="EDGES")
    bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    me.materials.append(mat); o = bpy.data.objects.new(name, me); link(o, C_FX); return o
def glossy(name, col, em):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = 0.18; b.inputs["Coat Weight"].default_value = 0.8
    b.inputs["Emission Color"].default_value = (*col, 1); b.inputs["Emission Strength"].default_value = em
    return m
MA = glossy("ArrowFlood", (0.95, 0.42, 0.06), 0.6); MW_ = glossy("ArrowWeight", (0.35, 0.85, 1.0), 0.8)
for i, z in enumerate((0.14, 0.34, 0.54)):
    o = arrow(f"FloodArrow_{i}", 1.2, 0.045, MA); o.rotation_euler = (R_(-90), 0, 0); o.location = (CUT_X + 0.12, -10.95, z)
wa = arrow("WeightArrow", 1.1, 0.075, MW_); wa.rotation_euler = (R_(180), 0, 0); wa.location = (CUT_X + 0.12, -9.0, 2.05)
# flood wall section for the explainer (brown water pressing on the street side)
me = bpy.data.meshes.new("FloodWall"); bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=60, y_segments=30, size=1.0)
bmesh.ops.scale(bm, vec=(4.5, 1.6, 1), verts=bm.verts)
ext = bmesh.ops.extrude_face_region(bm, geom=bm.faces[:]); bmesh.ops.translate(bm, vec=(0, 0, -0.7), verts=[v for v in ext["geom"] if isinstance(v, bmesh.types.BMVert)])
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
bm.to_mesh(me); bm.free()
fw = bpy.data.objects.new("FloodWall", me); link(fw, C_FX); fw.location = (CUT_X - 4.5, -11.05, 0.55)
wv = fw.modifiers.new("Wave", "WAVE"); wv.height = 0.03; wv.width = 0.6; wv.speed = 0.04; wv.use_normal = False
msec = bpy.data.materials.new("FloodSection"); msec.use_nodes = True; nt = msec.node_tree
b = nt.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = (0.2, 0.13, 0.06, 1); b.inputs["Transmission Weight"].default_value = 0.0
b.inputs["Roughness"].default_value = 0.06; b.inputs["IOR"].default_value = 1.33
b.inputs["Subsurface Weight"].default_value = 0.6; b.inputs["Subsurface Radius"].default_value = (0.5, 0.3, 0.12); b.inputs["Subsurface Scale"].default_value = 0.3
va = nt.nodes.new("ShaderNodeVolumeAbsorption"); va.inputs["Color"].default_value = (0.55, 0.36, 0.16, 1); va.inputs["Density"].default_value = 3.0
vsc = nt.nodes.new("ShaderNodeVolumeScatter"); vsc.inputs["Color"].default_value = (0.6, 0.45, 0.28, 1); vsc.inputs["Density"].default_value = 2.5
ad = nt.nodes.new("ShaderNodeAddShader"); nt.links.new(va.outputs[0], ad.inputs[0]); nt.links.new(vsc.outputs[0], ad.inputs[1])
me.materials.append(msec)
# suspended silt and leaf bits in the section
bsilt = bme.copy(); msilt = bpy.data.materials.new("Silt"); msilt.use_nodes = True
msilt.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.12, 0.08, 0.04, 1); bsilt.materials[0] = msilt
for i in range(90):
    o = bpy.data.objects.new(f"Silt_{i}", bsilt); link(o, C_FX); o.parent = fw
    o.location = (random.uniform(0.2, 9.0), random.uniform(-1.5, 1.5), random.uniform(-0.65, -0.05)); o.scale = [random.uniform(0.004, 0.015)] * 3
fw.modifiers.new("Sub", "SUBSURF").levels = 1
dsp = fw.modifiers.new("Chop", "DISPLACE"); tx = bpy.data.textures.new("Chop", "CLOUDS"); tx.noise_scale = 0.35; dsp.texture = tx; dsp.strength = 0.14; dsp.direction = "Z"

# garden hose: reel at the house front wall, hose across the lawn to Valve_0 (end hooked to the valve)
hose_reel = bpy.data.objects.new("HoseReel", ASSET["hose"].data); link(hose_reel, C_SET); hose_reel.location = (-4.6, -6.15, 0.0); hose_reel.rotation_euler.z = R_(90)
cu = bpy.data.curves.new("Hose", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 0.011; cu.bevel_resolution = 3
spl = cu.splines.new("BEZIER"); P = [(-4.45, -6.2, 0.32), (-4.5, -6.5, 0.02), (-4.9, -7.1, 0.015), (-5.25, -7.6, 0.015), (-5.3, -8.25, 0.05), (-5.3, -8.85, 0.2)]
spl.bezier_points.add(len(P) - 1)
for bp_, p in zip(spl.bezier_points, P): bp_.co = p; bp_.handle_left_type = bp_.handle_right_type = "AUTO"
hose = bpy.data.objects.new("Hose", cu); link(hose, C_SET)
mh = bpy.data.materials.new("HoseRubber"); mh.use_nodes = True; hb = mh.node_tree.nodes["Principled BSDF"]
hb.inputs["Base Color"].default_value = (0.05, 0.22, 0.06, 1); hb.inputs["Roughness"].default_value = 0.4
tcx = mh.node_tree.nodes.new("ShaderNodeTexCoord"); wvh = mh.node_tree.nodes.new("ShaderNodeTexWave"); wvh.inputs["Scale"].default_value = 30
mh.node_tree.links.new(tcx.outputs["UV"], wvh.inputs["Vector"]); bph = mh.node_tree.nodes.new("ShaderNodeBump"); bph.inputs["Strength"].default_value = 0.2
mh.node_tree.links.new(wvh.outputs["Fac"], bph.inputs["Height"]); mh.node_tree.links.new(bph.outputs[0], hb.inputs["Normal"]);
cu.materials.append(mh)
# nozzle (brass) at the end
me = bpy.data.meshes.new("Nozzle"); bm = bmesh.new()
bmesh.ops.create_cone(bm, cap_ends=True, segments=20, radius1=0.018, radius2=0.013, depth=0.12); bm.to_mesh(me); bm.free()
mn = bpy.data.materials.new("Brass"); mn.use_nodes = True; nb = mn.node_tree.nodes["Principled BSDF"]
nb.inputs["Base Color"].default_value = (0.75, 0.55, 0.25, 1); nb.inputs["Metallic"].default_value = 1; nb.inputs["Roughness"].default_value = 0.3
me.materials.append(mn); noz = bpy.data.objects.new("Nozzle", me); link(noz, C_SET)
cn2 = noz.constraints.new("COPY_LOCATION"); cn2.target = bpy.data.objects["Valve_0"]; cn2.use_offset = True; noz.location = (0.0, 0.03, 0.17); noz.rotation_euler = (R_(-30), 0, R_(-33))
print("RING_SEGMENTS", [round(o["length"], 1) for o in TUBES if "length" in o])
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SAVED", OUT)
