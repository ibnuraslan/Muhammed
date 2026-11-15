"""Phase-1 animation: every shot is its own clip (about 1.3x the reference slot), laid end to end, with its own camera
(CAM_<id>, timeline marker bound at the clip start = hard cut). Clip starts come from shots.json, so Phase 2 can re-lay
them to the VO frames by re-running this script with new starts (no time-stretch).
blender -b sets.blend -P 04_anim.py -- <repo>/blender shots.json out.blend"""
import bpy, bmesh, sys, os, math, json, random
from mathutils import Vector, Matrix, Euler, Quaternion
a = sys.argv[sys.argv.index("--") + 1:]; ROOT, SHOTS, OUT = a
exec(open(os.path.join(ROOT, "pipeline/anim_lib.py")).read())
exec(open(os.path.join(ROOT, "pipeline/hand_poses.py")).read())
sc = bpy.context.scene; R_ = math.radians; random.seed(3)
OCEAN, UNDER, MOUTH, HOSP = Vector((0, 0, 0)), Vector((3000, 0, 0)), Vector((6000, 0, 0)), Vector((9000, 0, 0))
SH = json.load(open(SHOTS))
order = [s["id"] for s in SH["shots"]]
F = {}; f = 1
for s in SH["shots"]:
    f0 = s.get("start", f); n = s["frames"]; F[s["id"]] = (f0, f0 + n - 1); f = f0 + n
sc.frame_start, sc.frame_end = 1, f - 1
sc.render.fps = 60
print("TIMELINE", F, "end", sc.frame_end)

def lerp(a_, b_, t): return a_ + (b_ - a_) * t
def ease(t): return smooth(t)
def frames(sid, step=2):
    f0, f1 = F[sid]; out = list(range(f0, f1 + 1, step))
    if out[-1] != f1: out.append(f1)
    return out
def T(sid, fr):
    f0, f1 = F[sid]; return (fr - f0) / max(1, f1 - f0)

# ---------------------------------------------------------------- visibility and lights per set
SETS = {"1a": "O", "1b": "O", "1c": "O", "2": "M", "3a": "U", "3b": "U", "3c": "U", "4a": "U", "4b": "U", "5a": "M", "5b": "M", "5c": "M",
        "6a": "O", "6b": "O", "6c": "O", "7a": "H", "7b": "H", "8a": "H", "8b": "H", "9": "H", "10": "H", "11a": "U", "11b": "U",
        "12a": "O", "12b": "O", "13": "O"}
def key_vis(ob, f_, vis):
    ob.hide_render = ob.hide_viewport = not vis
    ob.keyframe_insert("hide_render", frame=f_); ob.keyframe_insert("hide_viewport", frame=f_)
LIGHTSETS = {"Sun": "O", "UW_sun": "U"}
for ln, st in LIGHTSETS.items():
    o = bpy.data.objects[ln]
    for sid in order: key_vis(o, F[sid][0], SETS[sid] == st)
vest = bpy.data.objects["Diver.vest"]
for sid in order: key_vis(vest, F[sid][0], SETS[sid] == "H")
for o in bpy.data.objects:
    if o.animation_data and o.animation_data.action:
        for fc in o.animation_data.action.fcurves if hasattr(o.animation_data.action, "fcurves") else []:
            for k in fc.keyframe_points: k.interpolation = 'CONSTANT'
def constant_keys(ob, path_prefix=("hide_",)):
    ad = ob.animation_data
    if not ad or not ad.action: return
    for fc in _fcurves(ad.action):
        if fc.data_path.startswith(path_prefix):
            for k in fc.keyframe_points: k.interpolation = 'CONSTANT'
def _fcurves(act):
    if hasattr(act, "fcurves") and len(act.fcurves): return list(act.fcurves)
    out = []
    for layer in getattr(act, "layers", []):
        for strip in layer.strips:
            for cb in strip.channelbags: out += list(cb.fcurves)
    return out

# ---------------------------------------------------------------- whale
W = bpy.data.objects["WhaleRig"]; WR = Rig(W)
for pb in W.pose.bones: pb.rotation_mode = 'XYZ'
def key_whale(f_, loc, rot, jaw=0.0, swim=0.0, amp=1.0, flip=0.0):
    """rot = world euler (deg). swim = phase (cycles). jaw = opening (deg)."""
    W.location = loc; W.rotation_euler = [R_(x) for x in rot]
    W.keyframe_insert("location", frame=f_); W.keyframe_insert("rotation_euler", frame=f_)
    ph = 2 * math.pi * swim
    for n, A, lag in (("sp1", 2.0, 0.0), ("sp2", 5.0, 0.6), ("tail", 9.0, 1.2), ("fluke", 14.0, 1.8)):
        W.pose.bones[n].rotation_euler = (R_(A * amp * math.sin(ph - lag)), 0, 0)
        W.pose.bones[n].keyframe_insert("rotation_euler", frame=f_)
    W.pose.bones["head"].rotation_euler = (R_(-1.5 * amp * math.sin(ph + 0.5)), 0, 0); W.pose.bones["head"].keyframe_insert("rotation_euler", frame=f_)
    W.pose.bones["jaw"].rotation_euler = (R_(-jaw), 0, 0); W.pose.bones["jaw"].keyframe_insert("rotation_euler", frame=f_)
    for s, sg in (("L", 1), ("R", -1)):
        W.pose.bones["flip." + s].rotation_euler = (R_(8 * math.sin(ph * 0.5 + 0.3) + flip), 0, 0)
        W.pose.bones["flip." + s].keyframe_insert("rotation_euler", frame=f_)
def whale_park(f_):
    key_whale(f_, UNDER + Vector((0, 400, -150)), (0, 0, 0))

# ---------------------------------------------------------------- shark (held at its widest bite pose, frame 8 of the CC-BY loop)
SR = bpy.data.objects["SharkRig"]; SROOT = bpy.data.objects["Shark_root"]
sc.frame_set(8)
held = {pb.name: (pb.location.copy(), pb.rotation_quaternion.copy() if pb.rotation_mode == 'QUATERNION' else pb.rotation_euler.to_quaternion(), pb.scale.copy()) for pb in SR.pose.bones}
SR.animation_data.action = None
for pb in SR.pose.bones: pb.rotation_mode = 'QUATERNION'
SROOT.scale = Vector(SROOT.scale) * 2.6
def key_shark(f_, loc, yaw=0.0, pitch=0.0, wig=0.0, jaw_extra=0.0):
    SROOT.location = loc; SROOT.rotation_euler = (R_(pitch) + R_(90) * 0 + SROOT.rotation_euler.x * 0, 0, R_(yaw))
    SROOT.keyframe_insert("location", frame=f_); SROOT.keyframe_insert("rotation_euler", frame=f_)
    for pb in SR.pose.bones:
        l, q, s_ = held[pb.name]; pb.location = l; pb.scale = s_
        if pb.name.startswith(("Spine", "BackFin")):
            q = q @ Quaternion((0, 0, 1), R_(3.0 * math.sin(wig)))
        if pb.name.startswith("Jaw"): q = q @ Quaternion((1, 0, 0), R_(jaw_extra))
        pb.rotation_quaternion = q
        pb.keyframe_insert("location", frame=f_); pb.keyframe_insert("rotation_quaternion", frame=f_)
SHARK_ROT0 = SROOT.rotation_euler.copy()

# ---------------------------------------------------------------- characters
class Actor:
    def __init__(self, name):
        self.o = bpy.data.objects[name]; self.o.location = (0, 0, 0); self.o.rotation_euler = (0, 0, 0)
        self.r = Rig(self.o); self.h = Human(self.r)
        self.root_head = self.h.root_head
        for pb in self.o.pose.bones: pb.rotation_mode = 'QUATERNION'
    def key_body(self, f_, M):
        """M = world matrix of the body frame (rest: origin at the root head, character faces -Y, up +Z)"""
        self.r.key_world("root", f_, Matrix.Translation(M.translation) @ M.to_3x3().to_4x4() @ Matrix.Translation(-self.root_head) @ self.r.rest("root"))
    def key_foot(self, s, f_, M, p_loc, yaw=0.0, pitch=0.0, knee_dir=Vector((0, -1, 0.3))):
        """p_loc: ankle position in the body frame (rest ankle = self.h.ankle[s] - root_head)"""
        a_ = self.h.ankle[s]
        Rl = Matrix.Rotation(R_(yaw), 4, 'Z') @ Matrix.Rotation(R_(pitch), 4, 'X')
        Mw = M @ Matrix.Translation(p_loc) @ Rl @ Matrix.Translation(-a_) @ self.r.rest("IK_foot." + s)
        self.r.key_world("IK_foot." + s, f_, Mw)
        n = "Pole_knee." + s; pb = self.r.PB[n]
        pole = M @ (p_loc + Vector((0, 0, 0.45)) + knee_dir.normalized() * 0.7)
        pb.location = self.r.rest(n).to_3x3().inverted() @ (pole - self.r.BN[n].head_local); pb.keyframe_insert("location", frame=f_, group=n)
    def key_hand(self, s, f_, M, palm_loc, normal_loc, fdir_loc, elbow_loc):
        place_hand(self.o, s, f_, M @ palm_loc, M.to_3x3() @ normal_loc, M.to_3x3() @ fdir_loc)
        n = "Pole_elbow." + s; pb = self.r.PB[n]
        pb.location = self.r.rest(n).to_3x3().inverted() @ ((M @ elbow_loc) - self.r.BN[n].head_local); pb.keyframe_insert("location", frame=f_, group=n)
    def key_spine(self, f_, flex=0.0, twist=0.0, side=0.0, head=(0.0, 0.0)):
        self.h.key_spine(f_, flex, twist, side, head)
    def hand_pose(self, s, f_, pose, amount=1.0):
        apply_pose(self.o, s, pose, f_, amount)
    def rest_ankle(self, s): return self.h.ankle[s] - self.root_head
    def shoulder(self, s): return self.r.BN["upperarm01." + s].head_local - self.root_head
    def park(self, f_):
        M = Matrix.Translation(HOSP + Vector((0, 60, 0)) + self.root_head)
        self.key_body(f_, M)
        for s in "LR":
            self.key_foot(s, f_, M, self.rest_ankle(s))
            sx = 1 if s == "L" else -1
            self.key_hand(s, f_, M, self.shoulder(s) + Vector((sx * 0.08, -0.02, -0.62)), Vector((-sx, 0, 0)), Vector((0, 0, -1)), self.shoulder(s) + Vector((sx * 0.2, 0.3, -0.3)))

D = Actor("Diver"); DM = Actor("DocM"); DF = Actor("DocF")
_v = bpy.data.objects["Diver.vest"]; _v.matrix_parent_inverse = Matrix.Identity(4)
def M_of(pos, yaw=0.0, pitch=0.0, roll=0.0):
    """body frame at world pos: yaw about Z (0 = facing -Y), pitch about X (+ = lean forward), roll about Y"""
    return Matrix.Translation(pos) @ (Matrix.Rotation(R_(yaw), 4, 'Z') @ Matrix.Rotation(R_(pitch), 4, 'X') @ Matrix.Rotation(R_(roll), 4, 'Y'))

def arms_hang(A, f_, M, swing=0.0, out=0.0):
    for s in "LR":
        sx = 1 if s == "L" else -1; sh = A.shoulder(s)
        A.key_hand(s, f_, M, sh + Vector((sx * (0.10 + out), -0.06 + swing * sx, -0.60)), Vector((-sx, 0.1, 0)), Vector((0, -0.05, -1)),
                   sh + Vector((sx * 0.25, 0.35, -0.3)))
def legs_stand(A, f_, M, crouch=0.0, spread=0.0):
    for s in "LR":
        sx = 1 if s == "L" else -1; a_ = A.rest_ankle(s)
        A.key_foot(s, f_, M, Vector((a_.x + sx * spread, a_.y - 0.02, a_.z + crouch)))

# ---------------------------------------------------------------- effects: splash crown + foam ring, keyed scale and alpha
def fx_material(name, rgb, strength=0.6):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; P = N["Principled BSDF"]
    P.inputs['Base Color'].default_value = (*rgb, 1); P.inputs['Roughness'].default_value = 0.3
    P.inputs['Emission Color'].default_value = (*rgb, 1); P.inputs['Emission Strength'].default_value = strength
    return m
def make_splash(name):
    """a spray crown: droplets thrown up and out in a cone, uniform size (scaled uniformly by key_fx)"""
    bm = bmesh.new()
    for i in range(1800):
        ang = random.uniform(0, 2 * math.pi); h = random.random() ** 0.7; r = 0.35 + 0.65 * h * random.uniform(0.6, 1.0)
        c0 = Vector((math.cos(ang) * r, math.sin(ang) * r, h * random.uniform(0.5, 1.0)))
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=random.uniform(0.002, 0.005) * (1.3 - 0.7 * h), matrix=Matrix.Translation(c0))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); o = bpy.data.objects.new(name, me); sc.collection.objects.link(o)
    m = bpy.data.materials.new(name + "_m"); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links; N.clear()
    gl = N.new('ShaderNodeBsdfGlass'); gl.inputs['Color'].default_value = (0.9, 0.97, 1.0, 1); gl.inputs['Roughness'].default_value = 0.05
    tr = N.new('ShaderNodeBsdfTransparent'); mx = N.new('ShaderNodeMixShader'); mx.inputs[0].default_value = 0.55
    out = N.new('ShaderNodeOutputMaterial'); L.new(tr.outputs[0], mx.inputs[1]); L.new(gl.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs[0])
    me.materials.append(m); o.visible_shadow = False      # fine translucent spray (director, Nov 15)
    return o
def make_ring(name):
    """flat foam patch on the water: a disc with a soft procedural foam pattern and alpha"""
    bpy.ops.mesh.primitive_circle_add(vertices=64, radius=1.0, fill_type='NGON'); o = bpy.context.object; o.name = name
    m = bpy.data.materials.new(name + "_m"); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links; N.clear()
    tc = N.new('ShaderNodeTexCoord'); nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 3.0; nz.inputs['Detail'].default_value = 6
    ln = N.new('ShaderNodeVectorMath'); ln.operation = 'LENGTH'
    mr = N.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 1.0; mr.inputs['From Max'].default_value = 0.35
    mul = N.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
    rr = N.new('ShaderNodeValToRGB'); rr.color_ramp.elements[0].position = 0.45; rr.color_ramp.elements[1].position = 0.62
    L.new(tc.outputs['Object'], nz.inputs['Vector']); L.new(tc.outputs['Object'], ln.inputs[0])
    L.new(nz.outputs['Fac'], rr.inputs[0]); L.new(ln.outputs['Value'], mr.inputs[0]); L.new(rr.outputs[0], mul.inputs[0]); L.new(mr.outputs[0], mul.inputs[1])
    P = N.new('ShaderNodeBsdfPrincipled'); P.inputs['Base Color'].default_value = (0.92, 0.96, 0.98, 1); P.inputs['Roughness'].default_value = 0.6
    tr = N.new('ShaderNodeBsdfTransparent'); mx = N.new('ShaderNodeMixShader'); out = N.new('ShaderNodeOutputMaterial')
    L.new(mul.outputs[0], mx.inputs[0]); L.new(tr.outputs[0], mx.inputs[1]); L.new(P.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs[0])
    o.data.materials.append(m); o.visible_shadow = False
    return o
SPL = make_splash("FX_splash"); RING = make_ring("FX_foamring")
def key_fx(o, f_, loc, scale, vis=True):
    o.location = loc; o.scale = scale if isinstance(scale, (tuple, list, Vector)) else (scale, scale, scale)
    o.keyframe_insert("location", frame=f_); o.keyframe_insert("scale", frame=f_); key_vis(o, f_, vis)
def fx_off(f_):
    for o in (SPL, RING): key_fx(o, f_, Vector((0, 0, -500)), 0.01, False)
for sid in order: fx_off(F[sid][0])

# ---------------------------------------------------------------- cameras
cam_col = bpy.data.collections.new("CAMERAS"); sc.collection.children.link(cam_col)
CAMS = {}
def camera(sid, keys, lens=35):
    """keys: list of (t 0..1, cam_pos, target_pos); level horizon via Track To (up = world Z)"""
    cd = bpy.data.cameras.new("CAM_" + sid); cd.lens = lens; cd.dof.use_dof = False; cd.clip_start = 0.05; cd.clip_end = 2000
    c = bpy.data.objects.new("CAM_" + sid, cd); cam_col.objects.link(c)
    t = bpy.data.objects.new("TGT_" + sid, None); cam_col.objects.link(t)
    tr = c.constraints.new('TRACK_TO'); tr.target = t; tr.track_axis = 'TRACK_NEGATIVE_Z'; tr.up_axis = 'UP_Y'
    f0, f1 = F[sid]
    for tt, p, q in keys:
        fr = round(f0 + tt * (f1 - f0)); c.location = p; t.location = q
        c.keyframe_insert("location", frame=fr); t.keyframe_insert("location", frame=fr)
    for ob in (c, t):
        for fc in _fcurves(ob.animation_data.action):
            for k in fc.keyframe_points: k.interpolation = 'BEZIER'; k.handle_left_type = k.handle_right_type = 'AUTO_CLAMPED'
    m = sc.timeline_markers.new("S" + sid, frame=f0); m.camera = c
    CAMS[sid] = c
    return c

# ---------------------------------------------------------------- park everything at frame 1 of each shot that doesn't use it
SEA_Z = 0.0
def sea_time():
    oc = bpy.data.objects["Sea"].modifiers["Ocean"]
    for fr in (sc.frame_start, sc.frame_end):
        oc.time = fr / 60.0 * 0.8; oc.keyframe_insert("time", frame=fr)
    for fc in _fcurves(bpy.data.objects["Sea"].animation_data.action):
        for k in fc.keyframe_points: k.interpolation = 'LINEAR'
sea_time()

def whale_breach(sid, t0, t1, z0, z1, jaw0, jaw1, tilt=0.0, x=0.0, y=0.0, sw0=0.0):
    for fr in frames(sid):
        t = T(sid, fr); u = lerp(t0, t1, t)
        key_whale(fr, OCEAN + Vector((x, y, lerp(z0, z1, ease(u)))), (0, 90 - tilt, 0), jaw=lerp(jaw0, jaw1, ease(u)), swim=sw0 + 0.4 * u, amp=0.4)

# ============================================================== SHOTS
# 1a: breach, jaws wide, the diver in the gap pushing up
def jaw_hinge_world(fr):
    """a point inside the open gap between the jaws, a little above the hinge"""
    sc.frame_set(fr); P = W.pose.bones; Mw = W.matrix_world
    hinge = Mw @ P["jaw"].head; tips = ((Mw @ P["jaw"].tail) + (Mw @ P["head"].tail)) / 2
    return hinge.lerp(tips, 0.62)
sid = "1a"; whale_breach(sid, 0.0, 1.0, -6.0, -2.6, 42, 38, tilt=8)
for fr in frames(sid, 4):
    hp = jaw_hinge_world(fr); t = T(sid, fr)
    M = M_of(hp + Vector((0.0, 0.0, -0.35)), yaw=0, pitch=-8)
    D.key_body(fr, M); D.key_spine(fr, flex=-10, head=(-14 + 6 * math.sin(t * 6), 10 * math.sin(t * 4)))
    legs_stand(D, fr, M, crouch=0.05)
    for s in "LR":
        sx = 1 if s == "L" else -1; sh = D.shoulder(s)
        D.key_hand(s, fr, M, sh + Vector((sx * 0.22, -0.18, 0.55 + 0.04 * math.sin(t * 9 + sx))), Vector((0, 0.1, 1)), Vector((sx * 0.2, -0.3, 0.3)), sh + Vector((sx * 0.5, 0.2, 0.0)))
for s in "LR": D.hand_pose(s, F[sid][0], "open_alarm")
key_fx(SPL, F[sid][0], OCEAN + Vector((-1, 0, -0.5)), (4, 4, 2.5)); key_fx(SPL, F[sid][1], OCEAN + Vector((-1, 0, -0.5)), (7, 7, 4.5))
key_fx(RING, F[sid][0], OCEAN + Vector((-1, 0, 0.05)), (3.5, 3.5, 1)); key_fx(RING, F[sid][1], OCEAN + Vector((-1, 0, 0.05)), (6, 6, 1))
camera(sid, [(0, OCEAN + Vector((-4, -16, 1.4)), OCEAN + Vector((0, 0, 2.5))), (1, OCEAN + Vector((-3, -14, 1.8)), OCEAN + Vector((0, 0, 4.0)))], lens=30)

# 1b: jaws close, the diver drops below the lip line (cut before they meet)
sid = "1b"; whale_breach(sid, 0.0, 1.0, -2.6, -2.0, 38, 6, tilt=10, sw0=0.4)
for fr in frames(sid, 4):
    hp = jaw_hinge_world(fr); t = T(sid, fr)
    M = M_of(hp + Vector((0.0, 0.0, -0.35 - 1.6 * ease(min(1, t * 1.6)))), yaw=0, pitch=-8)
    D.key_body(fr, M); D.key_spine(fr, flex=-5, head=(-20, 0))
    legs_stand(D, fr, M, crouch=0.05)
    for s in "LR":
        sx = 1 if s == "L" else -1; sh = D.shoulder(s)
        D.key_hand(s, fr, M, sh + Vector((sx * 0.22, -0.18, 0.55)), Vector((0, 0.1, 1)), Vector((sx * 0.2, -0.3, 0.3)), sh + Vector((sx * 0.5, 0.2, 0.0)))
key_fx(SPL, F[sid][0], OCEAN + Vector((-1, 0, -0.5)), (7, 7, 4)); key_fx(SPL, F[sid][1], OCEAN + Vector((-1, 0, -0.5)), (9, 9, 3))
key_fx(RING, F[sid][0], OCEAN + Vector((-1, 0, 0.05)), (6, 6, 1)); key_fx(RING, F[sid][1], OCEAN + Vector((-1, 0, 0.05)), (8, 8, 1))
camera(sid, [(0, OCEAN + Vector((6, -9, 3.0)), OCEAN + Vector((0, -0.5, 4.2))), (1, OCEAN + Vector((5, -8, 3.2)), OCEAN + Vector((0, -0.5, 4.0)))], lens=30)

# 1c: the whale falls back and sinks; foam ring and spray
sid = "1c"
for fr in frames(sid):
    t = T(sid, fr)
    key_whale(fr, OCEAN + Vector((2.0 * t, 0, lerp(-2.2, -12.0, ease(t)))), (0, lerp(78, 40, ease(t)), 0), jaw=0, swim=0.8 + 0.5 * t, amp=0.8)
D.park(F[sid][0])
key_fx(SPL, F[sid][0], OCEAN + Vector((-2, 0, -0.6)), (9, 9, 3)); key_fx(SPL, F[sid][1], OCEAN + Vector((-2, 0, -0.6)), (12, 12, 1.2))
key_fx(RING, F[sid][0], OCEAN + Vector((-2, 0, 0.05)), (8, 8, 1)); key_fx(RING, F[sid][1], OCEAN + Vector((-2, 0, 0.05)), (12, 12, 1))
camera(sid, [(0, OCEAN + Vector((10, -24, 8)), OCEAN + Vector((-1.5, 0, 1.5))), (1, OCEAN + Vector((10, -24, 12)), OCEAN + Vector((-1.5, 0, 0.5)))], lens=32)

# 2: inside the mouth, lying on the tongue, waking: hands come up in front of his face, looks around
def tongue_z(x, y):
    return 0.55 * math.exp(-(x / 2.2) ** 2) * (0.6 + 0.4 * math.cos(min(1, abs(y) / 4.5) * math.pi / 2)) + 0.06 * math.sin(x * 2.1) * math.sin(y * 1.7) + 0.35 * (abs(x) / 3.5) ** 3
sid = "2"; whale_park(F[sid][0])
for fr in frames(sid, 3):
    t = T(sid, fr)
    up = ease(min(1, t * 1.4))
    pos = MOUTH + Vector((0, -0.4, tongue_z(0, -0.4) + 0.13 + 0.04 * up))
    M = M_of(pos, yaw=0, pitch=-90 + 25 * up)                 # lying on his back, head toward the throat, torso lifting
    D.key_body(fr, M); D.key_spine(fr, flex=8 * up, head=(18 * up + 6 * math.sin(t * 5), 28 * math.sin(t * 3.2)))
    for s in "LR":
        sx = 1 if s == "L" else -1; a_ = D.rest_ankle(s)
        D.key_foot(s, fr, M, Vector((a_.x + sx * 0.05, a_.y + 0.05, a_.z)), pitch=0, knee_dir=Vector((0, -1, 0)))
        sh = D.shoulder(s)
        hand = sh.lerp(sh + Vector((sx * 0.12, -0.45, -0.05)), 1.0)
        D.key_hand(s, fr, M, lerp(sh + Vector((sx * 0.15, -0.12, -0.45)), sh + Vector((sx * 0.14, -0.48, 0.02)), up),
                   Vector((0, 1, 0)), Vector((0, -0.2, 1)), sh + Vector((sx * 0.35, 0.1, -0.3)))
for s in "LR": D.hand_pose(s, F[sid][0], "relaxed"); D.hand_pose(s, F[sid][0] + 40, "open_alarm")
camera(sid, [(0, MOUTH + Vector((0.9, -1.9, 2.0)), MOUTH + Vector((0, 0.3, 0.8))), (1, MOUTH + Vector((0.7, -1.6, 1.85)), MOUTH + Vector((0, 0.4, 0.9)))], lens=28)

# 3a: imagined great white swims straight at camera, mouth wide
sid = "3a"
for fr in frames(sid):
    t = T(sid, fr); key_shark(fr, UNDER + Vector((0, 30 - 10 * t, 2)), yaw=0, wig=t * 9)
camera(sid, [(0, UNDER + Vector((0, -16, 4.5)), UNDER + Vector((0, 20, 3))), (1, UNDER + Vector((0, -20, 4.2)), UNDER + Vector((0, 14, 3)))], lens=30)
D.park(F[sid][0])

# 3b/3c: the diver inside the open shark jaw (imagined): standing small in the mouth, hands up
SB = bpy.data.objects["Shark_body"]
def shark_mouth_world(fr):
    """floor of the open mouth: from the evaluated mesh, the front 2.5 m of the head"""
    sc.frame_set(fr); dg = bpy.context.evaluated_depsgraph_get(); ev_ = SB.evaluated_get(dg); Mw = ev_.matrix_world
    vs = [Mw @ v.co for v in ev_.data.vertices]; ymin = min(v.y for v in vs); fr_ = [v for v in vs if v.y < ymin + 2.5]
    cx = sum(v.x for v in fr_) / len(fr_); zmin = min(v.z for v in fr_)
    return Vector((cx, ymin + 1.45, zmin + 1.2)), None
for sid, cam_keys, lens in (("3b", [(0, UNDER + Vector((0, -12, 3.4)), UNDER + Vector((0, 0, 1.6))), (1, UNDER + Vector((0, -9.5, 3.0)), UNDER + Vector((0, 0, 1.7)))], 32),
                            ("3c", [(0, UNDER + Vector((-7, -8, 0.2)), UNDER + Vector((0, 0, 1.8))), (1, UNDER + Vector((-5, -9, 0.6)), UNDER + Vector((0, 0, 1.8)))], 30)):
    for fr in frames(sid):
        t = T(sid, fr); key_shark(fr, UNDER + Vector((0, 8.0 - 0.6 * t, -0.6)), yaw=0, wig=t * 4)
    for fr in frames(sid, 4):
        t = T(sid, fr); jt, hh = shark_mouth_world(fr)
        base = jt
        M = M_of(base + Vector((0, 0, D.root_head.z)), yaw=0 + (25 * math.sin(t * 3) if sid == "3c" else 0))
        D.key_body(fr, M); D.key_spine(fr, flex=-4, head=(-12, 30 * math.sin(t * 3.5) if sid == "3c" else 0))
        legs_stand(D, fr, M, spread=0.06)
        for s in "LR":
            sx = 1 if s == "L" else -1; sh = D.shoulder(s); k = 0.04 * math.sin(t * 8 + sx)
            D.key_hand(s, fr, M, sh + Vector((sx * 0.30, -0.15, 0.32 + k)), Vector((0, 1, 0.2)), Vector((sx * 0.3, 0, 1)), sh + Vector((sx * 0.45, 0.15, -0.05)))
    for s in "LR": D.hand_pose(s, F[sid][0], "open_alarm")
    camera(sid, cam_keys, lens)

# 4a/4b: the humpback underwater
D.park(F["4a"][0]); D.park(F["11a"][0])
sid = "4a"
for fr in frames(sid):
    t = T(sid, fr); key_whale(fr, UNDER + Vector((14 - 9 * t, 0, 0)), (0, 0, 0), swim=1.2 * t, amp=1.0)
key_shark(F[sid][0], UNDER + Vector((0, 300, -150)))
camera(sid, [(0, UNDER + Vector((10, -26, -1)), UNDER + Vector((10, 0, 0))), (1, UNDER + Vector((5, -26, -0.5)), UNDER + Vector((5, 0, 0)))], lens=26)
sid = "4b"
for fr in frames(sid):
    t = T(sid, fr); key_whale(fr, UNDER + Vector((4 - 4 * t, 0, 0)), (0, -3, -8 + 4 * t), jaw=2 * math.sin(t * 6) ** 2, swim=1.3 + 1.0 * t, amp=0.9)
camera(sid, [(0, UNDER + Vector((-9, -13, 1.0)), UNDER + Vector((-2.5, 0, 0.6))), (1, UNDER + Vector((-12, -14, 0.6)), UNDER + Vector((-5.5, 0, 0.6)))], lens=30)

# 5a/5b/5c: inside the mouth, he gets up and pushes at the baleen wall
def stand_in_mouth(fr, x, y, yaw, crouch, lean):
    z = tongue_z(x, y) + D.root_head.z - crouch
    return M_of(MOUTH + Vector((x, y, z)), yaw=yaw, pitch=lean)
sid = "5a"; whale_park(F[sid][0])
for fr in frames(sid, 3):
    t = T(sid, fr); M = stand_in_mouth(fr, 0.2, 0.3, 160 + 40 * math.sin(t * 2.5), 0.18, 12)
    D.key_body(fr, M); D.key_spine(fr, flex=10, head=(-15 + 10 * math.sin(t * 4), 35 * math.sin(t * 3)))
    for s in "LR":
        sx = 1 if s == "L" else -1; a_ = D.rest_ankle(s)
        D.key_foot(s, fr, M, Vector((a_.x + sx * 0.12, a_.y + (0.12 if s == "L" else -0.1), a_.z + 0.18 - 0.0)), knee_dir=Vector((sx * 0.3, -1, 0)))
    arms_hang(D, fr, M, swing=0.05 * math.sin(t * 5), out=0.08)
for s in "LR": D.hand_pose(s, F[sid][0], "relaxed")
camera(sid, [(0, MOUTH + Vector((0.6, 3.6, 2.6)), MOUTH + Vector((0, -0.5, 1.0))), (1, MOUTH + Vector((0.4, 2.8, 2.3)), MOUTH + Vector((0.1, -0.2, 1.0)))], lens=24)
for sid, side in (("5b", 1), ("5c", -1)):
    wall_x = side * 2.63
    for fr in frames(sid, 3):
        t = T(sid, fr); push = 0.5 + 0.5 * math.sin(t * 2 * math.pi * 2.2)
        x = side * (1.85 - 0.06 * push)
        M = stand_in_mouth(fr, x, 0.0, 90 * side, 0.22, 20 + 6 * push)
        D.key_body(fr, M); D.key_spine(fr, flex=12 + 6 * push, head=(-8 - (14 * t if sid == "5c" else 0), (-25 * side * t if sid == "5c" else 0)))
        for s in "LR":
            sx = 1 if s == "L" else -1; a_ = D.rest_ankle(s)
            D.key_foot(s, fr, M, Vector((a_.x + sx * 0.05, a_.y + (0.28 if s == "L" else -0.18), a_.z + 0.22)), knee_dir=Vector((0, -1, 0.2)))
        # palms flat on the baleen plates (world x = wall), at shoulder height
        Minv = M.inverted()
        for s in "LR":
            sx = 1 if s == "L" else -1
            pw = Vector((MOUTH.x + wall_x, MOUTH.y + sx * 0.28 * side, MOUTH.z + 1.35 + 0.03 * push))
            pl = Minv @ pw
            D.key_hand(s, fr, M, pl, Minv.to_3x3() @ Vector((side, 0, 0)), Minv.to_3x3() @ Vector((0, 0, 1)), D.shoulder(s) + Vector((sx * 0.35, 0.1, -0.35)))
    for s in "LR": D.hand_pose(s, F[sid][0], "flat_palm")
cx = 1
camera("5b", [(0, MOUTH + Vector((-0.6, -2.6, 1.7)), MOUTH + Vector((1.7, 0, 1.15))), (1, MOUTH + Vector((-0.4, -2.2, 1.6)), MOUTH + Vector((1.7, 0.1, 1.15)))], lens=26)
camera("5c", [(0, MOUTH + Vector((0.8, 2.5, 1.3)), MOUTH + Vector((-1.6, 0, 1.4))), (1, MOUTH + Vector((0.6, 2.2, 1.0)), MOUTH + Vector((-1.6, -0.4, 1.8)))], lens=26)

# 6a: the whale's head bursts up through the surface
sid = "6a"
for fr in frames(sid):
    t = T(sid, fr); key_whale(fr, OCEAN + Vector((0, 0, lerp(-9, -3.6, ease(t)))), (0, 55, 90), jaw=0, swim=0.3 * t, amp=0.5)
D.park(F[sid][0])
key_fx(SPL, F[sid][0], OCEAN + Vector((-1.5, 0, -0.5)), (2, 2, 1)); key_fx(SPL, F[sid][1], OCEAN + Vector((-1.5, 0, -0.5)), (6, 6, 3.5))
key_fx(RING, F[sid][0], OCEAN + Vector((-1.5, 0, 0.05)), (2.5, 2.5, 1)); key_fx(RING, F[sid][1], OCEAN + Vector((-1.5, 0, 0.05)), (5, 5, 1))
camera(sid, [(0, OCEAN + Vector((-3, -16, 1.0)), OCEAN + Vector((0, -2, 2.0))), (1, OCEAN + Vector((-3, -15, 1.2)), OCEAN + Vector((0, -2.5, 3.0)))], lens=30)

# 6b: jaws open, the diver is thrown out in a short arc and splashes down
sid = "6b"
for fr in frames(sid):
    t = T(sid, fr); key_whale(fr, OCEAN + Vector((0, 0, -3.6 - 1.5 * t)), (0, 55 - 10 * t, 90), jaw=lerp(0, 35, ease(min(1, t * 3))), swim=0.4 + 0.3 * t, amp=0.5)
sc.frame_set(round(lerp(*F[sid], 0.2))); start = ((W.matrix_world @ W.pose.bones["jaw"].tail) + (W.matrix_world @ W.pose.bones["head"].tail)) / 2
land = OCEAN + Vector((-9.5, -1.0, -0.3))
for fr in frames(sid, 2):
    t = T(sid, fr); u = max(0.0, min(1.0, (t - 0.18) / 0.62))
    p = start.lerp(land, u) + Vector((0, 0, 4.2 * math.sin(math.pi * u) if u < 1 else 0))
    if u >= 1: p = land + Vector((0, 0, -1.2 * min(1, (t - 0.8) / 0.2)))
    M = M_of(p + Vector((0, 0, 0)), yaw=-90, pitch=-30 - 140 * u, roll=10)
    D.key_body(fr, M); D.key_spine(fr, flex=15, head=(10, 0))
    for s in "LR":
        sx = 1 if s == "L" else -1; a_ = D.rest_ankle(s); sh = D.shoulder(s)
        D.key_foot(s, fr, M, Vector((a_.x + sx * 0.08, a_.y - 0.25, a_.z + 0.25)), knee_dir=Vector((0, -1, 0)))
        D.key_hand(s, fr, M, sh + Vector((sx * 0.55, -0.15, 0.05 + 0.08 * math.sin(t * 12 + sx))), Vector((0, 0, -1)), Vector((sx, 0, 0)), sh + Vector((sx * 0.3, 0.25, -0.1)))
for s in "LR": D.hand_pose(s, F[sid][0], "open_alarm")
key_fx(SPL, F[sid][0], OCEAN + Vector((-1.5, 0, -0.5)), (6, 6, 3)); key_fx(SPL, round(lerp(*F[sid], 0.79)), OCEAN + Vector((-1.5, 0, -0.5)), (7, 7, 1.5))
key_fx(SPL, round(lerp(*F[sid], 0.8)), land + Vector((0, 0, -0.2)), (0.6, 0.6, 0.6)); key_fx(SPL, F[sid][1], land + Vector((0, 0, -0.2)), (1.6, 1.6, 1.8))
key_fx(RING, F[sid][0], OCEAN + Vector((-1.5, 0, 0.05)), (5, 5, 1)); key_fx(RING, F[sid][1], OCEAN + Vector((-1.5, 0, 0.05)), (7, 7, 1))
camera(sid, [(0, OCEAN + Vector((-5, -24, 3.2)), OCEAN + Vector((-5, 0, 3.5))), (1, OCEAN + Vector((-6, -23, 2.6)), OCEAN + Vector((-6.5, 0, 2.0)))], lens=26)

# 6c / 13: treading water at the surface
def tread(sid, pos, cam_keys, lens, look=(0.0, 0.0)):
    for fr in frames(sid, 3):
        t = T(sid, fr); bob = 0.05 * math.sin(t * 2 * math.pi * 1.6)
        M = M_of(pos + Vector((0, 0, bob)), yaw=look[0] * math.sin(t * 2.0), pitch=8)
        D.key_body(fr, M); D.key_spine(fr, flex=4, head=(-6 + look[1] * t, 20 * math.sin(t * 2.6)))
        for s in "LR":
            sx = 1 if s == "L" else -1; a_ = D.rest_ankle(s); sh = D.shoulder(s); k = math.sin(t * 2 * math.pi * 1.6 + (0 if s == "L" else math.pi))
            D.key_foot(s, fr, M, Vector((a_.x + sx * 0.1, a_.y + 0.15 * k, a_.z + 0.15 + 0.08 * k)), knee_dir=Vector((0, -1, 0)))
            D.key_hand(s, fr, M, sh + Vector((sx * (0.42 + 0.12 * k), -0.25, -0.38)), Vector((0, 0, -1)), Vector((sx * 0.4, -1, 0)), sh + Vector((sx * 0.45, 0.2, -0.25)))
    for s in "LR": D.hand_pose(s, F[sid][0], "relaxed")
    camera(sid, cam_keys, lens)
sid = "6c"
for fr in frames(sid):
    t = T(sid, fr); key_whale(fr, OCEAN + Vector((4, 6, lerp(-5.5, -9, t))), (0, 10, 60), swim=0.7 + 0.4 * t, amp=0.6)
key_fx(RING, F[sid][0], OCEAN + Vector((-9.5, -0.2, 0.08)), (1.6, 1.6, 1)); key_fx(RING, F[sid][1], OCEAN + Vector((-9.5, -0.2, 0.08)), (2.6, 2.6, 1))
tread(sid, OCEAN + Vector((-9.5, -1.0, -0.26)), [(0, OCEAN + Vector((-9.2, -2.9, 0.75)), OCEAN + Vector((-9.5, -1.0, 0.55))), (1, OCEAN + Vector((-9.1, -2.6, 0.7)), OCEAN + Vector((-9.5, -1.0, 0.55)))], 34, look=(15, 0))

# 7a..10: hospital. The diver sits up on the bed, legs on the mattress
bed = bpy.data.objects["Bed"]
def mattress_z(x, y):
    dg = bpy.context.evaluated_depsgraph_get(); be = bed.evaluated_get(dg); inv = bed.matrix_world.inverted()
    hit, loc, nrm, idx = be.ray_cast(inv @ Vector((x, y, 3.0)), inv.to_3x3() @ Vector((0, 0, -1)))
    print('MATTRESS hit', hit); return (bed.matrix_world @ loc).z if hit else 0.55
_bb = [bed.matrix_world @ Vector(c) for c in bed.bound_box]; BX = sum(c.x for c in _bb) / 8; BY = sum(c.y for c in _bb) / 8
sit_y = BY + 0.55; mz = mattress_z(BX, sit_y)
print("MATTRESS z", mz)
def sit(fr, lean=-12.0, knee_up=0.0, turn=0.0, head=(0.0, 0.0), hand_rib=0.0, hand_thigh=0.0):
    pos = Vector((BX - 0.05, sit_y, mz + 0.10))
    M = M_of(pos, yaw=0, pitch=lean)                      # faces -Y (toward the room), seated: legs forward along -Y
    D.key_body(fr, M); D.key_spine(fr, flex=8, twist=turn, head=head)
    for s in "LR":
        sx = 1 if s == "L" else -1
        # legs forward on the mattress: ankles ~0.85 m in front of the pelvis
        up = knee_up if s == "L" else 0.0
        ank_w = Vector((BX - 0.05 + sx * 0.10, sit_y - 0.88 + 0.30 * up, mz + 0.07 + 0.05 * up))
        Ml = M.inverted()
        D.key_foot(s, fr, M, Ml @ ank_w, pitch=-75, knee_dir=Vector((0, -0.3, 1)))
    return M
def hosp_arms(fr, M, rib=0.0, thigh_L=0.0, t=0.0):
    Ml = M.inverted()
    for s in "LR":
        sx = 1 if s == "L" else -1; sh = D.shoulder(s)
        # resting hand on the mattress beside the hip
        bed_pt = Vector((BX - 0.05 + sx * 0.34, sit_y - 0.12, mz + 0.03))
        p = Ml @ bed_pt
        D.key_hand(s, fr, M, p, Ml.to_3x3() @ Vector((0, 0, -1)), Ml.to_3x3() @ Vector((0, -1, 0)), sh + Vector((sx * 0.3, 0.3, -0.3)))
def thigh_hand(fr, M, s, frac=0.55):
    """left hand on the thigh above the knee (body-local), palm down"""
    sx = 1 if s == "L" else -1; sh = D.shoulder(s)
    hip = D.r.BN["upperleg01." + s].head_local - D.root_head; knee = D.r.BN["lowerleg01." + s].head_local - D.root_head
    sc.frame_set(fr)
    hipw = D.o.matrix_world @ D.o.pose.bones["upperleg01." + s].head; kneew = D.o.matrix_world @ D.o.pose.bones["lowerleg01." + s].head
    pw = hipw.lerp(kneew, frac) + Vector((0, 0, 0.09))
    Ml = M.inverted()
    D.key_hand(s, fr, M, Ml @ pw, Ml.to_3x3() @ Vector((0, 0, -1)), Ml.to_3x3() @ (kneew - hipw).normalized(), sh + Vector((sx * 0.3, 0.25, -0.35)))
whale_park(F["7a"][0])
for sid in ("7a", "7b", "8a", "8b", "9", "10"):
    for fr in frames(sid, 3):
        t = T(sid, fr); br = math.sin(t * 2 * math.pi * 1.2)
        if sid == "7a": M = sit(fr, lean=-10 + 1.5 * br, head=(-18 + 6 * t, -15 + 10 * t))
        elif sid == "7b": M = sit(fr, lean=-10 + 1.5 * br, turn=-8 * t, head=(-8, -10 - 25 * ease(t)))
        elif sid in ("8a", "8b"): M = sit(fr, lean=-6 + 1.5 * br, knee_up=0.45 if sid == "8a" else 0.45 - 0.15 * math.sin(t * math.pi), head=(-26, 8))
        else: M = sit(fr, lean=-12 + 1.5 * br, head=(-10, 20 * math.sin(t * 2)))
        hosp_arms(fr, M)
    for s in "LR": D.hand_pose(s, F[sid][0], "relaxed")
    if sid in ("8a", "8b"):
        for fr in frames(sid, 3): thigh_hand(fr, sit(fr, lean=-6, knee_up=0.45 if sid == "8a" else 0.45 - 0.15 * math.sin(T(sid, fr) * math.pi), head=(-26, 8)), "L")
cy = sit_y
camera("7a", [(0, HOSP + Vector((0.35, cy - 2.4, 1.6)), Vector((BX, cy, mz + 0.6))), (1, HOSP + Vector((0.3, cy - 2.0, 1.6)), Vector((BX, cy, mz + 0.65)))], lens=30)
camera("7b", [(0, HOSP + Vector((-0.9, cy - 1.3, 1.45)), Vector((BX, cy, mz + 0.75))), (1, HOSP + Vector((-0.7, cy - 1.25, 1.45)), Vector((BX, cy, mz + 0.78)))], lens=32)
def knee_w(sid):
    sc.frame_set((F[sid][0] + F[sid][1]) // 2); return D.o.matrix_world @ D.o.pose.bones["lowerleg01.L"].head
k8 = knee_w("8a")
camera("8a", [(0, k8 + Vector((0.75, -0.55, 0.55)), k8 + Vector((-0.05, 0.12, -0.02))), (1, k8 + Vector((0.65, -0.48, 0.5)), k8 + Vector((-0.05, 0.12, -0.02)))], lens=35)
k8 = knee_w("8b")
camera("8b", [(0, k8 + Vector((0.42, -0.36, 0.32)), k8 + Vector((0, 0.02, -0.02))), (1, k8 + Vector((0.38, -0.32, 0.3)), k8 + Vector((0, 0.02, -0.02)))], lens=40)
camera("9", [(0, HOSP + Vector((1.2, -3.6, 1.7)), Vector((BX - 0.2, cy - 0.5, 0.9))), (1, HOSP + Vector((0.4, -3.6, 1.7)), Vector((BX - 0.2, cy - 0.5, 0.9)))], lens=26)
camera("10", [(0, HOSP + Vector((0.0, -2.9, 1.45)), Vector((BX, cy, 1.05))), (1, HOSP + Vector((0.0, -2.5, 1.40)), Vector((BX, cy, 1.05)))], lens=28)

# doctors: walk in during 9, stand doubtful in 10 (no arm crosses a face; arms hang or rest)
for A in (DM, DF): A.park(F["1a"][0])
docs = {DM: (Vector((HOSP.x + 0.75, cy - 1.9, 0)), 285), DF: (Vector((HOSP.x - 0.75, cy - 1.9, 0)), 75)}
sid = "9"
for A, (end, yaw_end) in docs.items():
    start = end + Vector((2.6, -0.6, 0))
    path = lambda fr, s_=start, e_=end: s_.lerp(e_, ease(T("9", fr)))
    yaw_fn = lambda fr, s_=start, e_=end: math.degrees(math.atan2(-(e_ - s_).x, (e_ - s_).y)) + 180 * 0
    A.h.walk(path, lambda fr: -90.0, F[sid][0], F[sid][1], stride=0.7)
    for fr in frames(sid, 4):
        sc.frame_set(fr); Mr = A.o.matrix_world @ A.o.pose.bones["root"].matrix
        Mb = Matrix.Translation(Mr.translation) @ Matrix.Rotation(R_(-90), 4, 'Z')
        t = T(sid, fr)
        for s in "LR":
            sx = 1 if s == "L" else -1; sh = A.shoulder(s); sw = 0.12 * math.sin(t * 2 * math.pi * 2.2 + (0 if s == "L" else math.pi))
            A.key_hand(s, fr, Mb, sh + Vector((sx * 0.1, sw, -0.58)), Vector((-sx, 0, 0)), Vector((0, 0, -1)), sh + Vector((sx * 0.25, 0.35, -0.3)))
        A.key_spine(fr, flex=3, head=(-4, -20))
    for s in "LR": A.hand_pose(s, F[sid][0], "relaxed")
sid = "10"
for A, (end, yaw_end) in docs.items():
    for fr in frames(sid, 4):
        t = T(sid, fr); br = 0.006 * math.sin(t * 2 * math.pi * 1.1)
        M = M_of(end + Vector((0, 0, A.root_head.z + br)), yaw=yaw_end)
        A.key_body(fr, M); legs_stand(A, fr, M)
        if A is DM: A.key_spine(fr, flex=2, twist=-6, head=(-6 + 4 * math.sin(t * 6), (-25 if t < 0.45 else 25 * math.sin((t - 0.45) * 7))))
        else: A.key_spine(fr, flex=2, side=4 * ease(t), head=(-4, 25 if t < 0.5 else -15))
        arms_hang(A, fr, M, swing=0.0, out=0.04)
    for s in "LR": A.hand_pose(s, F[sid][0], "relaxed")
for A in (DM, DF): A.park(F["11a"][0])

# 11a/11b: whale calmly gliding through a fish school
fish_mat = fx_material("Fish", (0.75, 0.85, 0.95), 0.15)
bm = bmesh.new()
for i in range(140):
    c0 = Vector((random.gauss(0, 2.2), random.gauss(0, 1.4), random.gauss(0, 1.0)))
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.2, matrix=Matrix.Translation(c0) @ Matrix.Diagonal((1.0, 0.28, 0.45, 1)))
    tv = [bm.verts.new(c0 + Vector(d)) for d in ((0.16, 0, 0), (0.32, 0, 0.1), (0.32, 0, -0.1))]; bm.faces.new(tv)
fm = bpy.data.meshes.new("FishSchool"); bm.to_mesh(fm); bm.free(); fish = bpy.data.objects.new("FishSchool", fm); sc.collection.objects.link(fish); fm.materials.append(fish_mat)
for sid in order: key_vis(fish, F[sid][0], False)
def key_fish(fr, loc, rot=0.0):
    fish.location = loc; fish.rotation_euler = (0, 0, R_(rot)); fish.keyframe_insert("location", frame=fr); fish.keyframe_insert("rotation_euler", frame=fr)
sid = "11a"
for fr in frames(sid):
    t = T(sid, fr); key_whale(fr, UNDER + Vector((16 - 10 * t, 2, -1)), (0, 0, 0), swim=2.0 + 1.2 * t, amp=1.0)
    key_fish(fr, UNDER + Vector((-2 - 3 * t, -1.5, 2.2)), 10 * t)
camera(sid, [(0, UNDER + Vector((8, -22, 0.5)), UNDER + Vector((6, 0, -0.5))), (1, UNDER + Vector((4, -22, 0.8)), UNDER + Vector((2, 0, -0.5)))], lens=28)
sid = "11b"
for fr in frames(sid):
    t = T(sid, fr); key_whale(fr, UNDER + Vector((3 - 3.5 * t, 2, -1)), (0, 0, -12 + 6 * t), swim=3.2 + 1.0 * t, amp=0.9)
    key_fish(fr, UNDER + Vector((-6 - 2 * t, -1.0, 1.8)), 20 + 10 * t)
camera(sid, [(0, UNDER + Vector((-12, -11, 1.5)), UNDER + Vector((-4, 1, -0.6))), (1, UNDER + Vector((-13, -12, 1.2)), UNDER + Vector((-6, 1, -0.6)))], lens=30)
# 12a/12b: the lunge for fish (no man)
D.park(F["12a"][0])
sid = "12a"; whale_breach(sid, 0.0, 1.0, -6.0, -2.6, 40, 40, tilt=6, x=2.0, sw0=1.0)
key_fx(SPL, F[sid][0], OCEAN + Vector((1, 0, -0.5)), (4, 4, 2.5)); key_fx(SPL, F[sid][1], OCEAN + Vector((1, 0, -0.5)), (7, 7, 4))
key_fx(RING, F[sid][0], OCEAN + Vector((1, 0, 0.05)), (3.5, 3.5, 1)); key_fx(RING, F[sid][1], OCEAN + Vector((1, 0, 0.05)), (6, 6, 1))
camera(sid, [(0, OCEAN + Vector((-2, -16, 1.4)), OCEAN + Vector((2, 0, 2.5))), (1, OCEAN + Vector((-1, -14, 1.8)), OCEAN + Vector((2, 0, 4.0)))], lens=30)
sid = "12b"; whale_breach(sid, 0.0, 1.0, -2.6, -2.0, 40, 4, tilt=8, x=2.0, sw0=1.4)
key_fx(SPL, F[sid][0], OCEAN + Vector((1, 0, -0.5)), (7, 7, 4)); key_fx(SPL, F[sid][1], OCEAN + Vector((1, 0, -0.5)), (9, 9, 3))
key_fx(RING, F[sid][0], OCEAN + Vector((1, 0, 0.05)), (6, 6, 1)); key_fx(RING, F[sid][1], OCEAN + Vector((1, 0, 0.05)), (8, 8, 1))
camera(sid, [(0, OCEAN + Vector((9, -9, 3.0)), OCEAN + Vector((2, -0.5, 4.2))), (1, OCEAN + Vector((8, -8, 3.2)), OCEAN + Vector((2, -0.5, 4.0)))], lens=30)
# 13: the diver at the surface, calm, looks at camera
sid = "13"; whale_park(F[sid][0])
tread(sid, OCEAN + Vector((0, 0, -0.26)), [(0, OCEAN + Vector((0.25, -2.0, 0.7)), OCEAN + Vector((0, 0, 0.55))), (1, OCEAN + Vector((0.18, -1.6, 0.66)), OCEAN + Vector((0, 0, 0.58)))], 36, look=(8, 0))

# ---------------------------------------------------------------- bruises (hospital only): vertex attribute mask + keyed mix
body = bpy.data.objects["Diver.body"]
BNd = D.o.data.bones
def bone_pt(n, u=0.0): b = BNd[n]; return b.head_local.lerp(b.tail_local, u)
spots = [(bone_pt("head", 0.35) + Vector((0.075, -0.075, -0.02)), 0.045),       # left cheek (character's left = +X)
         (bone_pt("spine03", 0.6) + Vector((0.09, -0.11, 0.02)), 0.07),         # left chest
         (bone_pt("lowerleg01.L", 0.0) + Vector((0.0, -0.05, 0.0)), 0.065)]      # left knee
me = body.data
at = me.attributes.get("bruise") or me.attributes.new("bruise", 'FLOAT', 'POINT')
for v in me.vertices:
    val = 0.0
    for c_, r_ in spots:
        d = (v.co - c_).length; val = max(val, max(0.0, 1 - (d / r_) ** 2))
    at.data[v.index].value = val
for m in body.data.materials:
    nt = m.node_tree; N = nt.nodes; out = next(n for n in N if n.type == 'OUTPUT_MATERIAL')
    lk = next(l for l in nt.links if l.to_node == out and l.to_socket.name == "Surface"); src = lk.from_socket; nt.links.remove(lk)
    attr = N.new('ShaderNodeAttribute'); attr.attribute_name = "bruise"
    amt = N.new('ShaderNodeMath'); amt.operation = 'MULTIPLY'; amt.name = "BruiseAmount"; amt.inputs[1].default_value = 0.0
    nt.links.new(attr.outputs['Fac'] if 'Fac' in attr.outputs else attr.outputs[2], amt.inputs[0])
    bp = N.new('ShaderNodeBsdfPrincipled'); bp.inputs['Base Color'].default_value = (0.32, 0.07, 0.30, 1); bp.inputs['Roughness'].default_value = 0.45
    mx = N.new('ShaderNodeMixShader'); nt.links.new(amt.outputs[0], mx.inputs[0]); nt.links.new(src, mx.inputs[1]); nt.links.new(bp.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs['Surface'])
    for sid in order:
        amt.inputs[1].default_value = 0.75 if SETS[sid] == "H" else 0.0
        amt.inputs[1].keyframe_insert("default_value", frame=F[sid][0])

# ---------------------------------------------------------------- shot metadata, constant visibility keys, save
for o in bpy.data.objects: constant_keys(o)
def shot_of(fr):
    for i, sid_ in enumerate(order):
        if F[sid_][0] <= fr <= F[sid_][1]: return i
    return -1
ncut = 0
for act in bpy.data.actions:
    for fc in _fcurves(act):
        kp = fc.keyframe_points
        for i in range(len(kp) - 1):
            if shot_of(round(kp[i].co.x)) != shot_of(round(kp[i + 1].co.x)): kp[i].interpolation = 'CONSTANT'; ncut += 1
for m in bpy.data.materials:
    if m.node_tree and m.node_tree.animation_data and m.node_tree.animation_data.action:
        for fc in _fcurves(m.node_tree.animation_data.action):
            for k in fc.keyframe_points: k.interpolation = 'CONSTANT'
print("BOUNDARY constant keys", ncut)
for sid in order:
    c = CAMS[sid]; c["shot"] = sid; c["clip_start"] = F[sid][0]; c["clip_end"] = F[sid][1]; c["set"] = SETS[sid]
sc.camera = CAMS[order[0]]
json.dump({sid: F[sid] for sid in order}, open(os.path.join(os.path.dirname(OUT), "clips.json"), "w"), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("ANIM_DONE", OUT, sc.frame_end)
