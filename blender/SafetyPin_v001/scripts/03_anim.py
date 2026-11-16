"""B20 SafetyPin: characters, animation (each beat a clip in its own window), cameras + markers.
blender -b work/sets.blend --python 03_anim.py -- out.blend [B1,B2,...]"""
import bpy, sys, math, json, bmesh
from mathutils import Vector, Matrix, Quaternion, Euler
exec(open("/home/user/Muhammed/blender/SafetyPin_v001/scripts/lib.py").read())
a_ = sys.argv[sys.argv.index("--") + 1:]; OUT = a_[0]
ONLY = set(a_[1].split(",")) if len(a_) > 1 else None
P = PIPE
exec(open(P + "anim_lib.py").read())
exec(open(P + "hand_poses.py").read())
sc = bpy.context.scene; R_ = math.radians
WIN = {"B1": (1, 480), "B2": (481, 810), "B3": (811, 1200), "B4": (1201, 1590),
       "B5": (1591, 1860), "B6": (1861, 2220), "B7": (2221, 2460), "B8": (2461, 2730)}
sc.frame_start, sc.frame_end = 1, 2730
FLOORS = []
def ground_z(x, y): return 0.0
CUR_WIN = None
exec(open(V + "scripts/animlib.py").read())
exec(open(V + "scripts/props.py").read())
exec(open(V + "scripts/grips.py").read())
def want(b): return ONLY is None or b in ONLY
BT = sc.get("bench_top", 0.778)
cP = bpy.data.collections["Props"]

def show_only(obj, wins):
    """visible only inside the given (f0, f1) windows"""
    edges = sorted(set([1] + [w[0] for w in wins] + [w[1] + 1 for w in wins]))
    for f in edges:
        on = any(w[0] <= f <= w[1] for w in wins)
        vis(obj, f, on)

def bone_w(rig, n, tail=False):
    pb = rig.pose.bones[n]; return rig.matrix_world @ (pb.tail if tail else pb.head)

def seat(R, H, f, hip, flex=12.0, yaw=0.0, knee_dy=-0.42, foot_dy=-0.50, kx=0.12):
    """seated on a stool: hip world point, knees forward, feet flat on the floor (character faces -Y rotated by yaw)"""
    H.key_root(f, hip, yaw=yaw, flex=flex)
    Rz = Matrix.Rotation(R_(yaw), 3, 'Z')
    for s, sx in (("L", 1), ("R", -1)):
        knee = hip + Rz @ Vector((sx * kx, knee_dy, -0.02))
        foot = hip + Rz @ Vector((sx * (kx + 0.02), foot_dy, 0)); foot.z = H.ankle[s].z
        foot_at(R, H, s, f, foot, yaw=yaw)
        knee_pole(R, s, f, knee + Rz @ Vector((sx * 0.05, -0.6, 0.2)))

def arm_poles(R, f, hip, yaw=0.0, out=0.55, back=0.05, z=0.55):
    Rz = Matrix.Rotation(R_(yaw), 3, 'Z')
    for s, sx in (("L", 1), ("R", -1)):
        pole(R, s, f, hip + Rz @ Vector((sx * out, back, z - hip.z)))

# ------------------------------------------------------------------ characters (single rigs, visibility per beat)
hunt, RH, HH = setup("Hunt")
pal, RP, HP = setup("Pal")
buyer, RB, HB = setup("Buyer")
show_only(hunt, [WIN["B1"], WIN["B2"], WIN["B4"], WIN["B5"], WIN["B6"]])
show_only(pal, [WIN["B3"], WIN["B4"]])
# v002b: the Judge rig's pale grey irises read white at medium range -> use the inventor's eye material (same MPFB eye mesh/UVs)
_he = next(o for o in hunt.children if o.name.endswith("high-poly")); _pe = next(o for o in pal.children if o.name.endswith("high-poly"))
pass
for _s in "LR":   # director: the friend's jacket read as a bust -> flatten the breast bones (body + jacket both follow)
    pass   # (v002b: friend re-cast on a male donor; breast-bone offsets removed)
# chest lattice (follows spine01): pushes the front of the chest back so body + jacket read flat and male
def _flat_chest(rig, depth=0.075):
    sc.frame_set(1); bpy.context.view_layer.update()
    B = rig.data.bones; bl = B["breast.L"].head_local; br = B["breast.R"].head_local
    c = (bl + br) / 2; c.y += 0.02
    ld = bpy.data.lattices.new(rig.name + "_ChestLat"); ld.points_u = ld.points_v = ld.points_w = 3
    ld.interpolation_type_u = ld.interpolation_type_v = ld.interpolation_type_w = 'KEY_BSPLINE'
    lo = bpy.data.objects.new(rig.name + "_ChestLat", ld); sc.collection.objects.link(lo)
    lo.location = rig.matrix_world @ c; lo.scale = (0.46, 0.30, 0.34); lo.hide_render = True
    for i, p_ in enumerate(ld.points):
        u, v, w = i % 3, (i // 3) % 3, i // 9
        if v == 0 and w == 1: p_.co_deform.y += depth / 0.30 * (1.0 if u == 1 else 0.6)
        if v == 0 and w == 2 and u == 1: p_.co_deform.y += depth / 0.30 * 0.4
    parent_to_bone(lo, rig, "spine01", 1)
    for ch in rig.children:
        if ch.type == 'MESH' and ("body" in ch.name or "suit" in ch.name):
            vg = ch.vertex_groups.new(name="ChestFlat")
            cc = c.copy(); cc.y -= 0.02
            for v in ch.data.vertices:
                d = Vector(((v.co.x - cc.x) / 0.20, (v.co.y - cc.y) / 0.22, (v.co.z - cc.z) / 0.15)).length
                if d < 1.0 and v.co.y < cc.y + 0.05: vg.add([v.index], (1 - d) ** 0.7, 'REPLACE')
            m = ch.modifiers.new("ChestFlat", 'LATTICE'); m.object = lo; m.vertex_group = "ChestFlat"
            arm = next((i for i, mm in enumerate(ch.modifiers) if mm.type == 'ARMATURE'), None)
            with bpy.context.temp_override(object=ch):
                bpy.ops.object.modifier_move_to_index(modifier="ChestFlat", index=(arm + 1) if arm is not None else 0)
# _flat_chest(pal)   # superseded by the MPFB re-phenotype in 01_chars
show_only(buyer, [WIN["B6"]])
HIP_H = Vector((-0.30, 0.12, 0.62)); HIP_P = Vector((0.38, 0.12, 0.62)); HIP_B = Vector((-0.05, -1.10, 0.62))
HIP_B = Vector((-0.05, -1.20, 0.62))
for _n, _y in (("StoolHunt", 0.14), ("StoolPal", 0.14), ("StoolBuyer", -1.22)): bpy.data.objects[_n].location.y = _y
# bench moved 8 cm away from the sitters (jacket hems cleared the top's underside); bench dressing moves with it
for _n in ["Workbench", "Candle", "Spool", "PinCushion", "Cloth0", "Cloth1"] + ["CushionPin%d" % i for i in range(7)] + [o.name for o in bpy.data.objects if o.name.startswith("SpoolFlange")]:
    _o = bpy.data.objects.get(_n)
    if _o: _o.location.y -= 0.08
_l = bpy.data.objects.get("OilLamp")
if _l:
    for _c in list(_l.children_recursive): bpy.data.objects.remove(_c)
    bpy.data.objects.remove(_l)
# workbench: remove the long front/back aprons and the low stretcher (legs went through them); keep top, legs, end aprons
_tb = bpy.data.objects["WoodenTable_01"]; _mw = _tb.matrix_world
_bm = bmesh.new(); _bm.from_mesh(_tb.data)
def _c(f): return _mw @ f.calc_center_median()
_del = [f for f in _bm.faces if _c(f).z < 0.725 and abs(_c(f).x) < 0.76]
bmesh.ops.delete(_bm, geom=_del, context='FACES'); _bm.to_mesh(_tb.data); _bm.free(); print("TABLE_TRIM", len(_del))

# props built here (meshes, so grips can be measured)
bpy.data.objects.remove(bpy.data.objects["Wire"])
wire = twist_wire("Wire", cP)
proto_b = to_mesh(bpy.data.objects["ProtoPin_Body"]); proto_a = bpy.data.objects["ProtoPin_Arm"]
hero_b = to_mesh(bpy.data.objects["HeroPin_Body"]); hero_a = bpy.data.objects["HeroPin_Arm"]
proto_a = bpy.data.objects["ProtoPin_Arm"]; hero_a = bpy.data.objects["HeroPin_Arm"]
for o in (proto_a, hero_a):
    if o.type == 'CURVE': to_mesh(o)
proto_a = bpy.data.objects["ProtoPin_Arm"]; hero_a = bpy.data.objects["HeroPin_Arm"]
spin = to_mesh(bpy.data.objects["StraightPin"])

RIGHT_FD = Vector((0.45, -0.75, -0.45)); RIGHT_PN = Vector((0.2, -0.3, 1.0))
def hold_pin(body, s, f, C, rig=None, fd=None, pn=None, point_dir=Vector((0.45, -0.85, 0.25)), out_w=0.8):
    """pinch the pin by its coil: hand first, then the pin is oriented so its normal (Y) runs along the pad axis"""
    rig = rig or hunt
    ax, g = pinch_at(rig, s, f, C, fd or RIGHT_FD, pn or RIGHT_PN, gap=0.0050)
    sc.frame_set(int(f)); bpy.context.view_layer.update()
    out = (LAST_Q - (rig.matrix_world @ rig.pose.bones["wrist." + s].head)).normalized()   # away from the hand, past the fingertips
    pdir = (out * out_w + point_dir.normalized() * (1 - out_w))
    x = (pdir - ax * pdir.dot(ax)).normalized(); z = x.cross(ax)
    M = Matrix((x, ax, z)).transposed()
    body.matrix_world = Matrix.Translation(LAST_Q) @ M.to_4x4(); bpy.context.view_layer.update()   # at the measured pad midpoint
    parent_to_bone(body, rig, "wrist." + s, f)
    return x, ax

def tip_world(arm, d_from_tip=0.006):
    """world point on the pin arm `d_from_tip` behind its point"""
    L = PIN_L; x = 0.0005 + (L - 0.006) - d_from_tip; z = PIN_R - 0.0013 * (x / (L - 0.006))
    return arm.matrix_world @ Vector((x, 0.0012, z))

# ================================================================== B1 wire -> spring (1..480)
def beat_B1():
    f0, f1 = WIN["B1"]
    for f in (f0, f1): seat(RH, HH, f, HIP_H, flex=6)
    for f in range(f0, f1 + 1, 30):
        ph = math.sin(2 * math.pi * (f - f0) / 170)
        HH.key_spine(f, flex=8 + 1.2 * ph, head=(24 + 2 * ph, 2 * ph))
    arm_poles(RH, f0, HIP_H); arm_poles(RH, f1, HIP_H)
    # --- 1a/1b (1..330): both hands pinch the wire ends; the left hand twists about the wire, the coil winds in
    C = Vector((-0.30, -0.42, 0.94)); half = 0.035
    wire.location = C; wire.rotation_euler = (0, 0, 0)
    sk = wire.data.shape_keys.key_blocks["S1"]
    for f, v in ((f0, 0.0), (40, 0.0), (300, 1.0), (330, 1.0)):
        sk.value = v; sk.keyframe_insert("value", frame=f)
    pR = C + Vector((-half + 0.004, 0, 0)); pL = C + Vector((half - 0.004, 0, 0))
    pinch_at(hunt, "R", f0, pR, Vector((0.05, -0.8, -0.6)), Vector((0.9, -0.1, 0.4)), gap=0.0023)
    wire.location = LAST_Q + (C - pR); C = wire.location.copy(); pL = C + Vector((half - 0.004, 0, 0))   # wire end sits in the measured pinch
    sc.frame_set(f0); pb = hunt.pose.bones["IK_hand.R"]; pb.keyframe_insert("location", frame=330); pb.keyframe_insert("rotation_quaternion", frame=330)
    hold_fingers(hunt, "R", f0, 330)
    for k, f in enumerate(list(range(f0, 331, 30)) + [330]):
        tw = 12 * math.sin(k * 1.3)       # twisting: the hand rolls about the wire axis through the pinch point
        Rx = Matrix.Rotation(R_(tw), 3, 'X')
        pinch_at(hunt, "L", f, pL, Rx @ Vector((-0.05, -0.8, -0.6)), Rx @ Vector((-0.9, -0.1, 0.4)), gap=0.0023)
    show_only(wire, [(f0, 330)])
    # --- 1c (331..480): macro, the finished coil spring: right hand holds the coil, left pinches the arm tip and opens/closes it
    f2 = 331
    pin_C = Vector((-0.31, -0.43, 0.96))
    xax, yax = hold_pin(proto_b, "R", f2, pin_C)
    for f in (f2, f1): pass
    hold_R = f2
    proto_a.rotation_euler = (0, R_(-22), 0)      # no clasp yet: the point stands open
    # he turns the pin in the light (wrist roll about the pin), the other hand rests on the bench
    for f, ang in ((f2, 0), (405, -14), (480, -22)):
        hand_delta(RH, "R", f2, f, (0, 0, 0.004 * abs(ang) / 22), rot=Matrix.Rotation(R_(ang), 3, Vector((0.3, -0.9, 0.2)).normalized()))
        hold_fingers(hunt, "R", f2, f)
    for f in (f0, 330):
        pass
    for f in (f2, f1):
        place_hand(hunt, "L", f, Vector((-0.19, -0.03, 0.69)), Vector((0, 0, -1)), Vector((0.1, -1, -0.25))); apply_pose(hunt, "L", "relaxed", f)
    show_only(proto_b, [(f2, f1)])
    # cameras
    cam_shot("Cam1a", f0, 150, [(f0, (0.10, -1.55, 1.02), (-0.30, -0.25, 0.98)), (150, (0.0, -1.32, 1.00), (-0.30, -0.25, 0.97))], lens=38)
    cam_shot("Cam1b", 151, 330, [(151, tuple(C + Vector((0.07, -0.30, 0.09))), tuple(C)), (330, tuple(C + Vector((0.05, -0.25, 0.08))), tuple(C))], lens=55, fstop=11)
    cam_shot("Cam1c", f2, f1, [(f2, tuple(pin_C + Vector((0.10, -0.24, 0.08))), tuple(pin_C + xax * 0.022)), (f1, tuple(pin_C + Vector((0.08, -0.20, 0.07))), tuple(pin_C + xax * 0.022))], lens=55, fstop=11)
    for nm in ("Cam1a",): catchlight(hunt, bpy.data.objects[nm], 0, 0)

# ================================================================== B2 clasp (481..810)
def beat_B2():
    f0, f1 = WIN["B2"]
    for f in (f0, f1): seat(RH, HH, f, HIP_H, flex=6)
    arm_poles(RH, f0, HIP_H); arm_poles(RH, f1, HIP_H)
    # 2a (481..650): macro, the clasp: the left fingers swing the point down into the clasp head
    pin_C = Vector((-0.31, -0.43, 0.96))
    for f in range(f0, 651, 30):
        ph = math.sin(2 * math.pi * (f - f0) / 160)
        HH.key_spine(f, flex=8 + ph, head=(24 + 2 * ph, 0))
    xax, yax = hold_pin(hero_b, "R", f0, pin_C)

    hero_a.rotation_euler = (0, 0, 0)
    for f, ang in ((f0, 10), (560, 0), (650, -12)):
        hand_delta(RH, "R", f0, f, (0, 0, 0), rot=Matrix.Rotation(R_(ang), 3, Vector((0.3, -0.9, 0.2)).normalized()))
        hold_fingers(hunt, "R", f0, f)
    for f in (f0, 625, 810):
        place_hand(hunt, "L", f, Vector((-0.19, -0.03, 0.69)), Vector((0, 0, -1)), Vector((0.1, -1, -0.25))); apply_pose(hunt, "L", "relaxed", f)
    # 2b (651..810): he lifts the finished pin to look at it, small smile, face to camera
    sc.frame_set(650); M650 = hunt.pose.bones["IK_hand.R"].matrix.copy()
    for f, dz, dy in ((690, 0.10, -0.02), (760, 0.13, -0.03), (810, 0.13, -0.03)):
        hand_delta(RH, "R", 650, f, (0.0, dy, dz), rot=Matrix.Rotation(R_(-25 * min(1, (f - 650) / 60)), 3, 'Z')); hold_fingers(hunt, "R", 650, f)
    for f in range(651, f1 + 1, 20):
        u = min(1, (f - 651) / 50); ph = math.sin(2 * math.pi * (f - 651) / 150)
        HH.key_spine(f, flex=8 - 6 * u + ph, head=(24 - 22 * u + 2 * ph, -6 * u))
    show_only(hero_b, [(f0, f1)])
    sc.frame_set(f0); bpy.context.view_layer.update()
    clasp_w = hero_b.matrix_world @ Vector((PIN_L - 0.004, 0, 0))
    mid_w = hero_b.matrix_world @ Vector((PIN_L * 0.55, 0, 0))
    side = yax if yax.dot(Vector((0, -1, 0.3))) > 0 else -yax          # the pin's flat side that faces the front
    cam_shot("Cam2a", f0, 650, [(f0, tuple(mid_w + side * 0.15 + Vector((0, 0, 0.03))), tuple(mid_w)), (650, tuple(mid_w + side * 0.12 + Vector((0, 0, 0.025))), tuple(mid_w))], lens=60, fstop=14)
    cam_shot("Cam2b", 651, f1, [(651, (0.10, -1.20, 1.10), (-0.30, -0.20, 1.02)), (f1, (0.04, -1.05, 1.10), (-0.30, -0.20, 1.04))], lens=42)
    catchlight(hunt, bpy.data.objects["Cam2b"], 0, 0)

def hand_delta(R, s, f_src, f_dst, delta, rot=None):
    sc.frame_set(f_src); pb = R.PB["IK_hand." + s]; M = pb.matrix.copy()
    if rot is not None:
        t = M.translation.copy(); M = Matrix.Translation(t) @ rot.to_4x4() @ Matrix.Translation(-t) @ M
    M = Matrix.Translation(Vector(delta)) @ M
    R.key_world("IK_hand." + s, f_dst, M)

def hold_fingers(rig, s, f_src, f_dst):
    sc.frame_set(f_src)
    for k in (1, 2, 3, 4, 5):
        for j in (1, 2, 3):
            pb = rig.pose.bones["finger%d-%d.%s" % (k, j, s)]; pb.keyframe_insert("rotation_quaternion", frame=f_dst, group=pb.name)

if want("B1"): beat_B1()
if want("B2"): beat_B2()
exec(open(V + "scripts/anim_b3_b8.py").read())
eye_fix_all()
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("ANIM_OK", OUT)
