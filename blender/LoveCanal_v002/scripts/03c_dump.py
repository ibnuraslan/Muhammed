# exec'd by 03_anim.py: underground S7, S8; dump site S9-S14; house frames on the cut-away S15
UX = Vector((600, 0, 0)); UX2 = Vector((600, 60, 0)); DX = Vector((900, 0, 0))
key_vis(OB["Backdrop_under"], [(0, False)] + [x for s_ in ("S7", "S8", "S15") for x in ((f0(s_), True), (f1(s_) + 1, False))])
camshot("S7", [(0.0, (600.0, -40.0, 3.5), (600.0, 0.0, 0.5), 32), (1.0, (600.0, -37.0, 1.6), (600.0, 0.0, -3.0), 32)])
camshot("S8", [(0.0, (597.5, -15.0, -5.7), (600.0, -4.0, -5.9), 30), (1.0, (598.8, -11.8, -5.75), (600.5, -3.0, -6.0), 30)])
SL = OB["Under_sludge"]; SL2 = OB["Under2_sludge"]
for o in (SL, SL2):             # slow flow: the ripple texture drifts (keyed, not Scene Time)
    tx = o.modifiers["ripple"].texture; tcoord = bpy.data.objects.new(o.name + "_flow", None); o.users_collection[0].objects.link(tcoord)
    o.modifiers["ripple"].texture_coords = 'OBJECT'; o.modifiers["ripple"].texture_coords_object = tcoord
    tcoord.location = (0, 0, 0); tcoord.keyframe_insert("location", frame=1); tcoord.location = (0, 18, 0); tcoord.keyframe_insert("location", frame=sc.frame_end)
    for fc in fcurves_of(tcoord.animation_data.action):
        for k in fc.keyframe_points: k.interpolation = 'LINEAR'

# ================================================================== S9: the Worker rolls a drum by pushing it with both palms
WK = CH["Worker"]; HAT = OB.get("Worker.hardhat")
if HAT:          # bone parent: the hat rides on the head bone, sitting on the crown
    rig = WK.r.o; bn = rig.data.bones["head"]
    tail = bn.tail_local; desired = Matrix.Translation(tail + Vector((0, -0.005, -0.045)))
    HAT.parent = rig; HAT.parent_type = 'BONE'; HAT.parent_bone = "head"
    Mb = Matrix.Translation(tail) @ bn.matrix_local.to_3x3().to_4x4()
    HAT.matrix_parent_inverse = Matrix.Identity(4); HAT.matrix_basis = Mb.inverted() @ desired
DR = copy_obj(OB["LIB_drum"], "PushDrum", (0, 0, 0), c=OB["DumpGround"].users_collection[0])
r_d = 0.285
WK0 = DX + Vector((-1.6, -18.0, 0)); V_W = 0.9
put("Worker", [("S9", WK0, 90), ("S10", DX + Vector((0, 18.6, 0)), 0)])
fa = f0("S9"); fe = fx("S9")
pth = lambda f: Vector((0, -V_W * (f - fa) / FPS, 0))
WK.walk(pth, lambda f: 0.0, fa, fe, stride=0.5, lift=0.05, bob=0.012, crouch=0.2, lean=56)
DR.rotation_mode = 'XYZ'
for f in range(fa - 1, fe + 2):
    d = V_W * (f - fa) / FPS
    c = WK0 + Vector((0.74 + d, 0, r_d))
    DR.location = c; DR.rotation_euler = (R_(90), d / r_d, 0)      # lying, axis along Y, rolling toward +X
    DR.keyframe_insert("location", frame=f); DR.keyframe_insert("rotation_euler", frame=f)
    if (f - fa) % 2: continue
    ev(f)
    for s, sy in (("L", 0.16), ("R", -0.16)):
        p = c + Vector((-0.1, sy, r_d + 0.02)); n = (c + Vector((0, sy, 0)) - p).normalized()
        place_hand(WK.r.o, s, f, p, n, Vector((1.0, 0, 0.32)))
for s in "LR": apply_pose(WK.r.o, s, "flat_palm", fa)
face(WK, fa, -0.004, -12); blinks(WK, fa, fe, -0.004, -12)
for f in frs(fa, fe, 20): WK.key_spine(f, flex=34, head=(-34, 0))
camshot("S9", [(0.0, (DX.x + 2.6, -19.6, 0.75), (DX.x - 0.6, -18.0, 0.95), 32), (1.0, (DX.x + 2.9, -19.2, 0.75), (DX.x + 0.0, -18.0, 0.95), 34)])

# ================================================================== S10: trucks loaded with drums; the Worker walks between them
fa = f0("S10"); fe = fx("S10")
fw_ = fa + int((fe - fa) * 0.55)
pth = walk_line(WK, fa, fw_, (0, 0), 1.1)
walk_arms(WK, fa, fw_, pth); face(WK, fa, -0.002, -8)
_p_end = pth(fw_)
for i, f in enumerate(frs(fw_ + 2, fe, 6)):          # stops, turns toward the right truck and waves it back
    stand(WK, f, pos=(_p_end.x, _p_end.y), yaw=0, flex=3, spine=4, twist=-22, head=(-4, -40))
    sh = WK.r.BN["upperarm01.R"].head_local
    sw = math.sin(i * 1.1)
    W = Vector((_p_end.x + sh.x - 0.28 + 0.12 * sw, _p_end.y + sh.y - 0.12, sh.z + 0.22 + 0.04 * abs(sw)))
    WK.key_hand("R", f, W, Vector((-0.2 * sw, -0.3, 1)), Vector((0, -1, 0)), pole=W + Vector((-0.4, 0.4, -0.3)))
    shL = WK.r.BN["upperarm01.L"].head_local
    WL = Vector((_p_end.x + shL.x + 0.05, _p_end.y + shL.y - 0.03, shL.z - 0.58))
    WK.key_hand("L", f, WL, Vector((0, -0.12, -1)), Vector((-1, 0, 0)), pole=WL + Vector((0.3, 0.5, 0.25)))
apply_pose(WK.r.o, "R", "open_alarm", fw_ + 8)
for f in frs(fa, fw_, 20): WK.key_spine(f, flex=4, head=(2, 0))
camshot("S10", [(0.0, (DX.x + 1.8, 7.0, 1.7), (DX.x - 0.2, 17.0, 1.4), 24), (1.0, (DX.x + 1.0, 12.2, 1.6), (DX.x - 0.2, 17.5, 1.45), 26)])

# ================================================================== S11-S13: drums tip out of the truck beds and heap up in the pit
# A throwaway rigid-body drop settles a dense heap in the pit (slots). Each drum is then KEYED: it flies in on an arc from the
# truck side (off-frame) into its slot, lowest slots first, so nothing passes through the heap and nothing nears a lens.
DCOLL = coll("SET_drums"); L_dr = OB["LIB_drum"]; random.seed(11)
HS0, HS1 = 1, 360
bpy.ops.rigidbody.world_add(); rbw = sc.rigidbody_world
rbw.substeps_per_frame = 8; rbw.solver_iterations = 20
rbw.point_cache.frame_start = HS0; rbw.point_cache.frame_end = HS1
if not rbw.collection: rbw.collection = bpy.data.collections.new("RigidBodyWorld")
def rb(o, typ, shape, mass=180.0, fr=0.8, rest=0.02):
    with bpy.context.temp_override(object=o, active_object=o, selected_objects=[o]):
        bpy.ops.rigidbody.object_add()
    r = o.rigid_body; r.type = typ; r.collision_shape = shape; r.mass = mass; r.friction = fr; r.restitution = rest
    r.collision_margin = 0.01; r.use_deactivation = False; r.linear_damping = 0.4; r.angular_damping = 0.8
    return r
rb(OB["DumpGround"], 'PASSIVE', 'MESH', fr=0.95)
for g in [o for o in OB if o.name.startswith(("DumpTruck", "Worker", "PushDrum"))]: pass
heap = []
for layer in range(11):
    for gx in range(-6, 7):
        for gy in range(-6, 7):
            x = gx * 0.98 + random.uniform(-0.1, 0.1) + (0.49 if layer % 2 else 0); y = gy * 0.98 + random.uniform(-0.1, 0.1)
            if math.hypot(x, y) > 4.8 - 0.22 * layer: continue
            d = copy_obj(L_dr, "Drum_h%d_%d_%d" % (layer, gx + 6, gy + 6), DX + Vector((x, y, -1.0 + 1.0 * layer)), c=DCOLL)
            d.rotation_euler = (R_(random.choice((random.uniform(-20, 20), random.uniform(70, 110)))), R_(random.uniform(-20, 20)), random.random() * 6)
            rb(d, 'ACTIVE', 'CYLINDER'); heap.append(d)
for f in range(HS0, HS1 + 1): sc.frame_set(f)
final = {d.name: d.matrix_world.copy() for d in heap}
for d in heap:
    with bpy.context.temp_override(object=d, active_object=d, selected_objects=[d]): bpy.ops.rigidbody.object_remove()
with bpy.context.temp_override(object=OB["DumpGround"], active_object=OB["DumpGround"], selected_objects=[OB["DumpGround"]]):
    bpy.ops.rigidbody.object_remove()
with bpy.context.temp_override(scene=sc): bpy.ops.rigidbody.world_remove()
slots = []
for d in heap:
    M = final[d.name]; r = (M.translation.to_2d() - DX.to_2d()).length
    if r < 7.0 and M.translation.z > -3.6: slots.append((M.translation.z, d, M))
    else: bpy.data.objects.remove(d, do_unlink=True)
_G = OB["DumpGround"]; _Gi = _G.matrix_world.inverted(); _dco = [Vector(c) for c in L_dr.bound_box]
def _gz(x, y):
    ok, loc, n, i = _G.ray_cast(_Gi @ Vector((x, y, 50)), _Gi.to_3x3() @ Vector((0, 0, -1)))
    return (_G.matrix_world @ loc).z if ok else 0.0
dropped = 0; keep_ = []
for z_, d, M in slots:              # a drum sunk into the ground reads as a sliced wedge: leave it out
    pen = max(_gz((M @ c).x, (M @ c).y) - (M @ c).z for c in _dco)
    if pen > 0.015: bpy.data.objects.remove(d, do_unlink=True); dropped += 1
    else: keep_.append((z_, d, M))
slots = keep_
# a drum whose core sits inside another drum (deep interpenetration) is also left out
_ax = []
for z_, d, M in slots:
    a_ = (M.to_3x3() @ Vector((0, 0, 1))).normalized(); c_ = M @ Vector((0, 0, 0.44))
    _ax.append((c_, a_))
bad = set()
for i in range(len(slots)):
    if i in bad: continue
    ci, ai = _ax[i]
    for j in range(i + 1, len(slots)):
        if j in bad: continue
        cj, aj = _ax[j]
        if (ci - cj).length > 0.95: continue
        if (ci - cj).length < 0.5: bad.add(j); continue           # two 0.57 m drums can't have centres this close
        for t in (-0.3, -0.15, 0, 0.15, 0.3):
            p_ = ci + ai * t; v_ = p_ - cj; h_ = v_.dot(aj)
            if abs(h_) < 0.38 and (v_ - aj * h_).length < 0.22: bad.add(j); break
for k in sorted(bad, reverse=True):
    bpy.data.objects.remove(slots[k][1], do_unlink=True); slots.pop(k)
print("HEAP dropped (ground)", dropped, "(overlap)", len(bad))
slots.sort(key=lambda t: t[0])
print("HEAP slots", len(slots), "of", len(heap), "top z", round(slots[-1][0], 2))
HC = sum((t[2].translation for t in slots), Vector()) / len(slots); HC.z = 0.0
sc.frame_set(1)
# truck beds tip (keyed hinge rotation)
BEDS = [OB["DumpTruck%d_bed" % i] for i in range(2)]
TIP0, TIP1 = f0("S11") + 10, f0("S11") + 100
for b in BEDS:
    b.rotation_mode = 'XYZ'
    b.rotation_euler = (0, 0, 0); b.keyframe_insert("rotation_euler", frame=0); b.keyframe_insert("rotation_euler", frame=TIP0)
    b.rotation_euler = (R_(-52), 0, 0); b.keyframe_insert("rotation_euler", frame=TIP1)
def fly(d, fs, fe_, P0, M1, q0, spin, lane=0):
    """keyed path into slot M1 landing at fe_: travel high over the heap to a point straight above the slot (rotation done
    on the way), then a vertical drop. Lower slots are filled first, so a vertical drop never passes through a landed drum."""
    P1, q1, _ = M1.decompose(); d.rotation_mode = 'QUATERNION'
    zt = max(P1.z + 1.5, 3.0, P0.z) + 0.3 * (lane % 9)          # own travel height: drums in the air never meet
    A = Vector((P1.x, P1.y, zt)); split = 0.62
    for f in list(range(fs, fe_ + 1, 2)) + [fe_]:
        u = (f - fs) / max(1, fe_ - fs)
        if u < split:
            w = smooth(u / split); p = P0.lerp(A, w); p.z = P0.z + (zt - P0.z) * (1 - (1 - w) ** 2)
            q = q0.slerp(q1, w) @ Quaternion((1, 0, 0), spin * (1 - w))
        else:
            w = ((u - split) / (1 - split)) ** 2; p = A.lerp(P1, w); q = q1.copy()
        if f != fe_:
            R3 = q.to_matrix(); low = min((R3 @ c for c in _dco), key=lambda v: v.z)
            for _ in range(2):
                pc = p + low; need = _gz(pc.x, pc.y) + 0.02 - pc.z
                if need > 0: p.z += need
        d.location = p; d.rotation_quaternion = q
        d.keyframe_insert("location", frame=f); d.keyframe_insert("rotation_quaternion", frame=f)
drums = []
for z_, src, M1 in slots:                 # the heap is already there (years of dumping): every heap drum rests from frame 0
    src.rotation_mode = 'QUATERNION'; l_, q_, _ = M1.decompose(); src.location = l_; src.rotation_quaternion = q_
    src.keyframe_insert("location", frame=0); src.keyframe_insert("rotation_quaternion", frame=0); drums.append(src)
def _overlap(da, db, Ma=None, Mb=None):
    Ma = Ma or da.matrix_world; Mb = Mb or db.matrix_world
    ca = Ma @ Vector((0, 0, 0.44)); cb = Mb @ Vector((0, 0, 0.44))
    if (ca - cb).length > 0.95: return False
    if (ca - cb).length < 0.5: return True
    aa = (Ma.to_3x3() @ Vector((0, 0, 1))).normalized(); ab = (Mb.to_3x3() @ Vector((0, 0, 1))).normalized()
    for (c1, a1, c2, a2) in ((ca, aa, cb, ab), (cb, ab, ca, aa)):
        for t in (-0.3, -0.15, 0, 0.15, 0.3):
            v = c1 + a1 * t - c2; h = v.dot(a2)
            if abs(h) < 0.38 and (v - a2 * h).length < 0.22: return True
    return False
def tumble(d, fs, fe_, P0, q0, M1, roll):
    """slide off the tail and tumble DOWN to M1: z only ever descends (never above the release point), lands at fe_"""
    P1, q1, _ = M1.decompose(); d.rotation_mode = 'QUATERNION'
    for f in list(range(fs, fe_ + 1, 2)) + [fe_]:
        u = (f - fs) / max(1, fe_ - fs)
        p = P0.lerp(P1, smooth(u) * 0.4 + u * 0.6); p.z = P0.z + (P1.z - P0.z) * (u * u)
        q = q0.slerp(q1, smooth(u)) @ Quaternion((1, 0, 0), roll * (1 - u))
        if f != fe_:
            R3 = q.to_matrix(); low = min((R3 @ c for c in _dco), key=lambda v: v.z)
            pc = p + low; need = _gz(pc.x, pc.y) + 0.02 - pc.z
            if need > 0: p.z += need
        d.location = p; d.rotation_quaternion = q
        d.keyframe_insert("location", frame=f); d.keyframe_insert("rotation_quaternion", frame=f)
_gone = []                               # resting heap: any drum still overlapping another is left out
for i in range(len(drums)):
    if drums[i] in _gone: continue
    for j in range(i + 1, len(drums)):
        if drums[j] not in _gone and _overlap(None, None, slots[i][2], slots[j][2]): _gone.append(drums[j])
for d in _gone: drums.remove(d); bpy.data.objects.remove(d, do_unlink=True)
print("HEAP static overlap removed", len(_gone))
ev(1); landed = []
for bi, b in enumerate(BEDS):            # each truck's load: 6 drums ride the tipping bed, slide off the tail, tumble <= 3 m
    bmn, bmx = bbox([b]); cx = (bmn.x + bmx.x) / 2
    for iy in range(2):
        for ix in range(3):
            x = cx + (ix - 1) * 0.66; y = bmn.y + 0.55 + iy * 0.75
            d = copy_obj(L_dr, "Drum_b%d_%d%d" % (bi, ix, iy), (x, y, bmn.z + 0.32 + 0.002), c=DCOLL); d.rotation_mode = 'QUATERNION'
            d.rotation_quaternion = Quaternion((0, 0, 1), random.random() * 6)
            REL = TIP0 + 50 + iy * 44 + ix * 12          # the row at the tail goes first; the second row only after it has landed
            ev(TIP0); OFF = b.matrix_world.inverted() @ d.matrix_world
            for f in frs(TIP0, REL, 2):
                ev(f); l_, q_, _ = (b.matrix_world @ OFF).decompose(); d.location = l_; d.rotation_quaternion = q_
                d.keyframe_insert("location", frame=f); d.keyframe_insert("rotation_quaternion", frame=f)
            ev(REL); P0, q0, _ = d.matrix_world.decompose()
            qL = Quaternion((0, 0, 1), R_(random.uniform(-25, 25))) @ Quaternion((0, 1, 0), R_(90))      # lying, axis roughly along X
            ax = qL @ Vector((0, 0, 1))
            for step in range(12):                       # resting spot behind the tail, clear of the heap and of the other loads
                tx = cx + (ix - 1) * 1.05 + random.uniform(-0.1, 0.1); ty = bmn.y - 1.2 - (1 - iy) * 0.9 - step * 0.25       # first row out lands farther, the second stops nearer the tail
                tz = max(_gz(tx + ax.x * t, ty + ax.y * t) for t in (-0.44, 0, 0.44)) + 0.29
                M1 = Matrix.Translation(Vector((tx, ty, tz)) - ax * 0.44) @ qL.to_matrix().to_4x4()
                pen = max(_gz((M1 @ c).x, (M1 @ c).y) + 0.01 - (M1 @ c).z for c in _dco)
                if pen > 0: M1 = Matrix.Translation((0, 0, pen)) @ M1
                if not any(_overlap(None, o, M1, Mo) for o, Mo in [(o_, o_.matrix_world) for o_ in drums] + landed): break
            landed.append((d, M1))
            tumble(d, REL, REL + 34, P0, q0, M1, R_(random.choice((-160, 160))))
            drums.append(d)
ev(1)
ARR0, ARR1 = TIP0, TIP0 + 140
print("DRUMS heap", len(slots), "loads", len(landed), "landing by", ARR1)
camshot("S11", [(0.0, (DX.x + 0.01, 10.5, 18.0), (DX.x, 10.51, 0.0), 26), (1.0, (DX.x + 0.01, 9.0, 21.0), (DX.x, 9.01, 0.0), 26)])
camshot("S12", [(0.0, HC + Vector((0.01, 0.6, 14.0)), HC + Vector((0, 0.61, 0)), 24), (1.0, HC + Vector((0.01, 0.6, 16.5)), HC + Vector((0, 0.61, 0)), 24)])
camshot("S13", [(0.0, HC + Vector((-11.0, -10.0, 3.8)), HC + Vector((0, 0, 0.2)), 28), (1.0, HC + Vector((-7.8, -12.6, 4.0)), HC + Vector((0, 0, 0.2)), 28)])

# ================================================================== S14: the bulldozer pushes a wave of dirt over the drums
fa = f0("S14"); fe = fx("S14")
DOZ = OB["Dozer"]; DOZ.rotation_mode = 'XYZ'
DOZ_RZ = 180.0                       # the model's blade faces -X
M_dirt = bpy.data.materials["Dirt"]
FILL = box("DirtFill", (1, 30, 4.0), (0, 0, -2.0), M_dirt, OB["DumpGround"].users_collection[0])
FILL.data.transform(Matrix.Translation((0.5, 0, 0))); FILL.location = DX + Vector((-16, 0, 0.12))
x0 = HC.x - 12.0; v = 2.2
for f in range(fa - 1, fe + 2, 2):
    x = x0 + v * max(0, (f - fa)) / FPS
    key_prop(DOZ, f, (x, 0.0, 0.12), (0, 0, DOZ_RZ))
    FILL.scale = (max(0.01, x - 1.0 - FILL.location.x), 1, 1); FILL.keyframe_insert("scale", frame=f)
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=24, ring_count=12); MOUND = bpy.context.active_object; MOUND.name = "DirtWave"
MOUND.scale = (0.9, 2.6, 0.75); MOUND.data.materials.append(pbr('DirtWave', 'brown_mud', 0.5, tint=(0.75, 0.55, 0.4), coords='Object')); link(MOUND, OB["DumpGround"].users_collection[0])
txm = bpy.data.textures.new("mound", 'CLOUDS'); txm.noise_scale = 0.35; dm = MOUND.modifiers.new("lumps", 'DISPLACE'); dm.texture = txm; dm.strength = 0.25
for f in range(fa - 1, fe + 2, 2):
    x = x0 + v * max(0, (f - fa)) / FPS
    key_prop(MOUND, f, (x + DOZ.get("blade", 3.6), 0.0, 0.25), (0, 0, 0))
key_vis(MOUND, [(0, False), (fa, True)]); key_vis(FILL, [(0, False), (fa, True)])
camshot("S14", [(0.0, HC + Vector((-4.5, -13.5, 3.6)), HC + Vector((-7.0, 0.0, 0.6)), 30), (1.0, HC + Vector((-3.6, -12.6, 3.4)), HC + Vector((-5.5, 0.0, 0.6)), 30)])
for d in drums:                           # buried as the dirt wave in front of the blade reaches them
    ev(f1("S13")); px = d.matrix_world.translation.x
    tb = (px - (x0 + DOZ.get("blade", 3.6) + 0.6)) / v
    if tb < 0: key_vis(d, [(0, True), (f0("S14"), False)]) if not (d.animation_data and d.animation_data.action and any(fc.data_path == "hide_render" for fc in fcurves_of(d.animation_data.action))) else key_vis(d, [(f0("S14"), False)])
    elif fa + tb * FPS < fe + 60: key_vis(d, [(0, True), (int(fa + tb * FPS), False)]) if not (d.animation_data and d.animation_data.action and any(fc.data_path == "hide_render" for fc in fcurves_of(d.animation_data.action))) else key_vis(d, [(int(fa + tb * FPS), False)])

# ================================================================== S15: houses are framed on top of the cut-away while the green pockets glow underneath
fa = f0("S15"); fe = fx("S15")
k = 0
for r_ in ("Frame0", "Frame1"):
    root = OB[r_]
    kids = sorted([c for c in root.children], key=lambda o: (0 if "deck" in o.name else 2 if "roof" in o.name else 1, o.name))
    for c in kids:
        st = fa + 6 + k * 9 + (40 if "roof" in c.name else 0); k += 1
        base = c.location.copy()
        c.location = base + Vector((0, 0, -3.4)); c.keyframe_insert("location", frame=0); c.keyframe_insert("location", frame=st)
        c.location = base + Vector((0, 0, 0.12)); c.keyframe_insert("location", frame=st + 18)
        c.location = base; c.keyframe_insert("location", frame=st + 24)
camshot("S15", [(0.0, (574.0, 30.0, 9.0), (600.0, 60.0, -1.5), 30), (1.0, (589.0, 24.5, 8.0), (600.0, 60.0, -1.5), 30)])
