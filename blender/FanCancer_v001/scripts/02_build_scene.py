"""FanCancer sets. Exec'd by 00_build.py inside humans.blend.
RINK at origin (glass line y=0, her side y>0, bench + ice y<0), TUNNEL x -15..-25 -> CLINIC x -25..-31,
SKIN cutaway at x=200, CITY at x=-300, HOME at (-300, 200)."""
import os, math, random
import bpy, bmesh
from mathutils import Vector, Matrix

A = os.environ["FC_ASSETS"]; PH = A + "/ph"; OB = A + "/objv"
sc = bpy.context.scene
FPS, END = 60, 2640
random.seed(30)

sc.render.fps, sc.render.fps_base = FPS, 1.0
sc.frame_start, sc.frame_end = 1, END
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, 100
sc.render.engine = 'CYCLES'
c = sc.cycles
c.device = 'CPU'; c.samples = 48; c.use_adaptive_sampling = True; c.adaptive_threshold = 0.05
c.use_denoising = True; c.denoiser = 'OPENIMAGEDENOISE'
c.max_bounces = 8; c.diffuse_bounces = 3; c.glossy_bounces = 3; c.transmission_bounces = 8
c.caustics_reflective = c.caustics_refractive = False
sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = 0.5
sc.render.use_persistent_data = True
vs = sc.view_settings; vs.view_transform = 'AgX'; vs.look = 'AgX - Medium High Contrast'
im = sc.render.image_settings; im.file_format = 'PNG'; im.color_mode = 'RGB'
sc.render.filepath = "//render/FanCancer_"

def coll(name):
    cl = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if cl.name not in sc.collection.children: sc.collection.children.link(cl)
    return cl
C_RINK, C_SKIN, C_CLIN, C_CITY, C_HOME, C_FX = (coll(n) for n in ("RINK", "SKIN", "CLINIC", "CITY", "HOME", "FX"))

def link(o, cl):
    for u in list(o.users_collection): u.objects.unlink(o)
    cl.objects.link(o); return o

def img(p, nc=False):
    i = bpy.data.images.load(p, check_existing=True)
    if nc: i.colorspace_settings.name = 'Non-Color'
    return i

def tex(base, k):
    d = f"{PH}/{base}/textures/"
    for f in os.listdir(d):
        if f.startswith(f"{base}_{k}_"): return d + f
    return None

def pbr(name, base, scale=1.0, tint=None, rough_mul=1.0, bump=1.0, coords='UV', val=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links; p = n["Principled BSDF"]
    tc = n.new('ShaderNodeTexCoord'); mp = n.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1 / scale,) * 3
    l.new(tc.outputs[coords], mp.inputs['Vector'])
    def ti(path, nc):
        t = n.new('ShaderNodeTexImage'); t.image = img(path, nc); l.new(mp.outputs['Vector'], t.inputs['Vector'])
        if coords == 'Object': t.projection = 'BOX'; t.projection_blend = 0.2
        return t
    d = ti(tex(base, "diff"), False)
    col = d.outputs['Color']
    if tint or val != 1.0:
        mx = n.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
        t_ = tint or (val, val, val); mx.inputs['B'].default_value = (*t_, 1); l.new(col, mx.inputs['A']); col = mx.outputs['Result']
    l.new(col, p.inputs['Base Color'])
    rp = tex(base, "rough")
    if rp:
        r = ti(rp, True); mm = n.new('ShaderNodeMath'); mm.operation = 'MULTIPLY'; mm.inputs[1].default_value = rough_mul; mm.use_clamp = True
        l.new(r.outputs['Color'], mm.inputs[0]); l.new(mm.outputs[0], p.inputs['Roughness'])
    npth = tex(base, "nor_gl")
    if npth:
        t = ti(npth, True); nm = n.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = bump
        l.new(t.outputs['Color'], nm.inputs['Color']); l.new(nm.outputs['Normal'], p.inputs['Normal'])
    return m

def mat(name, rgb, rough=0.5, metal=0.0, emit=None, estr=0.0, noise=0.0, nscale=50.0, sss=0.0, trans=0.0, alpha=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links; p = n["Principled BSDF"]
    p.inputs['Base Color'].default_value = (*rgb, 1); p.inputs['Roughness'].default_value = rough; p.inputs['Metallic'].default_value = metal
    if trans: p.inputs['Transmission Weight'].default_value = trans
    if sss: p.inputs['Subsurface Weight'].default_value = sss; p.inputs['Subsurface Radius'].default_value = (1.0, 0.35, 0.2)
    if emit: p.inputs['Emission Color'].default_value = (*emit, 1); p.inputs['Emission Strength'].default_value = estr
    if alpha < 1: p.inputs['Alpha'].default_value = alpha
    if noise:
        nt = n.new('ShaderNodeTexNoise'); nt.inputs['Scale'].default_value = nscale; nt.inputs['Detail'].default_value = 12
        bp = n.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = noise
        l.new(nt.outputs['Fac'], bp.inputs['Height']); l.new(bp.outputs['Normal'], p.inputs['Normal'])
        cr = n.new('ShaderNodeMix'); cr.data_type = 'RGBA'; cr.blend_type = 'MULTIPLY'; cr.inputs['Factor'].default_value = 0.35
        cr.inputs['A'].default_value = (*rgb, 1); l.new(nt.outputs['Color'], cr.inputs['B']); l.new(cr.outputs['Result'], p.inputs['Base Color'])
    return m

def box(name, size, loc, m, cl, bevel=0.01, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        b = o.modifiers.new("bev", 'BEVEL'); b.width = bevel; b.segments = 2
    bpy.ops.mesh.uv_texture_add() if not o.data.uv_layers else None
    o.data.materials.append(m); return link(o, cl)

def uvbox(o, s=1.0):
    bpy.context.view_layer.objects.active = o
    for x in bpy.context.selected_objects: x.select_set(False)
    o.select_set(True); bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.cube_project(cube_size=s); bpy.ops.object.mode_set(mode='OBJECT')

def plane(name, sx, sy, loc, m, cl, rot=(0, 0, 0), cuts=0):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object; o.name = name; o.scale = (sx, sy, 1); bpy.ops.object.transform_apply(scale=True)
    if cuts:
        bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.subdivide(number_cuts=cuts); bpy.ops.object.mode_set(mode='OBJECT')
    o.data.materials.append(m); return link(o, cl)

def glb(path, name, cl, height=None, length=None, loc=(0, 0, 0), rot_z=0.0, keep_parts=False):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]; ms = [o for o in new if o.type == 'MESH']
    for o in ms:
        mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
    for o in new:
        if o.type != 'MESH': bpy.data.objects.remove(o, do_unlink=True)
    for o in bpy.context.selected_objects: o.select_set(False)
    for o in ms: o.select_set(True)
    bpy.context.view_layer.objects.active = ms[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    if len(ms) > 1: bpy.ops.object.join()
    o = bpy.context.object; o.name = name
    bb = [Vector(v) for v in o.bound_box]; mn = Vector([min(v[i] for v in bb) for i in range(3)]); mx = Vector([max(v[i] for v in bb) for i in range(3)])
    s = 1.0
    if height: s = height / (mx.z - mn.z)
    if length: s = length / max(mx.x - mn.x, mx.y - mn.y)
    ctr = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))
    o.data.transform(Matrix.Scale(s, 4) @ Matrix.Translation(-ctr))
    o.location = loc; o.rotation_euler.z = rot_z
    return link(o, cl)

def ph_blend(asset, cl, loc, rot_z=0.0, scale=1.0):
    p = f"{PH}/{asset}/{asset}_1k.blend"
    with bpy.data.libraries.load(p) as (src, dst):
        dst.objects = src.objects
    alls = [o for o in dst.objects if o]; obs = [o for o in alls if o.type == 'MESH']
    root = bpy.data.objects.new(asset + "_root", None); cl.objects.link(root); root.location = loc; root.rotation_euler.z = rot_z
    root.scale = (scale,) * 3; root.hide_render = True
    for o in alls:
        cl.objects.link(o)
        if o.parent is None: o.parent = root
    return root, obs

# ================================================================== world: per-set HDRI switching is done by keyed mix in 03
w = bpy.data.worlds.new("FC_World"); sc.world = w; w.use_nodes = True
wn, wl = w.node_tree.nodes, w.node_tree.links
bg = wn["Background"]; out = wn["World Output"]
envs = {}
for k in ("circus_arena", "hospital_room", "lythwood_lounge", "dresden_station_night"):
    e = wn.new('ShaderNodeTexEnvironment'); e.image = img(f"{PH}/hdri/{k}_1k.hdr"); envs[k] = e
# chain of mixes; fac keyed per set in 03 (world_mix_N)
m1 = wn.new('ShaderNodeMix'); m1.data_type = 'RGBA'; m1.name = "WMIX1"
m2 = wn.new('ShaderNodeMix'); m2.data_type = 'RGBA'; m2.name = "WMIX2"
m3 = wn.new('ShaderNodeMix'); m3.data_type = 'RGBA'; m3.name = "WMIX3"
wl.new(envs["circus_arena"].outputs['Color'], m1.inputs['A']); wl.new(envs["hospital_room"].outputs['Color'], m1.inputs['B'])
wl.new(m1.outputs['Result'], m2.inputs['A']); wl.new(envs["dresden_station_night"].outputs['Color'], m2.inputs['B'])
wl.new(m2.outputs['Result'], m3.inputs['A']); wl.new(envs["lythwood_lounge"].outputs['Color'], m3.inputs['B'])
wl.new(m3.outputs['Result'], bg.inputs['Color']); bg.inputs['Strength'].default_value = 0.5; bg.name = "WBG"

# ================================================================== RINK
M_ice = bpy.data.materials.new("Ice"); M_ice.use_nodes = True
n, l = M_ice.node_tree.nodes, M_ice.node_tree.links; p = n["Principled BSDF"]
tc = n.new('ShaderNodeTexCoord')
scr = n.new('ShaderNodeTexWave'); scr.wave_type = 'BANDS'; scr.inputs['Scale'].default_value = 3.0; scr.inputs['Distortion'].default_value = 25
scr.inputs['Detail'].default_value = 8; scr.inputs['Detail Scale'].default_value = 6
nz = n.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 1.5; nz.inputs['Detail'].default_value = 10
cr = n.new('ShaderNodeValToRGB'); cr.color_ramp.elements[0].color = (0.50, 0.56, 0.62, 1); cr.color_ramp.elements[1].color = (0.80, 0.83, 0.86, 1)
l.new(tc.outputs['Object'], scr.inputs['Vector']); l.new(tc.outputs['Object'], nz.inputs['Vector'])
mx_ = n.new('ShaderNodeMath'); mx_.operation = 'MULTIPLY_ADD'; mx_.inputs[1].default_value = 0.35
l.new(nz.outputs['Fac'], mx_.inputs[0]); l.new(scr.outputs['Fac'], mx_.inputs[2]); l.new(mx_.outputs[0], cr.inputs['Fac'])
# painted lines: blue line at y=-9, red centre line at y=-15 (object coords), plus a faceoff circle
sep = n.new('ShaderNodeSeparateXYZ'); l.new(tc.outputs['Object'], sep.inputs['Vector'])
def band(y0, wdt):
    a = n.new('ShaderNodeMath'); a.operation = 'SUBTRACT'; a.inputs[1].default_value = y0; l.new(sep.outputs['Y'], a.inputs[0])
    b = n.new('ShaderNodeMath'); b.operation = 'ABSOLUTE'; l.new(a.outputs[0], b.inputs[0])
    c_ = n.new('ShaderNodeMath'); c_.operation = 'LESS_THAN'; c_.inputs[1].default_value = wdt; l.new(b.outputs[0], c_.inputs[0]); return c_
blue = band(-9.0, 0.15); red = band(-15.0, 0.15)
m_b = n.new('ShaderNodeMix'); m_b.data_type = 'RGBA'; m_b.inputs['B'].default_value = (0.05, 0.12, 0.45, 1)
l.new(blue.outputs[0], m_b.inputs['Factor']); l.new(cr.outputs['Color'], m_b.inputs['A'])
m_r = n.new('ShaderNodeMix'); m_r.data_type = 'RGBA'; m_r.inputs['B'].default_value = (0.55, 0.04, 0.04, 1)
l.new(red.outputs[0], m_r.inputs['Factor']); l.new(m_b.outputs['Result'], m_r.inputs['A'])
l.new(m_r.outputs['Result'], p.inputs['Base Color'])
rr = n.new('ShaderNodeMapRange'); rr.inputs['To Min'].default_value = 0.03; rr.inputs['To Max'].default_value = 0.22
l.new(scr.outputs['Fac'], rr.inputs['Value']); l.new(rr.outputs['Result'], p.inputs['Roughness'])
bp = n.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.08; l.new(scr.outputs['Fac'], bp.inputs['Height']); l.new(bp.outputs['Normal'], p.inputs['Normal'])
p.inputs['Coat Weight'].default_value = 0.6; p.inputs['Coat Roughness'].default_value = 0.02
ice = plane("Ice", 34, 30, (0, -17.0, 0), M_ice, C_RINK)

M_board = mat("BoardsWhite", (0.82, 0.82, 0.80), 0.35, noise=0.15, nscale=8)
M_cap = mat("BoardCapYellow", (0.75, 0.55, 0.08), 0.4, noise=0.1)
M_kick = mat("KickPlate", (0.03, 0.03, 0.035), 0.6, noise=0.3, nscale=120)
M_glass = mat("Glass", (0.92, 0.96, 0.95), 0.03, trans=1.0)
gp = M_glass.node_tree.nodes["Principled BSDF"]; gn = M_glass.node_tree.nodes
smg = gn.new('ShaderNodeTexNoise'); smg.inputs['Scale'].default_value = 3; smg.inputs['Detail'].default_value = 8
smr = gn.new('ShaderNodeMapRange'); smr.inputs['From Min'].default_value = 0.45; smr.inputs['From Max'].default_value = 0.75
smr.inputs['To Min'].default_value = 0.0; smr.inputs['To Max'].default_value = 0.03
M_glass.node_tree.links.new(smg.outputs['Fac'], smr.inputs['Value']); M_glass.node_tree.links.new(smr.outputs['Result'], gp.inputs['Roughness'])
gp.inputs['IOR'].default_value = 1.49
for nm_, y0, x0, x1 in (("Boards", 0.0, -15, 15), ("BenchFront", -2.1, -15, 15), ("FarBoards", -32.0, -15, 15)):
    L = x1 - x0
    box(nm_, (L, 0.1, 1.07), ((x0 + x1) / 2, y0, 0.535), M_board, C_RINK)
    box(nm_ + "Cap", (L, 0.16, 0.05), ((x0 + x1) / 2, y0, 1.09), M_cap, C_RINK)
    box(nm_ + "Kick", (L, 0.105, 0.25), ((x0 + x1) / 2, y0, 0.125), M_kick, C_RINK, bevel=0.003)
for i in range(-7, 8):  # glass panels along the glass line, with stanchion posts
    g = box(f"GlassPane{i}", (1.98, 0.016, 1.5), (i * 2.0, 0.0, 1.87), M_glass, C_RINK, bevel=0.004)
    box(f"Stanchion{i}", (0.05, 0.06, 1.55), (i * 2.0 + 1.0, 0.0, 1.87), mat("Stanchion", (0.6, 0.62, 0.65), 0.3, 1.0), C_RINK, bevel=0.005)
for i in range(-7, 8):
    box(f"FarGlass{i}", (1.98, 0.016, 1.5), (i * 2.0, -32.0, 1.87), M_glass, C_RINK, bevel=0.004)
M_rub = pbr("RubberFloor", "rubber_tiles", 1.5, tint=(0.35, 0.35, 0.38))
plane("BenchFloor", 30, 2.0, (0, -1.05, 0.005), M_rub, C_RINK)
plane("FanFloor", 30, 1.6, (0, 0.85, 0.0), M_rub, C_RINK)
M_wood = mat("BenchWood", (0.35, 0.22, 0.12), 0.5, noise=0.3, nscale=30)
box("BenchSeat", (10, 0.42, 0.05), (0, -1.55, 0.45), M_wood, C_RINK)
for i in range(-4, 5):
    box(f"BenchLeg{i}", (0.06, 0.35, 0.45), (i * 1.2, -1.55, 0.225), mat("BenchMetal", (0.2, 0.2, 0.22), 0.4, 1.0), C_RINK, bevel=0.005)
# stands: risers with concrete, seats from Objaverse
M_conc = pbr("Concrete", "concrete_floor_02", 2.0, coords='Object', val=0.8)
seats = glb(OB + "/seats.glb", "SeatsSrc", C_RINK)
bb = [Vector(v) for v in seats.bound_box]; sx = max(v.x for v in bb) - min(v.x for v in bb)
ROWS = []
for k in range(7):
    y = 1.65 + 0.85 * k; z = 0.42 * k + 0.42
    box(f"Riser{k}", (32, 0.86, z), (0, y, z / 2), M_conc, C_RINK, bevel=0.01)
    ROWS.append((y, z))
for side, y0, ry in ((1, 0, 0.0), (-1, -32.0, math.pi)):
    for k in range(7):
        y = y0 + side * (1.65 + 0.85 * k); z = 0.42 * k + 0.42
        if side < 0: box(f"FarRiser{k}", (32, 0.86, z), (0, y, z / 2), M_conc, C_RINK, bevel=0.01)
# seats: the source model is a row; scale it to a 0.55 m seat pitch row and instance per row
sm = seats.dimensions
seats.data.transform(Matrix.Scale(0.9 / sm.z, 4))
sm = seats.dimensions
seats.hide_render = True; seats.hide_viewport = True
for side, y0, ry in ((1, 0, math.pi), (-1, -32.0, 0.0)):
    for k in range(7):
        y = y0 + side * (1.65 + 0.85 * k + 0.12); z = 0.42 * k + 0.42
        xx = -15.0
        while xx < 15.0:
            o = seats.copy(); o.hide_render = o.hide_viewport = False; o.location = (xx + sm.x / 2, y, z); o.rotation_euler.z = ry
            C_RINK.objects.link(o); xx += sm.x
box("BackWall", (40, 0.3, 12), (0, 8.2, 6), M_conc, C_RINK, bevel=0)
box("FarBackWall", (40, 0.3, 12), (0, -40.2, 6), M_conc, C_RINK, bevel=0)
box("EndWallL", (0.3, 60, 12), (16.5, -16, 6), M_conc, C_RINK, bevel=0)
M_dark = mat("CeilingDark", (0.03, 0.03, 0.035), 0.8, noise=0.2, nscale=4)
box("Ceiling", (40, 60, 0.3), (0, -16, 13), M_dark, C_RINK, bevel=0)
# truss + light panels
M_steel = mat("Truss", (0.25, 0.26, 0.28), 0.45, 1.0, noise=0.2, nscale=60)
for i in range(-3, 4):
    box(f"Truss{i}", (0.25, 58, 0.5), (i * 5.0, -16, 11.5), M_steel, C_RINK, bevel=0.01)
M_lamp = mat("ArenaLamp", (1, 1, 1), 0.3, emit=(1.0, 0.97, 0.92), estr=60)
for i in range(-3, 4):
    for j in range(6):
        yy = -2 - j * 5.2
        box(f"Lamp{i}_{j}", (0.6, 0.6, 0.1), (i * 5.0, yy, 11.15), M_lamp, C_RINK, bevel=0.01)
        L = bpy.data.lights.new(f"ArenaL{i}_{j}", 'SPOT'); L.energy = 1500; L.spot_size = math.radians(70); L.spot_blend = 0.6
        L.shadow_soft_size = 0.4; L.color = (1.0, 0.97, 0.92)
        lo = bpy.data.objects.new(L.name, L); lo.location = (i * 5.0, yy, 11.0); C_RINK.objects.link(lo)
# fill on the stands so faces read
for x in (-8, 0, 8):
    L = bpy.data.lights.new(f"StandFill{x}", 'AREA'); L.energy = 900; L.size = 4; L.color = (1.0, 0.9, 0.8)
    lo = bpy.data.objects.new(L.name, L); lo.location = (x, -5, 6); lo.rotation_euler = (math.radians(-55), 0, 0); C_RINK.objects.link(lo)
# tunnel
M_cw = pbr("TunnelWall", "concrete_wall_006", 2.0, coords='Object', val=0.85)
box("TunnelWallS", (12, 0.25, 2.8), (-21, -2.2, 1.4), M_cw, C_RINK, bevel=0)
box("TunnelWallN", (12, 0.25, 2.8), (-21, 0.12, 1.4), M_cw, C_RINK, bevel=0)
box("TunnelRoof", (12, 2.6, 0.25), (-21, -1.05, 2.9), M_cw, C_RINK, bevel=0)
plane("TunnelFloor", 12, 2.3, (-21, -1.05, 0.004), M_rub, C_RINK)
box("RinkEndWall", (0.3, 2.0, 1.07), (-15.1, -1.05, 0.535), M_board, C_RINK) if False else None
M_tl = mat("TunnelLight", (1, 1, 1), 0.3, emit=(0.85, 0.95, 1.0), estr=25)
for i in range(5):
    box(f"TunnelTube{i}", (1.2, 0.08, 0.04), (-16.5 - 2.2 * i, -1.05, 2.75), M_tl, C_RINK, bevel=0.01)
    L = bpy.data.lights.new(f"TunnelL{i}", 'AREA'); L.energy = 120; L.size = 1.0; L.color = (0.85, 0.95, 1.0)
    lo = bpy.data.objects.new(L.name, L); lo.location = (-16.5 - 2.2 * i, -1.05, 2.7); lo.rotation_euler = (math.pi, 0, 0); C_RINK.objects.link(lo)
# door into the clinic (opened in 03)
M_door = mat("Door", (0.55, 0.6, 0.62), 0.35, noise=0.1, nscale=20)
door = box("ClinicDoor", (0.05, 1.0, 2.1), (-25.0, -0.55, 1.05), M_door, C_CLIN, bevel=0.01)
door_piv = bpy.data.objects.new("DoorPivot", None); door_piv.location = (-25.0, -1.05, 0); C_CLIN.objects.link(door_piv)
door.parent = door_piv; door.location = (0, 0.5, 1.05)

# ================================================================== CLINIC  (x -25 .. -31, y -3.0 .. 1.5)
M_pl = pbr("ClinicWall", "painted_plaster_wall", 1.5, tint=(0.82, 0.88, 0.88), coords='Object')
M_lam = pbr("ClinicFloor", "laminate_floor_02", 1.5)
plane("ClinicFloorP", 6.2, 4.6, (-28.1, -0.75, 0.003), M_lam, C_CLIN)
box("ClinicWallE_S", (0.2, 1.9, 2.8), (-25.0, -2.1, 1.4), M_pl, C_CLIN, bevel=0)
box("ClinicWallE_N", (0.2, 1.4, 2.8), (-25.0, 0.8, 1.4), M_pl, C_CLIN, bevel=0)
box("ClinicWallE_T", (0.2, 1.1, 0.6), (-25.0, -0.55, 2.5), M_pl, C_CLIN, bevel=0)
box("ClinicWallW", (0.2, 4.8, 2.8), (-31.2, -0.75, 1.4), M_pl, C_CLIN, bevel=0)
box("ClinicWallS", (6.4, 0.2, 2.8), (-28.1, -3.1, 1.4), M_pl, C_CLIN, bevel=0)
box("ClinicWallN", (6.4, 0.2, 2.8), (-28.1, 1.6, 1.4), M_pl, C_CLIN, bevel=0)
box("ClinicCeil", (6.4, 4.8, 0.1), (-28.1, -0.75, 2.85), mat("CeilTile", (0.85, 0.85, 0.83), 0.8, noise=0.2, nscale=40), C_CLIN, bevel=0)
# exam bed: padded top (leather) on a steel frame
M_leath = pbr("BedLeather", "fabric_leather_02", 0.5, tint=(0.25, 0.45, 0.50))
box("ExamBedPad", (1.9, 0.7, 0.12), (-28.6, -2.4, 0.76), M_leath, C_CLIN, bevel=0.04)
box("ExamBedBase", (1.7, 0.6, 0.66), (-28.6, -2.4, 0.35), mat("BedBase", (0.85, 0.86, 0.86), 0.35, noise=0.05), C_CLIN, bevel=0.02)
box("PaperRoll", (1.8, 0.5, 0.004), (-28.6, -2.4, 0.822), mat("Paper", (0.95, 0.95, 0.93), 0.9, noise=0.3, nscale=200), C_CLIN, bevel=0.001)
office = glb(OB + "/office.glb", "OfficeAssets", C_CLIN, height=1.7, loc=(-30.6, 0.4, 0.0), rot_z=math.pi / 2)
cab, _ = ph_blend("drawer_cabinet", C_CLIN, (-26.2, 1.2, 0), rot_z=math.pi)
stl, _ = ph_blend("metal_stool_01", C_CLIN, (-28.3, -1.55, 0))
# patient monitor on a wall arm, with a live trace (texture scrolled in 03)
M_mon = mat("MonitorBody", (0.12, 0.12, 0.13), 0.4, noise=0.1, nscale=60)
box("MonitorBody", (0.06, 0.45, 0.32), (-31.05, -1.6, 1.65), M_mon, C_CLIN, bevel=0.01)
M_trace = bpy.data.materials.new("MonitorTrace"); M_trace.use_nodes = True
n, l = M_trace.node_tree.nodes, M_trace.node_tree.links; p = n["Principled BSDF"]
tc = n.new('ShaderNodeTexCoord'); mp = n.new('ShaderNodeMapping'); mp.name = "TraceMap"; l.new(tc.outputs['UV'], mp.inputs['Vector'])
wv = n.new('ShaderNodeTexWave'); wv.wave_profile = 'SAW'; wv.inputs['Scale'].default_value = 3; wv.bands_direction = 'X'
l.new(mp.outputs['Vector'], wv.inputs['Vector'])
sp = n.new('ShaderNodeSeparateXYZ'); l.new(tc.outputs['UV'], sp.inputs['Vector'])
spike = n.new('ShaderNodeMath'); spike.operation = 'POWER'; spike.inputs[1].default_value = 14; l.new(wv.outputs['Fac'], spike.inputs[0])
yv = n.new('ShaderNodeMath'); yv.operation = 'MULTIPLY_ADD'; yv.inputs[1].default_value = 0.5; yv.inputs[2].default_value = 0.35
l.new(spike.outputs[0], yv.inputs[0])
df = n.new('ShaderNodeMath'); df.operation = 'SUBTRACT'; l.new(sp.outputs['Y'], df.inputs[0]); l.new(yv.outputs[0], df.inputs[1])
ab = n.new('ShaderNodeMath'); ab.operation = 'ABSOLUTE'; l.new(df.outputs[0], ab.inputs[0])
ln = n.new('ShaderNodeMath'); ln.operation = 'LESS_THAN'; ln.inputs[1].default_value = 0.02; l.new(ab.outputs[0], ln.inputs[0])
em = n.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (0.2, 1.0, 0.4, 1)
ms_ = n.new('ShaderNodeMath'); ms_.operation = 'MULTIPLY_ADD'; ms_.inputs[1].default_value = 12; ms_.inputs[2].default_value = 0.15
l.new(ln.outputs[0], ms_.inputs[0]); l.new(ms_.outputs[0], em.inputs['Strength'])
l.new(em.outputs['Emission'], n["Material Output"].inputs['Surface'])
plane("MonitorScreen", 0.38, 0.26, (-31.015, -1.6, 1.65), M_trace, C_CLIN, rot=(math.pi / 2, 0, -math.pi / 2))
L = bpy.data.lights.new("ClinicKey", 'AREA'); L.energy = 220; L.size = 1.6; L.color = (1.0, 0.97, 0.94)
lo = bpy.data.objects.new("ClinicKey", L); lo.location = (-28.4, -1.8, 2.75); lo.rotation_euler = (0, 0, 0); C_CLIN.objects.link(lo)
L = bpy.data.lights.new("ClinicFill", 'AREA'); L.energy = 90; L.size = 2.0; L.color = (0.85, 0.92, 1.0)
lo = bpy.data.objects.new("ClinicFill", L); lo.location = (-26.0, 0.5, 2.0); lo.rotation_euler = (math.radians(60), 0, math.radians(120)); C_CLIN.objects.link(lo)
for i in range(2):
    box(f"ClinicPanel{i}", (1.2, 0.6, 0.02), (-27.4 - 1.6 * i, -1.0, 2.79), mat("CeilPanel", (1, 1, 1), 0.3, emit=(1, 0.98, 0.95), estr=3), C_CLIN, bevel=0.005)

# ================================================================== SKIN cutaway at x=200 (1 unit = 1 mm)
SK = Vector((200, 0, 0))
# backdrop: deep teal -> navy gradient, camera only
M_bd = bpy.data.materials.new("CutawayBackdrop"); M_bd.use_nodes = True
n, l = M_bd.node_tree.nodes, M_bd.node_tree.links
for x in list(n):
    if x.type != 'OUTPUT_MATERIAL': n.remove(x)
tc = n.new('ShaderNodeTexCoord'); sp = n.new('ShaderNodeSeparateXYZ'); l.new(tc.outputs['Generated'], sp.inputs['Vector'])
cr = n.new('ShaderNodeValToRGB'); cr.color_ramp.elements[0].color = (0.005, 0.015, 0.05, 1); cr.color_ramp.elements[1].color = (0.02, 0.17, 0.20, 1)
l.new(sp.outputs['Z'], cr.inputs['Fac'])
em = n.new('ShaderNodeEmission'); em.inputs['Strength'].default_value = 1.0; l.new(cr.outputs['Color'], em.inputs['Color'])
l.new(em.outputs['Emission'], n["Material Output"].inputs['Surface'])
bpy.ops.mesh.primitive_uv_sphere_add(radius=60, location=SK)
bd = bpy.context.object; bd.name = "CutawayBackdrop"; bd.data.materials.append(M_bd); link(bd, C_SKIN)
bd.visible_diffuse = bd.visible_glossy = bd.visible_shadow = bd.visible_transmission = False
# skin block 12 x 12 mm, 4 mm deep; top surface displaced with pores and wrinkles; front face (y=-6) is the section
def skin_material(name, mole=True, scale=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links; p = n["Principled BSDF"]
    tc = n.new('ShaderNodeTexCoord'); mp = n.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (scale,) * 3; mp.name = "SkinMap"
    l.new(tc.outputs['Object'], mp.inputs['Vector'])
    vor = n.new('ShaderNodeTexVoronoi'); vor.inputs['Scale'].default_value = 3.0; vor.feature = 'DISTANCE_TO_EDGE'; l.new(mp.outputs['Vector'], vor.inputs['Vector'])
    pore = n.new('ShaderNodeTexVoronoi'); pore.inputs['Scale'].default_value = 9.0; l.new(mp.outputs['Vector'], pore.inputs['Vector'])
    nz = n.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 1.2; nz.inputs['Detail'].default_value = 12; l.new(mp.outputs['Vector'], nz.inputs['Vector'])
    base = n.new('ShaderNodeValToRGB'); base.color_ramp.elements[0].color = (0.55, 0.33, 0.25, 1); base.color_ramp.elements[1].color = (0.78, 0.55, 0.44, 1)
    l.new(nz.outputs['Fac'], base.inputs['Fac'])
    col = base.outputs['Color']
    if mole:
        # mole mask: distance from centre distorted by noise -> irregular border, 3-tone interior
        dn = n.new('ShaderNodeTexNoise'); dn.inputs['Scale'].default_value = 0.35; dn.inputs['Detail'].default_value = 6; dn.inputs['Distortion'].default_value = 0.6
        l.new(mp.outputs['Vector'], dn.inputs['Vector'])
        vm = n.new('ShaderNodeVectorMath'); vm.operation = 'LENGTH'
        sxy = n.new('ShaderNodeVectorMath'); sxy.operation = 'MULTIPLY'; sxy.inputs[1].default_value = (1, 1, 0)
        l.new(mp.outputs['Vector'], sxy.inputs[0]); l.new(sxy.outputs['Vector'], vm.inputs[0])
        ad = n.new('ShaderNodeMath'); ad.operation = 'MULTIPLY_ADD'; ad.inputs[1].default_value = 2.2
        l.new(dn.outputs['Fac'], ad.inputs[0]); l.new(vm.outputs['Value'], ad.inputs[2])
        mk = n.new('ShaderNodeMapRange'); mk.name = 'MoleMask'; mk.inputs['From Min'].default_value = 4.2; mk.inputs['From Max'].default_value = 3.7
        l.new(ad.outputs[0], mk.inputs['Value'])
        mc = n.new('ShaderNodeValToRGB'); e = mc.color_ramp.elements
        e[0].color = (0.10, 0.04, 0.025, 1); e[1].color = (0.30, 0.13, 0.07, 1); e.new(0.5).color = (0.03, 0.015, 0.012, 1)
        e.new(0.75).color = (0.35, 0.10, 0.10, 1)
        l.new(dn.outputs['Fac'], mc.inputs['Fac'])
        mm = n.new('ShaderNodeMix'); mm.data_type = 'RGBA'; l.new(mk.outputs['Result'], mm.inputs['Factor'])
        l.new(col, mm.inputs['A']); l.new(mc.outputs['Color'], mm.inputs['B']); col = mm.outputs['Result']
    l.new(col, p.inputs['Base Color'])
    p.inputs['Subsurface Weight'].default_value = 0.35; p.inputs['Subsurface Radius'].default_value = (1.0, 0.4, 0.25)
    p.inputs['Subsurface Scale'].default_value = 0.3
    p.inputs['Roughness'].default_value = 0.42; p.inputs['Specular IOR Level'].default_value = 0.6
    p.inputs['Coat Weight'].default_value = 0.15; p.inputs['Coat Roughness'].default_value = 0.25
    h = n.new('ShaderNodeMath'); h.operation = 'MULTIPLY_ADD'; h.inputs[1].default_value = 0.6
    l.new(vor.outputs['Distance'], h.inputs[0]); l.new(pore.outputs['Distance'], h.inputs[2])
    bp = n.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.35; l.new(h.outputs[0], bp.inputs['Height']); l.new(bp.outputs['Normal'], p.inputs['Normal'])
    return m
M_skin_macro = skin_material("SkinMacro")
bpy.ops.mesh.primitive_grid_add(x_subdivisions=260, y_subdivisions=260, size=12, location=SK)
top = bpy.context.object; top.name = "SkinTop"; top.data.materials.append(M_skin_macro); link(top, C_SKIN)
tx = bpy.data.textures.new("SkinWrinkle", 'VORONOI'); tx.noise_scale = 1.3; tx.distance_metric = 'DISTANCE'
dm = top.modifiers.new("disp", 'DISPLACE'); dm.texture = tx; dm.strength = -0.08; dm.texture_coords = 'GLOBAL'
tx2 = bpy.data.textures.new("SkinBump", 'CLOUDS'); tx2.noise_scale = 0.6; tx2.noise_depth = 4
dm2 = top.modifiers.new("disp2", 'DISPLACE'); dm2.texture = tx2; dm2.strength = 0.12; dm2.texture_coords = 'GLOBAL'
# the mole is raised a little
tx3 = bpy.data.textures.new("MoleBump", 'BLEND'); tx3.progression = 'SPHERICAL'
mole_emp = bpy.data.objects.new("MoleCentre", None); mole_emp.location = SK; mole_emp.scale = (4.5, 4.5, 4.5); C_SKIN.objects.link(mole_emp); mole_emp.hide_render = True
dm3 = top.modifiers.new("disp3", 'DISPLACE'); dm3.texture = tx3; dm3.strength = 0.18; dm3.texture_coords = 'OBJECT'; dm3.texture_coords_object = mole_emp
# skin hairs (fine, sparse)
# cross-section block under the top: layers by depth (z), section face toward -y
M_sec = bpy.data.materials.new("SkinSection"); M_sec.use_nodes = True
n, l = M_sec.node_tree.nodes, M_sec.node_tree.links; p = n["Principled BSDF"]
tc = n.new('ShaderNodeTexCoord'); sp = n.new('ShaderNodeSeparateXYZ'); l.new(tc.outputs['Object'], sp.inputs['Vector'])
wob = n.new('ShaderNodeTexNoise'); wob.inputs['Scale'].default_value = 0.4; wob.inputs['Detail'].default_value = 5; l.new(tc.outputs['Object'], wob.inputs['Vector'])
zz = n.new('ShaderNodeMath'); zz.operation = 'MULTIPLY_ADD'; zz.inputs[1].default_value = 0.6
l.new(wob.outputs['Fac'], zz.inputs[0]); l.new(sp.outputs['Z'], zz.inputs[2])
lay = n.new('ShaderNodeValToRGB'); e = lay.color_ramp.elements; lay.color_ramp.interpolation = 'EASE'
# depth (mm, negative down): fat (yellow lobules) < -2.6, dermis pink fibrous, epidermis thin darker band near 0
mr = n.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = -4.0; mr.inputs['From Max'].default_value = 0.3
l.new(zz.outputs[0], mr.inputs['Value']); l.new(mr.outputs['Result'], lay.inputs['Fac'])
e[0].color = (0.75, 0.55, 0.18, 1); e[0].position = 0.0
e[1].color = (0.62, 0.20, 0.20, 1); e[1].position = 0.5
e.new(0.32).color = (0.80, 0.60, 0.22, 1); e.new(0.40).color = (0.70, 0.30, 0.28, 1)
e.new(0.86).color = (0.72, 0.36, 0.33, 1); e.new(0.90).color = (0.50, 0.28, 0.22, 1); e.new(0.97).color = (0.62, 0.42, 0.34, 1)
fib = n.new('ShaderNodeTexWave'); fib.inputs['Scale'].default_value = 1.4; fib.inputs['Distortion'].default_value = 12; fib.inputs['Detail'].default_value = 10
l.new(tc.outputs['Object'], fib.inputs['Vector'])
lob = n.new('ShaderNodeTexVoronoi'); lob.inputs['Scale'].default_value = 0.9; lob.feature = 'DISTANCE_TO_EDGE'; l.new(tc.outputs['Object'], lob.inputs['Vector'])
mx1 = n.new('ShaderNodeMix'); mx1.data_type = 'RGBA'; mx1.blend_type = 'MULTIPLY'; mx1.inputs['Factor'].default_value = 0.35
l.new(lay.outputs['Color'], mx1.inputs['A']); l.new(fib.outputs['Color'], mx1.inputs['B'])
lobm = n.new('ShaderNodeMapRange'); lobm.inputs['From Min'].default_value = 0.0; lobm.inputs['From Max'].default_value = 0.06
l.new(lob.outputs['Distance'], lobm.inputs['Value'])
mx2 = n.new('ShaderNodeMix'); mx2.data_type = 'RGBA'; mx2.blend_type = 'MULTIPLY'
fatmask = n.new('ShaderNodeMath'); fatmask.operation = 'LESS_THAN'; fatmask.inputs[1].default_value = -2.6; l.new(zz.outputs[0], fatmask.inputs[0])
inv = n.new('ShaderNodeMath'); inv.operation = 'MULTIPLY'; l.new(fatmask.outputs[0], inv.inputs[0])
one = n.new('ShaderNodeMath'); one.operation = 'SUBTRACT'; one.inputs[0].default_value = 1.0; l.new(lobm.outputs['Result'], one.inputs[1]); l.new(one.outputs[0], inv.inputs[1])
l.new(inv.outputs[0], mx2.inputs['Factor']); l.new(mx1.outputs['Result'], mx2.inputs['A']); mx2.inputs['B'].default_value = (0.45, 0.25, 0.1, 1)
l.new(mx2.outputs['Result'], p.inputs['Base Color'])
p.inputs['Subsurface Weight'].default_value = 0.5; p.inputs['Subsurface Radius'].default_value = (1.0, 0.35, 0.2); p.inputs['Subsurface Scale'].default_value = 0.4
p.inputs['Roughness'].default_value = 0.25; p.inputs['Coat Weight'].default_value = 0.5; p.inputs['Coat Roughness'].default_value = 0.08
hb = n.new('ShaderNodeMath'); hb.operation = 'ADD'; l.new(fib.outputs['Fac'], hb.inputs[0]); l.new(lob.outputs['Distance'], hb.inputs[1])
bp = n.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.5; l.new(hb.outputs[0], bp.inputs['Height']); l.new(bp.outputs['Normal'], p.inputs['Normal'])
bpy.ops.mesh.primitive_grid_add(x_subdivisions=200, y_subdivisions=80, size=1, location=SK + Vector((0, -6.0, -2.05)), rotation=(math.pi / 2, 0, 0))
sec = bpy.context.object; sec.name = "SkinSection"; sec.scale = (12, 4.1, 1); bpy.ops.object.transform_apply(scale=True)
sec.data.materials.append(M_sec); link(sec, C_SKIN)
tx4 = bpy.data.textures.new("SecBump", 'CLOUDS'); tx4.noise_scale = 0.25; tx4.noise_depth = 3
d4 = sec.modifiers.new("disp", 'DISPLACE'); d4.texture = tx4; d4.strength = 0.25; d4.texture_coords = 'GLOBAL'
box("SkinBody", (12, 12, 4.0), tuple(SK + Vector((0, 0, -2.1))), M_sec, C_SKIN, bevel=0)
# abnormal cells: dark irregular clusters growing down from the mole, out of the section face (scaled in 03)
M_cell = bpy.data.materials.new("MelanomaCell"); M_cell.use_nodes = True
n, l = M_cell.node_tree.nodes, M_cell.node_tree.links; p = n["Principled BSDF"]
vv = n.new('ShaderNodeTexVoronoi'); vv.inputs['Scale'].default_value = 14
cc = n.new('ShaderNodeValToRGB'); cc.color_ramp.elements[0].color = (0.04, 0.012, 0.02, 1); cc.color_ramp.elements[1].color = (0.32, 0.08, 0.14, 1)
l.new(vv.outputs['Distance'], cc.inputs['Fac']); l.new(cc.outputs['Color'], p.inputs['Base Color'])
p.inputs['Subsurface Weight'].default_value = 0.4; p.inputs['Roughness'].default_value = 0.2; p.inputs['Coat Weight'].default_value = 0.6
bpn = n.new('ShaderNodeBump'); bpn.inputs['Strength'].default_value = 0.6; l.new(vv.outputs['Distance'], bpn.inputs['Height']); l.new(bpn.outputs['Normal'], p.inputs['Normal'])
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=1.0, location=(0, 0, -50))
cell = bpy.context.object; cell.name = "CellSrc"; cell.data.materials.append(M_cell); link(cell, C_SKIN)
tc5 = bpy.data.textures.new("CellLump", 'VORONOI'); tc5.noise_scale = 0.45
d5 = cell.modifiers.new("disp", 'DISPLACE'); d5.texture = tc5; d5.strength = 0.18
bpy.ops.object.modifier_apply(modifier="disp")
bpy.ops.object.shade_smooth()

nuc_m = mat("CellNucleus", (0.02, 0.0, 0.03), 0.3, sss=0.2)
CELLS = []
for i in range(70):
    # branching down-and-out from the mole along random walk paths
    br = i % 5; t = (i // 5) / 14.0
    ang = br * 1.25 + random.uniform(-0.2, 0.2)
    rr = 1.0 + 2.6 * t + random.uniform(-0.3, 0.3)
    loc = SK + Vector((math.cos(ang) * rr * 0.9, -5.6 + random.uniform(-0.25, 0.25) - 0.15 * t, -0.35 - 2.4 * t + random.uniform(-0.2, 0.2)))
    o = cell.copy(); o.data = cell.data; o.location = loc; o.scale = (0.001,) * 3
    o.rotation_euler = (random.random() * 6, random.random() * 6, random.random() * 6); o["s"] = random.uniform(0.18, 0.36); o["t"] = t
    C_SKIN.objects.link(o); CELLS.append(o)
cell.hide_render = True; cell.hide_viewport = True
# vessels: displaced bevelled curves in the dermis
M_ves = mat("Vessel", (0.45, 0.03, 0.04), 0.2, sss=0.6, noise=0.4, nscale=6)
for i in range(4):
    cu = bpy.data.curves.new(f"Vessel{i}", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.12 + 0.05 * i; cu.bevel_resolution = 4
    sp_ = cu.splines.new('NURBS'); pts = []
    for k in range(8):
        pts.append(SK + Vector((-6 + k * 1.75, -5.7 + 0.1 * math.sin(k + i), -1.4 - 0.5 * i + 0.35 * math.sin(k * 1.3 + i))))
    sp_.points.add(len(pts) - 1)
    for k, pt in enumerate(pts): sp_.points[k].co = (*pt, 1)
    sp_.use_endpoint_u = True; sp_.order_u = 4
    vo = bpy.data.objects.new(f"Vessel{i}", cu); vo.data.materials.append(M_ves); C_SKIN.objects.link(vo)
# fine hairs on the top surface
for i in range(40):
    x, y = random.uniform(-6, 6), random.uniform(-6, 6)
    if x * x + y * y < 9: continue
    cu = bpy.data.curves.new(f"Hair{i}", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.012
    sp_ = cu.splines.new('BEZIER'); sp_.bezier_points.add(1)
    a = random.uniform(0, 6.28)
    sp_.bezier_points[0].co = SK + Vector((x, y, 0.0)); sp_.bezier_points[1].co = SK + Vector((x + math.cos(a) * 1.5, y + math.sin(a) * 1.5, 0.5))
    for b in sp_.bezier_points: b.handle_left_type = b.handle_right_type = 'AUTO'
    ho = bpy.data.objects.new(f"Hair{i}", cu); ho.data.materials.append(mat("SkinHair", (0.08, 0.05, 0.03), 0.4)); C_SKIN.objects.link(ho)
# studio key/rim for the cutaway
for nm_, loc, rot, e_, col in (("SkinKey", (6, -14, 10), (math.radians(55), 0, math.radians(25)), 3000, (1, 0.96, 0.9)),
                                ("SkinRim", (-10, 8, 6), (math.radians(-60), 0, math.radians(200)), 2500, (0.4, 0.9, 1.0)),
                                ("SkinFill", (-12, -14, 2), (math.radians(80), 0, math.radians(-40)), 800, (0.7, 0.85, 1.0))):
    L = bpy.data.lights.new(nm_, 'AREA'); L.energy = e_; L.size = 8; L.color = col
    lo = bpy.data.objects.new(nm_, L); lo.location = SK + Vector(loc); lo.rotation_euler = rot; C_SKIN.objects.link(lo)

# ================================================================== CITY at x=-300 (night)
CT = Vector((-300, 0, 0))
M_asph = mat("Asphalt", (0.05, 0.05, 0.055), 0.6, noise=0.4, nscale=40)
plane("Street", 200, 200, CT, M_asph, C_CITY)
bsrc = glb(OB + "/cityblock.glb", "CityBlockSrc", C_CITY, height=26.0)
bsrc.hide_render = bsrc.hide_viewport = True
BUILDINGS = []
for i, (x, y, r) in enumerate(((-30, 25, 0), (0, 25, 0), (30, 25, 0), (-30, -25, math.pi), (0, -25, math.pi), (30, -25, math.pi),
                               (-60, 25, 0), (60, -25, math.pi), (-60, -25, math.pi), (60, 25, 0))):
    o = bsrc.copy(); o.hide_render = o.hide_viewport = False; o.location = CT + Vector((x, y, 0)); o.rotation_euler.z = r + math.pi / 2
    C_CITY.objects.link(o); BUILDINGS.append(o)
# lit windows with phones/screens: emissive cards just in front of the facades
M_win = mat("WindowGlow", (1, 0.8, 0.5), 0.5, emit=(1.0, 0.75, 0.45), estr=6)
M_scr = mat("PhoneGlow", (0.6, 0.8, 1.0), 0.5, emit=(0.55, 0.78, 1.0), estr=14)
WINDOWS = []
for b in BUILDINGS:
    for k in range(18):
        u = random.uniform(-10, 10); h = random.choice([4.5, 8, 11.5, 15, 18.5, 22])
        side = 1 if b.location.y < CT.y else -1
        loc = Vector((b.location.x + u, CT.y + side * 12.3 * (1 if b.location.y < CT.y else 1) * 0 + b.location.y + side * 11.9, h))
        w_ = plane(f"Win_{b.name}_{k}", 1.4, 1.6, loc, M_win if random.random() < 0.6 else M_scr, C_CITY, rot=(math.pi / 2, 0, 0))
        WINDOWS.append(w_)
for i in range(6):
    L = bpy.data.lights.new(f"StreetLamp{i}", 'POINT'); L.energy = 3000; L.color = (1.0, 0.7, 0.4); L.shadow_soft_size = 0.5
    lo = bpy.data.objects.new(L.name, L); lo.location = CT + Vector((-50 + i * 20, 9 * (1 if i % 2 else -1), 7)); C_CITY.objects.link(lo)
bus = glb(OB + "/bus.glb", "Bus", C_CITY, length=11.0, loc=CT + Vector((-30, -4, 0)))
L = bpy.data.lights.new("BusInterior", 'AREA'); L.energy = 1500; L.size = 8; L.color = (0.9, 0.95, 1.0)
lo = bpy.data.objects.new("BusInterior", L); lo.location = (0, 0, 2.4); lo.rotation_euler = (math.pi, 0, 0); lo.parent = bus; C_CITY.objects.link(lo)

# ================================================================== HOME at (-300, 200)
HM = Vector((-300, 200, 0))
M_hw = pbr("HomeWall", "painted_plaster_wall", 1.5, tint=(0.78, 0.68, 0.58), coords='Object')
M_hf = pbr("HomeFloor", "laminate_floor_02", 1.2)
plane("HomeFloorP", 6, 6, HM, M_hf, C_HOME)
box("HomeWallN", (6, 0.2, 2.8), tuple(HM + Vector((0, 3.0, 1.4))), M_hw, C_HOME, bevel=0)
box("HomeWallW", (0.2, 6, 2.8), tuple(HM + Vector((-3.0, 0, 1.4))), M_hw, C_HOME, bevel=0)
box("HomeWallE", (0.2, 6, 2.8), tuple(HM + Vector((3.0, 0, 1.4))), M_hw, C_HOME, bevel=0)
box("HomeCeil", (6, 6, 0.1), tuple(HM + Vector((0, 0, 2.85))), mat("HomeCeilM", (0.85, 0.83, 0.8), 0.9, noise=0.1), C_HOME, bevel=0)
# south wall with a window (camera enters through the curtain)
box("HomeWallS_L", (2.2, 0.2, 2.8), tuple(HM + Vector((-1.9, -3.0, 1.4))), M_hw, C_HOME, bevel=0)
box("HomeWallS_R", (2.2, 0.2, 2.8), tuple(HM + Vector((1.9, -3.0, 1.4))), M_hw, C_HOME, bevel=0)
box("HomeWallS_B", (1.6, 0.2, 0.9), tuple(HM + Vector((0, -3.0, 0.45))), M_hw, C_HOME, bevel=0)
box("HomeWallS_T", (1.6, 0.2, 0.5), tuple(HM + Vector((0, -3.0, 2.55))), M_hw, C_HOME, bevel=0)
M_curt = pbr("Curtain", "knitted_fleece", 0.25, tint=(0.75, 0.62, 0.5))
M_curt.node_tree.nodes["Principled BSDF"].inputs['Transmission Weight'].default_value = 0.3
sofa, _ = ph_blend("Sofa_01", C_HOME, HM + Vector((0, 1.9, 0)), rot_z=math.pi)
tbl, _ = ph_blend("modern_coffee_table_01", C_HOME, HM + Vector((0, 0.7, 0)))
lamp, _ = ph_blend("desk_lamp_arm_01", C_HOME, HM + Vector((1.2, 2.3, 0.0)))
plant, _ = ph_blend("potted_plant_04", C_HOME, HM + Vector((-2.2, 2.2, 0)), scale=1.4)
laptop, LAPOBS = ph_blend("classic_laptop", C_HOME, HM + Vector((0.0, 0.62, 0.0)), rot_z=math.pi)
L = bpy.data.lights.new("HomeLamp", 'POINT'); L.energy = 120; L.color = (1.0, 0.75, 0.45); L.shadow_soft_size = 0.2
lo = bpy.data.objects.new("HomeLamp", L); lo.location = HM + Vector((0.9, 2.0, 1.4)); C_HOME.objects.link(lo)
L = bpy.data.lights.new("HomeFill", 'AREA'); L.energy = 300; L.size = 3; L.color = (1.0, 0.85, 0.7)
lo = bpy.data.objects.new("HomeFill", L); lo.location = HM + Vector((-1.5, -1.5, 2.6)); lo.rotation_euler = (math.radians(30), 0, math.radians(-30)); C_HOME.objects.link(lo)
L = bpy.data.lights.new("TVFlicker", 'AREA'); L.energy = 150; L.size = 1.0; L.color = (0.5, 0.7, 1.0)
lo = bpy.data.objects.new("TVFlicker", L); lo.location = HM + Vector((2.6, 0.5, 1.0)); lo.rotation_euler = (0, math.radians(-90), 0); C_HOME.objects.link(lo)
print("SCENE_OK", len(bpy.data.objects))
# curtain over the home window: folded (wave displacement), half sheer
bpy.ops.mesh.primitive_grid_add(x_subdivisions=120, y_subdivisions=60, size=1, location=HM + Vector((0, -2.86, 1.45)), rotation=(math.pi / 2, 0, 0))
cur = bpy.context.object; cur.name = "Curtain"; cur.scale = (1.9, 2.3, 1); bpy.ops.object.transform_apply(scale=True)
cur.data.materials.append(M_curt); link(cur, C_HOME)
twv = bpy.data.textures.new("CurtainFolds", 'WOOD'); twv.wood_type = 'BANDS'; twv.noise_basis_2 = 'SIN'; twv.turbulence = 2
cdm = cur.modifiers.new("folds", 'DISPLACE'); cdm.texture = twv; cdm.strength = 0.06; cdm.texture_coords = 'GLOBAL'
