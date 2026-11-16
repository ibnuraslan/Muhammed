# exec'd by 03_anim.py: underground S7, S8; dump site S9-S14; house frames on the cut-away S15
UX = Vector((600, 0, 0)); UX2 = Vector((600, 60, 0)); DX = Vector((900, 0, 0))
key_vis(OB["Backdrop_under"], [(0, False)] + [x for s_ in ("S7", "S8", "S15") for x in ((f0(s_), True), (f1(s_) + 1, False))])
camshot("S7", [(0.0, (600.0, -42.0, 4.0), (600.0, 0.0, 1.5), 32), (1.0, (600.0, -39.0, 2.2), (600.0, 0.0, -4.0), 32)])
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
for f in range(fa, fe + 1, 20): WK.key_spine(f, flex=34, head=(-34, 0))
camshot("S9", [(0.0, (DX.x + 2.6, -19.6, 0.75), (DX.x - 0.6, -18.0, 0.95), 32), (1.0, (DX.x + 2.9, -19.2, 0.75), (DX.x + 0.0, -18.0, 0.95), 34)])

# ================================================================== S10: trucks loaded with drums; the Worker walks between them
fa = f0("S10"); fe = fx("S10")
pth = walk_line(WK, fa, fe, (0, 0), 1.1)
walk_arms(WK, fa, fe, pth); face(WK, fa, -0.002, -8)
for f in range(fa, fe + 1, 20): WK.key_spine(f, flex=4, head=(2, 0))
camshot("S10", [(0.0, (DX.x + 1.8, 7.5, 1.75), (DX.x - 0.3, 17.0, 1.4), 24), (1.0, (DX.x + 1.5, 8.6, 1.7), (DX.x - 0.3, 17.0, 1.4), 24)])

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
def fly(d, fs, fe_, P0, M1, q0, spin):
    """keyed arc from P0 (with orientation q0) into slot matrix M1, landing at fe_"""
    P1, q1, _ = M1.decompose(); d.rotation_mode = 'QUATERNION'
    apex = max(P0.z, P1.z) + 1.6
    for f in list(range(fs, fe_ + 1, 2)) + [fe_]:
        u = (f - fs) / max(1, fe_ - fs); w = u * u * (3 - 2 * u) * 0.35 + u * 0.65
        p = P0.lerp(P1, w); p.z = (1 - w) ** 2 * P0.z + 2 * (1 - w) * w * apex + w * w * P1.z
        q = q0.slerp(q1, smooth(u)) @ Quaternion((1, 0, 0), spin * (1 - smooth(u)))
        d.location = p; d.rotation_quaternion = q
        d.keyframe_insert("location", frame=f); d.keyframe_insert("rotation_quaternion", frame=f)
drums = []
ev(1); k = 0
for bi, b in enumerate(BEDS):            # wave 1: drums standing in each bed (seen in S10) ride the bed, then slide into the lowest slots
    bmn, bmx = bbox([b])
    for ix in range(3):
        for iy in range(5):
            x = bmn.x + 0.45 + ix * 0.62; y = bmn.y + 0.7 + iy * 0.75
            d = copy_obj(L_dr, "Drum_b%d_%d%d" % (bi, ix, iy), (x, y, bmn.z + 0.32 + 0.002), c=DCOLL); d.rotation_mode = 'QUATERNION'
            d.rotation_quaternion = Quaternion((0, 0, 1), random.random() * 6)
            REL = TIP0 + 50 + (4 - iy) * 6 + ix * 2
            ev(TIP0); OFF = b.matrix_world.inverted() @ d.matrix_world
            for f in range(TIP0, REL + 1, 2):
                ev(f); l_, q_, _ = (b.matrix_world @ OFF).decompose(); d.location = l_; d.rotation_quaternion = q_
                d.keyframe_insert("location", frame=f); d.keyframe_insert("rotation_quaternion", frame=f)
            ev(REL); P0, q0, _ = d.matrix_world.decompose()
            z_, src, M1 = slots[k]; k += 1
            fly(d, REL, REL + 46, P0, M1, q0, R_(160))
            drums.append(d)
ARR0, ARR1 = TIP0 + 120, f1("S13") - 25
rest = slots[k:]
for i, (z_, src, M1) in enumerate(rest):   # wave 2: one after another from the truck side, lowest slots first
    land = ARR0 + int((ARR1 - ARR0) * i / max(1, len(rest) - 1)); st = land - 44
    P1 = M1.translation
    P0 = Vector((P1.x * 0.7 + DX.x * 0.3 + random.uniform(-0.6, 0.6), DX.y + 12.8, 1.4 + random.uniform(0, 0.6)))
    src.rotation_mode = 'QUATERNION'
    fly(src, st, land, P0, M1, Quaternion((0, 0, 1), random.random() * 6) @ Quaternion((1, 0, 0), R_(80)), R_(random.choice((-200, 200))))
    key_vis(src, [(0, False), (st, True)])
    drums.append(src)
print("DRUMS keyed", len(drums), "landing", ARR0, ARR1)
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
    if tb < 0: key_vis(d, [(f0("S14"), False)])
    elif fa + tb * FPS < fe + 60: key_vis(d, [(int(fa + tb * FPS), False)])

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
