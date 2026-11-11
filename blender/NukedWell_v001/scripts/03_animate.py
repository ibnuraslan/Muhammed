"""NukedWell animation: camera spline, device/crane/cap, concrete, fire, gas, sky, blast, squeeze, crew.
blender -b scene.blend --python 03_animate.py -- <pipeline_dir> <out.blend>"""
import sys, os, math, random
import bpy
from mathutils import Vector, Matrix

PIPE, OUT = sys.argv[sys.argv.index("--") + 1:][:2]
exec(open(os.path.join(PIPE, "anim_lib.py")).read())
HERE = os.path.dirname(os.path.abspath(__file__))
sc = bpy.context.scene
O = bpy.data.objects
END = sc.frame_end
SHAFT = Vector((-14.0, -2.7)); WELL = Vector((0.0, -1.6)); BLAST_Z = -60.0
random.seed(18)

def ground_z(x, y):   # flat site; the shaft collar top is at 0.5
    r = (Vector((x, y)) - SHAFT).length
    return 0.5 if 2.35 < r < 3.45 else 0.0

def F(t): return 1 + round(t * 60)          # seconds -> frame
BEAT = {1: F(0.0), 2: F(3.2), 3: F(5.7), 4: F(9.0), 5: F(10.3), 6: F(14.9), 7: F(18.5), 8: F(23.0), 9: F(26.4), 10: F(28.0), 11: F(31.6)}

def K(target, path, keys, interp=None, index=-1):
    """keys: [(frame, value)], value scalar or tuple"""
    for f, v in keys:
        if isinstance(v, (tuple, list, Vector)):
            setattr(target, path, v) if index < 0 else None
            if index < 0: target.keyframe_insert(path, frame=f)
        else:
            if index >= 0:
                getattr(target, path)[index] = v; target.keyframe_insert(path, index=index, frame=f)
            else:
                setattr(target, path, v); target.keyframe_insert(path, frame=f)
    if interp:
        ad = target.animation_data if hasattr(target, "animation_data") else target.id_data.animation_data
        set_interp(target, interp)
def fcurves_of(idb):
    ad = idb.animation_data
    if not ad or not ad.action: return []
    out = []
    act = ad.action
    for layer in getattr(act, "layers", []):
        for strip in layer.strips:
            for cb in getattr(strip, "channelbags", []):
                out += list(cb.fcurves)
    if not out and hasattr(act, "fcurves"): out = list(act.fcurves)
    return out
def set_interp(target, interp, frames=None):
    idb = target.id_data
    for fc in fcurves_of(idb):
        for kp in fc.keyframe_points:
            if frames is None or int(kp.co.x) in frames: kp.interpolation = interp
def sock(mat, node, idx=0):
    return bpy.data.materials[mat].node_tree.nodes[node].outputs[idx]
def KS(socket, keys, interp=None):
    for f, v in keys:
        socket.default_value = v; socket.keyframe_insert("default_value", frame=f)
def sample(fn, f0, f1, step=2):
    fs = list(range(f0, f1 + 1, step))
    if fs[-1] != f1: fs.append(f1)
    return [(f, fn(f)) for f in fs]

# ================================================================== time-reversal map for the rewind (beat 3)
RW0, RW1 = BEAT[3], BEAT[4] - 1          # 343..540: plays 1..343 backwards (first part), then pre-history
def story(f):
    """frame -> 'story frame' used by beat 1-2 elements; rewind runs it backwards"""
    if f <= RW0: return f
    if f <= RW0 + 120: return RW0 - (f - RW0) * (RW0 - 1) / 120.0     # 343 -> 1 over 2 s
    return 1 - (f - RW0 - 120)        # keeps going "before frame 1"

# ================================================================== device / hook / cable / crane slew
CR = O["Crane_Slew"]; TROL = O["Crane_Trolley"]; HOOK = O["Hook"]; DEV = O["Device"]; CABLE = O["Cable"]; CAP = O["Cap"]
CB = CR.location.copy()
def slew_for(p2):
    d = p2 - CB.to_2d(); return math.atan2(d.x, -d.y), d.length
YAW_SHAFT, R_SHAFT = slew_for(SHAFT); YAW_WELL, R_WELL = slew_for(WELL); YAW_PARK = R_(150)
TOPZ = 32.5
def dev_z_story(s):
    """device origin (top) height vs story frame in the opening (1966, beats 1-2)"""
    if s >= 193: return -57.0
    if s >= 1:
        t = (s - 1) / 192.0; e = smooth(t) ** 1.15
        return 3.0 + (-57.0 - 3.0) * e
    # before frame 1 (rewind): device rises up to the jib, then the crane parks it
    return min(TOPZ - 3.0, 3.0 + (1 - s) * 0.55)
def dev_state(f):
    """(xy, z, yaw_slew, trolley_r, visible)"""
    if f <= RW1:
        s = story(f); z = dev_z_story(s)
        yaw = YAW_SHAFT
        if s < -40: yaw = YAW_SHAFT + (YAW_PARK - YAW_SHAFT) * smooth((-40 - s) / 50.0)
        return yaw, R_SHAFT, z, f < RW1 - 6
    b8 = BEAT[8]
    if f < 1250: return YAW_PARK, R_SHAFT, TOPZ - 3, False
    if f < b8:   # crane swings the device over the shaft (after the cap job)
        t = smooth((f - 1255) / 110.0); return YAW_PARK + (YAW_SHAFT - YAW_PARK) * t, R_SHAFT, TOPZ - 3 - (TOPZ - 3 - 10.6) * smooth((f - 1290) / 90.0), True
    if f < 1460: return YAW_SHAFT, R_SHAFT, 10.6 - 0.9 * smooth((f - b8) / 79.0), True
    t = (f - 1460) / (BEAT[9] - 6 - 1460)
    return YAW_SHAFT, R_SHAFT, 9.7 + (-57.0 - 9.7) * smooth(min(1, t)) ** 1.6, True

def cap_state(f):
    """cap: hangs from the hook 1040-1170 over the well, sits on the wellhead after"""
    b7 = BEAT[7]
    if f < 1000: return YAW_PARK, R_WELL, None
    if f < b7:
        t = smooth((f - 1000) / (b7 - 1000)); return YAW_PARK + (YAW_WELL - YAW_PARK) * t, R_WELL, 16.0
    if f < 1172: return YAW_WELL, R_WELL, 16.0 - (16.0 - 3.75) * smooth((f - b7) / (1172 - b7)) ** 1.3
    return YAW_WELL, R_WELL, 3.75

for f in range(1, END + 1, 2):
    yaw_d, r_d, z_d, vis = dev_state(f)
    if 1000 <= f < 1250:
        yaw_c, r_c, z_c = cap_state(f)
        yaw = yaw_c; r = r_c; hook_z = z_c + 0.8 if z_c is not None else TOPZ - 3
        if f >= 1172: hook_z = 3.75 + 0.8 + (TOPZ - 3 - 4.55) * smooth((f - 1180) / 60.0)   # hook released, rises
    else:
        yaw, r, hook_z = yaw_d, r_d, z_d + 0.7
    CR.rotation_euler = (0, 0, yaw); CR.keyframe_insert("rotation_euler", index=2, frame=f)
    TROL.location = (0, -r, 32.9); TROL.keyframe_insert("location", frame=f)
    tip = CB + Matrix.Rotation(yaw, 3, 'Z') @ Vector((0, -r, 0))
    HOOK.location = (tip.x, tip.y, hook_z + 0.6); HOOK.keyframe_insert("location", frame=f)
    CABLE.location = (tip.x, tip.y, hook_z + 1.2); CABLE.scale = (1, 1, max(0.1, 32.4 - (hook_z + 1.2)))
    CABLE.keyframe_insert("location", frame=f); CABLE.keyframe_insert("scale", frame=f)
    swing = 0.0
    if f > BEAT[8] - 130 and f < 1460: swing = 0.6 * math.sin(f * 0.07) * (1 - smooth((f - 1380) / 70.0))
    DEV.location = (tip.x + swing, tip.y, z_d); DEV.rotation_euler = (0, R_(swing * 2), (f * 0.002) % 6.3)
    DEV.keyframe_insert("location", frame=f); DEV.keyframe_insert("rotation_euler", frame=f)
    yaw_c, r_c, z_c = cap_state(f)
    if z_c is None: CAP.location = (0, 0, -200)
    else:
        ctip = CB + Matrix.Rotation(yaw_c, 3, 'Z') @ Vector((0, -r_c, 0)) if f < BEAT[7] else WELL.to_3d()
        CAP.location = (ctip.x, ctip.y, z_c) if f < 1172 else (WELL.x, WELL.y, 3.75)
    CAP.keyframe_insert("location", frame=f)
for o, keys in ((DEV, [(1, False), (RW1 - 6, True), (1250, False)]),):
    for f, h in keys: o.hide_render = h; o.keyframe_insert("hide_render", frame=f)
for ch in DEV.children:
    for f, h in ((1, False), (RW1 - 6, True), (1250, False)): ch.hide_render = h; ch.keyframe_insert("hide_render", frame=f)

# ================================================================== concrete pour (beat 2), mixer drum, rewind
MIX = O["MixerTruck"]; DRUM = O["MixerDrum"]; PLUG = O["ConcretePlug"]; POUR = O["PourStream"]
bpy.context.view_layer.update()
chute = O["MixerChute"]; tipw = chute.matrix_world @ Vector((1.7, 0, 0))
mouth = Vector((SHAFT.x, SHAFT.y, 0.6))
# arc stream: a curve from the chute tip to the shaft mouth then down the shaft to the plug top
cu = bpy.data.curves.new("PourArc", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.32; cu.bevel_resolution = 2; cu.use_fill_caps = True
sp = cu.splines.new('POLY'); pts = []
for k in range(9):
    t = k / 8; p = tipw.lerp(mouth, t); p.z += 1.2 * math.sin(math.pi * t) * 0.3 - 0.0; pts.append(p)
pts += [Vector((SHAFT.x, SHAFT.y, z)) for z in (-5, -15, -25, -35, -45, -55)]
sp.points.add(len(pts) - 1)
for p_, v in zip(sp.points, pts): p_.co = (*v, 1)
ARC = bpy.data.objects.new("PourArc", cu); bpy.data.collections["FX"].objects.link(ARC); cu.materials.append(bpy.data.materials["M_WetConcrete"])
POUR.hide_render = True; POUR.keyframe_insert("hide_render", frame=1)
NPTS = len(pts)
def pour_state(s):
    """story frame -> (stream end fraction 0..1 along the arc, plug height)"""
    if s < 200: return 0.0, 0.0
    plug = 22.0 * smooth((s - 215) / 125.0)
    top = -56.3 + plug
    # fraction of the arc down to the plug top
    L_arc = (mouth - tipw).length; L_down = 0.6 - top
    end = min(1.0, (s - 200) / 14.0)
    frac = (L_arc + L_down * end) / (L_arc + 56.9)
    if s > 338: frac *= max(0.0, 1 - (s - 338) / 6.0)
    return frac, plug
for f in range(1, RW1 + 2, 2):
    s = story(f); frac, plug = pour_state(s)
    cu.bevel_factor_end = max(0.0, frac); cu.keyframe_insert("bevel_factor_end", frame=f)
    PLUG.scale = (1, 1, max(0.001, plug)); PLUG.location = (SHAFT.x, SHAFT.y + 1.3, -56.3); PLUG.keyframe_insert("scale", frame=f); PLUG.keyframe_insert("location", frame=f)
    DRUM.rotation_euler = (0, R_(-76), -s * 0.09); DRUM.keyframe_insert("rotation_euler", frame=f)
for f, h in ((1, False), (RW1, True), (BEAT[9] - 30, False)):
    ARC.hide_render = h; ARC.keyframe_insert("hide_render", frame=f)
cu.bevel_factor_end = 0.0; cu.keyframe_insert("bevel_factor_end", frame=RW1 + 2)
# plug for the real shot (beat 8-9): fills fast behind the descending device
for f in range(BEAT[9] - 30, BEAT[9] + 2, 2):
    t = smooth((f - (BEAT[9] - 30)) / 28.0)
    PLUG.scale = (1, 1, max(0.001, 22 * t)); PLUG.keyframe_insert("scale", frame=f)
    cu.bevel_factor_end = t * 0.6 + 0.0; cu.keyframe_insert("bevel_factor_end", frame=f)
for f, v in ((BEAT[9] + 4, 0.0),): cu.bevel_factor_end = v; cu.keyframe_insert("bevel_factor_end", frame=f)
for f, h in ((BEAT[9] + 4, True),): ARC.hide_render = h; ARC.keyframe_insert("hide_render", frame=f)
# mixer drives in reverse during the rewind (its rewound arrival), parked again later
for f in range(1, END + 1, 4):
    s = story(f) if f <= RW1 else 1e9
    x = -23.5 if s >= -10 else -23.5 - min(60.0, (-10 - s) * 0.5)
    if f > RW1: x = -23.5 if f > 1250 else -80.0
    MIX.location = (x, 2.2, 0); MIX.keyframe_insert("location", frame=f)

# ================================================================== fire / smoke / fissures / cracks / gas
FIRE, SMOKE = O["FireColumn"], O["SmokePlume"]
FIS = [O["FissureFire%d" % i] for i in range(6)]; CRK = [O["Crack%d" % i] for i in range(6)]
b4, b5, b7, b11 = BEAT[4], BEAT[5], BEAT[7], BEAT[11]
def fire_h(f):
    """main column height scale 0..1"""
    if f <= RW0 + 70: return 1.0
    if f <= RW1: return max(0.0, 1 - smooth((f - RW0 - 70) / 110.0))
    if f < b4 + 52: return 0.0
    if f < b4 + 80: return 1.15 * smooth((f - b4 - 52) / 28.0)
    if f < 1172: return 1.0 + 0.15 * max(0.0, 1 - (f - b4 - 80) / 30.0)
    if f < 1215: return 0.12 + 0.05 * math.sin(f * 0.8)
    if f < 1260: return 0.12 + 0.6 * smooth((f - 1215) / 45.0)
    if f < b11: return 0.75
    if f < b11 + 70: return 0.75 - 0.6 * smooth((f - b11) / 70.0)
    if f < b11 + 140: return max(0.0, 0.15 * (1 - (f - b11 - 70) / 70.0) * (0.6 + 0.4 * math.sin(f * 0.9)))
    return 0.0
def fis_h(f):
    if f <= RW0 + 50: return 1.0
    if f <= RW1: return max(0.0, 1 - smooth((f - RW0 - 50) / 90.0))
    if f < 1232: return 0.0
    if f < 1262: return 1.2 * smooth((f - 1232) / 30.0)
    if f < b11 + 20: return 1.0
    return max(0.0, 1 - smooth((f - b11 - 20) / 70.0))
def crack_s(f):
    if f <= RW0 + 40: return 1.0
    if f <= RW1: return max(0.0, 1 - smooth((f - RW0 - 40) / 80.0))
    if f < 1205: return 0.0
    return smooth((f - 1205) / 35.0)
for f in range(1, END + 1, 2):
    h = fire_h(f); w = 1.0 + 0.04 * math.sin(f * 0.21) + 0.03 * math.sin(f * 0.53)
    FIRE.scale = (max(0.02, (0.35 + 0.65 * min(1, h)) * w), max(0.02, (0.35 + 0.65 * min(1, h)) * w), max(0.001, h)); FIRE.keyframe_insert("scale", frame=f)
    SMOKE.scale = (max(0.05, min(1, h)), max(0.05, min(1, h)), max(0.05, min(1, h))); SMOKE.location = (4, 8, 2.6 + 97 * max(0.05, min(1, h)))
    SMOKE.keyframe_insert("scale", frame=f); SMOKE.keyframe_insert("location", frame=f)
    for i, o in enumerate(FIS):
        hh = fis_h(f - i * 3); ww = 1.0 + 0.08 * math.sin(f * 0.3 + i)
        o.scale = (max(0.02, ww * min(1, hh + 0.2) if hh > 0 else 0.02), max(0.02, ww * min(1, hh + 0.2) if hh > 0 else 0.02), max(0.001, hh))
        o.keyframe_insert("scale", frame=f)
    for i, o in enumerate(CRK):
        s_ = crack_s(f - i * 2); o.scale = (max(0.001, s_),) * 3; o.keyframe_insert("scale", frame=f)
fm = bpy.data.materials["M_Fire"].node_tree.nodes
for mat in ("M_Fire", "M_FissureFire", "M_Smoke"):
    nn = bpy.data.materials[mat].node_tree.nodes
    KS(nn["FireNoise"].inputs['W'], [(1, 0.0), (END, 36.0)]); KS(nn["FlowMap"].inputs['Location'], [(1, (0, 0, 0)), (END, (0, 0, -30.0 if mat != "M_Smoke" else -8.0))])
    for fc in fcurves_of(bpy.data.materials[mat].node_tree):
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
KS(sock("M_Crack", "Principled BSDF", 0).node.inputs['Emission Strength'], [(1, 2.5), (RW1, 0.0), (1205, 0.0), (1235, 4.0), (b11, 3.0), (b11 + 90, 0.0)])
# fire lights
for i in range(3):
    L = O["L_Fire%d" % i]
    keys = []
    for f in range(1, END + 1, 4):
        h = fire_h(f); fl = 1 + 0.25 * math.sin(f * 0.9 + i) + 0.15 * math.sin(f * 2.3 + i * 2)
        keys.append((f, (1.5e5, 2.0e5, 1.2e5)[i] * min(1.2, h) * fl))
    K(L.data, "energy", keys)
# embers: small hot sparks spiralling up out of the column (deterministic keys, no sim)
import bmesh
M_EMB = bpy.data.materials.new("M_Ember"); M_EMB.use_nodes = True
pe = M_EMB.node_tree.nodes["Principled BSDF"]; pe.inputs['Base Color'].default_value = (1, 0.4, 0.1, 1)
pe.inputs['Emission Color'].default_value = (1.0, 0.45, 0.12, 1); pe.inputs['Emission Strength'].default_value = 40.0
bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.12); me_e = bpy.data.meshes.new("Ember"); bm.to_mesh(me_e); bm.free()
me_e.materials.append(M_EMB)
rng = random.Random(7)
for i in range(70):
    e = bpy.data.objects.new("Ember%02d" % i, me_e); bpy.data.collections["FX"].objects.link(e); e.visible_shadow = False
    per = rng.randint(110, 200); ph = rng.random() * per; a0 = rng.random() * 6.28; r0 = rng.uniform(3, 11); sp = rng.uniform(0.6, 1.4)
    for f in range(1, END + 1, 6):
        t = ((f + ph) % per) / per; h = fire_h(f)
        if h < 0.25:
            e.location = (0, 0, -300)
        else:
            a = a0 + t * 9 * sp; r = r0 + t * 25
            e.location = (WELL.x + r * math.cos(a), WELL.y + r * math.sin(a), 6 + t * 150 * h)
        e.keyframe_insert("location", frame=f)
        e.scale = (max(0.05, 1 - t),) * 3; e.keyframe_insert("scale", frame=f)
# gas flow in the casing: pulses race up during the eruption; cut off above the pinch after beat 10
gm = bpy.data.materials["M_GasFlow"].node_tree.nodes
KS(gm["GasAmt"].outputs[0], [(1, 0.0), (b4, 0.0), (b4 + 12, 1.0), (b5 + 60, 1.0), (b5 + 120, 0.0), (BEAT[10] - 40, 0.0), (BEAT[10] - 10, 0.8), (END, 0.8)])
KS(gm["GasTop"].outputs[0], [(1, 5.0), (BEAT[10] + 40, 5.0), (BEAT[10] + 75, BLAST_Z - 2), (END, BLAST_Z - 2)])
KS(gm["GasMap"].inputs['Location'], [(1, (0, 0, 0)), (END, (0, 0, -260.0))])
for fc in fcurves_of(bpy.data.materials["M_GasFlow"].node_tree):
    if fc.data_path.endswith("inputs[1].default_value"):
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
rv = bpy.data.materials["M_ResGlow"].node_tree.nodes
KS(rv["ResAmt"].outputs[0], [(1, 0.5), (b4, 0.6), (b4 + 10, 1.5), (b4 + 70, 0.8), (BEAT[10] + 80, 0.8), (BEAT[10] + 140, 0.3)])

# ================================================================== water + steam (beat 6)
b6 = BEAT[6]
HOSE = {}   # filled by crew section (nozzle positions)

# ================================================================== sun / sky / exposure: day-night in beat 5, sky rewind in beat 3
SUN = O["Sun"]; wn = sc.world.node_tree.nodes
def sun_x(f):
    base = 40.0
    if f <= RW0: return base
    if f <= RW1: return base - 360.0 * smooth((f - RW0) / (RW1 - RW0))     # sun races backwards once
    if f < b5 + 40: return base
    if f < BEAT[6] - 20: return base + 360.0 * smooth((f - b5 - 40) / (BEAT[6] - 20 - b5 - 40))
    if f < b11 + 60: return base
    return base + 18.0 * smooth((f - b11 - 60) / 200.0)      # golden end
def sky(f):
    x = sun_x(f); d = Matrix.Rotation(R_(x), 3, 'X') @ Vector((0, 0, -1)); elev = math.degrees(math.asin(max(-1, min(1, -d.z))))
    day = smooth((elev + 2) / 14.0); dusk = max(0.0, 1 - abs(elev - 6) / 22.0)
    return x, elev, day, dusk
for f in range(1, END + 1, 2):
    x, elev, day, dusk = sky(f)
    SUN.rotation_euler = (R_(x), 0, R_(200)); SUN.keyframe_insert("rotation_euler", index=0, frame=f)
    SUN.data.energy = 3.0 * day; SUN.data.keyframe_insert("energy", frame=f)
    SUN.data.color = (1.0, 0.95 - 0.25 * dusk, 0.88 - 0.4 * dusk); SUN.data.keyframe_insert("color", frame=f)
    wn["SkyDusk"].inputs['Factor'].default_value = min(1.0, dusk * 1.3); wn["SkyDusk"].inputs['Factor'].keyframe_insert("default_value", frame=f)
    wn["SkyNight"].inputs['Factor'].default_value = 1 - day; wn["SkyNight"].inputs['Factor'].keyframe_insert("default_value", frame=f)
    wn["SkyBG"].inputs['Strength'].default_value = 0.7 * (0.35 + 0.65 * day); wn["SkyBG"].inputs['Strength'].keyframe_insert("default_value", frame=f)
    flash = 1.4 * math.exp(-(f - BEAT[9]) / 5.0) if BEAT[9] <= f < BEAT[9] + 40 else 0.0
    sc.view_settings.exposure = 0.3 * (1 - day) + flash; sc.view_settings.keyframe_insert("exposure", frame=f)

# ================================================================== blast (beat 9) + glow + jolt + dust ring
b9, b10 = BEAT[9], BEAT[10]
BL = O["BlastSphere"]; BLE = bpy.data.materials["M_Blast"].node_tree.nodes["BlastEmit"]
K(BL, "scale", [(1, (0.001,) * 3), (b9 - 1, (0.001,) * 3), (b9 + 8, (10.5,) * 3), (b9 + 20, (8.5,) * 3), (b10 + 40, (7.5,) * 3)])
KS(BLE.inputs['Strength'], [(1, 0.0), (b9 - 1, 0.0), (b9 + 2, 120.0), (b9 + 20, 30.0), (b9 + 70, 3.0), (b10 + 40, 0.6)])
KS(BLE.inputs['Color'], [(b9, (1, 0.97, 0.9, 1)), (b9 + 40, (1.0, 0.6, 0.25, 1)), (b10 + 100, (0.9, 0.3, 0.08, 1))])
K(O["L_Blast"].data, "energy", [(1, 0.0), (b9 - 1, 0.0), (b9 + 3, 6e6), (b9 + 25, 1e6), (b9 + 90, 6e4), (b10 + 120, 1e4)])
st = bpy.data.materials["M_Strata"].node_tree.nodes
KS(st["GlowAmt"].outputs[0], [(1, 0.0), (b9, 0.0), (b9 + 6, 12.0), (b9 + 40, 3.0), (b10, 0.8), (b10 + 60, 0.25), (END, 0.15)])
KS(st["GlowRad"].outputs[0], [(1, 4.0), (b9, 4.0), (b9 + 12, 24.0), (b10 + 60, 18.0)])
# surface jolt: everything above ground rides a JoltRoot
J = bpy.data.objects.new("JoltRoot", None); bpy.data.collections["Set"].objects.link(J)
SKIP = {"CAM_Film", "CAM_Target", "StrataFace", "Casing", "GasFlow", "ReservoirGlow", "ShaftLining", "BlastSphere", "L_Blast", "Sun",
        "Device", "ConcretePlug", "PourStream", "PourArc", "Cable", "Hook", "JoltRoot", "Cap", "FireColumn", "SmokePlume", "DustRing"}
jolted = []
for o in list(O):
    if o.parent is None and o.name not in SKIP and not o.name.startswith(("L_Section", "L_ShaftLamp")) and o.type != 'ARMATURE':
        o.parent = J; jolted.append(o.name)
jk = [(1, 0.0), (b9 + 4, 0.0), (b9 + 10, 1.6), (b9 + 16, -0.3), (b9 + 21, 0.45), (b9 + 27, -0.1), (b9 + 34, 0.0)]
K(J, "location", [(f, (0, 0, z)) for f, z in jk])
DU = O["DustRing"]; dn = bpy.data.materials["M_Dust"].node_tree.nodes
K(DU, "scale", [(1, (0.5, 0.5, 1)), (b9 + 8, (0.5, 0.5, 1)), (b9 + 30, (45, 45, 6)), (b9 + 80, (110, 110, 12)), (b10 + 120, (150, 150, 16))])
KS(dn["DustAmt"].outputs[0], [(1, 0.0), (b9 + 8, 0.0), (b9 + 14, 2.5), (b9 + 70, 1.2), (b10 + 140, 0.0)])
KS(dn["SteamNoise"].inputs['W'], [(1, 0.0), (END, 12.0)])

# ================================================================== squeeze (beat 10): strata wave + casing pinch (shape keys)
FACE = O["StrataFace"]; CAS = O["Casing"]; GASO = O["GasFlow"]
BC = Vector((SHAFT.x, 0, BLAST_Z))
def push(co):
    d = co - BC; d.y = 0; r = d.length
    if r < 1e-3: return Vector()
    a = 9.0 * math.exp(-((r - 6) / 26.0) ** 2) if r > 6 else 9.0 * (r / 6)
    return d.normalized() * a
FACE.shape_key_add(name="Basis")
kq = FACE.shape_key_add(name="Squeeze")
for i, v in enumerate(FACE.data.vertices):
    kq.data[i].co = v.co + push(v.co)
for o in (CAS, GASO):
    o.shape_key_add(name="Basis"); kp_ = o.shape_key_add(name="Pinch")
    for i, v in enumerate(o.data.vertices):
        co = v.co.copy(); w = math.exp(-((co.z - BLAST_Z) / 7.0) ** 2)
        c0 = Vector((0, -1.6, co.z)); rel = co - c0
        nco = c0 + Vector((rel.x * (1 - 0.93 * w), rel.y * (1 - 0.55 * w), 0)) + Vector((push(Vector((0, 0, co.z))).x * 0.35, 0, 0))
        kp_.data[i].co = nco
def key_sk(o, name, keys):
    kb = o.data.shape_keys.key_blocks[name]
    for f, v in keys: kb.value = v; kb.keyframe_insert("value", frame=f)
key_sk(FACE, "Squeeze", [(1, 0.0), (b10 - 2, 0.0), (b10 + 40, 1.1), (b10 + 60, 0.93), (b10 + 80, 1.0)])
for o in (CAS, GASO): key_sk(o, "Pinch", [(1, 0.0), (b10 + 10, 0.0), (b10 + 50, 1.05), (b10 + 70, 1.0)])

# ================================================================== crew
def body_frame(yaw):
    fw = Vector((math.sin(R_(yaw)), -math.cos(R_(yaw)), 0)); lf = Vector((math.cos(R_(yaw)), math.sin(R_(yaw)), 0))
    return fw, lf
def yaw_to(src, dst):
    d = (dst - src).to_2d(); return math.degrees(math.atan2(d.x, -d.y))
CREW = {}
for nm in ("SolA", "SolB", "SolC", "SolD", "EngA", "EngB"):
    rig = make_human_ctrl(O[nm]); CREW[nm] = Human(rig)
# ---------------- soldiers' field caps: rigid, bone-parented to 'head', sized to clear the hair
import bmesh
M_CAPC = bpy.data.materials.get("M_Canvas").copy(); M_CAPC.name = "M_FieldCap"
for nd in M_CAPC.node_tree.nodes:
    if nd.type == 'MIX' and nd.blend_type == 'MULTIPLY': nd.inputs['B'].default_value = (0.24, 0.27, 0.15, 1)
def add_cap(nm):
    rig = O[nm]; hair = next(c for c in rig.children if c.type == 'MESH' and c.name.split(".")[-1].startswith("short"))
    body = next(c for c in rig.children if c.name.endswith(".body"))
    vs = [hair.matrix_world @ v.co for v in hair.data.vertices] + [body.matrix_world @ v.co for v in body.data.vertices if v.co.z > 1.4]
    top = max(v.z for v in vs); band = [v for v in vs if v.z > top - 0.11]
    cx = sum(v.x for v in band) / len(band); cy = sum(v.y for v in band) / len(band)
    rx = max(abs(v.x - cx) for v in band) * 1.06; ry = max(abs(v.y - cy) for v in band) * 1.06
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=1.0)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -0.05], context='VERTS')
    for v in bm.verts: v.co = Vector((v.co.x * rx, v.co.y * ry, max(0.0, v.co.z) * 0.11 + 0.0))
    # bill at the front (-Y)
    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((0, -ry - 0.03, 0.004)) @ Matrix.Diagonal((rx * 1.3, 0.09, 0.012, 1)))
    me = bpy.data.meshes.new(nm + "_Cap"); bm.to_mesh(me); bm.free(); me.materials.append(M_CAPC)
    for p_ in me.polygons: p_.use_smooth = True
    cap = bpy.data.objects.new(nm + "_Cap", me); bpy.data.collections["Props"].objects.link(cap)
    sol = cap.modifiers.new("solid", 'SOLIDIFY'); sol.thickness = 0.012
    bpy.context.view_layer.update()
    W = Matrix.Translation((cx, cy, top - 0.075))
    cap.parent = rig; cap.parent_type = 'BONE'; cap.parent_bone = "head"
    bpy.context.view_layer.update(); cap.matrix_world = W
    return cap
for nm in ("SolA", "SolB", "SolC", "SolD"):
    add_cap(nm)
def hand_local(h, s, pos, yaw, off, d_loc=(0, 0, -1), n_loc=None):
    fw, lf = body_frame(yaw); up = Vector((0, 0, 1))
    sx = 1 if s == "L" else -1
    W = pos.to_3d() + lf * off[0] * 1 + fw * off[1] + up * off[2]
    d = (lf * d_loc[0] + fw * d_loc[1] + up * d_loc[2]).normalized()
    n = (lf * (-sx)) if n_loc is None else (lf * n_loc[0] + fw * n_loc[1] + up * n_loc[2])
    return W, d, n
def pole_for(pos, yaw, s, z=1.0):
    fw, lf = body_frame(yaw); sx = 1 if s == "L" else -1
    return pos.to_3d() + lf * sx * 0.55 - fw * 0.5 + Vector((0, 0, z))
HANDS = {   # local offsets (left(+)/right(-) x, forward, up), finger dir, palm normal (None = inward)
    "side": ((0.24, 0.04, 0.80), (0, 0.15, -1), None),
    "hip": ((0.27, -0.02, 1.0), (0, 0.6, -0.8), None),
    "chest": ((0.12, 0.32, 1.25), (-0.2, 0.9, 0.1), None),
    "point": ((0.18, 0.62, 1.42), (0, 1, 0.05), (0, 0, -1)),
    "point_down": ((0.16, 0.6, 1.05), (0, 0.8, -0.6), (0, 0, -1)),
    "shield": ((0.05, 0.28, 1.62), (0, 0.1, 1), (0, 1, 0)),
    "up": ((0.28, 0.12, 2.02), (0, 0.1, 1), (0, 1, 0)),
    "wave_a": ((0.42, 0.18, 1.9), (0.4, 0.1, 1), (0, 1, 0)),
    "wave_b": ((0.18, 0.22, 1.95), (-0.3, 0.1, 1), (0, 1, 0)),
    "radio": ((0.12, 0.08, 1.58), (0, 0.2, 1), (1, 0, 0)),
    "brace": ((0.3, 0.25, 1.05), (0, 0.6, -0.4), None),
}
def pose(nm, f, pos, yaw, L="side", R="side", crouch=0.03, flex=6.0, twist=0.0, side=0.0, head=(0.0, 0.0),
         feet=None, sway=0.0, hand_world=None):
    """one full key: root, spine, both feet (planted unless given), both hands"""
    h = CREW[nm]; pos = Vector((pos[0], pos[1]))
    fw, lf = body_frame(yaw)
    gz = ground_z(pos.x, pos.y)
    h.key_root(f, Vector((pos.x + lf.x * sway, pos.y + lf.y * sway, gz + h.root_head.z - crouch)), yaw=yaw, flex=flex * 0.4, side=side)
    h.key_spine(f, flex=flex, twist=twist, side=side * 0.5, head=head)
    for s in "LR":
        if feet and s in feet: xy, fy = feet[s]
        else: xy, fy = h.foot_xy(s, pos, yaw), yaw
        h.key_foot(s, f, Vector(xy), fy)
    for s, spec in (("L", L), ("R", R)):
        if hand_world and s in hand_world:
            W, d, n = hand_world[s]
        else:
            off, dl, nl = HANDS[spec]; sx = 1 if s == "L" else -1
            off = (off[0] * sx, off[1], off[2]); dl = (dl[0] * sx, dl[1], dl[2])
            nl = None if nl is None else (nl[0] * sx, nl[1], nl[2])
            W, d, n = hand_local(h, s, pos, yaw, off, dl, nl)
        h.key_hand(s, f, W, d, n, pole_for(pos, yaw, s))
def stance(nm, pos, yaw, front=0.0, width=1.0):
    """feet placement dict: brace stance (L forward, R back)"""
    h = CREW[nm]; fw, lf = body_frame(yaw); pos = Vector(pos)
    out = {}
    for s, k in (("L", 1), ("R", -1)):
        base = h.foot_xy(s, pos, yaw); base = pos + (base - pos) * width
        out[s] = (base + fw.to_2d() * front * k, yaw + (8 * k if front else 0))
    return out
def idle(nm, f0, f1, pos, yaw, L="side", R="side", every=24, gest=None, feet=None, **kw):
    """keys a living hold: weight shifts, head turns, breathing; gest: list of (frame, L, R) overrides"""
    gl = {g[0]: g for g in (gest or [])}
    f = f0; i = 0
    while f <= f1:
        Lh, Rh = L, R
        for gf in sorted(gl):
            if gf <= f: Lh, Rh = gl[gf][1], gl[gf][2]
        ph = i * 1.7 + sum(map(ord, nm)) % 7
        kw2 = dict(kw)
        kw2["head"] = (kw.get("head", (0, 0))[0] + 6 * math.sin(ph * 0.7), kw.get("head", (0, 0))[1] + 22 * math.sin(ph * 0.45))
        kw2["twist"] = kw.get("twist", 0) + 8 * math.sin(ph * 0.5)
        kw2["sway"] = 0.035 * math.sin(ph)
        kw2["side"] = kw.get("side", 0) + 3 * math.sin(ph)
        pose(nm, f, pos, yaw, Lh, Rh, feet=feet, **kw2)
        f += every; i += 1
    if (f - every) != f1: pose(nm, f1, pos, yaw, L, R, feet=feet, **kw)
def walk(nm, f0, f1, p0, p1, yaw=None, backwards=False, stride=0.72):
    h = CREW[nm]; p0 = Vector(p0); p1 = Vector(p1)
    yw = yaw if yaw is not None else yaw_to(p0, p1) + (180 if backwards else 0)
    path = lambda f: p0.lerp(p1, smooth((f - f0) / (f1 - f0))).to_3d()
    h.walk(path, lambda f: yw, f0, f1, stride=stride if not backwards else 0.5)
    for s in "LR":   # arm swing
        for f in range(f0, f1 + 1, 12):
            ph = (f - f0) / 24.0 * math.pi * 2 * (1 if s == "L" else -1)
            pos = p0.lerp(p1, smooth((f - f0) / (f1 - f0)))
            sx = 1 if s == "L" else -1
            W, d, n = hand_local(h, s, pos, yw, (0.25 * sx, 0.12 * math.sin(ph), 0.84), (0, 0.15, -1))
            h.key_hand(s, f, W, d, n, pole_for(pos, yw, s))
    return yw

B = BEAT
sh = SHAFT
# ---------------- beats 1-2 (1966 opening, rim crew); beat 3 rewind holds these as small figures
idle("SolA", 1, B[3] + 60, (sh.x - 4.2, sh.y + 4.2), yaw_to(Vector((sh.x - 4.2, sh.y + 4.2)), sh), "side", "point_down", gest=[(1, "side", "point_down"), (120, "hip", "point_down"), (220, "side", "chest")], flex=14)
idle("SolB", 1, B[3] + 60, (sh.x + 4.0, sh.y + 4.6), yaw_to(Vector((sh.x + 4.0, sh.y + 4.6)), sh), "radio", "side", gest=[(1, "radio", "side"), (150, "side", "point")], flex=10)
idle("EngA", 1, B[3] + 60, (-19.0, 6.2), yaw_to(Vector((-19, 6.2)), Vector((-16, 1))), "wave_a", "side", gest=[(1, "wave_a", "side"), (40, "wave_b", "side"), (80, "wave_a", "side"), (200, "point", "side"), (260, "wave_a", "side")])
idle("EngB", 1, B[3] + 60, (-8.0, 7.5), yaw_to(Vector((-8, 7.5)), sh), "hip", "hip", gest=[(160, "hip", "point")])
idle("SolC", 1, B[3] + 60, (-4.5, 9.5), yaw_to(Vector((-4.5, 9.5)), Vector((0, 0))), "shield", "side")
idle("SolD", 1, B[3] + 60, (-27.5, 9.0), yaw_to(Vector((-27.5, 9.0)), Vector((-23, 3))), "side", "side", gest=[(200, "point", "side")])
# ---------------- beats 4-5 (1963): two engineers far out watching the eruption, soldiers run back
T0 = B[3] + 61
pose("EngA", T0, (34, 52), yaw_to(Vector((34, 52)), WELL)); pose("EngB", T0, (37.5, 55), yaw_to(Vector((37.5, 55)), WELL))
idle("EngA", T0 + 1, B[6] - 40, (34, 52), yaw_to(Vector((34, 52)), WELL), "side", "side", gest=[(B[4] + 55, "shield", "side"), (B[5] + 90, "shield", "point"), (B[5] + 160, "side", "chest")])
idle("EngB", T0 + 1, B[6] - 40, (37.5, 55), yaw_to(Vector((37.5, 55)), WELL), "side", "side", gest=[(B[4] + 58, "shield", "shield"), (B[5] + 120, "hip", "hip")])
for nm, a, b in (("SolA", (6, 20), (16, 46)), ("SolB", (-5, 18), (-12, 45)), ("SolC", (12, 14), (24, 38)), ("SolD", (-14, 12), (-20, 40))):
    pose(nm, T0, a, yaw_to(Vector(a), WELL)); idle(nm, T0 + 1, B[4] + 56, a, yaw_to(Vector(a), WELL), "side", "side")
    yw = walk(nm, B[4] + 57, B[4] + 57 + 150, a, b, stride=1.1)
    idle(nm, B[4] + 208, B[6] - 40, b, yaw_to(Vector(b), WELL), "shield", "side")
# ---------------- beat 6: hose crews (water at the fire), engineer commanding
H1 = (Vector((15.5, 18.5)), Vector((18.0, 22.4)))   # front, back person positions
H2 = (Vector((-16.5, 17.5)), Vector((-19.0, 21.6)))
def hose_setup(name, front, back, nmF, nmB, f0, f1):
    tgt = WELL; yawF = yaw_to(front, tgt)
    fw, lf = body_frame(yawF)
    nozzle = front.to_3d() + fw * 0.85 + Vector((0, 0, 1.12)) - lf * 0.12
    tail = back.to_3d() - fw * 3.0 + Vector((0, 0, 0.1))
    # hose: nozzle -> back person's hands -> trailing on the ground to the truck
    hp = [nozzle, front.to_3d() + fw * 0.2 + Vector((0, 0, 1.0)) - lf * 0.15, back.to_3d() + fw * 0.35 + Vector((0, 0, 0.95)) - lf * 0.12,
          back.to_3d() - fw * 0.8 + Vector((0, 0, 0.2)), tail]
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.055; cu.bevel_resolution = 2
    sp = cu.splines.new('NURBS'); sp.points.add(len(hp) - 1); sp.use_endpoint_u = True; sp.order_u = 3
    for p_, v in zip(sp.points, hp): p_.co = (*v, 1)
    ho = bpy.data.objects.new(name, cu); bpy.data.collections["Props"].objects.link(ho); cu.materials.append(bpy.data.materials["M_DarkSteel"])
    nz = bpy.data.objects.new(name + "_Nozzle", None); bpy.data.collections["Props"].objects.link(nz)
    # hands: on the hose line
    def on_line(a, b, t): return a.lerp(b, t)
    for nm, pos, a, b in ((nmF, front, hp[0], hp[1]), (nmB, back, hp[1], hp[2])):
        yw = yaw_to(pos, tgt)
        WL = on_line(a, b, 0.25 if nm == nmF else 0.55); WR = on_line(a, b, 0.75 if nm == nmF else 0.85)
        dvec = (a - b).normalized()
        hw = {"L": (WL + Vector((0, 0, 0.03)), dvec, Vector((0, 0, -1))), "R": (WR + Vector((0, 0, 0.03)), dvec, Vector((0, 0, -1)))}
        ft = stance(nm, pos, yw, front=0.38, width=1.3)
        f = f0; i = 0
        while f <= f1:
            k = math.sin(i * 1.3)
            pose(nm, f, pos, yw, crouch=0.12 + 0.03 * k, flex=18 + 4 * k, side=2 * k, head=(5, 6 * k), feet=ft, hand_world=hw)
            f += 18; i += 1
    # water arc
    tgt3 = Vector((WELL.x, WELL.y, 6.0)); d = (tgt3 - nozzle)
    wc = bpy.data.curves.new(name + "_Water", 'CURVE'); wc.dimensions = '3D'; wc.bevel_depth = 0.16; wc.bevel_resolution = 2
    sp = wc.splines.new('POLY'); N = 16; sp.points.add(N - 1)
    for k in range(N):
        t = k / (N - 1); p = nozzle.lerp(tgt3, t); p.z += 5.5 * math.sin(math.pi * t); sp.points[k].co = (*p, 1); sp.points[k].radius = 0.6 + 2.5 * t
    wo = bpy.data.objects.new(name + "_Water", wc); bpy.data.collections["FX"].objects.link(wo); wc.materials.append(bpy.data.materials["M_Water"])
    for f, v in ((1, 0.0), (b6 + 8, 0.0), (b6 + 30, 1.0), (B[7] - 10, 1.0), (B[7] + 10, 0.0)):
        wc.bevel_factor_end = v; wc.keyframe_insert("bevel_factor_end", frame=f)
    for f, hdn in ((1, True), (b6 + 6, False), (B[7] + 12, True)):
        wo.hide_render = hdn; wo.keyframe_insert("hide_render", frame=f); ho.hide_render = hdn if f != 1 else True; ho.keyframe_insert("hide_render", frame=f)
    return nozzle
T6 = B[6] - 39
for nm, p in (("SolA", H1[0]), ("SolB", H1[1]), ("SolC", H2[0]), ("SolD", H2[1])):
    pose(nm, T6, p, yaw_to(p, WELL))
HOSE["A"] = hose_setup("HoseA", H1[0], H1[1], "SolA", "SolB", T6 + 1, B[7] + 100)
HOSE["B"] = hose_setup("HoseB", H2[0], H2[1], "SolC", "SolD", T6 + 1, B[7] + 100)
pose("EngA", T6, (1.5, 30.0), yaw_to(Vector((1.5, 24)), WELL)); pose("EngB", T6, (18, 33), yaw_to(Vector((18, 33)), WELL))
idle("EngA", T6 + 1, B[7] + 100, (1.5, 30.0), yaw_to(Vector((1.5, 30)), WELL), "wave_a", "point", every=14,
     gest=[(T6 + 1, "wave_a", "point"), (b6 + 20, "wave_b", "point"), (b6 + 34, "wave_a", "point"), (b6 + 48, "wave_b", "point"), (b6 + 62, "wave_a", "chest"), (b6 + 120, "side", "point"), (b6 + 170, "hip", "hip")])
idle("EngB", T6 + 1, B[7] + 100, (18, 33), yaw_to(Vector((18, 33)), WELL), "radio", "side")
steam = [O["Steam%d" % i] for i in range(3)]
ssock = bpy.data.materials["M_Steam"].node_tree.nodes
KS(ssock["SteamAmt"].outputs[0], [(1, 0.0), (b6 + 26, 0.0), (b6 + 45, 1.4), (b6 + 90, 0.8), (b6 + 120, 1.5), (b6 + 170, 0.7), (B[7] + 20, 0.0)])
KS(ssock["SteamNoise"].inputs['W'], [(1, 0.0), (END, 14.0)])
for i, o in enumerate(steam):
    K(o, "scale", [(b6 + 26, (0.3,) * 3), (b6 + 60 + i * 10, (1.3,) * 3), (b6 + 140, (1.0,) * 3), (B[7] + 20, (1.6,) * 3)])
# ---------------- beat 7: crew backs away from the fissures (fire bursts out of the ground around them)
for nm, a, b in (("SolA", H1[0], (19, 28)), ("SolB", H1[1], (21, 31)), ("SolC", H2[0], (-20, 27)), ("SolD", H2[1], (-22, 30)),
                 ("EngA", (1.5, 30.0), (3, 40)), ("EngB", (18, 33), (22, 42))):
    a = Vector(a); b = Vector(b)
    walk(nm, 1236, 1236 + 90, a, b, yaw=yaw_to(a, WELL), backwards=True)
    idle(nm, 1327, B[8] - 70, b, yaw_to(b, WELL), "shield", "side")
# ---------------- beat 8: soldiers guide the device into the bore, engineer signals the crane
T8 = B[8] - 69
DZ0 = 10.6 - 9.0   # device bottom at the start of beat 8
def dev_guide(nm, sgn, f0, f1):
    pos = SHAFT + Vector((sgn * 2.75, 0.55)); yw = yaw_to(pos, SHAFT)
    pose(nm, f0 - 1, pos, yw)
    f = f0
    while f <= f1:
        _, _, zd, _ = dev_state(f); zb = zd - 9.0
        hz = max(zb + 0.5, 1.55); hz = min(hz, zb + 2.5)
        cx = SHAFT.x + sgn * 1.76 + (0.6 * math.sin(f * 0.07) * (1 - smooth((f - 1380) / 70.0)) if f < 1460 else 0)
        release = smooth((f - 1452) / 14.0)
        hw = {}
        for s, dy in (("L", 0.38 * sgn), ("R", -0.38 * sgn)):
            W = Vector((cx + sgn * 0.02 + sgn * 0.35 * release, SHAFT.y + dy + 0.15, hz + 0.0 - 0.3 * release))
            hw[s] = (W, Vector((0, 0, 1)), Vector((-sgn, 0, 0)))
        pose(nm, f, pos, yw, crouch=0.05, flex=22 - 10 * release, head=(-12, 0), hand_world=hw, sway=0.02 * math.sin(f * 0.1))
        f += 6
dev_guide("SolA", -1, T8 + 2, 1500)
dev_guide("SolB", 1, T8 + 2, 1500)
idle("SolA", 1501, B[9] - 6, SHAFT + Vector((-2.75, 0.55)), yaw_to(SHAFT + Vector((-2.75, 0.55)), SHAFT), "side", "point_down", flex=16)
idle("SolB", 1501, B[9] - 6, SHAFT + Vector((2.75, 0.55)), yaw_to(SHAFT + Vector((2.75, 0.55)), SHAFT), "side", "side", flex=16)
pE = Vector((-8.5, 4.5)); pose("EngA", T8, pE, yaw_to(pE, CB.to_2d()))
idle("EngA", T8 + 1, B[9] - 6, pE, yaw_to(pE, CB.to_2d()), "up", "side", every=12,
     gest=[(T8 + 1, "wave_a", "side"), (T8 + 13, "wave_b", "side"), (T8 + 25, "wave_a", "side"), (T8 + 37, "wave_b", "side"), (1440, "up", "point"), (1480, "side", "point_down")], head=(18, 0))
for nm, p, L, R in (("SolC", Vector((-19.5, 4.0)), "radio", "side"), ("SolD", Vector((-9.5, 8.0)), "hip", "hip"), ("EngB", Vector((-21.0, 7.5)), "side", "chest")):
    pose(nm, T8, p, yaw_to(p, SHAFT)); idle(nm, T8 + 1, B[9] - 6, p, yaw_to(p, SHAFT), L, R)
# ---------------- beats 9-11: everyone behind the sandbags at the bunker (watching the test), jolt stumble, cheer
BK = Vector((-25.0, 62.3))
spots = {"SolA": (-4.2, 0.0), "SolB": (-2.4, 0.3), "SolC": (-0.6, -0.1), "EngA": (1.2, 0.2), "EngB": (3.0, 0.0), "SolD": (4.8, 0.4)}
T9 = B[9] - 5
for nm, (dx, dy) in spots.items():
    p = BK + Vector((dx, dy)); yw = yaw_to(p, Vector((SHAFT.x, SHAFT.y))) * 0.4
    pose(nm, T9, p, yw, "hip" if nm.startswith("Eng") else "side", "side")
    # jolt: stumble (crouch + arms out) riding with the ground (rig not parented: offset root by the jolt)
    for f_, jz in jk:
        if f_ < T9: continue
    pose(nm, B[9] + 9, p, yw, "brace", "brace", crouch=0.18, flex=25, side=8)
    pose(nm, B[9] + 22, p, yw, "brace", "chest", crouch=0.10, flex=12, side=-5, head=(10, 15))
    idle(nm, B[9] + 36, B[11] + 40, p, yw, "side", "chest" if nm != "EngA" else "radio", every=26)
    # cheer when the fire dies
    cf = B[11] + 70 + random.randint(0, 25)
    pose(nm, cf - 8, p, yw, "side", "side", crouch=0.08, flex=8)
    pose(nm, cf + 6, p, yw, "up", "up", crouch=0.0, flex=-6, head=(-18, 0))
    pose(nm, cf + 24, p, yw + 25 * (1 if dx > 0 else -1), "wave_a", "up", crouch=0.02, flex=-4, head=(-10, 25 * (1 if dx < 0 else -1)))
    pose(nm, cf + 44, p, yw - 15 * (1 if dx > 0 else -1), "up", "wave_b", crouch=0.06, flex=0, head=(-14, -20 * (1 if dx < 0 else -1)))
    idle(nm, cf + 60, END, p, yw + 30 * (1 if dx < 0 else -1), "chest", "hip", every=26, head=(0, 0))
# crew rigs ride the jolt too
for nm in CREW:
    O[nm].parent = J

# ================================================================== camera: one continuous Catmull-Rom spline through ~1 s framings
CAMK = [  # frame, camera, target, lens
    (1,    (-8.0, -11.5, 5.2),  (-14.0, -2.7, 3.6), 30),
    (50,   (-8.5, -17.0, 1.6), (-14.0, -2.7, -1.0), 28),
    (100,  (-10.0, -36.0, -10.0), (-10.0, -2.7, -16.0), 24),
    (150,  (-4.0, -50.0, -26.0), (-8.0, -2.7, -32.0), 24),
    (193,  (-12.0, -44.0, -40.0), (-11.0, -2.7, -44.0), 26),
    (240,  (-26.0, -42.0, -32.0), (-13.0, -2.7, -34.0), 24),
    (290,  (-24.0, -44.0, -10.0), (-13.0, -2.7, -10.0), 24),
    (335,  (-29.0, -15.0, 3.2), (-18.5, 2.5, 1.5), 28),
    (380,  (-52.0, -70.0, 40.0), (-8.0, 8.0, 8.0), 24),
    (430,  (-30.0, -170.0, 100.0), (-2.0, 10.0, 12.0), 24),
    (470,  (0.0, -190.0, 105.0), (0.0, 10.0, 15.0), 26),
    (505,  (12.0, -85.0, 22.0), (0.0, 0.0, 0.0), 26),
    (541,  (9.0, -45.0, -35.0), (0.0, -1.6, -62.0), 26),
    (575,  (7.0, -36.0, -16.0), (0.0, -1.6, -20.0), 26),
    (605,  (6.0, -42.0, 7.0), (0.0, 0.0, 14.0), 24),
    (650,  (12.0, -70.0, 18.0), (0.0, 0.0, 55.0), 22),
    (710,  (70.0, -120.0, 30.0), (5.0, 10.0, 60.0), 22),
    (770,  (46.0, -14.0, 3.5), (28.0, 24.0, 22.0), 24),
    (830,  (-8.0, -62.0, 2.6), (0.0, 10.0, 32.0), 22),
    (885,  (-30.0, -48.0, 20.0), (0.0, 20.0, 18.0), 24),
    (935,  (17.0, 33.0, 2.0), (10.0, 14.0, 3.0), 26),
    (990,  (20.0, 15.0, 5.0), (3.0, 2.0, 8.0), 24),
    (1045, (6.0, 26.0, 9.0), (-3.0, 4.0, 10.0), 24),
    (1095, (-30.0, 12.0, 9.0), (-6.0, 14.0, 6.0), 24),
    (1140, (15.0, -22.0, 11.0), (0.0, -1.6, 7.5), 50),
    (1180, (12.0, -18.0, 5.5), (0.0, -1.6, 3.4), 50),
    (1240, (13.0, -24.0, 14.0), (2.0, 10.0, 1.0), 26),
    (1300, (32.0, -62.0, 46.0), (0.0, 14.0, 3.0), 24),
    (1350, (2.0, -40.0, 20.0), (-12.0, 0.0, 6.0), 26),
    (1400, (-6.0, -11.5, 5.5), (-14.0, -2.7, 4.5), 30),
    (1450, (-19.5, -10.5, 2.4), (-14.0, -2.7, 2.6), 24),
    (1500, (-21.0, -6.0, 1.8), (-14.0, -2.7, 0.5), 28),
    (1545, (-17.0, -12.5, -7.0), (-14.0, -2.7, -18.0), 26),
    (1592, (-4.0, -52.0, -40.0), (-14.0, -2.7, -56.0), 24),
    (1632, (-8.0, -72.0, -6.0), (-14.0, 0.0, -20.0), 22),
    (1665, (-21.0, -62.0, 10.0), (-14.0, 5.0, 2.0), 22),
    (1705, (-6.0, -46.0, -40.0), (-7.0, 0.0, -55.0), 26),
    (1760, (-2.0, -17.0, -58.0), (0.0, -1.6, -60.0), 38),
    (1830, (4.0, -40.0, -55.0), (-5.0, 0.0, -55.0), 30),
    (1880, (6.0, -70.0, -42.0), (-4.0, 0.0, -42.0), 26),
    (1925, (2.0, -50.0, 0.5), (0.0, 0.0, 24.0), 24),
    (1968, (14.0, 16.0, 5.0), (0.0, -1.6, 5.0), 26),
    (2015, (-21.0, 50.5, 2.0), (-25.0, 62.0, 1.6), 30),
    (2055, (-17.0, 64.0, 5.5), (-20.0, 40.0, 3.0), 28),
    (2100, (-28.0, 76.0, 11.0), (-8.0, 0.0, 6.0), 26),
    (2160, (-32.0, 98.0, 30.0), (-6.0, 0.0, 4.0), 26),
]
CAM = O["CAM_Film"]; TG = O["CAM_Target"]
cpos = catmull([(k[0], Vector(k[1])) for k in CAMK]); ctg = catmull([(k[0], Vector(k[2])) for k in CAMK]); clens = pchip([(k[0], float(k[3])) for k in CAMK])
for f in range(1, END + 1):
    p = cpos(f); t = ctg(f)
    # shake on the detonation
    if B[9] <= f < B[9] + 70:
        a = 0.9 * math.exp(-(f - B[9]) / 18.0)
        p = p + Vector((a * math.sin(f * 2.1), 0, a * math.sin(f * 2.9 + 1)))
    CAM.location = p; CAM.keyframe_insert("location", frame=f)
    TG.location = t; TG.keyframe_insert("location", frame=f)
    CAM.data.lens = clens(f); CAM.data.keyframe_insert("lens", frame=f)
print("CAMKEYS", len(CAMK))
json_beats = [{"beat": k, "frame": v, "first_words": w} for (k, v), w in zip(sorted(BEAT.items()), [
    "The massive nuclear device was lowered down the shaft", "and then concrete was poured on top", "You see, three years earlier",
    "a gas well had erupted into flames", "and a fireball over 400 feet tall", "Engineers tried to put it out with water",
    "And capping it with a lid", "So finally, they sent down a nuclear bomb", "When it detonated", "the enormous blast squeezed the earth",
    "sealing the pipe shut"])]
import json
json.dump(json_beats, open(os.path.join(HERE, "..", "beats.json"), "w"), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("ANIM SAVED", OUT)
