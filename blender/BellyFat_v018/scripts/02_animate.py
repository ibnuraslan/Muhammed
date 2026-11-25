"""BellyFat v018 stage B: her acting, the ONE bullet, the wound, the ONE camera (no cuts), the impact flashes, VO.
blender -b a.blend --python 02_animate.py -- <vo.mp3> <out.blend>
Built to the client's VO from the start (BellyFat v017 timing, frames 1-1273, beats 1/73/181/451/715/829/1147).
Scene changes happen inside the move: the bullet hits her shirt -> a short warm impact flash around the bullet (only the
bullet shows) -> the same bullet, same camera-relative pose, in the cross-section (140). Back out: up the wound track ->
flash -> her shirt hole -> pull out to her face (1137)."""
import bpy, sys, math, random, os
from mathutils import Vector, Matrix, Quaternion
from mathutils.bvhtree import BVHTree
PIPE = "/home/user/Muhammed/blender/pipeline"
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(PIPE + "/anim_lib.py").read())
exec(open(PIPE + "/hand_poses.py").read())
exec(open(HERE + "/lib_anim.py").read())
args = sys.argv[sys.argv.index("--") + 1:]
VO, OUT = args[0], args[1]
random.seed(10)
END = 1273
LOG = []
def log(*a):
    s = " ".join(str(x) for x in a); LOG.append(s); print("LOG", s)
O = bpy.data.objects
WR, WB, CL = O["Woman"], O["Woman.body"], O["Woman.clothes"]
BUL, TIP, TRAIL, WCTL = O["Bullet"], O["TipCtl"], O["BulletTrail"], O["WoundCtl"]
CRACK = O["HM_GlassCrack"]
MX = Vector((20.0, 0.0, 0.0))
GLASS_Y = -1.025
SWAP1, SWAP2 = 140, 1137

# ================================================================== rig
CT = make_human_ctrl(WR)
add_hand_limits(WR)
for pb in WR.pose.bones: pb.rotation_mode = 'QUATERNION'
for s in "LR":
    lo = WR.pose.bones["lowerarm01." + s]; lo.use_ik_limit_x = True; lo.ik_min_x = math.radians(-40); lo.ik_max_x = math.radians(145)
H = Human(CT)

def key_pole(s, f, target, kind="elbow"):
    n = ("Pole_elbow." if kind == "elbow" else "Pole_knee.") + s; pb = CT.PB[n]
    pb.location = CT.rest(n).to_3x3().inverted() @ (Vector(target) - CT.BN[n].head_local)
    pb.keyframe_insert("location", frame=f, group=n)

def key_spine(f, flex=0.0, twist=0.0, side=0.0):
    for n, w in Human.SPINE_W.items():
        CT.key_rot(n, f, [("X", flex * w), ("Y", side * w), ("Z", twist * w)])

_HS = {}
def head_signs():
    if _HS: return _HS["s"]
    pb = WR.pose.bones["head"]; q0 = pb.rotation_quaternion.copy(); upd()
    e0 = Wh(WR, "eye.L"); out = {}
    for ax, i in (("X", 0), ("Z", 2)):
        pb.rotation_quaternion = Quaternion(Vector([1 if k == i else 0 for k in range(3)]), math.radians(10)); upd()
        out[ax] = Wh(WR, "eye.L") - e0; pb.rotation_quaternion = q0; upd()
    _HS["s"] = (1 if out["X"].z < 0 else -1, 1 if out["Z"].x > 0 else -1)
    return _HS["s"]
def key_head(f, yaw, pitch, roll=0.0):
    """yaw +: toward her own left (+X); pitch +: look down"""
    sx, sz = head_signs()
    for n, w in (("neck01", 0.25), ("neck02", 0.25), ("neck03", 0.2), ("head", 0.3)):
        CT.key_rot(n, f, [("X", sx * pitch * w), ("Y", roll * w), ("Z", sz * yaw * w)])

def stand(f, flex=2.0, side=0.0, dz=0.0, twist=0.0):
    H.key_root(f, Vector((0.0, 0.0, H.root_head.z - 0.012 + dz)), yaw=0.0, flex=flex, side=side)
    for s, sg in (("L", 1), ("R", -1)):
        a = CT.BN["foot." + s].head_local
        tgt = Vector((sg * 0.12, 0.0, a.z))
        M = Matrix.Translation(tgt) @ Matrix.Translation(-a) @ CT.rest("IK_foot." + s)
        CT.key_world("IK_foot." + s, f, M)
        key_pole(s, f, tgt + Vector((sg * 0.05, -0.8, 0.45)), kind="knee")

# ---- surfaces for clearance (evaluated with every modifier: what renders)
def bvh_eval(obj):
    upd(); dg = bpy.context.evaluated_depsgraph_get(); e = obj.evaluated_get(dg); me = e.to_mesh(); Mw = obj.matrix_world
    b = BVHTree.FromPolygons([Mw @ v.co for v in me.vertices], [p.vertices[:] for p in me.polygons]); e.to_mesh_clear(); return b
def ray_surface(objs, origin, direction):
    best = None
    for o in objs:
        h = bvh_eval(o).ray_cast(Vector(origin), Vector(direction).normalized(), 5.0)
        if h[0] is not None and (best is None or h[3] < best[3]): best = h
    return best

# ================================================================== idle arms (hanging, elbow bent ~20 deg, hands clear of the hips)
def hang_hand(s, f, fwd=0.06, drop=0.50, out_extra=0.0):
    """hand hanging relaxed by her side, 4 cm outside her hip surface (ray-cast), palm toward the thigh"""
    sx = 1 if s == "L" else -1
    fs(f); sh = Wh(WR, "upperarm01." + s)
    z = sh.z - drop; y = sh.y - fwd
    hit = ray_surface([CL, WB], (sx * 0.8, y, z), (-sx, 0, 0))
    surf_x = hit[0].x if hit else sx * 0.22
    wrist = Vector((surf_x + sx * (0.045 + out_extra), y, z))
    d = Vector((sx * 0.08, -0.25, -1.0)).normalized(); n = Vector((-sx, 0.0, 0.0))
    H.key_hand(s, f, wrist, d, n, pole=sh + Vector((sx * 0.25, 0.45, -0.25)))
    apply_pose(WR, s, "relaxed", f)

# ================================================================== her acting (keys)
# beats: 1 'A stray bullet struck her' / 73 'right in the stomach' / 181 'It pierced her skin' / 451 'Layer by layer'
#        715 'deeper tissue' / 829 'lost most of its force' / 1147 'saving her life'
for f, flex, side, dz in ((1, 2.0, 0.0, 0.0), (40, 2.5, 0.6, 0.0), (70, 1.5, -0.3, 0.004), (110, 1.8, 0.0, 0.004),
                          (128, 2.0, 0.0, 0.004), (150, -4.0, 0.0, 0.0), (220, 9.0, 0.0, -0.008), (1137, 9.0, 0.0, -0.008),
                          (1180, 6.0, 0.0, -0.006), (1205, 3.0, 0.0, -0.002), (1232, 7.0, 0.0, -0.010), (1273, 5.0, 0.0, -0.006)):
    stand(f, flex=flex, side=side, dz=dz)
# breathing on the spine (every 20 frames), faster after the hit, a long exhale at 1205-1232
def breath(f):
    per = 220 if f < 128 else (110 if f < 1205 else 200)
    amp = 1.0 if f < 128 else 1.6
    return amp * math.sin(2 * math.pi * f / per)
def spine_flex(f):
    return pchip([(1, 1.0), (128, 1.0), (150, -5.0), (230, 8.0), (1137, 8.0), (1180, 7.0), (1205, 2.0), (1232, 9.0), (1273, 7.0)])(f)
for f in list(range(1, END + 1, 20)) + [END]:
    key_spine(f, flex=spine_flex(f) + breath(f), twist=pchip([(1, 0), (34, 0), (50, -6), (128, -5), (160, 0), (END, 0)])(f))
# head: looks out of the window (slightly right), turns to the crack at the sound, then later down at her belly
HEAD = [(1, 6, -2), (30, 8, -3), (38, -10, -4), (60, -14, -2), (128, -12, 0), (150, 0, -8), (220, 0, 24),
        (1137, 2, 26), (1170, -2, 24), (1188, 4, 4), (1205, 6, -2), (1232, 4, -10), (1255, 2, -6), (1273, 3, -5)]
hy = pchip([(f, y) for f, y, p in HEAD]); hp = pchip([(f, p) for f, y, p in HEAD])
for f in list(range(1, END + 1, 6)) + [END]:
    key_head(f, hy(f), hp(f))
# face: calm -> startled (crack) -> (hit) -> shocked looking down -> relief exhale -> small smile
for f, sm, br, jaw, sq in ((1, 0.15, 0.0, 0.0, 0.0), (30, 0.15, 0.0, 0.0, 0.0), (38, 0.0, 0.9, 0.35, 0.0), (70, -0.1, 0.8, 0.2, 0.0),
                           (128, -0.2, 0.9, 0.25, 0.0), (160, -0.4, -0.6, 0.35, 0.4), (1137, -0.3, 0.7, 0.25, 0.0),
                           (1180, -0.2, 0.8, 0.30, 0.0), (1205, 0.0, 0.4, 0.15, 0.0), (1225, 0.1, 0.1, 0.2, 0.0),
                           (1245, 0.8, 0.3, 0.05, 0.15), (1273, 0.85, 0.3, 0.05, 0.15)):
    key_face(WR, f, smile=sm, brow=br, jaw=jaw, squint=sq)
blinks(WR, [14, 96, 1158])
saccades(CT, 1, 128, every=36, amp=(1.5, 2.5), seed=4)
saccades(CT, 1137, END, every=34, amp=(1.5, 2.5), seed=5)

# ---- arms: both hang relaxed until after the hit; the right hand goes flat onto her belly while the camera is in the
#      cross-section (never on screen); the left keeps hanging, with small idle motion
for f, fw, dr in ((1, 0.05, 0.50), (40, 0.07, 0.48), (90, 0.06, 0.49), (128, 0.06, 0.49), (150, 0.10, 0.46)):
    hang_hand("R", f, fwd=fw, drop=dr)
for f, fw, dr in ((1, 0.05, 0.50), (40, 0.07, 0.48), (90, 0.06, 0.49), (128, 0.06, 0.49), (150, 0.10, 0.46), (240, 0.08, 0.49),
                  (1137, 0.08, 0.49), (1180, 0.07, 0.49), (1210, 0.06, 0.50), (1232, 0.05, 0.51), (1273, 0.06, 0.50)):
    hang_hand("L", f, fwd=fw, drop=dr)

# ================================================================== where the bullet hits (her shirt, f128 pose)
fs(128)
zs = [1.00]          # navel height (spine03 0.95 .. spine02 1.04), on the shirt
best = None
for z in zs:
    h = ray_surface([CL], (0.035, -0.9, z), (0, 1, 0))
    if h and (best is None or h[0].y < best[0].y): best = h
B_HIT = best[0].copy(); B_N = best[1].copy()
log("belly hit point", tuple(round(x, 3) for x in B_HIT), "normal", tuple(round(x, 2) for x in B_N))
G = Vector((-0.22, GLASS_Y, B_HIT.z + 0.16))
BDIR = (B_HIT - G).normalized()
O["HM_GlassCrack"].location = G + Vector((0, -0.006, 0))
log("glass point", tuple(round(x, 3) for x in G), "flight m", round((B_HIT - G).length, 3))

# ================================================================== the bullet: one object, store flight -> macro
BL = 0.0155                                   # base -> nose
def store_nose(f):
    """nose position along the flight line: fast outside (12 cm/frame), slow-motion inside (to the shirt at 128), 7 mm dent"""
    if f <= 30: return G - BDIR * (30 - f) * 0.12
    if f <= 128: return G + (B_HIT - G) * ((f - 30) / 98.0)
    u = min(1.0, (f - 128) / 8.0); return B_HIT + BDIR * 0.007 * (1 - (1 - u) ** 2)
def q_dir(d):
    return Vector((0, 0, 1)).rotation_difference(Vector(d).normalized())
BUL.rotation_mode = 'QUATERNION'
spin = 0.0
for f in range(1, SWAP1):
    spin += math.radians(14 if f <= 30 else 5)
    nose = store_nose(f)
    q = q_dir(BDIR) @ Quaternion((0, 0, 1), spin)
    BUL.location = nose - BDIR * BL; BUL.rotation_quaternion = q
    BUL.keyframe_insert("location", frame=f); BUL.keyframe_insert("rotation_quaternion", frame=f)
# macro: nose depth below the shirt top (m) on the VO beats; monotone (PCHIP) so it only ever slows
ZN = pchip([(SWAP1, 0.0005), (150, -0.0004), (165, -0.0015), (192, -0.0060), (300, -0.0150), (451, -0.0245), (600, -0.0350),
            (715, -0.0430), (829, -0.0476), (905, -0.0494), (960, -0.0502), (990, -0.0503), (SWAP2, -0.0503)])
QM = Quaternion((1, 0, 0), math.pi)          # nose straight down (-Z)
for f in range(SWAP1, END + 1):
    sp_rate = max(0.0, 5.0 * (1 - (f - SWAP1) / 820.0))
    spin += math.radians(sp_rate)
    zn = ZN(min(f, SWAP2))
    BUL.location = MX + Vector((0, 0, zn + BL)); BUL.rotation_quaternion = QM @ Quaternion((0, 0, 1), spin)
    BUL.keyframe_insert("location", frame=f); BUL.keyframe_insert("rotation_quaternion", frame=f)
set_interp(BUL, 'LINEAR')
quat_continuity(BUL)
# the air trail: long while it is fast outside, short in slow motion, gone at the shirt
TRAIL.scale = (1, 1, 0.45)
for f, L_ in ((1, 0.45), (30, 0.45), (32, 0.05), (112, 0.04), (120, 0.02), (124, 0.001)):
    TRAIL.scale = (1, 1, L_); TRAIL.keyframe_insert("scale", frame=f)
vis(TRAIL, 1, False); vis(TRAIL, 12, True); vis(TRAIL, 124, False)
vis(BUL, 1, False); vis(BUL, 12, True)
# glass crack spreads from the hole as the bullet passes (f30-33)
for f, s_ in ((1, 0.001), (30, 0.001), (31, 0.5), (33, 1.0)):
    CRACK.scale = (s_,) * 3; CRACK.keyframe_insert("scale", frame=f)
vis(CRACK, 1, False); vis(CRACK, 30, True)
# wound state: x energy, y ripple phase, z entry
EN = pchip([(SWAP1, 1.0), (192, 0.9), (451, 0.7), (715, 0.50), (829, 0.32), (905, 0.15), (985, 0.0), (SWAP2, 0.0)])
for f in list(range(SWAP1, SWAP2 + 1, 5)) + [SWAP2]:
    WCTL.location = (EN(f), 0.0, 0.0); WCTL.keyframe_insert("location", index=0, frame=f)
for f, v in ((1, 0.0), (163, 0.0), (166, 1.0), (END, 1.0)):
    WCTL.location.z = v; WCTL.keyframe_insert("location", index=2, frame=f)
for f in (1, END):
    WCTL.location.y = 0.33 * f; WCTL.keyframe_insert("location", index=1, frame=f)
set_interp(WCTL, 'LINEAR')

# ================================================================== the shirt: a dent at the hit, then the hole (follows the shirt)
def clothes_rest_points():
    saved = []
    for m in CL.modifiers:
        if m.type in ('SUBSURF', 'SOLIDIFY'): saved.append((m, m.show_viewport)); m.show_viewport = False
    upd(); dg = bpy.context.evaluated_depsgraph_get(); e = CL.evaluated_get(dg); me = e.to_mesh()
    pts = [(v.index, CL.matrix_world @ v.co) for v in me.vertices]; e.to_mesh_clear()
    for m, sv in saved: m.show_viewport = sv
    upd(); return pts
fs(128)
pts = clothes_rest_points()
near = sorted(pts, key=lambda t: (t[1] - B_HIT).length)
if not CL.data.shape_keys: CL.shape_key_add(name="Basis")
dent = CL.shape_key_add(name="dent"); dent.value = 0.0
for i, p in pts:
    d = (p - B_HIT).length
    if d < 0.03:
        v = CL.data.vertices[i]
        w = 0.5 * (1 + math.cos(math.pi * d / 0.03))
        dent.data[i].co = v.co - v.normal * 0.007 * w
for f, v in ((1, 0.0), (128, 0.0), (134, 1.0), (150, 0.4), (220, 0.0)):
    dent.value = v; dent.keyframe_insert("value", frame=f)
# the hole: painted procedurally into the shirt's own material at the hit point (UV space, measured in metres on the
# shirt), so it sits exactly on the cloth, follows every fold, and stays crisp at 3 cm. Keyed on at 134 (inside the flash).
def uv_at_hit():
    saved = []
    for m in CL.modifiers:
        if m.type in ('SUBSURF', 'SOLIDIFY'): saved.append((m, m.show_viewport)); m.show_viewport = False
    fs(128); upd(); dg = bpy.context.evaluated_depsgraph_get(); e = CL.evaluated_get(dg); me = e.to_mesh(); Mw = CL.matrix_world
    bv = BVHTree.FromPolygons([Mw @ v.co for v in me.vertices], [p.vertices[:] for p in me.polygons])
    loc, nrm, idx, dist = bv.ray_cast(B_HIT - BDIR * 0.05, BDIR, 1.0)
    poly = me.polygons[idx]; uvl = me.uv_layers.active.data
    vs = [Mw @ me.vertices[vi].co for vi in poly.vertices]; uvs = [uvl[li].uv.copy() for li in poly.loop_indices]
    from mathutils.geometry import intersect_point_tri, barycentric_transform
    tri = None
    for k in range(1, len(vs) - 1):
        if intersect_point_tri(loc, vs[0], vs[k], vs[k + 1]) is not None or k == len(vs) - 2:
            tri = (0, k, k + 1); break
    a_, b_, c_ = tri
    uv3 = barycentric_transform(loc, vs[a_], vs[b_], vs[c_], uvs[a_].to_3d(), uvs[b_].to_3d(), uvs[c_].to_3d())
    # Jacobian world <- uv on that triangle (rest-ish): columns dP/du, dP/dv
    e1, e2 = vs[b_] - vs[a_], vs[c_] - vs[a_]; t1, t2 = uvs[b_] - uvs[a_], uvs[c_] - uvs[a_]
    det = t1.x * t2.y - t2.x * t1.y
    dPdu = (e1 * t2.y - e2 * t1.y) / det; dPdv = (e2 * t1.x - e1 * t2.x) / det
    e.to_mesh_clear()
    for m, sv in saved: m.show_viewport = sv
    upd(); return uv3.to_2d(), dPdu, dPdv
UV0, DPDU, DPDV = uv_at_hit()
G11, G12, G22 = DPDU.dot(DPDU), DPDU.dot(DPDV), DPDV.dot(DPDV)
log("hole uv", tuple(round(x, 4) for x in UV0), "m per uv", round(math.sqrt(G11), 3), round(math.sqrt(G22), 3))
smat = CL.data.materials[0]; nt = smat.node_tree
pr = [n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'][0]
src = pr.inputs["Base Color"].links[0].from_socket
uvn = nt.nodes.new("ShaderNodeUVMap"); sepu = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(uvn.outputs["UV"], sepu.inputs[0])
def mth(op, a_, b_=None):
    m_ = nt.nodes.new("ShaderNodeMath"); m_.operation = op
    for i_, x in enumerate((a_, b_)):
        if x is None: continue
        if isinstance(x, (int, float)): m_.inputs[i_].default_value = float(x)
        else: nt.links.new(x, m_.inputs[i_])
    return m_.outputs[0]
du = mth('SUBTRACT', sepu.outputs["X"], UV0.x); dv = mth('SUBTRACT', sepu.outputs["Y"], UV0.y)
d2 = mth('ADD', mth('ADD', mth('MULTIPLY', mth('MULTIPLY', du, du), G11), mth('MULTIPLY', mth('MULTIPLY', du, dv), 2 * G12)),
         mth('MULTIPLY', mth('MULTIPLY', dv, dv), G22))
dist = mth('SQRT', mth('MAXIMUM', d2, 0.0))
nzh = nt.nodes.new("ShaderNodeTexNoise"); nzh.inputs["Scale"].default_value = 900.0
nt.links.new(uvn.outputs["UV"], nzh.inputs["Vector"])
distn = mth('ADD', dist, mth('MULTIPLY', mth('SUBTRACT', nzh.outputs["Fac"], 0.5), 0.0016))   # ragged torn edge
ramp = nt.nodes.new("ShaderNodeValToRGB"); cr_ = ramp.color_ramp; cr_.interpolation = 'LINEAR'
cr_.elements[0].position = 0.0; cr_.elements[0].color = (0.035, 0.004, 0.004, 1)
cr_.elements[1].position = 1.0; cr_.elements[1].color = (0.0, 0.0, 0.0, 0)
for pos_, col_ in ((0.24, (0.06, 0.005, 0.005, 1)), (0.30, (0.30, 0.02, 0.04, 1)), (0.40, (0.55, 0.02, 0.06, 1)), (0.70, (0.62, 0.03, 0.10, 0.55))):
    el = cr_.elements.new(pos_); el.color = col_
mrh = nt.nodes.new("ShaderNodeMapRange"); mrh.inputs["From Max"].default_value = 0.020; nt.links.new(distn, mrh.inputs["Value"])
nt.links.new(mrh.outputs[0], ramp.inputs["Fac"])
hon = nt.nodes.new("ShaderNodeValue"); hon.name = "HoleOn"; hon.outputs[0].default_value = 0.0
fac = mth('MULTIPLY', ramp.outputs["Alpha"], hon.outputs[0])
mixh = nt.nodes.new("ShaderNodeMix"); mixh.data_type = 'RGBA'; nt.links.new(fac, mixh.inputs["Factor"])
nt.links.new(src, mixh.inputs["A"]); nt.links.new(ramp.outputs["Color"], mixh.inputs["B"])
nt.links.new(mixh.outputs["Result"], pr.inputs["Base Color"])
for f, v in ((1, 0.0), (133, 0.0), (134, 1.0), (END, 1.0)):
    hon.outputs[0].default_value = v; hon.outputs[0].keyframe_insert("default_value", frame=f)
for fc in iter_fcurves(nt.animation_data.action):
    for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
# where the hole is on later poses: the evaluated position of the clothes vertex nearest to the hit (no subsurf/solidify)
HV = near[0][0]
def hole_world(f):
    saved = []
    for m in CL.modifiers:
        if m.type in ('SUBSURF', 'SOLIDIFY'): saved.append((m, m.show_viewport)); m.show_viewport = False
    fs(f); upd(); dg = bpy.context.evaluated_depsgraph_get(); e = CL.evaluated_get(dg); me = e.to_mesh()
    p = CL.matrix_world @ me.vertices[HV].co; n = (CL.matrix_world.to_3x3() @ me.vertices[HV].normal).normalized(); e.to_mesh_clear()
    for m, sv in saved: m.show_viewport = sv
    upd()
    h = ray_surface([CL], p + n * 0.05, -n)            # onto the rendered (solidified) surface
    return (h[0].copy(), h[1].copy()) if h else (p, n)
# ================================================================== right hand flat on her belly (end pose, set while the camera is in the macro)
def belly_point(f, x, z):
    fs(f); h = ray_surface([CL], (x, -0.9, z), (0, 1, 0)); return h
HOLE_W, HOLE_N = hole_world(1137)
log("hole at 1137", tuple(round(x, 3) for x in HOLE_W), "normal", tuple(round(x, 2) for x in HOLE_N))
palm_h = belly_point(1137, HOLE_W.x - 0.080, HOLE_W.z + 0.010)
PALM_P, PALM_N = palm_h[0].copy(), palm_h[1].copy()
FDIR = Vector((0.45, 0.0, -0.90)); FDIR = (FDIR - PALM_N * FDIR.dot(PALM_N)).normalized()
log("palm point", tuple(round(x, 3) for x in PALM_P))
def hand_on_belly(f, lift=0.0, skin=0.015):
    place_hand(WR, "R", f, PALM_P + PALM_N * lift, -PALM_N, FDIR, skin=skin)
    key_pole("R", f, Wh(WR, "upperarm01.R") + Vector((-0.40, 0.30, -0.30)))
    apply_pose(WR, "R", "flat_palm", f, spread=0)
# path: the hanging hand comes forward and up outside the hip, then settles flat (all inside the macro range)
fs(260); sh = Wh(WR, "upperarm01.R")
H.key_hand("R", 260, Vector((sh.x - 0.06, sh.y - 0.28, sh.z - 0.38)), Vector((0.5, -0.3, -0.8)).normalized(), Vector((0.4, 0.6, 0)).normalized(),
           pole=sh + Vector((-0.30, 0.35, -0.25)))
apply_pose(WR, "R", "relaxed", 260)
hand_on_belly(330, lift=0.03)
for f, l_ in ((380, 0.0), (1137, 0.0), (1180, 0.0), (1205, 0.0), (1232, 0.0), (1273, 0.0)):
    hand_on_belly(f, lift=l_)

# ---- hand clearance (palm/fingers vs shirt) on the end pose: nudge the lift until no finger point is inside the shirt
def finger_min_clear(f):
    fs(f); b = bvh_eval(CL); worst = 9.0
    for n in [pb.name for pb in WR.pose.bones if pb.name.endswith(".R") and (pb.name.startswith("finger") or pb.name.startswith("metacarpal"))]:
        for t in (0.0, 0.5, 1.0):
            p = WR.matrix_world @ WR.pose.bones[n].head.lerp(WR.pose.bones[n].tail, t)
            loc, nrm, idx, dist = b.find_nearest(p)
            if loc is None: continue
            sd = (p - loc).dot(nrm)
            worst = min(worst, sd)
    return worst
for f in (380, 1137, 1205, 1232, 1273):
    lift = 0.0; c_ = finger_min_clear(f)
    for it in range(5):
        if c_ >= 0.008: break
        lift += 0.008 - c_ + 0.001; hand_on_belly(f, lift=lift); c_ = finger_min_clear(f)
    fs(f); pc = (Wh(WR, "finger3-1.R") + Wh(WR, "wrist.R")) / 2
    log("palm reach err mm", f, round((pc - (PALM_P + PALM_N * (0.015 + lift))).length * 1000, 1), "lift mm", round(lift * 1000, 1))
    log("right hand on belly: min bone-axis clearance to shirt (mm)", f, round(c_ * 1000, 1))

# ================================================================== camera: ONE camera, PCHIP paths, level horizon (except inside the flash)
cam_d = bpy.data.cameras.new("CAM_Film"); CAM = bpy.data.objects.new("CAM_Film", cam_d); sc.collection.objects.link(CAM); sc.camera = CAM
AIM = bpy.data.objects.new("CAM_Film_Aim", None); sc.collection.objects.link(AIM)
cam_d.sensor_fit = 'AUTO'; cam_d.sensor_width = 36; cam_d.dof.use_dof = False; cam_d.clip_start = 0.004; cam_d.clip_end = 60
CAM.rotation_mode = 'QUATERNION'
def bpos(f): fs(f); return BUL.matrix_world.translation.copy()
def bctr(f): fs(f); return BUL.matrix_world @ Vector((0, 0, BL * 0.5))
def head_c(f): fs(f); return (Wh(WR, "eye.L") + Wh(WR, "eye.R")) / 2
UP = Vector((0, 0, 1)); RGT = BDIR.cross(UP).normalized()     # to the right of the flight, seen from behind
def P(*v): return Vector(v)
def chase(f, d, h, r, up_aim, reach):
    return (lambda: bpos(f) - BDIR * d + UP * h + RGT * r, lambda: bpos(f) + (BDIR + UP * up_aim) * reach)
SEG_A = [
    (1,   lambda: P(0.42, -3.95, 1.32), lambda: P(-0.04, -0.55, 1.30), 26),
    (26,  lambda: P(0.52, -3.20, 1.30), lambda: P(-0.02, -0.40, 1.30), 28),
    (40,  lambda: P(0.62, -1.70, 1.30), lambda: P(0.0, -0.10, 1.30), 34),
    (52,  lambda: P(0.45, -0.95, 1.24), lambda: P(-0.05, -0.20, 1.24), 30),
]
for f, h, r, d, w_, ln in ((72, 0.07, 0.15, 0.18, 0.38, 22), (86, 0.07, 0.12, 0.21, 0.36, 22), (100, 0.06, 0.09, 0.20, 0.34, 22)):
    SEG_A.append((f, (lambda f=f, d=d, h=h, r=r: bpos(f) - BDIR * d + UP * h + RGT * r), (lambda f=f, w_=w_: bpos(f).lerp(head_c(f), w_)), ln))
for f, d, h, r, ua, rc, ln in ((112, 0.070, -0.010, 0.035, 0.0, 0.012, 28),
                               (122, 0.036, -0.022, 0.0, 0.0, 0.009, 34), (128, 0.027, -0.020, 0.0, 0.0, 0.008, 38), (139, 0.021, -0.017, 0.0, 0.0, 0.008, 40)):
    pf, af = chase(f, d, h, r, ua, rc); SEG_A.append((f, pf, af, ln))
def zc(f): return MX + Vector((0, 0, ZN(min(f, SWAP2)) + BL * 0.5))
def orb(f, ang, dist, dz, aimz=0.0):
    a_ = math.radians(ang); return (lambda: zc(f) + P(math.sin(a_) * dist, -math.cos(a_) * dist, dz), lambda: zc(f) + P(0, 0, aimz))
SEG_M = []
for f, ang, dist, dz, az, ln in ((147, 10, 0.050, 0.006, -0.002, 50), (220, 0, 0.060, 0.008, 0.002, 50), (330, -14, 0.068, 0.004, -0.003, 48),
                                 (451, -26, 0.078, 0.000, -0.006, 44), (580, -12, 0.082, -0.006, -0.008, 44), (715, -22, 0.086, -0.012, -0.011, 42),
                                 (770, 0, 0.070, -0.008, -0.008, 46), (829, 26, 0.058, -0.004, -0.005, 50), (905, 24, 0.060, 0.000, -0.003, 50), (985, 20, 0.046, 0.002, 0.0, 54),
                                 (1032, 8, 0.082, -0.010, -0.015, 44), (1075, -6, 0.098, -0.016, -0.018, 42)):
    pf, af = orb(f, ang, dist, dz, az); SEG_M.append((f, pf, af, ln))
SEG_M += [
    (1102, lambda: MX + P(-0.004, -0.088, -0.024), lambda: MX + P(0, 0, -0.026), 44),
    (1120, lambda: MX + P(0.002, -0.055, -0.006), lambda: MX + P(0, 0, -0.008), 46),
    (1133, lambda: MX + P(0.0, -0.034, 0.0), lambda: MX + P(0, 0, -0.003), 48),
    (1136, lambda: MX + P(0.0, -0.031, 0.0), lambda: MX + P(0, 0, -0.003), 48),
]
def face_c(f): return head_c(f) + Vector((0, 0, -0.02))
SEG_B = [
    (1137, lambda: HOLE_W + HOLE_N * 0.032 + Vector((0.012, 0, 0)), lambda: HOLE_W + Vector((0.012, 0, 0)), 40),
    (1146, lambda: HOLE_W + HOLE_N * 0.11 + Vector((0.03, 0, 0.03)), lambda: HOLE_W + Vector((0.015, 0, 0.03)), 34),
    (1160, lambda: HOLE_W + Vector((0.06, -0.50, 0.12)), lambda: HOLE_W.lerp(face_c(1160), 0.50), 24),
    (1180, lambda: P(0.12, -0.92, 1.15), lambda: HOLE_W.lerp(face_c(1180), 0.52), 24),
    (1215, lambda: P(0.04, -0.92, 1.16), lambda: HOLE_W.lerp(face_c(1215), 0.53), 24),
    (END,  lambda: P(-0.03, -0.92, 1.17), lambda: HOLE_W.lerp(face_c(END), 0.53), 24),
]
def look_q(p, a, up=Vector((0, 0, 1))):
    zc_ = (p - a).normalized(); yc = (up - zc_ * up.dot(zc_)); yc = yc.normalized() if yc.length > 1e-6 else Vector((0, 1, 0))
    xc = yc.cross(zc_); return Matrix((xc, yc, zc_)).transposed().to_quaternion()
CAMKEYS = {}
def run_seg(seg, f_from, f_to):
    ks = [(f, pf(), af(), l) for f, pf, af, l in seg]
    fx = [pchip([(k[0], k[1][i]) for k in ks]) for i in range(3)]
    ax = [pchip([(k[0], k[2][i]) for k in ks]) for i in range(3)]
    fl = pchip([(k[0], k[3]) for k in ks])
    for f in range(f_from, f_to + 1):
        p = Vector([fx[i](f) for i in range(3)]); a_ = Vector([ax[i](f) for i in range(3)])
        CAMKEYS[f] = (p, look_q(p, a_), a_, fl(f))
run_seg(SEG_A, 1, SWAP1 - 1)
run_seg(SEG_M, 147, SWAP2 - 1)
run_seg(SEG_B, SWAP2, END)
# inside the first flash (140-146): the camera keeps its pose relative to the bullet (store -> macro), then turns level
pS, qS, aS, lS = CAMKEYS[SWAP1 - 1]
fs(SWAP1 - 1); MB_s = BUL.matrix_world.copy()
rel = MB_s.inverted() @ (Matrix.Translation(pS) @ qS.to_matrix().to_4x4())
fs(SWAP1); MB_m = BUL.matrix_world.copy()
M0 = MB_m @ rel
p0, q0 = M0.translation.copy(), M0.to_quaternion()
p1, q1, a1, l1 = CAMKEYS[147]
for f in range(SWAP1, 147):
    u = smoothstep((f - SWAP1) / (147 - SWAP1))
    fs(f); Mb = BUL.matrix_world.copy()
    relp = (MB_m.inverted() @ p0).lerp(MB_m.inverted() @ p1, u)
    q = q0.slerp(q1, u)
    CAMKEYS[f] = (MB_m @ relp + (Mb.translation - MB_m.translation), q, a1, lS + (l1 - lS) * u)
prev = None
for f in range(1, END + 1):
    p, q, a_, l_ = CAMKEYS[f]
    if prev is not None and prev.dot(q) < 0: q = -q
    prev = q
    CAM.location = p; CAM.rotation_quaternion = q; AIM.location = a_; cam_d.lens = l_
    CAM.keyframe_insert("location", frame=f); CAM.keyframe_insert("rotation_quaternion", frame=f)
    AIM.keyframe_insert("location", frame=f); cam_d.keyframe_insert("lens", frame=f)
set_interp(CAM, 'LINEAR'); set_interp(AIM, 'LINEAR'); set_interp(cam_d, 'LINEAR')
log("camera keyed", len(CAMKEYS))
# a small catchlight riding with the camera (eyes never read as black holes), scaled with distance, HOME only
cl = bpy.data.lights.new("Catch", 'AREA'); cl.energy = 4.0; cl.size = 0.25; cl.color = (1, 0.96, 0.92)
clo = bpy.data.objects.new("Catchlight", cl); bpy.data.collections["HOME"].objects.link(clo); clo.parent = CAM; clo.location = (0.0, 0.10, 0.0)
for f in list(range(1, END + 1, 6)) + [END]:
    fs(f); d_ = (CAM.matrix_world.translation - head_c(f)).length
    cl.energy = max(0.1, min(2.0, 2.0 * (d_ / 0.9) ** 2)); cl.keyframe_insert("energy", frame=f)

# ================================================================== the impact flash (camera-parented sphere, camera rays only)
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=48, ring_count=24); FL = bpy.context.active_object; FL.name = "ImpactFlash"
for p_ in FL.data.polygons: p_.use_smooth = True
fm = bpy.data.materials.new("M_ImpactFlash"); fm.use_nodes = True; nt = fm.node_tree
for n in list(nt.nodes):
    if n.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n)
tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sep.inputs[0])
cxy = nt.nodes.new("ShaderNodeCombineXYZ"); nt.links.new(sep.outputs["X"], cxy.inputs[0]); nt.links.new(sep.outputs["Y"], cxy.inputs[1])
ab = nt.nodes.new("ShaderNodeVectorMath"); ab.operation = 'LENGTH'; nt.links.new(cxy.outputs[0], ab.inputs[0])
cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (1.0, 0.92, 0.65, 1); cr.color_ramp.elements[1].position = 0.95
cr.color_ramp.elements[1].color = (0.55, 0.02, 0.01, 1)
e_ = cr.color_ramp.elements.new(0.35); e_.color = (1.0, 0.45, 0.05, 1)
nt.links.new(ab.outputs[1], cr.inputs["Fac"])
em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Strength"].default_value = 1.0; nt.links.new(cr.outputs["Color"], em.inputs["Color"])
tr = nt.nodes.new("ShaderNodeBsdfTransparent"); lp = nt.nodes.new("ShaderNodeLightPath")
av = nt.nodes.new("ShaderNodeValue"); av.name = "FlashAlpha"; av.outputs[0].default_value = 0.0
mul = nt.nodes.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'; nt.links.new(lp.outputs["Is Camera Ray"], mul.inputs[0]); nt.links.new(av.outputs[0], mul.inputs[1])
mx = nt.nodes.new("ShaderNodeMixShader"); nt.links.new(mul.outputs[0], mx.inputs["Fac"]); nt.links.new(tr.outputs["BSDF"], mx.inputs[1]); nt.links.new(em.outputs["Emission"], mx.inputs[2])
nt.links.new(mx.outputs["Shader"], nt.nodes["Material Output"].inputs["Surface"])
FL.data.materials.append(fm)
FL.visible_shadow = False; FL.visible_diffuse = False; FL.visible_glossy = False; FL.visible_transmission = False
for c in list(FL.users_collection): c.objects.unlink(FL)
sc.collection.objects.link(FL)
FL.parent = CAM; FL.matrix_parent_inverse = Matrix.Identity(4); FL.location = (0, 0, 0); FL.scale = (0.042,) * 3
for f, r_ in ((1, 0.042), (140, 0.042), (147, 0.075), (157, 0.075), (1120, 0.042), (END, 0.042)):
    FL.scale = (r_,) * 3; FL.keyframe_insert("scale", frame=f)
VA = av.outputs[0]
for f, a_ in ((1, 0.0), (127, 0.0), (133, 1.0), (147, 1.0), (157, 0.0), (1130, 0.0), (1135, 1.0), (1139, 1.0), (1144, 0.0), (END, 0.0)):
    VA.default_value = a_; VA.keyframe_insert("default_value", frame=f)
vis(FL, 1, False); vis(FL, 126, True); vis(FL, 158, False); vis(FL, 1129, True); vis(FL, 1145, False)

# ================================================================== set visibility (keyed hide_render + hide_viewport on every object)
HOME = [o for o in bpy.data.collections["HOME"].all_objects]
MACRO = [o for o in bpy.data.collections["MACRO"].all_objects]
for o in HOME:
    vis(o, 1, True); vis(o, SWAP1, False); vis(o, SWAP2, True)
for o in MACRO:
    vis(o, 1, False); vis(o, SWAP1, True); vis(o, SWAP2, False)
# objects keyed above keep their own extra keys (bullet, trail, crack, hole): re-apply theirs on top
vis(CRACK, 1, False); vis(CRACK, 30, True); vis(CRACK, SWAP1, False); vis(CRACK, SWAP2, True)

# ================================================================== VO, output, render
sc.frame_start, sc.frame_end = 1, END
if not sc.sequence_editor: sc.sequence_editor_create()
se = sc.sequence_editor; strips = se.strips if hasattr(se, "strips") else se.sequences
snd = strips.new_sound("VO", VO, 1, 1)
sc.render.filepath = "//render/BellyFat_v018_####.png"; sc.render.image_settings.file_format = 'PNG'
for o in O:
    for m in getattr(o, "modifiers", []):
        if m.type == 'SUBSURF': m.show_viewport = False
log("quat flips fixed", quat_continuity(WR))
sc.frame_set(1)
open(os.path.join(os.path.dirname(OUT), "animate_log.txt"), "w").write("\n".join(LOG))
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("ANIM_DONE", OUT)
