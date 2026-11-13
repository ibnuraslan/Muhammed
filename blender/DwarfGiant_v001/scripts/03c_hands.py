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
    # MakeHuman rest pose has the palms facing down: the curl is the sign that moves the fingertip down
    z = {}
    for sg in (1, -1):
        pb.rotation_quaternion = Quaternion((1, 0, 0), R_(30 * sg)); bpy.context.view_layer.update()
        z[sg] = tip_world(rig, "finger3-2." + s).z
    pb.rotation_quaternion = old; bpy.context.view_layer.update()
    return 1 if z[1] < z[-1] else -1

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
        if any(cc.type == "COPY_ROTATION" for cc in pb.constraints):
            nlim += 0   # IK-driven hand: orientation is solved explicitly (key_hand); a clamp here folds the hand into a mitten
        c = pb.constraints.new("LIMIT_ROTATION"); c.owner_space = "LOCAL"; c.name = "HandLimit"
        if any(cc.type == "COPY_ROTATION" for cc in pb.constraints): c.mute = True
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
# ---- v003: shared hand-pose library (director, Nov 12) replaces the hand-set finger angles above
exec(open(__import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "pipeline", "hand_poses.py")).read())
for rig in RIGS:
    for pb in rig.pose.bones:                       # drop my own finger limits; the library adds the agreed ones
        if pb.name.startswith("finger"):
            for c in [c for c in pb.constraints if c.name == "HandLimit"]: pb.constraints.remove(c)
    add_hand_limits(rig)
    for s_ in "LR":
        wr = rig.pose.bones["wrist." + s_]
        if any(c.type == "COPY_ROTATION" for c in wr.constraints):      # IK-solved wrist: a clamp folds the hand (v002 mitten bug)
            for c in wr.constraints:
                if c.type == "LIMIT_ROTATION": c.mute = True
    for s_ in "LR": apply_pose(rig, s_, "relaxed", 1)
OBR = bpy.data.objects
POSES_PLAN = [("Hero", "L", [(680, "relaxed"), (696, "flat_palm"), (880, "flat_palm"), (900, "relaxed"),
                             (1380, "relaxed"), (1398, "cup_hold"), (1470, "cup_hold"), (1482, "relaxed")]),
              ("Officer1", "L", [(188, "relaxed")]),
              ("Clerk", "L", [(1, "flat_palm")]), ("Clerk", "R", [(1, "flat_palm")]),
              ("Surgeon1", "R", [(1565, "relaxed"), (1575, "flat_palm"), (1712, "flat_palm"), (1725, "relaxed")]),
              ("Nurse", "L", [(1681, "relaxed"), (1690, "flat_palm"), (1857, "flat_palm"), (1866, "relaxed")]),
              ("Nurse", "R", [(1681, "relaxed"), (1690, "flat_palm"), (1857, "flat_palm"), (1866, "relaxed")])]
for ch, s_, keys in POSES_PLAN:
    for f, pose in keys: apply_pose(OBR["RIG_" + ch], s_, pose, f)
# clerk: palms resting ON the desk top (surface found by ray cast), small writing strokes with the right hand
dg = bpy.context.evaluated_depsgraph_get()
def surface_z(x, y):
    ok, loc, n_, i_, ob_, m_ = sc.ray_cast(bpy.context.evaluated_depsgraph_get(), Vector((x, y, 1.6)), Vector((0, 0, -1)))
    return loc.z if ok else 0.948
CLR = OBR["RIG_Clerk"]
for c in [c for c in CLR.children if c.type == "MESH"]: c.hide_viewport = True     # don't ray-hit himself
for f in range(1, 1500, 10):
    sc.frame_set(f); st = math.sin(f * 0.35)
    xr, yr = 0.60 + 0.012 * st, 1.74 + 0.025 * math.sin(f * 0.11)
    place_hand(CLR, "R", f, Vector((xr, yr, surface_z(xr, yr) + 0.003 * max(0.0, st))), Vector((0, 0, -1)), Vector((-1, -0.15, 0)))
    place_hand(CLR, "L", f, Vector((0.61, 1.46, surface_z(0.61, 1.46))), Vector((0, 0, -1)), Vector((-1, 0.2, 0)))
for c in [c for c in CLR.children if c.type == "MESH"]: c.hide_viewport = False
# officer 1: real wrap grip on the height-rod mesh (grip_object closes each finger onto it, thumb opposes)
ROD = Vector((-0.30, 2.97, 0.0)); O1R = OBR["RIG_Officer1"]
gauge = [o for o in OBR["Gauge"].children_recursive if o.type == "MESH"]; print("GAUGE_MESHES", [(o.name, tuple(round(d, 2) for d in o.dimensions)) for o in gauge])
rod = max(gauge, key=lambda o: max(o.dimensions), default=None)   # the tall measuring column
if rod:
    P1 = Vector((-0.66, 2.86, 0.0)); app = (ROD - P1); app.z = 0; app.normalize()
    for f, z in ((1, 1.62), (40, 1.58), (90, 1.48), (130, 1.43), (172, 1.43)):
        sc.frame_set(f); ok, loc, nrm, idx = rod.closest_point_on_mesh(rod.matrix_world.inverted() @ Vector((ROD.x - 0.2, ROD.y, z)))
        cp = rod.matrix_world @ loc
        # the 2.3 cm bar stands flush with the wall, so no hand can wrap it: palm flat on its side face, fingers up the bar
        place_hand(O1R, "L", f, Vector((cp.x, cp.y, z)), Vector((1, 0, 0)), Vector((0, 0.15, 1)), skin=0.006)
        apply_pose(O1R, "L", "flat_palm", f)
        sc.frame_set(f); tip = O1R.matrix_world @ O1R.pose.bones["finger3-3.L"].tail; pal = O1R.matrix_world @ O1R.pose.bones["finger3-1.L"].head
        print("ROD_CONTACT", f, round(_dist_to(rod, tip), 3), round(_dist_to(rod, pal), 3))
print("HAND_POSES applied")
bpy.ops.wm.save_as_mainfile(filepath=out)
