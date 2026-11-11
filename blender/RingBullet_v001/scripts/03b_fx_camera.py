"""RingBullet stage 2: bullet + fragments, sparks, muzzle FX, world-time (slow motion) props, police lights, camera, beats.json.
blender -b anim.blend --python 03b_fx_camera.py -- <out.blend>"""
import sys, os, math, random, json
import bpy
from mathutils import Vector, Matrix, Quaternion, Euler

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
exec(open(os.path.join(ROOT, "..", "pipeline", "anim_lib.py")).read())
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; O = bpy.data.objects
rnd = random.Random(21)
ANIM = os.environ.get("RB_LOOK") == "anim"   # v004+: animated-CG look (no handheld shake, deeper focus, no sweat)
FIRE, IMPACT, SPLIT, LODGE, GRAZE, SWAP = 30, 541, 700, 896, 1003, 1244
def F(t): return 1 + round(t * 60)
def key(o, path, f, v=None, idx=-1):
    if v is not None:
        if idx < 0: setattr(o, path, v)
        else: getattr(o, path)[idx] = v
    o.keyframe_insert(path, frame=f, index=idx)
def hide(o, f, h):
    o.hide_render = h; o.keyframe_insert("hide_render", frame=f)
def fcurves_of(act):
    out = []
    for layer in getattr(act, "layers", []):
        for strip in layer.strips:
            for cb in getattr(strip, "channelbags", []): out += list(cb.fcurves)
    return out
def const_hide(o):
    if o.animation_data and o.animation_data.action:
        for fc in fcurves_of(o.animation_data.action):
            if fc.data_path.startswith("hide"):
                for k in fc.keyframe_points: k.interpolation = 'CONSTANT'
def wpos(o): return o.matrix_world.translation.copy()
def at(f): sc.frame_set(f)

# ---------------------------------------------------------------- world time: real speed, slow motion f40..1000, real again
WT = pchip([(1, 0.0), (FIRE, 29 / 60), (45, 0.62), (60, 0.66), (1000, 0.66 + 940 * 0.06 / 60), (1030, 0.66 + 940 * 0.06 / 60 + 0.25), (1410, 0.66 + 940 * 0.06 / 60 + 0.25 + 380 / 60)])
tc = O.get("TimeCtl") or bpy.data.objects.new("TimeCtl", None)
if tc.name not in sc.collection.objects: sc.collection.objects.link(tc)
tc["wt"] = 0.0
for f in range(1, 1411, 4):
    tc["wt"] = WT(f); tc.keyframe_insert('["wt"]', frame=f)
# feed world time into rain + dust GN (replace Scene Time seconds) and window drops
for ng in bpy.data.node_groups:
    for n in list(ng.nodes):
        if n.bl_idname == 'GeometryNodeInputSceneTime':
            v = ng.nodes.new('ShaderNodeValue'); v.name = "WorldTime"
            for l in list(n.outputs['Seconds'].links): ng.links.new(v.outputs[0], l.to_socket)
            ng.nodes.remove(n)
            d = v.outputs[0].driver_add("default_value"); d.driver.type = 'AVERAGE'
            var = d.driver.variables.new(); var.type = 'SINGLE_PROP'; var.targets[0].id = tc; var.targets[0].data_path = '["wt"]'
mg = bpy.data.materials["M_WinGlass"]
for n in mg.node_tree.nodes:
    if n.bl_idname == 'ShaderNodeTexVoronoi':
        n.inputs['W'].driver_remove("default_value")
        d = n.inputs['W'].driver_add("default_value"); d.driver.type = 'SCRIPTED'; d.driver.expression = "wt*0.5"
        var = d.driver.variables.new(); var.name = "wt"; var.type = 'SINGLE_PROP'; var.targets[0].id = tc; var.targets[0].data_path = '["wt"]'
# pendulum + clock in world time
pend = O["PendulumPivot"]; pend.rotation_mode = 'XYZ'
for f in range(1, 1411, 3):
    key(pend, "rotation_euler", f, math.radians(7) * math.sin(2 * math.pi * WT(f) / 2.0), idx=0)

# wall clock second hand ticks once per world-second (snaps in 3 frames)
sh_ = O.get("WallClock_second_hand")
if sh_:
    sh_.rotation_mode = 'XYZ'; base = sh_.rotation_euler.copy()
    t0 = WT(1); t1 = WT(1410); k = 0
    for f in range(1, 1411):
        if int(WT(f) - t0) != k or f == 1:
            k = int(WT(f) - t0)
            for ff, kk in ((f - 1, k - 1), (f + 2, k)):
                if ff < 1: continue
                e = base.copy(); e.y = base.y + math.radians(6.0) * (kk + 23); sh_.rotation_euler = e; sh_.keyframe_insert("rotation_euler", frame=ff)
# ---------------------------------------------------------------- muzzle, impact point, bullet path
G = O["Gun"]; at(FIRE)
MZ = G.matrix_world @ Vector((0.19, 0, 0)); GUNX = (G.matrix_world.to_3x3() @ Vector((1, 0, 0))).normalized()
ring = O["WeddingRing"]; at(IMPACT)
RC = wpos(ring); RAX = (ring.matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized()
to_m = MZ - RC; radial = (to_m - RAX * to_m.dot(RAX)).normalized()
R_OUT = 0.0111 * ring.matrix_world.to_scale().x
P_IMP = RC + radial * R_OUT
DIR = (P_IMP - MZ).normalized()
U = pchip([(FIRE, 0.0), (FIRE + 20, 0.12), (F(1.5), 0.24), (F(2.7), 0.42), (F(4.5), 0.64), (F(6.8), 0.86), (IMPACT, 1.0)])
B0 = MZ + DIR * 0.004; B1 = P_IMP - DIR * 0.0149
def bpos(f): return B0.lerp(B1, U(f))
bul = O["Bullet"]; bul.rotation_mode = 'QUATERNION'
qdir = DIR.to_track_quat('Z', 'Y')
hide(bul, 1, True); hide(bul, FIRE, False); hide(bul, SPLIT, True)
for f in range(FIRE, IMPACT + 1, 2):
    bul.location = bpos(f); key(bul, "location", f)
    spin = Quaternion(Vector((0, 0, 1)), U(f) * 40.0)
    bul.rotation_quaternion = qdir @ spin; key(bul, "rotation_quaternion", f)
# glance: after impact the squashed bullet slides along the ring surface a little
GL = (DIR - RAX * DIR.dot(RAX)).cross(RAX).normalized()
sk = bul.data.shape_keys.key_blocks["Squash"]
sk.value = 0.0; sk.keyframe_insert("value", frame=IMPACT)
for f, v, slide in ((IMPACT + 30, 0.6, 0.002), (SPLIT - 20, 1.0, 0.004), (SPLIT, 1.0, 0.005)):
    sk.value = v; sk.keyframe_insert("value", frame=f)
    bul.location = B1 + GL * slide - DIR * 0.002 * v; key(bul, "location", f)
    bul.rotation_quaternion = qdir @ Quaternion(Vector((0, 0, 1)), 40.0) @ Quaternion(GL, 0.25 * v); key(bul, "rotation_quaternion", f)
# ring dent + glint
dk = ring.data.shape_keys.key_blocks["Dented"]
dk.value = 0.0; dk.keyframe_insert("value", frame=IMPACT); dk.value = 0.8; dk.keyframe_insert("value", frame=IMPACT + 40); dk.value = 1.0; dk.keyframe_insert("value", frame=SPLIT)
# rotate the ring about the finger so the dent (+Y local) faces where the bullet hit
loc_imp = ring.matrix_world.inverted() @ P_IMP; ang = math.atan2(loc_imp.y, loc_imp.x) - math.pi / 2
ring.matrix_basis = ring.matrix_basis @ Matrix.Rotation(ang, 4, 'Z')

# ---------------------------------------------------------------- fragments
fa, fb = O["FragmentA"], O["FragmentB"]
nick = O["FingerNick"]
def nick_pos(f): at(f); return wpos(nick) + (nick.matrix_world.to_3x3() @ Vector((0, 1, 0))).normalized() * 0.0012
TA = nick_pos(LODGE)
NM = O["NeckMark"]; at(GRAZE); TB = wpos(NM); TBN = (NM.matrix_world.to_3x3() @ Vector((0, 1, 0))).normalized()
at(SPLIT); P_S = bul.matrix_world.translation.copy()
pa = catmull([(SPLIT, P_S), (SPLIT + 60, P_S.lerp(TA, 0.3) + GL * 0.012 - DIR * 0.01), (LODGE, TA)])
WALL_HIT = Vector((0.532, 1.5, 1.92))   # bookshelf side panel, open upper-left of frame at f1016 (picked by ray cast)   # hits the bookshelf front (books), behind his head as framed
pbk = [(SPLIT, P_S), (SPLIT + 90, P_S.lerp(TB, 0.35) - GL * 0.02 - DIR * 0.03), (GRAZE - 4, TB + TBN * 0.006 - DIR * 0.01), (GRAZE, TB + TBN * 0.002),
       (GRAZE + 4, TB + TBN * 0.004 + DIR * 0.03), (GRAZE + 5, TB.lerp(WALL_HIT, 0.55)), (GRAZE + 9, WALL_HIT)]
pb_ = catmull(pbk)
for o in (fa, fb): o.rotation_mode = 'XYZ'; hide(o, 1, True); hide(o, SPLIT, False)
for f in range(SPLIT, LODGE + 1, 2):
    fa.location = pa(f); key(fa, "location", f); key(fa, "rotation_euler", f, Euler((f * 0.05, f * 0.03, 0)))
for f in range(LODGE + 2, SWAP + 1, 4):
    fa.location = nick_pos(f); key(fa, "location", f)
hide(fa, SWAP, True)
for f in range(SPLIT, GRAZE + 10, 1):
    fb.location = pb_(f); key(fb, "location", f); key(fb, "rotation_euler", f, Euler((f * 0.06, 0, f * 0.04)))
hide(fb, GRAZE + 10, True)
const_hide(fa); const_hide(fb); const_hide(bul)

# ---------------------------------------------------------------- wall hit: dust puff + wood chips (real time after the slow motion)
WH = GRAZE + 9
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1); puff = bpy.context.active_object; puff.name = "WallDustPuff"
mpf = bpy.data.materials["M_Smoke"].copy(); mpf.name = "M_WallDust"
mpf.node_tree.nodes["Principled Volume"].inputs['Color'].default_value = (0.85, 0.76, 0.64, 1)
puff.data.materials.append(mpf); fxc = bpy.data.collections["FX"]
for c_ in list(puff.users_collection): c_.objects.unlink(puff)
fxc.objects.link(puff)
pd = mpf.node_tree.nodes["SmokeDensity"].inputs[1]
hide(puff, 1, True); hide(puff, WH, False); hide(puff, WH + 150, True); const_hide(puff)
for f, sc_, dv, off in ((WH, 0.01, 60, 0.0), (WH + 4, 0.06, 45, 0.04), (WH + 20, 0.11, 25, 0.08), (WH + 90, 0.15, 6, 0.11), (WH + 150, 0.18, 0.0, 0.13)):
    puff.location = WALL_HIT + Vector((-off, -off * 0.3, -off * 0.2)); key(puff, "location", f); key(puff, "scale", f, (sc_, sc_ * 0.7, sc_))
    pd.default_value = dv; pd.keyframe_insert("default_value", frame=f)
M_CHIP = bpy.data.materials["M_DeskWood"] if "M_DeskWood" in bpy.data.materials else bpy.data.materials["M_Trim"]
for i in range(14):
    bpy.ops.mesh.primitive_cube_add(size=1); ch = bpy.context.active_object; ch.name = "WallChip%02d" % i
    ch.scale = (rnd.uniform(0.003, 0.009), rnd.uniform(0.001, 0.003), rnd.uniform(0.002, 0.006)); ch.data.materials.append(M_CHIP)
    for c_ in list(ch.users_collection): c_.objects.unlink(ch)
    fxc.objects.link(ch); ch.rotation_mode = 'XYZ'
    v = Vector((rnd.uniform(-1.8, -0.8), rnd.uniform(-0.8, 0.5), rnd.uniform(-0.2, 1.0))) * rnd.uniform(0.6, 1.3)
    hide(ch, 1, True); hide(ch, WH, False); const_hide(ch)
    for f in range(WH, WH + 61, 3):
        t = (f - WH) / 60.0; pz = WALL_HIT + v * t + Vector((0, 0, -4.9 * t * t))
        if pz.z < 0.004: pz.z = 0.004
        ch.location = pz; key(ch, "location", f); key(ch, "rotation_euler", f, Euler((t * 30 + i, t * 20, t * 11)))
lwd = bpy.data.lights.new("L_WallHit", 'POINT'); lwd.shadow_soft_size = 0.05; lwd.color = (1.0, 0.8, 0.6)
lwo = bpy.data.objects.new("L_WallHit", lwd); bpy.data.collections["Lights"].objects.link(lwo); lwo.location = WALL_HIT + Vector((-0.15, -0.05, 0.05)); lwo.visible_camera = False
for f, e in ((1, 0), (WH - 1, 0), (WH + 1, 6), (WH + 10, 2.5), (WH + 40, 1.0), (WH + 90, 0)):
    lwd.energy = e; lwd.keyframe_insert("energy", frame=f)

# ---------------------------------------------------------------- sparks (impact burst + split burst), slow motion ballistic in world time
sparks = sorted([o for o in O if o.name.startswith("Spark")], key=lambda o: o.name)
def burst(objs, f0, origin, life, speed):
    for o in objs:
        d = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 0.2), rnd.uniform(-0.6, 1))); d = (d - RAX * d.dot(RAX) * 0.5).normalized()
        v = d * speed * rnd.uniform(0.4, 1.0); l = int(life * rnd.uniform(0.6, 1.0))
        o.rotation_mode = 'QUATERNION'
        hide(o, 1, True); hide(o, f0, False); hide(o, f0 + l, True)
        for f in range(f0, f0 + l + 1, 3):
            t = WT(f) - WT(f0)
            p = origin + v * t + Vector((0, 0, -4.9 * t * t)); vel = v + Vector((0, 0, -9.8 * t))
            o.location = p; key(o, "location", f)
            o.rotation_quaternion = vel.normalized().to_track_quat('Z', 'Y'); key(o, "rotation_quaternion", f)
        const_hide(o)
burst(sparks[:28], IMPACT, P_IMP, 150, 1.6)
burst(sparks[28:], SPLIT, P_S, 110, 1.0)
li = O["L_ImpactFlash"]; li.location = P_IMP - DIR * 0.02
for f, e in ((1, 0), (IMPACT - 1, 0), (IMPACT + 1, 0.25), (IMPACT + 12, 0.08), (IMPACT + 40, 0), (SPLIT - 1, 0), (SPLIT + 2, 0.08), (SPLIT + 25, 0)):
    li.data.energy = e; li.data.keyframe_insert("energy", frame=f)
# ---------------------------------------------------------------- muzzle flash, smoke, casing
fl = O["MuzzleFlash"]; fl.parent = G; fl.matrix_parent_inverse = Matrix.Identity(4); fl.location = (0.19, 0, 0)
gain = bpy.data.materials["M_MuzzleFlash"].node_tree.nodes["FlashGain"].inputs[1]
for f, g, s in ((1, 0, 0.2), (FIRE - 1, 0, 0.2), (FIRE, 90, 0.8), (FIRE + 3, 70, 1.1), (FIRE + 14, 25, 1.3), (FIRE + 40, 0, 1.4)):
    gain.default_value = g; gain.keyframe_insert("default_value", frame=f); key(fl, "scale", f, (s, s, s))
lm = O["L_MuzzleFlash"]; lm.location = MZ + DIR * 0.05
for f, e in ((1, 0), (FIRE - 1, 0), (FIRE, 120), (FIRE + 8, 40), (FIRE + 40, 0)):
    lm.data.energy = e; lm.data.keyframe_insert("energy", frame=f)
sm = O["MuzzleSmoke"]; dens = bpy.data.materials["M_Smoke"].node_tree.nodes["SmokeDensity"].inputs[1]
for f, s, dv, off in ((1, 0.001, 0, 0.0), (FIRE, 0.004, 8, 0.01), (FIRE + 20, 0.03, 6, 0.04), (F(2.7), 0.06, 4, 0.08), (F(6.0), 0.1, 1.5, 0.12), (F(9.0), 0.13, 0.0, 0.14)):
    sm.location = MZ + DIR * off + Vector((0, 0, off * 0.2)); key(sm, "location", f); key(sm, "scale", f, (s * 1.4, s, s))
    dens.default_value = dv; dens.keyframe_insert("default_value", frame=f)
cs = O["Casing"]; cs.rotation_mode = 'XYZ'
side = GUNX.cross(Vector((0, 0, 1))).normalized()
ej = G.matrix_world @ Vector((0.06, 0, 0.02)); v0 = (side * -1.0 + Vector((0, 0, 1.4)) - GUNX * 0.3) * 1.8
hide(cs, 1, True); hide(cs, FIRE + 1, False)
for f in range(FIRE + 1, 1000, 6):
    t = WT(f) - WT(FIRE + 1); p = ej + v0 * t + Vector((0, 0, -4.9 * t * t))
    if p.z < 0.012: p.z = 0.012
    cs.location = p; key(cs, "location", f); key(cs, "rotation_euler", f, Euler((t * 25, t * 9, t * 4)))
const_hide(cs)

# ---------------------------------------------------------------- robber exits (hidden once the camera has left him), lamp flicker, police lights
for o in O:
    if o.name.startswith("Robber") or o.parent == G or o == G:
        if o.type in ('MESH', 'ARMATURE', 'EMPTY') and o.name != "MuzzleFlash":
            hide(o, 1, False); hide(o, 1080, True); const_hide(o)
lamp = O["L_DeskLamp"].data
for f, e in ((1, 18), (IMPACT, 18), (IMPACT + 3, 6), (IMPACT + 10, 20), (IMPACT + 18, 12), (IMPACT + 30, 18)):
    lamp.energy = e; lamp.keyframe_insert("energy", frame=f)
pol = [(O["L_PoliceRed_Win"], 0.0, 500), (O["L_PoliceBlue_Win"], 0.5, 700), (O["L_PoliceRed_Door"], 0.0, 1800), (O["L_PoliceBlue_Door"], 0.5, 2600)]
bars = {"Red": bpy.data.materials["M_PoliceBarRed"], "Blue": bpy.data.materials["M_PoliceBarBlue"]}
P_ON = 1090
for lo, ph, emax in pol:
    lo.data.energy = 0; lo.data.keyframe_insert("energy", frame=1); lo.data.keyframe_insert("energy", frame=P_ON)
    f = P_ON; k = 0
    while f < 1415:
        ramp = min(1.0, (f - P_ON) / 60.0) * (2.2 if SWAP - 8 <= f <= SWAP + 6 else 1.0)
        on = ((k % 2) == (0 if ph == 0 else 1))
        lo.data.energy = emax * ramp if on else emax * 0.04 * ramp; lo.data.keyframe_insert("energy", frame=f)
        f += 9; k += 1
for nm, ph in (("Red", 0), ("Blue", 1)):
    inp = bars[nm].node_tree.nodes["Principled BSDF"].inputs['Emission Strength']
    inp.default_value = 0; inp.keyframe_insert("default_value", frame=1); inp.keyframe_insert("default_value", frame=P_ON)
    f = P_ON; k = 0
    while f < 1415:
        inp.default_value = 60.0 if (k % 2) == ph else 2.0; inp.keyframe_insert("default_value", frame=f); f += 9; k += 1
for o in O:
    if o.type == 'LIGHT': o.visible_camera = False

# ---------------------------------------------------------------- camera: one camera, Catmull-Rom through framings
def face(f): at(f); return (O["Owner"].matrix_world @ O["Owner"].pose.bones["head"].head) + Vector((0, -0.09, 0.06))
def ringp(f): at(f); return wpos(ring)
def handL(f): at(f); return O["Owner"].matrix_world @ O["Owner"].pose.bones["finger3-1.L"].head
def neckp(f): at(f); return wpos(NM)
def nickp(f): at(f); return wpos(nick)
SIDE = Vector((1, 0, 0))
K = []   # (frame, loc, target, lens, focus point)
def k_(f, loc, tgt, lens, foc=None): K.append((f, Vector(loc), Vector(tgt), lens, Vector(foc) if foc is not None else Vector(tgt)))
k_(1, (0.74, -2.95, 1.56), face(1) + Vector((0, 0, -0.1)), 32)
k_(F(0.5), (0.86, -2.3, 1.62), MZ.lerp(face(F(0.5)), 0.25), 34)
k_(F(1.0), MZ + Vector((0.11, -0.2, 0.06)), MZ + DIR * 0.3, 38, MZ)
for t in (1.6, 2.1, 2.6):
    f = F(t); b = bpos(f); sd = DIR.cross(Vector((0, 0, 1))).normalized(); k_(f, b - DIR * 0.09 + Vector((0, 0, 0.024)) - sd * 0.008, face(f), 40, b)
f = F(3.15); b = bpos(f); k_(f, b + Vector((0.16, 0.08, 0.04)), face(f), 40, b)
k_(F(3.7), (0.42, -0.95, 1.65), face(F(3.7)), 45)
k_(F(4.7), (0.34, -0.8, 1.44), handL(F(4.7)), 50)
r = ringp(F(5.7)); k_(F(5.7), r + Vector((0.07, -0.17, 0.03)), r, 60)
f = F(6.8); b = bpos(f); r = ringp(f); k_(f, b - DIR * 0.07 + Vector((0.006, 0.0, 0.012)), b.lerp(r, 0.25), 50, b)
f = F(7.5); b = bpos(f); r = ringp(f); k_(f, b - DIR * 0.07 + Vector((0.025, 0.0, 0.01)), b.lerp(r, 0.6), 50, r)
f = F(8.2); b = bpos(f); r = ringp(f); k_(f, b.lerp(r, 0.5) + Vector((0.13, 0.0, 0.01)), b.lerp(r, 0.6), 50, b.lerp(r, 0.7))
r = ringp(IMPACT); k_(IMPACT, r + Vector((0.085, -0.06, 0.012)), P_IMP, 60, P_IMP)
r = ringp(F(10.0)); k_(F(10.0), r + Vector((0.17, -0.25, 0.04)), r, 55)
def fmid(f): return (pa(min(f, LODGE)) + pb_(min(f, GRAZE))) / 2
r = ringp(F(11.0)); k_(F(11.0), r + Vector((0.1, -0.08, 0.0)), r, 60)
f = F(12.0); m = fmid(f).lerp(ringp(f), 0.3); k_(f, m + Vector((0.03, -0.15, -0.05)), m, 55)
f = F(13.0); m = fmid(f).lerp(ringp(f), 0.2); k_(f, m + Vector((-0.1, -0.15, 0.03)), m, 55)
f = F(13.9); m = fmid(f); k_(f, m + Vector((-0.04, -0.3, 0.06)), m, 50)
n_ = nickp(F(14.4)); k_(F(14.4), n_ + Vector((0.1, -0.2, 0.05)), n_, 55)
n_ = nickp(F(15.0)); k_(F(15.0), n_ + Vector((0.13, -0.24, 0.08)), n_, 50)
k_(F(15.6), (0.2, -0.72, 1.72), face(F(15.6)), 45)
nk = neckp(F(16.55)); k_(F(16.55), (-0.26, -0.5, 1.56), nk, 45)
nk = neckp(F(17.1)); k_(F(17.1), (-0.36, -0.48, 1.5), nk + Vector((0, 0, -0.02)), 42)
k_(F(17.9), (0.36, -0.86, 1.47), handL(F(17.9)).lerp(face(F(17.9)), 0.4), 42)
r = ringp(F(18.9)); k_(F(18.9), r + Vector((0.15, -0.2, 0.1)), r, 60)
r = ringp(F(19.5)); k_(F(19.5), r + Vector((-0.14, -0.3, 0.14)), r, 55)
k_(F(20.1), (-0.17, -0.64, 1.52), face(F(20.1)), 45)
k_(F(20.8), (-0.45, -1.45, 1.75), (0.25, 0.0, 1.4), 32)
k_(F(21.8), (-0.95, -2.5, 2.1), (1.3, 0.3, 1.1), 24)
k_(F(22.8), (-0.35, -2.3, 2.05), (2.55, 0.55, 1.15), 28)
k_(1410, (0.25, -1.75, 1.8), (2.75, 0.6, 1.2), 33)
cl = catmull([(k[0], k[1]) for k in K]); ct = catmull([(k[0], k[2]) for k in K]); cn = pchip([(k[0], float(k[3])) for k in K])
cf = catmull([(k[0], k[4]) for k in K])
cd = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cd); sc.collection.objects.link(cam); sc.camera = cam
cd.clip_start = 0.002; cd.clip_end = 60; cd.sensor_width = 36; cd.dof.use_dof = True; cd.dof.aperture_fstop = 4.0
cam.rotation_mode = 'QUATERNION'; prev = None
def ride(f):
    """orbit around the flying bullet: behind-above -> side -> below-side, closing in; target swings from the face to the bullet's nose"""
    u = smooth((f - F(1.25)) / (F(2.95) - F(1.25)))
    sd = DIR.cross(Vector((0, 0, 1))).normalized(); up = sd.cross(DIR).normalized()
    ang = math.radians(-20 + 75 * u)                      # around the flight axis
    rad = 0.035 + 0.02 * u; back = 0.075 - 0.05 * u
    b = bpos(f); off = (up * math.cos(ang) + sd * math.sin(ang)) * rad - DIR * back
    tgt = b + (face(f) - b).normalized() * 0.012 + up * 0.006
    return b + off, tgt, b
LOCKS = [  # (f0, f1, ramp, offset fn(f)->(loc, target, focus))
    (F(1.25), F(2.95), 14, lambda f: ride(f)),
    (F(6.6), F(7.4), 14, lambda f: (bpos(f) - DIR * 0.07 + Vector((0.006 + 0.03 * (f - F(6.6)) / 48, 0.0, 0.012)), bpos(f).lerp(ringp(f), 0.25 + 0.4 * smooth((f - F(6.6)) / 48)), bpos(f).lerp(ringp(f), smooth((f - F(6.8)) / 40)))),
]
FACE_C = {}
def lockw(f):
    for f0, f1, rp, fn in LOCKS:
        if f0 - rp <= f <= f1 + rp:
            w = smooth((f - (f0 - rp)) / rp) if f < f0 else (smooth(((f1 + rp) - f) / rp) if f > f1 else 1.0)
            return w, fn(max(f0, min(f1, f)))
    return 0.0, None
for f in range(1, 1411):
    p = cl(f); t = ct(f); w, lk = lockw(f)
    if lk is not None:
        p = p.lerp(lk[0], w); t = t.lerp(lk[1], w)
    if f in range(IMPACT, IMPACT + 18):   # impact shake
        a_ = (IMPACT + 18 - f) / 18.0; p = p + Vector((math.sin(f * 2.1), math.cos(f * 2.9), math.sin(f * 3.7))) * 0.0025 * a_
    q = (t - p).to_track_quat('-Z', 'Y')
    amp = 0.0 if ANIM else 0.10
    for f0_, a0_, d0_ in ((FIRE, 0.9, 22), (IMPACT, 0.6, 30), (SPLIT, 0.25, 20), (GRAZE + 9, 0.35, 18), (SWAP - 4, 0.2, 16)):
        if f0_ <= f < f0_ + d0_: amp += a0_ * (1 - (f - f0_) / d0_) ** 2
    jx = math.sin(f * 0.21) * 0.6 + math.sin(f * 0.53 + 1.3) * 0.3 + math.sin(f * 1.37 + 0.4) * 0.1
    jy = math.sin(f * 0.17 + 2.1) * 0.6 + math.sin(f * 0.61 + 0.2) * 0.3 + math.sin(f * 1.21 + 2.7) * 0.1
    q = q @ Euler((math.radians(amp * jx), math.radians(amp * jy), 0)).to_quaternion()
    if prev is not None and prev.dot(q) < 0: q = -q
    prev = q
    cam.location = p; cam.keyframe_insert("location", frame=f)
    cam.rotation_quaternion = q; cam.keyframe_insert("rotation_quaternion", frame=f)
    cd.lens = cn(f); cd.keyframe_insert("lens", frame=f)
    fp = cf(f) if lk is None else cf(f).lerp(lk[2], w)
    cd.dof.focus_distance = max(0.01, (fp - p).length); cd.dof.keyframe_insert("focus_distance", frame=f)
    dd_ = (fp - p).length; st = 11.0 if dd_ < 0.12 else (8.0 if dd_ < 0.35 else (8.0 if ANIM else 4.0))
    cd.dof.aperture_fstop = st; cd.dof.keyframe_insert("aperture_fstop", frame=f)

# ---------------------------------------------------------------- ring glints (rim kick placed near the camera->ring reflection)
lg = O["L_RingGlint"]
GL_KEYS = [(1, 0), (F(5.2), 0), (F(5.5), 0.12), (F(5.9), 0.02), (F(6.3), 0.08), (F(6.7), 0.0), (F(8.3), 0.0), (F(8.6), 0.25), (F(8.8), 0.06), (IMPACT - 6, 0.3), (IMPACT, 0.0)]
for f, e in GL_KEYS:
    at(f); r = wpos(ring); cp = cam.matrix_world.translation
    lg.location = r + (cp - r).normalized() * 0.03 + Vector((0, 0, 0.025)); key(lg, "location", f)
    lg.data.energy = e; lg.data.keyframe_insert("energy", frame=f)
# rim light brightens on the hand just before impact
rim = O["L_RimCool"].data
for f, e in ((1, 35), (F(8.0), 35), (F(8.7), 90), (IMPACT + 20, 90), (F(10.5), 35)):
    rim.energy = e; rim.keyframe_insert("energy", frame=f)

# sweat sheen on the owner's skin through the terror beats
for m in bpy.data.materials:
    gn = m.node_tree.nodes.get("SkinGroup") if m.node_tree else None
    if gn and m.name.startswith("Owner"):
        cc = gn.inputs["Clearcoat"]
        for f, v in (((1, 0.05), (1410, 0.05)) if ANIM else ((1, 0.08), (FIRE, 0.1), (300, 0.18), (1000, 0.22), (1249, 0.18), (1410, 0.12))):
            cc.default_value = v; cc.keyframe_insert("default_value", frame=f)
# lift the shadows in the opening wide (0-1.2 s)
fl_ = O["L_FillBounce"].data
for f, e in ((1, 45), (60, 40), (90, 15)):
    fl_.energy = e; fl_.keyframe_insert("energy", frame=f)
# officer: hidden while the robber is in the room (keeps the opening uncluttered)
for o in O:
    if o.name.startswith("Officer"):
        hide(o, 1, True); hide(o, 1100, False); const_hide(o)

# ---------------------------------------------------------------- beats
beats = [{"beat": 1, "frame": 1, "first_words": "The robber fired the gun"}, {"beat": 2, "frame": F(2.7), "first_words": "threw his hands up"},
         {"beat": 3, "frame": F(6.8), "first_words": "instead of going through"}, {"beat": 4, "frame": F(9.0), "first_words": "the bullet hit his wedding ring"},
         {"beat": 5, "frame": F(11.0), "first_words": "glanced off the metal"}, {"beat": 6, "frame": F(14.4), "first_words": "One piece lodged"},
         {"beat": 7, "frame": F(16.3), "first_words": "the other went into"}, {"beat": 8, "frame": F(17.9), "first_words": "minor injuries"},
         {"beat": 9, "frame": F(20.8), "first_words": "walked away okay"}]
json.dump(beats, open(os.path.join(ROOT, "beats.json"), "w"), indent=1)
sc.frame_set(1)
print("IMPACT", tuple(round(v, 3) for v in P_IMP), "MZ", tuple(round(v, 3) for v in MZ), "dist", round((P_IMP - MZ).length, 3))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SAVED", OUT)
