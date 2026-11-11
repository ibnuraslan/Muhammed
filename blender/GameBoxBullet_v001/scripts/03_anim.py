"""Animate: man + grip, box, bullet, wall breach, shatter, energy rings, room life, one continuous camera.
blender -b work/scene.blend --python scripts/03_anim.py -- work/film.blend"""
import sys, os, math, random, json
import bpy, bmesh
from mathutils import Vector, Matrix, Quaternion, Euler

OUT = sys.argv[sys.argv.index("--") + 1]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
exec(open(os.path.join(ROOT, "..", "pipeline", "anim_lib.py")).read())
sc = bpy.context.scene
random.seed(1515)
F_END = 1500
V = Vector

# ------------------------------------------------------------------ timing (frames at 60 fps)
BEATS = [(1, 1, "A stray bullet was fired toward his house"), (2, 151, "tore straight through the wall"),
         (3, 241, "heading right for his chest"), (4, 391, "But it slammed into his brand new video game collector's box set"),
         (5, 661, "The thick case cracked"), (6, 751, "the discs shattered"),
         (7, 841, "and layer by layer they soaked up the bullet's energy"), (8, 1081, "By the time it was halfway through"),
         (9, 1231, "the bullet had stopped, buried deep inside"), (10, 1351, "saving his life")]
F_WALL = 158      # nose meets the siding
F_HIT = 396       # nose meets the box cover
F_STOP = 1230

BOX_C = V((0.0, 2.97, 1.25))
broot = bpy.data.objects["BoxRoot"]
bullet = bpy.data.objects["Bullet"]

def kf(o, path, f, idx=-1):
    o.keyframe_insert(path, frame=f, index=idx)

# ------------------------------------------------------------------ box motion (world), driven by hands
def box_pose(f):
    """returns (location, euler) of BoxRoot"""
    loc = BOX_C.copy(); rx = 0.0; rz = 0.0
    # breathing before the hit
    loc.z += 0.004 * math.sin(f / 60 * 2 * math.pi * 0.25)
    # impact shove (slow-motion): pushed into his chest, then he braces
    if f > F_HIT:
        u = (f - F_HIT) / 50.0
        loc.y += 0.018 * (1 - math.exp(-u * 2.5)) * (1 + 0.25 * math.exp(-u) * math.sin(u * 5))
        rx += R_(-3.0) * (1 - math.exp(-u * 2.0))
    # beat 10: lowers the box and tilts the face up toward his eyes, then holds it out a little
    if f > 1355:
        u = smooth((f - 1355) / 70.0)
        loc.z -= 0.15 * u; loc.y -= 0.10 * u; rx += R_(-30) * u
        w = smooth((f - 1430) / 50.0)
        loc.z += 0.03 * w; rx += R_(8) * w
    return loc, Euler((rx, 0, rz))

for f in range(1, F_END + 1, 2):
    l, e = box_pose(f); broot.location = l; broot.rotation_euler = e
    kf(broot, "location", f); kf(broot, "rotation_euler", f)
def box_M(f):
    l, e = box_pose(f); return Matrix.Translation(l) @ e.to_matrix().to_4x4()

# ------------------------------------------------------------------ man
man = bpy.data.objects["Gamer"]
R = make_human_ctrl(man); H = Human(R)
MAN = V((0.0, 3.21, 0.0))
FZ = 0.25   # bedroom floor
bpy.context.view_layer.objects.active = man; bpy.ops.object.mode_set(mode='POSE')
# feet planted, never move
for f in (1, F_END):
    for s, dx in (("L", 0.13), ("R", -0.13)):
        xy = V((MAN.x + dx, MAN.y + 0.02 + (0.03 if s == "R" else -0.02)))
        a = H.ankle[s]; z = FZ + a.z + 0.0165
        M = Matrix.Translation(V((xy.x, xy.y, z))) @ Matrix.Rotation(R_(8 if s == "L" else -8), 4, 'Z') @ Matrix.Translation(-a) @ R.rest("IK_foot." + s)
        R.key_world("IK_foot." + s, f, M)
        pole = V((xy.x + dx, xy.y - 0.7, z + 0.45)); n = "Pole_knee." + s; pb = R.PB[n]
        pb.location = R.rest(n).to_3x3().inverted() @ (pole - R.BN[n].head_local); pb.keyframe_insert("location", frame=f)

def man_state(f):
    """root offset, spine flex/twist, head pitch/yaw"""
    dy = 0.0; dz = 0.0; flex = 6.0; twist = 0.0; side = 0.0; hp = 22.0; hy = 0.0
    br = math.sin(f / 60 * 2 * math.pi * 0.25)
    dz += 0.004 * br; flex += 1.0 * br
    # admiring the box, then the crack of the wall makes him start to lift his head (slow motion)
    u = smooth((f - 180) / 200.0); hp -= 26 * u; hy += 4 * u
    # impact: torso pushed back, knees give a little, head jerks
    if f > F_HIT:
        v = (f - F_HIT) / 60.0; k = 1 - math.exp(-v * 2.2)
        dy += 0.03 * k; dz -= 0.02 * k; flex -= 7 * k; hp -= 6 * k * math.exp(-v * 0.3); side += 2 * math.sin(v * 1.3) * math.exp(-v * 0.5)
        hp += 18 * smooth((f - 600) / 300.0)   # stares down at the box as it cracks
    # beat 10: looks down at the hole, breath, then up to the camera
    w = smooth((f - 1360) / 60.0); hp += 12 * w; flex += 10 * w
    z = smooth((f - 1415) / 50.0)
    hp -= 40 * z; hy += 26 * z; twist += 14 * z; flex -= 8 * z; dy -= 0.01 * z
    return dy, dz, flex, twist, side, hp, hy

for f in list(range(1, F_END + 1, 4)) + [F_END]:
    dy, dz, flex, twist, side, hp, hy = man_state(f)
    H.key_root(f, V((MAN.x, MAN.y + H.root_head.y + dy, FZ + H.root_head.z - 0.01 + dz)), yaw=0.0, flex=flex * 0.3, side=side)
    H.key_spine(f, flex=flex, twist=twist, side=side, head=(hp, hy))

# hands grip the box sides (wrist targets ride with the box)
GRIP_L = V((0.178, 0.050, -0.135)); GRIP_R = V((-0.178, 0.050, -0.135))
HAND_SIGN = float(os.environ.get("HAND_SIGN", "1"))
def key_hands(f):
    M = box_M(f); Rb = M.to_3x3()
    for s, g, sx in (("L", GRIP_L, 1), ("R", GRIP_R, -1)):
        W = M @ g
        d = Rb @ V((0.0, -1.0, 0.45)).normalized()         # fingers forward along the box side
        n = Rb @ V((sx * HAND_SIGN, 0.0, 0.0))             # back of the hand faces out
        pole = M @ V((sx * 0.55, 0.45, -0.35))
        H.key_hand(s, f, W, d, n, pole)
for f in list(range(1, F_END + 1, 2)) + [F_END]:
    key_hands(f)
# finger curl around the front edge, thumbs over the top edge
CURL = float(os.environ.get("CURL", "1"))
for f in (1, F_END):
    for s in "LR":
        for k in range(2, 6):
            for j, a in ((1, 25), (2, 45), (3, 35)):
                n = "finger%d-%d.%s" % (k, j, s); pb = R.PB[n]
                pb.rotation_quaternion = Quaternion(V((1, 0, 0)), R_(a * CURL)); pb.keyframe_insert("rotation_quaternion", frame=f)
        for j, a in ((2, 15), (3, 20)):
            n = "finger1-%d.%s" % (j, s); pb = R.PB[n]
            pb.rotation_quaternion = Quaternion(V((1, 0, 0)), R_(a * CURL)); pb.keyframe_insert("rotation_quaternion", frame=f)
bpy.ops.object.mode_set(mode='OBJECT')

# ------------------------------------------------------------------ bullet path
# world y of the nose before the hit; after the hit, depth inside the box (local y of the nose)
pre = pchip([(1, -30.0), (60, -19.8), (120, -9.2), (145, -3.2), (F_WALL, -0.03), (172, 0.10), (195, 0.30),
             (241, 0.80), (300, 1.55), (350, 2.22), (F_HIT, 2.90 - 0.0)])
depth = pchip([(F_HIT, -0.070), (430, -0.0675), (560, -0.0655), (661, -0.0640), (751, -0.0620), (790, -0.0565), (815, -0.0505),
               (845, -0.0460), (900, -0.0405), (1000, -0.0210), (1030, -0.0165), (1060, -0.0125), (1081, -0.0060),
               (1150, -0.0012), (F_STOP, 0.0)])
def nose_world(f):
    if f <= F_HIT:
        return V((0.0, pre(f), 1.30))
    M = box_M(f)
    return M @ V((0.0, depth(f), 0.05))
def bullet_dir(f):
    if f <= F_HIT: return V((0, 1, 0))
    return (box_M(f).to_3x3() @ V((0, 1, 0))).normalized()
bullet.rotation_mode = "QUATERNION"
for f in range(1, F_END + 1):
    p = nose_world(f); bullet.location = p
    q = V((0, 1, 0)).rotation_difference(bullet_dir(f))
    q = q @ Quaternion(V((0, 1, 0)), f * 0.35 if f < F_HIT else F_HIT * 0.35 + 0.35 * 60 * (1 - math.exp(-(f - F_HIT) / 60)))  # spin
    bullet.rotation_quaternion = q
    kf(bullet, "location", f); kf(bullet, "rotation_quaternion", f)
# nose mushrooms in the cover and keeps flattening through the discs
mk = bullet.data.shape_keys.key_blocks["mushroom"]
for f, v in ((F_HIT, 0.0), (F_HIT + 70, 0.55), (790, 0.75), (900, 1.0)):
    mk.value = v; mk.keyframe_insert("value", frame=f)
trail = bpy.data.objects["Bullet_trail"]
for f, s_, v in ((1, 1.0, False), (140, 1.0, False), (F_WALL, 0.25, False), (F_WALL + 6, 0.05, True)):
    trail.scale = (1, s_, 1); kf(trail, "scale", f)
    trail.hide_render = v; kf(trail, "hide_render", f)
trail.scale = (1, 0.6, 1); kf(trail, "scale", 60)

# ------------------------------------------------------------------ cutaway value (local x above which the box is see-through)
cutnode = bpy.data.node_groups["CutAway"].nodes["cut"]
for f, v in ((1, 1.0), (752, 1.0), (800, 0.0), (1352, 0.0), (1392, 1.0)):
    cutnode.outputs[0].default_value = v; cutnode.outputs[0].keyframe_insert("default_value", frame=f)
for o2 in [o for o in bpy.data.objects if o.get("xp_of")]:
    o1 = bpy.data.objects[o2["xp_of"]]; full = bpy.data.objects[o1.name + "_full"]
    for ob_, vis in ((full, [(1, False), (752, True), (1393, False)]), (o1, [(1, True), (752, False), (1393, True)]), (o2, [(1, True), (752, False), (801, True), (1352, False), (1393, True)])):
        for f, hidden in vis:
            ob_.hide_render = hidden; kf(ob_, "hide_render", f)
    if o1.name.startswith("Disc_"):
        full.hide_render = True; kf(full, "hide_render", 1393)
hon = bpy.data.materials["M_box_cover"].node_tree.nodes["hole_on"]
for f, v in ((1, 0.0), (F_HIT + 8, 0.0), (F_HIT + 30, 1.0)):
    hon.outputs[0].default_value = v; hon.outputs[0].keyframe_insert("default_value", frame=f)
crR = bpy.data.materials["M_box_cover"].node_tree.nodes["crack_radius"]
for f, v in ((1, 0.001), (F_HIT, 0.001), (F_HIT + 20, 0.012), (600, 0.03), (661, 0.045), (720, 0.11), (760, 0.16), (900, 0.20)):
    crR.outputs[0].default_value = v; crR.outputs[0].keyframe_insert("default_value", frame=f)

# ------------------------------------------------------------------ shards (discs split when the nose reaches them)
DISC_HIT = {"Disc_1": 790, "Disc_2": 815, "Disc_3": 1030}
for dn, fh in DISC_HIT.items():
    d = bpy.data.objects[dn]
    hitp = V((0.0, d.location.y, 0.05))
    for dd in (d, bpy.data.objects[dn + "_xp"]):
        dd.hide_render = False; kf(dd, "hide_render", fh - 1); dd.hide_render = True; kf(dd, "hide_render", fh)
        dd.hide_viewport = False; kf(dd, "hide_viewport", fh - 1); dd.hide_viewport = True; kf(dd, "hide_viewport", fh)
    for o in [o for o in bpy.data.objects if o.get("disc") == dn]:
        home = V(o["home"]); rel = home - hitp; rel.y = 0; dist = rel.length
        o.hide_render = True; kf(o, "hide_render", fh - 1); o.hide_render = False; kf(o, "hide_render", fh)
        o.hide_viewport = True; kf(o, "hide_viewport", fh - 1); o.hide_viewport = False; kf(o, "hide_viewport", fh)
        strength = max(0.0, 1 - dist / 0.06)
        dirv = rel.normalized() if dist > 1e-4 else V((1, 0, 0))
        spd = (0.006 + 0.02 * strength) * (0.6 + 0.8 * random.random())
        ax = V((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1))).normalized()
        spin = random.uniform(0.4, 2.2) * strength
        o.rotation_mode = "QUATERNION"
        for f in range(fh - 1, min(F_END, fh + 240) + 1, 3):
            t = max(0, f - fh) / 60.0
            g = 1 - math.exp(-t * 1.8)
            o.location = home + dirv * spd * g + V((0, 0.004 * strength * g, 0))
            o.rotation_quaternion = Quaternion(ax, spin * g)
            kf(o, "location", f); kf(o, "rotation_quaternion", f)

# pages bow ahead of the nose, then stay bent
for i, pgn in enumerate(sorted(o.name for o in bpy.data.objects if o.name.startswith("Page_") and not o.name.endswith("_xp") and not o.name.endswith("_full"))):
  pgf = bpy.data.objects[pgn + "_full"]
  pgf.data.shape_keys.key_blocks["bulge"].value = 0.0
  for pg in (bpy.data.objects[pgn], bpy.data.objects[pgn + "_xp"]):
    py = -0.040 + i * 0.00105
    kb = pg.data.shape_keys.key_blocks["bulge"]
    fa = min(range(F_HIT, F_STOP), key=lambda f: abs(depth(f) - (py - 0.004)))
    fb = min(range(F_HIT, F_STOP), key=lambda f: abs(depth(f) - py))
    for f, v in ((1, 0.0), (fa, 0.0), (fb, 1.0), (fb + 40, 0.55)):
        kb.value = v; kb.keyframe_insert("value", frame=f)
# a soft studio key on the cross-section while it is open
kl = bpy.data.lights.new("L_cutaway_key", "AREA"); kl.size = 0.3; kl.color = (0.9, 0.95, 1.0)
klo = bpy.data.objects.new("L_cutaway_key", kl); bpy.data.collections["FX"].objects.link(klo)
klo.parent = broot; klo.location = (0.30, -0.12, 0.30); klo.rotation_euler = (0, R_(60), R_(30))
klo.rotation_mode = "QUATERNION"; klo.rotation_quaternion = (V((0, 0, 0.0)) - V((0.30, -0.12, 0.30))).to_track_quat('-Z', 'Y')
for f, e in ((1, 0.0), (750, 0.0), (800, 30.0), (1350, 30.0), (1395, 0.0)):
    kl.energy = e; kl.keyframe_insert("energy", frame=f)

# ------------------------------------------------------------------ energy rings (each layer contact)
ringmat = bpy.data.materials.new("M_energy_ring"); ringmat.use_nodes = True
nt = ringmat.node_tree; nt.nodes.clear()
oi = nt.nodes.new("ShaderNodeObjectInfo"); em = nt.nodes.new("ShaderNodeEmission"); tr = nt.nodes.new("ShaderNodeBsdfTransparent")
ad = nt.nodes.new("ShaderNodeAddShader"); mo = nt.nodes.new("ShaderNodeOutputMaterial")
mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; mul.inputs[1].default_value = 40.0
nt.links.new(oi.outputs["Color"], em.inputs["Color"]); nt.links.new(oi.outputs["Alpha"], mul.inputs[0]); nt.links.new(mul.outputs[0], em.inputs["Strength"])
nt.links.new(em.outputs[0], ad.inputs[0]); nt.links.new(tr.outputs[0], ad.inputs[1]); nt.links.new(ad.outputs[0], mo.inputs[0])
C_FX = bpy.data.collections["FX"]
RING_F = [(F_HIT + 2, (1.0, 0.55, 0.15)), (790, (0.3, 0.8, 1.0)), (815, (0.3, 0.8, 1.0)), (845, (1.0, 0.7, 0.3)), (905, (1.0, 0.85, 0.5)),
          (940, (1.0, 0.85, 0.5)), (975, (1.0, 0.85, 0.5)), (1030, (0.3, 0.8, 1.0)), (1062, (1.0, 0.7, 0.3)), (1110, (1.0, 0.5, 0.2))]
for i, (fr, col) in enumerate(RING_F):
    bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.035, major_segments=64, minor_segments=8)
    o = bpy.context.active_object; o.name = "EnergyRing_%02d" % i
    for c_ in list(o.users_collection): c_.objects.unlink(o)
    C_FX.objects.link(o); o.data.materials.append(ringmat)
    o.parent = broot; o.rotation_euler = (R_(90), 0, 0); o.location = (0, depth(fr) - 0.006, 0.05)
    big = 0.05 if i else 0.09
    for f, s_, a in ((fr - 1, 0.002, 0.0), (fr, 0.004, 1.0), (fr + 30, big * 0.7, 0.5), (fr + 70, big, 0.0)):
        o.scale = (s_, s_, s_); o.color = (*col, a); kf(o, "scale", f); kf(o, "color", f)
    o.hide_render = True; kf(o, "hide_render", fr - 2); o.hide_render = False; kf(o, "hide_render", fr - 1); o.hide_render = True; kf(o, "hide_render", fr + 72)

# ------------------------------------------------------------------ wall breach debris + dust
def mat_dust(name, col, dens):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt_ = m.node_tree; nt_.nodes.clear()
    vol = nt_.nodes.new("ShaderNodeVolumePrincipled"); vol.inputs["Color"].default_value = (*col, 1)
    nz = nt_.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 6; nz.inputs["Detail"].default_value = 4
    gr = nt_.nodes.new("ShaderNodeTexGradient"); gr.gradient_type = "SPHERICAL"; tc_ = nt_.nodes.new("ShaderNodeTexCoord")
    mm = nt_.nodes.new("ShaderNodeMath"); mm.operation = "MULTIPLY"; m2 = nt_.nodes.new("ShaderNodeMath"); m2.operation = "MULTIPLY"
    oi_ = nt_.nodes.new("ShaderNodeObjectInfo"); m3 = nt_.nodes.new("ShaderNodeMath"); m3.operation = "MULTIPLY"; m3.inputs[1].default_value = dens
    nt_.links.new(tc_.outputs["Object"], gr.inputs[0]); nt_.links.new(gr.outputs[0], mm.inputs[0]); nt_.links.new(nz.outputs[0], mm.inputs[1])
    nt_.links.new(mm.outputs[0], m2.inputs[0]); nt_.links.new(oi_.outputs["Alpha"], m2.inputs[1]); nt_.links.new(m2.outputs[0], m3.inputs[0])
    nt_.links.new(m3.outputs[0], vol.inputs["Density"])
    o_ = nt_.nodes.new("ShaderNodeOutputMaterial"); nt_.links.new(vol.outputs[0], o_.inputs["Volume"])
    return m
M_dust = mat_dust("M_dust", (0.85, 0.82, 0.76), 5.0)
M_drydust = mat_dust("M_drywall_dust", (0.95, 0.95, 0.93), 4.0)
M_splinter = bpy.data.materials["M_stud"]; M_chip = bpy.data.materials["M_siding_blue"]; M_dw = bpy.data.materials["M_drywall"]
M_fluff = bpy.data.materials["M_insulation"]

def piece(name, dims, mat):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = V((v.co.x * dims[0], v.co.y * dims[1], v.co.z * dims[2])) + V([random.uniform(-0.15, 0.15) * d for d in dims])
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.materials.append(mat)
    o = bpy.data.objects.new(name, me); C_FX.objects.link(o); return o

def ballistic(o, p0, v0, f0, f1, grav=0.4, drag=0.8, spin=6.0, floor=None, step=2):
    """v0 in m/s of slow-motion film time; keys every step frames; hides before f0"""
    ax = V((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1))).normalized(); o.rotation_mode = "QUATERNION"
    o.hide_render = True; kf(o, "hide_render", f0 - 1); o.hide_render = False; kf(o, "hide_render", f0)
    o.location = p0; kf(o, "location", f0 - 1)
    p = p0.copy(); v = v0.copy(); landed = False
    for f in range(f0, f1 + 1, step):
        dt = step / 60.0
        if not landed:
            v = v * math.exp(-drag * dt) + V((0, 0, -grav * dt)); p = p + v * dt
            if floor is not None and p.z < floor: p.z = floor; landed = True
        o.location = p; o.rotation_quaternion = Quaternion(ax, spin * (1 - math.exp(-(f - f0) / 90.0)) * (0.3 if landed else 1))
        kf(o, "location", f); kf(o, "rotation_quaternion", f)

HOLE = V((0, 0, 1.30))
# outside face: siding splinters and paint chips blown back toward the lawn
for i in range(36):
    o = piece("Splinter_out_%02d" % i, (random.uniform(0.004, 0.012), random.uniform(0.002, 0.004), random.uniform(0.01, 0.05)), random.choice([M_chip, M_splinter]))
    a = random.uniform(0, 6.28); r = random.uniform(0.01, 0.07)
    p0 = HOLE + V((r * math.cos(a), -0.02, r * math.sin(a)))
    v0 = V((math.cos(a) * random.uniform(0.1, 0.5), -random.uniform(0.15, 0.6), math.sin(a) * random.uniform(0.1, 0.5) + 0.1))
    ballistic(o, p0, v0, F_WALL + random.randint(0, 4), F_END, grav=0.25)
# inside: drywall chunks + splinters + insulation fluff in a cone that follows the bullet into the room
for i in range(70):
    kind = random.random()
    if kind < 0.5:
        o = piece("Drywall_chunk_%02d" % i, [random.uniform(0.006, 0.03)] * 2 + [random.uniform(0.004, 0.012)], M_dw)
    elif kind < 0.8:
        o = piece("Splinter_in_%02d" % i, (random.uniform(0.003, 0.008), random.uniform(0.02, 0.07), random.uniform(0.003, 0.008)), M_splinter)
    else:
        o = piece("Fluff_%02d" % i, [random.uniform(0.008, 0.02)] * 3, M_fluff)
    a = random.uniform(0, 6.28); r = random.uniform(0.04, 0.10)
    p0 = HOLE + V((r * math.cos(a), 0.16, r * math.sin(a)))
    cone = random.uniform(0.18, 0.5)
    v0 = V((math.cos(a) * cone, random.uniform(0.25, 0.9), math.sin(a) * cone))
    ballistic(o, p0, v0, 190 + random.randint(0, 10), F_END, grav=0.35, floor=FZ + 0.005)
# dust puffs (volumes) both sides of the wall, expanding and thinning
def puff(name, p0, drift, f0, r0, r1, mat, dur=240):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.0, location=p0); o = bpy.context.active_object; o.name = name
    for c in list(o.users_collection): c.objects.unlink(o)
    C_FX.objects.link(o); o.data.materials.append(mat)
    o.hide_render = True; kf(o, "hide_render", f0 - 1); o.hide_render = False; kf(o, "hide_render", f0); o.hide_render = True; kf(o, "hide_render", f0 + dur)
    for f, u in ((f0, 0.0), (f0 + dur * 0.25, 0.45), (f0 + dur * 0.6, 0.8), (f0 + dur, 1.0)):
        s_ = r0 + (r1 - r0) * u; o.scale = (s_, s_ * 0.8, s_); o.location = p0 + drift * u
        o.color = (1, 1, 1, (1 - u) ** 1.5); kf(o, "scale", int(f)); kf(o, "location", int(f)); kf(o, "color", int(f))
for i in range(4):
    puff("Dust_out_%d" % i, HOLE + V((random.uniform(-0.05, 0.05), -0.08, random.uniform(-0.05, 0.05))), V((random.uniform(-0.3, 0.3), -0.4, 0.15)), F_WALL + i * 3, 0.02, 0.35, M_dust, 300)
for i in range(6):
    puff("Dust_in_%d" % i, HOLE + V((random.uniform(-0.05, 0.05), 0.25 + 0.05 * i, random.uniform(-0.05, 0.05))), V((random.uniform(-0.3, 0.3), 0.5 + 0.1 * i, random.uniform(-0.1, 0.2))), 188 + 4 * i, 0.03, 0.45, M_drydust, 360)
# impact puff + flakes at the box cover
for i in range(24):
    o = piece("Cover_flake_%02d" % i, [random.uniform(0.002, 0.006)] * 2 + [0.0008], bpy.data.materials["M_box_shell"])
    a = random.uniform(0, 6.28); p0 = nose_world(F_HIT) + V((0.004 * math.cos(a), -0.003, 0.004 * math.sin(a)))
    v0 = V((math.cos(a) * random.uniform(0.02, 0.08), -random.uniform(0.02, 0.1), math.sin(a) * random.uniform(0.02, 0.08)))
    ballistic(o, p0, v0, F_HIT + random.randint(0, 6), 1300, grav=0.05, drag=3.0, step=3)
puff("Dust_box", nose_world(F_HIT) + V((0, -0.02, 0)), V((0, -0.08, 0.04)), F_HIT + 1, 0.01, 0.10, M_drydust, 260)

# ------------------------------------------------------------------ the world in slow motion: grass, fan, motes
def bpos(f): return nose_world(f)
for o in bpy.data.objects:
    if o.name.startswith("Grass_") and abs(o.location.x) < 1.6:
        fy = min(range(1, F_WALL), key=lambda f: abs(pre(f) - o.location.y))
        st = max(0.0, 1 - abs(o.location.x) / 1.6) * 0.35
        base = o.rotation_euler.copy()
        for f, k in ((fy - 4, 0.0), (fy + 6, 1.0), (fy + 40, -0.35), (fy + 90, 0.1), (fy + 140, 0.0)):
            o.rotation_euler = (base.x + st * k * 0.6, base.y + st * k * (0.5 if o.location.x > 0 else -0.5), base.z)
            kf(o, "rotation_euler", max(1, f))
fan = [o for o in bpy.data.objects if o.name.startswith("ceiling_fan_blades")]
for o in fan:
    o.rotation_mode = "XYZ"; z0 = o.rotation_euler.z
    ang = 0.0
    for f in range(1, F_END + 1, 10):
        spd = 0.25 if f < 150 else (0.02 if f < 1360 else 0.02 + 0.23 * smooth((f - 1360) / 120))
        o.rotation_euler.z = z0 + ang; kf(o, "rotation_euler", f, 2); ang += spd * 10 / 6
# dust motes in the window light
bm = bmesh.new()
for i in range(260):
    c = V((random.uniform(-2.2, 1.0), random.uniform(0.3, 3.8), random.uniform(0.5, 2.5)))
    r = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=random.uniform(0.0015, 0.004))
    bmesh.ops.translate(bm, verts=r["verts"], vec=c)
me = bpy.data.meshes.new("Motes"); bm.to_mesh(me); bm.free()
motes = bpy.data.objects.new("Dust_motes", me); bpy.data.collections["Bedroom"].objects.link(motes)
mm_ = bpy.data.materials.new("M_mote"); mm_.use_nodes = True; bb_ = mm_.node_tree.nodes["Principled BSDF"]
bb_.inputs["Emission Color"].default_value = (1.0, 0.95, 0.85, 1); bb_.inputs["Emission Strength"].default_value = 3.0
me.materials.append(mm_)
for f, z, y in ((1, 0.0, 0.0), (750, -0.03, 0.03), (F_END, -0.08, 0.05)):
    motes.location = (0, y, z); kf(motes, "location", f)

# ------------------------------------------------------------------ camera: one continuous Catmull-Rom move
cam_d = bpy.data.cameras.new("CAM_Film"); cam_d.sensor_fit = "AUTO"; cam_d.clip_start = 0.004; cam_d.clip_end = 300
cam = bpy.data.objects.new("CAM_Film", cam_d); sc.collection.objects.link(cam); sc.camera = cam
B = bpos
def behind(f, back, up=0.0, side=0.0):
    return B(f) + V((side, -back, up))
CK = [  # frame, camera position, aim point, lens
    (1,    behind(1, 0.9, 0.18, 0.14),     V((0.0, -20.0, 1.32)), 30),
    (45,   behind(45, 0.55, 0.08, 0.10),   V((0.0, -12.0, 1.30)), 32),
    (95,   V((0.9, -14.0, 0.45)),       V((0.0, -2.0, 1.55)), 26),
    (130,  V((0.25, -6.5, 1.20)),       V((0.0, 0.0, 1.30)), 32),
    (150,  behind(150, 0.55, 0.04, 0.06), V((0.0, 0.3, 1.30)), 36),
    (F_WALL, behind(F_WALL, 0.40, 0.02, 0.03), V((0.0, 0.5, 1.30)), 38),
    (175,  behind(175, 0.30, 0.0, 0.0),  V((0.0, 0.8, 1.30)), 38),
    (200,  behind(200, 0.26, 0.0, 0.0),  V((0.0, 1.5, 1.32)), 36),
    (228,  V((0.06, 0.42, 1.36)),       V((0.0, 2.0, 1.35)), 30),
    (270,  V((0.62, 0.62, 1.62)),       V((0.0, 2.2, 1.38)), 26),
    (330,  V((1.25, 1.55, 1.48)),       V((0.0, 2.55, 1.36)), 28),
    (378,  V((0.55, 2.52, 1.36)),       V((0.0, 2.90, 1.31)), 40),
    (420,  V((0.30, 2.50, 1.40)),       V((0.0, 2.90, 1.33)), 38),
    (480,  V((-0.05, 2.18, 1.56)),      V((0.0, 2.97, 1.45)), 34),
    (540,  V((-0.62, 2.32, 1.36)),      V((0.0, 2.95, 1.38)), 34),
    (600,  V((-0.42, 2.52, 1.12)),      V((0.0, 2.92, 1.36)), 32),
    (650,  V((-0.13, 2.70, 1.29)),      V((0.0, 2.90, 1.31)), 40),
    (695,  V((-0.045, 2.795, 1.335)),   V((0.0, 2.92, 1.30)), 50),
    (735,  V((0.06, 2.805, 1.27)),      V((0.0, 2.92, 1.31)), 55),
    (772,  V((0.20, 2.81, 1.33)),       V((0.0, 2.93, 1.30)), 50),
    (805,  V((0.235, 2.90, 1.325)),     V((0.0, 2.925, 1.30)), 50),
]
def nose_cam(f, dx, dz, dy=-0.016, ady=-0.012):
    p = B(f); return (p + V((dx, dy, dz)), p + V((0, ady, 0)))
for f, dx, dz, lens in ((845, 0.22, 0.07, 50), (900, 0.19, 0.09, 55), (960, 0.18, 0.05, 60), (1020, 0.19, 0.09, 62), (1075, 0.20, 0.07, 62)):
    c, a = nose_cam(f, dx, dz); CK.append((f, c, a, lens))
CK += [
    (1140, V((0.50, 2.90, 1.52)),       V((0.0, 2.975, 1.27)), 46),
    (1200, V((0.50, 2.86, 1.46)),       V((0.0, 2.975, 1.27)), 50),
]
cB = lambda: B(1240)
for f, a, h, r, lens in ((1245, -35, 0.06, 0.20, 55), (1290, 0, 0.09, 0.19, 55), (1335, 22, 0.12, 0.20, 50)):
    c0 = B(f); c = c0 + V((r * math.cos(R_(a)), r * math.sin(R_(a)), h)); CK.append((f, c, c0 + V((0, -0.01, 0)), lens))
CK += [
    (1395, V((0.80, 2.20, 1.55)),       V((0.0, 2.95, 1.30)), 35),
    (1445, V((1.05, 1.95, 1.62)),       V((0.0, 2.95, 1.40)), 30),
    (1500, V((1.20, 1.90, 1.66)),       V((0.0, 3.0, 1.45)), 30),
]
fc = catmull([(f, c) for f, c, a, l in CK]); fa = catmull([(f, a) for f, c, a, l in CK]); fl = catmull([(f, float(l)) for f, c, a, l in CK])
cam_d.dof.use_dof = True; cam_d.dof.aperture_fstop = 8.0
CAMLOG = []
for f in range(1, F_END + 1):
    c = fc(f); a = fa(f)
    cam.location = c
    d = (a - c).normalized()
    cam.rotation_mode = "QUATERNION"
    q = d.to_track_quat('-Z', 'Y'); cam.rotation_quaternion = q
    cam_d.lens = fl(f); cam_d.dof.focus_distance = max(0.03, (B(f) - c).length if 150 < f < 1350 else (a - c).length)
    kf(cam, "location", f); kf(cam, "rotation_quaternion", f); cam_d.keyframe_insert("lens", frame=f); cam_d.dof.keyframe_insert("focus_distance", frame=f)
    CAMLOG.append((f, tuple(round(x, 4) for x in c), tuple(round(x, 4) for x in a), round(fl(f), 1)))
json.dump(CAMLOG[::10], open(os.path.join(ROOT, "camera_path.json"), "w"))
json.dump([{"beat": b, "frame": f, "first_words": w} for b, f, w in BEATS], open(os.path.join(ROOT, "beats.json"), "w"), indent=1)
sc.cycles.transparent_max_bounces = 64
sc.frame_start, sc.frame_end = 1, F_END
print("ANIM_DONE")
bpy.ops.wm.save_as_mainfile(filepath=OUT)
