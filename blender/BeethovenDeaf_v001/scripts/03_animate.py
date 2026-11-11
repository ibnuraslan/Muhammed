"""Composer rig + acting: sits at the piano, bites the rod, plays (gentle -> crash -> passionate), eyes close in bliss.
blender -b scene.blend --python 03_animate.py -- <out.blend>"""
import sys, os, math, random
import bpy
from mathutils import Vector, Matrix, Quaternion
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "..", "..", "pipeline", "anim_lib.py")).read())
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; RND = random.Random(1770)
FPS = 60
def T(s): return 1 + round(s * FPS)
BEAT = [T(t) for t in (0.0, 3.9, 5.2, 8.6, 11.9, 16.4, 18.4, 20.1)]; END = 1590
C = bpy.data.objects["Composer"]
CR = make_human_ctrl(C); H = Human(CR); PB = CR.PB
piano = bpy.data.objects["Piano"]

# ---------------------------------------------------------------- keyboard geometry (ray cast)
def ray_down(o, x, y, z0=3.0):
    inv = o.matrix_world.inverted(); ok, loc, nrm, idx = o.ray_cast(inv @ Vector((x, y, z0)), Vector((0, 0, -1)))
    return (o.matrix_world @ loc).z if ok else None
KEY_Y = 0.075
xs = [i * 0.01 for i in range(-75, 76)]
zk = {x: ray_down(piano, x, KEY_Y) for x in xs}
keys = [x for x in xs if zk[x] is not None and 0.76 < zk[x] < 0.86]
KX0, KX1 = min(keys) + 0.03, max(keys) - 0.03
KEY_Z = sorted(zk[x] for x in keys)[len(keys) // 2]
print("KEYBOARD", KX0, KX1, KEY_Z)
sc["key_z"] = KEY_Z; sc["kx"] = (KX0, KX1)
def key_z(x): 
    z = ray_down(piano, x, KEY_Y + 0.02); return z if z and z < 0.9 else KEY_Z

# ---------------------------------------------------------------- bench + seat
bench = bpy.data.objects["Bench"]; bench.location = (0, -0.60, 0); bench.rotation_euler = (0, 0, 0)
SEAT_Z = 0.4507
ROOT_P = Vector((0, -0.56, SEAT_Z + 0.105))

# ---------------------------------------------------------------- body keys: rocking, leaning toward the rod, bigger as the music grows
def intensity(f):
    if f < BEAT[1]: return 0.35
    if f < BEAT[1] + 80: return 1.0
    if f < BEAT[3] - 40: return 0.5
    if f < BEAT[6] + 70: return 0.12   # inside his head: keep the skull steady for the macro anatomy
    if f < BEAT[7]: return 0.5
    return 1.0
step = 4
for f in range(1, END + 1, step):
    I = intensity(f); t = f / FPS
    rock = math.sin(t * 2 * math.pi * 0.45) * I
    sway = math.sin(t * 2 * math.pi * 0.31 + 0.7) * I
    pump = math.sin(t * 2 * math.pi * 1.6) * I
    side = 3.5 * sway
    H.key_root(f, ROOT_P + Vector((0.025 * sway, 0.012 * rock, 0)), yaw=180 + 4 * sway, flex=8 + 3 * rock, side=side)
    if f < 32:   # hook: head back, jaw open, then lunges forward onto the rod
        u = smooth((f - 1) / 30.0); flex = 16 + 10 * u; hp = -12 + 10 * u
    else:
        flex = 25 + 3 * rock + 1.2 * pump; hp = -3 - 2 * rock
    H.key_spine(f, flex=flex, twist=-6 * sway, side=-side * 0.8, head=(hp, 2 * sway))
for s in "LR":
    sx = 1 if s == "L" else -1
    for f in (1, END):
        H.key_foot(s, f, Vector((sx * 0.15, -0.05 - (0.04 if s == "R" else 0))), 180 + sx * 6)
# right foot works the sustain pedal in beat 8 (toe dips, heel planted)
for f in range(BEAT[7], END - 40, 60):
    for df, p in ((0, 0), (8, -9), (40, -9), (48, 0)):
        H.key_foot("R", f + df, Vector((-0.15, -0.09)), 174, 0.0, p)

# ---------------------------------------------------------------- hands on the keys
SH = {s: CR.BN["upperarm01." + s].head_local.copy() for s in "LR"}
DOWN = []   # (side, frame, x) frames where fingertips touch the keys
def hand_pose(s, f, x, lift, yaw=0.0, wrist_up=0.0):
    sx = 1 if s == "L" else -1
    W = Vector((x, KEY_Y - 0.115, key_z(x) + 0.055 + lift))
    d = Matrix.Rotation(R_(yaw), 3, 'Z') @ Vector((-0.12 * sx * 0, 1.0, -0.42 + wrist_up)).normalized()
    nrm = Matrix.Rotation(R_(yaw), 3, 'Z') @ Vector((0.18 * sx, 0.0, -1.0))
    pole = W + Vector((sx * 0.45, -0.35, -0.15))
    H.key_hand(s, f, W, d, nrm, pole)
def fingers(s, f, curl, spread=0.0, thumb=20):
    sx = 1 if s == "L" else -1
    for k in range(1, 6):
        for j in range(1, 4):
            b = "finger%d-%d.%s" % (k, j, s)
            if k == 1:
                CR.key_rot(b, f, [("Z", sx * (thumb * 0.5 * j))]); continue
            c = curl[k - 2] if isinstance(curl, (list, tuple)) else curl
            CR.key_rot(b, f, [("X", -c * (0.8, 1.1, 0.8)[j - 1]), ("Z", sx * spread * (k - 3) * (1 if j == 1 else 0))])
def phrase(s, f0, f1, centre_fn, every, lift, span=0.12, accent=None):
    f = f0; i = 0
    while f < f1:
        x = centre_fn(f) + span * math.sin(i * 1.7 + (0 if s == "L" else 2.1)) * 0.5
        x = max(KX0, min(KX1, x))
        hit = f; up = f + every // 2
        hand_pose(s, hit, x, 0.0, yaw=RND.uniform(-6, 6)); DOWN.append((s, hit, x))
        c = [RND.uniform(25, 50) for _ in range(4)]; fingers(s, hit, c, spread=4)
        L_ = lift * (accent(f) if accent else 1.0)
        hand_pose(s, up, x + RND.uniform(-0.03, 0.03), L_, yaw=RND.uniform(-6, 6), wrist_up=0.15 * L_ / max(lift, 1e-3))
        fingers(s, up, [RND.uniform(8, 20) for _ in range(4)], spread=8)
        f += every; i += 1
# beat 1: gentle, he is mid-piece as he bites
phrase("L", 1, BEAT[1] - 6, lambda f: -0.28 + 0.04 * math.sin(f / 40), 18, 0.03)
phrase("R", 10, BEAT[1] - 6, lambda f: 0.16 + 0.06 * math.sin(f / 33), 14, 0.035)
# beat 2: wind up, both hands high, then CRASH, then sweep outward across the keys
for s, x0 in (("L", -0.2), ("R", 0.12)):
    sx = 1 if s == "L" else -1
    hand_pose(s, BEAT[1] - 2, x0, 0.05); fingers(s, BEAT[1] - 2, 20)
    hand_pose(s, BEAT[1] + 10, x0 - sx * 0.02, 0.17, wrist_up=0.1); fingers(s, BEAT[1] + 10, 5, spread=14)
    hand_pose(s, BEAT[1] + 17, x0 - sx * 0.03, 0.0); fingers(s, BEAT[1] + 17, [55, 60, 55, 50], spread=12); DOWN.append((s, BEAT[1] + 17, x0 - sx * 0.03))
    hand_pose(s, BEAT[1] + 21, x0 - sx * 0.03, 0.0); DOWN.append((s, BEAT[1] + 21, x0 - sx * 0.03)); fingers(s, BEAT[1] + 21, [55, 60, 55, 50], spread=12)
phrase("L", BEAT[1] + 30, BEAT[2] + 10, lambda f: -0.23 - 0.30 * smooth((f - BEAT[1] - 30) / 60), 8, 0.09)
phrase("R", BEAT[1] + 30, BEAT[2] + 10, lambda f: 0.15 + 0.32 * smooth((f - BEAT[1] - 30) / 60), 8, 0.09)
# beats 3-7: steady, expressive playing (mostly seen from inside his head, but always moving)
phrase("L", BEAT[2] + 14, BEAT[7] - 4, lambda f: -0.3 + 0.12 * math.sin(f / 70), 16, 0.05)
phrase("R", BEAT[2] + 20, BEAT[7] - 4, lambda f: 0.18 + 0.14 * math.sin(f / 55 + 1), 12, 0.05)
# beat 8: passionate, big sweeps and a cross-hand leap
phrase("L", BEAT[7], 1380, lambda f: -0.35 + 0.18 * math.sin((f - BEAT[7]) / 30), 10, 0.13, span=0.2)
phrase("R", BEAT[7] + 4, 1380, lambda f: 0.25 + 0.2 * math.sin((f - BEAT[7]) / 26 + 2), 9, 0.13, span=0.2)
for s, x0 in (("L", -0.3), ("R", 0.3)):   # arms fly up and slam a big chord
    hand_pose(s, 1392, x0, 0.2, wrist_up=0.12); fingers(s, 1392, 5, spread=15)
    hand_pose(s, 1402, x0 * 1.1, 0.0); fingers(s, 1402, [55, 60, 55, 50], spread=12); DOWN.append((s, 1402, x0 * 1.1))
    hand_pose(s, 1406, x0 * 1.1, 0.0); fingers(s, 1406, [55, 60, 55, 50], spread=12); DOWN.append((s, 1406, x0 * 1.1))
phrase("L", 1414, END, lambda f: -0.42 + 0.25 * smooth((f - 1414) / 170), 10, 0.12, span=0.22)
phrase("R", 1418, END, lambda f: 0.42 - 0.2 * smooth((f - 1418) / 170), 9, 0.12, span=0.22)

# ---------------------------------------------------------------- jaw: open for the hook, clamps on the rod at f30, keeps the clamp
JAW_KEYS = [(1, 14), (18, 16), (28, 5), (32, 3.2), (END, 3.2)]
for f, a_ in JAW_KEYS: CR.key_rot("jaw", f, [("X", -a_)])
# lips pulled back in effort while clamped; brief grimace at the crash
for f, a_ in ((1, 0), (30, 4), (BEAT[1] + 15, 9), (BEAT[2], 4), (BEAT[6] + 40, 7), (END, 6)):
    for s in "LR":
        sx = 1 if s == "L" else -1
        CR.key_rot("risorius03." + s, f, [("Z", sx * a_)])
# eyes: intense, squinting while he plays; blinks; close in bliss on "so he could still hear"
CLOSE = BEAT[6] + 18
def lids(f, up, low):
    for s in "LR":
        CR.key_rot("orbicularis03." + s, f, [("X", up)]); CR.key_rot("orbicularis04." + s, f, [("X", low)])
lids(1, 0, 0)
for b in (150, 420, 760, 960):
    lids(b, 0, 0); lids(b + 4, 26, -8); lids(b + 9, 0, 0)
lids(CLOSE - 1, 0, 0); lids(CLOSE + 16, 27, -9); lids(1290, 27, -9); lids(1302, 6, 0); lids(1440, 6, 0); lids(1446, 24, -7); lids(1452, 6, 0); lids(END, 6, 0)

# ---------------------------------------------------------------- fingertip contact: correct each DOWN key so the middle fingertip lands on the key top
def tip(s):
    pb = PB["finger3-3." + s]; return C.matrix_world @ pb.tail
for it in range(2):
    err = []
    for s, f, x in DOWN:
        ev(f); tz = tip(s).z; target = key_z(tip(s).x) + 0.006
        dz = target - tz; err.append(abs(dz))
        pb = PB["IK_hand." + s]
        # IK_hand is a root-level bone: shift its armature-space location by dz
        M = CR.rest("IK_hand." + s) @ Matrix.Translation(pb.location)
        pb.location = pb.location + (CR.rest("IK_hand." + s).to_3x3().inverted() @ Vector((0, 0, dz)))
        pb.keyframe_insert("location", frame=f, group="IK_hand." + s)
    print("TIP_ERR iter", it, "max %.3f mean %.3f" % (max(err), sum(err) / len(err)))

# ---------------------------------------------------------------- the brass rod: pinned on the piano, its tip clamped between his teeth from f30
head_pb = PB["head"]
bite = bpy.data.objects.new("Bite", None); sc.collection.objects.link(bite)
bite.parent = C; bite.parent_type = 'BONE'; bite.parent_bone = "head"
ev(1)
rest_bite = Vector((0.0, -0.128, 1.531))   # between the incisors, 1 cm behind their front edge (rest space)
hb = CR.BN["head"]
bite.matrix_parent_inverse = Matrix.Identity(4)
bite.location = (hb.matrix_local.inverted() @ rest_bite) - Vector((0, hb.length, 0))
ev(32); B32 = bite.matrix_world.translation.copy()
ANCHOR = Vector((0.0, 0.172, 1.0))
sc["anchor"] = list(ANCHOR)
brass = bpy.data.materials.get("M_Brass")
rodm = bpy.data.materials.new("M_RodBrass"); rodm.use_nodes = True; P = rodm.node_tree.nodes["Principled BSDF"]
P.inputs['Base Color'].default_value = (0.85, 0.62, 0.3, 1); P.inputs['Metallic'].default_value = 1.0; P.inputs['Roughness'].default_value = 0.22
bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.0042, depth=1.0); rod = bpy.context.active_object; rod.name = "Rod"
rod.data.transform(Matrix.Rotation(R_(-90), 4, 'X')); rod.data.transform(Matrix.Translation((0, 0.5, 0)))
rod.data.materials.append(rodm); rod.location = ANCHOR
tipE = bpy.data.objects.new("RodTip", None); sc.collection.objects.link(tipE); tipE.location = B32
cl = tipE.constraints.new('COPY_LOCATION'); cl.target = bite
cl.influence = 0.0; cl.keyframe_insert("influence", frame=29); cl.influence = 1.0; cl.keyframe_insert("influence", frame=31)
st = rod.constraints.new('STRETCH_TO'); st.target = tipE; st.rest_length = 1.0; st.volume = 'NO_VOLUME'
# bracket where the rod enters the piano case
bpy.ops.mesh.primitive_cube_add(size=1, location=ANCHOR + Vector((0, 0.01, -0.005))); br = bpy.context.active_object; br.name = "RodBracket"
br.scale = (0.035, 0.03, 0.03); br.data.materials.append(rodm)
bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.009, depth=0.03, location=ANCHOR + Vector((0, -0.012, 0))); col_ = bpy.context.active_object; col_.name = "RodCollar"
col_.rotation_euler = (R_(90), 0, 0); col_.data.materials.append(rodm)
# music desk with a manuscript (behind the rod)
dm = bpy.data.materials.get("M_DarkWood")
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.33, 1.15)); desk = bpy.context.active_object; desk.name = "MusicDesk"
desk.scale = (0.62, 0.015, 0.26); desk.rotation_euler = (R_(-14), 0, 0); desk.data.materials.append(dm)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.30, 1.035)); ledge = bpy.context.active_object; ledge.name = "MusicDesk_Ledge"
ledge.scale = (0.62, 0.05, 0.02); ledge.data.materials.append(dm)
DESK_PAGES = []
pm = [m for m in bpy.data.materials if m.name.startswith("M_Manuscript")]
for i, dx in enumerate((-0.14, 0.12, -0.02, 0.2, -0.22)):
    bpy.ops.mesh.primitive_plane_add(size=1); p = bpy.context.active_object; p.name = "DeskPage%d" % i
    p.data.transform(Matrix.Diagonal((0.23, 0.31, 1, 1)))
    p.modifiers.new("sol", 'SOLIDIFY').thickness = 0.0008
    bd = p.modifiers.new("curl", 'SIMPLE_DEFORM'); bd.deform_method = 'BEND'; bd.deform_axis = 'Y'; bd.angle = R_(6)
    p.data.materials.append(pm[i % len(pm)])
    p.location = (dx, 0.316 - 0.002 * i, 1.19); p.rotation_euler = (R_(90 - 14), 0, R_(RND.uniform(-4, 4)))
    DESK_PAGES.append(p)
sc["desk_pages"] = [p.name for p in DESK_PAGES]

# ---------------------------------------------------------------- pages fly off the desk in beat 8 and land flat on the floor
for i, p in enumerate(DESK_PAGES[2:]):
    f0 = BEAT[7] + 30 + i * 55
    L0, R0 = p.location.copy(), p.rotation_euler.copy()
    land = Vector((RND.choice((-1, 1)) * RND.uniform(0.9, 1.6), RND.uniform(-1.4, 0.3), 0.0016 + 0.0004 * i))
    for f in (1, f0):
        p.location = L0; p.rotation_euler = R0; p.keyframe_insert("location", frame=f); p.keyframe_insert("rotation_euler", frame=f)
    N = 70
    for k in range(1, N + 1, 3):
        u = k / N; f = f0 + k
        pos = L0.lerp(land, smooth(u)) + Vector((0, 0, 0.35 * math.sin(math.pi * u) * (1 - u)))
        pos.z = max(pos.z, land.z)
        p.location = pos
        p.rotation_euler = (R0.x * (1 - smooth(u)) + 0.5 * math.sin(k * 0.35) * (1 - u), 0.6 * math.sin(k * 0.22) * (1 - u), R0.z + u * RND.uniform(-2, 2))
        p.keyframe_insert("location", frame=f); p.keyframe_insert("rotation_euler", frame=f)
    p.location = land; p.rotation_euler = (0, 0, p.rotation_euler.z); p.keyframe_insert("location", frame=f0 + N + 2); p.keyframe_insert("rotation_euler", frame=f0 + N + 2)

# ---------------------------------------------------------------- wardrobe: black coat, white shirt, red cravat; wild grey hair
suit = bpy.data.objects["Composer.male_elegantsuit01"]
for m in suit.data.materials:
    nt = m.node_tree
    for nd in list(nt.nodes):
        if nd.type == 'TEX_IMAGE' and nd.image and "diffuse" in nd.image.name.lower():
            for lk in list(nd.outputs['Color'].links):
                sep = nt.nodes.new('ShaderNodeSeparateColor'); sep.mode = 'HSV'; nt.links.new(nd.outputs['Color'], sep.inputs['Color'])
                sat = nt.nodes.new('ShaderNodeMapRange'); sat.inputs['From Min'].default_value = 0.12; sat.inputs['From Max'].default_value = 0.2
                nt.links.new(sep.outputs['Green'], sat.inputs['Value'])
                val = nt.nodes.new('ShaderNodeMapRange'); val.inputs['From Min'].default_value = 0.62; val.inputs['From Max'].default_value = 0.72
                nt.links.new(sep.outputs['Blue'], val.inputs['Value'])
                coat = nt.nodes.new('ShaderNodeMix'); coat.data_type = 'RGBA'; coat.blend_type = 'MULTIPLY'; coat.inputs['Factor'].default_value = 1
                nt.links.new(nd.outputs['Color'], coat.inputs['A']); coat.inputs['B'].default_value = (0.07, 0.065, 0.075, 1)
                shirt = nt.nodes.new('ShaderNodeMix'); shirt.data_type = 'RGBA'
                nt.links.new(val.outputs['Result'], shirt.inputs['Factor']); nt.links.new(coat.outputs['Result'], shirt.inputs['A'])
                shirt.inputs['B'].default_value = (0.82, 0.78, 0.7, 1)
                tie = nt.nodes.new('ShaderNodeMix'); tie.data_type = 'RGBA'
                nt.links.new(sat.outputs['Result'], tie.inputs['Factor']); nt.links.new(shirt.outputs['Result'], tie.inputs['A'])
                tie.inputs['B'].default_value = (0.42, 0.03, 0.03, 1)
                nt.links.new(tie.outputs['Result'], lk.to_socket)
# cravat: a puffed silk neckcloth wrapped round the collar, knot and falls at the front
silk = bpy.data.materials.new("M_CravatSilk"); silk.use_nodes = True; P = silk.node_tree.nodes["Principled BSDF"]
P.inputs['Base Color'].default_value = (0.5, 0.025, 0.03, 1); P.inputs['Roughness'].default_value = 0.38; P.inputs['Sheen Weight'].default_value = 0.6
nk = CR.BN["neck01"].head_local
bpy.ops.mesh.primitive_torus_add(major_radius=0.058, minor_radius=0.011, major_segments=32, minor_segments=12, location=nk + Vector((0, -0.008, 0.03)))
band = bpy.context.active_object; band.name = "Cravat_Band"; band.scale = (1.0, 0.92, 1.0); band.rotation_euler = (R_(-14), 0, 0)
bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=16, radius=0.027, location=nk + Vector((0, -0.07, 0.005)))
knot = bpy.context.active_object; knot.name = "Cravat_Knot"; knot.scale = (1.1, 0.6, 0.85)
bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=16, radius=0.034, location=nk + Vector((0, -0.075, -0.045)))
fall = bpy.context.active_object; fall.name = "Cravat_Fall"; fall.scale = (0.85, 0.38, 1.1)
for o in (band, knot, fall):
    o.data.materials.append(silk)
    tx = bpy.data.textures.new(o.name + "_folds", 'CLOUDS'); tx.noise_scale = 0.02
    dsp = o.modifiers.new("folds", 'DISPLACE'); dsp.texture = tx; dsp.strength = 0.006; dsp.texture_coords = 'OBJECT'
    o.modifiers.new("sub", 'SUBSURF').levels = 1
    cc_ = o.constraints.new('CHILD_OF'); cc_.target = C; cc_.subtarget = "neck01"
    cc_.inverse_matrix = (C.matrix_world @ CR.BN["neck01"].matrix_local).inverted()
hair = bpy.data.objects["Composer.short02"]
hm = bpy.data.materials.new("M_GreyHair"); hm.use_nodes = True; hn = hm.node_tree.nodes; hn.clear()
ho = hn.new('ShaderNodeOutputMaterial'); hb_ = hn.new('ShaderNodeBsdfHairPrincipled'); hb_.parametrization = 'COLOR'
hb_.inputs['Color'].default_value = (0.3, 0.29, 0.28, 1); hb_.inputs['Roughness'].default_value = 0.42
hb_.inputs['Random Roughness'].default_value = 0.2
hm.node_tree.links.new(hb_.outputs[0], ho.inputs['Surface'])
for m in hair.data.materials:   # the cap itself: grey
    for nd in list(m.node_tree.nodes):
        if nd.type == 'TEX_IMAGE' and nd.image and "diffuse" in nd.image.name.lower():
            for lk in list(nd.outputs['Color'].links):
                hs = m.node_tree.nodes.new('ShaderNodeHueSaturation'); hs.inputs['Saturation'].default_value = 0.08; hs.inputs['Value'].default_value = 1.9
                m.node_tree.links.new(nd.outputs['Color'], hs.inputs['Color']); m.node_tree.links.new(hs.outputs['Color'], lk.to_socket)
hair.data.materials.append(hm)
psm = hair.modifiers.new("WildHair", 'PARTICLE_SYSTEM'); ps = psm.particle_system; pt = ps.settings
pt.type = "HAIR"; pt.count = 2200; pt.hair_length = 0.045; pt.use_advanced_hair = False
pt.emit_from = 'FACE'; pt.material = len(hair.data.materials)
pass
pt.child_type = 'INTERPOLATED'; pt.child_percent = 6; pt.rendered_child_count = 6; pt.child_length = 0.85; pt.child_length_threshold = 0.4
pt.clump_factor = 0.25; pt.roughness_1 = 0.004; pt.roughness_endpoint = 0.012; pt.roughness_2 = 0.006; pt.roughness_2_size = 0.5
pt.kink = 'WAVE'; pt.kink_amplitude = 0.006; pt.kink_frequency = 1.5
pt.root_radius = 0.6; pt.tip_radius = 0.1; pt.radius_scale = 0.0012
pt.display_step = 3; pt.render_step = 4
pt.effector_weights.gravity = 0.0
# keep the eyebrows bushy grey
for m in bpy.data.objects["Composer.eyebrow010"].data.materials:
    for nd in list(m.node_tree.nodes):
        if nd.type == 'TEX_IMAGE' and nd.image and "diffuse" in nd.image.name.lower():
            for lk in list(nd.outputs['Color'].links):
                hs = m.node_tree.nodes.new('ShaderNodeHueSaturation'); hs.inputs['Saturation'].default_value = 0.1; hs.inputs['Value'].default_value = 1.6
                m.node_tree.links.new(nd.outputs['Color'], hs.inputs['Color']); m.node_tree.links.new(hs.outputs['Color'], lk.to_socket)

# ---------------------------------------------------------------- candle flicker (flames scale + lights)
for i, fl in enumerate([o for o in bpy.data.objects if o.name.startswith("Flame")]):
    s0 = fl.scale.copy(); ph = RND.uniform(0, 10)
    for f in range(1, END + 1, 6):
        g = 1 + 0.12 * math.sin(f * 0.37 + ph) + 0.07 * math.sin(f * 1.1 + ph * 2)
        if BEAT[1] + 10 < f < BEAT[1] + 70: g *= 0.75 + 0.25 * math.sin(f * 0.9)   # gust from the crash
        fl.scale = (s0.x * (2 - g) ** 0.5, s0.y * (2 - g) ** 0.5, s0.z * g); fl.keyframe_insert("scale", frame=f)
for i, L in enumerate([o for o in bpy.data.objects if o.name.startswith("CandleLight")]):
    e0 = L.data.energy; ph = RND.uniform(0, 10)
    for f in range(1, END + 1, 6):
        L.data.energy = e0 * (1 + 0.18 * math.sin(f * 0.37 + ph) + 0.1 * math.sin(f * 1.3 + ph)); L.data.keyframe_insert("energy", frame=f)
print("DOWN", len(DOWN))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("ANIM_DONE")
