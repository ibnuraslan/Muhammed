"""B23 sets: the field (stump, village huts, trees), the open-sided thatched meeting hut with the forge, the battlefield
(same meadow, other end) with the invaders' flag. World: clear blue sky with soft clouds, keyed to a pink dusk for the
defeat beats (property DUSK on the world, driven per shot in 03_anim.py).
blender -b chars.blend --python 02_sets.py -- <out.blend>"""
import sys, os, math, random
import bpy, bmesh
from mathutils import Vector, Matrix, noise
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "00_lib.py")).read())
OUT = sys.argv[sys.argv.index("--") + 1]
BRAND = os.path.join(HERE, "..", "..", "assets", "brand")
sc = bpy.context.scene
random.seed(23)
CS = coll("Set"); CF = coll("Field", CS); CH = coll("Hut", CS); CB = coll("Battle", CS)

def place(o, loc, yaw=0.0, scale=1.0):
    o.location = loc; o.rotation_euler = (0, 0, R_(yaw)); o.scale = (scale,) * 3
    return o

def ph_model(asset, c, name=None):
    path = os.path.join(ASSETS, asset, asset + "_1k.blend")
    with bpy.data.libraries.load(path, link=False) as (s, d):
        d.objects = [n for n in s.objects]
    objs = [o for o in d.objects if o is not None and o.type == 'MESH']
    for im in bpy.data.images:     # Poly Haven blends reference their textures relative to the asset blend
        if im.filepath.startswith("//") and not os.path.exists(bpy.path.abspath(im.filepath)):
            cand = os.path.join(os.path.dirname(path), im.filepath[2:])
            if os.path.exists(cand): im.filepath = cand; im.reload()
    for o in objs: c.objects.link(o)
    if len(objs) > 1:
        bpy.ops.object.select_all(action='DESELECT')
        for o in objs: o.select_set(True)
        bpy.context.view_layer.objects.active = objs[0]; bpy.ops.object.join()
    o = objs[0]; o.name = name or asset
    o.location = (0, 0, 0)
    return o

def inst(src, name, loc, yaw=0.0, scale=1.0, c=None):
    o = src.copy(); (c or src.users_collection[0]).objects.link(o); o.name = name
    return place(o, loc, yaw, scale)

def soften(o, sat=1.15, rough_min=0.4):
    for m in o.data.materials:
        if m is None or not m.node_tree: continue
        for n in m.node_tree.nodes:
            if n.type == 'NORMAL_MAP': n.inputs['Strength'].default_value = min(n.inputs['Strength'].default_value, 0.35)
            if n.type == 'BUMP': n.inputs['Strength'].default_value = min(n.inputs['Strength'].default_value, 0.3)

def logo_mat(name, which):
    m = bpy.data.materials.new(name); n, l = nodes_of(m)
    bs = next(x for x in n if x.type == 'BSDF_PRINCIPLED'); t = n.new('ShaderNodeTexImage')
    t.image = img(os.path.join(BRAND, "DaKrasFilms_logo_%s.png" % which)); t.extension = 'CLIP'
    l.new(t.outputs['Color'], bs.inputs['Base Color']); l.new(t.outputs['Alpha'], bs.inputs['Alpha'])
    bs.inputs['Roughness'].default_value = 0.6
    try: m.blend_method = 'HASHED'
    except Exception: pass
    return m

def decal(name, w, h, mat, c):
    """plane in local XZ (normal -Y), size w x h, UV 0..1"""
    bm = bmesh.new(); uv = bm.loops.layers.uv.new()
    vs = [bm.verts.new((x, 0, z)) for x, z in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]
    f = bm.faces.new(vs)
    for lp, co in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): lp[uv].uv = co
    return mesh_obj(name, bm, [mat], c)

# ================================================================== world: sky with soft clouds, keyed dusk mix
w = bpy.data.worlds.new("Sky"); sc.world = w; w.use_nodes = True
nt = w.node_tree; N = nt.nodes; L = nt.links; N.clear()
out = N.new('ShaderNodeOutputWorld'); bg = N.new('ShaderNodeBackground'); bg.inputs['Strength'].default_value = 1.0
tc = N.new('ShaderNodeTexCoord'); sep = N.new('ShaderNodeSeparateXYZ'); L.new(tc.outputs['Generated'], sep.inputs[0])
nrm = N.new('ShaderNodeVectorMath'); nrm.operation = 'NORMALIZE'; L.new(tc.outputs['Generated'], nrm.inputs[0])
sep2 = N.new('ShaderNodeSeparateXYZ'); L.new(nrm.outputs[0], sep2.inputs[0])
def ramp(stops):
    r = N.new('ShaderNodeValToRGB'); el = r.color_ramp.elements
    el[0].position, el[0].color = stops[0][0], (*stops[0][1], 1); el[1].position, el[1].color = stops[1][0], (*stops[1][1], 1)
    for p, c in stops[2:]: e = el.new(p); e.color = (*c, 1)
    return r
day = ramp([(0.0, (0.55, 0.62, 0.55)), (0.5, (0.86, 0.94, 1.0)), (0.62, (0.55, 0.78, 1.0)), (1.0, (0.18, 0.45, 0.95))])
dusk = ramp([(0.0, (0.45, 0.3, 0.35)), (0.5, (1.0, 0.72, 0.62)), (0.6, (0.95, 0.55, 0.65)), (1.0, (0.55, 0.32, 0.62))])
mr = N.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = -1; mr.inputs['From Max'].default_value = 1
L.new(sep2.outputs[2], mr.inputs['Value']); L.new(mr.outputs[0], day.inputs[0]); L.new(mr.outputs[0], dusk.inputs[0])
# clouds: noise on the view direction, only above the horizon
cn = N.new('ShaderNodeTexNoise'); cn.inputs['Scale'].default_value = 2.2; cn.inputs['Detail'].default_value = 4.0
cmap = N.new('ShaderNodeVectorMath'); cmap.operation = 'MULTIPLY'; cmap.inputs[1].default_value = (1.0, 1.0, 3.0)
L.new(nrm.outputs[0], cmap.inputs[0]); L.new(cmap.outputs[0], cn.inputs['Vector'])
cr = ramp([(0.0, (0, 0, 0)), (0.58, (0, 0, 0)), (0.72, (1, 1, 1))])
L.new(cn.outputs['Fac'], cr.inputs[0])
hz = N.new('ShaderNodeMapRange'); hz.inputs['From Min'].default_value = 0.04; hz.inputs['From Max'].default_value = 0.3
L.new(sep2.outputs[2], hz.inputs['Value'])
cm = N.new('ShaderNodeMath'); cm.operation = 'MULTIPLY'; L.new(cr.outputs[0], cm.inputs[0]); L.new(hz.outputs[0], cm.inputs[1])
cm2 = N.new('ShaderNodeMath'); cm2.operation = 'MULTIPLY'; cm2.inputs[1].default_value = 0.85; L.new(cm.outputs[0], cm2.inputs[0])
dmix = N.new('ShaderNodeMix'); dmix.data_type = 'RGBA'; dmix.name = "DUSK"; dmix.inputs['Factor'].default_value = 0.0
L.new(day.outputs[0], dmix.inputs['A']); L.new(dusk.outputs[0], dmix.inputs['B'])
cloudcol = N.new('ShaderNodeMix'); cloudcol.data_type = 'RGBA'; cloudcol.inputs['B'].default_value = (1.0, 1.0, 1.0, 1)
L.new(cm2.outputs[0], cloudcol.inputs['Factor']); L.new(dmix.outputs['Result'], cloudcol.inputs['A'])
dcl = N.new('ShaderNodeMix'); dcl.data_type = 'RGBA'; dcl.inputs['A'].default_value = (1, 1, 1, 1); dcl.inputs['B'].default_value = (1.0, 0.82, 0.86, 1)
dfac = N.new('ShaderNodeValue'); dfac.name = "DUSKV"
L.new(dfac.outputs[0], dmix.inputs['Factor']); L.new(dfac.outputs[0], dcl.inputs['Factor']); L.new(dcl.outputs['Result'], cloudcol.inputs['B'])
L.new(cloudcol.outputs['Result'], bg.inputs['Color']); L.new(bg.outputs[0], out.inputs[0])

sun = bpy.data.lights.new("Sun", 'SUN'); sun.energy = 3.2; sun.angle = R_(4); sun.color = (1.0, 0.96, 0.9)
so = bpy.data.objects.new("Sun", sun); CS.objects.link(so); so.rotation_euler = (R_(48), 0, R_(-35))

# ================================================================== the meadow (one big ground for field + battle)
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=160, y_segments=160, size=110)
for v in bm.verts:
    d = min((Vector((v.co.x, v.co.y)) - Vector(a_)).length for a_ in ((0, 0), (40, 0), (-40, 0), (20, 0), (-20, 0)))
    flat_ = min(1.0, max(0.0, (d - 12) / 30))          # flat around the action, rolling hills beyond
    v.co.z = flat_ * (6.0 * noise.noise(Vector((v.co.x / 45, v.co.y / 45, 0.3))) + 4.0 + 0.15 * noise.noise(Vector((v.co.x / 6, v.co.y / 6, 1.7))))
ground_mat = pbr("Meadow", "leafy_grass", scale=0.35, tint=(0.95, 1.1, 0.75), bump=0.3)
G = mesh_obj("Ground", bm, [ground_mat], CF); shade_smooth(G)
sc["GROUND"] = "Ground"

# grass tufts (Poly Haven grass_medium_01) scattered with a particle system, not inside the action spots
grass = ph_model("grass_medium_01", CF, "GrassTuft"); soften(grass); grass.hide_render = True; grass.location = (0, 0, -50)
gv = G.vertex_groups.new(name="grass")
ACTION = [(0, 0), (40, 0), (-40, 0)]
gidx = [v.index for v in G.data.vertices if all((Vector((v.co.x, v.co.y)) - Vector(a)).length > 4.5 for a in ACTION)]
gv.add(gidx, 1.0, 'REPLACE')
ps = G.modifiers.new("Grass", 'PARTICLE_SYSTEM').particle_system; pst = ps.settings

pst.type = 'HAIR'; pst.use_advanced_hair = True; pst.count = 0; pst.render_type = 'OBJECT'; pst.instance_object = grass
pst.particle_size = 0.9; pst.size_random = 0.5; pst.use_rotations = True; pst.rotation_mode = 'GLOB_Z'; pst.phase_factor_random = 2.0
pst.hair_length = 1.0; ps.vertex_group_density = "grass"; pst.use_emit_random = True; ps.seed = 3
pst.distribution = 'RAND'

# trees and shrubs ring
sh2 = ph_model("shrub_02", CF, "Shrub2Src"); soften(sh2); sh2.location = (0, 0, -80)
sh4 = ph_model("shrub_04", CF, "Shrub4Src"); soften(sh4); sh4.location = (0, 0, -80)
def gz(x, y):
    d = min((Vector((x, y)) - Vector(a_)).length for a_ in ((0, 0), (40, 0), (-40, 0), (20, 0), (-20, 0))); flat_ = min(1.0, max(0.0, (d - 12) / 30))
    return flat_ * (6.0 * noise.noise(Vector((x / 45, y / 45, 0.3))) + 4.0 + 0.15 * noise.noise(Vector((x / 6, y / 6, 1.7))))
SHRUB_SPOTS = [(-6, 9), (7, 11), (-12, 5), (12, 4), (-3, 14), (5, -12), (-9, -10), (34, 9), (47, 8), (-36, 8), (-46, 9), (-44, -6), (-33, -8), (15, -6), (-16, -4)]
for i, (x, y) in enumerate(SHRUB_SPOTS):
    inst(sh2 if i % 2 else sh4, "Shrub%02d" % i, (x, y, gz(x, y) - 0.05), random.uniform(0, 360), random.uniform(1.4, 2.2), CF)
for i in range(30):
    a = random.uniform(0, 2 * math.pi); r = random.uniform(16, 40)
    x, y = r * math.cos(a), r * math.sin(a)
    if min((Vector((x, y)) - Vector(c_)).length for c_ in ((0, 0), (40, 0), (-40, 0))) < 8: continue
    inst(sh2 if i % 2 else sh4, "ShrubR%02d" % i, (x, y, gz(x, y) - 0.05), random.uniform(0, 360), random.uniform(1.2, 2.4), CF)

# ---- trees (CC-BY acacias), palisades, rail fences and huts so every meadow shot has a village edge behind it
acc = glb_asset("acacia", CF, target_size=7.0, axis=2); acc.name = "AccSrcA"
acc2 = glb_asset("tree2", CF, target_size=8.0, axis=2); acc2.name = "AccSrcB"
for o in (acc, acc2): soften(o)
TREES = [(-9, 16), (14, 15), (-14, 9), (17, 6), (6, 22), (-4, 24), (20, -4), (-18, -2), (11, -14), (-12, -15),
         (16, 30), (-20, 20), (26, 4), (22, 22),
         (-40 - 12, 15), (-40 + 13, 15), (-40 - 15, -8), (-40 - 9, -16), (-40 + 16, -6), (-40 - 20, 6), (-40 + 4, 22), (-40 - 3, -22),
         (40 - 12, 12), (40 + 12, -12), (40 - 14, -10)]
for i, (x, y) in enumerate(TREES):
    src_ = acc if i % 2 else acc2
    inst(src_, "Acc%02d" % i, (x, y, gz(x, y) - 0.05), random.uniform(0, 360), random.uniform(0.8, 1.2), CF)
acc.location = (0, 0, -60); acc2.location = (0, 0, -60); acc.hide_render = acc2.hide_render = True
pal = glb_asset("palisade", CF, target_size=2.6, axis=2); pal.name = "PalSrc"
pw = max(pal.dimensions.x, pal.dimensions.y); pal_long_x = pal.dimensions.x >= pal.dimensions.y
fen = glb_asset("fence", CF, target_size=1.1, axis=2); fen.name = "FenSrc"
fw_ = max(fen.dimensions.x, fen.dimensions.y); fen_long_x = fen.dimensions.x >= fen.dimensions.y
def line_of(src_, w_, long_x, p0, p1, name, jitter=0.0):
    p0 = Vector(p0); p1 = Vector(p1); d = p1 - p0; n = max(1, int(d.length / (w_ * 0.98)))
    yaw = math.degrees(math.atan2(d.y, d.x)) + (0 if long_x else -90)
    for k in range(n):
        q = p0 + d * ((k + 0.5) / n)
        inst(src_, "%s%02d" % (name, k), (q.x, q.y, gz(q.x, q.y) - 0.05), yaw + random.uniform(-jitter, jitter), 1.0, CF)
    src_.location = (0, 0, -60); src_.hide_render = True
# field village edge (behind S01-S03, looking +y / +x)
line_of(pal, pw, pal_long_x, (-9, 13), (13, 13), "PalF", 2)
line_of(fen, fw_, fen_long_x, (-6, 6.5), (5, 7.5), "FenF", 3)
# battle village edge: behind S12 (looking +y) and S13/S14 (looking -x)
line_of(pal, pw, pal_long_x, (-49, 12), (-33, 12), "PalB", 2)
line_of(pal, pw, pal_long_x, (-51, -6), (-51, 9), "PalW", 2)
line_of(fen, fw_, fen_long_x, (-46, -3.5), (-46, 3.5), "FenB", 3)

# the stump (punishment block) at the field origin
stump = ph_model("tree_stump_01", CF, "Stump"); soften(stump)
mn, mx = bbox_world([stump]); sd = mx - mn
s_ = 0.55 / max(sd.x, sd.y)
stump.scale = (s_, s_, 0.5 / sd.z)
bpy.context.view_layer.update(); mn, mx = bbox_world([stump])
stump.location = (-(mn.x + mx.x) / 2, -(mn.y + mx.y) / 2, -mn.z - 0.02)
bpy.context.view_layer.update(); mn, mx = bbox_world([stump])
sc["STUMP_TOP"] = mx.z; print("STUMP", tuple(round(v, 3) for v in mn), tuple(round(v, 3) for v in mx))

# village huts (CC-BY model) on the far side of the field toward the meeting hut
hut = glb_asset("hut", CF, target_size=4.2, axis=2)
for i, (x, y, yaw, s) in enumerate([(28, 14, 200, 1.0), (33, 18, 160, 0.9), (52, 12, 240, 1.1), (55, -10, 280, 1.0), (24, 20, 190, 0.85), (47, 19, 210, 0.95),
        (-4, 17, 180, 1.0), (4, 18.5, 170, 0.9), (10, 16.5, 200, 1.0), (-45, 16, 180, 1.0), (-38, 17, 160, 0.9), (-55, 0, 270, 1.0), (-56, 7, 250, 0.9), (-55, -6, 290, 1.0)]):
    o = hut if i == 0 else inst(hut, "Hut%02d" % i, (0, 0, 0), c=CF)
    place(o, (x, y, gz(x, y) - 0.05), yaw, s)

# ================================================================== the meeting hut (open sides, thatch cone) at (40, 0)
HX, HY = 40.0, 0.0; HR = 4.6
floor_m = pbr("DirtFloor", "dirt_floor", scale=0.6, tint=(1.05, 0.95, 0.85), bump=0.3)
bm = bmesh.new(); bmesh.ops.create_circle(bm, cap_ends=True, segments=48, radius=HR + 0.4)
fl = mesh_obj("HutFloor", bm, [floor_m], CH); fl.location = (HX, HY, 0.012)
wood = pbr("Wood", "wood_planks", scale=1.2, tint=(0.75, 0.55, 0.38), bump=0.3)
POSTS = []
for i in range(10):
    a = 2 * math.pi * i / 10 + 0.31
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=0.09, radius2=0.08, depth=2.75)
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, 1.375))
    o = mesh_obj("Post%d" % i, bm, [wood], CH); shade_smooth(o); o.location = (HX + HR * math.cos(a), HY + HR * math.sin(a), 0)
    POSTS.append(o)
# ring beam
bm = bmesh.new(); bmesh.ops.create_circle(bm, segments=40, radius=HR)
o = mesh_obj("RingBeam", bm, [wood], CH); o.location = (HX, HY, 2.72)
sk = o.modifiers.new("Skin", 'SKIN')
for v in o.data.skin_vertices[0].data: v.radius = (0.07, 0.07)
# low clay wall on the back half (open toward the field)
clay = pbr("Clay", "clay_plaster", scale=0.8, tint=(1.0, 0.85, 0.7), bump=0.3)
bm = bmesh.new()
segs = 30; a0, a1 = math.radians(60), math.radians(300)
ring_lo, ring_hi = [], []
for i in range(segs + 1):
    a = a0 + (a1 - a0) * i / segs
    for rr, lst in ((HR + 0.05, ring_lo),):
        lst.append((bm.verts.new((HR * math.cos(a), HR * math.sin(a), 0)), bm.verts.new((HR * math.cos(a), HR * math.sin(a), 0.95))))
for i in range(segs):
    bm.faces.new([ring_lo[i][0], ring_lo[i + 1][0], ring_lo[i + 1][1], ring_lo[i][1]])
wall = mesh_obj("LowWall", bm, [clay], CH); wall.location = (HX, HY, 0)
m = wall.modifiers.new("Thick", 'SOLIDIFY'); m.thickness = 0.18; m.offset = 0
# thatch cone roof
thatch = pbr("Thatch", "thatch_roof_angled", scale=0.7, tint=(1.05, 0.95, 0.75), bump=0.35)
bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=False, segments=48, radius1=HR + 1.1, radius2=0.05, depth=3.2)
bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, 1.6))
roof = mesh_obj("Roof", bm, [thatch], CH); roof.location = (HX, HY, 2.45); shade_smooth(roof)
m = roof.modifiers.new("Thick", 'SOLIDIFY'); m.thickness = 0.25
# rafters under the thatch (visible from inside)
for i in range(12):
    a = 2 * math.pi * i / 12
    bm = bmesh.new(); p0 = Vector((HR * math.cos(a), HR * math.sin(a), 2.72)); p1 = Vector((0, 0, 5.4))
    bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.05, radius2=0.04, depth=(p1 - p0).length)
    d = (p1 - p0).normalized(); rot = d.to_track_quat('Z', 'Y').to_matrix().to_4x4()
    bmesh.ops.transform(bm, matrix=Matrix.Translation((p0 + p1) / 2) @ rot, verts=bm.verts)
    o = mesh_obj("Rafter%d" % i, bm, [wood], CH); o.location = (HX, HY, -0.18)

# forge: Poly Haven stone fire pit with emissive coals; anvil on a block beside it
pit = ph_model("stone_fire_pit", CH, "FirePit"); soften(pit)
mn, mx = bbox_world([pit]); s_ = 1.1 / max(mx.x - mn.x, mx.y - mn.y); pit.scale = (s_,) * 3
bpy.context.view_layer.update(); mn, mx = bbox_world([pit])
FORGE = Vector((HX + 1.9, HY + 2.0, 0))
pit.location = (FORGE.x - (mn.x + mx.x) / 2, FORGE.y - (mn.y + mx.y) / 2, -mn.z)
bpy.context.view_layer.update(); mn, mx = bbox_world([pit])
coal_m = flat("Coals", (0.025, 0.018, 0.015), rough=1.0, emit=(1.0, 0.28, 0.04), emit_str=2.0)
_n, _l = nodes_of(coal_m); _bs = next(x for x in _n if x.type == 'BSDF_PRINCIPLED')
_nz = _n.new('ShaderNodeTexNoise'); _nz.inputs['Scale'].default_value = 9.0
_mr = _n.new('ShaderNodeMapRange'); _mr.inputs['From Min'].default_value = 0.35; _mr.inputs['From Max'].default_value = 0.7
_mr.inputs['To Min'].default_value = 0.0; _mr.inputs['To Max'].default_value = 3.0
_l.new(_nz.outputs['Fac'], _mr.inputs['Value']); _l.new(_mr.outputs[0], _bs.inputs['Emission Strength'])
bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
for v in bm.verts: v.co = Vector((v.co.x * 0.36, v.co.y * 0.36, max(v.co.z, 0) * 0.08 + 0.02 * noise.noise(v.co * 6)))
ash_m = flat("Ash", (0.06, 0.05, 0.045), rough=1.0)
coal = mesh_obj("AshBed", bm, [ash_m], CH); coal.location = (FORGE.x, FORGE.y, mx.z * 0.45)
# individual coal lumps on the ash bed (dark, glowing in the cracks)
bm = bmesh.new()
for i in range(280):
    a_ = random.uniform(0, 2 * math.pi); r_ = 0.32 * math.sqrt(random.random())
    rad_ = random.uniform(0.018, 0.04)
    g_ = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=rad_)
    for v in g_['verts']:
        v.co = Vector((v.co.x * random.uniform(0.8, 1.3), v.co.y * random.uniform(0.8, 1.3), v.co.z * 0.7))
    h_ = max(0.0, 0.08 * (1 - (r_ / 0.36) ** 2)) * 0.36 / 0.36 * 0.36 + 0.01
    bmesh.ops.translate(bm, verts=g_['verts'], vec=(r_ * math.cos(a_), r_ * math.sin(a_), 0.03 * (1 - (r_ / 0.36) ** 2) + 0.04))
lumps = mesh_obj("Coals", bm, [coal_m], CH); lumps.location = (FORGE.x, FORGE.y, mx.z * 0.45)
sc["FORGE"] = list(FORGE); sc["FORGE_TOP"] = mx.z * 0.45 + 0.05

anvil = glb_asset("anvil", CH, target_size=0.62, axis=1)
block = ph_model("tree_stump_01", CH, "AnvilBlock"); soften(block)
mn, mx = bbox_world([block]); s_ = 0.5 / max(mx.x - mn.x, mx.y - mn.y); block.scale = (s_, s_, 0.6 / (mx.z - mn.z))
bpy.context.view_layer.update(); mn, mx = bbox_world([block])
ANV = Vector((HX + 0.6, HY + 1.2, 0))
block.location = (ANV.x - (mn.x + mx.x) / 2, ANV.y - (mn.y + mx.y) / 2, -mn.z)
bpy.context.view_layer.update(); mn, mx = bbox_world([block])
anvil.location = (ANV.x, ANV.y, mx.z - 0.01); anvil.rotation_euler = (0, 0, R_(90))
bpy.context.view_layer.update(); amn, amx = bbox_world([anvil])
sc["ANVIL"] = list(ANV); sc["ANVIL_TOP"] = amx.z
print("ANVIL top", round(amx.z, 3), "dims", tuple(round(d, 2) for d in anvil.dimensions))

# table for the knives (S10) on the open side
tbl_top = (Vector((HX - 1.8, HY + 2.2, 0.78)))
def box(name, mn_, mx_, mat, c):
    bm = bmesh.new(); add_box(bm, Vector(mn_), Vector(mx_)); o = mesh_obj(name, bm, [mat], c)
    b = o.modifiers.new("Bevel", 'BEVEL'); b.width = 0.01; b.segments = 2
    return o
T = tbl_top
box("TableTop", (T.x - 0.55, T.y - 0.32, T.z - 0.05), (T.x + 0.55, T.y + 0.32, T.z), wood, CH)
for dx in (-0.48, 0.48):
    for dy in (-0.26, 0.26):
        box("TableLeg", (T.x + dx - 0.04, T.y + dy - 0.04, 0), (T.x + dx + 0.04, T.y + dy + 0.04, T.z - 0.05), wood, CH)
sc["TABLE"] = list(T)

# baskets, buckets, crate with our logo
bask = ph_model("wicker_basket_01", CH, "Basket"); soften(bask)
mn, mx = bbox_world([bask]); s_ = 0.45 / max(mx.x - mn.x, mx.y - mn.y); bask.scale = (s_,) * 3
place(bask, (HX - 3.0, HY + 2.4, 0), 20, s_)
inst(bask, "Basket2", (HX - 2.5, HY + 3.0, 0), 75, s_ * 0.8, CH)
buck = ph_model("wooden_bucket_01", CH, "Bucket"); soften(buck)
mn, mx = bbox_world([buck]); s_ = 0.32 / max(mx.x - mn.x, mx.y - mn.y)
place(buck, (FORGE.x + 0.9, FORGE.y - 0.3, 0), 0, s_)
CR = Vector((HX - 1.05, HY - 0.75, 0)); cw = 0.62
crate = box("LogoCrate", (CR.x - cw / 2, CR.y - cw / 2, 0), (CR.x + cw / 2, CR.y + cw / 2, 0.55), wood, CH)
crate.rotation_euler = (0, 0, 0)
lm = logo_mat("LogoWhite", "white")
lg = decal("Logo_Crate", 0.5, 0.5 * 414 / 967, lm, CH)
lg.location = (CR.x + cw / 2 + 0.004, CR.y, 0.3); lg.rotation_euler = (0, 0, R_(90))
lg2 = decal("Logo_Crate2", 0.5, 0.5 * 414 / 967, lm, CH)
lg2.location = (CR.x, CR.y - cw / 2 - 0.004, 0.3)
sc["CRATE"] = list(CR)

# ================================================================== the battlefield at (-40, 0): invaders' flag on a pole
FL = Vector((-46.0, 6.0, 0))
bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=0.04, radius2=0.03, depth=6.0)
bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, 3.0))
pole = mesh_obj("FlagPole", bm, [wood], CB); shade_smooth(pole); pole.location = (FL.x, FL.y, gz(FL.x, FL.y) - 0.2)
flag_m = bpy.data.materials.new("Flag"); n, l = nodes_of(flag_m); bs = next(x for x in n if x.type == 'BSDF_PRINCIPLED')
tcn = n.new('ShaderNodeTexCoord'); sx = n.new('ShaderNodeSeparateXYZ'); l.new(tcn.outputs['UV'], sx.inputs[0])
# plain field with a red diagonal band (generic, no emblem)
dd = n.new('ShaderNodeMath'); dd.operation = 'SUBTRACT'; l.new(sx.outputs[0], dd.inputs[0]); l.new(sx.outputs[1], dd.inputs[1])
ab = n.new('ShaderNodeMath'); ab.operation = 'ABSOLUTE'; l.new(dd.outputs[0], ab.inputs[0])
lt = n.new('ShaderNodeMath'); lt.operation = 'LESS_THAN'; lt.inputs[1].default_value = 0.12; l.new(ab.outputs[0], lt.inputs[0])
fm = n.new('ShaderNodeMix'); fm.data_type = 'RGBA'; fm.inputs['A'].default_value = (0.95, 0.93, 0.88, 1); fm.inputs['B'].default_value = (0.7, 0.05, 0.05, 1)
l.new(lt.outputs[0], fm.inputs['Factor']); l.new(fm.outputs['Result'], bs.inputs['Base Color']); bs.inputs['Roughness'].default_value = 0.8
bm = bmesh.new(); uv = bm.loops.layers.uv.new(); NX, NZ = 24, 14; FW, FH = 1.9, 1.25
vs = [[bm.verts.new((i / NX * FW, 0, -j / NZ * FH)) for i in range(NX + 1)] for j in range(NZ + 1)]
for j in range(NZ):
    for i in range(NX):
        f = bm.faces.new([vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]])
        for lp in f.loops: lp[uv].uv = (lp.vert.co.x / FW, 1 + lp.vert.co.z / FH)
flag = mesh_obj("Flag", bm, [flag_m], CB); shade_smooth(flag)
flag.location = (FL.x + 0.04, FL.y, pole.location.z + 5.95)
m = flag.modifiers.new("Solid", 'SOLIDIFY'); m.thickness = 0.01
wv = flag.modifiers.new("Wave", 'WAVE'); wv.use_normal = False; wv.use_y = True; wv.use_x = False
wv.height = 0.09; wv.width = 0.9; wv.speed = 0.0; wv.narrowness = 1.0; wv.start_position_x = FL.x
wv.time_offset = 0.0   # keyed per frame in 03_anim.py (not Scene Time)
sc["FLAG"] = [FL.x, FL.y, pole.location.z + 5.95]

for o in bpy.data.objects:
    if o.type == 'MESH' and o.name.endswith("Src"): o.hide_render = True; o.hide_viewport = True
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SETS_DONE")
