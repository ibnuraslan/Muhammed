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

BOX_C = V((0.0, 2.97, 1.42))
broot = bpy.data.objects["BoxRoot"]
bullet = bpy.data.objects["Bullet"]

def kf(o, path, f, idx=-1):
    o.keyframe_insert(path, frame=f, index=idx)

# ------------------------------------------------------------------ box motion (world), driven by hands
def shove(f):
    if f <= F_HIT: return 0.0
    u = (f - F_HIT) / 60.0
    return 0.085 * (1 - math.exp(-u * 2.2)) * (1 + 0.12 * math.exp(-u) * math.sin(u * 4))
def box_pose(f):
    """returns (location, euler) of BoxRoot"""
    loc = BOX_C.copy(); rx = 0.0; rz = 0.0
    # breathing before the hit
    loc.z += 0.004 * math.sin(f / 60 * 2 * math.pi * 0.25)
    # unboxing: he turns the new box in his hands near his chest, admiring it; squares it up just before the hit
    fade = 1 - smooth((f - 250) / 110.0)
    rz += R_(10) * math.sin(2 * math.pi * f / 180.0) * fade; rx += R_(-6) * fade
    loc.z -= 0.0 * fade; loc.y -= 0.0 * fade; loc.x += 0.02 * math.sin(2 * math.pi * f / 180.0 + 0.7) * fade
    # impact shove (slow motion): driven back into his chest, he staggers half a step
    loc.y += shove(f) + 0.003 * (1 - math.exp(-max(0, f - F_HIT) / 30.0)) * (f > F_HIT)
    if f > F_HIT:
        u = (f - F_HIT) / 50.0
        rx += R_(-4.0) * (1 - math.exp(-u * 2.0)) * (1 + 0.3 * math.exp(-u) * math.sin(u * 5))
    # beat 10: lowers the box and tilts the face up toward his eyes, then holds it out a little
    if f > 1355:
        u = smooth((f - 1355) / 70.0)
        loc.z -= 0.04 * u; loc.y -= 0.02 * u; rx += R_(-10) * u
        w = smooth((f - 1430) / 50.0)
        loc.z += 0.01 * w; rx += R_(4) * w
    return loc, Euler((rx, 0, rz))

for f in range(1, F_END + 1, 2):
    l, e = box_pose(f); broot.location = l; broot.rotation_euler = e
    kf(broot, "location", f); kf(broot, "rotation_euler", f)
def box_M(f):
    l, e = box_pose(f); return Matrix.Translation(l) @ e.to_matrix().to_4x4()

# ------------------------------------------------------------------ man
man = bpy.data.objects["Gamer"]
R = make_human_ctrl(man); H = Human(R)
MAN = V((0.0, 3.255, 0.0))
FZ = 0.25   # bedroom floor
bpy.context.view_layer.objects.active = man; bpy.ops.object.mode_set(mode='POSE')
# feet planted; after the hit the right foot steps back ~14 cm (stagger), the left stays put
STEP = [(1, 0.0, 0.0), (F_HIT + 20, 0.0, 0.0), (F_HIT + 60, 0.07, 0.045), (F_HIT + 100, 0.14, 0.0), (F_END, 0.14, 0.0)]
for s, dx, keys in (("L", 0.13, [(1, 0, 0), (F_END, 0, 0)]), ("R", -0.13, STEP)):
    for f, sy, lift in keys:
        xy = V((MAN.x + dx, MAN.y + 0.02 + (0.03 if s == "R" else -0.02) + sy))
        a = H.ankle[s]; z = FZ + a.z + 0.0165 + lift
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
        dy += shove(f); dz -= 0.02 * k; flex -= 7 * k; hp -= 6 * k * math.exp(-v * 0.3); side += 2 * math.sin(v * 1.3) * math.exp(-v * 0.5)
        hp += 18 * smooth((f - 600) / 300.0)   # stares down at the box as it cracks
    # beat 10: looks down at the hole, breath, then up to the camera
    w = smooth((f - 1360) / 60.0); hp += 12 * w; flex += 6 * w; dz -= 0.02 * w
    z = smooth((f - 1415) / 50.0)
    hp -= 40 * z; hy += 34 * z; twist += 4 * z
    # acting pass: weight shifts foot to foot, head and shoulders follow the box he is turning, small tremor after the hit
    fade = 1 - smooth((f - 250) / 110.0)
    ws = math.sin(2 * math.pi * f / 240.0)
    wx = 0.016 * ws; side += 2.5 * ws; dz -= 0.006 * abs(ws)
    twist += 5 * math.sin(2 * math.pi * f / 180.0 + 0.4) * fade; hy += 7 * math.sin(2 * math.pi * f / 180.0 + 0.9) * fade
    if f > F_HIT:
        e = math.exp(-(f - F_HIT) / 420.0); hp += 1.6 * math.sin(f * 0.11) * e; hy += 1.2 * math.sin(f * 0.07 + 1) * e
    return dy, dz, flex, twist, side, hp, hy, wx

for f in list(range(1, F_END + 1, 4)) + [F_END]:
    dy, dz, flex, twist, side, hp, hy, wx = man_state(f)
    H.key_root(f, V((MAN.x + wx, MAN.y + H.root_head.y + dy, FZ + H.root_head.z - 0.01 + dz)), yaw=0.0, flex=flex * 0.3, side=side)
    H.key_spine(f, flex=flex, twist=twist, side=side, head=(hp, hy))

JAWK = [(1, 0.0), (F_HIT + 10, 0.0), (F_HIT + 90, 14.0)] + [(F_HIT + 90 + 50 * i, 14.0 + (2.5 if i % 2 else -2.5)) for i in range(1, 16)] + [(1300, 10.0), (1420, 16.0), (1450, 12.0), (1475, 15.0), (F_END, 10.0)]
for f, a in sorted(JAWK):
    pb = R.PB["jaw"]; pb.rotation_quaternion = Quaternion(V((1, 0, 0)), R_(a * float(os.environ.get("JAW", "1")))); pb.keyframe_insert("rotation_quaternion", frame=f)
# face: smile while unboxing (mouth corners up/back, cheeks up), eyes wide open after the hit
SM = float(os.environ.get("SMILE_SIGN", "1")); LID = float(os.environ.get("LID_SIGN", "-1"))
def key_face(f, smile, wide):
    for sd, sx in (("L", 1), ("R", -1)):
        for n, d in (("oris03.", V((sx * 0.003, 0.004, 0.006))), ("oris07.", V((sx * 0.003, 0.004, 0.004))),
                     ("risorius03.", V((sx * 0.002, 0.003, 0.005))), ("levator05.", V((0, 0.001, 0.002))),
                     ("orbicularis04.", V((0, 0, 0.002)))):
            nm = n + sd; pb = R.PB[nm]
            pb.location = R.rest(nm).to_3x3().inverted() @ (d * smile * SM); pb.keyframe_insert("location", frame=f)
        for nm, a in (("orbicularis03." + sd, -16 * wide * LID), ("orbicularis04." + sd, 8 * wide * LID)):
            pb = R.PB[nm]; pb.rotation_quaternion = Quaternion(V((1, 0, 0)), R_(a)); pb.keyframe_insert("rotation_quaternion", frame=f)
for f, sm_, wd in ((1, 0.6, 0.0), (90, 1.0, 0.0), (200, 0.8, 0.0), (300, 1.0, 0.0), (F_HIT, 0.9, 0.1), (F_HIT + 30, 0.0, 0.9),
                   (700, -0.2, 1.0), (1300, -0.2, 0.8), (1380, 0.0, 0.6), (1440, -0.1, 1.0), (F_END, -0.1, 0.95)):
    key_face(f, sm_, wd)
# blinks: lids close fast and reopen, every ~2-3 s (keyed on top of the lid curves)
def blink_keys():
    act = man.animation_data.action
    BL = [60, 205, 330, 470, 600, 760, 900, 1060, 1210, 1330, 1395, 1488]
    for sd in "LR":
        nm = "orbicularis03." + sd; pb = R.PB[nm]
        fcs = [fc for fc in act.fcurves if fc.data_path == 'pose.bones["%s"].rotation_quaternion' % nm] if hasattr(act, "fcurves") else []
        for fb in BL:
            if fb > F_END - 4: continue
            qs = []
            for ff in (fb - 3, fb + 4):
                sc.frame_set(ff); qs.append((ff, pb.rotation_quaternion.copy()))
            for ff, q in qs:
                pb.rotation_quaternion = q; pb.keyframe_insert("rotation_quaternion", frame=ff)
            pb.rotation_quaternion = Quaternion(V((1, 0, 0)), R_(22 * LID)); pb.keyframe_insert("rotation_quaternion", frame=fb)
# hands grip the box sides (wrist targets ride with the box)
GX = float(os.environ.get("GX", "0.178")); GZ = float(os.environ.get("GZ", "-0.12")); GY = float(os.environ.get("GY", "0.02"))
GRIP_L = V((GX, GY, GZ)); GRIP_R = V((-GX, GY, GZ))
HAND_SIGN = float(os.environ.get("HAND_SIGN", "1"))
def key_hands(f):
    M = box_M(f); Rb = M.to_3x3()
    for s, g, sx in (("L", GRIP_L, 1), ("R", GRIP_R, -1)):
        W = M @ g
        d = Rb @ V((0.0, -0.12, -1.0)).normalized()       # fingers point down the box side toward the bottom-front corner
        n = Rb @ V((-sx * HAND_SIGN, 0.0, 0.0))           # palm flat against the side
        pole = M @ V((sx * 0.55, 0.45, -0.35))
        H.key_hand(s, f, W, d, n, pole)
for f in list(range(1, F_END + 1, 2)) + [F_END]:
    key_hands(f)
blink_keys()
# finger curl around the front edge, thumbs over the top edge
CURL = float(os.environ.get("CURL", "1"))
for f in (1, F_END):
    for s in "LR":
        for k in range(2, 6):
            for j, a in {2: ((1, 25), (2, 55), (3, 35)), 3: ((1, 28), (2, 60), (3, 35)), 4: ((1, 30), (2, 60), (3, 35)), 5: ((1, 32), (2, 55), (3, 30))}[k]:
                n = "finger%d-%d.%s" % (k, j, s); pb = R.PB[n]
                pb.rotation_quaternion = Quaternion(V((1, 0, 0)), R_(a * CURL)); pb.keyframe_insert("rotation_quaternion", frame=f)
        TZ = float(os.environ.get("TZ", "35")); TX = float(os.environ.get("TX", "-20"))
        pb = R.PB["finger1-1." + s]; pb.rotation_quaternion = Quaternion(V((0, 0, 1)), R_(TZ if s == "R" else -TZ)) @ Quaternion(V((1, 0, 0)), R_(TX)); pb.keyframe_insert("rotation_quaternion", frame=f)
        for j, a in ((2, 5), (3, 5)):   # thumb rests on the box side, opposing the fingers underneath
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
        return V((0.0, pre(f), 1.47))
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
trail = bpy.data.objects["Bullet_trail"]; trail.hide_render = True


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
for f, v in ((1, 0.0003), (F_HIT, 0.0003), (F_HIT + 15, 0.05), (661, 0.075), (720, 0.13), (760, 0.16), (900, 0.20)):
    crR.outputs[0].default_value = v; crR.outputs[0].keyframe_insert("default_value", frame=f)

# deep teal-navy studio card behind the cross-section, faded in only while it is open
mbd = bpy.data.materials.new("M_backdrop"); mbd.use_nodes = True; nt_ = mbd.node_tree; nt_.nodes.clear()
tc_ = nt_.nodes.new("ShaderNodeTexCoord"); gr_ = nt_.nodes.new("ShaderNodeTexGradient"); gr_.gradient_type = "SPHERICAL"
mp_ = nt_.nodes.new("ShaderNodeMapping"); mp_.inputs["Scale"].default_value = (1.2, 1.2, 1.2)
cr_ = nt_.nodes.new("ShaderNodeValToRGB"); cr_.color_ramp.elements[0].color = (0.0015, 0.004, 0.010, 1); cr_.color_ramp.elements[1].color = (0.006, 0.030, 0.045, 1)
df_ = nt_.nodes.new("ShaderNodeBsdfDiffuse"); tr_ = nt_.nodes.new("ShaderNodeBsdfTransparent"); mx_ = nt_.nodes.new("ShaderNodeMixShader"); mx_.name = "fade"
o_ = nt_.nodes.new("ShaderNodeOutputMaterial")
nt_.links.new(tc_.outputs["Object"], mp_.inputs[0]); nt_.links.new(mp_.outputs[0], gr_.inputs[0]); nt_.links.new(gr_.outputs[1], cr_.inputs[0])
nt_.links.new(cr_.outputs[0], df_.inputs[0]); nt_.links.new(df_.outputs[0], mx_.inputs[1]); nt_.links.new(tr_.outputs[0], mx_.inputs[2]); nt_.links.new(mx_.outputs[0], o_.inputs[0])
bpy.ops.mesh.primitive_plane_add(size=1.0); bd_ = bpy.context.active_object; bd_.name = "Cutaway_backdrop"
for c_ in list(bd_.users_collection): c_.objects.unlink(bd_)
bpy.data.collections["FX"].objects.link(bd_); bd_.data.materials.append(mbd)
bd_.parent = broot; bd_.location = (-0.42, 0.0, 0.02); bd_.rotation_euler = (0, R_(90), 0); bd_.scale = (1.4, 1.4, 1)
for f, v in ((1, 1.0), (770, 1.0), (820, 0.0), (1340, 0.0), (1385, 1.0)):
    mx_.inputs[0].default_value = v; mx_.inputs[0].keyframe_insert("default_value", frame=f)
bd_.hide_render = True; kf(bd_, "hide_render", 1); bd_.hide_render = False; kf(bd_, "hide_render", 769); bd_.hide_render = True; kf(bd_, "hide_render", 1386)

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
for f, e in ((1, 0.0), (750, 0.0), (800, 5.0), (1350, 5.0), (1395, 0.0)):
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

def ballistic(o, p0, v0, f0, f1, grav=0.4, drag=0.8, spin=6.0, floor=None, step=4):
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
        if landed or f - f0 > 520: break

HOLE = V((0, 0, 1.47))
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
    sx_ = 1 if i % 2 else -1   # off the bullet/camera line so the room reads through
    puff("Dust_in_%d" % i, HOLE + V((sx_ * random.uniform(0.12, 0.22), 0.25 + 0.05 * i, random.uniform(-0.12, 0.12))), V((sx_ * random.uniform(0.2, 0.4), 0.5 + 0.1 * i, random.uniform(-0.1, 0.2))), 188 + 4 * i, 0.03, 0.30, M_drydust, 300)
# impact puff + flakes at the box cover
for i in range(24):
    o = piece("Cover_flake_%02d" % i, [random.uniform(0.002, 0.006)] * 2 + [0.0008], bpy.data.materials["M_box_shell"])
    a = random.uniform(0, 6.28); p0 = nose_world(F_HIT) + V((0.004 * math.cos(a), -0.003, 0.004 * math.sin(a)))
    v0 = V((math.cos(a) * random.uniform(0.02, 0.08), -random.uniform(0.02, 0.1), math.sin(a) * random.uniform(0.02, 0.08)))
    ballistic(o, p0, v0, F_HIT + random.randint(0, 6), 1300, grav=0.05, drag=3.0, step=6)
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
for i in range(60):
    t_ = random.random(); c = V((random.uniform(-2.3, -1.1), 0.3 + 2.0 * t_, 2.0 - 1.2 * t_ + random.uniform(-0.2, 0.2)))
    r = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=random.uniform(0.0008, 0.0016))
    bmesh.ops.translate(bm, verts=r["verts"], vec=c)
me = bpy.data.meshes.new("Motes"); bm.to_mesh(me); bm.free()
motes = bpy.data.objects.new("Dust_motes", me); bpy.data.collections["Bedroom"].objects.link(motes)
mm_ = bpy.data.materials.new("M_mote"); mm_.use_nodes = True; bb_ = mm_.node_tree.nodes["Principled BSDF"]
bb_.inputs["Emission Color"].default_value = (1.0, 0.95, 0.85, 1); bb_.inputs["Emission Strength"].default_value = 0.6
me.materials.append(mm_)
for f, z, y in ((1, 0.0, 0.0), (750, -0.03, 0.03), (F_END, -0.08, 0.05)):
    motes.location = (0, y, z); kf(motes, "location", f)


# ------------------------------------------------------------------ street life (all in the same slow motion)
def ground_z(x, y):
    return 0.06 if -23.8 < y < -22.2 else 0.0
walker = bpy.data.objects["Walker"]
RW = make_human_ctrl(walker); HW = Human(RW)
bpy.context.view_layer.objects.active = walker; bpy.ops.object.mode_set(mode='POSE')
wpath = lambda f: V((-1.9 + 0.40 * (f - 1) / 300.0, -22.9, 0.0))
HW.walk(wpath, lambda f: -90.0, 1, 301, stride=0.7, step=3)
WARM = float(os.environ.get("WARM", "-1"))
for pb in walker.pose.bones:      # her hands carry nothing: arms are FK, not reaching for an unkeyed IK target
    for c in pb.constraints:
        if c.type in ("IK", "COPY_ROTATION") and (c.subtarget.startswith("IK_hand")): c.mute = True
for sd, sx in (("L", 1), ("R", -1)):   # arms hang at the sides and swing a little
    for f, a in ((1, 12), (150, -6), (301, 12)):
        RW.key_rot("upperarm01." + sd, f, [("Y", -sx * 32 * WARM), ("X", a * sx)])
for f in (1, 301):   # relaxed, slightly curled hands
    for sd in "LR":
        for k in range(2, 6):
            for j, a in ((1, 12), (2, 22), (3, 14)):
                pb = RW.PB["finger%d-%d.%s" % (k, j, sd)]; pb.rotation_quaternion = Quaternion(V((1, 0, 0)), R_(a)); pb.keyframe_insert("rotation_quaternion", frame=f)
        for j, a in ((2, 12), (3, 10)):
            pb = RW.PB["finger1-%d.%s" % (j, sd)]; pb.rotation_quaternion = Quaternion(V((1, 0, 0)), R_(a)); pb.keyframe_insert("rotation_quaternion", frame=f)
bpy.ops.object.mode_set(mode='OBJECT')
# joint limits on every finger, thumb and wrist (local space): no backward bends
def hand_limits(rig):
    for pb in rig.pose.bones:
        n = pb.name
        if n.startswith("finger") and not n.startswith("finger1"):
            lim = ((0, 90), (-10, 10), (-10, 10))
        elif n.startswith("finger1"):
            lim = ((-20, 60), (-30, 30), (-30, 30))
        else:
            continue
        c = pb.constraints.new("LIMIT_ROTATION"); c.name = "HandLimit"; c.owner_space = "LOCAL"
        c.use_limit_x = c.use_limit_y = c.use_limit_z = True
        (c.min_x, c.max_x), (c.min_y, c.max_y), (c.min_z, c.max_z) = [(R_(a), R_(b)) for a, b in lim]
hand_limits(man); hand_limits(walker)
# sprinkler: spinner turns, water jets frozen into slow-motion arcs of droplets
spin = bpy.data.objects.get("garden_sprinkler_01_spinner")
M_water = bpy.data.materials.new("M_water"); M_water.use_nodes = True
bw = M_water.node_tree.nodes["Principled BSDF"]; bw.inputs["Transmission Weight"].default_value = 1.0; bw.inputs["Roughness"].default_value = 0.0; bw.inputs["IOR"].default_value = 1.33
if spin:
    spin.rotation_mode = "XYZ"
    for f, a in ((1, 0.0), (F_END, 2.5)):
        spin.rotation_euler.z = a; kf(spin, "rotation_euler", f, 2)
    bm = bmesh.new()
    for side in (-1, 1):
        for k in range(70):
            t = k / 70.0; d = 2.2 * t
            p = V((side * d * 0.5, d * 0.85, 0.12 + 1.4 * t - 1.6 * t * t)) + V([random.gauss(0, 0.02) for _ in range(3)])
            if p.z < 0.02: continue
            r = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=random.uniform(0.004, 0.009)); bmesh.ops.translate(bm, verts=r["verts"], vec=p)
    me = bpy.data.meshes.new("Water_jets"); bm.to_mesh(me); bm.free(); me.materials.append(M_water)
    wj = bpy.data.objects.new("Water_jets", me); bpy.data.collections["Exterior"].objects.link(wj)
    wj.location = spin.matrix_world.translation; wj.rotation_mode = "XYZ"
    for f, a in ((1, 0.0), (F_END, 2.5)):
        wj.rotation_euler.z = a; kf(wj, "rotation_euler", f, 2)
# birds lifting off the small tree as the bullet passes
M_bird = bpy.data.materials.new("M_bird"); M_bird.use_nodes = True; M_bird.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.06, 0.05, 0.05, 1)
for i in range(5):
    bm = bmesh.new()
    body = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0)["verts"]
    for v in body: v.co = V((v.co.x * 0.025, v.co.y * 0.08, v.co.z * 0.025))
    me = bpy.data.meshes.new("Bird%d" % i); bm.to_mesh(me); bm.free(); me.materials.append(M_bird)
    bd = bpy.data.objects.new("Bird_%d" % i, me); bpy.data.collections["Exterior"].objects.link(bd)
    for sd in (-1, 1):
        bm = bmesh.new(); vs = [bm.verts.new(c) for c in ((0, -0.03, 0), (0, 0.03, 0), (sd * 0.14, -0.01, 0))]; bm.faces.new(vs)
        mw = bpy.data.meshes.new("Wing"); bm.to_mesh(mw); bm.free(); mw.materials.append(M_bird)
        wg = bpy.data.objects.new("Bird_%d_wing" % i, mw); bpy.data.collections["Exterior"].objects.link(wg); wg.parent = bd
        for f in range(1, 241, 6):
            wg.rotation_euler.y = sd * R_(45) * math.sin(f / 10.0 + i); kf(wg, "rotation_euler", f, 1)
    p0 = V((-4.5 + random.uniform(-0.8, 0.8), -9.0 + random.uniform(-0.8, 0.8), 2.2 + random.uniform(0, 0.8)))
    dirb = V((random.uniform(-1, -0.2), random.uniform(-0.3, 0.5), 0.6)).normalized()
    bd.rotation_euler.z = math.atan2(-dirb.x, dirb.y)
    for f in range(1, 241, 6):
        t = max(0, f - 40) / 60.0; bd.location = p0 + dirb * (0.6 * t * t / (1 + t)); kf(bd, "location", f)
# room life: RGB strip and monitor flicker, a poster knocked crooked, dust shaken from the ceiling
led = bpy.data.materials["M_led"].node_tree.nodes["Principled BSDF"]
for f in range(1, F_END + 1, 12):
    hue = (f / 600.0) % 1.0
    import colorsys
    led.inputs["Emission Color"].default_value = (*colorsys.hsv_to_rgb(hue, 0.8, 1.0), 1)
    led.inputs["Emission Strength"].default_value = 6 + 3 * random.random()
    led.inputs["Emission Color"].keyframe_insert("default_value", frame=f); led.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)
pst = bpy.data.objects["Poster3"]; pst.rotation_mode = "XYZ"; y0_ = pst.rotation_euler.y
for f, a in ((1, 0), (205, 0), (260, -5), (320, -3.5), (F_END, -4)):
    pst.rotation_euler.y = y0_ + R_(a); kf(pst, "rotation_euler", f, 1)
puff("Dust_ceiling", V((-0.4, 0.5, 2.62)), V((0.0, 0.1, -0.5)), 215, 0.05, 0.35, M_drydust, 400)
for n_, fh in (("Plug_siding", F_WALL), ("Plug_osb", F_WALL + 2), ("Plug_drywall", 178)):
    o = bpy.data.objects[n_]; o.hide_render = False; kf(o, "hide_render", fh - 1); o.hide_render = True; kf(o, "hide_render", fh)
fk = bpy.data.lights.new("L_face_key", "AREA"); fk.size = 0.6; fk.color = (1.0, 0.93, 0.86)
fko = bpy.data.objects.new("L_face_key", fk); bpy.data.collections["Bedroom"].objects.link(fko)
fko.location = (0.9, 2.1, 1.95); fko.rotation_mode = "QUATERNION"; fko.rotation_quaternion = (V((0, 3.2, 1.75)) - V((0.9, 2.1, 1.95))).to_track_quat('-Z', 'Y')
for f, e in ((1, 0.0), (1340, 0.0), (1400, 14.0), (F_END, 14.0)):
    fk.energy = e; fk.keyframe_insert("energy", frame=f)
# a little light inside the wall cavity so studs/insulation read as the camera passes
cl = bpy.data.lights.new("L_cavity", "POINT"); cl.shadow_soft_size = 0.02; cl.color = (1.0, 0.9, 0.75)
clo = bpy.data.objects.new("L_cavity", cl); bpy.data.collections["Wall"].objects.link(clo); clo.location = (0.0, 0.08, 1.59)
for f, e in ((1, 0.0), (165, 0.0), (180, 3.0), (205, 3.0), (215, 0.0)):
    cl.energy = e; cl.keyframe_insert("energy", frame=f)
# sharp bright streak behind the bullet outside
bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=False, segments=12, radius1=0.0012, radius2=0.0002, depth=0.35)
bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(R_(90), 3, 'X')); bmesh.ops.translate(bm, verts=bm.verts, vec=(0, -0.19, 0))
me = bpy.data.meshes.new("Streak"); bm.to_mesh(me); bm.free()
mst = bpy.data.materials.new("M_streak"); mst.use_nodes = True; nt_ = mst.node_tree; nt_.nodes.clear()
e_ = nt_.nodes.new("ShaderNodeEmission"); e_.inputs["Color"].default_value = (1.0, 0.85, 0.6, 1); e_.inputs["Strength"].default_value = 6
t_ = nt_.nodes.new("ShaderNodeBsdfTransparent"); m_ = nt_.nodes.new("ShaderNodeMixShader"); m_.inputs[0].default_value = 0.75
o_ = nt_.nodes.new("ShaderNodeOutputMaterial"); nt_.links.new(e_.outputs[0], m_.inputs[1]); nt_.links.new(t_.outputs[0], m_.inputs[2]); nt_.links.new(m_.outputs[0], o_.inputs[0])
me.materials.append(mst); stk = bpy.data.objects.new("Bullet_streak", me); bpy.data.collections["FX"].objects.link(stk); stk.parent = bullet
for f, v in ((1, False), (F_WALL, False), (F_WALL + 2, True)):
    stk.hide_render = v; kf(stk, "hide_render", f)

# ------------------------------------------------------------------ camera: one continuous Catmull-Rom move
cam_d = bpy.data.cameras.new("CAM_Film"); cam_d.sensor_fit = "AUTO"; cam_d.clip_start = 0.004; cam_d.clip_end = 300
cam = bpy.data.objects.new("CAM_Film", cam_d); sc.collection.objects.link(cam); sc.camera = cam
B = bpos
def behind(f, back, up=0.0, side=0.0):
    return B(f) + V((side, -back, up))
def SH(f, v): return v + V((0, shove(f) + 0.003, 0)) if f > F_HIT else v
CK = [  # frame, camera position, aim point, lens
    (1,    behind(1, 0.45, 0.07, 0.08),    V((0.0, -20.0, 1.490)), 36),
    (45,   behind(45, 0.32, 0.04, 0.06),   V((0.0, -12.0, 1.470)), 40),
    (95,   behind(95, 0.36, -0.10, 0.16),  V((0.0, -6.0, 1.570)), 34),
    (130,  behind(130, 0.42, 0.10, -0.12), V((0.0, 0.0, 1.470)), 36),
    (150,  behind(150, 1.10, 0.30, 0.55),  V((-0.2, 0.3, 1.470)), 24),
    (F_WALL, behind(F_WALL, 0.55, 0.10, 0.18), V((0.0, 0.5, 1.470)), 28),
    (166,  behind(166, 0.25, 0.0, 0.01),   V((0.0, 0.8, 1.470)), 35),
    (178,  behind(178, 0.24, 0.0, 0.0),    V((0.0, 0.9, 1.470)), 34),
    (186,  V((0.0, -0.045, 1.470)),         V((0.0, 1.0, 1.470)), 34),
    (192,  V((0.0, 0.20, 1.470)),           V((0.0, 1.2, 1.480)), 32),
    (206,  V((0.01, 0.31, 1.480)),          V((0.0, 1.5, 1.490)), 30),
    (228,  V((0.06, 0.45, 1.530)),       V((0.0, 2.0, 1.520)), 30),
    (270,  V((0.62, 0.62, 1.790)),       V((0.0, 2.2, 1.550)), 26),
    (330,  V((1.25, 1.55, 1.650)),       V((0.0, 2.55, 1.530)), 28),
    (378,  V((0.50, 2.40, 1.720)),       V((0.0, 2.95, 1.620)), 32),
]
for f, c, a, l in [
    (420,  V((0.32, 2.38, 1.750)),       V((0.0, 2.95, 1.630)), 32),
    (480,  V((-0.05, 2.18, 1.730)),      V((0.0, 2.97, 1.620)), 34),
    (540,  V((-0.62, 2.32, 1.530)),      V((0.0, 2.95, 1.550)), 34),
    (600,  V((-0.55, 2.45, 1.550)),      V((0.0, 2.95, 1.620)), 30),
    (650,  V((-0.13, 2.70, 1.460)),      V((0.0, 2.90, 1.480)), 40),
    (695,  V((-0.045, 2.795, 1.505)),   V((0.0, 2.92, 1.470)), 50),
    (735,  V((0.06, 2.805, 1.440)),      V((0.0, 2.92, 1.480)), 55),
    (772,  V((0.11, 2.80, 1.530)),       V((0.0, 2.92, 1.480)), 50),
    (805,  V((0.17, 2.835, 1.515)),     V((0.0, 2.925, 1.470)), 50)]:
    CK.append((f, SH(f, c), SH(f, a), l))
def nose_cam(f, dx, dz, dy=-0.016, ady=-0.012):
    p = B(f); return (p + V((dx, dy, dz)), p + V((0, ady, 0)))
for f, dx, dz, lens in ((850, 0.22, 0.07, 50), (900, 0.19, 0.09, 55), (960, 0.18, 0.05, 60), (1020, 0.19, 0.09, 62), (1075, 0.20, 0.07, 62)):
    c, a = nose_cam(f, dx, dz); CK.append((f, c, a, lens))
for f, c, a, l in [(1140, V((0.50, 2.90, 1.690)), V((0.0, 2.975, 1.440)), 46), (1200, V((0.50, 2.86, 1.630)), V((0.0, 2.975, 1.440)), 50)]:
    CK.append((f, SH(f, c), SH(f, a), l))
for f, a, h, r, lens in ((1245, -35, 0.06, 0.20, 55), (1290, 0, 0.09, 0.19, 55), (1335, 22, 0.12, 0.20, 50)):
    c0 = B(f); c = c0 + V((r * math.cos(R_(a)), r * math.sin(R_(a)), h)); CK.append((f, c, c0 + V((0, -0.01, 0.0)), lens))
for f, c, a, l in [(1395, V((0.75, 2.25, 1.670)), V((0.0, 2.95, 1.470)), 35), (1445, V((0.55, 2.35, 1.750)), V((0.0, 3.0, 1.570)), 34),
                   (1500, V((0.45, 2.42, 1.770)), V((0.0, 3.05, 1.620)), 36)]:
    CK.append((f, SH(f, c), SH(f, a), l))
fc = catmull([(f, c) for f, c, a, l in CK]); fa = catmull([(f, a) for f, c, a, l in CK]); fl = catmull([(f, float(l)) for f, c, a, l in CK])
cam_d.dof.use_dof = True; cam_d.dof.aperture_fstop = 8.0
for f_, v_ in ((1, 8.0), (172, 8.0), (184, 22.0), (232, 22.0), (250, 8.0)):
    cam_d.dof.aperture_fstop = v_; cam_d.dof.keyframe_insert("aperture_fstop", frame=f_)
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
