"""B17 PilotSuckedOut: per-shot animation clips (1x), cameras and markers, from shots.py.
blender -b sets.blend --python 03_shots.py -- out.blend"""
import bpy, sys, os, math, random
from mathutils import Vector, Matrix, Quaternion, Euler
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[sys.argv.index("--") + 1:][0]
exec(open(os.path.join(HERE, "poselib.py")).read())
exec(open(os.path.join(HERE, "..", "..", "pipeline", "hand_poses.py")).read())
exec(open(os.path.join(HERE, "shots.py")).read())
D = bpy.data; sc = bpy.context.scene; R_ = math.radians
LAY = layout(); SH = {sid: (st, f0, f1) for sid, st, f0, f1 in LAY}
sc.frame_start = 1; sc.frame_end = LAY[-1][3]; sc.render.fps = 60
CAP, FO, ATT = D.objects["CAPT"], D.objects["FO"], D.objects["Attendant"]
AP, AL = D.objects["Airliner"], D.objects["Airliner_LAND"]
# ------------------------------------------------------------------ rig prep
for rig in (CAP, FO, ATT):
    rig.rotation_mode = 'XYZ'
    for pb in rig.pose.bones:
        for c in pb.constraints:
            if c.type in ('IK', 'COPY_ROTATION') and (rig is not ATT or "leg" in pb.name or "foot" in pb.name):
                c.influence = 0.0; c.mute = True
    for s in "LR":                                   # open the elbow (MPFB rest ~46 deg)
        for bn in ("lowerarm01." + s, "lowerarm02." + s):
            pb = rig.pose.bones.get(bn)
            if pb:
                for c in pb.constraints:
                    if c.type == 'LIMIT_ROTATION': c.min_x = min(c.min_x, R_(-60)); c.min_z = min(c.min_z, R_(-60))
    add_hand_limits(rig)
# eye fix on every EnhancedEye group (LegoInNose eye_fix.py a44130b), idempotent
for g in [g for g in D.node_groups if g.name.startswith("EnhancedEye")]:
    if any(n.name.startswith("CorneaTransparentMix") for n in g.nodes): continue
    P = next((n for n in g.nodes if n.type == "BSDF_PRINCIPLED"), None); OUTN = next((n for n in g.nodes if n.type == "GROUP_OUTPUT"), None)
    if not P or not OUTN: continue
    tl = [l for l in g.links if l.to_node == P and l.to_socket.name == "Transmission Weight"]; srcs = tl[0].from_socket if tl else None
    for l in tl: g.links.remove(l)
    P.inputs["Transmission Weight"].default_value = 0.0
    ol = [l for l in g.links if l.from_node == P and l.to_node == OUTN]
    if not ol: continue
    out_sock = ol[0].to_socket; g.links.remove(ol[0])
    tr = g.nodes.new("ShaderNodeBsdfTransparent"); mx = g.nodes.new("ShaderNodeMixShader"); mx.name = "CorneaTransparentMix"
    if srcs: g.links.new(srcs, mx.inputs[0])
    else: mx.inputs[0].default_value = 0.0
    g.links.new(P.outputs[0], mx.inputs[1]); g.links.new(tr.outputs[0], mx.inputs[2]); g.links.new(mx.outputs[0], out_sock)
# attendant: opaque dark tights (a 3 mm shell of her leg skin, same armature and masks), so no bare knees read as skin
import bmesh
src = D.objects["Attendant.body"]
if "Attendant.tights" not in D.objects:
    tg = src.copy(); tg.data = src.data.copy(); tg.name = "Attendant.tights"
    for c in src.users_collection: c.objects.link(tg)
    rigb = {b.name for b in ATT.data.bones}; gi = {g.index: g.name for g in tg.vertex_groups}
    legs = ("upperleg", "lowerleg", "pelvis")
    bm = bmesh.new(); bm.from_mesh(tg.data); dl = bm.verts.layers.deform.active; dead = []
    for v in bm.verts:
        gs = [(gi[k], w) for k, w in v[dl].items() if gi.get(k) in rigb]
        if not gs or not max(gs, key=lambda x: x[1])[0].startswith(legs): dead.append(v)
    bmesh.ops.delete(bm, geom=dead, context='VERTS'); bm.to_mesh(tg.data); bm.free()
    dm = tg.modifiers.new("tights_offset", 'DISPLACE'); dm.strength = 0.004; dm.mid_level = 0.0
    mt = D.materials.new("M_tights"); mt.use_nodes = True; Pn = mt.node_tree.nodes["Principled BSDF"]
    Pn.inputs["Base Color"].default_value = (0.03, 0.03, 0.04, 1); Pn.inputs["Roughness"].default_value = 0.55
    tg.data.materials.clear(); tg.data.materials.append(mt)
    for poly in tg.data.polygons: poly.material_index = 0
    print("TIGHTS verts", len(tg.data.vertices))
for o in FO.children:
    for m in (o.data.materials if o.type == 'MESH' else []):
        if m and m.node_tree:
            for n in m.node_tree.nodes:
                if n.type == 'GROUP' and n.node_tree and n.node_tree.name.startswith("EnhancedEye"):
                    n.inputs["IrisMajorColor"].default_value = (0.09, 0.045, 0.018, 1); n.inputs["IrisMinorColor"].default_value = (0.025, 0.012, 0.006, 1)
                    n.inputs["EyeWhiteColor"].default_value = (0.66, 0.62, 0.58, 1)
for o in CAP.children:                         # captain's shoes: dark brown (the tan shoes read as bare skin)
    if o.type == 'MESH' and "shoes" in o.name:
        ms = D.materials.new("M_capt_shoes"); ms.use_nodes = True; Pn = ms.node_tree.nodes["Principled BSDF"]
        Pn.inputs["Base Color"].default_value = (0.045, 0.03, 0.02, 1); Pn.inputs["Roughness"].default_value = 0.35
        o.data.materials.clear(); o.data.materials.append(ms)
        for poly in o.data.polygons: poly.material_index = 0
REST_ROOT = CAP.data.bones["root"].head_local.copy()
def place(rig, f, pelvis_world, yaw_deg, extra=None):
    """key the rig object so the root head lands on pelvis_world, facing yaw (0 = faces -Y, 180 = faces +Y)"""
    Rz = Matrix.Rotation(R_(yaw_deg), 3, 'Z')
    rh = rig.data.bones["root"].head_local
    rig.rotation_euler = (0, 0, R_(yaw_deg)); rig.location = Vector(pelvis_world) - Rz @ rh
    rig.keyframe_insert("location", frame=f); rig.keyframe_insert("rotation_euler", frame=f)
def to_rig(rig, d_world):
    return (rig.matrix_world.inverted().to_3x3() @ Vector(d_world)).normalized()
def bone_w(rig, bn, tail=False):
    pb = rig.pose.bones[bn]; return rig.matrix_world @ (pb.tail if tail else pb.head)
def arm_ik(rig, s, f, wrist_target, pole_world, hand_dir=None):
    """2-bone IK by aims: returns spec for uarm/farm(/hand) in rig frame"""
    bpy.context.view_layer.update()
    S = bone_w(rig, "upperarm01." + s); BN = rig.data.bones
    l1 = (BN["lowerarm01." + s].head_local - BN["upperarm01." + s].head_local).length
    l2 = (BN["wrist." + s].head_local - BN["lowerarm01." + s].head_local).length
    T = Vector(wrist_target); d = (T - S); L = min(d.length, (l1 + l2) * 0.985); u = d.normalized()
    a = (l1 * l1 - l2 * l2 + L * L) / (2 * L); h = math.sqrt(max(0.0, l1 * l1 - a * a))
    pv = Vector(pole_world) - S; v = (pv - u * pv.dot(u)).normalized()
    E = S + u * a + v * h; T2 = S + u * L
    spec = {"uarm." + s: to_rig(rig, E - S), "farm." + s: to_rig(rig, T2 - E)}
    if hand_dir is not None: spec["hand." + s] = to_rig(rig, hand_dir)
    return spec
def pose(rig, f, spec, root_q=None):
    key_pose(rig, f, spec, root=(Vector((0, 0, 0)), root_q or Quaternion()))
def jaw(rig, f, deg):
    pb = rig.pose.bones["jaw"]; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = Quaternion((1, 0, 0), R_(deg))
    pb.keyframe_insert("rotation_quaternion", frame=f, group="jaw")
# ------------------------------------------------------------------ captain poses (rig frame: +Z up, -Y front, +X his left)
def cap_out(f, lean=17, armL=(0.75, 0.35, 0.55), armR=(-0.75, 0.3, 0.6), fL=(0.55, 0.45, 0.9), fR=(-0.5, 0.5, 0.85),
            head=(0, 0.25, 1), legs=(0.65, 1.2), limp=False, side=0.0):
    sp = Vector((math.sin(R_(side)), math.sin(R_(lean)) * math.cos(R_(side)), math.cos(R_(lean)) * math.cos(R_(side)))).normalized()
    spec = {"spine": sp, "neck": (sp + Vector((0, 0.1, 0))).normalized(), "head": V(*head),
            "uarm.L": V(*armL), "farm.L": V(*fL), "uarm.R": V(*armR), "farm.R": V(*fR),
            "hand.L": V(*fL), "hand.R": V(*fR),
            "thigh.L": V(0.06, legs[0], -1), "shin.L": V(0.02, legs[1], -1), "foot.L": V(0, 0.9, -1),
            "thigh.R": V(-0.06, legs[0] - 0.05, -1), "shin.R": V(-0.02, legs[1] + 0.1, -1), "foot.R": V(0, 0.95, -1)}
    pose(CAP, f, spec)
    for s in "LR": apply_pose(CAP, s, "relaxed", f)
HOLE = AP.matrix_world @ Vector((17.86, 0.44, 4.10))          # centre of the open captain windscreen (737)
COCK_WIN = Vector((-0.31, 2.62, 1.59))                        # captain windscreen opening, cockpit set
def cap_at_nose(f, dz=-0.06):  place(CAP, f, HOLE + Vector((0, 0, dz)), 90 - 0)       # faces +X (flight direction)
def cap_at_cock(f):            place(CAP, f, COCK_WIN, 180)                         # faces +Y (the nose)
# ------------------------------------------------------------------ attendant: kneels on the captain's seat, holds his shins
def shin_pt(s, t):
    bpy.context.view_layer.update()
    return bone_w(CAP, "lowerleg01." + s).lerp(bone_w(CAP, "foot." + s), t)
def att_hold(f, lean=24, t=0.45, head=(0, -0.25, 1), pel=(-0.43, 1.70, 1.06), reach=1.0, hands=True):
    place(ATT, f, Vector(pel), 180)
    sp = Vector((0, -math.sin(R_(lean)), math.cos(R_(lean))))
    spec = {"spine": sp, "neck": (sp + Vector((0, -0.05, 0.3))).normalized(), "head": V(*head),
            "thigh.L": V(0.03, -0.25, -1), "shin.L": V(0.02, 1, -0.12), "foot.L": V(0.02, 1, 0.2),
            "thigh.R": V(-0.03, -0.25, -1), "shin.R": V(-0.02, 1, -0.12), "foot.R": V(-0.02, 1, 0.2)}
    pose(ATT, f, spec)
    if not hands: return
    for s_att, s_cap, out in (("L", "L", Vector((-1, 0, 0))), ("R", "R", Vector((1, 0, 0)))):
        c = shin_pt(s_cap, 0.8 if s_att == "R" else max(t, 0.55))   # right hand nearer the ankle: within reach, fingers clear of the knee
        up = Vector((0, 0, 1))
        palm = c + up * (0.16 if s_att == "R" else 0.135) - out * 0.01               # palm pressed down on TOP of his shin: no arm passes under or through a leg
        fd = (out + Vector((0, -0.25, -0.35))).normalized()   # fingers drape over the shin to its outer side, away from the knee
        if reach < 1.0:
            sh = bone_w(ATT, "upperarm01." + s_att); palm = sh.lerp(palm, reach)
        place_hand(ATT, s_att, f, palm, -up, fd, skin=0.0)
        apply_pose(ATT, s_att, "relaxed", f)          # palm pressed flat on the outside of his shin (a wrap grip curled into the leg)
# ------------------------------------------------------------------ helpers: cameras, markers
CAMS = {}
def camera(sid, keys, lens=35, fstop=11.0, focus=None):
    st, f0, f1 = SH[sid]
    cd = D.cameras.new("CAM_" + sid); cd.lens = lens; cd.clip_start = 0.03; cd.clip_end = 100000
    cd.dof.use_dof = focus is not None; cd.dof.aperture_fstop = fstop
    cam = D.objects.new("CAM_" + sid, cd); sc.collection.objects.link(cam); cam.rotation_mode = 'QUATERNION'
    for t, p, tg in keys:
        fr = f0 + round(t * (f1 - f0)); p = Vector(p); tg = Vector(tg)
        cam.location = p; q = (tg - p).to_track_quat('-Z', 'Y')
        if cam.rotation_quaternion.dot(q) < 0: q = -q
        cam.rotation_quaternion = q
        cam.keyframe_insert("location", frame=fr); cam.keyframe_insert("rotation_quaternion", frame=fr)
    if focus is not None: cd.dof.focus_object = focus
    lt = D.lights.new("CATCH_" + sid, 'POINT'); lt.energy = 1.5; lt.shadow_soft_size = 0.02
    lo = D.objects.new("CATCH_" + sid, lt); sc.collection.objects.link(lo); lo.parent = cam; lo.location = (0, 0.06, 0)
    m = sc.timeline_markers.new("S" + sid, frame=f0); m.camera = cam; CAMS[sid] = cam
    return cam
def F(sid, t): st, f0, f1 = SH[sid]; return f0 + round(t * (f1 - f0))       # cameras only (camera moves may fit the shot)
def Fc(sid, t): st, f0, f1 = SH[sid]; return min(f1, f0 + round(t * (P1LEN[sid] - 1)))   # characters: 1x, trimmed, never stretched
# ------------------------------------------------------------------ world motion: clouds near the 737 drift aft
cn = D.objects.new("CLOUD_DRIFT", None); sc.collection.objects.link(cn)
for o in D.collections["CLOUDS_NEAR"].objects: o.parent = cn
cn.location = (0, 0, 0); cn.keyframe_insert("location", frame=1)
cn.location = (-0.9 * sc.frame_end, 0, 0); cn.keyframe_insert("location", frame=sc.frame_end)
for fc in _fcurves(cn.animation_data.action):
    for k in fc.keyframe_points: k.interpolation = 'LINEAR'
# ------------------------------------------------------------------ FO seated at the right yoke (whole film; acting in 11/12/16)
YR = D.objects["YOKE_R"]
HORN = [Vector((0.325, 2.10, 0.82)), Vector((0.655, 2.10, 0.82))]   # yoke horn grips, measured from YOKE_R verts
GRIP_AMT = 0.0
def fo_seat(f, lean=8, head=(0, 0.05, 1), hy=0.0, ht=0.0, back=0.0):
    place(FO, f, Vector((0.48, 1.44, 0.77)), 180)
    sp = Vector((0, math.sin(R_(-lean)), math.cos(R_(-lean))))
    spec = {"spine": sp, "neck": V(0, -0.05, 1), "head": V(*head),
            "thigh.L": V(0.03, -1, 0.04), "shin.L": V(0.0, 0.35, -1), "foot.L": V(0, -1, -0.4),
            "thigh.R": V(-0.1, -1, 0.04), "shin.R": V(0.0, 0.35, -1), "foot.R": V(0, -1, -0.4)}
    pose(FO, f, spec)
    bpy.context.view_layer.update()
    for s, h in (("L", HORN[0]), ("R", HORN[1])):
        side = 1 if s == "L" else -1
        tgt = h + Vector((0, -0.17 + hy - back, 0.03 + back * 0.3))
        out = 1 if h.x > 0.5 else -1
        elbow_pole = bone_w(FO, "upperarm01." + s) + Vector((0.25 * out, 0.1, -0.7))
        spec = arm_ik(FO, s, f, tgt, elbow_pole, hand_dir=Vector((0, 1, 0.1)))
        key_pose(FO, f, spec, root=(Vector((0, 0, 0)), Quaternion()))
        apply_pose(FO, s, "relaxed", f); apply_pose(FO, s, "wrap_grip", f, amount=GRIP_AMT)
# ------------------------------------------------------------------ roof profile above the 737 captain window (for the folded-back poses)
def skin_z(x, y):
    o = AP; inv = o.matrix_world.inverted()
    ok, loc, n, i = o.ray_cast(inv @ Vector((x, y, 20.0)), Vector((0, 0, -1)))
    return (o.matrix_world @ loc).z if ok else None
for xx in (16.6, 16.9, 17.2, 17.5):
    print("ROOF", xx, round(skin_z(xx, HOLE.y) or -1, 3), round(skin_z(xx, HOLE.y + 0.4) or -1, 3))
# ------------------------------------------------------------------ papers that whip out of the open frame (plain sheets, no print)
M_paper = D.materials.new("M_paper"); M_paper.use_nodes = True
M_paper.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.95, 0.95, 0.92, 1)
PAPERS = []
for i in range(6):
    bpy.ops.mesh.primitive_plane_add(size=1); pp = bpy.context.active_object; pp.name = "PAPER_%d" % i
    pp.scale = (0.21, 0.297, 1); bpy.ops.object.transform_apply(scale=True)
    sd = pp.modifiers.new("sd", 'SIMPLE_DEFORM'); sd.deform_method = 'BEND'; sd.angle = R_(25 + 10 * i)
    pp.data.materials.append(M_paper); PAPERS.append(pp)
    pp.location = HOLE + Vector((0, 0, -1.5)); pp.keyframe_insert("location", frame=1)
def papers(sid, t0=0.05):
    st, f0, f1 = SH[sid]; rnd = random.Random(int(sid))
    for i, pp in enumerate(PAPERS):
        fs = f0 + round((t0 + 0.11 * i) * (P1LEN[sid] - 1)); fe = fs + 34
        if fs + 2 > f1: continue
        start = HOLE + Vector((rnd.uniform(0.05, 0.2), 0.42 + rnd.uniform(0.0, 0.06), 0.05))
        end = start + Vector((-7 - rnd.uniform(0, 4), 3.0 + rnd.uniform(0, 3.0), 2.0 + rnd.uniform(0, 2.0)))
        pp.location = HOLE + Vector((0, 0, -1.5)); pp.keyframe_insert("location", frame=f0)
        pp.keyframe_insert("location", frame=fs - 1)
        pp.location = start; pp.rotation_euler = (0, 0, 0); pp.keyframe_insert("location", frame=fs); pp.keyframe_insert("rotation_euler", frame=fs)
        pp.location = end; pp.rotation_euler = (rnd.uniform(4, 9), rnd.uniform(3, 7), rnd.uniform(2, 6)); pp.keyframe_insert("location", frame=fe); pp.keyframe_insert("rotation_euler", frame=fe)
        pp.location = HOLE + Vector((0, 0, -1.5)); pp.keyframe_insert("location", frame=min(fe + 1, f1)); pp.keyframe_insert("location", frame=f1)
# ------------------------------------------------------------------ flail: arm keys every ~18 frames
def clearance():
    """min signed distance (m) of the captain's spine/neck/head/shoulder bone points to the 737 skin (exterior shots)"""
    bpy.context.view_layer.update(); inv = AP.matrix_world.inverted(); best = 9.0
    for bn in ("spine03", "spine02", "spine01", "neck01", "head", "upperarm01.L", "upperarm01.R"):
        for tail in (False, True):
            p = bone_w(CAP, bn, tail); ok, loc, n, i = AP.closest_point_on_mesh(inv @ p)
            if not ok: continue
            w = AP.matrix_world @ loc; nw = (AP.matrix_world.to_3x3() @ n).normalized(); d = (p - w).length * (1 if (p - w).dot(nw) >= 0 else -1)
            best = min(best, d)
    return best
def flail(f0, f1, lean0, lean1, jaw_deg=12, step=18, amp=1.0, head=(0, 0.25, 1), legs=(0.65, 1.2), seed=1, limp=False, side=0.0, low_left=False):
    rnd = random.Random(seed); f = f0
    while True:
        t = (f - f0) / max(1, (f1 - f0)); lean = lean0 + (lean1 - lean0) * (t * t * (3 - 2 * t))
        if limp:
            cap_out(f, lean=lean, armL=(0.75, 0.75 + 0.05 * math.sin(f * 0.3), 0.15), fL=(0.5, 1.0, 0.1),
                    armR=(-0.45, 0.9 + 0.05 * math.cos(f * 0.27), 0.25), fR=(-0.3, 1.0, 0.2), head=head, legs=legs, side=side)
        else:
            a = amp; u = rnd.uniform(-1, 1); v_ = rnd.uniform(-1, 1)
            aL = (0.85, 0.55 + 0.15 * v_, -0.3 + 0.1 * u) if low_left else (0.7 + 0.15 * u, 0.75 + 0.2 * v_, 0.05 + 0.2 * a * u)
            fLL = (0.55, 0.75 + 0.15 * u, -0.15 + 0.1 * v_) if low_left else (0.35 + 0.15 * v_, 0.8 + 0.25 * u, 0.35 + 0.2 * a * v_)
            cap_out(f, lean=lean, armL=aL,
                    fL=fLL,
                    armR=(-0.7 - 0.15 * v_, 0.8 + 0.2 * u, 0.0 + 0.2 * a * v_),
                    fR=(-0.35 - 0.15 * u, 0.85 + 0.25 * v_, 0.3 + 0.2 * a * u),
                    head=(head[0] + 0.15 * rnd.uniform(-1, 1), head[1], head[2]), legs=legs, side=side)
        jaw(CAP, f, jaw_deg * (0.8 + 0.4 * rnd.random()))
        if f >= f1: break
        f = min(f1, f + step)
# ------------------------------------------------------------------ build each shot
ATT_PARK = Vector((-0.45, -0.9, 0.9))     # behind the cockpit door when not in the shot
for sid, st, f0, f1 in LAY:
    n = f1 - f0
    if st == "cock":
        bk = 0.06 if sid in ("04", "05") else 0.0
        fo_seat(f0, back=bk); fo_seat(f1, head=(-0.18, 0.05, 1) if sid == "16" else (0, 0.05, 1), back=bk)
        if sid == "11": fo_seat(Fc(sid, 0.5), head=(0.04, 0.02, 1), hy=0.015)
        if sid == "16": fo_seat(Fc(sid, 0.45), head=(-0.18, 0.05, 1))
    if sid == "01":
        cap_at_cock(f0); cap_out(f0, lean=12, legs=(1.0, 2.7)); cap_out(f1, lean=12, legs=(1.0, 2.7))
        place(ATT, f0, ATT_PARK, 180); att_hold(f0, hands=False, pel=tuple(ATT_PARK)); att_hold(f1, hands=False, pel=tuple(ATT_PARK))
        camera(sid, [(0, (78, -2950, 20), (4, -3000, 3)), (1, (46, -2974, 9.5), (13, -3000, 3.8))], lens=30)
    elif sid == "02":
        rise = Fc(sid, 0.22)
        place(CAP, f0, HOLE + Vector((0.05, 0, -0.75)), 90); place(CAP, rise, HOLE + Vector((0, 0, -0.06)), 90); place(CAP, f1, HOLE + Vector((0, 0, -0.04)), 90)
        flail(f0, f1, 0, 14, jaw_deg=7, seed=2)
        camera(sid, [(0, (23.5, -2997.0, 5.3), (17.9, -2999.6, 4.6)), (1, (22.0, -2997.6, 5.6), (17.9, -2999.6, 4.85))], lens=35)
    elif sid == "03":
        place(CAP, f0, HOLE + Vector((0, 0, -0.04)), 90); place(CAP, f1, HOLE + Vector((0, 0, -0.03)), 90)
        flail(f0, f1, 14, 20, jaw_deg=7, seed=3, step=16)
        camera(sid, [(0, (19.9, -2999.0, 4.95), (17.85, -2999.56, 4.75)), (1, (19.4, -2998.5, 5.1), (17.85, -2999.56, 4.8))], lens=35)
    elif sid in ("04", "05"):
        cap_at_cock(f0); cap_at_cock(f1)
        for k, f in enumerate(range(f0, f1 + 1, 20)):
            w = 0.0   # she is holding his shins from S04 on (director v002b): no kick, so her grip stays on the trousers
            cap_out(f, lean=12, legs=(1.0, 2.7 + w)); 
        cap_out(f1, lean=12, legs=(1.0, 2.7))
        att_hold(f0, lean=26); att_hold(Fc(sid, 0.5), lean=28); att_hold(f1, lean=26)
        if sid == "04": camera(sid, [(0, (-0.95, 1.0, 1.95), (-0.35, 2.2, 1.3)), (1, (-0.9, 1.15, 1.9), (-0.35, 2.25, 1.35))], lens=18)
        elif False: camera(sid, [(0, (-1.0, 0.85, 1.6), (-0.33, 2.2, 1.3)), (1, (-0.85, 1.25, 1.4), (-0.33, 2.4, 1.35))], lens=22)
        else: camera(sid, [(0, (0.62, 0.85, 1.85), (-0.38, 2.3, 1.35)), (1, (0.6, 1.05, 1.8), (-0.38, 2.3, 1.4))], lens=18)
    elif sid == "06":
        place(CAP, f0, HOLE + Vector((0, 0, -0.03)), 90); place(CAP, f1, HOLE + Vector((0, 0, -0.03)), 90)
        flail(f0, f1, 20, 26, jaw_deg=6, seed=6, step=20); papers(sid)
        camera(sid, [(0, (19.1, -2998.6, 4.75), (17.95, -2999.45, 4.2)), (1, (18.9, -2998.4, 4.8), (17.9, -2999.5, 4.25))], lens=30)
    elif sid == "07":
        place(CAP, f0, HOLE + Vector((0, 0, -0.03)), 90); place(CAP, f1, HOLE + Vector((0, 0, -0.03)), 90)
        flail(f0, f1, 24, 40, jaw_deg=7, seed=7); papers(sid, 0.2)
        camera(sid, [(0, (19.6, -2997.4, 3.9), (17.8, -2999.5, 4.7)), (1, (19.0, -2997.1, 4.1), (17.7, -2999.5, 4.8))], lens=28)
    elif sid == "08":
        place(CAP, f0, HOLE + Vector((0, 0, -0.03)), 90); place(CAP, f1, HOLE + Vector((0, 0, -0.03)), 90)
        flail(f0, f1, 34, 40, jaw_deg=8, seed=8, head=(0, 0.45, 1), step=14)
        camera(sid, [(0, (18.75, -2998.85, 5.55), (17.6, -2999.56, 5.0)), (1, (18.55, -2998.75, 5.5), (17.55, -2999.56, 5.0))], lens=40)
    elif sid in ("09", "10", "13", "16"):
        cap_at_cock(f0); cap_at_cock(f1)
        for k, f in enumerate(range(f0, f1 + 1, 30)):
            w = 0.06 * math.sin(k * 1.3); cap_out(f, lean=12, legs=(1.0 + w, 2.7 - w))
        cap_out(f1, lean=12, legs=(1.0, 2.7))
        if sid == "09":
            att_hold(f0, lean=18); att_hold(Fc(sid, 0.3), lean=20); att_hold(Fc(sid, 0.5), lean=6, head=(0, 0.1, 1)); att_hold(Fc(sid, 0.7), lean=16); att_hold(f1, lean=18)
            camera(sid, [(0, (-0.95, 2.15, 1.75), (-0.35, 1.95, 1.32)), (1, (-0.86, 2.06, 1.72), (-0.35, 1.95, 1.32))], lens=16)
        elif sid == "10":
            att_hold(f0, lean=18); att_hold(Fc(sid, 0.35), lean=6, head=(0.05, 0.1, 1)); att_hold(Fc(sid, 0.6), lean=16); att_hold(f1, lean=18)
            camera(sid, [(0, (-0.9, 2.1, 1.73), (-0.35, 1.95, 1.34)), (1, (-0.82, 2.02, 1.7), (-0.35, 1.95, 1.36))], lens=17)
        elif sid == "13":
            att_hold(f0, lean=27); att_hold(Fc(sid, 0.5), lean=24, head=(0, 0.05, 1)); att_hold(f1, lean=24, head=(0, 0.1, 1))
            camera(sid, [(0, (-0.95, 2.15, 1.65), (-0.42, 1.85, 1.35)), (1, (-0.93, 2.1, 1.6), (-0.42, 1.85, 1.35))], lens=26)
        else:
            att_hold(f0, lean=18); att_hold(Fc(sid, 0.4), lean=6, head=(0.1, 0.1, 1)); att_hold(Fc(sid, 0.75), lean=16); att_hold(f1, lean=18, head=(0.15, -0.2, 1))
            camera(sid, [(0, (-0.97, 2.2, 1.78), (-0.3, 1.9, 1.34)), (1, (-0.88, 2.1, 1.74), (-0.3, 1.9, 1.34))], lens=16)
    elif sid in ("11", "12"):
        cap_at_cock(f0); cap_at_cock(f1); cap_out(f0, lean=12, legs=(1.0, 2.7)); cap_out(f1, lean=12, legs=(1.0, 2.7))
        att_hold(f0, lean=26); att_hold(f1, lean=27)
        if sid == "11": camera(sid, [(0, (1.0, 2.3, 1.38), (0.45, 1.6, 1.12)), (1, (0.98, 2.2, 1.35), (0.45, 1.6, 1.12))], lens=22)
        else: camera(sid, [(0, (0.8, 2.12, 1.48), (0.46, 1.6, 1.45)), (1, (0.78, 2.07, 1.47), (0.46, 1.6, 1.45))], lens=35)
    elif sid in ("14", "15", "17"):
        place(CAP, f0, HOLE + Vector((0, 0, -0.03)), 90); place(CAP, f1, HOLE + Vector((0, 0, -0.03)), 90)
        DZ = Vector((0, 0, 0.06))
        place(CAP, f0, HOLE + DZ, 90); place(CAP, f1, HOLE + DZ, 90)
        if sid == "14":
            flail(f0, f1, 26, 33, jaw_deg=6, seed=14, side=20, head=(0.2, 0.15, 1), step=16, amp=0.8, low_left=True)
            for f in sorted(set(list(range(f0, f1 + 1, 16)) + [f1])):    # face turned to camera: clear profile
                key_pose(CAP, f, {"twist": {"head": 40, "neck03": 20}}, root=(Vector((0, 0, 0)), Quaternion()))
            print("CLEAR", sid, f1, round(clearance(), 3))
            camera(sid, [(0, (17.55, -2997.2, 5.35), (17.65, -2999.3, 4.85)), (1, (18.1, -2997.5, 5.1), (17.65, -2999.3, 4.85))], lens=35)
        else:
            flail(f0, f1, 40, 42, jaw_deg=6, seed=15, limp=True, head=(0.45, 0.3, 1), side=30)
            print("CLEAR", sid, f1, round(clearance(), 3))
            if sid == "15": camera(sid, [(0, (19.2, -2997.6, 5.75), (17.6, -2999.3, 4.8)), (1, (18.5, -2998.2, 5.4), (17.6, -2999.3, 4.85))], lens=32)
            else: camera(sid, [(0, (27, -2994.5, 7.0), (17.4, -2999.6, 4.5)), (1, (25.5, -2995.3, 6.6), (17.4, -2999.6, 4.5))], lens=35)
    elif sid in ("18", "19"):
        cap_at_cock(f0); cap_at_cock(f1)
        if sid == "18": camera(sid, [(0, (14, -2988.0, 7.0), (2.5, -2994.0, 2.2)), (1, (11.5, -2986.5, 5.8), (1.5, -2994.0, 1.8))], lens=26)
        else: camera(sid, [(0, (12.5, -2990.0, 2.6), (3.5, -2994.7, 1.4)), (1, (11.5, -2989.0, 2.3), (2.5, -2994.7, 1.3))], lens=30)
    elif st == "land":
        cap_at_cock(f0); cap_at_cock(f1)
L0 = Vector((0, -20000, -3000))
def plane_key(f, x, z, pitch=0.0):
    AL.location = L0 + Vector((x, 0, z)); AL.rotation_euler = (0, R_(-pitch), 0)
    AL.keyframe_insert("location", frame=f); AL.keyframe_insert("rotation_euler", frame=f)
def plane_path(sid, keys):
    """keys at P1 frame offsets (off, x, z, pitch); keyed at 1x from the shot start, trimmed at the shot end"""
    st, f0, f1 = SH[sid]; n = f1 - f0
    def at(off):
        for (o0, *a0), (o1, *a1) in zip(keys, keys[1:]):
            if o0 <= off <= o1:
                t = (off - o0) / (o1 - o0); return [u + (v - u) * t for u, v in zip(a0, a1)]
        return list(keys[-1][1:])
    for off, x, z, p in keys:
        if off < n: plane_key(f0 + off, x, z, p)
    x, z, p = at(n); plane_key(f1, x, z, p)
    return at
def pc(at, off, dz=3.0):
    x, z, p = at(off); return L0 + Vector((x, 0, z + dz))
at20 = plane_path("20", [(0, -950, 48, 4), (169, -620, 24, 4)]); n20 = SH["20"][2] - SH["20"][1]
camera("20", [(k / 6, L0 + Vector((-805 + 5 * k / 6, -45 + 3 * k / 6, 30 - 2 * k / 6)), pc(at20, round(n20 * k / 6))) for k in range(7)], lens=35)
at21 = plane_path("21", [(0, -420, 3.0, 4), (67, -320, 0.0, 2), (149, -220, 0.0, 0)]); n21 = SH["21"][2] - SH["21"][1]
camera("21", [(0, L0 + Vector((-345, -40, 2.2)), pc(at21, 0)), (0.5, L0 + Vector((-343, -40, 2.2)), pc(at21, n21 // 2)), (1, L0 + Vector((-341, -40, 2.2)), pc(at21, n21))], lens=28)
at22 = plane_path("22", [(0, 140, 0.0, 0), (139, 180, 0.0, 0)]); n22 = SH["22"][2] - SH["22"][1]
camera("22", [(0, L0 + Vector((193, -20, 2.6)), pc(at22, 0)), (1, L0 + Vector((192, -21, 2.5)), pc(at22, n22))], lens=30)
at23 = plane_path("23", [(0, 215, 0.0, 0), (169, 255, 0.0, 0)])
camera("23", [(0, L0 + Vector((257.5, -64, 1.7)), L0 + Vector((260.5, -40, 2.4))), (1, L0 + Vector((258.5, -63.5, 1.7)), L0 + Vector((260.5, -40, 2.5)))], lens=30, fstop=11)
at23 = None
st, f0, f1 = SH["24"]; x24 = 215 + 40 * (SH["23"][2] - SH["23"][1]) / 169.0
plane_key(f0, x24, 0.0, 0); plane_key(f1, x24, 0.0, 0)
bpy.context.scene.frame_set(f0)
H24 = L0 + Vector((x24, 0, 0)) + Vector((17.86, 0.44, 4.10))
place(CAP, f0, H24 + Vector((0, 0, 0.06)), 90); place(CAP, f1, H24 + Vector((0, 0, 0.06)), 90)
cap_out(f0, lean=40, side=24, armL=(0.75, 0.75, 0.15), fL=(0.5, 1.0, 0.1), armR=(-0.45, 0.9, 0.25), fR=(-0.3, 1.0, 0.2), head=(0.45, 0.3, 1)); jaw(CAP, f0, 4)
cap_out(f0 + 20, lean=38, side=22, armL=(0.75, 0.72, 0.18), fL=(0.5, 1.0, 0.15), armR=(-0.45, 0.88, 0.28), fR=(-0.3, 1.0, 0.25), head=(0.25, 0.15, 1)); jaw(CAP, f0 + 20, 3)
cap_out(f1, lean=36, side=20, armL=(0.72, 0.7, 0.2), fL=(0.45, 0.95, 0.2), armR=(-0.45, 0.85, 0.3), fR=(-0.3, 0.95, 0.3), head=(0.12, 0.05, 1)); jaw(CAP, f1, 2)
camera("24", [(0, H24 + Vector((1.9, 2.3, 1.2)), H24 + Vector((-0.2, 0.3, 0.55))), (1, H24 + Vector((1.6, 2.0, 1.1)), H24 + Vector((-0.2, 0.3, 0.6)))], lens=35)
for o_ in [D.objects[n] for n in ("HILLS", "GRASS", "RUNWAY", "RUNWAY_PAINT", "FENCE_MESH", "FENCE_POSTS", "EDGE_LIGHTS", "EDGE_LAMPS")]:
    for f_, hv in ((1, True), (SH["20"][1], False)):
        o_.hide_render = hv; o_.hide_viewport = hv
        o_.keyframe_insert("hide_render", frame=f_); o_.keyframe_insert("hide_viewport", frame=f_)
for sid in [k for k in SH if SH[k][0] != "land"]:
    st, f0, f1 = SH[sid]; plane_key(f0, -1250, 70, 4)
# cuts: constant interpolation on object transforms of the rigs, the landing plane; markers bind cameras
for o in (CAP, FO, ATT, AL): const_interp(o)
for o in (AL,):
    ad = o.animation_data
    for fc in _fcurves(ad.action):
        kp = fc.keyframe_points
        for i, k in enumerate(kp): k.interpolation = 'LINEAR'
# landing plane: hold position across the cockpit/sky shots (constant), linear within the landing shots
for fc in _fcurves(AL.animation_data.action):
    for k in fc.keyframe_points:
        if k.co.x < SH["20"][1]: k.interpolation = 'CONSTANT'
sc.camera = CAMS["01"]
r = sc.render; r.resolution_x = 1080; r.resolution_y = 1920; r.fps = 60
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("SHOTS_OK", LAY[-1])
