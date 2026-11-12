# helpers copied from 02
def link(o, c="Set"):
    C(c).objects.link(o); return o
def pbr(name, col, rough=0.6, metal=0.0, emit=None, estr=0.0, alpha=1.0, trans=0.0, ior=1.45):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal; b.inputs["IOR"].default_value = ior
    if trans: b.inputs["Transmission Weight"].default_value = trans
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1); b.inputs["Emission Strength"].default_value = estr
    if alpha < 1: b.inputs["Alpha"].default_value = alpha
    return m

def cyl(name, loc, r, h, mat, c="Set", verts=16, r2=None, rot=None):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=verts, radius1=r, radius2=r if r2 is None else r2, depth=h)
    bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new(name, me); o.location = loc
    if rot: o.rotation_euler = rot
    me.materials.append(mat); link(o, c); return o
def sphere(name, loc, r, mat, c="Set", scale=(1, 1, 1)):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=r); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new(name, me); o.location = loc; o.scale = scale
    me.materials.append(mat); link(o, c); return o
def inst(src, name, loc, rotz=0.0, scale=1.0, c="Set"):
    o = src.copy(); o.name = name; o.location = loc; o.rotation_euler = (0, 0, rotz)
    o.scale = (scale, scale, scale) if isinstance(scale, (int, float)) else scale
    link(o, c); return o
# Part 2 of 03_animate.py: props attached to hands, laptop UI + bill bar, lever + sparks, fans, clock, traffic,
# grid pulses, dusk + power cut lighting, and the one continuous camera.

def ev(f):
    sc.frame_set(int(f))
def bone_world(rig, bone, f):
    ev(f); return rig.matrix_world @ rig.pose.bones[bone].matrix
def frame_from(loc, fwd, up):
    fwd = fwd.normalized(); up = (up - fwd * up.dot(fwd)).normalized(); x = fwd.cross(up)
    # object convention: -Y = front, +Z = up
    return Matrix.Translation(loc) @ Matrix((x, -fwd, up)).transposed().to_4x4()
def attach_seq(o, seq):
    """seq: list of (frame, parent_obj, bone or None, W_desired at that frame). one CHILD_OF per entry, influences switched"""
    o.matrix_world = Matrix.Identity(4); o.location = (0, 0, 0); o.rotation_euler = (0, 0, 0); o.scale = (1, 1, 1)
    cons = []
    for i, ent in enumerate(seq):
        f, par, bone, Wd = ent[:4]; fe = ent[4] if len(ent) > 4 else f
        c = o.constraints.new("CHILD_OF"); c.name = "cof%d" % i; c.target = par
        if bone: c.subtarget = bone
        ev(fe)
        P = par.matrix_world @ (par.pose.bones[bone].matrix if bone else Matrix.Identity(4))
        if not bone: P = par.matrix_world.copy()
        c.inverse_matrix = P.inverted() @ Wd
        c.set_inverse_pending = False
        cons.append((f, c))
    for i, (f, c) in enumerate(cons):
        nxt = cons[i + 1][0] if i + 1 < len(cons) else 10 ** 6
        c.influence = 0.0; c.keyframe_insert("influence", frame=1)
        c.influence = 1.0; c.keyframe_insert("influence", frame=max(1, f))
        if nxt < 10 ** 6:
            c.influence = 0.0; c.keyframe_insert("influence", frame=nxt)
    for fc in fcurves(o):
        for k in fc.keyframe_points: k.interpolation = "CONSTANT"
def head_frame(rig, f, up_off=0.085, fwd_off=0.012, sink=0.124):
    Mh = bone_world(rig, "head", f); hp = Mh.translation; up = (Mh.to_3x3() @ Vector((0, 1, 0))).normalized()
    zc = (Mh.to_3x3() @ Vector((0, 0, 1))).normalized()
    pos, yaw = RIG[rig.name].frame_of(f); front = Matrix.Rotation(R_(yaw), 3, "Z") @ Vector((0, -1, 0))
    fwd = zc if zc.dot(front) > 0 else -zc
    # seat the shell on the actual top of the head (evaluated body/hair mesh), not on a guessed bone offset
    dg = bpy.context.evaluated_depsgraph_get(); top = None
    for o in meshes(rig):
        if not any(k in o.name for k in (".short", ".braid")): continue
        me = o.evaluated_get(dg).to_mesh()
        for v in me.vertices:
            w = o.matrix_world @ v.co
            if (w - hp).length < 0.45:
                d = (w - hp).dot(up)
                if top is None or d > top: top = d
        o.evaluated_get(dg).to_mesh_clear()
    print("HEADTOP", rig.name, f, round(top, 3))
    return frame_from(hp + up * (top - sink) + fwd * (fwd_off - 0.01), fwd, up)
def hand_frame(rig, s, f, off=(0, 0, 0), fwd_axis="fingers"):
    Mw = bone_world(rig, "wrist." + s, f); R3 = Mw.to_3x3()
    return Mw @ Matrix.Translation(Vector(off))

# hard hats
hatR = ob("HardHat_Road"); hatW = ob("HardHat_Work")
ev(296); Mb = bike.matrix_world.copy()
seat_pose = Mb @ Matrix.Translation(Vector(HAT_SEAT) + Vector((0, 0, 0.005)))
attach_seq(hatR, [(1, bike, None, seat_pose, 296), (302, CH["Man"], "wrist.L", seat_pose),
                  (318, CH["Man"], "head", head_frame(CH["Man"], 318))])
desk_o = ob("Office_Desk")
hat_desk = Matrix.Translation(Vector((DESK.x - 0.82, DESK.y + 0.22, 0.795))) @ Matrix.Rotation(R_(35), 4, "Z")
attach_seq(hatW, [(1, CH["ManW"], "head", head_frame(CH["ManW"], 320), 320), (508, desk_o, None, hat_desk, 508),
                  (1380, CH["ManW"], "head", head_frame(CH["ManW"], 1390), 1390)])
for nm, cp in CAPS.items():
    fe_ = 1 if nm == "OfficerA" else 1200
    attach_seq(cp, [(1, CH[nm], "head", head_frame(CH[nm], fe_, 0.07, 0.0, sink=0.005), fe_)])
# ticket pad (officer's left hand), slip (officer right -> man right), phone torch, fanning paper
pad = ob("TicketPad"); slip = ob("TicketSlip")
def palm_pose(rig, s, f, along=0.08, out=0.025, flip=False):
    Mw = bone_world(rig, "wrist." + s, f); ch = RIG[rig.name]
    d = (Mw.to_3x3() @ Vector((0, 1, 0))).normalized()
    ev(f); f3 = (rig.matrix_world @ rig.pose.bones["finger3-1." + s].head - Mw.translation).normalized()
    i2 = rig.matrix_world @ rig.pose.bones["finger2-1." + s].head; p5 = rig.matrix_world @ rig.pose.bones["finger5-1." + s].head
    a = (i2 - p5).normalized(); n = f3.cross(a) if s == "L" else a.cross(f3)
    n = -n if flip else n
    loc = Mw.translation + f3 * along + n * out
    return loc, f3, n
loc, f3, n = palm_pose(CH["OfficerA"], "L", 250, 0.07, -0.03)
attach_seq(pad, [(1, CH["OfficerA"], "wrist.L", frame_from(loc, f3, -n), 250)])
loc, f3, n = palm_pose(CH["OfficerA"], "R", 268, 0.09, -0.02)
loc2, f32, n2 = palm_pose(CH["Man"], "R", TICKET_F, 0.09, -0.02)
attach_seq(slip, [(1, CH["OfficerA"], "wrist.R", frame_from(loc, f3, -n), 268), (TICKET_F, CH["Man"], "wrist.R", frame_from(loc2, f32, -n2))])
key_vis(slip, [(262, 345)])
phone = ob("St_Phone")
loc, f3, n = palm_pose(CH["OfficerC"], "R", 1200, 0.075, -0.045)
attach_seq(phone, [(1, CH["OfficerC"], "wrist.R", frame_from(loc, -n, f3), 1200)])
torch = bpy.data.lights.new("PhoneTorch", "SPOT"); torch.energy = 160; torch.spot_size = R_(70); torch.spot_blend = 0.6; torch.shadow_soft_size = 0.01
torch.color = (1.0, 0.97, 0.92)
to = bpy.data.objects.new("PhoneTorch", torch); C("Station").objects.link(to)
to.parent = phone; to.location = (0, 0.02, 0.13); to.rotation_euler = (R_(-90), 0, 0)
key_vis(phone, [(1150, 1560)])
BEAM = bpy.data.materials.new("TorchBeam"); BEAM.use_nodes = True; bn = BEAM.node_tree.nodes; bl = BEAM.node_tree.links
for x in list(bn): bn.remove(x)
bo_ = bn.new("ShaderNodeOutputMaterial"); em_ = bn.new("ShaderNodeEmission"); em_.inputs["Color"].default_value = (1.0, 0.97, 0.9, 1); em_.inputs["Strength"].default_value = 0.025
tr_ = bn.new("ShaderNodeBsdfTransparent"); ad_ = bn.new("ShaderNodeAddShader")
bl.new(em_.outputs[0], ad_.inputs[0]); bl.new(tr_.outputs[0], ad_.inputs[1]); bl.new(ad_.outputs[0], bo_.inputs[0])
beam = cyl("PhoneBeam", (0, 0, 0), 0.55, 1.6, BEAM, c="Station", verts=16, r2=0.01)
beam.parent = to; beam.location = (0, 0, -0.8); beam.rotation_euler = (0, 0, 0)
key_vis(beam, [])   # beam read as an opaque disc at review res; the spot light alone carries the torch
fp = ob("FanPaper_0")
loc, f3, n = palm_pose(CH["OfficerB"], "R", 1200, 0.07, -0.02)
attach_seq(fp, [(1, CH["OfficerB"], "wrist.R", frame_from(loc + f3 * 0.1, f3, -n), 1200)])
for nm, p_ in (("A", A_SEAT), ("B", OB_SEAT)):
    inst(bpy.data.objects["SRC_plastic_monobloc_chair_01"], "St_Chair_" + nm, (p_.x - 0.12, p_.y, 0.0), rotz=R_(90), c="Station")
inst(bpy.data.objects["SRC_plastic_monobloc_chair_01"], "St_Chair_C", (-16.4, 57.0, 0.0), rotz=R_(-90), c="Station")
for i_, (x_, y_) in enumerate(((-6.2, 22.5), (-4.6, 15.6))):
    pass

# ------------------------------------------------------------------ laptop UI on the screen
lapo = ob("Office_Laptop")
smi = [i for i, m in enumerate(lapo.data.materials) if m and "screen" in m.name]
polys = [p for p in lapo.data.polygons if p.material_index in smi]
pts = [lapo.matrix_world @ lapo.data.vertices[v].co for p in polys for v in p.vertices]
nrm = sum((lapo.matrix_world.to_3x3() @ p.normal for p in polys), Vector()).normalized()
if nrm.y > 0: nrm = -nrm                         # faces the man (-Y)
SC_C = sum(pts, Vector()) / len(pts)
right = Vector((1, 0, 0)); up = nrm.cross(right).normalized()
if up.z < 0: up = -up
right = up.cross(nrm).normalized()
ws = max((p - SC_C).dot(right) for p in pts) * 2; hs = max((p - SC_C).dot(up) for p in pts) * 2
print("SCREEN", tuple(round(x, 3) for x in SC_C), "n", tuple(round(x, 2) for x in nrm), "w", round(ws, 3), "h", round(hs, 3))
SCR = Matrix((right, up, nrm)).transposed()
def scr(u, v, d=0.002):
    return SC_C + right * (u * ws / 2) + up * (v * hs / 2) + nrm * d
UIM = bpy.data.materials.new("ScreenBG"); UIM.use_nodes = True
bb = UIM.node_tree.nodes["Principled BSDF"]; bb.inputs["Base Color"].default_value = (0.01, 0.02, 0.04, 1)
bb.inputs["Emission Color"].default_value = (0.05, 0.12, 0.25, 1); bb.inputs["Emission Strength"].default_value = 1.5; bb.inputs["Roughness"].default_value = 0.2
lapo.data = lapo.data.copy()
for i in smi: lapo.data.materials[i] = UIM
def emit(name, col, strength=3.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Emission Color"].default_value = (*col, 1); b.inputs["Emission Strength"].default_value = strength
    return m
def ui_plane(name, u, v, w, h, mat, d=0.002, par=None):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    for p in ((0, -h / 2), (w, -h / 2), (w, h / 2), (0, h / 2)): bm.verts.new((p[0], p[1], 0))
    bm.faces.new(bm.verts); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); me.materials.append(mat); C("Office").objects.link(o)
    o.matrix_world = Matrix.Translation(scr(u, v, d)) @ SCR.to_4x4()
    return o
ROW_COL = [(0.2, 0.7, 0.9), (0.3, 0.8, 0.4), (0.2, 0.7, 0.9), (0.3, 0.8, 0.4), (0.2, 0.7, 0.9), (0.3, 0.8, 0.4)]
BAR_LEN = [0.35, 0.5, 0.3, 0.42, 0.25, 0.46]
ICON_M = emit("UI_Icon", (0.85, 0.9, 1.0), 2.5)
POLICE_ROW = 2
RED = emit("UI_Red", (1.0, 0.08, 0.05), 0.0)
bars = []
for r in range(6):
    v = 0.72 - r * 0.28
    hdr = ui_plane("UI_RowBG_%d" % r, -0.95, v, 1.9 * ws / 2, hs * 0.11, emit("UI_RowBG", (0.04, 0.08, 0.15), 1.0), d=0.001)
    # building icon: block + roof triangle (no text anywhere)
    ic = ui_plane("UI_Icon_%d" % r, -0.88, v - 0.02, ws * 0.035, hs * 0.07, ICON_M, d=0.002)
    me = bpy.data.meshes.new("roof%d" % r); bm = bmesh.new()
    a_, b_, c_ = bm.verts.new((-0.004, 0, 0)), bm.verts.new((ws * 0.035 + 0.004, 0, 0)), bm.verts.new((ws * 0.0175, hs * 0.045, 0))
    bm.faces.new((a_, b_, c_)); bm.to_mesh(me); bm.free()
    ro = bpy.data.objects.new("UI_Roof_%d" % r, me); me.materials.append(ICON_M); C("Office").objects.link(ro)
    ro.matrix_world = Matrix.Translation(scr(-0.88, v - 0.02 + 0.035 * 2 / 1.0 * 0.5 * 1.0, 0.002) + up * 0.0) @ SCR.to_4x4()
    m = emit("UI_Bar_%d" % r, ROW_COL[r], 2.5)
    bar = ui_plane("UI_Bar_%d" % r, -0.7, v, ws * BAR_LEN[r], hs * 0.06, m, d=0.003)
    bars.append(bar)
# police row: icon swaps to a badge, row + bar turn red (f640), three calendar pages flip (f700-860)
pr_v = 0.72 - POLICE_ROW * 0.28
bm_ = bars[POLICE_ROW].data.materials[0]; bsd = bm_.node_tree.nodes["Principled BSDF"]
for f, col, st in ((1, ROW_COL[POLICE_ROW], 2.5), (636, ROW_COL[POLICE_ROW], 2.5), (646, (1.0, 0.06, 0.04), 9.0), (1560, (1.0, 0.06, 0.04), 9.0)):
    bsd.inputs["Emission Color"].default_value = (*col, 1); bsd.inputs["Emission Color"].keyframe_insert("default_value", frame=f)
    bsd.inputs["Base Color"].default_value = (*col, 1); bsd.inputs["Base Color"].keyframe_insert("default_value", frame=f)
    bsd.inputs["Emission Strength"].default_value = st; bsd.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)
glow = ui_plane("UI_RedRow", -0.95, pr_v, 1.9 * ws / 2, hs * 0.13, emit("UI_RedRowM", (1.0, 0.1, 0.05), 4.0), d=0.0015)
key_vis(glow, [(642, 1560)])
for nm in ("UI_Icon_%d" % POLICE_ROW, "UI_Roof_%d" % POLICE_ROW): key_vis(ob(nm), [(1, 641)])
me = bpy.data.meshes.new("uibadge"); bm = bmesh.new()
vs = [bm.verts.new(((hs * 0.06 if k % 2 == 0 else hs * 0.025) * math.sin(math.pi * k / 5), (hs * 0.06 if k % 2 == 0 else hs * 0.025) * math.cos(math.pi * k / 5), 0)) for k in range(10)]
bm.faces.new(vs); bm.to_mesh(me); bm.free()
badge = bpy.data.objects.new("UI_Badge", me); me.materials.append(emit("UI_Gold", (1.0, 0.75, 0.2), 6.0)); C("Office").objects.link(badge)
badge.matrix_world = Matrix.Translation(scr(-0.86, pr_v, 0.004)) @ SCR.to_4x4(); key_vis(badge, [(642, 1560)])
CAL_M = emit("UI_Cal", (0.95, 0.95, 0.9), 3.0); CAL_TOP = emit("UI_CalTop", (1.0, 0.15, 0.1), 5.0)
for k in range(3):
    piv = bpy.data.objects.new("UI_CalPivot_%d" % k, None); C("Office").objects.link(piv)
    piv.matrix_world = Matrix.Translation(scr(0.55 + 0.0 * k, pr_v + 0.22, 0.004 + 0.0008 * (3 - k))) @ SCR.to_4x4()
    pg = bpy.data.objects.new("UI_CalPage_%d" % k, bpy.data.meshes.new("calpg%d" % k)); C("Office").objects.link(pg)
    bm = bmesh.new()
    for p in ((-0.018, 0, 0), (0.018, 0, 0), (0.018, -0.04, 0), (-0.018, -0.04, 0)): bm.verts.new(p)
    bm.faces.new(bm.verts); bm.to_mesh(pg.data); bm.free(); pg.data.materials.append(CAL_M)
    pg.parent = piv
    tb = bpy.data.objects.new("UI_CalTop_%d" % k, bpy.data.meshes.new("caltop%d" % k)); C("Office").objects.link(tb)
    bm = bmesh.new()
    for p in ((-0.018, 0.0, 0.0002), (0.018, 0.0, 0.0002), (0.018, -0.01, 0.0002), (-0.018, -0.01, 0.0002)): bm.verts.new(p)
    bm.faces.new(bm.verts); bm.to_mesh(tb.data); bm.free(); tb.data.materials.append(CAL_TOP); tb.parent = pg
    piv.rotation_mode = "XYZ"; base = piv.rotation_euler.copy()
    f0 = 705 + k * 50
    for f, a in ((1, 0.0), (f0, 0.0), (f0 + 22, R_(-170))):
        e = (piv.matrix_world.to_3x3()).to_euler()
        piv.matrix_world = Matrix.Translation(piv.matrix_world.translation) @ (SCR @ Matrix.Rotation(a, 3, "X")).to_4x4()
        piv.keyframe_insert("rotation_euler", frame=f)
    for o in (pg, tb): key_vis(o, [(642, f0 + 22)])
# the bill bar grows huge: out of the bezel, across the room toward the switchgear (f895 -> 1000)
big = bars[POLICE_ROW]
grow_m = emit("UI_BillBar", (1.0, 0.05, 0.03), 16.0)
bb_ = bpy.data.objects.new("BillBar", bpy.data.meshes.new("billbar")); C("Office").objects.link(bb_)
bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
for v in bm.verts: v.co = Vector(((v.co.x + 0.5) * 1.0, v.co.y * hs * 0.11, v.co.z * 0.016))
bm.to_mesh(bb_.data); bm.free(); bb_.data.materials.append(grow_m)
x0 = scr(-0.7, pr_v, 0.008)
bb_.matrix_world = Matrix.Translation(x0) @ SCR.to_4x4()
BAR_END = 24.35 - x0.x
for f, L_ in ((1, ws * BAR_LEN[POLICE_ROW]), (895, ws * BAR_LEN[POLICE_ROW]), (915, ws * 1.6), (940, 0.9), (975, 2.2), (1000, BAR_END), (1062, BAR_END)):
    bb_.scale = (L_, 1, 1); bb_.keyframe_insert("scale", frame=f)
for f, z in ((1, 1.0), (930, 1.0), (960, 3.0), (1000, 5.0)):
    bb_.scale[2] = z; bb_.keyframe_insert("scale", index=2, frame=f)
key_vis(bb_, [(895, 1068)])
key_vis(big, [(1, 894)])
tipL = bpy.data.lights.new("BarGlow", "POINT"); tipL.energy = 0; tipL.color = (1, 0.1, 0.05); tipL.shadow_soft_size = 0.05
tl = bpy.data.objects.new("BarGlow", tipL); C("Office").objects.link(tl)
for f, e in ((1, 0), (640, 0), (660, 6), (895, 6), (940, 40), (1000, 60), (1062, 60), (1068, 0)):
    tipL.energy = e; tipL.keyframe_insert("energy", frame=f)
for f in (1, 895, 940, 975, 1000, 1062):
    L_ = {1: 0.05, 895: 0.05, 940: 0.9, 975: 2.2, 1000: BAR_END, 1062: BAR_END}[f]
    tl.location = x0 + right * L_ * 0.8 + nrm * 0.12; tl.keyframe_insert("location", frame=f)

# ------------------------------------------------------------------ lever, cabinet lights, sparks
plate = bpy.data.objects.new("LeverPlate", bpy.data.meshes.new("lplate")); C("Office").objects.link(plate)
bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
for v in bm.verts: v.co = Vector((v.co.x * 0.08, v.co.y * 0.16, v.co.z * 0.36))
bm.to_mesh(plate.data); bm.free(); plate.data.materials.append(bpy.data.materials["Steel"])
plate.location = LEVER_PIVOT + Vector((0.07, 0, -0.02))
piv = bpy.data.objects.new("LeverPivot", None); C("Office").objects.link(piv); piv.location = LEVER_PIVOT
rod = cyl("LeverRod", (0, 0, LEVER_LEN / 2), 0.014, LEVER_LEN, bpy.data.materials["Steel"], c="Office", verts=10); rod.parent = piv
grip = cyl("LeverGrip", (0, 0, LEVER_LEN - 0.02), 0.024, 0.13, pbr("LeverRed", (0.7, 0.03, 0.02), 0.35), c="Office", verts=12); grip.parent = piv
hub = cyl("LeverHub", (0, 0, 0), 0.04, 0.06, bpy.data.materials["Steel"], c="Office", verts=12, rot=(R_(90), 0, 0)); hub.parent = piv
for f in range(1000, 1100, 1):
    ang = lever_ang(lever_a(f)); beta = math.atan2(-math.cos(ang), math.sin(ang))
    piv.rotation_euler = (0, beta, 0); piv.keyframe_insert("rotation_euler", frame=f)
CAB_LIGHTS = []
for k in range(4):
    m = pbr("CabLamp_%d" % k, (0.1, 1.0, 0.2) if k % 2 == 0 else (1.0, 0.6, 0.1), 0.2, emit=(0.1, 1.0, 0.2) if k % 2 == 0 else (1.0, 0.6, 0.1), estr=10)
    o = sphere("CabLamp_%d" % k, (25.44, CABINET.y + 0.25 + k * 0.06, 1.62), 0.012, m, c="Office")
    e = m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
    for f, v_ in ((1, 10), (1066, 10), (1068, 0)): e.default_value = v_; e.keyframe_insert("default_value", frame=f)
SPARK_M = emit("Spark", (1.0, 0.75, 0.3), 40.0)
random.seed(3)
SP0 = LEVER_PIVOT + Vector((0.02, 0, 0.02))
for i in range(46):
    s_ = cyl("Spark_%d" % i, (0, 0, 0), 0.0035, 0.045, SPARK_M, c="Office", verts=5)
    v0 = Vector((random.uniform(-2.8, -0.4), random.uniform(-1.4, 1.4), random.uniform(-0.5, 2.6)))
    fs = 1064 + random.randint(0, 6); life = random.randint(18, 42)
    for f in range(fs, fs + life + 1, 2):
        t = (f - fs) / 60.0; p = SP0 + v0 * t + Vector((0, 0, -4.9 * t * t))
        if p.z < 0.01: p.z = 0.01
        vel = v0 + Vector((0, 0, -9.8 * t))
        s_.location = p; s_.rotation_euler = Vector((0, 0, 1)).rotation_difference(vel.normalized()).to_euler()
        sc_ = 1.0 - (f - fs) / life
        s_.scale = (1, 1, 0.6 + vel.length * 0.5 * sc_)
        s_.keyframe_insert("location", frame=f); s_.keyframe_insert("rotation_euler", frame=f); s_.keyframe_insert("scale", frame=f)
    key_vis(s_, [(fs, fs + life)])
flashL = bpy.data.lights.new("ArcFlash", "POINT"); flashL.color = (1.0, 0.8, 0.5); flashL.shadow_soft_size = 0.05
fo = bpy.data.objects.new("ArcFlash", flashL); fo.location = SP0 + Vector((-0.1, 0, 0)); C("Office").objects.link(fo)
for f, e in ((1, 0), (1063, 0), (1065, 900), (1068, 250), (1072, 600), (1080, 60), (1095, 0)):
    flashL.energy = e; flashL.keyframe_insert("energy", frame=f)
arc = sphere("ArcBall", SP0, 0.05, emit("Arc", (0.8, 0.9, 1.0), 60.0), c="Office"); key_vis(arc, [(1065, 1070)])
# office lights die with the power cut? (no: he cuts the station, his office stays lit)

# gate swings open on its hinge as he pushes it (f414 -> 440)
gate_o = ob("Gate"); gl = gate_o.location.copy()
hinge = bpy.data.objects.new("GateHinge", None); C("Substation").objects.link(hinge); hinge.location = gl + Vector((0, 0.475, 0))
gate_o.parent = hinge; gate_o.location = gl - hinge.location
for f, a in ((1, 0.0), (414, 0.0), (424, R_(25)), (442, R_(100)), (450, R_(96))):
    hinge.rotation_euler = (0, 0, a); hinge.keyframe_insert("rotation_euler", frame=f)
# records load: bars grow in one after another while he scrolls (f520 -> 615)
for r, bar in enumerate(bars):
    sx_ = bar.scale.copy()
    for f, k in ((1, 0.02), (520 + r * 12, 0.02), (538 + r * 12, 1.0)):
        bar.scale = (sx_.x * k, sx_.y, sx_.z); bar.keyframe_insert("scale", frame=f)
# ------------------------------------------------------------------ fans, clock, indicators, flags
def spin(o, f0, f1, rpm, axis=2, decel_from=None, decel_to=None):
    o.rotation_mode = "XYZ"; a = 0.0; w = rpm / 60.0 * 2 * math.pi / 60.0
    for f in range(f0, f1 + 1, 2):
        k = 1.0
        if decel_from and f > decel_from: k = max(0.0, 1 - (f - decel_from) / (decel_to - decel_from))
        a += w * 2 * k
        e = list(o.rotation_euler); e[axis] = a; o.rotation_euler = e; o.keyframe_insert("rotation_euler", index=axis, frame=f)
spin(ob("OfficeFan_ceiling_fan_blades"), 1, 1560, 180)
spin(ob("StationFan_ceiling_fan_blades"), 1, 1560, 180, decel_from=1200, decel_to=1290)
for nm_ in ("StationFan_ceiling_fan_blades", "StationFan_ceiling_fan"): ob(nm_).location.z = 3.4 - 0.92
ob("StationFan_ceiling_fan").location = ob("StationFan_ceiling_fan_blades").location
fp2 = ob("FanPaper_1"); loc, f3, n = palm_pose(CH["OfficerE"], "R", 1200, 0.07, -0.02)
attach_seq(fp2, [(1, CH["OfficerE"], "wrist.R", frame_from(loc + f3 * 0.1, f3, -n), 1200)])
fp3 = inst(bpy.data.objects["SRC_a4"], "TapFile", (0, 0, 0), c="Station")   # plain paper: the clipboard clip carries printed text; loc, f3, n = palm_pose(CH["OfficerD"], "R", 1200, 0.06, -0.02)
attach_seq(fp3, [(1, CH["OfficerD"], "wrist.R", frame_from(loc + f3 * 0.12, f3, -n), 1200)])
ob("OfficeFan_ceiling_fan").location = ob("OfficeFan_ceiling_fan_blades").location
# wall clock: find its thin axis and face it +X on the back wall; hands spin 5 hours (f1290 -> 1381)
cparts = {n: ob("St_" + n) for n in ("wall_clock", "wall_clock_hours_hand", "wall_clock_minute_hand", "wall_clock_second_hand")}
cb = cparts["wall_clock"]; pts = [Vector(c_) for c_ in cb.bound_box]
dims = [max(p[i] for p in pts) - min(p[i] for p in pts) for i in range(3)]; thin = dims.index(min(dims))
print("CLOCK dims", [round(d, 3) for d in dims], "thin", thin)
croot = bpy.data.objects.new("ClockRoot", None); C("Station").objects.link(croot)
croot.location = CLOCK_POS
# rotate so the thin axis points +X (face out of the back wall)
if thin == 1: croot.rotation_euler = (0, 0, R_(90))
elif thin == 2: croot.rotation_euler = (0, R_(90), 0)
for o in cparts.values(): o.parent = croot; o.scale = (1.6, 1.6, 1.6)
# cover the small maker's mark printed under the 12 (no brand marks on props)
dial_m = pbr("DialWhite", (0.86, 0.86, 0.84), 0.5)
bpy.context.view_layer.update()
cw = [croot.matrix_world @ (cb.matrix_basis @ Vector(c_)) for c_ in cb.bound_box]
front_x = max(p.x for p in cw)
for nm_, zoff in (("DialPatch", 0.085),):
    dp = cyl(nm_, (0, 0, 0), 0.036, 0.002, dial_m, c="Station", verts=20, rot=(0, R_(90), 0))
    dp.location = Vector((-18.81, CLOCK_POS.y, CLOCK_POS.z + zoff))
    dp["front_x"] = front_x
print("CLOCK front", round(front_x, 3))
ax = thin
for nm, turns in (("wall_clock_hours_hand", 5 / 12), ("wall_clock_minute_hand", 5.0), ("wall_clock_second_hand", 20.0)):
    o = cparts[nm]; o.rotation_mode = "XYZ"
    for f, u in ((1, 0.0), (1290, 0.0), (1381, 1.0), (1560, 1.0 + 0.02)):
        e = [0, 0, 0]; e[ax] = -2 * math.pi * turns * u; o.rotation_euler = e; o.keyframe_insert("rotation_euler", frame=f)
for i, o in enumerate([x for x in bpy.data.objects if x.name.startswith("Indicator_")]):
    m = o.data.materials[0]; e = m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
    for f in range(1, 1561, 24):
        e.default_value = 8.0 if ((f // 24 + i) % 2) else 1.5; e.keyframe_insert("default_value", frame=f)
for o in bpy.data.objects:
    if o.name.startswith(("Flag_", "B_")) and ("Flag_" in o.name or "_cloth" in o.name):
        o.keyframe_insert("rotation_euler", frame=1)
        for fc in fcurves(o):
            md = fc.modifiers.new("NOISE"); md.scale = 14 + random.uniform(0, 8); md.strength = 0.5 if "Flag" in o.name else 0.15; md.phase = random.uniform(0, 100)

# ------------------------------------------------------------------ traffic: rickshaws (left-hand traffic), wheels spin
def drive(root, f0, f1, p0, p1, heading_deg):
    root.rotation_euler = (0, 0, R_(heading_deg))
    for f in range(f0, f1 + 1, 4):
        u = (f - f0) / (f1 - f0); root.location = Vector(p0).lerp(Vector(p1), u)
        root.location.z = 0.012 * math.sin(f * 0.9); root.keyframe_insert("location", frame=f)
    root.keyframe_insert("rotation_euler", frame=f0)
    dist = (Vector(p1) - Vector(p0)).length
    for wn in root["wheels"]:
        w = ob(wn); w.rotation_mode = "YXZ"
        for f in (f0, f1):
            w.rotation_euler = (dist * (f - f0) / (f1 - f0) / 0.25, R_(90), 0); w.keyframe_insert("rotation_euler", frame=f)
        for fc in fcurves(w):
            for k in fc.keyframe_points: k.interpolation = "LINEAR"
drive(ob("Rick_0"), 1, 260, (-3.8, 4.0, 0), (-3.8, 14.5, 0), 180)
drive(ob("Rick_1"), 1, 420, (1.9, 40.0, 0), (1.9, 40.0 - 5.0 * 7, 0), 0)
drive(ob("Rick_2"), 1, 420, (1.9, 75.0, 0), (1.9, 75.0 - 6.0 * 7, 0), 0)
drive(ob("Rick_3"), 1, 1560, (-1.8, 32.0, 0), (-1.8, 118.0, 0), 180)
drive(ob("Rick_4"), 1370, 1560, (1.9, 75.0, 0), (1.9, 75.0 - 5.0 * 3.2, 0), 0)
for nm in ("Rick_0", "Rick_1", "Rick_2", "Rick_3"):
    for fc in fcurves(ob(nm)):
        pass
# animals: the cows chew and sway, the dog breathes
for nm_, amp in (("Cow", 4.0), ("Cow2", 3.0)):
    o_ = ob(nm_); r0 = o_.rotation_euler.z
    for f in range(1, 1561, 45):
        o_.rotation_euler.z = r0 + R_(amp) * math.sin(f / 37.0); o_.keyframe_insert("rotation_euler", index=2, frame=f)
bpy.data.objects.remove(ob("Dog"), do_unlink=True)
# dust puffs kicked up behind the bike
DUST = bpy.data.materials.new("Dust"); DUST.use_nodes = True; dn = DUST.node_tree.nodes; dl_ = DUST.node_tree.links
bsd = dn["Principled BSDF"]; bsd.inputs["Base Color"].default_value = (0.55, 0.45, 0.33, 1); bsd.inputs["Roughness"].default_value = 1.0
nz = dn.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 6; tcd = dn.new("ShaderNodeTexCoord")
dl_.new(tcd.outputs["Object"], nz.inputs["Vector"])
mrd = dn.new("ShaderNodeMapRange"); mrd.inputs["From Min"].default_value = 0.45; mrd.inputs["From Max"].default_value = 0.75; mrd.inputs["To Max"].default_value = 0.35
dl_.new(nz.outputs["Fac"], mrd.inputs["Value"]); dl_.new(mrd.outputs["Result"], bsd.inputs["Alpha"])
for i in range(14):
    fs = 10 + i * 15; p, _ = bike_pt(fs, 0.0, -0.95, 0.15)
    d_ = sphere("Dust_%d" % i, p, 0.25, DUST, c="Traffic")
    for f, s_ in ((fs, 0.2), (fs + 30, 1.6), (fs + 60, 2.4)):
        d_.scale = (s_, s_ * 1.3, s_ * 0.6); d_.location = p + Vector((random.uniform(-0.2, 0.2), -0.4 * (f - fs) / 30, 0.1 * (f - fs) / 30))
        d_.keyframe_insert("scale", frame=f); d_.keyframe_insert("location", frame=f)
    key_vis(d_, [(fs, fs + 60)])
for k in range(5):     # dust as he brakes
    p, _ = bike_pt(FS - 10, 0.0, -0.8 + k * 0.3, 0.1); d_ = sphere("DustStop_%d" % k, p, 0.3, DUST, c="Traffic")
    for f, s_ in ((FS - 14, 0.3), (FS + 20, 1.8), (FS + 70, 2.6)):
        d_.scale = (s_, s_, s_ * 0.5); d_.keyframe_insert("scale", frame=f)
    key_vis(d_, [(FS - 14, FS + 70)])

# ------------------------------------------------------------------ grid pulses: glowing packets running along the lines (beat 4)
PULSE_M = emit("Pulse", (0.5, 0.85, 1.0), 30.0)
pcount = 0
for lo_ in [o for o in bpy.data.objects if o.name.startswith(("Line_", "FeedLine"))]:
    for si, sp_ in enumerate(lo_.data.splines):
        pts_ = [lo_.matrix_world @ Vector(p.co[:3]) for p in sp_.points]
        for rep in range(2):
            pu = sphere("Pulse_%d" % pcount, pts_[0], 0.3, PULSE_M, c="Grid", scale=(1, 1, 1)); pcount += 1
            f0 = 380 + rep * 45 + si * 6
            for f in range(f0, f0 + 61, 3):
                u = (f - f0) / 60 * (len(pts_) - 1); i0 = min(int(u), len(pts_) - 2)
                pu.location = pts_[i0].lerp(pts_[i0 + 1], u - i0); pu.keyframe_insert("location", frame=f)
            key_vis(pu, [(f0, f0 + 60)])

# ------------------------------------------------------------------ lighting: day -> dusk, station power cut, town lights at dusk
W_ = sc.world.node_tree
wn, wl = W_.nodes, W_.links
envs = [n for n in wn if n.type == "TEX_ENVIRONMENT"]; klopp = next(n for n in envs if "kloppenheim" in n.image.name)
lp = wn.new("ShaderNodeLightPath"); tint = wn.new("ShaderNodeMix"); tint.data_type = "RGBA"; tint.blend_type = "MULTIPLY"
wl.new(klopp.outputs["Color"], tint.inputs["A"]); tint.inputs["B"].default_value = (1.0, 0.55, 0.4, 1)
wl.new(wn["DuskMix"].outputs["Result"], wn.new("ShaderNodeMath").inputs[0])
camsel = wn.new("ShaderNodeMix"); camsel.data_type = "RGBA"
tf = tint.inputs["Factor"]
wl.new(wn["DuskMix"].outputs["Result"], camsel.inputs["A"]); wl.new(tint.outputs["Result"], camsel.inputs["B"])
wl.new(lp.outputs["Is Camera Ray"], camsel.inputs["Factor"])
wl.new(camsel.outputs["Result"], wn["WorldBG"].inputs["Color"])
for f, v_ in ((1, 0.0), (1150, 0.0), (1235, 1.0)):
    tf.default_value = v_; tf.keyframe_insert("default_value", frame=f)
mixf = W_.nodes["DuskMix"].inputs["Factor"]; bgs = W_.nodes["WorldBG"].inputs["Strength"]
sunO = ob("Sun")
for f, mf, st, se, sel, col in ((1, 0.0, 1.0, 4.5, 40, (1.0, 0.95, 0.88)), (1150, 0.0, 1.0, 4.5, 40, (1.0, 0.95, 0.88)),
                               (1235, 1.0, 0.55, 1.2, 8, (1.0, 0.55, 0.3)), (1560, 1.0, 0.5, 1.0, 6, (1.0, 0.5, 0.28))):
    mixf.default_value = mf; mixf.keyframe_insert("default_value", frame=f)
    bgs.default_value = st; bgs.keyframe_insert("default_value", frame=f)
    sunO.data.energy = se; sunO.data.keyframe_insert("energy", frame=f)
    sunO.data.color = col; sunO.data.keyframe_insert("color", frame=f)
    sunO.rotation_euler = (R_(90 - sel), 0, R_(-140)); sunO.keyframe_insert("rotation_euler", frame=f)
WIN_LIT = ["StWinLit_%d" % i for i in range(4)]
ST_TUBES = ["St_tube_0", "St_tube_1"]
# station windows go dark one by one (upper floor), interior tubes + fills die, door lamps die
for i, mn in enumerate(WIN_LIT):
    e = bpy.data.materials[mn].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
    fo_ = 1188 + [0, 2, 1, 3][i] * 9
    for f, v_ in ((1, 5.0), (fo_, 5.0), (fo_ + 2, 0.0)):
        e.default_value = v_; e.keyframe_insert("default_value", frame=f)
for nm in ST_TUBES + ["StLamp"]:
    m = bpy.data.materials[nm] if nm in bpy.data.materials else ob(nm).data.materials[0]
    e = m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
    for f, v_ in ((1, 6.0), (1214, 6.0), (1216, 0.0)):
        e.default_value = v_; e.keyframe_insert("default_value", frame=f)
for i in range(2):
    L = ob("StFill_%d" % i).data
    for f, v_ in ((1, 600), (1214, 600), (1216, 0)):
        L.energy = v_; L.keyframe_insert("energy", frame=f)
moon = bpy.data.lights.new("StDusk", "AREA"); moon.energy = 260; moon.size = 4; moon.color = (0.35, 0.45, 0.85)
mo = bpy.data.objects.new("StDusk", moon); mo.location = (-11.5, 57.0, 3.25); mo.rotation_euler = (0, 0, 0); moon.size = 7; C("Station").objects.link(mo)
for f, v_ in ((1, 0), (1214, 0), (1230, 260)):
    moon.energy = v_; moon.keyframe_insert("energy", frame=f)
# town windows: a share of them light up warm as dusk falls; street lamps on
WL = bpy.data.materials.new("WinLitTown"); WL.use_nodes = True; wb = WL.node_tree.nodes["Principled BSDF"]
wb.inputs["Base Color"].default_value = (0.05, 0.05, 0.05, 1); wb.inputs["Emission Color"].default_value = (1.0, 0.78, 0.45, 1); wb.inputs["Roughness"].default_value = 0.1
for f, v_ in ((1, 0.0), (1180, 0.0), (1260, 4.0)):
    wb.inputs["Emission Strength"].default_value = v_; wb.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)
random.seed(11)
for o in bpy.data.objects:
    if o.name.endswith("_glass") and o.name.startswith("B_") and random.random() < 0.45:
        o.data = o.data.copy(); o.data.materials[0] = WL
bulb = bpy.data.materials.get("street_lamp_01_bulb")
if bulb:
    bs_ = next(n for n in bulb.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bs_.inputs["Emission Color"].default_value = (1.0, 0.75, 0.4, 1)
    for f, v_ in ((1, 0.0), (1200, 0.0), (1240, 12.0)):
        bs_.inputs["Emission Strength"].default_value = v_; bs_.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)
for f, ex in ((1, 0.0), (1150, 0.0), (1235, 0.8), (1250, 1.2), (1388, 1.2), (1418, 0.9), (1560, 0.9)):
    sc.view_settings.exposure = ex; sc.view_settings.keyframe_insert("exposure", frame=f)

# warm spill from the shop across the road lights his face for the final smirk
ff = bpy.data.lights.new("FaceFill", "AREA"); ff.size = 1.2; ff.color = (1.0, 0.8, 0.55)
ffo = bpy.data.objects.new("FaceFill", ff); C("Lights").objects.link(ffo) if "Lights" in bpy.data.collections else sc.collection.objects.link(ffo)
ffo.location = (-2.4, 58.6, 2.4); ffo.rotation_euler = (Vector((-3.6, 56.8, 1.6)) - ffo.location).to_track_quat("-Z", "Y").to_euler()
for f, e in ((1, 0), (1430, 0), (1470, 45), (1560, 45)):
    ff.energy = e; ff.keyframe_insert("energy", frame=f)
ob("Office_Clip").hide_render = True   # clipboard clip has printed text
# ------------------------------------------------------------------ the one continuous camera
cam_d = bpy.data.cameras.new("CAM_Film"); cam_d.lens = 24; cam_d.sensor_fit = "AUTO"; cam_d.clip_start = 0.02
cam_d.dof.use_dof = True; cam_d.dof.aperture_fstop = 4.0
cam = bpy.data.objects.new("CAM_Film", cam_d); sc.collection.objects.link(cam); sc.camera = cam
aim = bpy.data.objects.new("CAM_Film_Aim", None); sc.collection.objects.link(aim)
tt = cam.constraints.new("TRACK_TO"); tt.target = aim; tt.track_axis = "TRACK_NEGATIVE_Z"; tt.up_axis = "UP_Y"
cam_d.dof.focus_object = aim
def by(f): return bike_y(f)
SCRN = SC_C
def headw(f):
    return bone_world(CH["ManW"], "head", f).translation + Vector((0, -0.02, 0.07))
HW = {f: headw(f) for f in (600, 619, 660, 710, 760, 810, 860, 895, 925)}
for f, h in HW.items(): print("HEADW", f, tuple(round(x, 3) for x in h))
FACE = HW[760]
CAMK = [
    (1, V(-1.35, by(1) + 1.15, 0.32), V(-2.55, by(1) + 0.45, 0.6), 22),
    (40, V(-1.25, by(40) + 1.5, 0.65), V(-2.6, by(40) + 0.15, 1.15), 24),
    (75, V(-1.5, by(75) + 1.95, 1.65), V(-2.6, by(75) - 0.05, 1.6), 30),
    (110, V(-1.9, by(110) + 2.6, 1.85), V(-2.6, by(110) - 0.2, 1.5), 28),
    (140, V(-3.75, by(140) + 3.4, 1.35), V(-2.6, by(140), 1.3), 26),
    (170, V(-1.7, 17.6, 1.7), V(-4.2, 23.0, 1.6), 28),
    (200, V(-0.8, 18.9, 1.8), V(-3.9, 22.7, 1.5), 28),
    (235, V(-1.45, 19.95, 1.78), V(-3.6, 22.3, 1.25), 34),
    (262, V(-2.0, 20.3, 1.62), V(-3.35, 21.9, 1.2), 40),
    (290, V(-1.5, 22.5, 1.55), V(-2.6, 20.95, 1.55), 32),
    (312, V(-1.3, 22.9, 1.75), V(-2.6, 20.9, 1.82), 30),
    (322, V(-1.05, 22.85, 1.75), V(-1.2, 25.6, 1.8), 30),
    (330, V(0.0, 22.9, 1.72), V(3.2, 26.0, 1.8), 30),
    (340, V(1.4, 23.0, 1.7), V(7.3, 24.6, 1.7), 30),
    (370, V(4.5, 23.55, 1.7), V(7.3, 24.35, 1.68), 34),
    (397, V(5.9, 23.85, 1.72), V(7.3, 24.35, 1.66), 40),
    (430, V(5.8, 24.9, 2.4), V(9.5, 26.0, 2.0), 26),
    (460, V(7.6, 28.5, 6.5), V(12.0, 36.0, 10.0), 22),
    (485, V(9.5, 31.5, 15.5), V(12.0, 36.0, 20.0), 22),
    (510, V(12.5, 30.0, 24.0), V(2.0, 60.0, 10.0), 24),
    (540, V(19.0, 31.0, 7.0), V(21.5, 38.0, 1.6), 26),
    (562, V(21.5, 35.4, 2.2), V(21.5, 42.0, 1.3), 24),
    (578, V(21.55, 38.0, 1.62), V(21.5, 43.0, 1.15), 24),
    (600, V(21.95, 41.7, 1.55), SCRN, 28),
    (619, V(22.1, 42.25, 1.42), SCRN, 30),
    (660, HW[660] + V(0.4, 0.22, 0.0), SCRN, 30),
    (710, V(21.84, 43.38, 1.12), scr(-0.1, pr_v), 36),
    (735, V(22.25, 43.45, 1.12), HW[710] + V(0, 0.1, -0.04), 32),
    (770, V(22.1, 43.56, 1.05), HW[760] + V(0, 0.1, -0.04), 34),
    (805, V(21.8, 43.45, 1.07), scr(0.55, pr_v + 0.1), 42),
    (835, V(22.3, 43.4, 1.16), HW[810] + V(0, 0.1, -0.04), 34),
    (865, V(22.12, 43.55, 1.08), HW[860] + V(0, 0.1, -0.04), 36),
    (895, V(22.32, 43.36, 1.17), HW[895] + V(0, 0.1, -0.04), 36),
    (925, V(22.6, 43.05, 1.15), V(21.6, 43.3, 1.0), 24),
    (960, V(23.4, 43.0, 1.12), V(22.0, 43.4, 1.0), 24),
    (995, V(24.05, 42.85, 1.14), V(22.2, 43.3, 1.15), 26),
    (1025, V(23.95, 42.5, 1.35), V(24.7, 43.3, 1.3), 28),
    (1050, V(24.8, 42.68, 1.5), V(LEVER_PIVOT.x - 0.1, LEVER_PIVOT.y, 1.45), 34),
    (1075, V(24.85, 42.72, 1.32), V(LEVER_PIVOT.x - 0.05, LEVER_PIVOT.y, 1.28), 38),
    (1100, V(23.6, 41.4, 1.7), V(25.0, 43.2, 1.35), 26),
    (1128, V(21.5, 39.3, 1.6), V(22.5, 42.5, 1.3), 24),
    (1142, V(21.5, 37.3, 1.62), V(21.6, 41.0, 1.5), 24),
    (1156, V(21.3, 35.6, 5.8), V(20.5, 40.0, 3.0), 24),
    (1174, V(15.5, 42.5, 16.5), V(-4.0, 57.0, 5.0), 24),
    (1195, V(3.5, 51.0, 10.5), V(-7.0, 56.0, 3.0), 24),
    (1215, V(-1.0, 52.5, 5.5), V(-7.2, 55.0, 3.6), 26),
    (1232, V(-5.3, 53.9, 1.75), V(-9.0, 53.9, 1.6), 26),
    (1250, V(-7.3, 53.9, 1.62), V(-11.0, 54.6, 1.3), 24),
    (1290, V(-9.2, 55.2, 1.5), V(-11.4, 53.6, 1.25), 28),
    (1306, V(-10.0, 56.5, 1.45), V(-12.1, 57.8, 1.95), 28),
    (1324, V(-11.2, 57.1, 1.6), V(-14.3, 56.4, 1.45), 30),
    (1344, V(-14.4, 59.3, 1.7), V(-17.3, 62.2, 1.45), 30),
    (1364, V(-15.7, 57.4, 2.15), CLOCK_POS, 42),
    (1381, V(-17.5, 57.1, 2.32), CLOCK_POS, 45),
    (1406, V(-10.1, 59.1, 1.55), V(-11.35, 60.5, 1.12), 30),
    (1424, V(-9.0, 57.4, 1.6), V(-4.0, 56.4, 1.45), 26),
    (1440, V(-7.6, 57.0, 1.6), V(-3.6, 55.2, 1.4), 26),
    (1470, V(-5.6, 57.8, 1.55), V(-3.6, 55.6, 1.5), 28),
    (1515, V(-4.5, 58.9, 1.58), V(-3.6, 56.5, 1.6), 32),
    (1560, V(-4.25, 58.25, 1.6), V(-3.63, 56.8, 1.63), 40)]
fc_ = catmull([(f, c) for f, c, a, l in CAMK]); fa_ = catmull([(f, a) for f, c, a, l in CAMK]); fl_ = catmull([(f, float(l)) for f, c, a, l in CAMK])
for f in list(range(1, FRAME_END + 1, 2)) + [FRAME_END]:
    cam.location = fc_(f); cam.keyframe_insert("location", frame=f)
    aim.location = fa_(f); aim.keyframe_insert("location", frame=f)
    cam_d.lens = fl_(f); cam_d.keyframe_insert("lens", frame=f)
sc.frame_set(1)
import json
json.dump([{"beat": b, "frame": F(t), "first_words": w} for b, t, w in BEATS], open(os.path.join(HERE, "..", "beats.json"), "w"), indent=1)
print("FX_CAMERA_DONE")
