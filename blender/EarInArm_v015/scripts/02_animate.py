"""EarInArm v015 stage B: staging, acting, the one-model ear story, x-ray, the one continuous camera.
blender -b base.blend --python 02_animate.py -- <out.blend>
Timing is built on the client's VO from the start (beats.json): 1,109,301,463,649,907,1129,1267,1447; end 1572."""
import bpy, bmesh, sys, math, random
from mathutils import Vector, Matrix, Quaternion, Euler
PIPE = "/home/user/Muhammed/blender/pipeline"
exec(open(PIPE + "/anim_lib.py").read())
exec(open(PIPE + "/hand_poses.py").read())
OUT = sys.argv[sys.argv.index("--") + 1]
random.seed(11)
sc = bpy.context.scene
END = 1572
O = bpy.data.objects
PAT, DOC = O["Patient"], O["Surgeon"]
PB, DB = O["Patient.body"], O["Surgeon.body"]
EAR, FORC, SCAL, NEED, TRAY, TH = O["Ear"], O["Forceps"], O["Scalpel"], O["NeedleHolder"], O["Tray"], O["RibCage"]
LOG = []
def log(*a):
    s = " ".join(str(x) for x in a); LOG.append(s); print("LOG", s)

# speed: viewport (evaluation) without subdivision; render keeps it
for o in O:
    for m in getattr(o, "modifiers", []):
        if m.type == 'SUBSURF': m.show_viewport = False

def upd(): bpy.context.view_layer.update()
def fs(f): sc.frame_set(int(f))
def W(rig, bone): return rig.matrix_world @ rig.pose.bones[bone].matrix
def Wh(rig, bone): return rig.matrix_world @ rig.pose.bones[bone].head
def Wt(rig, bone): return rig.matrix_world @ rig.pose.bones[bone].tail

def frame_from(y_dir, z_hint, origin):
    y = Vector(y_dir).normalized(); z = Vector(z_hint); z = (z - y * z.dot(y)).normalized(); x = y.cross(z)
    M = Matrix((x, y, z)).transposed().to_4x4(); M.translation = Vector(origin); return M

def set_interp(obj_or_data, kind='CONSTANT', path_contains=None):
    ad = obj_or_data.animation_data
    if not ad or not ad.action: return
    for fc in iter_fcurves(ad.action):
        if path_contains and path_contains not in fc.data_path: continue
        for kp in fc.keyframe_points: kp.interpolation = kind

def iter_fcurves(action):
    try:
        for fc in action.fcurves: yield fc
    except AttributeError:
        for layer in action.layers:
            for strip in layer.strips:
                for cb in strip.channelbags:
                    for fc in cb.fcurves: yield fc

# ================================================================== trolley closer to the surgeon, tray at waist height (Mayo-stand style)
TR_OFF = Vector((0.12, -0.02, 0.15))
for o in list(O):
    if o.name.startswith(("Trolley", "Tray")):
        o.location.x += TR_OFF.x; o.location.y += TR_OFF.y
        if o.name.startswith(("TrolleyTop", "TrolleyDrape", "Tray")): o.location.z += TR_OFF.z
        if o.name.startswith("TrolleyLeg"): o.location.z += TR_OFF.z / 2; o.scale.z *= (0.82 + TR_OFF.z) / 0.82

# ================================================================== rigs
PR = make_human_ctrl(PAT)
DR = make_human_ctrl(DOC)
add_hand_limits(PAT); add_hand_limits(DOC)
for s_ in "LR":
    for c in list(DOC.pose.bones["wrist." + s_].constraints):
        if c.name == "HandLimit": DOC.pose.bones["wrist." + s_].constraints.remove(c)
for s in "LR":   # patient arms are posed FK (resting on supports); legs keep IK
    PAT.pose.bones["lowerarm02." + s].constraints["IK"].influence = 0.0
    for c in PAT.pose.bones["wrist." + s].constraints:
        if c.type == 'COPY_ROTATION': c.influence = 0.0
DOC.location = (-0.48, 0.15, 0.0); DOC.rotation_euler = (0, 0, math.radians(14))
HP, HD = Human(PR), Human(DR)
for pb in list(PAT.pose.bones) + list(DOC.pose.bones):
    pb.rotation_mode = 'QUATERNION'

# ================================================================== patient: seated, static support contacts (R2/R3)
HP.key_root(1, Vector((0, 0.13, 0.60)), flex=-7.0)
HP.key_spine(1, flex=6.0)
for s in "LR":
    a = PR.BN["foot." + s].head_local
    tgt = Vector((a.x * 1.25, -0.40, a.z))
    PR.key_world("IK_foot." + s, 1, Matrix.Translation(tgt - a) @ PR.rest("IK_foot." + s))
    n = "Pole_knee." + s; pb = PR.PB[n]
    pb.location = PR.rest(n).to_3x3().inverted() @ (Vector((a.x * 1.3, -1.2, 0.75)) - PR.BN[n].head_local)
    pb.keyframe_insert("location", frame=1, group=n)
fs(1)

def aim_bone(rig, name, direction, twist=0.0, f=1):
    """FK: rotate pose bone so its Y axis points along `direction` (armature space), minimal swing, then twist about it"""
    upd(); pb = rig.pose.bones[name]; cur = pb.matrix.copy()
    y = cur.col[1].to_3d().normalized(); q = y.rotation_difference(Vector(direction).normalized())
    R = q.to_matrix() @ cur.to_3x3().normalized()
    if twist: R = Matrix.Rotation(twist, 3, Vector(direction).normalized()) @ R
    M = R.to_4x4(); M.translation = cur.translation; pb.matrix = M; upd()
    pb.keyframe_insert("rotation_quaternion", frame=f, group=name)

def twist_of(q):
    t = Quaternion((q.w, 0, q.y, 0));
    if t.magnitude < 1e-6: return 0.0
    t.normalize(); return 2 * math.atan2(t.y, t.w)

def pose_hand_world(rig, s, fdir, palm_dir, f=1, share=0.5):
    """orient wrist: fingers along fdir, palm facing palm_dir (armature space). Twist shared with the forearm twist bone (R6)."""
    wr, B0, basis, palm = _rest_hand(rig, s)
    sign = _rest_palm_sign(rig, s, B0.col[2])
    Rm = basis(Vector(fdir), Vector(palm_dir) * sign) @ B0.transposed()
    Wd = Rm @ rig.data.bones["wrist." + s].matrix_local.to_3x3()
    upd()
    for it in range(2):
        L2 = rig.pose.bones["lowerarm02." + s]; rel = (L2.matrix.to_3x3().normalized().inverted() @ Wd).to_quaternion()
        rel_rest = (rig.data.bones["lowerarm02." + s].matrix_local.to_3x3().inverted() @ rig.data.bones["wrist." + s].matrix_local.to_3x3()).to_quaternion()
        local = rel @ rel_rest.inverted()
        tw = twist_of(local)
        if abs(tw) < math.radians(3): break
        q = L2.rotation_quaternion.copy() @ Quaternion((0, 1, 0), tw * share)
        L2.rotation_quaternion = q; upd()
    rig.pose.bones["lowerarm02." + s].keyframe_insert("rotation_quaternion", frame=f, group="lowerarm02." + s)
    pb = rig.pose.bones["wrist." + s]; M = Wd.to_4x4(); M.translation = pb.matrix.translation; pb.matrix = M; upd()
    pb.keyframe_insert("rotation_quaternion", frame=f, group="wrist." + s)

def pose_arm(rig, s, elbow_dir, fore_dir, fdir, palm, f=1):
    for n in ("upperarm01.", "upperarm02.", "lowerarm01.", "lowerarm02.", "wrist."):
        rig.pose.bones[n + s].rotation_quaternion = Quaternion()
    upd()
    aim_bone(rig, "upperarm01." + s, elbow_dir, f=f)
    rig.pose.bones["upperarm02." + s].keyframe_insert("rotation_quaternion", frame=f)
    aim_bone(rig, "lowerarm01." + s, fore_dir, f=f)
    pose_hand_world(rig, s, fdir, palm, f=f)

# right arm out on the arm board (palm up), left forearm along the armrest (palm down)
pose_arm(PAT, "R", Vector((-0.42, -0.30, -0.86)), Vector((-0.80, -0.52, -0.06)), Vector((-0.80, -0.56, -0.08)), Vector((0, 0, 1)))
pose_arm(PAT, "L", Vector((0.30, -0.25, -0.92)), Vector((0.10, -0.99, -0.02)), Vector((0.08, -0.99, -0.10)), Vector((0, 0, -1)))
apply_pose(PAT, "R", "relaxed", 1); apply_pose(PAT, "L", "shield", 1)
fs(1)

def eval_mesh_points(obj, filt=None):
    """world coords of the evaluated mesh (masks off so indices = mesh indices)"""
    saved = []
    for m in obj.modifiers:
        if m.type in ('MASK', 'SUBSURF'): saved.append((m, m.show_viewport)); m.show_viewport = False
    upd(); dg = bpy.context.evaluated_depsgraph_get(); ev_ = obj.evaluated_get(dg); me = ev_.to_mesh()
    pts = [(v.index, obj.matrix_world @ v.co, (obj.matrix_world.to_3x3() @ v.normal).normalized()) for v in me.vertices]
    ev_.to_mesh_clear()
    for m, sv in saved: m.show_viewport = sv
    upd()
    return pts if filt is None else [p for p in pts if filt(p[0])]

def dom_bones(body, rig):
    names = {b.name for b in rig.data.bones}; i2n = {g.index: g.name for g in body.vertex_groups if g.name in names}
    out = {}
    for v in body.data.vertices:
        best = (0, None)
        for g in v.groups:
            n = i2n.get(g.group)
            if n and g.weight > best[0]: best = (g.weight, n)
        out[v.index] = best[1]
    return out
DOMP = dom_bones(PB, PAT)

def fit_support(name, side, width, thick, post_obj=None, extend=(0.07, 0.05)):
    """R2: build the arm support exactly under the forearm + hand (top plane through the lowest points)."""
    sel = {i for i, b in DOMP.items() if b and b.endswith("." + side) and any(b.startswith(k) for k in ("lowerarm", "wrist", "finger", "metacarpal"))}
    pts = eval_mesh_points(PB, lambda i: i in sel)
    E = Wh(PAT, "lowerarm01." + side); Wr = Wh(PAT, "wrist." + side)
    ax = (Wr - E); ax.z = 0; ax.normalize(); lat = Vector((-ax.y, ax.x, 0))
    ts = [(p[1] - E).dot(ax) for p in pts]; t0, t1 = min(ts), max(ts)
    bins = {}
    for p, t in zip(pts, ts):
        b = int((t - t0) / max(1e-6, (t1 - t0)) * 8.999); bins.setdefault(b, []).append(p[1].z)
    lo = [(t0 + (b + 0.5) * (t1 - t0) / 9, min(z)) for b, z in sorted(bins.items())]
    # contoured cushion: the top follows the lowest skin line of the forearm + hand (soft vinyl pad), 1.5 mm under it
    zb = [z for _, z in lo]; tb_ = [t for t, _ in lo]
    zs_ = [min(zb[i], (zb[max(0, i - 1)] + zb[min(len(zb) - 1, i + 1)]) / 2) - 0.0015 for i in range(len(zb))]
    def ztop(t):
        if t <= tb_[0]: return zs_[0]
        if t >= tb_[-1]: return zs_[-1]
        for i in range(len(tb_) - 1):
            if tb_[i] <= t <= tb_[i + 1]:
                u = (t - tb_[i]) / (tb_[i + 1] - tb_[i]); return zs_[i] * (1 - u) + zs_[i + 1] * u
    gap = [round(z - ztop(t), 4) for t, z in lo]
    lats = [(p[1] - E).dot(lat) for p in pts]; lm = (max(lats) + min(lats)) / 2
    ta, tb = t0 - extend[0], t1 + extend[1]
    rows = [ta] + [t for t in tb_ if ta < t < tb] + [tb]
    zbot = min(ztop(t) for t in rows) - thick
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    T_ = []; B_ = []
    for t in rows:
        r_ = []; rb = []
        for u in (lm - width / 2, lm + width / 2):
            base = E + ax * t + lat * u
            r_.append(bm.verts.new((base.x, base.y, ztop(t)))); rb.append(bm.verts.new((base.x, base.y, zbot)))
        T_.append(r_); B_.append(rb)
    for i in range(len(rows) - 1):
        bm.faces.new([T_[i][0], T_[i][1], T_[i + 1][1], T_[i + 1][0]])
        bm.faces.new([B_[i][0], B_[i + 1][0], B_[i + 1][1], B_[i][1]])
        bm.faces.new([T_[i][0], T_[i + 1][0], B_[i + 1][0], B_[i][0]])
        bm.faces.new([T_[i][1], B_[i][1], B_[i + 1][1], T_[i + 1][1]])
    bm.faces.new([T_[0][0], B_[0][0], B_[0][1], T_[0][1]]); bm.faces.new([T_[-1][0], T_[-1][1], B_[-1][1], B_[-1][0]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:]); bm.to_mesh(me); bm.free()
    ob = O.get(name)
    if ob: bpy.data.objects.remove(ob, do_unlink=True)
    ob = bpy.data.objects.new(name, me); sc.collection.objects.link(ob)
    me.materials.append(bpy.data.materials["M_Vinyl"])
    bv = ob.modifiers.new("bev", 'BEVEL'); bv.width = 0.012; bv.segments = 4; bv.limit_method = 'ANGLE'; bv.angle_limit = math.radians(50)
    for p in me.polygons: p.use_smooth = True
    k = 0.0
    mid = E + ax * ((ta + tb) / 2) + lat * lm
    log("support", name, "gaps(m)", gap, "top_mid_z", round(ztop((ta + tb) / 2), 3))
    return ob, Vector((mid.x, mid.y, zbot))

for n in ("ArmBoard", "ChairArmL"):
    bpy.data.objects.remove(O[n], do_unlink=True)
board, board_bot = fit_support("ArmBoard", "R", 0.15, 0.045)
arm_l, arml_bot = fit_support("ChairArmL", "L", 0.11, 0.055, extend=(0.10, 0.04))
# posts under the supports, down to the floor / seat frame
post = O["ArmBoardPost"]; post.location = (board_bot.x, board_bot.y, board_bot.z / 2); post.scale.z = board_bot.z / 0.60
O["ArmBoardFoot"].location = (board_bot.x, board_bot.y, 0.015)
for o in [o for o in O if o.name.startswith("ChairArmPost")]:
    o.location = (arml_bot.x, arml_bot.y + 0.06, (arml_bot.z + 0.50) / 2); o.scale.z = max(0.2, (arml_bot.z - 0.45) / 0.18)

# R3: seat top snapped under the trousers (pelvis on the seat, 3 mm cushion press)
trs = O["Patient.trousers"]
upd(); dg = bpy.context.evaluated_depsgraph_get(); ev_ = trs.evaluated_get(dg); me = ev_.to_mesh()
zs = [(trs.matrix_world @ v.co) for v in me.vertices]
seat_pts = [p.z for p in zs if abs(p.x) < 0.2 and -0.15 < p.y < 0.22]
ev_.to_mesh_clear()
seat_top = min(seat_pts) + 0.003
dz = seat_top - 0.52
for nme in ("ChairSeat", "ChairBack"):
    O[nme].location.z += dz
O["ChairColumn"].scale.z = max(0.3, (O["ChairSeat"].location.z - 0.05 - 0.06) / 0.36); O["ChairColumn"].location.z = 0.06 + (O["ChairSeat"].location.z - 0.05 - 0.06) / 2
log("seat_top", round(seat_top, 3), "dz", round(dz, 3))

# ================================================================== patient head acting (keyed before any anchor is measured)
def key_head(f, yaw, pitch, roll=0.0):
    for n, w in (("neck01", 0.25), ("neck02", 0.25), ("neck03", 0.2), ("head", 0.3)):
        PR.key_rot(n, f, [("X", pitch * w), ("Y", roll * w), ("Z", yaw * w)])
HEADK = [(1, 12, 6), (50, 18, 3), (105, 16, 0), (150, 4, 14), (230, -6, 18), (300, -26, 8), (420, -30, 10), (470, -34, 22), (640, -34, 24),
         (700, -36, 26), (880, -32, 24), (960, -36, 26), (1080, -10, 8), (1120, 14, 0), (1440, 14, 0), (1500, 4, -2), (1572, -4, -3)]
for f, yw, pt in HEADK:
    key_head(f, yw, pt)

# ================================================================== anchors
fs(1)
head_c = Wh(PAT, "head")
EAR_SITE_REST = Vector(sc["ear_site_rest"])
def site_world():
    """the healed earless site (closest evaluated skin point to the rest site, through the head bone)"""
    hb = PAT.pose.bones["head"]; Mh = PAT.matrix_world @ hb.matrix @ PAT.data.bones["head"].matrix_local.inverted()
    p = Mh @ EAR_SITE_REST
    pts = eval_mesh_points(PB, lambda i: DOMP.get(i) == "head")
    best = min(pts, key=lambda q: (q[1] - p).length)
    return best[1], best[2]
SITE0, SITEN0 = site_world()
log("site", tuple(round(x, 3) for x in SITE0), "n", tuple(round(x, 2) for x in SITEN0))

# forearm ear spot: the most upward-facing skin point at 55% along the right forearm (volar side, palm up)
E_ = Wh(PAT, "lowerarm01.R"); Wr_ = Wh(PAT, "wrist.R"); fax = (Wr_ - E_).normalized()
fsel = {i for i, b in DOMP.items() if b in ("lowerarm01.R", "lowerarm02.R")}
fpts = eval_mesh_points(PB, lambda i: i in fsel)
cand = [p for p in fpts if 0.42 < (p[1] - E_).dot(Wr_ - E_) / (Wr_ - E_).length_squared < 0.62]
spot = max(cand, key=lambda p: p[2].z + 2.0 * p[1].z)
ARM_PT, ARM_N, ARM_IDX = spot[1], spot[2], spot[0]
ARM_N = (ARM_N * 0.5 + Vector((0, 0, 0.5))).normalized()
log("arm spot", tuple(round(x, 3) for x in ARM_PT), "n", tuple(round(x, 2) for x in ARM_N))

# ---- mound shape key on the patient's forearm (the pocket bump that grows), rest space around ARM_IDX
if not PB.data.shape_keys: PB.shape_key_add(name="Basis")
mk = PB.shape_key_add(name="mound"); mk.value = 0.0
crest = PB.data.vertices[ARM_IDX].co.copy()
rest_n = PB.data.vertices[ARM_IDX].normal.copy()
ax_rest = (PAT.data.bones["wrist.R"].head_local - PAT.data.bones["lowerarm01.R"].head_local).normalized()
for v in PB.data.vertices:
    if DOMP.get(v.index) not in ("lowerarm01.R", "lowerarm02.R", "wrist.R"): continue
    d = v.co - crest; along = d.dot(ax_rest); across = (d - ax_rest * along).length
    r = math.sqrt((along / 0.050) ** 2 + (across / 0.034) ** 2)
    if r < 1.0 and v.normal.dot(rest_n) > 0.2:
        mk.data[v.index].co = v.co + v.normal * 0.009 * (1 - r * r) ** 2

# ================================================================== shader: localized x-ray (skin + tee), driven by keyed values
xg = bpy.data.node_groups.new("XRay", 'ShaderNodeTree')
xg.interface.new_socket("Shader", in_out='INPUT', socket_type='NodeSocketShader')
xg.interface.new_socket("Shader", in_out='OUTPUT', socket_type='NodeSocketShader')
gi_ = xg.nodes.new("NodeGroupInput"); go_ = xg.nodes.new("NodeGroupOutput")
MASK_E = bpy.data.objects.new("XrayMask", None); sc.collection.objects.link(MASK_E); MASK_E.empty_display_size = 0.05
tc = xg.nodes.new("ShaderNodeTexCoord"); tc.object = MASK_E
ln = xg.nodes.new("ShaderNodeVectorMath"); ln.operation = 'LENGTH'; xg.links.new(tc.outputs["Object"], ln.inputs[0])
mr = xg.nodes.new("ShaderNodeMapRange"); mr.interpolation_type = 'SMOOTHSTEP'
mr.inputs["From Min"].default_value = 0.75; mr.inputs["From Max"].default_value = 1.0; mr.inputs["To Min"].default_value = 1.0; mr.inputs["To Max"].default_value = 0.0
xg.links.new(ln.outputs["Value"], mr.inputs["Value"])
strength = xg.nodes.new("ShaderNodeValue"); strength.name = "XStrength"; strength.outputs[0].default_value = 0.0
mul = xg.nodes.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'
xg.links.new(mr.outputs["Result"], mul.inputs[0]); xg.links.new(strength.outputs[0], mul.inputs[1])
geo = xg.nodes.new("ShaderNodeNewGeometry")
tr = xg.nodes.new("ShaderNodeBsdfTransparent"); tr.inputs["Color"].default_value = (0.92, 0.97, 1.0, 1)
lw = xg.nodes.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.35
em = xg.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (0.45, 0.85, 1.0, 1); em.inputs["Strength"].default_value = 1.4
rim = xg.nodes.new("ShaderNodeMixShader"); xg.links.new(lw.outputs["Facing"], rim.inputs["Fac"])
xg.links.new(tr.outputs["BSDF"], rim.inputs[1]); xg.links.new(em.outputs["Emission"], rim.inputs[2])
# inside faces (seen through the window) read as a clean blue x-ray backdrop
bk = xg.nodes.new("ShaderNodeEmission"); bk.inputs["Color"].default_value = (0.45, 0.78, 0.97, 1); bk.inputs["Strength"].default_value = 1.0
inv = xg.nodes.new("ShaderNodeMath"); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0; xg.links.new(mr.outputs["Result"], inv.inputs[1])
bko = xg.nodes.new("ShaderNodeMath"); bko.operation = 'MULTIPLY'; xg.links.new(geo.outputs["Backfacing"], bko.inputs[0]); xg.links.new(inv.outputs[0], bko.inputs[1])
inner = xg.nodes.new("ShaderNodeMixShader"); xg.links.new(bko.outputs[0], inner.inputs["Fac"])
xg.links.new(rim.outputs["Shader"], inner.inputs[1]); xg.links.new(bk.outputs["Emission"], inner.inputs[2])
mx_ = xg.nodes.new("ShaderNodeMath"); mx_.operation = 'MAXIMUM'; xg.links.new(mr.outputs["Result"], mx_.inputs[0]); xg.links.new(geo.outputs["Backfacing"], mx_.inputs[1])
fm = xg.nodes.new("ShaderNodeMath"); fm.operation = 'MULTIPLY'; xg.links.new(mx_.outputs[0], fm.inputs[0]); xg.links.new(strength.outputs[0], fm.inputs[1])
fin = xg.nodes.new("ShaderNodeMixShader"); xg.links.new(fm.outputs[0], fin.inputs["Fac"])
xg.links.new(gi_.outputs[0], fin.inputs[1]); xg.links.new(inner.outputs["Shader"], fin.inputs[2])
xg.links.new(fin.outputs["Shader"], go_.inputs[0])
def add_xray(m):
    nt = m.node_tree; out = [n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output] or [n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL']
    out = out[0]; src = out.inputs["Surface"].links[0].from_socket
    g = nt.nodes.new("ShaderNodeGroup"); g.node_tree = xg
    nt.links.new(src, g.inputs[0]); nt.links.new(g.outputs[0], out.inputs["Surface"])
for m in PB.data.materials:
    if m and m.use_nodes: add_xray(m)
add_xray(bpy.data.materials["M_PatientTee"])
XS = xg.nodes["XStrength"].outputs[0]
def key_x(f, v):
    XS.default_value = v; XS.keyframe_insert("default_value", frame=f)
def key_mask(f, loc, r):
    MASK_E.location = loc; MASK_E.scale = (r, r, r)
    MASK_E.keyframe_insert("location", frame=f); MASK_E.keyframe_insert("scale", frame=f)
    set_interp(MASK_E, 'CONSTANT')

# ================================================================== the ear: block shape key, skin-creep material
def make_block_key():
    me = EAR.data
    if not me.shape_keys: EAR.shape_key_add(name="Basis")
    kb = EAR.shape_key_add(name="block")
    vs = me.vertices
    cx = sum(v.co.x for v in vs) / len(vs); cz = sum(v.co.z for v in vs) / len(vs); cy = sum(v.co.y for v in vs) / len(vs)
    bins = {}
    for v in vs:
        th = math.atan2(v.co.z - cz, v.co.x - cx); r = math.hypot(v.co.z - cz, v.co.x - cx)
        b = int((th + math.pi) / (2 * math.pi) * 36) % 36; bins[b] = max(bins.get(b, 0), r)
    hx, hz, hy = 0.0215 / 0.78, 0.0285 / 0.78, 0.0068 / 0.78     # slab a little bigger than the carved ear
    for v in vs:
        dx, dz = v.co.x - cx, v.co.z - cz; th = math.atan2(dz, dx); r = math.hypot(dx, dz)
        b = int((th + math.pi) / (2 * math.pi) * 36) % 36; rout = max(1e-6, bins[b])
        c, s_ = math.cos(th), math.sin(th)
        # rounded-rectangle radius at angle th (superellipse n=6)
        rb = 1.0 / ((abs(c) / hx) ** 6 + (abs(s_) / hz) ** 6) ** (1 / 6)
        u = min(1.0, r / rout) ** 0.6
        ny = v.normal.y
        y = cy + (-hy if ny < -0.3 else hy if ny > 0.3 else (v.co.y - cy) * 0.6)
        kb.data[v.index].co = Vector((cx + c * rb * u, y, cz + s_ * rb * u))
    # relax the slab (no creases)
    nb = {i: [] for i in range(len(vs))}
    for e in me.edges:
        nb[e.vertices[0]].append(e.vertices[1]); nb[e.vertices[1]].append(e.vertices[0])
    for _ in range(12):
        new = [kb.data[i].co.copy() for i in range(len(vs))]
        for i in range(len(vs)):
            if nb[i]:
                avg = sum((kb.data[j].co for j in nb[i]), Vector()) / len(nb[i]); new[i] = kb.data[i].co.lerp(avg, 0.5)
        for i in range(len(vs)): kb.data[i].co = new[i]
    return kb
BLOCK = make_block_key()
BLOCK.value = 1.0

# skin colour of the patient (mean of the diffuse texture, times the tint)
skin_col = Vector((0.78, 0.52, 0.42))
for m in PB.data.materials:
    for nd in (m.node_tree.nodes if m and m.use_nodes else []):
        if nd.type == 'TEX_IMAGE' and nd.image and "diffuse" in nd.image.name.lower() and nd.image.size[0] > 0:
            px = nd.image.pixels[:]; n = len(px) // 4; step = max(1, n // 20000)
            acc = Vector((0, 0, 0)); cnt = 0
            for i in range(0, n, step):
                if px[i * 4 + 3] > 0.5: acc += Vector(px[i * 4:i * 4 + 3]); cnt += 1
            if cnt: skin_col = Vector((acc.x / cnt, acc.y / cnt, acc.z / cnt)) * Vector((1.0, 0.93, 0.88)); break
log("skin_col", tuple(round(x, 3) for x in skin_col))
em_ = EAR.data.materials[0]; nt = em_.node_tree; p = nt.nodes["Principled BSDF"]
skin_p = nt.nodes.new("ShaderNodeBsdfPrincipled")
lwE = nt.nodes.new("ShaderNodeLayerWeight"); lwE.inputs["Blend"].default_value = 0.45
rampE = nt.nodes.new("ShaderNodeValToRGB"); rampE.color_ramp.elements[0].color = (0.78, 0.40, 0.33, 1); rampE.color_ramp.elements[1].color = (0.42, 0.15, 0.13, 1)
rampE.color_ramp.elements[0].position = 0.35
nt.links.new(lwE.outputs["Facing"], rampE.inputs["Fac"]); nt.links.new(rampE.outputs["Color"], skin_p.inputs["Base Color"])
rampC = nt.nodes.new("ShaderNodeValToRGB"); rampC.color_ramp.elements[0].color = (0.90, 0.86, 0.74, 1); rampC.color_ramp.elements[1].color = (0.58, 0.52, 0.40, 1)
rampC.color_ramp.elements[0].position = 0.35
nt.links.new(lwE.outputs["Facing"], rampC.inputs["Fac"]); nt.links.new(rampC.outputs["Color"], p.inputs["Base Color"]); skin_p.inputs["Roughness"].default_value = 0.45
skin_p.inputs["Subsurface Weight"].default_value = 0.0; skin_p.inputs["Subsurface Radius"].default_value = (0.9, 0.35, 0.2); skin_p.inputs["Subsurface Scale"].default_value = 0.003
p.inputs["Alpha"].default_value = 1.0; p.inputs["Coat Weight"].default_value = 0.0; p.inputs["Roughness"].default_value = 0.55
tc2 = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc2.outputs["Object"], sep.inputs[0])
edge = nt.nodes.new("ShaderNodeValue"); edge.name = "SkinEdge"; edge.outputs[0].default_value = -0.06
sub = nt.nodes.new("ShaderNodeMath"); sub.operation = 'SUBTRACT'; nt.links.new(edge.outputs[0], sub.inputs[0]); nt.links.new(sep.outputs["Z"], sub.inputs[1])
mr2 = nt.nodes.new("ShaderNodeMapRange"); mr2.interpolation_type = 'SMOOTHSTEP'; mr2.inputs["From Min"].default_value = -0.004; mr2.inputs["From Max"].default_value = 0.004
nt.links.new(sub.outputs[0], mr2.inputs["Value"])
mx = nt.nodes.new("ShaderNodeMixShader"); nt.links.new(mr2.outputs["Result"], mx.inputs["Fac"])
nt.links.new(p.outputs["BSDF"], mx.inputs[1]); nt.links.new(skin_p.outputs["BSDF"], mx.inputs[2])
nt.links.new(mx.outputs["Shader"], nt.nodes["Material Output"].inputs["Surface"])
EDGE = edge.outputs[0]; EALPHA = p.inputs["Alpha"]
def key_edge(f, v): EDGE.default_value = v; EDGE.keyframe_insert("default_value", frame=f)
def key_ealpha(f, v): EALPHA.default_value = v; EALPHA.keyframe_insert("default_value", frame=f)
key_edge(1, -0.06); key_ealpha(1, 1.0)

# ================================================================== surgeon tools: Child Of the wrist bone (R4)
TOOLS = {}
def tool_setup(tool, side, pose, grip_y):
    fs(0)
    apply_pose(DOC, side, pose, 0); apply_pose(DOC, side, pose, 1); upd()
    th = Wt(DOC, "finger1-3." + side); ix = Wt(DOC, "finger2-3." + side)
    G = (th + ix) / 2 + (Wh(DOC, "finger2-2." + side) - th).normalized() * 0.004
    fdir = (Wt(DOC, "finger2-3." + side) - Wh(DOC, "finger2-1." + side)).normalized()
    Mw = W(DOC, "wrist." + side)
    back = (Mw.to_3x3() @ Vector((0, 0, 1)))
    wr, B0, basis, palm = _rest_hand(DOC, side); sign = _rest_palm_sign(DOC, side, B0.col[2])
    pal = (Mw.to_3x3() @ (PAT.data.bones["wrist." + side].matrix_local.to_3x3().inverted() @ B0.col[2])) if False else None
    # palm normal in world: rest palm normal (B0 col 2 * sign) carried by the wrist's pose rotation
    Rpose = (DOC.matrix_world.to_3x3() @ DOC.pose.bones["wrist." + side].matrix.to_3x3() @ DOC.data.bones["wrist." + side].matrix_local.to_3x3().inverted())
    palmN = (Rpose @ (B0.col[2] * sign)).normalized()
    ydir = (fdir - palmN * fdir.dot(palmN) * 0.5).normalized()
    T = frame_from(ydir, -palmN, G)
    T = T @ Matrix.Translation(Vector((0, -grip_y, 0)))
    tool.matrix_world = T
    c = tool.constraints.new('CHILD_OF'); c.name = "Hand"; c.target = DOC; c.subtarget = "wrist." + side
    c.inverse_matrix = (DOC.matrix_world @ DOC.pose.bones["wrist." + side].matrix).inverted()
    c.set_inverse_pending = False
    tool.keyframe_insert("location", frame=0); tool.keyframe_insert("rotation_euler", frame=0)
    off = Mw.inverted() @ T
    TOOLS[tool.name] = dict(side=side, off=off, tip=Vector((0, max(v.co.y for v in tool.data.vertices), 0)))
    return off
tool_setup(FORC, "L", "pinch", -0.012)
tool_setup(SCAL, "R", "tripod", -0.030)
tool_setup(NEED, "R", "tripod", -0.040)
NEED.constraints["Hand"].influence = 0.0
for t in (FORC, SCAL, NEED):
    t.constraints["Hand"].keyframe_insert("influence", frame=0)

SH = {s: None for s in "LR"}
def shoulder(side):
    return Wh(DOC, "upperarm01." + side)

EUL = [(x, y, z) for x in range(-40, 41, 10) for y in range(-30, 31, 15) for z in range(-24, 25, 12)]
def key_tool(tool, f, Tdes, fix=True):
    """key IK_hand so the tool TIP lands on Tdes's tip. The wrist keeps a natural in-limit bend (small angles preferred,
    Tdes's direction only as a weak wish): the tool points where the hand naturally points (R6, no helicopter wrists)."""
    info = TOOLS[tool.name]; s = info["side"]; off = info["off"]; tipL = info["tip"]
    tip = Tdes @ tipL; want_y = Tdes.to_3x3().col[1].normalized(); want_z = Tdes.to_3x3().col[2].normalized()
    L2r = DOC.data.bones["lowerarm02." + s].matrix_local; Wr = DOC.data.bones["wrist." + s].matrix_local
    MW = DOC.matrix_world; MWi = MW.inverted()
    Wdes = Tdes @ off.inverted(); DR.key_world("IK_hand." + s, f, MWi @ Wdes)
    err = 9.0; best = None
    for it in range(10):
        fs(f)
        base = DOC.pose.bones["lowerarm02." + s].matrix @ L2r.inverted() @ Wr
        best = None
        for (ex, ey, ez) in EUL:
            q = Euler((math.radians(ex), math.radians(ey), math.radians(ez)), 'XYZ').to_matrix().to_4x4()
            R3 = (MW @ base @ q @ off).to_3x3().normalized()
            c = 0.6 * (1 - R3.col[1].normalized().dot(want_y)) + 0.2 * (1 - R3.col[2].normalized().dot(want_z)) + 0.00015 * (ex * ex + ey * ey + ez * ez)
            if best is None or c < best[0]: best = (c, base @ q, (ex, ey, ez))
        Wa = best[1].copy()
        tip_now = (MW @ Wa @ off) @ tipL
        Wa.translation = Wa.translation + MWi.to_3x3() @ (tip - tip_now)
        DR.key_world("IK_hand." + s, f, Wa)
        fs(f)
        tip_now = MW @ DOC.pose.bones["wrist." + s].matrix @ off @ tipL; err = (tip - tip_now).length
        base2 = DOC.pose.bones["lowerarm02." + s].matrix @ L2r.inverted() @ Wr
        e_ = (base2.inverted() @ DOC.pose.bones["wrist." + s].matrix).to_euler('XYZ')
        ok = abs(math.degrees(e_.x)) < 58 and abs(math.degrees(e_.y)) < 48 and abs(math.degrees(e_.z)) < 34
        if err < 0.0015 and ok: break
    return err
WANG = []
_kt_inner = key_tool
def key_tool(tool, f, Tdes, fix=True):
    err = _kt_inner(tool, f, Tdes, fix)
    s = TOOLS[tool.name]["side"]; fs(f)
    L2r = DOC.data.bones["lowerarm02." + s].matrix_local; Wr = DOC.data.bones["wrist." + s].matrix_local
    loc_ = (DOC.pose.bones["lowerarm02." + s].matrix @ L2r.inverted() @ Wr).inverted() @ DOC.pose.bones["wrist." + s].matrix
    WANG.append((f, tool.name, [round(math.degrees(x)) for x in loc_.to_euler('XYZ')], round(err * 1000, 1)))
    return err

def natural(tool, tip, down=0.55, aim=None, roll_up=Vector((0, 0, 1))):
    """a natural tool frame: pointing from the hand's shoulder toward the tip, tilted down; returns the tool matrix with its tip at `tip`"""
    s = TOOLS[tool.name]["side"]
    d = (Vector(tip) - shoulder(s)); d.z = 0; d.normalize()
    ydir = (d * (1 - down) + Vector((0, 0, -1)) * down).normalized() if aim is None else Vector(aim).normalized()
    M = frame_from(ydir, roll_up, Vector((0, 0, 0)))
    M.translation = Vector(tip) - M.to_3x3() @ TOOLS[tool.name]["tip"]
    return M

def ready(tool, f, dx=0.0, dz=0.0, fwd=0.30):
    """surgeon's ready hands: tools held in front of his own lower chest, pointing up-forward, clear of the patient"""
    s = TOOLS[tool.name]["side"]
    face = DOC.matrix_world.to_3x3() @ Vector((0, -1, 0)); lat = DOC.matrix_world.to_3x3() @ Vector((1, 0, 0))
    c0 = (Wh(DOC, "upperarm01.L") + Wh(DOC, "upperarm01.R")) / 2
    tip = c0 + face * (fwd - 0.06) + Vector((0, 0, -0.40 + dz)) + lat * ((0.02 if s == "L" else -0.09) + dx)
    M = natural(tool, tip, down=0.0, aim=(face + Vector((0, 0, 0.6))))
    e = key_tool(tool, f, M); ERR.append((f, tool.name, "ready", round(e * 1000, 1))); return e

ERR = []
def kt(tool, f, M, label=""):
    e = key_tool(tool, f, M); ERR.append((f, tool.name, label, round(e * 1000, 1)))
    if e > 0.003:
        s_ = TOOLS[tool.name]["side"]; fs(f)
        log("  reach", f, label, "shoulder->tip", round((shoulder(s_) - M @ TOOLS[tool.name]["tip"]).length, 3), "shoulder->wrist", round((shoulder(s_) - Wh(DOC, "wrist." + s_)).length, 3),
            "ik->wrist", round((DOC.matrix_world @ DOC.pose.bones["IK_hand." + s_].head - Wh(DOC, "wrist." + s_)).length, 3))
    return e

# body: feet planted, breathing + weight shift, lean and head look keyed per beat
fs(1)
for f in sorted(set(list(range(1, END + 1, 15)) + [455, 476, 508, 522, 548])):
    ph = f / 60.0
    sway = -0.085 * smooth((f - 200) / 60.0) * (1 - smooth((f - 545) / 50.0)) - 0.05 * smooth((f - 1000) / 30.0) * (1 - smooth((f - 1090) / 40.0))
    turn = pchip([(1, 0), (215, 0), (255, -34), (455, -34), (476, -12), (508, -12), (522, -30), (548, -30), (590, 0), (END, 0)])(f)
    HD.key_root(f, Vector((sway + 0.006 * math.sin(ph * 2 * math.pi / 3.2), 0.066, 0.983 - 0.004 * (1 + math.sin(ph * 2 * math.pi / 4.0)))), yaw=turn, flex=0)
# left elbow stays in FRONT of the torso while the left hand works across at the tray (pole forward-left, not behind)
def key_pole(rig_ctrl, side, f, target):
    n = "Pole_elbow." + side; pb = rig_ctrl.PB[n]
    pb.location = (Vector((0, 0, 0)) if target is None else rig_ctrl.rest(n).to_3x3().inverted() @ (Vector(target) - rig_ctrl.BN[n].head_local))
    pb.keyframe_insert("location", frame=f, group=n)
for f_, t_ in ((1, None), (200, None), (236, (0.55, -0.55, 1.05)), (556, (0.55, -0.55, 1.05)), (590, None)):
    key_pole(DR, "L", f_, t_)
LEAN = [(1, 4, 0, 0, -12), (140, 4, 0, 0, -12), (185, 18, 10, 0, -20), (230, 18, -10, 0, -22), (262, 20, -8, -2, -24), (300, 22, -10, -2, -28),
        (460, 22, -10, -2, -28), (490, 28, -4, 0, -30), (524, 26, -6, -1, -30), (560, 28, -6, 0, -30), (622, 30, -4, 0, -32), (665, 14, 0, 0, -18),
        (900, 14, 0, 0, -18), (945, 30, -4, 0, -32), (1016, 30, -2, 0, -32), (1052, 22, 4, 0, -24), (1150, 12, 14, 0, -12), (1420, 12, 14, 0, -12),
        (1480, 5, 6, 0, -6), (END, 4, 4, 0, -4)]
def key_lean(f, flex, twist, side, hp, hy=None):
    HD.key_spine(f, flex=flex, twist=twist, side=side, head=(hp, hy if hy is not None else twist * 0.8))
for f, fl, tw, sd, hp in LEAN:
    key_lean(f, fl, tw, sd, -hp)

# ================================================================== geometry helpers for the story
fs(1)
def tray_top(x, y):
    hit, loc, n, i = TRAY.ray_cast(TRAY.matrix_world.inverted() @ Vector((x, y, 2.0)), TRAY.matrix_world.inverted().to_3x3() @ Vector((0, 0, -1)))
    return (TRAY.matrix_world @ loc).z if hit else TRAY.location.z + 0.004
for m_ in TRAY.data.materials:
    if m_ and m_.use_nodes and "Principled BSDF" in m_.node_tree.nodes:
        pp_ = m_.node_tree.nodes["Principled BSDF"]
        for l_ in list(pp_.inputs["Roughness"].links): m_.node_tree.links.remove(l_)
        pp_.inputs["Roughness"].default_value = 0.5; pp_.inputs["Metallic"].default_value = 0.6
        for l_ in list(pp_.inputs["Base Color"].links): m_.node_tree.links.remove(l_)
        pp_.inputs["Base Color"].default_value = (0.22, 0.30, 0.36, 1)
TRAY_C = Vector((TRAY.location.x + 0.085, TRAY.location.y + 0.075, 0)); TRAY_C.z = tray_top(TRAY_C.x, TRAY_C.y)
log("tray top", round(TRAY_C.z, 4))

EAR_S0 = 0.78
EAR.scale = (EAR_S0,) * 3
ear_half_y = max(v.co.y for v in EAR.data.vertices)   # half thickness (local)
ear_top_z = max(v.co.z for v in EAR.data.vertices); ear_bot_z = min(v.co.z for v in EAR.data.vertices)

# canonical forceps->ear hold H: the ear's lobe end in the tips, the ear extends along the forceps, pitched up 30 deg
H = Matrix.Rotation(math.radians(30), 4, 'X') @ Matrix.Translation(Vector((0, 0, 0)))
def hold_matrix(tip_local):
    # ear frame relative to the forceps: ear z (top) along forceps +Y rotated up, ear -y (face) along forceps +Z
    R = Matrix(((1, 0, 0), (0, 0, 1), (0, -1, 0))).to_4x4()        # forceps axes -> ear axes: ear z = forceps y, ear y = -forceps z
    R = Matrix.Rotation(math.radians(30), 4, 'X') @ R
    M = Matrix.Translation(tip_local) @ R
    # lobe end at the tip: shift along ear z by -bot (scaled)
    return M @ Matrix.Translation(Vector((0, 0, -(ear_bot_z * 0.62) * EAR_S0 / EAR_S0))) @ Matrix.Scale(EAR_S0, 4)
HOLD = hold_matrix(TOOLS["Forceps"]["tip"] + Vector((0, -0.004, 0)))

# ---- rib-cage placement (inside the chest) and the harvest point
fs(1)
sp3 = Wh(PAT, "spine03"); sp1 = Wh(PAT, "spine01"); nk = Wh(PAT, "neck01")
chest_pts = eval_mesh_points(PB, lambda i: DOMP.get(i) in ("spine03", "spine02", "spine04", "breast.L", "breast.R") )
front_y = min(p[1].y for p in chest_pts if abs(p[1].x) < 0.03 and abs(p[1].z - sp3.z) < 0.08)
TH.location = (0, (front_y + sp3.y + 0.05) / 2 + 0.01, nk.z - 0.055)
TH.rotation_euler = (math.radians(-7), 0, 0)
for m_ in TH.data.materials:   # open anatomy shells: inner faces read as the same clean bone colour
    nt_ = m_.node_tree; p_ = nt_.nodes["Principled BSDF"]; out_ = nt_.nodes["Material Output"]
    g_ = nt_.nodes.new("ShaderNodeNewGeometry"); e_ = nt_.nodes.new("ShaderNodeEmission"); e_.inputs["Color"].default_value = p_.inputs["Base Color"].default_value; e_.inputs["Strength"].default_value = 0.6
    mx2 = nt_.nodes.new("ShaderNodeMixShader"); nt_.links.new(g_.outputs["Backfacing"], mx2.inputs["Fac"]); nt_.links.new(p_.outputs["BSDF"], mx2.inputs[1]); nt_.links.new(e_.outputs["Emission"], mx2.inputs[2])
    nt_.links.new(mx2.outputs["Shader"], out_.inputs["Surface"])
for f_, h_ in ((1, True), (118, False), (275, True)):
    TH.hide_render = h_; TH.hide_viewport = h_; TH.keyframe_insert("hide_render", frame=f_); TH.keyframe_insert("hide_viewport", frame=f_)
upd()
# harvest point: front of the patient's right lower ribs, 1.2 cm under the skin
fs(185)
L_sh = shoulder("L")
hz = nk.z - 0.20
front_y = min(p[1].y for p in chest_pts if abs(p[1].x + 0.085) < 0.03 and abs(p[1].z - hz) < 0.03)
HARV = Vector((-0.085, front_y + 0.03, hz))
hp_pts = eval_mesh_points(PB, lambda i: DOMP.get(i) in ("spine02", "spine03", "breast.R", "spine01"))
near = min(hp_pts, key=lambda q: (Vector((q[1].x, 0, q[1].z)) - Vector((HARV.x, 0, HARV.z))).length)
CHEST_N = near[2]; HARV = near[1] - CHEST_N * 0.018
log("harvest", tuple(round(x, 3) for x in HARV), "front_y", round(front_y, 3))

# ================================================================== the story, keyed in time order
# ---- ear: rib block (owned by nothing; static basis), x-ray chest
EAR.rotation_mode = 'QUATERNION'
PG1 = HOLD.inverted() @ TOOLS["Forceps"]["tip"]            # the ear point held in the tips (lobe end), ear-local
def key_basis_M(f, M):
    loc, q, scl = M.decompose(); EAR.location = loc; EAR.rotation_quaternion = q; EAR.scale = scl
    for k_ in ("location", "rotation_quaternion", "scale"): EAR.keyframe_insert(k_, frame=f)
def active_parent(f):
    """world matrix of the ear's active Child Of target at frame f (evaluated) and the constraint"""
    for c in EAR.constraints:
        if c.influence > 0.5:
            P_ = c.target.matrix_world @ c.target.pose.bones[c.subtarget].matrix if c.subtarget else c.target.matrix_world.copy()
            return P_, c
    return None, None
def owner_switch(f, target=None, sub=None):
    """from frame f the ear is owned by `target` (Child Of, R4) or by nobody (static); world kept continuous"""
    fs(f - 1); Wprev = EAR.matrix_world.copy()
    for c in EAR.constraints:
        c.keyframe_insert("influence", frame=f - 1); c.influence = 0.0; c.keyframe_insert("influence", frame=f)
    if target is None:
        key_basis_M(f, Wprev)
    else:
        c = EAR.constraints.new('CHILD_OF'); c.name = "own_%d" % f; c.target = target
        if sub: c.subtarget = sub
        c.influence = 0.0; c.keyframe_insert("influence", frame=0); c.keyframe_insert("influence", frame=f - 1)
        c.influence = 1.0; c.keyframe_insert("influence", frame=f)
        fs(f)
        P_ = target.matrix_world @ target.pose.bones[sub].matrix if sub else target.matrix_world.copy()
        c.inverse_matrix = P_.inverted() @ Wprev
        key_basis_M(f, Matrix.Identity(4))
    set_interp(EAR, 'CONSTANT')
    fs(f); log("owner", f, target.name if target else None, sub, "jump_mm", round((EAR.matrix_world.translation - Wprev.translation).length * 1000, 2))
def ear_follow(fa, fb, Rd, pg, ramp):
    """while held, the ear pivots in the tips (about the held point pg) into the rotation Rd (world)"""
    for t in range(fa, fb + 1):
        fs(t); P_, c = active_parent(t)
        A = P_ @ c.inverse_matrix
        S_ = A.to_scale()
        Ed = (Rd.to_3x3().normalized().to_4x4() @ Matrix.Diagonal((S_.x, S_.y, S_.z, 1.0)))
        Ed.translation = (A @ pg) - Ed.to_3x3() @ pg
        qB = (A.inverted() @ Ed).to_quaternion()
        u = smooth((t - fa) / max(1, ramp))
        q = Quaternion().slerp(qB, u)
        B = Matrix.Translation(pg) @ q.to_matrix().to_4x4() @ Matrix.Translation(-pg)
        key_basis_M(t, B)
    set_interp(EAR, 'CONSTANT')

# the forceps grip on the rib block decides the block's pose (the block is part of the costal cartilage)
F_G1 = natural(FORC, HARV, down=0.40)
kt(FORC, 200, F_G1, "grip rib")
fs(200); F_G1a = FORC.matrix_world.copy()
E_RIB = F_G1a @ HOLD
key_basis_M(1, E_RIB)
BLOCK.value = 1.0; BLOCK.keyframe_insert("value", frame=1)

# chest x-ray window
key_mask(1, HARV + CHEST_N * 0.02, 0.13); key_x(1, 0.0); key_x(122, 0.0); key_x(150, 1.0); key_x(242, 1.0); key_x(268, 0.0)

# ---- forceps (L) and scalpel (R): ready
for f in (1, 70, 140):
    ready(FORC, f, dz=0.01 * math.sin(f)); ready(SCAL, f, dz=0.01 * math.cos(f))
apply_pose(DOC, "L", "pinch", 1); apply_pose(DOC, "R", "tripod", 1)

# B2: reach into the chest window, grip the cartilage block, lift it out, carry to the tray (one model, held)
kt(FORC, 185, Matrix.Translation(CHEST_N * 0.06 + Vector((0, 0, 0.02))) @ F_G1, "approach")
kt(FORC, 212, F_G1, "grip hold")
owner_switch(204, FORC)
OUTC = Matrix.Translation(CHEST_N * 0.10 + Vector((-0.10, 0.04, -0.02))) @ F_G1
kt(FORC, 238, OUTC, "out of chest")
# drop pose on the tray: ear flat (face up), long axis pointing away from the surgeon
away = (TRAY_C - shoulder("L")); away.z = 0; away.normalize()
def flat_pose(center_xy, top_dir, surf_z, normal=Vector((0, 0, 1)), s=EAR_S0, lift=0.0005):
    z = Vector(top_dir).normalized(); yN = -Vector(normal).normalized(); x = yN.cross(z)
    M = Matrix((x, yN, z)).transposed().to_4x4() @ Matrix.Scale(s, 4)
    M.translation = Vector((center_xy.x, center_xy.y, surf_z)) + Vector(normal) * (ear_half_y * s + lift)
    return M
E_TRAY = flat_pose(TRAY_C, (away - Vector((0, 0, 0))).normalized(), TRAY_C.z)
F_D1 = E_TRAY @ HOLD.inverted()
kt(FORC, 270, Matrix.Translation(Vector((0, 0, 0.06))) @ F_D1, "above tray")
kt(FORC, 290, F_D1, "drop")
ear_follow(214, 291, E_TRAY, PG1, 50)
owner_switch(292, None)
kt(FORC, 296, F_D1, "release")
BLOCK.keyframe_insert("value", frame=300)

# B3: carving. forceps tip steadies the lobe end (resting on its top face); scalpel strokes round the outline.
fs(300)
lobe_top = EAR.matrix_world @ Vector((0, -ear_half_y * 1.05, ear_bot_z * 0.55))
F_ST = natural(FORC, lobe_top, down=0.62)
kt(FORC, 306, Matrix.Translation(Vector((0, 0, 0.025))) @ F_ST, "steady approach")
for f_ in (316, 346, 376, 406, 436, 456): kt(FORC, f_, F_ST, "steady")
outline = []
vs = EAR.data.vertices
for k in range(24):
    th = -math.pi / 2 + k / 24 * 2 * math.pi
    d = Vector((math.cos(th), 0, math.sin(th)))
    best = max(vs, key=lambda v: Vector((v.co.x, 0, v.co.z)).dot(d) - 0.2 * abs(v.co.y))
    outline.append(Vector((best.co.x, -ear_half_y * 0.5, best.co.z)))
strokes = [(318, 348, 5, 11), (352, 382, 11, 17), (386, 416, 17, 22), (420, 450, 1, 6)]
blocks = [1.0, 0.72, 0.45, 0.2, 0.0]
for si, (f0, f1, a_, b_) in enumerate(strokes):
    BLOCK.value = blocks[si]; BLOCK.keyframe_insert("value", frame=f0)
    BLOCK.value = blocks[si + 1]; BLOCK.keyframe_insert("value", frame=f1)
    pts = [outline[i % 24] for i in range(a_, b_ + 1)]
    for j, lp in enumerate(pts):
        f = int(f0 + (f1 - f0) * j / max(1, len(pts) - 1))
        fs(f); grow = 1.0 + 0.22 * BLOCK.value
        tip = EAR.matrix_world @ Vector((lp.x * grow, lp.y, lp.z * grow))
        kt(SCAL, f, natural(SCAL, tip, down=0.65), "carve")
    fs(f1); tip_up = SCAL.matrix_world @ TOOLS["Scalpel"]["tip"] + Vector((0, 0, 0.015))
    kt(SCAL, f1 + 2, natural(SCAL, tip_up, down=0.65), "lift")
ready(SCAL, 300, dz=0.02)
kt(SCAL, 310, natural(SCAL, EAR.matrix_world @ (outline[5] + Vector((0, -0.012, 0))), down=0.65), "approach")
# shavings: four curls that peel off the blade at each stroke end and settle on the tray
shav_m = bpy.data.materials["M_Ear"]
for si, (f0, f1, a_, b_) in enumerate(strokes):
    bpy.ops.mesh.primitive_torus_add(major_radius=0.004, minor_radius=0.0009, major_segments=16, minor_segments=6)
    sv = bpy.context.active_object; sv.name = "Shaving%d" % si; sv.data.materials.append(bpy.data.materials["M_RibCartilage"])
    bm = bmesh.new(); bm.from_mesh(sv.data); bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.y < -0.001 and v.co.x > 0], context='VERTS'); bm.to_mesh(sv.data); bm.free()
    fs(f1 - 4); tipw = SCAL.matrix_world @ TOOLS["Scalpel"]["tip"]
    land = Vector((TRAY_C.x - 0.03 + 0.018 * si, TRAY_C.y + 0.045 - 0.01 * si, TRAY_C.z + 0.0009))
    sv.location = tipw; sv.scale = (0.05, 0.05, 0.05); sv.rotation_euler = (1.2, 0.3 * si, 0.0)
    for k_ in ("location", "scale", "rotation_euler"): sv.keyframe_insert(k_, frame=f1 - 6)
    sv.scale = (1, 1, 1); sv.keyframe_insert("scale", frame=f1 + 2); sv.location = tipw + Vector((0, 0, 0.004)); sv.keyframe_insert("location", frame=f1 + 2)
    sv.location = land; sv.rotation_euler = (math.pi / 2, 0.3 * si, 0.8 * si); sv.keyframe_insert("location", frame=f1 + 16); sv.keyframe_insert("rotation_euler", frame=f1 + 16)
    sv.scale = (0, 0, 0); sv.keyframe_insert("scale", frame=0)
    # the curl exists only from the stroke end on: before that it is zero-size inside the blade
    sv.keyframe_insert("scale", frame=f1 - 7)
    for fc in iter_fcurves(sv.animation_data.action):
        if fc.data_path == "scale":
            for kp in fc.keyframe_points:
                if kp.co.x <= f1 - 7: kp.interpolation = 'CONSTANT'
BLOCK.value = 0.0; BLOCK.keyframe_insert("value", frame=455)

# B4: incision on the forearm (scalpel), pick the ear up, slide it into the pocket under the skin
fs(463)
d_top = (fax - ARM_N * fax.dot(ARM_N)).normalized()          # ear lies along the forearm, top toward the hand
lat_a = ARM_N.cross(d_top).normalized()
E_FINAL = flat_pose(ARM_PT - ARM_N * 0.012, d_top, 0.0, normal=ARM_N, s=EAR_S0, lift=0.0)
E_FINAL.translation = ARM_PT - ARM_N * 0.0125
INC_C = ARM_PT - d_top * 0.030
inc_pts = [INC_C + lat_a * (u * 0.020) + ARM_N * 0.0006 for u in (-1, -0.5, 0, 0.5, 1)]
kt(SCAL, 470, natural(SCAL, inc_pts[0] + ARM_N * 0.015, down=0.7), "inc approach")
for j, pnt in enumerate(inc_pts):
    kt(SCAL, 478 + j * 7, natural(SCAL, pnt, down=0.7), "incise")
kt(SCAL, 514, natural(SCAL, inc_pts[-1] + ARM_N * 0.02, down=0.7), "inc lift")
ready(SCAL, 570, dz=0.06, fwd=0.12); ready(SCAL, 900, dz=0.06, fwd=0.12)
def curve_line(name, pts_, bevel, matname, parent=None):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = bevel; cu.bevel_resolution = 2
    sp = cu.splines.new('POLY'); sp.points.add(len(pts_) - 1)
    for i, p_ in enumerate(pts_): sp.points[i].co = (*p_, 1)
    ob = bpy.data.objects.new(name, cu); sc.collection.objects.link(ob)
    cu.materials.append(bpy.data.materials.get(matname) or mat_simple(matname))
    cu.use_fill_caps = True
    return ob
def mat_simple(name, col=(0.55, 0.12, 0.14), emit=0.0, rough=0.4):
    m = bpy.data.materials.new(name); m.use_nodes = True; p_ = m.node_tree.nodes["Principled BSDF"]
    p_.inputs["Base Color"].default_value = (*col, 1); p_.inputs["Roughness"].default_value = rough
    if emit: p_.inputs["Emission Color"].default_value = (*col, 1); p_.inputs["Emission Strength"].default_value = emit
    return m
mat_simple("M_Incision", (0.55, 0.16, 0.16), rough=0.5)
inc = curve_line("Incision", inc_pts, 0.0010, "M_Incision")
inc.data.bevel_factor_end = 0.0; inc.data.keyframe_insert("bevel_factor_end", frame=477)
inc.data.bevel_factor_end = 1.0; inc.data.keyframe_insert("bevel_factor_end", frame=506)
# pick-up from the tray with the same hold
kt(FORC, 470, Matrix.Translation(Vector((0, 0, 0.03))) @ F_ST, "steady lift")
F_G2 = natural(FORC, E_TRAY @ PG1, down=0.62)
kt(FORC, 512, Matrix.Translation(Vector((0, 0, 0.05))) @ F_G2, "pick approach")
kt(FORC, 524, F_G2, "pick")
owner_switch(527, FORC)
kt(FORC, 530, F_G2, "pick hold")
kt(FORC, 548, Matrix.Translation(Vector((0, 0, 0.06))) @ F_G2, "pick lift")
E0 = E_FINAL.copy(); E0.translation = E_FINAL.translation - d_top * 0.052 + ARM_N * 0.022
E1 = E_FINAL.copy(); E1.translation = E_FINAL.translation - d_top * 0.040 + ARM_N * 0.012
kt(FORC, 576, Matrix.Translation(ARM_N * 0.04) @ E0 @ HOLD.inverted(), "over arm")
kt(FORC, 590, E0 @ HOLD.inverted(), "enter")
kt(FORC, 600, E1 @ HOLD.inverted(), "slide")
kt(FORC, 614, E_FINAL @ HOLD.inverted(), "in pocket")
ear_follow(531, 616, E_FINAL, PG1, 45)
owner_switch(617, PAT, "lowerarm02.R")
kt(FORC, 622, E_FINAL @ HOLD.inverted(), "release")
kt(FORC, 640, Matrix.Translation(ARM_N * 0.05 - d_top * 0.03) @ E_FINAL @ HOLD.inverted(), "withdraw")
ready(FORC, 690, fwd=0.12, dz=0.06, dx=0.04); ready(FORC, 900, fwd=0.12, dz=0.06, dx=0.04)
mk.value = 0.0; mk.keyframe_insert("value", frame=590); mk.value = 0.32; mk.keyframe_insert("value", frame=622)

# B5: inside the arm (x-ray window): vessels grow over the ear, skin creeps across it, the ear grows and rises
key_mask(640, ARM_PT, 0.075); key_x(650, 0.0); key_x(676, 1.0); key_x(770, 1.0); key_x(805, 0.0)

key_edge(690, -0.04); key_edge(800, 0.045)
# vessels in ear-local space (just under the front face), parented to the ear
vs = EAR.data.vertices
front = [v for v in vs if v.normal.y < -0.5]
vmat = mat_simple("M_Vessel", (0.78, 0.06, 0.10), emit=0.4, rough=0.3)
vmat2 = mat_simple("M_Vein", (0.12, 0.22, 0.72), emit=0.3, rough=0.3)
VESS = []
for k in range(7):
    rnd = random.Random(k)
    start = Vector((rnd.uniform(-0.6, 0.6) * 0.01, 0, ear_bot_z * 0.85))
    goal = Vector((rnd.uniform(-1, 1) * 0.015, 0, ear_top_z * rnd.uniform(0.55, 0.95)))
    path = []
    for j in range(14):
        u = j / 13; q = start.lerp(goal, u) + Vector((math.sin(u * 7 + k) * 0.003, 0, 0))
        v_ = min(front, key=lambda v: (Vector((v.co.x, 0, v.co.z)) - Vector((q.x, 0, q.z))).length)
        path.append(v_.co + v_.normal * 0.0005)
    ob = curve_line("Vessel%d" % k, path, 0.00045 if k % 3 else 0.0006, "M_Vessel" if k % 2 == 0 else "M_Vein")
    ob.parent = EAR; ob.matrix_parent_inverse = Matrix.Identity(4)
    ob.data.bevel_factor_end = 0.0; ob.data.keyframe_insert("bevel_factor_end", frame=668 + 6 * k)
    ob.data.bevel_factor_end = 1.0; ob.data.keyframe_insert("bevel_factor_end", frame=760 + 4 * k)
    ob.data.bevel_factor_start = 0.0; ob.data.keyframe_insert("bevel_factor_start", frame=800 + 3 * k)
    ob.data.bevel_factor_start = 1.0; ob.data.keyframe_insert("bevel_factor_start", frame=850 + 3 * k)
    VESS.append(ob)
# growth: scale 0.78 -> 1.0, rising so the grown ear stands on the forearm (basis animation under the forearm owner)
fs(617)
# basis is identity at the switch; ear local axes: -y = face normal (toward ARM_N)
for t in range(700, 941):
    u = smooth((t - 700) / 240.0); s_ = EAR_S0 + (1.0 - EAR_S0) * u; rise = 0.022 * u
    B = Matrix.Translation(Vector((0, -rise / EAR_S0, 0))) @ Matrix.Scale(s_ / EAR_S0, 4)
    key_basis_M(t, B)
set_interp(EAR, 'CONSTANT')
mk.value = 0.32; mk.keyframe_insert("value", frame=700); mk.value = 1.0; mk.keyframe_insert("value", frame=940)

# B6: scalpel cuts round the ear, forceps grips the top and lifts it out; the mound flattens
fs(905)
ring = []
for k in range(9):
    th = k / 8 * 2 * math.pi
    lp = Vector((math.cos(th) * 0.026, -ear_half_y * 0.2, math.sin(th) * 0.036))
    pw = EAR.matrix_world @ (lp / 1.0)
    # project onto the skin surface (closest evaluated forearm point)
    q = min(fpts, key=lambda p_: (p_[1] - pw).length)
    ring.append(q[1] + q[2] * 0.0006)
kt(SCAL, 938, natural(SCAL, ring[0] + ARM_N * 0.015, down=0.7), "ring approach")
for k, pnt in enumerate(ring):
    kt(SCAL, 945 + k * 6, natural(SCAL, pnt, down=0.7), "ring cut")
kt(SCAL, 999, natural(SCAL, ring[-1] + ARM_N * 0.025, down=0.7), "ring lift")
cut2 = curve_line("Incision2", ring, 0.0006, "M_Incision")
cut2.data.bevel_factor_end = 0.0; cut2.data.keyframe_insert("bevel_factor_end", frame=944)
cut2.data.bevel_factor_end = 1.0; cut2.data.keyframe_insert("bevel_factor_end", frame=993)
fs(1005)
top_grip = EAR.matrix_world @ Vector((-0.012, 0, ear_bot_z * 0.62))
F_G3 = natural(FORC, top_grip, down=0.75)
kt(FORC, 996, Matrix.Translation(ARM_N * 0.04) @ F_G3, "top approach")
kt(FORC, 1010, F_G3, "grip top")
owner_switch(1013, FORC)
kt(FORC, 1016, F_G3, "grip top hold")
mk.value = 1.0; mk.keyframe_insert("value", frame=1016); mk.value = 0.0; mk.keyframe_insert("value", frame=1052)
fs(1013); E_G3 = EAR.matrix_world.copy(); OFF3 = F_G3.inverted() @ E_G3
LIFT = Matrix.Translation(ARM_N * 0.045) @ E_G3
kt(FORC, 1046, LIFT @ OFF3.inverted(), "lift out")

# B7: to the head: the ear is set on the healed site, vessels join (x-ray window at the site)
fs(1150)
SITE, SITEN = site_world()
hm = W(PAT, "head"); nose_dir = (Wh(PAT, "head") - Wt(PAT, "head"));
fwd_h = (PAT.matrix_world.to_3x3() @ PAT.pose.bones["head"].matrix.to_3x3() @ Vector((0, 0, 1))).normalized()
fwd_h = Vector((fwd_h.x, fwd_h.y, 0)).normalized()
outw = Vector((SITEN.x, SITEN.y, 0)).normalized()
fwd_h = (fwd_h - outw * fwd_h.dot(outw)).normalized()
up_h = outw.cross(fwd_h)
if up_h.z < 0: up_h = -up_h
tilt = Matrix.Rotation(math.radians(-14), 3, outw)
zx = (tilt @ up_h).normalized(); yx = -outw; xx = yx.cross(zx)
Rh = Matrix((xx, yx, zx)).transposed()
E_HEAD = Rh.to_4x4() @ Matrix.Scale(1.0, 4)
ear_back = ear_half_y
E_HEAD.translation = SITE + outw * (ear_back * 1.0 + 0.0005) + up_h * 0.004
log("ear on head: front", tuple(round(x, 2) for x in (E_HEAD.to_3x3() @ Vector((1, 0, 0)))), "out", tuple(round(x, 2) for x in outw))
NEAR_HEAD = Matrix.Translation(outw * 0.05 + Vector((0, 0, 0.02))) @ E_HEAD
kt(FORC, 1080, Matrix.Translation(Vector((0, 0, 0.10))).lerp if False else Matrix.Translation((LIFT.translation.lerp(NEAR_HEAD.translation, 0.5)) - LIFT.translation + Vector((0, 0, 0.05))) @ LIFT @ OFF3.inverted(), "carry")
kt(FORC, 1125, NEAR_HEAD @ OFF3.inverted(), "near head")
kt(FORC, 1150, Matrix.Translation(outw * 0.008) @ E_HEAD @ OFF3.inverted(), "set")
kt(FORC, 1168, E_HEAD @ OFF3.inverted(), "placed")
PG3 = OFF3.inverted() @ TOOLS["Forceps"]["tip"]
ear_follow(1048, 1171, E_HEAD, PG3, 80)
owner_switch(1172, PAT, "head")

kt(FORC, 1240, E_HEAD @ OFF3.inverted(), "hold while placing")
kt(FORC, 1262, Matrix.Translation(outw * 0.05 + fwd_h * -0.03) @ E_HEAD @ OFF3.inverted(), "release")
ready(FORC, 1340, fwd=0.22); ready(FORC, 1460, fwd=0.22, dz=0.01); ready(FORC, 1572, fwd=0.21, dz=0.0)
skin_p.inputs["Emission Color"].default_value = (1.0, 0.35, 0.35, 1)
ES = skin_p.inputs["Emission Strength"]
for f_, v_ in ((1, 0.0), (1196, 0.0), (1218, 0.5), (1245, 0.0)):
    ES.default_value = v_; ES.keyframe_insert("default_value", frame=f_)
# R hand: scalpel back to the tray, needle holder up from the tray (both lie flat on the drape)
def lie_on_tray(tool, cx, cy, yaw):
    vz = min(v.co.z for v in tool.data.vertices)
    M = Matrix.Translation(Vector((cx, cy, tray_top(cx, cy) - vz + 0.0004))) @ Matrix.Rotation(yaw, 4, 'Z')
    return M
T_SC = lie_on_tray(SCAL, TRAY_C.x + 0.06, TRAY_C.y + 0.07, math.radians(100))
T_NH = lie_on_tray(NEED, TRAY_C.x - 0.06, TRAY_C.y + 0.08, math.radians(80))
kt(SCAL, 1022, Matrix.Translation(Vector((0, 0, 0.05))) @ T_SC, "to tray")
kt(SCAL, 1040, T_SC, "put down")
def tool_release(tool, f, Tworld):
    c = tool.constraints["Hand"]
    c.influence = 1.0; c.keyframe_insert("influence", frame=f - 1)
    c.influence = 0.0; c.keyframe_insert("influence", frame=f)
    tool.matrix_world = Tworld; tool.constraints["Hand"].influence = 0.0
    tool.keyframe_insert("location", frame=f); tool.keyframe_insert("rotation_euler", frame=f)
    set_interp(tool, 'CONSTANT')
def tool_pick(tool, f, Tworld0_basis):
    c = tool.constraints["Hand"]
    c.influence = 0.0; c.keyframe_insert("influence", frame=f - 1)
    c.influence = 1.0; c.keyframe_insert("influence", frame=f)
    tool.matrix_basis = Tworld0_basis
    tool.keyframe_insert("location", frame=f); tool.keyframe_insert("rotation_euler", frame=f)
    set_interp(tool, 'CONSTANT')
fs(0); B_SC0 = SCAL.matrix_basis.copy(); B_NH0 = NEED.matrix_basis.copy()
# needle holder waits on the tray from frame 0
NEED.matrix_basis = T_NH; NEED.keyframe_insert("location", frame=1); NEED.keyframe_insert("rotation_euler", frame=1)
NEED.matrix_basis = B_NH0; NEED.keyframe_insert("location", frame=0); NEED.keyframe_insert("rotation_euler", frame=0)
set_interp(NEED, 'CONSTANT')
fs(1041); tool_release(SCAL, 1042, T_SC)
kt(NEED, 1056, Matrix.Translation(Vector((0, 0, 0.05))) @ T_NH, "to needle")
kt(NEED, 1070, T_NH, "pick needle")
tool_pick(NEED, 1071, B_NH0)
kt(NEED, 1074, T_NH, "pick hold")
kt(NEED, 1096, Matrix.Translation(Vector((0, 0, 0.08))) @ T_NH, "lift needle")
# B8: stitching along the front + lower edge of the ear root; the thread follows the needle
fs(1260)
seam = []
for k in range(7):
    u = k / 6
    lp = Vector((-0.017 + 0.003 * u, ear_half_y * 0.9, ear_top_z * 0.55 - u * (ear_top_z * 0.55 - ear_bot_z * 0.10)))
    pw = EAR.matrix_world @ lp
    seam.append(pw + outw * 0.0012)
nh_hover = [p_ + outw * 0.012 for p_ in seam]
kt(NEED, 1200, natural(NEED, nh_hover[0] + outw * 0.03 + Vector((0, 0, 0.02)), down=0.25), "near head wait")
kt(NEED, 1262, natural(NEED, nh_hover[0], down=0.6), "stitch start")
thread_pts = []
f = 1272
for k, p_ in enumerate(seam):
    kt(NEED, f, natural(NEED, p_, down=0.6), "bite")
    kt(NEED, f + 9, natural(NEED, p_ + outw * 0.006 + Vector((0, 0, 0.006)), down=0.6), "pull")
    f += 21
kt(NEED, f + 4, natural(NEED, seam[-1] + outw * 0.04 + Vector((0, 0, 0.04)), down=0.25), "done")
stitch_m = mat_simple("M_Suture", (0.05, 0.06, 0.25), rough=0.35)
sut_pts = []
for k in range(len(seam) - 1):
    a_, b_ = seam[k], seam[k + 1]
    sut_pts += [a_, a_.lerp(b_, 0.5) + outw * 0.0007, b_]
sut = curve_line("Suture", sut_pts, 0.0008, "M_Suture")
sut.data.bevel_factor_end = 0.0; sut.data.keyframe_insert("bevel_factor_end", frame=1272)
sut.data.bevel_factor_end = 1.0; sut.data.keyframe_insert("bevel_factor_end", frame=1272 + 21 * (len(seam) - 1))
ready(NEED, 1470, fwd=0.22, dz=0.0, dx=-0.03); ready(NEED, 1572, fwd=0.21, dz=0.01, dx=-0.03)
ready(SCAL, 1040, fwd=0.30) if False else None

# stitches + join vessels ride on the head (Child Of head bone)
fs(1172)
for ob in (sut, inc, cut2):
    sw = ob.modifiers.new("skin", 'SHRINKWRAP'); sw.target = PB; sw.wrap_method = 'NEAREST_SURFACEPOINT'; sw.offset = 0.0005
for ob in (sut,):
    c = ob.constraints.new('CHILD_OF'); c.target = PAT; c.subtarget = "head"
    c.inverse_matrix = (PAT.matrix_world @ PAT.pose.bones["head"].matrix).inverted()
for ob in (inc, cut2):
    c = ob.constraints.new('CHILD_OF'); c.target = PAT; c.subtarget = "lowerarm02.R"
    c.inverse_matrix = (PAT.matrix_world @ PAT.pose.bones["lowerarm02.R"].matrix).inverted()

# ================================================================== patient acting: head looks, blinks, eyes, smile
# blinks: find the closing direction of the upper lid numerically
def lid_close_rot(s):
    pb = PAT.pose.bones["orbicularis03." + s]; fs(1)
    t0 = Wt(PAT, pb.name).z; pb.rotation_quaternion = Quaternion((1, 0, 0), math.radians(20)); upd(); t1 = Wt(PAT, pb.name).z
    pb.rotation_quaternion = Quaternion(); upd()
    return 1.0 if t1 < t0 else -1.0
blink_frames = [40, 190, 330, 520, 700, 860, 1010, 1180, 1330, 1470, 1545]
for s in "LR":
    sg = lid_close_rot(s); pb = PAT.pose.bones["orbicularis03." + s]
    pb.rotation_quaternion = Quaternion(); pb.keyframe_insert("rotation_quaternion", frame=1)
    for bf in blink_frames:
        for df, ang in ((0, 0), (4, 24), (7, 24), (13, 0)):
            pb.rotation_quaternion = Quaternion((1, 0, 0), math.radians(ang * sg)); pb.keyframe_insert("rotation_quaternion", frame=bf + df)
# eyes: small saccades toward what he looks at
for f in range(1, END, 45):
    rnd = random.Random(f)
    for s in "LR":
        PR.key_rot("eye." + s, f, [("X", rnd.uniform(-3, 3)), ("Z", rnd.uniform(-5, 5))])
# smile on "a brand new ear": mouth corners up and out
def corner_nudge(bone, f, amount):
    pb = PAT.pose.bones[bone]; fs(f)
    base = Wt(PAT, bone); best = None
    for ax in ((1, 0, 0), (0, 0, 1), (0, 1, 0)):
        for sg in (1, -1):
            pb.rotation_quaternion = Quaternion(ax, math.radians(12 * sg)); upd()
            d = Wt(PAT, bone) - base
            want = Vector((0, 0, 1)) + Vector((1 if bone.endswith(".L") else -1, 0, 0)) * 0.6
            sc_ = d.dot(want.normalized())
            if best is None or sc_ > best[0]: best = (sc_, ax, sg)
    pb.rotation_quaternion = Quaternion(); pb.keyframe_insert("rotation_quaternion", frame=f)
    return best
for bone in ("risorius03.L", "risorius03.R", "levator05.L", "levator05.R", "oris04.L", "oris04.R"):
    if bone not in PAT.pose.bones: continue
    sc_, ax, sg = corner_nudge(bone, 1455, 1)
    pb = PAT.pose.bones[bone]
    pb.rotation_quaternion = Quaternion(); pb.keyframe_insert("rotation_quaternion", frame=1462)
    pb.rotation_quaternion = Quaternion(ax, math.radians(15 * sg)); pb.keyframe_insert("rotation_quaternion", frame=1500)
    pb.keyframe_insert("rotation_quaternion", frame=END)
# patient's free (left) hand fingers: a small relaxed shift now and then (no pose snaps)
for f in (1, 400, 800, 1200, END):
    apply_pose(PAT, "L", "shield", f)

# surgeon: blinks too (eyes above the mask read alive)
for s in "LR":
    pbn = "orbicularis03." + s
    if pbn not in DOC.pose.bones: continue
    pb = DOC.pose.bones[pbn]; fs(1)
    t0 = Wt(DOC, pbn).z; pb.rotation_quaternion = Quaternion((1, 0, 0), math.radians(20)); upd(); sg = 1.0 if Wt(DOC, pbn).z < t0 else -1.0
    pb.rotation_quaternion = Quaternion(); pb.keyframe_insert("rotation_quaternion", frame=1)
    for bf in (90, 260, 560, 780, 1000, 1240, 1400, 1520):
        for df, ang in ((0, 0), (4, 24), (7, 24), (13, 0)):
            pb.rotation_quaternion = Quaternion((1, 0, 0), math.radians(ang * sg)); pb.keyframe_insert("rotation_quaternion", frame=bf + df)

# surgeon head aims at the working point (yaw/pitch over the spine keys)
WORK = {"L": [], "R": []}

# ================================================================== the camera: ONE camera, one continuous move
fs(1)
cam_d = bpy.data.cameras.new("CAM_Film"); CAM = bpy.data.objects.new("CAM_Film", cam_d); sc.collection.objects.link(CAM); sc.camera = CAM
AIM = bpy.data.objects.new("CAM_Film_Aim", None); sc.collection.objects.link(AIM)
cam_d.sensor_fit = 'AUTO'; cam_d.sensor_width = 36; cam_d.dof.use_dof = True; cam_d.dof.focus_object = AIM; cam_d.dof.aperture_fstop = 11.0
cam_d.clip_start = 0.02
def P(*v): return Vector(v)
fs(1); HEAD1 = Wh(PAT, "head") + Vector((0, -0.02, 0.05))
CH = HARV + CHEST_N * 0.02
TR = TRAY_C + Vector((0, 0, 0.03))
ARM = ARM_PT
SITEV = SITE
SURG_HEAD = Wh(DOC, "head")
CAMK = [  # frame, camera position, aim point, lens
    (1,    P(-1.30, -2.05, 1.40), P(-0.28, 0.02, 1.15), 30),
    (60,   P(-0.80, -1.10, 1.38), HEAD1.lerp(SITE0, 0.35) + P(0, 0, -0.04), 36),
    (108,  P(-0.55, -0.70, 1.30), SITE0.lerp(HEAD1, 0.45), 38),
    (150,  P(-0.40, -0.80, 1.18), CH.lerp(HEAD1, 0.45), 32),
    (200,  P(-0.26, -0.44, 1.06), CH, 40),
    (235,  P(-0.30, -0.42, 1.10), CH + P(-0.03, 0, 0.02), 40),
    (272,  P(-0.72, -0.82, 1.32), CH.lerp(TR, 0.6) + P(0, 0, 0.22), 28),
    (312,  P(-0.82, -0.56, 1.42), TR + P(0, 0, 0.12), 32),
    (350,  P(-0.86, -0.20, 1.30), TR, 40),
    (410,  P(-0.74, -0.22, 1.30), TR, 40),
    (455,  P(-0.80, -0.38, 1.40), TR.lerp(ARM, 0.5) + P(0, 0, 0.08), 32),
    (500,  P(-0.58, -0.42, 1.30), ARM, 36),
    (560,  P(-0.52, -0.32, 1.24), ARM, 38),
    (612,  P(-0.50, -0.25, 1.20), ARM, 50),
    (700,  P(-0.48, -0.22, 1.18), ARM, 52),
    (800,  P(-0.42, -0.24, 1.17), ARM, 52),
    (880,  P(-0.53, -0.21, 1.18), ARM, 50),
    (945,  P(-0.50, -0.26, 1.24), ARM, 40),
    (1005, P(-0.46, -0.30, 1.30), ARM, 38),
    (1055, P(-0.48, -0.52, 1.34), ARM.lerp(SITE0, 0.35), 32),
    (1110, P(-0.50, -0.64, 1.42), ARM.lerp(SITE0, 0.8), 32),
    (1180, P(-0.40, -0.40, 1.34), SITE, 44),
    (1260, P(-0.32, -0.36, 1.20), SITE + P(0, 0, -0.01), 56),
    (1340, P(-0.30, -0.40, 1.19), SITE + P(0, 0, -0.01), 56),
    (1430, P(-0.34, -0.46, 1.24), SITE, 46),
    (1500, P(-0.40, -0.86, 1.42), HEAD1.lerp(SURG_HEAD, 0.35), 32),
    (1572, P(-0.22, -0.98, 1.44), HEAD1.lerp(SURG_HEAD, 0.35) + P(0.04, 0, 0), 32),
]
fr = [k[0] for k in CAMK]
fx = [pchip([(k[0], k[1][i]) for k in CAMK]) for i in range(3)]
ax_ = [pchip([(k[0], k[2][i]) for k in CAMK]) for i in range(3)]
fl = pchip([(k[0], k[3]) for k in CAMK])
for f in range(1, END + 1):
    CAM.location = (fx[0](f), fx[1](f), fx[2](f)); AIM.location = (ax_[0](f), ax_[1](f), ax_[2](f)); cam_d.lens = fl(f)
    CAM.keyframe_insert("location", frame=f); AIM.keyframe_insert("location", frame=f); cam_d.keyframe_insert("lens", frame=f)
tt = CAM.constraints.new('TRACK_TO'); tt.target = AIM; tt.track_axis = 'TRACK_NEGATIVE_Z'; tt.up_axis = 'UP_Y'
set_interp(CAM, 'LINEAR'); set_interp(AIM, 'LINEAR'); set_interp(cam_d, 'LINEAR')
# catchlight: a small soft light riding with the camera
cl = bpy.data.lights.new("Catch", 'AREA'); cl.energy = 4.0; cl.size = 0.25; cl.color = (1, 0.97, 0.94)
clo = bpy.data.objects.new("Catchlight", cl); sc.collection.objects.link(clo); clo.parent = CAM; clo.location = (0.0, 0.12, 0.0)

# ================================================================== audio, range, save
sc.frame_start, sc.frame_end = 1, END
if not sc.sequence_editor: sc.sequence_editor_create()
vo = "/home/user/Muhammed/blender/EarInArm_v015/EarInArm_v015_VO.mp3"
try:
    se = sc.sequence_editor
    strips = se.strips if hasattr(se, "strips") else se.sequences
    strips.new_sound("VO", vo, 1, 1)
except Exception as e:
    log("vo strip failed", e)
for o in O:
    for m in getattr(o, "modifiers", []):
        if m.type == 'SUBSURF': m.show_viewport = True
def quat_continuity(obj):
    groups = {}
    for fc in iter_fcurves(obj.animation_data.action):
        if fc.data_path.endswith("rotation_quaternion"): groups.setdefault(fc.data_path, {})[fc.array_index] = fc
    nfix = 0
    for dp, ch in groups.items():
        if len(ch) != 4: continue
        frames = sorted({kp.co.x for kp in ch[0].keyframe_points})
        def val(i, fr):
            for kp in ch[i].keyframe_points:
                if abs(kp.co.x - fr) < 1e-3: return kp
        prev = None
        for fr in frames:
            kps = [val(i, fr) for i in range(4)]
            if any(k is None for k in kps): continue
            q = Quaternion([k.co.y for k in kps])
            if prev is not None and prev.dot(q) < 0:
                for k in kps:
                    k.co.y = -k.co.y; k.handle_left.y = -k.handle_left.y; k.handle_right.y = -k.handle_right.y
                q = -q; nfix += 1
            prev = q
        for c in ch.values(): c.update()
    return nfix
from mathutils.bvhtree import BVHTree
def tool_head_hits(tools, f0, f1, step=4):
    hits = []
    for f in range(f0, f1 + 1, step):
        fs(f); dg = bpy.context.evaluated_depsgraph_get(); ev_ = PB.evaluated_get(dg)
        bvh = BVHTree.FromObject(ev_, dg)
        Minv = PB.matrix_world.inverted()
        for t in tools:
            if t.constraints["Hand"].influence < 0.5: continue
            vs_ = t.data.vertices; idxs = range(0, len(vs_), max(1, len(vs_) // 80))
            for i in idxs:
                pw = Minv @ (t.matrix_world @ vs_[i].co)
                loc_, nrm_, _, d_ = bvh.find_nearest(pw)
                if loc_ is not None and (pw - loc_).dot(nrm_) < -0.0005:
                    hits.append((f, t.name)); break
    return hits
H_ = tool_head_hits([FORC, NEED], 1100, 1460)
log("TOOL_IN_BODY frames (graft):", len(H_), H_[:20])
log("quat flips fixed", quat_continuity(DOC), quat_continuity(PAT))
for f, n, lab, e in ERR:
    if e > 3.0: log("TIP_ERR", f, n, lab, e, "mm")
log("tip errors: max", max(e for *_, e in ERR), "mm over", len(ERR), "keys")
for w_ in WANG:
    if max(abs(x) for x in w_[2]) > 55: log("WRIST", w_)
log("wrist max |x|,|y|,|z| deg", max(abs(a[2][0]) for a in WANG), max(abs(a[2][1]) for a in WANG), max(abs(a[2][2]) for a in WANG))
sc.frame_set(1)
sc.render.filepath = "//render/EarInArm_v015_####.png"; sc.render.image_settings.file_format = 'PNG'
sc.render.image_settings.compression = 15
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
open(OUT + ".log.txt", "w").write("\n".join(LOG))
print("ANIM_OK", OUT)
