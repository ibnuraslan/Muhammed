# SwedishCoffee build: sets, cast, animation, one continuous camera.
# blender -b --python 02_build.py -- <out.blend>
import sys
exec(open("/home/user/Muhammed/blender/SwedishCoffee_v001/scripts/lib.py").read())
OUT = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else None
random.seed(27)
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
for c in list(bpy.data.collections): bpy.data.collections.remove(c)
GZ = [0.0]; REKEY = []
def ground_z(x, y): return GZ[0]

# ------------------------------------------------------------------ render settings
r = sc.render; r.engine = 'CYCLES'; r.resolution_x, r.resolution_y, r.resolution_percentage = 1080, 1920, 100
r.fps, r.fps_base = 60, 1.0; sc.frame_start, sc.frame_end = 1, 2670
cy = sc.cycles; cy.device = 'CPU'; cy.samples = 48; cy.adaptive_threshold = 0.05; cy.use_denoising = True; cy.denoiser = 'OPENIMAGEDENOISE'
cy.max_bounces = 6; cy.volume_bounces = 0; cy.volume_step_rate = 4.0
r.use_motion_blur = True; r.motion_blur_shutter = 0.35
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
r.image_settings.file_format = 'PNG'

W = bpy.data.worlds.new("World"); sc.world = W; W.use_nodes = True
wn = W.node_tree.nodes; wl = W.node_tree.links
env = wn.new("ShaderNodeTexEnvironment"); env.image = _img(PH + "/hdri/kloofendal_overcast_puresky_2k.hdr")
wl.new(env.outputs[0], wn["Background"].inputs[0])
WBG = wn["Background"]
def world_keys(keys):
    for f, s in keys:
        WBG.inputs[1].default_value = s; WBG.inputs[1].keyframe_insert("default_value", frame=f)

# ------------------------------------------------------------------ materials
M = dict(
    cobble=pbr("m_cobble", "cobblestone_floor_01", 0.35, coord="UV", bump=1.0),
    castle=pbr("m_castle", "castle_wall_varriation", 0.3, coord="Generated" if False else "Object", bump=1.0),
    plaster=simple("m_plaster", (0.86, 0.80, 0.66), rough=0.75),
    paleblue=simple("m_paleblue", (0.55, 0.70, 0.82), rough=0.7),
    gold=simple("m_gold", (0.95, 0.70, 0.25), rough=0.3, metal=1.0),
    oak=pbr("m_oak", "medieval_wood", 0.6, coord="Object", bump=0.6),
    parquet=pbr("m_parquet", "herringbone_parquet", 0.3, coord="UV", bump=0.5, rough_mul=0.6),
    marble=pbr("m_marble", "marble_01", 0.2, coord="UV", bump=0.2, rough_mul=0.35),
    planks=pbr("m_planks", "dark_wooden_planks", 0.4, coord="Object", bump=0.7),
    snow=pbr("m_snow", "snow_02", 0.25, coord="UV", bump=1.0),
    roof=pbr("m_roof", "grey_roof_tiles", 0.4, coord="Object", bump=1.0),
    velvet=pbr("m_velvet", "velour_velvet", 2.0, coord="Object", tint=(0.5, 0.06, 0.07), bump=0.5),
    linen=pbr("m_linen", "rough_linen", 2.0, coord="Object", tint=(0.95, 0.93, 0.88), bump=0.6),
    coffee=simple("m_coffee", (0.025, 0.012, 0.006), rough=0.05),
    tea=simple("m_tea", (0.45, 0.18, 0.04), rough=0.05, trans=0.6),
    silver=simple("m_silver", (0.85, 0.85, 0.86), rough=0.18, metal=1.0),
    flame=simple("m_flame", (1, 0.6, 0.2), emit=(1.0, 0.55, 0.18), ew=25.0),
    wax=simple("m_wax", (0.9, 0.85, 0.72), rough=0.4, trans=0.0),
    glass=simple("m_glass", (0.9, 0.95, 1.0), rough=0.02, trans=1.0),
)
M["wax"].node_tree.nodes["Principled BSDF"].inputs["Subsurface Weight"].default_value = 0.6
def steam_mat(name, dens=0.6, col=(0.92, 0.92, 0.95)):
    m = bpy.data.materials.new(name); m.use_nodes = True; N, L = m.node_tree.nodes, m.node_tree.links
    N.remove(N["Principled BSDF"]); pv = N.new("ShaderNodeVolumePrincipled"); pv.inputs["Color"].default_value = (*col, 1)
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); nz = N.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 6.0; nz.inputs["Detail"].default_value = 6; nz.inputs["Roughness"].default_value = 0.6
    L.new(tc.outputs["Object"], mp.inputs[0]); L.new(mp.outputs[0], nz.inputs[0])
    gr = N.new("ShaderNodeTexGradient"); gr.gradient_type = 'SPHERICAL'; L.new(tc.outputs["Object"], gr.inputs[0])
    mr = N.new("ShaderNodeMapRange"); mr.inputs[1].default_value = 0.45; mr.inputs[2].default_value = 0.75; L.new(nz.outputs[0], mr.inputs[0])
    mul = N.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'; L.new(mr.outputs[0], mul.inputs[0]); L.new(gr.outputs[0], mul.inputs[1])
    dv = N.new("ShaderNodeValue"); dv.name = "Dens"; dv.outputs[0].default_value = dens
    mul2 = N.new("ShaderNodeMath"); mul2.operation = 'MULTIPLY'; L.new(mul.outputs[0], mul2.inputs[0]); L.new(dv.outputs[0], mul2.inputs[1])
    L.new(mul2.outputs[0], pv.inputs["Density"]); L.new(pv.outputs[0], N["Material Output"].inputs["Volume"])
    # drift: animate mapping location with a driver on frame
    d = mp.inputs["Location"].driver_add("default_value", 2).driver; d.expression = "-frame/90"
    return m

# ------------------------------------------------------------------ assets (templates)
A_ = {}
def T(name, size, axis="z", rot=(0, 0, 0)): A_[name] = asset(name, size, axis, rot); return A_[name]
T("gallows", 4.6); T("htb1", 9.0); T("htb3", 12.0); T("htb5", 13.0); T("house0", 10.0); T("house3", 9.0); T("house7", 7.5)
T("throne", 1.9); T("table", 0.78); T("chair", 1.0); T("chandelier", 1.6); 
T("silverpot", 0.26); T("coffeepot_cu", 0.28); T("teapot", 0.2); T("cup", 0.075)
T("quill", 0.3, "y"); T("book", 0.06); T("skull", 0.3); T("cart", 3.6, "x"); T("sack", 0.75); T("bean", 0.012, "x")
T("tricorn", 0.36, "x"); T("wig", 0.31); T("mask", 0.17, "x"); T("stall", 3.0, "x"); T("fountain", 5.0, "x"); T("church", 26.0); T("shackles", 0.42, "x")
for nm in ("GothicBed_01", "Chandelier_01", "Barrel_01", "Lantern_01", "brass_candleholders", "brass_goblets", "WoodenTable_01", "WoodenChair_01", "ArmChair_01", "GothicCabinet_01"):
    try: A_[nm] = ph_model(nm)
    except Exception as e: print("PHFAIL", nm, e)

for b in ("TwinA", "TwinB", "TwinA_old", "TwinB_old", "TwinA_vold", "King", "Guard", "Doctor1", "Doctor2", "Woman", "Townsman", "Townswoman"):
    base_human(b)

# ------------------------------------------------------------------ set chain
def P(pos, yaw): return Matrix.Translation(V(pos)) @ Matrix.Rotation(R_(yaw), 4, 'Z')
SETDEF = [  # name, frames [on, off), entry portal, exit portal (local pos, yaw of travel)
    ("S1_Courtyard", 1, 158, ((0, -14, 4), 0), ((4.6, -1.2, 4.2), 0)),
    ("S2_ThroneHall", 158, 575, ((0, -3.5, 2.6), 0), ((-1.0, 4.62, 1.22), -29)),
    ("S3_Street", 575, 705, ((0, -9, 3.0), 0), ((-2.2, 6.0, 1.9), 90)),
    ("S4_Chamber", 705, 1630, ((0, -3.2, 1.8), 0), ((5.2, -1.0, 1.9), -90)),
    ("S5_Church", 1630, 1850, ((0, -16, 2.5), 0), ((0, -3.0, 2.3), 0)),
    ("S6_Ballroom", 1850, 1985, ((0, -6.6, 2.1), 0), ((-2.5, 2.0, 1.5), 135)),
    ("S7_Bedroom", 1985, 2490, ((0, -2.6, 1.9), 0), ((4.7, -1.0, 1.7), -90)),
    ("S8_Square", 2490, 2671, ((0, -8.0, 2.2), 0), None),
]
ROOT = []; SETC = []
Mw = Matrix.Identity(4)
for i, (nm, on, off, ent, ex) in enumerate(SETDEF):
    if i > 0:
        pex = SETDEF[i - 1][4]
        Mw = ROOT[i - 1].matrix_world @ P(*pex) @ P(*ent).inverted()
    c = coll(nm); SETC.append(c)
    e = bpy.data.objects.new(nm + "_root", None); c.objects.link(e); e.matrix_world = Mw; ROOT.append(e)
bpy.context.view_layer.update()
def finish_set(i):
    c, rt = SETC[i], ROOT[i]
    for o in c.all_objects:
        if o.parent is None and o != rt and not o.constraints:
            o.parent = rt; o.matrix_parent_inverse = Matrix.Identity(4)
CUR = [0]
def S(i): CUR[0] = i; LOCALROOT[0] = ROOT[i]; return SETC[i]
def toW(i, p): return ROOT[i].matrix_world @ V(p)

CK = []  # (frame, set, cam_local, target_local, lens)
def cam(f, p, t, lens=30): CK.append((f, CUR[0], p, t, lens))

def light(c, kind, loc, energy, col=(1, 1, 1), size=1.0, rot=None, name="L"):
    l = bpy.data.lights.new(name, kind); l.energy = energy; l.color = col
    if kind == 'AREA': l.size = size
    elif kind in ('POINT', 'SPOT'): l.shadow_soft_size = size
    o = bpy.data.objects.new(name, l); c.objects.link(o); o.location = loc
    if rot: o.rotation_euler = [R_(a) for a in rot]
    return o
def aim(o, tgt):
    d = V(tgt) - o.location; o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()

def room(c, x0, x1, y0, y1, h, floor, wall, ceil=None, skip=()):
    plane("floor", c, (x1 - x0, y1 - y0), ((x0 + x1) / 2, (y0 + y1) / 2, 0), floor)
    # wall normals face INTO the room (a camera inside sees front faces)
    for nm, sz, loc, rot in (("wN", (x1 - x0, h), ((x0 + x1) / 2, y1, h / 2), (90, 0, 0)), ("wS", (x1 - x0, h), ((x0 + x1) / 2, y0, h / 2), (90, 0, 180)),
                             ("wE", (y1 - y0, h), (x1, (y0 + y1) / 2, h / 2), (90, 0, -90)), ("wW", (y1 - y0, h), (x0, (y0 + y1) / 2, h / 2), (90, 0, 90))):
        if nm not in skip: plane(nm, c, sz, loc, wall, rot)
    if ceil: plane("ceil", c, (x1 - x0, y1 - y0), ((x0 + x1) / 2, (y0 + y1) / 2, h), ceil, (180, 0, 0))

def candle(c, loc, h=0.22, burn=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.022, depth=1, location=(0, 0, 0.5))
    w = bpy.context.active_object; w.name = "candle"; bpy.ops.object.transform_apply(location=True); link(w, c); setmat(w, M["wax"])
    w.location = loc; w.scale = (1, 1, h)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.012, location=(0, 0, 0)); fl = bpy.context.active_object; fl.name = "flame"; link(fl, c)
    fl.scale = (1, 1, 2.2); setmat(fl, M["flame"]); fl.location = (loc[0], loc[1], loc[2] + h + 0.02)
    pl = light(c, 'POINT', fl.location, 6, (1, 0.62, 0.3), 0.02, name="candleL")
    if burn:
        for f, s in burn:
            w.scale.z = h * s; w.keyframe_insert("scale", index=2, frame=f)
            fl.location.z = loc[2] + h * s + 0.02; fl.keyframe_insert("location", index=2, frame=f)
            pl.location.z = fl.location.z; pl.keyframe_insert("location", index=2, frame=f)
    return w

def hat(arm, tmpl, c, dz=0.10, dy=0.0, s=1.0, rx=0.0):
    sc.frame_set(1); bpy.context.view_layer.update()
    hb = arm.pose.bones["head"]; Mh = arm.matrix_world @ hb.matrix
    o = inst(tmpl, c, name=arm.name + "_" + tmpl.name)
    o.matrix_world = Matrix.Translation(Mh.to_translation() + V((0, dy, dz))) @ Matrix.Rotation(R_(rx), 4, 'X') @ Matrix.Scale(s, 4)
    attach(o, arm, "head"); return o

def human(base, nm, c):
    a = clone(base, nm, c); a.parent = ROOT[CUR[0]]; a.matrix_parent_inverse = Matrix.Identity(4); return Actor(a)

def crowd_idle(A, f0, f1, pos, yaw, mode="jeer", seed=0, phase=0.0):
    """alive standing crowd: weight shifts, fists, pointing; feet planted"""
    rnd = random.Random(seed)
    per = rnd.uniform(40, 70); A.pos = V(pos); A.yaw = yaw
    f = f0
    while f <= f1:
        u = math.sin((f + phase * per) / per * 2 * math.pi)
        A.stand(f, flex=4 + 3 * u, twist=8 * u, side=3 * u, head=(-5 + 6 * u, 10 * math.sin(f / per * 3.1)), lean=2 * u)
        if mode == "jeer":
            up = (u > 0.2)
            A.hand(f, "R", (-0.25, -0.2, 1.75 + 0.15 * u) if up else (-0.38, -0.2, 0.95), d=(0, -0.2, 1) if up else (-0.15, -0.2, -1),
                   n=(0, -1, 0) if up else (1, 0, 0), pole=(-0.6, 0.3, 1.3))
            A.hand(f, "L", (0.35, -0.11, 0.9), d=(0.05, -0.05, -1), n=(-1, 0, 0), pole=(0.3, 0.6, 1.1))
            A.face(f, brow=-1.5, jaw=10 * max(0, u), frown=1)
        elif mode == "toast":
            up = u > -0.3
            A.hand(f, "R", (-0.2, -0.32, 1.55 + 0.25 * u) if up else (-0.2, -0.3, 1.2), d=(0, -0.3, 1), n=(1, 0, 0), pole=(-0.5, 0.4, 1.2))
            A.hand(f, "L", (0.35, -0.11, 0.9), d=(0.05, -0.05, -1), n=(-1, 0, 0), pole=(0.3, 0.6, 1.1))
            A.face(f, brow=1.2, smile=1.5, jaw=8 * max(0, u)); grip(A.R, f, "R", 0.8)
        elif mode == "watch":
            A.arms_down(f, sway=0.02 * u); A.face(f, brow=0.5 * u, lids=0.1)
        f += int(per / 2)

def walker(base, nm, c, p0, p1, f0, f1, stride=0.7):
    A = human(base, nm, c); p0 = V(p0); p1 = V(p1)
    yw = math.degrees(math.atan2(-(p1 - p0).x, (p1 - p0).y)) + 180
    A.H.walk(lambda f: p0.lerp(p1, (f - f0) / (f1 - f0)), lambda f: yw, f0, f1, stride=stride, duty=0.62, lift=0.08, lean=5)
    for f in range(f0, f1 + 1, 30):
        A.pos = p0.lerp(p1, (f - f0) / (f1 - f0)).to_2d(); A.yaw = yw; A.arms_down(f, sway=0.04 * math.sin(f / 9)); A.face(f, brow=0.4)
    return A

TAPI = _img(sorted(glob.glob(PH + "/fabric_pattern_07/textures/*col_1*"))[0])
def tapestry(c, loc, rz, w=1.6, h=2.4, tint=(0.75, 0.2, 0.15)):
    nm_ = "m_tap%.2f" % tint[0]
    m = bpy.data.materials.get(nm_)
    if not m:
        m = bpy.data.materials.new(nm_); m.use_nodes = True; N_, L_ = m.node_tree.nodes, m.node_tree.links
        tc_ = N_.new("ShaderNodeTexCoord"); mp_ = N_.new("ShaderNodeMapping"); mp_.inputs["Scale"].default_value = (1.0, 1.4, 1); L_.new(tc_.outputs["UV"], mp_.inputs[0])
        vo_ = N_.new("ShaderNodeTexVoronoi"); vo_.feature = 'SMOOTH_F1'; vo_.inputs["Scale"].default_value = 9.0; L_.new(mp_.outputs[0], vo_.inputs[0])
        wv_ = N_.new("ShaderNodeTexWave"); wv_.inputs["Scale"].default_value = 14.0; wv_.inputs["Distortion"].default_value = 6.0; L_.new(mp_.outputs[0], wv_.inputs[0])
        mm_ = N_.new("ShaderNodeMath"); mm_.operation = 'MULTIPLY'; L_.new(vo_.outputs["Distance"], mm_.inputs[0]); L_.new(wv_.outputs["Fac"], mm_.inputs[1])
        mr_ = N_.new("ShaderNodeMapRange"); mr_.inputs[1].default_value = 0.15; mr_.inputs[2].default_value = 0.35; L_.new(mm_.outputs[0], mr_.inputs[0])
        mx_ = N_.new("ShaderNodeMix"); mx_.data_type = 'RGBA'; L_.new(mr_.outputs[0], mx_.inputs[0])
        mx_.inputs["A"].default_value = (*[v * 0.55 for v in tint], 1); mx_.inputs["B"].default_value = (*tint, 1)
        L_.new(mx_.outputs["Result"], N_["Principled BSDF"].inputs["Base Color"]); N_["Principled BSDF"].inputs["Roughness"].default_value = 0.55
        N_["Principled BSDF"].inputs["Sheen Weight"].default_value = 0.6
    o = plane("tapestry", c, (w, h), loc, m, (90, 0, rz))
    for i, (u, v) in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)]): o.data.uv_layers[0].data[i].uv = (u, v)
    box("rod", c, (w + 0.2, 0.05, 0.05) if rz in (0, 180) else (0.05, w + 0.2, 0.05), (loc[0], loc[1], loc[2] + h / 2 + 0.03), M["gold"])
    return o
def picture(c, loc, rz, s_=1.0):
    if "hanging_picture_frame_01" not in A_:
        try: A_["hanging_picture_frame_01"] = ph_model("hanging_picture_frame_01")
        except Exception as e: print("PHFAIL frame", e); return None
    return inst(A_["hanging_picture_frame_01"], c, loc, rz=rz, s=s_)
def candelabra(c, loc, h=1.4):
    box("candStand", c, (0.06, 0.06, h), (loc[0], loc[1], h / 2), M["gold"])
    box("candBase", c, (0.35, 0.35, 0.05), (loc[0], loc[1], 0.025), M["gold"])
    for dx in (-0.12, 0.0, 0.12): candle(c, (loc[0] + dx, loc[1], h), h=0.18)
def rug(c, loc, size, rz=0):
    r_ = box("rug", c, (size[0], size[1], 0.012), (loc[0], loc[1], loc[2] + 0.006), M["velvet"], rz=rz)
    box("rugBorder", c, (size[0] + 0.12, size[1] + 0.12, 0.008), (loc[0], loc[1], loc[2] + 0.004), M["gold"], rz=rz)
    return r_

# ================================================================== S1 Courtyard (b1)
c = S(0)
plane("ground", c, 70, (0, 0, 0), M["cobble"])
g = inst(A_["gallows"], c, (0, 0.5, 0), rz=0)
for t, p, rz in (("htb5", (-9, 12, 0), 0), ("house0", (2, 13, 0), 0), ("htb3", (11, 11, 0), 0), ("htb1", (-14, 2, 0), 90), ("house3", (-13, -8, 0), 90),
                 ("htb5", (14, -2, 0), -90), ("house7", (13, -11, 0), -90), ("htb3", (-5, -27, 0), 180), ("house0", (6, -25, 0), 180), ("htb1", (-14, 12, 0), 0)):
    inst(A_[t], c, p, rz=rz)
# platform height: ray down beside the centre
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
hit, loc, *_ = g.evaluated_get(dg).ray_cast(V((0.4, -0.2, 3.2)), V((0, 0, -1)))
PZ = loc.z if hit and loc.z < 3.0 else 1.6
print("PLATFORM_Z", hit, loc.z)
twins = []
for k, (b, x) in enumerate((("TwinA", -0.45), ("TwinB", 0.45))):
    A = human(b, b + "_S1", c); A.z = PZ; GZ[0] = PZ; twins.append(A)
    for f in range(1, 176, 30):
        u = math.sin(f / 23 + k)
        A.stand(f, pos=(x, 0.2), yaw=8 * (1 if k else -1), flex=10 + 3 * u, head=(12 + 4 * u, 6 * u))
        for s in "LR":
            sx = 1 if s == "L" else -1
            A.hand(f, s, (0.075 * sx, -0.22, 1.0), d=(-0.1 * sx, -1, 0.0), n=(-sx, 0, 0), pole=(0.4 * sx, 0.3, 1.0)); grip(A.R, f, s, pose="relaxed")
        A.face(f, brow=2.2, lids=-0.3, jaw=6 + 4 * u, frown=0.6)
    sh = inst(A_["shackles"], c, A.W((0, -0.22, 1.0)), rz=0, name="shackle_" + b); sh.rotation_euler.x = R_(90)
    attach(sh, A.a, "wrist.R", 1, local=True)
for k, x in enumerate((-1.3, 1.3)):
    A = human("Guard", "Guard_S1_%d" % k, c); A.z = PZ; GZ[0] = PZ
    for f in range(1, 176, 40):
        A.stand(f, pos=(x, 0.9), yaw=-25 * (1 if k else -1), head=(5, 0), flex=3)
        A.hand(f, "L" if k == 0 else "R", ((0.5 if k == 0 else -0.5), -0.5, 1.4), d=(0, -1, 0), n=(0, 0, -1))
        A.hand(f, "R" if k == 0 else "L", ((-0.35 if k == 0 else 0.35), -0.11, 0.9), d=((-0.15 if k == 0 else 0.15), -0.1, -1))
        A.face(f, brow=-1.5, frown=0.8)
    hat(A.a, A_["tricorn"], c)
GZ[0] = 0.0
CROWD = ["Townsman", "Townswoman", "Woman", "Townsman", "Townswoman", "Woman", "Townsman", "Townswoman"]
for k, b in enumerate(CROWD):
    A = human(b, "Crowd_S1_%d" % k, c)
    x = -3.2 + (k % 4) * 2.1 + random.uniform(-0.4, 0.4); y = -4.2 - (k // 4) * 1.9 + random.uniform(-0.3, 0.3)
    crowd_idle(A, 1, 175, (x, y), 180 + random.uniform(-25, 25), "jeer", seed=k, phase=random.random())
    if b == "Townsman": hat(A.a, A_["tricorn"], c)
light(c, 'SUN', (0, 0, 20), 3.0, (1.0, 0.93, 0.82), rot=(50, 0, 30), name="sun")
walker("Townsman", "Walk_S1_0", c, (-9, -2, 0), (-5, -9, 0), 1, 175); walker("Woman", "Walk_S1_1", c, (8, -10, 0), (6, -2, 0), 1, 175, 0.6)
cam(1, (-2.0, -15.0, 5.5), (0, 0, 2.6), 28)
cam(60, (-0.8, -9.5, 3.6), (0, 0.2, 2.8), 30)
cam(110, (0.25, -2.1, 2.85), (0, 0.2, 2.72), 40)
cam(140, (1.0, -1.5, 4.2), (2.0, 4.0, 5.0), 30)
cam(162, (2.3, 4.5, 5.6), (3.0, 12.0, 6.0), 26)
finish_set(0)

# ================================================================== S2 Throne hall (b2, b3)
c = S(1)
room(c, -6, 6, -8, 8, 7, M["parquet"], M["paleblue"], M["plaster"], skip=())
box("dais", c, (4, 3, 0.4), (0, 6.3, 0.2), M["marble"])
th = inst(A_["throne"], c, (0, 6.6, 0.4), rz=180)
box("carpet", c, (2.2, 13, 0.01), (0, -1.5, 0.005), M["velvet"])
for x in (-5.5, 5.5):
    for y in (-5, 0, 5):
        box("pillar", c, (0.7, 0.7, 7), (x, y, 3.5), M["marble"])
st = inst(A_["table"], c, (-1.15, 5.1, 0.4), rz=90); st.scale = (0.5, 0.3, 0.54)
cupK = inst(A_["cup"], c, (-1.0, 5.0, 0.4 + 0.42), name="KingCup")
bpy.ops.mesh.primitive_cylinder_add(radius=0.038, depth=0.002, location=(-1.0, 5.0, 0.4 + 0.42 + 0.064)); cf = bpy.context.active_object; link(cf, c); setmat(cf, M["coffee"])
# steam + skull (volume)
bpy.ops.mesh.primitive_cylinder_add(radius=0.12, depth=0.6, location=(-1.0, 5.0, 1.15)); stm = bpy.context.active_object; stm.name = "steamK"; link(stm, c)
setmat(stm, steam_mat("m_steamK", 3.5))
sk = inst(A_["skull"], c, (-1.0, 5.0, 1.16), rz=180, name="SteamSkull"); sk.scale = (0.9, 0.9, 0.9)
skm = steam_mat("m_skull", 0.0, (0.95, 0.95, 0.97)); setmat(sk, skm)
dn = skm.node_tree.nodes["Dens"]
for f, v in ((470, 0.0), (500, 30.0), (560, 40.0), (588, 16.0)):
    dn.outputs[0].default_value = v; dn.outputs[0].keyframe_insert("default_value", frame=f)
for f, z in ((470, 1.08), (588, 1.26)):
    sk.location.z = z; sk.keyframe_insert("location", index=2, frame=f)
K = human("King", "King_S2", c); K.z = 0.4; GZ[0] = 0.4; K.pos = V((0, 6.45)); K.yaw = 0
for f, hand_up, lean, br in ((175, 0, 0, -0.5), (185, 0.5, 4, -1.5), (200, 1, 8, -2.5), (240, 1, 6, -2.5), (285, 0.3, 2, -2), (300, 0, 14, -2.5), (360, 0, 20, -2.8), (420, 0, 22, -3), (590, 0, 22, -3)):
    K.sit(f, seat_z=0.48, flex=lean, twist=-18 if f >= 300 else 0, head=(10 if f >= 300 else -5, -25 if f >= 300 else 0))
    if hand_up:
        K.hand(f, "R", (-0.35, -0.35, 1.0 + 0.75 * hand_up), d=(0, -0.3, 1), n=(0, -1, 0), pole=(-0.7, 0.2, 1.2)); grip(K.R, f, "R", pose="relaxed")
    else:
        K.hand(f, "R", (-0.30, -0.25, 0.70), d=(0, -1, -0.2), n=(0, 0, -1), pole=(-0.6, 0.4, 0.9))
    K.hand(f, "L", (0.30, -0.25, 0.70), d=(0, -1, -0.2), n=(0, 0, -1), pole=(0.6, 0.4, 0.9))
    K.face(f, brow=br, frown=1.2 if f >= 185 else 0.3, jaw=14 if 185 <= f <= 240 else 0, lids=-0.2)
GZ[0] = 0.0
G = human("Guard", "Guard_S2", c); hat(G.a, A_["tricorn"], c)
G.stand(175, pos=(1.8, 4.2), yaw=200); G.arms_down(175); G.face(175, brow=1.5)
G.stand(200, pos=(1.8, 4.2), yaw=200, flex=10); G.arms_down(200)
G.H.walk(lambda f: V((1.8, 4.2, 0)).lerp(V((-3.5, -7.5, 0)), smooth((f - 205) / 90)), lambda f: 160, 205, 295, stride=1.5, duty=0.42, lift=0.14, lean=14)
G.arms_down(205)
for f_ in range(220, 296, 15):   # hands follow the running body
    u_ = smooth((f_ - 205) / 90); G.pos = V((1.8, 4.2)).lerp(V((-3.5, -7.5)), u_); G.yaw = 160; G.arms_down(f_, sway=0.05 * math.sin(f_ / 4))
G.pos = V((-3.5, -7.5)); G.arms_down(295); G.stand(296, pos=(-3.5, -7.5), yaw=160); G.stand(590, pos=(-3.5, -7.5), yaw=160); G.arms_down(590)
for x in (-3.5, 3.5):
    W_ = human("Guard", "Guard_S2b_%d" % (x > 0), c); hat(W_.a, A_["tricorn"], c)
    crowd_idle(W_, 175, 590, (x, 1.0), 90 if x > 0 else -90, "watch", seed=int(x))
ch = inst(A_["Chandelier_01"] if "Chandelier_01" in A_ else A_["chandelier"], c, (0, 1.5, 5.2), s=1.0)
for y_ in (-4.0, 2.5):
    tapestry(c, (-5.95, y_, 3.2), 90, tint=(0.45, 0.03, 0.05)); tapestry(c, (5.95, y_, 3.2), -90, tint=(0.04, 0.10, 0.45))
tapestry(c, (0, 7.95, 4.2), 180, w=3.0, h=3.0, tint=(0.04, 0.10, 0.45))
box("wainscotN", c, (11.9, 0.08, 1.2), (0, 7.95, 0.6), M["oak"]); box("wainscotW2", c, (0.08, 15.9, 1.2), (-5.95, 0, 0.6), M["oak"]); box("wainscotE2", c, (0.08, 15.9, 1.2), (5.95, 0, 0.6), M["oak"])
for x_ in (-1.8, 1.8): candelabra(c, (x_, 6.0), 1.5)
inst(A_["GothicCabinet_01"], c, (4.8, 6.6, 0), rz=-90, s=0.9); inst(A_["ArmChair_01"], c, (-3.0, 5.5, 0), rz=200)
for x_, y_ in ((-2.2, 7.4), (2.2, 7.4)):
    Gx = human("Guard", "Guard_S2c_%d" % (x_ > 0), c); hat(Gx.a, A_["tricorn"], c)
    crowd_idle(Gx, 175, 590, (x_, y_), 0, "watch", seed=int(x_ * 10))
for y_ in (-2.0, 3.0): picture(c, (-5.9, y_, 1.9), -90, 1.2)
light(c, 'AREA', (3, -1, 6), 900, (1, 0.85, 0.7), 5, rot=(40, 0, 30), name="key")
light(c, 'AREA', (-4, 4, 3), 500, (0.9, 0.95, 1.0), 3, rot=(70, 0, -120), name="fill")
light(c, 'AREA', (0, 0, 6.8), 2500, (1.0, 0.95, 0.88), 8, rot=(0, 0, 0), name="ceilSoft")
aim(light(c, 'SPOT', (0, 2, 6.5), 1500, (1, 0.8, 0.6), 0.3, rot=(-20, 0, 0), name="throneSpot"), (0, 6.5, 1.2))

for p in ((-5.4, -2.5, 2.0), (5.4, -2.5, 2.0), (-5.4, 2.5, 2.0), (5.4, 2.5, 2.0)): candle(c, p)
cam(185, (0.3, -1.5, 2.3), (0, 6.3, 1.6), 30)
cam(215, (0.4, -2.5, 2.4), (0, 6.3, 1.5), 32)
cam(260, (1.2, 2.2, 1.7), (0, 6.4, 1.55), 35)
cam(300, (0.6, 4.4, 1.55), (-0.05, 6.35, 1.55), 45)
cam(360, (-0.6, 4.6, 1.5), (-0.2, 6.3, 1.5), 50)
cam(420, (-1.9, 3.6, 1.45), (-0.5, 5.6, 1.3), 38)
cam(480, (-1.65, 3.85, 1.25), (-0.55, 5.4, 1.2), 45)
cam(540, (-1.55, 4.05, 1.3), (-0.6, 5.45, 1.3), 45)
cam(586, (-1.0, 4.58, 1.21), (-1.0, 5.4, 1.23), 40)
finish_set(1)

# ================================================================== S3 Street (b4)
c = S(2)
gnd = plane("ground", c, (14, 50), (0, 5, 0), M["cobble"])
for k, y in enumerate((-6, 3, 12, 21)):
    inst(A_[("htb1", "house3", "htb5", "house0")[k]], c, (-8.5, y, 0), rz=90)
    inst(A_[("house7", "htb3", "htb1", "house3")[k]], c, (8.5, y, 0), rz=-90)
inst(A_["cart"], c, (3.5, 7.5, 0), rz=80)
for p in ((3.0, 5.6), (4.2, 5.8)): inst(A_["sack"], c, (*p, 0), rz=random.uniform(0, 360))
inst(A_["Barrel_01"] if "Barrel_01" in A_ else A_["sack"], c, (-3.8, 7, 0))
S1_ = human("Guard", "Soldier_S3_a", c); hat(S1_.a, A_["tricorn"], c)
S1_.stand(588, pos=(1.0, 1.0), yaw=160);
pot = inst(A_["coffeepot_cu"], c, (0, 0, 0), name="SmashPot")
# soldier lifts the pot overhead and smashes it down
for f, up, fl in ((588, 0.0, 0), (612, 1.0, -8), (632, 1.0, -12), (645, -0.4, 35), (660, -0.5, 30), (700, 0.0, 10), (725, 0, 5)):
    S1_.stand(f, crouch=0.12 if up < 0 else 0, flex=fl)
    hz = 1.05 + 1.0 * up if up >= 0 else 0.75
    for s in "LR":
        sx = 1 if s == "L" else -1
        S1_.hand(f, s, (0.1 * sx, -0.35, hz), d=(-0.3 * sx, -0.6, 0.6 if up > 0 else -0.3), n=(-sx, 0, 0), pole=(0.5 * sx, 0.3, 1.2))
    S1_.face(f, brow=-2.5, jaw=10 if up < 0 else 4, frown=1.2)
    for s in "LR": grip(S1_.R, f, s, pose="wrap_grip")
# pot keyed in world: in hands until 645 then smash on cobbles with shards
sc.frame_set(588); bpy.context.view_layer.update()
for f in (588, 600, 612, 624, 632, 640, 645):
    sc.frame_set(f); hw = (hand_world(S1_.a, "L") + hand_world(S1_.a, "R")) / 2
    pot.matrix_world = Matrix.Translation(ROOT[2].matrix_world.inverted() @ hw + V((0, 0, -0.12)))
    pot.keyframe_insert("location", frame=f)
for f in (588, 600, 612, 624, 632, 640, 645):
    sc.frame_set(f); bpy.context.view_layer.update()
    Pw = pot.matrix_world.translation.copy() if pot.parent is None else pot.matrix_world.translation.copy()
    Pw = ROOT[2].matrix_world @ pot.location
    lat = ROOT[2].matrix_world.to_3x3() @ (Matrix.Rotation(R_(S1_.yaw), 3, 'Z') @ V((1, 0, 0)))
    for s_, sx in (("L", 1), ("R", -1)):
        grip_object(S1_.a, s_, f, pot, Pw + lat * (0.085 * sx) + V((0, 0, 0.12)), -lat * sx)
pot.hide_render = False; pot.keyframe_insert("hide_render", frame=648); pot.hide_render = True; pot.keyframe_insert("hide_render", frame=649)
ip = pot.location.copy(); ip.z = 0.0
for k in range(10):
    sh = inst(A_["coffeepot_cu"], c, ip, name="shard%d" % k); sh.scale = (0.32,) * 3
    for f, h in ((1, True), (649, False)):
        sh.hide_render = h; sh.keyframe_insert("hide_render", frame=f)
    ang = k / 10 * 6.283; vel = V((math.cos(ang), math.sin(ang), 0)) * random.uniform(0.6, 1.4)
    for f in (649, 660, 672, 690):
        t = (f - 649) / 60; sh.location = ip + vel * min(t, 0.45) + V((0, 0, max(0.0, 0.5 * t - 2.5 * t * t) if t < 0.25 else 0.0))
        sh.rotation_euler = (t * 9 * random.random(), t * 7, ang); sh.keyframe_insert("location", frame=f); sh.keyframe_insert("rotation_euler", frame=f)
# second soldier pours a sack of beans into the gutter
S2_ = human("Guard", "Soldier_S3_b", c); hat(S2_.a, A_["tricorn"], c)
for f in (588, 620, 660, 700, 725):
    S2_.stand(f, pos=(2.4, 3.2), yaw=110, flex=25, crouch=0.08)
    S2_.hand(f, "R", (-0.18, -0.45, 1.15), d=(0, -1, 0), n=(0, 0, -1)); S2_.hand(f, "L", (0.18, -0.45, 1.0), d=(0, -1, 0), n=(0, 0, 1))
    S2_.face(f, brow=-1.5, frown=0.8)
sk2 = inst(A_["sack"], c, S2_.W((0, -0.55, 0.65)), rz=0, name="PourSack"); sk2.rotation_euler = (R_(-110), 0, R_(110 + 180)); sk2.scale = (0.8,) * 3
attach(sk2, S2_.a, "wrist.R", 588, local=True)
# beans: particle emitter (falls under gravity, collides with street)
mouth = S2_.W((0.0, -0.95, 0.72))
em = gn_fall("BeanEmitter", c, [mouth + V((random.uniform(-0.05, 0.05), random.uniform(-0.05, 0.05), random.uniform(-0.03, 0.03))) for _ in range(1600)], A_["bean"], "pour", 592, 712)
for k, (x, y) in enumerate(((-2.0, 2.0), (-2.8, 3.4), (-1.6, 4.4), (-3.2, 0.6), (-2.4, 5.6))):
    b = ("Townsman", "Townswoman", "Woman", "Townsman", "Townswoman")[k]
    A = human(b, "Protest_S3_%d" % k, c)
    crowd_idle(A, 588, 725, (x, y), -70 + random.uniform(-20, 20), "jeer", seed=10 + k, phase=random.random())
light(c, 'SUN', (0, 0, 20), 3.0, (1.0, 0.92, 0.8), rot=(45, 0, -30), name="sun")
walker("Townswoman", "Walk_S3_0", c, (-1, 16, 0), (0.5, 8, 0), 588, 725, 0.6); walker("Townsman", "Walk_S3_1", c, (4.5, 14, 0), (5.0, 5, 0), 588, 725)
cam(588, (0, -8.7, 3.0), (1.2, 2.0, 1.2), 28)
cam(625, (1.6, -3.0, 1.4), (1.2, 1.5, 0.8), 30)
cam(655, (1.6, -0.6, 0.9), (2.0, 3.6, 0.9), 26)
cam(690, (-1.0, 2.5, 1.7), (-3.0, 3.5, 1.6), 28)
cam(722, (-5.3, 6.0, 2.5), (-9.0, 6.0, 2.5), 28)
finish_set(2)

# ================================================================== S4 Chamber (b5-b8)
c = S(3)
room(c, -5, 5, -5, 5, 4.2, M["planks"], M["plaster"], M["plaster"], skip=("wE",))
wall_opening(c, "x", 5.0, (-5, 5), 4.2, M["plaster"], -1.0, 1.5, 1.0, 2.8, M["oak"])
for y_ in (-3.5, 0.0, 3.5): box("beam", c, (10, 0.25, 0.3), (0, y_, 4.05), M["oak"])
box("wainscot", c, (9.9, 0.06, 1.0), (0, 4.95, 0.5), M["oak"]); box("wainscotW", c, (0.06, 9.9, 1.0), (-4.95, 0, 0.5), M["oak"])
tb = inst(A_["table"], c, (0, 0.9, 0), rz=90); tb.scale = (1.2, 1.2, 1.0)
TZ = 0.78
for x in (-0.6, 0.6): inst(A_["chair"], c, (x, 1.75, 0), rz=0)
plane("outGround", c, (30, 40), (18, -1, -3.0), M["cobble"])
for t, y in (("htb5", -9), ("house0", -1), ("htb3", 8)): inst(A_[t], c, (21, y, -3.0), rz=90)
season = plane("season", c, (60.0, 30.0), (34.0, -1.0, 8.0), simple("m_season", (0.3, 0.5, 0.25), emit=(0.35, 0.55, 0.3), ew=1.5), (90, 0, -90))
sm = season.data.materials[0].node_tree.nodes["Principled BSDF"]
for f, col in ((725, (0.35, 0.55, 0.30)), (1360, (0.45, 0.62, 0.30)), (1420, (0.75, 0.45, 0.15)), (1480, (0.9, 0.92, 0.96)), (1540, (0.45, 0.62, 0.30)), (1600, (0.75, 0.45, 0.15))):
    sm.inputs["Emission Color"].default_value = (*col, 1); sm.inputs["Emission Color"].keyframe_insert("default_value", frame=f)
    sm.inputs["Base Color"].default_value = (*col, 1); sm.inputs["Base Color"].keyframe_insert("default_value", frame=f)
sunwin = light(c, 'AREA', (6.2, -1.0, 2.6), 1600, (1, 0.9, 0.75), 2.0, rot=(0, -70, 0), name="windowSun")
for f, e in ((725, 1600), (1330, 1600), (1360, 200), (1390, 1700), (1420, 150), (1450, 1600), (1480, 250), (1510, 1500), (1540, 200), (1570, 1600), (1650, 1600)):
    sunwin.data.energy = e; sunwin.data.keyframe_insert("energy", frame=f)
light(c, 'AREA', (-3, -3, 3.8), 1600, (0.95, 0.95, 1.0), 4, rot=(50, 0, -140), name="fill")
light(c, 'AREA', (0, -2, 4.0), 1200, (1.0, 0.95, 0.88), 5, rot=(0, 0, 0), name="ceilSoft")
light(c, 'AREA', (0, 4.5, 3.6), 500, (1.0, 0.85, 0.7), 3, rot=(-50, 0, 0), name="rim")
light(c, 'SPOT', (0, -1, 3.9), 1500, (1, 0.8, 0.6), 0.2, rot=(30, 0, 0), name="tableSpot")
BURN = [(725, 1.0), (1300, 1.0), (1640, 0.15)]
for p in ((-0.35, 0.75, TZ), (0.35, 0.75, TZ), (2.6, -2.4, TZ), (3.4, -2.4, TZ)): candle(c, p, burn=BURN)
# twins: young until 1480, old after (swap during the bright window flash while camera is on the doctors)
TW = {}
for k, (b, x) in enumerate((("TwinA", -0.6), ("TwinB", 0.6))):
    for age in ("", "_old"):
        nm = b + age
        A = human(nm, nm + "_S4", c); A.pos = V((x, 1.75)); A.yaw = 180 * 0 + 0
        TW[nm] = A
# coffee side (A, left x<0) and tea side (B)
cupA = inst(A_["cup"], c, (-0.62, 1.05, TZ), name="CupA")
bpy.ops.mesh.primitive_cylinder_add(radius=0.038, depth=0.002, location=(0, 0, 0.064)); cfa = bpy.context.active_object; link(cfa, c); setmat(cfa, M["coffee"])
cfa.parent = cupA
for k in range(3): inst(A_["silverpot"], c, (-1.25 + k * 0.22, 0.65, TZ), rz=200)
cupB = inst(A_["cup"], c, (0.62, 1.05, TZ), name="CupB"); cupB.scale = (0.85, 0.85, 0.8)
bpy.ops.mesh.primitive_cylinder_add(radius=0.038, depth=0.002, location=(0, 0, 0.064)); cfb = bpy.context.active_object; link(cfb, c); setmat(cfb, M["tea"]); cfb.parent = cupB
for k in range(3): inst(A_["teapot"] if "teapot" in A_ else A_["coffeepot_porc"], c, (0.95 + k * 0.2, 0.65, TZ), rz=160)
for k in range(5): inst(A_["cup"], c, (-1.05 - (k % 3) * 0.09, 1.15 - (k // 3) * 0.1, TZ), name="emptyCup")
def drink(A, s, cup, f0, f1, per=80, old=False):
    """sip cycle: reach cup, lift to lips, sip, set down"""
    sx = 1 if s == "L" else -1
    rest_cup = cup.location.copy()
    f = f0
    while f < f1:
        A.sit(f, flex=12, head=(8, 0)); A.hand(f, s, (0.09 * sx, -0.6, TZ + 0.08), d=(0, -1, 0.1), n=(-sx, 0, 0), g=0.8)
        A.face(f, brow=0.3, smile=0.4 if not old else 0.0)
        A.sit(f + per * 0.22, flex=12, head=(8, 0)); A.hand(f + per * 0.22, s, (0.09 * sx, -0.6, TZ + 0.08), d=(0, -1, 0.1), n=(-sx, 0, 0), g=0.8)
        A.sit(f + per * 0.35, flex=4, head=(-12, 0)); A.hand(f + per * 0.35, s, (0.04 * sx, -0.27, 1.04), d=(-0.25 * sx, -0.3, 1.0), n=(-sx, 0, 0), pole=(0.45 * sx, 0.1, 0.9), g=0.8)
        A.face(f + per * 0.35, lids=0.6, jaw=4)
        A.sit(f + per * 0.65, flex=4, head=(-14, 0)); A.hand(f + per * 0.65, s, (0.04 * sx, -0.26, 1.05), d=(-0.25 * sx, -0.3, 1.0), n=(-sx, 0, 0), pole=(0.45 * sx, 0.1, 0.9), g=0.8)
        A.face(f + per * 0.65, lids=0.7, smile=0.6)
        f += per
    A.sit(f1, flex=12, head=(8, 0)); A.hand(f1, s, (0.09 * sx, -0.6, TZ + 0.08), d=(0, -1, 0.1), n=(-sx, 0, 0), g=0.8)
def rest_hands(A, f):
    for s in "LR":
        sx = 1 if s == "L" else -1
        A.hand(f, s, (0.18 * sx, -0.5, TZ + 0.075), d=(-0.45 * sx, -1, 0.0), n=(0.35 * sx, 0, -1), pole=(0.5 * sx, 0.3, 0.9), g=0.7)
        grip(A.R, f, s, 0.7, 0.4)
for nm, A in TW.items():
    old = "old" in nm
    if old:
        A.sit(1300, flex=10); rest_hands(A, 1300); A.face(1300, brow=0.2)
    else:
        A.sit(725, flex=8, head=(5, 8 if "A" in nm else -8)); rest_hands(A, 725); A.face(725, brow=1.5, lids=-0.2)
    for fv in ((1, True), (725, old), (1480, not old)):
        pass
# drinks
drink(TW["TwinA"], "R", cupA, 830, 1290, per=92)
TW["TwinB"].sit(830, flex=8); rest_hands(TW["TwinB"], 830); TW["TwinB"].face(830, brow=1.0, frown=0.3)
drink(TW["TwinB"], "L", cupB, 1105, 1290, per=96)
rest_hands(TW["TwinA"], 1300); rest_hands(TW["TwinB"], 1300); TW["TwinA"].sit(1300, flex=10); TW["TwinB"].sit(1300, flex=10)
drink(TW["TwinA_old"], "R", cupA, 1490, 1650, per=110, old=True)
TW["TwinB_old"].sit(1490, flex=12); rest_hands(TW["TwinB_old"], 1490)
# cups follow the drinking hand
for cup, A, s, f0, f1 in ((cupA, TW["TwinA"], "R", 830, 1290), (cupB, TW["TwinB"], "L", 1105, 1290), (cupA, TW["TwinA_old"], "R", 1490, 1650)):
    inv = ROOT[3].matrix_world.inverted()
    for f in range(f0, f1 + 1, 6):
        hw = inv @ hold_point(A.a, s, f)
        cup.location = hw; cup.keyframe_insert("location", frame=f)
    sc.frame_set(f1 + 6); cup.location = V((A.pos.x, 1.05, TZ)); cup.keyframe_insert("location", frame=f1 + 8)
# servants pour into the resting cup between sips (hand over the cup, pot tipped, coffee/tea stream)
POURS = {0: (TW["TwinA"], "R", [830, 1014, 1198], "silverpot", "Woman", (-1.40, 1.30), -70, M["coffee"]),
         1: (TW["TwinB"], "L", [1105, 1201], "teapot", "Townswoman", (1.40, 1.30), 70, M["tea"])}
for k, (TA, ts, pours, tmpl, b, spos, syaw, liq) in POURS.items():
    A = human(b, "Servant_S4_%d" % k, c); hs = "R" if k == 0 else "L"; os_ = "L" if k == 0 else "R"; sxh = -1 if hs == "R" else 1
    pot = inst(A_[tmpl], c, (0, 0, 0), name="ServPot%d" % k)
    A.pos = V(spos); A.yaw = syaw
    cup_rest = TA.W((0.09 * (1 if ts == "L" else -1), -0.6, 0.0)); cup_rest = V((cup_rest.x, cup_rest.y, TZ))
    sp3 = V((spos[0], spos[1], TZ))
    keyf = sorted(set(list(range(705, 1631, 30)) + [p_ + o_ for p_ in pours for o_ in (-34, -14, -4, 10, 18, 40)]))
    for f in keyf:
        near = min(pours, key=lambda p_: abs(f - p_)); dt = f - near
        u = math.sin(f / 45 + k)
        if -14 <= dt <= 18:
            tip = 1.0 if -4 <= dt <= 10 else 0.3
            A.stand(f, flex=22, twist=-8 * sxh, head=(22, 0))
            PP = cup_rest + (sp3 - cup_rest).normalized() * 0.10 + V((0, 0, 0.30))
            dd = (cup_rest - sp3).normalized() + V((0, 0, -0.35 - 0.6 * tip))
            hand_at(A, f, hs, PP, d=tuple(dd), n=(0, 0, 1), g=0.9)
            A.hand(f, os_, (0.35 * -sxh, -0.11, 0.9), d=(0, 0, -1)); A.face(f, brow=0.8, smile=0.4, lids=0.2)
        elif -34 <= dt < -14 or 18 < dt <= 40:
            A.stand(f, flex=12, head=(12, 0)); A.hand(f, hs, (0.2 * sxh, -0.4, 1.05), d=(0, -1, 0), n=(-sxh, 0, 0), g=0.9)
            A.hand(f, os_, (0.35 * -sxh, -0.11, 0.9), d=(0, 0, -1)); A.face(f, brow=0.5, smile=0.3)
        else:
            A.stand(f, flex=5, twist=5 * u, head=(5, 10 * u)); A.hand(f, hs, (0.24 * sxh, -0.25, 0.98), d=(0, -1, 0), n=(-sxh, 0, 0), g=0.9)
            A.hand(f, os_, (0.35 * -sxh, -0.11, 0.9), d=(0, 0, -1)); A.face(f, brow=0.5, smile=0.3)
    # v009: the pot is keyed in set-local space with its handle in the hand, spout toward the cup (tilted while pouring),
    # then grip_object closes the hand on the handle (pot-local handle point / spout direction measured from the models)
    hl, spl = {0: (V((0, 0.075, 0.17)), V((0, -1, 0))), 1: (V((0, -0.135, 0.12)), V((0, 1, 0)))}[k]
    Ri = ROOT[3].matrix_world.inverted()
    for f in keyf:
        near = min(pours, key=lambda p_: abs(f - p_)); dt = f - near
        tilt = (1.0 if -4 <= dt <= 10 else 0.3) if -14 <= dt <= 18 else 0.0
        sc.frame_set(f); bpy.context.view_layer.update(); ht = Ri @ hand_world(A.a, hs)
        toc = cup_rest - ht if tilt > 0 else (cup_rest - sp3); toc.z = 0; toc.normalize()
        Rz = Matrix.Rotation(math.atan2(toc.y, toc.x) - math.atan2(spl.y, spl.x), 3, 'Z'); ax_ = (Rz @ spl).cross(V((0, 0, 1))).normalized()
        Rm = Matrix.Rotation(-R_(55) * tilt, 3, ax_) @ Rz
        pot.matrix_world = Matrix.Translation(ht - Rm @ hl) @ Rm.to_4x4()
        pot.keyframe_insert("location", frame=f); pot.keyframe_insert("rotation_euler", frame=f)
    for f in keyf:
        sc.frame_set(f); bpy.context.view_layer.update()
        PM = ROOT[3].matrix_world @ pot.matrix_world
        grip_object(A.a, hs, f, pot, PM @ hl, PM.to_3x3() @ spl)
    for p_ in pours:   # liquid stream from the spout into the cup during each pour
        bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=0.006, depth=0.2, location=tuple(cup_rest + V((0, 0, 0.17))))
        st_ = bpy.context.active_object; st_.name = "pourStream%d_%d" % (k, p_); link(st_, c); setmat(st_, liq)
        for ff, h in ((1, True), (p_ - 2, False), (p_ + 12, True)):
            REKEY.append((st_, ff, h))
for k, x in enumerate((-1.4, 1.4)):
    A = human("Guard", "Guard_S4_%d" % k, c); hat(A.a, A_["tricorn"], c)
    crowd_idle(A, 725, 1650, (x, 3.4), 0, "watch", seed=40 + k)
# doctors at their desk, observing, writing
desk = inst(A_["table"], c, (3.0, -2.45, 0), rz=90); desk.scale = (0.75, 0.8, 1.0)
inst(A_["GothicCabinet_01"], c, (4.3, -4.4, 0), rz=0, s=0.9); inst(A_["GothicCabinet_01"], c, (-4.3, 3.0, 0), rz=-90, s=0.9)
tapestry(c, (-4.95, -1.5, 2.4), 90, w=1.8, h=2.0, tint=(0.04, 0.10, 0.45)); tapestry(c, (0.0, 4.95, 2.6), 180, w=2.2, h=1.8, tint=(0.45, 0.03, 0.05))
picture(c, (2.6, -4.93, 2.2), 0, 1.1); picture(c, (-2.5, 4.93, 2.3), 180, 1.0)
rug(c, (0, 1.2, 0), (4.0, 2.6)); rug(c, (3.0, -2.6, 0), (2.4, 1.8))
candelabra(c, (-3.8, -3.8), 1.3); candelabra(c, (1.8, 3.9), 1.3)
for k_, (x_, y_) in enumerate(((-3.8, 0.5), (4.2, 1.8))):
    Gy = human("Guard", "Guard_S4b_%d" % k_, c); hat(Gy.a, A_["tricorn"], c); crowd_idle(Gy, 725, 1650, (x_, y_), 90 if x_ < 0 else -90, "watch", seed=60 + k_)
for k, (b, x) in enumerate((("Doctor1", 2.35), ("Doctor2", 3.65))):
    A = human(b, b + "_S4", c); A.pos = V((x, -3.05)); A.yaw = 180 - 15 + 30 * k
    inst(A_["chair"], c, (x, -3.15, 0), rz=180)
    f = 725; i = 0
    while f <= 1650:
        A.sit(f, flex=16 if i % 2 else 8, head=(10 if i % 2 else -4, 25 if i % 2 == 0 else 0))
        A.hand(f, "R", (-0.12, -0.42, TZ + 0.07 + 0.02 * (i % 2)), d=(0.3, -1, 0.0), n=(0, 0, -1))
        A.hand(f, "L", (0.2, -0.4, TZ + 0.075), d=(-0.45, -1, 0.0), n=(0.35, 0, -1)); grip(A.R, f, "L", 0.7, 0.4)
        A.face(f, brow=-0.8 if i % 2 else 0.6, lids=0.3 if i % 2 else 0.0)
        f += 70; i += 1
    q = inst(A_["quill"], c, (x - 0.12, -2.7, TZ + 0.1), name="quill%d" % k); q.rotation_euler = (R_(60), 0, R_(20))
    attach(q, A.a, "wrist.R", 725, local=True)
    bk = inst(A_["book"], c, (x, -2.6, TZ), rz=180, name="ledger%d" % k)
    bk.data = bk.data.copy(); setmat(bk, pbr("m_ledger", "brown_leather", 4, tint=(0.45, 0.22, 0.12), rough_mul=0.8))   # plain cover: the model's spine has lettering
# visibility of young/old twins inside the chamber
for nm, A in TW.items():
    old = "old" in nm
    objs = [A.a] + list(A.a.children)
    for o in objs:
        for f, h in ((725, old), (1440, not old)):
            REKEY.append((o, f, h))
cam(725, (0, -4.9, 2.0), (0, 1.5, 1.2), 28)
cam(790, (-1.2, -2.0, 1.5), (0, 1.6, 1.15), 30)
cam(860, (-1.6, -0.4, 1.3), (-0.6, 1.55, 1.2), 38)
cam(920, (-0.95, 0.55, 1.02), (-0.62, 1.1, 0.95), 45)
cam(980, (-2.2, 0.0, 1.5), (-0.6, 1.6, 1.2), 35)
cam(1040, (-1.1, -0.3, 1.25), (-0.6, 1.7, 1.25), 42)
cam(1099, (0.3, -1.0, 1.35), (0.6, 1.6, 1.2), 38)
cam(1160, (0.85, 0.5, 1.0), (0.6, 1.05, 0.9), 50)
cam(1230, (1.7, 0.2, 1.4), (0.6, 1.7, 1.25), 38)
cam(1250, (1.9, 0.1, 1.55), (1.45, -0.6, 1.3), 32)
cam(1275, (1.8, -0.3, 1.6), (2.6, -2.6, 1.15), 32)
cam(1297, (1.6, -0.9, 1.6), (3.0, -2.7, 1.2), 32)
cam(1360, (1.6, -1.6, 1.9), (3.0, -2.8, 1.0), 32)
cam(1420, (3.0, -0.7, 1.7), (3.0, -2.7, 1.25), 34)
cam(1440, (3.4, -0.9, 1.7), (3.0, -2.8, 1.2), 32)
cam(1462, (3.8, -1.3, 1.7), (2.4, -2.2, 1.25), 30)
cam(1480, (4.2, -1.8, 1.8), (2.5, 0.2, 1.2), 28)
cam(1545, (2.6, 0.2, 1.5), (0.0, 1.6, 1.2), 30)
cam(1590, (2.9, 0.1, 1.6), (0.3, 1.6, 1.2), 30)
cam(1612, (3.9, -0.7, 1.8), (0.3, 1.6, 1.2), 30)
cam(1648, (5.15, -1.0, 1.9), (8.0, -1.0, 1.9), 28)
finish_set(3)

# ================================================================== S5 Church in snow (b9)
c = S(4)
plane("ground", c, 80, (0, 0, 0), M["snow"])
chg = inst(A_["church"], c, (0, 22, 0), rz=180)
_cm = A_["church"].data
for _m in (M["roof"], M["castle"]):
    _bs = _m.node_tree.nodes["Principled BSDF"]
    if _bs.inputs["Base Color"].links: _m.node_tree.links.new(_bs.inputs["Base Color"].links[0].from_socket, _bs.inputs["Emission Color"])
    _bs.inputs["Emission Strength"].default_value = 0.6
_cm.materials.append(M["roof"]); _cm.materials.append(M["castle"]); _iroof, _istone = len(_cm.materials) - 2, len(_cm.materials) - 1
for _p in _cm.polygons:
    _mn = _cm.materials[_p.material_index].name if _cm.materials[_p.material_index] else ""
    if "Roof" in _mn: _p.material_index = _iroof
    elif "BrickOldRounded" in _mn or "concrete" in _mn: _p.material_index = _istone
for m in A_["church"].data.materials:   # brighten the dark scan materials (clean animated look)
    if not m or not m.node_tree: continue
    bs_ = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if not bs_: continue
    lk = bs_.inputs["Base Color"].links
    hs = m.node_tree.nodes.new("ShaderNodeHueSaturation"); hs.inputs["Value"].default_value = 2.4; hs.inputs["Saturation"].default_value = 1.1
    lift = m.node_tree.nodes.new("ShaderNodeMix"); lift.data_type = 'RGBA'; lift.inputs[0].default_value = 0.3; lift.inputs["B"].default_value = (0.55, 0.5, 0.45, 1)
    if lk:
        src_ = lk[0].from_socket; m.node_tree.links.new(src_, hs.inputs["Color"])
    else:
        hs.inputs["Color"].default_value = bs_.inputs["Base Color"].default_value
    m.node_tree.links.new(hs.outputs[0], lift.inputs["A"]); m.node_tree.links.new(lift.outputs["Result"], bs_.inputs["Base Color"])
    m.use_backface_culling = False
    if hasattr(m, "use_backface_culling_shadow"): m.use_backface_culling_shadow = False
    if hasattr(m, "surface_render_method"): m.surface_render_method = 'DITHERED'
    for lk_ in list(bs_.inputs["Normal"].links): m.node_tree.links.remove(lk_)   # scan normal maps render black after the JPEG shrink
    for k_ in ("Metallic", "Alpha", "Transmission Weight"):
        for lk_ in list(bs_.inputs[k_].links): m.node_tree.links.remove(lk_)
    bs_.inputs["Metallic"].default_value = 0.0; bs_.inputs["Alpha"].default_value = 1.0
    if any(k in m.name for k in ("Roof", "Wood049", "concrete", "default")):   # roofing scans render near-black: clean slate colour
        for lk_ in list(bs_.inputs["Base Color"].links): m.node_tree.links.remove(lk_)
        bs_.inputs["Base Color"].default_value = (0.42, 0.45, 0.52, 1); bs_.inputs["Roughness"].default_value = 0.6
for t, p, rz in (("house3", (-16, 4, 0), 90), ("htb1", (16, 2, 0), -90)): inst(A_[t], c, p, rz=rz)
# coffins: hexagonal box built procedurally with dark wood + bevel
def coffin(name):
    me = bpy.data.meshes.new(name)
    L_, W1, W2, H = 2.0, 0.35, 0.6, 0.55
    prof = [(-L_ / 2, -W1 / 2), (L_ * 0.18, -W2 / 2), (L_ / 2, -W1 * 0.45), (L_ / 2, W1 * 0.45), (L_ * 0.18, W2 / 2), (-L_ / 2, W1 / 2)]
    vs = [(x, y, 0) for x, y in prof] + [(x, y, H) for x, y in prof]; n = len(prof)
    fs = [tuple(range(n))[::-1], tuple(range(n, 2 * n))] + [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    me.from_pydata(vs, [], fs); o = bpy.data.objects.new(name, me); c.objects.link(o)
    bv = o.modifiers.new("bev", 'BEVEL'); bv.width = 0.02; bv.segments = 3
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.uv.cube_project(cube_size=1.0); bpy.ops.object.mode_set(mode='OBJECT')
    setmat(o, M["planks"]); return o
GZ[0] = 0.0
for ci, x in enumerate((-1.3, 1.3)):
    cf = coffin("coffin%d" % ci)
    y0, y1 = 9.0 + ci * 1.5, -6.0 + ci * 1.5
    path = lambda f, y0=y0, y1=y1: V((0, y0 + (y1 - y0) * (f - 1650) / 222, 0))
    for f in range(1650, 1873, 6):
        p = path(f); cf.location = V((x, p.y + 0.0, 0.72)); cf.rotation_euler = (0, 0, R_(90)); cf.keyframe_insert("location", frame=f)
    for k, (dx, dy) in enumerate(((-0.55, -0.6), (0.55, -0.6), (-0.55, 0.6), (0.55, 0.6))):
        A = human(("Townsman", "Guard", "Townsman", "Guard")[k], "Bearer_S5_%d_%d" % (ci, k), c)
        A.H.walk(lambda f, x=x, dx=dx, dy=dy, path=path: V((x + dx, path(f).y + dy, 0)), lambda f: 0, 1650, 1872, stride=0.6, duty=0.6, lift=0.06, lean=3)
        s_in = "R" if dx > 0 else "L"; s_out = "L" if dx > 0 else "R"
        for f in range(1650, 1873, 12):
            yy = path(f).y + dy
            A.pos = V((x + dx, yy)); A.yaw = 0
            sx = 1 if s_in == "L" else -1
            A.hand(f, s_in, (0.25 * sx, -0.04, 0.9), d=(0.15 * sx, -0.1, -1), n=(sx, 0, 0), pole=(0.1 * sx, 0.45, 1.0))
            A.hand(f, s_out, (-0.35 * sx, -0.11, 0.9), d=(0, 0, -1), n=(sx, 0, 0), pole=(-0.3 * sx, 0.6, 1.1))
            A.face(f, brow=0.8, lids=0.35, frown=0.6); grip(A.R, f, s_in, 0.9)
for k, b in enumerate(("TwinA_old", "TwinB_old")):
    A = human(b, b + "_S5", c)
    A.H.walk(lambda f, k=k: V((-0.5 + k * 1.0, 12.5 - 15.0 * (f - 1650) / 222, 0)), lambda f: 0, 1650, 1872, stride=0.6, duty=0.6, lift=0.06, lean=4)
    for f in range(1630, 1873, 12):
        A.pos = V((-0.5 + k * 1.0, 12.5 - 15.0 * (f - 1650) / 222)); A.yaw = 0   # hands follow the walking body
        A.arms_down(f, sway=0.02 * math.sin(f / 9 + k)); A.face(f, brow=1.6, lids=0.4, frown=1.0)
# falling snow
bpy.ops.mesh.primitive_ico_sphere_add(radius=0.012, subdivisions=1); flake = bpy.context.active_object; flake.name = "flake"; link(flake, LIBC); setmat(flake, simple("m_flake", (1, 1, 1), rough=0.6))
sn = gn_fall("SnowEmit", c, [(random.uniform(-12, 12), random.uniform(-18, 12), random.uniform(0, 14)) for _ in range(7000)], flake, "snow", H=14.0, speed=0.02)
light(c, 'SUN', (0, 0, 20), 4.5, (1.0, 0.88, 0.75), rot=(60, 0, 15), name="sun")
for x_ in (-9, -4, 4, 9):
    light(c, 'POINT', (x_, 11.0, 4.0), 900, (1.0, 0.65, 0.3), 1.0, name="churchWin")
aim(light(c, 'AREA', (0, -2, 14), 20000, (0.8, 0.85, 1.0), 16, name="moonFill"), (0, 12, 6))
aim(light(c, 'AREA', (0, 2, 4), 12000, (1.0, 0.85, 0.7), 14, name="facadeFill"), (0, 12, 10))
for x_ in (-10, 0, 10):   # warm interior glow: the model's roof has open gaps that otherwise show a black interior
    light(c, 'POINT', (x_, 22, 12), 60000, (1.0, 0.8, 0.6), 3.0, name="churchInterior")
cam(1650, (0, -15.5, 2.5), (0, 4.0, 1.6), 26)
cam(1700, (-3.0, -8.0, 2.2), (-0.5, 2.0, 1.4), 30)
cam(1760, (-3.2, -2.5, 1.6), (0.0, 0.5, 1.4), 32)
cam(1810, (-2.6, -1.0, 1.75), (-0.5, 2.0, 1.65), 40)
cam(1845, (0, 1.0, 4.5), (0, 8.0, 7.0), 28)
cam(1870, (0, 7.3, 7.0), (0, 14.0, 7.0), 28)
finish_set(4)

# ================================================================== S6 Masked ball (b10)
c = S(5)
room(c, -8, 8, -10.5, 10, 8, M["marble"], M["paleblue"], M["plaster"], skip=("wW",))
wall_opening(c, "x", -8.0, (-10.5, 10), 8, M["paleblue"], 0.0, 1.8, 0.0, 2.9, M["gold"])
plane("corridor", c, (6, 4), (-12.0, 0, 2.0), M["oak"], (90, 0, 90))
for y0_, y1_ in ((-10.4, -0.95), (0.95, 9.9)):
    box("wainscotBW", c, (0.08, y1_ - y0_, 1.2), (-7.95, (y0_ + y1_) / 2, 0.6), M["oak"])
for y_ in (-4.5, 4.5): picture(c, (-7.92, y_, 2.6), 90, 1.4)
tapestry(c, (-7.93, -8.0, 4.0), 90, w=1.6, h=2.6, tint=(0.45, 0.03, 0.05)); tapestry(c, (-7.93, 8.0, 4.0), 90, w=1.6, h=2.6, tint=(0.04, 0.10, 0.45))
for y_ in (-2.0, 2.0): candelabra(c, (-7.4, y_), 1.5)
rug(c, (-5.0, 0, 0), (3.0, 4.0))
plane("corrFloor", c, (5, 3), (-10.5, 0, 0.0), M["planks"])
light(c, 'POINT', (-10.5, 0.8, 2.2), 60, (1, 0.6, 0.3), 0.05, name="corrLamp")
for y in (-5, 1, 7):
    ch = inst(A_["chandelier"], c, (0, y, 5.8), s=1.0)
    for a in range(6):
        light(c, 'POINT', (math.cos(a) * 0.6, y + math.sin(a) * 0.6, 5.9), 40, (1, 0.65, 0.3), 0.05, name="chandL")
for x in (-7.5, 7.5):
    for y in (-7, -2, 3, 8):
        box("pillar", c, (0.8, 0.8, 8), (x, y, 4), M["marble"])
K = human("King", "King_S6", c)
MF = human("Doctor1", "Masked_S6", c)
mk = hat(MF.a, A_["mask"], c, dz=-0.05, dy=-0.1)
K.pos = V((0.5, 2.5)); K.yaw = 10
for f, ph in ((1872, 0), (1900, 0), (1909, 1), (1916, 1.5), (1925, 2), (1936, 2.5), (1948, 3), (2004, 3)):
    if ph == 1.5:   # knees give way
        K.stand(f, crouch=0.18, flex=14, side=6, lean=8, head=(10, 5)); K.face(f, brow=2.5, lids=0.3, jaw=16)
        K.hand(f, "R", (-0.1, -0.38, 1.28), d=(0.5, 0.1, 0.3), n=(0, 1, 0), g=0.6); K.hand(f, "L", (0.36, -0.12, 0.85), d=(0.15, -0.1, -1), g=0.4)
    elif ph == 2.5:  # on one knee, folding sideways
        K.stand(f, crouch=0.62, flex=40, side=25, lean=35, head=(25, 15)); K.face(f, brow=2.0, lids=0.7, jaw=10)
        K.hand(f, "R", (-0.45, -0.3, 0.25), d=(-0.2, -0.4, -1), n=(0, 0, -1), g=0.25); K.hand(f, "L", (0.45, -0.15, 0.22), d=(0.2, -0.3, -1), n=(0, 0, -1), g=0.25)
    elif ph < 2:
        K.stand(f, flex=3, head=(0, -10)); K.arms_down(f); K.face(f, smile=0.6 if ph == 0 else 0, brow=2.5 if ph else 0, jaw=14 if ph else 0)
    elif ph == 2:
        K.stand(f, crouch=0.45, flex=35, side=15, lean=20, head=(20, 10)); K.face(f, brow=2.5, lids=0.5, jaw=16)
        K.hand(f, "R", (-0.42, -0.28, 0.5), d=(-0.2, -0.4, -1), n=(0, 0, -1), g=0.25); K.hand(f, "L", (0.42, -0.24, 0.45), d=(0.2, -0.4, -1), n=(0, 0, -1), g=0.25)   # reaching out to break the fall
    else:   # collapsed: lying on the floor on his side
        K.H.key_root(f, V((0.5, 2.5 + 0.6, 0.17)), yaw=10, flex=-85, side=10)
        K.H.key_spine(f, flex=-6, head=(-10, 20))
        for s in "LR":
            sx = 1 if s == "L" else -1
            K.H.key_foot(s, f, K.W((0.15 * sx, 1.0 + 0.6, 0)).to_2d(), 10, lift=-0.02, pitch=-80)
        sc.frame_set(f); bpy.context.view_layer.update()
        shR, shL = K.a.pose.bones["upperarm01.R"].head.copy(), K.a.pose.bones["upperarm01.L"].head.copy()
        ax = (K.a.pose.bones["head"].head - K.a.pose.bones["root"].head); ax.z = 0; ax.normalize()
        lat = (shR - shL); lat.z = 0; lat.normalize()
        for s_, sh, sg in (("R", shR, 1), ("L", shL, -1)):   # palms flat on the floor beside the shoulders, arms out from the body
            hp = V((sh.x, sh.y, 0.05)) + lat * sg * 0.42 - ax * 0.15
            K.H.key_hand(s_, f, hp, (lat * sg - ax * 0.3).normalized(), V((0, 0, -1)), pole=V((sh.x, sh.y, 0.6)) + lat * sg * 0.3)
            grip(K.R, f, s_, pose="flat_palm")
        K.face(f, lids=1.0, jaw=6)
MF.pos = V((1.2, 4.2)); MF.yaw = 180 + 15
for f, ph in ((1872, 0), (1895, 1), (1905, 1), (1925, 0), (2004, 0)):
    MF.stand(f, flex=4 if ph else 0)
    MF.hand(f, "R", (-0.15, -0.55, 1.35) if ph else (-0.35, -0.11, 0.9), d=(0, -1, 0) if ph else (0, 0, -1), n=(1, 0, 0)); grip(MF.R, f, "R", pose="power_fist" if ph else "relaxed")
    MF.hand(f, "L", (0.35, -0.11, 0.9), d=(0, 0, -1))
# muzzle flash at 1907 (light + glow puff) from in front of the masked figure's hand; no weapon detail
fl = light(c, 'POINT', MF.W((-0.15, -0.75, 1.36)), 0, (1, 0.75, 0.4), 0.05, name="flash")
for f, e in ((1904, 0), (1907, 6000), (1910, 800), (1916, 0)):
    fl.data.energy = e; fl.data.keyframe_insert("energy", frame=f)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.25, location=tuple(MF.W((-0.15, -0.8, 1.36)))); puff = bpy.context.active_object; puff.name = "smokePuff"; link(puff, c)
pm = steam_mat("m_puff", 0.0, (0.6, 0.6, 0.62)); setmat(puff, pm); pdn = pm.node_tree.nodes["Dens"]
for f, v, s in ((1905, 0, 0.2), (1908, 3, 0.35), (1940, 0.8, 1.2), (1990, 0, 1.8)):
    pdn.outputs[0].default_value = v; pdn.outputs[0].keyframe_insert("default_value", frame=f); puff.scale = (s,) * 3; puff.keyframe_insert("scale", frame=f)
# dancers: three couples turning slowly, facing each other with joined raised hands; they scatter at the shot
SHOT = 1912
for pi, (cx, cy0) in enumerate(((-1.5, -3.2), (1.7, -2.6), (-1.6, 0.6))):
    for side in (0, 1):
        k = pi * 2 + side
        b = ("Townsman", "Woman", "Guard", "Townswoman", "Townsman", "Woman")[k]
        A = human(b, "Dancer_S6_%d" % k, c)
        ang0 = pi * 1.3 + side * math.pi
        def pos_(f, cx=cx, cy0=cy0, ang0=ang0):
            a = ang0 + (min(f, SHOT) - 1850) / 70.0
            return V((cx + 0.38 * math.cos(a), cy0 + 0.38 * math.sin(a), 0))
        def dpath(f, pos_=pos_):
            if f <= SHOT: return pos_(f)
            p0 = pos_(SHOT); dirv = (p0 - V((0.5, 2.5, 0))); dirv.z = 0; dirv.normalize()
            return p0 + dirv * 1.7 * smooth((f - SHOT - 4) / 70)
        def dyaw(f, cx=cx, cy0=cy0, pos_=pos_):
            p = pos_(min(f, SHOT))
            d = (V((cx, cy0, 0)) - p) if f <= SHOT + 4 else (p - V((0.5, 2.5, 0)))
            return math.degrees(math.atan2(-d.x, d.y))
        A.H.walk(dpath, dyaw, 1850, 1985, stride=0.5, duty=0.62, lift=0.06, lean=3)
        for f in range(1850, 1986, 8):
            A.pos = dpath(f).to_2d(); A.yaw = dyaw(f)
            if f < SHOT + 3:
                a = ang0 + (f - 1850) / 70.0; c_ = V((cx, cy0, 0))
                hs = "R" if side == 0 else "L"; os_ = "L" if side == 0 else "R"; sxh = -1 if hs == "R" else 1
                mid = c_ + V((0, 0, 1.42)) + V((math.cos(a + math.pi / 2), math.sin(a + math.pi / 2), 0)) * 0.12 * (1 if side == 0 else -1) * -1
                hand_at(A, f, hs, mid, d=(0, 0, 1), n=tuple((c_ - pos_(f)).normalized())); grip(A.R, f, hs, pose="wrap_grip")
                A.hand(f, os_, (0.18 * -sxh, -0.18, 1.05), d=(0.3 * sxh, -1, 0.1), n=(0, 0, -1), g=0.4)
                A.face(f, smile=0.9, brow=0.5)
            else:
                A.hand(f, "R", (-0.22, -0.25, 1.45), d=(0, -0.2, 1), n=(0, -1, 0), g=0.4); A.hand(f, "L", (0.22, -0.25, 1.4), d=(0, -0.2, 1), n=(0, -1, 0), g=0.4)
                A.face(f, brow=2.5, jaw=16, lids=-0.3)
        hat(A.a, A_["mask"], c, dz=-0.05, dy=-0.1)
light(c, 'AREA', (4, -4, 7), 1400, (1, 0.8, 0.6), 6, rot=(35, 0, 40), name="key")
light(c, 'AREA', (-5, 6, 4), 400, (0.8, 0.85, 1.0), 4, rot=(70, 0, -140), name="rim")
light(c, 'AREA', (0, 0, 7.8), 3000, (1.0, 0.93, 0.85), 10, rot=(0, 0, 0), name="ceilSoft")
cam(1872, (0, -9.8, 5.2), (0, 2.0, 3.0), 28)
cam(1890, (0.3, -1.4, 2.0), (0.6, 2.8, 1.5), 32)
cam(1905, (2.2, 6.0, 1.75), (0.5, 2.4, 1.5), 32)
cam(1930, (2.6, 4.8, 1.1), (0.5, 2.6, 0.7), 30)
cam(1960, (-1.7, 4.4, 0.9), (0.5, 2.9, 0.3), 28)
cam(1985, (-5.5, 1.5, 1.6), (-9.0, 0.0, 1.8), 28)
cam(2002, (-8.0, 0.0, 1.8), (-11.0, 0.0, 1.8), 28)
finish_set(5)

# ================================================================== S7 Bedroom (b11, b12)
c = S(6)
room(c, -4.5, 4.5, -4.5, 4.5, 3.5, M["planks"], M["plaster"], M["plaster"], skip=("wE",))
wall_opening(c, "x", 4.5, (-4.5, 4.5), 3.5, M["plaster"], -1.0, 1.4, 0.9, 2.6, M["oak"])
plane("outside", c, (60, 30), (34.0, -1.0, 8.0), simple("m_out", (0.75, 0.82, 0.9), emit=(0.85, 0.9, 1.0), ew=1.2), (90, 0, -90))
plane("outGround", c, (30, 40), (18, -1, -3.0), M["cobble"])
for t, y in (("house3", -8), ("htb1", 0), ("house7", 7)): inst(A_[t], c, (20, y, -3.0), rz=90)
bed = inst(A_["GothicBed_01"], c, (0, 2.6, 0), rz=180) if "GothicBed_01" in A_ else None
# mattress top: ray down
bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
BZ = 0.62
if bed:
    hit, loc, *_ = bed.evaluated_get(dg).ray_cast(bed.matrix_world.inverted() @ V((0, 2.2, 1.3)), V((0, 0, -1)))
    print("BED_Z", hit, loc)
    if hit and 0.3 < (bed.matrix_world @ loc).z < 1.2: BZ = (bed.matrix_world @ loc).z
B = human("TwinB_old", "TwinB_bed_S7", c)
# lying on his back: whole armature rotated so the body lies along -Y on the mattress, head on the pillow (+Y)
B.a.rotation_euler = (R_(-90), 0, 0); B.a.location = (0, 1.5, BZ + 0.13)
for f in (2004, 2120, 2240):
    B.H.key_spine(f, flex=-3, head=(-12, 8)); B.face(f, lids=1.0, smile=0.25)
    B.H.key_hand("L", f, V((0.33, 0.06, 0.95)), V((0, 0.05, -1)).normalized(), V((-1, 0, 0)), pole=V((0.4, 0.6, 1.1)))
    B.H.key_hand("R", f, V((-0.40, -0.22, 1.02)), V((0.15, 0, -1)).normalized(), V((0, 1, 0)), pole=V((-0.45, 0.2, 1.25)))
    grip(B.R, f, "R", 0.35); grip(B.R, f, "L", 0.3)
blanket = box("blanket", c, (1.15, 1.45, 0.18), (0, 2.2, BZ + 0.2), pbr("m_blanket", "velour_velvet", 3.0, coord="Object", tint=(0.35, 0.05, 0.06), bump=0.8))
bl = blanket.modifiers.new("sub", 'SUBSURF'); bl.levels = bl.render_levels = 2
dsp = blanket.modifiers.new("dsp", 'DISPLACE'); tx = bpy.data.textures.new("folds", 'CLOUDS'); tx.noise_scale = 0.3; dsp.texture = tx; dsp.strength = 0.05
OA = human("TwinA_old", "TwinA_bed_S7", c); OA.pos = V((-1.22, 2.45)); OA.yaw = -90 + 180
inst(A_["chair"], c, (-1.32, 2.45, 0), rz=-90)
for f in range(2004, 2240, 40):
    OA.sit(f, flex=30, knee_fwd=0.26, head=(22, 0)); OA.face(f, brow=1.8, lids=0.45, frown=1.0)
    sc.frame_set(f); bpy.context.view_layer.update()
    bh = ROOT[6].matrix_world.inverted() @ (B.a.matrix_world @ B.a.pose.bones["finger3-1.R"].head)
    hand_at(OA, f, "L", bh + V((0.0, 0.0, 0.035)), d=(1, 0.15, -0.25), n=(0, 0, -1), g=0.45)
    OA.hand(f, "R", (-0.2, -0.32, 0.64), d=(0, -1, 0), n=(0, 0, -1), g=0.5)
for o in [OA.a] + list(OA.a.children):
    for f, h in ((2004, False), (2230, True)):
        REKEY.append((o, f, h))
candle(c, (-1.6, 3.5, 0.75));
for x_ in (-0.78, 0.78):
    box("bedCurtain", c, (0.06, 0.5, 1.9), (x_, 3.45, 1.15), M["velvet"])
box("canopy", c, (1.65, 2.15, 0.08), (0, 2.6, 2.15), M["velvet"]); box("canopyTrim", c, (1.72, 2.22, 0.03), (0, 2.6, 2.1), M["gold"])
rug(c, (0, 0.5, 0), (2.8, 1.8)); picture(c, (-4.45, 0.5, 1.7), 90, 1.0); picture(c, (1.8, 4.45, 1.8), 180, 0.9)
tapestry(c, (-4.45, -2.5, 1.8), 90, w=1.4, h=1.8, tint=(0.04, 0.10, 0.45))
candelabra(c, (1.4, 3.9), 1.2); inst(A_["GothicCabinet_01"], c, (2.9, 4.0, 0), rz=180, s=0.8)
DR = human("Doctor2", "Doctor_S7", c); crowd_idle(DR, 1985, 2240, (1.25, 3.0), -90, "watch", seed=91)

nst = inst(A_["GothicCabinet_01"] if "GothicCabinet_01" in A_ else A_["table"], c, (-1.6, 3.6, 0), rz=180, s=0.5)
# window seat + very old twin A with coffee
VA = human("TwinA_vold", "TwinA_vold_S7", c); VA.pos = V((3.3, -1.6)); VA.yaw = -125
inst(A_["ArmChair_01"] if "ArmChair_01" in A_ else A_["chair"], c, (3.38, -1.66, 0), rz=-125)
cupV = inst(A_["cup"], c, (3.0, -1.2, 0.9), name="CupV")
bpy.ops.mesh.primitive_cylinder_add(radius=0.038, depth=0.002, location=(0, 0, 0.064)); cfv = bpy.context.active_object; link(cfv, c); setmat(cfv, M["coffee"]); cfv.parent = cupV
f = 2228
while f < 2510:
    VA.sit(f, seat_z=0.42, flex=10, head=(8, 0)); VA.hand(f, "R", (-0.05, -0.38, 0.86), d=(0.4, -1, 0.3), n=(1, 0, 0)); VA.face(f, smile=1.6, lids=0.35, brow=0.6)
    VA.hand(f, "L", (0.2, -0.3, 0.66), d=(0, -1, 0), n=(0, 0, -1)); grip(VA.R, f, "R", 0.75)
    VA.sit(f + 40, seat_z=0.42, flex=4, head=(-12, 0)); VA.hand(f + 40, "R", (-0.02, -0.2, 1.06), d=(0.1, -0.4, 1), n=(1, 0, 0), pole=(-0.45, 0.1, 0.8)); VA.face(f + 40, lids=0.7, smile=1.0)
    f += 95
inv = ROOT[6].matrix_world.inverted()
for f in range(2228, 2510, 5):
    cupV.location = inv @ hold_point(VA.a, "R", f); cupV.keyframe_insert("location", frame=f)
bpy.ops.mesh.primitive_cylinder_add(radius=0.04, depth=0.35, location=(0, 0, 0.2)); stv = bpy.context.active_object; link(stv, c); setmat(stv, steam_mat("m_steamV", 0.8)); stv.parent = cupV
light(c, 'AREA', (6.0, -1.0, 2.6), 2500, (1, 0.9, 0.75), 2.0, rot=(0, -75, 0), name="winLight")
for y0_, y1_ in ((-4.45, -1.75), (-0.25, 4.45)):
    box("wainscotE7", c, (0.08, y1_ - y0_, 0.9), (4.45, (y0_ + y1_) / 2, 0.45), M["oak"])
box("sillE7", c, (0.25, 1.6, 0.08), (4.4, -1.0, 0.88), M["oak"])
for y_ in (-2.05, 0.05):   # window curtains with folds
    cu = box("winCurtain", c, (0.06, 0.45, 2.6), (4.38, y_, 1.55), M["velvet"])
    sb = cu.modifiers.new("sub", 'SUBSURF'); sb.levels = sb.render_levels = 2
    wv = cu.modifiers.new("folds", 'WAVE'); wv.use_normal = True; wv.height = 0.03; wv.width = 0.12; wv.speed = 0; wv.use_x = False
box("curtainRod", c, (0.04, 3.0, 0.04), (4.38, -1.0, 2.9), M["gold"])
picture(c, (4.43, 2.6, 1.8), -90, 1.0)
inst(A_["table"], c, (2.6, -2.9, 0), rz=0).scale = (0.45, 0.25, 0.85)
candle(c, (2.6, -2.9, 0.67)); rug(c, (3.0, -1.5, 0), (2.2, 2.0))
light(c, 'AREA', (0, 0.5, 3.3), 700, (1, 0.8, 0.6), 2.0, rot=(0, 0, 0), name="bedTop")
light(c, 'AREA', (0, -1, 3.4), 900, (1.0, 0.95, 0.88), 4, rot=(0, 0, 0), name="ceilSoft")
light(c, 'AREA', (-2, -3, 3.3), 900, (0.7, 0.75, 1.0), 2.5, rot=(40, 0, -140), name="fill")
cam(2004, (0, -4.3, 1.7), (0, 2.5, 0.9), 28)
cam(2070, (-2.2, -0.8, 1.9), (0, 2.6, 0.9), 30)
cam(2140, (-0.3, 0.5, 1.8), (-0.4, 2.2, 0.8), 34)
cam(2200, (-0.95, 0.5, 1.5), (-0.5, 1.9, 0.8), 40)
cam(2225, (1.2, 0.3, 1.55), (3.3, -1.6, 1.15), 30)
cam(2250, (1.6, 0.6, 1.4), (3.3, -1.6, 1.1), 32)
cam(2320, (2.3, -0.4, 1.35), (3.25, -1.55, 1.15), 45)
cam(2400, (2.0, -2.4, 1.3), (3.2, -1.5, 1.15), 40)
cam(2448, (2.4, -0.2, 1.65), (3.3, -1.6, 1.15), 34)
cam(2472, (3.7, -0.5, 1.6), (3.3, -1.6, 1.15), 32)
cam(2470, (2.6, -0.4, 1.5), (3.25, -1.6, 1.15), 34)
cam(2506, (4.65, -1.0, 1.7), (8.0, -1.0, 1.7), 28)
finish_set(6)

# ================================================================== S8 Town square celebration (b13)
c = S(7)
plane("ground", c, 70, (0, 0, 0), M["cobble"])
inst(A_["fountain"], c, (0, 4, 0))
for t, p, rz in (("htb5", (-10, 12, 0), 0), ("house0", (0, 15, 0), 0), ("htb3", (10, 12, 0), 0), ("htb1", (-15, 0, 0), 90), ("house3", (15, -1, 0), -90), ("house7", (-14, -10, 0), 90)):
    inst(A_[t], c, p, rz=rz)
for p, rz in (((-5.5, 0.5, 0), 70), ((5.5, 1.0, 0), -70), ((-4.5, 7.5, 0), 110)):
    inst(A_["stall"], c, p, rz=rz)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.25, depth=1.6, location=(p[0], p[1], 2.0)); stS = bpy.context.active_object; link(stS, c); setmat(stS, steam_mat("m_steamS", 0.5))
for k in range(8):
    b = ("Townsman", "Woman", "Townswoman", "Townsman", "Woman", "Guard", "Townswoman", "Townsman")[k]
    A = human(b, "Cheer_S8_%d" % k, c)
    x = -3.0 + (k % 4) * 2.0; y = -1.5 + (k // 4) * 2.2
    crowd_idle(A, 2508, 2670, (x + random.uniform(-0.3, 0.3), y), random.uniform(-40, 40) + (180 if k % 2 else 0), "toast", seed=70 + k, phase=random.random())
    cp = inst(A_["cup"], c, (0, 0, 0), name="toastCup%d" % k)
    bpy.context.view_layer.update(); cp.matrix_world = Matrix.Translation(hold_point(A.a, "R", 2509))
    attach(cp, A.a, "wrist.R", 2509)
    if b == "Townsman": hat(A.a, A_["tricorn"], c)
light(c, 'SUN', (0, 0, 20), 3.5, (1.0, 0.9, 0.75), rot=(40, 0, 40), name="sun")
walker("Townsman", "Walk_S8_0", c, (-9, -2, 0), (-6.5, -8, 0), 2508, 2670); walker("Woman", "Walk_S8_1", c, (7, -5, 0), (3, 6, 0), 2508, 2670, 0.6)
cam(2508, (0, -12.7, 3.0), (0, 2.0, 1.5), 28)
cam(2545, (-1.2, -6.0, 1.3), (0, 0.0, 1.4), 30)
cam(2590, (0.8, -4.5, 3.5), (0, 1.0, 1.2), 28)
cam(2635, (0.0, -8.5, 8.5), (0, 2.0, 0.5), 26)
cam(2670, (0.0, -9.0, 9.0), (0, 2.0, 0.5), 26)
finish_set(7)

# ------------------------------------------------------------------ set visibility + world strength
for i, (nm, on, off, *_r) in enumerate(SETDEF):
    vis(SETC[i], on, off)
for o, f, h in REKEY:   # per-character swaps inside a set, applied after the set keys
    o.hide_render = h; o.keyframe_insert("hide_render", frame=f)
    o.hide_viewport = h; o.keyframe_insert("hide_viewport", frame=f)
world_keys([(1, 1.0), (157, 1.0), (158, 0.12), (574, 0.12), (575, 1.0), (704, 1.0), (705, 0.35), (1629, 0.35), (1630, 1.4), (1849, 1.4), (1850, 0.2), (1984, 0.2), (1985, 0.35), (2489, 0.35), (2490, 1.0)])
for fc in (W.node_tree.animation_data.action.fcurves if W.node_tree.animation_data and hasattr(W.node_tree.animation_data.action, "fcurves") else []):
    for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'

# ------------------------------------------------------------------ portal pass-throughs (textured surfaces the camera flies through, <= 6 frames)
PC = coll("PORTALS")
for i in range(len(SETDEF) - 1):
    if i != 1: continue   # only the steam pass has a pass-through volume; windows/doorways are openings, the rest are whip-pans
    ex = SETDEF[i][4]; Mx = ROOT[i].matrix_world @ P(*ex)
    f = SETDEF[i][2]
    if i == 1:   # steam
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.35, location=Mx.translation); o = bpy.context.active_object; link(o, PC); setmat(o, steam_mat("m_portalSteam", 24.0))
    else:
        o = plane("portal%d" % i, PC, (6, 6), (0, 0, 0), M["plaster"] if i not in (3, 6) else M["oak"])
        o.matrix_world = Mx @ Matrix.Rotation(R_(90), 4, 'X')
    for ff, h in ((1, True), (f - 3, False), (f + 3, True)):
        o.hide_render = h; o.keyframe_insert("hide_render", frame=ff)
        o.hide_viewport = h; o.keyframe_insert("hide_viewport", frame=ff)

# ------------------------------------------------------------------ one camera: Catmull-Rom through the framings, baked per frame
TR = [(SETDEF[i][2], i) for i in range(len(SETDEF) - 1)]
CK[:] = [k for k in CK if all(abs(k[0] - f) > 20 for f, i in TR)]
for f, i in TR:
    ex = SETDEF[i][4]; Mx = ROOT[i].matrix_world @ P(*ex); d = (Mx.to_3x3() @ V((0, 1, 0))).normalized(); p0 = Mx.translation
    li = ROOT[i].matrix_world.inverted(); li2 = ROOT[i + 1].matrix_world.inverted()
    if i in (0, 2, 4, 5):   # whip-pan
        wf = 6 if i == 4 else 12   # churchyard: hold on the mourners longer, shorter whip in open air: fast 110 deg pan, set swaps mid-whip, camera position continuous
        r70 = Matrix.Rotation(R_(70), 3, 'Z'); r35 = Matrix.Rotation(R_(35), 3, 'Z')
        CK.append((f - wf, i, li @ (p0 - d * 0.9), li @ (p0 + (r70 @ d) * 5), 28))
        CK.append((f, i, li @ p0, li @ (p0 + (r35 @ d) * 5), 28))
        CK.append((f + wf, i + 1, li2 @ (p0 + d * 0.9), li2 @ (p0 + d * 7 + V((0, 0, {5: -1.3, 4: -1.2}.get(i, 0.0)))), 28))   # whip ends facing forward, onto the next beat (down onto the bed for the bedroom)
    elif i in (3, 6):   # window exits: keep the room's characters until the last frames, whip out through the window
        back = {3: V((0.3, 1.6, 1.2)), 6: V((3.3, -1.6, 1.15))}[i]
        CK.append((f - 8, i, (V((4.0, -0.2, 1.6)) if i == 6 else li @ (p0 - d * 0.8)), back, 26 if i == 6 else 30))
        CK.append((f, i, li @ p0, li @ (p0 + d * 6), 26))
        CK.append((f + 18, i + 1, li2 @ (p0 + d * 2.2), li2 @ (p0 + d * 8), 26))
    else:
        CK.append((f - 5, i, li @ (p0 - d * 0.7), li @ (p0 + d * 4), 26))
        CK.append((f, i, li @ p0, li @ (p0 + d * 6), 26))
        CK.append((f + 18, i + 1, li2 @ (p0 + d * 2.2), li2 @ (p0 + d * 8), 26))
CK.sort(key=lambda k: k[0])
wp = [(k[0], toW(k[1], k[2])) for k in CK]; wt = [(k[0], toW(k[1], k[3])) for k in CK]; wl = [(k[0], float(k[4])) for k in CK]
fp, ft, fl_ = catmull(wp), catmull(wt), pchip(wl)
camd = bpy.data.cameras.new("Camera"); camo = bpy.data.objects.new("Camera", camd); sc.collection.objects.link(camo); sc.camera = camo
camd.sensor_width = 36; camd.clip_start = 0.02; camd.clip_end = 400
prev = None
# v009 aim fix: Track-To on a head, ramped in and out over 10 frames, world up (no roll): 31.0 s on the king, 41.0 s on the very old twin
AIM = [(1854, 1892, "King_S6"), (2436, 2484, "TwinA_vold_S7")]
def aim_w(f, a, b): return max(0.0, min(1.0, (f - a) / 10.0, (b - f) / 10.0))
for f in range(1, 2671):
    p = fp(f); t = ft(f)
    for a_, b_, nm_ in AIM:
        w_ = aim_w(f, a_, b_)
        if w_ > 0:
            w_ = w_ * w_ * (3 - 2 * w_); rg_ = bpy.data.objects[nm_]; sc.frame_set(f)
            hb_ = rg_.pose.bones["head"]; hp_ = rg_.matrix_world @ ((hb_.head + hb_.tail) / 2)
            d_ = ((t - p).normalized() * (1 - w_) + (hp_ - p).normalized() * w_).normalized(); t = p + d_ * 5
    q = (t - p).to_track_quat('-Z', 'Y'); e = q.to_euler('XYZ', prev) if prev else q.to_euler('XYZ')
    camo.location = p; camo.rotation_euler = e; prev = e
    camo.keyframe_insert("location", frame=f); camo.keyframe_insert("rotation_euler", frame=f)
    camd.lens = fl_(f); camd.keyframe_insert("lens", frame=f)

# ------------------------------------------------------------------ beats.json
import json
BEATS = [(1, 0.0, "The twins were about to be executed"), (2, 2.8, "the king suddenly stopped it"), (3, 4.9, "the king hated coffee"),
         (4, 9.7, "banned it across his kingdom"), (5, 12.0, "instead of killing them"), (6, 13.7, "three pots of coffee every day"),
         (7, 18.3, "the other drank three pots of tea"), (8, 21.6, "Two doctors watched them for years"), (9, 27.4, "both doctors died first"),
         (10, 31.1, "the king was assassinated"), (11, 33.3, "the tea-drinking twin died"), (12, 37.1, "coffee drinker as the last survivor"),
         (13, 41.7, "the ban on coffee was lifted")]
json.dump([{"beat": b, "frame": round(t * 60) + 1, "first_words": w} for b, t, w in BEATS],
          open("/home/user/Muhammed/blender/SwedishCoffee_v001/beats.json", "w"), indent=1)
for b, t, w in BEATS: sc.timeline_markers.new("b%02d" % b, frame=round(t * 60) + 1)

# ---- shrink textures: everything to <=1024 (GLB props 512 unless hero), saved as JPEG next to the scratch build
os.makedirs(SCR + "/tex", exist_ok=True)
HERO = ("cup", "silverpot", "throne", "wig", "teapot", "mask", "coffeepot", "skull")
bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
for im in list(bpy.data.images):
    if im.source != 'FILE' or im.size[0] == 0: continue
    users_mat = [m.name for m in bpy.data.materials if m.node_tree and any(n.type == 'TEX_IMAGE' and n.image == im for n in m.node_tree.nodes)]
    glb = im.packed_file is not None and not any(k in im.name.lower() for k in ("_1k", "_2k"))
    mx = 1024
    if glb and not any(h in " ".join(users_mat).lower() + im.name.lower() for h in HERO): mx = 512
    w, h = im.size
    if im.filepath.lower().endswith((".hdr",)): continue
    sc_ = min(1.0, mx / max(w, h))
    nc = im.colorspace_settings.name
    if sc_ < 1.0: im.scale(max(1, int(w * sc_)), max(1, int(h * sc_)))
    path = SCR + "/tex/%s.jpg" % bpy.path.clean_name(im.name)
    im.filepath_raw = path; im.file_format = 'JPEG'
    try:
        im.save(); 
        if im.packed_file: im.unpack(method='REMOVE')
        im.filepath = path; im.source = 'FILE'; im.reload(); im.colorspace_settings.name = nc
    except Exception as e: print("IMGFAIL", im.name, e)
sc.frame_set(1)
if OUT: bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("BUILD_DONE")
