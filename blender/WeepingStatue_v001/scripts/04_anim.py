"""WeepingStatue: every shot as its own clip in its own frame block (hard cuts), characters, props, water FX, one camera
that jumps at the cuts. Block frames come from shots.json, so Phase 2 rebuilds the same clips at the VO frames
(each clip is built at 1x and only trimmed, never stretched).
blender -b statue.blend --python 04_anim.py -- <shots.json> <out.blend>"""
import sys, os, math, json, random
import bpy
from mathutils import Vector, Matrix, Quaternion
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "..", "..", "pipeline", "anim_lib.py")).read())
exec(open(os.path.join(HERE, "..", "..", "pipeline", "hand_poses.py")).read())
A = sys.argv[sys.argv.index("--") + 1:]
SHOTS = json.load(open(A[0])); OUT = A[1]
V = Vector
sc = bpy.context.scene
random.seed(11)
BX = sc["BX"]; TOE = V(sc["TOE"])
ORDER = ["S01", "S02", "S03", "S04", "S05", "S06", "S07", "S08", "S09", "S10", "S11", "S12", "S13", "S14", "S15", "S16", "S17", "S18"]
F0 = {k: SHOTS[k][0] for k in ORDER}; F1 = {k: SHOTS[k][1] for k in ORDER}
sc.frame_start = 1; sc.frame_end = max(F1.values())
def ground_z(x, y): return 0.0
def Rz(d): return Matrix.Rotation(R_(d), 3, 'Z')
def Rx(d): return Matrix.Rotation(R_(d), 3, 'X')
def Ry(d): return Matrix.Rotation(R_(d), 3, 'Y')

# ---------------------------------------------------------------- cast: rig controls, eye fix, hand limits, elbows, tints
CAST = ["Woman", "Investigator", "CrowdM1", "CrowdM2", "CrowdM3", "CrowdM4", "CrowdM5", "CrowdM6", "CrowdM7", "CrowdW2", "CrowdW4"]
DROP = ["CrowdW1", "CrowdW3", "Caretaker"]          # a child and a crop top: not used
for n in DROP:
    r = bpy.data.objects[n]
    for c in list(r.children): bpy.data.objects.remove(c, do_unlink=True)
    bpy.data.objects.remove(r, do_unlink=True)
RIG, HUM = {}, {}
for n in CAST:
    RIG[n] = make_human_ctrl(bpy.data.objects[n]); HUM[n] = Human(RIG[n])
    add_hand_limits(RIG[n].o)
    lo_ = [RIG[n].PB["lowerarm01." + s] for s in "LR"]
    for pb in lo_: pb.ik_min_x = R_(-40)                   # MPFB rest elbow ~46 deg: open the limit so arms can hang straight-ish
# eye fix (black-hole eyes): cornea transmission -> transparent mix
def eye_fix(g):
    """eye_fix.py (LegoInNose a44130b) for one EnhancedEye group copy"""
    if "CorneaTransparentMix" in g.nodes: return
    P = next(n for n in g.nodes if n.type == "BSDF_PRINCIPLED"); OUTN = next(n for n in g.nodes if n.type == "GROUP_OUTPUT")
    tl = [l for l in g.links if l.to_node == P and l.to_socket.name == "Transmission Weight"]
    src = tl[0].from_socket if tl else None
    for l in tl: g.links.remove(l)
    P.inputs["Transmission Weight"].default_value = 0.0
    ol = [l for l in g.links if l.from_node == P and l.to_node == OUTN][0]; out_sock = ol.to_socket; g.links.remove(ol)
    tr = g.nodes.new("ShaderNodeBsdfTransparent"); mx = g.nodes.new("ShaderNodeMixShader"); mx.name = "CorneaTransparentMix"
    if src: g.links.new(src, mx.inputs[0])
    else: mx.inputs[0].default_value = 0.0
    g.links.new(P.outputs[0], mx.inputs[1]); g.links.new(tr.outputs[0], mx.inputs[2]); g.links.new(mx.outputs[0], out_sock)
for g in bpy.data.node_groups:
    if g.name.startswith("EnhancedEye"): eye_fix(g); print("EYEFIX", g.name)
def tint(n, key, rgb, mode="MULTIPLY"):
    for ch in RIG[n].o.children:
        if ch.type == 'MESH' and key in ch.name:
            for i, m in enumerate(ch.data.materials):
                if not m or not m.use_nodes: continue
                m = m.copy(); ch.data.materials[i] = m
                p = next((x for x in m.node_tree.nodes if x.type == 'BSDF_PRINCIPLED'), None)
                if p is None: continue
                src = p.inputs['Base Color'].links[0].from_socket if p.inputs['Base Color'].links else None
                mx = m.node_tree.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = mode; mx.inputs['Factor'].default_value = 1.0
                mx.inputs['B'].default_value = (*rgb, 1)
                if src: m.node_tree.links.new(src, mx.inputs['A'])
                else: mx.inputs['A'].default_value = p.inputs['Base Color'].default_value
                m.node_tree.links.new(mx.outputs['Result'], p.inputs['Base Color'])
def suit_blue(n):
    """blue blazer over the white shirt: dark texels (the black suit) become royal blue above the hips, trousers stay dark"""
    hipz = RIG[n].BN["upperleg01.L"].head_local.z + 0.03
    for ch in RIG[n].o.children:
        if ch.type == 'MESH' and "elegantsuit" in ch.name:
            for i, m in enumerate(ch.data.materials):
                m = m.copy(); ch.data.materials[i] = m; nt = m.node_tree
                p = next(x for x in nt.nodes if x.type == 'BSDF_PRINCIPLED')
                src = p.inputs['Base Color'].links[0].from_socket
                lum = nt.nodes.new('ShaderNodeRGBToBW'); nt.links.new(src, lum.inputs[0])
                dark = nt.nodes.new('ShaderNodeMapRange'); dark.inputs['From Min'].default_value = 0.10; dark.inputs['From Max'].default_value = 0.30
                dark.inputs['To Min'].default_value = 1.0; dark.inputs['To Max'].default_value = 0.0; nt.links.new(lum.outputs[0], dark.inputs['Value'])
                tc = nt.nodes.new('ShaderNodeTexCoord'); sp = nt.nodes.new('ShaderNodeSeparateXYZ')
                at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_type = 'GEOMETRY'; at.attribute_name = 'rest_z'
                # rest-pose height: Generated coords of a skinned mesh are its undeformed bounds (0..1)
                nt.links.new(tc.outputs['Generated'], sp.inputs[0])
                zs = [v.co.z for v in ch.data.vertices]; z0, z1 = min(zs), max(zs)
                up = nt.nodes.new('ShaderNodeMapRange'); up.inputs['From Min'].default_value = (hipz - z0) / (z1 - z0) - 0.01
                up.inputs['From Max'].default_value = (hipz - z0) / (z1 - z0) + 0.01; nt.links.new(sp.outputs['Z'], up.inputs['Value'])
                fac = nt.nodes.new('ShaderNodeMath'); fac.operation = 'MULTIPLY'; nt.links.new(dark.outputs['Result'], fac.inputs[0]); nt.links.new(up.outputs['Result'], fac.inputs[1])
                mul = nt.nodes.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MIX'
                blue = nt.nodes.new('ShaderNodeMix'); blue.data_type = 'RGBA'; blue.blend_type = 'MULTIPLY'; blue.inputs['Factor'].default_value = 1.0
                blue.inputs['B'].default_value = (0.08, 0.2, 0.95, 1)
                br = nt.nodes.new('ShaderNodeMath'); br.operation = 'MULTIPLY_ADD'; br.inputs[1].default_value = 4.0; br.inputs[2].default_value = 0.35
                nt.links.new(lum.outputs[0], br.inputs[0])
                bc = nt.nodes.new('ShaderNodeCombineColor'); [nt.links.new(br.outputs[0], bc.inputs[k]) for k in range(3)]
                nt.links.new(bc.outputs[0], blue.inputs['A'])
                nt.links.new(fac.outputs[0], mul.inputs['Factor']); nt.links.new(src, mul.inputs['A']); nt.links.new(blue.outputs['Result'], mul.inputs['B'])
                nt.links.new(mul.outputs['Result'], p.inputs['Base Color'])
suit_blue("Investigator")
tint("Woman", "female_casualsuit02", (0.10, 0.45, 0.16), mode="MIX")       # green (saree-like colour, as in the reference)
tint("CrowdM5", "male_worksuit01", (0.25, 0.45, 0.3))
tint("CrowdW4", "female_casualsuit01", (0.75, 0.2, 0.25))
tint("CrowdM2", "male_casualsuit01", (0.6, 0.65, 1.0))
tint("CrowdW2", "female_elegantsuit01", (0.75, 0.75, 1.0))
# catchlight: tiny camera-only emitter rides with the camera (set up with the camera below)

PARK = {}
for i, n in enumerate(CAST): PARK[n] = V((300.0 + 3 * i, 300.0, -60.0))
ACTIVE = {n: [] for n in CAST}          # (f0, f1) blocks where the rig is on stage
def on_stage(n, f0, f1): ACTIVE[n].append((f0, f1))

def body_R(yaw=0.0, flex=0.0, side=0.0): return Rz(yaw) @ Rx(flex) @ Ry(side)
def rest_head(n, bone): return RIG[n].BN[bone].head_local.copy()
def bw(n, P, Rb, local): return P + Rb @ (local - HUM[n].root_head)
def facing(x, y, tx, ty): return math.degrees(math.atan2(tx - x, -(ty - y)))
def relaxed_hand(n, P, Rb, s, fwd=0.0, out=0.0, up=0.0):
    sx = 1 if s == "L" else -1
    sh = rest_head(n, "upperarm01." + s); wr = rest_head(n, "wrist." + s)
    L = (sh - wr).length
    fem = n.startswith(("CrowdW", "Woman"))
    bulk = {"CrowdM4": 0.06, "Investigator": 0.03}.get(n, 0.0)
    loc = sh + V((sx * (0.10 + (0.04 if fem else 0.0) + bulk + out), -fwd, -L * 0.93 + up))
    W = bw(n, P, Rb, loc)
    d = Rb @ V((0, -0.15 * fwd, -1)).normalized(); nn = Rb @ V((-sx, 0, 0))
    return W, d, nn
def elbow_pole(n, P, Rb, s, back=0.55, out=0.25, down=-0.1):
    sx = 1 if s == "L" else -1
    return bw(n, P, Rb, rest_head(n, "lowerarm01." + s) + V((out * sx, back, down)))
def key_hands(n, f, P, Rb, hands=None):
    for s in "LR":
        h = (hands or {}).get(s)
        if h is None: h = relaxed_hand(n, P, Rb, s)
        pole = h[3] if len(h) > 3 else elbow_pole(n, P, Rb, s)
        HUM[n].key_hand(s, f, h[0], h[1], h[2], pole)
def stand(n, f, x, y, yaw, flex=0.0, head=(0.0, 0.0), twist=0.0, sway=0.0, hands=None, fingers="relaxed", lean=0.0):
    """standing, feet planted, relaxed arms unless `hands` given"""
    H = HUM[n]
    P = V((x, y, H.root_head.z - 0.01)); Rb = body_R(yaw, lean)
    H.key_root(f, P + Rz(yaw) @ V((sway, 0, 0)), yaw=yaw, flex=lean)
    H.key_spine(f, flex=flex, twist=twist, head=(-head[0], head[1]))     # head[0] > 0 = look up
    for s in "LR":
        H.key_foot(s, f, H.foot_xy(s, V((x, y, 0)), yaw), yaw)
    key_hands(n, f, P, Rb, hands)
    if fingers:
        for s in "LR":
            fs = fingers.get(s, "relaxed") if isinstance(fingers, dict) else fingers
            apply_pose(RIG[n].o, s, fs, f)
    return P, Rb
def idle(n, f0, f1, x, y, yaw, head=(0.0, 0.0), head2=None, every=40, flex=0.0, hands=None, fingers="relaxed", ph=0.0, lean=0.0):
    """breathing idle across the block: chest rises, small head move, weight shift"""
    on_stage(n, f0, f1)
    k = 0; f = f0
    while True:
        u = (f - f0) / max(1, f1 - f0)
        hd = head if head2 is None else (head[0] + (head2[0] - head[0]) * smooth(u), head[1] + (head2[1] - head[1]) * smooth(u))
        br = math.sin(ph + k * 1.7)
        stand(n, f, x, y, yaw, flex=flex + 1.2 * br, head=(hd[0] + 1.5 * br, hd[1]), sway=0.006 * math.sin(ph + k), hands=hands,
              fingers=fingers if k == 0 else None, lean=lean)
        if f >= f1: break
        f = min(f1, f + every); k += 1

# ---------------------------------------------------------------- courtyard crowd layout (facing the statue)
LOOK = (0.0, -0.5)
CROWD = {   # name: (x, y)
    "Woman": (0.40, -1.55), "CrowdM1": (-0.85, -1.70), "CrowdW2": (-1.55, -2.15), "CrowdM2": (1.30, -1.95), "CrowdM4": (0.75, -2.55),
    "CrowdM6": (-0.35, -2.50), "CrowdW4": (-1.20, -3.05), "CrowdM5": (1.75, -2.85), "CrowdM7": (0.25, -3.30), "CrowdM3": (-2.15, -2.70),
}
def crowd_idle(f0, f1, names=None, head_up=18.0, skip=()):
    for i, (n, (x, y)) in enumerate(CROWD.items()):
        if (names and n not in names) or n in skip: continue
        yaw = facing(x, y, *LOOK)
        idle(n, f0, f1, x, y, yaw, head=(head_up, random.uniform(-8, 8)), head2=(head_up + random.uniform(-4, 4), random.uniform(-10, 10)),
             every=36 + 4 * (i % 3), ph=i * 1.3)

# ---------------------------------------------------------------- camera (one object, jumps at the cuts)
cam_d = bpy.data.cameras.new("CAM"); cam_d.sensor_fit = 'AUTO'; cam_d.clip_start = 0.02; cam_d.clip_end = 300
cam_d.dof.use_dof = True; cam_d.dof.aperture_fstop = 8.0
CAM = bpy.data.objects.new("CAM", cam_d); sc.collection.objects.link(CAM); sc.camera = CAM
AIM = bpy.data.objects.new("CAM_Aim", None); sc.collection.objects.link(AIM)
tt = CAM.constraints.new('TRACK_TO'); tt.target = AIM; tt.track_axis = 'TRACK_NEGATIVE_Z'; tt.up_axis = 'UP_Y'
cam_d.dof.focus_object = AIM
cl_ = bpy.data.objects.new("CAM_Catchlight", bpy.data.lights.new("CAM_Catchlight", 'POINT')); sc.collection.objects.link(cl_)
cl_.data.energy = 6.0; cl_.data.shadow_soft_size = 0.03; cl_.parent = CAM; cl_.location = (0.08, 0.10, 0.0)
cl_.visible_diffuse = False; cl_.visible_volume_scatter = False; cl_.visible_transmission = False
def vpchip(keys):
    fs = [pchip([(f, v[i]) for f, v in keys]) for i in range(3)]
    return lambda x: V((fs[0](x), fs[1](x), fs[2](x)))
def cam_keys(shot, keys, fstop=8.0):
    """keys: [(u in 0..1 of the block, cam pos, aim pos, lens)] -- PCHIP through them, keyed every frame"""
    f0, f1 = F0[shot], F1[shot]
    fr = [f0 + (f1 - f0) * k[0] for k in keys]
    fc = vpchip(list(zip(fr, [V(k[1]) for k in keys]))) if len(keys) > 2 else None
    for f in range(f0, f1 + 1):
        if len(keys) == 2:
            u = smooth((f - f0) / (f1 - f0)) * 0.6 + 0.4 * (f - f0) / (f1 - f0)
            c = V(keys[0][1]).lerp(V(keys[1][1]), u); a = V(keys[0][2]).lerp(V(keys[1][2]), u); l = keys[0][3] + (keys[1][3] - keys[0][3]) * u
        else:
            c = fc(f); a = vpchip(list(zip(fr, [V(k[2]) for k in keys])))(f); l = pchip(list(zip(fr, [float(k[3]) for k in keys])))(f)
        CAM.location = c; CAM.keyframe_insert("location", frame=f)
        AIM.location = a; AIM.keyframe_insert("location", frame=f)
        cam_d.lens = l; cam_d.keyframe_insert("lens", frame=f)
    cam_d.dof.aperture_fstop = fstop; cam_d.dof.keyframe_insert("aperture_fstop", frame=f0)

# ---------------------------------------------------------------- water FX
DROPS = [bpy.data.objects["FX_Drop%d" % i] for i in range(8)]
DPARK = V((0, 0, -80))
def key_drop(d, f, p, s=1.0):
    d.location = p; d.keyframe_insert("location", frame=f)
    d.scale = (s, s, s * 1.5); d.keyframe_insert("scale", frame=f)
def drop_cycle(d, f_grow, f_fall, f_end, top, floor_z, f0, f1):
    """swell at `top` from f_grow, fall from f_fall under gravity to floor_z, then park (all within the block)"""
    key_drop(d, f0, DPARK, 0.2)
    if f_grow > f0: key_drop(d, f_grow - 1, DPARK, 0.2)
    key_drop(d, f_grow, top, 0.25)
    key_drop(d, f_fall, top - V((0, 0, 0.004)), 1.0)
    t_hit = math.sqrt(2 * max(0.01, top.z - floor_z) / 9.81); fh = f_fall + max(2, int(t_hit * 60))
    for f in range(f_fall + 2, fh + 1, 2):
        t = (f - f_fall) / 60.0
        key_drop(d, f, top - V((0, 0, 0.004 + 4.905 * t * t)), 1.1)
    key_drop(d, fh + 1, DPARK, 0.2)
    if f_end > fh + 1: key_drop(d, f_end, DPARK, 0.2)
    return fh
def drops_idle(f0, f1):
    for d in DROPS: key_drop(d, f0, DPARK, 0.2); key_drop(d, f1, DPARK, 0.2)
M_WATER = bpy.data.materials["M_Water"]
# splash droplets (tiny) on the plinth
SPL = []
for i in range(4):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=10, ring_count=6, radius=0.0035); o = bpy.context.active_object
    o.name = "FX_Splash%d" % i; o.data.materials.append(M_WATER); SPL.append(o); o.location = DPARK
def splash(f, p, f0, f1):
    for i, o in enumerate(SPL):
        a = i * math.pi / 2 + 0.4; v = V((0.25 * math.cos(a), 0.25 * math.sin(a), 0.9 + 0.2 * i))
        o.location = DPARK; o.keyframe_insert("location", frame=f0); o.keyframe_insert("location", frame=f - 1)
        for k in range(0, 14, 2):
            t = k / 60.0; o.location = p + V((v.x * t, v.y * t, v.z * t - 4.905 * t * t)); o.keyframe_insert("location", frame=f + k)
        o.location = DPARK; o.keyframe_insert("location", frame=f + 15); o.keyframe_insert("location", frame=f1)

def fcurves_of(obj):
    ad = obj.animation_data
    if not ad or not ad.action: return []
    out = []
    for layer in ad.action.layers:
        for strip in layer.strips:
            for cb in strip.channelbags: out += list(cb.fcurves)
    return out
# ================================================================= SHOTS
def S01():     # macro of the feet: a drop swells at the toes, runs and falls; a second one starts
    s = "S01"; f0, f1 = F0[s], F1[s]
    drops_idle(f0, f1)
    top = TOE + V((0, 0, -0.004))
    drop_cycle(DROPS[0], f0, f0 + 70, f1, top, 0.33, f0, f1)
    drop_cycle(DROPS[1], f0 + 92, f0 + 150, f1, top + V((0.012, 0.004, 0.006)), 0.33, f0, f1)
    t = TOE
    cam_keys(s, [(0, t + V((0.10, -0.62, 0.20)), t + V((0, 0, 0.12)), 50), (1, t + V((0.06, -0.44, 0.10)), t + V((0, 0, 0.06)), 55)], fstop=11)
def S02():     # low angle: the drop falls from the toes onto the wet plinth, small splash
    s = "S02"; f0, f1 = F0[s], F1[s]
    drops_idle(f0, f1)
    fh = drop_cycle(DROPS[2], f0, f0 + 22, f1, TOE + V((0, 0, -0.004)), 0.33, f0, f1)
    splash(fh, V((TOE.x, TOE.y, 0.325)), f0, f1)
    cam_keys(s, [(0, V((0.6, -1.9, 0.8)), V((0.0, -0.5, 1.25)), 22), (1, V((0.55, -1.8, 0.75)), V((0.0, -0.5, 1.1)), 22)], fstop=11)
def S03():     # the whole statue on the cross: slow push / crane down
    s = "S03"; f0, f1 = F0[s], F1[s]
    drops_idle(f0, f1)
    cam_keys(s, [(0, V((0.6, -7.6, 3.4)), V((0, -0.3, 2.45)), 30), (1, V((0.3, -6.2, 2.6)), V((0, -0.3, 2.3)), 30)], fstop=11)
def S04():     # crowd gathers at the wall, looks up; two point at the feet
    s = "S04"; f0, f1 = F0[s], F1[s]
    crowd_idle(f0, f1, skip=("CrowdM1", "CrowdM2"))
    for n, side, ph in (("CrowdM1", "R", 0.0), ("CrowdM2", "L", 1.0)):
        x, y = CROWD[n]; yaw = facing(x, y, *LOOK); on_stage(n, f0, f1)
        H = HUM[n]; P = V((x, y, H.root_head.z - 0.01)); Rb = body_R(yaw)
        sh = bw(n, P, Rb, rest_head(n, "upperarm01." + side)); tgt = TOE + V((0, -0.05, 0.1))
        dirv = (tgt - sh).normalized()
        for k, f in enumerate((f0, f0 + 30, f0 + 55, f1 - 40, f1)):
            raise_ = 0.0 if k == 0 else 1.0 if k < 4 else 0.85
            W0, d0, n0 = relaxed_hand(n, P, Rb, side)
            W1 = sh + dirv * 0.50
            W = W0.lerp(W1, raise_)
            d = d0.lerp(dirv, raise_).normalized(); nn = (Rz(yaw) @ V((0, 0, -1))).lerp(V((0, 0, -1)), 0.5)
            stand(n, f, x, y, yaw, head=(20.0, 0.0), flex=1.0 * math.sin(k), fingers=None,
                  hands={side: (W, d, nn, sh + V((0, 0, -0.45)) + Rz(yaw) @ V((0.3 if side == "L" else -0.3, 0.2, 0)))})
            apply_pose(RIG[n].o, side, "point" if raise_ > 0.5 else "relaxed", f)
            apply_pose(RIG[n].o, "L" if side == "R" else "R", "relaxed", f)
    drops_idle(f0, f1)
    drop_cycle(DROPS[3], f0 + 20, f0 + 80, f1, TOE + V((0, 0, -0.004)), 0.33, f0, f1)
    cam_keys(s, [(0, V((1.6, -7.4, 3.3)), V((0.0, -1.2, 1.7)), 26), (1, V((1.2, -6.4, 3.0)), V((0.0, -0.9, 1.8)), 27)], fstop=11)
def S05():     # crowd 3/4: faces, murmur; one woman lifts her hands to her chest
    s = "S05"; f0, f1 = F0[s], F1[s]
    crowd_idle(f0, f1, skip=("CrowdW2",), head_up=14.0)
    n = "CrowdW2"; x, y = CROWD[n]; yaw = facing(x, y, *LOOK); on_stage(n, f0, f1)
    H = HUM[n]; P = V((x, y, H.root_head.z - 0.01)); Rb = body_R(yaw)
    chest = bw(n, P, Rb, rest_head(n, "spine03") + V((0, -0.20, 0.02)))
    for k, f in enumerate((f0, f0 + 40, f0 + 75, f1)):
        u = 0.0 if k == 0 else 1.0
        hs = {}
        for side in "LR":
            sx = 1 if side == "L" else -1
            W0, d0, n0 = relaxed_hand(n, P, Rb, side)
            W1 = chest + Rb @ V((0.035 * sx, 0, -0.02 * sx))
            hs[side] = (W0.lerp(W1, u), d0.lerp(Rb @ V((-sx * 0.5, 0, 0.85)), u).normalized(), (Rb @ V((0, 1, 0))).lerp(n0, 1 - u),
                        bw(n, P, Rb, rest_head(n, "lowerarm01." + side) + V((0.28 * sx, 0.15, -0.12))))
        stand(n, f, x, y, yaw, head=(16.0 + 3 * k, -6.0), hands=hs, fingers="relaxed" if k == 0 else None)
    drops_idle(f0, f1)
    cam_keys(s, [(0, V((2.7, -0.95, 1.85)), V((-0.6, -2.5, 1.5)), 28), (1, V((2.5, -0.9, 1.82)), V((-0.7, -2.45, 1.55)), 30)], fstop=8)
def S06():     # the Woman in close-up, looking up at the statue, small smile/breath
    s = "S06"; f0, f1 = F0[s], F1[s]
    crowd_idle(f0, f1, skip=("Woman",))
    n = "Woman"; x, y = CROWD[n]; yaw = facing(x, y, *LOOK)
    idle(n, f0, f1, x, y, yaw, head=(16.0, 4.0), head2=(22.0, -6.0), every=30, ph=0.3)
    drops_idle(f0, f1)
    H = HUM[n]; hd = V((x, y, 0)) + V((0, 0, H.root_head.z)) + (rest_head(n, "head") - H.root_head)
    face = V((x, y, rest_head(n, "head").z + 0.08))
    cam_keys(s, [(0, face + V((-0.30, 0.62, 0.05)), face + V((0, 0, 0.02)), 50), (1, face + V((-0.22, 0.52, 0.03)), face + V((0, 0, 0.03)), 55)], fstop=8)
CUP = bpy.data.objects["PR_Cup"]; CUPW = bpy.data.objects["PR_CupWater"]
def S07():     # the Woman holds a cup of the water at her chest, looks into it, lifts it a little
    s = "S07"; f0, f1 = F0[s], F1[s]
    crowd_idle(f0, f1, skip=("Woman",))
    n = "Woman"; x, y = CROWD[n]; yaw = facing(x, y, *LOOK); on_stage(n, f0, f1)
    H = HUM[n]; P = V((x, y, H.root_head.z - 0.01)); Rb = body_R(yaw)
    fw = Rz(yaw) @ V((0, -1, 0)); sd = Rz(yaw) @ V((1, 0, 0))
    cup_c = V((x, y, 0)) + fw * 0.38 + sd * (-0.10) + V((0, 0, rest_head(n, "spine03").z + 0.02))
    stand(n, f0, x, y, yaw, head=(-8.0, -6.0), fingers="relaxed")
    # place the cup, grip it with the right hand at f0, then Child Of the hand
    CUP.location = cup_c - V((0, 0, 0.046)); CUP.rotation_euler = (0, 0, 0); CUP.keyframe_insert("location", frame=f0)
    ev(f0)
    # the cup rests on her open right palm (no wrap grip: the thumb went through the cup wall)
    fd_ = (fw - sd * 0.25).normalized()
    place_hand(RIG[n].o, "R", f0, cup_c - V((0, 0, 0.046)) - fd_ * 0.022 + sd * 0.014, V((0, 0, 1)), fd_, skin=0.026)
    apply_pose(RIG[n].o, "R", "relaxed", f0)
    ev(f0)
    pbw = RIG[n].o.pose.bones["wrist.R"]
    c_ = CUP.constraints.new('CHILD_OF'); c_.name = "HoldCup"; c_.target = RIG[n].o; c_.subtarget = "wrist.R"
    c_.inverse_matrix = (RIG[n].o.matrix_world @ pbw.matrix).inverted()
    c_.influence = 1.0
    # later keys: copy the gripped IK target and lift it a little (cup follows the hand)
    pb = RIG[n].PB["IK_hand.R"]; L0 = pb.location.copy(); Q0 = pb.rotation_quaternion.copy()
    restR = RIG[n].BN["IK_hand.R"].matrix_local.to_3x3().inverted()
    for f, dz, hd in ((f0 + 50, 0.0, (-10.0, -4.0)), (f0 + 95, 0.06, (12.0, 0.0)), (f1, 0.07, (18.0, 2.0))):
        stand(n, f, x, y, yaw, head=hd, fingers=None, hands={"L": None})
        pb.location = L0 + restR @ V((0, 0, dz)); pb.rotation_quaternion = Q0
        pb.keyframe_insert("location", frame=f, group="IK_hand.R"); pb.keyframe_insert("rotation_quaternion", frame=f, group="IK_hand.R")
        pe = RIG[n].PB["Pole_elbow.R"]; pe.keyframe_insert("location", frame=f, group="Pole_elbow.R")
    CUPW.location = (0, 0, 0.055); CUPW.keyframe_insert("location", frame=f0)
    drops_idle(f0, f1)
    face = V((x, y, rest_head(n, "head").z + 0.02))
    cam_keys(s, [(0, cup_c + fw * 0.75 + sd * 0.30 + V((0, 0, 0.15)), cup_c.lerp(face, 0.45), 40),
                 (1, cup_c + fw * 0.62 + sd * 0.24 + V((0, 0, 0.12)), cup_c.lerp(face, 0.5), 42)], fstop=8)
    return c_
def S08():     # a man lays his fingertips on the statue's foot; the others watch
    s = "S08"; f0, f1 = F0[s], F1[s]
    crowd_idle(f0, f1, skip=("CrowdM4", "Woman"))
    n = "Woman"; x, y = CROWD[n]; idle(n, f0, f1, x - 0.15, y - 0.25, facing(x - 0.15, y - 0.25, *LOOK), head=(18.0, 0.0), ph=2)
    n = "CrowdM4"; on_stage(n, f0, f1)
    x, y = 0.18, -1.02; yaw = facing(x, y, TOE.x, TOE.y)
    H = HUM[n]; P = V((x, y, H.root_head.z - 0.01)); Rb = body_R(yaw)
    sh = bw(n, P, Rb, rest_head(n, "upperarm01.R"))
    ev(f0)
    stb = bpy.data.objects["S1_Statue.body"]; dg_ = bpy.context.evaluated_depsgraph_get(); se_ = stb.evaluated_get(dg_)
    contact = V((TOE.x + 0.06, sc["CROSS_FRONT_Y"], TOE.z - 0.16))     # flat wet stone of the cross under the feet
    cn_ = V((0, -1, 0))
    print("S08 contact", tuple(round(t, 3) for t in contact), tuple(round(t, 2) for t in cn_))
    for k, f in enumerate((f0, f0 + 40, f0 + 70, f1)):
        stand(n, f, x, y, yaw, head=(22.0, 0.0), lean=6.0 if k else 0.0, fingers="relaxed" if k == 0 else None)
        if k == 0: continue
    ev(f0 + 70)
    place_hand(RIG[n].o, "R", f0 + 70, contact, -cn_, V((-0.15, 0, 1)).normalized(), skin=0.018)
    place_hand(RIG[n].o, "R", f1, contact + V((0, 0, -0.015)), -cn_, V((-0.15, 0, 1)).normalized(), skin=0.018)
    apply_pose(RIG[n].o, "R", "flat_palm", f0 + 70); apply_pose(RIG[n].o, "R", "flat_palm", f1)
    # reach in (between f0+10 and f0+70): an intermediate key below/in front of the contact
    place_hand(RIG[n].o, "R", f0 + 40, contact + V((0.0, -0.18, -0.20)), V((0, 1, 0.3)).normalized(), V((0, 0.3, 1)).normalized(), skin=0.03)
    apply_pose(RIG[n].o, "R", "relaxed", f0 + 40)
    for f in (f0 + 40, f0 + 70, f1):
        pe = RIG[n].PB["Pole_elbow.R"]; nm = "Pole_elbow.R"
        pe.location = RIG[n].rest(nm).to_3x3().inverted() @ (sh + V((-0.35, -0.15, -0.45)) - RIG[n].BN[nm].head_local); pe.keyframe_insert("location", frame=f, group=nm)
    drops_idle(f0, f1)
    cam_keys(s, [(0, V((-1.15, -0.62, 1.72)), V((0.12, -0.92, 1.45)), 26), (1, V((-1.05, -0.62, 1.70)), V((0.12, -0.9, 1.47)), 28)], fstop=8)
# ---------------------------------------------------------------- bathroom
CTK = "CrowdM5"
CT = (BX - 0.05, -0.78); IV = (BX + 0.62, -0.52)
def S09():     # wide from the door: Investigator and Caretaker beside the toilet, the damp stain on the wall
    s = "S09"; f0, f1 = F0[s], F1[s]
    drops_idle(f0, f1)
    idle(CTK, f0, f1, CT[0], CT[1], facing(*CT, IV[0], IV[1]) - 35, head=(4.0, 10.0), head2=(4.0, 18.0), ph=0.5)
    idle("Investigator", f0, f1, IV[0], IV[1], facing(*IV, CT[0], CT[1]) + 35, head=(0.0, -12.0), head2=(-6.0, 15.0), ph=1.2)
    cam_keys(s, [(0, V((BX + 0.05, -1.62, 1.62)), V((BX + 0.25, 0.4, 1.15)), 17), (1, V((BX + 0.12, -1.45, 1.58)), V((BX + 0.3, 0.5, 1.2)), 18)], fstop=11)
JOINT = V(sc["JOINT"])
def S10():     # Investigator turns and points at the leaking pipe joint; Caretaker looks
    s = "S10"; f0, f1 = F0[s], F1[s]
    drops_idle(f0, f1)
    idle(CTK, f0, f1, CT[0], CT[1], facing(*CT, IV[0], IV[1]) - 35, head=(6.0, 20.0), head2=(14.0, -12.0), ph=0.5)
    n = "Investigator"; x, y = IV; on_stage(n, f0, f1)
    yaw0 = facing(x, y, CT[0], CT[1]) + 35; yaw1 = facing(x, y, JOINT.x, JOINT.y) + 20
    H = HUM[n]
    for k, f in enumerate((f0, f0 + 30, f0 + 60, f1)):
        yaw = yaw0 + (yaw1 - yaw0) * min(1.0, k / 1.5)
        P = V((x, y, H.root_head.z - 0.01)); Rb = body_R(yaw)
        sh = bw(n, P, Rb, rest_head(n, "upperarm01.R")); dirv = (JOINT - sh).normalized()
        W0, d0, n0 = relaxed_hand(n, P, Rb, "R"); u = 0.0 if k == 0 else 1.0 if k >= 2 else 0.5
        W = W0.lerp(sh + dirv * 0.52, u); d = d0.lerp(dirv, u).normalized()
        stand(n, f, x, y, yaw, head=(-14.0, -12.0 * u), fingers=None,
              hands={"R": (W, d, V((0, 0, -1)), sh + V((0, 0, -0.45)) + Rz(yaw) @ V((-0.35, 0.25, 0)))})
        apply_pose(RIG[n].o, "R", "point" if u > 0.6 else "relaxed", f); apply_pose(RIG[n].o, "L", "relaxed", f)
    cam_keys(s, [(0, V((BX + 0.15, -1.42, 1.62)), V((BX + 0.15, 0.6, 1.4)), 17), (1, V((BX + 0.15, -1.36, 1.62)), V((BX + 0.18, 0.6, 1.45)), 18)], fstop=11)
DRAIN = V(sc["DRAIN"])
def S11():     # the floor drain overflows: a pool spreads from the grate
    s = "S11"; f0, f1 = F0[s], F1[s]
    drops_idle(f0, f1)
    bpy.ops.mesh.primitive_circle_add(vertices=48, radius=1.0, fill_type='NGON', location=DRAIN + V((0, 0, 0.0125)))
    pool = bpy.context.active_object; pool.name = "FX_DrainPool"
    mp_ = bpy.data.materials.new("M_Puddle"); mp_.use_nodes = True; nt = mp_.node_tree; nn_ = nt.nodes; ll_ = nt.links
    pr_ = nn_["Principled BSDF"]; pr_.inputs['Base Color'].default_value = (0.08, 0.09, 0.09, 1); pr_.inputs['Roughness'].default_value = 0.06
    pr_.inputs['Coat Weight'].default_value = 1.0
    tc_ = nn_.new('ShaderNodeTexCoord'); ln_ = nn_.new('ShaderNodeVectorMath'); ln_.operation = 'LENGTH'; ll_.new(tc_.outputs['Object'], ln_.inputs[0])
    nz_ = nn_.new('ShaderNodeTexNoise'); nz_.inputs['Scale'].default_value = 3.0; ll_.new(tc_.outputs['Object'], nz_.inputs['Vector'])
    ad_ = nn_.new('ShaderNodeMath'); ad_.operation = 'MULTIPLY_ADD'; ll_.new(nz_.outputs['Fac'], ad_.inputs[0]); ad_.inputs[1].default_value = 0.5; ad_.inputs[2].default_value = 0.55
    lt_ = nn_.new('ShaderNodeMath'); lt_.operation = 'LESS_THAN'; ll_.new(ln_.outputs['Value'], lt_.inputs[0]); ll_.new(ad_.outputs[0], lt_.inputs[1])
    ll_.new(lt_.outputs[0], pr_.inputs['Alpha'])
    pool.data.materials.append(mp_)
    pool.visible_shadow = False
    for f, r in ((f0, 0.14), (f0 + 40, 0.19), (f1, 0.24)):
        pool.scale = (max(r, 0.001), max(r * 0.85, 0.001), 1); pool.keyframe_insert("scale", frame=f)
    pool.location = DRAIN + V((0, 0, 0.0125)); pool.keyframe_insert("location", frame=f0)
    pool.location = DRAIN + V((0, 0, -5)); pool.keyframe_insert("location", frame=f0 - 1); pool.keyframe_insert("location", frame=f1 + 1)
    pool.location = DRAIN + V((0, 0, 0.0125)); pool.keyframe_insert("location", frame=f1)
    for fc in fcurves_of(pool):
        if fc.data_path == "location":
            for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
    pool.scale = (1, 1, 1); pool.keyframe_insert("scale", frame=1)
    # bubbles welling up through the grate
    for i, d in enumerate(DROPS[:4]):
        for k in range(0, f1 - f0, 6):
            f = f0 + k; ph = (k / 6 + i * 1.7)
            p = DRAIN + V((0.04 * math.cos(ph * 2.1 + i), 0.04 * math.sin(ph * 1.3 + i), 0.012 + 0.006 * abs(math.sin(ph))))
            key_drop(d, f, p, 0.9 + 0.3 * math.sin(ph))
        key_drop(d, f1, DPARK, 0.2)
    cam_keys(s, [(0, DRAIN + V((0.42, -0.62, 0.42)), DRAIN + V((0, 0.02, 0.0)), 35), (1, DRAIN + V((0.32, -0.48, 0.32)), DRAIN + V((0, 0.03, 0.0)), 38)], fstop=11)
def S12():     # the leaking joint: drops form under the coupling and run into the wall
    s = "S12"; f0, f1 = F0[s], F1[s]
    drops_idle(f0, f1)
    for i, (dx, g, fl) in enumerate(((0.0, 0, 40), (0.03, 50, 95), (-0.025, 100, 140))):
        if f0 + fl < f1: drop_cycle(DROPS[i], f0 + g, f0 + fl, f1, JOINT + V((dx, 0.02, -0.004)), 1.30, f0, f1)
    cam_keys(s, [(0, JOINT + V((-0.28, -0.85, 0.22)), JOINT + V((0, 0.05, -0.05)), 32), (1, JOINT + V((-0.16, -0.55, 0.12)), JOINT + V((0, 0.05, -0.08)), 36)], fstop=11)
# trickle down the damp streak: a thin water ribbon revealed top-down by a keyed value
def trickle():
    import bmesh
    me = bpy.data.meshes.new("Trickle"); bm = bmesh.new()
    top = JOINT.z - 0.01; N = 80; prev = None
    for i in range(N + 1):
        t = i / N; z = top - t * (top - 0.02)
        xo = 0.012 * math.sin(t * 23) + 0.02 * math.sin(t * 7.3)
        w = 0.010 + 0.012 * t
        a = bm.verts.new((JOINT.x + xo - w, 0, z)); b = bm.verts.new((JOINT.x + xo + w, 0, z))
        if prev: bm.faces.new((prev[0], prev[1], b, a))
        prev = (a, b)
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("FX_Trickle", me); sc.collection.objects.link(o)
    o.location = (0, sc["BATH"][3] - 0.006, 0)
    m = bpy.data.materials.new("M_Trickle"); m.use_nodes = True; nt = m.node_tree
    p = nt.nodes["Principled BSDF"]; p.inputs['Base Color'].default_value = (0.2, 0.24, 0.2, 1); p.inputs['Roughness'].default_value = 0.02
    p.inputs['Coat Weight'].default_value = 1.0
    tc = nt.nodes.new('ShaderNodeTexCoord'); sp = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Generated'], sp.inputs[0])
    val = nt.nodes.new('ShaderNodeValue'); val.name = "Reveal"
    gt = nt.nodes.new('ShaderNodeMath'); gt.operation = 'GREATER_THAN'; nt.links.new(sp.outputs['Z'], gt.inputs[0]); nt.links.new(val.outputs[0], gt.inputs[1])
    nt.links.new(gt.outputs[0], p.inputs['Alpha'])
    m.blend_method = 'HASHED' if hasattr(m, "blend_method") else None
    me.materials.append(m); o.visible_shadow = False
    return o, val
TRK, TRV = trickle()
def key_reveal(f, v): TRV.outputs[0].default_value = v; TRV.outputs[0].keyframe_insert("default_value", frame=f)
def S13():     # tilt down the wet streak while the trickle runs down
    s = "S13"; f0, f1 = F0[s], F1[s]
    drops_idle(f0, f1)
    key_reveal(f0, 0.97); key_reveal(f1, 0.30)
    J = JOINT
    cam_keys(s, [(0, J + V((-0.05, -0.95, 0.05)), J + V((0, 0.1, -0.12)), 30), (0.5, J + V((-0.08, -1.0, -0.45)), J + V((0, 0.1, -0.65)), 30),
                 (1, J + V((-0.1, -1.0, -0.95)), J + V((0, 0.1, -1.2)), 30)], fstop=11)
def S14():     # the trickle reaches the floor line and spreads; the wall is soaked
    s = "S14"; f0, f1 = F0[s], F1[s]
    drops_idle(f0, f1)
    key_reveal(f0, 0.30); key_reveal(f0 + 90, 0.0); key_reveal(f1, 0.0)
    b = V((JOINT.x, sc["BATH"][3], 0.0))
    cam_keys(s, [(0, b + V((0.35, -0.95, 0.55)), b + V((0, 0, 0.35)), 28), (1, b + V((0.25, -0.8, 0.40)), b + V((0, 0, 0.25)), 30)], fstop=11)
# ---------------------------------------------------------------- the investigator back at the statue
TROL = bpy.data.objects["PR_Trolley"]; TROL.rotation_mode = 'XYZ'
INV_P = (0.55, -3.35)
ANGRY = {"CrowdM1": (-0.9, -1.75), "CrowdW2": (-1.6, -2.2), "CrowdM2": (1.3, -2.0), "CrowdM6": (-0.2, -2.25), "CrowdM5": (1.9, -2.6),
         "CrowdM7": (0.35, -1.6), "CrowdW4": (-1.25, -1.55), "Woman": (0.9, -1.45), "CrowdM3": (-2.2, -2.6), "CrowdM4": (2.4, -1.9)}
def angry_crowd(f0, f1, pointers=()):
    for i, (n, (x, y)) in enumerate(ANGRY.items()):
        if n in pointers: continue
        yaw = facing(x, y, *INV_P)
        idle(n, f0, f1, x, y, yaw, head=(-4.0, 0.0), head2=(-2.0, 6.0 * math.sin(i)), every=24, ph=i)
        # slow disapproving head shake for some
        if i % 3 == 0:
            for k, f in enumerate(range(f0 + 10, f1 - 5, 16)):
                RIG[n].key_rot("head", f, [("X", 2.0), ("Z", 9.0 * (1 if k % 2 else -1))])
def trolley_at(f, p, yaw, tilt=0.0):
    TROL.location = p; TROL.rotation_euler = (R_(tilt), 0, R_(yaw))
    TROL.keyframe_insert("location", frame=f); TROL.keyframe_insert("rotation_euler", frame=f)
TB = sc["TROLLEY_BB"]
HANDLE_TOP = TB[5]
def S15():     # Investigator in front of the crowd at the cross, crowd behind frowning
    s = "S15"; f0, f1 = F0[s], F1[s]
    drops_idle(f0, f1)
    angry_crowd(f0, f1)
    n = "Investigator"; x, y = INV_P; yaw = 8.0
    idle(n, f0, f1, x, y, yaw, head=(-6.0, 0.0), head2=(-10.0, 12.0), ph=0.2)
    sd = Rz(yaw) @ V((1, 0, 0))
    for f in (f0, f1): trolley_at(f, V((x, y, 0)) + sd * -0.42 + Rz(yaw) @ V((0, -0.05, 0)), yaw + 90)
    cam_keys(s, [(0, V((x + 0.3, y - 2.4, 1.62)), V((x - 0.1, y + 1.0, 1.45)), 32), (1, V((x + 0.25, y - 2.1, 1.6)), V((x - 0.1, y + 1.0, 1.5)), 34)], fstop=8)
def S16():     # two men point at him; he lowers his head
    s = "S16"; f0, f1 = F0[s], F1[s]
    drops_idle(f0, f1)
    P_ = ("CrowdM7", "CrowdM2")
    angry_crowd(f0, f1, pointers=P_)
    for i, n in enumerate(P_):
        x, y = ANGRY[n]; yaw = facing(x, y, *INV_P); on_stage(n, f0, f1)
        H = HUM[n]; P = V((x, y, H.root_head.z - 0.01)); Rb = body_R(yaw)
        side = "R" if i == 0 else "L"
        sh = bw(n, P, Rb, rest_head(n, "upperarm01." + side))
        tgt = V((INV_P[0], INV_P[1], 1.5)); dirv = (tgt - sh).normalized()
        for k, f in enumerate((f0, f0 + 20 + 10 * i, f0 + 70, f1)):
            u = 0.0 if k == 0 else 1.0
            W0, d0, n0 = relaxed_hand(n, P, Rb, side)
            stand(n, f, x, y, yaw, head=(-6.0, 0.0), lean=-2.0 * u, fingers=None,
                  hands={side: (W0.lerp(sh + dirv * 0.50, u), d0.lerp(dirv, u).normalized(), V((0, 0, -1)),
                                sh + V((0, 0, -0.45)) + Rz(yaw) @ V((0.35 if side == "L" else -0.35, 0.2, 0)))})
            apply_pose(RIG[n].o, side, "point" if u else "relaxed", f); apply_pose(RIG[n].o, "L" if side == "R" else "R", "relaxed", f)
    n = "Investigator"; x, y = INV_P; yaw = 8.0
    idle(n, f0, f1, x, y, yaw, head=(-10.0, 10.0), head2=(-30.0, 0.0), every=30, ph=0.5)
    sd = Rz(yaw) @ V((1, 0, 0))
    for f in (f0, f1): trolley_at(f, V((x, y, 0)) + sd * -0.42 + Rz(yaw) @ V((0, -0.05, 0)), yaw + 90)
    cam_keys(s, [(0, V((x + 1.6, y - 1.2, 1.7)), V((-0.2, -1.8, 1.45)), 28), (1, V((x + 1.45, y - 1.05, 1.68)), V((-0.2, -1.8, 1.5)), 30)], fstop=8)
def S17():     # close-up: eyes down, a sigh; his left hand rests on the case handle
    s = "S17"; f0, f1 = F0[s], F1[s]
    drops_idle(f0, f1)
    angry_crowd(f0, f1)
    n = "Investigator"; x, y = INV_P; yaw = 8.0; on_stage(n, f0, f1)
    sd = Rz(yaw) @ V((1, 0, 0)); fw = Rz(yaw) @ V((0, -1, 0))
    tp = V((x, y, 0)) + sd * 0.40 + fw * 0.06
    for f in (f0, f1): trolley_at(f, tp, yaw + 90)
    top = tp + V((0, 0, HANDLE_TOP - 0.012))
    for k, f in enumerate((f0, f0 + 45, f0 + 85, f1)):
        stand(n, f, x, y, yaw, head=(-26.0 + 4 * math.sin(k), 6.0), flex=4.0 + 2.5 * (k % 2), fingers=None, hands={"L": None})
        place_hand(RIG[n].o, "L", f, top, V((0, 0, -1)), (fw * 0.3 + sd * -0.0 + fw).normalized(), skin=0.02)
        apply_pose(RIG[n].o, "L", "cup_hold", f); apply_pose(RIG[n].o, "R", "relaxed", f)
        pe = RIG[n].PB["Pole_elbow.L"]; nm = "Pole_elbow.L"
        pe.location = RIG[n].rest(nm).to_3x3().inverted() @ (V((x, y, 1.0)) + sd * 0.7 + fw * -0.3 - RIG[n].BN[nm].head_local); pe.keyframe_insert("location", frame=f, group=nm)
    face = V((x, y, rest_head(n, "head").z + 0.06))
    cam_keys(s, [(0, face + fw * 0.95 + sd * 0.25 + V((0, 0, -0.12)), face + V((0, 0, -0.18)), 45), (1, face + fw * 0.82 + sd * 0.2 + V((0, 0, -0.12)), face + V((0, 0, -0.2)), 48)], fstop=8)
def S18():     # he turns and walks away pulling the case (logo side to camera)
    s = "S18"; f0, f1 = F0[s], F1[s]
    drops_idle(f0, f1)
    angry_crowd(f0, f1)
    n = "Investigator"; on_stage(n, f0, f1); H = HUM[n]
    x0, y0 = INV_P; start = V((x0, y0, 0)); end = V((x0 - 3.2, y0 - 1.0, 0))
    yaw_w = facing(x0, y0, end.x, end.y)
    def path(f):
        u = max(0.0, min(1.0, (f - f0 - 20) / (f1 - f0 - 20))); return start.lerp(end, u)
    def yawf(f): return yaw_w
    stand(n, f0, x0, y0, yaw_w, head=(-12.0, 0.0), fingers="relaxed")
    H.walk(path, yawf, f0 + 20, f1, stride=0.62, lean=4.0)
    fw = Rz(yaw_w) @ V((0, -1, 0)); sd = Rz(yaw_w) @ V((1, 0, 0))
    TILT = 40.0; h = HANDLE_TOP
    for f in range(f0, f1 + 1, 2):
        p = path(f); Rb = body_R(yaw_w)
        P = V((p.x, p.y, H.root_head.z - 0.03))
        back = Rb @ V((0, 1, 0)); right = Rb @ V((-1, 0, 0))
        u = max(0.0, min(1.0, (f - f0) / 20.0)); th = R_(TILT) * smooth(u)
        base = V((p.x, p.y, 0)) + right * 0.36 + back * (0.22 + h * math.sin(R_(TILT)))
        top = base - back * (h * math.sin(th)) + V((0, 0, h * math.cos(th)))
        trolley_at(f, base, yaw_w, tilt=math.degrees(th))
        hands = {"R": (top + V((0, 0, 0.035)), (Rb @ V((0, 0.35, -1))).normalized(), right, P + Rb @ V((-0.5, 0.25, -0.1)))}
        sw = math.sin((f - f0) / 60.0 * 2 * math.pi * 0.9)
        W0, d0, n0 = relaxed_hand(n, P, Rb, "L", fwd=0.10 * sw, out=0.04); hands["L"] = (W0, d0, n0)
        key_hands(n, f, P, Rb, hands)
    apply_pose(RIG[n].o, "R", "wrap_grip", f0 + 20)
    cam_keys(s, [(0, V((x0 + 2.1, y0 - 1.0, 1.5)), V((x0 - 0.3, y0 - 0.4, 1.05)), 30), (1, V((x0 + 0.9, y0 - 1.2, 1.45)), V((x0 - 2.6, y0 - 1.0, 0.9)), 32)], fstop=8)

for s in ORDER:
    print("SHOT", s, F0[s], F1[s]); globals()[s]()
# props outside their shots: park
CUP_SHOTS = [("S07",)]
for f, loc in ((1, V((0, 0, -50))), (F0["S07"] - 1, V((0, 0, -50)))):
    pass
# cup: only visible in S07 (constraint influence 1 there, parked otherwise)
c_ = CUP.constraints.get("HoldCup")
for f, inf in ((1, 0.0), (F0["S07"] - 1, 0.0), (F0["S07"], 1.0), (F1["S07"], 1.0), (F1["S07"] + 1, 0.0)):
    c_.influence = inf; c_.keyframe_insert("influence", frame=f)
_cl = CUP.location.copy()
for f, loc in ((1, V((0, 0, -50))), (F0["S07"] - 1, V((0, 0, -50))), (F1["S07"], _cl), (F1["S07"] + 1, V((0, 0, -50)))):
    CUP.location = loc; CUP.keyframe_insert("location", frame=f)
# trolley parked except S15-S18
TROL.location = (0, 0, -60); TROL.keyframe_insert("location", frame=1); TROL.keyframe_insert("location", frame=F0["S15"] - 1)
TROL.keyframe_insert("location", frame=max(F1.values()) + 1)
key_reveal(1, 1.0); key_reveal(F0["S13"] - 1, 1.0)
# rigs: park off stage outside their blocks (object location, constant)
for n in CAST:
    o = RIG[n].o
    blocks = sorted(ACTIVE[n])
    o.location = PARK[n]; o.keyframe_insert("location", frame=1)
    for (a, b) in blocks:
        o.location = (0, 0, 0); o.keyframe_insert("location", frame=a)
        o.location = PARK[n]; o.keyframe_insert("location", frame=b + 1)
    # within a block the rig must be at the origin: drop park keys that fall inside a later block
for fc in fcurves_of(CUP) + fcurves_of(TROL):
    if fc.data_path in ("location", "rotation_euler") and fc.id_data is not None:
        pass
for fc in fcurves_of(CUP):
    for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
for n in CAST:
    for fc in fcurves_of(RIG[n].o):
        if fc.data_path == "location":
            for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
# hard cuts: every key at a block boundary gets flat handles (no overshoot from the jump to the next block)
BOUND = set()
for s in ORDER: BOUND.add(F0[s]); BOUND.add(F1[s])
ids = [o for o in bpy.data.objects if o.animation_data] + [cam_d] + [m for m in bpy.data.materials if m.node_tree and m.node_tree.animation_data]
for o in ids:
    src = o.node_tree if isinstance(o, bpy.types.Material) else o
    fcs = []
    ad = src.animation_data
    if ad and ad.action:
        for layer in ad.action.layers:
            for strip in layer.strips:
                for cb in strip.channelbags: fcs += list(cb.fcurves)
    for fc in fcs:
        for kp in fc.keyframe_points:
            fr = int(round(kp.co.x))
            if fr in BOUND:
                kp.handle_left_type = kp.handle_right_type = 'FREE'
                kp.handle_left = (kp.co.x - 1, kp.co.y); kp.handle_right = (kp.co.x + 1, kp.co.y)
            if fr in {F1[s] for s in ORDER} and (o is CAM or o is AIM or o is cam_d): kp.interpolation = 'CONSTANT'
        fc.update()
# markers for the shots (review)
for s in ORDER: sc.timeline_markers.new(s, frame=F0[s])
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("ANIM_OK", sc.frame_end)
