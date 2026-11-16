# exec'd by 03_anim.py: kitchen S4, S5 and hospital S22
GLASS = OB["Glass"]; FA = CH["Father"]; MO = CH["Mother"]; BOY = CH["Boy"]
KX = Vector((300, 0, 0))
FP = KX + Vector((0, 1.42, 0))
GLASS_REST = GLASS.location.copy()

# ================================================================== S4: Father raises the glass, sips (rim below the lips), lowers it, frowns, hand to throat
put("Father", [("S4", FP, 0), ("S5", FP, 0)])
fa = f0("S4"); fe = fx("S4")
MOUTH = face_point(FA, "mouth"); CHIN = face_point(FA, "chin")
def glass_path(f):
    """glass centre (rig local, facing -Y): chest -> just below the lips -> chest"""
    t = f - fa
    lo = Vector((-0.11, -0.32, 1.27)); hi_ = None
    ev(f); m = posed(FA, MOUTH)
    hi_ = m + Vector((-0.01, -0.085, -0.13))
    u = smooth(t / 30) - smooth((t - 95) / 30)
    return lo.lerp(hi_, u), u
for i, f in enumerate(frs(fa, fe, 20)):
    sip = smooth((f - fa - 25) / 20) - smooth((f - fa - 90) / 20)
    stand(FA, f, flex=3, spine=4 + 3 * math.sin(i), head=(10 * sip + 4 - 10 * smooth((f - fa - 110) / 20), 0))
arms_hang(FA, fa)
face(FA, fa, 0.0, -6); face(FA, fa + 60, 0.0, -18); face(FA, fa + 100, -0.006, -18, 1); face(FA, fa + 118, -0.010, -22, 2); face(FA, fe, -0.010, -20, 2)
blinks(FA, fa, fa + 60, every=100)
for f in frs(fa, fe, 2):
    p, u = glass_path(f)
    tilt = 18 * (smooth((f - fa - 40) / 18) - smooth((f - fa - 85) / 18))
    gw = world(FA, p)
    GLASS.rotation_mode = 'XYZ'; GLASS.location = gw - Vector((0, 0, 0.075)); GLASS.rotation_euler = (R_(-tilt), 0, 0)
    GLASS.keyframe_insert("location", frame=f); GLASS.keyframe_insert("rotation_euler", frame=f)
ev(fa); _side = (FA.r.o.matrix_world.to_3x3() @ Vector((1, 0, 0))).normalized(); _gc = GLASS.matrix_world @ Vector((0, 0, 0.07))
print("GLASS grip", grip_follow(FA.r.o, "R", GLASS, fa, list(frs(fa, fe, 2)) + [fe], _gc - _side * 0.04, _side, back=0.009))
# left hand to the collar after the frown
NECK = (FA.r.BN["neck01"].head_local + FA.r.BN["neck02"].head_local) / 2
for f in frs(fa + 110, fe, 4):
    ev(f); M = FA.r.o.matrix_world
    n_ = M @ (FA.r.PB["spine01"].head + Vector((0.04, -0.13, -0.03))); fw = (M.to_3x3() @ Vector((0, -1, 0))).normalized()
    u = smooth((f - fa - 110) / 24)
    sh = M @ FA.r.PB["upperarm01.L"].head
    tgt = (sh + Vector((0, 0, -0.5)) + fw * 0.15).lerp(n_ + fw * 0.03, u)
    place_hand(FA.r.o, "L", f, tgt, -fw, (M.to_3x3() @ Vector((-1, 0, 0.4))).normalized())
apply_pose(FA.r.o, "L", "relaxed", fa + 110); apply_pose(FA.r.o, "L", "shield", fa + 134)
camshot("S4", [(0.0, (300.08, -0.05, 1.58), (300.0, 1.2, 1.42), 40), (1.0, (300.06, 0.15, 1.57), (300.0, 1.2, 1.44), 40)])

# ================================================================== S5: kitchen wide: glass on the counter, Father bends, hand over his mouth; Mother and Boy look on
fa = f0("S5"); fe = fx("S5")
key_vis_g = None
GL_C = KX + Vector((-0.28, 0.62, 0.905))
GLASS.location = GL_C; GLASS.rotation_euler = (0, 0, 0); GLASS.keyframe_insert("location", frame=fa); GLASS.keyframe_insert("rotation_euler", frame=fa)
for i, f in enumerate(frs(fa, fe, 15)):
    u = smooth((f - fa) / 50.0)
    stand(FA, f, flex=4 + 6 * u, spine=6 + 10 * u + 5 * math.sin(i * 1.9), head=(6 + 6 * u + 4 * math.sin(i * 1.9), 0), dz=-0.02 * u)
face(FA, fa, -0.010, -20, 2); face(FA, fe, -0.011, -24, 2); blinks(FA, fa, fe, -0.010, -20, every=90)
for f in frs(fa, fe, 4):        # right palm flat on the counter edge, left hand in front of the mouth
    ev(f); M = FA.r.o.matrix_world; fw = (M.to_3x3() @ Vector((0, -1, 0))).normalized()
    place_hand(FA.r.o, "R", f, KX + Vector((-0.42, 0.66, 0.905)), Vector((0, 0, -1)), Vector((0.15, -1, 0)))
    m = M @ posed(FA, MOUTH); u = smooth((f - fa) / 24)
    sh = M @ FA.r.PB["upperarm01.L"].head
    place_hand(FA.r.o, "L", f, (sh + Vector((0, 0, -0.4)) + fw * 0.2).lerp(m + fw * 0.03, u), -fw, (M.to_3x3() @ Vector((-1, 0, 0.25))).normalized())
apply_pose(FA.r.o, "R", "flat_palm", fa); apply_pose(FA.r.o, "L", "shield", fa)
MOP = KX + Vector((-0.78, 1.32, 0)); BOP = KX + Vector((1.52, 0.42, 0))
def yaw_to(p, tgt):
    d = (tgt - p); return math.degrees(math.atan2(d.x, -d.y))
put("Mother", [("S5", MOP, yaw_to(MOP, FP))])
put("Boy", [("S1", (0, 0, 0), 180), ("S5", BOP, yaw_to(BOP, FP)), ("S22", (0, 0, 0), 0)])
breathe(MO, fa, fe, head=(6, -4), step=24, flex=3, amp=2.5); arms_hang(MO, fa)
ev(fa + 24); _M = MO.r.o.matrix_world; _c = _M @ (MO.r.PB["spine02"].head + Vector((-0.05, -0.15, 0.0)))
for f in (fa + 24, fe):      # Mother's right hand comes to her own chest (worry)
    place_hand(MO.r.o, "R", f, _c, (_M.to_3x3() @ Vector((0, 1, 0))).normalized(), (_M.to_3x3() @ Vector((1, 0, 0.3))).normalized())
apply_pose(MO.r.o, "R", "shield", fa + 24)
face(MO, fa, 0.004, -6, 1); blinks(MO, fa, fe, 0.004, -6, ofs=40)
breathe(BOY, fa, fe, head=(-10, 8), step=24, flex=2, amp=2.5); arms_hang(BOY, fa)
face(BOY, fa, 0.003, -4); blinks(BOY, fa, fe, 0.003, -4, ofs=70)
camshot("S5", [(0.0, (301.9, -2.1, 1.05), (300.45, 1.0, 1.15), 26), (1.0, (301.8, -1.75, 1.04), (300.45, 1.0, 1.15), 26)])

# ================================================================== S22: hospital: Father in bed, Boy beside him, his hand resting on his father's
HX = Vector((2100, 0, 0)); HBED = OB["HospitalBed"]; HCH = OB["BedsideChair"]
fa = f0("S22"); fe = fx("S22")
dg = bpy.context.evaluated_depsgraph_get()
bmn, bmx = bbox([HBED]); bc = (bmn + bmx) / 2
def top_at(x, y):
    hit = sc.ray_cast(bpy.context.evaluated_depsgraph_get(), Vector((x, y, 2.7)), Vector((0, 0, -1)))
    return hit[1].z if hit[0] else 0.0
ends = {sgn: max(top_at(bc.x + sgn * (bmx.x - bmn.x) / 2 * 0.97, bc.y + dy) for dy in (-0.3, 0, 0.3)) for sgn in (-1, 1)}
HEAD_SGN = -1 if ends[-1] >= ends[1] else 1                          # taller end = headboard
MTOP = max(top_at(bc.x + dx, bc.y) for dx in (-0.3, 0.0, 0.3))
print("BED headboard side", HEAD_SGN, "mattress top", round(MTOP, 3), ends)
h = Vector((HEAD_SGN, 0, 0)); Yw = Vector((0, 0, -1)); Xw = Yw.cross(h)
Rl = Matrix((Xw, Yw, h)).transposed().to_4x4()
tilt = Matrix.Identity(4)                                              # flat bed; the head rests on a pillow
head_end = bc.x + HEAD_SGN * ((bmx.x - bmn.x) / 2 - 0.22)
height = FA.r.BN["head"].tail_local.z + 0.1
origin = Vector((head_end - HEAD_SGN * height, bc.y, MTOP + 0.135))
CHAIR_SIDE = 1                                                         # boy's chair on the far side: he faces the camera across the bed
MF = Matrix.Translation(origin) @ tilt @ Rl
put("Father", [("S4", FP, 0), ("S5", FP, 0), ("S22", None, MF)])
ev(fa + 1)
for i, f in enumerate(frs(fa, fe, 30)):
    u = smooth((f - fa - 60) / 60)
    stand(FA, f, flex=0, spine=10 + 1.2 * math.sin(i * 1.5), head=(14, 14 * u * (1 if Xw.y > 0 else -1) * CHAIR_SIDE))
    for s_ in "LR": FA.key_foot(s_, f, FA.foot_xy(s_, Vector((0, 0)), 0.0) + Vector((0.0, -0.04)), 0.0, lift=-0.04, pitch=-55)   # lying: feet relaxed and pointed
face(FA, fa, 0.002, -14); face(FA, fe, 0.004, -16, 1); blinks(FA, fa, fe, 0.002, -14, every=120)
PIL = box("Pillow", (0.42, 0.62, 0.12), (head_end + HEAD_SGN * 0.02, bc.y, MTOP + 0.06), mat("PillowWhite", (0.95, 0.95, 0.97), 0.8), HBED.users_collection[0], bevel=0.05)
PIL.modifiers.new("sub", 'SUBSURF').levels = 2
# blanket: built at fa with the right arm lifted out of the way, draped by ray casts over body and mattress
NEAR = -1 if bc.y > HX.y - 0.2 else 1                                  # bed side facing the room (-Y)
for s in "LR": apply_pose(FA.r.o, s, "relaxed", fa)
arms_hang(FA, fa)
near_side = "L" if (MF.to_3x3() @ Vector((1, 0, 0))).y * CHAIR_SIDE > 0 else "R"   # the arm on the boy's side
far_side = "L" if near_side == "R" else "R"
ev(fa)
hip_w = FA.r.o.matrix_world @ FA.r.PB["root"].head; chest_w = FA.r.o.matrix_world @ FA.r.PB["spine03"].head
x_feet = origin.x - HEAD_SGN * 0.15; x_top = hip_w.x + HEAD_SGN * 0.2     # blanket up to the waist: hands rest on his chest, clear of it
nx, ny = 46, 34; W_ = (bmx.y - bmn.y) * 0.82
# height field from the body/clothes vertices (arm and hand vertices left out), not from ray casts
_mods = [(o, m) for o in OB if o.parent == FA.r.o for m in getattr(o, "modifiers", []) if m.type in ("SUBSURF", "MASK") and m.show_viewport]
for o, m in _mods: m.show_viewport = False
bpy.context.view_layer.update(); _dg = bpy.context.evaluated_depsgraph_get(); cell = {}
gx0 = x_feet; gy0 = bc.y - W_ / 2 - 0.3 if CHAIR_SIDE > 0 else bc.y - W_ / 2; dx_ = (x_top - x_feet) / nx; dy_ = (W_ + 0.3) / ny
for part in [o for o in OB if o.parent == FA.r.o and o.type == 'MESH' and any(k in o.name for k in ("body", "suit", "shoes"))]:
    gi = {g.index: g.name for g in part.vertex_groups}; ev_ = part.evaluated_get(_dg); me_ = ev_.to_mesh(); mw_ = ev_.matrix_world
    skip = set()
    if len(me_.vertices) == len(part.data.vertices):
        for v in part.data.vertices:
            if v.groups:
                gname = gi.get(max(v.groups, key=lambda g: g.weight).group, "")
                if any(k in gname for k in ("arm", "wrist", "finger", "metacarpal", "hand", "thumb")): skip.add(v.index)
    for v in me_.vertices:
        if v.index in skip: continue
        w = mw_ @ v.co; i = round((w.x - gx0) / dx_); j = round((w.y - gy0) / dy_)
        for ii in (i - 1, i, i + 1):
            for jj in (j - 1, j, j + 1):
                if 0 <= ii <= nx and 0 <= jj <= ny: cell[jj, ii] = max(cell.get((jj, ii), -9), w.z)
    ev_.to_mesh_clear()
for o, m in _mods: m.show_viewport = True
print("BLANKET cells", len(cell))
zs = []
for j in range(ny + 1):
    row = []
    for i in range(nx + 1):
        y = gy0 + dy_ * j; z = max(MTOP, cell.get((j, i), -9)) + 0.035
        off = abs(y - bc.y) - W_ / 2
        if off > 0 and (y - bc.y) * CHAIR_SIDE > 0: z = MTOP + 0.035 - 0.25 * off       # boy's side: no overhang onto his legs
        elif off > 0: z = max(MTOP - 0.3, MTOP + 0.022 - 1.1 * off)
        row.append(z)
    zs.append(row)
raw = [r[:] for r in zs]
zs = [[z + 0.02 for z in r] for r in zs]
for _ in range(12):
    zs = [[(zs[j][i] * 2 + sum(zs[jj][ii] for jj, ii in ((j - 1, i), (j + 1, i), (j, i - 1), (j, i + 1)) if 0 <= jj <= ny and 0 <= ii <= nx) /
            max(1, sum(1 for jj, ii in ((j - 1, i), (j + 1, i), (j, i - 1), (j, i + 1)) if 0 <= jj <= ny and 0 <= ii <= nx)) * 2) / 4
           for i in range(nx + 1)] for j in range(ny + 1)]
zs = [[max(zs[j][i], raw[j][i] + 0.008) + 0.01 for i in range(nx + 1)] for j in range(ny + 1)]
bm = bmesh.new(); vv = {}
for j in range(ny + 1):
    for i in range(nx + 1):
        vv[j, i] = bm.verts.new((x_feet + (x_top - x_feet) * i / nx, gy0 + dy_ * j, zs[j][i]))
for j in range(ny):
    for i in range(nx): bm.faces.new((vv[j, i], vv[j, i + 1], vv[j + 1, i + 1], vv[j + 1, i]))
me = bpy.data.meshes.new("Blanket"); bm.to_mesh(me); bm.free()
BL = bpy.data.objects.new("Blanket", me); HBED.users_collection[0].objects.link(BL)
for p_ in me.polygons: p_.use_smooth = True
so = BL.modifiers.new("thick", 'SOLIDIFY'); so.thickness = 0.04; so.offset = 1

mb_ = mat("BlanketBlue", (0.16, 0.3, 0.55), 0.8); BL.data.materials.append(mb_)
_nt = mb_.node_tree; _P = _nt.nodes["Principled BSDF"]; _tc = _nt.nodes.new("ShaderNodeTexCoord"); _wv = _nt.nodes.new("ShaderNodeTexWave")
_wv.inputs["Scale"].default_value = 2.5; _wv.inputs["Distortion"].default_value = 6.0; _nt.links.new(_tc.outputs["Object"], _wv.inputs["Vector"])
_bp = _nt.nodes.new("ShaderNodeBump"); _bp.inputs["Strength"].default_value = 0.35; _nt.links.new(_wv.outputs["Fac"], _bp.inputs["Height"]); _nt.links.new(_bp.outputs["Normal"], _P.inputs["Normal"])
_P.inputs["Sheen Weight"].default_value = 0.4
_txb = bpy.data.textures.new("blanket_folds", 'CLOUDS'); _txb.noise_scale = 0.18
_db = BL.modifiers.new("folds", 'DISPLACE'); _db.texture = _txb; _db.strength = 0.025; _db.texture_coords = 'GLOBAL'
BL.modifiers.move(len(BL.modifiers) - 1, 0)
# the near arm rests on top of the blanket, hand by the hip
ev(fa)
def blanket_z(x, y):
    hit = sc.ray_cast(bpy.context.evaluated_depsgraph_get(), Vector((x, y, 2.7)), Vector((0, 0, -1)))
    return hit[1].z if hit[0] else MTOP
yh = hip_w.y + (-1 if near_side == "R" and Xw.y > 0 else 1) * 0.0
# his hand rests on his own chest (above the blanket's top edge), toward the boy's side
_hx = hip_w.x + HEAD_SGN * 0.42; _hy = bc.y + CHAIR_SIDE * 0.22
_h = sc.ray_cast(bpy.context.evaluated_depsgraph_get(), Vector((_hx, _hy, 2.7)), Vector((0, 0, -1)))
HAND_P = Vector((_hx, _hy, (_h[1].z if _h[0] else MTOP + 0.25) + 0.035))
for f in (fa, fe):
    place_hand(FA.r.o, near_side, f, HAND_P, Vector((0, 0, -1)), Vector((-HEAD_SGN, 0, 0)))
key_vis(BL, [(0, False), (fa, True)])
# chair beside the bed at the Father's hip, facing the bed; the Boy sits, leans in, and rests his palm on his father's hand
cmn, cmx = bbox([HCH]); back_hi = [v for v in HCH.data.vertices if (HCH.matrix_world @ v.co).z > cmn.z + 0.8 * (cmx.z - cmn.z)]
back_y = sum((HCH.matrix_world @ v.co).y for v in back_hi) / max(1, len(back_hi)); back_x = sum((HCH.matrix_world @ v.co).x for v in back_hi) / max(1, len(back_hi))
cc = (cmn + cmx) / 2; bdir = Vector((back_x - cc.x, back_y - cc.y, 0)).normalized()
want = Vector((0, CHAIR_SIDE, 0))
ang = math.atan2(want.y, want.x) - math.atan2(bdir.y, bdir.x)
HCH.rotation_euler = (0, 0, HCH.rotation_euler.z + ang)
seat_y = (bmx.y + 0.40) if CHAIR_SIDE > 0 else (bmn.y - 0.40)
HCH.location = HCH.location + Vector((hip_w.x - cc.x - HEAD_SGN * 0.75, seat_y - cc.y + 0.12 * CHAIR_SIDE, 0))   # chair set back toward the foot end; the boy stands at the bedside
ev(fa); cmn, cmx = bbox([HCH])
SEAT_Z = top_at((cmn.x + cmx.x) / 2, (cmn.y + cmx.y) / 2 + 0.05 * -want.y)
print("CHAIR seat", round(SEAT_Z, 3))
BP = Vector((hip_w.x + HEAD_SGN * 0.62, bmx.y + 0.36 if CHAIR_SIDE > 0 else bmn.y - 0.36, 0))
put("Boy", [("S1", (0, 0, 0), 180), ("S5", BOP, yaw_to(BOP, FP)), ("S22", HX + Vector((BP.x - HX.x, BP.y, 0)), 180 if want.y < 0 else 0)])
ev(fa + 1)
for i, f in enumerate(frs(fa, fe, 30)):
    stand(BOY, f, flex=12, spine=12 + 1.5 * math.sin(i * 1.3), head=(-12, 6 * math.sin(i * 0.8)))
face(BOY, fa, 0.003, -12); blinks(BOY, fa, fe, 0.003, -12, ofs=55)
bside = "R" if near_side == "R" else "R"
for f in (fa, fe):
    place_hand(BOY.r.o, "R", f, HAND_P + Vector((0, 0, 0.032)), Vector((0, 0, -1)), Vector((-HEAD_SGN * 0.7, 0.7 if want.y < 0 else -0.7, 0)).normalized())
apply_pose(BOY.r.o, "R", "relaxed_even" if "relaxed_even" in POSES else "relaxed", fa)
ev(fa); M = BOY.r.o.matrix_world
for f in (fa, fe):
    pass
arms_hang(BOY, fa); arms_hang(BOY, fe)
for f in (fa, fe):
    place_hand(BOY.r.o, "R", f, HAND_P + Vector((0, 0, 0.032)), Vector((0, 0, -1)), Vector((-HEAD_SGN * 0.7, 0.7 if want.y < 0 else -0.7, 0)).normalized())
camshot("S22", [(0.0, (hip_w.x + HEAD_SGN * 0.05, bc.y - 1.75, 1.42), (hip_w.x + HEAD_SGN * 0.5, bc.y + 0.45, 0.92), 28),
                (1.0, (hip_w.x + HEAD_SGN * 0.05, bc.y - 1.5, 1.38), (hip_w.x + HEAD_SGN * 0.5, bc.y + 0.45, 0.94), 28)])
