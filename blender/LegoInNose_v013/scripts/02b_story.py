# LegoInNose v013 stage B part 2 (exec'd by 02_animate.py): faces, nostril/passage, x-ray, the story keyed in time order.

# ================================================================== face rig helpers (directions solved numerically per rig)
_NUDGE = {}
def nudge_q(rig, bone, want, deg):
    key = (rig.name, bone, tuple(round(x, 2) for x in want))
    if key not in _NUDGE:
        pb = rig.pose.bones[bone]; q0 = pb.rotation_quaternion.copy(); upd()
        base = Wt(rig, bone); best = None
        for ax in ((1, 0, 0), (0, 0, 1), (0, 1, 0)):
            for sg in (1, -1):
                pb.rotation_quaternion = Quaternion(ax, math.radians(10 * sg)); upd()
                d = (Wt(rig, bone) - base).dot(Vector(want).normalized())
                if best is None or d > best[0]: best = (d, ax, sg)
        pb.rotation_quaternion = q0; upd()
        _NUDGE[key] = best
    d, ax, sg = _NUDGE[key]
    return Quaternion(ax, math.radians(deg * sg))

def face_dirs(rig):
    """world directions of the face at rest-orientation of the root (rig faces -Y at rest)"""
    return Vector((0, -1, 0)), Vector((0, 0, 1))

def key_face(rig, f, smile=0.0, jaw=0.0, brow=0.0, squint=0.0, pucker=0.0):
    """expressions as bone nudges (rest-relative). smile 0..1, jaw 0..1 open, brow -1(frown)..1(raised), squint 0..1"""
    up = Vector((0, 0, 1))
    for s, sx in (("L", 1), ("R", -1)):
        out = Vector((sx, 0, 0))
        for b, amt in (("risorius03." + s, 14), ("levator05." + s, 10), ("oris04." + s, 8)):
            if b in rig.pose.bones:
                q = nudge_q(rig, b, up + out * 0.7, amt) if smile >= 0 else nudge_q(rig, b, -up + out * 0.2, amt)
                pb = rig.pose.bones[b]; pb.rotation_quaternion = Quaternion().slerp(q, abs(smile)); pb.keyframe_insert("rotation_quaternion", frame=f)
        for b in ("oculi01." + s, "oculi02." + s):
            if b in rig.pose.bones:
                q = nudge_q(rig, b, up, 10) if brow >= 0 else nudge_q(rig, b, -up - out * 0.5, 10)
                pb = rig.pose.bones[b]; pb.rotation_quaternion = Quaternion().slerp(q, abs(brow)); pb.keyframe_insert("rotation_quaternion", frame=f)
        b = "orbicularis04." + s     # lower lid up for squint
        if b in rig.pose.bones:
            q = nudge_q(rig, b, up, 12); pb = rig.pose.bones[b]; pb.rotation_quaternion = Quaternion().slerp(q, squint); pb.keyframe_insert("rotation_quaternion", frame=f)
    q = nudge_q(rig, "jaw", -up, 14); pb = rig.pose.bones["jaw"]; pb.rotation_quaternion = Quaternion().slerp(q, jaw); pb.keyframe_insert("rotation_quaternion", frame=f)

def blinks(rig, frames, close_deg=26):
    for s in "LR":
        b = "orbicularis03." + s; pb = rig.pose.bones[b]
        q = nudge_q(rig, b, Vector((0, 0, -1)), close_deg)
        pb.rotation_quaternion = Quaternion(); pb.keyframe_insert("rotation_quaternion", frame=1)
        for bf in frames:
            for df, u in ((0, 0), (3, 1), (6, 1), (11, 0)):
                pb.rotation_quaternion = Quaternion().slerp(q, u); pb.keyframe_insert("rotation_quaternion", frame=bf + df)

def eyes_closed(rig, f0, f1, ramp=8):
    for s in "LR":
        b = "orbicularis03." + s; pb = rig.pose.bones[b]; q = nudge_q(rig, b, Vector((0, 0, -1)), 26)
        for f, u in ((f0, 0), (f0 + ramp, 1), (f1 - ramp, 1), (f1, 0)):
            pb.rotation_quaternion = Quaternion().slerp(q, u); pb.keyframe_insert("rotation_quaternion", frame=f)

def saccades(ctrl, f0, f1, every=40, amp=(3, 5), seed=1):
    rnd = random.Random(seed)
    for f in range(f0, f1, every):
        for s in "LR":
            ctrl.key_rot("eye." + s, f, [("X", rnd.uniform(-amp[0], amp[0])), ("Z", rnd.uniform(-amp[1], amp[1]))])

def breathe(ctrl, f0, f1, base_flex, per=200, amp=1.2, twist=0.0):
    for f in range(f0, f1 + 1, 20):
        key_spine(ctrl, f, flex=base_flex(f) + amp * math.sin(2 * math.pi * f / per), twist=twist)

# ================================================================== nostril + passage in head REST space (per character)
FACEB = ("head", "levator", "oris", "risorius", "special", "jaw", "orbic", "oculi", "temporalis")
def nostril_rest(body, rig, dom, side="R"):
    sx = 1 if side == "L" else -1
    vs = body.data.vertices; ez = rig.data.bones["eye.L"].head_local.z
    mid = [v for v in vs if abs(v.co.x) < 0.004 and ez - 0.07 < v.co.z < ez - 0.01 and (dom.get(v.index) or "").startswith(FACEB)]
    tip = min(mid, key=lambda v: v.co.y).co.copy()
    cand = [v for v in vs if 0.003 < v.co.x * sx < 0.016 and tip.z - 0.026 < v.co.z < tip.z - 0.002 and tip.y - 0.002 < v.co.y < tip.y + 0.03
            and v.normal.z < -0.45 and (dom.get(v.index) or "").startswith(FACEB)]
    if not cand: cand = [v for v in vs if 0.003 < v.co.x * sx < 0.016 and tip.z - 0.03 < v.co.z < tip.z and tip.y < v.co.y < tip.y + 0.03]
    N = sum((v.co for v in cand), Vector()) / len(cand)
    return tip, N + Vector((0, 0, 0.0025)), len(cand)

A_REST = Vector((0, 0.55, 1.0)).normalized()         # vestibule: up and back
D2_REST = Vector((0, 1.0, 0.12)).normalized()         # then back along the nasal floor
def path_dir(t, k=1.0):
    u = smoothstep((t / k - 0.004) / 0.016)
    return A_REST.lerp(D2_REST, u).normalized()
def path_pt(N, t, k=1.0, n=40):
    p = Vector(N); dt = t / n
    for i in range(n): p = p + path_dir((i + 0.5) * dt, k) * dt
    return p

def head_M(rig, f=None):
    if f is not None: fs(f)
    pb = rig.pose.bones["head"]
    return rig.matrix_world @ pb.matrix @ rig.data.bones["head"].matrix_local.inverted()

BRICK_LEN = 0.0114   # brick + stud height along its z
def brick_M_rest(N, tb, kind, k=1.0):
    """rest-space matrix of a brick in the passage: bottom face (origin) at path parameter tb (the deep end),
    studs pointing OUT toward the nostril, so the next brick's bottom can click onto them"""
    z = -path_dir(tb, k); X = Vector((1, 0, 0))
    x = X if kind == "red" else z.cross(X).normalized()
    y = z.cross(x).normalized(); x = y.cross(z).normalized()
    R = Matrix((x, y, z)).transposed()
    M = R.to_4x4(); M.translation = path_pt(N, tb, k); return M

BOY_TIP, BOY_N, nc = nostril_rest(BB, BOY, DOMB)
MAN_TIP, MAN_N, nc2 = nostril_rest(NB, MAN, DOMN)
log("nostril boy", tuple(round(x, 4) for x in BOY_N), "tip", tuple(round(x, 4) for x in BOY_TIP), nc, "man", tuple(round(x, 4) for x in MAN_N), nc2)
K_MAN = (MAN_TIP - MAN.data.bones["eye.L"].head_local).length / (BOY_TIP - BOY.data.bones["eye.L"].head_local).length
log("man/boy face scale", round(K_MAN, 3))

# ---- passage mesh (x-ray anatomy): a curved tube with turbinate bumps, in REST space of each head, parented to the head bone
mucosa = bpy.data.materials.new("M_Passage"); mucosa.use_nodes = True
nt = mucosa.node_tree; p_ = nt.nodes["Principled BSDF"]
p_.inputs["Base Color"].default_value = (0.95, 0.42, 0.45, 1); p_.inputs["Roughness"].default_value = 0.3; p_.inputs["Coat Weight"].default_value = 0.5
lw = nt.nodes.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.4
tr = nt.nodes.new("ShaderNodeBsdfTransparent")
fm_ = nt.nodes.new("ShaderNodeMapRange"); fm_.inputs["To Min"].default_value = 0.06; nt.links.new(lw.outputs["Facing"], fm_.inputs["Value"])
mx = nt.nodes.new("ShaderNodeMixShader"); nt.links.new(fm_.outputs["Result"], mx.inputs["Fac"])
nt.links.new(tr.outputs["BSDF"], mx.inputs[1]); nt.links.new(p_.outputs["BSDF"], mx.inputs[2])
nt.links.new(mx.outputs["Shader"], nt.nodes["Material Output"].inputs["Surface"])
skull_m = bpy.data.materials["M_SkullBone"]
nt = skull_m.node_tree; p_ = nt.nodes["Principled BSDF"]
lw = nt.nodes.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.25
tr = nt.nodes.new("ShaderNodeBsdfTransparent")
fm2 = nt.nodes.new("ShaderNodeMapRange"); fm2.inputs["To Min"].default_value = 0.25; nt.links.new(lw.outputs["Facing"], fm2.inputs["Value"])
mx = nt.nodes.new("ShaderNodeMixShader"); nt.links.new(fm2.outputs["Result"], mx.inputs["Fac"])
nt.links.new(tr.outputs["BSDF"], mx.inputs[1]); nt.links.new(p_.outputs["BSDF"], mx.inputs[2])
nt.links.new(mx.outputs["Shader"], nt.nodes["Material Output"].inputs["Surface"])

def passage(name, rig, N, k):
    pts = [N - A_REST * 0.006 * k] + [path_pt(N, t * k, k) for t in (0.0, 0.008, 0.016, 0.026, 0.040, 0.056, 0.072)]
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.0068 * k; cu.bevel_resolution = 6
    sp = cu.splines.new('BEZIER'); sp.bezier_points.add(len(pts) - 1)
    for i, q in enumerate(pts):
        bp = sp.bezier_points[i]; bp.co = q; bp.handle_left_type = bp.handle_right_type = 'AUTO'
        bp.radius = (1.15 if i < 2 else 1.0 if i < 5 else 1.35)
    cu.use_fill_caps = False
    ob = bpy.data.objects.new(name, cu); sc.collection.objects.link(ob); cu.materials.append(mucosa)
    bpy.context.view_layer.objects.active = ob; ob.select_set(True)
    bpy.ops.object.convert(target='MESH'); ob = bpy.context.active_object
    tex = bpy.data.textures.new(name + "_t", 'CLOUDS'); tex.noise_scale = 0.006
    d = ob.modifiers.new("bumps", 'DISPLACE'); d.texture = tex; d.strength = 0.0018 * k; d.mid_level = 0.5
    for p in ob.data.polygons: p.use_smooth = True
    c = ob.constraints.new('CHILD_OF'); c.target = rig; c.subtarget = "head"
    c.inverse_matrix = rig.data.bones["head"].matrix_local.inverted() @ Matrix.Identity(4)   # rest space -> follows the head deform
    c.inverse_matrix = (rig.matrix_world @ rig.data.bones["head"].matrix_local).inverted()
    ob.select_set(False)
    return ob

def skull_for(rig, body, dom, name):
    sk = O["Skull"].copy(); sk.data = O["Skull"].data.copy(); sk.name = name; sc.collection.objects.link(sk)
    hv = [v.co for v in body.data.vertices if (dom.get(v.index) or "").startswith(FACEB) and v.co.z > rig.data.bones["neck03"].head_local.z]
    mn = Vector([min(v[i] for v in hv) for i in range(3)]); mx_ = Vector([max(v[i] for v in hv) for i in range(3)])
    d0 = sk.data; bb = [v.co for v in d0.vertices]
    smn = Vector([min(v[i] for v in bb) for i in range(3)]); smx = Vector([max(v[i] for v in bb) for i in range(3)])
    s = (mx_.x - mn.x - 0.014) / (smx.x - smn.x) * 0.86
    sk.data.transform(Matrix.Translation(-(smn + smx) / 2))
    sk.data.transform(Matrix.Scale(s, 4))
    if SKULL_FLIP: sk.data.transform(Matrix.Rotation(math.pi, 4, 'Z'))
    sk.matrix_world = Matrix.Translation(Vector(((mn.x + mx_.x) / 2, (mn.y + mx_.y) / 2 + 0.016, mx_.z - 0.016 - (smx.z - smn.z) * s / 2)))
    upd(); Mrest = sk.matrix_world.copy()
    c = sk.constraints.new('CHILD_OF'); c.target = rig; c.subtarget = "head"
    c.inverse_matrix = (rig.matrix_world @ rig.data.bones["head"].matrix_local).inverted()
    sk.matrix_basis = Mrest
    return sk
SKULL_FLIP = True
fs(0)
# rest-space parenting: evaluate constraints against the REST head (set at frame 0 with the pose cleared is not needed: the
# Child Of inverse uses the rest bone matrix, so the child = posed_head @ rest_head^-1 @ rest_world, i.e. it rides the head deform)
PASS_B = passage("PassageBoy", BOY, BOY_N, 1.0)
PASS_M = passage("PassageMan", MAN, MAN_N, K_MAN)
SK_B = skull_for(BOY, BB, DOMB, "SkullBoy"); SK_M = skull_for(MAN, NB, DOMN, "SkullMan")
SK_M.data = SK_B.data.copy()
O["Skull"].hide_render = O["Skull"].hide_viewport = True
log("skulls", tuple(round(d, 3) for d in SK_B.dimensions), tuple(round(d, 3) for d in SK_M.dimensions))

# ================================================================== x-ray (per character): skin turns to a glass window round the nose
def make_xray(rig, body, dom, tag):
    # vertex attribute: 1 on face/head skin (hands etc. never go glass)
    at = body.data.attributes.get("xr") or body.data.attributes.new("xr", 'FLOAT', 'POINT')
    for v in body.data.vertices:
        d = dom.get(v.index) or ""
        at.data[v.index].value = 1.0 if (d.startswith(FACEB) or d.startswith(("neck03",))) else 0.0
    g = bpy.data.node_groups.new("XRay_" + tag, 'ShaderNodeTree')
    g.interface.new_socket("Shader", in_out='INPUT', socket_type='NodeSocketShader')
    g.interface.new_socket("Mask", in_out='INPUT', socket_type='NodeSocketFloat')
    g.interface.new_socket("Shader", in_out='OUTPUT', socket_type='NodeSocketShader')
    gi = g.nodes.new("NodeGroupInput"); go = g.nodes.new("NodeGroupOutput")
    E = bpy.data.objects.new("XMask_" + tag, None); sc.collection.objects.link(E); E.empty_display_size = 0.03
    tc = g.nodes.new("ShaderNodeTexCoord"); tc.object = E
    ln = g.nodes.new("ShaderNodeVectorMath"); ln.operation = 'LENGTH'; g.links.new(tc.outputs["Object"], ln.inputs[0])
    mr = g.nodes.new("ShaderNodeMapRange"); mr.interpolation_type = 'SMOOTHSTEP'
    mr.inputs["From Min"].default_value = 0.7; mr.inputs["From Max"].default_value = 1.0; mr.inputs["To Min"].default_value = 1.0; mr.inputs["To Max"].default_value = 0.0
    g.links.new(ln.outputs["Value"], mr.inputs["Value"])
    st = g.nodes.new("ShaderNodeValue"); st.name = "XStrength"; st.outputs[0].default_value = 0.0
    va = g.nodes.new("ShaderNodeValue"); va.name = "Vanish"; va.outputs[0].default_value = 0.0
    m1 = g.nodes.new("ShaderNodeMath"); m1.operation = 'MULTIPLY'; g.links.new(mr.outputs["Result"], m1.inputs[0]); g.links.new(gi.outputs["Mask"], m1.inputs[1])
    geo = g.nodes.new("ShaderNodeNewGeometry")
    bf = g.nodes.new("ShaderNodeMath"); bf.operation = 'MULTIPLY'; g.links.new(geo.outputs["Backfacing"], bf.inputs[0]); g.links.new(gi.outputs["Mask"], bf.inputs[1])
    tr = g.nodes.new("ShaderNodeBsdfTransparent"); tr.inputs["Color"].default_value = (0.95, 0.98, 1.0, 1)
    lw = g.nodes.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.22
    em = g.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (0.45, 0.88, 1.0, 1); em.inputs["Strength"].default_value = 1.6
    rim = g.nodes.new("ShaderNodeMixShader"); g.links.new(lw.outputs["Facing"], rim.inputs["Fac"])
    g.links.new(tr.outputs["BSDF"], rim.inputs[1]); g.links.new(em.outputs["Emission"], rim.inputs[2])
    bk = g.nodes.new("ShaderNodeEmission"); bk.inputs["Color"].default_value = (0.10, 0.30, 0.52, 1); bk.inputs["Strength"].default_value = 1.0
    inner = g.nodes.new("ShaderNodeMixShader"); g.links.new(geo.outputs["Backfacing"], inner.inputs["Fac"])
    g.links.new(rim.outputs["Shader"], inner.inputs[1]); g.links.new(bk.outputs["Emission"], inner.inputs[2])
    mx_ = g.nodes.new("ShaderNodeMath"); mx_.operation = 'MAXIMUM'; g.links.new(m1.outputs[0], mx_.inputs[0]); g.links.new(bf.outputs[0], mx_.inputs[1])
    fm = g.nodes.new("ShaderNodeMath"); fm.operation = 'MULTIPLY'; g.links.new(mx_.outputs[0], fm.inputs[0]); g.links.new(st.outputs[0], fm.inputs[1])
    fin = g.nodes.new("ShaderNodeMixShader"); g.links.new(fm.outputs[0], fin.inputs["Fac"])
    g.links.new(gi.outputs["Shader"], fin.inputs[1]); g.links.new(inner.outputs["Shader"], fin.inputs[2])
    tr2 = g.nodes.new("ShaderNodeBsdfTransparent")
    van = g.nodes.new("ShaderNodeMixShader"); g.links.new(va.outputs[0], van.inputs["Fac"])
    g.links.new(fin.outputs["Shader"], van.inputs[1]); g.links.new(tr2.outputs["BSDF"], van.inputs[2])
    g.links.new(van.outputs["Shader"], go.inputs[0])
    done = set()
    for c in rig.children:
        if c.type != 'MESH': continue
        for m in c.data.materials:
            if not m or not m.use_nodes or m.name in done: continue
            done.add(m.name)
            nt = m.node_tree; outs = [n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL']
            out = ([n for n in outs if n.is_active_output] or outs)[0]
            if not out.inputs["Surface"].links: continue
            src = out.inputs["Surface"].links[0].from_socket
            gn = nt.nodes.new("ShaderNodeGroup"); gn.node_tree = g
            nt.links.new(src, gn.inputs[0]); nt.links.new(gn.outputs[0], out.inputs["Surface"])
            if c == body:
                an = nt.nodes.new("ShaderNodeAttribute"); an.attribute_name = "xr"; nt.links.new(an.outputs["Fac"], gn.inputs["Mask"])
            else:
                gn.inputs["Mask"].default_value = 0.0
    c = E.constraints.new('CHILD_OF'); c.target = rig; c.subtarget = "head"
    c.inverse_matrix = (rig.matrix_world @ rig.data.bones["head"].matrix_local).inverted()
    return dict(g=g, E=E, S=g.nodes["XStrength"].outputs[0], V=g.nodes["Vanish"].outputs[0])
XB = make_xray(BOY, BB, DOMB, "Boy"); XN = make_xray(MAN, NB, DOMN, "Man"); XM = make_xray(MOM, MB, DOMM, "Mom")
def key_x(X, f, v): X["S"].default_value = v; X["S"].keyframe_insert("default_value", frame=f)
def key_van(X, f, v): X["V"].default_value = v; X["V"].keyframe_insert("default_value", frame=f)
def key_mask(X, f, center_rest, r):
    X["E"].location = center_rest; X["E"].scale = (r, r, r)
    X["E"].keyframe_insert("location", frame=f); X["E"].keyframe_insert("scale", frame=f)
for X_ in (XB, XN, XM): key_x(X_, 1, 0.0); key_van(X_, 1, 0.0)

# anatomy visibility follows the x-ray (never seen through opaque skin, never outside it)
def anat_vis(objs, f, show):
    for o in objs: vis(o, f, show)

# ================================================================== props: grip offsets and placement through the hand (R4)
PROP_OFF = {}
def grab(rig, s, f, prop):
    """prop becomes Child Of wrist.<s> from frame f (world continuous); records the grip offset"""
    owner_switch(prop, f, rig, "wrist." + s, log)
    fs(f); PROP_OFF[prop.name] = (rig, s, W(rig, "wrist." + s).inverted() @ prop.matrix_world)

def place_prop(ctrl, f, prop, Mdes, pose=None, it=7, pole=None):
    """key IK_hand so the held prop lands at world matrix Mdes (orientation through the wrist, translation refined)"""
    rig, s, off = PROP_OFF[prop.name]
    if pose: apply_pose(rig, s, pose, f)
    Wd = Mdes @ off.inverted()
    ctrl.key_world("IK_hand." + s, f, rig.matrix_world.inverted() @ Wd)
    if pole is not None: key_pole(ctrl, s, f, pole)
    pb = rig.pose.bones["IK_hand." + s]; Rr = rig.data.bones["IK_hand." + s].matrix_local.to_3x3().inverted()
    for k in range(it):
        fs(f); err = Mdes.translation - prop.matrix_world.translation
        if err.length < 0.0008: break
        pb.location = pb.location + Rr @ err; pb.keyframe_insert("location", frame=f, group=pb.name)
    fs(f); e = (Mdes.translation - prop.matrix_world.translation).length
    ang = math.degrees(Mdes.to_quaternion().rotation_difference(prop.matrix_world.to_quaternion()).angle)
    if e > 0.003 or ang > 20: log("PLACE_ERR", prop.name, f, round(e * 1000, 1), "mm", round(ang), "deg")
    return e

def swing_to(Mcur, z_target, pos):
    """rotate Mcur minimally so its local z points along z_target; put its origin at pos"""
    R = Mcur.to_3x3().normalized(); q = R.col[2].rotation_difference(Vector(z_target).normalized())
    M = (q.to_matrix() @ R).to_4x4(); M.translation = pos; return M

def brick_world(rig, N, tb, kind, f, k=1.0):
    return head_M(rig, f) @ brick_M_rest(N, tb, kind, k)

def key_brick_head(obj, rig, N, f, tb, kind, k=1.0):
    key_world_while_owned(obj, f, brick_world(rig, N, tb, kind, f, k))

def stud_end(obj):
    return obj.matrix_world @ Vector((0, 0, BRICK_LEN))

def tip_of(rig, s, finger=2): return Wt(rig, "finger%d-3.%s" % (finger, s))

def mask_anat(obj, X, tag):
    """anatomy only shows inside the x-ray window (never pokes out of the face)"""
    new = []
    for i, m in enumerate(obj.data.materials):
        m2 = m.copy(); m2.name = m.name + "_" + tag; obj.data.materials[i] = m2
        nt = m2.node_tree; out = nt.nodes["Material Output"]; src = out.inputs["Surface"].links[0].from_socket
        tc = nt.nodes.new("ShaderNodeTexCoord"); tc.object = X["E"]
        ln = nt.nodes.new("ShaderNodeVectorMath"); ln.operation = 'LENGTH'; nt.links.new(tc.outputs["Object"], ln.inputs[0])
        mr = nt.nodes.new("ShaderNodeMapRange"); mr.interpolation_type = 'SMOOTHSTEP'
        mr.inputs["From Min"].default_value = 0.75; mr.inputs["From Max"].default_value = 0.98; mr.inputs["To Min"].default_value = 1.0; mr.inputs["To Max"].default_value = 0.0
        nt.links.new(ln.outputs["Value"], mr.inputs["Value"])
        tr = nt.nodes.new("ShaderNodeBsdfTransparent"); mx = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(mr.outputs["Result"], mx.inputs["Fac"]); nt.links.new(tr.outputs["BSDF"], mx.inputs[1]); nt.links.new(src, mx.inputs[2])
        nt.links.new(mx.outputs["Shader"], out.inputs["Surface"])
for o_, X_, t_ in ((PASS_B, XB, "B"), (SK_B, XB, "B"), (PASS_M, XN, "M"), (SK_M, XN, "M")):
    mask_anat(o_, X_, t_)
ANAT_B = [PASS_B, SK_B]; ANAT_M = [PASS_M, SK_M]

# ================================================================== BOY acting: head, spine, face (keyed before any anchor is measured)
BOYHEAD = [(1, 18, 28), (22, 22, 32), (40, 12, 14), (60, 4, -2), (78, 0, -6), (95, 0, -14), (135, 0, -12), (150, -8, -4), (175, 8, 6),
           (194, 16, 22), (240, 22, 32), (270, 8, 8), (300, 0, -14), (335, 0, -12), (370, -12, -6), (420, -16, -10), (440, 0, -14),
           (470, 2, -10), (510, 8, 0), (545, 0, -12), (600, 0, -14), (640, 0, -6), (700, -10, -4), (730, 10, -6), (760, -30, -8),
           (800, -62, -18), (860, -64, -20), (900, -56, -12), (940, -40, -6), (1000, -30, -2), (1060, -18, -4), (1140, -12, -4), (1300, -12, -4)]
for f, yw, pt in BOYHEAD: key_head(PR, f, yw, pt)
BOYSPINE = [(1, 10, 6, 8), (22, 16, 10, 10), (50, 6, 2, 2), (95, 2, 0, 0), (180, 6, 2, 2), (194, 10, 6, 6), (240, 16, 10, 10), (280, 4, 0, 0),
            (500, 2, 0, 0), (560, 4, 0, 0), (700, 2, 0, 0), (780, 0, -12, -6), (820, 4, -20, -12), (900, 4, -18, -10), (1000, 2, -8, -2), (1300, 2, -8, -2)]
for f, fl, tw, sd in BOYSPINE: key_spine(PR, f, flex=fl, twist=tw, side=sd)
for f, fl in ((1, -4), (700, -4), (735, -7), (760, -4), (1300, -4)): boy_root(f, flex=fl)
blinks(BOY, [70, 180, 262, 350, 430, 530, 620, 690, 790, 880, 960, 1030, 1110])
saccades(PR, 1, 1300, every=37, seed=2)
for f, kw in ((1, {}), (60, dict(brow=0.4)), (100, dict(brow=0.3, squint=0.3)), (140, dict(brow=-0.3, jaw=0.15)), (180, {}),
              (330, dict(brow=0.2)), (380, dict(smile=0.4, brow=0.3)), (470, dict(smile=0.9, brow=0.5)), (530, dict(smile=0.7, jaw=0.2, brow=0.3)),
              (580, dict(brow=-0.6, squint=0.5, smile=-0.3)), (640, dict(brow=0.6, jaw=0.3)), (700, dict(brow=0.8, jaw=0.15, squint=0.4)),
              (740, dict(brow=0.7, jaw=0.45)), (790, dict(brow=0.8, jaw=0.55, smile=-0.4)), (830, dict(brow=0.6, jaw=0.2, squint=0.3)),
              (900, dict(brow=0.4, jaw=0.1)), (940, dict(smile=0.8, brow=0.3)), (1020, dict(smile=0.6, squint=0.5)), (1100, dict(smile=0.4)), (1300, dict(smile=0.4))):
    key_face(BOY, f, **kw)

# ================================================================== MOM acting: reading on the sofa, looks up, reaches, removes the yellow brick
MOMHEAD = [(1, 0, 30), (300, 4, 32), (600, -4, 30), (760, 0, 26), (775, 18, -2), (820, 26, 4), (860, 28, 8), (900, 22, 0), (950, 8, -8), (1050, 14, 0), (1300, 14, 0)]
for f, yw, pt in MOMHEAD: key_head(MR, f, yw, pt)
MOMSPINE = [(1, 8, 0, 0), (760, 8, 0, 0), (790, 14, -8, 0), (830, 34, 12, 0), (880, 34, 12, 0), (930, 18, 4, 0), (990, 10, 0, 0), (1300, 10, 0, 0)]
for f, fl, dx in ((1, 0, 0), (790, 0, 0), (830, 16, 0.05), (885, 16, 0.05), (940, 4, 0.0), (1300, 0, 0)): mom_root(f, dx=dx, flex=fl)
for f, fl, tw, sd in MOMSPINE: key_spine(MR, f, flex=fl, twist=tw, side=sd)
blinks(MOM, [50, 210, 380, 560, 700, 790, 880, 1000, 1150])
saccades(MR, 1, 1300, every=43, seed=3)
for f, kw in ((1, dict(smile=0.2)), (760, dict(smile=0.1)), (780, dict(brow=0.6, jaw=0.2)), (830, dict(brow=0.3, squint=0.2)),
              (870, dict(brow=-0.2, squint=0.4)), (905, dict(smile=0.7, brow=0.3)), (1000, dict(smile=0.8)), (1300, dict(smile=0.6))):
    key_face(MOM, f, **kw)

# ================================================================== anchors (heads now move): book on Mom's lap, tweezers on the seat
fs(1)
def lap_point(rig, trs_obj, u=0.55):
    hp = (Wh(rig, "upperleg01.L") + Wh(rig, "upperleg01.R")) / 2; kn = (Wh(rig, "lowerleg01.L") + Wh(rig, "lowerleg01.R")) / 2
    c = hp.lerp(kn, u); zs = []
    for s in "LR":
        q = Wh(rig, "upperleg01." + s).lerp(Wh(rig, "lowerleg01." + s), u); zz = ray_down([trs_obj], q.x, q.y)
        if zz is not None: zs.append(zz)
    return Vector((c.x, c.y, max(zs)))
LAP = lap_point(MOM, O["Mom.trousers"])
BOOK.rotation_mode = 'XYZ'; BOOK.location = LAP + Vector((0, 0, 0.001)); BOOK.rotation_euler = (0, math.radians(-6), math.radians(90))
upd()
# tweezers lying on the seat cushion at Mom's right (-Y side)
TW_XY = Vector((MOM_X + 0.06, MY + 0.23))
tz = ray_down([SOFA], TW_XY.x, TW_XY.y)
TWZ.rotation_mode = 'XYZ'; TWZ.location = (TW_XY.x, TW_XY.y, tz + 0.006); TWZ.rotation_euler = (math.radians(90), 0, math.radians(-110))
upd()
bb = [TWZ.matrix_world @ Vector(c) for c in TWZ.bound_box]; zmin = min(p.z for p in bb); TWZ.location.z += (tz + 0.001) - zmin; upd()
log("book lap", tuple(round(x, 3) for x in LAP), "tweezers seat z", round(tz, 3))
def book_edge(s):
    sx = 1 if s == "L" else -1     # Mom faces +X: her left is +Y
    return BOOK.matrix_world @ Vector((0.0, 0.0, 0.022)) + Vector((0.0, sx * 0.075, 0))
for f in (1, 300, 600, 760, 880):
    rest_hand(MOM, MR, "R", f, book_edge("R"), Vector((0, 0, -1)), Vector((1, -0.25, -0.1)), pose="relaxed")
for f in (1, 300, 600, 760):
    rest_hand(MOM, MR, "L", f, book_edge("L"), Vector((0, 0, -1)), Vector((1, 0.25, -0.1)), pose="relaxed")
    rest_hand(MOM, MR, "R", f, book_edge("R"), Vector((0, 0, -1)), Vector((1, -0.25, -0.1)), pose="relaxed")
for f in (1000, 1300):
    rest_hand(MOM, MR, "R", f, book_edge("R"), Vector((0, 0, -1)), Vector((1, -0.25, -0.1)), pose="relaxed")
apply_pose(MOM, "L", "relaxed", 1)
for f in (450,):   # page turn gesture: L hand lifts the page corner a little
    rest_hand(MOM, MR, "L", f, book_edge("L") + Vector((0.03, -0.01, 0.025)), Vector((0, 0, -1)), Vector((1, 0.25, 0.1)), pose="relaxed")

# ================================================================== BOY right hand rests on his right knee
def knee_top(rig, s, trs_obj, f):
    fs(f); k = Wh(rig, "lowerleg01." + s); z = ray_down([trs_obj], k.x, k.y - 0.02)
    return Vector((k.x, k.y - 0.02, z))
def rug_r(f):
    fs(f); h = Wh(BOY, "upperleg01.R"); return Vector((h.x - 0.13, h.y - 0.06, RUG))
for f in (1, 300, 600, 700):
    rest_hand(BOY, PR, "R", f, rug_r(f), Vector((0, 0, -1)), Vector((-0.2, -1, 0)), pose="relaxed")

TOY_DX = BX + 0.30
for o_ in [o for o in O if o.name.startswith(("Scatter", "ToyTub", "BrickRed", "BrickYellow"))]: o_.location.x += TOY_DX
upd()
# ================================================================== the bricks (ONE red model, ONE yellow model): rug -> hand -> nostril
N_B = BOY_N
fs(1)
RED.rotation_mode = 'QUATERNION'; YEL.rotation_mode = 'QUATERNION'
RED0 = RED.matrix_world.copy(); YEL0 = YEL.matrix_world.copy()
key_basis(RED, 1, RED0); key_basis(YEL, 1, YEL0)
def brick_center(o): return o.matrix_world @ Vector((0, 0, 0.0048))
FD_PICK = Vector((0.15, -0.35, -0.92)).normalized()      # fingers down-forward at the pick
PN_PICK = Vector((0.0, 0.92, -0.35)).normalized()       # palm toward the body, down

# --- red: reach, pinch, lift, look, carry to the nostril
reach(BOY, PR, "L", 1, brick_center(RED) + Vector((0.02, -0.02, 0.06)), FD_PICK, PN_PICK, pose="relaxed")
reach(BOY, PR, "L", 14, brick_center(RED) + Vector((0, 0, 0.02)), FD_PICK, PN_PICK, pose="pinch")
reach(BOY, PR, "L", 22, brick_center(RED) + Vector((0, 0, 0.001)), FD_PICK, PN_PICK, pose="pinch")
reach(BOY, PR, "L", 23, brick_center(RED) + Vector((0, 0, 0.001)), FD_PICK, PN_PICK, pose="pinch")
grab(BOY, "L", 24, RED)
def ahead_of_face(f, fwd, down, side=0.0):
    M = head_M(BOY, f); e = (BOY.data.bones["eye.L"].head_local + BOY.data.bones["eye.R"].head_local) / 2
    return M @ (e + Vector((side, -fwd, -down)))
def ins(rig, N, f, tb, kind, k=1.0): return brick_world(rig, N, tb, kind, f, k)
def finger_dir(rig, s):
    return (Wt(rig, "finger2-3." + s) - Wh(rig, "finger2-1." + s)).normalized()
POLE_L = lambda: Vector((BX + 0.38, -0.28, 0.12))
def carry(obj, f, P, fdir, palm, Mfinal=None, pose="pinch", s="L"):
    """hand posed naturally (pinch point at P), then the brick keyed in the fingertips: centre at the pinch point,
    studs back toward the palm (z = -finger direction) -- or exactly Mfinal (in-nostril pose) when given"""
    reach(BOY, PR, s, f, P, fdir, palm, pose=pose, pole=POLE_L())
    fs(f)
    if Mfinal is None:
        cur = obj.matrix_world.copy(); zt = -finger_dir(BOY, s)
        M = swing_to(cur, zt, Vector((0, 0, 0))); M.translation = pinch_pt(BOY, s) - M.to_3x3() @ Vector((0, 0, 0.0048))
    else:
        M = Mfinal
    key_world_while_owned(obj, f, M)
PALM_UP = Vector((0, 0.85, -0.5))
def brick_c_world(M): return M @ Vector((0, 0, 0.0048))
carry(RED, 42, ahead_of_face(42, 0.30, 0.30, 0.10), Vector((0.1, -0.2, 1)), Vector((0, 0.9, 0.3)))
carry(RED, 62, ahead_of_face(62, 0.22, 0.10, 0.12), Vector((-0.2, 0.3, 1)), Vector((-0.3, 1, -0.2)))
carry(RED, 76, ahead_of_face(76, 0.18, 0.09, 0.07), Vector((-0.1, 0.4, 1)), Vector((-0.2, 1, -0.3)))
for f, tb in ((95, -0.016), (104, -0.002), (112, 0.006)):
    M_ = ins(BOY, N_B, f, tb, "red"); A_w = -(M_.to_3x3() @ Vector((0, 0, 1))).normalized()
    carry(RED, f, brick_c_world(M_), A_w, PALM_UP, Mfinal=M_)
owner_switch(RED, 113, BOY, "head", log)
# index finger pushes it in (the brick moves with the fingertip on its stud end)
RED_TB = [(113, 0.006), (124, 0.011), (134, 0.016)]
for f, tb in RED_TB: key_brick_head(RED, BOY, N_B, f, tb, "red")
def push_finger(f, obj, s="L", back=0.0015):
    fs(f); z = (obj.matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized()
    P = stud_end(obj) + z * back
    reach(BOY, PR, s, f, P, -z, PALM_UP, pose="point", pt=lambda r, s_: tip_of(r, s_, 2), pole=POLE_L())
for f, tb in RED_TB[1:]: push_finger(f, RED)
push_finger(118, RED)
# hand back down to the rug beside the pile (palm down, relaxed)
def rug_rest(f, dx=0.0, dy=0.0):
    k = knee_top(BOY, "L", trs, f)
    rest_hand(BOY, PR, "L", f, k + Vector((0.01 + dx, 0.05 + dy, 0)), Vector((0, 0, -1)), Vector((-0.1, -1, -0.3)), pose="relaxed")
reach(BOY, PR, "L", 145, ahead_of_face(145, 0.16, 0.14, 0.06), Vector((0.2, 0.2, 1)), Vector((0, 0.9, -0.3)), pose="relaxed",
      pt=lambda r, s_: Wh(r, "wrist." + s_))
rug_rest(172, 0.0, 0.0)

# --- yellow: the second brick, from the rug to the same nostril; it clicks onto the red one's studs
reach(BOY, PR, "L", 205, brick_center(YEL) + Vector((0.02, -0.02, 0.07)), FD_PICK, PN_PICK, pose="relaxed")
reach(BOY, PR, "L", 228, brick_center(YEL) + Vector((0, 0, 0.02)), FD_PICK, PN_PICK, pose="pinch")
reach(BOY, PR, "L", 238, brick_center(YEL) + Vector((0, 0, 0.001)), FD_PICK, PN_PICK, pose="pinch")
reach(BOY, PR, "L", 241, brick_center(YEL) + Vector((0, 0, 0.001)), FD_PICK, PN_PICK, pose="pinch")
grab(BOY, "L", 242, YEL)
def ycarry(f, P, fdir, palm, Mfinal=None):
    reach(BOY, PR, "L", f, P, fdir, palm, pose="pinch", pole=POLE_L()); fs(f)
    if Mfinal is None:
        cur = YEL.matrix_world.copy(); M = swing_to(cur, -finger_dir(BOY, "L"), Vector((0, 0, 0)))
        M.translation = pinch_pt(BOY, "L") - M.to_3x3() @ Vector((0, 0, 0.0048))
    else: M = Mfinal
    key_world_while_owned(YEL, f, M)
ycarry(262, ahead_of_face(262, 0.30, 0.28, 0.10), Vector((0.1, -0.2, 1)), Vector((0, 0.9, 0.3)))
ycarry(282, ahead_of_face(282, 0.18, 0.10, 0.02), Vector((0.0, 0.4, 1)), Vector((0, 1, -0.3)))
for f, tb in ((300, -0.014), (318, -0.004), (330, 0.0025)):
    M_ = ins(BOY, N_B, f, tb, "yel"); A_w = -(M_.to_3x3() @ Vector((0, 0, 1))).normalized()
    ycarry(f, brick_c_world(M_), A_w, PALM_UP, Mfinal=M_)
owner_switch(YEL, 331, BOY, "head", log)
key_brick_head(YEL, BOY, N_B, 331, 0.0025, "yel")
reach(BOY, PR, "L", 352, ahead_of_face(352, 0.14, 0.15, 0.07), Vector((0.2, 0.2, 1)), Vector((0, 0.9, -0.3)), pose="relaxed",
      pt=lambda r, s_: Wh(r, "wrist." + s_))
rug_rest(380, 0.03, 0.02); rug_rest(425, 0.04, 0.0)
# "thinking that because the piece is connected": he pushes it the last mm -> CLICK (studs into the yellow's bottom)
YEL_TB = [(331, 0.0025), (446, 0.0025), (456, 0.0064), (465, 0.0134)]
for f, tb in YEL_TB: key_brick_head(YEL, BOY, N_B, f, tb, "yel")
for f in (446, 456, 465, 470): push_finger(f, YEL)
key_brick_head(RED, BOY, N_B, 456, 0.016, "red"); key_brick_head(RED, BOY, N_B, 465, 0.023, "red")
reach(BOY, PR, "L", 490, ahead_of_face(490, 0.15, 0.16, 0.07), Vector((0.2, 0.2, 1)), Vector((0, 0.9, -0.3)), pose="relaxed",
      pt=lambda r, s_: Wh(r, "wrist." + s_))
# click flash: a small bright star at the joint
star_m = bpy.data.materials.new("M_Click"); star_m.use_nodes = True
pp = star_m.node_tree.nodes["Principled BSDF"]; pp.inputs["Emission Color"].default_value = (1.0, 0.95, 0.6, 1); pp.inputs["Emission Strength"].default_value = 12
bpy.ops.mesh.primitive_ico_sphere_add(radius=0.004, subdivisions=2); STAR = bpy.context.active_object; STAR.name = "ClickFlash"
STAR.data.materials.append(star_m)
for i in range(4):
    bpy.ops.mesh.primitive_cone_add(radius1=0.0012, depth=0.012, vertices=6, rotation=(0, math.radians(90), math.radians(45 * i)))
    sp = bpy.context.active_object; sp.data.materials.append(star_m)
    bpy.ops.object.select_all(action='DESELECT'); sp.select_set(True); STAR.select_set(True); bpy.context.view_layer.objects.active = STAR; bpy.ops.object.join()
fs(465); STAR.matrix_world = Matrix.Translation(YEL.matrix_world @ Vector((0, 0, 0)))
owner_switch(STAR, 2, BOY, "head", log)
fs(465); STAR.rotation_mode = 'QUATERNION'
for f, sc_ in ((1, 0.0), (462, 0.0), (467, 1.4), (474, 0.6), (480, 0.0)):
    STAR.scale = (sc_, sc_, sc_); STAR.keyframe_insert("scale", frame=f)

# --- "he could pull both of them out together": pinch the yellow end and tug -- nothing moves
fs(540); YEND = stud_end(YEL)
def pinch_yellow(f, pull=0.0):
    fs(f); z = (YEL.matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized()
    P = stud_end(YEL) - z * 0.003 + z * pull
    reach(BOY, PR, "L", f, P, -z, Vector((0, 0.9, -0.3)), pose="pinch", pole=POLE_L())
rug_rest(520, 0.0, 0.0); rug_rest(600, 0.01, 0.0)
rug_rest(668, 0.0, 0.0)
# "both pieces became stuck": a hard sniff sucks both deeper; he panics and calls Mom
for f, tbr, tby in ((690, 0.023, 0.0134), (706, 0.027, 0.0174), (716, 0.031, 0.0214)):
    key_brick_head(RED, BOY, N_B, f, tbr, "red"); key_brick_head(YEL, BOY, N_B, f, tby, "yel")
key_brick_head(RED, BOY, N_B, 134, 0.016, "red"); key_brick_head(RED, BOY, N_B, 689, 0.023, "red"); key_brick_head(YEL, BOY, N_B, 689, 0.0134, "yel")
rug_rest(760, 0.01, 0.0)
rest_hand(BOY, PR, "L", 800, knee_top(BOY, "L", trs, 800), Vector((0, 0, -1)), Vector((-0.1, -1, -0.3)), pose="relaxed")
for f in (800, 1300):
    rest_hand(BOY, PR, "R", f, rug_r(f), Vector((0, 0, -1)), Vector((-0.2, -1, 0)), pose="relaxed")
rest_hand(BOY, PR, "L", 1300, knee_top(BOY, "L", trs, 1300), Vector((0, 0, -1)), Vector((-0.1, -1, -0.3)), pose="relaxed")
key_brick_head(RED, BOY, N_B, 1000, 0.031, "red")
key_brick_head(RED, BOY, N_B, 1030, 0.040, "red")     # relieved sniff: the small one slips deeper, unseen
key_brick_head(RED, BOY, N_B, 1100, 0.040, "red")

# ================================================================== MOM: tweezers from the seat -> the yellow brick -> out
fs(790)
TW0 = TWZ.matrix_world.copy(); TWZ.rotation_mode = 'QUATERNION'; key_basis(TWZ, 1, TW0)
tw_len = max(v.co.y for v in TWZ.data.vertices); tw_tail = min(v.co.y for v in TWZ.data.vertices)
TW_TIP = Vector((0, tw_len, 0))
def tw_grip_pt(): return TWZ.matrix_world @ Vector((0, tw_tail * 0.15, 0))
d_tw = (TW0.to_3x3() @ Vector((0, 1, 0))).normalized()
reach(MOM, MR, "L", 776, tw_grip_pt() + Vector((0, 0, 0.08)), Vector((0.3, -0.3, -0.9)), Vector((0, 0, -1)), pose="relaxed")
reach(MOM, MR, "L", 792, tw_grip_pt() + Vector((0, 0, 0.004)), d_tw, Vector((0, 0, -1)), pose="pinch")
reach(MOM, MR, "L", 795, tw_grip_pt() + Vector((0, 0, 0.004)), d_tw, Vector((0, 0, -1)), pose="pinch")
grab(MOM, "L", 796, TWZ)
def tw_at(f, tip_world, axis_world):
    """tweezers world matrix: tip at tip_world, long axis (+Y) along axis_world, arms vertical-ish"""
    y = Vector(axis_world).normalized(); M = frame_from(y, Vector((0, 0, 1)) - y * 0.0, Vector((0, 0, 0)))
    M.translation = Vector(tip_world) - M.to_3x3() @ TW_TIP; return M
def yel_outer(f):
    fs(f); return stud_end(YEL), (YEL.matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized()
P_, z_ = yel_outer(820)
place_prop(MR, 815, TWZ, tw_at(815, P_ - z_ * -0.10 + Vector((0, 0, -0.03)), -z_ + Vector((0, 0, 0.2))), pose="pinch")
P_, z_ = yel_outer(840)
place_prop(MR, 840, TWZ, tw_at(840, P_ + z_ * 0.025, -z_), pose="pinch")
for f in (852, 858):
    P_, z_ = yel_outer(f); place_prop(MR, f, TWZ, tw_at(f, P_ + z_ * 0.001, -z_), pose="pinch")
owner_switch(YEL, 859, TWZ, None, log)
for f, out in ((868, 0.006), (880, 0.018), (892, 0.040)):
    fs(858); P_, z_ = yel_outer(858)
    M858 = tw_at(858, P_ + z_ * 0.001, -z_)
    Mh858 = head_M(BOY, 858); Mhf = head_M(BOY, f)
    Mt = Mhf @ Mh858.inverted() @ Matrix.Translation(z_ * out) @ M858
    place_prop(MR, f, TWZ, Mt, pose="pinch")
# she lifts it to show him (in front of her face, tip up)
def mom_face_pt(f, fwd, down, side):
    fs(f); M = head_M(MOM, f); e = (MOM.data.bones["eye.L"].head_local + MOM.data.bones["eye.R"].head_local) / 2
    return M @ (e + Vector((side, -fwd, -down)))
place_prop(MR, 925, TWZ, tw_at(925, mom_face_pt(925, 0.24, 0.08, 0.10), Vector((0.4, -0.3, 1.0))), pose="pinch", pole=Vector((MOM_X + 0.1, MY + 0.45, 0.6)))
place_prop(MR, 980, TWZ, tw_at(980, mom_face_pt(980, 0.25, 0.10, 0.11), Vector((0.4, -0.35, 1.0))), pose="pinch", pole=Vector((MOM_X + 0.1, MY + 0.45, 0.6)))
fs(1000)
kn = Wh(MOM, "lowerleg01.L"); kz = ray_down([O["Mom.trousers"]], kn.x - 0.04, kn.y)
place_prop(MR, 1040, TWZ, tw_at(1040, Vector((kn.x + 0.06, kn.y - 0.02, kz + 0.05)), Vector((0.8, 0.2, 0.5))), pose="pinch")
place_prop(MR, 1300, TWZ, tw_at(1300, Vector((kn.x + 0.06, kn.y - 0.02, kz + 0.05)), Vector((0.8, 0.2, 0.5))), pose="pinch")

XC_B = path_pt(N_B, 0.012) + Vector((0, 0.004, 0))
XBEATS = [(66, 78, 150, 164), (294, 308, 730, 742), (843, 855, 905, 917), (1038, 1050, None, None)]
key_x(XB, 1, 0.0); anat_vis(ANAT_B, 1, False)
for a0, a1, b0, b1 in XBEATS:
    key_x(XB, a0, 0.0); key_x(XB, a1, 1.0); anat_vis(ANAT_B, a1 - 4, True)
    if b0: key_x(XB, b0, 1.0); key_x(XB, b1, 0.0); anat_vis(ANAT_B, b0 + 4, False)

# ================================================================== MAN in bed: lying ON the mattress, head ON the pillow (R3)
MAT_Z = sc["mat_top"]
MAN_REST_ROOT = NR.BN["root"].head_local.copy()
TV = 1572           # teleport frame (inside the void: the man is fully vanished)
BEDF = 1180         # first frame the man is posed in bed (still vanished until the void lifts)
def man_bed_root(f, y=0.70, z=0.55, flex=-78.0, side=0.0):
    HN_.key_root(f, Vector((BED_X + 0.0, y, z)), yaw=0.0, flex=flex, side=side)
MBED = dict(y=0.70, z=0.55, flex=-78.0)
def bed_feet(f):
    for s in "LR":
        a = NR.BN["foot." + s].head_local
        tgt = Vector((BED_X + a.x * 1.1, MBED["y"] - 0.93, MAT_Z + 0.075))
        M = Matrix.Translation(tgt) @ Matrix.Rotation(math.radians(-80), 4, 'X') @ Matrix.Translation(-a) @ NR.rest("IK_foot." + s)
        NR.key_world("IK_foot." + s, f, M)
        key_pole(NR, s, f, (BED_X + a.x * 1.6, MBED["y"] - 0.5, MAT_Z + 0.9), kind="knee")
man_bed_root(BEDF, **MBED); bed_feet(BEDF)
fs(BEDF)
mbt = O["Man.trousers"]; mtop = O["Man.top"]
for _ in range(4):
    pts = [p[1] for p in eval_points(mbt) if abs(p[1].x - BED_X) < 0.16 and abs(p[1].y - MBED["y"]) < 0.14]
    low = min(p.z for p in pts); MBED["z"] += (MAT_Z + 0.004) - low
    man_bed_root(BEDF, **MBED); bed_feet(BEDF); fs(BEDF)
# the back of the head rests on the pillow: tilt the recline until the skull-back point meets the pillow surface
def head_back_gap():
    fs(BEDF); hb = Wh(MAN, "head") + (head_M(MAN, BEDF).to_3x3() @ Vector((0, 0.095, 0.03)))
    zp = ray_down([BED], hb.x, hb.y)
    return hb.z - (zp or 0), hb
for _ in range(6):
    g, hb = head_back_gap()
    if abs(g) < 0.004: break
    MBED["flex"] += max(-6, min(6, -math.degrees(math.atan2(g, 0.68))))
    man_bed_root(BEDF, **MBED); bed_feet(BEDF)
    for _ in range(2):
        pts = [p[1] for p in eval_points(mbt) if abs(p[1].x - BED_X) < 0.16 and abs(p[1].y - MBED["y"]) < 0.14]
        MBED["z"] += (MAT_Z + 0.004) - min(p.z for p in pts); man_bed_root(BEDF, **MBED); bed_feet(BEDF)
log("man in bed", {k: round(v, 3) for k, v in MBED.items()}, "head-pillow gap", round(head_back_gap()[0], 4))
for f in (BEDF, TV - 1):
    man_bed_root(f, **MBED); bed_feet(f)
# head/neck acting in bed (pitch +: chin to chest)
MANHEAD = [(BEDF, 0, 14), (1300, 0, 16), (1322, 2, 10), (1330, 0, 16), (1347, -2, 10), (1355, 0, 16), (1372, 2, 9), (1380, 0, 18),
           (1398, -4, 22), (1420, 0, 14), (1450, 0, 4), (1490, 0, 2), (1503, 0, 2), (1508, 0, 14), (1520, -14, 12), (1540, 10, 10), (TV - 1, 4, 8)]
for f, yw, pt in MANHEAD: key_head(NR, f, yw, pt)
for f, fl in ((BEDF, 6), (1300, 6), (1398, 10), (1450, 3), (1503, 3), (1508, 10), (TV - 1, 6)): key_spine(NR, f, flex=fl)
blinks(MAN, [1290, 1335, 1365, 1412, 1528, 1560])
eyes_closed(MAN, 1440, 1505, ramp=10)
saccades(NR, BEDF, TV, every=31, seed=4)
for f, kw in ((BEDF, dict(brow=-0.3)), (1310, dict(brow=-0.5, jaw=0.25, squint=0.3)), (1322, dict(brow=-0.6, jaw=0.1, squint=0.5)),
              (1340, dict(brow=-0.4, jaw=0.3)), (1372, dict(brow=-0.6, squint=0.5)), (1392, dict(jaw=0.25, brow=0.1)), (1405, dict(jaw=0.1)),
              (1430, dict(brow=0.0)), (1460, dict(jaw=0.45)), (1480, dict(jaw=0.5)), (1503, dict(jaw=0.5)), (1507, dict(jaw=0.65, brow=0.9)),
              (1520, dict(brow=-0.5, jaw=0.1)), (1545, dict(brow=-0.6, squint=0.3)), (TV - 1, dict(brow=-0.5))):
    key_face(MAN, f, **kw)
# hands: left on the belly; right holds the inhaler on the mattress, lifts it to the mouth for one puff
fs(BEDF)
def belly_pt(f, dx=0.0):
    fs(f); c = (Wh(MAN, "spine01") + Wh(MAN, "spine02")) / 2 + Vector((dx, 0, 0)); z = ray_down([mtop], c.x, c.y)
    return Vector((c.x, c.y, z))
def mat_side(f):
    fs(f); c = Wh(MAN, "spine01") + Vector((0.30, -0.12, 0)); return Vector((c.x, c.y, ray_down([BED], c.x, c.y)))
for f in (BEDF, 1300, 1450, TV - 1):
    rest_hand(MAN, NR, "L", f, mat_side(f), Vector((0, 0, -1)), Vector((0.1, -1, 0)), pose="relaxed")
def mattress_pt(f, dx, dy):
    fs(f); c = Wh(MAN, "spine01") + Vector((dx, dy, 0)); return Vector((c.x, c.y, ray_down([BED], c.x, c.y)))
# inhaler lies in his palm; the hand wraps it
P0 = belly_pt(BEDF, -0.07)
def rhand_rest(f, pose="wrap_grip"):
    apply_pose(MAN, "R", pose, f); place_hand(MAN, "R", f, belly_pt(f, -0.07), Vector((0, 0, -1)), Vector((0.3, 1, 0)), skin=0.045)
rhand_rest(BEDF)
fs(BEDF); palm_c = Wh(MAN, "wrist.R").lerp(Wh(MAN, "finger3-1.R"), 0.70)
Rr = Matrix.Rotation(math.radians(90), 4, 'Y') @ Matrix.Rotation(math.radians(90), 4, 'X')
cen = sum((v.co for v in INH.data.vertices), Vector()) / len(INH.data.vertices)
tgt = palm_c + Vector((0, 0, -0.022))
Mi = Matrix.Translation(tgt - Rr.to_3x3() @ cen) @ Rr
apply_pose(MAN, "R", "wrap_grip", BEDF)
fs(BEDF); Wr_ = W(MAN, "wrist.R")
ci = INH.constraints.new('CHILD_OF'); ci.name = "own_hand"; ci.target = MAN; ci.subtarget = "wrist.R"
ci.inverse_matrix = Wr_.inverted(); ci.influence = 1.0; ci.keyframe_insert("influence", frame=1)
INH.rotation_mode = 'QUATERNION'; key_basis(INH, 1, Mi)
fs(BEDF); log("inhaler in palm: dist", round((INH.matrix_world.translation - Mi.translation).length * 1000, 1), "mm")
PROP_OFF[INH.name] = (MAN, "R", Wr_.inverted() @ Mi)
def mouth_pt(f, fwd):
    M = head_M(MAN, f); jaw = MAN.data.bones["jaw"].head_local; tip = MAN_TIP
    lips = Vector((0, tip.y + 0.012, tip.z - 0.075))
    return M @ (lips + Vector((0, -fwd, 0)))
def inh_at(f, mouth_fwd):
    fs(f); M = head_M(MAN, f)
    fw = (M.to_3x3() @ Vector((0, -1, 0))).normalized(); up = (M.to_3x3() @ Vector((0, 0, 1))).normalized()
    mp = mouth_pt(f, mouth_fwd)
    # inhaler local: mouthpiece toward -Y (into the mouth), canister +Z up
    y = -fw; z = up; x = y.cross(z).normalized(); z = x.cross(y)
    R = Matrix((x, y, z)).transposed().to_4x4(); R.translation = mp - (R.to_3x3() @ Vector((0, -0.029, 0.010)))
    return R
place_prop(NR, 1300, INH, INH.matrix_world.copy()) if False else None
for f in (1300, 1360): rhand_rest(f)
place_prop(NR, 1382, INH, inh_at(1382, 0.07), pose="wrap_grip", pole=Vector((BED_X - 0.5, MBED["y"] - 0.2, MAT_Z + 0.1)))
place_prop(NR, 1394, INH, inh_at(1394, 0.004), pose="wrap_grip", pole=Vector((BED_X - 0.5, MBED["y"] - 0.2, MAT_Z + 0.1)))
place_prop(NR, 1406, INH, inh_at(1406, 0.004), pose="wrap_grip", pole=Vector((BED_X - 0.5, MBED["y"] - 0.2, MAT_Z + 0.1)))
place_prop(NR, 1420, INH, inh_at(1420, 0.08), pose="wrap_grip", pole=Vector((BED_X - 0.5, MBED["y"] - 0.2, MAT_Z + 0.1)))
for f in (1446, TV - 1): rhand_rest(f)
# puff: a small soft mist cloud at the mouthpiece
mist_m = bpy.data.materials.new("M_Mist"); mist_m.use_nodes = True; nt = mist_m.node_tree
tr = nt.nodes.new("ShaderNodeBsdfTransparent"); em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (0.92, 0.96, 1.0, 1); em.inputs["Strength"].default_value = 0.8
lw = nt.nodes.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.6
mxs = nt.nodes.new("ShaderNodeMixShader"); nt.links.new(lw.outputs["Facing"], mxs.inputs["Fac"])
nt.links.new(em.outputs["Emission"], mxs.inputs[1]); nt.links.new(tr.outputs["BSDF"], mxs.inputs[2])
nt.links.new(mxs.outputs["Shader"], nt.nodes["Material Output"].inputs["Surface"])
bpy.ops.mesh.primitive_ico_sphere_add(radius=0.012, subdivisions=3); MIST = bpy.context.active_object; MIST.name = "InhalerMist"; MIST.data.materials.append(mist_m)
fs(1398); MIST.matrix_world = Matrix.Translation(mouth_pt(1398, 0.0))
owner_switch(MIST, 2, MAN, "head", log)
for f, s_ in ((1, 0), (1397, 0), (1401, 1.0), (1410, 1.5), (1418, 0.0)): MIST.scale = (s_,) * 3; MIST.keyframe_insert("scale", frame=f)

# man x-ray window and anatomy timing (bed)
N_M = MAN_N; KM = K_MAN
XC_M = path_pt(N_M, 0.016 * KM, KM) + Vector((0, 0.005, 0))
# the red brick rides in the man's passage (same relative depth, real size: ONE model)
TB_DEEP = 0.040 * KM

# ================================================================== MAN in the shower (same model; moved at TV while vanished inside the void)
TUB_FLOOR = 0.06
SH_Y = 0.42
def man_shower_root(f, dz=0.0, flex=0.0, side=0.0):
    HN_.key_root(f, Vector((BATH_X - 0.02, SH_Y, MAN_REST_ROOT.z + TUB_FLOOR - 0.012 + dz)), yaw=0.0, flex=flex, side=side)
def shower_feet(f):
    for s in "LR":
        a = NR.BN["foot." + s].head_local
        tgt = Vector((BATH_X - 0.02 + a.x * 1.05, SH_Y + a.y - MAN_REST_ROOT.y, TUB_FLOOR + a.z))
        NR.key_world("IK_foot." + s, f, Matrix.Translation(tgt - a) @ NR.rest("IK_foot." + s))
        key_pole(NR, s, f, (BATH_X + a.x * 1.4, SH_Y - 0.8, 0.5), kind="knee")
for f in (TV, 1680, 1700, 1720, 2036):
    shower_feet(f)
SHROOT = [(TV, 0, 0), (1660, 0, 0), (1673, -0.003, 4), (1682, 0, 1), (1693, -0.004, 5), (1702, 0, 1), (1828, 0, 1), (1834, -0.004, 4),
          (1845, 0, 3), (1950, 0, 4), (1965, -0.006, 6), (1980, 0, 2), (1995, -0.006, 6), (2010, 0, 2), (2036, 0, 2)]
for f, dz, fl in SHROOT: man_shower_root(f, dz=dz, flex=fl)
MANHEAD2 = [(TV, 0, -6), (1620, 4, -8), (1650, 0, 2), (1673, 0, 8), (1682, 0, 3), (1693, 0, 9), (1702, 0, 4), (1740, -4, 3), (1800, 2, 4),
            (1833, 0, 9), (1845, 0, 12), (1900, 2, 14), (1950, -6, 10), (1975, -8, 0), (2000, 6, -6), (2036, 2, -2)]
for f, yw, pt in MANHEAD2: key_head(NR, f, yw, pt)
for f, fl in ((TV, 2), (1673, 8), (1682, 3), (1693, 9), (1702, 3), (1845, 6), (1950, 5), (1975, -4), (2000, 2), (2036, 0)): key_spine(NR, f, flex=fl)
blinks(MAN, [1612, 1650, 1740, 1790, 1880, 1930, 2020])
for s in "LR":   # eyes squeeze on each blow
    pass
for f, kw in ((TV, dict(brow=-0.3)), (1640, dict(brow=-0.2)), (1670, dict(squint=0.9, brow=-0.6, jaw=0.0)), (1680, dict(squint=0.3)),
              (1690, dict(squint=1.0, brow=-0.7)), (1702, dict(squint=0.2)), (1760, dict(brow=-0.2)), (1828, dict(squint=1.0, brow=-0.8)),
              (1836, dict(brow=1.0, jaw=0.55)), (1860, dict(brow=1.0, jaw=0.4)), (1930, dict(brow=0.8, jaw=0.2, smile=0.2)),
              (1960, dict(smile=1.0, jaw=0.6, squint=0.5, brow=0.4)), (1985, dict(smile=1.0, jaw=0.45, squint=0.6)), (2010, dict(smile=1.0, jaw=0.6, squint=0.5)),
              (2036, dict(smile=0.9, jaw=0.4))):
    key_face(MAN, f, **kw)
# hands: below the tiled wall until he cups them under his nose; the brick lands in the left palm
def chest_pt(f, dx, dz):
    fs(f); c = Wh(MAN, "spine03"); return c + Vector((dx, -0.20, dz))
for f in (TV, 1615):
    for s, sx in (("L", 1), ("R", -1)):
        rest_hand(MAN, NR, s, f, chest_pt(f, sx * 0.10, -0.36), Vector((0, 1, 0)), Vector((-sx * 0.3, 0, 1)), pose="relaxed")
CAP_Z = 1.575
def cap_pt(f, s):
    fs(f); sx = 1 if s == "L" else -1; c = Wh(MAN, "upperarm01." + s)
    return Vector((c.x + sx * 0.06, 0.07, CAP_Z))
for f in (1630,):     # left hand low behind the tiled wall until the nose blow
    rest_hand(MAN, NR, "L", f, chest_pt(f, 0.10, -0.36), Vector((0, 1, 0)), Vector((-0.3, 0, 1)), pose="relaxed")
for f in (1640, 2036):
    rest_hand(MAN, NR, "R", f, chest_pt(f, -0.10, -0.36), Vector((0, 1, 0)), Vector((0.3, 0, 1)), pose="relaxed")
def ala_L(f):
    """the pad of the left index rests on the outside of his LEFT nostril wing (the brick is in the right one)"""
    fs(f); M = head_M(MAN, f); tip = MAN_TIP
    return M @ Vector((0.021, tip.y + 0.018, MAN_N.z + 0.006))
for f in (1700,):
    rest_hand(MAN, NR, "L", f, chest_pt(f, 0.10, -0.36), Vector((0, 1, 0)), Vector((-0.3, 0, 1)), pose="relaxed")
for f in (1664, 1672, 1684, 1694, 1708):
    fs(f); P_ = ala_L(f); R3 = head_M(MAN, f).to_3x3()
    reach(MAN, NR, "L", f, P_, (R3 @ Vector((-0.15, 0.1, 1.0))).normalized(), (R3 @ Vector((-1, 0, 0))).normalized(), pose="point",
          pt=lambda r, s_: tip_of(r, s_, 2), pole=Vector((BATH_X + 0.45, SH_Y - 0.05, 1.0)))
for f in (1735, 1850, 2036):
    rest_hand(MAN, NR, "L", f, chest_pt(f, 0.10, -0.36), Vector((0, 1, 0)), Vector((-0.3, 0, 1)), pose="relaxed")
# ================================================================== the bed/shower switch at TV (keys at TV-1 and TV only change in the hidden void)
for f in (TV - 1,):
    for s in "LR":
        NR.PB["IK_hand." + s].keyframe_insert("location", frame=f); NR.PB["IK_hand." + s].keyframe_insert("rotation_quaternion", frame=f)
# inhaler: let go at TV (it stays on the mattress, the hand is far away in the shower)
fs(TV - 1); owner_switch(INH, TV, None, None, log)
fs(TV); INH.keyframe_insert("location", frame=TV)

# ================================================================== the red brick: boy -> (void, scaled growth) -> man -> shoots out
G_SWAP = 1225
fs(G_SWAP - 1)
# growth of the boy's anatomy in the void (about the nostril, head rest space), brick keeps its real size
def grow_M(g): return Matrix.Translation(N_B) @ Matrix.Scale(g, 4) @ Matrix.Translation(-N_B)
SKB_BASIS = SK_B.matrix_basis.copy()
for f in range(1196, G_SWAP):
    g = 1.0 + (K_MAN - 1.0) * smoothstep((f - 1196) / (G_SWAP - 1 - 1196))
    PASS_B.matrix_basis = grow_M(g); PASS_B.keyframe_insert("location", frame=f); PASS_B.keyframe_insert("scale", frame=f)
    SK_B.matrix_basis = grow_M(g) @ SKB_BASIS; SK_B.keyframe_insert("location", frame=f); SK_B.keyframe_insert("scale", frame=f)
    pos = N_B + (path_pt(N_B, 0.040) - N_B) * g
    Mb = brick_M_rest(N_B, 0.040, "red"); Mb.translation = pos
    key_world_while_owned(RED, f, head_M(BOY, f) @ Mb)
PASS_B.matrix_basis = Matrix.Identity(4); PASS_B.keyframe_insert("location", frame=1195); PASS_B.keyframe_insert("scale", frame=1195)
SK_B.matrix_basis = SKB_BASIS; SK_B.keyframe_insert("location", frame=1195); SK_B.keyframe_insert("scale", frame=1195)
# man's skull = the boy's skull grown by K about the nostril (so the swap is seamless)
SK_M.constraints.clear()
SKM_REST = Matrix.Translation(N_M) @ Matrix.Scale(K_MAN, 4) @ Matrix.Translation(-N_B) @ SKB_BASIS
c = SK_M.constraints.new('CHILD_OF'); c.target = MAN; c.subtarget = "head"
c.inverse_matrix = (MAN.matrix_world @ MAN.data.bones["head"].matrix_local).inverted()
SK_M.matrix_basis = SKM_REST
# brick ownership: boy head -> man head at the swap (world jump hidden by the camera riding the nostril frame)
owner_switch(RED, G_SWAP, MAN, "head", log)
for f in (G_SWAP, 1800):
    key_brick_head(RED, MAN, N_M, f, TB_DEEP, "red", KM)
# shower: the blow (1806-1832) drives it down the passage and out; flight 1833-1845 into the left palm
for f, tb in ((1806, TB_DEEP), (1816, 0.020 * KM), (1826, 0.004 * KM), (1832, -0.008 * KM)):
    key_brick_head(RED, MAN, N_M, f, tb, "red", KM)
fs(1832); OUT0 = RED.matrix_world.copy()
owner_switch(RED, 1833, None, None, log)
fs(1846)
land_c = Vector((BATH_X - 0.02 + 0.01, 0.055, CAP_Z))
z_up = Vector((0, 0, 1))
M_land = swing_to(OUT0, z_up, land_c)
p0 = OUT0.translation.copy()
for f in range(1833, 1847):
    u = (f - 1832) / 14.0
    p = p0.lerp(M_land.translation, u) + Vector((0, -0.02, 0.06)) * math.sin(math.pi * u)
    q = OUT0.to_quaternion().slerp(M_land.to_quaternion(), u) @ Quaternion((1, 0, 0), 2 * math.pi * u)
    M = q.to_matrix().to_4x4(); M.translation = p; key_basis(RED, f, M)
key_basis(RED, 1846, M_land); key_basis(RED, 1849, Matrix.Translation((0, 0, 0.004)) @ M_land); key_basis(RED, 1852, M_land)


# ================================================================== x-ray, vanish, anatomy visibility timeline
# boy: window opens for the first insertion and stays on through Mom's removal; then the dive
for f, r in ((1, 0.034), (1100, 0.034), (1150, 0.06), (1178, 0.16), (1200, 0.30)): key_mask(XB, f, XC_B, r)
key_van(XB, 1176, 0.0); key_van(XB, 1184, 1.0)
anat_vis(ANAT_B, G_SWAP, False); anat_vis([RED], 1, True)
# man: ghost appears after the swap, window closes as the camera pulls back in the bedroom
for f, r in ((1, 0.30), (1232, 0.30), (1250, 0.16), (1266, 0.05), (1330, 0.04)): key_mask(XN, f, XC_M, r)
for f, v in ((1, 1.0), (1248, 1.0), (1255, 0.0)): key_van(XN, f, v)
for f, v in ((1, 1.0), (1312, 1.0), (1336, 0.0), (1522, 0.0), (1540, 1.0), (1650, 1.0), (1668, 0.0), (1722, 0.0), (1742, 1.0), (1900, 1.0), (1925, 0.0)): key_x(XN, f, v)
for f, r in ((1520, 0.04), (1545, 0.06), (1560, 0.16), (1584, 0.16), (1598, 0.045), (1720, 0.045), (1900, 0.045)): key_mask(XN, f, XC_M, r)
for f, v in ((1556, 0.0), (1564, 1.0), (1588, 1.0), (1595, 0.0)): key_van(XN, f, v)
anat_vis(ANAT_M, 1, False); anat_vis(ANAT_M, G_SWAP, True); anat_vis(ANAT_M, 1338, False); anat_vis(ANAT_M, 1520, True); anat_vis(ANAT_M, 1670, False)
anat_vis(ANAT_M, 1720, True); anat_vis(ANAT_M, 1928, False)
key_van(XM, 1, 0.0)

exec(open(HERE + "/02c_camera.py").read())
