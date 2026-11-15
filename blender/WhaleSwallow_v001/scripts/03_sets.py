"""All sets in one scene, far apart, each seen only by its own cameras:
  OCEAN  (origin)      sea surface (Ocean modifier), sky, clouds
  UNDER  (x=+3000)     bright underwater dome, sun shafts, caustic surface, plankton; humpback and shark swim here
  MOUTH  (x=+6000)     built mouth interior: tongue floor, palate, baleen walls, lip gap with sea light
  HOSP   (x=+9000)     hospital room: chequered floor, pale-blue walls, white bed, IV stand, cabinet, monitor, logo poster
blender -b --factory-startup -P 03_sets.py -- <repo>/blender <assets_dir> chars.blend whale.blend out.blend"""
import bpy, bmesh, sys, os, math, random
from mathutils import Vector, Matrix, Euler
a = sys.argv[sys.argv.index("--") + 1:]; ROOT, AS, CHARS, WHALE, OUT = a
bpy.ops.wm.open_mainfile(filepath=CHARS)
sc = bpy.context.scene
random.seed(7)
OCEAN, UNDER, MOUTH, HOSP = Vector((0, 0, 0)), Vector((3000, 0, 0)), Vector((6000, 0, 0)), Vector((9000, 0, 0))

def col(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in sc.collection.children: sc.collection.children.link(c)
    return c
def link(o, c):
    for u in list(o.users_collection): u.objects.unlink(o)
    c.objects.link(o)
def mat(name, rgb, rough=0.45, metal=0.0, emit=None, estr=0.0, alpha=1.0, coat=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; p = m.node_tree.nodes["Principled BSDF"]
    p.inputs['Base Color'].default_value = (*rgb, 1); p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal; p.inputs['Coat Weight'].default_value = coat
    if emit: p.inputs['Emission Color'].default_value = (*emit, 1); p.inputs['Emission Strength'].default_value = estr
    if alpha < 1: p.inputs['Alpha'].default_value = alpha
    return m
def box(name, size, loc, m, c, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot); o = bpy.context.object; o.name = name
    o.scale = size; bpy.ops.object.transform_apply(scale=True); o.data.materials.append(m); link(o, c)
    bev = o.modifiers.new("Bevel", 'BEVEL'); bev.width = min(0.02, min(size) * 0.2); bev.segments = 2
    return o
def glb(path, c):
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new: link(o, c)
    return new
def flatten(objs):
    meshes = [o for o in objs if o.type == 'MESH']
    for o in meshes:
        M = o.matrix_world.copy(); o.parent = None; o.matrix_world = M
    for o in [o for o in objs if o.type == 'EMPTY']: bpy.data.objects.remove(o)
    return meshes

for n, c in (("Diver", "CHARS"), ("DocM", "CHARS"), ("DocF", "CHARS")):
    r = bpy.data.objects[n]; cc = col(c); link(r, cc); r.location = (9000 + {"Diver": 0, "DocM": 2.5, "DocF": 3.2}[n], -3.0, 0)
    for ch in r.children: link(ch, cc)

# ---------------------------------------------------------------- world: sky for lighting, gradient set per set by domes
w = sc.world or bpy.data.worlds.new("World"); sc.world = w; w.use_nodes = True; nt = w.node_tree; nt.nodes.clear()
grad_tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ'); ramp = nt.nodes.new('ShaderNodeValToRGB')
nt.links.new(grad_tc.outputs['Window'], sep.inputs[0]); nt.links.new(sep.outputs['Y'], ramp.inputs[0])
ramp.color_ramp.elements[0].position = 0.45; ramp.color_ramp.elements[0].color = (0.78, 0.90, 1.0, 1)
ramp.color_ramp.elements[1].position = 1.0; ramp.color_ramp.elements[1].color = (0.12, 0.45, 0.95, 1)
bg_cam = nt.nodes.new('ShaderNodeBackground'); bg_cam.inputs[1].default_value = 1.0; nt.links.new(ramp.outputs[0], bg_cam.inputs[0])
bg_light = nt.nodes.new('ShaderNodeBackground'); bg_light.inputs[1].default_value = 0.8; bg_light.inputs[0].default_value = (0.55, 0.70, 0.90, 1)
lp = nt.nodes.new('ShaderNodeLightPath'); mix = nt.nodes.new('ShaderNodeMixShader')
nt.links.new(lp.outputs['Is Camera Ray'], mix.inputs[0]); nt.links.new(bg_light.outputs[0], mix.inputs[1]); nt.links.new(bg_cam.outputs[0], mix.inputs[2])
wo = nt.nodes.new('ShaderNodeOutputWorld'); nt.links.new(mix.outputs[0], wo.inputs[0])

# ---------------------------------------------------------------- OCEAN
C = col("SET_OCEAN")
bpy.ops.mesh.primitive_plane_add(size=1, location=OCEAN); sea = bpy.context.object; sea.name = "Sea"; link(sea, C)
oc = sea.modifiers.new("Ocean", 'OCEAN'); oc.geometry_mode = 'GENERATE'; oc.size = 4.0; oc.spatial_size = 60; oc.resolution = 14
oc.repeat_x = oc.repeat_y = 5; oc.wave_scale = 1.6; oc.choppiness = 1.1; oc.wind_velocity = 10; oc.use_normals = True
oc.use_foam = True; oc.foam_layer_name = "foam"; oc.foam_coverage = 0.0
sea.location = OCEAN - Vector((0, 0, 0)); sea.data.materials.clear()
wm = bpy.data.materials.new("SeaWater"); wm.use_nodes = True; N = wm.node_tree.nodes; P = N["Principled BSDF"]
P.inputs['Base Color'].default_value = (0.01, 0.13, 0.28, 1); P.inputs['Roughness'].default_value = 0.08
P.inputs['Specular IOR Level'].default_value = 0.05
P.inputs['Coat Weight'].default_value = 0.0
attr = N.new('ShaderNodeAttribute'); attr.attribute_name = "foam"; fr = N.new('ShaderNodeValToRGB')
fr.color_ramp.elements[0].position = 0.55; fr.color_ramp.elements[1].position = 0.95
mx = N.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.inputs['A'].default_value = (0.01, 0.13, 0.28, 1); mx.inputs['B'].default_value = (0.85, 0.92, 0.95, 1)
wm.node_tree.links.new(attr.outputs['Fac'], fr.inputs[0]); wm.node_tree.links.new(fr.outputs[0], mx.inputs['Factor'])
wm.node_tree.links.new(mx.outputs['Result'], P.inputs['Base Color'])
sea.data.materials.append(wm)
sea.keyframe_insert  # Ocean time is keyed in 04_anim (keyed values, not Scene Time)
cloud_m = mat("Cloud", (1, 1, 1), rough=0.9, emit=(1, 1, 1), estr=0.6)
for i in range(14):
    ang = random.uniform(0, 2 * math.pi); r = random.uniform(220, 330)
    base = OCEAN + Vector((math.cos(ang) * r, math.sin(ang) * r, random.uniform(45, 95)))
    for k in range(6):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=random.uniform(9, 16), location=base + Vector((random.uniform(-22, 22), random.uniform(-6, 6), random.uniform(-3, 5))))
        cl = bpy.context.object; cl.name = "Cloud"; cl.scale = (1.6, 1.0, 0.55); cl.data.materials.append(cloud_m); link(cl, C)
        cl.visible_shadow = False
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN')); sun.data.energy = 4.0; sun.data.angle = math.radians(3)
sun.rotation_euler = (math.radians(40), 0, math.radians(200)); C.objects.link(sun)

# ---------------------------------------------------------------- UNDER: dome with vertical gradient, surface, specks
C = col("SET_UNDER")
bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=180, location=UNDER); dome = bpy.context.object; dome.name = "UW_dome"; link(dome, C)
bpy.ops.object.shade_smooth(); dome.visible_shadow = False; dome.visible_diffuse = False; dome.visible_glossy = False
dm = bpy.data.materials.new("UW_gradient"); dm.use_nodes = True; N = dm.node_tree.nodes; N.clear()
tc = N.new('ShaderNodeTexCoord'); sx = N.new('ShaderNodeSeparateXYZ'); mr = N.new('ShaderNodeMapRange'); rr = N.new('ShaderNodeValToRGB')
mr.inputs['From Min'].default_value = -150; mr.inputs['From Max'].default_value = 150
rr.color_ramp.elements[0].position = 0.0; rr.color_ramp.elements[0].color = (0.02, 0.22, 0.36, 1)
rr.color_ramp.elements[1].position = 0.85; rr.color_ramp.elements[1].color = (0.30, 0.78, 0.92, 1)
em = N.new('ShaderNodeEmission'); em.inputs[1].default_value = 1.0; out = N.new('ShaderNodeOutputMaterial')
L = dm.node_tree.links; L.new(tc.outputs['Object'], sx.inputs[0]); L.new(sx.outputs['Z'], mr.inputs[0]); L.new(mr.outputs[0], rr.inputs[0])
L.new(rr.outputs[0], em.inputs[0]); L.new(em.outputs[0], out.inputs[0]); dome.data.materials.append(dm)
for p in dome.data.polygons: p.flip() if False else None
bpy.ops.mesh.primitive_plane_add(size=360, location=UNDER + Vector((0, 0, 40))); surf = bpy.context.object; surf.name = "UW_surface"; link(surf, C)
surf.visible_shadow = False; surf.visible_diffuse = False; surf.visible_glossy = False
sm = bpy.data.materials.new("UW_surface"); sm.use_nodes = True; N = sm.node_tree.nodes; N.clear()
vor = N.new('ShaderNodeTexVoronoi'); vor.feature = 'DISTANCE_TO_EDGE'; vor.inputs['Scale'].default_value = 0.06
rr = N.new('ShaderNodeValToRGB'); rr.color_ramp.elements[0].position = 0.0; rr.color_ramp.elements[0].color = (0.85, 0.97, 1, 1)
rr.color_ramp.elements[1].position = 0.12; rr.color_ramp.elements[1].color = (0.30, 0.75, 0.90, 1)
em = N.new('ShaderNodeEmission'); em.inputs[1].default_value = 1.4; out = N.new('ShaderNodeOutputMaterial')
L = sm.node_tree.links; L.new(vor.outputs['Distance'], rr.inputs[0]); L.new(rr.outputs[0], em.inputs[0]); L.new(em.outputs[0], out.inputs[0])
surf.data.materials.append(sm)
uw_sun = bpy.data.objects.new("UW_sun", bpy.data.lights.new("UW_sun", 'SUN')); uw_sun.data.energy = 2.2; uw_sun.data.color = (0.75, 0.95, 1.0)
uw_sun.rotation_euler = (math.radians(20), 0, math.radians(30)); C.objects.link(uw_sun)
# plankton specks: one mesh of tiny tetrahedra
bm = bmesh.new()
for i in range(900):
    c0 = UNDER + Vector((random.uniform(-60, 60), random.uniform(-60, 60), random.uniform(-25, 30)))
    s = random.uniform(0.02, 0.05)
    vs = [bm.verts.new(c0 + Vector(d) * s) for d in ((1, 0, 0), (-0.5, 0.86, 0), (-0.5, -0.86, 0), (0, 0, 1.2))]
    for f in ((0, 1, 2), (0, 1, 3), (1, 2, 3), (2, 0, 3)): bm.faces.new([vs[k] for k in f])
pm = bpy.data.meshes.new("Plankton"); bm.to_mesh(pm); bm.free()
pl = bpy.data.objects.new("UW_plankton", pm); C.objects.link(pl); pm.materials.append(mat("Speck", (0.9, 1, 1), emit=(0.8, 1, 1), estr=0.8))
pl.visible_shadow = False
# shafts of light: thin emissive transparent wedges from the surface
shm = bpy.data.materials.new("Shaft"); shm.use_nodes = True; N = shm.node_tree.nodes; N.clear()
tr = N.new('ShaderNodeBsdfTransparent'); em = N.new('ShaderNodeEmission'); em.inputs[0].default_value = (0.8, 0.97, 1, 1); em.inputs[1].default_value = 0.10
ad = N.new('ShaderNodeAddShader'); out = N.new('ShaderNodeOutputMaterial')
shm.node_tree.links.new(tr.outputs[0], ad.inputs[0]); shm.node_tree.links.new(em.outputs[0], ad.inputs[1]); shm.node_tree.links.new(ad.outputs[0], out.inputs[0])
try: shm.blend_method = 'BLEND'
except Exception: pass
for i in range(10):
    bpy.ops.mesh.primitive_plane_add(size=1, location=UNDER + Vector((random.uniform(-40, 40), random.uniform(10, 50), 10)))
    s = bpy.context.object; s.name = "UW_shaft"; s.scale = (random.uniform(1.5, 4), 1, 70); s.rotation_euler = (math.radians(90), math.radians(random.uniform(-14, -8)), math.radians(random.uniform(-20, 20)))
    s.data.materials.append(shm); link(s, C); s.visible_shadow = False
# shark
sh = glb(os.path.join(AS, "shark_bite.glb"), C)
ico = [o for o in sh if o.name.startswith("Icosphere")]
sh = [o for o in sh if o not in ico]
for o in ico: bpy.data.objects.remove(o)
srig = next(o for o in sh if o.type == 'ARMATURE'); top = srig
while top.parent: top = top.parent
top.name = "Shark_root"; top.location = UNDER + Vector((0, 0, 200)); top.scale = Vector(top.scale) * 0.75
srig.name = "SharkRig"
for o in sh:
    if o.type == 'MESH': o.name = "Shark_body"
if srig.animation_data and srig.animation_data.action: srig.animation_data.action.name = "SharkBite"
# shark look: cleaner (roughness, less bump)
for m in bpy.data.materials:
    if m.name == "material_0":
        m.name = "Shark_skin"; P = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
        for l in list(m.node_tree.links):
            if l.to_socket in (P.inputs['Roughness'], P.inputs['Metallic']): m.node_tree.links.remove(l)
        P.inputs['Roughness'].default_value = 0.4; P.inputs['Metallic'].default_value = 0.0
        for n in m.node_tree.nodes:
            if n.type == 'NORMAL_MAP': n.inputs['Strength'].default_value = 0.35
# whale
with bpy.data.libraries.load(WHALE, link=False) as (src, dst):
    dst.objects = [n for n in src.objects]
WC = col("WHALE")
for o in dst.objects: WC.objects.link(o)
wrig = bpy.data.objects["WhaleRig"]; wrig.location = UNDER + Vector((0, 0, 300))

# ---------------------------------------------------------------- MOUTH interior (y forward = toward the lip gap at -Y)
C = col("SET_MOUTH")
pink = mat("Mouth_tongue", (0.86, 0.38, 0.45), rough=0.32, coat=0.5)
palate = mat("Mouth_palate", (0.78, 0.30, 0.38), rough=0.35, coat=0.4)
bale = mat("Mouth_baleen", (0.22, 0.20, 0.19), rough=0.5)
fringe = mat("Mouth_fringe", (0.62, 0.57, 0.5), rough=0.6)
# tongue floor: 7 x 9 m, domed, soft noise
bpy.ops.mesh.primitive_grid_add(x_subdivisions=70, y_subdivisions=90, size=1, location=(0, 0, 0)); tg = bpy.context.object; tg.name = "Mouth_tongue"
tg.scale = (7, 9, 1); bpy.ops.object.transform_apply(scale=True)
for v in tg.data.vertices:
    x, y = v.co.x, v.co.y
    v.co.z = 0.55 * math.exp(-(x / 2.2) ** 2) * (0.6 + 0.4 * math.cos(min(1, abs(y) / 4.5) * math.pi / 2)) + 0.06 * math.sin(x * 2.1) * math.sin(y * 1.7) + 0.35 * (abs(x) / 3.5) ** 3
tg.location = MOUTH; tg.data.materials.append(pink); link(tg, C); bpy.ops.object.shade_smooth()
sub = tg.modifiers.new("Sub", 'SUBSURF'); sub.levels = sub.render_levels = 1
# palate: half tube over the floor, radius 3.4, from y=-4.5 to +4.5, with ridges; open at the lip end (-Y)
bm = bmesh.new()
NX, NY = 48, 60; R0 = 3.4
grid = []
for j in range(NY + 1):
    y = -4.5 + 9.0 * j / NY; row = []
    for i in range(NX + 1):
        t = math.pi * i / NX; r = R0 * (1 + 0.025 * math.sin(y * 9))
        row.append(bm.verts.new(MOUTH + Vector((-math.cos(t) * r, y, 0.25 + math.sin(t) * r * 0.82))))
    grid.append(row)
for j in range(NY):
    for i in range(NX):
        bm.faces.new([grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]])
pmesh = bpy.data.meshes.new("Mouth_palate"); bm.to_mesh(pmesh); bm.free()
pal = bpy.data.objects.new("Mouth_palate", pmesh); C.objects.link(pal); pmesh.materials.append(palate)
for p in pal.data.polygons: p.use_smooth = True
# back of the throat: a closing wall at +Y with a darker red ring (lit, never black)
bpy.ops.mesh.primitive_circle_add(vertices=48, radius=3.4, fill_type='TRIFAN', location=MOUTH + Vector((0, 4.5, 0.4)), rotation=(math.radians(90), 0, 0))
th = bpy.context.object; th.name = "Mouth_throat"; th.scale = (1, 0.82, 1); th.data.materials.append(mat("Mouth_throat", (0.55, 0.16, 0.22), rough=0.4)); link(th, C)
# baleen walls: plates hanging from the palate edge on both sides, from y=-4.2 to +3.8
bm = bmesh.new(); bmf = bmesh.new()
for side in (-1, 1):
    y = -4.2
    while y < 3.8:
        top = MOUTH + Vector((side * 3.05, y, 1.9)); h = 1.55 + 0.1 * math.sin(y * 3); wdt = 0.55; t = 0.018
        inward = Vector((-side, 0, 0))
        def plate(bmx, z0, z1, wf):
            vs = [bmx.verts.new(top + Vector((0, dy, 0)) + inward * dx + Vector((0, 0, dz))) for dx, dy, dz in
                  [(0, -t, -z0), (0, t, -z0), (wdt * wf, t, -z0), (wdt * wf, -t, -z0), (0, -t, -z1), (0, t, -z1), (wdt * wf * 0.45, t, -z1 * 0.97), (wdt * wf * 0.45, -t, -z1 * 0.97)]]
            for f in [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]: bmx.faces.new([vs[k] for k in f])
        plate(bm, 0.0, h * 0.8, 1.0); plate(bmf, h * 0.8, h, 0.7)
        y += 0.075
for nm, b_, m_ in (("Mouth_baleen", bm, bale), ("Mouth_fringe", bmf, fringe)):
    me = bpy.data.meshes.new(nm); b_.to_mesh(me); b_.free(); o = bpy.data.objects.new(nm, me); C.objects.link(o); me.materials.append(m_)
# lip gap: the front end is closed by the two lips with a bright horizontal slit of sea light
lipm = mat("Mouth_lip", (0.30, 0.30, 0.34), rough=0.5)
box("Mouth_lip_upper", (7.4, 0.5, 2.6), MOUTH + Vector((0, -4.6, 3.05)), lipm, C)
box("Mouth_lip_lower", (7.4, 0.5, 1.2), MOUTH + Vector((0, -4.6, -0.1)), lipm, C)
gl = mat("Mouth_gap_light", (0.6, 0.9, 1), emit=(0.65, 0.92, 1.0), estr=6.0)
bpy.ops.mesh.primitive_plane_add(size=1, location=MOUTH + Vector((0, -4.95, 1.1)), rotation=(math.radians(90), 0, 0)); gp = bpy.context.object
gp.name = "Mouth_gap_glow"; gp.scale = (7.4, 1.6, 1); gp.data.materials.append(gl); link(gp, C)
sp = bpy.data.objects.new("Mouth_gap_spot", bpy.data.lights.new("Mouth_gap_spot", 'AREA')); sp.data.energy = 900; sp.data.size = 6; sp.data.size_y = 0.6
sp.data.shape = 'RECTANGLE'; sp.data.color = (0.7, 0.92, 1.0); sp.location = MOUTH + Vector((0, -4.2, 1.15)); sp.rotation_euler = (math.radians(-80), 0, 0); C.objects.link(sp)
fill = bpy.data.objects.new("Mouth_fill", bpy.data.lights.new("Mouth_fill", 'AREA')); fill.data.energy = 500; fill.data.size = 4
fill.data.color = (1.0, 0.78, 0.8); fill.location = MOUTH + Vector((0, 0.5, 2.9)); C.objects.link(fill)
# ---------------------------------------------------------------- HOSPITAL room
C = col("SET_HOSP")
O = HOSP
tile = bpy.data.materials.new("Floor_checker"); tile.use_nodes = True; N = tile.node_tree.nodes; P = N["Principled BSDF"]
ck = N.new('ShaderNodeTexChecker'); ck.inputs['Scale'].default_value = 16; ck.inputs['Color1'].default_value = (0.9, 0.92, 0.94, 1); ck.inputs['Color2'].default_value = (0.10, 0.13, 0.18, 1)
tile.node_tree.links.new(ck.outputs['Color'], P.inputs['Base Color']); P.inputs['Roughness'].default_value = 0.35
bpy.ops.mesh.primitive_plane_add(size=8, location=O); fl = bpy.context.object; fl.name = "Hosp_floor"; fl.data.materials.append(tile); link(fl, C)
wallm = mat("Hosp_wall", (0.42, 0.62, 0.78), rough=0.6); ceil = mat("Hosp_ceiling", (0.95, 0.96, 0.97), rough=0.7)
box("Hosp_wall_back", (8, 0.1, 3.2), O + Vector((0, 4, 1.6)), wallm, C)
box("Hosp_wall_left", (0.1, 8, 3.2), O + Vector((-4, 0, 1.6)), wallm, C)
box("Hosp_wall_right", (0.1, 8, 3.2), O + Vector((4, 0, 1.6)), wallm, C)
box("Hosp_wall_front", (8, 0.1, 3.2), O + Vector((0, -4.6, 1.6)), wallm, C)
box("Hosp_ceiling", (8, 8.8, 0.1), O + Vector((0, -0.3, 3.25)), ceil, C)
for i, p in enumerate([(-1.5, 1.0), (1.5, 1.0), (-1.5, -2.0), (1.5, -2.0)]):
    l = bpy.data.objects.new("Hosp_light%d" % i, bpy.data.lights.new("Hosp_light%d" % i, 'AREA')); l.data.energy = 110; l.data.size = 1.2
    l.location = O + Vector((p[0], p[1], 3.1)); C.objects.link(l)
    box("Hosp_lamp%d" % i, (1.2, 1.2, 0.03), O + Vector((p[0], p[1], 3.19)), mat("Lamp", (1, 1, 1), emit=(1, 1, 1), estr=3), C)
skirt = mat("Hosp_skirting", (0.85, 0.88, 0.9), rough=0.5)
box("Hosp_skirt_back", (8, 0.04, 0.12), O + Vector((0, 3.94, 0.06)), skirt, C)
# bed (CC-BY, Yvo Pors), cm -> m, long axis Y, head at +Y against the back wall
bd = flatten(glb(os.path.join(AS, "bed_white.glb"), C))
for o in bd: o.select_set(True)
bpy.context.view_layer.objects.active = bd[0]; bpy.ops.object.join(); bed = bpy.context.object; bed.name = "Bed"
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
cs_ = [Vector(c) for c in bed.bound_box]; ctr = sum(cs_, Vector()) / 8; zb = min(c.z for c in cs_)
bed.data.transform(Matrix.Translation(-Vector((ctr.x, ctr.y, zb)))); bed.data.transform(Matrix.Diagonal((0.0068, 0.0068, 0.0068, 1)))
bed.location = O + Vector((0, 1.6, 0)); bed.rotation_euler = (0, 0, 0); bed.scale = (1, 1, 1)
bed.data.materials.clear(); bed.data.materials.append(mat("Bed_white", (0.93, 0.94, 0.95), rough=0.4))
print("BED dims", [round(d, 2) for d in bed.dimensions], "loc", tuple(round(x, 2) for x in bed.location))
sheet = mat("Bed_sheet", (0.82, 0.9, 0.97), rough=0.8)
# IV stand
st = mat("Steel", (0.75, 0.77, 0.8), rough=0.3, metal=0.8)
bpy.ops.mesh.primitive_cylinder_add(radius=0.015, depth=1.9, location=O + Vector((1.1, 2.6, 0.95))); iv = bpy.context.object; iv.name = "IV_pole"; iv.data.materials.append(st); link(iv, C)
bpy.ops.mesh.primitive_cylinder_add(radius=0.25, depth=0.03, location=O + Vector((1.1, 2.6, 0.04))); ivb = bpy.context.object; ivb.name = "IV_base"; ivb.data.materials.append(st); link(ivb, C)
box("IV_bag", (0.16, 0.05, 0.26), O + Vector((1.1, 2.6, 1.72)), mat("IV_bag", (0.85, 0.95, 1.0), rough=0.15), C)
# wall cabinet and monitor (blank screen)
box("Cabinet", (1.4, 0.4, 0.7), O + Vector((-2.4, 3.78, 1.9)), mat("Cabinet", (0.94, 0.95, 0.96), rough=0.4), C)
box("Cabinet_low", (1.4, 0.5, 0.9), O + Vector((-2.4, 3.72, 0.45)), mat("Cabinet2", (0.93, 0.94, 0.95), rough=0.4), C)
box("Monitor", (0.55, 0.06, 0.4), O + Vector((1.9, 3.88, 1.75)), mat("Monitor_frame", (0.2, 0.22, 0.25), rough=0.4), C)
box("Monitor_screen", (0.5, 0.01, 0.34), O + Vector((1.9, 3.845, 1.75)), mat("Monitor_screen", (0.1, 0.3, 0.35), emit=(0.25, 0.75, 0.7), estr=1.5), C)
box("Chair", (0.5, 0.5, 0.45), O + Vector((-1.5, 1.2, 0.225)), mat("Chair", (0.35, 0.55, 0.75), rough=0.5), C)
# logo poster on the back wall, behind the doctors' shot (dark logo on a white board)
logo = bpy.data.images.load(os.path.join(ROOT, "assets/brand/DaKrasFilms_logo_dark.png")); logo.pack()
pm_ = bpy.data.materials.new("Poster_logo"); pm_.use_nodes = True; N = pm_.node_tree.nodes; P = N["Principled BSDF"]
ti = N.new('ShaderNodeTexImage'); ti.image = logo; mxc = N.new('ShaderNodeMix'); mxc.data_type = 'RGBA'
mxc.inputs['A'].default_value = (0.97, 0.97, 0.96, 1)
pm_.node_tree.links.new(ti.outputs['Alpha'], mxc.inputs['Factor']); pm_.node_tree.links.new(ti.outputs['Color'], mxc.inputs['B'])
pm_.node_tree.links.new(mxc.outputs['Result'], P.inputs['Base Color']); P.inputs['Roughness'].default_value = 0.5
bpy.ops.mesh.primitive_plane_add(size=1, location=O + Vector((-0.3, 3.94, 1.85)), rotation=(math.radians(90), 0, 0)); pst = bpy.context.object
pst.name = "Poster_logo"; pst.scale = (1.3, 1.3 * 414 / 967 + 0.12, 1); pst.data.materials.append(pm_); link(pst, C)
bpy.ops.object.transform_apply(scale=True)
box("Poster_frame", (1.38, 0.02, 0.76), O + Vector((-0.3, 3.955, 1.85)), mat("Poster_frame", (0.3, 0.45, 0.65), rough=0.4), C)

# ---------------------------------------------------------------- life vest (CC-BY, DPMA): orange, fitted on the diver
VC = col("CHARS")
vs_ = flatten(glb(os.path.join(AS, "lifevest.glb"), VC)); vest = vs_[0]; vest.name = "Diver.vest"
for m in vest.data.materials:
    P = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bl = next((l for l in m.node_tree.links if l.to_socket == P.inputs['Base Color']), None)
    if bl:
        hs = m.node_tree.nodes.new('ShaderNodeHueSaturation'); hs.inputs['Hue'].default_value = 0.08 + 0.5 - 0.5
        src = bl.from_socket; m.node_tree.links.remove(bl)
        bw = m.node_tree.nodes.new('ShaderNodeRGBToBW'); m.node_tree.links.new(src, bw.inputs[0])
        rmp = m.node_tree.nodes.new('ShaderNodeValToRGB')
        rmp.color_ramp.elements[0].position = 0.06; rmp.color_ramp.elements[0].color = (0.04, 0.04, 0.045, 1)
        rmp.color_ramp.elements[1].position = 0.18; rmp.color_ramp.elements[1].color = (0.95, 0.30, 0.03, 1)
        m.node_tree.links.new(bw.outputs[0], rmp.inputs[0]); m.node_tree.links.new(rmp.outputs[0], P.inputs['Base Color'])
    for l in list(m.node_tree.links):
        if l.to_socket in (P.inputs['Roughness'], P.inputs['Metallic']): m.node_tree.links.remove(l)
    P.inputs['Roughness'].default_value = 0.5; P.inputs['Metallic'].default_value = 0.0
diver = bpy.data.objects["Diver"]; dbody = bpy.data.objects["Diver.body"]
diver.location = (0, 0, 0); bpy.context.view_layer.update()   # weights must be transferred with the rig at the origin
BN = diver.data.bones
ch_z = (BN["spine03"].head_local.z + BN["neck01"].head_local.z) / 2 - 0.06
bpy.context.view_layer.objects.active = vest; vest.select_set(True)
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
vest.location = (BN["spine03"].head_local.x, BN["spine03"].head_local.y - 0.005, ch_z)
vest.scale = (0.30, 0.30, 0.30); bpy.ops.object.transform_apply(location=False, scale=True)
bpy.context.view_layer.update()
print("VEST dims", [round(d, 3) for d in vest.dimensions], "at", tuple(round(x, 3) for x in vest.location))
vest.parent = diver; vest.matrix_parent_inverse = diver.matrix_world.inverted()
dt = vest.modifiers.new("DT", 'DATA_TRANSFER'); dt.object = dbody; dt.use_vert_data = True; dt.data_types_verts = {'VGROUP_WEIGHTS'}
dt.vert_mapping = 'POLYINTERP_NEAREST'; dt.layers_vgroup_select_src = 'ALL'; dt.layers_vgroup_select_dst = 'NAME'
bpy.ops.object.datalayout_transfer(modifier="DT"); bpy.ops.object.modifier_apply(modifier="DT")
for g in list(vest.vertex_groups):
    if g.name not in BN: vest.vertex_groups.remove(g)
am = vest.modifiers.new("Armature", 'ARMATURE'); am.object = diver
sw = vest.modifiers.new("KeepOut", 'SHRINKWRAP'); sw.target = dbody; sw.wrap_method = 'NEAREST_SURFACEPOINT'; sw.wrap_mode = 'OUTSIDE'; sw.offset = 0.012
vest.hide_render = vest.hide_viewport = True   # keyed visible only in the hospital shots (04_anim)

sc.render.engine = 'CYCLES'; sc.render.resolution_x, sc.render.resolution_y = 1080, 1920; sc.render.fps = 60
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("SETS_DONE", OUT)
