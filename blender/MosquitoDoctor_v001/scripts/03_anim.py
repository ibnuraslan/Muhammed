"""B22 MosquitoDoctor animation: every beat at 1x on a master timeline, each block ~30% longer than the expected VO beat
(Phase 2 trims/shifts blocks to the VO frames, no time-stretch). Hard cuts between shots (cameras in 04_cams.py).
blender -b scene.blend --python 03_anim.py -- anim.blend"""
import sys, os, math, random
import bpy, bmesh
from mathutils import Vector, Matrix, Quaternion
HERE = os.path.dirname(os.path.abspath(__file__)); PIPE = os.path.join(HERE, "..", "..", "pipeline")
exec(open(os.path.join(PIPE, "anim_lib.py")).read())
exec(open(os.path.join(PIPE, "hand_poses.py")).read())
exec(open(os.path.join(HERE, "lib_b22.py")).read())
OUT = sys.argv[sys.argv.index("--") + 1]
random.seed(22)
BLK = dict(A=(1, 240), B=(241, 440), C=(441, 710), D=(711, 950), E=(951, 1490), F=(1491, 1730), G=(1731, 2030), H=(2031, 2270),
           I=(2271, 2510), J=(2511, 2710), K=(2711, 2950), L=(2951, 3190))
sc.frame_start, sc.frame_end = 1, 3190; sc.render.fps = 60
for n in ("Doctor", "Boy", "ColA", "ColB", "Nurse", "PatA", "PatB"): setup_human(n)
for n in ("Doctor", "Boy"): key_vis(D[n], 1, True)   # visible from frame 1 (later hide keys must not extrapolate back)
MATT_Z = 0.614
# ------------------------------------------------------------------ BOY lying in bed (blocks A-E), head on the pillow, body along +y
BOY_HEAD = (-1.4, 0.50)
def boy_pose(f, head=(8, 0), breathe=0.0, rhand=None):
    P, Rb = lie("Boy", f, BOY_HEAD, MATT_Z, toward=(0, 1), head=head, breathe=breathe, hip_up=0.105)
    for s in "LR":
        sx = -1 if s == "R" else 1           # his right side = +x in this lie orientation
        shw = bw("Boy", P, Rb, rest_head("Boy", "upperarm01." + s))
        if s == "R" and rhand is not None: W = rhand
        else: W = V((P.x - sx * 0.27, P.y - 0.02, BLANKET_Z.get(s, MATT_Z + 0.16)))
        d = V((0, 1, -0.15)).normalized(); nn = V((0, 0, -1))
        pole = shw + V((-sx * 0.35, 0.25, -0.15))
        HUM["Boy"].key_hand(s, f, W, d, nn, pole); apply_pose(D["Boy"], s, "relaxed", f)
    return P, Rb
# frame 0: arms raised out of the way to drape the blanket over the body alone
BLANKET_Z = {}
P0, Rb0 = lie("Boy", 0, BOY_HEAD, MATT_Z, toward=(0, 1), head=(20, 0), hip_up=0.105)
for s in "LR":
    shw = bw("Boy", P0, Rb0, rest_head("Boy", "upperarm01." + s))
    HUM["Boy"].key_hand(s, 0, shw + V((0, -0.35, 0.30)), V((0, -0.6, 0.8)).normalized(), V((0, -1, 0)), shw + V((0, 0.3, 0.2)))
sc.frame_set(0)
BOYMESH = [D["Boy.body"], D["Boy.male_casualsuit03"]]
BEDMESH = [o for o in D if o.name.startswith("low_Pillow_1_lagen") and o.users_collection[0] == sc.collection or o.name in ("low_Pillow_1_lagen_0",)]
BEDMESH = [D["low_Pillow_1_lagen_0"], D["low_Pillow_1_pillow_0"]]
def drape(name, x0, x1, y0, y1, bodies, base_z, nx=44, ny=52, lift=0.04, edge_drop=0.2):
    bm = bmesh.new(); vs = {}
    for i in range(nx + 1):
        for j in range(ny + 1):
            x = x0 + (x1 - x0) * i / nx; y = y0 + (y1 - y0) * j / ny
            h = ray_down(V((x, y, 1.6)), bodies, up=0.0)
            z = (h[0].z + lift) if h else base_z - edge_drop
            vs[i, j] = [x, y, max(z, base_z - edge_drop), (h[0].z + lift * 0.9) if h else -9]
    for it in range(14):    # smooth (cloth-like), never below the surface
        new = {}
        for (i, j), v in vs.items():
            nb = [vs[k] for k in ((i - 1, j), (i + 1, j), (i, j - 1), (i, j + 1)) if k in vs]
            z = 0.5 * v[2] + 0.5 * sum(n[2] for n in nb) / len(nb)
            new[i, j] = max(z, v[3])
        for k in vs: vs[k][2] = new[k]
    vv = {k: bm.verts.new((v[0], v[1], v[2])) for k, v in vs.items()}
    for i in range(nx):
        for j in range(ny): bm.faces.new((vv[i, j], vv[i + 1, j], vv[i + 1, j + 1], vv[i, j + 1]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o)
    for p in me.polygons: p.use_smooth = True
    so = o.modifiers.new("solid", 'SOLIDIFY'); so.thickness = 0.012; so.offset = 1
    o.modifiers.new("sub", 'SUBSURF').levels = 1
    m = bpy.data.materials.new(name + "Mat"); m.use_nodes = True; Pn = m.node_tree.nodes["Principled BSDF"]
    Pn.inputs["Base Color"].default_value = (0.55, 0.72, 0.90, 1); Pn.inputs["Roughness"].default_value = 0.85
    Pn.inputs["Sheen Weight"].default_value = 0.4; me.materials.append(m)
    return o, vs
BLANKET, BV = drape("BoyBlanket", -2.06, -0.74, 0.84, 2.02, BOYMESH + BEDMESH, MATT_Z)
def blanket_z_at(x, y):
    h = ray_down(V((x, y, 1.5)), [BLANKET], up=0.0); return h[0].z if h else MATT_Z + 0.15
for fc in D["Boy"].animation_data.action.fcurves if hasattr(D["Boy"].animation_data.action, "fcurves") else []:
    for kp in [k for k in fc.keyframe_points if k.co.x == 0]: fc.keyframe_points.remove(kp)
def strip_frame0(o):
    ad = o.animation_data
    if not ad or not ad.action: return
    for layer in getattr(ad.action, "layers", []):
        for strip in layer.strips:
            for cb in strip.channelbags:
                for fc in cb.fcurves:
                    for kp in [k for k in fc.keyframe_points if abs(k.co.x) < 0.01][::-1]: fc.keyframe_points.remove(kp)
    if hasattr(ad.action, "fcurves"):
        for fc in ad.action.fcurves:
            for kp in [k for k in fc.keyframe_points if abs(k.co.x) < 0.01][::-1]: fc.keyframe_points.remove(kp)
strip_frame0(D["Boy"])
# hands rest on the blanket: palm down, fingers toward the feet; right hand (room side) a bit out from the body
RH = V((-1.13, 0.92, 0)); RH.z = blanket_z_at(RH.x, RH.y + 0.08) + 0.07
LH_Z = blanket_z_at(-1.67, 1.0) + 0.06
BLANKET_Z["L"] = LH_Z
print("BLANKET right hand z", round(RH.z, 3), "left", round(LH_Z, 3))
for f in range(1, BLK["E"][1] + 1, 40):
    ph = (f // 40) % 3
    hd = (20, 0) if f < 120 else (22, 20)                     # from ~120 he turns his head toward his right hand
    boy_pose(f, head=hd, breathe=math.sin(f / 40 * 2.1), rhand=RH)
boy_pose(BLK["E"][1], head=(22, 16), breathe=0.0, rhand=RH)
boy_pose(2950, head=(22, 16), breathe=0.0, rhand=RH)
sc.frame_set(60)
# mosquito landing point: back of the right hand (ray from above at the hand centre)
wr = bone_world("Boy", "wrist.R").translation; k3 = bone_world("Boy", "finger3-1.R").translation
hp = wr.lerp(k3, 0.55)
hit = ray_down(hp, [D["Boy.body"]], up=0.15)
LAND_BOY = (hit[0], hit[1]); print("LAND boy hand", [round(x, 3) for x in hit[0]], [round(x, 2) for x in hit[1]])

# ------------------------------------------------------------------ MOSQUITO
MQ = D["Mosquito"]; MR = D["MosqRig"]; MRig = Rig(MR)
for pb in MR.pose.bones: pb.rotation_mode = 'QUATERNION'
S_MQ = 0.0018
FOOT = 2.62 * S_MQ          # origin height above the feet plane
def surf_matrix(p, n, yaw_deg, dz=0.0, pitch=0.0):
    z = n.normalized(); ref = V((0, 1, 0)) if abs(z.y) < 0.9 else V((1, 0, 0))
    x = ref.cross(z).normalized(); y = z.cross(x)
    Rm = Matrix((x, y, z)).transposed() @ Rz(yaw_deg) @ Rx(-pitch)
    return Matrix.Translation(p + z * (FOOT + dz)) @ Rm.to_4x4()
def wings(f, spread=0.0, flap=0.0):
    for b, sx in (("asa_e_Armature_PERNILONGO", 1), ("asa_d_Armature_PERNILONGO", -1)):
        MRig.key_rot(b, f, [("Z", -spread * sx), ("Y", flap * sx)])
def legs_fly(f, amt):
    for b in ("pata2_Armature_PERNILONGO", "pata_e2_Armature_PERNILONGO", "pata3_Armature_PERNILONGO", "pata_e3_Armature_PERNILONGO",
              "pata1_Armature_PERNILONGO", "pata_e1_Armature_PERNILONGO"):
        MRig.key_rot(b, f, [("X", 10 * amt)])
FEED = D["MQ_Body"].data.materials[0].node_tree.nodes["Feed"].outputs[0]
def feed(f, v): FEED.default_value = v; FEED.keyframe_insert("default_value", frame=f)
def fly(f0, f1, path, flap=True):
    """path(u)->(Matrix) ; wings beat every frame"""
    for f in range(f0, f1 + 1):
        u = (f - f0) / max(1, f1 - f0); M = path(u); key_obj(MQ, f, M)
        if flap: wings(f, spread=40, flap=(55 if f % 2 else -15)); legs_fly(f, 1.0)
def land_hold(f, M):
    key_obj(MQ, f, M); wings(f, 0, 0); legs_fly(f, 0.0)
# A: flies in from the room side, lands on the back of the boy's right hand (lands at 70)
LM = surf_matrix(LAND_BOY[0], LAND_BOY[1], yaw_deg=200)
start = LM.translation + V((0.22, -0.18, 0.16))
def pathA(u):
    p = start.lerp(LM.translation + V((0, 0, 0.01)), smooth(min(1, u * 1.05)))
    p += V((0.01 * math.sin(u * 19), 0.008 * math.cos(u * 23), 0.006 * math.sin(u * 31))) * (1 - u)
    return Matrix.Translation(p) @ LM.to_quaternion().to_matrix().to_4x4()
fly(1, 66, pathA)
land_hold(67, Matrix.Translation(LM.translation + V((0, 0, 0.004))) @ LM.to_quaternion().to_matrix().to_4x4())
land_hold(72, LM); feed(1, 0.0); feed(240, 0.0)
land_hold(240, LM)
# B: pierces: pitches nose-down so the proboscis tip meets the skin (and 1 mm in), abdomen fills red
BITE_B = surf_matrix(LAND_BOY[0], LAND_BOY[1], yaw_deg=200, dz=-0.0008, pitch=6)
land_hold(241, LM); land_hold(300, BITE_B); land_hold(440, BITE_B)
feed(241, 0.0); feed(300, 0.05); feed(440, 0.55)

# ------------------------------------------------------------------ DOCTOR: C at the bedside chair, traps the mosquito in the vial
VIAL = D["Vial"]; CORK = D["Cork"]
def bake_to_hand(o, n, s, f0, f1, rel):
    for f in range(f0, f1 + 1):
        sc.frame_set(f); key_obj(o, f, bone_world(n, "wrist." + s) @ rel)
# a second chair at the bedside (copy of the desk chair)
src = D["DeskChair_pivot"]
BCH = src.copy(); sc.collection.objects.link(BCH); BCH.name = "BedsideChair_pivot"
for c in src.children:
    c2 = c.copy(); sc.collection.objects.link(c2); c2.parent = BCH
    for g in c.children:
        g2 = g.copy(); sc.collection.objects.link(g2); g2.parent = c2
BCH.location = V((-0.35, 0.98, 0)); BCH.rotation_euler = (0, 0, math.radians(-90 + 180))   # seat faces -x (the bed)
SEAT_Z = 0.44
dc0, dc1 = BLK["C"]
VIAL_UP = Matrix.Rotation(math.pi, 4, 'X')      # vial inverted: mouth down
def vial_over(p_skin, n, lift):
    z = n.normalized(); return Matrix.Translation(p_skin + z * (0.0015 + 0.075 + lift)) @ VIAL_UP
for f in range(dc0, dc1 + 1, 30):
    br = math.sin(f / 30 * 1.7)
    sit("Doctor", f, -0.4, 0.98, SEAT_Z, yaw=-90, lean=14, spine=16, head=(22, 0), knee_fwd=0.40, breathe=br)
sit("Doctor", dc1, -0.4, 0.98, SEAT_Z, yaw=-90, lean=14, spine=16, head=(22, 0), knee_fwd=0.40)
# grip: right hand wraps the vial near its (upturned) bottom from the doctor's side
GF = 640
VM_end = vial_over(LAND_BOY[0], LAND_BOY[1], 0.0)
VIAL.matrix_world = VM_end; sc.frame_set(GF)
cp = VM_end @ V((0.0, 0.0, 0.062)); cp.x += 0.0135   # outer wall, doctor side (+x), near the vial bottom
ret = grip_object(D["Doctor"], "R", GF, VIAL, cp, approach_dir=V((-1, 0, 0)), finger_dir=V((0, -1, 0)))
print("GRIP C", ret if not isinstance(ret, dict) else {k: ret[k] for k in list(ret)[:4]})
sc.frame_set(GF); WRm = bone_world("Doctor", "wrist.R"); REL_C = WRm.inverted() @ VM_end
print("REACH C wrist->vial cm", round((WRm.translation - VM_end.translation).length * 100, 1))
IKm = D["Doctor"].pose.bones["IK_hand.R"].matrix.copy()
for f, lift in ((dc0, 0.16), (520, 0.12), (580, 0.07), (GF, 0.0), (dc1, 0.0)):
    M = IKm.copy(); M.translation = IKm.translation + D["Doctor"].matrix_world.inverted().to_3x3() @ (LAND_BOY[1].normalized() * lift + V((0.03 * lift / 0.16, 0, 0)))
    key_ikhand_matrix("Doctor", "R", f, M, clamp=lift > 0)
    for g in ("wrap_grip",): pass
for f in (dc0, dc1):
    sc.frame_set(f)
key_relaxed("Doctor", dc0, *sit("Doctor", dc0, -0.4, 0.98, SEAT_Z, yaw=-90, lean=14, spine=16, head=(22, 0), knee_fwd=0.40), sides="L")
# left hand rests on his left thigh
bake_to_hand(VIAL, "Doctor", "R", dc0, dc1, REL_C)
key_vis(CORK, 1, False)
# mosquito: on the skin until 655, then flies up into the vial and settles on the inner wall
land_hold(dc0, BITE_B); feed(dc0, 0.55); land_hold(655, BITE_B)
def pathC(u):
    sc.frame_set(int(656 + u * 44)); V_M = bone_world("Doctor", "wrist.R") @ REL_C
    top = V_M @ V((0, 0, 0.03))
    p = BITE_B.translation.lerp(top, smooth(u)); p += V((0.002 * math.sin(u * 25), 0.002 * math.cos(u * 21), 0))
    return Matrix.Translation(p) @ BITE_B.to_quaternion().to_matrix().to_4x4()
fly(656, 700, pathC)
for f in range(701, dc1 + 1):
    sc.frame_set(f); V_M = bone_world("Doctor", "wrist.R") @ REL_C
    key_obj(MQ, f, Matrix.Translation(V_M @ V((0, 0, 0.03))) @ BITE_B.to_quaternion().to_matrix().to_4x4()); wings(f, 40, 55 if f % 2 else -15)

# ------------------------------------------------------------------ D: at the desk, the vial over the back of his own left hand
DESK_Z = 0.748
dd0, dd1 = BLK["D"]
SEAT_D = 0.44
for f in range(dd0, dd1 + 1, 30):
    br = math.sin(f / 30 * 1.9)
    sit("Doctor", f, 1.4, 2.22, SEAT_D, yaw=0, lean=10, spine=12, head=(26, 0), knee_fwd=0.42, breathe=br)
sit("Doctor", dd1, 1.4, 2.22, SEAT_D, yaw=0, lean=10, spine=12, head=(26, 0), knee_fwd=0.42)
# left hand flat on the desk, back up, fingers forward (-y)
LHW = V((1.58, 1.72, DESK_Z + 0.028))
for f in (dd0, dd1):
    sc.frame_set(f)
    place_hand(D["Doctor"], "L", f, V((LHW.x, LHW.y, DESK_Z)), V((0, 0, -1)), V((-0.15, -1, 0)).normalized())
    apply_pose(D["Doctor"], "L", "relaxed", f)
    pb = RIG["Doctor"].PB["Pole_elbow.L"]; nm = "Pole_elbow.L"
    pole = V((2.0, 2.2, 0.9)); pb.location = RIG["Doctor"].rest(nm).to_3x3().inverted() @ (pole - RIG["Doctor"].BN[nm].head_local); pb.keyframe_insert("location", frame=f, group=nm)
sc.frame_set(dd0 + 5)
wr = bone_world("Doctor", "wrist.L").translation; k3 = bone_world("Doctor", "finger3-1.L").translation
hit = ray_down(wr.lerp(k3, 0.5), [D["Doctor.body"]], up=0.15); LAND_DOC = (hit[0], hit[1])
print("LAND doctor hand", [round(x, 3) for x in hit[0]], [round(x, 2) for x in hit[1]])
VM_D = vial_over(LAND_DOC[0], LAND_DOC[1], 0.0)
VIAL.matrix_world = VM_D; GD = dd0 + 5
cp = VM_D @ V((0.0, 0.0, 0.062)); cp.y += 0.011     # doctor side (+y)
grip_object(D["Doctor"], "R", GD, VIAL, cp, approach_dir=V((0, -1, 0)), finger_dir=V((1, 0, 0)))
sc.frame_set(GD); REL_D = bone_world("Doctor", "wrist.R").inverted() @ VM_D
print("REACH D wrist->vial cm", round((bone_world("Doctor", "wrist.R").translation - VM_D.translation).length * 100, 1))
IKd = D["Doctor"].pose.bones["IK_hand.R"].matrix.copy()
for f, off in ((dd0, V((0, 0, 0))), (790, V((0, 0, 0))), (830, V((-0.05, 0.03, 0.14))), (dd1, V((-0.10, 0.06, 0.16)))):
    M = IKd.copy(); M.translation = IKd.translation + off; key_ikhand_matrix("Doctor", "R", f, M, clamp=off.length > 0)
for f in (dd0, 790, 830, dd1): apply_pose(D["Doctor"], "R", "wrap_grip", f) if False else None
bake_to_hand(VIAL, "Doctor", "R", dd0, dd1, REL_D)
# mosquito already on his hand under the vial; bites; stays when the vial lifts
DM = surf_matrix(LAND_DOC[0], LAND_DOC[1], yaw_deg=150)
DB = surf_matrix(LAND_DOC[0], LAND_DOC[1], yaw_deg=150, dz=-0.0008, pitch=6)
land_hold(dd0, DM); land_hold(760, DM); land_hold(800, DB); land_hold(dd1, DB)
feed(dd0, 0.0); feed(800, 0.05); feed(dd1, 0.5)

# ================================================================== E/F: at the desk: writing, the corked vial at eye level, the bite
NB = D["Notebook"]; NB.location = V((1.40, 1.62, DESK_Z)); NB.rotation_euler = (0, 0, 0)
PEN = D["Pen"]; PEN_REST = PEN.matrix_world.copy()
def desk_sit(f, br, head=(30, 0), lean=12, spine=14):
    return sit("Doctor", f, 1.4, 2.22, SEAT_D, yaw=0, lean=lean, spine=spine, head=head, knee_fwd=0.42, breathe=br)
def doc_pole(s, f, pole):
    pb = RIG["Doctor"].PB["Pole_elbow." + s]; nm = "Pole_elbow." + s
    pb.location = RIG["Doctor"].rest(nm).to_3x3().inverted() @ (pole - RIG["Doctor"].BN[nm].head_local); pb.keyframe_insert("location", frame=f, group=nm)
def flat_left(f, x=1.70, y=1.72):
    place_hand(D["Doctor"], "L", f, V((x, y, DESK_Z + 0.012)), V((0, 0, -1)), V((0.25, -1, 0)).normalized()); apply_pose(D["Doctor"], "L", "relaxed", f)
    doc_pole("L", f, V((x + 0.45, 2.1, 0.95)))
def write_block(f0, f1):
    for f in range(f0, f1 + 1, 30): desk_sit(f, math.sin(f / 30 * 1.6), head=(32, 4))
    desk_sit(f1, 0.0, head=(32, 4))
    for f in (f0, f1): flat_left(f)
    # pen in the right hand (pinch), tip on the right page; hand makes small writing strokes
    sc.frame_set(f0)
    tip = V((1.27, 1.62, DESK_Z + 0.018))
    PEN.matrix_world = Matrix.Translation(tip) @ (Rz(160) @ Ry(-55)).to_4x4()
    grip_object(D["Doctor"], "R", f0, PEN, PEN.matrix_world @ V((0, 0, 0.035)), approach_dir=V((0.2, -0.3, -1)).normalized())
    doc_pole("R", f0, V((1.05, 2.15, 0.95)))
    sc.frame_set(f0); rel = bone_world("Doctor", "wrist.R").inverted() @ PEN.matrix_world
    IK0 = D["Doctor"].pose.bones["IK_hand.R"].matrix.copy()
    for k, f in enumerate(list(range(f0, f1 + 1, 12)) + ([f1] if (f1 - f0) % 12 else [])):
        M = IK0.copy(); M.translation = IK0.translation + V((0.012 * ((k % 4) - 1.5) / 1.5, 0.004 * math.sin(k * 2.3), 0.003 * (k % 2)))
        key_ikhand_matrix("Doctor", "R", f, M, clamp=False); doc_pole("R", f, V((1.05, 2.15, 0.95)))
        apply_pose(D["Doctor"], "R", "pinch", f) if False else None
    bake_to_hand(PEN, "Doctor", "R", f0, f1, rel)
    key_obj(PEN, f1 + 1, PEN_REST); key_obj(PEN, f0 - 1, PEN_REST)
key_obj(PEN, 1, PEN_REST)
e0, e1 = BLK["E"]
write_block(e0, 1280)
# S11 1281-1490: corked vial up at eye level, mosquito inside on the bottom
key_vis(CORK, 951, True)
key_obj(VIAL, 951, Matrix.Translation(V((1.85, 1.45, DESK_Z)))); key_obj(VIAL, 1280, Matrix.Translation(V((1.85, 1.45, DESK_Z))))
key_obj(MQ, 951, Matrix.Translation(V((30, 0, 0)))); key_obj(MQ, 1280, Matrix.Translation(V((30, 0, 0))))
VSTUDY = Matrix.Translation(V((1.36, 1.66, DESK_Z))) @ Rz(15).to_4x4()
for f in range(1281, e1 + 1, 30): desk_sit(f, math.sin(f / 30 * 1.6), head=(22, 4), lean=16, spine=16)
desk_sit(e1, 0.0, head=(22, 4), lean=16, spine=16)
for f in (1281, e1):
    sc.frame_set(f); flat_left(f, 1.66, 1.76)
    place_hand(D["Doctor"], "R", f, V((1.06, 1.76, DESK_Z + 0.01)), V((0, 0, -1)), V((0.2, -1, 0)).normalized()); apply_pose(D["Doctor"], "R", "relaxed", f)
    doc_pole("R", f, V((0.85, 2.15, 0.95)))
key_obj(VIAL, 1281, VSTUDY); key_obj(VIAL, e1, VSTUDY)
for f in (1281, e1):
    key_obj(MQ, f, VSTUDY @ Matrix.Translation(V((0, 0, 0.0035 + FOOT))) @ Rz(40).to_4x4()); wings(f, 0, 0)
feed(1281, 0.5)
# F: S12 the bite on the back of his left hand (red bump), S13 writing again
f0, f1 = BLK["F"]
for f in list(range(f0, 1610 + 1, 30)) + [1610]: desk_sit(f, math.sin(f / 30 * 1.6), head=(38, -6), lean=14, spine=16)
for f in (f0, 1610):
    sc.frame_set(f); place_hand(D["Doctor"], "L", f, V((LHW.x, LHW.y, DESK_Z)), V((0, 0, -1)), V((-0.15, -1, 0)).normalized())
    apply_pose(D["Doctor"], "L", "relaxed", f, amount=1.0); doc_pole("L", f, V((2.0, 2.2, 0.9)))
    W, d, nn = V((1.20, 1.78, DESK_Z + 0.05)), V((0.2, -1, -0.2)).normalized(), V((0, 0, -1))
    place_hand(D["Doctor"], "R", f, V((1.18, 1.74, DESK_Z + 0.01)), V((0, 0, -1)), V((0.2, -1, 0)).normalized()); apply_pose(D["Doctor"], "R", "relaxed", f)
    doc_pole("R", f, V((0.95, 2.15, 0.95)))
apply_pose(D["Doctor"], "L", "relaxed", 1550, amount=1.0, spread=6)
BUMP = bpy.data.objects.new("BiteBump", bpy.data.meshes.new("BiteBump")); sc.collection.objects.link(BUMP)
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=8, radius=0.004); bm.to_mesh(BUMP.data); bm.free()
BUMP.scale = (1.4, 1.4, 0.35)
mb = bpy.data.materials.new("BiteRed"); mb.use_nodes = True; mb.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.85, 0.18, 0.15, 1)
mb.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.5; BUMP.data.materials.append(mb)
for p_ in BUMP.data.polygons: p_.use_smooth = True
sc.frame_set(f0 + 2)
bump_world = Matrix.Translation(LAND_DOC[0] - LAND_DOC[1] * 0.0003) @ LAND_DOC[1].to_track_quat('Z', 'Y').to_matrix().to_4x4() @ Matrix.Diagonal((1.4, 1.4, 0.35, 1))
REL_B = bone_world("Doctor", "wrist.L").inverted() @ bump_world
key_vis(BUMP, 1, False); key_vis(BUMP, f0, True); key_vis(BUMP, 1611, False)
bake_to_hand(BUMP, "Doctor", "L", f0, 1610, REL_B)
write_block(1611, f1)
key_obj(MQ, f0, Matrix.Translation(V((30, 0, 0))))     # mosquito gone after the bite
# vial on the desk (upright, corked) from F on
VDESK = Matrix.Translation(V((1.85, 1.45, DESK_Z))) @ Rz(0).to_4x4()
key_obj(VIAL, f0, VDESK); key_vis(CORK, f0, True)

# ================================================================== G: fever at the desk; flushed, then yellow
g0, g1 = BLK["G"]
for f in list(range(g0, g1 + 1, 20)) + [g1]:
    br = math.sin(f / 20 * 1.3) * 1.6
    hd = (30, 0) if f < 1850 else (6, 0)
    desk_sit(f, br, head=hd, lean=18 if f < 1850 else 8, spine=22 if f < 1850 else 8)
for f in (g0, g1):
    sc.frame_set(f); flat_left(f, 1.72, 1.74)
    place_hand(D["Doctor"], "R", f, V((1.18, 1.70, DESK_Z + 0.01)), V((0, 0, -1)), V((0.2, -1, 0)).normalized()); apply_pose(D["Doctor"], "R", "relaxed", f)
    doc_pole("R", f, V((0.95, 2.15, 0.95)))
skin_tint("Doctor", 1, (1, 0.2, 0.2), 0.05); skin_tint("Doctor", g0, (1, 0.2, 0.2), 0.05)
skin_tint("Doctor", 1800, (1.0, 0.35, 0.30), 0.16); skin_tint("Doctor", 1940, (1.0, 0.35, 0.30), 0.16)
skin_tint("Doctor", 1990, (1.0, 0.88, 0.45), 0.10)
eye_white("Doctor", 1, (0.9, 0.9, 0.9)); eye_white("Doctor", 1940, (0.9, 0.9, 0.9)); eye_white("Doctor", 1990, (0.93, 0.87, 0.55))
# ================================================================== H: sick over the basin (no fluid shown), then the stain on the floor
h0, h1 = BLK["H"]
for k, f in enumerate(list(range(h0, h1 + 1, 20)) + [h1]):
    heave = 1.0 if k % 3 == 1 else 0.0
    sit("Doctor", f, 1.4, 2.22, SEAT_D, yaw=-70, lean=26 + 6 * heave, spine=24 + 8 * heave, twist=-4, head=(22 + 6 * heave, -4), knee_fwd=0.42)
for f in (h0, h1):
    sc.frame_set(f)
    P = bone_world("Doctor", "spine04").translation
    place_hand(D["Doctor"], "R", f, P + V((0.0, -0.13, -0.05)), V((0, 1, 0.2)).normalized(), V((1, 0, 0))); apply_pose(D["Doctor"], "R", "relaxed", f)
    doc_pole("R", f, P + V((-0.4, 0.2, -0.1)))
    kn = bone_world("Doctor", "lowerleg01.L").translation
    place_hand(D["Doctor"], "L", f, kn + V((0, 0.06, 0.06)), V((0, 0, -1)), V((0, -1, 0))); apply_pose(D["Doctor"], "L", "relaxed", f)
    doc_pole("L", f, kn + V((0.4, 0.3, 0.4)))
key_vis(D["FloorStain"], 1, False); key_vis(D["FloorStain"], 2151, True); key_vis(D["FloorStain"], h1 + 1, False)
# ================================================================== I: organs cutaway, standing by the cabinet
i0, i1 = BLK["I"]
for k, f in enumerate(list(range(i0, i1 + 1, 30))):
    look = math.sin(math.pi * min(1.0, k / 5.0))     # looks down at his chest, then back up to camera
    stand("Doctor", f, 0.1, 2.25, yaw=0, spine=2 + math.sin(k) * 1.5, head=(2 + 24 * look, 10 * math.sin(k * 0.9)), dz=-0.004 * math.sin(k * 1.9))
stand("Doctor", i1, 0.1, 2.25, yaw=0, spine=2, head=(4, 0))
CUT = bpy.data.objects.new("CutawayCutter", bpy.data.meshes.new("CutawayCutter")); sc.collection.objects.link(CUT)
bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(CUT.data); bm.free()
CUT.display_type = 'WIRE'; CUT.hide_render = True
CUT_REST = Matrix.Translation(V((0, -0.135, 1.20))) @ Matrix.Diagonal((0.25, 0.14, 0.40, 1))
LIN = bpy.data.objects.new("CutawayLining", bpy.data.meshes.new("CutawayLining")); sc.collection.objects.link(LIN)
bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
for fa in [fa for fa in bm.faces if fa.normal.y < -0.5]: bm.faces.remove(fa)
bmesh.ops.reverse_faces(bm, faces=bm.faces[:]); bm.to_mesh(LIN.data); bm.free()
ml = bpy.data.materials.new("CavityPink"); ml.use_nodes = True; Pl = ml.node_tree.nodes["Principled BSDF"]
Pl.inputs["Base Color"].default_value = (0.80, 0.38, 0.40, 1); Pl.inputs["Roughness"].default_value = 0.45; Pl.inputs["Coat Weight"].default_value = 0.4
LIN.data.materials.append(ml)
LIN_REST = Matrix.Translation(V((0, -0.095, 1.20))) @ Matrix.Diagonal((0.235, 0.10, 0.385, 1))
for nm in ("Doctor.body", "Doctor.male_elegantsuit01"):
    b = D[nm].modifiers.new("Cutaway", 'BOOLEAN'); b.operation = 'DIFFERENCE'; b.object = CUT; b.solver = 'EXACT'
ORG = D["Organs_pivot"]; ORGM = [c for c in ORG.children_recursive if c.type == 'MESH']
ORG_REST = Matrix.Translation(V((0, -0.10, 1.17))) @ Rz(0).to_4x4()
for m in {sl.material for o in ORGM for sl in o.material_slots}:
    nt = m.node_tree; P = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    if P.inputs["Base Color"].links:
        src_ = P.inputs["Base Color"].links[0].from_socket
        mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.name = "Fail"
        nt.links.new(src_, mx.inputs[6]); mx.inputs[7].default_value = (0.55, 0.50, 0.32, 1); nt.links.new(mx.outputs[2], P.inputs["Base Color"])
        mx.inputs[0].default_value = 0.0; mx.inputs[0].keyframe_insert("default_value", frame=2330)
        mx.inputs[0].default_value = 0.85; mx.inputs[0].keyframe_insert("default_value", frame=2500)
FAR = Matrix.Translation(V((0, 0, -50)))
def anchor(): return bone_world("Doctor", "spine03") @ RIG["Doctor"].rest("spine03").inverted()
for o, RR in ((CUT, CUT_REST), (LIN, LIN_REST), (ORG, ORG_REST)):
    o.rotation_mode = 'QUATERNION'
    key_obj(o, 1, FAR) if o is not ORG else None
for f in range(i0, i1 + 1):
    sc.frame_set(f); A_ = D["Doctor"].matrix_world @ anchor()
    for o, RR in ((CUT, CUT_REST), (LIN, LIN_REST)):
        o.matrix_world = A_ @ RR; o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_quaternion", frame=f); o.keyframe_insert("scale", frame=f)
    ORG.matrix_world = A_ @ ORG_REST @ Matrix.Diagonal((ORG.scale.x, ORG.scale.y, ORG.scale.z, 1)) if False else A_ @ ORG_REST
    ORG.keyframe_insert("location", frame=f); ORG.keyframe_insert("rotation_quaternion", frame=f)
for o in (CUT, LIN):
    o.matrix_world = FAR; o.keyframe_insert("location", frame=i1 + 1); o.keyframe_insert("location", frame=i0 - 1)
key_vis(ORG, 1, False); key_vis(ORG, i0, True); key_vis(ORG, i1 + 1, False)
key_vis(LIN, 1, False); key_vis(LIN, i0, True); key_vis(LIN, i1 + 1, False)
# ================================================================== J: in the bed, yellow, weak; then the empty desk
j0, j1 = BLK["J"]
key_vis(BLANKET, 1, True); key_vis(D["Boy"], j0, False); key_vis(BLANKET, j0, False)
for f in range(j0, j1 + 1, 40):
    P, Rb = lie("Doctor", f, (-1.4, 0.50), MATT_Z, toward=(0, 1), head=(10, 14 + 3 * math.sin(f / 40)), breathe=math.sin(f / 40 * 1.3), hip_up=0.12)
    for s in "LR":
        sx = -1 if s == "R" else 1
        shw = bw("Doctor", P, Rb, rest_head("Doctor", "upperarm01." + s))
        HUM["Doctor"].key_hand(s, f, shw + V((0, -0.05, 0.45)), V((0, -0.6, 0.8)).normalized(), V((0, -1, 0)), shw + V((0, 0.3, 0.2))) if f == -1 else None
key_vis(D["FloorStain"], j0, False)
sc.frame_set(j0)
for s in "LR":   # temp arms up for the drape
    pass
P, Rb = lie("Doctor", 2509, (-1.4, 0.50), MATT_Z, toward=(0, 1), head=(10, 14), hip_up=0.12)
for s in "LR":
    shw = bw("Doctor", P, Rb, rest_head("Doctor", "upperarm01." + s))
    HUM["Doctor"].key_hand(s, 2509, shw + V((0, -0.35, 0.30)), V((0, -0.6, 0.8)).normalized(), V((0, -1, 0)), shw + V((0, 0.3, 0.2)))
sc.frame_set(2509)
DBLANKET, _ = drape("DocBlanket", -2.06, -0.74, 0.90, 2.02, [D["Doctor.body"], D["Doctor.male_elegantsuit01"]] + BEDMESH, MATT_Z)
def del_keys_at(o, fr):
    ad = o.animation_data
    for layer in getattr(ad.action, "layers", []):
        for strip in layer.strips:
            for cb in strip.channelbags:
                for fc in cb.fcurves:
                    for kp in [k for k in fc.keyframe_points if abs(k.co.x - fr) < 0.01][::-1]: fc.keyframe_points.remove(kp)
del_keys_at(D["Doctor"], 2509)
for f in range(j0, j1 + 1, 40):
    P, Rb = lie("Doctor", f, (-1.4, 0.50), MATT_Z, toward=(0, 1), head=(10, 14 + 3 * math.sin(f / 40)), breathe=math.sin(f / 40 * 1.3), hip_up=0.12)
    for s in "LR":
        sx = -1 if s == "R" else 1
        shw = bw("Doctor", P, Rb, rest_head("Doctor", "upperarm01." + s))
        W = V((P.x - sx * 0.25, P.y + 0.05, 0))
        h = ray_down(V((W.x, W.y, 1.5)), [DBLANKET], up=0.0); W.z = (h[0].z if h else MATT_Z + 0.2) + 0.035
        HUM["Doctor"].key_hand(s, f, W, V((0, 1, -0.15)).normalized(), V((0, 0, -1)), shw + V((-sx * 0.35, 0.25, -0.15))); apply_pose(D["Doctor"], s, "relaxed", f)
key_vis(DBLANKET, 1, False); key_vis(DBLANKET, j0, True); key_vis(DBLANKET, j1 + 1, False)
skin_tint("Doctor", j0, (1.0, 0.88, 0.45), 0.10); eye_white("Doctor", j0, (0.93, 0.87, 0.55))
# empty desk shot 2621-2710: chair pushed back, notebook closed? (open notebook, pen down, vial on the desk)
CH = D["DeskChair_pivot"]; CH.keyframe_insert("location", frame=1); CH.location.y += 0.45; CH.location.x += 0.55; CH.rotation_euler.z += math.radians(25)
CH.keyframe_insert("location", frame=2621); CH.keyframe_insert("rotation_euler", frame=2621)
CH.location.y -= 0.45; CH.location.x -= 0.55; CH.rotation_euler.z -= math.radians(25); CH.keyframe_insert("location", frame=2620); CH.keyframe_insert("rotation_euler", frame=2620)
CH.keyframe_insert("rotation_euler", frame=1)
# ================================================================== K: colleagues at the desk; the vial held up
k0, k1 = BLK["K"]
key_vis(D["Doctor"], k0, False); key_vis(DBLANKET, k0, False)
for n in ("ColA", "ColB"): key_vis(D[n], 1, False); key_vis(D[n], k0, True)
for k, f in enumerate(range(k0, k1 + 1, 30)):
    stand("ColA", f, 1.30, 2.30, yaw=0, flex=8, spine=18, head=(26, 0), hands=False)
    stand("ColB", f, 2.35, 2.20, yaw=-35, flex=6, spine=10, head=(22 + 3 * math.sin(k), 0), hands=False)
for n in ("ColA", "ColB"): stand(n, k1, *( (1.30, 2.30) if n == "ColA" else (2.35, 2.20)), yaw=0 if n == "ColA" else -35, flex=8, spine=18 if n == "ColA" else 10, head=(26, 0) if n == "ColA" else (22, 0), hands=False)
def hands_front(n, f, P, yaw, sides="LR", flex=0.0):
    """arms relaxed with a soft elbow bend: hands at the side of the thighs, a little forward (no straight mannequin arms)"""
    Rb = body_R(yaw, flex, 0)
    for s_ in sides:
        W, d, nn = relaxed_hand(n, P, Rb, s_, fwd=0.13, out=0.02, up=0.09)
        HUM[n].key_hand(s_, f, W, d, nn, elbow_pole(n, P, Rb, s_, back=0.6, out=0.3, down=-0.05))
        apply_pose(D[n], s_, "relaxed", f)
for f in (k0, 2830, k1):
    sc.frame_set(f)
    hands_front("ColA", f, V((1.30, 2.30, HUM["ColA"].root_head.z - 0.02)), 0, flex=8)
    hands_front("ColB", f, V((2.35, 2.20, HUM["ColB"].root_head.z - 0.02)), -35, sides="L", flex=6)
for f in (k0, 2760, 2830):
    sc.frame_set(f); sh = bone_world("ColB", "upperarm01.R").translation
    nbk = V((1.45, 1.62, DESK_Z)); dirn = (nbk - sh); dirn.z = 0; dirn.normalize()
    u = 0.0 if f == k0 else 1.0
    tgt = sh + dirn * (0.22 + 0.20 * u) + V((0, 0, -0.30 + 0.12 * u))      # comes up from the side to chest height
    fdir = (nbk - tgt).normalized()
    HUM["ColB"].key_hand("R", f, tgt, fdir, V((0, 0, -1)), sh + V((0, 0.10, -0.40)) + Rz(-35) @ V((-0.25, 0, 0)))
    apply_pose(D["ColB"], "R", "point" if f > k0 else "relaxed", f)
key_vis(D["Doctor"], k0, False)
# S24 2831-2950: the corked vial stands on the desk by the notebook; ColB leans in and studies it (no grip)
VK = Matrix.Translation(V((1.12, 1.62, DESK_Z))) @ Rz(10).to_4x4()
key_obj(VIAL, 2830, VDESK); key_obj(MQ, 2830, Matrix.Translation(V((30, 0, 0))))
for f in list(range(2831, k1 + 1, 30)) + [k1]:
    stand("ColB", f, 2.35, 2.20, yaw=-35, flex=14, spine=20, head=(24, 6 * math.sin(f / 40)), hands=False)
    sc.frame_set(f)
    for s_, hx, hy in (("L", 2.14, 1.86), ("R", 1.90, 1.84)):
        place_hand(D["ColB"], s_, f, V((hx, hy, DESK_Z + 0.012)), V((0, 0, -1)), V((-0.4, -1, 0)).normalized()); apply_pose(D["ColB"], s_, "relaxed", f)
        nm = "Pole_elbow." + s_; pb = RIG["ColB"].PB[nm]; pole = V((2.75 if s_ == "L" else 1.95, 2.45, 1.0))
        pb.location = RIG["ColB"].rest(nm).to_3x3().inverted() @ (pole - RIG["ColB"].BN[nm].head_local); pb.keyframe_insert("location", frame=f, group=nm)
for f in (2831, k1):
    key_obj(VIAL, f, VK); key_obj(MQ, f, VK @ Matrix.Translation(V((0, 0, 0.0035 + FOOT))) @ Rz(40).to_4x4())
key_obj(MQ, k1 + 1, Matrix.Translation(V((30, 0, 0))))
key_obj(VIAL, k1 + 1, VDESK)
# ================================================================== L: the ward (x=40): patients resting under nets, the boy recovered, a nurse
l0, l1 = BLK["L"]
WX = 40.0
for n in ("Nurse", "PatA", "PatB"): key_vis(D[n], 1, False); key_vis(D[n], l0, True)
key_vis(D["Boy"], l0, True)
for n in ("ColA", "ColB"): key_vis(D[n], l0, False)
WARD_PAT = (("Boy", -1, 0.5, 0.10), ("PatA", 1, -1.5, 0.10), ("PatB", -1, 2.5, 0.12))
def ward_lie(n, side, by, hu, f, hd=(18, 0), br=0.0, arms_up=False):
    head = (WX + side * (2.5 - 0.72), by)
    P, Rb = lie(n, f, head, MATT_Z, toward=(side, 0), head=hd, breathe=br, hip_up=hu)
    for s_ in "LR":
        sx = 1 if s_ == "L" else -1
        if arms_up:
            shw = bw(n, P, Rb, rest_head(n, "upperarm01." + s_))
            HUM[n].key_hand(s_, f, shw + V((0, 0, 0.45)) + Rb @ V((0, 0, 0.2)), V((0, 0, 1)), Rb @ V((0, -1, 0)), shw + V((0, 0, 0.2)) + Rb @ V((0, 0, -0.2))); continue
        W = bw(n, P, Rb, V((0.21 * sx, rest_head(n, "root").y + 0.02, rest_head(n, "root").z - 0.04)))
        HUM[n].key_hand(s_, f, W, Rb @ V((0, 0, -1)), Rb @ V((-sx, 0, 0)), bw(n, P, Rb, rest_head(n, "lowerarm01." + s_) + V((0.25 * sx, 0.25, 0))))
        apply_pose(D[n], s_, "relaxed", f)
    return P, Rb
WBL = []
for n, side, by, hu in WARD_PAT:
    ward_lie(n, side, by, hu, l0, arms_up=False)
    sc.frame_set(l0)
    xa, xb = (WX + side * 2.5 - 0.98, WX + side * 2.5 + 0.98)
    # blanket from the chest to the feet (chest edge 0.45 m from the head end)
    hx = WX + side * (2.5 - 0.72)
    x0, x1 = (min(hx + side * 0.42, WX + side * 3.48), max(hx + side * 0.42, WX + side * 3.48))
    wb, _ = drape("WardBlanket_" + n, x0, x1, by - 0.66, by + 0.66, [D[n + ".body"]] + [c for c in D[n].children if "suit" in c.name], MATT_Z, nx=40, ny=30)
    WBL.append(wb)
for n, side, by, hu in WARD_PAT:
    for f in list(range(l0, l1 + 1, 40)) + [l1]:
        ward_lie(n, side, by, hu, f, hd=(18, -side * 12 * math.sin(f / 60)), br=math.sin(f / 40))
for wb in WBL: key_vis(wb, 1, False); key_vis(wb, l0, True)
# nurse: stands in the aisle by the boy's bed, hands in front, looks at him, small weight shifts
for k, f in enumerate(list(range(l0, l1 + 1, 30)) + [l1]):
    stand("Nurse", f, WX - 0.75, 0.5, yaw=-90, spine=4, head=(14, -8 + 6 * math.sin(k * 0.8)), dz=-0.003 * math.sin(k * 1.7), hands=False)
    hands_front("Nurse", f, V((WX - 0.75, 0.5, HUM["Nurse"].root_head.z - 0.02)), -90)
for n in ("Doctor",): key_vis(D[n], l0, False)
print("ANIM all blocks done")
sc["BLK"] = str(BLK)
for o in (D["Doctor"], D["Boy"], MR):
    pass
print("ANIM A-D done")
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
