"""B32 KidHacker phase 2 (v002): the P1 clips cut to the client VO word frames (beat frame = 1 + round(s * 60)).
Every action keeps its P1 speed (u is measured against the P1 clip length) and is trimmed, never stretched.
blender -b /tmp/claude-0/kh/work/sets.blend --python 06_vo_build.py -- out.blend"""
import bpy, sys, math, json, random
from mathutils import Vector, Matrix, Quaternion, Euler
P = "/home/user/Muhammed/blender/pipeline/"; SD = "/home/user/Muhammed/blender/KidHacker_v001/scripts/"
W = "/tmp/claude-0/kh/work/"
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]
exec(open(P + "anim_lib.py").read())
exec(open(P + "hand_poses.py").read())
sc = bpy.context.scene; R_ = math.radians
random.seed(32)
def ground_z(x, y): return 0.0

# ------------------------------------------------------------------ shot table (seconds = reference beat x 1.3)
P1 = [("S01", 1.4), ("S02", 2.4), ("S03", 1.4), ("S04", 2.6), ("S05", 2.6), ("S06", 2.6), ("S07", 2.6), ("S08", 2.6), ("S09", 3.6),
      ("S10", 2.6), ("S11", 3.6), ("S12", 1.6), ("S13", 1.6), ("S14", 2.6), ("S15", 2.6), ("S16", 3.4), ("S17", 3.4), ("S18", 2.6),
      ("S19", 3.6), ("S20", 2.0), ("S21", 2.8), ("S22", 2.6), ("S23", 2.0), ("S24", 2.6)]
P1LEN = {k: int(round(d * 60)) - 1 for k, d in P1}
# VO word starts (s) from transcribe.py (B32_KidHacker_VO.words.json); each shot runs to the next one; end = last word + 0.5 s
VO = [("S01", 0.00, "She sat down at a library computer"), ("S03", 1.80, "that connected to the"),
      ("S04", 2.80, "internet through a phone line"), ("S05", 4.74, "Then she used it to automatically dial"),
      ("S06", 6.82, "hundreds of other computers"), ("S07", 8.32, "until one finally answered"), ("S08", 10.70, "Back then, if you had the password"),
      ("S09", 12.72, "you could sometimes access the files"), ("S10", 14.94, "So she randomly typed"), ("S11", 16.40, "oh, oh, oh, oh"),
      ("S12", 18.40, "To her surprise"), ("S13", 19.54, "it opened an FBI"), ("S14", 20.74, "database"),
      ("S16", 21.94, "But because the password was so easy"), ("S17", 24.26, "she assumed it was just some kind of computer game"),
      ("S18", 26.86, "For two weeks"), ("S19", 28.10, "she explored secret information"), ("S20", 29.58, "while the FBI searched"),
      ("S21", 30.86, "for the hacker"), ("S22", 32.06, "When agents finally traced it"), ("S23", 33.90, "they were shocked to discover"),
      ("S24", 35.02, "the hacker was only a child")]
VO_END = 36.74 + 0.5
def F(t): return 1 + round(t * 60)
WIN = {}
for i, (sid, t, w) in enumerate(VO):
    t1 = VO[i + 1][1] if i + 1 < len(VO) else VO_END
    WIN[sid] = (F(t), F(t1) - 1)
f = F(VO_END)
sc.frame_start, sc.frame_end = 1, f - 1
def has(sid): return sid in WIN
print("FRAMES", f - 1)

# ------------------------------------------------------------------ helpers
def mat(name, rgb, rough=0.5, metal=0.0):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True; Pn = m.node_tree.nodes["Principled BSDF"]
    Pn.inputs["Base Color"].default_value = (*rgb, 1); Pn.inputs["Roughness"].default_value = rough; Pn.inputs["Metallic"].default_value = metal
    return m

def emat(name, rgb, strength=1.0):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    e = nt.nodes.new("ShaderNodeEmission"); e.inputs[0].default_value = (*rgb, 1); e.inputs[1].default_value = strength
    o = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(e.outputs[0], o.inputs[0])
    return m

def vis(o, f, show):
    for ob in [o] + list(o.children_recursive):
        ob.hide_render = not show; ob.hide_viewport = not show
        ob.keyframe_insert("hide_render", frame=f); ob.keyframe_insert("hide_viewport", frame=f)

def show_only(o, ranges):
    """visible only inside the given (f0, f1) windows (constant keys, hide_viewport keyed with hide_render)"""
    vis(o, 0, False)
    for f0, f1 in ranges:
        vis(o, f0, True); vis(o, f1 + 1, False)

def const_all(o):
    ad = o.animation_data
    if not ad or not ad.action: return
    for fc in _fc(ad.action):
        if fc.data_path in ("hide_render", "hide_viewport"):
            for k in fc.keyframe_points: k.interpolation = 'CONSTANT'

def _fc(act):
    if hasattr(act, "fcurves") and len(getattr(act, "fcurves", [])): return list(act.fcurves)
    out = []
    for layer in getattr(act, "layers", []):
        for strip in layer.strips:
            for cb in getattr(strip, "channelbags", []): out += list(cb.fcurves)
    return out

def load_char(cid):
    with bpy.data.libraries.load(W + "chars.blend", link=False) as (fd, td):
        td.objects = [n for n in fd.objects if n == cid or n.startswith(cid + ".") or n.startswith(cid + "_")]
    c = bpy.data.collections.new("CH_" + cid); sc.collection.children.link(c)
    rig = None
    for o in td.objects:
        if not o: continue
        c.objects.link(o); o.hide_render = False; o.hide_viewport = False
        if o.type == 'ARMATURE' and o.name == cid: rig = o
    return rig

RIGS = {}; HUM = {}; RR = {}
def setup(cid):
    rig = load_char(cid)
    R = make_human_ctrl(rig); add_hand_limits(rig)
    for s in "LR":   # MPFB rest elbow ~46 deg: open the IK limit so arms can straighten (LESSONS 8)
        lo = rig.pose.bones["lowerarm01." + s]; lo.use_ik_limit_x = True; lo.ik_min_x = R_(-40); lo.ik_max_x = R_(125)
    H = Human(R); RIGS[cid] = rig; HUM[cid] = H; RR[cid] = R
    H.sh = {s: R.BN["upperarm01." + s].head_local.copy() for s in "LR"}
    return rig, R, H

def pole(cid, s, f, Wp):
    R = RR[cid]; n = "Pole_elbow." + s; pb = R.PB[n]
    pb.location = R.rest(n).to_3x3().inverted() @ (Vector(Wp) - R.BN[n].head_local); pb.keyframe_insert("location", frame=f, group=n)

def knee_pole(cid, s, f, Wp):
    R = RR[cid]; n = "Pole_knee." + s; pb = R.PB[n]
    pb.location = R.rest(n).to_3x3().inverted() @ (Vector(Wp) - R.BN[n].head_local); pb.keyframe_insert("location", frame=f, group=n)

def foot_at(cid, s, f, Wp, yaw=0.0, pitch=0.0):
    R = RR[cid]; H = HUM[cid]; a_ = H.ankle[s]
    M = Matrix.Translation(Vector(Wp)) @ Matrix.Rotation(R_(yaw), 4, 'Z') @ Matrix.Rotation(R_(pitch), 4, 'X') @ Matrix.Translation(-a_) @ R.rest("IK_foot." + s)
    R.key_world("IK_foot." + s, f, M)

def key_jaw(cid, f, open_deg):
    R = RR[cid]; R.key_rot("jaw", f, [("X", open_deg)])

def key_eyes(cid, f, pitch=0.0, yaw=0.0):
    R = RR[cid]
    for s in "LR": R.key_rot("eye." + s, f, [("X", pitch), ("Z", yaw)])

def bone_w(cid, n, tail=False):
    rig = RIGS[cid]; pb = rig.pose.bones[n]; return rig.matrix_world @ (pb.tail if tail else pb.head)

def head_pt(cid, f):
    sc.frame_set(f); bpy.context.view_layer.update()
    return bone_w(cid, "head").lerp(bone_w(cid, "head", True), 0.45)

def fingers(cid, s, f, pose="relaxed", amount=1.0):
    apply_pose(RIGS[cid], s, pose, f, amount)

def tip_to(cid, s, f, target, n_iter=3):
    """shift IK_hand.<s> at frame f so the index fingertip lands on target (world)"""
    rig = RIGS[cid]; R = RR[cid]
    for _ in range(n_iter):
        sc.frame_set(f); bpy.context.view_layer.update()
        tip = rig.matrix_world @ rig.pose.bones["finger2-3." + s].tail
        d = Vector(target) - tip
        pb = R.PB["IK_hand." + s]; Mx = pb.matrix.copy(); Mx = Matrix.Translation(d) @ Mx
        R.key_world("IK_hand." + s, f, Mx)

CAMS = []
def cam_shot(name, sid, keys, lens=35, fstop=8.0, track=None):
    """keys: [(u in 0..1 of the shot window, loc, target)]; level horizon (track quat with world up)"""
    f0, f1 = WIN[sid]
    c = bpy.data.objects.new(name, bpy.data.cameras.new(name)); sc.collection.objects.link(c)
    c.data.lens = lens; c.data.clip_start = 0.02; c.data.dof.use_dof = True; c.data.dof.aperture_fstop = fstop
    c.data.sensor_fit = 'AUTO'
    for u, loc, tgt in keys:
        fr = f0 + round(u * (f1 - f0))
        c.location = loc; d = Vector(tgt) - Vector(loc)
        c.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler('XYZ', c.rotation_euler)
        c.keyframe_insert("location", frame=fr); c.keyframe_insert("rotation_euler", frame=fr)
        c.data.dof.focus_distance = d.length; c.data.dof.keyframe_insert("focus_distance", frame=fr)
    m = sc.timeline_markers.new(sid, frame=f0); m.camera = c
    CAMS.append((sid, f0, f1, c.name))
    # catchlight: tiny camera-side point light (eyes read)
    L = bpy.data.lights.new("Catch_" + name, 'POINT'); L.energy = 0.12; L.shadow_soft_size = 0.02
    lo = bpy.data.objects.new("Catch_" + name, L); sc.collection.objects.link(lo); lo.parent = c; lo.location = (0.04, 0.05, 0)
    show_only(lo, [(f0, f1)])
    return c

def U(sid, u):
    f0, f1 = WIN[sid]; return f0 + round(u * (f1 - f0))

# chair seat height (ray down, before any character exists)
dg = bpy.context.evaluated_depsgraph_get()
hit = sc.ray_cast(dg, Vector((0.0, 0.08, 2.0)), Vector((0, 0, -1)))
SEAT = hit[1].z if hit[0] else 0.47
print("SEAT", SEAT, hit[4].name if hit[0] else None)
for nm, xy in (("SEAT_OFF", (40.0, 0.08)), ("SEAT_INT", (80.0 - 0.62, 0.0))):
    h_ = sc.ray_cast(dg, Vector((xy[0], xy[1], 2.0)), Vector((0, 0, -1))); print(nm, h_[1].z if h_[0] else None, h_[4].name if h_[0] else None)
# ------------------------------------------------------------------ characters
KID, Rk, Hk = setup("Kid")
AGB, Rb, Hb = setup("AgentB")
AGC, Rc, Hc = setup("AgentC")
for r in (KID, AGB, AGC): r.location = (0, 0, 0)

# ------------------------------------------------------------------ library geometry refs
DESK_TOP = 0.7191; KB_TOP = 0.7655; KB_Y = -0.40
MS = bpy.data.objects["Mouse"]
GX = -0.04   # girl x (keyboard centre)

# ------------------------------------------------------------------ girl at the library computer
def kid_seat(f, lean=0.0, head=(0.0, 0.0), twist=0.0, back=0.0, yaw=0.0):
    """seated, facing -Y. lean = forward flex (deg) of the hips; back = hip slide back (m)"""
    hip = Vector((GX, -0.09 + back, SEAT + 0.11))
    Hk.key_root(f, hip, yaw=yaw, flex=-lean)
    Hk.key_spine(f, flex=-lean * 0.6, twist=twist, head=head)
    for s in "LR":
        sx = 1 if s == "L" else -1
        foot_at("Kid", s, f, Vector((GX + sx * 0.10, -0.24, 0.07 + Hk.ankle[s].z * 0.0 + 0.05)), yaw=0, pitch=-10)
        knee_pole("Kid", s, f, Vector((GX + sx * 0.12, -0.9, 0.55)))

def kid_hands(f, mode="keys", bob=0.0, side_bob=1):
    """hands: keys (both on the keyboard), mouse (R on mouse, L on keys), lap, desk (forearms resting on the desk edge)"""
    for s in "LR":
        sx = 1 if s == "L" else -1
        if mode == "keysL" and s == "R": continue
        if mode in ("keys", "keysL") or (mode == "mouse" and s == "L"):
            dz = bob if (s == "L") == (side_bob > 0) else 0.0
            place_hand(KID, s, f, (GX + sx * 0.085, KB_Y + 0.07, KB_TOP + 0.048 + dz), (0, 0, -1), (-sx * 0.15, -1, -0.25))
            fingers("Kid", s, f, "relaxed")
            pole("Kid", s, f, (GX + sx * 0.32, 0.25, 0.45))
        elif mode == "mouse" and s == "R":
            place_hand(KID, s, f, (MS.location.x + 0.005, MS.location.y + 0.02, MS.location.z + 0.062 + bob * 0.3), (0, 0, -1), (0.1, -1, -0.15))
            fingers("Kid", s, f, "relaxed")   # v002: cup_hold curled the ring finger into the mouse shell
            pole("Kid", s, f, (GX + sx * 0.5, 0.2, 0.55))
        elif mode == "lap":
            place_hand(KID, s, f, (GX + sx * 0.08, -0.22, SEAT + 0.19), (0, 0, -1), (-sx * 0.25, -1, -0.2))   # on the thighs, in front of the belly
            fingers("Kid", s, f, "relaxed")
            pole("Kid", s, f, (GX + sx * 0.32, 0.15, 0.45))
        elif mode == "desk":
            place_hand(KID, s, f, (GX + sx * 0.36, -0.25, DESK_TOP + 0.042), (0, 0, -1), (-sx * 0.45, -1, 0))   # beside the keyboard, palm flat
            fingers("Kid", s, f, "flat_palm")
            pole("Kid", s, f, (GX + sx * 0.3, 0.3, 0.45))

def kid_block(sid, mode, lean_fn, head_fn, step=12, bob=0.0, twist_fn=None, back_fn=None, yaw_fn=None):
    """key the seated girl for the whole shot window"""
    f0, f1 = WIN[sid]
    fr = list(range(f0, f1, step)) + [f1]
    for i, f in enumerate(fr):
        u = (f - f0) / max(1, P1LEN[sid])   # P1 speed: trimmed, never stretched
        kid_seat(f, lean_fn(u), head_fn(u), twist_fn(u) if twist_fn else 0.0, back_fn(u) if back_fn else 0.0, yaw_fn(u) if yaw_fn else 0.0)
        kid_hands(f, mode(u) if callable(mode) else mode, bob=(bob if i % 2 else 0.0), side_bob=1 if (i // 2) % 2 else -1)
    key_jaw("Kid", f0, 0.0); key_jaw("Kid", f1, 0.0)
    key_eyes("Kid", f0); key_eyes("Kid", f1)

def FR(f0, f1, step):
    """key frames of a shot window, always including its last frame (no drift into the next shot)"""
    return sorted(set(list(range(f0, f1 + 1, step)) + [f1]))

HEADSIGN = 1    # S24 head turn toward the agents (camera side)

def breath(u, amp=1.0, per=1.4): return amp * math.sin(2 * math.pi * u * per)

# ------------------------------------------------------------------ screen UI (flat emissive shapes, no text)
SCR = bpy.data.objects["Screen_Lib"]; SCRO = bpy.data.objects["Screen_Off"]
def rect(parent, name, u, v, w, h, rgb, layer=1, strength=1.0):
    bpy.ops.mesh.primitive_plane_add(size=1); o = bpy.context.object; o.name = name
    o.scale = (w, h, 1); bpy.ops.object.transform_apply(scale=True)
    for cc in o.users_collection: cc.objects.unlink(o)
    parent.users_collection[0].objects.link(o)
    o.parent = parent; o.location = (u, v, 0.0015 * layer)
    o.data.materials.append(emat("UI_%02x%02x%02x_%d" % (int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255), int(strength * 10)), rgb, strength))
    return o

def disc(parent, name, u, v, r, rgb, layer=1, strength=1.0, verts=32):
    bpy.ops.mesh.primitive_circle_add(vertices=verts, radius=r, fill_type='NGON'); o = bpy.context.object; o.name = name
    for cc in o.users_collection: cc.objects.unlink(o)
    parent.users_collection[0].objects.link(o)
    o.parent = parent; o.location = (u, v, 0.0015 * layer)
    o.data.materials.append(emat("UI_%02x%02x%02x_%d" % (int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255), int(strength * 10)), rgb, strength))
    return o

def state(parent, name):
    e = bpy.data.objects.new(name, None); parent.users_collection[0].objects.link(e); e.parent = parent
    return e

SW, SH = 1.50, 1.14     # usable screen size (model units)
TEAL = (0.05, 0.45, 0.5); GREY = (0.78, 0.8, 0.82); BLUE = (0.05, 0.15, 0.6); WHITE = (0.95, 0.95, 0.95)
def window(st, name, u, v, w, h, body=GREY, bar=BLUE):
    rect(st, name + "_body", u, v, w, h, body, 2)
    rect(st, name + "_bar", u, v + h / 2 - 0.05, w, 0.1, bar, 3)
    rect(st, name + "_x", u + w / 2 - 0.07, v + h / 2 - 0.05, 0.07, 0.07, (0.8, 0.8, 0.8), 4)

def pc_icon(st, name, u, v, s=1.0, layer=4):
    rect(st, name + "_m", u, v + 0.03 * s, 0.16 * s, 0.13 * s, (0.85, 0.85, 0.8), layer)
    rect(st, name + "_s", u, v + 0.035 * s, 0.12 * s, 0.09 * s, (0.15, 0.55, 0.85), layer + 1)
    rect(st, name + "_b", u, v - 0.06 * s, 0.2 * s, 0.04 * s, (0.85, 0.85, 0.8), layer)

ST = {}
def build_states():
    # desktop
    s = state(SCR, "UI_Desk"); ST["desk"] = s
    rect(s, "bg", 0, 0, SW, SH, TEAL, 1)
    for i in range(4):
        rect(s, "ic%d" % i, -0.68, 0.48 - i * 0.24, 0.13, 0.11, [(0.95, 0.85, 0.3), (0.9, 0.9, 0.9), (0.4, 0.8, 0.95), (0.95, 0.55, 0.3)][i], 2)
        rect(s, "il%d" % i, -0.68, 0.40 - i * 0.24, 0.13, 0.025, (0.85, 0.95, 0.95), 2)
    rect(s, "task", 0, -SH / 2 + 0.04, SW, 0.08, (0.75, 0.76, 0.78), 2)
    rect(s, "start", -SW / 2 + 0.1, -SH / 2 + 0.04, 0.16, 0.06, (0.6, 0.62, 0.65), 3)
    # dialler: two PCs and lighting dots between them, attempt rows filling a list, progress bar
    s = state(SCR, "UI_Dial"); ST["dial"] = s
    rect(s, "bg", 0, 0, SW, SH, TEAL, 1)
    window(s, "w", 0, 0.02, 1.3, 1.08)
    rect(s, "band", 0, 0.30, 1.22, 0.28, (0.55, 0.85, 0.45), 3)
    pc_icon(s, "pcA", -0.38, 0.30, 1.1); pc_icon(s, "pcB", 0.38, 0.30, 1.1)
    for i in range(6):
        d = disc(s, "dot%d" % i, -0.2 + i * 0.08, 0.30, 0.018, (0.1, 0.25, 0.1), 5)
        d2 = disc(s, "doton%d" % i, -0.2 + i * 0.08, 0.30, 0.022, (1.0, 0.95, 0.4), 6, 2.0)
    rect(s, "list", 0, -0.18, 1.18, 0.5, WHITE, 3)
    for i in range(7):
        rect(s, "row%d" % i, -0.55 + 0.5 * (0.35 + 0.5 * random.random()) / 2, 0.03 - i * 0.065, 0.5 * (0.35 + 0.5 * random.random()), 0.03, (0.3, 0.32, 0.36), 4)
    rect(s, "pbar_bg", 0, -0.48, 1.0, 0.05, (0.6, 0.62, 0.64), 3)
    pb = rect(s, "pbar", -0.5, -0.48, 1.0, 0.05, (0.1, 0.3, 0.85), 4)
    pb.data.transform(Matrix.Translation((0.5, 0, 0)))
    # login prompt (answered): green check badge, two fields, 4 password dots
    s = state(SCR, "UI_Login"); ST["login"] = s
    rect(s, "bg", 0, 0, SW, SH, TEAL, 1)
    window(s, "w", 0, 0.0, 1.2, 0.86)
    disc(s, "ok", -0.38, 0.12, 0.12, (0.15, 0.75, 0.3), 3, 1.2)
    rect(s, "ok_t1", -0.40, 0.11, 0.08, 0.025, WHITE, 4).rotation_euler = (0, 0, R_(-45))
    rect(s, "ok_t2", -0.35, 0.13, 0.14, 0.025, WHITE, 4).rotation_euler = (0, 0, R_(50))
    rect(s, "f1", 0.18, 0.18, 0.62, 0.09, WHITE, 3); rect(s, "f2", 0.18, 0.0, 0.62, 0.09, WHITE, 3)
    rect(s, "f1v", -0.02, 0.18, 0.18, 0.035, (0.3, 0.32, 0.36), 4)
    for i in range(4): disc(s, "pw%d" % i, -0.05 + i * 0.07, 0.0, 0.022, (0.05, 0.05, 0.08), 4)
    rect(s, "btn", 0.3, -0.22, 0.26, 0.09, (0.7, 0.72, 0.75), 3)
    rect(s, "cur", -0.11, 0.0, 0.012, 0.06, (0.05, 0.05, 0.08), 5)
    # database: dark window, gold seal (generic star), rows streaming in
    s = state(SCR, "UI_DB"); ST["db"] = s
    rect(s, "bg", 0, 0, SW, SH, (0.02, 0.04, 0.1), 1)
    rect(s, "head", 0, 0.5, SW, 0.18, (0.08, 0.16, 0.38), 2)
    disc(s, "seal", -0.62, 0.5, 0.075, (0.9, 0.72, 0.2), 3, 1.2); disc(s, "seal2", -0.62, 0.5, 0.055, (0.08, 0.16, 0.38), 4)
    disc(s, "star", -0.62, 0.5, 0.04, (0.9, 0.72, 0.2), 5, 1.2, verts=5)
    rect(s, "hbar", 0.1, 0.5, 0.9, 0.04, (0.6, 0.7, 0.9), 3)
    for i in range(12):
        y = 0.32 - i * 0.07
        rect(s, "dr%da" % i, -0.6, y, 0.22, 0.03, (0.3, 0.9, 0.5), 3)
        ww = 0.3 + 0.6 * random.random()
        rect(s, "dr%db" % i, -0.42 + ww / 2, y, ww, 0.03, (0.7, 0.75, 0.8), 3)
    # "game": bright window with bouncing coloured tiles
    s = state(SCR, "UI_Game"); ST["game"] = s
    rect(s, "bg", 0, 0, SW, SH, (0.15, 0.2, 0.6), 1)
    window(s, "w", 0, 0.0, 1.4, 1.1, body=(0.95, 0.95, 0.98))
    cols = [(0.95, 0.3, 0.3), (0.95, 0.75, 0.2), (0.3, 0.8, 0.4), (0.3, 0.6, 0.95), (0.8, 0.4, 0.9), (0.95, 0.55, 0.2)]
    for i in range(12):
        rect(s, "tile%d" % i, -0.5 + (i % 4) * 0.33, 0.25 - (i // 4) * 0.3, 0.22, 0.2, cols[i % 6], 3)
    # documents: white page, grey text lines, black redaction bars stamping in
    s = state(SCR, "UI_Doc"); ST["doc"] = s
    rect(s, "bg", 0, 0, SW, SH, (0.3, 0.32, 0.36), 1)
    rect(s, "page", 0, 0, 1.05, 1.2, (0.97, 0.96, 0.92), 2)
    disc(s, "stamp", 0.33, 0.45, 0.07, (0.85, 0.15, 0.15), 3, 1.0)
    for i in range(14):
        y = 0.42 - i * 0.065; ww = 0.55 + 0.3 * random.random()
        rect(s, "tl%d" % i, -0.42 + ww / 2, y, ww, 0.022, (0.45, 0.45, 0.48), 3)
        if i % 3 == 1:
            rx = random.random() * 0.4
            rect(s, "red%d" % i, -0.35 + rx + 0.12, y, 0.26, 0.045, (0.02, 0.02, 0.02), 4)
    # banned: red screen with a white padlock
    s = state(SCR, "UI_Red"); ST["red"] = s
    rect(s, "bg", 0, 0, SW, SH, (0.85, 0.05, 0.04), 1, 1.3)
    lk = state(s, "lock"); lk.location = (0, -0.05, 0.003)
    rect(lk, "body", 0, -0.05, 0.42, 0.34, WHITE, 2, 1.3)
    rect(lk, "hole", 0, -0.05, 0.05, 0.12, (0.85, 0.05, 0.04), 3, 1.3)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.13, minor_radius=0.03, major_segments=32, minor_segments=8)
    t = bpy.context.object; t.name = "UI_shackle"
    bm_ = t.data; import bmesh as _bm; b = _bm.new(); b.from_mesh(bm_); _bm.ops.delete(b, geom=[v for v in b.verts if v.co.y < -0.01], context='VERTS'); b.to_mesh(bm_); b.free()
    t.scale = (1, 1, 0.1)
    for cc in t.users_collection: cc.objects.unlink(t)
    SCR.users_collection[0].objects.link(t); t.parent = lk; t.location = (0, 0.12, 0.002); t.data.materials.append(emat("UI_ffffff_13", WHITE, 1.3))
    # office monitor: map with grid + blinking red dot
    s = state(SCRO, "UI_Map"); ST["map"] = s
    rect(s, "bg", 0, 0, SW, SH, (0.02, 0.08, 0.2), 1)
    for i in range(9): rect(s, "gv%d" % i, -0.72 + i * 0.18, 0, 0.006, SH, (0.1, 0.3, 0.5), 2)
    for i in range(7): rect(s, "gh%d" % i, 0, -0.54 + i * 0.18, SW, 0.006, (0.1, 0.3, 0.5), 2)
    for i in range(14):
        disc(s, "land%d" % i, random.uniform(-0.6, 0.6), random.uniform(-0.4, 0.4), random.uniform(0.06, 0.16), (0.12, 0.45, 0.3), 3)
    disc(s, "dot", 0.12, 0.05, 0.035, (1.0, 0.1, 0.1), 5, 2.0)
    disc(s, "ring", 0.12, 0.05, 0.07, (1.0, 0.3, 0.3), 4, 1.0)
build_states()
for k, s in ST.items(): vis(s, 0, False)

def screen_on(key, ranges):
    for f0, f1 in ranges:
        vis(ST[key], f0, True); vis(ST[key], f1 + 1, False)

def ui(key, name):
    return bpy.data.objects[name] if name in bpy.data.objects else next(o for o in ST[key].children_recursive if o.name.startswith(name))

# logo on the CRT bezel, below the glass (dark logo on beige plastic)
PCR = bpy.data.objects["PC_Lib"]
mon = bpy.data.objects["PCL_Object_6"]
dg = bpy.context.evaluated_depsgraph_get()
origin = PCR.matrix_world @ Vector((2.0, 0.0, 0.50)); dirw = (PCR.matrix_world.to_3x3() @ Vector((-1, 0, 0))).normalized()
hitp = sc.ray_cast(dg, origin, dirw)
print("LOGO_HIT", hitp[0], hitp[1], hitp[4].name if hitp[0] else None)
def logo_decal(name, parent, loc_world, normal, up, width, dark=True):
    img = bpy.data.images.load("/home/user/Muhammed/blender/assets/brand/" + ("DaKrasFilms_logo_dark.png" if dark else "DaKrasFilms_logo_white.png"), check_existing=True)
    m = bpy.data.materials.new(name + "_mat"); m.use_nodes = True; nt = m.node_tree; Pn = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = img
    nt.links.new(t.outputs["Color"], Pn.inputs["Base Color"]); nt.links.new(t.outputs["Alpha"], Pn.inputs["Alpha"]); Pn.inputs["Roughness"].default_value = 0.5
    h = width * 414 / 967
    bpy.ops.mesh.primitive_plane_add(size=1); o = bpy.context.object; o.name = name
    o.scale = (width, h, 1); bpy.ops.object.transform_apply(scale=True); o.data.materials.append(m)
    n = Vector(normal).normalized(); u_ = Vector(up).normalized(); x = u_.cross(n)
    o.matrix_world = Matrix.Translation(Vector(loc_world)) @ Matrix((x, u_, n)).transposed().to_4x4()
    mw = o.matrix_world.copy(); o.parent = parent; o.matrix_world = mw
    return o
if hitp[0]:
    LOGO = logo_decal("Logo_CRT", PCR, hitp[1] + hitp[2] * 0.003, hitp[2], (0, 0, 1), 0.10, dark=True)

# ================================================================== SHOTS
GF = Vector((GX, -0.02, SEAT + 0.68))   # approx girl face (refined per shot from the head bone)

def kid_lib_shots():
    # S01 she logs on: medium 3/4 from her left-front, hand on the mouse, slow push-in
    kid_block("S01", "mouse", lambda u: 8, lambda u: (8 + breath(u, 1), 0), bob=0.004)
    hf = head_pt("Kid", WIN["S01"][0])
    cam_shot("Cam_S01", "S01", [(0, (0.72, -0.44, 1.22), (GX - 0.05, -0.05, 0.96)), (1, (0.64, -0.40, 1.20), (GX - 0.05, -0.03, 0.98))], lens=28)
    screen_on("desk", [WIN["S01"]])
    if has("S02"):
        # S02 the library computer: face lit by the screen, slow orbit, she looks across the screen
        kid_block("S02", "mouse", lambda u: 10, lambda u: (10 + breath(u, 1.2), -6 + 12 * u), bob=0.004)
        hf = head_pt("Kid", WIN["S02"][0])
        cam_shot("Cam_S02", "S02", [(0, hf + Vector((0.26, -0.44, 0.03)), hf + Vector((0, 0, -0.04))), (1, hf + Vector((0.10, -0.48, 0.04)), hf + Vector((0, 0, -0.04)))], lens=50)
    # S03 which connected: the back of the tower, cable leaving it; camera slides along the cable toward the panel
    kid_block("S03", "keys", lambda u: 8, lambda u: (12, 0), bob=0.006)
    cam_shot("Cam_S03", "S03", [(0, (0.56, -0.70, 1.10), (0.49, -1.08, 0.90)), (1, (0.55, -0.78, 1.06), (0.49, -1.09, 0.91))], lens=35, fstop=10)   # close on cable + jack, tower face edge-on
    # S04 to the internet via a phone line: wall jack close-up, push in on the plug
    kid_block("S04", "keys", lambda u: 8, lambda u: (12, 0), bob=0.006)
    J = Vector((0.48, -1.098, 0.919))
    cam_shot("Cam_S04", "S04", [(0, J + Vector((0.08, 0.42, 0.10)), J + Vector((0, 0, 0.0))), (1, J + Vector((0.04, 0.24, 0.05)), J + Vector((0, 0, 0.01)))], lens=40, fstop=11)
    # S05-S07 screen: dialler; camera close on the CRT face, slow drift (logo on the bezel in frame)
    for sid in ("S05", "S06", "S07"):
        kid_block(sid, "keys", lambda u: 9, lambda u: (12, 0), bob=0.006)
    sp = PCR.matrix_world @ Vector((0.43, 0.0, 1.1))   # screen centre (lower-ish, keeps the bezel logo in frame)
    nrm = (PCR.matrix_world.to_3x3() @ Vector((1, 0, 0))).normalized()
    cam_shot("Cam_S05", "S05", [(0, sp + nrm * 0.40 + Vector((0.04, 0, 0.03)), sp + Vector((0, 0, -0.01))), (1, sp + nrm * 0.36 + Vector((0.01, 0, 0.02)), sp + Vector((0, 0, -0.01)))], lens=22, fstop=9)
    cam_shot("Cam_S06", "S06", [(0, sp + nrm * 0.38 + Vector((-0.04, 0, 0.04)), sp), (1, sp + nrm * 0.36 + Vector((-0.01, 0, 0.03)), sp)], lens=22, fstop=9)
    cam_shot("Cam_S07", "S07", [(0, sp + nrm * 0.42 + Vector((0.02, 0, 0.02)), sp), (1, sp + nrm * 0.36 + Vector((0.0, 0, 0.02)), sp)], lens=22, fstop=9)
    screen_on("dial", [(WIN["S03"][0], WIN["S06"][1])])
    screen_on("login", [(WIN["S07"][0], WIN["S13"][0] + 7)])
    # dial animation: dots light in sequence, rows appear, progress bar grows (S05..S06)
    f0, f1 = WIN["S05"][0], WIN["S06"][1]
    for i in range(6):
        o = ui("dial", "UI_Dial") if False else next(x for x in ST["dial"].children if x.name.startswith("doton%d" % i))
        vis(o, f0, False)
        for k in range(0, (f1 - f0) // 60 + 1):
            fa = f0 + k * 60 + i * 8
            if fa < f1: vis(o, fa, True); vis(o, min(f1, fa + 8), False)
    rows = sorted([x for x in ST["dial"].children if x.name.startswith("row")], key=lambda x: x.name)
    for i, o in enumerate(rows):
        vis(o, f0, False); vis(o, f0 + 20 + i * 38, True)
    pbo = next(x for x in ST["dial"].children if x.name.startswith("pbar") and not x.name.startswith("pbar_bg"))
    pbo.scale = (0.02, 1, 1); pbo.keyframe_insert("scale", frame=f0); pbo.scale = (0.95, 1, 1); pbo.keyframe_insert("scale", frame=f1)
    # S08 now back then...: she sits back, head tilts, looks up thinking (hands drop to the desk edge)
    kid_block("S08", "lap", lambda u: 2 - 4 * u, lambda u: (-6 - 8 * u + breath(u, 1), 10 * u), back_fn=lambda u: 0.02 * u, twist_fn=lambda u: 4 * u)
    hf = head_pt("Kid", WIN["S08"][0]); sp = PCR.matrix_world @ Vector((0.43, 0.0, 1.1))
    cam_shot("Cam_S08", "S08", [(0, hf + Vector((0.42, 0.55, 0.16)), sp + Vector((0, 0, -0.02))), (1, hf + Vector((0.36, 0.48, 0.13)), sp + Vector((0, 0, -0.02)))], lens=30)   # v002d: 3/4-back OTS onto the glowing monitor
    # S09 you could access other people's files: the idea - she leans in fast, head up, eyes bright
    kid_block("S09", lambda u: "desk" if u < 0.3 else "keys", lambda u: 2 + 12 * min(1, u / 0.3), lambda u: (-8 + 22 * min(1, u / 0.3) + breath(u, 1), 6 - 6 * min(1, u / 0.3)), bob=0.006)
    hf = head_pt("Kid", WIN["S09"][1])
    cam_shot("Cam_S09", "S09", [(0, hf + Vector((1.40, -0.30, -0.02)), hf + Vector((0, -0.30, -0.22))), (1, hf + Vector((1.32, -0.36, -0.03)), hf + Vector((0, -0.30, -0.22)))], lens=24)   # v002d: side medium, face <12% of width
    # S10 so she typed in: over-the-shoulder on the login box, password dots appear (S10..S11)
    kid_block("S10", "keys", lambda u: 12, lambda u: (16, 0), bob=0.008)
    cam_shot("Cam_S10", "S10", [(0, (GX + 0.32, 0.22, 1.20), sp + Vector((0, 0, 0.04))), (1, (GX + 0.26, 0.02, 1.12), sp + Vector((0, 0, 0.04)))], lens=35, fstop=8)
    # S11 0-0-0-0: macro on the keyboard, right index finger presses one key four times (arm runs off frame to the shoulder)
    f0, f1 = WIN["S11"]
    _kb = bpy.data.objects["PCL_Object_13"]; _inv = _kb.matrix_world.inverted()
    _ok, _loc, _n, _i = _kb.ray_cast(_inv @ Vector((GX - 0.075, -0.34, 1.5)), (_inv.to_3x3() @ Vector((0, 0, -1))).normalized())
    KEY = Vector((GX - 0.075, -0.34, ((_kb.matrix_world @ _loc).z if _ok else KB_TOP - 0.01) + 0.002)); print("KEYHIT", _ok, KEY)
    kid_block("S11", "keysL", lambda u: 14, lambda u: (18, 0))
    presses = [F(16.90), F(17.00), F(17.26), F(17.56)]
    fr = sorted(set([f0, f1, presses[0] - 12] + [p + d for p in presses for d in (-3, 0, 3)]))
    for fx in fr:
        fx = max(f0, min(f1, fx))
        down = any(fx == p for p in presses)
        kid_seat(fx, 14, (18, 0))
        place_hand(KID, "R", fx, (KEY.x - 0.02, KEY.y + 0.08, KEY.z + 0.07), (0, 0, -1), (0.05, -1, -0.5))
        fingers("Kid", "R", fx, "point")
        pole("Kid", "R", fx, (GX - 0.45, 0.2, 0.55))
        tip_to("Kid", "R", fx, KEY + Vector((0, 0, 0.005 if down else 0.018)))
        sc.frame_set(fx); print("TIP", fx, tuple(round(x, 3) for x in KID.matrix_world @ KID.pose.bones["finger2-3.R"].tail), tuple(round(x, 3) for x in KEY))
    pw = sorted([x for x in ST["login"].children if x.name.startswith("pw")], key=lambda x: x.name)
    cur = next(x for x in ST["login"].children if x.name.startswith("cur"))
    for o in pw: vis(o, WIN["S07"][0], False)
    for i, (o, p) in enumerate(zip(pw, presses)):
        vis(o, p, True)
    cam_shot("Cam_S11", "S11", [(0, KEY + Vector((-0.30, 0.12, 0.16)), KEY + Vector((0.0, 0.0, 0.02))), (1, KEY + Vector((-0.24, 0.06, 0.12)), KEY + Vector((0.0, 0.0, 0.02)))], lens=40, fstop=11)
    # S12 as a guess: 3/4 profile, she waits, leaning in a little
    kid_block("S12", "keys", lambda u: 12 + 3 * u, lambda u: (14, 0))
    hf = head_pt("Kid", WIN["S12"][0])
    cam_shot("Cam_S12", "S12", [(0, hf + Vector((0.70, -0.45, 0.02)), hf + Vector((0, 0, -0.06))), (1, hf + Vector((0.62, -0.50, 0.02)), hf + Vector((0, 0, -0.06)))], lens=45)
    # S13 but to her surprise: screen side angle (girl beyond the CRT), screen flips to the database
    kid_block("S13", "keys", lambda u: 14 - 10 * min(1, u / 0.4), lambda u: (14 - 6 * min(1, u / 0.4), 0))
    cam_shot("Cam_S13", "S13", [(0, (-0.78, -0.22, 1.08), (0.0, -0.78, 0.95)), (1, (-0.70, -0.30, 1.06), (0.0, -0.78, 0.95))], lens=28)
    screen_on("db", [(WIN["S13"][0] + 8, WIN["S14"][1])])
    # S14-S15 it connected / FBI database: screen close-up, rows stream in
    kid_block("S14", "keys", lambda u: 8, lambda u: (12, 0))
    cam_shot("Cam_S14", "S14", [(0, sp + nrm * 0.44 + Vector((-0.03, 0, 0.03)), sp), (1, sp + nrm * 0.37 + Vector((-0.01, 0, 0.03)), sp)], lens=22, fstop=9)
    if False: cam_shot("Cam_S15", "S15", [(0, sp + nrm * 0.38 + Vector((0.04, 0, 0.04)), sp + Vector((0, 0, 0.02))), (1, sp + nrm * 0.35 + Vector((0.01, 0, 0.03)), sp + Vector((0, 0, 0.02)))], lens=22, fstop=9)
    rows = [x for x in ST["db"].children if x.name.startswith("dr")]
    rows.sort(key=lambda x: int(''.join(c for c in x.name[2:4] if c.isdigit())))
    fdb = WIN["S13"][0] + 8
    for o in rows:
        i = int(''.join(c for c in o.name[2:4] if c.isdigit()))
        vis(o, fdb, False); vis(o, WIN["S13"][0] + 14 + i * 8, True)
    # S16 the password was so easy: close-up, she leans back with a pleased look (head tilt), hands to the desk
    kid_block("S16", lambda u: "keys" if u < 0.25 else "desk", lambda u: 10 - 10 * min(1, u / 0.5), lambda u: (6 - 10 * min(1, u / 0.5) + breath(u, 1.2), -8 * min(1, u / 0.5)), back_fn=lambda u: 0.02 * min(1, u / 0.5), twist_fn=lambda u: -6 * min(1, u / 0.5))
    hf = head_pt("Kid", WIN["S16"][1])
    cam_shot("Cam_S16", "S16", [(0, hf + Vector((-1.40, -0.40, -0.02)), hf + Vector((0, -0.25, -0.22))), (1, hf + Vector((-1.32, -0.34, -0.03)), hf + Vector((0, -0.25, -0.22)))], lens=24)   # v002d: side medium from her left, face <12% of width
    # S17 she thought it was a game: over her right shoulder, mouse clicks, tiles pop
    kid_block("S17", "mouse", lambda u: 10, lambda u: (12 + breath(u, 1.5), 0), bob=0.004)
    cam_shot("Cam_S17", "S17", [(0, (GX - 0.40, 0.30, 1.22), sp + Vector((0, 0, 0.02))), (1, (GX - 0.30, 0.14, 1.16), sp + Vector((0, 0, 0.02)))], lens=32)
    screen_on("game", [WIN["S17"]])
    for i, o in enumerate(sorted([x for x in ST["game"].children if x.name.startswith("tile")], key=lambda x: x.name)):
        fa = WIN["S17"][0] + 10 + (i * 13) % 150
        o.scale = (1, 1, 1); o.keyframe_insert("scale", frame=fa); o.scale = (1.25, 1.25, 1); o.keyframe_insert("scale", frame=fa + 6)
        o.scale = (1, 1, 1); o.keyframe_insert("scale", frame=fa + 14)
    # S18 two weeks: the wall clock's hands race round (time-lapse), girl small in the foreground at her desk
    kid_block("S18", "mouse", lambda u: 10, lambda u: (12, 0))
    CK = bpy.data.objects["Clock"]
    cam_shot("Cam_S18", "S18", [(0, (0.55, -0.9, 1.55), CK.location + Vector((0, 0, -0.05))), (1, (0.45, -1.15, 1.75), CK.location + Vector((0, 0, -0.02)))], lens=40, fstop=9)
    hr = bpy.data.objects["ClockHour"]; mn = bpy.data.objects["ClockMinute"]
    f0, f1 = WIN["S18"]
    for o, turns in ((hr, 0.6), (mn, 6.0)):
        o.rotation_euler = (0, 0, 0); o.keyframe_insert("rotation_euler", frame=f0)
        o.rotation_euler = (0, 0, -turns * 2 * math.pi); o.keyframe_insert("rotation_euler", frame=f1)
        for fc in _fc(o.animation_data.action):
            for k in fc.keyframe_points: k.interpolation = 'LINEAR'
    # S19 top-secret information: over-the-shoulder on documents, redaction bars, she scrolls (mouse)
    kid_block("S19", "mouse", lambda u: 12, lambda u: (14 + breath(u, 1.0), 0), bob=0.004)
    cam_shot("Cam_S19", "S19", [(0, (GX + 0.35, 0.18, 1.22), sp + Vector((0, 0, 0.03))), (1, (GX + 0.22, -0.04, 1.12), sp + Vector((0, 0, 0.03)))], lens=32)
    screen_on("doc", [(WIN["S18"][0], WIN["S19"][1]), (WIN["S22"][0], WIN["S24"][1])])
    for o in ST["doc"].children:
        if o.name.startswith("red"):
            i = int(''.join(c for c in o.name[3:5] if c.isdigit()))
            vis(o, WIN["S19"][0], False); vis(o, WIN["S19"][0] + 20 + i * 12, True)

def office_shots():
    # S20 while the FBI scrambled: agent B at the office desk leans to his monitor (map with blinking dot); agent C crosses behind
    OX = 40.0; f0, f1 = WIN["S20"]; PL = P1LEN["S20"]
    screen_on("map", [(f0, f1)])
    dot = next(x for x in ST["map"].children if x.name.startswith("dot"))
    for k in range(f0, f1, 20): vis(dot, k, ((k - f0) // 20) % 2 == 0)
    seat_o = 0.47
    for fx in FR(f0, f1, 12):
        u = (fx - f0) / PL
        Hb.key_root(fx, Vector((OX + 0.0, 0.06, seat_o + 0.12)), flex=-(10 + 6 * u))
        Hb.key_spine(fx, flex=-(8 + 4 * u), head=(10 + breath(u, 1), -5 + 5 * u))
        for s in "LR":
            sx = 1 if s == "L" else -1
            foot_at("AgentB", s, fx, Vector((OX + sx * 0.14, -0.38, 0.07)), pitch=0)
            knee_pole("AgentB", s, fx, Vector((OX + sx * 0.16, -1.0, 0.6)))
            place_hand(AGB, s, fx, (OX + sx * 0.20, -0.36, 0.749 + 0.032), (0, 0, -1), (-sx * 0.4, -1, 0))
            fingers("AgentB", s, fx, "relaxed"); pole("AgentB", s, fx, (OX + sx * 0.6, 0.3, 0.8))
    # agent C walks past behind (left to right), arms swinging
    walk_char("AgentC", Hc, lambda fx: Vector((OX - 1.7 + 1.1 * (fx - f0) / PL, 1.6, 0)), lambda fx: -90, f0, f1)   # stays clear of agent B's head
    hb = head_pt("AgentB", f0)
    cam_shot("Cam_S20", "S20", [(0, (OX - 0.75, -1.55, 1.45), hb + Vector((0.0, 0.0, -0.1))), (1, (OX - 0.55, -1.40, 1.40), hb + Vector((0.0, 0.0, -0.1)))], lens=30)
    # S21 to find the hacker: agent B stands at the end of the pinboard, 3/4 to camera, scanning it (head turns along the strings)
    f0, f1 = WIN["S21"]; PL = P1LEN["S21"]
    p = Vector((OX + 1.35, -1.85, 0)); yb = -112   # 3/4 toward the camera, board on his left
    Rz = Matrix.Rotation(R_(yb), 3, 'Z')
    for fx in FR(f0, f1, 12):
        u = (fx - f0) / PL
        Hb.key_root(fx, Vector((p.x, p.y, Hb.root_head.z)), yaw=yb)
        Hb.key_spine(fx, flex=2, twist=8 - 10 * u, head=(-4 + breath(u, 1), 22 - 26 * u))   # glances from the board toward camera
        for s_ in "LR":
            sx = 1 if s_ == "L" else -1
            foot_at("AgentB", s_, fx, p + Rz @ Vector((sx * 0.12, 0.0, 0.07)), yaw=yb)
            knee_pole("AgentB", s_, fx, p + Rz @ Vector((sx * 0.14, -0.8, 0.6)))
            hang("AgentB", Hb, s_, fx, p, yb, 0.0)
    walk_char("AgentC", Hc, lambda fx: Vector((OX + 2.6, 2.5, 0)), lambda fx: -90, f0, f1, still=True)
    cam_shot("Cam_S21", "S21", [(0, (OX + 0.10, -0.25, 1.62), (OX + 1.05, -1.95, 1.45)), (1, (OX + 0.28, -0.42, 1.62), (OX + 1.05, -1.95, 1.47))], lens=24)

def walk_char(cid, H, path, yaw_fn, f0, f1, still=False):
    """walk with opposite arm swing (anim_lib walk + hanging arms keyed in the body frame)"""
    rig = RIGS[cid]
    if still:
        p = path(f0); y = yaw_fn(f0); Rz = Matrix.Rotation(R_(y), 3, 'Z')
        for fx in (f0, f1):
            H.key_root(fx, Vector((p.x, p.y, H.root_head.z)), yaw=y); H.key_spine(fx)
            for s in "LR":
                sx = 1 if s == "L" else -1
                foot_at(cid, s, fx, p + Rz @ Vector((sx * 0.12, 0, 0.07)), yaw=y)
                knee_pole(cid, s, fx, p + Rz @ Vector((sx * 0.14, -0.8, 0.6)))
                hang(cid, H, s, fx, p, y, 0.0)
        return
    H.walk(path, yaw_fn, f0, f1, stride=1.25, lift=0.07, bob=0.015, crouch=0.02, lean=3.0, step=2)
    for s in "LR":
        for fx in (f0 - 1, f1 + 1):
            pass
    dist = 0.0; prev = path(f0)
    for fx in FR(f0, f1, 2):
        p = path(fx); dist += (p - prev).to_2d().length; prev = p
        ph = 2 * math.pi * dist / 1.25
        for s in "LR":
            sw = (0.12 if s == "R" else -0.12) * math.sin(ph)
            hang(cid, H, s, fx, p, yaw_fn(fx), sw)

def hang(cid, H, s, fx, p, yaw, swing, bend=0.0):
    sx = 1 if s == "L" else -1
    Rz = Matrix.Rotation(R_(yaw), 3, 'Z')
    sh = H.sh[s] - H.root_head
    off = Vector((sh.x + 0.045 * sx, sh.y - 0.04 - swing - 0.16 * bend, sh.z - H.arm_len * 0.93 + abs(swing) * 0.25 + 0.14 * bend))
    W = Vector((p.x, p.y, H.root_head.z)) + Rz @ off
    place_hand(RIGS[cid], s, fx, W, Rz @ Vector((-sx, 0, 0)), Rz @ Vector((0, -0.25 - swing, -1)))
    fingers(cid, s, fx, "relaxed")
    pole(cid, s, fx, Vector((p.x, p.y, 0)) + Rz @ Vector((sx * 0.45, 0.6, H.root_head.z + 0.3)))

for cid in ("Kid", "AgentB", "AgentC"):
    R = RR[cid]; B = R.BN
    HUM[cid].arm_len = (B["upperarm01.L"].head_local - B["lowerarm01.L"].head_local).length + (B["lowerarm01.L"].head_local - B["wrist.L"].head_local).length

def arrival_shots():
    # S22 they finally showed up: from inside the library looking at the lit doorway, two agents walk in
    f0, f1 = WIN["S22"]; PL = P1LEN["S22"]
    walk_char("AgentB", Hb, lambda fx: Vector((0.75, 5.6 - 2.6 * (fx - f0) / PL, 0)), lambda fx: 0, f0, f1)
    walk_char("AgentC", Hc, lambda fx: Vector((1.55, 6.2 - 2.6 * (fx - f0) / PL, 0)), lambda fx: 0, f0, f1)
    cam_shot("Cam_S22", "S22", [(0, (0.3, 0.4, 1.25), (1.15, 4.0, 1.25)), (1, (0.45, 0.8, 1.3), (1.15, 3.6, 1.35))], lens=30)
    kid_block("S22", "mouse", lambda u: 10, lambda u: (12, 0))
    # S23 they were shocked (v002b): they walk in, slow to a stop; B looks down at the child, C glances round the room; elbows bent
    f0, f1 = WIN["S23"]; PL = P1LEN["S23"]; fm = f0 + int(0.45 * (f1 - f0))
    for cid, H, x, y0 in (("AgentB", Hb, 0.75, 3.55), ("AgentC", Hc, 1.55, 3.75)):
        y1 = y0 - 0.55
        walk_char(cid, H, lambda fx, x=x, y0=y0, y1=y1: Vector((x, y0 + (y1 - y0) * (1 - (1 - (fx - f0) / max(1, fm - f0)) ** 2), 0)), lambda fx: 0, f0, fm)
        p = Vector((x, y1, 0))
        for fx in FR(fm + 1, f1, 6):
            u = (fx - fm) / max(1, f1 - fm)
            look = (12 * min(1, u * 2) + breath(u, 0.8), 0) if cid == "AgentB" else (4, 30 * math.sin(u * math.pi * 1.2))
            H.key_root(fx, Vector((p.x, p.y, H.root_head.z)), yaw=0, flex=2)
            H.key_spine(fx, flex=-3, twist=(look[1] * 0.4 if cid == "AgentC" else 0), head=look)
            ease = min(1, u * 2.5)
            for s_ in "LR":
                sx = 1 if s_ == "L" else -1
                foot_at(cid, s_, fx, p + Vector((sx * 0.13, 0, 0.07)))
                knee_pole(cid, s_, fx, p + Vector((sx * 0.14, -0.8, 0.6)))
                sh = Vector((p.x, p.y, 0)) + H.sh[s_]
                if cid == "AgentB" and s_ == "R":     # hand resting on the front of his belt buckle side, forearm forward, elbow out to the side
                    hp = Vector((p.x + sx * 0.12, p.y - 0.255, H.root_head.z + 0.04))   # palm on the jacket front, not inside it
                    if ease < 1:
                        hang(cid, H, s_, fx, p, 0, 0.0, bend=0.6 + 0.4 * ease)
                    else:
                        place_hand(RIGS[cid], s_, fx, hp, (0, 1, 0), (-sx * 0.8, 0.1, -0.6))
                        fingers(cid, s_, fx, "relaxed"); pole(cid, s_, fx, Vector((p.x + sx * 0.75, p.y - 0.05, H.root_head.z + 0.2)))
                elif cid == "AgentC" and s_ == "L":   # open-hand gesture toward the room (palm up, forearm forward)
                    W = Vector((p.x + sx * 0.2, p.y - 0.36, H.root_head.z + 0.15 + 0.03 * math.sin(u * math.pi * 2)))
                    hang(cid, H, s_, fx, p, 0, 0.0, bend=0.6) if ease < 0.3 else place_hand(RIGS[cid], s_, fx, W, (0.2 * sx, 0.1, 1.0), (0.25 * sx, -1, 0.1))
                    if ease >= 0.3: fingers(cid, s_, fx, "flat_palm"); pole(cid, s_, fx, Vector((p.x + sx * 0.45, p.y + 0.3, H.root_head.z - 0.1)))
                else:
                    hang(cid, H, s_, fx, p, 0, 0.0, bend=0.6)
            key_jaw(cid, fx, 5 * min(1, u * 2))
    Lf = bpy.data.lights.new("ArrivalFill", 'AREA'); Lf.energy = 30; Lf.size = 1.5; Lf.color = (0.8, 0.88, 1.0)
    lf = bpy.data.objects.new("ArrivalFill", Lf); sc.collection.objects.link(lf); lf.location = (1.15, 1.4, 2.0)
    lf.rotation_euler = (Vector((1.15, 3.0, 1.6)) - lf.location).to_track_quat('-Z', 'Y').to_euler(); show_only(lf, [WIN["S22"], WIN["S23"]])
    cam_shot("Cam_S23", "S23", [(0, (1.15, 0.85, 1.55), (1.15, 3.0, 1.5)), (1, (1.15, 1.05, 1.55), (1.15, 3.0, 1.52))], lens=26)   # both agents fully in frame
    kid_block("S23", "mouse", lambda u: 10, lambda u: (12, 0))
    # S24 it was a child: she turns on her chair toward them (yaw), head turned, innocent look; camera from the agents' side
    kid_block("S24", "desk", lambda u: 0, lambda u: (4, HEADSIGN * 55 * min(1, u / 0.4)), twist_fn=lambda u: HEADSIGN * 24 * min(1, u / 0.4))
    hf = head_pt("Kid", WIN["S24"][1])
    cam_shot("Cam_S24", "S24", [(0, hf + Vector((0.95, 0.40, 0.12)), hf + Vector((0, 0, -0.1))), (1, hf + Vector((0.80, 0.36, 0.10)), hf + Vector((0, 0, -0.08)))], lens=40)

IX = 80.0
def int_sit(cid, H, f, side, lean=0.0, head=(0.0, 0.0), hands="table", yaw_extra=0.0, seat=0.454):
    """seated at the interrogation table; side -1 = west chair facing +X, +1 = east chair facing -X"""
    yaw = 90 if side < 0 else -90
    yaw += yaw_extra
    Rz = Matrix.Rotation(R_(yaw), 3, 'Z')
    base = Vector((IX + side * 0.66, 0, 0))
    H.key_root(f, base + Vector((0, 0, seat + 0.12)), yaw=yaw, flex=-lean)
    H.key_spine(f, flex=-lean * 0.5, head=head)
    for s in "LR":
        sx = 1 if s == "L" else -1
        foot_at(cid, s, f, base + Rz @ Vector((sx * 0.12, -0.42, 0.07)), yaw=yaw)
        knee_pole(cid, s, f, base + Rz @ Vector((sx * 0.14, -1.0, 0.6)))
        if hands == "table":
            place_hand(RIGS[cid], s, f, base + Rz @ Vector((sx * 0.17, -0.40, 0.0)) + Vector((0, 0, 0.759 + 0.032)), (0, 0, -1), Rz @ Vector((-sx * 0.45, -1, 0)))
        elif hands == "lap":
            place_hand(RIGS[cid], s, f, base + Rz @ Vector((sx * 0.08, -0.30, 0)) + Vector((0, 0, seat + 0.19)), (0, 0, -1), Rz @ Vector((-sx * 0.25, -1, -0.2)))
        fingers(cid, s, f, "relaxed")
        pole(cid, s, f, base + Rz @ Vector((sx * 0.55, 0.3, 0.8)))

def make_photo():
    img = bpy.data.images.load(W + "family_photo.png")
    m = bpy.data.materials.new("FamilyPhoto"); m.use_nodes = True; nt = m.node_tree; Pn = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = img; nt.links.new(t.outputs["Color"], Pn.inputs["Base Color"]); Pn.inputs["Roughness"].default_value = 0.3
    bpy.ops.mesh.primitive_plane_add(size=1); o = bpy.context.object; o.name = "FamilyPhoto"; o.scale = (0.16, 0.12, 1); bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(m)
    bpy.ops.mesh.primitive_plane_add(size=1); fr = bpy.context.object; fr.name = "FamilyPhotoBorder"; fr.scale = (0.18, 0.14, 1); bpy.ops.object.transform_apply(scale=True)
    fr.data.materials.append(mat("PhotoBorder", (0.93, 0.93, 0.9), 0.4)); fr.parent = o; fr.location = (0, 0, -0.0015)
    o.rotation_euler = (0, 0, R_(-90 + 8))   # image upright for the girl's side (west), slightly askew
    return o

def interro_shots():
    # S25 brought her in for questioning: wide of the room, kid west (small), agent A east; slow push-in
    for sid in ("S25", "S26"):
        f0, f1 = WIN[sid]
        for fx in FR(f0, f1, 12):
            u = (fx - f0) / PL
            int_sit("Kid", Hk, fx, -1, lean=4, head=(6 + breath(u, 1), 0), hands="lap", seat=0.454)
            int_sit("AgentB", Hb, fx, +1, lean=8 + 4 * u, head=(8 + breath(u, 1), 0), hands="table")
    cam_shot("Cam_S25", "S25", [(0, (IX, -2.25, 1.75), (IX, 0, 0.85)), (1, (IX + 0.05, -1.95, 1.65), (IX, 0, 0.88))], lens=24)
    # S26 discovered her mother worked for NASA: family photo on the table, agent's hand rests beside it; push in
    PH = bpy.data.objects.get("FamilyPhoto")
    pp = Vector((IX + 0.05, -0.05, 0.759 + 0.004))
    if PH: PH.location = pp
    cam_shot("Cam_S26", "S26", [(0, pp + Vector((-0.42, -0.28, 0.52)), pp), (1, pp + Vector((-0.30, -0.18, 0.38)), pp)], lens=35, fstop=9)
    # S27-S30 the mother at the table (west chair), agent A opposite: she explains, hands open, then looks down
    for sid, lean0, head_fn in (("S27", 6, lambda u: (4 + breath(u, 1.5), 4 * math.sin(u * 6))), ("S28", 10, lambda u: (6 + breath(u, 1), -6 + 6 * u)),
                                ("S29", 14, lambda u: (8 + 4 * u + breath(u, 1), 0)), ("S30", 10, lambda u: (8 + 22 * min(1, u / 0.5), 0))):
        f0, f1 = WIN[sid]
        for fx in FR(f0, f1, 10):
            u = (fx - f0) / PL
            int_sit("Mom", Hm, fx, -1, lean=lean0, head=head_fn(u), hands="table", seat=0.454)
            int_sit("AgentB", Hb, fx, +1, lean=6, head=(6, 0), hands="table")
            key_jaw("Mom", fx, (5 + 4 * math.sin(fx * 0.35)) if sid in ("S27", "S28") else 1.0)
    hm = head_pt("Mom", WIN["S27"][0])
    cam_shot("Cam_S27", "S27", [(0, hm + Vector((0.85, -0.45, 0.02)), hm + Vector((0, 0, -0.1))), (1, hm + Vector((0.75, -0.32, 0.02)), hm + Vector((0, 0, -0.1)))], lens=45)
    cam_shot("Cam_S28", "S28", [(0, (IX + 1.35, 0.45, 1.45), hm + Vector((0, 0, -0.15))), (1, (IX + 1.25, 0.30, 1.42), hm + Vector((0, 0, -0.15)))], lens=40)
    cam_shot("Cam_S29", "S29", [(0, hm + Vector((0.75, 0.40, -0.02)), hm + Vector((0, 0, -0.08))), (1, hm + Vector((0.62, 0.32, -0.02)), hm + Vector((0, 0, -0.08)))], lens=45)
    cam_shot("Cam_S30", "S30", [(0, hm + Vector((0.70, -0.35, -0.05)), hm + Vector((0, 0, -0.12))), (1, hm + Vector((0.62, -0.30, -0.08)), hm + Vector((0, 0, -0.14)))], lens=45)

def ending_shots():
    # S31 but instead: over her shoulder, the screen turns red with a padlock
    kid_block("S31", "keys", lambda u: 12 - 6 * min(1, u / 0.4), lambda u: (14 - 4 * min(1, u / 0.4), 0))
    sp = PCR.matrix_world @ Vector((0.43, 0.0, 1.2))
    cam_shot("Cam_S31", "S31", [(0, (GX + 0.30, 0.25, 1.22), sp), (1, (GX + 0.22, 0.10, 1.16), sp)], lens=32)
    f0 = WIN["S31"][0]
    screen_on("desk", [(f0, f0 + 25)]); screen_on("red", [(f0 + 26, WIN["S33"][1])])
    lk = next(x for x in ST["red"].children if x.name.startswith("lock"))
    for i, fx in enumerate(range(f0 + 26, WIN["S33"][1], 30)):
        lk.scale = (1.0 if i % 2 else 1.08,) * 3; lk.keyframe_insert("scale", frame=fx)
    # S32 banned from computers: face close-up lit red, she slumps a little
    kid_block("S32", "desk", lambda u: 6 - 8 * u, lambda u: (8 - 4 * u + breath(u, 1), 0), back_fn=lambda u: 0.02 * u)
    hf = head_pt("Kid", WIN["S32"][0])
    cam_shot("Cam_S32", "S32", [(0, hf + Vector((0.22, -0.46, 0.03)), hf + Vector((0, 0, -0.05))), (1, hf + Vector((0.15, -0.40, 0.03)), hf + Vector((0, 0, -0.05)))], lens=50)
    # S33 for eight years: she sits back, hands into her lap; camera pulls back and rises to a wide of the dark library
    kid_block("S33", lambda u: "desk" if u < 0.3 else "lap", lambda u: -2 - 4 * min(1, u / 0.5), lambda u: (10 + 6 * min(1, u / 0.5) + breath(u, 0.8), 0), back_fn=lambda u: 0.03 * min(1, u / 0.5))
    hf = head_pt("Kid", WIN["S33"][0])
    cam_shot("Cam_S33", "S33", [(0, hf + Vector((-0.42, -0.60, 0.08)), hf + Vector((0, 0, -0.16))), (1, hf + Vector((-0.95, -1.05, 0.40)), hf + Vector((0, 0, -0.08)))], lens=40)   # feet stay out of frame

kid_lib_shots(); office_shots(); arrival_shots()   # the VO ends at "only a child": S25-S33 are not in the film

# kid in the library windows vs interrogation; who is visible where
def rng(*sids): return [WIN[s] for s in sids]
LIB_KID = [k for k in WIN if k not in ("S20", "S21")]
show_only(KID, rng(*LIB_KID))
show_only(AGB, rng("S20", "S21", "S22", "S23"))
show_only(AGC, rng("S22", "S23"))
for o in bpy.data.objects:
    const_all(o)
# hold the kid in a neutral seat on the frames she is hidden is unnecessary: every shot keys its own pose at its first and last frame
# ONE film camera (farm rule): bake every shot camera into CAM_Film, keyed every frame, constant interpolation (hard cuts)
FC = bpy.data.objects.new("CAM_Film", bpy.data.cameras.new("CAM_Film")); sc.collection.objects.link(FC)
FC.data.dof.use_dof = True; FC.data.clip_start = 0.02; FC.rotation_mode = 'XYZ'
for sid, f0, f1, cn in CAMS:
    c = bpy.data.objects[cn]
    for fx in range(f0, f1 + 1):
        sc.frame_set(fx)
        FC.matrix_world = c.matrix_world.copy()
        FC.keyframe_insert("location", frame=fx); FC.keyframe_insert("rotation_euler", frame=fx)
        for attr in ("lens",):
            setattr(FC.data, attr, getattr(c.data, attr)); FC.data.keyframe_insert(attr, frame=fx)
        FC.data.dof.focus_distance = c.data.dof.focus_distance; FC.data.dof.keyframe_insert("focus_distance", frame=fx)
        FC.data.dof.aperture_fstop = c.data.dof.aperture_fstop; FC.data.dof.keyframe_insert("aperture_fstop", frame=fx)
for ob in (FC, FC.data):
    for fc in _fc(ob.animation_data.action):
        for k in fc.keyframe_points: k.interpolation = 'CONSTANT'
# euler continuity (no spin between frames)
for fc in _fc(FC.animation_data.action):
    if fc.data_path == "rotation_euler":
        prev = None
        for k in fc.keyframe_points:
            if prev is not None:
                while k.co[1] - prev > math.pi: k.co[1] -= 2 * math.pi
                while k.co[1] - prev < -math.pi: k.co[1] += 2 * math.pi
            prev = k.co[1]
Lc = bpy.data.lights.new("Catch_Film", 'POINT'); Lc.energy = 0.12; Lc.shadow_soft_size = 0.02
lc = bpy.data.objects.new("Catch_Film", Lc); sc.collection.objects.link(lc); lc.parent = FC; lc.location = (0.04, 0.05, 0)
for sid, f0, f1, cn in CAMS:
    c = bpy.data.objects[cn]
    for ch in list(c.children): bpy.data.objects.remove(ch)
    bpy.data.objects.remove(c)
sc.timeline_markers.clear(); sc.camera = FC
CAMS = [(sid, f0, f1, "CAM_Film") for sid, f0, f1, cn in CAMS]
sc.sequence_editor_create()
snd = sc.sequence_editor.strips.new_sound("VO", "/tmp/claude-0/kh/vo/B32_KidHacker_VO.mp3", 1, 1) if hasattr(sc.sequence_editor, "strips") else sc.sequence_editor.sequences.new_sound("VO", "/tmp/claude-0/kh/vo/B32_KidHacker_VO.mp3", 1, 1)
json.dump({"shots": [{"shot": s, "f0": f0, "f1": f1, "cam": c} for s, f0, f1, c in CAMS], "frame_end": sc.frame_end}, open(W + "shots_v002.json", "w"), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("SHOTS_OK", OUT, sc.frame_end)
