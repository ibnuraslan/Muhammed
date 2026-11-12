"""Hands pass (client 23:00): joint limits on fingers/thumb/wrist/elbow for every MPFB rig, relaxed curled default hand.
blender -b film.blend --python 03c_hands.py -- <out.blend>"""
import bpy, sys, math
from mathutils import Vector, Quaternion
out = sys.argv[sys.argv.index("--") + 1]
R_ = math.radians
sc = bpy.context.scene
RIGS = [o for o in bpy.data.objects if o.type == "ARMATURE" and o.name.startswith("RIG_")]

def tip_world(rig, bone):
    return rig.matrix_world @ rig.pose.bones[bone].tail

def curl_sign(rig, s):
    """+1 if a positive local-X rotation of finger3-2 moves its tip toward the palm side"""
    pb = rig.pose.bones["finger3-2." + s]; B = rig.data.bones
    wr = B["wrist." + s].head_local; dd = B["finger3-1." + s].head_local - wr
    aa = B["finger2-1." + s].head_local - B["finger5-1." + s].head_local
    nn = dd.cross(aa) if s == "L" else aa.cross(dd)          # same convention as anim_lib key_hand
    old = pb.rotation_quaternion.copy(); res = {}
    for sg in (1, -1):
        pb.rotation_quaternion = Quaternion((1, 0, 0), R_(30 * sg)); bpy.context.view_layer.update()
        res[sg] = (rig.matrix_world.inverted() @ tip_world(rig, "finger3-2." + s)).dot(nn.normalized())
    pb.rotation_quaternion = old; bpy.context.view_layer.update()
    return 1 if res[1] < res[-1] else -1      # palm normal from key_hand points out of the back of the hand in MPFB

sc.frame_set(1)
nlim = 0
for rig in RIGS:
    for pb in rig.pose.bones: pb.rotation_mode = "QUATERNION"
    for s in "LR":
        sg = curl_sign(rig, s)
        for fi in range(1, 6):
            for seg in (1, 2, 3):
                n = f"finger{fi}-{seg}.{s}"
                if n not in rig.pose.bones: continue
                pb = rig.pose.bones[n]
                c = pb.constraints.new("LIMIT_ROTATION"); c.owner_space = "LOCAL"; c.name = "HandLimit"
                c.use_limit_x = c.use_limit_y = c.use_limit_z = True
                if fi == 1:   # thumb: natural cone
                    c.min_x, c.max_x = (R_(-10), R_(50)) if sg > 0 else (R_(-50), R_(10))
                    c.min_y, c.max_y = R_(-20), R_(20); c.min_z, c.max_z = R_(-25), R_(25)
                else:
                    c.min_x, c.max_x = (0.0, R_(90)) if sg > 0 else (R_(-90), 0.0)
                    c.min_y, c.max_y = R_(-5), R_(5); c.min_z, c.max_z = R_(-10), R_(10)
                nlim += 1
                # relaxed curled default (fingers slightly curled, never flat-splayed)
                deg = {1: 8, 2: 14, 3: 10}[seg] if fi == 1 else {1: 14 + 3 * fi, 2: 22 + 3 * fi, 3: 14 + 2 * fi}[seg]
                if not (pb.id_data.animation_data and pb.id_data.animation_data.action and
                        any(fc.data_path == f'pose.bones["{n}"].rotation_quaternion' for l in pb.id_data.animation_data.action.layers
                            for st in l.strips for cb in st.channelbags for fc in cb.fcurves)):
                    pb.rotation_quaternion = Quaternion((1, 0, 0), R_(deg * sg)); pb.keyframe_insert("rotation_quaternion", frame=1, group=n)
        # wrist: +-60 flex, +-25 side
        pb = rig.pose.bones["wrist." + s]
        c = pb.constraints.new("LIMIT_ROTATION"); c.owner_space = "LOCAL"; c.name = "HandLimit"
        # which local axis is flex (moves fingertips along the palm normal) vs side (in the palm plane)?
        B = rig.data.bones; wr = B["wrist." + s].head_local
        nn = (B["finger3-1." + s].head_local - wr).cross(B["finger2-1." + s].head_local - B["finger5-1." + s].head_local).normalized()
        old = pb.rotation_quaternion.copy(); t0 = rig.pose.bones["finger3-3." + s].head.copy(); comp = {}
        for ax, v in (("X", (1, 0, 0)), ("Z", (0, 0, 1))):
            pb.rotation_quaternion = Quaternion(v, R_(20)); bpy.context.view_layer.update()
            comp[ax] = abs((rig.pose.bones["finger3-3." + s].head - t0).normalized().dot(nn))
        pb.rotation_quaternion = old; bpy.context.view_layer.update()
        flex = "X" if comp["X"] > comp["Z"] else "Z"
        if abs(comp["X"] - comp["Z"]) < 0.05: flex = "diag"
        c.use_limit_x = c.use_limit_z = True
        if flex == "X": c.min_x, c.max_x, c.min_z, c.max_z = R_(-60), R_(60), R_(-25), R_(25)
        elif flex == "Z": c.min_z, c.max_z, c.min_x, c.max_x = R_(-60), R_(60), R_(-25), R_(25)
        else: c.min_x, c.max_x, c.min_z, c.max_z = R_(-60), R_(60), R_(-45), R_(45)   # MPFB wrist axes sit diagonal to the palm
        if rig.name == "RIG_Hero" and s == "L": print("WRIST flex axis", flex, comp)
        nlim += 1
        # elbow: hinge only, 0..145 in the IK solver (no hyper-extension, no twist)
        el = rig.pose.bones["lowerarm01." + s]
        el.lock_ik_y = el.lock_ik_z = True; el.use_ik_limit_x = True
        # find flex sign: rotation that brings the wrist closer to the shoulder
        old = el.rotation_quaternion.copy(); d = {}
        for sg2 in (1, -1):
            el.rotation_quaternion = Quaternion((1, 0, 0), R_(40 * sg2)); bpy.context.view_layer.update()
            d[sg2] = (rig.pose.bones["wrist." + s].head - rig.pose.bones["upperarm01." + s].head).length
        el.rotation_quaternion = old; bpy.context.view_layer.update()
        fs = 1 if d[1] < d[-1] else -1
        el.ik_min_x, el.ik_max_x = (R_(0), R_(145)) if fs > 0 else (R_(-145), R_(0))
        if not any(c.type == "IK" for c in rig.pose.bones["lowerarm02." + s].constraints):   # FK rigs: plain limit
            c = el.constraints.new("LIMIT_ROTATION"); c.owner_space = "LOCAL"; c.name = "HandLimit"
            c.use_limit_x = True; c.min_x, c.max_x = el.ik_min_x, el.ik_max_x
        nlim += 1
# hero's left hand lies flat on the desk (beat 5): fingers almost straight there, relaxed curl before/after
hr = bpy.data.objects["RIG_Hero"]; sgL = curl_sign(hr, "L")
for fi in range(1, 6):
    for seg in (1, 2, 3):
        n = f"finger{fi}-{seg}.L"
        if n not in hr.pose.bones: continue
        pb = hr.pose.bones[n]; relaxed = pb.rotation_quaternion.copy()
        for f, q in ((680, relaxed), (696, Quaternion((1, 0, 0), R_(3 * sgL))), (880, Quaternion((1, 0, 0), R_(3 * sgL))), (900, relaxed)):
            pb.rotation_quaternion = q; pb.keyframe_insert("rotation_quaternion", frame=f, group=n)
print("LIMITS", nlim, "on", len(RIGS), "rigs")
bpy.ops.wm.save_as_mainfile(filepath=out)
