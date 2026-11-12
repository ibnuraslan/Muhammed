"""All sets in one continuous space (one camera flies between them):
  jungle edge + enclosure (x < 4), rescue clinic room (x 4..10), monitor-portal data void behind the clinic wall (x 10..18).
blender -b -P 03_sets.py -- <out.blend>   (needs work/bird.blend, work/vets.blend)"""
import bpy, bmesh, sys, os, math, random
import numpy as np
from mathutils import Vector, Matrix, Euler
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(HERE, "assets"); PH = os.path.join(A, "ph"); WK = os.path.join(HERE, "work")
out = sys.argv[sys.argv.index("--") + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
random.seed(4)
R_ = math.radians

def coll(name):
    c = bpy.data.collections.new(name); sc.collection.children.link(c); return c
C_J, C_C, C_V, C_P = coll("Jungle"), coll("Clinic"), coll("Void"), coll("Props")

def link(o, c):
    for x in o.users_collection: x.objects.unlink(o)
    c.objects.link(o)

def pbr(name, pid, scale=1.0, disp=0.0, tint=None, rough_mul=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; L = nt.links
    b = N["Principled BSDF"]; T = os.path.join(PH, pid, "textures")
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (scale, scale, scale)
    L.new(tc.outputs["UV"], mp.inputs[0])
    def tex(key, nc=False):
        fs = [f for f in os.listdir(T) if key in f]
        if not fs: return None
        t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(os.path.join(T, fs[0]), check_existing=True)
        if nc: t.image.colorspace_settings.name = "Non-Color"
        L.new(mp.outputs[0], t.inputs[0]); return t
    d = tex("diff") or tex("col")
    if tint:
        mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs[0].default_value = 1
        L.new(d.outputs[0], mx.inputs[6]); mx.inputs[7].default_value = tint + (1,); L.new(mx.outputs[2], b.inputs["Base Color"])
    else: L.new(d.outputs[0], b.inputs["Base Color"])
    r = tex("rough", True)
    if r:
        if rough_mul != 1.0:
            mm = N.new("ShaderNodeMath"); mm.operation = 'MULTIPLY'; mm.inputs[1].default_value = rough_mul
            L.new(r.outputs[0], mm.inputs[0]); L.new(mm.outputs[0], b.inputs["Roughness"])
        else: L.new(r.outputs[0], b.inputs["Roughness"])
    n = tex("nor_gl", True)
    if n:
        nm = N.new("ShaderNodeNormalMap"); L.new(n.outputs[0], nm.inputs["Color"]); L.new(nm.outputs[0], b.inputs["Normal"])
    if disp:
        dp = tex("disp", True)
        if dp:
            dn = N.new("ShaderNodeDisplacement"); dn.inputs["Scale"].default_value = disp; L.new(dp.outputs[0], dn.inputs["Height"])
            L.new(dn.outputs[0], N["Material Output"].inputs["Displacement"]); m.displacement_method = 'BOTH'
    return m

def imp(name, c, size=None, axis=None, loc=(0, 0, 0), rotz=0.0, base=True, join=True):
    """import glb, apply transforms, optionally join; scale so the largest (or `axis`) dimension == size; base at loc"""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(A, name + ".glb"))
    new = [o for o in bpy.data.objects if o not in before]
    ms = [o for o in new if o.type == 'MESH']
    for o in ms:
        mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
    for o in new:
        if o.type != 'MESH': bpy.data.objects.remove(o)
    for o in bpy.context.selected_objects: o.select_set(False)
    for o in ms: o.select_set(True)
    bpy.context.view_layer.objects.active = ms[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    if join and len(ms) > 1:
        bpy.ops.object.join(); ms = [bpy.context.view_layer.objects.active]
    o = ms[0]; o.name = name
    V = np.array([v.co[:] for v in o.data.vertices]); mn, mx = V.min(0), V.max(0)
    dim = mx - mn; k = 1.0
    if size: k = size / (dim[axis] if axis is not None else dim.max())
    ctr = Vector(((mn[0] + mx[0]) / 2, (mn[1] + mx[1]) / 2, mn[2] if base else (mn[2] + mx[2]) / 2))
    o.data.transform(Matrix.Scale(k, 4) @ Matrix.Translation(-ctr))
    o.location = loc; o.rotation_euler = (0, 0, rotz)
    link(o, c); o.select_set(False)
    return o

def box(name, c, size, loc, mat=None, bevel=0.0):
    me = bpy.data.meshes.new(name); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    bm.to_mesh(me); bm.free(); o = bpy.data.objects.new(name, me); c.objects.link(o)
    o.scale = size; o.location = loc
    if mat: me.materials.append(mat)
    bpy.context.view_layer.objects.active = o; o.select_set(True); bpy.ops.object.transform_apply(location=False, rotation=False, scale=True); o.select_set(False)
    if bevel:
        bv = o.modifiers.new("bv", 'BEVEL'); bv.width = bevel; bv.segments = 3
    me.uv_layers.new() if not me.uv_layers else None
    return o

def cube_uv(o, s=1.0):
    """box-project UVs in world-ish metres so tiling textures have real scale"""
    me = o.data
    if not me.uv_layers: me.uv_layers.new()
    uv = me.uv_layers.active.data
    for p in me.polygons:
        n = p.normal; ax = max(range(3), key=lambda i: abs(n[i]))
        for li in p.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            u, v = [co[i] for i in range(3) if i != ax]
            uv[li].uv = (u * s, v * s)

# ------------------------------------------------------------------ world, render
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, 100
sc.render.fps = 60; sc.frame_start = 1; sc.frame_end = 2250
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 48; sc.cycles.adaptive_threshold = 0.05
sc.cycles.use_denoising = True; sc.cycles.denoiser = 'OPENIMAGEDENOISE'
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = 0.5
sc.cycles.max_bounces = 6; sc.cycles.transparent_max_bounces = 16
w = bpy.data.worlds.new("World"); sc.world = w; w.use_nodes = True
env = w.node_tree.nodes.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(os.path.join(PH, "hdri", "forest_slope_1k.hdr"))
mpw = w.node_tree.nodes.new("ShaderNodeMapping"); tcw = w.node_tree.nodes.new("ShaderNodeTexCoord")
w.node_tree.links.new(tcw.outputs["Generated"], mpw.inputs[0]); w.node_tree.links.new(mpw.outputs[0], env.inputs[0])
mpw.inputs["Rotation"].default_value = (0, 0, R_(140))
w.node_tree.links.new(env.outputs[0], w.node_tree.nodes["Background"].inputs[0]); w.node_tree.nodes["Background"].inputs[1].default_value = 0.9

# ------------------------------------------------------------------ JUNGLE
M_ground = pbr("Forest_floor", "brown_mud_leaves_01", scale=12, tint=(0.8, 0.75, 0.6))
bpy.ops.mesh.primitive_grid_add(x_subdivisions=160, y_subdivisions=160, size=30, location=(-11.1, 0, 0))
g = bpy.context.active_object; g.name = "Ground"; link(g, C_J); g.data.materials.append(M_ground)
tx = bpy.data.textures.new("gnd", 'CLOUDS'); tx.noise_scale = 2.5
d = g.modifiers.new("d", 'DISPLACE'); d.texture = tx; d.strength = 0.35; d.mid_level = 0.6
g.data.polygons.foreach_set("use_smooth", [True] * len(g.data.polygons))
# keep clinic floor area flat-ish: vertex group mask
vg = g.vertex_groups.new(name="mask")
for v in g.data.vertices:
    x = v.co.x + g.location.x
    vg.add([v.index], float(min(1, max(0, (3.0 - x) / 1.5))), 'REPLACE')
d.vertex_group = "mask"
leaf_litter = pbr("Leaf_litter", "forest_leaves_02", scale=1.0)

M_bark = pbr("Bark", "bark_brown_02", scale=1.0, disp=0.04)
M_bark2 = pbr("Bark_willow", "bark_willow_02", scale=1.0, disp=0.05)
def trunk(name, loc, r, h, mat, lean=(0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=r, depth=h, location=(loc[0], loc[1], h / 2 - 0.3))
    t = bpy.context.active_object; t.name = name; link(t, C_J)
    bpy.ops.object.shade_smooth()
    sub = t.modifiers.new("s", 'SUBSURF'); sub.levels = 1; sub.render_levels = 2
    tx_ = bpy.data.textures.new(name, 'STUCCI'); tx_.noise_scale = 0.25
    dd = t.modifiers.new("d", 'DISPLACE'); dd.texture = tx_; dd.strength = r * 0.06
    tx2 = bpy.data.textures.new(name + "b", 'CLOUDS'); tx2.noise_scale = 1.2
    dd2 = t.modifiers.new("d2", 'DISPLACE'); dd2.texture = tx2; dd2.strength = r * 0.15
    t.rotation_euler = (R_(lean[0]), R_(lean[1]), random.uniform(0, 6))
    # cylindrical UVs
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.cylinder_project(scale_to_bounds=False); bpy.ops.object.mode_set(mode='OBJECT')
    for l in t.data.uv_layers.active.data: l.uv = (l.uv[0] * 2 * math.pi * r, l.uv[1] * h)
    t.data.materials.append(mat); return t
trunk("Trunk_hero", (-0.62, 0.05), 0.2, 9, M_bark2, (2, -3))
for i, (x, y, r) in enumerate([(-3.5, -2.5, 0.35), (-6, 2.5, 0.5), (-2.2, 4.2, 0.28), (-8, -5, 0.6), (-4.5, 6.5, 0.4),
                                (1.5, -6.5, 0.3), (-10, 1, 0.7), (0.5, 6.0, 0.25), (-1.8, -5.5, 0.32), (2.5, 4.5, 0.22)]):
    trunk("Trunk_%d" % i, (x, y), r, 24, M_bark if i % 2 else M_bark2, (random.uniform(-4, 4), random.uniform(-4, 4)))

# perch branch (scanned) running along x from the hero trunk
br = imp("branch", C_J, size=1.25, loc=(0, 0, 0))
V = np.array([v.co[:] for v in br.data.vertices]); dims = V.max(0) - V.min(0)
ax = int(np.argmax(dims))
if ax == 1: br.data.transform(Matrix.Rotation(R_(90), 4, 'Z'))
if ax == 2: br.data.transform(Matrix.Rotation(R_(90), 4, 'Y'))
V = np.array([v.co[:] for v in br.data.vertices]); c = (V.max(0) + V.min(0)) / 2
br.data.transform(Matrix.Translation(Vector((-c[0], -c[1], -c[2]))))
br.location = (-0.0, 0.0, 1.6); br.name = "Perch"
# second branch for the background toucan + vines
br2 = br.copy(); br2.data = br.data; br2.name = "Perch_bg"; C_J.objects.link(br2)
br2.location = (-3.3, -2.0, 3.1); br2.rotation_euler = (0, R_(-8), R_(35))

# tropical plants scattered (real CC-BY models), each with gentle sway (background life)
plants = [imp(n, C_P, size=1.0) for n in ("monstera", "plant2", "plant3")]
for p in plants: p.hide_render = True; p.hide_viewport = True; p.location = (0, 0, -50)
def plant(i, loc, size, rot=None):
    src = plants[i % 3]; o = src.copy(); o.data = src.data; o.hide_render = False; o.hide_viewport = False
    C_J.objects.link(o); o.location = loc; o.scale = (size,) * 3; o.rotation_euler = (0, 0, rot if rot is not None else random.uniform(0, 6.28))
    o.name = "Plant_%03d" % len(C_J.objects)
    for k in range(2):
        fc = o.driver_add("rotation_euler", k)
        fc.driver.expression = "%.3f*sin(frame/%.1f+%.2f)" % (R_(2.2), random.uniform(38, 70), random.uniform(0, 6))
    return o
# foreground cluster the camera flies through (between perch and clinic window)
for k in range(9):
    plant(k, (2.3 + random.uniform(-0.4, 0.4), random.uniform(-0.9, 0.9), 0), random.uniform(1.3, 2.0))
for k in range(70):
    a = random.uniform(0, 6.28); rr = random.uniform(1.0, 9.0)
    x, y = -1.0 + rr * math.cos(a), rr * math.sin(a)
    if x > 3.2: continue
    if -0.6 < x < 2.0 and -1.3 < y < 2.6: continue
    if -1.6 < x < 2.8 and -4.3 < y < -1.0: continue          # enclosure camera orbit          # keep the camera corridor around the perch clear
    plant(k, (x, y, 0), random.uniform(0.7, 2.4))
# plants on the trunk height near the perch (epiphytes/understory behind bird)
for k, (x, y, z, s) in enumerate([(-0.9, -0.9, 0, 2.6), (0.4, -1.7, 0, 2.2), (-1.5, 0.9, 0, 2.4), (-1.0, 2.0, 0, 1.8), (0.2, -2.4, 0, 2.8)]):
    plant(k, (x, y, z), s)

# fig on a twig hanging in front of the bird (feeding beat); figs for the enclosure dish
fig_src = imp("fig", C_P, size=0.05, base=False); fig_src.name = "Fig"
fig_src.location = (0, 0.3, 1.86)
fig2 = fig_src.copy(); fig2.data = fig_src.data; fig2.name = "Fig_enclosure"; C_P.objects.link(fig2)
twig = imp("stick", C_J, size=0.42, base=False); twig.name = "Fig_twig"
V = np.array([v.co[:] for v in twig.data.vertices]); ax = int(np.argmax(V.max(0) - V.min(0)))
if ax == 0: twig.data.transform(Matrix.Rotation(R_(90), 4, 'Y'))
if ax == 1: twig.data.transform(Matrix.Rotation(R_(90), 4, 'X'))
twig.data.transform(Matrix.Diagonal((0.4, 0.4, 1.0, 1.0)))
# the stick that strikes (scanned wood)
weapon = imp("stick", C_P, size=0.95, base=False); weapon.name = "Strike_stick"
V = np.array([v.co[:] for v in weapon.data.vertices]); ax = int(np.argmax(V.max(0) - V.min(0)))
if ax == 0: weapon.data.transform(Matrix.Rotation(R_(90), 4, 'Y'))
if ax == 1: weapon.data.transform(Matrix.Rotation(R_(90), 4, 'X'))
weapon.data.transform(Matrix.Diagonal((0.38, 0.38, 1.0, 1.0)))   # slimmer: a swung branch, not a log
weapon.data.transform(Matrix.Translation(Vector((0, 0, 0.42))))   # pivot near one end (z from -0.05 to 0.9)

# dust motes in the light (background life)
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.0012, location=(0, 0, -60)); mote = bpy.context.active_object; mote.name = "Mote"; link(mote, C_P)
mm_ = bpy.data.materials.new("Mote"); mm_.use_nodes = True; mm_.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = (1, 0.9, 0.7, 1)
mm_.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 3; mote.data.materials.append(mm_)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0.3, 0, 2.0)); em = bpy.context.active_object; em.name = "Mote_emitter"; em.scale = (4, 4, 2.2); link(em, C_J)
ps = em.modifiers.new("motes", 'PARTICLE_SYSTEM').particle_system.settings
ps.count = 900; ps.frame_start = -200; ps.frame_end = -199; ps.lifetime = 5000; ps.emit_from = 'VOLUME'
ps.physics_type = 'NEWTON'; ps.effector_weights.gravity = 0.0; ps.brownian_factor = 0.02; ps.normal_factor = 0; ps.render_type = 'OBJECT'; ps.instance_object = mote
ps.particle_size = 1.0; ps.size_random = 0.6
em.show_instancer_for_render = False

# sun shafts
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN')); C_J.objects.link(sun)
sun.data.energy = 3.5; sun.data.angle = R_(2.0); sun.data.color = (1.0, 0.9, 0.75); sun.rotation_euler = (R_(48), R_(18), R_(-120))

# ------------------------------------------------------------------ ENCLOSURE (outside the clinic, beside the window)
fence = imp("fence", C_J, size=2.6, axis=2, loc=(0.0, -6.2, 0), rotz=0.0)
print("FENCE dims", fence.dimensions[:])
fence2 = fence.copy(); fence2.data = fence.data; C_J.objects.link(fence2); fence2.location = (-5.6, -10.0, 0); fence2.rotation_euler = (0, 0, R_(90))
enc_perch = br.copy(); enc_perch.data = br.data; enc_perch.name = "Perch_enclosure"; C_J.objects.link(enc_perch)
enc_perch.location = (-0.15, -3.75, 1.15); enc_perch.rotation_euler = (0, R_(3), R_(-20))
M_wood = pbr("Rough_wood", "rough_wood", scale=1.0)
plat = box("Feeding_platform", C_J, (0.34, 0.26, 0.035), (1.02, -3.02, 1.235), M_wood, bevel=0.005); cube_uv(plat)
post = box("Platform_post", C_J, (0.07, 0.07, 1.22), (1.02, -3.02, 0.61), M_wood, bevel=0.006); cube_uv(post)
for k in range(10):
    plant(k, (random.uniform(-1.2, 2.4), random.uniform(-5.9, -4.4), 0), random.uniform(1.0, 2.2))
encl = bpy.data.objects.new("Enclosure_sky", bpy.data.lights.new("Enclosure_sky", 'AREA')); C_J.objects.link(encl)
encl.data.size = 3.0; encl.data.energy = 220; encl.data.color = (0.85, 0.92, 1.0); encl.location = (2.2, -1.6, 3.0)
encl.rotation_euler = (Vector((0.98, -3.1, 1.3)) - encl.location).to_track_quat('-Z', 'Y').to_euler()

# ------------------------------------------------------------------ CLINIC  (room x 4..10, y -3..3, z 0..2.8)
M_wall = pbr("Plaster", "plastered_wall_02", scale=1.0, tint=(0.88, 0.92, 0.9))
M_floor = pbr("Clinic_floor", "brushed_concrete", scale=1.0, tint=(0.75, 0.78, 0.8), rough_mul=0.6)
M_steel = pbr("Steel", "metal_plate", scale=2.0, rough_mul=0.5)
for nd in M_steel.node_tree.nodes:
    if nd.type == 'BSDF_PRINCIPLED': nd.inputs["Metallic"].default_value = 1.0
WX0, WX1, WY, WZ = 4.0, 10.0, 3.0, 2.8
t = 0.12
fl = box("Clinic_floor", C_C, (WX1 - WX0 + 0.3, 2 * WY + 0.3, 0.1), ((WX0 + WX1) / 2, 0, -0.05), M_floor); cube_uv(fl)
ce = box("Clinic_ceiling", C_C, (WX1 - WX0 + 0.3, 2 * WY + 0.3, 0.1), ((WX0 + WX1) / 2, 0, WZ + 0.05), M_wall); cube_uv(ce)
for nm, sz, lc in (("Wall_S", (WX1 - WX0, t, WZ), ((WX0 + WX1) / 2, -WY - t / 2, WZ / 2)),
                   ("Wall_N", (WX1 - WX0, t, WZ), ((WX0 + WX1) / 2, WY + t / 2, WZ / 2))):
    o = box(nm, C_C, sz, lc, M_wall); cube_uv(o)
# west wall with window (y -0.8..0.8, z 0.95..2.25)
for nm, sz, lc in (("WallW_a", (t, WY - 0.8, WZ), (WX0 - t / 2, -(0.8 + WY) / 2, WZ / 2)),
                   ("WallW_b", (t, WY - 0.8, WZ), (WX0 - t / 2, (0.8 + WY) / 2, WZ / 2)),
                   ("WallW_c", (t, 1.6, 0.95), (WX0 - t / 2, 0, 0.475)),
                   ("WallW_d", (t, 1.6, WZ - 2.25), (WX0 - t / 2, 0, (WZ + 2.25) / 2))):
    o = box(nm, C_C, sz, lc, M_wall); cube_uv(o)
for nm, sz, lc in (("Win_sill", (0.24, 1.7, 0.05), (WX0 - t / 2, 0, 0.95)), ("Win_head", (0.2, 1.7, 0.06), (WX0 - t / 2, 0, 2.25)),
                   ("Win_jambL", (0.2, 0.06, 1.3), (WX0 - t / 2, -0.82, 1.6)), ("Win_jambR", (0.2, 0.06, 1.3), (WX0 - t / 2, 0.82, 1.6))):
    o = box(nm, C_C, sz, lc, M_wood, bevel=0.004); cube_uv(o)
# east wall with the portal patch behind the monitor (patch y 0.95..1.55, z 0.95..1.35)
PY0, PY1, PZ0, PZ1 = 1.0, 1.5, 0.93, 1.17
for nm, sz, lc in (("WallE_a", (t, PY0 + WY, WZ), (WX1 + t / 2, (PY0 - WY) / 2, WZ / 2)),
                   ("WallE_b", (t, WY - PY1, WZ), (WX1 + t / 2, (PY1 + WY) / 2, WZ / 2)),
                   ("WallE_c", (t, PY1 - PY0, PZ0), (WX1 + t / 2, (PY0 + PY1) / 2, PZ0 / 2)),
                   ("WallE_d", (t, PY1 - PY0, WZ - PZ1), (WX1 + t / 2, (PY0 + PY1) / 2, (WZ + PZ1) / 2)),
                   ("Wall_patch", (t, PY1 - PY0, PZ1 - PZ0), (WX1 + t / 2, (PY0 + PY1) / 2, (PZ0 + PZ1) / 2))):
    o = box(nm, C_C, sz, lc, M_wall); cube_uv(o)
# ceiling light panels (real emitters with housings)
M_panel = bpy.data.materials.new("Light_panel"); M_panel.use_nodes = True
pb_ = M_panel.node_tree.nodes["Principled BSDF"]; pb_.inputs["Emission Color"].default_value = (1, 0.97, 0.92, 1); pb_.inputs["Emission Strength"].default_value = 6
for k, (x, y) in enumerate([(6.0, -1.2), (6.0, 1.2), (8.4, -1.2), (8.4, 1.2)]):
    box("Lamp_housing_%d" % k, C_C, (1.22, 0.32, 0.05), (x, y, WZ - 0.03), M_steel, bevel=0.005)
    box("Lamp_diffuser_%d" % k, C_C, (1.18, 0.28, 0.01), (x, y, WZ - 0.06), M_panel)
    L_ = bpy.data.objects.new("Lamp_%d" % k, bpy.data.lights.new("Lamp_%d" % k, 'AREA')); C_C.objects.link(L_)
    L_.data.shape = 'RECTANGLE'; L_.data.size = 1.15; L_.data.size_y = 0.26; L_.data.energy = 140; L_.location = (x, y, WZ - 0.08)
    L_.data.color = (1, 0.96, 0.9)
# key light over the exam table (exam lamp)
key = bpy.data.objects.new("Exam_key", bpy.data.lights.new("Exam_key", 'AREA')); C_C.objects.link(key)
key.data.size = 0.5; key.data.energy = 90; key.location = (6.6, -0.6, 2.2); key.rotation_euler = (R_(20), R_(-10), 0)
rim = bpy.data.objects.new("Exam_rim", bpy.data.lights.new("Exam_rim", 'AREA')); C_C.objects.link(rim)
rim.data.size = 0.4; rim.data.energy = 60; rim.data.color = (0.8, 0.9, 1.0); rim.location = (7.6, 1.2, 1.8)
rim.rotation_euler = (Vector((7.0, 0, 0.95)) - rim.location).to_track_quat('-Z', 'Y').to_euler()

# exam table (steel top on trolley model), towel
trol_top = 0.86
for k, (dx, dy) in enumerate([(-0.58, -0.28), (0.58, -0.28), (-0.58, 0.28), (0.58, 0.28)]):
    box("Table_leg_%d" % k, C_C, (0.035, 0.035, trol_top), (7.0 + dx, dy, trol_top / 2), M_steel, bevel=0.004)
shelf = box("Table_shelf", C_C, (1.18, 0.58, 0.02), (7.0, 0, 0.22), M_steel, bevel=0.003); cube_uv(shelf, 2)
top = box("Exam_top", C_C, (1.25, 0.66, 0.025), (7.0, 0, trol_top + 0.0125), M_steel, bevel=0.004); cube_uv(top, 2)
TABLE_Z = trol_top + 0.025
M_towel = pbr("Towel", "fabric_pattern_07", scale=3.0)
_b = M_towel.node_tree.nodes["Principled BSDF"]
for l in list(_b.inputs["Base Color"].links): M_towel.node_tree.links.remove(l)
_n = M_towel.node_tree.nodes.new("ShaderNodeTexNoise"); _n.inputs["Scale"].default_value = 400
_r = M_towel.node_tree.nodes.new("ShaderNodeValToRGB"); M_towel.node_tree.links.new(_n.outputs[0], _r.inputs[0])
_r.color_ramp.elements[0].color = (0.12, 0.32, 0.38, 1); _r.color_ramp.elements[1].color = (0.2, 0.45, 0.5, 1)
M_towel.node_tree.links.new(_r.outputs[0], _b.inputs["Base Color"]); _b.inputs["Sheen Weight"].default_value = 1.0
bpy.ops.mesh.primitive_grid_add(x_subdivisions=40, y_subdivisions=30, size=1, location=(7.0, 0.05, TABLE_Z + 0.004))
tw = bpy.context.active_object; tw.name = "Towel"; tw.scale = (0.55, 0.42, 1); link(tw, C_C); tw.data.materials.append(M_towel)
txw = bpy.data.textures.new("towel", 'CLOUDS'); txw.noise_scale = 0.08
dw = tw.modifiers.new("d", 'DISPLACE'); dw.texture = txw; dw.strength = 0.012; dw.mid_level = 0.0
so = tw.modifiers.new("s", 'SOLIDIFY'); so.thickness = 0.004
tw.data.polygons.foreach_set("use_smooth", [True] * len(tw.data.polygons))
# desk + monitor (portal) on the east wall, chair; printer on side bench; instrument tray
cab = imp("cabinet", C_C, size=1.9, axis=2, loc=(5.0, 2.72, 0), rotz=R_(180))
cab2 = imp("cabinet2", C_C, size=1.9, axis=2, loc=(6.2, 2.75, 0), rotz=R_(180))
print("CABINETS", cab.dimensions[:], cab2.dimensions[:])
desk = imp("desk", C_C, size=1.6, loc=(9.62, 1.25, 0), rotz=R_(90))
V = np.array([v.co[:] for v in desk.data.vertices]); DESK_Z = V[:, 2].max()
mon = imp("monitor", C_C, size=0.62, loc=(9.78, (PY0 + PY1) / 2, DESK_Z), rotz=0.0)
# orient: screen (material "Display") must face -x (into the room)
di = [i for i, m in enumerate(mon.data.materials) if m.name.startswith("Display")][0]
nrm = Vector((0, 0, 0)); ctr_s = Vector((0, 0, 0)); ns = 0
for p_ in mon.data.polygons:
    if p_.material_index == di: nrm += p_.normal * p_.area; ctr_s += p_.center; ns += 1
ctr_all = sum((v.co for v in mon.data.vertices), Vector()) / len(mon.data.vertices)
ctr_s /= ns; front = (ctr_s - ctr_all); front.z = 0; front.normalize()   # screen sits on the front side
ang = math.atan2(front.y, front.x); mon.data.transform(Matrix.Rotation(math.pi - ang, 4, 'Z'))
# split off back shell (faces pointing at the wall) -> hidden from camera during the portal push
bm = bmesh.new(); bm.from_mesh(mon.data)
back = bmesh.new()
mon_back = bpy.data.objects.new("Monitor_back", bpy.data.meshes.new("Monitor_back")); C_C.objects.link(mon_back)
mon_back.location = mon.location
for m in mon.data.materials: mon_back.data.materials.append(m)
bm2 = bm.copy()
dz = [f.calc_center_median() for f in bm.faces if f.material_index == di]
scr_x = min(c.x for c in dz); scr_z0 = min(c.z for c in dz) - 0.03
def is_back(f):
    c = f.calc_center_median()
    return f.normal.x > 0.35 or (c.x > scr_x + 0.006 and c.z > scr_z0)
bmesh.ops.delete(bm, geom=[f for f in bm.faces if is_back(f)], context='FACES')
bmesh.ops.delete(bm2, geom=[f for f in bm2.faces if not is_back(f)], context='FACES')
bm.to_mesh(mon.data); bm2.to_mesh(mon_back.data); bm.free(); bm2.free()
mon.name = "Monitor"
M_screen = bpy.data.materials.new("Screen_glass"); M_screen.use_nodes = True; ntS = M_screen.node_tree
for n in list(ntS.nodes):
    if n.type == 'BSDF_PRINCIPLED': ntS.nodes.remove(n)
tr = ntS.nodes.new("ShaderNodeBsdfTransparent"); gl = ntS.nodes.new("ShaderNodeBsdfGlossy"); gl.inputs["Roughness"].default_value = 0.05
fr = ntS.nodes.new("ShaderNodeFresnel"); fr.inputs[0].default_value = 1.5
mxs = ntS.nodes.new("ShaderNodeMixShader"); ntS.links.new(fr.outputs[0], mxs.inputs[0]); ntS.links.new(tr.outputs[0], mxs.inputs[1]); ntS.links.new(gl.outputs[0], mxs.inputs[2])
ntS.links.new(mxs.outputs[0], ntS.nodes["Material Output"].inputs[0])
mon.data.materials[di] = M_screen
V = np.array([v.co[:] for v in mon.data.vertices])
print("MONITOR", mon.location[:], V.min(0) + np.array(mon.location), V.max(0) + np.array(mon.location))
sc["SCREEN"] = list(Vector(mon.location) + Vector(((V.min(0)[0]), (V.min(0)[1] + V.max(0)[1]) / 2, (V.min(0)[2] + V.max(0)[2]) / 2)))
chair = imp("chair", C_C, size=1.05, axis=2, loc=(8.6, 2.45, 0), rotz=R_(-120))
bench = box("Side_bench", C_C, (0.65, 1.5, 0.05), (9.62, -1.6, 0.88), M_wood, bevel=0.004); cube_uv(bench)
for k, (dy) in enumerate((-0.68, 0.68)):
    o = box("Bench_leg_%d" % k, C_C, (0.6, 0.04, 0.86), (9.62, -1.6 + dy, 0.43), M_steel, bevel=0.003)
# ---- clinic dressing (director C note): shelves with supplies, exam lamp, framed photos (no text), plants
def wall_face(o, want):
    """rotate o about z so its thinnest horizontal side faces `want` (a unit xy vector pointing away from the wall)"""
    V = np.array([v.co[:] for v in o.data.vertices]); d = V.max(0) - V.min(0)
    if d[0] < d[1]: o.data.transform(Matrix.Rotation(R_(90), 4, 'Z'))
    o.rotation_euler = (0, 0, math.atan2(want[1], want[0]) - math.pi / 2)
for k, x in enumerate((7.3, 8.45)):
    sh = imp("shelf", C_C, size=0.95, loc=(x, 2.83, 1.05)); wall_face(sh, (0, -1)); sh.name = "Shelf_%d" % k
    V = np.array([v.co[:] for v in sh.data.vertices]); shz = V[:, 2].max() - V[:, 2].min()
    for j in range(3):
        b_ = imp("bottles", C_C, size=0.24, loc=(x - 0.3 + 0.3 * j, 2.8, 1.05 + 0.005 + (shz * 0.5 if j == 1 else 0.0)))
        b_.rotation_euler = (0, 0, random.uniform(0, 6.28)); b_.name = "Supplies_%d_%d" % (k, j)
for j, (x, y) in enumerate([(9.75, -1.0), (9.5, -2.2)]):
    b_ = imp("bottles", C_C, size=0.22, loc=(x, y, 0.905)); b_.name = "Supplies_bench_%d" % j
lmp = imp("lamp", C_C, size=0.62, axis=2, loc=(7.58, -0.27, 0.885), rotz=R_(150)); lmp.name = "Exam_lamp"
pp = imp("potplant", C_C, size=1.25, axis=2, loc=(9.55, 2.55, 0)); pp.name = "Clinic_plant"
po = imp("pothos", C_C, size=0.45, axis=2, loc=(9.72, 0.45, DESK_Z if 'DESK_Z' in dir() else 0.75)); po.name = "Desk_plant"
M_photo = bpy.data.materials.new("Photo_print"); M_photo.use_nodes = True
pt = M_photo.node_tree; pb2 = pt.nodes["Principled BSDF"]; it = pt.nodes.new("ShaderNodeTexImage")
it.image = bpy.data.images.load(os.path.join(PH, "hdri", "forest_slope_1k.hdr"), check_existing=True)
pt.links.new(it.outputs[0], pb2.inputs["Base Color"]); pb2.inputs["Roughness"].default_value = 0.35
for k, (loc, face) in enumerate([((9.93, -0.75, 1.55), (-1, 0)), ((6.6, 2.93, 1.6), (0, -1)), ((5.3, -2.93, 1.55), (0, 1))]):
    fr_ = imp("frame", C_C, size=0.62, loc=loc, base=False); wall_face(fr_, face); fr_.name = "Photo_frame_%d" % k
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, -30)); ph_ = bpy.context.active_object; link(ph_, C_C); ph_.name = "Photo_%d" % k
    ph_.data.materials.append(M_photo); ph_.scale = (0.46, 0.34, 1)
    ph_.rotation_euler = (R_(90), 0, math.atan2(face[1], face[0]) - math.pi / 2)
    ph_.location = Vector(loc) + Vector((face[0], face[1], 0)) * 0.012
    for l_ in ph_.data.uv_layers.active.data: l_.uv = (0.15 + l_.uv[0] * 0.35 + 0.2 * k, 0.35 + l_.uv[1] * 0.3)

# X-ray lightbox (beak X-ray rendered from the real bird meshes by 01b_xray.py) on the east wall above the print bench
lbx = box("Xray_lightbox", C_C, (0.06, 0.72, 0.56), (9.96, -2.05, 1.62), M_steel, bevel=0.008)
M_xr = bpy.data.materials.new("Xray_film"); M_xr.use_nodes = True; xt = M_xr.node_tree; xb = xt.nodes["Principled BSDF"]
xi = xt.nodes.new("ShaderNodeTexImage"); xi.image = bpy.data.images.load(os.path.join(A, "xray_beak.png"))
xt.links.new(xi.outputs[0], xb.inputs["Base Color"]); xt.links.new(xi.outputs[0], xb.inputs["Emission Color"]); xb.inputs["Emission Strength"].default_value = 3.0
bpy.ops.mesh.primitive_plane_add(size=1, location=(9.925, -2.05, 1.62)); xp = bpy.context.active_object; link(xp, C_C); xp.name = "Xray_film"
xp.scale = (0.64, 0.48, 1); xp.rotation_euler = (R_(90), 0, R_(-90)); xp.data.materials.append(M_xr)

printer = imp("printer", C_C, size=0.55, loc=(9.62, -1.65, 0.905), rotz=R_(-90), join=True)
syr = imp("syringe", C_P, size=0.12, base=False); syr.name = "Glue_syringe"
twz = imp("tweezers", C_P, size=0.12, base=False); twz.name = "Tweezers"
for i in range(len(twz.data.materials)): twz.data.materials[i] = M_steel
if not twz.data.materials: twz.data.materials.append(M_steel)
# pin (stainless, 2.2 cm) and scanner (handheld 3D scanner, plastic + glass + laser line)
bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.0007, depth=0.022, location=(0, 0, -40)); pin = bpy.context.active_object; pin.name = "Pin"; link(pin, C_P)
pin.data.materials.append(M_steel)
M_plast = bpy.data.materials.new("Scanner_plastic"); M_plast.use_nodes = True
pp = M_plast.node_tree.nodes["Principled BSDF"]; pp.inputs["Base Color"].default_value = (0.08, 0.085, 0.09, 1); pp.inputs["Roughness"].default_value = 0.42
pn = M_plast.node_tree.nodes.new("ShaderNodeTexNoise"); pn.inputs["Scale"].default_value = 3000
pbm = M_plast.node_tree.nodes.new("ShaderNodeBump"); pbm.inputs["Strength"].default_value = 0.05
M_plast.node_tree.links.new(pn.outputs["Fac"], pbm.inputs["Height"]); M_plast.node_tree.links.new(pbm.outputs["Normal"], pp.inputs["Normal"])
M_orng = bpy.data.materials.new("Scanner_trim"); M_orng.use_nodes = True
M_orng.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.7, 0.32, 0.05, 1)
M_orng.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.35
M_glass = bpy.data.materials.new("Lens_glass"); M_glass.use_nodes = True
gg = M_glass.node_tree.nodes["Principled BSDF"]; gg.inputs["Base Color"].default_value = (0.02, 0.03, 0.05, 1); gg.inputs["Roughness"].default_value = 0.02
gg.inputs["Coat Weight"].default_value = 1
scanner = box("Scanner", C_P, (0.065, 0.045, 0.17), (0, 0, -40), M_plast, bevel=0.012)
grip = box("Scanner_grip", C_P, (0.04, 0.036, 0.11), (0, 0.0, -40), M_plast, bevel=0.012)
trim = box("Scanner_trim", C_P, (0.068, 0.048, 0.012), (0, 0, -40), M_orng, bevel=0.003)
lens = box("Scanner_lens", C_P, (0.05, 0.003, 0.11), (0, 0, -40), M_glass, bevel=0.002)
for o, off in ((grip, (0, -0.02, -0.11)), (trim, (0, 0, 0.06)), (lens, (0, 0.0235, 0.0))):
    o.parent = scanner; o.location = off
M_laser = bpy.data.materials.new("Laser"); M_laser.use_nodes = True
lz = M_laser.node_tree.nodes["Principled BSDF"]; lz.inputs["Base Color"].default_value = (0, 0, 0, 1)
lz.inputs["Emission Color"].default_value = (1.0, 0.05, 0.02, 1); lz.inputs["Emission Strength"].default_value = 40
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, -40)); laser = bpy.context.active_object; laser.name = "Laser_line"; link(laser, C_P)
laser.scale = (0.0009, 0.06, 1); laser.data.materials.append(M_laser)
laser.visible_shadow = False

# ------------------------------------------------------------------ VOID behind the east wall (x 10.2..18)
M_void = bpy.data.materials.new("Void_gradient"); M_void.use_nodes = True; nt = M_void.node_tree
for n in list(nt.nodes):
    if n.type == 'BSDF_PRINCIPLED': nt.nodes.remove(n)
tc = nt.nodes.new("ShaderNodeTexCoord"); sp = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Generated"], sp.inputs[0])
cr = nt.nodes.new("ShaderNodeValToRGB"); nt.links.new(sp.outputs["Z"], cr.inputs[0])
cr.color_ramp.elements[0].color = (0.004, 0.012, 0.045, 1); cr.color_ramp.elements[1].color = (0.01, 0.16, 0.2, 1)
cr.color_ramp.elements[0].position = 0.25; cr.color_ramp.elements[1].position = 0.75
nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3
mxv = nt.nodes.new("ShaderNodeMix"); mxv.data_type = 'RGBA'; mxv.blend_type = 'OVERLAY'; mxv.inputs[0].default_value = 0.15
nt.links.new(cr.outputs[0], mxv.inputs[6]); nt.links.new(nz.outputs["Color"], mxv.inputs[7])
emv = nt.nodes.new("ShaderNodeEmission"); nt.links.new(mxv.outputs[2], emv.inputs[0]); emv.inputs[1].default_value = 1.0
nt.links.new(emv.outputs[0], nt.nodes["Material Output"].inputs[0])
me = bpy.data.meshes.new("Void_box"); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
bmesh.ops.reverse_faces(bm, faces=bm.faces[:]); bm.to_mesh(me); bm.free()
vb = bpy.data.objects.new("Void_box", me); C_V.objects.link(vb); me.materials.append(M_void)
vb.scale = (8, 9, 6); vb.location = (10.18 + 4, 1.2, 1.2)
bpy.context.view_layer.objects.active = vb; vb.select_set(True); bpy.ops.object.transform_apply(scale=True); vb.select_set(False)
vb.visible_shadow = False
# split the wall-side face (x min) into Void_front: camera-visible only while the camera is inside the void
bm = bmesh.new(); bm.from_mesh(vb.data); bm2 = bm.copy()
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.calc_center_median().x < 10.5], context='FACES')
bmesh.ops.delete(bm2, geom=[f for f in bm2.faces if f.calc_center_median().x >= 10.5], context='FACES')
bm.to_mesh(vb.data); vf = bpy.data.objects.new("Void_front", bpy.data.meshes.new("Void_front")); C_V.objects.link(vf)
bm2.to_mesh(vf.data); bm.free(); bm2.free(); vf.data.materials.append(M_void); vf.visible_shadow = False
for k, (lc, en, col) in enumerate([((12.0, -0.6, 3.0), 160, (0.85, 0.95, 1)), ((15.5, 3.2, 2.2), 120, (0.5, 0.8, 1.0)), ((12.5, 2.5, -0.5), 60, (0.3, 0.9, 0.9))]):
    l = bpy.data.objects.new("Void_light_%d" % k, bpy.data.lights.new("Void_light_%d" % k, 'AREA')); C_V.objects.link(l)
    l.data.size = 2.0; l.data.energy = en; l.data.color = col; l.location = lc
    l.rotation_euler = (Vector((13.5, 1.2, 1.2)) - Vector(lc)).to_track_quat('-Z', 'Y').to_euler()

# ------------------------------------------------------------------ bring in bird + people
with bpy.data.libraries.load(os.path.join(WK, "bird.blend"), link=False) as (src, dst):
    dst.objects = [n for n in src.objects]
for o in dst.objects:
    if o: sc.collection.objects.link(o)
with bpy.data.libraries.load(os.path.join(WK, "vets.blend"), link=False) as (src, dst):
    dst.objects = [n for n in src.objects]
for o in dst.objects:
    if o: C_C.objects.link(o)
sc["TABLE_Z"] = TABLE_Z; sc["DESK_Z"] = DESK_Z
bpy.ops.wm.save_as_mainfile(filepath=out)
print("SETS_DONE", out)
