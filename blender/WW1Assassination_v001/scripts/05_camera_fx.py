"""One continuous camera (Catmull-Rom through ~1 s framings, anchored to moving subjects), plus FX: muzzle flashes,
the explosion (flash, light, smoke, debris, dust ring), the rewind grade (compositor), whiteout card for the cloud wipe.
blender -b map.blend --python 05_camera_fx.py -- <out.blend>"""
import sys, os, math, random
import bpy, bmesh
from mathutils import Vector, Matrix, Quaternion
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "00_lib.py")).read())
exec(open(os.path.join(HERE, "00_story.py")).read())
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
F_END = 2130
random.seed(5)
CF = coll("FX")
SEAT_R = sc.get("SEAT_R", 0.96)
A_LOCAL = Vector((-0.33, 0.86, SEAT_R + 0.55)); D_LOCAL = Vector((0.31, 0.86, SEAT_R + 0.5))

def car_M(s):
    p, h = car1(s); return Matrix.Translation(Vector((p.x, p.y, 0))) @ Matrix.Rotation(h, 4, 'Z')
GN = bpy.data.objects["Gunman"]
def gun_head(f):
    sc.frame_set(f); return GN.matrix_world @ GN.pose.bones["head"].head
# cache gunman head per frame on the frames we need (evaluated rig)
GH = {}
def gunhead(f):
    if f not in GH: GH[f] = gun_head(f)
    return GH[f]
def bomb_at(s):
    p = bomb_pos(s)
    return p if p is not None else Vector((REL_P.x, REL_P.y, REL_P.z))

def A(kind, v):
    """anchor -> function(f) -> world point"""
    v = Vector(v)
    if kind == "w": return lambda f: v
    if kind == "car": return lambda f: car_M(sig_f(f)) @ v
    if kind == "gun": return lambda f: gunhead(f) + v
    if kind == "bomb": return lambda f: bomb_at(sig_f(f)) + v
    if kind == "arch": return lambda f: car_M(sig_f(f)) @ (A_LOCAL + v)
    if kind == "duch": return lambda f: car_M(sig_f(f)) @ (D_LOCAL + v)
KEYS = [  # t, camera anchor, aim anchor, lens
    (0.0, A("car", (1.65, -1.7, 0.42)), A("car", (0.2, -1.0, 0.65)), 22),
    (1.0, A("car", (1.75, 0.3, 1.5)), A("car", (0.0, 0.7, 1.35)), 26),
    (2.0, A("car", (0.9, -3.3, 1.65)), A("car", (-0.2, 0.4, 1.3)), 26),
    (3.0, A("car", (-1.7, -0.5, 1.6)), A("arch", (0, 0, 0.05)), 35),
    (4.0, A("car", (1.35, -0.2, 1.75)), A("duch", (0, 0, 0.05)), 40),
    (5.0, A("w", (4.15, 12.0, 1.78)), A("arch", (0, 0, 0)), 40),
    (6.0, A("w", (3.92, 11.5, 1.66)), A("arch", (0, 0, -0.05)), 50),
    (6.9, A("w", (3.82, 11.3, 1.64)), A("arch", (0, 0, -0.05)), 55),
    (7.3, A("w", (1.8, 7.2, 3.0)), A("w", (0.8, 11.0, 1.2)), 28),
    (7.9, A("w", (6.0, 2.0, 7.5)), A("w", (22.0, 3.5, 2.0)), 26),
    (8.4, A("w", (30.0, -3.0, 10.0)), A("w", (60.0, 3.0, 1.0)), 24),
    (9.3, A("w", (65.0, -3.0, 6.0)), A("w", (88.0, 5.0, 1.5)), 26),
    (10.1, A("w", (88.6, 4.1, 1.75)), A("w", (90.9, 6.9, 1.55)), 32),
    (11.0, A("w", (89.7, 5.5, 1.45)), A("w", (90.7, 6.8, 1.25)), 45),
    (12.0, A("w", (88.4, 4.0, 1.85)), A("w", (91.2, 7.5, 1.5)), 30),
    (12.6, A("w", (83.9, 4.7, 1.95)), A("w", (82.3, 6.6, 1.75)), 30),
    (13.3, A("w", (84.2, 3.0, 2.5)), A("bomb", (0, 0, 0)), 32),
    (14.0, A("car", (-1.15, 2.05, 1.95)), A("car", (0.0, 1.18, 1.5)), 45),
    (14.8, A("w", (81.0, 3.3, 0.42)), A("bomb", (0, 0, 0)), 30),
    (15.5, A("w", (81.2, 0.6, 0.32)), A("w", (84.3, 1.4, 0.4)), 24),
    (16.2, A("w", (79.3, -2.6, 1.5)), A("w", (84.0, 1.5, 1.0)), 22),
    (17.2, A("w", (76.0, -5.5, 7.0)), A("w", (86.0, 4.0, 0.8)), 22),
    (18.2, A("w", (86.0, -6.0, 9.0)), A("w", (82.0, 3.5, 0.5)), 22),
    (18.9, A("car", (0.4, 4.4, 1.1)), A("car", (0.0, -2.0, 1.0)), 26),
    (19.6, A("car", (0.0, 7.0, 7.5)), A("car", (0.0, -3.0, 0.5)), 24),
    (20.5, A("w", (4.2, 3.6, 18.0)), A("w", (3.0, 5.6, 0.0)), 22),
    (21.5, A("car", (1.45, -0.7, 1.75)), A("car", (0.2, 0.1, 1.5)), 32),
    (22.4, A("w", (-1.0, 13.9, 1.85)), A("gun", (0.0, 0.0, -0.05)), 30),
    (23.3, A("gun", (-0.7, 1.45, 0.1)), A("gun", (0.0, 0.0, 0.0)), 45),
    (24.2, A("gun", (-0.5, 0.28, 0.04)), A("gun", (0.0, 0.0, 0.02)), 60),
    (25.0, A("gun", (0.55, 0.5, 0.14)), A("arch", (0, 0, 0)), 35),
    (25.8, A("gun", (0.75, 0.75, 0.22)), A("arch", (0, 0, -0.05)), 32),
    (26.8, A("w", (-0.6, 13.3, 2.2)), A("w", (1.0, 10.1, 1.25)), 40),
    (27.7, A("w", (0.0, 14.5, 6.0)), A("w", (1.5, 10.5, 1.0)), 28),
    (28.6, A("w", (1.0, 12.0, 26.0)), A("w", (1.5, 9.0, 0.0)), 24),
    (29.1, A("w", (0.0, 7.0, 80.0)), A("w", (0.0, 3.0, 0.0)), 24),
    (29.8, A("w", (0.0, -50.0, 150.0)), A("w", (5.0, 18.0, 0.0)), 26),
    (30.8, A("w", (12.0, -70.0, 180.0)), A("w", (15.0, 45.0, 0.0)), 26),
    (31.8, A("w", (-30.0, -90.0, 215.0)), A("w", (-15.0, 60.0, 0.0)), 25),
    (33.0, A("w", (-8.0, -80.0, 290.0)), A("w", (5.0, 72.0, 0.0)), 24),
    (34.3, A("w", (14.0, -88.0, 315.0)), A("w", (12.0, 74.0, 0.0)), 24),
    (35.5, A("w", (19.0, -90.0, 320.0)), A("w", (13.0, 75.0, 0.0)), 24)]
TS = [k[0] for k in KEYS]
def catmull_at(t, get):
    """get(j) -> value at TS[j] (Vector or float); only the 4 neighbours are evaluated"""
    xs = TS
    if t <= xs[0]: return get(0)
    if t >= xs[-1]: return get(len(xs) - 1)
    i = max(j for j in range(len(xs) - 1) if xs[j] <= t)
    x0, x1 = xs[i], xs[i + 1]
    p1, p2 = get(i), get(i + 1)
    p0 = get(i - 1) if i > 0 else p1 - (p2 - p1)
    p3 = get(i + 2) if i + 2 < len(xs) else p2 + (p2 - p1)
    t0 = xs[i - 1] if i > 0 else x0 - (x1 - x0)
    t3 = xs[i + 2] if i + 2 < len(xs) else x1 + (x1 - x0)
    m1 = (p2 - p0) * ((x1 - x0) / (x1 - t0)); m2 = (p3 - p1) * ((x1 - x0) / (t3 - x0))
    u = (t - x0) / (x1 - x0)
    h00 = 2 * u ** 3 - 3 * u ** 2 + 1; h10 = u ** 3 - 2 * u ** 2 + u; h01 = -2 * u ** 3 + 3 * u ** 2; h11 = u ** 3 - u ** 2
    return p1 * h00 + m1 * h10 + p2 * h01 + m2 * h11

cam_d = bpy.data.cameras.new("CAM_Film"); cam_d.sensor_fit = 'AUTO'; cam_d.clip_start = 0.02; cam_d.clip_end = 4000
cam_d.dof.use_dof = True; cam_d.dof.aperture_fstop = 2.8
cam = bpy.data.objects.new("CAM_Film", cam_d); sc.collection.objects.link(cam); sc.camera = cam
aim = bpy.data.objects.new("CAM_Film_Aim", None); sc.collection.objects.link(aim)
tt = cam.constraints.new('TRACK_TO'); tt.target = aim; tt.track_axis = 'TRACK_NEGATIVE_Z'; tt.up_axis = 'UP_Y'
cam_d.dof.focus_object = aim
BLAST_T = next(t_of(f) for f in range(800, 1100) if sig_f(f) >= BLAST_SIG)
print("BLAST film t", BLAST_T)
for f in list(range(1, F_END + 1, 2)) + [F_END]:
    t = t_of(f)
    c = catmull_at(t, lambda j: KEYS[j][1](f)); a_ = catmull_at(t, lambda j: KEYS[j][2](f)); ln = catmull_at(t, lambda j: float(KEYS[j][3]))
    u = t - BLAST_T
    if 0 < u < 1.0:
        amp = 0.12 * math.exp(-4 * u)
        c = c + Vector((math.sin(f * 2.1), math.sin(f * 1.7 + 1), math.sin(f * 2.9 + 2))) * amp
    cam.location = c; aim.location = a_; cam_d.lens = ln
    cam.keyframe_insert("location", frame=f); aim.keyframe_insert("location", frame=f); cam_d.keyframe_insert("lens", frame=f)
# deep DOF on the map
for f, fs in ((1, 2.8), (f_of(28.0), 2.8), (f_of(28.8), 16.0), (F_END, 16.0)):
    cam_d.dof.aperture_fstop = fs; cam_d.dof.keyframe_insert("aperture_fstop", frame=f)
print("CAMERA keyed")

# ------------------------------------------------------------------ whiteout card in front of the lens (cloud wipe)
bm = bmesh.new(); add_box(bm, V(-1, -1, 0), V(1, 1, 0.001), 0)
WM = bpy.data.materials.new("Whiteout"); n, l = nodes_of(WM); n.clear()
o_ = n.new('ShaderNodeOutputMaterial'); mx = n.new('ShaderNodeMixShader'); tr = n.new('ShaderNodeBsdfTransparent')
em = n.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (1, 1, 1, 1); em.inputs['Strength'].default_value = 1.6
val = n.new('ShaderNodeValue'); val.name = "WhiteAmt"
l.new(val.outputs[0], mx.inputs[0]); l.new(tr.outputs[0], mx.inputs[1]); l.new(em.outputs[0], mx.inputs[2]); l.new(mx.outputs[0], o_.inputs[0])
card = mesh_obj("WhiteoutCard", bm, [WM], CF); card.parent = cam; card.location = (0, 0, -0.05); card.scale = (0.2, 0.2, 1)
card.visible_shadow = False
SW = sc.get("SWAP_F", f_of(29.12))
for f, v in ((1, 0.0), (SW - 22, 0.0), (SW - 4, 1.0), (SW + 4, 1.0), (SW + 26, 0.0), (F_END, 0.0)):
    val.outputs[0].default_value = v; val.outputs[0].keyframe_insert("default_value", frame=f)

# ------------------------------------------------------------------ muzzle flashes (pistol), with a light that pops on faces and paint
pistol = bpy.data.objects["Pistol"]
bm = bmesh.new()
bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=0.05, radius2=0.0, depth=0.22, matrix=Matrix.Translation(V(0, -0.29, 0.04)) @ Matrix.Rotation(R_(90), 4, 'X'))
mf = mesh_obj("MuzzleFlash", bm, [flat("MuzzleFlashMat", (1, 0.8, 0.4), emit=(1.0, 0.75, 0.35), emit_str=60.0)], CF)
mf.parent = pistol; mf.visible_shadow = False
ml = bpy.data.objects.new("MuzzleLight", bpy.data.lights.new("MuzzleLight", 'POINT')); CF.objects.link(ml)
ml.parent = pistol; ml.location = (0, -0.3, 0.04); ml.data.shadow_soft_size = 0.05; ml.data.color = (1.0, 0.75, 0.4)
prev = None
for f in range(1, F_END + 1):
    s = sig_f(f)
    on = any(0.0 <= s - st < 0.06 for st in SHOT_S)
    if on != prev:
        mf.hide_render = not on; mf.keyframe_insert("hide_render", frame=f)
        ml.data.energy = 900.0 if on else 0.0; ml.data.keyframe_insert("energy", frame=f); prev = on
for idb in (mf, ml.data):
    for layer in idb.animation_data.action.layers:
        for st in layer.strips:
            for cb in st.channelbags:
                for fc in cb.fcurves:
                    for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
# gunsmoke wisps after each shot
SMK = bpy.data.materials.new("GunSmoke"); n, l = nodes_of(SMK); n.clear()
o_ = n.new('ShaderNodeOutputMaterial'); pv = n.new('ShaderNodeVolumePrincipled'); pv.inputs['Density'].default_value = 1.5
pv.inputs['Color'].default_value = (0.7, 0.7, 0.68, 1); l.new(pv.outputs[0], o_.inputs['Volume'])

# ------------------------------------------------------------------ the explosion under car 2 (no bodies)
E = BLAST_P
bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
fb = mesh_obj("BlastFireball", bm, [flat("BlastFire", (1, 0.6, 0.2), emit=(1.0, 0.42, 0.08), emit_str=10.0)], CF); fb.location = E
fb.visible_shadow = False
bl = bpy.data.objects.new("BlastLight", bpy.data.lights.new("BlastLight", 'POINT')); CF.objects.link(bl); bl.location = E + Vector((0, 0, 0.6))
bl.data.color = (1.0, 0.65, 0.3); bl.data.shadow_soft_size = 0.5
SMOKE = bpy.data.materials.new("BlastSmoke"); n, l = nodes_of(SMOKE); n.clear()
o_ = n.new('ShaderNodeOutputMaterial'); pv = n.new('ShaderNodeVolumePrincipled')
tc = n.new('ShaderNodeTexCoord'); nz = n.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 1.6; nz.inputs['Detail'].default_value = 6
l.new(tc.outputs['Object'], nz.inputs['Vector'])
ln_ = n.new('ShaderNodeVectorMath'); ln_.operation = 'LENGTH'; l.new(tc.outputs['Object'], ln_.inputs[0])
mr = n.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.6; mr.inputs['From Max'].default_value = 1.0
mr.inputs['To Min'].default_value = 1.0; mr.inputs['To Max'].default_value = 0.0; l.new(ln_.outputs['Value'], mr.inputs['Value'])
mul = n.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; l.new(mr.outputs['Result'], mul.inputs[0]); l.new(nz.outputs['Fac'], mul.inputs[1])
dval = n.new('ShaderNodeValue'); dval.name = "SmokeDensity"
mul2 = n.new('ShaderNodeMath'); mul2.operation = 'MULTIPLY'; l.new(mul.outputs[0], mul2.inputs[0]); l.new(dval.outputs[0], mul2.inputs[1])
l.new(mul2.outputs[0], pv.inputs['Density']); pv.inputs['Color'].default_value = (0.32, 0.3, 0.28, 1)
l.new(pv.outputs[0], o_.inputs['Volume'])
puffs = []
for k in range(5):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    puffs.append((mesh_obj(f"BlastSmoke_{k}", bm, [SMOKE], CF), Vector((random.uniform(-1, 1), random.uniform(-0.8, 0.8), 0)), random.uniform(0.8, 1.3)))
bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=False, segments=32, radius1=1.0, radius2=0.7, depth=0.25)
ring = mesh_obj("BlastDustRing", bm, [flat("Dust", (0.5, 0.45, 0.38), rough=1.0, alpha=0.6)], CF); ring.location = E
DEB = [flat("DebrisStone", (0.35, 0.33, 0.3), rough=0.9), flat("DebrisWood", (0.25, 0.15, 0.08), rough=0.8), flat("DebrisMetal", (0.08, 0.08, 0.08), rough=0.4, metal=0.8)]
debris = []
for k in range(44):
    bm = bmesh.new(); sz = random.uniform(0.04, 0.12)
    add_box(bm, V(-sz, -sz * 0.7, -sz * 0.5), V(sz, sz * 0.7, sz * 0.5), 0)
    o = mesh_obj(f"Debris_{k:02d}", bm, [DEB[k % 3]], CF)
    az = random.uniform(0, 2 * math.pi); el = random.uniform(R_(25), R_(75)); sp = random.uniform(4, 11)
    v0 = Vector((math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el))) * sp
    debris.append((o, v0, Vector((random.uniform(-9, 9), random.uniform(-9, 9), random.uniform(-9, 9)))))
dens_keys = []
for f in range(1, F_END + 1, 2):
    s = sig_f(f); u = s - BLAST_SIG
    vis = u > 0 and u < 12
    # fireball: grows fast, fades
    if 0 < u < 0.5:
        r = 1.3 * (1 - math.exp(-14 * u)) * (1 - 0.6 * u); e_ = 0
    else:
        r = 0.001; e_ = 0.0
    fb.scale = (r, r, r * 0.8); fb.keyframe_insert("scale", frame=f)
    bl.data.energy = 60000.0 * max(0.0, 1 - u / 0.35) if 0 < u < 0.35 else 0.0; bl.data.keyframe_insert("energy", frame=f)
    for o, off, gro in puffs:
        if u > 0:
            rr = gro * (0.6 + 2.6 * (1 - math.exp(-1.6 * u))); z = 0.6 + 1.1 * u
            o.location = E + off * (0.4 + 0.5 * u) + Vector((0, 0, z)); o.scale = (rr, rr, rr * 0.85)
        else:
            o.location = E; o.scale = (0.001,) * 3
        o.keyframe_insert("location", frame=f); o.keyframe_insert("scale", frame=f)
    dval.outputs[0].default_value = (0.45 * min(1.0, u / 0.15) * math.exp(-0.18 * max(0, u - 0.3))) if u > 0 else 0.0
    dval.outputs[0].keyframe_insert("default_value", frame=f)
    rr = 0.2 + 7.0 * (1 - math.exp(-3 * u)) if u > 0 else 0.001
    ring.scale = (rr, rr, 1.0 if u > 0 else 0.001); ring.keyframe_insert("scale", frame=f)
    for o, v0, w in debris:
        if u <= 0:
            p = E - Vector((0, 0, 1.5)); rot = Vector((0, 0, 0))
        else:
            tt_ = u; p = E + v0 * tt_ - Vector((0, 0, 4.9 * tt_ * tt_))
            if p.z < 0.05:   # ground: find landing time, slide to rest
                a, b, c_ = -4.9, v0.z, E.z - 0.05
                tl = (-b - math.sqrt(b * b - 4 * a * c_)) / (2 * a)
                pl = E + v0 * tl - Vector((0, 0, 4.9 * tl * tl)); vxy = Vector((v0.x, v0.y, 0)) * 0.25
                dt = min(tt_ - tl, 0.6); p = Vector((pl.x, pl.y, 0.05)) + vxy * dt * (1 - dt / 1.2); tt_ = tl + dt * 0.3
            rot = w * tt_
        o.location = p; o.rotation_euler = rot
        o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_euler", frame=f)
for o in [fb] + [p[0] for p in puffs] + [ring] + [d[0] for d in debris]:
    o.hide_render = True; o.keyframe_insert("hide_render", frame=1)
    o.hide_render = False; o.keyframe_insert("hide_render", frame=700)
    o.hide_render = True; o.keyframe_insert("hide_render", frame=1300)
    for layer in o.animation_data.action.layers:
        for st in layer.strips:
            for cb in st.channelbags:
                for fc in cb.fcurves:
                    if fc.data_path == "hide_render":
                        for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
print("FX keyed")

# ------------------------------------------------------------------ rewind grade + flicker (compositor) and exposure blips
# rewind grade: cool white balance (compositor needs a GPU context headless, so it is not used)
sc.render.use_compositing = False
vs = sc.view_settings
try:
    vs.use_white_balance = True
    for f, tk in ((1, 6500.0), (f_of(6.95), 6500.0), (f_of(7.25), 11000.0), (f_of(9.75), 11000.0), (f_of(10.15), 6500.0), (F_END, 6500.0)):
        vs.white_balance_temperature = tk; vs.keyframe_insert("white_balance_temperature", frame=f)
    print("WHITEBALANCE ok")
except Exception as e:
    print("WHITEBALANCE failed", e)
for f in range(1, F_END + 1, 2):
    t = t_of(f); ex = -0.7 if f < sc.get('SWAP_F', 1748) else -0.9
    if 7.0 < t < 10.0: ex += 0.25 * math.sin(f * 1.9) * math.sin(f * 0.7)
    if 0 < t - BLAST_T < 0.3: ex += 1.2 * (1 - (t - BLAST_T) / 0.3)
    for st in SHOT_S:
        tt0 = next((t_of(ff) for ff in range(1400, 1700) if sig_f(ff) >= st), None)
        if tt0 and 0 <= t - tt0 < 0.07: ex += 0.5
    sc.view_settings.exposure = ex; sc.view_settings.keyframe_insert("exposure", frame=f)
# render baseline
sc.cycles.samples = 48; sc.cycles.adaptive_threshold = 0.05; sc.cycles.use_adaptive_sampling = True; sc.cycles.use_denoising = True
sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = 0.5
sc.cycles.max_bounces = 8; sc.cycles.diffuse_bounces = 3; sc.cycles.glossy_bounces = 3; sc.cycles.transparent_max_bounces = 8
sc.render.use_persistent_data = True
sc.cycles.volume_step_rate = 4.0
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("CAMFX_DONE")
