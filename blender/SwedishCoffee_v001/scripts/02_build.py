# SwedishCoffee build: sets, cast, animation, one continuous camera.
# blender -b --python 02_build.py -- <out.blend>
import sys
exec(open("/home/user/Muhammed/blender/SwedishCoffee_v001/scripts/lib.py").read())
OUT = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else None
random.seed(27)
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
for c in list(bpy.data.collections): bpy.data.collections.remove(c)
GZ = [0.0]
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
    plaster=pbr("m_plaster", "plastered_stone_wall", 0.3, coord="Object", bump=0.8, tint=(0.95, 0.9, 0.82)),
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
T("throne", 1.9); T("table", 0.78); T("chair", 1.0); T("chandelier", 1.6); T("candleholder", 0.28); T("candles", 0.35)
T("silverpot", 0.26); T("coffeepot_cu", 0.28); T("coffeepot_porc", 0.30); T("teapot", 0.2); T("cup", 0.075); T("teacup", 0.08)
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
    ("S1_Courtyard", 1, 175, ((0, -14, 4), 0), ((3.0, 9.0, 6.0), 0)),
    ("S2_ThroneHall", 175, 588, ((0, -8.2, 4.0), 0), ((-1.0, 4.62, 1.22), 0)),
    ("S3_Street", 588, 725, ((0, -9, 3.0), 0), ((-5.7, 6.0, 2.5), 90)),
    ("S4_Chamber", 725, 1650, ((0, -5.2, 2.0), 0), ((5.2, -1.0, 1.9), -90)),
    ("S5_Church", 1650, 1872, ((0, -16, 2.5), 0), ((0, 7.5, 7.0), 0)),
    ("S6_Ballroom", 1872, 2004, ((0, -10.2, 5.2), 0), ((-8.2, 0.0, 1.8), 90)),
    ("S7_Bedroom", 2004, 2508, ((0, -4.7, 1.7), 0), ((4.7, -1.0, 1.7), -90)),
    ("S8_Square", 2508, 2671, ((0, -13, 3.0), 0), None),
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
    for nm, sz, loc, rot in (("wN", (x1 - x0, h), ((x0 + x1) / 2, y1, h / 2), (90, 0, 180)), ("wS", (x1 - x0, h), ((x0 + x1) / 2, y0, h / 2), (90, 0, 0)),
                             ("wE", (y1 - y0, h), (x1, (y0 + y1) / 2, h / 2), (90, 0, 90)), ("wW", (y1 - y0, h), (x0, (y0 + y1) / 2, h / 2), (90, 0, -90))):
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
            A.hand(f, "R", (-0.25, -0.2, 1.75 + 0.15 * u) if up else (-0.22, -0.05, 0.9), d=(0, -0.2, 1) if up else (0, -0.1, -1),
                   n=(0, -1, 0) if up else (1, 0, 0), pole=(-0.6, 0.3, 1.3))
            A.hand(f, "L", (0.22, -0.02, 0.88), d=(0.05, -0.05, -1), n=(-1, 0, 0), pole=(0.3, 0.6, 1.1))
            A.face(f, brow=-1.5, jaw=10 * max(0, u), frown=1)
        elif mode == "toast":
            up = u > -0.3
            A.hand(f, "R", (-0.2, -0.32, 1.55 + 0.25 * u) if up else (-0.2, -0.3, 1.2), d=(0, -0.3, 1), n=(1, 0, 0), pole=(-0.5, 0.4, 1.2))
            A.hand(f, "L", (0.22, -0.02, 0.88), d=(0.05, -0.05, -1), n=(-1, 0, 0), pole=(0.3, 0.6, 1.1))
            A.face(f, brow=1.2, smile=1.5, jaw=8 * max(0, u))
        elif mode == "watch":
            A.arms_down(f, sway=0.02 * u); A.face(f, brow=0.5 * u, lids=0.1)
        f += int(per / 2)

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
            A.hand(f, s, (0.05 * sx, -0.2, 1.0), d=(-0.4 * sx, -1, 0.1), n=(0, 0, 1), pole=(0.4 * sx, 0.3, 1.0))
        A.face(f, brow=2.2, lids=-0.3, jaw=6 + 4 * u, frown=0.6)
    sh = inst(A_["shackles"], c, A.W((0, -0.22, 1.0)), rz=0, name="shackle_" + b); sh.rotation_euler.x = R_(90)
    attach(sh, A.a, "wrist.R", 1, local=True)
for k, x in enumerate((-1.3, 1.3)):
    A = human("Guard", "Guard_S1_%d" % k, c); A.z = PZ; GZ[0] = PZ
    for f in range(1, 176, 40):
        A.stand(f, pos=(x, 0.9), yaw=-25 * (1 if k else -1), head=(5, 0), flex=3)
        A.hand(f, "L" if k == 0 else "R", ((0.5 if k == 0 else -0.5), -0.5, 1.4), d=(0, -1, 0), n=(0, 0, -1))
        A.hand(f, "R" if k == 0 else "L", ((-0.22 if k == 0 else 0.22), -0.02, 0.88), d=(0, 0, -1))
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
cam(1, (-2.0, -15.0, 5.5), (0, 0, 2.6), 28)
cam(60, (-0.8, -9.5, 3.6), (0, 0.2, 2.8), 30)
cam(110, (0.25, -2.1, 2.85), (0, 0.2, 2.72), 40)
cam(140, (1.0, -1.5, 4.2), (2.0, 4.0, 5.0), 30)
cam(162, (2.3, 4.5, 5.6), (3.0, 12.0, 6.0), 26)
finish_set(0)

# ================================================================== S2 Throne hall (b2, b3)
c = S(1)
room(c, -6, 6, -8, 8, 7, M["parquet"], M["plaster"], M["plaster"], skip=())
box("dais", c, (4, 3, 0.4), (0, 6.3, 0.2), M["marble"])
th = inst(A_["throne"], c, (0, 6.6, 0.4), rz=180)
box("carpet", c, (2.2, 13, 0.01), (0, -1.5, 0.005), M["velvet"])
for x in (-5.5, 5.5):
    for y in (-5, 0, 5):
        box("pillar", c, (0.7, 0.7, 7), (x, y, 3.5), M["marble"])
st = inst(A_["table"], c, (-1.15, 5.1, 0.4), rz=90); st.scale = (0.5, 0.3, 0.54)
cupK = inst(A_["cup"], c, (-1.0, 5.0, 0.4 + 0.42), name="KingCup")
bpy.ops.mesh.primitive_cylinder_add(radius=0.034, depth=0.002, location=(-1.0, 5.0, 0.4 + 0.42 + 0.055)); cf = bpy.context.active_object; link(cf, c); setmat(cf, M["coffee"])
# steam + skull (volume)
bpy.ops.mesh.primitive_cylinder_add(radius=0.12, depth=0.6, location=(-1.0, 5.0, 1.15)); stm = bpy.context.active_object; stm.name = "steamK"; link(stm, c)
setmat(stm, steam_mat("m_steamK", 1.5))
sk = inst(A_["skull"], c, (-1.0, 5.0, 1.16), rz=180, name="SteamSkull"); sk.scale = (0.9, 0.9, 0.9)
skm = steam_mat("m_skull", 0.0, (0.95, 0.95, 0.97)); setmat(sk, skm)
dn = skm.node_tree.nodes["Dens"]
for f, v in ((470, 0.0), (500, 6.0), (560, 9.0), (588, 3.0)):
    dn.outputs[0].default_value = v; dn.outputs[0].keyframe_insert("default_value", frame=f)
for f, z in ((470, 1.08), (588, 1.26)):
    sk.location.z = z; sk.keyframe_insert("location", index=2, frame=f)
K = human("King", "King_S2", c); K.z = 0.4; GZ[0] = 0.4; K.pos = V((0, 6.45)); K.yaw = 0
for f, hand_up, lean, br in ((175, 0, 0, -0.5), (185, 0.5, 4, -1.5), (200, 1, 8, -2.5), (240, 1, 6, -2.5), (285, 0.3, 2, -2), (300, 0, 14, -2.5), (360, 0, 20, -2.8), (420, 0, 22, -3), (590, 0, 22, -3)):
    K.sit(f, seat_z=0.48, flex=lean, twist=-18 if f >= 300 else 0, head=(10 if f >= 300 else -5, -25 if f >= 300 else 0))
    if hand_up:
        K.hand(f, "R", (-0.35, -0.35, 1.0 + 0.75 * hand_up), d=(0, -0.3, 1), n=(0, -1, 0), pole=(-0.7, 0.2, 1.2))
    else:
        K.hand(f, "R", (-0.30, -0.25, 0.70), d=(0, -1, -0.2), n=(0, 0, -1), pole=(-0.6, 0.4, 0.9))
    K.hand(f, "L", (0.30, -0.25, 0.70), d=(0, -1, -0.2), n=(0, 0, -1), pole=(0.6, 0.4, 0.9))
    K.face(f, brow=br, frown=1.2 if f >= 185 else 0.3, jaw=14 if 185 <= f <= 240 else 0, lids=-0.2)
hat(K.a, A_["wig"], c, dz=-0.07, dy=0.03)
GZ[0] = 0.0
G = human("Guard", "Guard_S2", c); hat(G.a, A_["tricorn"], c)
G.stand(175, pos=(1.8, 4.2), yaw=200); G.arms_down(175); G.face(175, brow=1.5)
G.stand(200, pos=(1.8, 4.2), yaw=200, flex=10); G.arms_down(200)
G.H.walk(lambda f: V((1.8, 4.2, 0)).lerp(V((-3.5, -7.5, 0)), smooth((f - 205) / 90)), lambda f: 160, 205, 295, stride=1.5, duty=0.42, lift=0.14, lean=14)
G.arms_down(205); G.arms_down(295)
for x in (-3.5, 3.5):
    W_ = human("Guard", "Guard_S2b_%d" % (x > 0), c); hat(W_.a, A_["tricorn"], c)
    crowd_idle(W_, 175, 590, (x, 1.0), 90 if x > 0 else -90, "watch", seed=int(x))
ch = inst(A_["Chandelier_01"] if "Chandelier_01" in A_ else A_["chandelier"], c, (0, 1.5, 5.2), s=1.0)
light(c, 'AREA', (3, -1, 6), 900, (1, 0.85, 0.7), 5, rot=(40, 0, 30), name="key")
light(c, 'AREA', (-4, 4, 3), 200, (0.7, 0.8, 1.0), 3, rot=(70, 0, -120), name="fill")
aim(light(c, 'SPOT', (0, 2, 6.5), 1500, (1, 0.8, 0.6), 0.3, rot=(-20, 0, 0), name="throneSpot"), (0, 6.5, 1.2))

for p in ((-5.4, -2.5, 2.0), (5.4, -2.5, 2.0), (-5.4, 2.5, 2.0), (5.4, 2.5, 2.0)): candle(c, p)
cam(175, (0, -7.5, 3.9), (0, 6.0, 1.6), 30)
cam(215, (0.4, -2.5, 2.4), (0, 6.3, 1.5), 32)
cam(260, (1.2, 2.2, 1.7), (0, 6.4, 1.55), 35)
cam(300, (0.6, 4.4, 1.55), (-0.05, 6.35, 1.55), 45)
cam(360, (-0.6, 4.6, 1.5), (-0.2, 6.3, 1.5), 50)
cam(420, (0.2, 5.6, 1.45), (-0.95, 5.0, 1.0), 40)
cam(480, (-0.8, 4.35, 1.0), (-1.0, 5.0, 0.92), 55)
cam(540, (-0.95, 4.35, 1.12), (-1.0, 5.0, 1.17), 50)
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
# pot keyed in world: in hands until 645 then smash on cobbles with shards
sc.frame_set(588); bpy.context.view_layer.update()
for f in (588, 600, 612, 624, 632, 640, 645):
    sc.frame_set(f); hw = (hand_world(S1_.a, "L") + hand_world(S1_.a, "R")) / 2
    pot.matrix_world = Matrix.Translation(ROOT[2].matrix_world.inverted() @ hw + V((0, 0, -0.1)))
    pot.keyframe_insert("location", frame=f)
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
bpy.ops.mesh.primitive_plane_add(size=0.12, location=tuple(S2_.W((0.0, -0.95, 0.75))))
em = bpy.context.active_object; em.name = "BeanEmitter"; link(em, c)
ps = em.modifiers.new("beans", 'PARTICLE_SYSTEM').particle_system.settings
ps.count = 1500; ps.frame_start = 590; ps.frame_end = 720; ps.lifetime = 400; ps.normal_factor = -0.5; ps.factor_random = 0.4
ps.render_type = 'OBJECT'; ps.instance_object = A_["bean"]; ps.particle_size = 1.0; ps.size_random = 0.3; ps.use_rotations = True; ps.rotation_factor_random = 1.0
em.show_instancer_for_render = False
gnd.modifiers.new("col", 'COLLISION'); gnd.collision.damping = 0.8
for k, (x, y) in enumerate(((-2.0, 2.0), (-2.8, 3.4), (-1.6, 4.4), (-3.2, 0.6), (-2.4, 5.6))):
    b = ("Townsman", "Townswoman", "Woman", "Townsman", "Townswoman")[k]
    A = human(b, "Protest_S3_%d" % k, c)
    crowd_idle(A, 588, 725, (x, y), -70 + random.uniform(-20, 20), "jeer", seed=10 + k, phase=random.random())
light(c, 'SUN', (0, 0, 20), 3.0, (1.0, 0.92, 0.8), rot=(45, 0, -30), name="sun")
cam(588, (0, -8.7, 3.0), (1.2, 2.0, 1.2), 28)
cam(625, (1.6, -3.0, 1.4), (1.2, 1.5, 0.8), 30)
cam(655, (1.9, 0.6, 0.35), (2.0, 4.0, 0.4), 26)
cam(690, (-1.0, 2.5, 1.7), (-3.0, 3.5, 1.6), 28)
cam(722, (-5.3, 6.0, 2.5), (-9.0, 6.0, 2.5), 28)
finish_set(2)

# ================================================================== S4 Chamber (b5-b8)
c = S(3)
room(c, -5, 5, -5, 5, 4.2, M["planks"], M["castle"], M["oak"], skip=())
tb = inst(A_["table"], c, (0, 0.9, 0), rz=90); tb.scale = (1.2, 1.2, 1.0)
TZ = 0.78
for x in (-0.6, 0.6): inst(A_["chair"], c, (x, 1.75, 0), rz=0)
season = plane("season", c, (3.0, 2.6), (5.6, -1.0, 2.0), simple("m_season", (0.3, 0.5, 0.25), emit=(0.35, 0.55, 0.3), ew=1.5), (90, 0, -90))
sm = season.data.materials[0].node_tree.nodes["Principled BSDF"]
for f, col in ((725, (0.35, 0.55, 0.30)), (1360, (0.45, 0.62, 0.30)), (1420, (0.75, 0.45, 0.15)), (1480, (0.9, 0.92, 0.96)), (1540, (0.45, 0.62, 0.30)), (1600, (0.75, 0.45, 0.15))):
    sm.inputs["Emission Color"].default_value = (*col, 1); sm.inputs["Emission Color"].keyframe_insert("default_value", frame=f)
    sm.inputs["Base Color"].default_value = (*col, 1); sm.inputs["Base Color"].keyframe_insert("default_value", frame=f)
sunwin = light(c, 'AREA', (6.5, -1.0, 2.6), 1600, (1, 0.9, 0.75), 2.0, rot=(0, -70, 0), name="windowSun")
for f, e in ((725, 1600), (1330, 1600), (1360, 200), (1390, 1700), (1420, 150), (1450, 1600), (1480, 250), (1510, 1500), (1540, 200), (1570, 1600), (1650, 1600)):
    sunwin.data.energy = e; sunwin.data.keyframe_insert("energy", frame=f)
light(c, 'AREA', (-3, -3, 3.8), 900, (0.75, 0.82, 1.0), 3, rot=(50, 0, -140), name="fill")
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
bpy.ops.mesh.primitive_cylinder_add(radius=0.034, depth=0.002, location=(0, 0, 0.055)); cfa = bpy.context.active_object; link(cfa, c); setmat(cfa, M["coffee"])
cfa.parent = cupA
for k in range(3): inst(A_["silverpot"], c, (-1.25 + k * 0.22, 0.65, TZ), rz=200)
cupB = inst(A_["teacup"], c, (0.62, 1.05, TZ), name="CupB")
for k in range(3): inst(A_["teapot"] if "teapot" in A_ else A_["coffeepot_porc"], c, (0.95 + k * 0.2, 0.65, TZ), rz=160)
for k in range(5): inst(A_["cup"], c, (-1.05 - (k % 3) * 0.09, 1.15 - (k // 3) * 0.1, TZ), name="emptyCup")
def drink(A, s, cup, f0, f1, per=80, old=False):
    """sip cycle: reach cup, lift to lips, sip, set down"""
    sx = 1 if s == "L" else -1
    rest_cup = cup.location.copy()
    f = f0
    while f < f1:
        A.sit(f, flex=12, head=(8, 0)); A.hand(f, s, (0.09 * sx + (rest_cup.x - A.pos.x) * 0, -0.6 + 0.0, TZ + 0.05), d=(0, -1, 0.1), n=(-sx, 0, 0))
        A.face(f, brow=0.3, smile=0.4 if not old else 0.0)
        A.sit(f + per * 0.35, flex=4, head=(-12, 0)); A.hand(f + per * 0.35, s, (0.04 * sx, -0.27, 1.04), d=(-0.25 * sx, -0.3, 1.0), n=(-sx, 0, 0), pole=(0.45 * sx, 0.1, 0.9))
        A.face(f + per * 0.35, lids=0.6, jaw=4)
        A.sit(f + per * 0.65, flex=4, head=(-14, 0)); A.hand(f + per * 0.65, s, (0.04 * sx, -0.26, 1.05), d=(-0.25 * sx, -0.3, 1.0), n=(-sx, 0, 0), pole=(0.45 * sx, 0.1, 0.9))
        A.face(f + per * 0.65, lids=0.7, smile=0.6)
        f += per
    A.sit(f1, flex=12, head=(8, 0)); A.hand(f1, s, (0.09 * sx, -0.6, TZ + 0.05), d=(0, -1, 0.1), n=(-sx, 0, 0))
def rest_hands(A, f):
    for s in "LR":
        sx = 1 if s == "L" else -1
        A.hand(f, s, (0.2 * sx, -0.55, TZ + 0.02), d=(-0.3 * sx, -1, 0), n=(0, 0, -1), pole=(0.5 * sx, 0.3, 0.9))
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
        sc.frame_set(f); hw = inv @ hand_world(A.a, s)
        cup.location = hw + V((0.0, 0.0, -0.05)); cup.keyframe_insert("location", frame=f)
    sc.frame_set(f1 + 6); cup.location = V((A.pos.x, 1.05, TZ)); cup.keyframe_insert("location", frame=f1 + 8)
# servants pouring from silver pot / porcelain pot (pot in hand, tilt)
for k, (b, x, yaw, tmpl, f0, f1) in enumerate((("Woman", -1.45, -60, "silverpot", 760, 1110), ("Townswoman", 1.45, 60, "teapot", 1040, 1300))):
    A = human(b, "Servant_S4_%d" % k, c)
    pot = inst(A_[tmpl], c, (0, 0, 0), name="ServPot%d" % k)
    f = 725
    while f <= 1650:
        u = math.sin(f / 45 + k)
        pour = f0 <= f <= f1 and (f // 60) % 2 == 0
        A.stand(f, pos=(x, 1.05), yaw=yaw, flex=18 if pour else 6, twist=6 * u)
        sx = -1 if k == 0 else 1
        A.hand(f, "R" if k == 0 else "L", (-0.18 * sx * -1, -0.48, 1.12 if pour else 0.95), d=(0, -1, -0.5 if pour else 0), n=(0, 0, 1))
        A.hand(f, "L" if k == 0 else "R", (0.22 * -sx, -0.02, 0.88), d=(0, 0, -1))
        A.face(f, brow=0.5, smile=0.3)
        f += 30
    sc.frame_set(726); bpy.context.view_layer.update()
    pot.matrix_world = Matrix.Translation(hand_world(A.a, "R" if k == 0 else "L") + V((0, 0, -0.12)))
    attach(pot, A.a, "wrist.R" if k == 0 else "wrist.L", 726)
for k, x in enumerate((-1.4, 1.4)):
    A = human("Guard", "Guard_S4_%d" % k, c); hat(A.a, A_["tricorn"], c)
    crowd_idle(A, 725, 1650, (x, 3.4), 0, "watch", seed=40 + k)
# doctors at their desk, observing, writing
desk = inst(A_["table"], c, (3.0, -2.45, 0), rz=90); desk.scale = (0.75, 0.8, 1.0)
for k, (b, x) in enumerate((("Doctor1", 2.6), ("Doctor2", 3.4))):
    A = human(b, b + "_S4", c); A.pos = V((x, -3.05)); A.yaw = 180 - 15 + 30 * k
    inst(A_["chair"], c, (x, -3.15, 0), rz=180)
    f = 725; i = 0
    while f <= 1650:
        A.sit(f, flex=16 if i % 2 else 8, head=(10 if i % 2 else -4, 25 if i % 2 == 0 else 0))
        A.hand(f, "R", (-0.12, -0.42, TZ + 0.03 + 0.02 * (i % 2)), d=(0.3, -1, -0.2), n=(0, 0, -1))
        A.hand(f, "L", (0.22, -0.4, TZ + 0.02), d=(-0.3, -1, 0), n=(0, 0, -1))
        A.face(f, brow=-0.8 if i % 2 else 0.6, lids=0.3 if i % 2 else 0.0)
        f += 70; i += 1
    q = inst(A_["quill"], c, (x - 0.12, -2.7, TZ + 0.1), name="quill%d" % k); q.rotation_euler = (R_(60), 0, R_(20))
    attach(q, A.a, "wrist.R", 725, local=True)
    bk = inst(A_["book"], c, (x, -2.6, TZ), rz=180, name="ledger%d" % k)
# visibility of young/old twins inside the chamber
for nm, A in TW.items():
    old = "old" in nm
    objs = [A.a] + list(A.a.children)
    for o in objs:
        for f, h in ((725, old), (1480, not old)):
            o.hide_render = h; o.keyframe_insert("hide_render", frame=f)
cam(725, (0, -4.9, 2.0), (0, 1.5, 1.2), 28)
cam(790, (-1.2, -2.0, 1.5), (0, 1.6, 1.15), 30)
cam(860, (-1.6, -0.4, 1.3), (-0.6, 1.55, 1.2), 38)
cam(920, (-0.95, 0.55, 1.02), (-0.62, 1.1, 0.95), 45)
cam(980, (-2.2, 0.0, 1.5), (-0.6, 1.6, 1.2), 35)
cam(1040, (-1.1, -0.3, 1.25), (-0.6, 1.7, 1.25), 42)
cam(1099, (0.3, -1.0, 1.35), (0.6, 1.6, 1.2), 38)
cam(1160, (0.85, 0.5, 1.0), (0.6, 1.05, 0.9), 50)
cam(1230, (1.7, 0.2, 1.4), (0.6, 1.7, 1.25), 38)
cam(1265, (1.9, 0.0, 1.6), (1.6, -1.4, 1.2), 32)
cam(1297, (1.6, -0.9, 1.6), (3.0, -2.7, 1.2), 32)
cam(1360, (1.6, -1.6, 1.9), (3.0, -2.8, 1.0), 32)
cam(1420, (3.0, -0.7, 1.7), (3.0, -2.7, 1.25), 34)
cam(1480, (4.2, -1.8, 1.8), (2.5, 0.2, 1.2), 28)
cam(1545, (2.6, 0.2, 1.5), (0.0, 1.6, 1.2), 30)
cam(1605, (3.6, -0.2, 1.8), (2.8, -2.8, 1.2), 28)
cam(1648, (5.15, -1.0, 1.9), (8.0, -1.0, 1.9), 28)
finish_set(3)

# ================================================================== S5 Church in snow (b9)
c = S(4)
plane("ground", c, 80, (0, 0, 0), M["snow"])
chg = inst(A_["church"], c, (0, 22, 0), rz=180)
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
        p = path(f); cf.location = V((x, p.y + 0.0, 1.38)); cf.rotation_euler = (0, 0, R_(90)); cf.keyframe_insert("location", frame=f)
    for k, (dx, dy) in enumerate(((-0.42, -0.6), (0.42, -0.6), (-0.42, 0.6), (0.42, 0.6))):
        A = human(("Townsman", "Guard", "Townsman", "Guard")[k], "Bearer_S5_%d_%d" % (ci, k), c)
        A.H.walk(lambda f, x=x, dx=dx, dy=dy, path=path: V((x + dx, path(f).y + dy, 0)), lambda f: 0, 1650, 1872, stride=0.6, duty=0.6, lift=0.06, lean=3)
        s_in = "R" if dx > 0 else "L"; s_out = "L" if dx > 0 else "R"
        for f in range(1650, 1873, 12):
            yy = path(f).y + dy
            A.pos = V((x + dx, yy)); A.yaw = 0
            sx = 1 if s_in == "L" else -1
            A.hand(f, s_in, (0.12 * sx, -0.05, 1.42), d=(-sx, 0, 0.3), n=(0, 0, 1), pole=(0.5 * sx, 0.2, 1.0))
            A.hand(f, s_out, (-0.24 * sx, -0.02, 0.88), d=(0, 0, -1), n=(sx, 0, 0), pole=(-0.3 * sx, 0.6, 1.1))
            A.face(f, brow=0.8, lids=0.35, frown=0.6)
for k, b in enumerate(("TwinA_old", "TwinB_old")):
    A = human(b, b + "_S5", c)
    A.H.walk(lambda f, k=k: V((-0.5 + k * 1.0, 12.5 - 15.0 * (f - 1650) / 222, 0)), lambda f: 0, 1650, 1872, stride=0.6, duty=0.6, lift=0.06, lean=4)
    for f in range(1650, 1873, 24):
        A.arms_down(f, sway=0.01); A.face(f, brow=1.6, lids=0.4, frown=1.0)
# falling snow
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 14)); sn = bpy.context.active_object; sn.name = "SnowEmit"; link(sn, c)
ps = sn.modifiers.new("snow", 'PARTICLE_SYSTEM').particle_system.settings
ps.count = 6000; ps.frame_start = 1400; ps.frame_end = 1872; ps.lifetime = 500; ps.normal_factor = 0; ps.effector_weights.gravity = 0.04
ps.render_type = 'OBJECT'
bpy.ops.mesh.primitive_ico_sphere_add(radius=0.012, subdivisions=1); flake = bpy.context.active_object; flake.name = "flake"; link(flake, LIBC); setmat(flake, simple("m_flake", (1, 1, 1), rough=0.6))
ps.instance_object = flake; ps.size_random = 0.6; sn.show_instancer_for_render = False
light(c, 'SUN', (0, 0, 20), 2.0, (0.85, 0.9, 1.0), rot=(55, 0, 160), name="sun")
cam(1650, (0, -15.5, 2.5), (0, 4.0, 1.6), 26)
cam(1700, (-3.0, -8.0, 2.2), (-0.5, 2.0, 1.4), 30)
cam(1760, (-3.2, -2.5, 1.6), (0.0, 0.5, 1.4), 32)
cam(1810, (-2.6, -1.0, 1.75), (-0.5, 2.0, 1.65), 40)
cam(1845, (0, 1.0, 4.5), (0, 8.0, 7.0), 28)
cam(1870, (0, 7.3, 7.0), (0, 14.0, 7.0), 28)
finish_set(4)

# ================================================================== S6 Masked ball (b10)
c = S(5)
room(c, -8, 8, -10.5, 10, 8, M["marble"], M["plaster"], M["plaster"])
for y in (-5, 1, 7):
    ch = inst(A_["chandelier"], c, (0, y, 5.8), s=1.0)
    for a in range(6):
        light(c, 'POINT', (math.cos(a) * 0.6, y + math.sin(a) * 0.6, 5.9), 40, (1, 0.65, 0.3), 0.05, name="chandL")
for x in (-7.5, 7.5):
    for y in (-7, -2, 3, 8):
        box("pillar", c, (0.8, 0.8, 8), (x, y, 4), M["marble"])
K = human("King", "King_S6", c); hat(K.a, A_["wig"], c, dz=-0.07, dy=0.03)
MF = human("Doctor1", "Masked_S6", c)
mk = hat(MF.a, A_["mask"], c, dz=-0.05, dy=-0.1)
K.pos = V((0.5, 2.5)); K.yaw = 10
for f, ph in ((1872, 0), (1900, 0), (1912, 1), (1925, 2), (1945, 3), (2004, 3)):
    if ph < 2:
        K.stand(f, flex=3, head=(0, -10)); K.arms_down(f); K.face(f, smile=0.6 if ph == 0 else 0, brow=2.5 if ph else 0, jaw=14 if ph else 0)
    elif ph == 2:
        K.stand(f, crouch=0.45, flex=35, side=15, lean=20, head=(20, 10)); K.face(f, brow=2.5, lids=0.5, jaw=16)
        K.hand(f, "R", (-0.25, 0.1, 0.55), d=(0, 0, -1)); K.hand(f, "L", (0.3, 0.1, 0.5), d=(0, 0, -1))
    else:   # collapsed: lying on the floor on his side
        K.H.key_root(f, V((0.5, 2.5 + 0.6, 0.17)), yaw=10, flex=-85, side=10)
        K.H.key_spine(f, flex=-6, head=(-10, 20))
        for s in "LR":
            sx = 1 if s == "L" else -1
            K.H.key_foot(s, f, K.W((0.15 * sx, 1.0 + 0.6, 0)).to_2d(), 10, lift=-0.02, pitch=-80)
        K.hand(f, "R", (-0.4, 0.4, 0.05), d=(0, -1, 0), n=(0, 0, -1)); K.hand(f, "L", (0.4, 0.2, 0.05), d=(0, -1, 0), n=(0, 0, -1))
        K.face(f, lids=1.0, jaw=6)
MF.pos = V((1.2, 4.2)); MF.yaw = 180 + 15
for f, ph in ((1872, 0), (1895, 1), (1905, 1), (1925, 0), (2004, 0)):
    MF.stand(f, flex=4 if ph else 0)
    MF.hand(f, "R", (-0.15, -0.55, 1.35) if ph else (-0.22, -0.02, 0.88), d=(0, -1, 0) if ph else (0, 0, -1), n=(1, 0, 0))
    MF.hand(f, "L", (0.22, -0.02, 0.88), d=(0, 0, -1))
# muzzle flash at 1907 (light + glow puff) from in front of the masked figure's hand; no weapon detail
fl = light(c, 'POINT', MF.W((-0.15, -0.75, 1.36)), 0, (1, 0.75, 0.4), 0.05, name="flash")
for f, e in ((1904, 0), (1907, 30000), (1910, 3000), (1916, 0)):
    fl.data.energy = e; fl.data.keyframe_insert("energy", frame=f)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.25, location=tuple(MF.W((-0.15, -0.8, 1.36)))); puff = bpy.context.active_object; puff.name = "smokePuff"; link(puff, c)
pm = steam_mat("m_puff", 0.0, (0.6, 0.6, 0.62)); setmat(puff, pm); pdn = pm.node_tree.nodes["Dens"]
for f, v, s in ((1905, 0, 0.3), (1908, 8, 0.6), (1940, 2, 2.0), (1990, 0, 3.0)):
    pdn.outputs[0].default_value = v; pdn.outputs[0].keyframe_insert("default_value", frame=f); puff.scale = (s,) * 3; puff.keyframe_insert("scale", frame=f)
# dancers: pairs turning, then scatter
for k in range(6):
    b = ("Woman", "Townsman", "Townswoman", "Guard", "Woman", "Townsman")[k]
    A = human(b, "Dancer_S6_%d" % k, c)
    cx, cy0 = (-3.2 + (k % 3) * 3.2, -3.0 + (k // 3) * 3.5)
    ang0 = k * 1.1
    def dpath(f, cx=cx, cy0=cy0, ang0=ang0, k=k):
        if f < 1912:
            a = ang0 + (f - 1872) / 50.0
            return V((cx + 0.5 * math.cos(a), cy0 + 0.5 * math.sin(a), 0))
        a = ang0 + 40 / 50.0
        p0 = V((cx + 0.5 * math.cos(a), cy0 + 0.5 * math.sin(a), 0)); dirv = (p0 - V((0.5, 2.5, 0))).normalized()
        return p0 + dirv * 2.6 * smooth((f - 1912) / 70)
    def dyaw(f, cx=cx, cy0=cy0, ang0=ang0):
        if f < 1912: return math.degrees(ang0 + (f - 1872) / 50.0) + 180
        a = ang0 + 40 / 50.0; p0 = V((cx + 0.5 * math.cos(a), cy0 + 0.5 * math.sin(a))); d = p0 - V((0.5, 2.5))
        return math.degrees(math.atan2(-d.x, d.y)) + 180
    A.H.walk(dpath, dyaw, 1872, 2004, stride=0.55, duty=0.6, lift=0.07, lean=3)
    for f in range(1872, 2005, 16):
        if f < 1915:
            A.hand(f, "R", (-0.3, -0.25, 1.35), d=(-0.3, -0.5, 0.6), n=(0, -1, 0)); A.hand(f, "L", (0.25, -0.2, 1.05), d=(0, -1, 0), n=(0, 0, -1))
            A.face(f, smile=0.8)
        else:
            A.hand(f, "R", (-0.2, -0.3, 1.5), d=(0, -0.2, 1), n=(0, -1, 0)); A.hand(f, "L", (0.2, -0.3, 1.45), d=(0, -0.2, 1), n=(0, -1, 0))
            A.face(f, brow=2.5, jaw=16, lids=-0.3)
    hat(A.a, A_["mask"], c, dz=-0.05, dy=-0.1)
light(c, 'AREA', (4, -4, 7), 1400, (1, 0.8, 0.6), 6, rot=(35, 0, 40), name="key")
light(c, 'AREA', (-5, 6, 4), 250, (0.6, 0.7, 1.0), 4, rot=(70, 0, -140), name="rim")
cam(1872, (0, -9.8, 5.2), (0, 2.0, 3.0), 28)
cam(1890, (0.6, -2.0, 4.2), (0.8, 3.0, 1.6), 30)
cam(1905, (2.2, 6.0, 1.75), (0.5, 2.4, 1.5), 32)
cam(1930, (2.6, 4.8, 1.1), (0.5, 2.6, 0.7), 30)
cam(1960, (-1.0, 4.0, 0.8), (0.5, 2.8, 0.3), 28)
cam(1985, (-5.5, 1.5, 1.6), (-9.0, 0.0, 1.8), 28)
cam(2002, (-8.0, 0.0, 1.8), (-11.0, 0.0, 1.8), 28)
finish_set(5)

# ================================================================== S7 Bedroom (b11, b12)
c = S(6)
room(c, -4.5, 4.5, -4.5, 4.5, 3.5, M["planks"], M["plaster"], M["oak"])
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
    for s_ in "LR":
        sx = 1 if s_ == "L" else -1
        B.H.key_hand(s_, f, V((0.2 * sx, 0.12, 0.95)), V((0, 0.05, -1)).normalized(), V((-sx, 0, 0)), pole=V((0.4 * sx, 0.6, 1.1)))
blanket = box("blanket", c, (1.15, 1.45, 0.18), (0, 2.2, BZ + 0.2), pbr("m_blanket", "wool_boucle", 3.0, coord="Object", tint=(0.45, 0.12, 0.10), bump=0.8))
bl = blanket.modifiers.new("sub", 'SUBSURF'); bl.levels = bl.render_levels = 2
dsp = blanket.modifiers.new("dsp", 'DISPLACE'); tx = bpy.data.textures.new("folds", 'CLOUDS'); tx.noise_scale = 0.3; dsp.texture = tx; dsp.strength = 0.05
OA = human("TwinA_old", "TwinA_bed_S7", c); OA.pos = V((-1.15, 1.9)); OA.yaw = -90 + 180
inst(A_["chair"], c, (-1.25, 1.9, 0), rz=-90)
for f in range(2004, 2240, 40):
    OA.sit(f, flex=22, head=(18, 0)); OA.face(f, brow=1.8, lids=0.45, frown=1.0)
    OA.hand(f, "R", (-0.1, -0.62, BZ + 0.22), d=(0, -1, -0.2), n=(0, 0, -1)); OA.hand(f, "L", (0.2, -0.45, 0.62), d=(0, -1, 0), n=(0, 0, -1))
for o in [OA.a] + list(OA.a.children):
    for f, h in ((2004, False), (2230, True)):
        o.hide_render = h; o.keyframe_insert("hide_render", frame=f)
candle(c, (-1.6, 3.5, 0.75));
nst = inst(A_["GothicCabinet_01"] if "GothicCabinet_01" in A_ else A_["table"], c, (-1.6, 3.6, 0), rz=180, s=0.5)
# window seat + very old twin A with coffee
VA = human("TwinA_vold", "TwinA_vold_S7", c); VA.pos = V((3.3, -1.6)); VA.yaw = -125
inst(A_["ArmChair_01"] if "ArmChair_01" in A_ else A_["chair"], c, (3.38, -1.66, 0), rz=-125 + 180)
cupV = inst(A_["cup"], c, (3.0, -1.2, 0.9), name="CupV")
f = 2228
while f < 2510:
    VA.sit(f, seat_z=0.42, flex=10, head=(8, 0)); VA.hand(f, "R", (-0.05, -0.38, 0.86), d=(0.4, -1, 0.3), n=(1, 0, 0)); VA.face(f, smile=1.6, lids=0.35, brow=0.6)
    VA.hand(f, "L", (0.2, -0.3, 0.66), d=(0, -1, 0), n=(0, 0, -1))
    VA.sit(f + 40, seat_z=0.42, flex=4, head=(-12, 0)); VA.hand(f + 40, "R", (-0.02, -0.2, 1.06), d=(0.1, -0.4, 1), n=(1, 0, 0), pole=(-0.45, 0.1, 0.8)); VA.face(f + 40, lids=0.7, smile=1.0)
    f += 95
inv = ROOT[6].matrix_world.inverted()
for f in range(2228, 2510, 5):
    sc.frame_set(f); cupV.location = inv @ hand_world(VA.a, "R") + V((0, 0, -0.05)); cupV.keyframe_insert("location", frame=f)
bpy.ops.mesh.primitive_cylinder_add(radius=0.04, depth=0.35, location=(0, 0, 0.2)); stv = bpy.context.active_object; link(stv, c); setmat(stv, steam_mat("m_steamV", 0.8)); stv.parent = cupV
light(c, 'AREA', (3.6, -1.0, 2.6), 1300, (1, 0.9, 0.75), 2.0, rot=(0, -60, 0), name="winLight")
light(c, 'AREA', (0, 0.5, 3.3), 700, (1, 0.8, 0.6), 2.0, rot=(0, 0, 0), name="bedTop")
light(c, 'AREA', (-2, -3, 3.3), 600, (0.7, 0.75, 1.0), 2.5, rot=(40, 0, -140), name="fill")
cam(2004, (0, -4.3, 1.7), (0, 2.5, 0.9), 28)
cam(2070, (-2.2, -0.8, 1.9), (0, 2.6, 0.9), 30)
cam(2140, (-0.2, 0.6, 2.2), (-0.4, 2.0, 0.8), 34)
cam(2200, (-0.55, 1.1, 1.15), (-0.6, 1.95, 0.75), 42)
cam(2250, (1.6, 0.6, 1.4), (3.3, -1.6, 1.1), 32)
cam(2320, (2.3, -0.4, 1.35), (3.25, -1.55, 1.15), 45)
cam(2400, (2.0, -2.4, 1.3), (3.2, -1.5, 1.15), 40)
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
    sc.frame_set(2509); bpy.context.view_layer.update(); cp.matrix_world = Matrix.Translation(hand_world(A.a, "R") + V((0, 0, -0.04)))
    attach(cp, A.a, "wrist.R", 2509)
    if b == "Townsman": hat(A.a, A_["tricorn"], c)
light(c, 'SUN', (0, 0, 20), 3.5, (1.0, 0.9, 0.75), rot=(40, 0, 40), name="sun")
cam(2508, (0, -12.7, 3.0), (0, 2.0, 1.5), 28)
cam(2545, (-1.2, -6.0, 1.3), (0, 0.0, 1.4), 30)
cam(2590, (0.8, -4.5, 3.5), (0, 1.0, 1.2), 28)
cam(2635, (0.0, -8.5, 8.5), (0, 2.0, 0.5), 26)
cam(2670, (0.0, -9.0, 9.0), (0, 2.0, 0.5), 26)
finish_set(7)

# ------------------------------------------------------------------ set visibility + world strength
for i, (nm, on, off, *_r) in enumerate(SETDEF):
    vis(SETC[i], on, off)
world_keys([(1, 1.0), (174, 1.0), (175, 0.12), (587, 0.12), (588, 1.0), (724, 1.0), (725, 0.35), (1649, 0.35), (1650, 0.8), (1871, 0.8), (1872, 0.2), (2003, 0.2), (2004, 0.35), (2507, 0.35), (2508, 1.0)])
for fc in (W.node_tree.animation_data.action.fcurves if W.node_tree.animation_data and hasattr(W.node_tree.animation_data.action, "fcurves") else []):
    for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'

# ------------------------------------------------------------------ portal pass-throughs (textured surfaces the camera flies through, <= 6 frames)
PC = coll("PORTALS")
for i in range(len(SETDEF) - 1):
    ex = SETDEF[i][4]; Mx = ROOT[i].matrix_world @ P(*ex)
    f = SETDEF[i][2]
    if i == 1:   # steam
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.35, location=Mx.translation); o = bpy.context.active_object; link(o, PC); setmat(o, steam_mat("m_portalSteam", 12.0))
    else:
        o = plane("portal%d" % i, PC, (6, 6), (0, 0, 0), M["plaster"] if i not in (3, 6) else M["oak"])
        o.matrix_world = Mx @ Matrix.Rotation(R_(90), 4, 'X')
    for ff, h in ((1, True), (f - 8, False), (f + 8, True)):
        o.hide_render = h; o.keyframe_insert("hide_render", frame=ff)

# ------------------------------------------------------------------ one camera: Catmull-Rom through the framings, baked per frame
TR = [(SETDEF[i][2], i) for i in range(len(SETDEF) - 1)]
CK[:] = [k for k in CK if all(abs(k[0] - f) > 20 for f, i in TR)]
for f, i in TR:
    ex = SETDEF[i][4]; Mx = ROOT[i].matrix_world @ P(*ex); d = (Mx.to_3x3() @ V((0, 1, 0))).normalized(); p0 = Mx.translation
    li = ROOT[i].matrix_world.inverted(); li2 = ROOT[i + 1].matrix_world.inverted()
    CK.append((f - 7, i, li @ (p0 - d * 0.8), li @ (p0 + d * 4), 26))
    CK.append((f, i, li @ p0, li @ (p0 + d * 6), 26))
    CK.append((f + 18, i + 1, li2 @ (p0 + d * 2.2), li2 @ (p0 + d * 8), 26))
CK.sort(key=lambda k: k[0])
wp = [(k[0], toW(k[1], k[2])) for k in CK]; wt = [(k[0], toW(k[1], k[3])) for k in CK]; wl = [(k[0], float(k[4])) for k in CK]
fp, ft, fl_ = catmull(wp), catmull(wt), pchip(wl)
camd = bpy.data.cameras.new("Camera"); camo = bpy.data.objects.new("Camera", camd); sc.collection.objects.link(camo); sc.camera = camo
camd.sensor_width = 36; camd.clip_start = 0.02; camd.clip_end = 400
prev = None
for f in range(1, 2671):
    p = fp(f); t = ft(f)
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

sc.frame_set(1)
if OUT: bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("BUILD_DONE")
