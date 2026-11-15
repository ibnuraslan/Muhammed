# SodaMouse animation helpers (exec'd after pipeline/anim_lib.py + pipeline/hand_poses.py)
import bpy, math
from mathutils import Vector, Matrix, Quaternion
R = math.radians
sc = bpy.context.scene

def ground_z(x, y): return 0.0          # flat floors in both sets
globals()["ground_z"] = ground_z

class Man:
    """thin wrapper: one MPFB rig (object at origin), world == armature space"""
    def __init__(self, name):
        self.o = bpy.data.objects[name]; self.o.location = (0, 0, 0)
        if self.o.animation_data is None: self.o.animation_data_create()
        if self.o.animation_data.action is None:
            self.o.animation_data.action = bpy.data.actions.new(name + "Action")
        for pb in self.o.pose.bones: pb.rotation_mode = 'QUATERNION'
        self.r = Rig(self.o); self.h = Human(self.r)
        self.hip = self.h.root_head.copy()
    def stand(self, f, xy, yaw=0.0, crouch=0.0, flex=0.0, side=0.0, stance=1.0):
        """root over xy, both feet planted under the hips (yaw deg, 0 = facing -Y)"""
        p = Vector((xy[0], xy[1], self.hip.z - crouch))
        self.h.key_root(f, p, yaw=yaw, flex=flex, side=side)
        for s in "LR":
            fx = self.h.foot_xy(s, p, yaw); c = Vector((xy[0], xy[1]))
            fx = c + (fx - c) * stance
            self.h.key_foot(s, f, fx, yaw)
    def spine(self, f, flex=0.0, twist=0.0, side=0.0, pitch=0.0, turn=0.0):
        self.h.key_spine(f, flex=flex, twist=twist, side=side, head=(pitch, turn))
    def jaw(self, f, deg):
        self.r.key_rot("jaw", f, [("X", deg)])
    def eyes(self, f, yaw=0.0, pitch=0.0):
        for s in "LR": self.r.key_rot("eye." + s, f, [("X", pitch), ("Z", yaw)])
    def hand(self, s, f, W, d, n, pole=None):
        self.h.key_hand(s, f, Vector(W), Vector(d), Vector(n), pole=None if pole is None else Vector(pole))
    def hang(self, s, f, yaw=0.0, out=0.0, fwd=0.0, pose="relaxed", lift=0.0):
        """relaxed arm hanging at the side, slight elbow bend, palm toward the thigh"""
        sx = 1 if s == "L" else -1
        B = self.r.BN; sh = B["upperarm01." + s].head_local
        root = self.r.PB["root"]
        M = self.o.matrix_world.inverted() @ (self.o.matrix_world @ root.matrix) @ self.r.rest("root").inverted()
        W = M @ Vector((sh.x + sx * (0.10 + out), sh.y + 0.03 - fwd, sh.z - 0.58 + lift))
        Rz = M.to_3x3()
        self.h.key_hand(s, f, W, Rz @ Vector((0.0, -0.08 - fwd, -1)), Rz @ Vector((-sx, 0, 0)),
                        pole=M @ Vector((sh.x + sx * 0.35, sh.y + 0.6, sh.z - 0.25)))
        apply_pose(self.o, s, pose, f)
    def wrist_world(self, s):
        return self.o.matrix_world @ self.r.PB["wrist." + s].matrix

def key_obj(o, f, loc=None, rot=None, scale=None):
    if loc is not None: o.location = loc; o.keyframe_insert("location", frame=f)
    if rot is not None: o.rotation_mode = 'XYZ'; o.rotation_euler = rot; o.keyframe_insert("rotation_euler", frame=f)
    if scale is not None: o.scale = scale; o.keyframe_insert("scale", frame=f)

def key_matrix(o, f, M):
    o.matrix_basis = M; o.rotation_mode = 'XYZ'
    o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_euler", frame=f); o.keyframe_insert("scale", frame=f)

def vis(o, f, on):
    for ob in [o] + [c for c in o.children_recursive if not c.name.startswith("MouseTailTip")]:
        ob.hide_render = not on; ob.hide_viewport = not on
        ob.keyframe_insert("hide_render", frame=f); ob.keyframe_insert("hide_viewport", frame=f)

class Held:
    """prop carried in a hand: Child Of wrist bone. grab() at f makes the prop follow the wrist from f with no jump;
    to_hand_target(C) gives the wrist world matrix that puts the prop at world matrix C."""
    def __init__(self, prop, man, side):
        self.p, self.m, self.s = prop, man, side; self.rel = None; self.cons = []
    def grab(self, f):
        sc.frame_set(f); W = self.m.wrist_world(self.s); P = self.p.matrix_world.copy()
        c = self.p.constraints.new('CHILD_OF'); c.name = "Hold%d" % f; c.target = self.m.o; c.subtarget = "wrist." + self.s
        c.inverse_matrix = W.inverted()
        # with inverse = W^-1 and basis = P (world, no parent) the result at f is W W^-1 P = P
        self.rel = P.inverted() @ W
        c.influence = 0.0; c.keyframe_insert("influence", frame=f - 1); c.influence = 1.0; c.keyframe_insert("influence", frame=f)
        for o in self.cons: o.influence = 0.0; o.keyframe_insert("influence", frame=f)
        self.cons.append(c); self._set_const(c)
        key_matrix(self.p, f, P)                    # basis frozen while held
        return c
    def wrist_for(self, C):
        return C @ self.rel
    def release(self, f):
        sc.frame_set(f); P = self.p.matrix_world.copy(); c = self.cons[-1]
        key_matrix(self.p, f - 1, self.p.matrix_basis.copy())
        c.influence = 1.0; c.keyframe_insert("influence", frame=f - 1); c.influence = 0.0; c.keyframe_insert("influence", frame=f)
        self._set_const(c); key_matrix(self.p, f, P); self._const_obj(f)
    def _set_const(self, c):
        ad = self.p.animation_data
        if ad and ad.action:
            for fc in ad.action.fcurves if hasattr(ad.action, "fcurves") else []:
                if fc.data_path.startswith('constraints["%s"]' % c.name):
                    for k in fc.keyframe_points: k.interpolation = 'CONSTANT'
    def _const_obj(self, f):
        pass

def all_fcurves(o):
    ad = o.animation_data
    if not ad or not ad.action: return []
    act = ad.action
    if hasattr(act, "fcurves"): return list(act.fcurves)
    out = []
    for layer in act.layers:
        for strip in layer.strips:
            for bag in strip.channelbags: out += list(bag.fcurves)
    return out

def hand_target(man, s, f, Wm, pole=None):
    """key IK_hand.<s> so the wrist sits at world matrix Wm"""
    rig = man.o; M = rig.matrix_world.inverted() @ Wm
    # IK_hand rest == wrist rest; wrist matrix (armature) == IK_hand matrix when solved
    man.r.key_world("IK_hand." + s, f, M)
    if pole is not None:
        pb = man.r.PB["Pole_elbow." + s]; n = "Pole_elbow." + s
        pb.location = man.r.rest(n).to_3x3().inverted() @ (Vector(pole) - man.r.BN[n].head_local)
        pb.keyframe_insert("location", frame=f, group=n)

def cam(name, lens=50, fstop=8.0):
    c = bpy.data.objects.get(name)
    if c is None:
        c = bpy.data.objects.new(name, bpy.data.cameras.new(name)); bpy.data.collections["CAMS"].objects.link(c)
    c.data.lens = lens; c.data.sensor_width = 36; c.data.dof.use_dof = True; c.data.dof.aperture_fstop = fstop
    c.data.clip_start = 0.01
    return c

def look(c, f, eye, tgt, focus=None):
    c.location = Vector(eye); d = Vector(tgt) - Vector(eye)
    c.rotation_mode = 'XYZ'; c.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    c.keyframe_insert("location", frame=f); c.keyframe_insert("rotation_euler", frame=f)
    c.data.dof.focus_distance = (focus if focus is not None else d.length); c.data.dof.keyframe_insert("focus_distance", frame=f)

def mouth_rest(man):
    t = next(o for o in man.o.children if "teeth" in o.name)
    vs = [v.co for v in t.data.vertices]; ymin = min(v.y for v in vs)
    front = [v for v in vs if v.y < ymin + 0.004]
    c = sum(front, Vector()) / len(front)
    return c + Vector((0, -0.012, -0.004))   # just in front of the lower lip

def head_point(man, p_rest):
    """world position of an armature-rest point carried by the head bone (current frame)"""
    pb = man.r.PB["head"]; M = man.o.matrix_world @ pb.matrix @ man.r.rest("head").inverted()
    return M @ p_rest

def can_frame(a, origin_lip, rim=0.026, h=0.122):
    """can matrix with its axis along a and the drinking-side rim point at origin_lip"""
    a = Vector(a).normalized(); z = Vector((0, 0, 1)); y = -(z - a * z.dot(a))
    if y.length < 1e-4: y = Vector((0, 1, 0))
    y.normalize(); x = y.cross(a)
    Rm = Matrix((x, y, a)).transposed()
    org = Vector(origin_lip) - Rm @ Vector((0, rim, h))
    return Matrix.Translation(org) @ Rm.to_4x4()
